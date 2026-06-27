---
topic: decisions
id: 26
title: The repo is the install unit; profiles are hand-authored and idempotently deployed
nav_exclude: true
status: accepted
date_proposed: 2026-06-01
date_resolved: 2026-06-01
assumes: []
supersedes: []
superseded_by: []
---

# ADR-26: The repo is the install unit; profiles are hand-authored and idempotently deployed

> **Amended (2026-06-10; 2026-06-23).** Three specifics below are now stale:
> (1) the repo ships **`src/`**, not `vault/`, as the source-of-truth tree the installer
> scaffolds and populates — see [ADR-55](55-src-scaffold-populate-golden-copy.md);
> read "`vault/`" throughout as "`src/`". (2) The profile compiler this ADR calls
> "deferred ([ADR-42](42-profile-compilation.md))" is superseded by the Co-PI/agent
> consolidation in [ADR-48](48-copi-and-agent-consolidation.md); the seven-profile
> premise no longer holds. (3) Profile configs are no longer entirely hand-authored:
> [ADR-115](115-profile-config-materialization.md) materializes only the mechanical
> capability blocks from `tool-registry.yaml`. The core decision (the repo is the
> install unit; idempotent profile deploy) stands.

## Context

> *Note (v0.1.0-alpha.2): "seven" profile directories below predates [ADR-48](48-copi-and-agent-consolidation.md), which consolidated the fleet to **five** (`.memoria/profiles/memoria-{copi,librarian,writer,peer-reviewer,engineer}`). The decision is unchanged — profiles remain hand-authored and idempotently deployed; the deferred-compiler trade-off now reads "five-profile scale".*

How Memoria is packaged, installed, and kept up to date has direct upgrade-path consequences — yet the model was only described in [Distribution model](../design/distribution-model.md) and never recorded as a decision. Two coupled questions need a fixed answer: what is the unit a user installs (the whole repo, or just the vault?), and how do the seven Hermes profile directories stay synchronized with their vault source over time without a build step? Recording this matters because the deferral of a profile compiler and the "repo is the install unit" choice both shape every future install and upgrade.

## Decision

**The repo (`memoria-vault`) is the install unit.** A user clones it (or runs the one-line bootstrap that clones it), and the bootstrap installers at the repo root deploy everything: `scripts/install.ps1` for native Windows production and `scripts/install.sh` for Linux/WSL testing. The repo has three parts with distinct audiences: `scripts/install.sh`/`scripts/install.ps1` (bootstrap), `src/` (the runtime artifact source deployed to a working vault), and `docs/` (developer-facing, not deployed). Consequences that follow as rules:

- **`vault/` is not independently installable** — installing requires the whole repo, and any reference from a vault-resident file to `docs/` is a **GitHub URL, never a relative path**, because the deployed vault does not carry them.
- **Profiles are hand-authored**, not compiled. The seven profile directories under `.memoria/profiles/` are maintained by hand; a profile compiler is **deferred** ([Profile compilation from a shared base](42-profile-compilation.md)) because seven-profile scale does not yet justify the complexity.
- **Profile install is idempotent.** The profile-install step (re-runnable on its own via `--profiles-only`) refreshes every author-owned file on each `git pull` and leaves human-owned secrets (`.env`, local overrides) untouched.

## Consequences

- Upgrades are "`git pull` then re-run the idempotent profile install" — that re-run is the mechanism that keeps deployed profiles synchronized with the vault source.
- A `profile-install-drift` detector was once planned to *catch* deployed copies diverging from source; it is **retired** ([ADR-67](67-drift-procedures-keep-or-retire.md)) — the vault-side Linter cannot see `~/.hermes`, and the idempotent re-run is both the detection and the fix.
- Hand-authoring accepts a known cost: common content (audit behavior, policy invariants, MCP connections) is duplicated across seven `SOUL.md` files kept in lockstep by human review. When that lockstep becomes painful, the deferred compiler proposal is the planned response — and adopting it would supersede the hand-authored clause here.
- The deployed-vault-carries-no-`docs/` rule is load-bearing: a relative cross-reference from a vault file silently breaks after deployment, so vault→docs links must be GitHub URLs.
- Windows installs must deploy off OneDrive, which the bootstrap handles by copying `src/` to a working production vault location.

## Alternatives considered

**Ship `vault/` as the independently installable unit (the earlier vault-centric framing).** Superseded by the bootstrap model: the installers live at the repo root because the clone is the entry point, which makes the repo — not the vault alone — the install unit. The vault-as-carrier framing is retained only as history.

**Generate profiles from a shared base via a compiler.** Deferred, not rejected: it would eliminate the seven-way duplication, but at seven-profile scale the duplication is not yet painful enough to justify a build step. Held as [Profile compilation from a shared base](42-profile-compilation.md) with hand-authoring as the current state.

## Related

- **Supporting rationale:** [Distribution model](../design/distribution-model.md) (the three-part repo, idempotent install, hand-authored profiles).
- **Related decisions:** [ADR-02 seven specialist profiles](02-seven-specialist-profiles.md) (the profiles being deployed); [ADR-22 build on Hermes](22-build-on-hermes-runtime.md) (profiles deploy to `~/.hermes/profiles/`).
- **Installer design:** [Bootstrap installer](../design/bootstrap-installer.md) (rationale) + [Installer (bootstrap)](../reference/installer.md) (inventories).
- **Proposals:** [Profile compilation from a shared base](42-profile-compilation.md) (the deferred compiler).
- **How-to:** [Redeploy profiles](../how-to-guides/operate/redeploy-profiles.md), [Set up the vault](../how-to-guides/setup/set-up-the-vault.md).
- **Source discussion:** retroactively records the distribution model in `distribution-model.md`; note this ADR follows the *current* repo-as-install-unit model, which has moved past the earlier vault-as-carrier framing.
