# Verification — 0.2.0, 2026-09-23

## Automated

26 tests passed on Home Assistant 2026.9.2 / Python 3.14: 19 library cases and 7 HA cases. Coverage includes fragmentation, truncation, bounds, timeouts, cancellation, serialized calls, settings validation/readback, malformed schedules, schedule conflict detection and index compaction, guarded pump stop, extra pump-status replies, HA actions, unit conversion, config flows, identity checks, availability, diagnostics and unload.

Ruff and strict library type checks pass. Wheel/sdist and self-contained integration ZIP build successfully.

## Live validation

- Approved HA-only TCP 5438 gateway/AP exceptions were applied before this upgrade; existing network policies were preserved. Restricted-SSID runtime negative testing remains outstanding.
- Previous integration backed up before scoped installation. HA configuration checks passed.
- Existing config entry retained; 22 entities loaded. Original probe entity IDs were preserved and now have temperature units.
- Sensitivity changed, read back through HA, and restored. Other numbers and switches accepted unchanged-value writes with readback. Paired temperature thresholds accepted unchanged-value readback.
- Inactive schedules appended and deleted; original schedules restored. Additional live tests identified contiguous append indices and compaction after deletion. Client and simulator were corrected accordingly.
- 408 log records decoded through the HA action. Completeness is explicitly unknown; some fractional nibbles are noncanonical and flagged. Log timestamps remain controller-local.
- Pump action testing revealed extra status replies after commands. Pump was returned to off and the connection lifecycle was corrected with a regression test. Final HA action verification is recorded below.

## Limitations

This is not full app parity. Password authentication, firmware updates, provisioning, maintenance actions, controller rename/webhook/Bluetooth settings, automatic clock sync and current-runtime sensor remain unsupported. Overnight encoding is tested offline; actual overnight execution, DST transitions, phone coexistence and the 48-hour soak are unverified. Polling remains off by default because connections may affect smart timers. Manual-mode states are snapshots.

## Final build verification

The corrected 0.2.0 build passed all live HA actions: pump trigger reported on, stop reported off, every tested setting read back, original sensitivity and schedules were restored, paired thresholds confirmed, and 408 log records decoded. The HA registry contains 22 entities under one device. Manual refresh advanced its timestamp. Config-entry reload succeeded without a restart, followed by a loaded entry and HA RUNNING state. Final-startup logs contained only the normal custom-integration warning for smart_recirc.

The generated archive's 29 deployed files are compared by SHA-256. No HA YAML deployment repository was edited. Source is reviewed through the feat/local-integration pull request in the dedicated private repository. CI builds downloadable installation bundles; merging this PR does not deploy to HA.
