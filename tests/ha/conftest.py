"""Home Assistant test fixtures (pytest-homeassistant-custom-component)."""

from __future__ import annotations

from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path
from unittest.mock import patch

from homeassistant.core import HomeAssistant, ServiceCall
import pytest
from pytest_homeassistant_custom_component.common import MockConfigEntry, MockModule, mock_integration

from helpers import FIXTURES, file_id

PACKAGES_CONFIG = """\
homeassistant:
  packages: !include_dir_named packages
"""

# hand written KNX YAML of the user, overlapping with the project (switch 1/0/1)
OWN_KNX_YAML = """\
knx:
  switch:
    - name: Handgeschrieben Wohnzimmer
      address: "1/0/1"
      state_address: "1/0/2"
"""


@pytest.fixture(autouse=True)
def auto_enable_custom_integrations(enable_custom_integrations):
    yield


@pytest.fixture
def config_dir(hass: HomeAssistant, tmp_path: Path) -> Path:
    hass.config.config_dir = str(tmp_path)
    (tmp_path / "configuration.yaml").write_text(PACKAGES_CONFIG + OWN_KNX_YAML, encoding="utf-8")
    return tmp_path


@pytest.fixture
def knx_reloads(hass: HomeAssistant) -> list[ServiceCall]:
    """Replace the KNX integration by a mock with a recording `knx.reload` service."""
    mock_integration(hass, MockModule("knx"))
    mock_integration(hass, MockModule("file_upload"))
    MockConfigEntry(domain="knx", title="KNX").add_to_hass(hass)
    calls: list[ServiceCall] = []

    async def reload(call: ServiceCall) -> None:
        calls.append(call)

    hass.services.async_register("knx", "reload", reload)
    return calls


@pytest.fixture
def upload():
    """Make `process_uploaded_file(hass, file_id(<fixture>))` yield that fixture."""
    by_id = {file_id(p.stem): p for p in FIXTURES.glob("*.knxproj")}

    @contextmanager
    def fake(hass, upload_id: str) -> Iterator[Path]:
        yield by_id[upload_id]

    with patch("homeassistant.components.file_upload.process_uploaded_file", fake):
        yield
