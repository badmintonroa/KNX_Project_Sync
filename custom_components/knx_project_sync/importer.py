"""Run an import: parse project -> manifest -> plan -> package YAML -> knx.reload."""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
import logging
from pathlib import Path
from typing import Any

from homeassistant.core import HomeAssistant
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers import area_registry as ar, entity_registry as er, issue_registry as ir
from homeassistant.helpers.dispatcher import async_dispatcher_send
from homeassistant.helpers.storage import Store
from homeassistant.util import dt as dt_util
import voluptuous as vol

from . import writer
from .const import (
    CONF_ASSIGN_AREAS,
    CONF_DOMAINS,
    CONF_PACKAGE_PATH,
    CONF_REMOVED,
    DEFAULT_PACKAGE_PATH,
    DOMAIN,
    EVENT_IMPORTED,
    ISSUE_PACKAGE_NOT_LOADED,
    ISSUE_RELOAD_FAILED,
    KNX_DOMAIN,
    KNX_PROJECT_STORAGE_KEY,
    REMOVED_KEEP,
    SIGNAL_IMPORTED,
    VERSION,
)
from .mapping import build_ha_entities, build_manifest, catalog_from_xknxproject
from .mapping.catalog import Catalog
from .mapping.manifest import DOMAINS
from .plan import ImportPlan, build_plan

_LOGGER = logging.getLogger(__name__)

STORAGE_VERSION = 1
GENERATOR = {"name": DOMAIN, "version": VERSION}


class KnxImportError(HomeAssistantError):
    """Import failed; `translation_key` explains why."""

    def __init__(self, key: str, **placeholders: str) -> None:
        super().__init__(key)
        self.key = key
        self.placeholders = placeholders


@dataclass
class Prepared:
    """Parsed project, ready to be planned with different options."""

    manifest: dict[str, Any]
    rooms: dict[str, str]  # entity key -> ETS room name


def default_options() -> dict[str, Any]:
    return {
        CONF_DOMAINS: list(DOMAINS),
        CONF_REMOVED: "delete",
        CONF_ASSIGN_AREAS: False,
        CONF_PACKAGE_PATH: DEFAULT_PACKAGE_PATH,
    }


# ---------------------------------------------------------------- parsing


def _rooms_for_entities(catalog: Catalog, manifest: dict[str, Any]) -> dict[str, str]:
    """Room of the first linked device (actuators first) of each entity's GAs."""
    devices_by_ga: dict[str, list[tuple[bool, str]]] = {}
    for link in catalog.links:
        sends = bool(link.flags and link.flags.get("TransmitFlag") and not link.flags.get("WriteFlag"))
        devices_by_ga.setdefault(link.ga_id, []).append((sends, link.device_id))
    rooms: dict[str, str] = {}
    for entity in manifest["entities"]:
        candidates = Counter()
        for source in entity["sources"]:
            for _, device in sorted(devices_by_ga.get(source["ga_id"] or "", [])):
                if room := catalog.device_rooms.get(device):
                    candidates[room] += 1
        if candidates:
            rooms[entity["key"]] = candidates.most_common(1)[0][0]
    return rooms


def prepare_project(project: dict[str, Any]) -> Prepared:
    catalog = catalog_from_xknxproject(project)
    manifest = build_manifest(catalog, build_ha_entities(catalog), GENERATOR)
    return Prepared(manifest=manifest, rooms=_rooms_for_entities(catalog, manifest))


def parse_project_file(path: Path, password: str | None) -> dict[str, Any]:
    """Parse a .knxproj (runs in the executor)."""
    from xknxproject import XKNXProj
    from xknxproject.exceptions import InvalidPasswordException, XknxProjectException

    try:
        return XKNXProj(path, password=password or None, language="de-DE").parse()
    except InvalidPasswordException as err:
        raise KnxImportError("invalid_password") from err
    except (XknxProjectException, KeyError, ValueError, OSError) as err:
        _LOGGER.exception("Could not parse %s", path)
        raise KnxImportError("invalid_project", error=str(err)) from err


async def async_prepare_upload(hass: HomeAssistant, file_id: str, password: str | None) -> Prepared:
    from homeassistant.components.file_upload import process_uploaded_file

    def _work() -> Prepared:
        with process_uploaded_file(hass, file_id) as path:
            return prepare_project(parse_project_file(path, password))

    return await hass.async_add_executor_job(_work)


