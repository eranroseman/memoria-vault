---
topic: decisions
id: 74
title: Manage bundled Obsidian plugins with a pinned provenance manifest
nav_exclude: true
status: superseded
date_proposed: 2026-06-14
date_resolved: 2026-06-18
assumes: []
supersedes: []
superseded_by: [125]
---

# ADR-74: Manage bundled Obsidian plugins with a pinned provenance manifest

> **Status note (0.1.0-alpha.15):** superseded by [ADR-125](125-standalone-cli-engine-architecture.md). Kept for decision history; current architecture is carried by the consolidation ADR.

## Context

Memoria commits the built files for its required Obsidian plugins under
`vault-template/.obsidian/plugins/` so a fresh vault works without downloading plugins at
install time. This supports the repo-as-install-unit and offline, reproducible
vault image chosen in [ADR-26](26-repo-as-install-unit.md) and
[ADR-55](55-src-scaffold-populate-golden-copy.md). The repository now records a
static, machine-readable provenance lock for those bundled artifacts in
`vault-template/.obsidian/plugin-provenance-lock.json`: plugin identity, upstream repository,
pinned local version, artifact SHA-256 digests, license assertion, and local-patch
status. That lock makes manual review auditable, but update automation is still
future work: CI validates the static lock against committed artifacts, while a
repository updater that fetches and replaces upstream-owned artifacts remains a
later increment.

## Decision

Memoria keeps bundled Obsidian plugin build artifacts committed in
`vault-template/.obsidian/plugins/`; installation remains network-independent and does not
download executable plugin code. The accepted supply-chain model is incremental:

- A versioned lock manifest beside the plugin inventory. For each bundled
  plugin it records the plugin ID, upstream repository, pinned release tag or
  commit, source/release URL, artifact SHA-256 digests, license, and whether the
  checked-in files are unmodified, patched, or Memoria-authored.
- A CI provenance doctor. It proves the lock matches committed
  artifacts, every enabled bundled plugin is represented exactly once, declared
  files exist, and no undeclared executable artifact has entered a plugin directory.
- A strict ownership split: `main.js`, upstream `manifest.json`, and upstream
  `styles.css` are vendored artifacts unless the lock says otherwise;
  Memoria-authored `data.json`, `.example` files, and configuration overlays are
  maintained separately and are never overwritten by the updater.
- A repository updater as a later increment, after the CI doctor is stable. It
  downloads into a temporary directory, verifies the declared upstream identity and
  pinned version, computes the locked digests, and replaces only upstream-owned
  build artifacts after explicit review.
- Explicit patch provenance. A locally modified plugin must use a maintained
  fork or a reviewable patch recorded by the lock; editing minified build output
  without reproducible source or patch history is not allowed.

The lock manifest and CI doctor are current behavior. Updater automation remains
sequenced implementation work, after the doctor is stable, so drift is detectable
before any automation can rewrite artifacts.

## Consequences

- Fresh installs remain batteries-included and deterministic even without
  network access.
- Plugin updates become reviewable supply-chain changes rather than opaque
  binary replacements.
- CI can detect partial upgrades, accidental local edits, missing provenance,
  and drift between the enabled-plugin list and shipped artifacts.
- The lock and updater add maintenance work, particularly for plugins whose
  upstream releases do not publish stable assets or checksums.
- A checksum proves that the repository contains the reviewed pinned artifact;
  by itself it does not establish that the upstream publisher or release was
  trustworthy. Version selection and upstream review remain human decisions.
- Memoria must define migration behavior for renamed plugin IDs and upstream
  manifests before automation can safely prune old plugin directories.

## Current implementation mapping

The lock is implemented in `vault-template/.obsidian/plugin-provenance-lock.json` and
validated by `scripts/plugin_provenance_doctor.py` in the required lint and local
L0 gates. `tests/test_plugin_provenance.py` shares the doctor core so test
fixtures and CI enforce the same contract: enabled-plugin coverage, exactly one
lock entry per bundled plugin directory, manifest-version parity, declared
upstream fields, SHA-256 digests for committed artifact files, and rejection of
undeclared executable artifacts. This is enough for manual audit and review of
vendored plugin changes, but it is not yet updater automation. Only after that
doctor is stable should Memoria add an updater that downloads and stages new
upstream artifacts for review.

Current plugin-boundary status (2026-06-29): Templater is not a required or bundled
plugin. QuickAdd and Modal Forms own Memoria capture flows instead. Obsidian Git remains
bundled for manual vault-history checkpoints, but automatic commits and pushes are disabled
by shipped configuration (`autoSaveInterval: 0`, `autoPushInterval: 0`) so it is not a
foreign machine writer competing with the worker path.

## When this matters

Revisit the remaining increments at each release cadence, with higher priority when
bundled plugin artifacts change regularly, a plugin update cannot be traced
confidently to an upstream release, a security advisory affects a bundled plugin,
local patches become necessary, or another maintainer needs to reproduce an update
without private context. These are scheduling signals, not automatic adoption gates.

## Alternatives considered

**Download plugins during installation.** This reduces repository size and
always fetches from a declared source, but makes installation network-dependent,
allows upstream disappearance or mutable releases to break old Memoria
versions, and moves executable supply-chain risk into the user installation
path. It conflicts with the repo-as-install-unit model, so committed pinned
artifacts remain the recommendation.

**Use Obsidian's community-plugin installer after first launch.** This delegates
updates to the standard UI and avoids vendoring code, but removes the
batteries-included first run and makes the runtime state depend on manual steps
and whatever version is current at installation time. It is appropriate for
recommended plugins, not Memoria's required set.

**Track plugin repositories as Git submodules.** Submodules provide commit
provenance, but Obsidian loads built release artifacts rather than arbitrary
source trees; many plugin repositories require a Node build with version-specific
tooling. Submodules would add contributor friction without eliminating the need
to build, verify, and commit the exact runtime files.

**Continue manual vendoring without a manifest.** This had the lowest immediate
implementation cost before ADR-74, but would leave updates non-reproducible and
weaken review of executable third-party changes. It is not the recommended
long-term model.

## Related

- **Files affected:** [`vault-template/.obsidian/plugins/`](https://github.com/eranroseman/memoria-vault/tree/main/vault-template/.obsidian/plugins),
  [`scripts/plugin_provenance_doctor.py`](https://github.com/eranroseman/memoria-vault/blob/main/scripts/plugin_provenance_doctor.py),
  [Obsidian plugin reference](../reference/obsidian-plugins.md)
- **Related decisions / Depends on:** [ADR-26](26-repo-as-install-unit.md),
  [ADR-55](55-src-scaffold-populate-golden-copy.md)
- **Tracking issue:** [#686](https://github.com/eranroseman/memoria-vault/issues/686)
  — CI provenance doctor before updater automation.
