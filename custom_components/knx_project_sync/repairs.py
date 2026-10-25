"""Repair "package not loaded": add the packages line to configuration.yaml."""

from __future__ import annotations

from typing import Any

from homeassistant.components.repairs import RepairsFlow
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResult

from .const import DOMAIN, ISSUE_PACKAGE_NOT_LOADED
from .importer import KnxImportError


class PackagesFix(RepairsFlow):
    """One click: configuration.yaml is backed up, changed, checked; then KNX reloads."""

    async def async_step_init(self, user_input: dict[str, Any] | None = None) -> FlowResult:
        return await self.async_step_confirm()

    async def async_step_confirm(self, user_input: dict[str, Any] | None = None) -> FlowResult:
        entries = self.hass.config_entries.async_loaded_entries(DOMAIN)
        if not entries:
            return self.async_abort(reason="not_set_up")
        entry = entries[0]
        if user_input is not None:
            try:
                await entry.runtime_data.async_fix_packages(entry)
            except KnxImportError as err:
                return self.async_abort(
                    reason="packages_manual", description_placeholders={"error": err.placeholders.get("error", "")}
                )
            return self.async_create_entry(data={})
        setup = await entry.runtime_data.async_package_setup(entry.options)
        return self.async_show_form(
            step_id="confirm",
            description_placeholders={"status": setup.status, "path": setup.package_path},
        )


async def async_create_fix_flow(hass: HomeAssistant, issue_id: str, data: dict[str, Any] | None) -> RepairsFlow:
    assert issue_id == ISSUE_PACKAGE_NOT_LOADED
    return PackagesFix()
