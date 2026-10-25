"""Import plan: what an import changes compared to the previous one.

Pure logic without Home Assistant imports (see docs/import.md):

    manifest (new project)  ─┐
    previous import state   ─┼─> ImportPlan: per entity new / changed / unchanged /
    own YAML unique_ids     ─┤    removed / kept / skipped (+ reason) and the
    options + validator     ─┘    unique_id migrations for the entity registry
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

WRITTEN = (NEW, CHANGED, UNCHANGED, KEPT)
SKIPPED = (EXCLUDED, DUPLICATE, INVALID, CONFLICT)

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
    previous_key: str | None = None
    previous_config: dict[str, Any] | None = None
    previous_unique_id: str | None = None


@dataclass
class ImportPlan:
    project: str | None
    entries: list[PlanEntry] = field(default_factory=list)
    unmapped: list[dict[str, Any]] = field(default_factory=list)
    # unique_ids defined in the user's own KNX YAML: their registry entries are never touched
    foreign_unique_ids: set[tuple[str, str]] = field(default_factory=set)

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
            and e.previous_unique_id != e.unique_id
            and (e.domain, e.previous_unique_id) not in self.foreign_unique_ids
        ]

    @property
    def removed_unique_ids(self) -> list[tuple[str, str]]:
        written = {(e.domain, e.unique_id) for e in self.written} | self.foreign_unique_ids
        return [(e.domain, e.unique_id) for e in self.by_status(REMOVED) if (e.domain, e.unique_id) not in written]

    @property
    def has_changes(self) -> bool:
        return any(e.status in (NEW, CHANGED, REMOVED) for e in self.entries)

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
) -> ImportPlan:
    """Compare the manifest with the previous import.

    `previous` maps entity key -> {"domain", "name", "config", "unique_id"} of
    the last applied import.
    """
    plan = ImportPlan(
        project=manifest.get("project", {}).get("name"),
        unmapped=list(manifest.get("unmapped", [])),
        foreign_unique_ids=set(foreign_unique_ids),
    )
    entities = manifest["entities"]

    # knx2home emits a switch next to a pattern based light on the same GA; keep the light
    light_addresses = {e["config"].get("address") for e in entities if e["domain"] == "light"}
    used: set[tuple[str, str]] = set()
    candidates: list[PlanEntry] = []
    for e in entities:
        entry = PlanEntry(
            key=e["key"],
            domain=e["domain"],
            name=e.get("name"),
            config=e["config"],
            unique_id=unique_id_for(e["domain"], e["config"]),
            status=NEW,
        )
        if e["domain"] not in domains:
            entry.status = EXCLUDED
        elif e["domain"] == "switch" and e["config"].get("address") in light_addresses and "light" in domains:
            entry.status, entry.reason = DUPLICATE, "light"
        elif (e["domain"], entry.unique_id) in used:
            entry.status, entry.reason = DUPLICATE, "unique_id"
        elif validate and (error := validate(e["domain"], e["config"])):
            entry.status, entry.reason = INVALID, error
        elif (e["domain"], entry.unique_id) in foreign_unique_ids:
            entry.status, entry.reason = CONFLICT, "own_yaml"
        if entry.status == NEW:
            used.add((entry.domain, entry.unique_id))
        candidates.append(entry)

    # match with the previous import: by key, then by unique_id (GA recreated in ETS)
    unmatched = dict(previous)
    by_uid = {(p["domain"], p["unique_id"]): k for k, p in previous.items()}
    for entry in candidates:
        if entry.status != NEW:
            continue
        prev_key = entry.key if entry.key in unmatched else None
        if prev_key is None:
            k = by_uid.get((entry.domain, entry.unique_id))
            prev_key = k if k in unmatched else None
        if prev_key is None:
            continue
        prev = unmatched.pop(prev_key)
        entry.previous_key = prev_key
        entry.previous_config = prev["config"]
        entry.previous_unique_id = prev["unique_id"]
        entry.status = UNCHANGED if prev["config"] == entry.config and prev_key == entry.key else CHANGED

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
                previous_config=prev["config"],
                previous_unique_id=prev["unique_id"],
            )
        )
    plan.entries = candidates
    return plan
