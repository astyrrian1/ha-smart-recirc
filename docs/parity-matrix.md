# Parity status — 0.3.0

| Feature | Implementation/evidence |
|---|---|
| Persistent updates | Single TCP reader, partial-state merges, no periodic polling, reconnect backoff; see [push verification](persistent-push.md) |
| Discovery, identity, firmware | Config flow and stable unique IDs; live HA verified |
| Temperatures, delta, flow | Android 4.3.3 parser mapping, mode-0 reads on firmware 6.2.2; flow remains pulses |
| Pump, timer, faults | Binary sensors; validated one-byte reads and pushed updates |
| Trigger/stop | Buttons; stop refuses an active schedule; waits for incoming status after one command/read exchange |
| Basic/advanced settings | Five validated numbers; paired temperature thresholds action |
| Controller, timers, smart timers, DST | Four switches, fresh read/write/readback |
| Ten schedules | Strict 16-byte codec, snapshot conflict detection, full readback; overnight encoding supported |
| Logs | Bounded snapshot, explicit unknown completeness; supports YMDhmsftt only |
| Authentication | Production unsupported; app-derived crypto codec tested offline and live ephemeral handshake verified; protected login remains untested |
| Name, webhook, Bluetooth settings | Mapped; extra reads verified; writes not exposed |
| Clock, reboot, erase, reset, provisioning, OTA | Packet formats documented; clock/provisioning/OTA codecs tested offline; not exposed as production controls |
| 48-hour soak, phone coexistence, DST transition | Not completed; short two-TCP-client push test passed |

Static mappings were extracted from the Android app package 4.3.3 (30434). Raw/decompiled artifacts remain outside the repository. Live status and settings payloads agree with those mappings. This is not a claim of app-screen correlation or full app parity.

Firmware 6.2.2 uses contiguous schedule indices: append at the current schedule count (maximum ten); deleting a record shifts later indices down. The client validates this and verifies the complete resulting list. Live inert-schedule tests confirmed append, delete and index compaction while preserving original schedules.

See [remaining protocol research](https://github.com/astyrrian1/leridian-smart-recirc/blob/main/docs/protocol-remaining.md) and [current HA freshness check](ha-data-verification.md).
