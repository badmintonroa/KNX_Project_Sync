"""Step 1: the golden knx2home-ha-manifest v1 files follow the documented contract."""

from __future__ import annotations

import jsonschema
import pytest

from helpers import FIXTURES, ROOT, load_json
from xknx_digest import parse

SCHEMA = load_json(ROOT / "schema" / "manifest-v1.schema.json")


@pytest.fixture
def manifest(fixture_name):
    return load_json(FIXTURES / f"{fixture_name}.manifest.json")


def test_schema(manifest):
    jsonschema.validate(manifest, SCHEMA)


def test_keys_unique_and_derived_from_primary_source(manifest):
    keys = [e["key"] for e in manifest["entities"]]
    assert len(keys) == len(set(keys))
    for entity in manifest["entities"]:
        base = entity["key"].split("#")[0]
        domain, ident = base.split(":", 1)
        assert domain == entity["domain"]
        if ident.startswith("addr:"):
            # fallback only for addresses without an ETS group address id
            assert any(s["address"] == ident[5:] and s["ga_id"] is None for s in entity["sources"]), entity
        else:
            assert any(s["ga_id"] == ident for s in entity["sources"]), entity


def test_sources_match_config(manifest):
    for entity in manifest["entities"]:
        for source in entity["sources"]:
            assert entity["config"][source["field"]] == source["address"]
        assert entity["name"] == entity["config"].get("name")


def test_sources_resolve_in_xknxproject(fixture_name, manifest, passwords):
    """Every GA the manifest refers to exists with the same ETS id in xknxproject."""
    project = parse(FIXTURES / f"{fixture_name}.knxproj", passwords.get(fixture_name))
    gas = project["group_addresses"]
    for entity in manifest["entities"]:
        for source in entity["sources"]:
            assert gas[source["address"]]["identifier"] == source["ga_id"]
    for item in manifest["unmapped"]:
        assert gas[item["address"]]["identifier"] == item["ga_id"]


def test_keys_survive_project_revision():
    """v1 -> v2: renamed and re-addressed GAs keep their entity key."""
    v1 = {e["key"]: e for e in load_json(FIXTURES / "musterhaus_v1.manifest.json")["entities"]}
    v2 = {e["key"]: e for e in load_json(FIXTURES / "musterhaus_v2.manifest.json")["entities"]}

    assert sorted(v1.keys() - v2.keys()) == ["date:GA-17", "time:GA-16"]
    assert sorted(v2.keys() - v1.keys()) == ["sensor:GA-19"]
    # renamed in ETS
    assert v1["switch:GA-1"]["name"] != v2["switch:GA-1"]["name"]
    # re-addressed in ETS: same key, new address
    assert v1["sensor:GA-12"]["config"]["state_address"] == "3/0/1"
    assert v2["sensor:GA-12"]["config"]["state_address"] == "3/1/1"
