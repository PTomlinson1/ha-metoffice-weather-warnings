"""Shared fixtures for the Met Office Warnings test suite."""

import json
from pathlib import Path

import pytest
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.metoffice_warnings.const import (
    AREA_ALL,
    CONF_API_KEY,
    CONF_AREAS,
    CONF_BASE_URL,
    DOMAIN,
)
from tests.nswws_helpers import NSWWS_BASE_URL

FIXTURES_DIR = Path(__file__).parent / "fixtures"

pytest_plugins = "pytest_homeassistant_custom_component"


@pytest.fixture(autouse=True)
def auto_enable_custom_integrations(enable_custom_integrations):
    """Enable custom integrations for every test in this suite."""
    yield


def _load_fixture(name: str) -> dict:
    return json.loads((FIXTURES_DIR / name).read_text())


@pytest.fixture
def issued_empty() -> dict:
    """Return a GeoJSON FeatureCollection with no active warnings."""
    return _load_fixture("issued_empty.json")


@pytest.fixture
def issued_active() -> dict:
    """Return a GeoJSON FeatureCollection with two active warnings."""
    return _load_fixture("issued_active.json")


@pytest.fixture
def mock_config_entry(hass):
    """Return a MockConfigEntry already registered with hass."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        title="Met Office Warnings",
        data={
            CONF_API_KEY: "test-key",
            CONF_BASE_URL: NSWWS_BASE_URL,
            CONF_AREAS: [AREA_ALL],
        },
        unique_id="test-key",
    )
    entry.add_to_hass(hass)
    return entry
