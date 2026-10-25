"""Regular expressions with JavaScript semantics where they differ from Python.

knx2home runs its regexes without the `u` flag: `\\b`, `\\w` and `\\d` only know
ASCII word characters there (so `ä` is not part of a word), while Python is
Unicode aware by default. Patterns using them are compiled with re.ASCII.
Patterns that need case-insensitive matching of non-ASCII letters (e.g. `süd`)
must not use these classes, which holds for all patterns ported from knx2home.
"""

from __future__ import annotations

import re

_ASCII_CLASSES = re.compile(r"\\[bBwWdD]")


def js(pattern: str, ignore_case: bool = False) -> re.Pattern[str]:
    flags = re.IGNORECASE if ignore_case else 0
    if _ASCII_CLASSES.search(pattern):
        if ignore_case and not pattern.isascii():
            raise ValueError(f"case-insensitive ASCII pattern with non-ASCII literal: {pattern}")
        flags |= re.ASCII
    return re.compile(pattern, flags)


def test(regex: re.Pattern[str], value: str) -> bool:
    """RegExp.prototype.test"""
    return regex.search(value) is not None


def replace_first(regex: re.Pattern[str], value: str, repl: str = "") -> str:
    """String.prototype.replace with a regex without the `g` flag."""
    return regex.sub(repl, value, count=1)


def replace_all(regex: re.Pattern[str], value: str, repl: str = "") -> str:
    """String.prototype.replace with a regex with the `g` flag."""
    return regex.sub(repl, value)


_WS = re.compile(r"\s+")


def collapse_ws(value: str) -> str:
    """value.replace(/\\s+/g, " ").trim()"""
    return _WS.sub(" ", value).strip()
