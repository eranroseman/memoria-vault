# Changelog

All notable changes to Memoria are documented here.
Format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).
Versions follow [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

Memoria is in **early pre-alpha development — there is no formal tagged release yet.**
The install path runs from current `main` as an alpha source install.

Release automation is paused (see `.github/workflows/release-please.yml`) so no
versions are minted until the first real release is cut. The earlier
`v0.1.0`–`v0.3.2` tags were release-please artifacts, not real releases, and have
been removed.

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
[0.1.0a18]: https://github.com/eranroseman/memoria-vault/compare/b650483f2c9236e6484365f6e43f14f15865d3d5...main
