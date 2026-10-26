"""Websocket API of the panel: choose, rename, retype, load a new project version."""

from __future__ import annotations

from pathlib import Path

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


async def test_adopt_own_yaml(hass: HomeAssistant, config_dir, knx_reloads, upload, hass_ws_client) -> None:
    from homeassistant.helpers import entity_registry as er

    await _first_import(hass)
    own = er.async_get(hass).async_get_or_create("switch", "knx", "1/0/1", suggested_object_id="handgeschrieben")
    client = await hass_ws_client(hass)
    await client.send_json_auto_id({"type": f"{DOMAIN}/plan"})
    row = _rows((await client.receive_json())["result"])["switch:GA-1"]
    assert row["conflict_with"] == {
        "domain": "switch",
        "name": "Handgeschrieben Wohnzimmer",
        "file": "configuration.yaml",
        "line": 5,
        "adoptable": True,
        "kind": "unique_id",
        "address": None,
    }

    await client.send_json_auto_id({"type": f"{DOMAIN}/apply", "selection": {"switch:GA-1": {"adopt": True}}})
    response = await client.receive_json()
    assert response["success"], response
    summary = response["result"]
    assert summary["adopted"] == 1
    configuration = (config_dir / "configuration.yaml").read_text(encoding="utf-8")
    assert "Handgeschrieben" not in configuration
    assert "  switch: []\n" in configuration
    assert len(summary["backups"]) == 1
    assert "Handgeschrieben" in Path(summary["backups"][0]).read_text(encoding="utf-8")
    assert {"name": "Handgeschrieben Wohnzimmer", "address": "1/0/1", "state_address": "1/0/2"} in _package(config_dir)[
        "switch"
    ]
    assert er.async_get(hass).async_get(own.entity_id) is not None

    await client.send_json_auto_id({"type": f"{DOMAIN}/plan"})
    result = (await client.receive_json())["result"]
    row = _rows(result)["switch:GA-1"]
    assert (row["status"], row["own_config"], row["conflict_with"]) == ("unchanged", True, None)
    assert "adopt" not in result["stored_selection"]["switch:GA-1"]


async def test_adopt_refused_for_flow_style(
    hass: HomeAssistant, config_dir, knx_reloads, upload, hass_ws_client
) -> None:
    await _first_import(hass)
    configuration = config_dir / "configuration.yaml"
    text = configuration.read_text(encoding="utf-8")
    flow = 'knx:\n  switch: [{name: Kurz, address: "1/0/1"}]\n'
    configuration.write_text(text[: text.index("knx:")] + flow, encoding="utf-8")
    package = (config_dir / PACKAGE).read_text(encoding="utf-8")

    client = await hass_ws_client(hass)
    await client.send_json_auto_id({"type": f"{DOMAIN}/apply", "selection": {"switch:GA-1": {"adopt": True}}})
    response = await client.receive_json()
    assert response["error"]["code"] == "adopt_failed"
    assert configuration.read_text(encoding="utf-8").endswith(flow)
    assert (config_dir / PACKAGE).read_text(encoding="utf-8") == package


async def test_correct_addresses(hass: HomeAssistant, config_dir, knx_reloads, upload, hass_ws_client) -> None:
    from homeassistant.helpers import entity_registry as er

    await _first_import(hass)
    temperature = er.async_get(hass).async_get_or_create("sensor", "knx", "3/0/1", suggested_object_id="temp")
    client = await hass_ws_client(hass)
    selection = {"sensor:GA-12": {"addresses": {"state_address": "3/0/9"}}}
    await client.send_json_auto_id({"type": f"{DOMAIN}/plan", "selection": selection})
    row = _rows((await client.receive_json())["result"])["sensor:GA-12"]
    assert row["status"] == "changed"
    assert row["addresses"] == [{"field": "state_address", "address": "3/0/9"}]
    assert row["project_addresses"] == {"state_address": "3/0/1"}
    assert row["address_fields"] == ["state_address"]

    # a typo is rejected by the KNX schema and not written
    await client.send_json_auto_id(
        {"type": f"{DOMAIN}/plan", "selection": {"sensor:GA-12": {"addresses": {"state_address": "3/0/x"}}}}
    )
    assert _rows((await client.receive_json())["result"])["sensor:GA-12"]["status"] == "invalid"

    await client.send_json_auto_id({"type": f"{DOMAIN}/apply", "selection": selection})
    assert (await client.receive_json())["success"]
    assert [s["state_address"] for s in _package(config_dir)["sensor"]] == ["3/0/9", "3/0/2"]
    assert er.async_get(hass).async_get(temperature.entity_id).unique_id == "3/0/9"


async def test_panel_after_setup(hass: HomeAssistant, config_dir, knx_reloads, upload, hass_ws_client) -> None:
    """Setup only reads the project: the panel shows everything preselected, nothing exists yet."""
    from test_import_flow import _setup

    await _setup(hass)
    client = await hass_ws_client(hass)
    await client.send_json_auto_id({"type": f"{DOMAIN}/plan"})
    result = (await client.receive_json())["result"]
    assert result["last_import"] is None
    assert result["has_changes"]
    rows = _rows(result)
    assert rows["light:GA-3"]["status"] == "new"
    assert rows["switch:GA-1"]["status"] == "conflict"
    assert not (config_dir / PACKAGE).exists()

    await client.send_json_auto_id({"type": f"{DOMAIN}/apply", "selection": {"sensor:GA-13": {"enabled": False}}})
    assert (await client.receive_json())["result"]["new"] == 5
    assert [s["state_address"] for s in _package(config_dir)["sensor"]] == ["3/0/1"]


