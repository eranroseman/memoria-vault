# Distribution model

Memoria ships as a single repo (`memoria-vault`) with two top-level folders that serve different audiences and can be used independently.

| Folder | Contents | Audience |
| --- | --- | --- |
| `docs/` and `docs2/` | Architecture, workflow, profile, and decision documents. Not needed at runtime. | Developers and contributors. |
| `vault/` | The starter vault: folder skeleton, Obsidian config, `.memoria/` scaffold, and `install.ps1`. | End users. |

The human opens `vault/` directly in Obsidian. The engineering docs explain how the system works but are not required for it to function. Because a user may use only one folder, any cross-folder reference is a GitHub URL, never a relative path.

---

## What ships in the starter vault

The starter vault is the single distributable artifact. Cloning it gives the human:

**Vault skeleton** — numbered top-level folders (`00-meta/` through `95-archive/`) encoding lifecycle stage, with note templates, dashboards, and human-facing reference notes pre-populated.

**`.obsidian/` config** — plugin config stubs and CSS snippets. Auto-hidden from Obsidian's file explorer by the dot-prefix convention.

**`.memoria/` scaffold** — Memoria's tooling directory, dot-prefixed and invisible to Obsidian's vault scanner. Contains:

- `profiles/` — seven hand-authored Hermes profile directories, each with a `SOUL.md` system prompt and (in v0.2) `config.yaml`, `mcp.json`, `skills/`, and `cron/`
- `mcp/` — Python sources for `policy_mcp.py` and `tasks_mcp.py` (v0.2)
- `lane-overrides/` — seven YAML files (one per lane) the policy MCP reads at startup
- `csl/` — Pandoc citation styles

---

## What `install.ps1` does

`install.ps1` is idempotent: re-running after `git pull` refreshes every author-owned file and leaves human-owned secrets untouched.

For each of the seven profiles it: stages the profile files, substitutes `{{VAULT_PATH}}` in `mcp.json` with the vault's absolute path, runs `hermes profile install`, and bootstraps `.env` from `.env.EXAMPLE` on first install only.

---

## v0.1 vs. v0.2 split

| Component | v0.1 (shipped) | v0.2 (next milestone) |
| --- | --- | --- |
| Vault skeleton + templates + dashboards | ✓ | — |
| `SOUL.md` prompts (all 7 profiles) | ✓ | — |
| `install.ps1` (Windows) | ✓ | `install.sh` (macOS / Linux) |
| `config.yaml`, `mcp.json`, `distribution.yaml` | Not authored | Required for `hermes profile install` |
| `policy_mcp.py`, `tasks_mcp.py` | Not authored | Runtime enforcement |
| Lane-override YAML files | ✓ (vault-side) | Policy MCP reads + enforces them |
| Kanban board | Not authored | Phase 4 |

---

## Why profiles are hand-authored

The seven profile directories share common content — audit-log behavior, common policy invariants, common MCP connections — duplicated across seven copies that must be kept in lockstep by hand. The Linter's `profile-install-drift` detector catches deployed copies diverging from the vault source; inter-profile drift between the seven `SOUL.md` files relies on human review during edits.

A profile compiler that generates profile directories from a shared base plus per-profile overlays would eliminate this duplication. That design is deferred to Phase 2 — the seven-profile scale does not yet make hand-authoring painful enough to justify the complexity.

---

## Related

- On-disk layout reference: [reference/on-disk-layout.md](../../reference/on-disk-layout.md)
- Profile structure: [explanation/profiles/README.md](../profiles/README.md)
- Install steps: [how-to-guides/setup/set-up-the-vault.md](../../how-to-guides/setup/set-up-the-vault.md)
