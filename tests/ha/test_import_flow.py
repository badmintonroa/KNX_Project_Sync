"""Config flow, package file, re-import with registry migration (steps 2, 4, 5)."""

from __future__ import annotations

from pathlib import Path

from homeassistant import config_entries
from homeassistant.components.persistent_notification import _async_get_or_create_notifications
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType
from homeassistant.helpers import entity_registry as er, issue_registry as ir
import yaml

from custom_components.knx_project_sync.const import DOMAIN
from helpers import file_id

PACKAGE = "packages/knx_project_sync.yaml"


async def _first_import(hass: HomeAssistant, fixture: str = "musterhaus_v1", **options):
    result = await hass.config_entries.flow.async_init(DOMAIN, context={"source": config_entries.SOURCE_USER})
    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "upload"
    result = await hass.config_entries.flow.async_configure(result["flow_id"], {"file": file_id(fixture)})
    assert result["step_id"] == "options"
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {
            "domains": options.get("domains", ["switch", "light", "sensor", "time", "date", "cover", "scene"]),
            "removed": options.get("removed", "delete"),
            "assign_areas": False,
            "package_path": PACKAGE,
        },
    )
    assert result["step_id"] == "confirm"
    confirm = result
    result = await hass.config_entries.flow.async_configure(result["flow_id"], {})
    assert result["type"] is FlowResultType.CREATE_ENTRY
    await hass.async_block_till_done()
    return confirm, result


def _package(config_dir: Path) -> dict:
    return yaml.safe_load((config_dir / PACKAGE).read_text(encoding="utf-8"))["knx"]


async def test_knx_required(hass: HomeAssistant, config_dir) -> None:
    result = await hass.config_entries.flow.async_init(DOMAIN, context={"source": config_entries.SOURCE_USER})
    assert result["type"] is FlowResultType.ABORT
    assert result["reason"] == "knx_not_configured"


async def test_first_import(hass: HomeAssistant, config_dir, knx_reloads, upload) -> None:
    confirm, result = await _first_import(hass)
    placeholders = confirm["description_placeholders"]
    assert placeholders["project"] == "Musterhaus"
    # switch 1/0/1 is already in the hand written knx: YAML
    assert placeholders["conflict"] == "1"
    assert placeholders["new"] == "6"
    assert "Wohnzimmer Licht Schalten" in placeholders["details"]

    knx = _package(config_dir)
    assert "switch" not in knx
    assert knx["light"] == [
        {
            "name": "Esszimmer Licht",
            "address": "1/1/1",
            "state_address": "1/1/2",
            "brightness_address": "1/1/3",
            "brightness_state_address": "1/1/4",
        }
    ]
    assert [s["state_address"] for s in knx["sensor"]] == ["3/0/1", "3/0/2"]
    # the scene GA has no number in its name -> invalid for HA, not written
    assert "scene" not in knx
    assert len(knx_reloads) == 1
    assert result["title"] == "Musterhaus"
    assert not ir.async_get(hass).async_get_issue(DOMAIN, "package_not_loaded")

    state = hass.states.get("sensor.knx_project_sync_last_import")
    assert state is not None
    assert state.attributes["project"] == "Musterhaus"
    assert state.attributes["new"] == 6


