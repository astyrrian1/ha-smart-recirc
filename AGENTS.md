# Home Assistant integration repository

Own the `smart_recirc` integration, HA lifecycle tests, dashboards and installation packaging here. The standalone protocol library belongs in `astyrrian1/leridian-smart-recirc`; do not copy its maintained source into this repository.

- Read `library.lock.json` before changing dependency handling. Pin a full Git commit and exact package version.
- CI uses the existing self-hosted HA Smart Recirc runner. Do not switch to GitHub-hosted runners.
- Build the HA archive from a wheel produced from the clean pinned library checkout. Never edit generated `_vendor` files or commit dependency checkouts/artifacts.
- Never commit credentials, controller identities, raw captures, private dashboard backups or unsanitized diagnostics.
- Live device changes and HA deployment require task-specific authorization. Packaging/CI work alone must not modify the house.
- Run HA simulator tests and validate the installation archive before publishing a PR. Use feature branches; the owner merges.
- Preserve entity IDs and explicit parity limitations. Connections may re-enable smart timers. Never blindly retry writes.
- Manage storage dashboards through the HA API, with a backup, fresh-read conflict check and readback verification; never edit `.storage` directly.
