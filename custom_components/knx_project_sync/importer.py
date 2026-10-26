"""Run an import: parse project -> manifest -> plan -> package YAML -> knx.reload."""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
import logging
from pathlib import Path
from typing import Any

from homeassistant.components import persistent_notification
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers import area_registry as ar, entity_registry as er, issue_registry as ir
from homeassistant.helpers.dispatcher import async_dispatcher_send
from homeassistant.helpers.storage import Store
from homeassistant.util import dt as dt_util
import voluptuous as vol

from . import packages, writer, yamledit
from .const import (
    CONF_ASSIGN_AREAS,
    CONF_DOMAINS,
    CONF_PACKAGE_PATH,
    CONF_REMOVED,
    DATA_PACKAGES_ADDED,
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
from .mapping.manifest import HA_DOMAINS
from .plan import PENDING, ImportPlan, build_plan

_LOGGER = logging.getLogger(__name__)

STORAGE_VERSION = 1
NOTIFICATION_NEW = f"{DOMAIN}_new_entities"
NOTIFICATION_LOADED = f"{DOMAIN}_project_loaded"
PANEL_URL = "/knx-project-sync"
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
        CONF_DOMAINS: list(HA_DOMAINS),
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
        "text": schema.TextSchema,
    }

    def validate(domain: str, config: dict[str, Any]) -> str | None:
        try:
            schemas[domain].ENTITY_SCHEMA(dict(config))
        except vol.Invalid as err:
            return str(err)
        return None

    return validate


async def _async_foreign_entities(hass: HomeAssistant, package: Path) -> dict[tuple[str, str], dict[str, Any]]:
    """KNX YAML entities that are not ours (e.g. hand written knx: YAML), with file and line."""
    from homeassistant.config import async_hass_config_yaml

    try:
        config = await async_hass_config_yaml(hass)
    except HomeAssistantError:
        _LOGGER.warning("Could not read configuration.yaml to detect own KNX YAML entities")
        return {}
    merged = writer.entities_of_knx_config(config.get(KNX_DOMAIN) or {})
    ours = await hass.async_add_executor_job(writer.read_unique_ids, package)
    return {uid: info for uid, info in merged.items() if uid not in ours}


