"""Aggregate heuristics (port of knx2home src/lib/knx/aggregate.ts).

Aggregates are plain dicts so that key order and key counts behave like the
JavaScript objects they mirror (knx2home compares `Object.keys(...).length`).
`consumed` holds the GA ids an aggregate uses.

`contexts` is knx2home's `linksByGa` reduced to what the code reads from it:
GA id -> context of the GroupAddressRef link (ETS6 functions). The flags of
those links are always undefined, so `isReadFlag` is always false.
See docs/port-notes.md.
"""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

from .catalog import GroupAddress, Link
from .dpt import to_dot, to_hyphen
from .heuristics import guess_entity_type, is_la, is_scene_like_name, is_status_name, parse_address
from .jsre import collapse_ws, js, replace_all, replace_first, test

Agg = dict[str, Any]

_STATE_WORD = js(r"\bstate\b", True)


def _flag(link: Link, key: str) -> bool | None:
    return None if link.flags is None else link.flags.get(key)


def _is_state_object(link: Link) -> bool:
    return _flag(link, "WriteFlag") is False and (
        _flag(link, "ReadFlag") is True or _flag(link, "TransmitFlag") is True
    )


def _is_command_object(link: Link) -> bool:
    return _flag(link, "WriteFlag") is True


def _group(items, key: Callable) -> dict[str, list]:
    out: dict[str, list] = {}
    for item in items:
        k = key(item)
        if k:
            out.setdefault(k, []).append(item)
    return out


# ====================== LIGHT AGGREGATES ======================


def _light(name: str) -> Agg:
    return {"name": name, "consumed": set()}


def build_la_light_aggregates(gas: list[GroupAddress]) -> list[Agg]:
    by_base: dict[str, Agg] = {}
    for ga in gas:
        if not is_la(ga.name):
            continue
        parts = parse_address(ga.address)
        if not parts:
            continue
        base = (ga.name or ga.address).strip()
        agg = by_base.setdefault(base, _light(base))
        _, middle, _ = parts
        dpt = to_hyphen(ga.dpt)
        if dpt == "1-1":
            if middle == 1:
                agg["on_off"] = ga.address
            if middle == 5:
                agg["on_off_state"] = ga.address
            agg["consumed"].add(ga.id)
        elif dpt == "3-7":
            if middle == 2:
                agg["dimming"] = ga.address
            agg["consumed"].add(ga.id)
        elif dpt == "5-1":
            if middle == 3:
                agg["brightness"] = ga.address
            if middle == 4:
                agg["brightness_state"] = ga.address
            agg["consumed"].add(ga.id)
    return [a for a in by_base.values() if a.get("on_off") or a.get("brightness") or a.get("dimming")]


def build_address_light_aggregates(gas: list[GroupAddress]) -> list[Agg]:
    groups: dict[int, Agg] = {}
    for ga in gas:
        parts = parse_address(ga.address)
        if not parts:
            continue
        main, middle, sub = parts
        if main != 1 or middle in (0, 6, 7):
            continue
        dpt = to_hyphen(ga.dpt)
        g = groups.get(sub)
        if g is None:
            g = _light(ga.name or ga.address)
            groups[sub] = g
        if not g.get("_name_chosen") and middle in (1, 3) and ga.name:
            g["name"] = ga.name
            g["_name_chosen"] = True
        if middle == 1 and dpt == "1-1":
            g["on_off"] = ga.address
        elif middle == 5 and dpt == "1-1":
            g["on_off_state"] = ga.address
        elif middle == 2 and dpt == "3-7":
            g["dimming"] = ga.address
        elif middle == 3 and dpt in ("5-1", "5"):
            g["brightness"] = ga.address
        elif middle == 4 and dpt in ("5-1", "5"):
            g["brightness_state"] = ga.address
        else:
            continue
        g["consumed"].add(ga.id)
    return [a for a in groups.values() if a.get("brightness") or a.get("dimming")]


_STATUS_OR_STATE = js(r"\bstatus\b|\bstate\b", True)


