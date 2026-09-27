"""Local, evidence-backed Smart Recirc telemetry."""

from homeassistant.const import CONF_HOST, CONF_PORT, EVENT_HOMEASSISTANT_STOP, Platform

from .api import Client
from .coordinator import RecircConfigEntry, RecircCoordinator
from .services import async_register_services

PLATFORMS = [
    Platform.SENSOR,
    Platform.BUTTON,
    Platform.NUMBER,
    Platform.SWITCH,
    Platform.BINARY_SENSOR,
]


async def async_setup_entry(hass, entry: RecircConfigEntry) -> bool:
    coordinator = RecircCoordinator(
        hass, entry, Client(entry.data[CONF_HOST], entry.data[CONF_PORT])
    )
    try:
        await coordinator.async_config_entry_first_refresh()
        entry.runtime_data = coordinator
        async_register_services(hass)
        await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    except BaseException:
        await coordinator.stop()
        raise

    coordinator.start()

    async def close_on_stop(event):
        await coordinator.stop()

    entry.async_on_unload(hass.bus.async_listen_once(EVENT_HOMEASSISTANT_STOP, close_on_stop))
    entry.async_on_unload(entry.add_update_listener(_async_options_updated))
    return True


async def _async_options_updated(hass, entry):
    # The meter selection changes only the local conversion. Keep the existing
    # controller connection so this cannot re-enable smart timers.
    coordinator = entry.runtime_data
    coordinator.async_set_updated_data(coordinator.data)


async def async_unload_entry(hass, entry: RecircConfigEntry) -> bool:
    if await hass.config_entries.async_unload_platforms(entry, PLATFORMS):
        await entry.runtime_data.stop()
        return True
    return False