async def test_reimport_keeps_entities(hass: HomeAssistant, config_dir, knx_reloads, upload) -> None:
    await _first_import(hass)
    entry = hass.config_entries.async_entries(DOMAIN)[0]

    # what the KNX integration registered for the YAML entities of v1
    registry = er.async_get(hass)
    temperature = registry.async_get_or_create("sensor", "knx", "3/0/1", suggested_object_id="wz_temperatur")
    clock = registry.async_get_or_create("time", "knx", "5/0/1")
    light = registry.async_get_or_create("light", "knx", "1/1/1")

    result = await hass.config_entries.options.async_init(entry.entry_id)
    assert result["type"] is FlowResultType.MENU
    result = await hass.config_entries.options.async_configure(result["flow_id"], {"next_step_id": "upload"})
    result = await hass.config_entries.options.async_configure(result["flow_id"], {"file": file_id("musterhaus_v2")})
    assert result["step_id"] == "options"
    result = await hass.config_entries.options.async_configure(result["flow_id"], {})
    assert result["step_id"] == "confirm"
    placeholders = result["description_placeholders"]
    assert placeholders["new"] == "0"
    assert placeholders["pending"] == "1"  # CO2 sensor: offered in the panel, not added
    assert placeholders["changed"] == "1"  # temperature re-addressed
    assert placeholders["removed"] == "2"  # time and date sender removed
    result = await hass.config_entries.options.async_configure(result["flow_id"], {})
    assert result["type"] is FlowResultType.CREATE_ENTRY
    await hass.async_block_till_done()

    # same entity, new unique_id -> entity_id and history survive the re-addressing
    migrated = registry.async_get(temperature.entity_id)
    assert migrated.unique_id == "3/1/1"
    assert registry.async_get(clock.entity_id) is None
    assert registry.async_get(light.entity_id) is not None

    knx = _package(config_dir)
    assert [s["state_address"] for s in knx["sensor"]] == ["3/0/2", "3/1/1"]
    assert "time" not in knx
    assert len(knx_reloads) == 2

    notification = _async_get_or_create_notifications(hass)["knx_project_sync_new_entities"]
    assert "Wohnzimmer CO2" in notification["message"]


async def test_keep_removed(hass: HomeAssistant, config_dir, knx_reloads, upload) -> None:
    await _first_import(hass, removed="keep")
    entry = hass.config_entries.async_entries(DOMAIN)[0]
    result = await hass.config_entries.options.async_init(entry.entry_id)
    result = await hass.config_entries.options.async_configure(result["flow_id"], {"next_step_id": "upload"})
    result = await hass.config_entries.options.async_configure(result["flow_id"], {"file": file_id("musterhaus_v2")})
    result = await hass.config_entries.options.async_configure(result["flow_id"], {})
    assert result["description_placeholders"]["kept"] == "2"
    await hass.config_entries.options.async_configure(result["flow_id"], {})
    assert _package(config_dir)["time"][0]["address"] == "5/0/1"


async def test_settings_only(hass: HomeAssistant, config_dir, knx_reloads, upload) -> None:
    await _first_import(hass)
    entry = hass.config_entries.async_entries(DOMAIN)[0]
    result = await hass.config_entries.options.async_init(entry.entry_id)
    result = await hass.config_entries.options.async_configure(result["flow_id"], {"next_step_id": "settings"})
    result = await hass.config_entries.options.async_configure(result["flow_id"], {"domains": ["light"]})
    assert result["description_placeholders"]["removed"] == "5"
    await hass.config_entries.options.async_configure(result["flow_id"], {})
    assert list(_package(config_dir)) == ["light"]
    assert entry.options["domains"] == ["light"]


async def test_invalid_password(hass: HomeAssistant, config_dir, knx_reloads, upload) -> None:
    result = await hass.config_entries.flow.async_init(DOMAIN, context={"source": config_entries.SOURCE_USER})
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], {"file": file_id("musterhaus_protected")}
    )
    assert result["errors"] == {"base": "invalid_password"}
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], {"file": file_id("musterhaus_protected"), "password": "geheim"}
    )
    assert result["step_id"] == "options"


async def test_package_not_loaded(hass: HomeAssistant, config_dir, knx_reloads, upload) -> None:
    (config_dir / "configuration.yaml").write_text("default_config:\n", encoding="utf-8")
    await _first_import(hass)
    issue = ir.async_get(hass).async_get_issue(DOMAIN, "package_not_loaded")
    assert issue is not None


async def test_remove_entry_deletes_package(hass: HomeAssistant, config_dir, knx_reloads, upload) -> None:
    await _first_import(hass)
    entry = hass.config_entries.async_entries(DOMAIN)[0]
    await hass.config_entries.async_remove(entry.entry_id)
    await hass.async_block_till_done()
    assert not (config_dir / PACKAGE).exists()
    assert len(knx_reloads) == 2
