---
title: Distribution model
parent: Deployment
grand_parent: Design
nav_order: 1
---

# Distribution model

Memoria ships from the `memoria-vault` repo as a workspace template plus an
installable Python package ([alpha.15 standalone engine checkpoint](https://github.com/eranroseman/memoria-vault/blob/main/design-history/15-alpha.15.md)).
You clone it, or run the one-line bootstrap that clones it for you, and the
bootstrap installer at the repo root deploys the standalone workspace.

| Path | Contents | Audience |
| --- | --- | --- |
| `scripts/install.ps1` / `scripts/install.sh` (repo root) | The **bootstrap installers**: native Windows via PowerShell and Linux/WSL via bash. Both derive the workspace from `vault-template/` and install the standalone CLI/runtime package. | End users (run once). |
| `vault-template/` | **Source files only, never a live vault**: templates, OKF knowledge bundles, capability manifests, schemas, dashboards, and patterns. The installer scaffolds the vault tree and populates it from here. | The installer (and contributors). |
| `src/memoria_vault/` | The installable Python package for shared runtime helpers and policy logic. | Memoria operations, optional adapter servers, tests, and contributors. |
| `packages/memoria-obsidian/` | Optional alpha.20 proof adapter for Obsidian. It consumes the local HTTP surface and is not installed into the baseline vault. | Adapter testers and contributors. |
| `docs/` | Architecture, workflow, and decision documents. Not needed at runtime. | Developers and contributors. |

The installer derives the running workspace from `vault-template/` at a working
location. The deployed workspace is self-contained - it does not carry `docs/`,
so any reference from a workspace-resident file to `docs/` is a **GitHub Pages
URL, never a relative path**. The installers live at the repo root (not inside
`src/`) because the bootstrap is the clone/entry point; installing requires the
whole repo. See [Bootstrap installer](bootstrap-installer.md) for the installer's
design and [Installer (bootstrap)](../../reference/installer.md) for the component
inventories.

Shipping `vault-template/` rather than a live `vault/` template is deliberate:
a live-vault template blurs "source of truth" with "a running instance" and
invites accidental edits to the template. With `vault-template/`, authoring
(the repo/package) and runtime use stay cleanly separate, and user content and
system files are structurally distinct from the first minute.

---

## What ships in `vault-template/`

`vault-template/` carries the **workspace skeleton** and **`.memoria/` scaffold**.
The full directory catalog is [On-disk layout](../../reference/on-disk-layout.md);
the category-tree rationale is [The vault](../../explanation/architecture/vault.md).
Empty content dirs are recreated from `.memoria/schemas/folders.yaml`.

## Product-file refresh

Memoria does not maintain an in-vault product-file restore baseline. Product
files come from `vault-template/` and the installed `memoria_vault` package;
repair is a fresh workspace refresh or package reinstall, not migration or
three-way reconciliation inside the vault.

---

## Capabilities, Not Installed Profiles

Memoria ships capability manifests inside the Python package under
`src/memoria_vault/product/capabilities/`, with one checked Markdown file per
operation. Those manifests are the runtime
allowlist: they describe the operation id, input/output schema, allowed tools,
allowed paths, network ceiling, runner test/live branch policy, and required
checks.

The repo deliberately does not ship `vault-template/.memoria/profiles/`,
`vault-template/.memoria/lane-overrides/`, or a profile-rendering script. The
standalone `memoria` CLI and engine are the product surface. Optional adapters,
including the Obsidian proof adapter, may call the same CLI/engine, but they are
not the source of truth for capabilities and they do not belong in the runtime
vault bootstrap.

The absence is test-pinned by `tests/test_profiles.py` and
`scripts/checks/alpha14_negative_gate.py`.

---

## Running more than one vault

Nothing in the distribution model is single-vault by design. The rule is simple:
give each workspace its own directory, `.memoria/memoria.sqlite`, search index
state, Git history, and provider config. Optional app adapters must attach to
one workspace at a time and preserve the CLI/engine as the write path.

---

## Related

- The installer's design: [Bootstrap installer](bootstrap-installer.md)
- The decision: [alpha.15 standalone engine checkpoint](https://github.com/eranroseman/memoria-vault/blob/main/design-history/15-alpha.15.md) (consolidates the former src-scaffold and repo-as-install-unit decisions)
- Capability reference: [Operations](../../reference/operations.md)
- On-disk layout reference: [On-disk layout](../../reference/on-disk-layout.md)
