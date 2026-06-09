---
topic: decisions
id: 26
title: The repo is the install unit; profiles are hand-authored and idempotently deployed
status: accepted
date_proposed: 2026-06-01
date_resolved: 2026-06-01
supersedes: []
superseded_by: []
parent: Decisions
grand_parent: Explanation
nav_order: 26
---

# ADR-26: The repo is the install unit; profiles are hand-authored and idempotently deployed

## Context

How Memoria is packaged, installed, and kept up to date has direct upgrade-path consequences — yet the model was only described in [Distribution model](../explanation/deployment/distribution-model.md) and never recorded as a decision. Two coupled questions need a fixed answer: what is the unit a user installs (the whole repo, or just the vault?), and how do the seven Hermes profile directories stay synchronized with their vault source over time without a build step? Recording this matters because the deferral of a profile compiler and the "repo is the install unit" choice both shape every future install and upgrade.

## Decision

**The repo (`memoria-vault`) is the install unit.** A user clones it (or runs the one-line bootstrap that clones it), and the bootstrap installer at the repo root (`scripts/install.sh`, with `scripts/install.ps1` as a thin WSL2 launcher) deploys everything. The repo has three parts with distinct audiences: `scripts/install.sh`/`scripts/install.ps1` (bootstrap), `vault/` (the runtime artifact deployed to a working location off OneDrive on Windows), and `docs/` (developer-facing, not deployed). Consequences that follow as rules:

- **`vault/` is not independently installable** — installing requires the whole repo, and any reference from a vault-resident file to `docs/` or `project/` is a **GitHub URL, never a relative path**, because the deployed vault does not carry them.
- **Profiles are hand-authored**, not compiled. The seven profile directories under `.memoria/profiles/` are maintained by hand; a profile compiler is **deferred** ([Profile compilation from a shared base](42-profile-compilation.md)) because seven-profile scale does not yet justify the complexity.
- **Profile install is idempotent.** The profile-install step (re-runnable on its own via `--profiles-only`) refreshes every author-owned file on each `git pull` and leaves human-owned secrets (`.env`, local overrides) untouched.

## Consequences

- Upgrades are "`git pull` then re-run the idempotent profile install" — that re-run is the mechanism that keeps deployed profiles synchronized with the vault source.
- The Linter's `profile-install-drift` detector *catches* deployed copies diverging from source but cannot *fix* them; the idempotent re-run is the fix, so the detector and the installer are a matched pair.
- Hand-authoring accepts a known cost: common content (audit behavior, policy invariants, MCP connections) is duplicated across seven `SOUL.md` files kept in lockstep by human review. When that lockstep becomes painful, the deferred compiler proposal is the planned response — and adopting it would supersede the hand-authored clause here.
- The deployed-vault-carries-no-`docs/` rule is load-bearing: a relative cross-reference from a vault file silently breaks after deployment, so vault→docs links must be GitHub URLs.
- Windows installs must deploy off OneDrive (the `/mnt/c` OneDrive seam), which the bootstrap handles by copying `vault/` to a working location.

## Alternatives considered

**Ship `vault/` as the independently installable unit (the earlier vault-centric framing).** Superseded by the bootstrap model: the installers live at the repo root because the clone is the entry point, which makes the repo — not the vault alone — the install unit. The vault-as-carrier framing is retained only as history.

**Generate profiles from a shared base via a compiler.** Deferred, not rejected: it would eliminate the seven-way duplication, but at seven-profile scale the duplication is not yet painful enough to justify a build step. Held as [Profile compilation from a shared base](42-profile-compilation.md) with hand-authoring as the current state.

## Related

- **Supporting rationale:** [Distribution model](../explanation/deployment/distribution-model.md) (the three-part repo, idempotent install, hand-authored profiles).
- **Related decisions:** [ADR-02 seven specialist profiles](02-seven-specialist-profiles.md) (the profiles being deployed); [ADR-22 build on Hermes](22-build-on-hermes-runtime.md) (profiles deploy to `~/.hermes/profiles/`).
- **Installer design:** [Bootstrap installer](../explanation/deployment/bootstrap-installer.md) (rationale) + [Installer (bootstrap)](../reference/installer.md) (inventories).
- **Proposals:** [Profile compilation from a shared base](42-profile-compilation.md) (the deferred compiler).
- **How-to:** [Redeploy profiles](../how-to-guides/operate/redeploy-profiles.md), [Set up the vault](../how-to-guides/setup/set-up-the-vault.md).
- **Source discussion:** retroactively records the distribution model in `distribution-model.md`; note this ADR follows the *current* repo-as-install-unit model, which has moved past the earlier vault-as-carrier framing.
