---
title: Distribution model
parent: Deployment
nav_order: 1
---

# Distribution model

Memoria ships as a single repo (`memoria-vault`), version **0.1.1**. **The repo is the install unit** ([ADR-26](../../adr/26-repo-as-install-unit.md), as amended by [ADR-55](../../adr/55-src-scaffold-populate-golden-copy.md)) — you clone it (or run the one-line bootstrap, which clones it for you), and the bootstrap installer at the repo root deploys everything. The repo has three parts:

| Path | Contents | Audience |
| --- | --- | --- |
| `scripts/install.sh` / `scripts/install.ps1` (repo root) | The **bootstrap installer**: provisions the stack and derives the vault. `scripts/install.sh` is the real implementation; `scripts/install.ps1` is a thin WSL2 launcher. | End users (run once). |
| `src/` | **Source files only — never a live vault**: templates, profiles, skills, schemas, dashboards, patterns, and `.obsidian` config. The installer *scaffolds* the vault tree and *populates* it from here. | The installer (and contributors). |
| `docs/` | Architecture, workflow, and decision documents. Not needed at runtime. | Developers and contributors. |

The installer derives the running vault from `src/` at a working location (off OneDrive on Windows); the human opens **that deployed vault** in Obsidian. The deployed vault is self-contained — it does not carry `docs/`, so any reference from a vault-resident file (e.g. `home.md`) to `docs/` is a **GitHub Pages URL, never a relative path**. The installers live at the repo root (not inside `src/`) because the bootstrap is the clone/entry point; installing requires the whole repo. See [Bootstrap installer](bootstrap-installer.md) for the installer's design and [Installer (bootstrap)](../../reference/installer.md) for the component inventories.

Shipping `src/` rather than a live `vault/` template is deliberate ([ADR-55](../../adr/55-src-scaffold-populate-golden-copy.md)): a live-vault template blurs "source of truth" with "a running instance," invites accidental edits to the template, and offers no recovery path. With `src/`, authoring (the repo) and restoring (the runtime golden copy) stay cleanly separate, and user content and system files are structurally distinct from the first minute.

---

## What ships in `src/`

**Vault skeleton** — the type-first category tree ([ADR-47](../../adr/47-type-first-category-folders.md)): `catalog/`, `notes/`, `projects/`, `inbox/`, `system/`, with templates, dashboards, Bases, and `home.md` pre-populated. Empty content dirs are recreated by the installer's scaffold step, checked against the machine-read folder map (`.memoria/schemas/folders.yaml`).

**`.obsidian/` config** — Bases definitions, plugin config, layouts, graph color-groups. Auto-hidden from Obsidian's file explorer by the dot-prefix convention.

**`.memoria/` scaffold** — Memoria's hidden runtime directory: `profiles/` (the five agents), `engines/` (ingest · linter · sweeps), `mcp/` (the policy boundary), `schemas/` (the type schemas and folder map), `lane-overrides/`, `scripts/`, and `memoria.bib`.

## The golden copy: the restore source

At install time, every system file is also staged at `<vault>/.memoria/golden/` with a hash manifest. That golden copy is what makes the deployed vault **self-healing for system files**: the Linter's daily pass compares the live system files against the manifest, flags drift, and can restore a corrupted or hand-mangled file from the known-good baseline (`lint:restore` — propose-only by default) without re-running the installer. Releases refresh the golden copy by fresh install — never by in-place migration, whose half-migrated states are the failure mode D52 rejected.

---

## The five profiles: one shared layer, four unique files

The agents ship as five hand-authored profile directories under `src/.memoria/profiles/` — `memoria-copi`, `memoria-librarian`, `memoria-writer`, `memoria-peer-reviewer`, `memoria-engineer`. Each agent is a **shared layer + a unique layer** (D46):

- **Shared:** `AGENTS.md` — the one "how we work in this vault" instruction set every agent reads, living in the vault root so there is exactly one copy of the house rules.
- **Unique per agent:** `SOUL.md` (its posture — the stable stance, like *faithful* or *skeptical*), `config.yaml` (model + tools), `skills/` (assigned per lane), and `mcp.json` (connections). `distribution.yaml` packages it.

So the agents share the house rules but each brings its own stance and toolset. The old failure mode — seven near-identical SOUL files duplicating common policy by hand — is gone structurally: common content has one home (`AGENTS.md`), and what remains per-profile is genuinely per-profile. At five profiles, hand-authoring the unique layers stays cheap, and a profile compiler remains unnecessary.

## Why the profile install is idempotent

The bootstrap's profile-install step (also runnable on its own via `--profiles-only`) is designed to be re-run after every `git pull` without care about current state. It refreshes every author-owned file (profile sources, MCP configs, lane-override templates), **prunes** stale `memoria-*` profiles that are no longer shipped (the v0.1.0 seven-profile set), and leaves human-owned secrets (`.env`, any local overrides) untouched.

The idempotency matters because it is the mechanism that keeps deployed profiles synchronized with their source. Without it, the profile directories under `~/.hermes/profiles/` would drift from the repo over time — a drift the Linter detects but the re-run fixes; making the re-run safe is what makes the fix actionable.

---

## Related

- The installer's design: [Bootstrap installer](bootstrap-installer.md)
- The decisions: [ADR-55](../../adr/55-src-scaffold-populate-golden-copy.md), [ADR-26](../../adr/26-repo-as-install-unit.md)
- Profile structure: [Profiles](../profiles/README.md)
- Operationalizes idempotent deployment: [Redeploy profiles](../../how-to-guides/operate/redeploy-profiles.md)
- On-disk layout reference: [On-disk layout](../../reference/on-disk-layout.md)
