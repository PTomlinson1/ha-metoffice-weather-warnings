"""Tests for integration setup/unload."""

from aioresponses import aioresponses
from homeassistant.config_entries import ConfigEntryState

from tests.nswws_helpers import register_nswws, register_nswws_feed_error


async def test_setup_and_unload_entry(hass, issued_empty, mock_config_entry) -> None:
    with aioresponses() as mocked:
        register_nswws(mocked, issued_empty)
        assert await hass.config_entries.async_setup(mock_config_entry.entry_id)
        await hass.async_block_till_done()

    assert mock_config_entry.state is ConfigEntryState.LOADED

    assert await hass.config_entries.async_unload(mock_config_entry.entry_id)
    await hass.async_block_till_done()

    assert mock_config_entry.state is ConfigEntryState.NOT_LOADED


async def test_options_update_triggers_reload(
    hass, issued_empty, mock_config_entry
) -> None:
    with aioresponses() as mocked:
        register_nswws(mocked, issued_empty)
        assert await hass.config_entries.async_setup(mock_config_entry.entry_id)
        await hass.async_block_till_done()

    assert mock_config_entry.state is ConfigEntryState.LOADED

    with aioresponses() as mocked:
        register_nswws(mocked, issued_empty)
        hass.config_entries.async_update_entry(
            mock_config_entry, options={"scan_interval_minutes": 15}
        )
        await hass.async_block_till_done()

    assert mock_config_entry.state is ConfigEntryState.LOADED


async def test_setup_entry_auth_failure_starts_reauth(
    hass, mock_config_entry
) -> None:
    with aioresponses() as mocked:
        register_nswws_feed_error(mocked, status=403)
        assert not await hass.config_entries.async_setup(mock_config_entry.entry_id)
        await hass.async_block_till_done()

    assert mock_config_entry.state is ConfigEntryState.SETUP_ERROR
