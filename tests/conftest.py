"""Shared fixtures for the step 0/1 tests (xknxproject spike and manifest contract)."""

from __future__ import annotations

import json
from pathlib import Path
import sys

import pytest

ROOT = Path(__file__).parents[1]
FIXTURES = ROOT / "tests" / "fixtures"

sys.path.insert(0, str(ROOT / "tools" / "spike"))
sys.path.insert(0, str(ROOT / "tools" / "fixtures"))

FIXTURE_NAMES = sorted(p.stem for p in FIXTURES.glob("*.knxproj"))


def load_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


@pytest.fixture(scope="session")
def passwords() -> dict[str, str]:
    return load_json(FIXTURES / "passwords.json")


@pytest.fixture(params=FIXTURE_NAMES)
def fixture_name(request) -> str:
    return request.param
