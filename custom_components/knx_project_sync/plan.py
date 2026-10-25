"""Import plan: what an import changes compared to the previous one.

Pure logic without Home Assistant imports (see docs/import.md):

    manifest (new project)  ─┐
    previous import state   ─┼─> ImportPlan: per entity new / changed / unchanged /
    own YAML unique_ids     ─┤    removed / kept / skipped (+ reason) and the
    selection (panel)       ─┤    unique_id migrations for the entity registry
    options + validator     ─┘

The selection maps entity key -> {"enabled": bool, "domain": str, "name": str}.
Keys without a decision are written when they were part of the previous import (or
on the first import); otherwise they are only offered (`pending`).
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass, field
from typing import Any

from .mapping.manifest import DOMAINS, unique_id_for

NEW = "new"
CHANGED = "changed"
UNCHANGED = "unchanged"
REMOVED = "removed"
KEPT = "kept"
# not written to YAML
EXCLUDED = "excluded"  # domain not selected
DUPLICATE = "duplicate"  # same GA already used by a preferred entity
INVALID = "invalid"  # rejected by the KNX YAML schema
CONFLICT = "conflict"  # unique_id already defined in the user's own KNX YAML
DESELECTED = "deselected"  # switched off in the panel
PENDING = "pending"  # new in the project, can be added in the panel
EXISTING = "existing"  # marked in the panel as already defined elsewhere

WRITTEN = (NEW, CHANGED, UNCHANGED, KEPT)
SKIPPED = (PENDING, DESELECTED, EXISTING, EXCLUDED, DUPLICATE, INVALID, CONFLICT)

# entity types whose unique_id is the same GA field, so they can collide with each other
SAME_GA_DOMAINS = {"switch": "light", "light": "switch"}

# domains an entity can be switched to in the panel (on/off entities only)
SIMPLE_ON_OFF_FIELDS = {"name", "address", "state_address"}

Validator = Callable[[str, dict[str, Any]], str | None]


@dataclass
class PlanEntry:
    key: str
    domain: str
    name: str | None
    config: dict[str, Any]
    unique_id: str
    status: str
    reason: str | None = None
    detected_domain: str | None = None  # domain from the project, before a type change
    previous_key: str | None = None
    previous_domain: str | None = None
    previous_config: dict[str, Any] | None = None
    previous_unique_id: str | None = None
    # own YAML entity this one collides with: {"domain", "unique_id", "name", "file", "line"}
    conflict_with: dict[str, Any] | None = None
    adopt: bool = False  # taken over from the own YAML on apply


@dataclass
class ImportPlan:
    project: str | None
    entries: list[PlanEntry] = field(default_factory=list)
    unmapped: list[dict[str, Any]] = field(default_factory=list)
    # unique_ids defined in the user's own KNX YAML: their registry entries are never touched
    foreign_unique_ids: set[tuple[str, str]] = field(default_factory=set)

    @property
    def adoptions(self) -> list[PlanEntry]:
        """Entities moved from the user's own YAML into the package."""
        return [e for e in self.written if e.adopt]

    def by_status(self, *statuses: str) -> list[PlanEntry]:
        return [e for e in self.entries if e.status in statuses]

    @property
    def written(self) -> list[PlanEntry]:
        return self.by_status(*WRITTEN)

    @property
    def migrations(self) -> list[tuple[str, str, str]]:
        """(domain, old unique_id, new unique_id) for the entity registry."""
        return [
            (e.domain, e.previous_unique_id, e.unique_id)
            for e in self.written
            if e.previous_unique_id
            and e.previous_domain == e.domain
            and e.previous_unique_id != e.unique_id
            and (e.domain, e.previous_unique_id) not in self.foreign_unique_ids
        ]

    @property
    def removed_unique_ids(self) -> list[tuple[str, str]]:
        written = {(e.domain, e.unique_id) for e in self.written} | self.foreign_unique_ids
        gone = [(e.domain, e.unique_id) for e in self.by_status(REMOVED)]
        # deselected in the panel, or written under another domain now (switch <-> light)
        gone += [
            (e.previous_domain, e.previous_unique_id)
            for e in self.entries
            if e.previous_unique_id
            and (e.status in (DESELECTED, EXISTING) or (e.status in WRITTEN and e.previous_domain != e.domain))
        ]
        return list(dict.fromkeys(uid for uid in gone if uid not in written))

    @property
    def has_changes(self) -> bool:
        return any(e.status in (NEW, CHANGED, REMOVED) for e in self.entries)

    @property
    def has_pending(self) -> bool:
        return any(e.status == PENDING for e in self.entries)

    def summary(self) -> dict[str, int]:
        counts = {status: 0 for status in (*WRITTEN, REMOVED, *SKIPPED)}
        for e in self.entries:
            counts[e.status] += 1
        counts["unmapped"] = len(self.unmapped)
        return counts

    def state(self) -> dict[str, dict[str, Any]]:
        """What is stored as `applied` after the plan was applied."""
        return {
            e.key: {"domain": e.domain, "name": e.name, "config": e.config, "unique_id": e.unique_id}
            for e in self.written
        }

    def yaml_data(self) -> dict[str, list[dict[str, Any]]]:
        """`knx:` mapping of the package file."""
        data: dict[str, list[dict[str, Any]]] = {}
        for domain in DOMAINS:
            items = [e.config for e in self.written if e.domain == domain]
            if items:
                data[domain] = items
        return data