async def async_prepare_file(hass: HomeAssistant, path: str, password: str | None) -> Prepared:
    """Project file inside the config folder (or an allowlisted external dir)."""

    def _work() -> Prepared:
        file = Path(hass.config.path(path)).resolve()
        inside_config = file.is_relative_to(Path(hass.config.config_dir).resolve())
        if not (inside_config or hass.config.is_allowed_path(str(file))) or not file.is_file():
            raise KnxImportError("file_not_found", path=str(file))
        return prepare_project(parse_project_file(file, password))

    return await hass.async_add_executor_job(_work)


async def async_prepare_knx_project(hass: HomeAssistant) -> Prepared:
    """Use the project already uploaded in the KNX panel."""
    project = await Store[dict](hass, 1, KNX_PROJECT_STORAGE_KEY).async_load()
    if not project or not project.get("communication_objects"):
        raise KnxImportError("no_knx_project")
    return await hass.async_add_executor_job(prepare_project, project)


async def async_has_knx_project(hass: HomeAssistant) -> bool:
    return bool(await Store[dict](hass, 1, KNX_PROJECT_STORAGE_KEY).async_load())


# ---------------------------------------------------------------- planning


def _validator():
    """Validate entity configs with the KNX YAML schema of the installed HA version."""
    from homeassistant.components.knx import schema

    schemas = {
        "switch": schema.SwitchSchema,
        "binary_sensor": schema.BinarySensorSchema,
        "light": schema.LightSchema,
        "sensor": schema.SensorSchema,
        "time": schema.TimeSchema,
        "date": schema.DateSchema,
        "datetime": schema.DateTimeSchema,
        "cover": schema.CoverSchema,
        "scene": schema.SceneSchema,
        "climate": schema.ClimateSchema,
        "weather": schema.WeatherSchema,
    }

    def validate(domain: str, config: dict[str, Any]) -> str | None:
        try:
            schemas[domain].ENTITY_SCHEMA(dict(config))
        except vol.Invalid as err:
            return str(err)
        return None

    return validate


async def _async_foreign_unique_ids(hass: HomeAssistant, package: Path) -> set[tuple[str, str]]:
    """unique_ids of KNX YAML entities that are not ours (e.g. hand written knx: YAML)."""
    from homeassistant.config import async_hass_config_yaml

    try:
        config = await async_hass_config_yaml(hass)
    except HomeAssistantError:
        _LOGGER.warning("Could not read configuration.yaml to detect own KNX YAML entities")
        return set()
    merged = writer.unique_ids_of_knx_config(config.get(KNX_DOMAIN) or {})
    ours = await hass.async_add_executor_job(writer.read_unique_ids, package)
    return merged - ours


