"""Panel "KNX Project Sync": choose, rename and retype the entities of the project.

The panel keeps its changes as a draft and sends the complete selection with every
`plan` (preview) and `apply` call; nothing is stored before `apply`.
"""

from __future__ import annotations

from pathlib import Path
import re
from typing import Any, Final

from homeassistant.components import panel_custom, websocket_api
from homeassistant.components.http import StaticPathConfig
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers import entity_registry as er
import voluptuous as vol

from .const import DOMAIN, KNX_DOMAIN, SOURCE_KNX_PROJECT, SOURCE_UPLOAD
from .importer import (
    PANEL_URL,
    Importer,
    KnxImportError,
    Prepared,
    async_has_knx_project,
    async_prepare_knx_project,
    async_prepare_upload,
    default_options,
)
from .plan import WRITTEN, ImportPlan, domain_choices

STATIC_URL: Final = f"/{DOMAIN}_static"
FRONTEND_DIR: Final = Path(__file__).parent / "frontend"
PANEL_JS: Final = "knx-project-sync-panel.js"
WEBCOMPONENT: Final = "knx-project-sync-panel"
DATA_STATIC: Final = f"{DOMAIN}_static_path"

# names of switches that are probably lamps (offered as "probably a light")
LIGHT_HINT = re.compile(r"licht|lampe|leuchte|beleuchtung|spot|strahler|led|light|lamp", re.IGNORECASE)

SELECTION_SCHEMA = vol.Schema(
    {
        str: vol.Schema(
            {
                vol.Optional("enabled"): vol.Any(bool, None),
                vol.Optional("domain"): vol.Any(str, None),
                vol.Optional("name"): vol.Any(str, None),
            }
        )
    }
)


@callback
def async_register_commands(hass: HomeAssistant) -> None:
    websocket_api.async_register_command(hass, ws_plan)
    websocket_api.async_register_command(hass, ws_load_project)
    websocket_api.async_register_command(hass, ws_discard)
    websocket_api.async_register_command(hass, ws_apply)


async def async_register_panel(hass: HomeAssistant) -> None:
    """Sidebar panel, shown while the config entry is loaded."""
    if not hass.data.get(DATA_STATIC):
        hass.data[DATA_STATIC] = True
        await hass.http.async_register_static_paths(
            [StaticPathConfig(STATIC_URL, str(FRONTEND_DIR), cache_headers=False)]
        )
    version = await hass.async_add_executor_job(_version)
    await panel_custom.async_register_panel(
        hass,
        frontend_url_path=PANEL_URL.lstrip("/"),
        webcomponent_name=WEBCOMPONENT,
        sidebar_title="KNX Project Sync",
        sidebar_icon="mdi:home-import-outline",
        module_url=f"{STATIC_URL}/{PANEL_JS}?v={version}",
        embed_iframe=False,
        require_admin=True,
    )


@callback
def async_unregister_panel(hass: HomeAssistant) -> None:
    from homeassistant.components import frontend

    frontend.async_remove_panel(hass, PANEL_URL.lstrip("/"), warn_if_unknown=False)


def _version() -> str:
    try:
        return str(int((FRONTEND_DIR / PANEL_JS).stat().st_mtime))
    except OSError:
        return "0"


# ---------------------------------------------------------------- helpers


def _entry(hass: HomeAssistant) -> ConfigEntry | None:
    entries = hass.config_entries.async_loaded_entries(DOMAIN)
    return entries[0] if entries else None


def _current(importer: Importer) -> tuple[Prepared | None, str | None]:
    if importer.staged:
        return importer.staged
    return importer.stored_prepared(), importer.data.get("last_import", {}).get("source")


def _serialize(hass: HomeAssistant, prepared: Prepared, plan: ImportPlan, selection: dict) -> list[dict[str, Any]]:
    registry = er.async_get(hass)
    detected = {e["key"]: e for e in prepared.manifest["entities"]}
    rows = []
    for entry in plan.entries:
        source = detected.get(entry.key)
        base_domain = entry.detected_domain or entry.domain
        base_config = source["config"] if source else entry.config
        entity_id = None
        if entry.status in WRITTEN:
            entity_id = registry.async_get_entity_id(entry.domain, KNX_DOMAIN, entry.unique_id)
        elif entry.previous_unique_id and entry.previous_domain:
            entity_id = registry.async_get_entity_id(entry.previous_domain, KNX_DOMAIN, entry.previous_unique_id)
        ets_name = source.get("name") if source else entry.name
        rows.append(
            {
                "key": entry.key,
                "status": entry.status,
                "reason": entry.reason,
                "domain": entry.domain,
                "detected_domain": base_domain,
                "domains": domain_choices(base_domain, base_config) if source else [entry.domain],
                "name": entry.name,
                "ets_name": ets_name,
                "addresses": [
                    {"field": k, "address": v}
                    for k, v in entry.config.items()
                    if isinstance(v, str) and (k == "address" or k.endswith("_address") or k.startswith("address_"))
                ],
                "room": prepared.rooms.get(entry.key),
                "in_project": source is not None,
                "entity_id": entity_id,
                "previous_domain": entry.previous_domain,
                "selection": selection.get(entry.key, {}),
                "suggest_light": base_domain == "switch" and bool(ets_name and LIGHT_HINT.search(ets_name)),
            }
        )
    return rows


