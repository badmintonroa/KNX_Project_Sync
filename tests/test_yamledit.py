"""Removing a taken-over entity from the user's own YAML."""

from __future__ import annotations

import pytest
import yaml

from custom_components.knx_project_sync.yamledit import YamlEditError, remove_list_item

CONFIG = """\
homeassistant:
  packages: !include_dir_named packages

knx:
  switch:
    # Wohnzimmer
    - name: Handgeschrieben
      address: "1/0/1"   # Kanal A
      state_address:
        - "1/0/2"
        - "1/0/3"

    - name: Zweiter
      address: "1/0/9"
  light:  # Lichter
  - name: Flur
    address: 1/3/1
  sensor: [{name: x, state_address: 3/0/1}]
"""


def test_remove_item_keeps_the_rest():
    text = remove_list_item(CONFIG, 7)
    assert "Handgeschrieben" not in text
    assert "# Wohnzimmer" in text and "# Kanal A" not in text
    knx = yaml.safe_load(text.replace("!include_dir_named", ""))["knx"]
    assert knx["switch"] == [{"name": "Zweiter", "address": "1/0/9"}]
    assert knx["light"] == [{"name": "Flur", "address": "1/3/1"}]


def test_last_item_leaves_empty_list():
    text = remove_list_item(CONFIG, 16)
    assert "  light: []  # Lichter\n" in text
    knx = yaml.safe_load(text.replace("!include_dir_named", ""))["knx"]
    assert knx["light"] == []
    assert len(knx["switch"]) == 2
    both = remove_list_item(remove_list_item(CONFIG, 13), 7)
    assert yaml.safe_load(both.replace("!include_dir_named", ""))["knx"]["switch"] == []


def test_included_list_file():
    assert yaml.safe_load(remove_list_item("- name: Flur\n  address: 1/3/1\n", 1)) == []
    text = remove_list_item("- name: Flur\n  address: 1/3/1\n- name: B\n  address: 1/3/2\n", 3)
    assert yaml.safe_load(text) == [{"name": "Flur", "address": "1/3/1"}]


@pytest.mark.parametrize(("line", "reason"), [(18, "not_a_list_item"), (99, "line_not_found"), (5, "not_a_list_item")])
def test_refuses(line, reason):
    with pytest.raises(YamlEditError) as err:
        remove_list_item(CONFIG, line)
    assert err.value.reason == reason


def test_refuses_flow_item():
    with pytest.raises(YamlEditError) as err:
        remove_list_item("light:\n  - {name: a, address: 1/1/1}\n", 2)
    assert err.value.reason == "flow_style"
