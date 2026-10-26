"""Config and options flow: only choose where the project comes from.

Nothing is created here. The project is read and shown in the panel, where the
entities are chosen and applied.
"""

from __future__ import annotations

from typing import Any

from homeassistant.config_entries import ConfigEntry, ConfigFlow, ConfigFlowResult, OptionsFlow
from homeassistant.core import callback
from homeassistant.helpers import selector
import voluptuous as vol

from .const import (
    CONF_ASSIGN_AREAS,
    CONF_DOMAINS,
    CONF_FILE,
    CONF_PACKAGE_PATH,
    CONF_PASSWORD,
    CONF_REMOVED,
    DOMAIN,
    KNX_DOMAIN,
    REMOVED_DELETE,
    REMOVED_KEEP,
    SOURCE_KNX_PROJECT,
    SOURCE_UPLOAD,
)
from .importer import (
    PANEL_URL,
    Importer,
    KnxImportError,
    Prepared,
    async_has_knx_project,
    async_prepare_knx_project,
    async_prepare_upload,
    default_options,
    entry_options,
)
from .mapping.manifest import HA_DOMAINS


def _options_schema(options: dict[str, Any]) -> vol.Schema:
    return vol.Schema(
        {
            vol.Required(CONF_DOMAINS, default=options[CONF_DOMAINS]): selector.SelectSelector(
                selector.SelectSelectorConfig(options=list(HA_DOMAINS), multiple=True, translation_key=CONF_DOMAINS)
            ),
            vol.Required(CONF_REMOVED, default=options[CONF_REMOVED]): selector.SelectSelector(
                selector.SelectSelectorConfig(options=[REMOVED_DELETE, REMOVED_KEEP], translation_key=CONF_REMOVED)
            ),
            vol.Required(CONF_ASSIGN_AREAS, default=options[CONF_ASSIGN_AREAS]): selector.BooleanSelector(),
            vol.Required(CONF_PACKAGE_PATH, default=options[CONF_PACKAGE_PATH]): selector.TextSelector(),
        }
    )


UPLOAD_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_FILE): selector.FileSelector(selector.FileSelectorConfig(accept=".knxproj")),
        vol.Optional(CONF_PASSWORD): selector.TextSelector(
            selector.TextSelectorConfig(type=selector.TextSelectorType.PASSWORD)
        ),
    }
)


def _summary(prepared: Prepared) -> dict[str, str]:
    return {
        "project": prepared.manifest.get("project", {}).get("name") or "KNX",
        "entities": str(len(prepared.manifest["entities"])),
        "panel": PANEL_URL,
    }


class _SourceSteps:
    """Choose the project source: new file or the project of the KNX panel."""

    hass: Any

    async def _async_loaded(self, prepared: Prepared, source: str) -> ConfigFlowResult:
        raise NotImplementedError

    async def _async_source_menu(self, step_id: str, extra: list[str] | None = None) -> ConfigFlowResult:
        menu = [SOURCE_UPLOAD]
        if await async_has_knx_project(self.hass):
            menu.append(SOURCE_KNX_PROJECT)
        menu += extra or []
        if len(menu) == 1:
            return await self.async_step_upload()
        return self.async_show_menu(step_id=step_id, menu_options=menu)

    async def async_step_upload(self, user_input: dict[str, Any] | None = None) -> ConfigFlowResult:
        errors: dict[str, str] = {}
        placeholders = {"error": ""}
        if user_input is not None:
            try:
                prepared = await async_prepare_upload(self.hass, user_input[CONF_FILE], user_input.get(CONF_PASSWORD))
            except KnxImportError as err:
                errors["base"] = err.key
                if detail := err.placeholders.get("error"):
                    placeholders["error"] = f"\n\n`{detail}`"
            else:
                return await self._async_loaded(prepared, SOURCE_UPLOAD)
        return self.async_show_form(
            step_id="upload", data_schema=UPLOAD_SCHEMA, errors=errors, description_placeholders=placeholders
        )

    async def async_step_knx_project(self, user_input: dict[str, Any] | None = None) -> ConfigFlowResult:
        try:
            prepared = await async_prepare_knx_project(self.hass)
        except KnxImportError as err:
            return self.async_abort(reason=err.key)
        return await self._async_loaded(prepared, SOURCE_KNX_PROJECT)


class KnxProjectSyncConfigFlow(_SourceSteps, ConfigFlow, domain=DOMAIN):
    """Set up: read the project; choosing and creating entities happens in the panel."""

    VERSION = 1
    MINOR_VERSION = 2  # 1.2: "text" in the entity types

    async def async_step_user(self, user_input: dict[str, Any] | None = None) -> ConfigFlowResult:
        if not self.hass.config_entries.async_entries(KNX_DOMAIN):
            return self.async_abort(reason="knx_not_configured")
        return await self._async_source_menu("user")

    async def _async_loaded(self, prepared: Prepared, source: str) -> ConfigFlowResult:
        importer = Importer(self.hass)
        await importer.async_save_initial(prepared, source)
        summary = _summary(prepared)
        return self.async_create_entry(
            title=summary["project"], data={}, options=default_options(), description_placeholders=summary
        )

    @staticmethod
    @callback
    def async_get_options_flow(config_entry: ConfigEntry) -> OptionsFlow:
        return KnxProjectSyncOptionsFlow()


class KnxProjectSyncOptionsFlow(_SourceSteps, OptionsFlow):
    """New project version (shown in the panel) or settings."""

    async def async_step_init(self, user_input: dict[str, Any] | None = None) -> ConfigFlowResult:
        return await self._async_source_menu("init", ["settings"])

    async def _async_loaded(self, prepared: Prepared, source: str) -> ConfigFlowResult:
        importer: Importer = self.config_entry.runtime_data
        importer.staged = (prepared, source)
        importer.async_notify_loaded(prepared)
        return self.async_create_entry(
            data=dict(self.config_entry.options), description_placeholders=_summary(prepared)
        )

    async def async_step_settings(self, user_input: dict[str, Any] | None = None) -> ConfigFlowResult:
        options = entry_options(self.config_entry)
        if user_input is not None:
            # applied in the panel, which shows what the new settings change
            return self.async_create_entry(data={**options, **user_input})
        return self.async_show_form(step_id="settings", data_schema=_options_schema(options))