def build_linked_light_aggregates(gas: list[GroupAddress], contexts: dict[str, str] | None) -> list[Agg]:
    """GAs referenced by the same ETS6 function form one light."""
    if not contexts:
        return []
    by_ctx: dict[str, list[GroupAddress]] = {}
    for g in gas:
        ctx = contexts.get(g.id)
        if ctx:
            by_ctx.setdefault(ctx, []).append(g)

    def is_status(g: GroupAddress) -> bool:
        return test(_STATUS_OR_STATE, g.name or "")

    out = []
    for ctx, items in by_ctx.items():
        one_bits = [g for g in items if to_hyphen(g.dpt) == "1-1"]
        dimming = [g for g in items if to_hyphen(g.dpt) == "3-7"]
        bright = [g for g in items if to_hyphen(g.dpt) in ("5-1", "5")]
        if not one_bits and not dimming and not bright:
            continue
        agg = _light(items[0].name if items[0].name is not None else ctx)
        if one_bits:
            cmd = next((g for g in one_bits if not is_status(g)), one_bits[0])
            st = next((g for g in one_bits if is_status(g)), None)
            agg["on_off"] = cmd.address
            agg["consumed"].add(cmd.id)
            if st:
                agg["on_off_state"] = st.address
                agg["consumed"].add(st.id)
        if dimming:
            agg["dimming"] = dimming[0].address
            agg["consumed"].add(dimming[0].id)
        if bright:
            st = next((g for g in bright if is_status(g)), None)
            cmd = next((g for g in bright if not is_status(g)), bright[0])
            agg["brightness"] = cmd.address
            agg["consumed"].add(cmd.id)
            if st:
                agg["brightness_state"] = st.address
                agg["consumed"].add(st.id)
        if agg.get("on_off") or agg.get("brightness") or agg.get("dimming"):
            out.append(agg)
    return out


_NAME_SUFFIX = js(r"\s+(s|d|w|status|aan|uit|on|off)$", True)
_SWD_SUFFIX = js(r"\s+(s|d|w)$", True)
_STATUS_ANY = js(r"status", True)


def build_name_based_light_aggregates(gas: list[GroupAddress]) -> list[Agg]:
    by_base: dict[str, tuple[Agg, list[GroupAddress]]] = {}
    for ga in gas:
        base = replace_first(_NAME_SUFFIX, ga.name or "").strip()
        if not base:
            continue
        if base not in by_base:
            by_base[base] = (_light(base), [])
        by_base[base][1].append(ga)

    results = []
    for agg, candidates in by_base.values():
        for ga in candidates:
            m = _SWD_SUFFIX.search(ga.name or "")
            suffix = m.group(1).lower() if m else None
            dpt = to_hyphen(ga.dpt)
            if suffix == "s" and dpt == "1-1":
                agg["on_off"] = ga.address
                agg["consumed"].add(ga.id)
            elif suffix == "d" and dpt == "3-7":
                agg["dimming"] = ga.address
                agg["consumed"].add(ga.id)
            elif suffix == "w" and dpt == "5-1":
                agg["brightness"] = ga.address
                agg["consumed"].add(ga.id)
            if not suffix and test(_STATUS_ANY, ga.name or ""):
                if dpt == "1-1":
                    agg["on_off_state"] = ga.address
                    agg["consumed"].add(ga.id)
                elif dpt == "5-1":
                    agg["brightness_state"] = ga.address
                    agg["consumed"].add(ga.id)
        if agg.get("on_off") or agg.get("brightness"):
            results.append(agg)
    return results


_LIGHT_NAME_STRIP = js(r"\b(ein\/aus|an\/aus|on\/off|schalten|switch|switching)\b", True)
_RE_COVER_WORDS = js(
    r"\b(rolluik|jaloezie|lamel|screen|blind|shutter|cover|gordijn|raam|schuifdeur|schuifdeuren|deur|door)\b",
    True,
)
_RE_STATUS2 = js(r"\b(status|state|feedback|actual|istwert)\b", True)


