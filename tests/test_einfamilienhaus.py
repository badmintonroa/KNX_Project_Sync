"""Anonymised real ETS6 project (family house, 264 GAs, 36 devices from five manufacturers).

`tests/fixtures/einfamilienhaus.knxproj` was made from a real installation with
tools/fixtures/anonymize_project.py: structure, links and application programs are
kept, names, keys and identifiers of people and installation are not.
"""

from __future__ import annotations

from collections import Counter
import re
import zipfile

import anonymize_project
import yaml

from custom_components.knx_project_sync.mapping.manifest import DOMAINS
from custom_components.knx_project_sync.plan import build_plan
from custom_components.knx_project_sync.project import prepare_project
from custom_components.knx_project_sync.writer import render, unique_ids_of_knx_config
from helpers import FIXTURES, parse

PROJECT = FIXTURES / "einfamilienhaus.knxproj"
WORD = re.compile(r"[^\W\d_]+")


def _prepared():
    return prepare_project(parse(PROJECT))


# --- the fixture itself -------------------------------------------------------


def test_archive_contains_only_whitelisted_files():
    names = zipfile.ZipFile(PROJECT).namelist()
    assert "P-0C2D/project.xml" in names
    for name in names:
        assert re.fullmatch(
            r"knx_master\.xml|P-0C2D\.signature|P-0C2D/(?:project|0)\.xml|M-\w+/(?:Catalog|Hardware|M-\w+_A-[\w-]+)\.xml",
            name,
        ), name


def test_no_personal_data_in_project_files():
    archive = zipfile.ZipFile(PROJECT)
    for name in ("P-0C2D/project.xml", "P-0C2D/0.xml"):
        text = archive.read(name).decode("utf-8")
        for secret in ("ProjectTrace", "UserName", "FDSK", "ToolKey", "MACAddress", "BCUKey", "LastModified"):
            assert secret not in text, (name, secret)


def test_project_guid_is_replaced():
    text = zipfile.ZipFile(PROJECT).read("P-0C2D/project.xml").decode("utf-8")
    assert 'Guid="00000000-0000-4000-8000-000000000000"' in text


def test_all_names_are_generic_or_made_up():
    """Every word of every free text is in the vocabulary or one of the made-up first names."""
    allowed = anonymize_project.vocabulary() | set(anonymize_project.PSEUDONYMS) | {anonymize_project.PROJECT_NAME}
    project = parse(PROJECT)
    texts = [project["info"]["name"]]
    texts += [ga["name"] for ga in project["group_addresses"].values()]

    def collect(spaces):
        for space in spaces.values():
            texts.append(space["name"])
            collect(space["spaces"])

    collect(project["locations"])

    def collect_ranges(ranges):
        for group_range in ranges.values():
            texts.append(group_range["name"])
            collect_ranges(group_range["group_ranges"])

    collect_ranges(project["group_ranges"])
    unknown = {word for text in texts for word in WORD.findall(text)} - allowed
    assert not unknown


# --- structure of a real project -----------------------------------------------


def test_shape():
    project = parse(PROJECT)
    assert project["info"]["name"] == "Beispielhaus"
    assert len(project["group_addresses"]) == 264
    assert len(project["devices"]) == 36
    assert len(project["communication_objects"]) == 424
    assert {d["manufacturer_name"] for d in project["devices"].values()} >= {"Lingg & Janke", "MDT technologies"}


def test_detection_result():
    manifest = _prepared().manifest
    assert Counter(e["domain"] for e in manifest["entities"]) == {
        "switch": 49,
        "sensor": 42,
        "cover": 16,
        "climate": 14,
        "binary_sensor": 7,
        "light": 4,
        "time": 1,
        "date": 1,
        "weather": 1,
    }
    assert len(manifest["unmapped"]) == 6


def test_rooms_follow_the_innermost_location_of_the_device():
    """Devices sit in rooms, some of them in a distribution board inside a room."""
    rooms = _prepared().rooms
    assert len(rooms) == 126
    counts = Counter(rooms.values())
    assert counts["Esszimmer"] == 6
    assert counts["Wohnzimmer"] == 1
    # entities of the actuators in the distribution boards get the board, not the room around it
    assert counts["Schaltschrank"] == 57
    assert counts["Schlatschrank HWR oben"] == 17
    assert "HWR" in counts