class Importer:
    """Holds the import state of the (single) config entry."""

    def __init__(self, hass: HomeAssistant) -> None:
        self.hass = hass
        self._store = Store[dict](hass, STORAGE_VERSION, DOMAIN)
        self.data: dict[str, Any] = {}

    async def async_load(self) -> None:
        self.data = await self._store.async_load() or {}

    @property
    def manifest(self) -> dict[str, Any] | None:
        return self.data.get("manifest")

    @property
    def applied(self) -> dict[str, dict[str, Any]]:
        return self.data.get("applied", {})

    def package_path(self, options: dict[str, Any]) -> Path:
        return Path(self.hass.config.path(options.get(CONF_PACKAGE_PATH) or DEFAULT_PACKAGE_PATH))

    async def async_plan(self, prepared: Prepared, options: dict[str, Any]) -> ImportPlan:
        foreign = await _async_foreign_unique_ids(self.hass, self.package_path(options))
        validate = await self.hass.async_add_executor_job(_validator)
        return build_plan(
            prepared.manifest,
            self.applied,
            domains=options.get(CONF_DOMAINS) or list(DOMAINS),
            keep_removed=options.get(CONF_REMOVED) == REMOVED_KEEP,
            foreign_unique_ids=foreign,
            validate=validate,
        )

    def stored_prepared(self) -> Prepared | None:
        if not self.manifest:
            return None
        return Prepared(manifest=self.manifest, rooms=self.data.get("rooms", {}))

    # ------------------------------------------------------------ applying

    async def async_apply(self, prepared: Prepared, plan: ImportPlan, options: dict[str, Any], source: str) -> dict:
        hass = self.hass
        registry = er.async_get(hass)
        package = self.package_path(options)

        # 1. keep entity_id, name, area and history when a unique_id changes (e.g. GA re-addressed)
        migrated = 0
        for domain, old_uid, new_uid in plan.migrations:
            entity_id = registry.async_get_entity_id(domain, KNX_DOMAIN, old_uid)
            if not entity_id or registry.async_get_entity_id(domain, KNX_DOMAIN, new_uid):
                continue
            registry.async_update_entity(entity_id, new_unique_id=new_uid)
            migrated += 1

        # 2. package file + reload of the KNX integration
        content = writer.render(plan.yaml_data(), plan.project)
        await hass.async_add_executor_job(writer.write, package, content)
        await self._async_reload_knx()

        # 3. entities that are gone from the project
        removed = 0
        for domain, uid in plan.removed_unique_ids:
            if entity_id := registry.async_get_entity_id(domain, KNX_DOMAIN, uid):
                registry.async_remove(entity_id)
                removed += 1

        # 4. ETS rooms -> HA areas (only for entities without an area)
        areas = 0
        if options.get(CONF_ASSIGN_AREAS):
            areas = self._assign_areas(plan, prepared.rooms)

        await self._async_check_package_loaded(plan, package)

        summary = {**plan.summary(), "migrated": migrated, "deleted": removed, "areas": areas}
        self.data = {
            "manifest": prepared.manifest,
            "rooms": prepared.rooms,
            "applied": plan.state(),
            "last_import": {
                "time": dt_util.utcnow().isoformat(),
                "source": source,
                "project": plan.project,
                "summary": summary,
                "package": str(package),
            },
        }
        await self._store.async_save(self.data)
        async_dispatcher_send(hass, SIGNAL_IMPORTED)
        hass.bus.async_fire(EVENT_IMPORTED, {"project": plan.project, **summary})
        return summary

    async def _async_reload_knx(self) -> None:
        hass = self.hass
        if not hass.services.has_service(KNX_DOMAIN, "reload"):
            _LOGGER.warning("KNX integration is not set up, entities are created when it starts")
            return
        try:
            await hass.services.async_call(KNX_DOMAIN, "reload", blocking=True)
        except HomeAssistantError as err:
            ir.async_create_issue(
                hass,
                DOMAIN,
                ISSUE_RELOAD_FAILED,
                is_fixable=False,
                severity=ir.IssueSeverity.ERROR,
                translation_key=ISSUE_RELOAD_FAILED,
                translation_placeholders={"error": str(err)},
            )
            return
        ir.async_delete_issue(hass, DOMAIN, ISSUE_RELOAD_FAILED)

    async def _async_check_package_loaded(self, plan: ImportPlan, package: Path) -> None:
        """Repair issue if Home Assistant does not load the package file."""
        from homeassistant.config import async_hass_config_yaml

        written = plan.written
        if not written:
            ir.async_delete_issue(self.hass, DOMAIN, ISSUE_PACKAGE_NOT_LOADED)
            return
        try:
            config = await async_hass_config_yaml(self.hass)
        except HomeAssistantError:
            return
        loaded = writer.unique_ids_of_knx_config(config.get(KNX_DOMAIN) or {})
        if any((e.domain, e.unique_id) in loaded for e in written):
            ir.async_delete_issue(self.hass, DOMAIN, ISSUE_PACKAGE_NOT_LOADED)
            return
        ir.async_create_issue(
            self.hass,
            DOMAIN,
            ISSUE_PACKAGE_NOT_LOADED,
            is_fixable=False,
            severity=ir.IssueSeverity.WARNING,
            translation_key=ISSUE_PACKAGE_NOT_LOADED,
            translation_placeholders={"path": str(package)},
        )

    def _assign_areas(self, plan: ImportPlan, rooms: dict[str, str]) -> int:
        registry = er.async_get(self.hass)
        areas = ar.async_get(self.hass)
        count = 0
        for entry in plan.written:
            room = rooms.get(entry.key)
            entity_id = registry.async_get_entity_id(entry.domain, KNX_DOMAIN, entry.unique_id)
            if not room or not entity_id:
                continue
            reg_entry = registry.async_get(entity_id)
            if reg_entry is None or reg_entry.area_id:
                continue
            area = areas.async_get_area_by_name(room) or areas.async_create(room)
            registry.async_update_entity(entity_id, area_id=area.id)
            count += 1
        return count

    async def async_remove(self, options: dict[str, Any]) -> None:
        """Integration removed: drop the package file and the generated entities."""
        package = self.package_path(options)
        await self.hass.async_add_executor_job(lambda: package.unlink(missing_ok=True))
        await self._async_reload_knx()
        await self._store.async_remove()
