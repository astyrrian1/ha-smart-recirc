# Actions

Use Developer Tools → Actions and select the Smart Recirc integration entry.

- `smart_recirc.get_schedules` returns a `schedules` array, each with slot 0–9, start/end HH:MM and seven weekday booleans (Monday first).
- To edit/delete, pass the entire returned array as `expected_schedules`; a concurrent app edit causes refusal. `set_schedule` also takes slot, start, end and weekdays. `delete_schedule` takes slot. An all-false weekday array makes an inert schedule. These schedules execute on the controller, independent of HA.
- `smart_recirc.set_temperature_differences` takes low/high whole Fahrenheit degrees (1–30, low <= high), with atomic paired readback.
- `smart_recirc.get_logs` returns records plus `complete: false` and a completion reason. It closes the connection after two idle seconds, with a 15-second/1-MiB ceiling. It does not promise full history. Records retain controller-local timestamps. Noncanonical fractional nibbles follow the app arithmetic and are flagged.

A failed command may already have reached the controller. Refresh and inspect before deciding whether to retry. Automatic retries are intentionally absent.

Firmware 6.2.2 uses contiguous schedule indices: append at the current schedule count (maximum ten); deleting a record shifts later indices down. The client validates this and verifies the complete resulting list. Live inert-schedule tests confirmed append, delete and index compaction while preserving original schedules.
