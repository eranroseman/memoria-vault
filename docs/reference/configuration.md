---
title: Memoria configuration
parent: Reference
---

# Memoria configuration

Memoria configuration is split across repo-authored source, rendered Hermes
profiles, runtime vault files, Obsidian plugin files, and per-machine secrets.
This page is the ownership ledger: field-level contracts stay in the linked
reference pages and schema files.

## Configuration surfaces

| Surface | Source | Installed location | Owner | Edit policy | Validator |
| --- | --- | --- | --- | --- | --- |
| Hermes profile config | `src/.memoria/profiles/memoria-*/config.yaml` | `~/.hermes/profiles/memoria-*/config.yaml` | Memoria | Edit source, then redeploy profiles | `tests/test_profiles.py` |
| Profile metadata | `src/.memoria/profiles/memoria-*/distribution.yaml` | Hermes profile manifest | Memoria | Edit source | `tests/test_profiles.py` |
| Profile identity | `src/.memoria/profiles/memoria-*/SOUL.md` | Hermes profile directory | Memoria, with PI customization inside release limits | Edit source; reconcile runtime drift intentionally | profile docs and tests |
| Bundled profile skills | `src/.memoria/profiles/*/skills/` | Hermes profile directory | Memoria | Edit source | profile tests |
| Tool capability registry | `src/.memoria/tool-registry.yaml` | vault source and runtime vault | Memoria | Edit source | `tests/test_profiles.py` |
| Lane policy overlays | `src/.memoria/lane-overrides/*.yaml` | vault source and runtime vault | Memoria | Edit source | policy tests |
| Policy gate plugin | `src/.memoria/plugins/memoria-policy-gate/plugin.yaml` | Hermes profile plugins | Memoria | Edit source | policy tests |
| MCP server config | embedded in each profile `config.yaml` | Hermes profile config | Memoria | Edit source, then redeploy profiles | profile and MCP tests |
| MCP Python dependencies | `src/.memoria/mcp/requirements*.txt` | `<vault>/.memoria/.venv` | Memoria | Edit source; reinstall deps | installer tests |
| Project hints | `src/.memoria/project-hints.yaml.example` | `<vault>/.memoria/project-hints.yaml` | PI | Copy-on-first-use; absent means manual tagging | project-hints guide and linter checks |
| Schema config | `src/.memoria/schemas/**` | vault source and runtime vault | Memoria | Edit source | linter and schema tests |
| Calibration | `src/.memoria/schemas/calibration.yaml` | vault source and runtime vault | Memoria | Edit source | calibration and linter tests |
| Obsidian plugin settings | `src/.obsidian/plugins/**` | runtime vault `.obsidian/plugins/**` | Memoria except local secrets | Shipped config; reconcile intentionally | plugin docs and status checks |
| Local REST API secrets | example files only | runtime plugin `data.json` plus profile `.env` | PI machine | Never commit live secrets | setup docs |
| Profile environment variables | `.env.EXAMPLE` in each profile | `~/.hermes/profiles/<profile>/.env` | PI machine | Never commit; seed from shared Hermes env | installer smoke |
| Shared Hermes environment seed | not in repo | `~/.hermes/.env` | PI machine | Never commit; rerun profiles-only after changes | installer propagation |
| qmd index config and state | scripts plus runtime collection | `.qmd/` and runtime qmd store | generated | Rebuild; do not hand-edit | qmd scripts |
| Cron wrappers | `src/.memoria/scripts/*.sh` | vault source and Hermes cron commands | Memoria | Edit source | shellcheck |

## Rendered versus authored

`src/.memoria/profiles/**/config.yaml` is authored source.
`~/.hermes/profiles/**/config.yaml` is rendered installed output. If the two
drift, fix the source and redeploy unless the drift is an intentional local
experiment.

Profile `.env` files are user-owned secret stores. They are not source, and
Hermes profile runs read the profile-local `.env` rather than inheriting a
global fallback.

Memoria profiles do not use standalone `mcp.json`. MCP servers live in profile
`config.yaml`; an installed `~/.hermes/profiles/memoria-*/mcp.json` is legacy
stale state.

## Required redeploys

| Change | Command |
| --- | --- |
| Profile config, tools, MCP servers, or model overlay | `bash scripts/install.sh --profiles-only --vault ~/Memoria-test` |
| Secrets added or rotated in `~/.hermes/.env` | `bash scripts/install.sh --profiles-only --vault ~/Memoria-test` |
| Schema or vault source config | reinstall or refresh the vault, then run the linter |
| qmd index inputs | `bash scripts/qmd-codebase-index.sh --embed` |

Use the production vault path instead of `~/Memoria-test` only when you are
deploying a real runtime vault. Development verification uses the test vault.

## Never commit

- `OBSIDIAN_API_KEY`, model provider keys, or API tokens.
- Profile `.env` files.
- Local REST API live `data.json`.
- Generated qmd indexes.
- Runtime vault state, logs, and local diagnostics.

## Related references

- Profile surfaces and capability gates: [Profile capabilities](profiles.md)
- Installer rendering and environment overlays: [Installer (bootstrap)](installer.md)
- Write-gate contract: [Policy MCP](policy-mcp.md)
- Obsidian plugin files: [Obsidian plugin data files](obsidian-plugin-data-files.md)
- Obsidian plugin settings: [Obsidian plugin settings](obsidian-plugin-settings.md)
- External integrations: [External integrations](integrations.md)
- Frontmatter fields: [Frontmatter fields](frontmatter.md)
- Calibration thresholds: [Calibration](calibration.md)
- Search and qmd: [Search](search.md)
