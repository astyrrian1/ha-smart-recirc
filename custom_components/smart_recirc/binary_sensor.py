"""Observed pump, schedule and fault status."""

from homeassistant.components.binary_sensor import BinarySensorDeviceClass, BinarySensorEntity

from .api import STATUS
from .entity import RecircEntity


async def async_setup_entry(hass, entry, async_add_entities):
    async_add_entities(RecircBinarySensor(entry.runtime_data, key) for key in STATUS)


class RecircBinarySensor(RecircEntity, BinarySensorEntity):
    def __init__(self, coordinator, key):
        super().__init__(coordinator, key)
        self.key = key
        self._attr_name = key.replace("_", " ").capitalize()
        if key in ("run_time_exceeded", "temperature_error"):
            self._attr_device_class = BinarySensorDeviceClass.PROBLEM
        else:
            self._attr_device_class = BinarySensorDeviceClass.RUNNING

    @property
    def is_on(self):
        return self.coordinator.data.details[self.key]
