"""The committed fixtures are exactly what tools/fixtures/build_fixtures.py produces."""

from __future__ import annotations

import pytest

import build_fixtures
from conftest import FIXTURES


@pytest.mark.parametrize("name", sorted(build_fixtures.FIXTURES))
def test_fixture_is_generated(name):
    project = build_fixtures.FIXTURES[name]()
    if project.password:
        pytest.skip("AES encrypted archives contain a random salt")
    assert (FIXTURES / f"{name}.knxproj").read_bytes() == build_fixtures.build(project)


def test_passwords_file():
    import json

    assert json.loads((FIXTURES / "passwords.json").read_text()) == build_fixtures.PASSWORDS
