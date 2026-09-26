# Rollback

Disable the integration in Settings → Devices & services to stop reads. No device settings are restored automatically: connections themselves may have re-enabled timers, so verify timer behavior through the app.

For an upgrade rollback, use HACS → Leridian Smart Recirc → Redownload to select the previous published release, then restart HA. Preserve the existing configuration entry and entity IDs. If no previous HACS release is available or HA cannot start, recover using the pre-install HA backup. Do not edit `.storage` manually.

Any network rule rollback must follow the separate network approval workflow. Firmware and factory settings are untouched by this release.
