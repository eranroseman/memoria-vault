---
title: Memoria configuration
parent: System and infrastructure
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
| Policy gate plugin | `vault-template/.memoria/plugins/memoria-policy-gate/plugin.yaml` | workspace policy package for optional adapters | Memoria | Edit source | policy tests |
| Runtime Python package | `pyproject.toml` + `src/memoria_vault/**` | `<workspace>/.memoria/.venv` | Memoria | Edit source; reinstall runtime | installer tests |
| Schema config | `vault-template/.memoria/schemas/**` | workspace source | Memoria | Edit source | linter and schema tests |
| Calibration | `vault-template/.memoria/schemas/calibration.yaml` | workspace source | Memoria | Edit source | calibration and linter tests |
| Search index state | checked-only BM25 input tree and manifest | `<workspace>/.memoria/index/search/` | generated | Rebuild; do not hand-edit | `memoria doctor --check search` |
| Scheduled-task runner | `vault-template/.memoria/scripts/cron-runner.sh` | workspace source for operator-managed scheduled tasks | Memoria | Edit source | shellcheck |
| Optional editor adapter settings | adapter package, not the standalone template | adapter-owned files | adapter owner | Not part of alpha.15 baseline | adapter tests |

## Required redeploys

| Change | Command |
| --- | --- |
| Schema or workspace source config | reinstall or refresh the workspace, then run the linter |
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
