"""Climate for rooms without ETS links is grouped by GA name, and climate names are tidy."""

from __future__ import annotations

from custom_components.knx_project_sync.mapping import Catalog, build_ha_entities
from custom_components.knx_project_sync.mapping.aggregate import add_name_based_operation_modes
from custom_components.knx_project_sync.mapping.catalog import GroupAddress, Link


def _catalog(gas: list[GroupAddress], links: list[Link] | None = None) -> Catalog:
    return Catalog(name="x", group_addresses=gas, links=links or [])


def _room(prefix: str, base: int, shift_dpt: str | None, temp_dpt: str | None = None) -> list[GroupAddress]:
    names = [
        ("Sollwertverschiebung", shift_dpt),
        ("IST-Temp", temp_dpt),
        ("BASIS-Soll", temp_dpt),
        ("RM_Aktueller_Soll", temp_dpt),
        ("Betriebsvorwahl", None),
        ("RM_Betriebsvorwahl", None),
    ]
    return [
        GroupAddress(id=f"GA-{base + i}", name=f"{prefix}_H_{name}", address=f"4/0/{base + i}", dpt=dpt)
        for i, (name, dpt) in enumerate(names)
    ]


def test_unlinked_room_becomes_a_climate():
    ent = build_ha_entities(_catalog(_room("Kueche", 0, "9.002")))
    assert ent.climates == [
        {
            "name": "Kueche",
            "temperature_address": "4/0/1",
            "target_temperature_state_address": "4/0/2",
            "setpoint_shift_address": "4/0/0",
            "setpoint_shift_state_address": "4/0/0",
            "setpoint_shift_mode": "DPT9002",
            "operation_mode_address": "4/0/4",
            "operation_mode_state_address": "4/0/5",
        }
    ]
    # the GAs the climate uses are not offered again
    assert "4/0/0" not in {s["state_address"] for s in ent.sensors}
    assert "4/0/2" not in {s["state_address"] for s in ent.sensors}


def test_untyped_room_assumes_a_2_byte_shift():
    ent = build_ha_entities(_catalog(_room("Kueche", 0, None)))
    assert ent.climates[0]["setpoint_shift_mode"] == "DPT9002"


def test_1_bit_shift_is_no_setpoint_shift_and_no_cover():
    ent = build_ha_entities(_catalog(_room("Kueche", 0, "1.007")))
    assert "setpoint_shift_address" not in ent.climates[0]
    assert ent.covers == []


def test_6_010_shift_keeps_its_mode():
    ent = build_ha_entities(_catalog(_room("Kueche", 0, "6.010")))
    assert ent.climates[0]["setpoint_shift_mode"] == "DPT6010"


def test_two_rooms_stay_separate():
    ent = build_ha_entities(_catalog(_room("Bad", 0, "9.002") + _room("Flur", 10, "9.002")))
    assert sorted(c["name"] for c in ent.climates) == ["Bad", "Flur"]


def test_template_room_is_skipped():
    assert build_ha_entities(_catalog(_room("Zimmername", 0, None))).climates == []


def test_actual_temperature_without_setpoint_is_no_climate():
    gas = [g for g in _room("Bad", 0, "9.002") if "BASIS" not in g.name]
    assert build_ha_entities(_catalog(gas)).climates == []


def test_wrong_datapoint_type_is_no_climate():
    gas = _room("Bad", 0, "9.002", temp_dpt="5.001")
    assert build_ha_entities(_catalog(gas)).climates == []


def test_climate_name_drops_the_setpoint_word_and_dangling_separators():
    from custom_components.knx_project_sync.mapping.aggregate import _climate_name

    def name(text: str) -> str | None:
        return _climate_name(GroupAddress(id="GA-1", name=text, address="1/1/1", dpt="9.001"))

    assert name("Bad_H_BASIS-Soll") == "Bad"
    assert name("Kinderzimmer_H_BASIS-Soll") == "Kinderzimmer"
    assert name("Wohnzimmer Sollwert") == "Wohnzimmer"


def test_operation_mode_by_name_needs_no_or_the_matching_datapoint_type():
    def ga(i, name, dpt):
        return GroupAddress(id=f"GA-{i}", name=name, address=f"6/0/{i}", dpt=dpt)

    gas = [
        ga(1, "Office Actual temperature", "9.001"),
        ga(2, "Office Operation mode", "20.102"),
        ga(3, "Office Operation mode status", "20.102"),
        ga(4, "Hall Actual temperature", "9.001"),
        ga(5, "Hall HVAC mode", "1.001"),
    ]
    aggs = [
        {"name": "Office", "temperature_address": "6/0/1", "consumed": set()},
        {"name": "Hall", "temperature_address": "6/0/4", "consumed": set()},
    ]
    add_name_based_operation_modes(gas, aggs)
    assert aggs[0]["operation_mode_address"] == "6/0/2"
    assert aggs[0]["operation_mode_state_address"] == "6/0/3"
    assert "operation_mode_address" not in aggs[1]
