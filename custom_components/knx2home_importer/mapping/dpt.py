"""DPT normalization (port of knx2home src/lib/knx/utils.ts)."""

from __future__ import annotations

import re

_PREFIX = re.compile(r"^dpst?-")
_WS = re.compile(r"\s+")
_PARTS = re.compile(r"(\d+)(?:-(\d+))?", re.ASCII)


def _parts(dpt: str | None) -> tuple[int, int | None] | None:
    if not dpt:
        return None
    key = dpt.strip().lower()
    if not key:
        return None
    s = _PREFIX.sub("", key, count=1).replace("_", "-")
    s = _WS.sub("", s).replace(".", "-")
    m = _PARTS.fullmatch(s)
    if not m:
        return None
    return int(m.group(1)), int(m.group(2)) if m.group(2) is not None else None


def to_dot(dpt: str | None) -> str | None:
    """'DPST-9-1' / '9.1' -> '9.001', '5' -> '5', '5.0' -> '5'."""
    parts = _parts(dpt)
    if parts is None:
        return None
    main, sub = parts
    if sub is None or sub == 0:
        return str(main)
    return f"{main}.{sub:03d}"


def to_hyphen(dpt: str | None) -> str | None:
    """'DPST-9-1' / '9.001' -> '9-1'."""
    parts = _parts(dpt)
    if parts is None:
        return None
    main, sub = parts
    return str(main) if sub is None else f"{main}-{sub}"


def from_xknxproject(dpt: dict | None) -> str | None:
    """xknxproject DPTType -> knx2home catalog notation ('1.1', '5')."""
    if not dpt:
        return None
    if dpt.get("sub") is None:
        return str(dpt["main"])
    return f"{dpt['main']}.{dpt['sub']}"
