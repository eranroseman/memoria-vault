# Distribution model

Memoria ships as a single repo (`memoria-vault`). **The repo is the install unit** — you clone it (or run the one-line bootstrap, which clones it for you), and the bootstrap installer at the repo root deploys everything. The repo has three parts:

| Path | Contents | Audience |
| --- | --- | --- |
| `install.sh` / `install.ps1` (repo root) | The **bootstrap installer**: provisions the stack and deploys the vault. `install.sh` is the real implementation; `install.ps1` is a thin WSL2 launcher. | End users (run once). |
| `vault/` | The starter vault — folder skeleton, Obsidian config, and the `.memoria/` scaffold. The **runtime artifact**. | End users (opened in Obsidian after install). |
| `docs/` | Architecture, workflow, profile, and decision documents. Not needed at runtime. | Developers and contributors. |

The bootstrap copies `vault/` to a working location (off OneDrive on Windows); the human opens **that deployed copy** in Obsidian. The deployed vault is self-contained — it does not carry `docs/`, so any reference from a vault-resident file (e.g. `vault/README.md`) to `docs/` or `project-files/` is a **GitHub URL, never a relative path**. The installers live at the repo root (not inside `vault/`) because the bootstrap is the clone/entry point; consequently **`vault/` is no longer independently installable** — installing requires the whole repo. See [bootstrap-installer.md](../../../project-files/proposals/bootstrap-installer.md) for the full installer design.

---

## What ships in the starter vault

`vault/` is the runtime artifact the bootstrap deploys. It contains:

**Vault skeleton** — numbered top-level folders (`00-meta/` through `95-archive/`) encoding lifecycle stage, with note templates, dashboards, and human-facing reference notes pre-populated.

**`.obsidian/` config** — plugin config stubs and CSS snippets. Auto-hidden from Obsidian's file explorer by the dot-prefix convention.

**`.memoria/` scaffold** — Memoria's tooling directory, dot-prefixed and invisible to Obsidian's vault scanner. Contains:

- `profiles/` — seven hand-authored Hermes profile directories, each with a `SOUL.md` system prompt, `config.yaml`, `mcp.json`, `skills/`, and `cron/`
- `mcp/` — Python sources for `policy_mcp.py` and `policy_hook.py`
- `lane-overrides/` — seven YAML files (one per lane) the policy MCP reads at startup
- `csl/` — Pandoc citation styles

---

## Why the profile install is idempotent

The bootstrap's profile-install step (the function in `install.sh`, also runnable on its own via `--profiles-only`) is designed to be re-run after every `git pull` without care about current state. It refreshes every author-owned file (profile sources, MCP configs, lane-override templates) and leaves human-owned secrets (`.env`, any local overrides) untouched.

The idempotency matters because it is the mechanism that keeps deployed profiles synchronized with the vault source. Without it, the seven profile directories under `~/.hermes/profiles/` would drift from their vault source over time — a drift the Linter's `profile-install-drift` detector catches but cannot fix. The re-run is the fix; making it safe to re-run is what makes the fix actionable.

---

## Why profiles are hand-authored

The seven profile directories share common content — audit-log behavior, common policy invariants, common MCP connections — duplicated across seven copies that must be kept in lockstep by hand. The Linter's `profile-install-drift` detector catches deployed copies diverging from the vault source; inter-profile drift between the seven `SOUL.md` files relies on human review during edits.

A profile compiler that generates profile directories from a shared base plus per-profile overlays would eliminate this duplication. That design is deferred to — the seven-profile scale does not yet make hand-authoring painful enough to justify the complexity.

---

## Related

- On-disk layout reference: [reference/on-disk-layout.md](../../reference/on-disk-layout.md)
- Profile structure: [explanation/profiles/README.md](../profiles/README.md)
- Install steps: [how-to-guides/setup/set-up-the-vault.md](../../how-to-guides/setup/set-up-the-vault.md)