def build_plan(
    manifest: dict[str, Any],
    previous: dict[str, dict[str, Any]],
    *,
    domains: list[str],
    keep_removed: bool,
    foreign_unique_ids: set[tuple[str, str]] = frozenset(),
    validate: Validator | None = None,
    selection: dict[str, dict[str, Any]] | None = None,
    include_new: bool = True,
    foreign_entities: dict[tuple[str, str], dict[str, Any]] | None = None,
) -> ImportPlan:
    """Compare the manifest with the previous import.

    `previous` maps entity key -> {"domain", "name", "config", "unique_id"} of
    the last applied import. `include_new` writes new entities without a decision
    in `selection` (first import); otherwise they become `pending`.
    `foreign_entities` holds config, file and line of the own YAML entities by
    (domain, unique_id); a conflict with one of them can be adopted (`adopt` choice).
    """
    selection = selection or {}
    foreign_entities = foreign_entities or {}
    foreign_unique_ids = set(foreign_unique_ids) | set(foreign_entities)
    plan = ImportPlan(
        project=manifest.get("project", {}).get("name"),
        unmapped=list(manifest.get("unmapped", [])),
        foreign_unique_ids=foreign_unique_ids,
    )
    entities = manifest["entities"]

    # knx2home emits a switch next to a pattern based light on the same GA; keep the light
    light_addresses = {e["config"].get("address") for e in entities if e["domain"] == "light"}
    used: set[tuple[str, str]] = set()
    candidates: list[PlanEntry] = []
    for e in entities:
        choice = selection.get(e["key"], {})
        domain, name, config = apply_choice(e["domain"], e["config"], choice)
        entry = PlanEntry(
            key=e["key"],
            domain=domain,
            name=name,
            config=config,
            unique_id=unique_id_for(domain, config),
            status=NEW,
            detected_domain=e["domain"],
        )
        clash = _own_yaml_clash(domain, entry.unique_id, foreign_unique_ids)
        if clash:
            info = foreign_entities.get(clash, {})
            entry.conflict_with = {
                "domain": clash[0],
                "unique_id": clash[1],
                "name": (info.get("config") or {}).get("name"),
                "file": info.get("file"),
                "line": info.get("line"),
            }
            if choice.get("adopt") and info.get("file") and info.get("line"):
                # take the user's own definition over as it is
                entry.domain, entry.config, entry.adopt = clash[0], dict(info["config"]), True
                entry.name = entry.config.get("name")
                domain, config, clash = entry.domain, entry.config, None
        if domain not in domains:
            entry.status = EXCLUDED
        elif choice.get("enabled") is False:
            entry.status = DESELECTED
        elif choice.get("existing"):
            entry.status = EXISTING
        elif (
            e["domain"] == "switch"
            and domain == "switch"
            and config.get("address") in light_addresses
            and "light" in domains
        ):
            entry.status, entry.reason = DUPLICATE, "light"
        elif (domain, entry.unique_id) in used:
            entry.status, entry.reason = DUPLICATE, "unique_id"
        elif validate and (error := validate(domain, config)):
            entry.status, entry.reason = INVALID, error
        elif clash:
            entry.status, entry.reason = CONFLICT, "own_yaml"
        if entry.status == NEW:
            used.add((entry.domain, entry.unique_id))
        candidates.append(entry)

    # match with the previous import: by key, then by unique_id (GA recreated in ETS)
    unmatched = dict(previous)
    by_uid = {(p["domain"], p["unique_id"]): k for k, p in previous.items()}
    for entry in candidates:
        # invalid ones too: a typo must not delete the entity from the registry
        if entry.status not in (NEW, DESELECTED, EXISTING, INVALID):
            continue
        prev_key = entry.key if entry.key in unmatched else None
        if prev_key is None:
            k = by_uid.get((entry.domain, entry.unique_id))
            prev_key = k if k in unmatched else None
        if prev_key is None:
            continue
        prev = unmatched.pop(prev_key)
        entry.previous_key = prev_key
        entry.previous_domain = prev["domain"]
        entry.previous_config = prev["config"]
        entry.previous_unique_id = prev["unique_id"]
        if entry.status == NEW:
            same = prev["config"] == entry.config and prev_key == entry.key and prev["domain"] == entry.domain
            entry.status = UNCHANGED if same else CHANGED

    for entry in candidates:
        decided = "enabled" in selection.get(entry.key, {}) or entry.adopt
        if entry.status == NEW and not include_new and not decided:
            entry.status = PENDING
            used.discard((entry.domain, entry.unique_id))

    for prev_key, prev in unmatched.items():
        uid_taken = (prev["domain"], prev["unique_id"]) in used
        status = KEPT if keep_removed and not uid_taken and prev["domain"] in domains else REMOVED
        candidates.append(
            PlanEntry(
                key=prev_key,
                domain=prev["domain"],
                name=prev.get("name"),
                config=prev["config"],
                unique_id=prev["unique_id"],
                status=status,
                previous_key=prev_key,
                previous_domain=prev["domain"],
                previous_config=prev["config"],
                previous_unique_id=prev["unique_id"],
            )
        )
    plan.entries = candidates
    return plan