def build_channel_light_aggregates(gas: list[GroupAddress], links: list[Link]) -> list[Agg]:
    if not links:
        return []
    ga_by_id = {g.id: g for g in gas}
    by_channel = _group(links, lambda l: l.channel_id)

    def dpt_of(l: Link) -> str:
        g = ga_by_id.get(l.ga_id)
        return to_hyphen(g.dpt if g else None) or ""

    def name_of(l: Link) -> str:
        g = ga_by_id.get(l.ga_id)
        return g.name if g else ""

    def is_state_link(l: Link) -> bool:
        return _is_state_object(l) if l.flags is not None else test(_RE_STATUS2, name_of(l))

    out = []
    for ch_links in by_channel.values():

        def is_sending(l: Link) -> bool:
            return next(x for x in ch_links if x.com_object_id == l.com_object_id) is l

        dpts = {dpt_of(l) for l in ch_links}
        if any(d in dpts for d in ("1-7", "1-8", "1-10", "9-1", "18-1")):
            continue
        if any(test(_RE_COVER_WORDS, name_of(l)) for l in ch_links):
            continue
        brightness = [l for l in ch_links if dpt_of(l) == "5-1"]
        brightness_cmd = next((l for l in brightness if not is_state_link(l)), None)
        if not brightness_cmd:
            continue
        switch_cmd = next(
            (
                l
                for l in ch_links
                if dpt_of(l) == "1-1"
                and not is_state_link(l)
                and _flag(l, "TransmitFlag") is not True
                and is_sending(l)
            ),
            None,
        )
        if not switch_cmd or (switch_cmd.flags is not None and not _is_command_object(switch_cmd)):
            continue
        switch_ga = ga_by_id[switch_cmd.ga_id]
        name = collapse_ws(replace_all(_LIGHT_NAME_STRIP, switch_ga.name or ""))
        agg: Agg = {
            "name": name or switch_ga.name or switch_ga.address,
            "on_off": switch_ga.address,
            "brightness": ga_by_id[brightness_cmd.ga_id].address,
            "consumed": {switch_cmd.ga_id, brightness_cmd.ga_id},
        }
        on_off_state = next(
            (l for l in ch_links if dpt_of(l).startswith("1-") and l.ga_id != switch_cmd.ga_id and is_state_link(l)),
            None,
        )
        if on_off_state:
            agg["on_off_state"] = ga_by_id[on_off_state.ga_id].address
            agg["consumed"].add(on_off_state.ga_id)
        brightness_state = next((l for l in brightness if l.ga_id != brightness_cmd.ga_id and is_state_link(l)), None)
        if brightness_state:
            agg["brightness_state"] = ga_by_id[brightness_state.ga_id].address
            agg["consumed"].add(brightness_state.ga_id)
        dimming = next((l for l in ch_links if dpt_of(l) == "3-7"), None)
        if dimming:
            agg["dimming"] = ga_by_id[dimming.ga_id].address
            agg["consumed"].add(dimming.ga_id)
        out.append(agg)
    return out


# ====================== SWITCH AGGREGATES ======================

_NAME_STRIP = js(r"\b(status|aan\/?uit|aan|uit|schakel|switch|cmd|command)\b", True)


def _normalize_base_name(name: str) -> str:
    raw = name or ""
    n = collapse_ws(replace_all(_NAME_STRIP, raw.lower().strip()))
    return n if n else raw.lower().strip()


def build_switch_aggregates(
    gas: list[GroupAddress], links: list[Link], contexts: dict[str, str] | None = None
) -> list[Agg]:
    by_base: dict[str, Agg] = {}
    for ga in gas:
        if to_hyphen(ga.dpt) != "1-1":
            continue
        if is_scene_like_name(ga.name or ""):
            continue
        parts = parse_address(ga.address)
        if parts and parts[0] == 1 and parts[1] == 7:
            continue
        base = _normalize_base_name(ga.name or ga.address)
        agg = by_base.setdefault(base, {"name": ga.name or ga.address, "consumed": set()})
        if is_status_name(ga.name):
            agg.setdefault("state_address", ga.address)
        elif "address" not in agg:
            agg["address"] = ga.address
            agg["name"] = ga.name or agg["name"]
        agg["consumed"].add(ga.id)
    result = [a for a in by_base.values() if a.get("address")]
    if links:
        _pair_switch_states_from_links(result, gas, links)
    if not contexts:
        return result

    # a switch without state: a 1-bit GA of the same ETS6 function
    for agg in result:
        if agg.get("state_address") or not agg.get("address"):
            continue
        cmd = next((g for g in gas if g.address == agg["address"]), None)
        cmd_ctx = contexts.get(cmd.id) if cmd else None
        if not cmd_ctx:
            continue
        candidates = [g for g in gas if g.id != cmd.id and to_hyphen(g.dpt) == "1-1" and contexts.get(g.id) == cmd_ctx]
        chosen = next((g for g in candidates if is_status_name(g.name)), None) or (
            candidates[0] if candidates else None
        )
        if chosen:
            agg["state_address"] = chosen.address
            agg["consumed"].add(chosen.id)
    return result


def _pair_switch_states_from_links(switches: list[Agg], gas: list[GroupAddress], links: list[Link]) -> None:
    ga_by_id = {g.id: g for g in gas}
    ga_id_by_address = {g.address: g.id for g in gas}
    by_com_object = _group(links, lambda l: l.com_object_id)
    by_channel = _group(links, lambda l: l.channel_id)
    by_ga = _group(links, lambda l: l.ga_id)
    command_ids = {ga_id_by_address.get(s["address"]) for s in switches if s.get("address")} - {None}

    def state_ga(ga_id: str) -> GroupAddress | None:
        g = ga_by_id.get(ga_id)
        if not g or ga_id in command_ids:
            return None
        dpt = to_hyphen(g.dpt)
        if dpt == "1-11":
            return g
        if dpt and dpt.startswith("1-") and (is_status_name(g.name) or test(_STATE_WORD, g.name or "")):
            return g
        return None

    for agg in switches:
        if agg.get("state_address") or not agg.get("address"):
            continue
        cmd_id = ga_id_by_address.get(agg["address"])
        if not cmd_id:
            continue
        # only objects that send the command; listening objects (e.g. central off) are skipped
        sending = [l for l in by_ga.get(cmd_id, []) if by_com_object[l.com_object_id][0].ga_id == cmd_id]
        chosen = None
        for cmd_link in sending:
            for l in by_com_object.get(cmd_link.com_object_id, [])[1:]:
                chosen = state_ga(l.ga_id)
                if chosen:
                    break
            if chosen:
                break
        if not chosen:
            for cmd_link in sending:
                if not cmd_link.channel_id:
                    continue
                ch_links = by_channel.get(cmd_link.channel_id, [])
                switching = {l.com_object_id for l in ch_links if l.ga_id in command_ids}
                if len(switching) != 1:
                    continue
                for l in ch_links:
                    if l.com_object_id == cmd_link.com_object_id:
                        continue
                    chosen = state_ga(l.ga_id)
                    if chosen:
                        break
                if chosen:
                    break
        if chosen:
            agg["state_address"] = chosen.address
            agg["consumed"].add(chosen.id)


