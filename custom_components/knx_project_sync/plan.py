"""Import plan: what an import changes compared to the previous one.

Pure logic without Home Assistant imports (see docs/import.md):

    manifest (new project)  ─┐
    previous import state   ─┼─> ImportPlan: a status per entity (model.Status, with
    own YAML entities       ─┤    a reason for skipped ones), conflicts with the own
    selection (panel)       ─┤    YAML and the unique_id migrations for the registry
    options + validator     ─┘

Entities without a decision in the selection are written when they were part of
the previous import (or on the first import); otherwise they are only offered
(`pending`).
"""

from __future__ import annotations

from collections.abc import Callable, Set as AbstractSet
from dataclasses import dataclass, field
from typing import Any

from .mapping.manifest import HA_DOMAINS, unique_id_for
from .model import SKIPPED, WRITTEN, AppliedState, Choice, Conflict, OwnEntities, Selection, Status

# entity types whose unique_id is the same GA field, so they can collide with each other
SAME_GA_DOMAINS = {"switch": "light", "light": "switch"}

# domains an entity can be switched to in the panel (on/off entities only)
SIMPLE_ON_OFF_FIELDS = {"name", "address", "state_address"}
# DPT 16 (14 byte text); knx2home makes sensors of it, Home Assistant has a text entity
TEXT_TYPES = {"string", "latin_1"}

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
    # how the previous import wrote it (matched by key, or by unique_id after a re-import)
    previous_domain: str | None = None
    previous_unique_id: str | None = None
    conflict_with: Conflict | None = None
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
        gone = [(e.domain, e.unique_id) for e in self.by_status(Status.REMOVED)]
        # deselected in the panel, or written under another domain now (switch <-> light)
        gone += [
            (e.previous_domain, e.previous_unique_id)
            for e in self.entries
            if e.previous_unique_id
            and (
                e.status in (Status.DESELECTED, Status.EXISTING)
                or (e.status in WRITTEN and e.previous_domain != e.domain)
            )
        ]
        return list(dict.fromkeys(uid for uid in gone if uid not in written))

    @property
    def has_changes(self) -> bool:
        return any(e.status in (Status.NEW, Status.CHANGED, Status.REMOVED) for e in self.entries)

    def summary(self) -> dict[str, int]:
        counts = {status: 0 for status in (*WRITTEN, Status.REMOVED, *SKIPPED)}
        for e in self.entries:
            counts[e.status] += 1
        counts["unmapped"] = len(self.unmapped)
        return counts

    def state(self) -> AppliedState:
        """What is stored as `applied` after the plan was applied."""
        return {
            e.key: {"domain": e.domain, "name": e.name, "config": e.config, "unique_id": e.unique_id}
            for e in self.written
        }

    def yaml_data(self) -> dict[str, list[dict[str, Any]]]:
        """`knx:` mapping of the package file."""
        data: dict[str, list[dict[str, Any]]] = {}
        for domain in HA_DOMAINS:
            items = [e.config for e in self.written if e.domain == domain]
            if items:
                data[domain] = items
        return data


def build_plan(
    manifest: dict[str, Any],
    previous: AppliedState,
    *,
    domains: list[str],
    keep_removed: bool,
    validate: Validator | None = None,
    selection: Selection | None = None,
    include_new: bool = True,
    foreign_entities: OwnEntities | None = None,
) -> ImportPlan:
    """Compare the manifest with the previous import.

    `include_new` writes new entities without a decision in `selection` (first
    import); otherwise they become `pending`. A conflict with one of the
    `foreign_entities` (the user's own KNX YAML) can be adopted (`adopt` choice).
    """
    planner = _Planner(
        previous=previous,
        domains=domains,
        keep_removed=keep_removed,
        validate=validate,
        selection=selection or {},
        include_new=include_new,
        own=foreign_entities or {},
        light_addresses={e["config"].get("address") for e in manifest["entities"] if e["domain"] == "light"},
    )
    entries = [planner.candidate(e) for e in manifest["entities"]]
    planner.mark_weather_duplicates(entries)
    planner.mark_app_duplicates(entries)
    unmatched = planner.match_previous(entries)
    planner.mark_pending(entries)
    entries += planner.gone(unmatched)
    return ImportPlan(
        project=manifest.get("project", {}).get("name"),
        entries=entries,
        unmapped=list(manifest.get("unmapped", [])),
        foreign_unique_ids=set(planner.own),
    )


