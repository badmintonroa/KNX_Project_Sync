"""Scenes are found by DPT (17, 18) and name, not by the group address."""

from __future__ import annotations

import pytest

from custom_components.knx_project_sync.mapping.aggregate import map_single_ga_to_entity
from custom_components.knx_project_sync.mapping.catalog import GroupAddress


def _map(address: str, name: str, dpt: str | None) -> str:
    return map_single_ga_to_entity(GroupAddress(id="GA-1", name=name, address=address, dpt=dpt))[0]


@pytest.mark.parametrize("dpt", ["17.001", "18.001"])
def test_scene_dpts_are_scenes_at_any_address(dpt):
    assert _map("4/2/1", "Abend", dpt) == "scene"
    assert _map("0/1/3", "Abend", dpt) == "scene"


def test_scene_name_is_a_scene():
    assert _map("4/2/1", "Wohnzimmer Szene 3", None) == "scene"


def test_group_0_1_is_not_a_scene_by_itself():
    assert _map("0/1/21", "Südfassade Absolut", "5.001") == "sensor"
    assert _map("0/1/5", "Rollo Auf/Ab", "1.008") == "cover"
