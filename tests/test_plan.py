"""Import plan logic (pure Python)."""

from __future__ import annotations

from custom_components.knx_project_sync.mapping.manifest import DOMAINS
from custom_components.knx_project_sync.plan import apply_choice, build_plan, domain_choices
from custom_components.knx_project_sync.writer import render, unique_ids_of_knx_config
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


def _v1_state() -> dict:
    return build_plan(_manifest("musterhaus_v1"), {}, domains=DOMAINS, keep_removed=False).state()


def test_new_entities_are_pending_after_first_import():
    plan = build_plan(_manifest("musterhaus_v2"), _v1_state(), domains=DOMAINS, keep_removed=False, include_new=False)
    status = {e.key: e.status for e in plan.entries}
    assert status["sensor:GA-19"] == "pending"
    assert status["sensor:GA-12"] == "changed"
    assert "sensor:GA-19" not in plan.state()
    assert plan.has_pending

    # added in the panel
    plan = build_plan(
        _manifest("musterhaus_v2"),
        _v1_state(),
        domains=DOMAINS,
        keep_removed=False,
        include_new=False,
        selection={"sensor:GA-19": {"enabled": True}},
    )
    assert {e.key: e.status for e in plan.entries}["sensor:GA-19"] == "new"


def test_deselected_entity_is_removed_from_registry():
    plan = build_plan(
        _manifest("musterhaus_v1"),
        _v1_state(),
        domains=DOMAINS,
        keep_removed=True,
        selection={"light:GA-3": {"enabled": False}},
    )
    entry = next(e for e in plan.entries if e.key == "light:GA-3")
    assert entry.status == "deselected"
    assert "light:GA-3" not in plan.state()
    assert plan.removed_unique_ids == [("light", entry.unique_id)]
    assert plan.by_status("kept", "removed") == []


def test_switch_becomes_light():
    manifest = _manifest("musterhaus_v1")
    switch = next(e for e in manifest["entities"] if e["domain"] == "switch" and "state_address" in e["config"])
    assert domain_choices("switch", switch["config"]) == ["switch", "light"]
    previous = _v1_state()
    selection = {switch["key"]: {"domain": "light", "name": "Stehlampe"}}
    plan = build_plan(manifest, previous, domains=DOMAINS, keep_removed=False, selection=selection)
    entry = next(e for e in plan.entries if e.key == switch["key"])
    assert (entry.status, entry.domain, entry.detected_domain) == ("changed", "light", "switch")
    assert entry.config == {**switch["config"], "name": "Stehlampe"}
    assert entry.name == "Stehlampe"
    assert plan.state()[switch["key"]]["domain"] == "light"
    assert entry.config in plan.yaml_data()["light"]
    # the switch entity is replaced by a light entity
    assert ("switch", entry.unique_id) in plan.removed_unique_ids
    assert plan.migrations == []

    again = build_plan(manifest, plan.state(), domains=DOMAINS, keep_removed=False, selection=selection)
    assert next(e for e in again.entries if e.key == switch["key"]).status == "unchanged"


def test_choices():
    assert domain_choices("light", {"name": "a", "address": "1/1/1", "brightness_address": "1/1/3"}) == ["light"]
    assert domain_choices("light", {"name": "a", "address": "1/1/1"}) == ["light", "switch"]
    assert domain_choices("sensor", {"state_address": "1/1/1"}) == ["sensor"]
    # switch-only options are dropped, impossible changes ignored
    assert apply_choice("switch", {"name": "a", "address": "1/0/1", "respond_to_read": True}, {"domain": "light"}) == (
        "light",
        "a",
        {"name": "a", "address": "1/0/1"},
    )
    assert apply_choice("sensor", {"state_address": "3/0/1"}, {"domain": "light", "name": " "})[0] == "sensor"


