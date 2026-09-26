# Live HA data verification — 2026-09-25

Checked at 19:53:50 America/Chicago (2026-09-26 00:53:50 UTC).

The integration was loaded and available, but its last successful snapshot was 2026-09-24 00:30:52 UTC, roughly 48 hours old. Diagnostics confirmed manual mode (`poll_interval=0`). Availability means the previous read succeeded; it does not establish fresh telemetry.

An explicit HA Refresh readings action advanced the successful-read timestamp. A separate TCP read from the HA host agreed with HA:

| Reading | HA and controller |
|---|---|
| Low temperature | 72.0°F |
| High temperature | 72.9°F |
| Absolute temperature difference | 0.9°F |
| Flow pulses | 0 |
| Pump / active timer | Off / off |
| Runtime exceeded / temperature error | Off / off |
| Sensitivity / dormant interval | 5 / 15 minutes |
| Flow delay / initial run time | 50 hundredths / 35 seconds |
| Maximum run time | 5 minutes |
| Controller / timers / smart timers / DST | All enabled |
| Resident schedules | Two |

The prior runtime-exceeded state was on; refresh corrected it to off. HA can retain entity timestamps when the value is unchanged, so use Last successful read for freshness. No pump action or settings mutation was needed for this verification. Polling remains manual unless the owner explicitly selects automatic refresh and accepts its documented smart-timer effect.

Read-only HA MCP discovery was attempted, but no Home Assistant MCP tools were available in this session; authenticated HA REST and the installed library over HA-host SSH were used instead. Credentials and private registry/network data remain outside the repository.
