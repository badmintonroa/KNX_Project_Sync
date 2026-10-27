"""Step 3: the Python port produces the same manifest as knx2home for every fixture."""

from __future__ import annotations

from custom_components.knx_project_sync.mapping import (
    build_ha_entities,
    build_manifest,
    catalog_from_xknxproject,
)
from helpers import FIXTURES, load_json, parse

# deliberate differences, see docs/port-notes.md. The test fails when one of them disappears.
KNOWN_DIFFERENCES = {
    # The stop GA of the blind "Wohnzimmer Bodenttiefes Fenster" is 1.008 on the module
    # object only through an override on the ComObjectRef (docs/port-notes.md, point 3).
    # knx2home ignores the override, sees 1.007 and takes the GA as move_short_address.
    # The port keeps it a separate 1.008 command, which then ends up as a cover of its own.
    #
    # 0/1/x is a scene in knx2home whatever the DPT (point 8). Here it is the blind group:
    # two 5.001 "Absolut" GAs, which are percent sensors in the port.
    "einfamilienhaus": {
        "extra": {"cover:GA-19", "sensor:GA-236", "sensor:GA-237"},
        "missing": {"scene:GA-236", "scene:GA-237"},
        "changed": {"cover:GA-10"},
        "unmapped": [],
    },
    # "Zentral 3" without DPT on 0/1/3: a scene in knx2home by address, unmapped in the port
    "heuristics": {
        "extra": set(),
        "missing": {"scene:GA-25"},
        "changed": set(),
        "unmapped": [{"address": "0/1/3", "ga_id": "GA-25", "name": "Zentral 3", "dpt": None}],
    },
}


def test_manifest_matches_knx2home(fixture_name, passwords):
    expected = load_json(FIXTURES / f"{fixture_name}.manifest.json")
    project = parse(FIXTURES / f"{fixture_name}.knxproj", passwords.get(fixture_name))
    catalog = catalog_from_xknxproject(project)
    manifest = build_manifest(catalog, build_ha_entities(catalog), generator=expected["generator"])
    known = KNOWN_DIFFERENCES.get(fixture_name)
    if known is None:
        assert manifest["entities"] == expected["entities"]
        assert manifest["unmapped"] == expected["unmapped"]
        assert manifest == expected
        return
    want = {e["key"]: e for e in expected["entities"]}
    got = {e["key"]: e for e in manifest["entities"]}
    assert got.keys() - want.keys() == known["extra"]
    assert want.keys() - got.keys() == known["missing"]
    assert {key for key in want.keys() & got.keys() if got[key] != want[key]} == known["changed"]
    assert [u for u in manifest["unmapped"] if u not in expected["unmapped"]] == known["unmapped"]
    assert [u for u in expected["unmapped"] if u not in manifest["unmapped"]] == []