# ====================== CLIMATE ======================

_TARGET_TEMP = js(r"\b(soll|sollwert|setpoint|target|basissollwert)\b", True)
_CLIMATE_NAME_STRIP = js(
    r"\b(soll|sollwert|basissollwert|setpoint|target|ist|istwert|actual|temperatur|temperature)\b", True
)
_STATUS_WORD = js(r"\bstatus\b", True)


def _climate_name(ga: GroupAddress | None) -> str | None:
    if not ga or not ga.name:
        return None
    stripped = collapse_ws(replace_all(_CLIMATE_NAME_STRIP, ga.name))
    return stripped or ga.name


def build_climate_aggregates(gas: list[GroupAddress], links: list[Link]) -> list[Agg]:
    if not links:
        return []
    ga_by_id = {g.id: g for g in gas}
    by_channel = _group(links, lambda l: l.channel_id)
    by_device = _group(links, lambda l: l.device_id)

    def is_status(g: GroupAddress) -> bool:
        return test(_STATUS_WORD, g.name or "") or test(_STATE_WORD, g.name or "")

    def heat_cool_state_of(device_id: str | None) -> GroupAddress | None:
        heat_cool = [l for l in by_device.get(device_id or "", []) if to_hyphen(_dpt(ga_by_id.get(l.ga_id))) == "1-100"]
        states = [l for l in heat_cool if _is_state_object(l)]
        if not states:
            states = [l for l in heat_cool if is_status(ga_by_id[l.ga_id])]
        ids = list(dict.fromkeys(l.ga_id for l in states))
        return ga_by_id.get(ids[0]) if len(ids) == 1 else None

    def command_and_state(items: list[GroupAddress]) -> tuple[GroupAddress | None, GroupAddress | None]:
        if len(items) == 1:
            return None, items[0]
        state = next((g for g in items if is_status(g)), None)
        command = next((g for g in items if g is not state), None)
        return command, state

    out = []
    for ch_links in by_channel.values():
        seen: set[str] = set()
        by_dpt: dict[str, list[GroupAddress]] = {}
        for l in ch_links:
            g = ga_by_id.get(l.ga_id)
            if not g or g.id in seen:
                continue
            seen.add(g.id)
            dpt = to_hyphen(g.dpt)
            if not dpt:
                continue
            by_dpt.setdefault(dpt, []).append(g)

        temps = by_dpt.get("9-1", [])
        target = next((g for g in temps if test(_TARGET_TEMP, g.name or "")), None)
        actual = next((g for g in temps if g is not target and not test(_TARGET_TEMP, g.name or "")), None)
        if not actual or not target:
            continue
        agg: Agg = {
            "name": _climate_name(target) or _climate_name(actual),
            "temperature_address": actual.address,
            "target_temperature_state_address": target.address,
            "consumed": {target.id},
        }

        def use(g: GroupAddress | None, key: str) -> None:
            if not g:
                return
            agg[key] = g.address
            agg["consumed"].add(g.id)

        shift9 = by_dpt.get("9-2", [])
        shift6 = by_dpt.get("6-10", [])
        shift = shift9 or shift6
        if shift:
            command, state = command_and_state(shift)
            use(command or state, "setpoint_shift_address")
            use(state, "setpoint_shift_state_address")
            agg["setpoint_shift_mode"] = "DPT9002" if shift9 else "DPT6010"
        command, state = command_and_state(by_dpt.get("20-102", []))
        use(command, "operation_mode_address")
        use(state, "operation_mode_state_address")
        command, state = command_and_state(by_dpt.get("20-105", []))
        use(command, "controller_mode_address")
        use(state, "controller_mode_state_address")
        use((by_dpt.get("1-11") or [None])[0], "active_state_address")
        use((by_dpt.get("5-1") or [None])[0], "command_value_state_address")
        humidity = (by_dpt.get("9-7") or [None])[0]
        if humidity:
            agg["humidity_state_address"] = humidity.address
        heat_cool = heat_cool_state_of(ch_links[0].device_id if ch_links else None)
        if heat_cool:
            agg["heat_cool_state_address"] = heat_cool.address
        out.append(agg)
    return out


