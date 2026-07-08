---
title: Memoria configuration
parent: Reference
nav_order: 36
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
| Workspace seed | `src/memoria_vault/product/workspace_seed/**` | copied by `memoria init` | Memoria | Edit source; reinstall or repair workspace | package-seed tests |
| Schema config | `src/memoria_vault/product/workspace_seed/.memoria/schemas/**` | `<workspace>/.memoria/schemas/**` | Memoria | Edit source; reinstall or repair workspace | linter and schema tests |
| Calibration | `src/memoria_vault/product/workspace_seed/.memoria/schemas/calibration.yaml` | `<workspace>/.memoria/schemas/calibration.yaml` | Memoria | Edit source; reinstall or repair workspace | calibration and linter tests |
| Search index state | checked-only BM25 input tree and manifest | `<workspace>/.memoria/index/search/` | generated | Rebuild; do not hand-edit | `memoria doctor --check search` |
| Optional editor adapter settings | adapter package, not the standalone seed | adapter-owned files | adapter owner | Not part of standalone baseline | adapter tests |

## Required redeploys

| Change | Command |
| --- | --- |
| Schema or workspace source config | reinstall or run `memoria doctor --repair`, then run the linter |
| Search index inputs | `memoria workspace rebuild --search` |

Use a disposable workspace under `~/memoria-vault/sandbox` for development verification.

## Never commit

- Model provider keys, local adapter secrets, or API tokens.
- Generated search indexes under `.memoria/index/search/`.
- Runtime vault state, logs, and local diagnostics.

## Related references

- Installer rendering and environment overlays: [Installer (bootstrap)](installer.md)
- Write-gate contract: [Policy gate](policy-mcp.md)
- External integrations: [External integrations](integrations.md)
- Frontmatter fields: [Frontmatter fields](frontmatter.md)
- Calibration thresholds: [Calibration](calibration.md)
- Search: [Search](search.md)