@dataclass
class _Planner:
    """The steps of `build_plan`, in the order they run."""

    previous: AppliedState
    domains: list[str]
    keep_removed: bool
    validate: Validator | None
    selection: Selection
    include_new: bool
    own: OwnEntities  # the user's own KNX YAML
    # GAs of detected lights: knx2home also emits a switch on them, the light wins
    light_addresses: set[str | None]
    # (domain, unique_id) written so far: a second entity with it is a duplicate
    used: set[tuple[str, str]] = field(default_factory=set)
    adopted: set[tuple[str, str]] = field(default_factory=set)  # own entities taken over
    own_addresses: dict[str, tuple[str, str]] = field(init=False)  # GA -> own entity using it
    previous_uids: set[tuple[str, str]] = field(init=False)  # (domain, unique_id) of the last import

    def __post_init__(self) -> None:
        self.previous_uids = {(p["domain"], p["unique_id"]) for p in self.previous.values()}
        self.own_addresses = {}
        for uid, info in self.own.items():
            for address in _addresses(info.get("config") or {}):
                self.own_addresses.setdefault(address, uid)

    # 1. one entry per detected entity, with the panel choices applied

    def candidate(self, detected: dict[str, Any]) -> PlanEntry:
        choice = self._choice(detected)
        domain, name, config = apply_choice(detected["domain"], detected["config"], choice)
        entry = PlanEntry(
            key=detected["key"],
            domain=domain,
            name=name,
            config=config,
            unique_id=unique_id_for(domain, config),
            status=Status.NEW,
            detected_domain=detected["domain"],
        )
        blocking = self._conflict(entry, choice)
        entry.status, entry.reason = self._status(entry, choice, blocking)
        if entry.status == Status.NEW and self._decided(entry):
            self.used.add((entry.domain, entry.unique_id))
        return entry

    def _decided(self, entry: PlanEntry) -> bool:
        """Is the entity written (or kept) anyway, i.e. not just offered in the panel (`pending`)?

        Only such entities keep their unique_id and GAs from other entities.
        """
        return (
            self.include_new
            or entry.adopt
            or "enabled" in self.selection.get(entry.key, {})
            or entry.key in self.previous
            or (entry.domain, entry.unique_id) in self.previous_uids
        )

    def _choice(self, detected: dict[str, Any]) -> Choice:
        """The panel choice, with texts as text entities unless decided otherwise."""
        choice: Choice = self.selection.get(detected["key"], {})
        if (
            "domain" not in choice
            and not choice.get("config")
            and _is_text(detected["domain"], detected["config"])
            # imported as a sensor before: stays one, so it keeps its entity_id
            and self.previous.get(detected["key"], {}).get("domain", "text") == "text"
        ):
            return {**choice, "domain": "text"}
        return choice

    def _conflict(self, entry: PlanEntry, choice: Choice) -> Conflict | None:
        """Set `conflict_with` if the own YAML has this entity or one of its GAs.

        Taken over (`adopt`), the entry becomes the own definition. Returns the
        conflict if it keeps the entity from being written.
        """
        uid = _own_yaml_clash(entry.domain, entry.unique_id, self.own.keys())
        address = None
        if not uid and (hit := _shared_address(entry.config, self.own_addresses)):
            # one of its GAs is used by another own entity (e.g. the temperature of a climate)
            uid, address = hit
        if not uid:
            return None
        info = self.own.get(uid) or {"config": {}}
        conflict = entry.conflict_with = Conflict(
            domain=uid[0],
            unique_id=uid[1],
            name=info["config"].get("name"),
            kind="address" if address else "unique_id",
            address=address,
            file=info.get("file"),
            line=info.get("line"),
        )
        if choice.get("adopt") and conflict.adoptable and uid not in self.adopted:
            # take the user's own definition over as it is
            self.adopted.add(uid)
            entry.domain, entry.config, entry.adopt = uid[0], dict(info["config"]), True
            entry.name = entry.config.get("name")
            entry.unique_id = unique_id_for(entry.domain, entry.config)
            return None
        if address and choice.get("enabled") is True:
            return None  # only a shared GA: created anyway on request
        return conflict

    def _status(self, entry: PlanEntry, choice: Choice, conflict: Conflict | None) -> tuple[Status, str | None]:
        """The first reason not to write the entity, else NEW."""
        if entry.domain not in self.domains:
            return Status.EXCLUDED, None
        if choice.get("enabled") is False:
            return Status.DESELECTED, None
        if choice.get("existing"):
            return Status.EXISTING, None
        if (
            entry.detected_domain == "switch"
            and entry.domain == "switch"
            and entry.config.get("address") in self.light_addresses
            and "light" in self.domains
        ):
            return Status.DUPLICATE, "light"
        if (entry.domain, entry.unique_id) in self.used:
            return Status.DUPLICATE, "unique_id"
        if self.validate and (error := self.validate(entry.domain, entry.config)):
            return Status.INVALID, error
        if conflict:
            return Status.CONFLICT, "own_yaml" if conflict.kind == "unique_id" else "ga_in_use"
        return Status.NEW, None

    # 2. a weather station owns its GAs

    def mark_weather_duplicates(self, entries: list[PlanEntry]) -> None:
        """knx2home also emits sensors and switches on the GAs of a weather station, the weather wins."""
        if "weather" not in self.domains:
            return
        owners: dict[str, PlanEntry] = {}
        for entry in entries:
            if entry.status == Status.NEW and entry.domain == "weather" and self._decided(entry):
                for address in _addresses(entry.config):
                    owners.setdefault(address, entry)
        for entry in entries:
            if entry.status != Status.NEW or entry.domain not in SINGLE_GA_DOMAINS:
                continue
            if entry.key in self.previous or (entry.domain, entry.unique_id) in self.previous_uids:
                continue  # imported before: stays, so it keeps its entity_id and history
            addresses = _addresses(entry.config)
            if not addresses or not all(a in owners for a in addresses):
                continue
            owner = owners[addresses[0]]
            entry.status, entry.reason = Status.DUPLICATE, "ga_in_use"
            entry.conflict_with = Conflict(
                domain=owner.domain, unique_id=owner.unique_id, name=owner.name, kind="app", address=addresses[0]
            )
            self.used.discard((entry.domain, entry.unique_id))

    # 3. entities with a taken-over or own definition own their GAs

    def mark_app_duplicates(self, entries: list[PlanEntry]) -> None:
        """A detected entity on a GA of such an entity is a duplicate (unless switched on)."""
        owners: dict[str, PlanEntry] = {}
        for entry in entries:
            if (
                entry.status == Status.NEW
                and (entry.adopt or self.selection.get(entry.key, {}).get("config"))
                and self._decided(entry)
            ):
                for address in _addresses(entry.config):
                    owners.setdefault(address, entry)
        for entry in entries:
            is_owner = any(entry is owner for owner in owners.values())
            if entry.status != Status.NEW or is_owner or self.selection.get(entry.key, {}).get("enabled") is True:
                continue
            address = next((a for a in _addresses(entry.config) if a in owners), None)
            if address is None:
                continue
            owner = owners[address]
            entry.status, entry.reason = Status.DUPLICATE, "ga_in_use"
            entry.conflict_with = Conflict(
                domain=owner.domain, unique_id=owner.unique_id, name=owner.name, kind="app", address=address
            )
            self.used.discard((entry.domain, entry.unique_id))

    # 4. match with the previous import: by key, then by unique_id (GA recreated in ETS)

    def match_previous(self, entries: list[PlanEntry]) -> AppliedState:
        """Set previous_*, NEW -> CHANGED/UNCHANGED; returns the previous entities left over."""
        unmatched = dict(self.previous)
        by_uid = {(p["domain"], p["unique_id"]): k for k, p in self.previous.items()}
        candidates = [
            e
            for e in entries
            # invalid ones too: a typo must not delete the entity from the registry
            if e.status in (Status.NEW, Status.DESELECTED, Status.EXISTING, Status.INVALID)
        ]
        # same key first: an entry must not take the previous entity of another one by unique_id
        for by_key in (True, False):
            for entry in candidates:
                if entry.previous_unique_id:
                    continue
                if by_key:
                    key = entry.key if entry.key in unmatched else None
                else:
                    key = by_uid.get((entry.domain, entry.unique_id))
                if key not in unmatched:
                    continue
                prev = unmatched.pop(key)
                entry.previous_domain = prev["domain"]
                entry.previous_unique_id = prev["unique_id"]
                if entry.status == Status.NEW:
                    same = prev["config"] == entry.config and key == entry.key and prev["domain"] == entry.domain
                    entry.status = Status.UNCHANGED if same else Status.CHANGED
        return unmatched

    # 5. after the first import, new entities without a decision are only offered

    def mark_pending(self, entries: list[PlanEntry]) -> None:
        if self.include_new:
            return
        for entry in entries:
            decided = "enabled" in self.selection.get(entry.key, {}) or entry.adopt
            if entry.status == Status.NEW and not decided:
                entry.status = Status.PENDING
                self.used.discard((entry.domain, entry.unique_id))

    # 5. previous entities that are no longer in the project

    def gone(self, unmatched: AppliedState) -> list[PlanEntry]:
        entries = []
        for key, prev in unmatched.items():
            uid_taken = (prev["domain"], prev["unique_id"]) in self.used
            keep = self.keep_removed and not uid_taken and prev["domain"] in self.domains
            entries.append(
                PlanEntry(
                    key=key,
                    domain=prev["domain"],
                    name=prev.get("name"),
                    config=prev["config"],
                    unique_id=prev["unique_id"],
                    status=Status.KEPT if keep else Status.REMOVED,
                    previous_domain=prev["domain"],
                    previous_unique_id=prev["unique_id"],
                )
            )
        return entries


