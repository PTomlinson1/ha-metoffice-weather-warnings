"""Tests for the diagnostics platform."""

from aioresponses import aioresponses

from custom_components.metoffice_warnings.diagnostics import (
    async_get_config_entry_diagnostics,
)
from tests.nswws_helpers import register_nswws


async def test_diagnostics_redacts_api_key(
    hass, issued_active, mock_config_entry
) -> None:
    with aioresponses() as mocked:
        register_nswws(mocked, issued_active)
        assert await hass.config_entries.async_setup(mock_config_entry.entry_id)
        await hass.async_block_till_done()

    diagnostics = await async_get_config_entry_diagnostics(hass, mock_config_entry)

    assert diagnostics["entry"]["data"]["api_key"] == "**REDACTED**"
    assert diagnostics["coordinator_data"]["level"] == "amber"
    assert len(diagnostics["coordinator_data"]["warnings"]) == 2
