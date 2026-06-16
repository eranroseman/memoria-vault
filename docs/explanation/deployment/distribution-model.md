---
title: Distribution model
parent: Deployment
nav_order: 1
---

# Distribution model

Memoria ships as a single repo (`memoria-vault`), version **0.1.0-alpha.2**. **The repo is the install unit** ([ADR-26](../../adr/26-repo-as-install-unit.md), as amended by [ADR-55](../../adr/55-src-scaffold-populate-golden-copy.md)) — you clone it (or run the one-line bootstrap, which clones it for you), and the bootstrap installer at the repo root deploys everything. The repo has three parts:

| Path | Contents | Audience |
| --- | --- | --- |
| `scripts/install.ps1` / `scripts/install.sh` (repo root) | The **bootstrap installers**: native Windows production via PowerShell, Linux/WSL testing via bash. Both derive the vault from `src/` and deploy the same profile/runtime source. | End users (run once). |
| `src/` | **Source files only — never a live vault**: templates, profiles, skills, schemas, dashboards, patterns, and `.obsidian` config. The installer *scaffolds* the vault tree and *populates* it from here. | The installer (and contributors). |
| `docs/` | Architecture, workflow, and decision documents. Not needed at runtime. | Developers and contributors. |

The installer derives the running vault from `src/` at a working location (off OneDrive on Windows); the human opens **that deployed vault** in Obsidian. The deployed vault is self-contained — it does not carry `docs/`, so any reference from a vault-resident file (e.g. `home.md`) to `docs/` is a **GitHub Pages URL, never a relative path**. The installers live at the repo root (not inside `src/`) because the bootstrap is the clone/entry point; installing requires the whole repo. See [Bootstrap installer](bootstrap-installer.md) for the installer's design and [Installer (bootstrap)](../../reference/installer.md) for the component inventories.

Shipping `src/` rather than a live `vault/` template is deliberate ([ADR-55](../../adr/55-src-scaffold-populate-golden-copy.md)): a live-vault template blurs "source of truth" with "a running instance," invites accidental edits to the template, and offers no recovery path. With `src/`, authoring (the repo) and restoring (the runtime golden copy) stay cleanly separate, and user content and system files are structurally distinct from the first minute.

---

## What ships in `src/`

`src/` carries three kinds of source: the **vault skeleton** (the type-first category tree, [ADR-47](../../adr/47-type-first-category-folders.md), with templates, dashboards, Bases, and `home.md` pre-populated), the **`.obsidian/` config**, and the **`.memoria/` scaffold** (profiles, engines, the policy MCP, schemas, lane-overrides, scripts, and `memoria.bib`). The full directory catalog — every folder and what it holds — is owned by [On-disk layout](../../reference/on-disk-layout.md); the design rationale for the category tree is [The vault](../architecture/vault.md). Empty content dirs are recreated by the installer's scaffold step, checked against the machine-read folder map (`.memoria/schemas/folders.yaml`).

## The golden copy: the restore source

At install time, every system file is also staged at `<vault>/.memoria/golden/` with a hash manifest. That golden copy is what makes the deployed vault **self-healing for system files**: the Linter's daily pass compares the live system files against the manifest, flags drift, and can restore a corrupted or hand-mangled file from the known-good baseline (`lint:restore` — propose-only by default) without re-running the installer. Releases refresh the golden copy by fresh install — never by in-place migration, whose half-migrated states [ADR-55](../../adr/55-src-scaffold-populate-golden-copy.md) avoids.

---

## The five profiles: one shared layer, four unique files

The agents ship as five hand-authored profile directories under `src/.memoria/profiles/` — `memoria-copi`, `memoria-librarian`, `memoria-writer`, `memoria-peer-reviewer`, `memoria-engineer`. Each agent is a **shared layer + a unique layer** ([ADR-48](../../adr/48-copi-and-agent-consolidation.md)):

- **Shared:** `AGENTS.md` — the one "how we work in this vault" instruction set every agent reads, living in the vault root so there is exactly one copy of the house rules.
- **Unique per agent:** `SOUL.md` (its posture — the stable stance, like *faithful* or *skeptical*), `config.yaml` (model, tools, and MCP connections), optional `skills/` (assigned per lane), and `distribution.yaml` (packaging metadata).

So the agents share the house rules but each brings its own stance and toolset. The old failure mode — seven near-identical SOUL files duplicating common policy by hand — is gone structurally: common content has one home (`AGENTS.md`), and what remains per-profile is genuinely per-profile. At five profiles, hand-authoring the unique layers stays cheap, and a profile compiler remains unnecessary.

## Why the profile install is idempotent

The bootstrap's profile-install step (also runnable on its own via `--profiles-only`) is designed to be re-run after every `git pull` without care about current state. It refreshes every author-owned file (profile sources, MCP configs, lane-override templates), **prunes** stale `memoria-*` profiles that are no longer shipped (the v0.1.0-alpha.1 seven-profile set), and leaves human-owned secrets (`.env`, any local overrides) untouched.

The idempotency matters because it is the mechanism that keeps deployed profiles synchronized with their source. Without it, the profile directories under `~/.hermes/profiles/` would drift from the repo over time — a drift the Linter detects but the re-run fixes; making the re-run safe is what makes the fix actionable.

---

## Running more than one vault

Nothing in the distribution model is single-vault by design — you can fork the starter vault for a second project and run both at once. Coexistence works because three resources two vaults would otherwise contend for can each be isolated:

| Resource | What collides if shared | Isolation |
|---|---|---|
| **Obsidian REST API port** | Both Local REST API plugins bind the same HTTPS port; the second to start can't bind, so its `OBSIDIAN_MCP_PORT` serves nothing (or points Hermes at the wrong vault). | A distinct HTTPS port per vault, with each vault's profiles' `OBSIDIAN_MCP_PORT` and `OBSIDIAN_MCP_SSL_VERIFY` matching that instance. |
| **Hermes profiles** | Profiles substitute one `VAULT_PATH` at install; a shared `HERMES_HOME` points `memoria-*` at whichever vault was installed last, so the other vault's agents read and write the wrong tree. | Unique per-vault aliases (`project2-*`) **or** a separate `HERMES_HOME` per vault. |
| **Kanban queue** | The board/queue (`hermes kanban`) is Hermes runtime state under `HERMES_HOME`, **not** a file in the vault — so a shared `HERMES_HOME` is one shared queue: cards from both vaults intermix and cron fires against the wrong vault. | A separate `HERMES_HOME` per vault gives each its own independent queue. |

For full isolation, use a distinct REST port **and** a separate `HERMES_HOME` per vault. The step-by-step procedure is in [Add a second vault](../../how-to-guides/setup/add-a-second-vault.md).

---

## Related

- The installer's design: [Bootstrap installer](bootstrap-installer.md)
- The decisions: [ADR-55](../../adr/55-src-scaffold-populate-golden-copy.md), [ADR-26](../../adr/26-repo-as-install-unit.md)
- Profile structure: [Profiles](../profiles/README.md)
- Operationalizes idempotent deployment: [Redeploy profiles](../../how-to-guides/operate/redeploy-profiles.md)
- On-disk layout reference: [On-disk layout](../../reference/on-disk-layout.md)
