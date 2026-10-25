"""Compare xknxproject with the knx2home catalog digest for every fixture.

Usage: python tools/spike/compare.py [fixtures_dir]
Exit code 1 if any fixture differs.
"""

from __future__ import annotations

import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent))
from xknx_digest import digest, parse  # noqa: E402


def diff(expected: dict, actual: dict) -> list[str]:
    problems: list[str] = []
    if expected["project"] != actual["project"]:
        problems.append(f"project: {expected['project']} != {actual['project']}")
    exp = {ga["address"]: ga for ga in expected["group_addresses"]}
    act = {ga["address"]: ga for ga in actual["group_addresses"]}
    for address in sorted(exp.keys() - act.keys()):
        problems.append(f"{address}: only in knx2home")
    for address in sorted(act.keys() - exp.keys()):
        problems.append(f"{address}: only in xknxproject")
    for address in sorted(exp.keys() & act.keys()):
        for field in ("ga_id", "name", "dpt", "links"):
            if exp[address][field] != act[address][field]:
                problems.append(f"{address} {field}: {exp[address][field]!r} != {act[address][field]!r}")
    return problems


def main() -> int:
    fixtures = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(__file__).parents[2] / "tests" / "fixtures"
    passwords_file = fixtures / "passwords.json"
    passwords = json.loads(passwords_file.read_text()) if passwords_file.exists() else {}
    failed = False
    for knxproj in sorted(fixtures.glob("*.knxproj")):
        expected = json.loads(knxproj.with_suffix(".catalog.json").read_text(encoding="utf-8"))
        actual = digest(parse(knxproj, passwords.get(knxproj.stem)))
        problems = diff(expected, actual)
        status = "identisch" if not problems else f"{len(problems)} Abweichungen"
        print(f"{knxproj.stem}: {len(actual['group_addresses'])} GAs, {status}")
        for problem in problems:
            print(f"  - {problem}")
        failed |= bool(problems)
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
