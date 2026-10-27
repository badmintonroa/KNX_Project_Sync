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
    "einfamilienhaus": {"extra": {"cover:GA-19"}, "changed": {"cover:GA-10"}},
}


def test_manifest_matches_knx2home(fixture_name, passwords):
    expected = load_json(FIXTURES / f"{fixture_name}.manifest.json")
    project = parse(FIXTURES / f"{fixture_name}.knxproj", passwords.get(fixture_name))
    catalog = catalog_from_xknxproject(project)
    manifest = build_manifest(catalog, build_ha_entities(catalog), generator=expected["generator"])
    assert manifest["unmapped"] == expected["unmapped"]
    known = KNOWN_DIFFERENCES.get(fixture_name)
    if known is None:
        assert manifest["entities"] == expected["entities"]
        assert manifest == expected
        return
    want = {e["key"]: e for e in expected["entities"]}
    got = {e["key"]: e for e in manifest["entities"]}
    assert got.keys() - want.keys() == known["extra"]
    assert want.keys() - got.keys() == set()
    assert {key for key in want if got[key] != want[key]} == known["changed"]