def test_own_light_on_a_detected_switch_is_a_conflict():
    """Own YAML defines the GA as a light, the project detects a switch."""
    own = {
        ("light", "1/0/1"): {
            "config": {"name": "Mein Licht", "address": "1/0/1"},
            "file": "/c/configuration.yaml",
            "line": 7,
        }
    }
    plan = build_plan(_manifest("musterhaus_v1"), {}, domains=DOMAINS, keep_removed=False, foreign_entities=own)
    entry = next(e for e in plan.entries if e.key == "switch:GA-1")
    assert entry.status == "conflict"
    assert entry.conflict_with == {
        "domain": "light",
        "unique_id": "1/0/1",
        "name": "Mein Licht",
        "file": "/c/configuration.yaml",
        "line": 7,
        "kind": "unique_id",
        "address": None,
    }

    adopted = build_plan(
        _manifest("musterhaus_v1"),
        {},
        domains=DOMAINS,
        keep_removed=False,
        foreign_entities=own,
        selection={"switch:GA-1": {"adopt": True}},
    )
    entry = next(e for e in adopted.entries if e.key == "switch:GA-1")
    assert (entry.status, entry.domain, entry.config) == ("new", "light", {"name": "Mein Licht", "address": "1/0/1"})
    assert adopted.adoptions == [entry]
    assert {"name": "Mein Licht", "address": "1/0/1"} in adopted.yaml_data()["light"]
    assert adopted.removed_unique_ids == []

    # afterwards the own definition is gone and kept as the entity's config
    later = build_plan(
        _manifest("musterhaus_v1"),
        adopted.state(),
        domains=DOMAINS,
        keep_removed=False,
        selection={"switch:GA-1": {"domain": "light", "config": entry.config}},
    )
    assert next(e for e in later.entries if e.key == "switch:GA-1").status == "unchanged"


def test_marked_as_existing():
    previous = _v1_state()
    plan = build_plan(
        _manifest("musterhaus_v1"),
        previous,
        domains=DOMAINS,
        keep_removed=True,
        selection={"light:GA-3": {"existing": True}},
    )
    entry = next(e for e in plan.entries if e.key == "light:GA-3")
    assert entry.status == "existing"
    assert "light:GA-3" not in plan.state()
    # ours goes, unless the user's own YAML now defines the same entity
    assert plan.removed_unique_ids == [("light", "1/1/1")]
    own = build_plan(
        _manifest("musterhaus_v1"),
        previous,
        domains=DOMAINS,
        keep_removed=True,
        foreign_unique_ids={("light", "1/1/1")},
        selection={"light:GA-3": {"existing": True}},
    )
    assert own.removed_unique_ids == []


def test_addresses_corrected_by_hand():
    previous = _v1_state()
    selection = {
        # wrong status GA, missing brightness status
        "switch:GA-1": {"addresses": {"state_address": "1/0/3"}},
        "light:GA-3": {"addresses": {"address": "1/1/9", "brightness_state_address": None}},
    }
    plan = build_plan(_manifest("musterhaus_v1"), previous, domains=DOMAINS, keep_removed=False, selection=selection)
    entries = {e.key: e for e in plan.entries}
    assert entries["switch:GA-1"].config["state_address"] == "1/0/3"
    light = entries["light:GA-3"]
    assert light.status == "changed"
    assert light.config["address"] == "1/1/9"
    assert "brightness_state_address" not in light.config
    # new primary GA -> new unique_id, the registry entry moves with it
    assert ("light", "1/1/1", "1/1/9") in plan.migrations

    # unknown fields are ignored, type change keeps the edits
    domain, _, config = apply_choice(
        "switch",
        {"name": "a", "address": "1/0/1"},
        {"domain": "light", "addresses": {"state_address": "1/0/2", "bogus": "9/9/9"}},
    )
    assert (domain, config) == ("light", {"name": "a", "address": "1/0/1", "state_address": "1/0/2"})


