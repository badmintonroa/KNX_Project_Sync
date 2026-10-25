"""Import plan logic (pure Python)."""

from __future__ import annotations

from custom_components.knx2home_importer.mapping.manifest import DOMAINS
from custom_components.knx2home_importer.plan import build_plan
from custom_components.knx2home_importer.writer import render, unique_ids_of_knx_config
from helpers import FIXTURES, load_json


def _manifest(name: str) -> dict:
    return load_json(FIXTURES / f"{name}.manifest.json")


def test_first_import_all_new():
    plan = build_plan(_manifest("musterhaus_v1"), {}, domains=DOMAINS, keep_removed=False)
    assert plan.summary()["new"] == 8
    assert plan.migrations == []


def test_reimport_diff():
    v1 = build_plan(_manifest("musterhaus_v1"), {}, domains=DOMAINS, keep_removed=False)
    v2 = build_plan(_manifest("musterhaus_v2"), v1.state(), domains=DOMAINS, keep_removed=False)
    status = {e.key: e.status for e in v2.entries}
    assert status["sensor:GA-19"] == "new"
    assert status["sensor:GA-12"] == "changed"
    assert status["switch:GA-1"] == "changed"  # renamed
    assert status["light:GA-3"] == "unchanged"
    assert status["time:GA-16"] == status["date:GA-17"] == "removed"
    assert v2.migrations == [("sensor", "3/0/1", "3/1/1")]
    assert sorted(v2.removed_unique_ids) == [("date", "5/0/2"), ("time", "5/0/1")]
    assert not v1.has_changes or v2.has_changes


def test_same_project_again_is_unchanged():
    v1 = build_plan(_manifest("musterhaus_v1"), {}, domains=DOMAINS, keep_removed=False)
    again = build_plan(_manifest("musterhaus_v1"), v1.state(), domains=DOMAINS, keep_removed=False)
    assert not again.has_changes
    assert again.summary()["unchanged"] == 8


def test_recreated_ga_is_matched_by_unique_id():
    """GA deleted and recreated in ETS (new GA id, same address) -> same entity."""
    v1 = build_plan(_manifest("musterhaus_v1"), {}, domains=DOMAINS, keep_removed=False)
    manifest = _manifest("musterhaus_v1")
    for e in manifest["entities"]:
        if e["key"] == "sensor:GA-12":
            e["key"] = "sensor:GA-99"
    plan = build_plan(manifest, v1.state(), domains=DOMAINS, keep_removed=False)
    entry = next(e for e in plan.entries if e.key == "sensor:GA-99")
    assert entry.status == "changed"
    assert entry.previous_key == "sensor:GA-12"
    assert plan.by_status("removed") == []


def test_skips():
    manifest = _manifest("heuristics")
    foreign = {("switch", "12/0/1")}
    plan = build_plan(
        manifest,
        {},
        domains=[d for d in DOMAINS if d != "weather"],
        keep_removed=False,
        foreign_unique_ids=foreign,
        validate=lambda domain, config: "bad" if config.get("name") == "Zentral 3" else None,
    )
    status = {e.key: (e.status, e.reason) for e in plan.entries}
    assert status["switch:GA-1"] == ("duplicate", "light")  # light on the same GA
    assert status["switch:GA-43"] == ("conflict", "own_yaml")
    assert status["scene:GA-25"] == ("invalid", "bad")
    assert status["weather:GA-37"] == ("excluded", None)
    assert status["light:GA-1"] == ("new", None)


def test_keep_removed():
    v1 = build_plan(_manifest("musterhaus_v1"), {}, domains=DOMAINS, keep_removed=False)
    v2 = build_plan(_manifest("musterhaus_v2"), v1.state(), domains=DOMAINS, keep_removed=True)
    assert {e.key for e in v2.by_status("kept")} == {"time:GA-16", "date:GA-17"}
    assert v2.removed_unique_ids == []
    assert "time" in v2.yaml_data()


def test_yaml_roundtrip_unique_ids():
    plan = build_plan(_manifest("heuristics"), {}, domains=DOMAINS, keep_removed=False)
    import yaml

    data = yaml.safe_load(render(plan.yaml_data(), plan.project))
    assert unique_ids_of_knx_config(data["knx"]) == {(e.domain, e.unique_id) for e in plan.written}


def test_raw_yaml_unique_ids():
    knx = {
        "switch": [{"address": ["1/0/1", "1/0/3"]}, {"name": "x"}],
        "cover": {"move_long_address": "2/0/1"},
        "light": "not a list",
    }
    assert unique_ids_of_knx_config(knx) == {("switch", "1/0/1"), ("switch", "None"), ("cover", "2/0/1_None")}


def test_entity_now_in_own_yaml_is_not_deleted():
    """Imported before, now defined by hand: drop it from the package, keep the registry entry."""
    v1 = build_plan(_manifest("musterhaus_v1"), {}, domains=DOMAINS, keep_removed=False)
    plan = build_plan(
        _manifest("musterhaus_v1"),
        v1.state(),
        domains=DOMAINS,
        keep_removed=False,
        foreign_unique_ids={("light", "1/1/1")},
    )
    status = {(e.key, e.status) for e in plan.entries}
    assert ("light:GA-3", "conflict") in status
    assert ("light:GA-3", "removed") in status
    assert "light" not in plan.yaml_data()
    assert plan.removed_unique_ids == []
