---
topic: tests
title: Package Gate
status: stable
parent: Test plans
grand_parent: Testing
nav_order: 20
---

# Package Gate

The Package Gate proves the repository can assemble a disposable vault and replay
the deterministic workflow slice without live Obsidian, Zotero, or model quality.

## Run

```bash
scripts/verify package
```

Direct runner:

```bash
bash scripts/e2e-smoke.sh
```

## Pass Criteria

- Source Gate is green first.
- Disposable vault assembly completes.
- Git hooks and executable scripts are wired.
- Bundled plugins, CSS snippets, profiles, and skeleton files are present.
- The model-free workflow replay writes the expected alpha.11 artifacts: a
  checked source, checked project notes, an argument canvas projection, and an
  attention prompt.
- The known forbidden write is denied and audited.
- The evidence bundle records the disposable vault path and checked artifacts.

## Manual Extension

For release candidates, also run installer dry-run and real install checks in
[Release Gate](release-gate.md). The package smoke is PR-safe; the full install
still needs a real throwaway vault.

## Evidence Home

Use the `scripts/verify package` bundle for PR evidence. For release evidence,
link the bundle from the release readiness/stage issue.
