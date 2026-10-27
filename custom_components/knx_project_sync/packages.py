"""Make Home Assistant load the package file: find or add `homeassistant: packages:`.

The generated KNX entities live in their own file, which Home Assistant only reads
through packages. This module looks at the user's configuration.yaml (as text, tags
kept) and either finds that the file is loaded, finds a packages folder to put it
in, or adds the one line that is missing.

The text functions at the top are plain Python. The `async_` functions below apply
them to the real configuration.yaml: always with a backup, and the result is checked
with Home Assistant's YAML loader, which restores the backup on any problem.
"""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass
import logging
from pathlib import Path, PurePosixPath
import re
from typing import Any

from homeassistant.core import HomeAssistant
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers import issue_registry as ir
import yaml

from . import writer, yamledit
from .const import DOMAIN, ISSUE_PACKAGE_NOT_LOADED, KNX_DOMAIN
from .errors import KnxImportError
from .plan import PlanEntry

_LOGGER = logging.getLogger(__name__)

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


def has_core_key(text: str) -> bool:
    """configuration.yaml has a `homeassistant:` key."""
    return any(_TOP_KEY.match(line) for line in text.splitlines())


def added_line(setup: Setup) -> str:
    """The line `apply` adds for `setup` (without indentation)."""
    if setup.status == ADD:
        return LINE
    if setup.status == INCLUDE:
        return f"knx_project_sync: !include {setup.package_path}"
    raise ValueError(setup.status)


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
                lines.insert(i + 1, f"{indent}{added_line(setup)}{newline}")
                return "".join(lines)
        raise ValueError("packages_not_found")
    raise ValueError(setup.status)


def revert(text: str, line: str, block: bool) -> str:
    """configuration.yaml without the `line` that `apply` added.

    With `block`, `apply` had created the `homeassistant:` key as well; it goes
    too when nothing else was put under it since.
    """
    lines = text.splitlines(keepends=True)
    hits = [i for i, item in enumerate(lines) if item.strip() == line and item[:1].isspace()]
    if len(hits) != 1:
        raise ValueError("line_not_found")
    del lines[hits[0]]
    if not block:
        return "".join(lines)
    top = next((i for i, item in enumerate(lines) if _TOP_KEY.match(item.rstrip("\r\n"))), None)
    if top is None or _TOP_KEY.match(lines[top].rstrip("\r\n")).group("rest"):
        return "".join(lines)
    child = next((item for item in lines[top + 1 :] if item.strip() and not item.lstrip().startswith("#")), None)
    if child is not None and child[:1].isspace():
        return "".join(lines)  # the user added something under homeassistant:
    del lines[top]
    if top == len(lines) and lines and not lines[-1].strip():
        lines.pop()  # the blank line before the block
    return "".join(lines)


# ---------------------------------------------------------------- configuration.yaml


def _config_file(hass: HomeAssistant) -> Path:
    from homeassistant.config import YAML_CONFIG_FILE

    return Path(hass.config.path(YAML_CONFIG_FILE))


async def async_analyze(hass: HomeAssistant, package_path: str) -> Setup:
    """Is `package_path` loaded by configuration.yaml, and what would fix it."""
    config_file = _config_file(hass)

    def _work() -> Setup:
        try:
            text = config_file.read_text(encoding="utf-8")
        except OSError as err:
            return Setup(MANUAL, package_path, str(err))
        return analyze(text, package_path)

    return await hass.async_add_executor_job(_work)


async def async_add_line(hass: HomeAssistant, setup: Setup) -> dict[str, Any]:
    """Add the line `setup` asks for (ADD or INCLUDE) to configuration.yaml.

    Returns what `async_remove_line` needs to take it out again.
    """
    from homeassistant.config import async_hass_config_yaml

    config_file = _config_file(hass)

    def _edit() -> tuple[Path, bool]:
        text = config_file.read_text(encoding="utf-8")
        new_text = apply(text, setup)
        if analyze(new_text, setup.package_path).status != OK:
            raise ValueError("not_loaded_after_edit")
        backup = yamledit.backup_path(config_file)
        backup.write_text(text, encoding="utf-8")
        config_file.write_text(new_text, encoding="utf-8")
        return backup, not has_core_key(text)

    try:
        backup, block = await hass.async_add_executor_job(_edit)
    except (ValueError, OSError) as err:
        raise KnxImportError("packages_manual", error=str(err)) from err
    try:
        await async_hass_config_yaml(hass)
    except HomeAssistantError as err:
        await hass.async_add_executor_job(yamledit.restore, {config_file: backup})
        raise KnxImportError("packages_manual", error=str(err)) from err
    return {"line": added_line(setup), "block": block, "status": setup.status}


async def async_move_file(hass: HomeAssistant, old: Path, new: Path) -> None:
    """Put the package file into the folder packages are loaded from."""

    def _move() -> None:
        if old.exists() and not new.exists():
            new.parent.mkdir(parents=True, exist_ok=True)
            old.replace(new)

    await hass.async_add_executor_job(_move)


async def async_remove_line(hass: HomeAssistant, added: dict[str, Any]) -> None:
    """Take out the line `async_add_line` added, unless other packages need it."""
    from homeassistant.config import async_hass_config_yaml

    config_file = _config_file(hass)
    folder = Path(hass.config.path(DEFAULT_DIR))

    def _edit() -> Path | None:
        if added.get("status") == ADD and folder.is_dir():
            others = [p for p in folder.rglob("*") if p.suffix in (".yaml", ".yml")]
            if others:
                return None  # the folder holds packages of the user now
        text = config_file.read_text(encoding="utf-8")
        new_text = revert(text, added["line"], bool(added.get("block")))
        backup = yamledit.backup_path(config_file)
        backup.write_text(text, encoding="utf-8")
        config_file.write_text(new_text, encoding="utf-8")
        if added.get("status") == ADD and folder.is_dir() and not any(folder.iterdir()):
            folder.rmdir()
        return backup

    try:
        backup = await hass.async_add_executor_job(_edit)
    except (ValueError, OSError) as err:
        _LOGGER.warning("Could not remove the packages line from %s: %s", config_file, err)
        return
    if backup is None:
        return
    try:
        await async_hass_config_yaml(hass)
    except HomeAssistantError as err:
        await hass.async_add_executor_job(yamledit.restore, {config_file: backup})
        _LOGGER.warning("Could not remove the packages line from %s: %s", config_file, err)


async def async_check_loaded(hass: HomeAssistant, written: Iterable[PlanEntry], package: Path) -> None:
    """Repair issue if Home Assistant does not load the package file."""
    from homeassistant.config import async_hass_config_yaml

    written = list(written)
    if not written:
        ir.async_delete_issue(hass, DOMAIN, ISSUE_PACKAGE_NOT_LOADED)
        return
    try:
        config = await async_hass_config_yaml(hass)
    except HomeAssistantError:
        return
    loaded = writer.unique_ids_of_knx_config(config.get(KNX_DOMAIN) or {})
    if any((e.domain, e.unique_id) in loaded for e in written):
        ir.async_delete_issue(hass, DOMAIN, ISSUE_PACKAGE_NOT_LOADED)
        return
    ir.async_create_issue(
        hass,
        DOMAIN,
        ISSUE_PACKAGE_NOT_LOADED,
        is_fixable=True,
        severity=ir.IssueSeverity.WARNING,
        translation_key=ISSUE_PACKAGE_NOT_LOADED,
        translation_placeholders={"path": str(package)},
    )
