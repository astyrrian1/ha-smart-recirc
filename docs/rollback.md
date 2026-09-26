# Rollback

Disable the integration in Settings → Devices & services to stop reads. No device settings are restored automatically: connections themselves may have re-enabled timers, so verify timer behavior through the app.

For an upgrade rollback, disable the entry, restore the saved prior integration directory (including its bundled library), then restart HA. For this first installation, remove the config entry through HA, archive the smart_recirc directory outside custom_components, and restart. Do not edit `.storage` manually. Use the pre-install HA backup if broader recovery is required.

Any network rule rollback must follow the separate network approval workflow. Firmware and factory settings are untouched by this release.
