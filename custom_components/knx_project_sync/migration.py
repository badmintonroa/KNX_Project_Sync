"""Take over an installation of the former name "KNX2HOME Importer" (knx2home_importer, development builds).

The imported entities belong to the KNX integration and are identified by their group
addresses, so they survive the rename as long as their package file is not loaded twice.
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers import issue_registry as ir
from homeassistant.helpers.storage import Store

from .const import (
    CONF_PACKAGE_PATH,
    DEFAULT_PACKAGE_PATH,
    DOMAIN,
    ISSUE_LEGACY_ENTRY,
    LEGACY_DOMAIN,
    LEGACY_PACKAGE_PATH,
)
from .importer import STORAGE_VERSION, default_options


def _legacy_store(hass: HomeAssistant) -> Store[dict]:
    return Store[dict](hass, STORAGE_VERSION, LEGACY_DOMAIN)


def _legacy_entry(hass: HomeAssistant) -> ConfigEntry | None:
    entries = hass.config_entries.async_entries(LEGACY_DOMAIN)
    return entries[0] if entries else None


async def async_find_legacy(hass: HomeAssistant) -> dict[str, Any] | None:
    """State of a former installation, or None."""
    entry = _legacy_entry(hass)
    data = await _legacy_store(hass).async_load()
    if entry is None and not data:
        return None
    return {"title": entry.title if entry else None, "options": dict(entry.options) if entry else {}, "data": data}


async def async_take_over(hass: HomeAssistant, legacy: dict[str, Any]) -> dict[str, Any]:
    """Copy the import state, move the package file and return the options for the new entry."""
    options = {**default_options(), **legacy["options"]}
    old_package = options.get(CONF_PACKAGE_PATH) or LEGACY_PACKAGE_PATH
    if old_package == LEGACY_PACKAGE_PATH:
        options[CONF_PACKAGE_PATH] = DEFAULT_PACKAGE_PATH
        src, dst = Path(hass.config.path(old_package)), Path(hass.config.path(DEFAULT_PACKAGE_PATH))

        def move() -> None:
            if src.exists() and not dst.exists():
                os.replace(src, dst)

        await hass.async_add_executor_job(move)

    if legacy["data"]:
        await Store[dict](hass, STORAGE_VERSION, DOMAIN).async_save(legacy["data"])

    if (entry := _legacy_entry(hass)) is not None:
        # Removing the old entry deletes its package file: point it at the old,
        # now unused path so that the file taken over here stays.
        hass.config_entries.async_update_entry(entry, options={**entry.options, CONF_PACKAGE_PATH: LEGACY_PACKAGE_PATH})
    return options


@callback
def async_update_legacy_issue(hass: HomeAssistant) -> None:
    """Ask to delete the old entry while it exists."""
    if (entry := _legacy_entry(hass)) is None:
        ir.async_delete_issue(hass, DOMAIN, ISSUE_LEGACY_ENTRY)
        return
    ir.async_create_issue(
        hass,
        DOMAIN,
        ISSUE_LEGACY_ENTRY,
        is_fixable=False,
        severity=ir.IssueSeverity.WARNING,
        translation_key=ISSUE_LEGACY_ENTRY,
        translation_placeholders={"title": entry.title},
    )