def _dpt(ga: GroupAddress | None) -> str | None:
    return ga.dpt if ga else None


# ====================== WEATHER ======================

_OUTDOOR_TEMP = js(r"(au(ß|ss)en|outdoor|outside)", True)
_DIRECTIONS = [
    ("south", js(r"(süd|sued|south|zuid)", True)),
    ("west", js(r"west", True)),
    # `\b` before "ost" (JS: ASCII word boundary)
    ("east", js(r"(\bost|east|oost)", True)),
    ("north", js(r"(nord|north|noord)", True)),
]
_RAIN = js(r"regen|rain", True)
_FROST = js(r"frost", True)
_WIND = js(r"wind", True)
_DAY_NIGHT = js(r"tag.?nacht|day.?night", True)


def build_weather_aggregates(gas: list[GroupAddress], links: list[Link]) -> list[Agg]:
    if not links:
        return []
    ga_by_id = {g.id: g for g in gas}
    by_device: dict[str, list[GroupAddress]] = {}
    for l in links:
        g = ga_by_id.get(l.ga_id)
        if not g or not l.device_id:
            continue
        lst = by_device.setdefault(l.device_id, [])
        if g not in lst:
            lst.append(g)

    out = []
    for device_gas in by_device.values():

        def of_dpt(*dpts: str) -> list[GroupAddress]:
            return [g for g in device_gas if (to_hyphen(g.dpt) or "") in dpts]

        temps = of_dpt("9-1")
        temperature = next((g for g in temps if test(_OUTDOOR_TEMP, g.name or "")), None) or (
            temps[0] if len(temps) == 1 else None
        )
        if not temperature:
            continue
        brightness = of_dpt("9-4")
        wind_speed = (of_dpt("9-5", "9-28") or [None])[0]
        directional = [
            (direction, next((g for g in brightness if test(rx, g.name or "")), None)) for direction, rx in _DIRECTIONS
        ]
        if not wind_speed and not any(g for _, g in directional):
            continue
        bools = of_dpt("1-1", "1-2", "1-5", "1-11", "1-24")

        def by_name(rx) -> str | None:
            g = next((g for g in bools if test(rx, g.name or "")), None)
            return g.address if g else None

        def first(items: list[GroupAddress]) -> str | None:
            return items[0].address if items else None

        agg: Agg = {
            "name": "Wetterstation",
            "address_temperature": temperature.address,
            "address_brightness_south": directional[0][1].address if directional[0][1] else None,
            "address_brightness_west": directional[1][1].address if directional[1][1] else None,
            "address_brightness_east": directional[2][1].address if directional[2][1] else None,
            "address_brightness_north": directional[3][1].address if directional[3][1] else None,
            "address_wind_speed": wind_speed.address if wind_speed else None,
            "address_wind_bearing": first(of_dpt("5-3")),
            "address_rain_alarm": by_name(_RAIN),
            "address_frost_alarm": by_name(_FROST),
            "address_wind_alarm": by_name(_WIND),
            "address_day_night": by_name(_DAY_NIGHT),
            "address_air_pressure": first(of_dpt("9-6", "14-58")),
            "address_humidity": first(of_dpt("9-7")),
            "consumed": set(),
        }
        out.append({k: v for k, v in agg.items() if v is not None})
    best: dict[str, Agg] = {}
    for agg in out:
        current = best.get(agg["address_temperature"])
        if current is None or len(agg) > len(current):
            best[agg["address_temperature"]] = agg
    return list(best.values())


# ====================== COVERS ======================

_COVER_NAME_STRIP = js(r"(auf\s*\/\s*ab|hoch\s*\/\s*runter|up\s*\/\s*down|\bstopp?\b|\bauf\b|\bab\b)", True)
_SLATS = js(r"(slat|lamell|angle|winkel)", True)
_REFERENCE = js(r"reference", True)


