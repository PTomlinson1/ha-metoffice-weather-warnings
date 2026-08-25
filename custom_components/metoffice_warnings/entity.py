"""Shared base entity for Met Office Warnings platforms."""

from __future__ import annotations

from homeassistant.config_entries import ConfigEntry
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .coordinator import MetOfficeWarningsCoordinator, WarningsData


class MetOfficeWarningsEntity(CoordinatorEntity[MetOfficeWarningsCoordinator]):
    """Base entity tying every platform entity to one config-entry device."""

    _attr_has_entity_name = True

    def __init__(
        self, coordinator: MetOfficeWarningsCoordinator, entry: ConfigEntry
    ) -> None:
        super().__init__(coordinator)
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, entry.entry_id)},
            name=entry.title,
            manufacturer="Met Office",
            model="NSWWS Warnings Monitor",
        )

    @property
    def _data(self) -> WarningsData:
        return self.coordinator.data
