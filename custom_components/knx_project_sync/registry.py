"""Entity and area registry: what an import changes besides the package file."""

from __future__ import annotations

from collections.abc import Iterable

from homeassistant.core import HomeAssistant
from homeassistant.helpers import area_registry as ar, entity_registry as er

from .const import KNX_DOMAIN
from .plan import PlanEntry


def migrate_unique_ids(hass: HomeAssistant, migrations: Iterable[tuple[str, str, str]]) -> int:
    """Keep entity_id, name, area and history when a unique_id changes (e.g. GA re-addressed)."""
    registry = er.async_get(hass)
    count = 0
    for domain, old_uid, new_uid in migrations:
        entity_id = registry.async_get_entity_id(domain, KNX_DOMAIN, old_uid)
        if not entity_id or registry.async_get_entity_id(domain, KNX_DOMAIN, new_uid):
            continue
        registry.async_update_entity(entity_id, new_unique_id=new_uid)
        count += 1
    return count


def remove_entities(hass: HomeAssistant, unique_ids: Iterable[tuple[str, str]]) -> int:
    """Remove the registry entries of (domain, unique_id); returns how many existed."""
    registry = er.async_get(hass)
    count = 0
    for domain, uid in unique_ids:
        if entity_id := registry.async_get_entity_id(domain, KNX_DOMAIN, uid):
            registry.async_remove(entity_id)
            count += 1
    return count


def assign_areas(hass: HomeAssistant, written: Iterable[PlanEntry], rooms: dict[str, str]) -> int:
    """ETS rooms -> HA areas, only for entities without an area."""
    registry = er.async_get(hass)
    areas = ar.async_get(hass)
    count = 0
    for entry in written:
        room = rooms.get(entry.key)
        entity_id = registry.async_get_entity_id(entry.domain, KNX_DOMAIN, entry.unique_id)
        if not room or not entity_id:
            continue
        reg_entry = registry.async_get(entity_id)
        if reg_entry is None or reg_entry.area_id:
            continue
        area = areas.async_get_area_by_name(room) or areas.async_create(room)
        registry.async_update_entity(entity_id, area_id=area.id)
        count += 1
    return count
