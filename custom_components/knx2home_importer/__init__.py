"""KNX2HOME Importer: KNX entities from an ETS project, kept up to date on re-import."""

from __future__ import annotations

from typing import Any

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant, ServiceCall, ServiceResponse, SupportsResponse
from homeassistant.exceptions import ServiceValidationError
from homeassistant.helpers import config_validation as cv
from homeassistant.helpers.typing import ConfigType
import voluptuous as vol

from .const import CONF_PASSWORD, CONF_SOURCE, DOMAIN, SERVICE_IMPORT_PROJECT, SOURCE_KNX_PROJECT
from .importer import (
    Importer,
    KnxImportError,
    async_prepare_file,
    async_prepare_knx_project,
    default_options,
)

PLATFORMS = [Platform.SENSOR]
CONFIG_SCHEMA = cv.config_entry_only_config_schema(DOMAIN)

type Knx2HomeConfigEntry = ConfigEntry[Importer]

SERVICE_SCHEMA = vol.Schema(
    {
        vol.Optional("file"): cv.string,
        vol.Optional(CONF_PASSWORD): cv.string,
        vol.Optional(CONF_SOURCE, default="file"): vol.In(["file", SOURCE_KNX_PROJECT]),
        vol.Optional("dry_run", default=False): cv.boolean,
    }
)


async def async_setup(hass: HomeAssistant, config: ConfigType) -> bool:
    async def import_project(call: ServiceCall) -> ServiceResponse:
        entries = hass.config_entries.async_loaded_entries(DOMAIN)
        if not entries:
            raise ServiceValidationError(translation_domain=DOMAIN, translation_key="not_set_up")
        entry: Knx2HomeConfigEntry = entries[0]
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


async def async_setup_entry(hass: HomeAssistant, entry: Knx2HomeConfigEntry) -> bool:
    importer = Importer(hass)
    await importer.async_load()
    entry.runtime_data = importer
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True


async def async_unload_entry(hass: HomeAssistant, entry: Knx2HomeConfigEntry) -> bool:
    return await hass.config_entries.async_unload_platforms(entry, PLATFORMS)


async def async_remove_entry(hass: HomeAssistant, entry: Knx2HomeConfigEntry) -> None:
    importer = Importer(hass)
    await importer.async_load()
    options: dict[str, Any] = {**default_options(), **entry.options}
    await importer.async_remove(options)
