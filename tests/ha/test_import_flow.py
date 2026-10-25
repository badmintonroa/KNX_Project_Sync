"""Setup and options flow (only choose the source), apply, re-import with registry migration."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from homeassistant import config_entries
from homeassistant.components.persistent_notification import _async_get_or_create_notifications
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType
from homeassistant.helpers import entity_registry as er, issue_registry as ir
import yaml

from custom_components.knx_project_sync.const import DOMAIN
from custom_components.knx_project_sync.importer import default_options
from helpers import file_id

PACKAGE = "packages/knx_project_sync.yaml"
DOMAINS = ["switch", "light", "sensor", "time", "date", "cover", "scene"]


async def _setup(hass: HomeAssistant, fixture: str = "musterhaus_v1") -> dict:
    """Setup flow: upload the project; nothing is created yet."""
    result = await hass.config_entries.flow.async_init(DOMAIN, context={"source": config_entries.SOURCE_USER})
    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "upload"
    result = await hass.config_entries.flow.async_configure(result["flow_id"], {"file": file_id(fixture)})
    assert result["type"] is FlowResultType.CREATE_ENTRY
    await hass.async_block_till_done()
    return result


async def _apply(hass: HomeAssistant, selection: dict | None = None, **options: Any) -> dict:
    """What the panel's "Apply" does."""
    entry = hass.config_entries.async_entries(DOMAIN)[0]
    if options:
        hass.config_entries.async_update_entry(entry, options={**entry.options, **options})
    importer = entry.runtime_data
    prepared, source = importer.staged or (importer.stored_prepared(), importer.source)
    opts = {**default_options(), **entry.options}
    plan = await importer.async_plan(prepared, opts, selection)
    summary = await importer.async_apply(prepared, plan, opts, source, selection=selection)
    await hass.async_block_till_done()
    return summary


async def _first_import(hass: HomeAssistant, fixture: str = "musterhaus_v1", **options: Any) -> dict:
    await _setup(hass, fixture)
    return await _apply(hass, domains=options.get("domains", DOMAINS), removed=options.get("removed", "delete"))


def _package(config_dir: Path) -> dict:
    return yaml.safe_load((config_dir / PACKAGE).read_text(encoding="utf-8"))["knx"]


async def _options_upload(hass: HomeAssistant, fixture: str) -> dict:
    entry = hass.config_entries.async_entries(DOMAIN)[0]
    result = await hass.config_entries.options.async_init(entry.entry_id)
    assert result["type"] is FlowResultType.MENU
    result = await hass.config_entries.options.async_configure(result["flow_id"], {"next_step_id": "upload"})
    result = await hass.config_entries.options.async_configure(result["flow_id"], {"file": file_id(fixture)})
    assert result["type"] is FlowResultType.CREATE_ENTRY
    return result


async def test_knx_required(hass: HomeAssistant, config_dir) -> None:
    result = await hass.config_entries.flow.async_init(DOMAIN, context={"source": config_entries.SOURCE_USER})
    assert result["type"] is FlowResultType.ABORT
    assert result["reason"] == "knx_not_configured"


async def test_setup_only_reads_the_project(hass: HomeAssistant, config_dir, knx_reloads, upload) -> None:
    result = await _setup(hass)
    assert result["title"] == "Musterhaus"
    assert result["description_placeholders"]["entities"] == "8"
    # the success dialog links straight to the panel
    assert result["description_placeholders"]["panel"] == "/knx-project-sync"
    assert not (config_dir / PACKAGE).exists()
    assert not knx_reloads
    assert "knx_project_sync_project_loaded" in _async_get_or_create_notifications(hass)
    entry = hass.config_entries.async_entries(DOMAIN)[0]
    assert entry.runtime_data.manifest["project"]["name"] == "Musterhaus"
    assert entry.runtime_data.source == "upload"
    assert entry.runtime_data.applied == {}


async def test_first_import(hass: HomeAssistant, config_dir, knx_reloads, upload) -> None:
    summary = await _first_import(hass)
    # switch 1/0/1 is already in the hand written knx: YAML
    assert summary["conflict"] == 1
    assert summary["new"] == 6

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
    assert not ir.async_get(hass).async_get_issue(DOMAIN, "package_not_loaded")
    assert "knx_project_sync_project_loaded" not in _async_get_or_create_notifications(hass)

    state = hass.states.get("sensor.knx_project_sync_last_import")
    assert state is not None
    assert state.attributes["project"] == "Musterhaus"
    assert state.attributes["new"] == 6


async def test_reimport_keeps_entities(hass: HomeAssistant, config_dir, knx_reloads, upload) -> None:
    await _first_import(hass)

    # what the KNX integration registered for the YAML entities of v1
    registry = er.async_get(hass)
    temperature = registry.async_get_or_create("sensor", "knx", "3/0/1", suggested_object_id="wz_temperatur")
    clock = registry.async_get_or_create("time", "knx", "5/0/1")
    light = registry.async_get_or_create("light", "knx", "1/1/1")

    # options flow only loads the new version, the panel applies it
    result = await _options_upload(hass, "musterhaus_v2")
    assert result["description_placeholders"]["project"] == "Musterhaus"
    assert len(knx_reloads) == 1
    summary = await _apply(hass)
    assert summary["new"] == 0
    assert summary["pending"] == 1  # CO2 sensor: offered in the panel, not added
    assert summary["changed"] == 1  # temperature re-addressed
    assert summary["removed"] == 2  # time and date sender removed

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
    await _options_upload(hass, "musterhaus_v2")
    assert (await _apply(hass))["kept"] == 2
    assert _package(config_dir)["time"][0]["address"] == "5/0/1"


async def test_settings_only_save(hass: HomeAssistant, config_dir, knx_reloads, upload) -> None:
    await _first_import(hass)
    entry = hass.config_entries.async_entries(DOMAIN)[0]
    result = await hass.config_entries.options.async_init(entry.entry_id)
    result = await hass.config_entries.options.async_configure(result["flow_id"], {"next_step_id": "settings"})
    assert result["step_id"] == "settings"
    result = await hass.config_entries.options.async_configure(
        result["flow_id"],
        {"domains": ["light"], "removed": "delete", "assign_areas": False, "package_path": PACKAGE},
    )
    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert entry.options["domains"] == ["light"]
    assert len(knx_reloads) == 1  # nothing applied yet
    assert (await _apply(hass))["removed"] == 5
    assert list(_package(config_dir)) == ["light"]


async def test_invalid_password(hass: HomeAssistant, config_dir, knx_reloads, upload) -> None:
    result = await hass.config_entries.flow.async_init(DOMAIN, context={"source": config_entries.SOURCE_USER})
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], {"file": file_id("musterhaus_protected")}
    )
    assert result["errors"] == {"base": "invalid_password"}
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], {"file": file_id("musterhaus_protected"), "password": "geheim"}
    )
    assert result["type"] is FlowResultType.CREATE_ENTRY


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


async def test_migrate_options_adds_text(hass: HomeAssistant, config_dir, knx_reloads) -> None:
    from pytest_homeassistant_custom_component.common import MockConfigEntry

    entry = MockConfigEntry(
        domain=DOMAIN, version=1, minor_version=1, options={**default_options(), "domains": ["sensor", "light"]}
    )
    entry.add_to_hass(hass)
    assert await hass.config_entries.async_setup(entry.entry_id)
    assert entry.minor_version == 2
    assert entry.options["domains"] == ["sensor", "light", "text"]
