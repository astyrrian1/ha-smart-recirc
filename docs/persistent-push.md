# Persistent push updates — 0.3.0

## Behavior

HA keeps one TCP connection open, reads a complete initial snapshot and merges subsequent known frames into its shared state. The coordinator has no update interval and the manifest declares `local_push`. Previous `poll_interval` options are ignored; the options flow was removed. Existing device/entity unique IDs are preserved, including the timestamp sensor now labeled Last received update.

Initial connection, reconnection, explicit Refresh readings and user commands can read state. There are no periodic telemetry reads or application heartbeats. Pump confirmation waits for incoming status after one command/read exchange; it does not repeatedly poll pump state. TCP keepalive is enabled, with Linux idle/interval/count settings of 60 s / 10 s / 3 to detect a dead peer without application requests. Update cadence is controlled by the device; a quiet session is not assumed dead merely because values have not changed.

Disconnects mark entities unavailable. Reconnection uses exponential backoff starting at one second, with its base delay capped at 60 seconds and ±20% jitter. Every new HA session verifies identity/authentication state and obtains a fresh snapshot. No writes are automatically retried. Shutdown/unload cancels reconnect work, waits for an active operation and closes the reader/socket.

## Framing and command handling

A single reader handles both replies and unsolicited frames. Requests remain serialized and have bounded deadlines. Unrelated identifiers no longer fail an in-flight request. Known fields are validated before updating HA; unknown fields are ignored by HA rather than exposed under guessed meanings. Frames are limited to 4096 bytes, partially received frames time out, and malformed known fields close the connection. A fixed set of latest known frames preserves updates received while the initial snapshot is assembled.

The protocol has no transaction sequence number. A frame with the requested identifier can be a notification or a read response; those cannot be distinguished definitively. Writes retain value validation and readback comparison, and timeouts discard the connection so a late reply cannot satisfy a later request on a reused session. A readback is a state observation, not a transactional acknowledgment.

Log chunks use a bounded queue alongside ordinary telemetry. Retrieval still bounds total bytes and time and reports unknown completeness. Because there is no reliable end marker, it closes its session afterward; HA then obtains a fresh snapshot and resumes push updates. Ordinary commands leave the persistent session open.

## Verification

Offline tests cover unsolicited temperature/status/settings/flow updates without extra requests, legacy polling-option suppression, notification interleaving with reads and logs, unknown identifiers, malformed and oversized frames, partial-frame timeout, reconnection, unavailable state, unload during reconnect backoff, command controls and existing framing/settings/schedule behavior. All 40 tests pass on Python 3.14 / HA 2026.9.2, with Ruff and strict library typing passing.

Connections may re-enable smart timers. Phone coexistence and long-duration timer effects remain separate acceptance checks; push support does not resolve the existing protected-login, provisioning, clock-sync or OTA limitations.

## Live verification — 2026-09-26

Installed 0.3.0 after a fresh HA backup, scoped integration-directory backup and successful HA configuration validation. All 30 deployed archive files matched by SHA-256. All 22 existing entities loaded with their existing IDs under the same device. A config-entry reload succeeded, reopened one healthy session and left HA RUNNING; integration logs contained only the standard custom-integration warning. HA trigger/stop actions succeeded and returned the initially stopped pump to off.

The decisive push test used a separate TCP client to trigger and stop the controller while HA only listened:

| Observation | HA pump state | HA requests | HA connections | Received frames | Unsolicited frames |
|---|---|---|---|---|---|
| Before external control | off | 74 | 1 | 77 | 3 |
| External trigger | on | 74 | 1 | 79 | 5 |
| External stop | off | 74 | 1 | 80 | 6 |

HA therefore received the state transitions without issuing another request or reconnecting. This also verifies short-term coexistence of two TCP clients; it is not a phone-app or long-duration coexistence soak. The extra start frame is not assigned a new entity meaning here.

Separate 10-second running and 35-second idle windows also left HA request counters unchanged. Earlier standalone 45- and 90-second listens remained connected but had no updates while temperature values were unchanged; an additional ephemeral-key-handshake listen was also quiet. The successful HA test used the ordinary no-password startup reads, without a key exchange or clock write. Continuous periodic telemetry is not assumed: observed event-driven status push is sufficient to update HA as changes arrive.

Temperature/flow/settings notification parsing is covered offline. Their live notification cadence and the 48-hour soak remain unverified. No settings, schedules, clock, credentials or firmware were changed during this push verification; the only control exercise was temporary pump trigger/stop, restored to off.