def test_ga_used_by_an_own_climate():
    """The own YAML has a climate on the temperature GA the project detects as a sensor."""
    climate = {
        "name": "Wohnzimmer",
        "temperature_address": "3/0/1",
        "target_temperature_state_address": "3/0/9",
        "humidity_address": "3/0/2",
    }
    own = {("climate", "3/0/1_3/0/9_None_None"): {"config": climate, "file": "/c/configuration.yaml", "line": 20}}
    plan = build_plan(_manifest("musterhaus_v1"), {}, domains=DOMAINS, keep_removed=False, foreign_entities=own)
    entries = {e.key: e for e in plan.entries}
    temperature = entries["sensor:GA-12"]
    assert (temperature.status, temperature.reason) == ("conflict", "ga_in_use")
    assert temperature.conflict_with["domain"] == "climate"
    assert temperature.conflict_with["address"] == "3/0/1"
    assert entries["sensor:GA-13"].status == "conflict"

    # created anyway on request
    forced = build_plan(
        _manifest("musterhaus_v1"),
        {},
        domains=DOMAINS,
        keep_removed=False,
        foreign_entities=own,
        selection={"sensor:GA-12": {"enabled": True}},
    )
    assert next(e for e in forced.entries if e.key == "sensor:GA-12").status == "new"

    # take the climate over: only once, the other sensor on its GAs stays out
    selection = {"sensor:GA-12": {"adopt": True}, "sensor:GA-13": {"adopt": True}}
    adopted = build_plan(
        _manifest("musterhaus_v1"), {}, domains=DOMAINS, keep_removed=False, foreign_entities=own, selection=selection
    )
    entries = {e.key: e for e in adopted.entries}
    assert (entries["sensor:GA-12"].status, entries["sensor:GA-12"].domain) == ("new", "climate")
    assert entries["sensor:GA-12"].unique_id == "3/0/1_3/0/9_None_None"
    assert entries["sensor:GA-13"].status == "conflict"
    assert [e.key for e in adopted.adoptions] == ["sensor:GA-12"]

    # afterwards the climate is the app's own: the humidity sensor is a duplicate of it
    later = build_plan(
        _manifest("musterhaus_v1"),
        adopted.state(),
        domains=DOMAINS,
        keep_removed=False,
        selection={"sensor:GA-12": {"domain": "climate", "config": climate}},
    )
    entries = {e.key: e for e in later.entries}
    assert entries["sensor:GA-12"].status == "unchanged"
    assert (entries["sensor:GA-13"].status, entries["sensor:GA-13"].reason) == ("duplicate", "ga_in_use")
    assert entries["sensor:GA-13"].conflict_with["kind"] == "app"


def _text_manifest() -> dict:
    return {
        "project": {"name": "Texte"},
        "entities": [
            {
                "key": "sensor:GA-1",
                "domain": "sensor",
                "name": "Display Zeile 1",
                "config": {"name": "Display Zeile 1", "state_address": "7/0/1", "type": "string"},
                "sources": [],
            },
            {
                "key": "sensor:GA-2",
                "domain": "sensor",
                "name": "Temperatur",
                "config": {"name": "Temperatur", "state_address": "7/0/2", "type": "temperature"},
                "sources": [],
            },
        ],
        "unmapped": [],
    }


def test_texts_become_text_entities():
    from homeassistant.components.knx.schema import TextSchema

    plan = build_plan(_text_manifest(), {}, domains=[*DOMAINS, "text"], keep_removed=False)
    entries = {e.key: e for e in plan.entries}
    text = entries["sensor:GA-1"]
    assert (text.status, text.domain, text.detected_domain) == ("new", "text", "sensor")
    assert text.config == {"name": "Display Zeile 1", "address": "7/0/1", "state_address": "7/0/1", "type": "string"}
    assert text.unique_id == "7/0/1"
    TextSchema.ENTITY_SCHEMA(text.config)
    assert plan.yaml_data()["text"] == [text.config]
    assert entries["sensor:GA-2"].domain == "sensor"
    assert domain_choices("sensor", _text_manifest()["entities"][0]["config"]) == ["sensor", "text"]
    assert domain_choices("sensor", _text_manifest()["entities"][1]["config"]) == ["sensor"]

    # back to a sensor in the panel
    back = build_plan(
        _text_manifest(),
        plan.state(),
        domains=[*DOMAINS, "text"],
        keep_removed=False,
        selection={"sensor:GA-1": {"domain": "sensor"}},
    )
    entry = next(e for e in back.entries if e.key == "sensor:GA-1")
    assert (entry.domain, entry.config["state_address"], entry.config["type"]) == ("sensor", "7/0/1", "string")
    assert ("text", "7/0/1") in back.removed_unique_ids


def test_text_imported_as_sensor_stays_a_sensor():
    """Earlier versions imported texts as sensors: keep their entity_id."""
    old = build_plan(
        _text_manifest(),
        {},
        domains=[*DOMAINS, "text"],
        keep_removed=False,
        selection={"sensor:GA-1": {"domain": "sensor"}},
    ).state()
    plan = build_plan(_text_manifest(), old, domains=[*DOMAINS, "text"], keep_removed=False)
    entry = next(e for e in plan.entries if e.key == "sensor:GA-1")
    assert (entry.status, entry.domain) == ("unchanged", "sensor")
