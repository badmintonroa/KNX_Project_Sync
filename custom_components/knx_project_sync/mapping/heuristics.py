"""Name/DPT heuristics (port of knx2home src/lib/knx/heuristics.ts and utils.isSceneLikeName)."""

from __future__ import annotations

import re

from .dpt import to_dot, to_hyphen
from .jsre import js, test

_STATUS = js(r"\bstatus\b", True)
_COVER_LIKE = js(
    r"(rolluik|jaloezie|lamel|screen|blind|shutter|cover|gordijn|raam|zonwering|zonnescherm|awning|louver|stores|volet)",
    True,
)
_TIME_HINT = js(r"(tijd|time|clock|rtc|uur|zeit|uhr|hora|heure|std|stunden|stunde|ntp|utc)", True)
_DATE_HINT = js(r"(datum|date|calendar|kalender|fecha|jour|tag|giorno)", True)
_DATETIME_HINT = js(r"(datetime|date[\s_/-]*time|tijdstempel|timestamp|zeitstempel)", True)
_SWITCH_HINT = js(r"(aan|uit|switch|centraal|on|off)", True)
_LA_1 = js(r"^LA\d+", True)
_LA_2 = js(r"^LA\d+-", True)
_USER_HINT = js(r"\[(\w+)\]")
# applied to the lower-cased name, so no ignore-case needed (keeps \b ASCII-only like JS)
_SCENE_LIKE = js(r"(\bscene\b|\bscène\b|\bszene\b|\bscena\b)")
_BRIGHTNESS = js(r"(brightness|helderheid)", True)
_LIGHT_NAME = js(r"(licht|light|lamp|dim)")
_SENSOR_NAME = js(r"(temp|temperatuur|temperature|hum|co2|lux|druk|pressure|wind|rain|flow)")
_ADDRESS3 = js(r"^(\d+)/(\d+)/(\d+)$")


def is_status_name(name: str) -> bool:
    return test(_STATUS, name)


def is_cover_like(name: str) -> bool:
    return test(_COVER_LIKE, name)


def is_la(name: str) -> bool:
    return test(_LA_1, name) or test(_LA_2, name)


def is_scene_like_name(name: str) -> bool:
    return test(_SCENE_LIKE, name.lower())


def guess_entity_type(dpt: str | None, name: str, address: str | None = None) -> str:
    hint = _USER_HINT.search(name)
    if hint and hint.group(1).lower() in ("switch", "light", "cover", "sensor", "binary_sensor", "scene"):
        return hint.group(1).lower()

    nd = to_hyphen(dpt)
    dot = to_dot(dpt)
    lower = name.lower()
    is_switch_like = test(_SWITCH_HINT, lower)
    has_time = test(_TIME_HINT, lower)
    has_date = test(_DATE_HINT, lower)
    explicit_datetime = test(_DATETIME_HINT, lower)

    is_time = dot == "10.001" or nd == "10-1"
    is_date = dot == "11.001" or nd == "11-1"
    is_datetime = dot == "19.001" or nd == "19-1"

    if is_scene_like_name(lower):
        return "scene"

    if nd:
        if nd.startswith("18-") or nd == "18" or nd.startswith("17-") or nd == "17":
            return "scene"
        if is_datetime:
            if explicit_datetime or (has_time and has_date):
                return "datetime"
            if not is_switch_like:
                return "datetime"
        if is_time:
            if has_time or not is_switch_like:
                return "time"
        if is_date:
            if has_date or not is_switch_like:
                return "date"
        if nd == "1-1":
            return "binary_sensor" if is_status_name(name) else "switch"
        if nd in ("1-5", "1-6", "1-9"):
            return "binary_sensor"
        if nd == "1-10":
            return "binary_sensor" if is_status_name(name) else "switch"
        if nd == "3-7":
            return "light"
        if nd == "5-1":
            if is_cover_like(name):
                return "cover"
            if is_la(name):
                return "light"
            if test(_BRIGHTNESS, name):
                return "light"
            return "sensor"
        if nd == "5-3":
            return "cover" if is_cover_like(name) else "sensor"
        if nd.startswith(("7-", "8-", "9-")) or nd == "9":
            return "sensor"
        if nd.startswith("12-"):
            return "sensor"
        if nd == "16" or nd.startswith("16-"):
            return "sensor"
        if nd in ("1-7", "1-8", "1-10"):
            return "cover"
        if nd in ("1-2", "2-1"):
            return "switch"
        if nd in ("20-102", "20-105"):
            return "sensor"

    if is_la(name) or test(_LIGHT_NAME, lower):
        return "light"
    if is_cover_like(name):
        return "cover"
    if is_scene_like_name(lower):
        return "scene"
    if test(_SENSOR_NAME, lower):
        return "sensor"
    if is_status_name(name):
        return "binary_sensor"

    if not nd and address:
        m = _ADDRESS3.match(address)
        if m and int(m.group(1)) == 1 and int(m.group(2)) in (1, 2, 3, 4, 5):
            return "light"

    if is_switch_like:
        return "switch"
    return "unknown"


def parse_address(address: str) -> tuple[int, int, int] | None:
    m = re.fullmatch(r"(\d+)/(\d+)/(\d+)", address.strip(), re.ASCII)
    if not m:
        return None
    return int(m.group(1)), int(m.group(2)), int(m.group(3))
