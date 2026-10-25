"""Port vs. knx2home on real ETS projects (the test projects of xknxproject).

The projects are GPL-2.0 and therefore not part of this repository. CI clones
xknxproject at a pinned commit, writes the knx2home manifests with
tools/reference and sets REAL_PROJECTS_DIR (see .github/workflows/tests.yaml):

    REAL_PROJECTS_DIR=/path/with/*.knxproj+*.manifest.json+passwords.json pytest tests/test_real_projects.py
"""

from __future__ import annotations

import json
import os
from pathlib import Path

import pytest
from xknxproject import XKNXProj

from custom_components.knx_project_sync.mapping import build_ha_entities, build_manifest, catalog_from_xknxproject

REAL = Path(os.environ["REAL_PROJECTS_DIR"]) if os.environ.get("REAL_PROJECTS_DIR") else None
pytestmark = pytest.mark.skipif(REAL is None, reason="REAL_PROJECTS_DIR not set")

PASSWORDS = {"xknx_test_project": "test", "test_project-ets4": "test", "smart_linking": "test"}

# deliberate differences, see docs/port-notes.md
EXTRA_IN_PORT = {
    # GAs without DPT whose com object lists several DPT-9 subtypes: knx2home cannot
    # parse the DPT list and drops them, the port uses the first one (2byte_float sensor)
    "xknx_test_project": {"sensor:GA-9", "sensor:GA-10", "sensor:GA-12"},
}


def _names() -> list[str]:
    if REAL is None:
        return []
    return sorted(p.stem for p in REAL.glob("*.knxproj") if p.with_suffix(".manifest.json").exists())


@pytest.mark.parametrize("name", _names())
def test_real_project(name: str) -> None:
    expected = json.loads((REAL / f"{name}.manifest.json").read_text(encoding="utf-8"))
    project = XKNXProj(REAL / f"{name}.knxproj", password=PASSWORDS.get(name), language="de-DE").parse()
    catalog = catalog_from_xknxproject(project)
    manifest = build_manifest(catalog, build_ha_entities(catalog), expected["generator"])

    want = {e["key"]: e for e in expected["entities"]}
    got = {e["key"]: e for e in manifest["entities"]}
    extra = EXTRA_IN_PORT.get(name, set())
    assert got.keys() - want.keys() == extra
    assert {k: got[k] for k in want} == want
    extra_addresses = {got[k]["config"]["state_address"] for k in extra}
    # `dpt` of unmapped GAs is informational; the port fills it from the com object when the GA has none
    assert [(u["address"], u["name"]) for u in expected["unmapped"] if u["address"] not in extra_addresses] == [
        (u["address"], u["name"]) for u in manifest["unmapped"]
    ]
