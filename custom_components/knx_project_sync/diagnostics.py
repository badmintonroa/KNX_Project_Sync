"""Diagnostics: options, last import and the stored manifest (no secrets stored)."""

from __future__ import annotations

from typing import Any

from homeassistant.core import HomeAssistant

from . import KnxProjectSyncConfigEntry


async def async_get_config_entry_diagnostics(hass: HomeAssistant, entry: KnxProjectSyncConfigEntry) -> dict[str, Any]:
    importer = entry.runtime_data
    return {
        "options": dict(entry.options),
        "last_import": importer.data.get("last_import"),
        "applied": importer.applied,
        "manifest": importer.manifest,
    }
