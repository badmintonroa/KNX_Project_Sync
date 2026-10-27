"""Project data the mapping works on, built from xknxproject output.

Mirrors the parts of the knx2home KnxCatalog that buildHaEntities consumes:
`group_addresses` (legacy compat list, sorted by address) and the com object
links of ETS 5.7+/6 projects (`origin: "links"`).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from .dpt import from_xknxproject


@dataclass
class GroupAddress:
    """knx2home GroupAddressCompat."""

    id: str  # ETS id suffix, e.g. "GA-12"
    name: str  # GA name, the address if the GA has no name
    address: str
    dpt: str | None  # knx2home notation, e.g. "9.1"


@dataclass
class Link:
    """knx2home KnxLinkInfo with origin "links" (one com object -> GA link)."""

    ga_id: str
    com_object_id: str
    channel_id: str | None
    device_id: str  # individual address
    com_object: str | None  # function text of the com object
    dpt: str | None  # DPT of the com object, knx2home notation
    flags: dict[str, bool] | None  # ReadFlag/WriteFlag/TransmitFlag/UpdateFlag


@dataclass
class Catalog:
    name: str | None
    group_addresses: list[GroupAddress]
    links: list[Link]
    # individual address -> name of the innermost ETS location (room) holding the device
    device_rooms: dict[str, str] = field(default_factory=dict)
    # GA id -> context of the ETS6 function referencing it (knx2home: GroupAddressRef links,
    # `linksByGa`; the last reference of a GA wins like in the JS Map)
    function_context: dict[str, str] = field(default_factory=dict)


def three_level(raw_address: int) -> str:
    """knx2home writes every group address as main/middle/sub, whatever the ETS address style."""
    return f"{raw_address >> 11}/{(raw_address >> 8) & 0x7}/{raw_address & 0xFF}"


def _flags(flags: dict[str, Any] | None) -> dict[str, bool] | None:
    if not flags:
        return None
    out = {
        key: bool(flags[src])
        for key, src in (
            ("ReadFlag", "read"),
            ("WriteFlag", "write"),
            ("TransmitFlag", "transmit"),
            ("UpdateFlag", "update"),
        )
        if flags.get(src) is not None
    }
    return out or None


def _device_rooms(spaces: dict[str, Any]) -> dict[str, str]:
    rooms: dict[str, str] = {}

    def walk(nodes: dict[str, Any]) -> None:
        for space in nodes.values():
            # inner spaces are visited later and win
            for device in space.get("devices", []):
                rooms[device] = space["name"]
            walk(space.get("spaces", {}))

    walk(spaces)
    return rooms


def catalog_from_xknxproject(project: dict[str, Any]) -> Catalog:
    """Build the catalog from a parsed project (xknxproject KNXProject dict)."""
    gas_by_address = project["group_addresses"]
    # keys are formatted in the project's address style (three level, two level or free)
    id_by_address = {address: ga["identifier"] for address, ga in gas_by_address.items()}

    links: list[Link] = []
    co_dpt: dict[str, str] = {}
    for co_id, co in project["communication_objects"].items():
        device = co["device_address"]
        if co.get("channel"):
            channel_id = f"{device}_{co['channel']}"
        elif co.get("text"):
            # applications without ETS channels: group by object text (like knx2home)
            channel_id = f"{device}_text:{co['text'].strip()}"
        else:
            channel_id = None
        dpt = from_xknxproject(co["dpts"][0]) if co.get("dpts") else None
        if dpt:
            co_dpt[co_id] = dpt
        for address in co["group_address_links"]:
            if address not in id_by_address:
                continue
            links.append(
                Link(
                    ga_id=id_by_address[address],
                    com_object_id=co_id,
                    channel_id=channel_id,
                    device_id=device,
                    com_object=(co.get("function_text") or "").strip() or None,
                    dpt=dpt,
                    flags=_flags(co.get("flags")),
                )
            )

    group_addresses = []
    for ga in sorted(gas_by_address.values(), key=lambda g: g["raw_address"]):
        address = three_level(ga["raw_address"])
        dpt = from_xknxproject(ga.get("dpt"))
        if not dpt:
            # like knx2home: fall back to the DPT of a linked com object
            dpt = next((co_dpt[c] for c in ga.get("communication_object_ids", []) if c in co_dpt), None)
        # knx2home reads trimmed attributes
        name = (ga.get("name") or "").strip() or address
        group_addresses.append(GroupAddress(id=ga["identifier"], name=name, address=address, dpt=dpt))

    return Catalog(
        name=project.get("info", {}).get("name") or None,
        group_addresses=group_addresses,
        links=links,
        device_rooms=_device_rooms(project.get("locations", {})),
        function_context={
            id_by_address[address]: f"{function['name']} ({function['identifier']})"
            for function in project.get("functions", {}).values()
            for address in function.get("group_addresses", {})
            if address in id_by_address
        },
    )
