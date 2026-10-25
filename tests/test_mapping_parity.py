"""Step 3: the Python port produces the same manifest as knx2home for every fixture."""

from __future__ import annotations

from custom_components.knx_project_sync.mapping import (
    build_ha_entities,
    build_manifest,
    catalog_from_xknxproject,
)
from helpers import FIXTURES, load_json
from xknx_digest import parse


def test_manifest_matches_knx2home(fixture_name, passwords):
    expected = load_json(FIXTURES / f"{fixture_name}.manifest.json")
    project = parse(FIXTURES / f"{fixture_name}.knxproj", passwords.get(fixture_name))
    catalog = catalog_from_xknxproject(project)
    manifest = build_manifest(catalog, build_ha_entities(catalog), generator=expected["generator"])
    assert manifest["entities"] == expected["entities"]
    assert manifest["unmapped"] == expected["unmapped"]
    assert manifest == expected
