"""Python port of the knx2home entity detection.

Pure Python without Home Assistant imports. The reference implementation is
knx2home (TypeScript); tests/fixtures/*.manifest.json are its golden output and
tests/test_mapping_parity.py keeps this port in line with it. Deliberate
differences are documented in docs/port-notes.md.
"""

from .catalog import Catalog, GroupAddress, Link, catalog_from_xknxproject
from .entities import HaEntities, build_ha_entities
from .manifest import DOMAINS, build_manifest, unique_id_for

__all__ = [
    "DOMAINS",
    "Catalog",
    "GroupAddress",
    "HaEntities",
    "Link",
    "build_ha_entities",
    "build_manifest",
    "catalog_from_xknxproject",
    "unique_id_for",
]
