---
topic: architecture
---

# Distribution model

Memoria ships as two repos with distinct roles. One holds the engineering design documents; the other is the distributable artifact — the starter vault — which the human clones, opens in Obsidian, and installs from with a single script.

## The two repos

| Repo | Contents | Audience |
| --- | --- | --- |
| `memoria-docs` | ~125 architecture, workflow, profile, and decision documents. Not needed at runtime. | Developers and contributors. |
| `memoria-vault` | The starter vault: vault skeleton, Obsidian config, `.memoria/` scaffold including the seven hand-authored profile directories, and `install.ps1`. | End users. |

The human's vault is a clone of `memoria-vault` opened directly in Obsidian. The engineering docs in `memoria-docs` are a separate concern — they explain how the system works but are not required for it to function.

## What ships in the starter vault

The starter vault is the **single distributable artifact**. Cloning it gives the human:

- **Vault skeleton** — numbered top-level folders (`00-meta/` through `95-archive/`) encoding lifecycle stage, with the note templates, dashboards, and human-facing reference notes pre-populated.
- **`.obsidian/` config** — plugin config stubs and CSS snippets; auto-hidden from the Obsidian file explorer by the dot-prefix convention.
- **`.memoria/` scaffold** — Memoria's tooling directory, also dot-prefixed and therefore invisible to Obsidian's vault scanner. Contains:
  - `profiles/` — seven hand-authored Hermes profile directories (`memoria-librarian/` through `memoria-linter/`), each with a `SOUL.md` system prompt and (in v0.2) `config.yaml`, `mcp.json`, `skills/`, and `cron/`.
  - `mcp/` — Python sources for `policy_mcp.py` and `tasks_mcp.py` (v0.2; not yet authored in v0.1).
  - `lane-overrides/` — one YAML file per lane that the policy MCP reads at startup (v0.2).
  - `csl/` — Pandoc citation styles.

See [architecture/on-disk-layout.md](on-disk-layout.md) for the full annotated tree.

## What `install.ps1` does

`install.ps1` is the single install entry point on Windows. It is **idempotent**: re-running after `git pull` refreshes every author-owned file and leaves human-owned secrets untouched.

Steps:
1. Verify Hermes and Python are on PATH (each check is skippable during early development).
2. Install MCP server Python dependencies from `.memoria/mcp/requirements.txt` (skipped gracefully if the file does not exist in v0.1).
3. For each of the seven profiles, copy `.memoria/profiles/<name>/` to a temp staging directory, substitute the `{{VAULT_PATH}}` placeholder in `mcp.json` with the vault's absolute path (forward-slash form), then run `hermes profile install` to write the result to `~/.hermes/profiles/memoria-<name>/`.
4. Bootstrap `.env` from `.env.EXAMPLE` on first install; preserve existing `.env` on subsequent runs.

What `install.ps1` does **not** do in v0.1:
- No YAML wiring (`config.yaml`, `mcp.json`, `distribution.yaml` are v0.2 artifacts; profiles missing these files are skipped with a clear message).
- No MCP setup (policy and task MCP servers are not yet authored).
- No lane-override installation (the YAML files are v0.2).

After the script runs, the human opens the vault in Obsidian, fills in `.env` credentials, and starts a session with `hermes -p memoria-librarian chat`.

## v0.1 vs. v0.2 split

| Component | v0.1 (ships now) | v0.2 (next milestone) |
| --- | --- | --- |
| Vault skeleton | Shipped | — |
| 15 note templates | Shipped | — |
| 11 dashboards | Shipped | — |
| `SOUL.md` prompts (all 7 profiles) | Shipped | — |
| `install.ps1` (Windows) | Shipped | `install.sh` (macOS / Linux) |
| `config.yaml`, `mcp.json`, `distribution.yaml` | Not authored | Required for `hermes profile install` |
| `policy_mcp.py`, `tasks_mcp.py` | Not authored | Runtime enforcement |
| Lane-override YAML files | Not authored | Policy MCP reads at startup |
| Kanban board | Not authored | Phase 4 |

## Profile compiler vision (deferred, Phase 2)

The seven profile directories are **hand-authored**. Shared content — audit-log behavior, common policy invariants, common MCP connections — lives in seven copies that must be kept in lockstep by hand. The Linter's `profile-install-drift` detector catches deployed copies diverging from the vault source; inter-profile drift between the seven `SOUL.md` files relies on human review during edits.

A **profile compiler** that generates profile directories from a shared base plus per-profile overlays would eliminate this duplication. That design is documented in [roadmap/profile-compilation.md](../../project/roadmap/profile-compilation.md) and deferred to Phase 2 — the seven-profile scale does not yet make hand-authoring painful enough to justify the complexity.

## Related

- [architecture/on-disk-layout.md](on-disk-layout.md) — full annotated vault and runtime tree, installer flow, version-control rules
- [profiles/README.md](../profiles/README.md) — the seven profiles, their missions, and the lane-override YAML format