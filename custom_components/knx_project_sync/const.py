"""Constants for the KNX Project Sync integration."""

from __future__ import annotations

from typing import Final

DOMAIN: Final = "knx_project_sync"
VERSION: Final = "0.1.2"

KNX_DOMAIN: Final = "knx"
# xknxproject output of the project uploaded in the KNX panel
KNX_PROJECT_STORAGE_KEY: Final = "knx/knx_project.json"

CONF_SOURCE: Final = "source"
SOURCE_UPLOAD: Final = "upload"
SOURCE_KNX_PROJECT: Final = "knx_project"

CONF_FILE: Final = "file"
CONF_PASSWORD: Final = "password"
CONF_DOMAINS: Final = "domains"
CONF_REMOVED: Final = "removed"
REMOVED_DELETE: Final = "delete"
REMOVED_KEEP: Final = "keep"
CONF_ASSIGN_AREAS: Final = "assign_areas"
CONF_PACKAGE_PATH: Final = "package_path"

DEFAULT_PACKAGE_PATH: Final = "packages/knx_project_sync.yaml"

SIGNAL_IMPORTED: Final = f"{DOMAIN}_imported"
EVENT_IMPORTED: Final = f"{DOMAIN}_imported"

SERVICE_IMPORT_PROJECT: Final = "import_project"

ISSUE_PACKAGE_NOT_LOADED: Final = "package_not_loaded"
ISSUE_RELOAD_FAILED: Final = "knx_reload_failed"

# config entry data: the line added to configuration.yaml, taken out on removal
DATA_PACKAGES_ADDED: Final = "packages_added"
