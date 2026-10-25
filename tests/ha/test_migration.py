"""Take-over of an installation under the former name knx2home_importer (development builds)."""

from __future__ import annotations

from homeassistant import config_entries
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType
from homeassistant.helpers import issue_registry as ir
from homeassistant.helpers.storage import Store
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.knx_project_sync.const import DOMAIN, LEGACY_DOMAIN

OLD_PACKAGE = "packages/knx2home_importer.yaml"
NEW_PACKAGE = "packages/knx_project_sync.yaml"
STATE = {"manifest": {"entities": []}, "applied": {"switch:GA-1": {"domain": "switch", "unique_id": "1/0/1"}}}


async def test_take_over(hass: HomeAssistant, config_dir, knx_reloads) -> None:
    (config_dir / "packages").mkdir()
    (config_dir / OLD_PACKAGE).write_text("knx: {}\n", encoding="utf-8")
    legacy = MockConfigEntry(
        domain=LEGACY_DOMAIN,
        title="Musterhaus",
        options={"domains": ["light"], "removed": "keep", "package_path": OLD_PACKAGE},
    )
    legacy.add_to_hass(hass)
    await Store(hass, 1, LEGACY_DOMAIN).async_save(STATE)

    result = await hass.config_entries.flow.async_init(DOMAIN, context={"source": config_entries.SOURCE_USER})
    assert result["step_id"] == "legacy"
    result = await hass.config_entries.flow.async_configure(result["flow_id"], {})
    assert result["type"] is FlowResultType.CREATE_ENTRY
    await hass.async_block_till_done()

    assert result["title"] == "Musterhaus"
    assert result["options"]["domains"] == ["light"]
    assert result["options"]["removed"] == "keep"
    assert result["options"]["package_path"] == NEW_PACKAGE
    assert not (config_dir / OLD_PACKAGE).exists()
    assert (config_dir / NEW_PACKAGE).read_text(encoding="utf-8") == "knx: {}\n"
    entry = hass.config_entries.async_entries(DOMAIN)[0]
    assert entry.runtime_data.applied == STATE["applied"]
    assert not knx_reloads  # same entities, nothing to reload

    # removing the old entry must not delete the package taken over
    assert legacy.options["package_path"] == OLD_PACKAGE
    assert ir.async_get(hass).async_get_issue(DOMAIN, "legacy_entry")
    await hass.config_entries.async_remove(legacy.entry_id)
    await hass.async_block_till_done()
    assert not ir.async_get(hass).async_get_issue(DOMAIN, "legacy_entry")


async def test_custom_package_path_is_kept(hass: HomeAssistant, config_dir, knx_reloads) -> None:
    MockConfigEntry(domain=LEGACY_DOMAIN, title="Haus", options={"package_path": "packages/knx.yaml"}).add_to_hass(hass)
    result = await hass.config_entries.flow.async_init(DOMAIN, context={"source": config_entries.SOURCE_USER})
    result = await hass.config_entries.flow.async_configure(result["flow_id"], {})
    assert result["options"]["package_path"] == "packages/knx.yaml"
    # the old entry now points at its own unused default path
    assert hass.config_entries.async_entries(LEGACY_DOMAIN)[0].options["package_path"] == OLD_PACKAGE


async def test_no_legacy(hass: HomeAssistant, config_dir, knx_reloads, upload) -> None:
    result = await hass.config_entries.flow.async_init(DOMAIN, context={"source": config_entries.SOURCE_USER})
    assert result["step_id"] == "upload"
