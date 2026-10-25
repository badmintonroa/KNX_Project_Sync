"""Config and options flow: upload project -> options -> preview -> import."""

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
    Importer,
    KnxImportError,
    Prepared,
    async_has_knx_project,
    async_prepare_knx_project,
    async_prepare_upload,
    default_options,
)
from .mapping.manifest import DOMAINS
from .migration import async_find_legacy, async_take_over
from .plan import CHANGED, CONFLICT, DUPLICATE, INVALID, KEPT, NEW, REMOVED, ImportPlan

PREVIEW_LIMIT = 15


def _entry_line(entry) -> str:
    name = entry.name or entry.key
    if entry.status == CHANGED and entry.previous_config:
        changed = sorted(
            k for k in {*entry.config, *entry.previous_config} if entry.config.get(k) != entry.previous_config.get(k)
        )
        return f"- {entry.domain}: {name} ({', '.join(changed) or 'key'})"
    if entry.reason and entry.status in (INVALID, CONFLICT, DUPLICATE):
        reason = entry.reason if len(entry.reason) < 80 else entry.reason[:77] + "..."
        return f"- {entry.domain}: {name} – {reason}"
    return f"- {entry.domain}: {name}"


def preview_markdown(plan: ImportPlan) -> str:
    """Details of the plan for the confirm step (counts are separate placeholders)."""
    sections = [
        (NEW, "➕"),
        (CHANGED, "✏️"),
        (REMOVED, "🗑️"),
        (KEPT, "📌"),
        (CONFLICT, "⚠️"),
        (INVALID, "⛔"),
        (DUPLICATE, "♊"),
    ]
    lines: list[str] = []
    for status, icon in sections:
        entries = plan.by_status(status)
        if not entries:
            continue
        lines.append(f"**{icon} {status}** ({len(entries)})")
        lines.extend(_entry_line(e) for e in entries[:PREVIEW_LIMIT])
        if len(entries) > PREVIEW_LIMIT:
            lines.append(f"- … +{len(entries) - PREVIEW_LIMIT}")
        lines.append("")
    if plan.unmapped:
        lines.append(f"**❔ unmapped** ({len(plan.unmapped)})")
        lines.extend(f"- {u['address']} {u['name']}" for u in plan.unmapped[:PREVIEW_LIMIT])
    return "\n".join(lines) or "–"


