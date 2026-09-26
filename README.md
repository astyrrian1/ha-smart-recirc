# Home Assistant — Leridian Smart Recirc

Home Assistant integration and dashboards for Smart Recirculation Control 32. The independent Python protocol library lives in [leridian-smart-recirc](https://github.com/astyrrian1/leridian-smart-recirc).

Version **0.3.0** uses a persistent local push connection with automatic reconnect and no periodic polling. It preserves 22 existing entities and supplies validated controls, schedules and bounded logs. See [installation](docs/installation.md), [push behavior and live verification](docs/persistent-push.md), [Mechanical dashboard](docs/dashboard.md) and [parity limitations](docs/parity-matrix.md).

## Dependency and build

`library.lock.json` pins the external library to a full Git commit and package version. CI has a read-only deploy key for that private repository and runs on the existing self-hosted runner VM. No GitHub-hosted spending limit is needed.

For development, clone the library into `.deps/library` and check out the exact `commit` from the lock file. Git authentication must already be configured on your development machine. Then:

```sh
python3.14 -m venv .venv
. .venv/bin/activate
python -m pip install -r requirements-dev.txt
python -m pip install .deps/library
ruff check custom_components tests tools
pytest -q
python tools/build_integration.py
```

The builder rejects a dirty or incorrectly pinned library checkout, builds a wheel, verifies its package name/version and places the wheel's library package inside the generated HA ZIP. It records dependency provenance and the wheel hash. The live HA server needs neither GitHub credentials nor an unpublished PyPI requirement. Generated `_vendor` files, dependency checkouts and archives are not maintained source and are excluded from Git.

Installation and updates use **HACS** and the `smart_recirc.zip` asset attached to a GitHub release. The archive contains the integration files at its root, as HACS requires; it is not extracted into the HA configuration root. See [installation and release workflow](docs/installation.md). CI artifacts are validation outputs, not the normal installation path. Merging a PR does not deploy.

HACS requires this integration repository and its releases to be public. The separate Python repository may remain private, but its bundled runtime source is necessarily included in the public release asset. Until publication is approved and the first release is published, HACS installation is blocked.

## Updating the library

Make and test protocol changes in the Python repository. Update this repository's immutable lock in a new PR, install that revision and run the HA lifecycle tests and archive build. Changing only the Python repository never silently changes HA's dependency. Once an approved public package release exists, installation can be moved to an exact manifest requirement; private credentials must never be embedded in the manifest.

Controller connections may re-enable smart timers. Password authentication, provisioning, firmware updates and maintenance operations remain unsupported. The full capability limits and evidence are preserved in `docs/`.
