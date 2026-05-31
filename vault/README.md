# memoria-vault

The human-facing starter vault for **Memoria** — a research operating system that turns sources into durable knowledge through explicit Kanban states, specialized Hermes agent profiles, and a discipline of human-owned synthesis.

> **Status: v0.1 scaffold.** The vault skeleton, the 10 dashboards plus the `index.md` entry point, the 15 note templates, the 11 human-facing reference notes, the 5 plugin configs, and the 7 profile `SOUL.md` prompts ship in this repo. The wiring around them — `install.ps1`, the per-profile `config.yaml` / `mcp.json` / `.env.EXAMPLE`, the lane-override YAML, the policy and tasks MCP server source — is still being authored. **Clones today are for review, not running.**

## What's here

- `00-meta/` — vault skeleton
  - `01-dashboards/` — 10 dashboards + `index.md` (Daily Health is `index.md`; plus audit-log, board-state, contradictions, discuss-queue, drift-watch, fleet-health, loose-ends, open-questions, reading-pipeline, weekly-review)
  - `02-logs/` — populated Day 1 by the policy MCP (audit.jsonl, board-state.jsonl, lint-findings.jsonl, cron-history.jsonl)
  - `03-templates/` — 15 note templates (claim-note, paper-note, fleeting-note, …)
  - `04-reference/` — 11 human-facing reference notes (agent-roles, profile-policies, schema-reference, system-map, design-system, getting-started, safe-mode, obsidian-config, dataview-cheatsheet, performance-checklist, screening-protocol)
  - `index.md` — vault landing page (pin in sidebar)
  - `research-directions.md` — Librarian's session-start input (populate this)
  - `system-status.md` — runtime health snapshot
- `10-inbox/`, `20-sources/`, `30-synthesis/`, `40-workbench/`, `50-deliverables/`, `90-assets/`, `95-archive/` — empty human-facing folders following the standard numbered-prefix taxonomy
- `.obsidian/` — Obsidian config (auto-hidden by Obsidian)
  - `plugins/<plugin>/data.json{,.example,.TODO}` — five plugin configs (obsidian-Linter, obsidian-citation-plugin, agent-client, obsidian-local-rest-api, callout-manager)
  - `snippets/memoria-link-colors.css` — the Memoria visual-style snippet
- `.memoria/` — Memoria tooling, dot-prefixed and auto-hidden by Obsidian
  - `profiles/memoria-<name>/SOUL.md` — the seven hand-authored Hermes agent prompts (Librarian, Mapper, Socratic, Writer, Verifier, Coder, Linter)
  - `profiles/memoria-linter/M-detectors.md` — the Linter's structural-detector reference
  - `mcp/`, `lane-overrides/` — placeholders for Python MCP source and policy YAML (not yet authored)
  - `csl/`, `library.bib`, `tool-registry.yaml` — machine-read tool config (populated as needed)

The dot-prefix on `.memoria/` is the same trick `.obsidian/` uses: Obsidian's vault scanner auto-ignores both, so the human never sees tooling files in search, graph view, file explorer, or Dataview queries.

## Design docs

The full architectural design — workflows, ADRs, rationale, per-profile design summaries, references — lives in the [`docs/` folder](https://github.com/eranroseman/memoria-vault/tree/main/docs) of this repo (a sibling of this `vault/` folder, not a separate repository). This vault is the **runtime** artifact; `docs/` is the **engineering spec**. Either folder can be used on its own; cross-folder references use a GitHub URL.

## Quick check (what you can do with v0.1)

Clone with any folder name — Memoria is agnostic to it:

```bash
git clone https://github.com/eranroseman/memoria-vault.git my-research-vault
```

Open the folder in Obsidian as a vault. You'll see the numbered folders and templates; tooling stays out of the way. You can read the seven `.memoria/profiles/memoria-*/SOUL.md` prompts and the 10 dashboards + `index.md` (`00-meta/01-dashboards/*.md`) to understand the system. Start with `00-meta/index.md` as the landing page.

You **can't** run Memoria yet — `install.ps1` doesn't exist, the per-profile `config.yaml` / `mcp.json` / `.env.EXAMPLE` files aren't authored, the MCP servers aren't written.

## Roadmap to v0.2 (runnable)

In rough order:

1. ✅ `install.ps1` (Windows) -- ships in this v0.1.1 scaffold. Detects Hermes + Python on PATH, copies any complete profile dirs to `~/.hermes/profiles/memoria-*/`, substitutes `{{VAULT_PATH}}` in `mcp.json`, registers profiles with `hermes profile install --alias --force --yes`, bootstraps `.env` from `.env.EXAMPLE`. **Gracefully skips profiles missing the v0.2 wiring** -- run it today and you'll see all 7 profiles skipped with clear "missing required files" messages.
2. ⬜ `install.sh` (macOS/Linux) -- mirror of `install.ps1`.
3. ⬜ Per-profile `config.yaml`, `mcp.json` (with `{{VAULT_PATH}}` placeholder), `.env.EXAMPLE`, `distribution.yaml` (×7). Each makes its profile installable.
4. ⬜ `.memoria/lane-overrides/*.yaml` -- per-lane policy YAML the policy MCP reads at startup (×7).
5. ⬜ `.memoria/mcp/policy_mcp.py`, `tasks_mcp.py`, `requirements.txt` -- Memoria's two MCP servers.

When the per-profile wiring lands, `./install.ps1` will set up a working Memoria instance on the human's machine.

## Trying install.ps1 today

Even though no profiles will install yet, you can verify the script parses and runs correctly:

```powershell
./install.ps1 -SkipHermesCheck -SkipPythonCheck
```

It should report "0 of 7 installed" with all profiles skipped for "missing required files: config.yaml, mcp.json, distribution.yaml". That's the expected v0.1 behavior. When the wiring is authored for a single profile (say, `memoria-linter`), the next `./install.ps1` run will install just that one.

Useful flags:

- `-Only memoria-linter,memoria-librarian` -- target only specific profiles
- `-SkipHermesCheck` -- bypass the Hermes-on-PATH check
- `-SkipPythonCheck` -- bypass the Python check (until MCP servers need it)

## License

(TBD)
