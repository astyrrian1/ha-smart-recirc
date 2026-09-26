# Installation: local experimental release

Tested development target: Home Assistant 2026.9.2, Python 3.14. Full app parity is not implemented.

1. Download the `smart-recirc-installation` artifact from a successful GitHub Actions run for the reviewed commit, or follow the root README to check out the locked Python dependency, run HA tests and execute `python tools/build_integration.py`. The artifact contains `dist/smart_recirc.zip`.
2. Back up HA before installing. Preserve any existing integration directory before an upgrade.
3. Extract `dist/smart_recirc.zip` into HA's configuration directory so `custom_components/smart_recirc/manifest.json` exists. The archive includes the library under `_vendor`; do not install the source integration directory alone.
4. Validate HA configuration and restart HA to discover the custom integration.
5. Add **Leridian Smart Recirc** in Settings → Devices & services, or confirm discovery. Enter the controller host and TCP port (normally 5438), and acknowledge that connections may re-enable timers.
6. Check firmware, temperatures, status and last-read timestamp. Use **Refresh readings** for an explicit update.

Version 0.3.0 keeps a persistent connection for pushed updates and automatically reconnects after failures. There is no polling option; previous interval settings are ignored. Initial connection, reconnection, explicit refresh and user commands may read state. TCP keepalive detects dead peers without telemetry polling. Existing raw-probe entity IDs are retained and now report temperatures with units. Password-protected operation is not supported; do not remove a password just to enable this release.

This local release builds a wheel from the clean, immutable library revision in `library.lock.json` and bundles the wheel’s package. A future public release can replace bundling with a pinned published dependency. Existing Home Assistant deployment repositories may exclude custom_components; keep their exclusion rules intact.
