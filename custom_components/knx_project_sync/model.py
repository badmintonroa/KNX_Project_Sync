"""Shapes of the data the import works with: panel choices, applied state, own YAML.

Plain dicts at runtime (they are stored as JSON and sent to the panel); the
TypedDicts only name their keys.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from typing import Any, NotRequired, TypedDict


class Status(StrEnum):
    """What an import does with an entity."""

    NEW = "new"
    CHANGED = "changed"
    UNCHANGED = "unchanged"
    REMOVED = "removed"  # gone from the project, deleted
    KEPT = "kept"  # gone from the project, kept (option)
    # not written to YAML
    EXCLUDED = "excluded"  # domain not selected in the settings
    DUPLICATE = "duplicate"  # same GA already used by a preferred entity
    INVALID = "invalid"  # rejected by the KNX YAML schema
    CONFLICT = "conflict"  # already defined in the user's own KNX YAML
    DESELECTED = "deselected"  # switched off in the panel
    PENDING = "pending"  # new in the project, can be added in the panel
    EXISTING = "existing"  # marked in the panel as already defined elsewhere


WRITTEN = (Status.NEW, Status.CHANGED, Status.UNCHANGED, Status.KEPT)
SKIPPED = (
    Status.PENDING,
    Status.DESELECTED,
    Status.EXISTING,
    Status.EXCLUDED,
    Status.DUPLICATE,
    Status.INVALID,
    Status.CONFLICT,
)


class Choice(TypedDict, total=False):
    """What was chosen in the panel for one entity. Missing keys: no decision."""

    enabled: bool  # create it; False = deselected
    domain: str  # type change: switch <-> light, text <-> sensor
    name: str  # renamed
    existing: bool  # marked as already defined elsewhere
    adopt: bool  # take the definition over from the own YAML
    config: dict[str, Any]  # definition taken over from the own YAML, used as it is
    addresses: dict[str, str]  # group addresses corrected by hand; "" removes one


# entity key -> choice
type Selection = dict[str, Choice]


class Applied(TypedDict):
    """An entity as the last import wrote it."""

    domain: str
    name: str | None
    config: dict[str, Any]
    unique_id: str


# entity key -> applied entity
type AppliedState = dict[str, Applied]


class OwnEntity(TypedDict):
    """An entity of the user's own KNX YAML."""

    config: dict[str, Any]
    file: NotRequired[str | None]  # from Home Assistant's YAML loader
    line: NotRequired[int | None]


# (domain, unique_id) -> own entity
type OwnEntities = dict[tuple[str, str], OwnEntity]


@dataclass
class Conflict:
    """The entity another one collides with."""

    domain: str
    unique_id: str
    name: str | None
    # unique_id: the same entity in the own YAML; address: one GA is used by an own
    # entity; app: one GA belongs to an entity taken over into the app
    kind: str
    address: str | None = None  # the shared GA (kind address/app)
    file: str | None = None  # own YAML entity: where it is defined
    line: int | None = None

    @property
    def adoptable(self) -> bool:
        """Can be taken over: the definition can be removed from its file."""
        return bool(self.file and self.line)
