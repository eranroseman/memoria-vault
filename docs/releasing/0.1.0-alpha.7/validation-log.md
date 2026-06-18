---
title: v0.1.0-alpha.7 validation log
parent: v0.1.0-alpha.7
grand_parent: Releasing
nav_order: 3
---

# v0.1.0-alpha.7 validation log

Alpha.7 closed as an internal checkpoint on 2026-06-18. It did not cut a tag or
GitHub Release; `released` remains `false`.

## Implementation

- Implementation PR: [#677](https://github.com/eranroseman/memoria-vault/pull/677)
- Merge commit: `562ff68e235170735f02f029893ef8f0805f5a99`
- Durable decision: [ADR-81](../../adr/81-persistent-gate-dashboards.md)

## Local Evidence

- `scripts/test.sh all` passed locally: 383 pytest tests passed, static/schema checks
  passed, and `dashboard-field-drift,design-system-drift` was clean.
- `bash scripts/e2e-smoke.sh` passed and reported all gates green.
- `npx --yes cspell@8.19.4 lint --no-progress --no-must-find-files --gitignore "**/*.md"`
  checked 424 markdown files with 0 issues.

## CI Evidence

PR #677 passed the required checks before merge:

- `pr-policy`
- `lint`
- `python-selftest`
- `shellcheck (scripts/install.sh)`
- `PSScriptAnalyzer (scripts/install.ps1)`
- `cspell`
- `markdownlint structural (docs/)`
- `actionlint (.github/workflows)`
- `yamllint (config + workflows)`
- `json syntax (authored)`

## GitHub Closeout

The scoped alpha.7 UI issues were closed against PR #677:

- #659: Having a clear single title on notes
- #663: notes folders
- #664: home.md
- #665: Desk workspace
- #666: workspace plus
- #667: Using base to navigate is un intuitive
- #668: CSS snippets

The `0.1.0-alpha.7` milestone was closed after those issues were closed.

## Runtime Note

The Linux Obsidian launcher accepted the `obsidian://open?path=/home/eranr/Memoria-test`
URI during implementation closeout, but this shell could not observe a persistent
Obsidian process through process lookup. Headless fresh-vault, plugin provenance, schema, and
golden-copy checks passed; no claim of a visual GUI inspection is recorded here.
