"""Websocket API of the panel: choose, rename, retype, load a new project version."""

from __future__ import annotations

from homeassistant.components.persistent_notification import _async_get_or_create_notifications
from homeassistant.core import HomeAssistant
from test_import_flow import PACKAGE, _first_import
import yaml

from custom_components.knx_project_sync.const import DOMAIN
from helpers import file_id


def _package(config_dir) -> dict:
    return yaml.safe_load((config_dir / PACKAGE).read_text(encoding="utf-8"))["knx"]


def _rows(result: dict) -> dict[str, dict]:
    return {row["key"]: row for row in result["entities"]}


async def test_panel(hass: HomeAssistant, config_dir, knx_reloads, upload, hass_ws_client) -> None:
    await _first_import(hass)
    assert "knx-project-sync" in hass.data["frontend_panels"]
    client = await hass_ws_client(hass)

    await client.send_json_auto_id({"type": f"{DOMAIN}/plan"})
    result = (await client.receive_json())["result"]
    assert result["project"] == "Musterhaus"
    assert not result["has_changes"]
    rows = _rows(result)
    assert rows["light:GA-3"]["status"] == "unchanged"
    assert rows["light:GA-3"]["domains"] == ["light"]
    # hand written switch: conflict, but could be a light
    assert rows["switch:GA-1"]["status"] == "conflict"
    assert rows["switch:GA-1"]["domains"] == ["switch", "light"]
    assert rows["switch:GA-1"]["suggest_light"]

    selection = {"light:GA-3": {"enabled": False}, "sensor:GA-12": {"name": "Temperatur WZ"}}
    await client.send_json_auto_id({"type": f"{DOMAIN}/plan", "selection": selection})
    result = (await client.receive_json())["result"]
    assert result["has_changes"]
    assert _rows(result)["light:GA-3"]["status"] == "deselected"
    assert _rows(result)["sensor:GA-12"]["status"] == "changed"
    # a retyped switch stays a conflict with the own YAML switch on the same GA
    await client.send_json_auto_id({"type": f"{DOMAIN}/plan", "selection": {"switch:GA-1": {"domain": "light"}}})
    assert _rows((await client.receive_json())["result"])["switch:GA-1"]["status"] == "conflict"

    await client.send_json_auto_id({"type": f"{DOMAIN}/apply", "selection": selection})
    summary = (await client.receive_json())["result"]
    assert summary["deselected"] == 1
    knx = _package(config_dir)
    assert "light" not in knx
    assert knx["sensor"][0]["name"] == "Temperatur WZ"
    assert len(knx_reloads) == 2

    # new project version: the CO2 sensor is offered, not added
    await client.send_json_auto_id(
        {"type": f"{DOMAIN}/load_project", "source": "upload", "file_id": file_id("musterhaus_v2")}
    )
    assert (await client.receive_json())["success"]
    await client.send_json_auto_id({"type": f"{DOMAIN}/plan"})
    result = (await client.receive_json())["result"]
    assert result["staged"]
    assert result["stored_selection"] == selection
    rows = _rows(result)
    assert rows["sensor:GA-19"]["status"] == "pending"
    assert rows["light:GA-3"]["status"] == "deselected"
    assert rows["time:GA-16"]["status"] == "removed"

    await client.send_json_auto_id(
        {"type": f"{DOMAIN}/apply", "selection": {**selection, "sensor:GA-19": {"enabled": True}}}
    )
    assert (await client.receive_json())["result"]["new"] == 1
    knx = _package(config_dir)
    assert "Wohnzimmer CO2" in [s["name"] for s in knx["sensor"]]
    assert "light" not in knx
    assert "knx_project_sync_new_entities" not in _async_get_or_create_notifications(hass)

    await client.send_json_auto_id({"type": f"{DOMAIN}/plan"})
    assert not (await client.receive_json())["result"]["staged"]


async def test_load_errors(hass: HomeAssistant, config_dir, knx_reloads, upload, hass_ws_client) -> None:
    await _first_import(hass)
    client = await hass_ws_client(hass)
    await client.send_json_auto_id(
        {"type": f"{DOMAIN}/load_project", "source": "upload", "file_id": file_id("musterhaus_protected")}
    )
    response = await client.receive_json()
    assert response["error"]["code"] == "invalid_password"
    await client.send_json_auto_id({"type": f"{DOMAIN}/load_project", "source": "knx_project"})
    assert (await client.receive_json())["error"]["code"] == "no_knx_project"


async def test_not_set_up(hass: HomeAssistant, config_dir, knx_reloads, hass_ws_client) -> None:
    from homeassistant.setup import async_setup_component

    assert await async_setup_component(hass, DOMAIN, {})
    client = await hass_ws_client(hass)
    await client.send_json_auto_id({"type": f"{DOMAIN}/plan"})
    assert (await client.receive_json())["error"]["code"] == "not_set_up"


async def test_unload_removes_panel(hass: HomeAssistant, config_dir, knx_reloads, upload) -> None:
    await _first_import(hass)
    entry = hass.config_entries.async_entries(DOMAIN)[0]
    assert await hass.config_entries.async_unload(entry.entry_id)
    assert "knx-project-sync" not in hass.data["frontend_panels"]
    assert await hass.config_entries.async_setup(entry.entry_id)
    assert "knx-project-sync" in hass.data["frontend_panels"]
