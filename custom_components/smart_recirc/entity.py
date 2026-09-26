"""Common device identity; addresses and names never form unique IDs."""

from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN


class RecircEntity(CoordinatorEntity):
    _attr_has_entity_name = True

    def __init__(self, coordinator, key):
        super().__init__(coordinator)
        info = coordinator.data.info
        self._attr_unique_id = f"{info.identity}_{key}"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, info.identity)},
            name=info.name,
            manufacturer="Leridian Dynamics",
            model="Smart Recirculation Control 32",
            sw_version=info.firmware,
        )