def build_channel_cover_aggregates(gas: list[GroupAddress], links: list[Link]) -> list[Agg]:
    if not links:
        return []
    ga_by_id = {g.id: g for g in gas}
    by_channel = _group(links, lambda l: l.channel_id)

    def object_dpt(l: Link) -> str:
        return to_hyphen(l.dpt if l.dpt is not None else _dpt(ga_by_id.get(l.ga_id))) or ""

    out = []
    for ch_links in by_channel.values():
        sending = [l for l in ch_links if next(x for x in ch_links if x.com_object_id == l.com_object_id) is l]
        commands = [l for l in sending if not _is_state_object(l) and _flag(l, "TransmitFlag") is not True]
        states = [l for l in sending if _is_state_object(l)]

        def is_slats(l: Link) -> bool:
            return test(_SLATS, l.com_object or "")

        move_long = next(
            (l for l in commands if object_dpt(l) == "1-8" and not test(_REFERENCE, l.com_object or "")), None
        )
        position = next((l for l in commands if object_dpt(l) == "5-1" and not is_slats(l)), None)
        if not move_long and not position:
            continue
        if not any(object_dpt(l) in ("1-7", "1-8", "1-17") for l in commands):
            continue
        main = ga_by_id[(move_long or position).ga_id]
        name = collapse_ws(replace_all(_COVER_NAME_STRIP, main.name or ""))
        agg: Agg = {"name": name or main.name or main.address, "consumed": set()}

        def use(l: Link | None, key: str) -> None:
            g = ga_by_id.get(l.ga_id) if l else None
            if not l or not g:
                return
            agg[key] = g.address
            agg["consumed"].add(l.ga_id)

        use(move_long, "move_long_address")
        use(next((l for l in commands if object_dpt(l) == "1-7"), None), "move_short_address")
        use(next((l for l in commands if object_dpt(l) == "1-17"), None), "stop_address")
        use(position, "position_address")
        use(next((l for l in states if object_dpt(l) == "5-1" and not is_slats(l)), None), "position_state_address")
        use(next((l for l in commands if object_dpt(l) == "5-1" and is_slats(l)), None), "angle_address")
        use(next((l for l in states if object_dpt(l) == "5-1" and is_slats(l)), None), "angle_state_address")
        out.append(agg)

    by_main: dict[str, Agg] = {}
    for agg in out:
        key = agg.get("move_long_address") or agg.get("position_address")
        current = by_main.get(key)
        if current is None or len(agg) > len(current):
            by_main[key] = agg
    return list(by_main.values())


_RE_POS = js(r"\b(pos(ition)?|positie|stand)\b", True)
_RE_ANGLE = js(r"\b(angle|tilt|lamel|hoek)\b", True)
_RE_STOP = js(r"\bstopp?\b", True)
_RE_SHORT = js(r"\b(short|step|stap|kort)\b", True)
_RE_LONG = js(r"\b(long|lang|up\/?down|omhoog|omlaag|open|close|sluit|auf\s*\/\s*ab|hoch\s*\/\s*runter)\b", True)
_RE_INVERT = js(r"\b(invert|omgekeerd|inverse)\b", True)
_COVER_GROUP_NAME_SUFFIX = js(r"\s*(auf\s*\/\s*ab|hoch\s*\/\s*runter)\s*$", True)


def _cover_base_name(name: str) -> str:
    n = (name or "").lower()
    for rx in (_RE_STATUS2, _RE_POS, _RE_ANGLE, _RE_STOP, _RE_SHORT, _RE_LONG):
        n = replace_first(rx, n)
    n = collapse_ws(n)
    return n or (name or "").lower()


_COVER_ADDRESS_KEYS = (
    "move_long_address",
    "move_short_address",
    "stop_address",
    "position_address",
    "position_state_address",
    "angle_address",
    "angle_state_address",
)


