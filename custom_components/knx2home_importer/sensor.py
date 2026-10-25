"""Sensor with the time and result of the last import."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from homeassistant.components.sensor import SensorDeviceClass, SensorEntity
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.device_registry import DeviceEntryType, DeviceInfo
from homeassistant.helpers.dispatcher import async_dispatcher_connect
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback
from homeassistant.util import dt as dt_util

from . import Knx2HomeConfigEntry
from .const import DOMAIN, SIGNAL_IMPORTED, VERSION


async def async_setup_entry(
    hass: HomeAssistant, entry: Knx2HomeConfigEntry, async_add_entities: AddConfigEntryEntitiesCallback
) -> None:
    async_add_entities([LastImportSensor(entry)])


class LastImportSensor(SensorEntity):
    _attr_has_entity_name = True
    _attr_translation_key = "last_import"
    _attr_device_class = SensorDeviceClass.TIMESTAMP
    _attr_should_poll = False

    def __init__(self, entry: Knx2HomeConfigEntry) -> None:
        self._importer = entry.runtime_data
        self._attr_unique_id = f"{entry.entry_id}_last_import"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, entry.entry_id)},
            name="KNX2HOME Importer",
            entry_type=DeviceEntryType.SERVICE,
            sw_version=VERSION,
        )

    async def async_added_to_hass(self) -> None:
        self.async_on_remove(async_dispatcher_connect(self.hass, SIGNAL_IMPORTED, self._handle_import))

    @callback
    def _handle_import(self) -> None:
        self.async_write_ha_state()

    @property
    def _last(self) -> dict[str, Any]:
        return self._importer.data.get("last_import", {})

    @property
    def native_value(self) -> datetime | None:
        value = self._last.get("time")
        return dt_util.parse_datetime(value) if value else None

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        last = self._last
        return {
            "project": last.get("project"),
            "source": last.get("source"),
            "package": last.get("package"),
            "entities": len(self._importer.applied),
            **last.get("summary", {}),
        }
