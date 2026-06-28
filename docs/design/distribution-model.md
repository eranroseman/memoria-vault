---
title: Distribution model
parent: Design Book
grand_parent: Developers
nav_order: 24
---

# Distribution model

Memoria ships as a single repo (`memoria-vault`). **The repo is the install unit** ([ADR-26](../adr/26-repo-as-install-unit.md), as amended by [ADR-55](../adr/55-src-scaffold-populate-golden-copy.md)) — you clone it (or run the one-line bootstrap, which clones it for you), and the bootstrap installer at the repo root deploys everything. The repo has three parts:

| Path | Contents | Audience |
| --- | --- | --- |
| `scripts/install.ps1` / `scripts/install.sh` (repo root) | The **bootstrap installers**: native Windows production via PowerShell, Linux/WSL testing via bash. Both derive the vault from `vault-template/` and deploy the same profile/runtime source. | End users (run once). |
| `vault-template/` | **Source files only — never a live vault**: templates, profiles, skills, schemas, dashboards, patterns, and `.obsidian` config. The installer *scaffolds* the vault tree and *populates* it from here. | The installer (and contributors). |
| `src/memoria_vault/` | The installable Python package for shared runtime helpers and policy logic. | Memoria operations, MCP servers, tests, and contributors. |
| `docs/` | Architecture, workflow, and decision documents. Not needed at runtime. | Developers and contributors. |

The installer derives the running vault from `vault-template/` at a working location (off OneDrive on Windows); the human opens **that deployed vault** in Obsidian. The deployed vault is self-contained — it does not carry `docs/`, so any reference from a vault-resident file (e.g. `../explanation/obsidian/home.md`) to `docs/` is a **GitHub Pages URL, never a relative path**. The installers live at the repo root (not inside `src/`) because the bootstrap is the clone/entry point; installing requires the whole repo. See [Bootstrap installer](bootstrap-installer.md) for the installer's design and [Installer (bootstrap)](../reference/installer.md) for the component inventories.

Shipping `vault-template/` rather than a live `vault/` template is deliberate ([ADR-55](../adr/55-src-scaffold-populate-golden-copy.md)): a live-vault template blurs "source of truth" with "a running instance," invites accidental edits to the template, and offers no recovery path. With `vault-template/`, authoring (the repo) and restoring (the runtime golden copy) stay cleanly separate, and user content and system files are structurally distinct from the first minute.

---

## What ships in `vault-template/`

`vault-template/` carries the **vault skeleton**, **`.obsidian/` config**, and **`.memoria/` scaffold**. The full directory catalog is [On-disk layout](../reference/on-disk-layout.md); the category-tree rationale is [The vault](../explanation/architecture/vault.md). Empty content dirs are recreated from `.memoria/schemas/folders.yaml`.

## The golden copy: the restore source

At install time, every system file is also staged at `<vault>/.memoria/golden/` with a hash manifest. The Linter can compare live system files against that baseline, flag drift, and restore corrupted system files without re-running the installer. Releases refresh the golden copy by fresh install, not in-place migration ([ADR-55](../adr/55-src-scaffold-populate-golden-copy.md)).

---

## The five profiles: one shared layer, four profile files

The agents ship as five hand-authored profile directories under `vault-template/.memoria/profiles/` — `memoria-copi`, `memoria-librarian`, `memoria-writer`, `memoria-peer-reviewer`, `memoria-engineer`. Each agent is a **shared layer + a unique layer** ([ADR-48](../adr/48-copi-and-agent-consolidation.md)):

- **Shared:** `AGENTS.md` — the one "how we work in this vault" instruction set every agent reads, living in the vault root so there is exactly one copy of the house rules.
- **Unique per agent:** `SOUL.md` (its posture — the stable stance, like *faithful* or *skeptical*), `config.yaml` (model, tools, and MCP connections), optional `skills/` (assigned per lane), and `distribution.yaml` (packaging metadata).

So the agents share the house rules but each brings its own stance and toolset. Narrow capability blocks in `config.yaml` are materialized from `vault-template/.memoria/tool-registry.yaml` by `scripts/render_profile_configs.py`: one allowlist owner, plain Hermes profile files at runtime.

## Why the profile install is idempotent

The profile-install step is safe to re-run with `--profiles-only`: it refreshes author-owned profile files and leaves human-owned secrets (`.env`, local overrides) untouched. That is what makes profile drift actionable: the Linter can detect it, and a profile redeploy can fix it.

---

## Running more than one vault

Nothing in the distribution model is single-vault by design. The rule is simple: give each vault its own Obsidian REST port and its own `HERMES_HOME`, so profiles, crons, and Kanban state cannot cross. The step-by-step procedure is [Add a second vault](../how-to-guides/setup/add-a-second-vault.md).

---

## Related

- The installer's design: [Bootstrap installer](bootstrap-installer.md)
- The decisions: [ADR-55](../adr/55-src-scaffold-populate-golden-copy.md), [ADR-26](../adr/26-repo-as-install-unit.md)
- Profile structure: [Profiles](../explanation/profiles/README.md)
- Operationalizes idempotent deployment: [Redeploy profiles](../how-to-guides/operate/redeploy-profiles.md)
- On-disk layout reference: [On-disk layout](../reference/on-disk-layout.md)
