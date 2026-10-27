"""Read the ETS project: upload, file in the config folder, or the KNX panel's project.

The result is a `Prepared` project: the manifest of the detection plus the ETS room
of each entity. It can be planned again with other options without parsing again.
"""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
import logging
from pathlib import Path
from typing import Any

from homeassistant.core import HomeAssistant
from homeassistant.helpers.storage import Store

from .const import DOMAIN, KNX_PROJECT_STORAGE_KEY, VERSION
from .errors import KnxImportError
from .mapping import build_ha_entities, build_manifest, catalog_from_xknxproject
from .mapping.catalog import Catalog

_LOGGER = logging.getLogger(__name__)

GENERATOR = {"name": DOMAIN, "version": VERSION}


@dataclass
class Prepared:
    """Parsed project, ready to be planned with different options."""

    manifest: dict[str, Any]
    rooms: dict[str, str]  # entity key -> ETS room name


def _rooms_for_entities(catalog: Catalog, manifest: dict[str, Any]) -> dict[str, str]:
    """Room of the first linked device (actuators first) of each entity's GAs."""
    devices_by_ga: dict[str, list[tuple[bool, str]]] = {}
    for link in catalog.links:
        sends = bool(link.flags and link.flags.get("TransmitFlag") and not link.flags.get("WriteFlag"))
        devices_by_ga.setdefault(link.ga_id, []).append((sends, link.device_id))
    rooms: dict[str, str] = {}
    for entity in manifest["entities"]:
        candidates = Counter()
        for source in entity["sources"]:
            for _, device in sorted(devices_by_ga.get(source["ga_id"] or "", [])):
                if room := catalog.device_rooms.get(device):
                    candidates[room] += 1
        if candidates:
            rooms[entity["key"]] = candidates.most_common(1)[0][0]
    return rooms


def prepare_project(project: dict[str, Any]) -> Prepared:
    catalog = catalog_from_xknxproject(project)
    manifest = build_manifest(catalog, build_ha_entities(catalog), GENERATOR)
    return Prepared(manifest=manifest, rooms=_rooms_for_entities(catalog, manifest))


def parse_project_file(path: Path, password: str | None) -> dict[str, Any]:
    """Parse a .knxproj (runs in the executor)."""
    from xknxproject import XKNXProj
    from xknxproject.exceptions import InvalidPasswordException, XknxProjectException

    try:
        return XKNXProj(path, password=password or None, language="de-DE").parse()
    except InvalidPasswordException as err:
        raise KnxImportError("invalid_password") from err
    except (XknxProjectException, KeyError, ValueError, OSError) as err:
        _LOGGER.exception("Could not parse %s", path)
        raise KnxImportError("invalid_project", error=str(err)) from err


async def async_prepare_upload(hass: HomeAssistant, file_id: str, password: str | None) -> Prepared:
    from homeassistant.components.file_upload import process_uploaded_file

    def _work() -> Prepared:
        with process_uploaded_file(hass, file_id) as path:
            return prepare_project(parse_project_file(path, password))

    return await hass.async_add_executor_job(_work)


async def async_prepare_file(hass: HomeAssistant, path: str, password: str | None) -> Prepared:
    """Project file inside the config folder (or an allowlisted external dir)."""

    def _work() -> Prepared:
        file = Path(hass.config.path(path)).resolve()
        inside_config = file.is_relative_to(Path(hass.config.config_dir).resolve())
        if not (inside_config or hass.config.is_allowed_path(str(file))) or not file.is_file():
            raise KnxImportError("file_not_found", path=str(file))
        return prepare_project(parse_project_file(file, password))

    return await hass.async_add_executor_job(_work)


async def async_prepare_knx_project(hass: HomeAssistant) -> Prepared:
    """Use the project already uploaded in the KNX panel."""
    project = await Store[dict](hass, 1, KNX_PROJECT_STORAGE_KEY).async_load()
    if not project or not project.get("communication_objects"):
        raise KnxImportError("no_knx_project")
    return await hass.async_add_executor_job(prepare_project, project)


async def async_has_knx_project(hass: HomeAssistant) -> bool:
    return bool(await Store[dict](hass, 1, KNX_PROJECT_STORAGE_KEY).async_load())
