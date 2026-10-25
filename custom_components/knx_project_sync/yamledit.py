"""Remove an entity from the user's own KNX YAML when it is taken over into the package.

Only block style list items (`- name: …` with the following, deeper indented lines)
are removed, as text, so comments and formatting of the rest of the file stay. The
caller checks the result with Home Assistant's YAML loader and restores the backup if
anything else changed.
"""

from __future__ import annotations

from datetime import datetime
from pathlib import Path
import re
import shutil

ITEM = re.compile(r"^(?P<indent>[ ]*)-(?:[ ]+(?P<rest>\S.*)?)?$")
KEY_LINE = re.compile(r"^(?P<key>[ ]*[^#\s-][^#]*?:)[ ]*(?P<comment>#.*)?$")


class YamlEditError(Exception):
    """The item cannot be removed safely; `reason` is shown to the user."""

    def __init__(self, reason: str) -> None:
        super().__init__(reason)
        self.reason = reason


def _content(line: str) -> bool:
    stripped = line.strip()
    return bool(stripped) and not stripped.startswith("#")


def _indent(line: str) -> int:
    return len(line) - len(line.lstrip(" "))


def remove_list_item(text: str, line: int) -> str:
    """`text` without the list item that starts on 1-based `line`."""
    lines = text.splitlines(keepends=True)
    start = line - 1
    if not 0 <= start < len(lines):
        raise YamlEditError("line_not_found")
    match = ITEM.match(lines[start].rstrip("\r\n"))
    if not match:
        raise YamlEditError("not_a_list_item")
    if (match.group("rest") or "").startswith(("{", "[", "!", "&", "*")):
        raise YamlEditError("flow_style")
    indent = len(match.group("indent"))

    end = start + 1  # one past the last line of the item
    for i in range(start + 1, len(lines)):
        if not _content(lines[i]):
            continue
        if _indent(lines[i]) <= indent:
            break
        end = i + 1
    rest = lines[:start] + lines[end:]

    # last item of its list removed: keep the key, as an empty list
    prev = next((i for i in range(start - 1, -1, -1) if _content(rest[i])), None)
    nxt = next((i for i in range(start, len(rest)) if _content(rest[i])), None)
    sibling = nxt is not None and _indent(rest[nxt]) == indent and ITEM.match(rest[nxt].rstrip("\r\n"))
    key = KEY_LINE.match(rest[prev].rstrip("\r\n")) if prev is not None and not sibling else None
    if key and _indent(rest[prev]) <= indent:
        comment = f"  {key.group('comment')}" if key.group("comment") else ""
        newline = rest[prev][len(rest[prev].rstrip("\r\n")) :] or "\n"
        rest[prev] = f"{key.group('key')} []{comment}{newline}"
    if prev is None and nxt is None:
        # the file was only this list (e.g. `light: !include lights.yaml`)
        rest.append("[]\n")
    return "".join(rest)


def backup_path(path: Path) -> Path:
    stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    return path.with_name(f"{path.name}.knx_project_sync-{stamp}.bak")


def remove_items(config_dir: Path, items: list[tuple[str, int]]) -> dict[Path, Path]:
    """Remove items (file, line) from the user's YAML; returns file -> backup (executor).

    Lines of one file are removed bottom-up, so the line numbers stay valid.
    """
    by_file: dict[Path, list[int]] = {}
    for file, line in items:
        path = Path(file).resolve()
        if not path.is_relative_to(config_dir.resolve()):
            raise YamlEditError("outside_config")
        by_file.setdefault(path, []).append(line)
    new_texts = {}
    for path, lines in by_file.items():
        text = path.read_text(encoding="utf-8")
        for line in sorted(lines, reverse=True):
            text = remove_list_item(text, line)
        new_texts[path] = text
    backups: dict[Path, Path] = {}
    for path, text in new_texts.items():
        backups[path] = backup_path(path)
        shutil.copy2(path, backups[path])
        path.write_text(text, encoding="utf-8")
    return backups


def restore(backups: dict[Path, Path]) -> None:
    for path, backup in backups.items():
        shutil.copy2(backup, path)
