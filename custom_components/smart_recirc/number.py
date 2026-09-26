"""Validated controller settings with readback."""

from homeassistant.components.number import NumberEntity, NumberMode
from homeassistant.helpers.entity import EntityCategory

from .api import NUMBERS
from .entity import RecircEntity


async def async_setup_entry(hass, entry, async_add_entities):
    async_add_entities(RecircNumber(entry.runtime_data, key) for key in NUMBERS)


class RecircNumber(RecircEntity, NumberEntity):
    _attr_entity_category = EntityCategory.CONFIG
    _attr_mode = NumberMode.BOX
    _attr_native_step = 1

    def __init__(self, coordinator, key):
        super().__init__(coordinator, key)
        self.key = key
        setting = NUMBERS[key]
        self._attr_name = setting.name
        self._attr_native_min_value = setting.minimum
        self._attr_native_max_value = setting.maximum
        self._attr_native_unit_of_measurement = setting.unit

    @property
    def native_value(self):
        return self.coordinator.data.details[self.key]

    async def async_set_native_value(self, value):
        if value != int(value):
            raise ValueError("Whole numbers required")
        await self.coordinator.command("set_setting", self.key, int(value))
