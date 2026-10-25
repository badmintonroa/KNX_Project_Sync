"""Fixtures shared by all tests."""

from __future__ import annotations

import pytest

from helpers import FIXTURE_NAMES, FIXTURES, load_json


@pytest.fixture(scope="session")
def passwords() -> dict[str, str]:
    return load_json(FIXTURES / "passwords.json")


@pytest.fixture(params=FIXTURE_NAMES)
def fixture_name(request) -> str:
    return request.param
