"""Typed schedule and paired-threshold actions; no raw command interface."""

from dataclasses import asdict

import voluptuous as vol
from homeassistant.core import SupportsResponse
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers import config_validation as cv

from .api import Schedule
from .const import DOMAIN


def async_register_services(hass):
    if hass.services.has_service(DOMAIN, "get_schedules"):
        return
    base = {vol.Required("config_entry_id"): cv.string}
    slot = vol.All(vol.Coerce(int), vol.Range(min=0, max=9))

    async def handle(call):
        entry = hass.config_entries.async_get_entry(call.data["config_entry_id"])
        if not entry or entry.domain != DOMAIN or not hasattr(entry, "runtime_data"):
            raise HomeAssistantError("Loaded Smart Recirc entry required")
        coordinator = entry.runtime_data
        if call.service == "get_logs":
            return await coordinator.command("get_logs")
        if call.service == "get_schedules":
            await coordinator.async_refresh()
            if not coordinator.last_update_success:
                raise HomeAssistantError("Schedule refresh failed")
            return {
                "schedules": [
                    asdict(s) | {"weekdays": list(s.weekdays)} for s in coordinator.data.schedules
                ]
            }
        if call.service == "set_temperature_differences":
            await coordinator.command(
                "set_temperature_differences", call.data["low"], call.data["high"]
            )
            return
        expected = tuple(
            Schedule(item["slot"], item["start"], item["end"], tuple(item["weekdays"]))
            for item in call.data["expected_schedules"]
        )
        schedule = None
        if call.service == "set_schedule":
            schedule = Schedule(
                call.data["slot"],
                call.data["start"],
                call.data["end"],
                tuple(call.data["weekdays"]),
            )
        await coordinator.command("update_schedule", schedule, call.data["slot"], expected)

    schedule_schema = vol.Schema(
        {
            vol.Required("slot"): slot,
            vol.Required("start"): cv.string,
            vol.Required("end"): cv.string,
            vol.Required("weekdays"): vol.All([cv.boolean], vol.Length(min=7, max=7)),
        }
    )
    hass.services.async_register(
        DOMAIN,
        "get_schedules",
        handle,
        schema=vol.Schema(base),
        supports_response=SupportsResponse.ONLY,
    )
    hass.services.async_register(
        DOMAIN, "get_logs", handle, schema=vol.Schema(base), supports_response=SupportsResponse.ONLY
    )
    editing = base | {
        vol.Required("slot"): slot,
        vol.Required("expected_schedules"): vol.All([schedule_schema], vol.Length(max=10)),
    }
    hass.services.async_register(DOMAIN, "delete_schedule", handle, schema=vol.Schema(editing))
    hass.services.async_register(
        DOMAIN,
        "set_schedule",
        handle,
        schema=vol.Schema(
            editing
            | {
                vol.Required("start"): cv.string,
                vol.Required("end"): cv.string,
                vol.Required("weekdays"): vol.All([cv.boolean], vol.Length(min=7, max=7)),
            }
        ),
    )
    hass.services.async_register(
        DOMAIN,
        "set_temperature_differences",
        handle,
        schema=vol.Schema(
            base
            | {
                vol.Required("low"): vol.All(vol.Coerce(int), vol.Range(min=1, max=30)),
                vol.Required("high"): vol.All(vol.Coerce(int), vol.Range(min=1, max=30)),
            }
        ),
    )
