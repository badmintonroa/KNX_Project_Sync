"""Make Home Assistant load the package file: find or add `homeassistant: packages:`.

The generated KNX entities live in their own file, which Home Assistant only reads
through packages. This module looks at the user's configuration.yaml (as text, tags
kept) and either finds that the file is loaded, finds a packages folder to put it
in, or adds the one line that is missing. Callers back the file up and verify the
result with Home Assistant's YAML loader.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import PurePosixPath
import re
from typing import Any

import yaml

LINE = "packages: !include_dir_named packages"
DEFAULT_DIR = "packages"

OK = "ok"  # the package file is loaded
MOVE = "move"  # packages come from another folder: put the file there
ADD = "add"  # no packages yet: add the line
INCLUDE = "include"  # packages listed one by one: add ours
MANUAL = "manual"  # cannot be changed safely


@dataclass
class Setup:
    status: str
    package_path: str  # where the package file has to be (relative to the config folder)
    detail: str | None = None


class _Tag:
    def __init__(self, tag: str, value: Any) -> None:
        self.tag, self.value = tag, value


class _Loader(yaml.SafeLoader):
    """Keeps HA's tags (!include_dir_named …) instead of failing on them."""


def _tagged(loader: yaml.Loader, suffix: str, node: yaml.Node) -> _Tag:
    if isinstance(node, yaml.ScalarNode):
        return _Tag("!" + suffix, loader.construct_scalar(node))
    return _Tag("!" + suffix, None)


_Loader.add_multi_constructor("!", _tagged)

_TOP_KEY = re.compile(r"^homeassistant:[ \t]*(?P<rest>[^#\n]*?)[ \t]*(#.*)?$")
_PACKAGES_KEY = re.compile(r"^(?P<indent>[ \t]+)packages:[ \t]*(?P<rest>[^#\n]*?)[ \t]*(#.*)?$")


def _norm(path: str) -> str:
    return str(PurePosixPath(path.strip().strip("'\"").rstrip("/")))


def analyze(text: str, package_path: str) -> Setup:
    """What is needed so that `package_path` is loaded as a package."""
    try:
        config = yaml.load(text, Loader=_Loader) or {}
    except yaml.YAMLError as err:
        return Setup(MANUAL, package_path, f"yaml: {err}")
    if not isinstance(config, dict):
        return Setup(MANUAL, package_path, "not_a_mapping")
    core = config.get("homeassistant")
    file = PurePosixPath(package_path)
    if core is None:
        return Setup(ADD, package_path if str(file.parent) == DEFAULT_DIR else f"{DEFAULT_DIR}/{file.name}")
    if isinstance(core, _Tag) or not isinstance(core, dict):
        return Setup(MANUAL, package_path, "homeassistant_include")
    packages = core.get("packages")
    if packages is None:
        return Setup(ADD, package_path if str(file.parent) == DEFAULT_DIR else f"{DEFAULT_DIR}/{file.name}")
    if isinstance(packages, _Tag):
        if packages.tag in ("!include_dir_named", "!include_dir_merge_named") and packages.value:
            folder = _norm(packages.value)
            if packages.tag == "!include_dir_named":
                # every file of the folder (and its subfolders) is a package
                if str(file.parent) == folder or str(file.parent).startswith(folder + "/"):
                    return Setup(OK, package_path)
                return Setup(MOVE, f"{folder}/{file.name}")
            # merge_named expects files holding {package_name: config}
            return Setup(MANUAL, package_path, "include_dir_merge_named")
        return Setup(MANUAL, package_path, packages.tag)
    if isinstance(packages, dict):
        for value in packages.values():
            if isinstance(value, _Tag) and value.tag == "!include" and _norm(value.value or "") == _norm(package_path):
                return Setup(OK, package_path)
        return Setup(INCLUDE, package_path)
    return Setup(MANUAL, package_path, "packages_format")


def _child_indent(lines: list[str], start: int, default: str = "  ") -> str:
    for line in lines[start + 1 :]:
        if line.strip() and not line.lstrip().startswith("#"):
            indent = line[: len(line) - len(line.lstrip())]
            return indent or default
    return default


def apply(text: str, setup: Setup) -> str:
    """configuration.yaml with the change `setup` asks for (ADD or INCLUDE)."""
    lines = text.splitlines(keepends=True)
    newline = "\r\n" if "\r\n" in text else "\n"
    top = next((i for i, line in enumerate(lines) if _TOP_KEY.match(line.rstrip("\r\n"))), None)
    if setup.status == ADD:
        if top is None:
            if lines and not lines[-1].endswith(("\n", "\r\n")):
                lines[-1] += newline
            block = f"{newline if lines else ''}homeassistant:{newline}  {LINE}{newline}"
            return "".join(lines) + block
        if _TOP_KEY.match(lines[top].rstrip("\r\n")).group("rest"):
            raise ValueError("homeassistant_inline")
        indent = _child_indent(lines, top)
        lines.insert(top + 1, f"{indent}{LINE}{newline}")
        return "".join(lines)
    if setup.status == INCLUDE:
        if top is None:
            raise ValueError("homeassistant_missing")
        for i in range(top + 1, len(lines)):
            line = lines[i].rstrip("\r\n")
            if line and not line[0].isspace() and not line.startswith("#"):
                break  # next top level key
            if (match := _PACKAGES_KEY.match(line)) and not match.group("rest"):
                indent = _child_indent(lines, i, match.group("indent") * 2)
                lines.insert(i + 1, f"{indent}knx_project_sync: !include {setup.package_path}{newline}")
                return "".join(lines)
        raise ValueError("packages_not_found")
    raise ValueError(setup.status)
