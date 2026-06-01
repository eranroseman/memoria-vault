# memoria-vault

The human-facing starter vault for **Memoria** — a research operating system that turns sources into durable knowledge through explicit Kanban states, specialized Hermes agent profiles, and a discipline of human-owned synthesis.

> **Status: Memoria v0.1.** The v0.1 system is the complete system (see the glossary) and ships in this repo: the vault skeleton, the 10 dashboards plus the `index.md` entry point, the 16 note templates, the 11 human-facing reference notes, the **8 bundled, pre-configured Obsidian plugins**, and the **7 Hermes profiles with full wiring** (`SOUL.md` + `config.yaml` + `mcp.json` + `distribution.yaml`), plus the policy MCP servers under `.memoria/mcp/` and the lane-override policy YAML. Profiles install today via the repo-root `install.ps1` / `install.sh`. **Not yet verified end-to-end** — a few v0.1 pieces are still pending (e.g. K-Dense skills); see the [implementation status ledger](https://github.com/eranroseman/memoria-vault/blob/main/project-files/operations/implementation-status.md) for exact build state.

## What's here

- `00-meta/` — vault skeleton
  - `01-dashboards/` — 10 dashboards + `index.md` (Daily Health is `index.md`; plus audit-log, board-state, contradictions, discuss-queue, drift-watch, fleet-health, loose-ends, open-questions, reading-pipeline, weekly-review)
  - `02-logs/` — populated at runtime by the policy MCP (audit.jsonl, board-state.jsonl, lint-findings.jsonl, cron-history.jsonl)
  - `03-templates/` — 16 note templates (claim-note, paper-note, fleeting-note, …)
  - `04-reference/` — 11 human-facing reference notes (agent-roles, profile-policies, schema-reference, system-map, design-system, getting-started, safe-mode, obsidian-config, dataview-cheatsheet, performance-checklist, screening-protocol)
  - `index.md` — vault landing page (pin in sidebar)
  - `research-directions.md` — Librarian's session-start input (populate this)
  - `system-status.md` — runtime health snapshot
- `10-inbox/`, `20-sources/`, `30-synthesis/`, `40-workbench/`, `50-deliverables/`, `90-assets/`, `95-archive/` — empty human-facing folders following the standard numbered-prefix taxonomy
- `.obsidian/` — Obsidian config (auto-hidden by Obsidian)
  - `plugins/<id>/` — the **8 bundled, pre-configured community plugins**: `obsidian-local-rest-api`, `agent-client`, `dataview`, `templater-obsidian`, `quickadd`, `obsidian-citation-plugin`, `callout-manager`, `obsidian-git`. Secret/per-machine configs (REST API, agent-client) ship as `data.json.example` and are gitignored.
  - `snippets/memoria-link-colors.css` — the Memoria visual-style snippet
- `.memoria/` — Memoria tooling, dot-prefixed and auto-hidden by Obsidian
  - `profiles/memoria-<name>/` — the seven Hermes profiles (Librarian, Mapper, Socratic, Writer, Verifier, Coder, Linter), each with `SOUL.md` + `config.yaml` + `mcp.json` + `distribution.yaml`, plus `skills/` and `cron/`
  - `profiles/memoria-linter/structural-detectors.md` — the Linter's structural-detector reference
  - `mcp/` — the policy MCP servers (`policy_mcp.py`, `policy_hook.py`, `board_export.py`, `metrics_aggregate.py`) + `requirements.txt`
  - `lane-overrides/` — per-lane policy YAML the policy MCP reads at startup
  - `csl/`, `library.bib`, `tool-registry.yaml` — machine-read config (populated as needed)

The dot-prefix on `.memoria/` is the same trick `.obsidian/` uses: Obsidian's vault scanner auto-ignores both, so the human never sees tooling files in search, graph view, file explorer, or Dataview queries.

## Design docs

The full architectural design — workflows, ADRs, rationale, per-profile design summaries, references — lives in the [`docs/` folder](https://github.com/eranroseman/memoria-vault/tree/main/docs) of this repo (a sibling of this `vault/` folder, not a separate repository). This vault is the **runtime** artifact; `docs/` is the **engineering spec**.

## Install

The installers live at the **repository root** (one level above this `vault/` folder). From the repo root:

```powershell
./install.ps1     # Windows (profiles run under WSL2)
```

```bash
./install.sh      # Ubuntu/Debian or WSL2
```

They stage each profile, substitute `{{VAULT_PATH}}`, and register the seven profiles with Hermes (`hermes profile install … --force`), then bootstrap each profile's `.env` from its `.env.EXAMPLE` if absent. They are idempotent — safe to re-run after a `git pull`. Prerequisites (Hermes, Python) and the full setup of Obsidian, Zotero + Better BibTeX, and secrets are covered in [docs/how-to-guides/setup/](https://github.com/eranroseman/memoria-vault/tree/main/docs/how-to-guides/setup).

A **one-line full-stack bootstrap installer** (which also installs Obsidian, Hermes, and Zotero) is implemented — see [docs: bootstrap installer](https://github.com/eranroseman/memoria-vault/blob/main/docs/explanation/architecture/bootstrap-installer.md) (design) and [reference/installer.md](https://github.com/eranroseman/memoria-vault/blob/main/docs/reference/installer.md) (inventories).

Useful installer flags:

- `-Only memoria-linter,memoria-librarian` / `--only memoria-linter` — target specific profiles
- `-SkipHermesCheck` / `--skip-hermes-check` — bypass the Hermes-on-PATH check
- `-SkipPythonCheck` / `--skip-python-check` — bypass the Python check

## Versioning

Memoria's release version and each Hermes profile package `version` are kept in lockstep — both are `0.1.0` for this release. The profiles ship and install together, so they are not versioned independently. The separate `hermes_requires` field in each `distribution.yaml` is the Hermes **runtime** dependency (`>=0.12.0`), not a Memoria version.

## License

(TBD)
