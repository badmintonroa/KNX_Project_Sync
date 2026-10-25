"""One version everywhere, with a changelog entry."""

from __future__ import annotations

import json
import re

from awesomeversion import AwesomeVersion

from custom_components.knx_project_sync.const import VERSION
from helpers import ROOT, load_json


def test_versions_match():
    manifest = load_json(ROOT / "custom_components/knx_project_sync/manifest.json")
    package = json.loads((ROOT / "frontend/package.json").read_text(encoding="utf-8"))
    assert manifest["version"] == VERSION == package["version"]


def test_version_is_semver():
    # 0.1.0-beta.1: what HACS shows as release tag v0.1.0-beta.1
    assert re.fullmatch(r"\d+\.\d+\.\d+(-(alpha|beta|rc)\.\d+)?", VERSION)
    assert AwesomeVersion(VERSION).valid


def test_changelog_has_the_version():
    changelog = (ROOT / "CHANGELOG.md").read_text(encoding="utf-8")
    assert f"\n## {VERSION}\n" in changelog
