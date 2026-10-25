"""KNX Project Sync: KNX entities from an ETS project, kept up to date on re-import."""

from __future__ import annotations

from typing import Any

from homeassistant.config_entries import SIGNAL_CONFIG_ENTRY_CHANGED, ConfigEntry, ConfigEntryChange
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant, ServiceCall, ServiceResponse, SupportsResponse, callback
from homeassistant.exceptions import ServiceValidationError
from homeassistant.helpers import config_validation as cv
from homeassistant.helpers.dispatcher import async_dispatcher_connect
from homeassistant.helpers.typing import ConfigType
import voluptuous as vol

from .const import (
    CONF_DOMAINS,
    CONF_PASSWORD,
    CONF_SOURCE,
    DOMAIN,
    LEGACY_DOMAIN,
    SERVICE_IMPORT_PROJECT,
    SOURCE_KNX_PROJECT,
)
from .importer import (
    Importer,
    KnxImportError,
    async_prepare_file,
    async_prepare_knx_project,
    default_options,
)
from .migration import async_update_legacy_issue
from .websocket import async_register_commands, async_register_panel, async_unregister_panel

PLATFORMS = [Platform.SENSOR]
CONFIG_SCHEMA = cv.config_entry_only_config_schema(DOMAIN)

type KnxProjectSyncConfigEntry = ConfigEntry[Importer]

SERVICE_SCHEMA = vol.Schema(
    {
        vol.Optional("file"): cv.string,
        vol.Optional(CONF_PASSWORD): cv.string,
        vol.Optional(CONF_SOURCE, default="file"): vol.In(["file", SOURCE_KNX_PROJECT]),
        vol.Optional("dry_run", default=False): cv.boolean,
    }
)


async def async_setup(hass: HomeAssistant, config: ConfigType) -> bool:
    async_register_commands(hass)

    async def import_project(call: ServiceCall) -> ServiceResponse:
        entries = hass.config_entries.async_loaded_entries(DOMAIN)
        if not entries:
            raise ServiceValidationError(translation_domain=DOMAIN, translation_key="not_set_up")
        entry: KnxProjectSyncConfigEntry = entries[0]
        importer = entry.runtime_data
        try:
            if call.data[CONF_SOURCE] == SOURCE_KNX_PROJECT:
                prepared = await async_prepare_knx_project(hass)
            elif file := call.data.get("file"):
                prepared = await async_prepare_file(hass, file, call.data.get(CONF_PASSWORD))
            else:
                raise ServiceValidationError(translation_domain=DOMAIN, translation_key="file_required")
        except KnxImportError as err:
            raise ServiceValidationError(
                translation_domain=DOMAIN, translation_key=err.key, translation_placeholders=err.placeholders
            ) from err
        options = {**default_options(), **entry.options}
        plan = await importer.async_plan(prepared, options)
        if call.data["dry_run"]:
            return {
                "summary": plan.summary(),
                "entities": [
                    {"key": e.key, "domain": e.domain, "name": e.name, "status": e.status, "reason": e.reason}
                    for e in plan.entries
                ],
            }
        summary = await importer.async_apply(prepared, plan, options, call.data[CONF_SOURCE])
        return {"summary": summary}

    hass.services.async_register(
        DOMAIN,
        SERVICE_IMPORT_PROJECT,
        import_project,
        schema=SERVICE_SCHEMA,
        supports_response=SupportsResponse.OPTIONAL,
    )
    return True


async def async_migrate_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """1.1 -> 1.2: text entities exist; offer them wherever sensors were enabled."""
    if entry.version > 1:
        return False
    if entry.minor_version < 2:
        domains = list(entry.options.get(CONF_DOMAINS) or [])
        if "sensor" in domains and "text" not in domains:
            domains.append("text")
        options = {**entry.options, CONF_DOMAINS: domains} if domains else dict(entry.options)
        hass.config_entries.async_update_entry(entry, options=options, minor_version=2)
    return True


async def async_setup_entry(hass: HomeAssistant, entry: KnxProjectSyncConfigEntry) -> bool:
    importer = Importer(hass)
    await importer.async_load()
    entry.runtime_data = importer

    async_update_legacy_issue(hass)

    @callback
    def legacy_changed(change: ConfigEntryChange, changed: ConfigEntry) -> None:
        if changed.domain == LEGACY_DOMAIN:
            async_update_legacy_issue(hass)

    entry.async_on_unload(async_dispatcher_connect(hass, SIGNAL_CONFIG_ENTRY_CHANGED, legacy_changed))
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    await async_register_panel(hass)
    return True


async def async_unload_entry(hass: HomeAssistant, entry: KnxProjectSyncConfigEntry) -> bool:
    async_unregister_panel(hass)
    return await hass.config_entries.async_unload_platforms(entry, PLATFORMS)


async def async_remove_entry(hass: HomeAssistant, entry: KnxProjectSyncConfigEntry) -> None:
    importer = Importer(hass)
    await importer.async_load()
    options: dict[str, Any] = {**default_options(), **entry.options}
    await importer.async_remove(options)
