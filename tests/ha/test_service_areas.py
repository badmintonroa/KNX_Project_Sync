"""Service, KNX panel project as source, ETS rooms -> areas, diagnostics (steps 5, 6)."""

from __future__ import annotations

import shutil

from homeassistant import config_entries
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ServiceValidationError
from homeassistant.helpers import area_registry as ar, entity_registry as er
import pytest
from pytest_homeassistant_custom_component.components.diagnostics import get_diagnostics_for_config_entry
from xknxproject import XKNXProj
import yaml

from custom_components.knx_project_sync.const import DOMAIN
from helpers import FIXTURES, file_id


def _project_with_rooms() -> dict:
    project = XKNXProj(FIXTURES / "musterhaus_v1.knxproj", language="de-DE").parse()
    room = {
        "type": "Room", "identifier": "P-0A1B-0_BP-2", "name": "Esszimmer", "usage_id": None, "usage_text": "",
        "number": "", "description": "", "project_uid": None, "devices": ["1.1.2"], "spaces": {}, "functions": [],
    }  # fmt: skip
    project["locations"] = {
        "Haus": {**room, "type": "Building", "name": "Haus", "devices": [], "spaces": {"Esszimmer": room}}
    }
    return project


async def _setup_via_knx_project(hass: HomeAssistant, hass_storage, assign_areas: bool):
    hass_storage["knx/knx_project.json"] = {"version": 1, "key": "knx/knx_project.json", "data": _project_with_rooms()}
    result = await hass.config_entries.flow.async_init(DOMAIN, context={"source": config_entries.SOURCE_USER})
    assert result["type"] == "menu"
    result = await hass.config_entries.flow.async_configure(result["flow_id"], {"next_step_id": "knx_project"})
    result = await hass.config_entries.flow.async_configure(result["flow_id"], {"assign_areas": assign_areas})
    # entity the KNX integration creates when the package is loaded
    light = er.async_get(hass).async_get_or_create("light", "knx", "1/1/1")
    result = await hass.config_entries.flow.async_configure(result["flow_id"], {})
    assert result["type"] == "create_entry"
    await hass.async_block_till_done()
    return light


async def test_knx_project_source_and_areas(hass: HomeAssistant, hass_storage, config_dir, knx_reloads) -> None:
    light = await _setup_via_knx_project(hass, hass_storage, assign_areas=True)
    area = ar.async_get(hass).async_get_area_by_name("Esszimmer")
    assert area is not None
    assert er.async_get(hass).async_get(light.entity_id).area_id == area.id


async def test_existing_area_is_not_overwritten(hass: HomeAssistant, hass_storage, config_dir, knx_reloads) -> None:
    registry = er.async_get(hass)
    kitchen = ar.async_get(hass).async_create("Küche")
    light = registry.async_get_or_create("light", "knx", "1/1/1")
    registry.async_update_entity(light.entity_id, area_id=kitchen.id)
    await _setup_via_knx_project(hass, hass_storage, assign_areas=True)
    assert registry.async_get(light.entity_id).area_id == kitchen.id


async def test_service_dry_run_and_import(
    hass: HomeAssistant, hass_storage, config_dir, knx_reloads, hass_client
) -> None:
    await _setup_via_knx_project(hass, hass_storage, assign_areas=False)
    shutil.copy(FIXTURES / "musterhaus_v2.knxproj", config_dir / "projekt.knxproj")

    response = await hass.services.async_call(
        DOMAIN, "import_project", {"file": "projekt.knxproj", "dry_run": True}, blocking=True, return_response=True
    )
    assert response["summary"]["pending"] == 1
    assert {e["key"]: e["status"] for e in response["entities"]}["sensor:GA-12"] == "changed"
    assert len(knx_reloads) == 1

    response = await hass.services.async_call(
        DOMAIN, "import_project", {"file": "projekt.knxproj"}, blocking=True, return_response=True
    )
    assert response["summary"]["removed"] == 2
    assert len(knx_reloads) == 2
    package = yaml.safe_load((config_dir / "packages/knx_project_sync.yaml").read_text(encoding="utf-8"))
    assert [s["state_address"] for s in package["knx"]["sensor"]] == ["3/0/2", "3/1/1"]

    with pytest.raises(ServiceValidationError):
        await hass.services.async_call(DOMAIN, "import_project", {"file": "fehlt.knxproj"}, blocking=True)

    entry = hass.config_entries.async_entries(DOMAIN)[0]
    diagnostics = await get_diagnostics_for_config_entry(hass, hass_client, entry)
    assert diagnostics["last_import"]["project"] == "Musterhaus"
    assert "sensor:GA-12" in diagnostics["applied"]
    assert "sensor:GA-19" not in diagnostics["applied"]


async def test_service_requires_setup(hass: HomeAssistant, config_dir, knx_reloads, upload) -> None:
    from homeassistant.setup import async_setup_component

    assert await async_setup_component(hass, DOMAIN, {})
    with pytest.raises(ServiceValidationError):
        await hass.services.async_call(DOMAIN, "import_project", {"file": file_id("x")}, blocking=True)
