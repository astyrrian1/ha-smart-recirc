# Installation and updates through HACS

Tested target: Home Assistant 2026.9.2, Python 3.14. Full app parity is not implemented.

## Publication prerequisite

[HACS supports only public GitHub repositories](https://www.hacs.xyz/docs/faq/private_repositories/). This repository must be public and have a published release with `smart_recirc.zip` attached. The integration and bundled Python library use the MIT license. Public repository visibility and release publication still need owner approval. The Python repository can stay private: the build checks out the exact revision in `library.lock.json`, builds its wheel and bundles its runtime package. That bundled source becomes public with the release; no GitHub credentials are shipped to HA.

## Install or adopt an existing manual installation

1. Back up Home Assistant, including the current `custom_components/smart_recirc` directory.
2. In HACS, open the menu → **Custom repositories**. Add `https://github.com/astyrrian1/ha-smart-recirc` with type **Integration**.
3. Open **Leridian Smart Recirc**, choose the published version and **Download**. HACS installs the release ZIP, including the protocol library. Do not install the repository source or copy ZIPs manually.
4. Validate HA configuration and restart Home Assistant when HACS requests it.
5. For an existing installation, keep the existing SmartCirc configuration entry: do not delete or re-add it. The domain, unique IDs and entity IDs are unchanged. For a first installation, add **Leridian Smart Recirc** under Settings → Devices & services, enter the controller host/port and acknowledge that connections may re-enable smart timers.
6. Confirm the integration is loaded, existing entities are available, the Mechanical dashboard still resolves its entities, and HACS shows the downloaded version/update entity. Check HA logs for import or connection failures.
7. Verify pushed state changes arrive without an increase in request count. Static temperatures alone do not prove a failed connection; periodic temperature notification cadence remains unverified.

Future upgrades use HACS **Update/Redownload** and the requested HA restart. Do not edit files managed by HACS. HACS removal deletes integration files, so do not uninstall as part of adopting an existing installation. The dashboard remains separately configured in HA.

## Maintainer release workflow

1. Change code and, if needed, the immutable library lock in a PR; update `manifest.json` version for a new release.
2. CI runs HA simulator tests, builds the wheel/ZIP and validates HACS extraction layout, manifest parity, dependency provenance and a bundled import without site packages. CI uses the self-hosted runner. Fork PRs cannot execute on this runner or access the private library key.
3. After owner review and merge, manually run **Home Assistant validation** on `main` with **draft_release** enabled. It repeats validation and uploads the exact tested ZIP to a **draft** `v<manifest version>` release. Existing releases are never overwritten.
4. Review the draft asset and release notes, then publish it after public-distribution approval. HACS needs a published release, not just a Git tag or Actions artifact. `hide_default_branch` prevents offering the incomplete unbundled source tree as a download.
5. Adopt/update through HACS and perform the checks above. Record actual live results; successful CI does not establish that migration occurred.

Version 0.4.0 keeps a persistent local push connection and reconnects automatically, with no periodic polling. Initial/reconnect snapshots, explicit refresh and command readbacks may read state. TCP keepalive detects dead peers. Existing probe and raw-flow entity IDs are retained. To show estimated flow in gal/min, choose the installed meter under the integration's Configure options; otherwise the new flow-rate entity stays unknown. Password-protected operation is unsupported; do not remove a password to enable this release.
