"""Entity building (port of the aggregate path of knx2home buildHaEntities, export.ts)."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from .aggregate import (
    build_address_light_aggregates,
    build_channel_cover_aggregates,
    build_channel_light_aggregates,
    build_climate_aggregates,
    build_cover_aggregates,
    build_la_light_aggregates,
    build_linked_light_aggregates,
    build_name_based_climate_aggregates,
    build_name_based_light_aggregates,
    build_switch_aggregates,
    build_weather_aggregates,
    map_single_ga_to_entity,
)
from .catalog import Catalog

# knx2home list name -> HA domain, in knx2home order
LISTS = {
    "switches": "switch",
    "binary_sensors": "binary_sensor",
    "lights": "light",
    "sensors": "sensor",
    "times": "time",
    "dates": "date",
    "datetimes": "datetime",
    "covers": "cover",
    "climates": "climate",
    "weathers": "weather",
    "scenes": "scene",
    "unknowns": "_unknown",
}
LIST_BY_DOMAIN = {domain: name for name, domain in LISTS.items()}


@dataclass
class HaEntities:
    switches: list[dict] = field(default_factory=list)
    binary_sensors: list[dict] = field(default_factory=list)
    lights: list[dict] = field(default_factory=list)
    sensors: list[dict] = field(default_factory=list)
    times: list[dict] = field(default_factory=list)
    dates: list[dict] = field(default_factory=list)
    datetimes: list[dict] = field(default_factory=list)
    covers: list[dict] = field(default_factory=list)
    climates: list[dict] = field(default_factory=list)
    weathers: list[dict] = field(default_factory=list)
    scenes: list[dict] = field(default_factory=list)
    unknowns: list[dict] = field(default_factory=list)

    def of(self, domain: str) -> list[dict]:
        return getattr(self, LIST_BY_DOMAIN[domain])


def _is_reserve(payload: dict) -> bool:
    return (payload.get("name") or "").strip().lower() == "reserve"


def _light_fields(agg: dict) -> int:
    return sum(1 for k in ("on_off", "on_off_state", "dimming", "brightness", "brightness_state") if agg.get(k))


def build_ha_entities(catalog: Catalog, drop_reserve: bool = True) -> HaEntities:
    gas = catalog.group_addresses
    links = catalog.links
    contexts = catalog.function_context or None
    ent = HaEntities()

    def push(lst: list[dict], payload: dict[str, Any]) -> None:
        if not (drop_reserve and _is_reserve(payload)):
            lst.append(payload)

    channel_lights = build_channel_light_aggregates(gas, links)
    all_lights = [
        *channel_lights,
        *build_linked_light_aggregates(gas, contexts),
        *build_address_light_aggregates(gas),
        *build_la_light_aggregates(gas),
        *build_name_based_light_aggregates(gas),
    ]
    by_key: dict[str, dict] = {}
    for agg in all_lights:
        key = agg.get("on_off") or agg.get("brightness") or ""
        if not key:
            continue
        existing = by_key.get(key)
        if existing is None:
            by_key[key] = agg
        elif _light_fields(agg) > _light_fields(existing):
            agg["consumed"] = existing["consumed"] | agg["consumed"]
            by_key[key] = agg
        else:
            existing["consumed"] = existing["consumed"] | agg["consumed"]
    light_aggs = list(by_key.values())

    for a in light_aggs:
        if not a.get("on_off") and not a.get("brightness"):
            continue
        entry = {"name": a["name"], "address": a.get("on_off") or a["brightness"]}
        if a.get("on_off_state"):
            entry["state_address"] = a["on_off_state"]
        if a.get("brightness"):
            entry["brightness_address"] = a["brightness"]
        if a.get("brightness_state"):
            entry["brightness_state_address"] = a["brightness_state"]
        push(ent.lights, entry)

    switch_aggs = build_switch_aggregates(gas, links, contexts)
    # switch outputs of dimming actuators are exported as lights
    light_addresses = {a.get("on_off") for a in channel_lights if a.get("on_off")}
    for s in switch_aggs:
        if s.get("address") and s["address"] in light_addresses:
            continue
        entry = {"name": s["name"], "address": s["address"]}
        if s.get("state_address"):
            entry["state_address"] = s["state_address"]
        else:
            entry["respond_to_read"] = True
        push(ent.switches, entry)

    climate_aggs = build_climate_aggregates(gas, links)
    climate_aggs += build_name_based_climate_aggregates(gas, {c["temperature_address"] for c in climate_aggs})
    climate_ids = {i for c in climate_aggs for i in c["consumed"]}

    channel_covers = build_channel_cover_aggregates(gas, links)
    channel_cover_ids = {i for c in channel_covers for i in c["consumed"]}
    cover_aggs = [
        *channel_covers,
        *build_cover_aggregates(
            [g for g in gas if g.id not in channel_cover_ids and g.id not in climate_ids], contexts
        ),
    ]
    for c in cover_aggs:
        entry = {"name": c["name"]}
        for key in (
            "move_long_address",
            "move_short_address",
            "stop_address",
            "position_address",
            "position_state_address",
            "angle_address",
            "angle_state_address",
        ):
            if c.get(key):
                entry[key] = c[key]
        if c.get("invert_position"):
            entry["invert_position"] = True
        if c.get("invert_angle"):
            entry["invert_angle"] = True
        push(ent.covers, entry)

    for c in climate_aggs:
        push(ent.climates, {k: v for k, v in c.items() if k != "consumed"})

    for w in build_weather_aggregates(gas, links):
        ent.weathers.append({k: v for k, v in w.items() if k != "consumed"})

    consumed: set[str] = set()
    for group in (light_aggs, switch_aggs, cover_aggs, climate_aggs):
        for a in group:
            consumed |= a["consumed"]
    consumed_addresses: set[str] = set()
    for group in (light_aggs, switch_aggs, cover_aggs):
        for a in group:
            for key, value in a.items():
                if isinstance(value, str) and "address" in key:
                    consumed_addresses.add(value)

    for ga in gas:
        if ga.id in consumed or ga.address in consumed_addresses:
            continue
        domain, payload = map_single_ga_to_entity(ga)
        if domain == "_unknown":
            ent.unknowns.append(payload)
        else:
            push(ent.of(domain), payload)

    if drop_reserve:
        ent.unknowns = [u for u in ent.unknowns if u["name"].strip().lower() != "reserve"]
    return ent