def domain_choices(domain: str, config: dict[str, Any]) -> list[str]:
    """Domains the panel offers for an entity (first = detected)."""
    if domain == "switch":
        return ["switch", "light"]
    if domain == "light" and "address" in config and set(config) <= SIMPLE_ON_OFF_FIELDS:
        return ["light", "switch"]
    if _is_text(domain, config):
        return [domain, "text" if domain == "sensor" else "sensor"]
    return [domain]


def _is_text(domain: str, config: dict[str, Any]) -> bool:
    return domain in ("sensor", "text") and config.get("type", "latin_1" if domain == "text" else None) in TEXT_TYPES


def _retype(domain: str, target: str, config: dict[str, Any]) -> dict[str, Any]:
    """Config of the same GAs as another entity type."""
    if target == "text":
        address = config.get("state_address") or config.get("address")
        return {
            k: v
            for k, v in {
                "name": config.get("name"),
                "address": address,
                "state_address": config.get("state_address") or address,
                "type": config.get("type"),
            }.items()
            if v
        }
    if target == "sensor" and domain == "text":
        state = config.get("state_address") or config.get("address")
        return {
            k: v
            for k, v in {
                "name": config.get("name"),
                "state_address": state,
                "type": config.get("type") or "latin_1",
            }.items()
            if v
        }
    # switch <-> light: switch-only options (invert, respond_to_read, ...) do not exist for lights
    return {k: v for k, v in config.items() if k in SIMPLE_ON_OFF_FIELDS}


