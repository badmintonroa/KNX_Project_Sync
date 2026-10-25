"""Step 0: xknxproject provides the project data the knx2home mapping consumes.

Compares the group address digest built from xknxproject with the one the
knx2home reference parser wrote (tests/fixtures/<name>.catalog.json).
Known, documented differences live in <name>.deviations.json.
"""

from __future__ import annotations

from compare import diff
from helpers import FIXTURES, load_json
from xknx_digest import digest, parse


def _declared_deviations(name: str) -> set[tuple[str, str]]:
    path = FIXTURES / f"{name}.deviations.json"
    if not path.exists():
        return set()
    return {(d["address"], d["field"]) for d in load_json(path)["fields"]}


def test_digest_matches_knx2home(fixture_name, passwords):
    expected = load_json(FIXTURES / f"{fixture_name}.catalog.json")
    project = parse(FIXTURES / f"{fixture_name}.knxproj", passwords.get(fixture_name))
    problems = diff(expected, digest(project))

    found = {tuple(p.split(":")[0].split(" ")[:2]) for p in problems}
    assert found == _declared_deviations(fixture_name), "\n".join(problems)


def test_protected_project_needs_password():
    import pytest
    from xknxproject.exceptions import InvalidPasswordException

    with pytest.raises(InvalidPasswordException):
        parse(FIXTURES / "musterhaus_protected.knxproj", None)
    with pytest.raises(InvalidPasswordException):
        parse(FIXTURES / "musterhaus_protected.knxproj", "falsch")
