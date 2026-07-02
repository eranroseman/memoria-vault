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
| `scripts/install.ps1` / `scripts/install.sh` (repo root) | The **bootstrap installers**: native Windows via PowerShell and Linux/WSL via bash. Both derive the workspace from `vault-template/` and install the standalone CLI/runtime package. | End users (run once). |
| `vault-template/` | **Source files only — never a live vault**: templates, OKF knowledge bundles, capability manifests, schemas, dashboards, patterns, and optional app config. The installer *scaffolds* the vault tree and *populates* it from here. | The installer (and contributors). |
| `src/memoria_vault/` | The installable Python package for shared runtime helpers and policy logic. | Memoria operations, optional adapter servers, tests, and contributors. |
| `docs/` | Architecture, workflow, and decision documents. Not needed at runtime. | Developers and contributors. |

The installer derives the running vault from `vault-template/` at a working location (off OneDrive on Windows); the human opens **that deployed vault** in Obsidian. The deployed vault is self-contained — it does not carry `docs/`, so any reference from a vault-resident file (e.g. `../explanation/obsidian/home.md`) to `docs/` is a **GitHub Pages URL, never a relative path**. The installers live at the repo root (not inside `src/`) because the bootstrap is the clone/entry point; installing requires the whole repo. See [Bootstrap installer](bootstrap-installer.md) for the installer's design and [Installer (bootstrap)](../reference/installer.md) for the component inventories.

Shipping `vault-template/` rather than a live `vault/` template is deliberate ([ADR-55](../adr/55-src-scaffold-populate-golden-copy.md)): a live-vault template blurs "source of truth" with "a running instance," invites accidental edits to the template, and offers no recovery path. With `vault-template/`, authoring (the repo) and restoring (the runtime golden copy) stay cleanly separate, and user content and system files are structurally distinct from the first minute.

---

## What ships in `vault-template/`

`vault-template/` carries the **vault skeleton**, **`.obsidian/` config**, and **`.memoria/` scaffold**. The full directory catalog is [On-disk layout](../reference/on-disk-layout.md); the category-tree rationale is [The vault](../explanation/architecture/vault.md). Empty content dirs are recreated from `.memoria/schemas/folders.yaml`.

## The golden copy: the restore source

At install time, every system file is also staged at `<vault>/.memoria/golden/` with a hash manifest. The Linter can compare live system files against that baseline, flag drift, and restore corrupted system files without re-running the installer. Releases refresh the golden copy by fresh install, not in-place migration ([ADR-55](../adr/55-src-scaffold-populate-golden-copy.md)).

---

## Capabilities, Not Installed Profiles

Alpha.14 ships capability manifests under `vault-template/capabilities/`, with
one checked Markdown file per operation. Those manifests are the runtime
allowlist: they describe the operation id, input/output schema, allowed tools,
allowed paths, network ceiling, runner, model policy, and required checks.

The repo deliberately does not ship `vault-template/.memoria/profiles/`,
`vault-template/.memoria/lane-overrides/`, or a profile-rendering script. The
standalone `memoria` CLI and engine are the product surface. Optional future
adapters may call the same CLI/engine, but they are not the source of truth for
capabilities and they do not belong in the bootstrap installer.

The absence is test-pinned by [Installed profiles](../reference/profile-capabilities.md) and
`scripts/alpha14_negative_gate.py`.

---

## Running more than one vault

Nothing in the distribution model is single-vault by design. The rule is simple:
give each workspace its own directory, `.memoria/memoria.sqlite`, qmd index
state, Git history, and provider config. If an optional app adapter is added
later, it must attach to one workspace at a time and preserve the CLI/engine as
the write path.

---

## Related

- The installer's design: [Bootstrap installer](bootstrap-installer.md)
- The decisions: [ADR-55](../adr/55-src-scaffold-populate-golden-copy.md), [ADR-26](../adr/26-repo-as-install-unit.md)
- Capability reference: [Operations](../reference/operations.md)
- On-disk layout reference: [On-disk layout](../reference/on-disk-layout.md)