def build_cover_aggregates(gas: list[GroupAddress], contexts: dict[str, str] | None = None) -> list[Agg]:
    groups: dict[str, dict[str, Any]] = {}
    for ga in gas:
        name = ga.name or ""
        key = _cover_base_name(name or ga.address)
        d = to_hyphen(ga.dpt)
        is_stop = test(_RE_STOP, name)
        is_command = d in ("1-7", "1-8", "1-10") or is_stop or test(_RE_LONG, name) or test(_RE_SHORT, name)
        entry = {
            "ga": ga,
            "dpt": d,
            "is_command": is_command,
            "is_stop": is_stop,
            "is_cover_like": test(_RE_COVER_WORDS, name),
            "has_status": test(_RE_STATUS2, name),
            "has_position": d == "5-1" or test(_RE_POS, name),
            "has_angle": d == "5-3" or test(_RE_ANGLE, name),
            "has_invert": test(_RE_INVERT, name),
        }
        group = groups.get(key)
        if group is None:
            group = {"name": name or ga.address, "entries": [], "has_command": False}
            groups[key] = group
        if is_command and not group["has_command"]:
            group["name"] = name or group["name"]
        group["entries"].append(entry)
        if is_command:
            group["has_command"] = True

    aggregates = []
    for group in groups.values():
        agg: Agg = {
            "name": replace_first(_COVER_GROUP_NAME_SUFFIX, group["name"]) or group["name"],
            "consumed": set(),
        }
        for e in group["entries"]:
            ga, dpt = e["ga"], e["dpt"]
            if e["is_command"]:
                if e["is_stop"] and dpt in ("1-8", "1-17"):
                    agg.setdefault("stop_address", ga.address)
                    agg["consumed"].add(ga.id)
                elif dpt == "1-8" or (dpt == "1-10" and not e["is_stop"]):
                    agg.setdefault("move_long_address", ga.address)
                    agg["consumed"].add(ga.id)
                elif dpt == "1-7":
                    agg.setdefault("move_short_address", ga.address)
                    agg["consumed"].add(ga.id)
                elif dpt == "1-10" and e["is_stop"]:
                    agg.setdefault("stop_address", ga.address)
                    agg["consumed"].add(ga.id)
                if e["has_invert"]:
                    agg["invert_position"] = True
                continue
            if not (group["has_command"] or e["is_cover_like"]):
                continue
            if e["has_position"]:
                agg.setdefault("position_state_address" if e["has_status"] else "position_address", ga.address)
                agg["consumed"].add(ga.id)
                if e["has_invert"] and not e["has_angle"]:
                    agg["invert_position"] = True
                continue
            if e["has_angle"]:
                agg.setdefault("angle_state_address" if e["has_status"] else "angle_address", ga.address)
                agg["consumed"].add(ga.id)
                if e["has_invert"]:
                    agg["invert_angle"] = True
                continue
            if e["has_invert"]:
                agg["invert_position"] = True
        if any(agg.get(k) for k in _COVER_ADDRESS_KEYS):
            aggregates.append(agg)

    if contexts:
        # missing state addresses from GAs of the same ETS6 function
        by_address = {g.address: g for g in gas}
        by_ctx: dict[str, list[GroupAddress]] = {}
        for g in gas:
            if ctx := contexts.get(g.id):
                by_ctx.setdefault(ctx, []).append(g)
        for agg in aggregates:
            seed = next((agg.get(k) for k in _COVER_SEED_KEYS if agg.get(k)), None)
            seed_ga = by_address.get(seed) if seed else None
            ctx = contexts.get(seed_ga.id) if seed_ga else None
            if not ctx:
                continue
            peers = [
                g
                for g in by_ctx.get(ctx, [])
                if (to_hyphen(g.dpt) or "").startswith("5-") and test(_RE_STATUS2, g.name or "")
            ]
            for value_key, state_key, dpt in (
                ("position_address", "position_state_address", "5-1"),
                ("angle_address", "angle_state_address", "5-3"),
            ):
                if agg.get(value_key) and not agg.get(state_key):
                    cand = next((g for g in peers if to_hyphen(g.dpt) == dpt), None)
                    if cand:
                        agg[state_key] = cand.address
                        agg["consumed"].add(cand.id)
    return aggregates


_COVER_SEED_KEYS = ("position_address", "angle_address", "move_long_address", "move_short_address", "stop_address")


# ====================== SINGLE GA FALLBACK ======================

DPT_TO_HA = {
    "5": "1byte_unsigned", "5.001": "percent", "5.003": "angle", "5.004": "percentU8",
    "5.005": "decimal_factor", "5.006": "tariff", "5.010": "pulse",
    "6": "1byte_signed", "6.001": "percentV8", "6.010": "counter_pulses",
    "7": "2byte_unsigned", "7.001": "pulse_2byte", "7.002": "time_period_msec",
    "7.003": "time_period_10msec", "7.004": "time_period_100msec", "7.005": "time_period_sec",
    "7.006": "time_period_min", "7.007": "time_period_hrs", "7.011": "length_mm",
    "7.012": "current", "7.013": "brightness", "7.600": "color_temperature",
    "8": "2byte_signed", "8.001": "pulse_2byte_signed", "8.002": "delta_time_ms",
    "8.003": "delta_time_10ms", "8.004": "delta_time_100ms", "8.005": "delta_time_sec",
    "8.006": "delta_time_min", "8.007": "delta_time_hrs", "8.010": "percentV16",
    "8.011": "rotation_angle", "8.012": "length_m",
    "9": "2byte_float", "9.001": "temperature", "9.002": "temperature_difference_2byte",
    "9.003": "temperature_a", "9.004": "illuminance", "9.005": "wind_speed_ms",
    "9.006": "pressure_2byte", "9.007": "humidity", "9.008": "ppm", "9.009": "air_flow",
    "9.010": "time_1", "9.011": "time_2", "9.020": "voltage", "9.021": "curr",
    "9.022": "power_density", "9.023": "kelvin_per_percent", "9.024": "power_2byte",
    "9.025": "volume_flow", "9.026": "rain_amount", "9.027": "temperature_f",
    "9.028": "wind_speed_kmh", "9.029": "absolute_humidity", "9.030": "concentration_ugm3",
    "12": "4byte_unsigned", "12.001": "pulse_4_ucount", "12.100": "long_time_period_sec",
    "12.101": "long_time_period_min",
    "16": "string", "16.000": "string", "16.001": "latin_1",
}  # fmt: skip

