"""Tests for the Met Office Warnings sensor platform."""

from aioresponses import aioresponses

from tests.nswws_helpers import register_nswws


async def test_sensor_state_no_active_warnings(
    hass, issued_empty, mock_config_entry
) -> None:
    with aioresponses() as mocked:
        register_nswws(mocked, issued_empty)
        assert await hass.config_entries.async_setup(mock_config_entry.entry_id)
        await hass.async_block_till_done()

    state = hass.states.get("sensor.met_office_warnings_warning_level")
    assert state is not None
    assert state.state == "none"
    assert state.attributes["warnings"] == []
    assert state.attributes["warning_count"] == 0


async def test_sensor_state_active_warnings(
    hass, issued_active, mock_config_entry
) -> None:
    with aioresponses() as mocked:
        register_nswws(mocked, issued_active)
        assert await hass.config_entries.async_setup(mock_config_entry.entry_id)
        await hass.async_block_till_done()

    state = hass.states.get("sensor.met_office_warnings_warning_level")
    assert state.state == "amber"
    assert state.attributes["warning_count"] == 2
    assert state.attributes["warnings"][0]["id"] == (
        "11111111-1111-1111-1111-111111111111"
    )