async def test_own_climate_on_a_detected_sensor(
    hass: HomeAssistant, config_dir, knx_reloads, upload, hass_ws_client
) -> None:
    """Own YAML climate uses the GA the project detects as a temperature sensor."""
    from test_import_flow import _setup

    configuration = config_dir / "configuration.yaml"
    configuration.write_text(
        configuration.read_text(encoding="utf-8")
        + '  climate:\n    - name: "Wohnzimmer"\n      temperature_address: "3/0/1"\n'
        + '      target_temperature_state_address: "3/0/9"\n',
        encoding="utf-8",
    )
    await _setup(hass)
    client = await hass_ws_client(hass)
    await client.send_json_auto_id({"type": f"{DOMAIN}/plan"})
    row = _rows((await client.receive_json())["result"])["sensor:GA-12"]
    assert (row["status"], row["reason"]) == ("conflict", "ga_in_use")
    assert row["conflict_with"]["kind"] == "address"
    assert row["conflict_with"]["address"] == "3/0/1"
    assert row["conflict_with"]["domain"] == "climate"

    await client.send_json_auto_id({"type": f"{DOMAIN}/apply", "selection": {"sensor:GA-12": {"adopt": True}}})
    response = await client.receive_json()
    assert response["success"], response
    assert response["result"]["adopted"] == 1
    assert "Wohnzimmer" not in configuration.read_text(encoding="utf-8").split("climate:")[1]
    knx = _package(config_dir)
    assert knx["climate"] == [
        {"name": "Wohnzimmer", "temperature_address": "3/0/1", "target_temperature_state_address": "3/0/9"}
    ]
    assert [s["state_address"] for s in knx["sensor"]] == ["3/0/2"]


async def test_fix_packages(hass: HomeAssistant, config_dir, knx_reloads, upload, hass_ws_client) -> None:
    """configuration.yaml without packages: one click adds the line, KNX reloads, no restart."""
    from homeassistant.helpers import issue_registry as ir

    configuration = config_dir / "configuration.yaml"
    configuration.write_text("default_config:\n", encoding="utf-8")
    await _first_import(hass)
    issue = ir.async_get(hass).async_get_issue(DOMAIN, "package_not_loaded")
    assert issue is not None and issue.is_fixable

    client = await hass_ws_client(hass)
    await client.send_json_auto_id({"type": f"{DOMAIN}/plan"})
    assert (await client.receive_json())["result"]["packages"]["status"] == "add"

    await client.send_json_auto_id({"type": f"{DOMAIN}/fix_packages"})
    response = await client.receive_json()
    assert response["success"], response
    assert response["result"]["status"] == "ok"
    assert configuration.read_text(encoding="utf-8") == (
        "default_config:\n\nhomeassistant:\n  packages: !include_dir_named packages\n"
    )
    assert list(config_dir.glob("configuration.yaml.knx_project_sync-*.bak"))
    assert len(knx_reloads) == 2
    assert ir.async_get(hass).async_get_issue(DOMAIN, "package_not_loaded") is None


async def test_repair_flow(hass: HomeAssistant, config_dir, knx_reloads, upload) -> None:
    from custom_components.knx_project_sync.repairs import async_create_fix_flow

    (config_dir / "configuration.yaml").write_text("default_config:\n", encoding="utf-8")
    await _first_import(hass)
    flow = await async_create_fix_flow(hass, "package_not_loaded", None)
    flow.hass = hass
    result = await flow.async_step_init()
    assert result["step_id"] == "confirm"
    assert result["description_placeholders"]["path"] == PACKAGE
    result = await flow.async_step_confirm({})
    assert result["type"] == "create_entry"
    assert "packages: !include_dir_named packages" in (config_dir / "configuration.yaml").read_text(encoding="utf-8")


async def test_remove_takes_the_line_out(hass: HomeAssistant, config_dir, knx_reloads, upload, hass_ws_client) -> None:
    """Removing the integration undoes the one-click fix and drops the generated entities."""
    from homeassistant.helpers import entity_registry as er

    configuration = config_dir / "configuration.yaml"
    configuration.write_text("default_config:\n", encoding="utf-8")
    await _first_import(hass)
    client = await hass_ws_client(hass)
    await client.send_json_auto_id({"type": f"{DOMAIN}/fix_packages"})
    assert (await client.receive_json())["success"]

    entry = hass.config_entries.async_entries(DOMAIN)[0]
    applied = next(iter(entry.runtime_data.applied.values()))
    registry = er.async_get(hass)
    entity = registry.async_get_or_create(applied["domain"], "knx", applied["unique_id"])

    await hass.config_entries.async_remove(entry.entry_id)
    await hass.async_block_till_done()
    assert configuration.read_text(encoding="utf-8") == "default_config:\n"
    assert not (config_dir / "packages").exists()
    assert registry.async_get(entity.entity_id) is None


async def test_remove_keeps_the_line_for_other_packages(
    hass: HomeAssistant, config_dir, knx_reloads, upload, hass_ws_client
) -> None:
    configuration = config_dir / "configuration.yaml"
    configuration.write_text("default_config:\n", encoding="utf-8")
    await _first_import(hass)
    client = await hass_ws_client(hass)
    await client.send_json_auto_id({"type": f"{DOMAIN}/fix_packages"})
    assert (await client.receive_json())["success"]
    (config_dir / "packages" / "eigenes.yaml").write_text("input_boolean:\n  test: {}\n", encoding="utf-8")

    entry = hass.config_entries.async_entries(DOMAIN)[0]
    await hass.config_entries.async_remove(entry.entry_id)
    await hass.async_block_till_done()
    assert "packages: !include_dir_named packages" in configuration.read_text(encoding="utf-8")