async def _async_plan_response(
    hass: HomeAssistant, entry: ConfigEntry, selection: dict | None
) -> tuple[dict[str, Any], tuple[Prepared, ImportPlan, str | None] | None]:
    importer: Importer = entry.runtime_data
    prepared, source = _current(importer)
    selection = importer.selection if selection is None else _clean(selection)
    base: dict[str, Any] = {
        "language": hass.config.language,
        "has_knx_project": await async_has_knx_project(hass),
        "staged": importer.staged is not None,
        "last_import": importer.data.get("last_import"),
        "stored_selection": importer.selection,
        "domains": {**default_options(), **entry.options}["domains"],
    }
    if prepared is None:
        return {**base, "project": None, "entities": [], "unmapped": [], "summary": {}}, None
    options = {**default_options(), **entry.options}
    plan = await importer.async_plan(prepared, options, selection)
    return {
        **base,
        "project": plan.project,
        "entities": _serialize(hass, prepared, plan, selection),
        "unmapped": plan.unmapped,
        "summary": plan.summary(),
        "has_changes": plan.has_changes or importer.staged is not None or selection != importer.selection,
        "removed_unique_ids": len(plan.removed_unique_ids),
    }, (prepared, plan, source)


def _not_set_up(connection: websocket_api.ActiveConnection, msg: dict) -> None:
    connection.send_error(msg["id"], "not_set_up", "KNX Project Sync is not set up")


# ---------------------------------------------------------------- commands


@websocket_api.require_admin
@websocket_api.websocket_command({vol.Required("type"): f"{DOMAIN}/plan", vol.Optional("selection"): SELECTION_SCHEMA})
@websocket_api.async_response
async def ws_plan(hass: HomeAssistant, connection: websocket_api.ActiveConnection, msg: dict) -> None:
    """Entities of the current (or newly loaded) project with their status for a draft selection."""
    if (entry := _entry(hass)) is None:
        _not_set_up(connection, msg)
        return
    response, _ = await _async_plan_response(hass, entry, msg.get("selection"))
    connection.send_result(msg["id"], response)


@websocket_api.require_admin
@websocket_api.websocket_command(
    {
        vol.Required("type"): f"{DOMAIN}/load_project",
        vol.Required("source"): vol.In([SOURCE_UPLOAD, SOURCE_KNX_PROJECT]),
        vol.Optional("file_id"): str,
        vol.Optional("password"): str,
    }
)
@websocket_api.async_response
async def ws_load_project(hass: HomeAssistant, connection: websocket_api.ActiveConnection, msg: dict) -> None:
    """Read a new project version; it is shown in the panel and written on `apply`."""
    if (entry := _entry(hass)) is None:
        _not_set_up(connection, msg)
        return
    try:
        if msg["source"] == SOURCE_KNX_PROJECT:
            prepared = await async_prepare_knx_project(hass)
        elif file_id := msg.get("file_id"):
            prepared = await async_prepare_upload(hass, file_id, msg.get("password"))
        else:
            raise KnxImportError("file_required")
    except KnxImportError as err:
        connection.send_error(msg["id"], err.key, err.placeholders.get("error") or err.key)
        return
    entry.runtime_data.staged = (prepared, msg["source"])
    connection.send_result(msg["id"], {"project": prepared.manifest.get("project", {}).get("name")})


@websocket_api.require_admin
@websocket_api.websocket_command({vol.Required("type"): f"{DOMAIN}/discard"})
@callback
def ws_discard(hass: HomeAssistant, connection: websocket_api.ActiveConnection, msg: dict) -> None:
    """Forget a loaded but not applied project."""
    if (entry := _entry(hass)) is None:
        _not_set_up(connection, msg)
        return
    entry.runtime_data.staged = None
    connection.send_result(msg["id"])


@websocket_api.require_admin
@websocket_api.websocket_command({vol.Required("type"): f"{DOMAIN}/apply", vol.Required("selection"): SELECTION_SCHEMA})
@websocket_api.async_response
async def ws_apply(hass: HomeAssistant, connection: websocket_api.ActiveConnection, msg: dict) -> None:
    """Write the package for the selection (and a loaded project), reload KNX."""
    if (entry := _entry(hass)) is None:
        _not_set_up(connection, msg)
        return
    selection = _clean(msg["selection"])
    _, planned = await _async_plan_response(hass, entry, selection)
    if planned is None:
        connection.send_error(msg["id"], "no_project", "No project imported yet")
        return
    prepared, plan, source = planned
    options = {**default_options(), **entry.options}
    summary = await entry.runtime_data.async_apply(
        prepared, plan, options, source or SOURCE_UPLOAD, selection=selection, notify=False
    )
    connection.send_result(msg["id"], summary)


def _clean(selection: dict[str, dict[str, Any]]) -> dict[str, dict[str, Any]]:
    """Drop empty values so that only real choices are stored."""
    out: dict[str, dict[str, Any]] = {}
    for key, choice in selection.items():
        item = {k: v for k, v in choice.items() if v is not None and v != ""}
        if item:
            out[key] = item
    return out
