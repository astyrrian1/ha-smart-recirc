# Split provenance and operation

The integration/runtime files were carried forward from original `leridian-smart-recirc` PR #4 (persistent push 0.3.0, commit `300cc41`), and the dashboard from its merged PR #5. Firmware provenance research from PR #3 remains in the Python repository. The library is now an external dependency, pinned in `library.lock.json`; its source and protocol tests are not copied here.

The maintained HA files and dashboard retain the deployed behavior. This repository transition does not restart or redeploy HA. The generated archive includes dependency provenance so an installation can be tied to the Python source revision and wheel hash. The integration manifest has no private URL or authentication token.

CI uses a separate registration on the existing self-hosted runner VM, with the `ha-smart-recirc-ci` label. `SMART_RECIRC_LIBRARY_DEPLOY_KEY` is a read-only GitHub deploy key scoped to the Python repository and stored as an Actions secret here. `actions/checkout` removes checkout credentials before tests and packaging. The HA host never receives this key.

For a library upgrade, change the exact commit/version lock through an HA PR after the library tests pass. For an integration-only change, leave the lock unchanged. Each repository has its own validation workflow and artifacts. The owner reviews and merges both migration PRs.
