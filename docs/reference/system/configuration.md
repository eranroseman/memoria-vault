---
title: Memoria configuration
parent: System and infrastructure
nav_order: 1
grand_parent: Reference
---

# Memoria configuration

Memoria configuration is split across repo-authored source, runtime workspace
files, optional adapter files, and per-machine secrets.
This page is the ownership ledger; field-level contracts stay in the
linked reference pages and schema files.

## Configuration surfaces

| Surface | Source | Installed location | Owner | Edit policy | Validator |
| --- | --- | --- | --- | --- | --- |
| Runtime Python package | `pyproject.toml` + `src/memoria_vault/**` | `<workspace>/.memoria/.venv` | Memoria | Edit source; reinstall runtime | installer tests |
| Runtime-managed workspace seed | Packaged seed paths except the PI-owned preference and first-init bundle rows below | copied by `memoria init` | Memoria | Edit source; reinstall or repair workspace | package-seed tests |
| PI-owned view preferences | `catalog.base`, `claims.base`, `inbox.base`, `projects.base`, `sources.base`, `.obsidian/graph.json`, `.obsidian/types.json`, `steering.md`, `system/vocabulary.md` in `src/memoria_vault/product/workspace_seed/` | copied by `memoria init`; Obsidian files and Base files are skipped by `--no-obsidian` | PI after bootstrap | Edit the installed copy directly; `memoria doctor --repair` restores only a missing copy and preserves an existing one | seed-lifecycle tests |
| First-init agent/MCP bundle | `src/memoria_vault/product/workspace_seed/.claude/`, `src/memoria_vault/product/workspace_seed/.codex/hooks.json`, `src/memoria_vault/product/workspace_seed/.mcp.json`, `src/memoria_vault/product/workspace_seed/CLAUDE.md` | copied once by `memoria init`, including `--no-obsidian` | PI after bootstrap | Configure hosts; `memoria doctor --repair` neither creates nor overwrites it | package-seed tests |
| Schema config | `src/memoria_vault/product/workspace_seed/.memoria/schemas/**` | `<workspace>/.memoria/schemas/**` | Memoria | Edit source; reinstall or repair workspace | linter and schema tests |
| Search index state | checked-only BM25 input tree and manifest | `<workspace>/.memoria/index/search/` | generated | Rebuild; do not hand-edit | `memoria doctor --check search` |
| Optional editor adapter settings | adapter package, not the standalone seed | adapter-owned files | adapter owner | Not part of standalone baseline | adapter tests |

## Required redeploys

| Change | Command |
| --- | --- |
| Schema or runtime-managed workspace source config | reinstall or run `memoria doctor --repair`, then run the linter |
| PI-owned view preference | edit the installed copy directly; repair only restores a missing copy |
| First-init agent/MCP configuration | configure the PI-owned copy directly; repair does not manage it |
| Search index inputs | `memoria workspace rebuild --search` |

Use a disposable workspace under `~/memoria-vault/test-vault` for development verification.

## Model token ceiling

`MEMORIA_MODEL_TOKEN_CEILING` limits live model use in one process. It accepts a
nonnegative integer; when unset or set to `0`, it is disabled. Actual model
token usage accumulates for the process, and a later model call is refused once
the ceiling has been reached.

## Never commit

- Model provider keys, local adapter secrets, or API tokens.
- Generated search indexes under `.memoria/index/search/`.
- Runtime vault state, logs, and local diagnostics.

## Related references

- Installer rendering and environment overlays: [Installer (bootstrap)](installer.md)
- Write-gate contract: [Policy gate](../control-and-policy/policy-mcp.md)
- External integrations: [External integrations](../evidence-and-integrations/integrations.md)
- Frontmatter fields: [Frontmatter fields](../data-model/frontmatter.md)
- Score calibration: [Calibration](../analysis-and-surfaces/calibration.md)
- Search: [Search](../pipelines-and-io/search.md)
