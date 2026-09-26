"""Explicit read action. No unverified device write actions."""

from homeassistant.components.button import ButtonEntity
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers.entity import EntityCategory

from .entity import RecircEntity


async def async_setup_entry(hass, entry, async_add_entities):
    async_add_entities(
        [
            RefreshButton(entry.runtime_data, "refresh"),
            PumpButton(entry.runtime_data, True),
            PumpButton(entry.runtime_data, False),
        ]
    )


class RefreshButton(RecircEntity, ButtonEntity):
    _attr_name = "Refresh readings"
    _attr_entity_category = EntityCategory.DIAGNOSTIC

    @property
    def available(self):
        # Allow a manual reconnect attempt after a failed read.
        return True

    async def async_press(self):
        await self.coordinator.async_request_refresh()
        if not self.coordinator.last_update_success:
            raise HomeAssistantError("Controller refresh failed")


class PumpButton(RecircEntity, ButtonEntity):
    def __init__(self, coordinator, start):
        super().__init__(coordinator, "trigger" if start else "stop")
        self.start = start
        self._attr_name = "Trigger pump" if start else "Stop pump"

    @property
    def available(self):
        return super().available and (
            self.start or not self.coordinator.data.details["timer_active"]
        )

    async def async_press(self):
        await self.coordinator.command("trigger", self.start)