class Importer:
    """Holds the import state of the (single) config entry."""

    def __init__(self, hass: HomeAssistant) -> None:
        self.hass = hass
        self._store = Store[dict](hass, STORAGE_VERSION, DOMAIN)
        self.data: dict[str, Any] = {}
        # project loaded in the panel, not applied yet
        self.staged: tuple[Prepared, str] | None = None

    async def async_load(self) -> None:
        self.data = await self._store.async_load() or {}

    @property
    def manifest(self) -> dict[str, Any] | None:
        return self.data.get("manifest")

    @property
    def applied(self) -> dict[str, dict[str, Any]]:
        return self.data.get("applied", {})

    @property
    def selection(self) -> dict[str, dict[str, Any]]:
        """Choices made in the panel per entity key: enabled, domain, name."""
        return self.data.get("selection", {})

    def package_path(self, options: dict[str, Any]) -> Path:
        return Path(self.hass.config.path(options.get(CONF_PACKAGE_PATH) or DEFAULT_PACKAGE_PATH))

    async def async_plan(
        self, prepared: Prepared, options: dict[str, Any], selection: dict[str, dict[str, Any]] | None = None
    ) -> ImportPlan:
        """Plan an import; `selection` defaults to the stored choices of the panel."""
        foreign = await _async_foreign_entities(self.hass, self.package_path(options))
        validate = await self.hass.async_add_executor_job(_validator)
        return build_plan(
            prepared.manifest,
            self.applied,
            domains=options.get(CONF_DOMAINS) or list(HA_DOMAINS),
            keep_removed=options.get(CONF_REMOVED) == REMOVED_KEEP,
            foreign_entities=foreign,
            validate=validate,
            selection=self.selection if selection is None else selection,
            # first import: everything; later new entities are only offered in the panel
            include_new="last_import" not in self.data,
        )

    @property
    def source(self) -> str | None:
        """Where the current project came from (last import, or setup before any import)."""
        return self.data.get("last_import", {}).get("source") or self.data.get("source")

    async def async_save_initial(self, prepared: Prepared, source: str) -> None:
        """Setup: keep the project for the panel, nothing is created yet."""
        await self.async_load()
        self.data = {
            **self.data,
            "manifest": prepared.manifest,
            "rooms": prepared.rooms,
            "source": source,
        }
        await self._store.async_save(self.data)
        self.async_notify_loaded(prepared)

    def async_notify_loaded(self, prepared: Prepared) -> None:
        """Point to the panel after a project was read in a dialog."""
        project = prepared.manifest.get("project", {}).get("name") or "KNX"
        count = len(prepared.manifest["entities"])
        if self.hass.config.language.startswith("de"):
            title = f"KNX Project Sync: {project} eingelesen"
            message = (
                f"{count} Entities erkannt. Es wurde noch nichts angelegt.\n\n"
                f"[Im Panel auswählen und übernehmen]({PANEL_URL})"
            )
        else:
            title = f"KNX Project Sync: {project} loaded"
            message = f"{count} entities detected. Nothing was created yet.\n\n[Choose and apply them in the panel]({PANEL_URL})"
        persistent_notification.async_create(self.hass, message, title=title, notification_id=NOTIFICATION_LOADED)

    def stored_prepared(self) -> Prepared | None:
        if not self.manifest:
            return None
        return Prepared(manifest=self.manifest, rooms=self.data.get("rooms", {}))

    # ------------------------------------------------------------ applying

    async def async_apply(
        self,
        prepared: Prepared,
        plan: ImportPlan,
        options: dict[str, Any],
        source: str,
        selection: dict[str, dict[str, Any]] | None = None,
        notify: bool = True,
    ) -> dict:
        hass = self.hass
        known = {e["key"] for e in (self.manifest or {}).get("entities", [])}
        selection = dict(self.selection if selection is None else selection)

        # 0. definitions taken over from the own YAML: remove them there first
        registry = er.async_get(hass)
        package = self.package_path(options)
        adopted = await self._async_adopt(plan, package, selection)

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
        try:
            await hass.async_add_executor_job(writer.write, package, content)
        except Exception:
            # never lose an entity that was just removed from the own YAML
            await hass.async_add_executor_job(yamledit.restore, adopted)
            raise
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

        summary = {
            **plan.summary(),
            "migrated": migrated,
            "deleted": removed,
            "areas": areas,
            "adopted": len(adopted),
            "backups": sorted(str(b) for b in adopted.values()),
        }
        self.data = {
            "manifest": prepared.manifest,
            "rooms": prepared.rooms,
            "applied": plan.state(),
            "selection": selection,
            "last_import": {
                "time": dt_util.utcnow().isoformat(),
                "source": source,
                "project": plan.project,
                "summary": summary,
                "package": str(package),
            },
        }
        await self._store.async_save(self.data)
        self.staged = None
        persistent_notification.async_dismiss(hass, NOTIFICATION_LOADED)
        self._notify_new(plan, known if notify else None)
        async_dispatcher_send(hass, SIGNAL_IMPORTED)
        hass.bus.async_fire(EVENT_IMPORTED, {"project": plan.project, **summary})
        return summary

    async def _async_adopt(self, plan: ImportPlan, package: Path, selection: dict[str, dict[str, Any]]) -> dict:
        """Remove adopted entities from the user's YAML; returns file -> backup.

        Checked with Home Assistant's own YAML loader: exactly the adopted entities
        must be gone, otherwise the files are restored and nothing is applied.
        """
        entries = plan.adoptions
        if not entries:
            return {}
        items = [(e.conflict_with["file"], e.conflict_with["line"]) for e in entries]
        before = set(await _async_foreign_entities(self.hass, package))
        try:
            backups = await self.hass.async_add_executor_job(
                yamledit.remove_items, Path(self.hass.config.config_dir), items
            )
        except (yamledit.YamlEditError, OSError) as err:
            reason = err.reason if isinstance(err, yamledit.YamlEditError) else str(err)
            raise KnxImportError("adopt_failed", error=reason) from err
        gone = {(e.conflict_with["domain"], e.conflict_with["unique_id"]) for e in entries}
        after = set(await _async_foreign_entities(self.hass, package))
        if after != before - gone:
            await self.hass.async_add_executor_job(yamledit.restore, backups)
            raise KnxImportError("adopt_failed", error="verification")
        for e in entries:
            choice = {k: v for k, v in selection.get(e.key, {}).items() if k not in ("adopt", "existing")}
            selection[e.key] = {**choice, "domain": e.domain, "config": e.config}
        _LOGGER.info("Took over %s entities from the own KNX YAML, backups: %s", len(entries), backups)
        return backups

    def _notify_new(self, plan: ImportPlan, known: set[str] | None) -> None:
        """Tell about entities that are new in the project and can be added in the panel."""
        pending = plan.by_status(PENDING)
        if not pending or known is None:
            persistent_notification.async_dismiss(self.hass, NOTIFICATION_NEW)
            return
        new = [e for e in pending if e.key not in known]
        if not new:
            return
        names = "\n".join(f"- {e.name or e.key} ({e.domain})" for e in new[:10])
        if len(new) > 10:
            names += f"\n- … +{len(new) - 10}"
        if self.hass.config.language.startswith("de"):
            title = "KNX Project Sync: neue Entities gefunden"
            message = f"Das Projekt enthält {len(new)} neue Entities:\n\n{names}\n\n[Im Panel hinzufügen]({PANEL_URL})"
        else:
            title = "KNX Project Sync: new entities found"
            message = (
                f"The project contains {len(new)} new entities:\n\n{names}\n\n[Add them in the panel]({PANEL_URL})"
            )
        persistent_notification.async_create(self.hass, message, title=title, notification_id=NOTIFICATION_NEW)

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

    # ------------------------------------------------------------ packages

    async def async_package_setup(self, options: dict[str, Any]) -> packages.Setup:
        """Is the package file loaded by configuration.yaml, and what would fix it."""
        from homeassistant.config import YAML_CONFIG_FILE

        config_file = Path(self.hass.config.path(YAML_CONFIG_FILE))
        package = options.get(CONF_PACKAGE_PATH) or DEFAULT_PACKAGE_PATH

        def _work() -> packages.Setup:
            try:
                text = config_file.read_text(encoding="utf-8")
            except OSError as err:
                return packages.Setup(packages.MANUAL, package, str(err))
            return packages.analyze(text, package)

        return await self.hass.async_add_executor_job(_work)

    async def async_fix_packages(self, entry: Any) -> packages.Setup:
        """Make Home Assistant load the package file, then reload KNX.

        configuration.yaml is backed up and the result checked with Home Assistant's
        loader; on any problem the backup is restored.
        """
        from homeassistant.config import YAML_CONFIG_FILE, async_hass_config_yaml

        hass = self.hass
        options = {**default_options(), **entry.options}
        setup = await self.async_package_setup(options)
        if setup.status == packages.OK:
            return setup
        if setup.status == packages.MANUAL:
            raise KnxImportError("packages_manual", error=setup.detail or "")

        if setup.status != packages.MOVE:
            config_file = Path(hass.config.path(YAML_CONFIG_FILE))

            def _edit() -> tuple[Path, bool]:
                text = config_file.read_text(encoding="utf-8")
                new_text = packages.apply(text, setup)
                if packages.analyze(new_text, setup.package_path).status != packages.OK:
                    raise ValueError("not_loaded_after_edit")
                backup = yamledit.backup_path(config_file)
                backup.write_text(text, encoding="utf-8")
                config_file.write_text(new_text, encoding="utf-8")
                return backup, not packages.has_core_key(text)

            try:
                backup, block = await hass.async_add_executor_job(_edit)
            except (ValueError, OSError) as err:
                raise KnxImportError("packages_manual", error=str(err)) from err
            try:
                await async_hass_config_yaml(hass)
            except HomeAssistantError as err:
                await hass.async_add_executor_job(yamledit.restore, {config_file: backup})
                raise KnxImportError("packages_manual", error=str(err)) from err
            # taken out again when the integration is removed
            added = {"line": packages.added_line(setup), "block": block, "status": setup.status}
            hass.config_entries.async_update_entry(entry, data={**entry.data, DATA_PACKAGES_ADDED: added})
        if setup.package_path != options.get(CONF_PACKAGE_PATH):
            # the package file has to sit in the folder packages are loaded from
            old, new = self.package_path(options), Path(hass.config.path(setup.package_path))

            def _move() -> None:
                if old.exists() and not new.exists():
                    new.parent.mkdir(parents=True, exist_ok=True)
                    old.replace(new)

            await hass.async_add_executor_job(_move)
            hass.config_entries.async_update_entry(
                entry, options={**entry.options, CONF_PACKAGE_PATH: setup.package_path}
            )

        options = {**default_options(), **entry.options}
        package = self.package_path(options)
        if await hass.async_add_executor_job(package.exists):
            await self._async_reload_knx()
        ir.async_delete_issue(hass, DOMAIN, ISSUE_PACKAGE_NOT_LOADED)
        return await self.async_package_setup(options)

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
            is_fixable=True,
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

    async def async_remove(self, entry: Any) -> None:
        """Integration removed: drop the package file, the line added to
        configuration.yaml and the generated entities."""
        hass = self.hass
        options = {**default_options(), **entry.options}
        package = self.package_path(options)
        await hass.async_add_executor_job(lambda: package.unlink(missing_ok=True))
        if added := entry.data.get(DATA_PACKAGES_ADDED):
            await self._async_remove_packages_line(added, package)
        await self._async_reload_knx()
        registry = er.async_get(hass)
        for applied in self.applied.values():
            if entity_id := registry.async_get_entity_id(applied["domain"], KNX_DOMAIN, applied["unique_id"]):
                registry.async_remove(entity_id)
        await self._store.async_remove()

    async def _async_remove_packages_line(self, added: dict[str, Any], package: Path) -> None:
        """Take out the line `async_fix_packages` added, unless other packages need it."""
        from homeassistant.config import YAML_CONFIG_FILE, async_hass_config_yaml

        hass = self.hass
        config_file = Path(hass.config.path(YAML_CONFIG_FILE))
        folder = Path(hass.config.path(packages.DEFAULT_DIR))

        def _edit() -> Path | None:
            if added.get("status") == packages.ADD and folder.is_dir():
                others = [p for p in folder.rglob("*") if p.suffix in (".yaml", ".yml")]
                if others:
                    return None  # the folder holds packages of the user now
            text = config_file.read_text(encoding="utf-8")
            new_text = packages.revert(text, added["line"], bool(added.get("block")))
            backup = yamledit.backup_path(config_file)
            backup.write_text(text, encoding="utf-8")
            config_file.write_text(new_text, encoding="utf-8")
            if added.get("status") == packages.ADD and folder.is_dir() and not any(folder.iterdir()):
                folder.rmdir()
            return backup

        try:
            backup = await hass.async_add_executor_job(_edit)
        except (ValueError, OSError) as err:
            _LOGGER.warning("Could not remove the packages line from %s: %s", config_file, err)
            return
        if backup is None:
            return
        try:
            await async_hass_config_yaml(hass)
        except HomeAssistantError as err:
            await hass.async_add_executor_job(yamledit.restore, {config_file: backup})
            _LOGGER.warning("Could not remove the packages line from %s: %s", config_file, err)
