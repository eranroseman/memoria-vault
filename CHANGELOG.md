# Changelog

All notable changes to Memoria are documented here.
Format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).
Versions follow [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

Memoria is in **early pre-alpha development — there is no formal tagged release yet.**
The install path runs from current `main` as an alpha source install.

There is no release automation and no formal tagged release yet; installs run
from current `main`. The earlier `v0.1.0`–`v0.3.2` tags were artifacts of the
removed release-please setup, not real releases, and have been deleted.

## [0.1.0a21] - 2026-07-14

Alpha.21 is a source-install checkpoint, not a formal tag or GitHub Release.
It hardens the machinery alpha.20 delivered into enforceable, verifiable
behavior — provenance-honest actor authority, a verifiable journal, durable
off-machine backup, and honest control surfaces — then hardens the content
layer against untrusted markdown and plants the feedback-instrumentation seam.

### Changed

- Added per-operation actor enforcement: every mediated write consumes a
  validated `OperationContext` (`pi | agent | operation | integrity`), and a
  fixed `PROTECTED_OPERATION_ACTORS` map reserves destructive operations
  (`cascade-rollback`, `mark-checked`, `promote-draft-passage`, and peers) to
  the required actor, checked before any payload processing.
- Made `memoria journal verify` the one authoritative trust-read path over the
  `event_log` hash chain, checking the chain, live-tip anchor, committed-anchor
  prefix, and JSONL export subset together.
- Added `memoria workspace backup`/`restore`/`recover` for durable, PI-only,
  off-machine snapshots (SQLite, blobs, journal head), with `memoria doctor`
  failing when a blob has no corresponding backup coverage.
- Fixed control-surface honesty gaps: `_emit` no longer reports successes it
  did not perform, `list --type work` and `new-note --mode work` work
  correctly, dead CLI knobs were removed, and `argument.canvas` projection
  drift is now covered by the tracked-projection check.
- Added content-security hardening: `neutralize_untrusted_markdown` masks
  machine- or third-party-derived markdown at operation/knowledge field
  boundaries and the export choke; an insert-only `evidence_bindings` ledger
  binds evidence markers to their exact cited text; a `file_baseline` table
  witnesses foreign edits and restriction-key removal outside the operation
  envelope.
- Bumped the runtime SQLite schema to `user_version = 12`.
- Added `empirical_event.v1` `loudness` and `staleness_hit` fields and a
  server-side `disposition.v1` journal event emitted from `resolve-attention`,
  as the first (non-backfillable) slice of the I1 feedback-instrumentation
  seam; the dashboard and full package remain deferred to beta.1.
- Folded the pre-`main` corpus doctrine into the published Diátaxis `docs/`
  tree and retired `docs/superpowers/` as the tracked-but-unpublished working
  design record.
- Widened `scripts/verify` to also run the `runtime`, `package`, and `floor`
  test levels (only `live` stays out of the gate).

### Release management

- The Python package version is `0.1.0a21`.
- `release-please` remains `workflow_dispatch`-only and was not dispatched for
  this checkpoint; no tag or GitHub Release is cut.
- Formal release-please versioning, generated release notes, tags, and GitHub
  Releases remain deferred until the first real release.

## [0.1.0a20] - 2026-07-08

Alpha.20 is a source-install checkpoint, not a formal tag or GitHub Release.
It makes the CLI, loopback HTTP, and MCP surfaces contractual enough for local
editor and agent adapters while keeping the engine as the state owner.

### Changed

- Added the data-only surface contract registry plus drift checks for shared
  CLI, HTTP, MCP, and reference-doc surface details.
- Hardened local HTTP with startup read-scope caps, adapter-grade status
  responses, `/openapi.json`, and read parity for journal, project slice/draft,
  and exploration data.
- Added MCP tool descriptions and scoped read tools for project slice, project
  draft, and exploration; added CLI surface schema inspection and clearer shared
  surface help.
- Added the strict `empirical_event.v1` schema and `empirical-event-record`
  operation so local use events can be recorded without body text or absolute
  paths.
- Added the optional `packages/memoria-obsidian` proof adapter, seeded it by
  default through `memoria init`, and added `memoria init --no-obsidian` for
  non-Obsidian workspaces.
- Retired `vault-template/` in favor of the packaged workspace seed under
  `src/memoria_vault/product/workspace_seed/`.

### Release management

- `release-please` remains `workflow_dispatch`-only and was not dispatched for
  this checkpoint; no tag or GitHub Release is cut.
- Formal release-please versioning, generated release notes, tags, and GitHub
  Releases remain deferred until the first real release.

## [0.1.0a19] - 2026-07-07

Alpha.19 is a source-install checkpoint, not a formal tag or GitHub Release.
It adds the first runnable query/code substrate while keeping BM25 as the
default answer path and code execution fail-closed without a proven sandbox.

### Changed

- Renamed the generated full-text bundle root from `fulltext/` to `fulltexts/`
  while keeping `type: fulltext` as the document schema label.
- Bumped the runtime SQLite schema to `user_version = 8`; alpha DB v7 is
  rejected and should be rebuilt from markdown/catalog state.
- Added derived `passages`, `passage_fts`, `passage_vec`, `file_index_state`,
  and `concept_edges` tables with query-time stale passage refresh and
  same-transaction verdict/status cascade.
- Added optional `[vector]` packaging for `sqlite-vec`; core installs and
  `scripts/install.sh` still do not install vector dependencies.
- Added `code-artifact` markdown records plus `code_artifacts` and `code_runs`
  ledgers. The single runner gate remains unavailable until the local `bwrap`
  sandbox proof passes.
- Added `computed` evidence and `code-warrant` items; computed evidence is
  complete only when the referenced code run and output hash still verify.

### Release management

- `release-please` remains `workflow_dispatch`-only and was not dispatched for
  this checkpoint; no tag or GitHub Release is cut.
- Formal release-please versioning, generated release notes, tags, and GitHub
  Releases remain deferred until the first real release.

## [0.1.0a18] - 2026-07-07

Alpha.18 is a source-install checkpoint, not a formal tag or GitHub Release.
The Python package version is bumped so installed local source builds can report
the implemented checkpoint.

### Changed

- Normalized catalog identifiers from `source_id`/`source_type`/journal naming
  to `work_id`/`item_type`/event-log naming.
- Deleted the markdown `work` and `source-note` document types; catalog Works
  stay in SQLite and human Work interpretation is `note` with `mode: work`.
- Normalized bundle roots to `notes/`, `hubs/`, `projects/`, `digests/`, and
  `fulltext/`, with `fulltext` as a frontmatter schema label rather than a DB
  Concept type.
- Added `required_when` schema validation and aligned docs with the live
  frontmatter schemas.
- Bumped the SQLite schema to `user_version = 7`, removed private DB migration
  helpers, and documented delete-and-rebuild for local alpha dev vaults.
- Added schema-doc drift linting and free-join gap analysis over authors,
  institutions, and publication venues.

### Release management

- `release-please` remains `workflow_dispatch`-only and was not dispatched for
  this checkpoint; no tag or GitHub Release is cut.
- Formal release-please versioning, generated release notes, tags, and GitHub
  Releases remain deferred until the first real release.

[Unreleased]: https://github.com/eranroseman/memoria-vault/commits/main
[0.1.0a20]: https://github.com/eranroseman/memoria-vault/compare/c5af51be3da69d1e6b4e212734f2c829d680f158...bc0cd4de81bf9a35e7370965b443c620fc087a8e
[0.1.0a19]: https://github.com/eranroseman/memoria-vault/compare/d9394c7a4caae20f3e5cbfa62b00cd8308373ef7...c5af51be3da69d1e6b4e212734f2c829d680f158
[0.1.0a18]: https://github.com/eranroseman/memoria-vault/compare/b650483f2c9236e6484365f6e43f14f15865d3d5...d9394c7a4caae20f3e5cbfa62b00cd8308373ef7