def _options_schema(options: dict[str, Any]) -> vol.Schema:
    return vol.Schema(
        {
            vol.Required(CONF_DOMAINS, default=options[CONF_DOMAINS]): selector.SelectSelector(
                selector.SelectSelectorConfig(options=list(DOMAINS), multiple=True, translation_key=CONF_DOMAINS)
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


class _ImportSteps:
    """Steps shared by the config flow and the options flow."""

    hass: Any
    _importer: Importer
    _prepared: Prepared | None = None
    _plan: ImportPlan | None = None
    _source: str = SOURCE_UPLOAD
    _options: dict[str, Any]

    async def _async_importer(self) -> Importer:
        raise NotImplementedError

    async def _async_finish(self, summary: dict[str, Any]) -> ConfigFlowResult:
        raise NotImplementedError

    async def _async_source_menu(self) -> ConfigFlowResult:
        menu = [SOURCE_UPLOAD]
        if await async_has_knx_project(self.hass):
            menu.append(SOURCE_KNX_PROJECT)
        if len(menu) == 1:
            return await self.async_step_upload()
        return self.async_show_menu(step_id="user", menu_options=menu)

    async def async_step_upload(self, user_input: dict[str, Any] | None = None) -> ConfigFlowResult:
        errors: dict[str, str] = {}
        placeholders = {"error": ""}
        if user_input is not None:
            try:
                self._prepared = await async_prepare_upload(
                    self.hass, user_input[CONF_FILE], user_input.get(CONF_PASSWORD)
                )
            except KnxImportError as err:
                errors["base"] = err.key
                if detail := err.placeholders.get("error"):
                    placeholders["error"] = f"\n\n`{detail}`"
            else:
                self._source = SOURCE_UPLOAD
                return await self.async_step_options()
        return self.async_show_form(
            step_id="upload", data_schema=UPLOAD_SCHEMA, errors=errors, description_placeholders=placeholders
        )

    async def async_step_knx_project(self, user_input: dict[str, Any] | None = None) -> ConfigFlowResult:
        try:
            self._prepared = await async_prepare_knx_project(self.hass)
        except KnxImportError as err:
            return self.async_abort(reason=err.key)
        self._source = SOURCE_KNX_PROJECT
        return await self.async_step_options()

    async def async_step_options(self, user_input: dict[str, Any] | None = None) -> ConfigFlowResult:
        if user_input is not None:
            self._options = {**self._options, **user_input}
            importer = await self._async_importer()
            self._plan = await importer.async_plan(self._prepared, self._options)
            return await self.async_step_confirm()
        return self.async_show_form(step_id="options", data_schema=_options_schema(self._options))

    async def async_step_confirm(self, user_input: dict[str, Any] | None = None) -> ConfigFlowResult:
        plan = self._plan
        if user_input is not None:
            importer = await self._async_importer()
            summary = await importer.async_apply(self._prepared, plan, self._options, self._source)
            return await self._async_finish(summary)
        counts = plan.summary()
        return self.async_show_form(
            step_id="confirm",
            description_placeholders={
                "project": plan.project or "-",
                **{k: str(v) for k, v in counts.items()},
                "details": preview_markdown(plan),
            },
        )


class KnxProjectSyncConfigFlow(_ImportSteps, ConfigFlow, domain=DOMAIN):
    """First import."""

    VERSION = 1

    def __init__(self) -> None:
        self._options = default_options()
        self._importer_instance: Importer | None = None
        self._legacy: dict[str, Any] | None = None

    async def _async_importer(self) -> Importer:
        if self._importer_instance is None:
            self._importer_instance = Importer(self.hass)
            await self._importer_instance.async_load()
        return self._importer_instance

    async def async_step_user(self, user_input: dict[str, Any] | None = None) -> ConfigFlowResult:
        if not self.hass.config_entries.async_entries(KNX_DOMAIN):
            return self.async_abort(reason="knx_not_configured")
        if self._legacy is None:
            self._legacy = await async_find_legacy(self.hass) or {}
        if self._legacy:
            return await self.async_step_legacy()
        return await self._async_source_menu()

    async def async_step_legacy(self, user_input: dict[str, Any] | None = None) -> ConfigFlowResult:
        """Former installation found: take over its state instead of importing anew."""
        if user_input is None:
            return self.async_show_form(step_id="legacy")
        options = await async_take_over(self.hass, self._legacy)
        return self.async_create_entry(title=self._legacy["title"] or "KNX", data={}, options=options)

    async def _async_finish(self, summary: dict[str, Any]) -> ConfigFlowResult:
        return self.async_create_entry(title=self._plan.project or "KNX", data={}, options=self._options)

    @staticmethod
    @callback
    def async_get_options_flow(config_entry: ConfigEntry) -> OptionsFlow:
        return KnxProjectSyncOptionsFlow()


class KnxProjectSyncOptionsFlow(_ImportSteps, OptionsFlow):
    """Re-import: new project file, project from the KNX panel or changed settings."""

    async def _async_importer(self) -> Importer:
        return self.config_entry.runtime_data

    async def async_step_init(self, user_input: dict[str, Any] | None = None) -> ConfigFlowResult:
        self._options = {**default_options(), **self.config_entry.options}
        menu = [SOURCE_UPLOAD]
        if await async_has_knx_project(self.hass):
            menu.append(SOURCE_KNX_PROJECT)
        if (await self._async_importer()).stored_prepared():
            menu.append("settings")
        return self.async_show_menu(step_id="init", menu_options=menu)

    async def async_step_settings(self, user_input: dict[str, Any] | None = None) -> ConfigFlowResult:
        importer = await self._async_importer()
        self._prepared = importer.stored_prepared()
        self._source = importer.data.get("last_import", {}).get("source", SOURCE_UPLOAD)
        return await self.async_step_options()

    async def _async_finish(self, summary: dict[str, Any]) -> ConfigFlowResult:
        return self.async_create_entry(data=self._options)