_FALLBACK_PATTERNS = [
    (js(r"temp|temperatuur", True), "temperature"),
    (js(r"hum|humidity|rv", True), "humidity"),
    (js(r"lux|illuminance|lichtsterkte", True), "illuminance"),
    (js(r"\bppm\b|co2", True), "ppm"),
    (js(r"volt|spanning|voltage", True), "voltage"),
    (js(r"(^|\W)(amp|stroom|current|ma|a)($|\W)", True), "curr"),
    (js(r"power|vermogen|watt|kw\b", True), "power_2byte"),
    (js(r"press|druk", True), "pressure_2byte"),
    (js(r"wind.*km\/?h", True), "wind_speed_kmh"),
    (js(r"wind|windsnelheid", True), "wind_speed_ms"),
    (js(r"rain|regen", True), "rain_amount"),
    (js(r"flow|debiet", True), "volume_flow"),
]


def dpt_to_sensor_type(dpt: str | None, name: str | None) -> str | None:
    norm = to_dot(dpt)
    if norm in ("10.001", "11.001", "19.001"):
        return None
    if norm and norm in DPT_TO_HA:
        return DPT_TO_HA[norm]
    if name:
        for rx, sensor_type in _FALLBACK_PATTERNS:
            if test(rx, name):
                return sensor_type
    return None


_SCENE_NUMBER = js(r"\b(\d{1,2})\b")


def _scene(ga: GroupAddress) -> tuple[str, dict]:
    m = _SCENE_NUMBER.search(ga.name or "")
    payload = {"name": ga.name, "address": ga.address}
    if m:
        payload["scene_number"] = int(m.group(1))
    return "scene", payload


def _unknown(ga: GroupAddress) -> tuple[str, dict]:
    return "_unknown", {"name": ga.name or ga.address, "address": ga.address, "dpt": ga.dpt}


def map_single_ga_to_entity(ga: GroupAddress) -> tuple[str, dict]:
    t = guess_entity_type(ga.dpt, ga.name or "", ga.address)
    dpt_h = to_hyphen(ga.dpt)
    if t == "switch":
        return "switch", {"name": ga.name, "address": ga.address}
    if t == "binary_sensor":
        return "binary_sensor", {"name": ga.name, "state_address": ga.address}
    if t == "light":
        if dpt_h == "1-1":
            return "light", {"name": ga.name, "address": ga.address}
        if dpt_h == "5-1":
            return "sensor", {"name": ga.name, "state_address": ga.address, "type": "percent"}
    if t == "scene":
        return _scene(ga)
    if t == "sensor":
        sensor_type = dpt_to_sensor_type(ga.dpt, ga.name or "")
        if sensor_type:
            return "sensor", {"name": ga.name, "state_address": ga.address, "type": sensor_type}
        return _unknown(ga)
    if t in ("time", "date", "datetime"):
        return t, {"name": ga.name, "address": ga.address, "state_address": ga.address}
    if t == "cover":
        payload: dict[str, Any] = {"name": ga.name}
        nm = ga.name or ""
        has_status = test(_RE_STATUS2, nm)
        has_angle = test(_RE_ANGLE, nm)
        has_position = test(_RE_POS, nm)
        has_invert = test(_RE_INVERT, nm)
        is_stop = test(_RE_STOP, nm)
        invert_targets_angle = False

        def assign(kind: str) -> None:
            prefix = "angle" if kind == "angle" else "position"
            payload[f"{prefix}_state_address" if has_status else f"{prefix}_address"] = ga.address

        if dpt_h == "1-7":
            payload["move_short_address"] = ga.address
        elif dpt_h == "1-8" or (dpt_h == "1-10" and not is_stop):
            payload["move_long_address"] = ga.address
        elif dpt_h == "1-10" and is_stop:
            payload["stop_address"] = ga.address
        elif dpt_h == "5-3":
            invert_targets_angle = True
            assign("angle")
        elif dpt_h in ("5-1", "5"):
            assign("position")
        elif dpt_h and dpt_h.startswith("5-"):
            if has_angle and not has_position:
                invert_targets_angle = True
                assign("angle")
            else:
                assign("position")
        if any(payload.get(k) for k in _COVER_ADDRESS_KEYS):
            if has_invert:
                payload["invert_angle" if invert_targets_angle else "invert_position"] = True
            return "cover", payload
    return _unknown(ga)
