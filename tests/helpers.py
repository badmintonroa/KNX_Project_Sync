"""Shared test helpers (importable as `helpers`, tests/ is on the python path)."""

from __future__ import annotations

import json
from pathlib import Path
import sys
from typing import Any
import uuid

ROOT = Path(__file__).parents[1]
FIXTURES = ROOT / "tests" / "fixtures"

sys.path.insert(0, str(ROOT / "tools" / "fixtures"))

FIXTURE_NAMES = sorted(p.stem for p in FIXTURES.glob("*.knxproj"))


def parse(path: Path, password: str | None = None) -> dict[str, Any]:
    """xknxproject output of a project file, as the integration reads it."""
    from xknxproject import XKNXProj

    return XKNXProj(path, password=password, language="de-DE").parse()


def load_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def file_id(fixture: str) -> str:
    """Upload id (the file selector expects a UUID) standing for a fixture."""
    return str(uuid.uuid5(uuid.NAMESPACE_URL, fixture))