def domain_choices(domain: str, config: dict[str, Any]) -> list[str]:
    """Domains the panel offers for an entity (first = detected)."""
    if domain == "switch":
        return ["switch", "light"]
    if domain == "light" and "address" in config and set(config) <= SIMPLE_ON_OFF_FIELDS:
        return ["light", "switch"]
    return [domain]


def _own_yaml_clash(domain: str, uid: str, foreign: set[tuple[str, str]]) -> tuple[str, str] | None:
    """Own YAML entity on the same GA: same type, or switch vs. light."""
    for candidate in (domain, SAME_GA_DOMAINS.get(domain)):
        if candidate and (candidate, uid) in foreign:
            return (candidate, uid)
    return None


# group address fields the panel offers per entity type (HA KNX YAML)
ADDRESS_FIELDS: dict[str, tuple[str, ...]] = {
    "switch": ("address", "state_address"),
    "light": (
        "address",
        "state_address",
        "brightness_address",
        "brightness_state_address",
        "color_temperature_address",
        "color_temperature_state_address",
        "color_address",
        "color_state_address",
    ),
    "binary_sensor": ("state_address",),
    "sensor": ("state_address",),
    "time": ("address", "state_address"),
    "date": ("address", "state_address"),
    "datetime": ("address", "state_address"),
    "cover": (
        "move_long_address",
        "move_short_address",
        "stop_address",
        "position_address",
        "position_state_address",
        "angle_address",
        "angle_state_address",
    ),
    "scene": ("address",),
    "climate": (
        "temperature_address",
        "target_temperature_address",
        "target_temperature_state_address",
        "setpoint_shift_address",
        "setpoint_shift_state_address",
        "operation_mode_address",
        "operation_mode_state_address",
        "on_off_address",
        "on_off_state_address",
    ),
    "weather": (
        "address_temperature",
        "address_brightness_south",
        "address_brightness_east",
        "address_brightness_west",
        "address_brightness_north",
        "address_wind_speed",
        "address_rain_alarm",
        "address_frost_alarm",
        "address_wind_alarm",
        "address_day_night",
        "address_air_pressure",
        "address_humidity",
    ),
}


def is_address_field(field: str) -> bool:
    return field == "address" or field.endswith("_address") or field.startswith("address_")


def address_fields(domain: str, config: dict[str, Any]) -> list[str]:
    """Address fields of an entity: the ones it has, then the others its type supports."""
    present = [k for k in config if is_address_field(k)]
    return present + [f for f in ADDRESS_FIELDS.get(domain, ()) if f not in present]


def apply_choice(domain: str, config: dict[str, Any], choice: dict[str, Any]) -> tuple[str, str | None, dict[str, Any]]:
    """Domain, name and YAML config of an entity after type change, rename and address edits of the panel."""
    if choice.get("config"):
        # definition taken over from the own YAML: used as it is
        config = dict(choice["config"])
        domain = choice.get("domain") or domain
    else:
        config = dict(config)
        target = choice.get("domain") or domain
        if target != domain and target in domain_choices(domain, config):
            # switch-only options (invert, respond_to_read, ...) do not exist for lights
            config = {k: v for k, v in config.items() if k in SIMPLE_ON_OFF_FIELDS}
            domain = target
    allowed = set(address_fields(domain, config))
    for key, address in (choice.get("addresses") or {}).items():
        if key not in allowed:
            continue
        if address := (address or "").strip():
            config[key] = address  # corrected by hand
        else:
            config.pop(key, None)  # wrong address removed
    if name := (choice.get("name") or "").strip():
        config["name"] = name
    return domain, config.get("name"), config
