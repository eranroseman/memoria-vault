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
> read "`vault/`" throughout as "`src/`". (2) The deferred profile compiler is
> superseded by the Co-PI/agent consolidation in
> [ADR-48](48-copi-and-agent-consolidation.md); the seven-profile
> premise no longer holds. (3) Profile configs are no longer entirely hand-authored:
> [ADR-120](120-profile-config-materialization.md) materializes only the mechanical
> capability blocks from `tool-registry.yaml`. The core decision (the repo is the
> install unit; idempotent profile deploy) stands.

## Context

> *Note (0.1.0-alpha.2): "seven" profile directories below predates [ADR-48](48-copi-and-agent-consolidation.md), which consolidated the fleet to **five** (`.memoria/profiles/memoria-{copi,librarian,writer,peer-reviewer,engineer}`). The decision is unchanged — profiles remain hand-authored and idempotently deployed; the deferred-compiler trade-off now reads "five-profile scale".*

How Memoria is packaged and installed was only described in [Distribution model](../design/distribution-model.md) and never recorded as a decision. Two coupled questions need a fixed answer: what is the unit a user installs (the whole repo, or just the vault?), and how do the seven Hermes profile directories stay synchronized with their vault source over time without a build step? Recording this matters because the deferral of a profile compiler and the "repo is the install unit" choice both shape every install.

## Decision

**The repo (`memoria-vault`) is the install unit.** A user clones it (or runs the one-line bootstrap that clones it), and the bootstrap installers at the repo root deploy everything: `scripts/install.ps1` for native Windows production and `scripts/install.sh` for Linux/WSL testing. The repo has three parts with distinct audiences: `scripts/install.sh`/`scripts/install.ps1` (bootstrap), `src/` (the runtime artifact source deployed to a working vault), and `docs/` (developer-facing, not deployed). Consequences that follow as rules:

- **`vault/` is not independently installable** — installing requires the whole repo, and any reference from a vault-resident file to `docs/` is a **GitHub URL, never a relative path**, because the deployed vault does not carry them.
- **Profiles are hand-authored**, not compiled. The profile directories under `.memoria/profiles/` are maintained by hand; only the mechanical capability blocks are materialized from `tool-registry.yaml` ([ADR-120](120-profile-config-materialization.md)).
- **Profile install is idempotent.** The profile-install step (re-runnable on its own via `--profiles-only`) refreshes every author-owned file on each `git pull` and leaves human-owned secrets (`.env`, local overrides) untouched.

## Consequences

- There is no supported in-place migration or backwards-compatibility path while no production installation exists beyond disposable sandboxes. Refreshing a sandbox means pulling the repo and rerunning the installer/profile deploy against that sandbox.
- A `profile-install-drift` detector was once planned to *catch* deployed copies diverging from source, but the vault-side Linter cannot see `~/.hermes`; the idempotent profile deploy is both the detection pass and the fix.
- Hand-authoring accepts a known cost: common content (audit behavior, policy invariants, MCP connections) is duplicated across profile files kept in lockstep by human review. When that lockstep becomes painful, expand the narrow render step from [ADR-120](120-profile-config-materialization.md) rather than reintroducing a full compiler.
- The deployed-vault-carries-no-`docs/` rule is load-bearing: a relative cross-reference from a vault file silently breaks after deployment, so vault→docs links must be GitHub URLs.
- Windows installs must deploy off OneDrive, which the bootstrap handles by copying `src/` to a working production vault location.

## Alternatives considered

**Ship `vault/` as the independently installable unit (the earlier vault-centric framing).** Superseded by the bootstrap model: the installers live at the repo root because the clone is the entry point, which makes the repo — not the vault alone — the install unit. The vault-as-carrier framing is retained only as history.

**Generate profiles from a shared base via a compiler.** Rejected for current scale:
the profile postures remain short and distinct, while [ADR-120](120-profile-config-materialization.md)
removes the risky mechanical duplication.

## Related

- **Supporting rationale:** [Distribution model](../design/distribution-model.md) (the three-part repo, idempotent install, hand-authored profiles).
- **Related decisions:** [ADR-48 profile consolidation](48-copi-and-agent-consolidation.md) (the profiles being deployed); [ADR-22 build on Hermes](22-build-on-hermes-runtime.md) (profiles deploy to `~/.hermes/profiles/`).
- **Installer design:** [Bootstrap installer](../design/bootstrap-installer.md) (rationale) + [Installer (bootstrap)](../reference/installer.md) (inventories).
- **How-to:** [Redeploy profiles](../how-to-guides/operate/redeploy-profiles.md), [Set up the vault](../how-to-guides/setup/set-up-the-vault.md).
- **Source discussion:** retroactively records the distribution model in `distribution-model.md`; note this ADR follows the *current* repo-as-install-unit model, which has moved past the earlier vault-as-carrier framing.
