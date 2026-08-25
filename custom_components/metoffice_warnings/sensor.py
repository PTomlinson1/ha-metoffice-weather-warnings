"""Sensor platform for the Met Office Warnings integration."""

from __future__ import annotations

from homeassistant.components.sensor import SensorDeviceClass, SensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import WARNING_LEVELS
from .coordinator import MetOfficeWarningsCoordinator
from .entity import MetOfficeWarningsEntity


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the warning-level sensor for this config entry."""
    coordinator: MetOfficeWarningsCoordinator = entry.runtime_data
    async_add_entities([MetOfficeWarningLevelSensor(coordinator, entry)])


class MetOfficeWarningLevelSensor(MetOfficeWarningsEntity, SensorEntity):
    """Highest active warning level among the configured areas."""

    _attr_name = "Warning level"
    _attr_device_class = SensorDeviceClass.ENUM
    _attr_options = list(WARNING_LEVELS)

    def __init__(
        self, coordinator: MetOfficeWarningsCoordinator, entry: ConfigEntry
    ) -> None:
        super().__init__(coordinator, entry)
        self._attr_unique_id = f"{entry.entry_id}_warning_level"

    @property
    def native_value(self) -> str:
        return self._data.level

    @property
    def extra_state_attributes(self) -> dict:
        warnings = self._data.warnings
        return {
            "warning_count": len(warnings),
            "warnings": [w.as_dict() for w in warnings],
        }
