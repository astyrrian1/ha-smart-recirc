"""Device-resident enable switches."""

from homeassistant.components.switch import SwitchEntity
from homeassistant.helpers.entity import EntityCategory

from .api import SWITCHES
from .entity import RecircEntity


async def async_setup_entry(hass, entry, async_add_entities):
    async_add_entities(RecircSwitch(entry.runtime_data, key) for key in SWITCHES)


class RecircSwitch(RecircEntity, SwitchEntity):
    _attr_entity_category = EntityCategory.CONFIG

    def __init__(self, coordinator, key):
        super().__init__(coordinator, key)
        self.key = key
        self._attr_name = SWITCHES[key].name

    @property
    def is_on(self):
        return bool(self.coordinator.data.details[self.key])

    async def async_turn_on(self, **kwargs):
        await self.coordinator.command("set_setting", self.key, 1)

    async def async_turn_off(self, **kwargs):
        await self.coordinator.command("set_setting", self.key, 0)