# detected as one entity per GA, which a weather station can already cover
SINGLE_GA_DOMAINS = ("switch", "binary_sensor", "sensor")


def _addresses(config: dict[str, Any]) -> list[str]:
    """All group addresses of a config (raw YAML may hold lists)."""
    out: list[str] = []
    for key, value in config.items():
        if not is_address_field(key):
            continue
        for item in value if isinstance(value, list) else [value]:
            if isinstance(item, str) and item:
                out.append(item)
    return out


def _shared_address(
    config: dict[str, Any], foreign_addresses: dict[str, tuple[str, str]]
) -> tuple[tuple[str, str], str] | None:
    """(own entity, address) of the first GA of `config` the own YAML already uses."""
    for address in _addresses(config):
        if address in foreign_addresses:
            return foreign_addresses[address], address
    return None


def _own_yaml_clash(domain: str, uid: str, foreign: AbstractSet[tuple[str, str]]) -> tuple[str, str] | None:
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
    "text": ("address", "state_address"),
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


def apply_choice(domain: str, config: dict[str, Any], choice: Choice) -> tuple[str, str | None, dict[str, Any]]:
    """Domain, name and YAML config of an entity after type change, rename and address edits of the panel."""
    if choice.get("config"):
        # definition taken over from the own YAML: used as it is
        config = dict(choice["config"])
        domain = choice.get("domain") or domain
    else:
        config = dict(config)
        target = choice.get("domain") or domain
        if target != domain and target in domain_choices(domain, config):
            config = _retype(domain, target, config)
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
