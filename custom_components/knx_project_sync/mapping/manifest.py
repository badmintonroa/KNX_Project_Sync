"""knx2home-ha-manifest v1 (see docs/manifest-v1.md).

Same construction as tools/reference/generate.ts, so that manifests of the
Python port and the knx2home reference can be compared one to one.
"""

from __future__ import annotations

import json
from typing import Any

from .catalog import Catalog
from .dpt import to_dot
from .entities import HaEntities

FORMAT = "knx2home-ha-manifest"
VERSION = 1

# HA domains in manifest order
DOMAINS = [
    "switch",
    "binary_sensor",
    "light",
    "sensor",
    "time",
    "date",
    "datetime",
    "cover",
    "scene",
    "climate",
    "weather",
]

# what the integration can write: the knx2home domains plus types only the panel offers
HA_DOMAINS = [*DOMAINS, "text"]

PRIMARY_FIELDS = {
    "switch": ["address"],
    "binary_sensor": ["state_address"],
    "light": ["address", "brightness_address"],
    "sensor": ["state_address"],
    "time": ["address"],
    "date": ["address"],
    "datetime": ["address"],
    "cover": ["move_long_address", "position_address", "move_short_address", "stop_address"],
    "scene": ["address"],
    "climate": ["temperature_address", "target_temperature_state_address"],
    "weather": ["address_temperature"],
}


def is_address_field(key: str) -> bool:
    return key == "address" or key.endswith("_address") or key.startswith("address_")


def address_sort_key(address: str | None) -> str:
    return "/".join(part.rjust(5, "0") for part in (address or "").split("/"))


def _js_json(value: Any) -> str:
    """JSON.stringify for sorting ties like the reference generator."""
    return json.dumps(value, ensure_ascii=False, separators=(",", ":"))


def build_manifest(catalog: Catalog, ent: HaEntities, generator: dict[str, Any], drop_reserve: bool = True) -> dict:
    ga_by_address = {ga.address: ga for ga in catalog.group_addresses}
    entities: list[dict] = []
    for domain in DOMAINS:
        rows = []
        for payload in ent.of(domain):
            config = {k: v for k, v in payload.items() if v is not None}
            sources = []
            for key, value in config.items():
                if not is_address_field(key) or not isinstance(value, str):
                    continue
                ga = ga_by_address.get(value)
                sources.append({"field": key, "address": value, "ga_id": ga.id if ga else None})
            primary_field = next((f for f in PRIMARY_FIELDS[domain] if isinstance(config.get(f), str)), None)
            if primary_field is None and sources:
                primary_field = sources[0]["field"]
            primary = next((s for s in sources if s["field"] == primary_field), None)
            if primary and primary["ga_id"]:
                base = f"{domain}:{primary['ga_id']}"
            else:
                base = f"{domain}:addr:{primary['address'] if primary else 'none'}"
            rows.append((base, primary["address"] if primary else None, config, sources))
        rows.sort(key=lambda r: (address_sort_key(r[1]), _js_json(r[2])))
        counts: dict[str, int] = {}
        for base, _, config, sources in rows:
            counts[base] = counts.get(base, 0) + 1
            n = counts[base]
            entities.append(
                {
                    "key": base if n == 1 else f"{base}#{n}",
                    "domain": domain,
                    "name": config.get("name"),
                    "config": config,
                    "sources": sources,
                }
            )

    unmapped = []
    for u in sorted(ent.unknowns, key=lambda u: address_sort_key(u["address"])):
        ga = ga_by_address.get(u["address"])
        unmapped.append(
            {"address": u["address"], "ga_id": ga.id if ga else None, "name": u["name"], "dpt": to_dot(u.get("dpt"))}
        )

    return {
        "format": FORMAT,
        "version": VERSION,
        "generator": generator,
        "project": {"name": catalog.name},
        "options": {"drop_reserve": drop_reserve},
        "entities": entities,
        "unmapped": unmapped,
    }


def unique_id_for(domain: str, config: dict[str, Any]) -> str:
    """unique_id the HA KNX integration gives a YAML entity of this config (HA 2026.2)."""

    def ga(key: str) -> str:
        # KNX stringifies a missing group address as "None"
        return str(config.get(key))

    if domain in ("switch", "light", "time", "date", "datetime", "text"):
        return ga("address")
    if domain in ("binary_sensor", "sensor"):
        return ga("state_address")
    if domain == "cover":
        return f"{ga('move_long_address')}_{ga('position_address')}"
    if domain == "scene":
        return f"{ga('address')}_{config.get('scene_number')}"
    if domain == "climate":
        return (
            f"{ga('temperature_address')}_{ga('target_temperature_state_address')}_"
            f"{ga('target_temperature_address')}_{ga('setpoint_shift_address')}"
        )
    if domain == "weather":
        return ga("address_temperature")
    raise ValueError(f"unsupported domain {domain}")
