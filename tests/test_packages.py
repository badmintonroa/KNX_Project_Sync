"""Find or add `homeassistant: packages:` so that the package file is loaded."""

from __future__ import annotations

import pytest

from custom_components.knx_project_sync.packages import (
    ADD,
    INCLUDE,
    MANUAL,
    MOVE,
    OK,
    added_line,
    analyze,
    apply,
    revert,
)

PACKAGE = "packages/knx_project_sync.yaml"


def test_missing_homeassistant_key():
    text = "default_config:\n\nknx:\n  switch: []\n"
    setup = analyze(text, PACKAGE)
    assert setup.status == ADD
    new = apply(text, setup)
    assert new.endswith("\nhomeassistant:\n  packages: !include_dir_named packages\n")
    assert analyze(new, PACKAGE).status == OK


def test_homeassistant_without_packages():
    text = "homeassistant:\n    name: Zuhause  # Name\n    customize: !include customize.yaml\nknx: {}\n"
    setup = analyze(text, PACKAGE)
    assert setup.status == ADD
    new = apply(text, setup)
    assert new.splitlines()[1] == "    packages: !include_dir_named packages"
    assert "customize: !include customize.yaml" in new
    assert analyze(new, PACKAGE).status == OK


def test_already_loaded():
    assert analyze("homeassistant:\n  packages: !include_dir_named packages\n", PACKAGE).status == OK
    assert analyze("homeassistant:\n  packages: !include_dir_named packages/\n", PACKAGE).status == OK


def test_other_packages_folder_moves_the_file():
    setup = analyze("homeassistant:\n  packages: !include_dir_named integrations\n", PACKAGE)
    assert (setup.status, setup.package_path) == (MOVE, "integrations/knx_project_sync.yaml")


def test_packages_listed_one_by_one():
    text = "homeassistant:\n  packages:\n    heizung: !include heizung.yaml\nautomation: []\n"
    setup = analyze(text, PACKAGE)
    assert setup.status == INCLUDE
    new = apply(text, setup)
    assert "    knx_project_sync: !include packages/knx_project_sync.yaml\n" in new
    assert analyze(new, PACKAGE).status == OK


def test_custom_package_path_goes_into_the_new_folder():
    setup = analyze("knx: {}\n", "knx/generated.yaml")
    assert (setup.status, setup.package_path) == (ADD, "packages/generated.yaml")


@pytest.mark.parametrize(
    "text",
    [
        "homeassistant: !include core.yaml\n",
        "homeassistant:\n  packages: !include_dir_merge_named packages\n",
        "homeassistant: {name: x\n",
    ],
)
def test_manual(text):
    assert analyze(text, PACKAGE).status == MANUAL


@pytest.mark.parametrize(
    "text",
    [
        "default_config:\n\nknx:\n  switch: []\n",
        "default_config:\n",
        "",
        "homeassistant:\n    name: Zuhause  # Name\n    customize: !include customize.yaml\nknx: {}\n",
        "homeassistant:\n  packages:\n    eigenes: !include eigenes.yaml\n",
    ],
)
def test_revert_restores_the_file(text):
    setup = analyze(text, PACKAGE)
    new = apply(text, setup)
    block = "homeassistant:" not in text
    assert revert(new, added_line(setup), block) == text


def test_revert_keeps_what_the_user_added_since():
    text = "default_config:\n"
    setup = analyze(text, PACKAGE)
    new = apply(text, setup) + "  name: Zuhause\n"
    assert revert(new, added_line(setup), True) == "default_config:\n\nhomeassistant:\n  name: Zuhause\n"


def test_revert_line_gone():
    with pytest.raises(ValueError, match="line_not_found"):
        revert("default_config:\n", "packages: !include_dir_named packages", True)
