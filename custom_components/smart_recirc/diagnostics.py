"""Allowlisted diagnostics: no raw data, identity or addresses."""


async def async_get_config_entry_diagnostics(hass, entry):
    c = entry.runtime_data
    return {
        "integration_version": "0.3.0",
        "firmware": c.data.info.firmware if c.data else None,
        "last_update_success": c.last_update_success,
        "update_model": "persistent_push",
        "connected": c.client.connected,
        "last_connection_error": type(c.client.last_error).__name__
        if c.client.last_error
        else None,
        "frames_received": c.client.frames_received,
        "unsolicited_frames": c.client.unsolicited_frames,
        "requests": c.client.requests,
        "connections": c.client.connections,
        "capabilities": [
            "temperatures",
            "status",
            "settings",
            "pump_control",
            "schedules",
            "bounded_logs",
        ],
        "limitations": [
            "no_password_auth",
            "log_completeness_unknown",
            "push_cadence_device_controlled",
        ],
    }
