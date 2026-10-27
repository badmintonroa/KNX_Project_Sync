"""Error with a translation key, shown in the dialogs, the panel and the repair."""

from __future__ import annotations

from homeassistant.exceptions import HomeAssistantError


class KnxImportError(HomeAssistantError):
    """Import failed; `translation_key` explains why."""

    def __init__(self, key: str, **placeholders: str) -> None:
        super().__init__(key)
        self.key = key
        self.placeholders = placeholders
