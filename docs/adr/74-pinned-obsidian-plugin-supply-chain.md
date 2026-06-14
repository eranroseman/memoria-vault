---
topic: decisions
id: 74
title: Manage bundled Obsidian plugins with a pinned provenance manifest
status: deferred
nav_exclude: true
date_proposed: 2026-06-14
date_resolved:
assumes: [26, 55, 67]
supersedes: []
superseded_by: []
parent: Decisions
grand_parent: Explanation
nav_order: 74
---

# ADR-74: Manage bundled Obsidian plugins with a pinned provenance manifest

## Context

Memoria commits the built files for its required Obsidian plugins under
`src/.obsidian/plugins/` so a fresh vault works without downloading plugins at
install time. This supports the repo-as-install-unit and offline, reproducible
vault image chosen in [ADR-26](26-repo-as-install-unit.md) and
[ADR-55](55-src-scaffold-populate-golden-copy.md), but the repository does not
yet record a machine-readable upstream repository, pinned release or commit,
artifact digest, license, or local-patch status for each bundled plugin.
Consequently, an update requires manual discovery and review, while CI can
verify the resulting vault image but cannot prove where a changed `main.js`,
`manifest.json`, or `styles.css` came from.

## Decision

Memoria keeps bundled Obsidian plugin build artifacts committed in
`src/.obsidian/plugins/`; installation remains network-independent and does not
download executable plugin code. The deferred supply-chain model adds:

- A versioned lock manifest beside the plugin inventory. For each bundled
  plugin it records the plugin ID, upstream repository, pinned release tag or
  commit, source/release URL, artifact SHA-256 digests, license, and whether the
  checked-in files are unmodified, patched, or Memoria-authored.
- A repository updater that downloads into a temporary directory, verifies the
  declared upstream identity and pinned version, computes the locked digests,
  and replaces only upstream-owned build artifacts after an explicit review.
- A strict ownership split: `main.js`, upstream `manifest.json`, and upstream
  `styles.css` are vendored artifacts unless the lock says otherwise;
  Memoria-authored `data.json`, `.example` files, and configuration overlays are
  maintained separately and are never overwritten by the updater.
- A CI doctor that proves the lock matches committed artifacts, every enabled
  bundled plugin is represented exactly once, declared files exist, and no
  undeclared executable artifact has entered a plugin directory.
- Explicit patch provenance. A locally modified plugin must use a maintained
  fork or a reviewable patch recorded by the lock; editing minified build output
  without reproducible source or patch history is not allowed.

This ADR records the target model only. Until it is accepted and implemented,
the current committed plugin layout and manual update procedure remain
unchanged.

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

## When this matters

Revisit this at each release cadence, with higher priority when bundled plugin
artifacts change regularly, a plugin update cannot be traced confidently to an
upstream release, a security advisory affects a bundled plugin, local patches
become necessary, or another maintainer needs to reproduce an update without
private context. These are scheduling signals, not automatic adoption gates.

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

**Continue manual vendoring without a manifest.** This has the lowest immediate
implementation cost and is the present deferred state, but leaves updates
non-reproducible and weakens review of executable third-party changes. It is not
the recommended long-term model.

## Related

- **Files affected:** [`src/.obsidian/plugins/`](https://github.com/eranroseman/memoria-vault/tree/main/src/.obsidian/plugins),
  [Obsidian plugin reference](../reference/obsidian-plugins.md)
- **Related decisions / Depends on:** [ADR-26](26-repo-as-install-unit.md),
  [ADR-55](55-src-scaffold-populate-golden-copy.md),
  [ADR-67](67-drift-procedures-keep-or-retire.md)