# --- import of a real project ----------------------------------------------------


def test_first_import_and_unchanged_reimport():
    manifest = _prepared().manifest
    first = build_plan(manifest, {}, domains=DOMAINS, keep_removed=False)
    assert first.summary()["new"] == 123
    assert first.summary()["duplicate"] == 7  # the GAs of the weather station
    assert first.summary()["excluded"] == 5
    again = build_plan(manifest, first.state(), domains=DOMAINS, keep_removed=False)
    assert not again.has_changes
    assert again.summary()["unchanged"] == 123


def test_weather_station_owns_its_group_addresses():
    """Temperature, wind, sun, day/night and wind alarm are not offered a second time as sensors and switches."""
    manifest = _prepared().manifest
    plan = build_plan(manifest, {}, domains=DOMAINS, keep_removed=False)
    status = {e.key: e.status for e in plan.entries}
    assert status["weather:GA-229"] == "new"
    for key in (
        "sensor:GA-229",
        "sensor:GA-230",
        "sensor:GA-232",
        "sensor:GA-233",
        "sensor:GA-234",
        "switch:GA-235",
        "switch:GA-241",
    ):
        assert status[key] == "duplicate", key
    entry = next(e for e in plan.entries if e.key == "switch:GA-235")
    assert (entry.conflict_with.domain, entry.conflict_with.address) == ("weather", "0/4/22")

    without = build_plan(manifest, {}, domains=[d for d in DOMAINS if d != "weather"], keep_removed=False)
    assert {e.key: e.status for e in without.entries}["sensor:GA-229"] == "new"


def test_written_yaml_roundtrips_and_has_unique_ids():
    plan = build_plan(_prepared().manifest, {}, domains=DOMAINS, keep_removed=False)
    data = yaml.safe_load(render(plan.yaml_data(), plan.project))
    written = unique_ids_of_knx_config(data["knx"])
    assert written == {(e.domain, e.unique_id) for e in plan.written}
    assert len(written) == len(plan.written)


def _tag_nacht_taken_over() -> dict:
    """Panel choice left over from taking over a hand written weather entity onto the day/night switch."""
    config = {
        "name": "Home",
        "address_temperature": "0/4/16",
        "address_brightness_south": "0/4/20",
        "address_brightness_west": "0/4/19",
        "address_brightness_east": "0/4/21",
        "address_wind_speed": "0/4/17",
        "address_day_night": "0/4/22",
    }
    return {"switch:GA-235": {"config": config, "domain": "weather"}}


def test_undecided_entity_with_taken_over_config_does_not_win():
    """Offered in the panel only (`pending`): it must not take the unique_id and GAs of the weather station."""
    manifest = _prepared().manifest
    first = build_plan(manifest, {}, domains=[d for d in DOMAINS if d != "weather"], keep_removed=False)
    previous = {key: applied for key, applied in first.state().items() if key != "switch:GA-235"}  # never created
    selection = _tag_nacht_taken_over()
    plan = build_plan(manifest, previous, domains=DOMAINS, keep_removed=False, selection=selection, include_new=False)
    status = {e.key: (e.status, e.reason) for e in plan.entries}
    assert status["switch:GA-235"] == ("pending", None)
    assert status["weather:GA-229"] == ("pending", None)


def test_weather_rule_keeps_entities_imported_before():
    """Sensors imported before the weather station is chosen are not removed."""
    manifest = _prepared().manifest
    old = build_plan(manifest, {}, domains=[d for d in DOMAINS if d != "weather"], keep_removed=False)
    plan = build_plan(manifest, old.state(), domains=DOMAINS, keep_removed=False, include_new=False)
    status = {e.key: e.status for e in plan.entries}
    assert status["sensor:GA-229"] == "unchanged"
    assert status["weather:GA-229"] == "pending"
    assert plan.removed_unique_ids == []
