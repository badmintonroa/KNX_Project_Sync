"""Import state of the config entry: store, plan, apply, remove.

Reading the project is in `project.py`, the registry changes in `registry.py` and
everything about configuration.yaml in `packages.py`. This module ties them together.
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

from homeassistant.components import persistent_notification
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers import issue_registry as ir
from homeassistant.helpers.dispatcher import async_dispatcher_send
from homeassistant.helpers.storage import Store
from homeassistant.util import dt as dt_util
import voluptuous as vol

from . import packages, registry, writer, yamledit
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
    REMOVED_KEEP,
    SIGNAL_IMPORTED,
)
from .errors import KnxImportError
from .mapping.manifest import HA_DOMAINS
from .model import AppliedState, OwnEntities, Selection, Status
from .plan import ImportPlan, build_plan
from .project import Prepared

_LOGGER = logging.getLogger(__name__)

STORAGE_VERSION = 1
NOTIFICATION_NEW = f"{DOMAIN}_new_entities"
NOTIFICATION_LOADED = f"{DOMAIN}_project_loaded"
PANEL_URL = "/knx-project-sync"


def default_options() -> dict[str, Any]:
    return {
        CONF_DOMAINS: list(HA_DOMAINS),
        CONF_REMOVED: "delete",
        CONF_ASSIGN_AREAS: False,
        CONF_PACKAGE_PATH: DEFAULT_PACKAGE_PATH,
    }


def entry_options(entry: ConfigEntry) -> dict[str, Any]:
    """Options of the config entry, completed with the defaults."""
    return {**default_options(), **entry.options}


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


async def _async_foreign_entities(hass: HomeAssistant, package: Path) -> OwnEntities:
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
    def applied(self) -> AppliedState:
        return self.data.get("applied", {})

    @property
    def selection(self) -> Selection:
        """Choices made in the panel per entity key."""
        return self.data.get("selection", {})

    def package_path(self, options: dict[str, Any]) -> Path:
        return Path(self.hass.config.path(options.get(CONF_PACKAGE_PATH) or DEFAULT_PACKAGE_PATH))

    async def async_plan(
        self, prepared: Prepared, options: dict[str, Any], selection: Selection | None = None
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
        selection: Selection | None = None,
        notify: bool = True,
    ) -> dict:
        hass = self.hass
        known = {e["key"] for e in (self.manifest or {}).get("entities", [])}
        selection = dict(self.selection if selection is None else selection)
        package = self.package_path(options)

        adopted = await self._async_adopt(plan, package, selection)
        migrated = registry.migrate_unique_ids(hass, plan.migrations)
        await self._async_write_package(plan, package, adopted)
        await self._async_reload_knx()
        removed = registry.remove_entities(hass, plan.removed_unique_ids)
        areas = registry.assign_areas(hass, plan.written, prepared.rooms) if options.get(CONF_ASSIGN_AREAS) else 0
        await packages.async_check_loaded(hass, plan.written, package)

        summary = {
            **plan.summary(),
            "migrated": migrated,
            "deleted": removed,
            "areas": areas,
            "adopted": len(adopted),
            "backups": sorted(str(b) for b in adopted.values()),
        }
        await self._async_save_applied(prepared, plan, selection, source, package, summary)
        self._announce(plan, summary, known if notify else None)
        return summary

    async def _async_write_package(self, plan: ImportPlan, package: Path, adopted: dict) -> None:
        content = writer.render(plan.yaml_data(), plan.project)
        try:
            await self.hass.async_add_executor_job(writer.write, package, content)
        except Exception:
            # never lose an entity that was just removed from the own YAML
            await self.hass.async_add_executor_job(yamledit.restore, adopted)
            raise

    async def _async_save_applied(
        self,
        prepared: Prepared,
        plan: ImportPlan,
        selection: Selection,
        source: str,
        package: Path,
        summary: dict[str, Any],
    ) -> None:
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

    def _announce(self, plan: ImportPlan, summary: dict[str, Any], known: set[str] | None) -> None:
        """Notifications, the sensor and the event after an import."""
        persistent_notification.async_dismiss(self.hass, NOTIFICATION_LOADED)
        self._notify_new(plan, known)
        async_dispatcher_send(self.hass, SIGNAL_IMPORTED)
        self.hass.bus.async_fire(EVENT_IMPORTED, {"project": plan.project, **summary})

    async def _async_adopt(self, plan: ImportPlan, package: Path, selection: Selection) -> dict:
        """Remove adopted entities from the user's YAML; returns file -> backup.

        Checked with Home Assistant's own YAML loader: exactly the adopted entities
        must be gone, otherwise the files are restored and nothing is applied.
        """
        entries = plan.adoptions
        if not entries:
            return {}
        items = [(e.conflict_with.file, e.conflict_with.line) for e in entries]
        before = set(await _async_foreign_entities(self.hass, package))
        try:
            backups = await self.hass.async_add_executor_job(
                yamledit.remove_items, Path(self.hass.config.config_dir), items
            )
        except (yamledit.YamlEditError, OSError) as err:
            reason = err.reason if isinstance(err, yamledit.YamlEditError) else str(err)
            raise KnxImportError("adopt_failed", error=reason) from err
        gone = {(e.conflict_with.domain, e.conflict_with.unique_id) for e in entries}
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
        pending = plan.by_status(Status.PENDING)
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
        return await packages.async_analyze(self.hass, options.get(CONF_PACKAGE_PATH) or DEFAULT_PACKAGE_PATH)

    async def async_fix_packages(self, entry: ConfigEntry) -> packages.Setup:
        """Make Home Assistant load the package file, then reload KNX.

        configuration.yaml is backed up and the result checked with Home Assistant's
        loader; on any problem the backup is restored.
        """
        hass = self.hass
        options = entry_options(entry)
        setup = await self.async_package_setup(options)
        if setup.status == packages.OK:
            return setup
        if setup.status == packages.MANUAL:
            raise KnxImportError("packages_manual", error=setup.detail or "")

        if setup.status != packages.MOVE:
            added = await packages.async_add_line(hass, setup)
            # taken out again when the integration is removed
            hass.config_entries.async_update_entry(entry, data={**entry.data, DATA_PACKAGES_ADDED: added})
        if setup.package_path != options.get(CONF_PACKAGE_PATH):
            # the package file has to sit in the folder packages are loaded from
            new = Path(hass.config.path(setup.package_path))
            await packages.async_move_file(hass, self.package_path(options), new)
            hass.config_entries.async_update_entry(
                entry, options={**entry.options, CONF_PACKAGE_PATH: setup.package_path}
            )

        options = entry_options(entry)
        package = self.package_path(options)
        if await hass.async_add_executor_job(package.exists):
            await self._async_reload_knx()
        ir.async_delete_issue(hass, DOMAIN, ISSUE_PACKAGE_NOT_LOADED)
        return await self.async_package_setup(options)

    # ------------------------------------------------------------ removal

    async def async_remove(self, entry: ConfigEntry) -> None:
        """Integration removed: drop the package file, the line added to
        configuration.yaml and the generated entities."""
        hass = self.hass
        package = self.package_path(entry_options(entry))
        await hass.async_add_executor_job(lambda: package.unlink(missing_ok=True))
        if added := entry.data.get(DATA_PACKAGES_ADDED):
            await packages.async_remove_line(hass, added)
        await self._async_reload_knx()
        registry.remove_entities(hass, ((a["domain"], a["unique_id"]) for a in self.applied.values()))
        await self._store.async_remove()
