"""Group addresses without a datapoint type are recognised by German names."""

from __future__ import annotations

import pytest

from custom_components.knx_project_sync.mapping.aggregate import map_single_ga_to_entity
from custom_components.knx_project_sync.mapping.catalog import GroupAddress


def _map(address: str, name: str, dpt: str | None = None) -> tuple[str, dict]:
    return map_single_ga_to_entity(GroupAddress(id="GA-1", name=name, address=address, dpt=dpt))


def test_brightness_without_dpt_is_an_illuminance_sensor():
    domain, payload = _map("31/0/3", "Helligkeit Außen")
    assert (domain, payload["type"]) == ("sensor", "illuminance")


@pytest.mark.parametrize("name", ["EG CO Wohnzimmer", "EG CO₂ Esszimmer", "Raum CO2"])
def test_co2_without_dpt_is_a_ppm_sensor(name):
    domain, payload = _map("31/0/4", name)
    assert (domain, payload["type"]) == ("sensor", "ppm")


@pytest.mark.parametrize("name", ["Niederschlag", "Regen", "Regenalarm"])
def test_precipitation_without_dpt_is_a_binary_sensor(name):
    assert _map("31/0/6", name)[0] == "binary_sensor"


def test_precipitation_with_dpt_stays_a_rain_amount():
    domain, payload = _map("31/0/6", "Niederschlag", "9.026")
    assert (domain, payload["type"]) == ("sensor", "rain_amount")


def test_scene_by_name_does_not_depend_on_the_address():
    domain, payload = _map("8/0/3", "Szene 4 Essen")
    assert (domain, payload["scene_number"]) == ("scene", 4)
