"""Build the group address digest (see tools/reference/generate.ts) from xknxproject.

Step 0 spike: if this digest equals the one knx2home produces for the same
.knxproj, xknxproject delivers every input the knx2home mapping consumes and
the mapping can be ported on top of it.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from xknxproject import XKNXProj
from xknxproject.models import KNXProject


def canonical_dpt(dpt: dict[str, Any] | None) -> str | None:
    """{'main': 9, 'sub': 1} -> '9.001'."""
    if not dpt:
        return None
    if dpt.get("sub") is None:
        return str(dpt["main"])
    return f"{dpt['main']}.{dpt['sub']:03d}"


def address_sort_key(address: str) -> tuple[int, ...]:
    return tuple(int(part) for part in address.split("/"))


def parse(path: Path, password: str | None = None) -> KNXProject:
    return XKNXProj(path, password=password, language="de-DE").parse()


def digest(project: KNXProject) -> dict[str, Any]:
    cos = project["communication_objects"]
    devices = project["devices"]

    def link(co_id: str) -> dict[str, Any]:
        co = cos[co_id]
        channel = co["channel"]
        text = co["text"]
        if channel:
            text = devices[co["device_address"]]["channels"].get(channel, {}).get("name") or text
        return {
            "device": co["device_address"],
            "text": text or None,
            "function_text": co["function_text"] or None,
            "dpt": canonical_dpt(co["dpts"][0]) if co["dpts"] else None,
            "flags": {
                "read": co["flags"]["read"],
                "write": co["flags"]["write"],
                "transmit": co["flags"]["transmit"],
                "update": co["flags"]["update"],
            },
        }

    group_addresses = []
    for ga in sorted(project["group_addresses"].values(), key=lambda g: address_sort_key(g["address"])):
        links = [link(co_id) for co_id in ga["communication_object_ids"]]
        group_addresses.append(
            {
                "ga_id": ga["identifier"],
                "address": ga["address"],
                "name": ga["name"] or None,
                "dpt": canonical_dpt(ga["dpt"]),
                "links": sorted(links, key=_json_key),
            }
        )
    return {"project": {"name": project["info"]["name"] or None}, "group_addresses": group_addresses}


def _json_key(value: Any) -> str:
    import json

    # same ordering as JSON.stringify(...).localeCompare on the TS side for ASCII keys
    return json.dumps(value, ensure_ascii=False, separators=(",", ":"))
