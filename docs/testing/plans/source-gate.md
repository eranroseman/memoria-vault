---
topic: tests
title: Source Gate
status: stable
parent: Test plans
grand_parent: Testing
nav_order: 10
---

# Source Gate

The Source Gate proves the repository is coherent before any vault, GUI, or live
runtime work starts.

## Run

```bash
scripts/verify pr
```

For bisection:

```bash
scripts/test.sh l1
scripts/test.sh l0
```

## Pass Criteria

- `pytest tests/` passes.
- Static docs, links, generated references, status docs, agent docs, ruleset
  contract, GitHub hygiene, plugin provenance, Python compile, shell parse, and
  dashboard/design drift checks pass.
- Installer lint passes locally when `shellcheck`/PowerShell are available; CI
  enforces the required installer checks either way.
- The evidence bundle records the commit and command results.

## What This Gate Does Not Prove

- Live Hermes, Obsidian, Zotero, or model connectivity.
- Product quality.
- GUI/Bases rendering.
- Clean install on a fresh machine.

## Evidence Home

Use the `scripts/verify pr` `summary.json` bundle or the matching CI run. Do not
copy routine Source Gate output into docs.
