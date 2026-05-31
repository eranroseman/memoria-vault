# Distribution model

Memoria ships as a single repo (`memoria-vault`) with two top-level folders that serve different audiences and can be used independently.

| Folder | Contents | Audience |
| --- | --- | --- |
| `docs/` | Architecture, workflow, profile, and decision documents. Not needed at runtime. | Developers and contributors. |
| `vault/` | The starter vault: folder skeleton, Obsidian config, `.memoria/` scaffold, and `install.ps1`. | End users. |

The human opens `vault/` directly in Obsidian. The engineering docs explain how the system works but are not required for it to function. Because a user may use only one folder, any cross-folder reference is a GitHub URL, never a relative path.

---

## What ships in the starter vault

The starter vault is the single distributable artifact. Cloning it gives the human:

**Vault skeleton** — numbered top-level folders (`00-meta/` through `95-archive/`) encoding lifecycle stage, with note templates, dashboards, and human-facing reference notes pre-populated.

**`.obsidian/` config** — plugin config stubs and CSS snippets. Auto-hidden from Obsidian's file explorer by the dot-prefix convention.

**`.memoria/` scaffold** — Memoria's tooling directory, dot-prefixed and invisible to Obsidian's vault scanner. Contains:

- `profiles/` — seven hand-authored Hermes profile directories, each with a `SOUL.md` system prompt, `config.yaml`, `mcp.json`, `skills/`, and `cron/`
- `mcp/` — Python sources for `policy_mcp.py` and `policy_hook.py`
- `lane-overrides/` — seven YAML files (one per lane) the policy MCP reads at startup
- `csl/` — Pandoc citation styles

---

## Why `install.ps1` is idempotent

`install.ps1` is designed to be re-run after every `git pull` without requiring care about current state. It refreshes every author-owned file (profile sources, MCP configs, lane-override templates) and leaves human-owned secrets (`.env`, any local overrides) untouched.

The idempotency matters because the install script is the mechanism that keeps deployed profiles synchronized with the vault source. Without it, the seven profile directories under `~/.hermes/profiles/` would drift from their vault source over time — a drift the Linter's `profile-install-drift` detector catches but cannot fix. The script is the fix; making it safe to re-run is what makes the fix actionable.

---

## Why profiles are hand-authored

The seven profile directories share common content — audit-log behavior, common policy invariants, common MCP connections — duplicated across seven copies that must be kept in lockstep by hand. The Linter's `profile-install-drift` detector catches deployed copies diverging from the vault source; inter-profile drift between the seven `SOUL.md` files relies on human review during edits.

A profile compiler that generates profile directories from a shared base plus per-profile overlays would eliminate this duplication. That design is deferred to — the seven-profile scale does not yet make hand-authoring painful enough to justify the complexity.

---

## Related

- On-disk layout reference: [reference/on-disk-layout.md](../../reference/on-disk-layout.md)
- Profile structure: [explanation/profiles/README.md](../profiles/README.md)
- Install steps: [how-to-guides/setup/set-up-the-vault.md](../../how-to-guides/setup/set-up-the-vault.md)
