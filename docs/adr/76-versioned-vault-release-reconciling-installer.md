---
topic: decisions
id: 76
title: Distribute Memoria as a versioned vault release; deploy via a source-agnostic reconciling installer
status: accepted
date_proposed: 2026-06-14
date_resolved: 2026-06-19
assumes: [44, 46, 55, 69, 73]
supersedes: []
superseded_by: []
parent: Decisions
grand_parent: Explanation
nav_order: 76
---

# ADR-76: Distribute Memoria as a versioned vault release; deploy via a source-agnostic reconciling installer

## Context

The thing Memoria deploys is **a configured vault, not a Python package**. The
seven subtrees the installer lays down today are several things wearing one rsync:
importable Python (`operations/`, `mcp/`, `memoria_runtime/`, `lib/`), authored
boundary content that must track the release (the policy-gate shim, baseline
schemas, cron wrappers, shipped lane policy), PI-customizable authored content
(`SOUL.md`/`SKILL.md`, PI-added schema types, per-vault lane tuning), host-side
Hermes config rendered into `~/.hermes/profiles/<profile>/`, and per-vault state
(`logs/`, `.env`, the golden store, notes).

The obvious framing — "make the runtime an installable wheel; the vault holds data, not source" — optimizes only the first of those three and lets that artifact define the whole deployment story. It does not hold up: a wheel cannot carry `SOUL.md`/`SKILL.md`, the `plugin.yaml` gate shim (loaded **by the MCP host in its own interpreter**, not the venv), or the cron wrappers, so "vault holds data, not source" is unreachable — much of what stays in the vault is authored source by necessity. It also imports costs the audience does not yet justify (a prebuilt-wheel supply-chain trust surface, non-transactional `pip --upgrade` rollback) and turns the policy-gate reachability question into an open execution blocker. (The `engines → operations` rename that earlier framings sequenced *before* packaging has since landed in [#536](https://github.com/eranroseman/memoria-vault/issues/494), so that sequencing concern is already spent.)

Designing from scratch, the spine inverts: the unit is a **versioned vault release**, and the installer is a **pure function of `(release_root, vault_path)`** that reconciles each layer idempotently. The Python-package work the wheel framing wanted is still right — it is just *how the code layer lands inside the release*, not the spine itself.

This decision does **not** change integrity *protection*. A common misconception — that [ADR-55](55-src-scaffold-populate-golden-copy.md)'s golden copy protects the runtime code — is false: `golden_restore.py`'s manifest covers `system/{templates,dashboards,patterns,eval,scripts}/`, three system files, and three `.obsidian` config files, with **no `.memoria/` prefix**. Code-integrity protection is the MCP-only sandbox (agents cannot write files; [ADR-46](46-seven-layer-architecture.md)) plus Git as source of truth. This design *extends* ADR-55's manifest idea to cover the code and authored layers for **verification**, but leaves the protection mechanism untouched.

## Decision

Memoria moves from repo-subtree deployment to a single versioned vault release
deployed by a source-agnostic reconciling installer. Two decisions are
load-bearing; everything else follows from them.

**Accepted scope.** This records the deployment *spine* as decided; the work is
staged (see *Migration* and *Guard* below) and scheduling lives in the tracking
issue. The import-hygiene package half (step 2 — `src/`-layout, editable install,
console scripts, deleting the `sys.path`/`__file__` bootstraps) and the in-process
policy core (decision 2) are cleared to proceed on their own merits. The
tarball/signing/copy-install distribution half (decision 1's no-checkout path)
stays deferred — readiness `Later` — until a no-checkout audience is real; git-tag
remains the delivery posture until then.

### Load-bearing decision 1 — one versioned release, laid down by a reconciling installer that is layered by lifecycle

The installer is `install(release_root, vault_path)`: an idempotent function that does not care whether `release_root` is a checked-out Git tag or an unpacked tarball. It reconciles each layer by its own lifecycle:

| Layer | Examples | Lifecycle | How the installer handles it |
|---|---|---|---|
| **Code** | runtime (`operations`, `mcp`, `runtime`, `lib`), the extracted policy core | versioned; never hand-edited; recovery = reinstall | installed into `<vault>/.memoria/.venv` as the `memoria` package |
| **Authored boundary / contract** | gate shim, shipped `lane-overrides/<lane>.yaml`, baseline schemas, cron wrappers | release-owned; a security or schema fix must land | release-wins: apply the release, back up/report prior drift, never preserve-live |
| **PI configuration** | `SOUL.md`/`SKILL.md`, PI-added schema types, per-vault lane overlay | human-owned preference inside release ceilings | customize-preserve: preserve live changes, surface conflicts, never auto-merge over the PI |
| **Host-side config** | rendered `~/.hermes/profiles/<profile>/config.yaml` | managed at install; lives outside the vault | render from profile templates with `{{PYTHON}}`, `{{VAULT_PATH}}`, `{{QMD}}`, and model/Obsidian env refs |
| **Per-vault state** | notes, `logs/`, `.env`, golden store | never touched by an upgrade | excluded from the release manifest |

The shipped lane policy is boundary/contract, not state: release policy tightening must
land. PI lane tuning therefore moves to a separate preserved overlay merged at
load time with **tighten-only** semantics: an overlay may add denies or remove
allows, but it may not widen past the shipped baseline. The exact overlay path and
merge code are part of this proposal's implementation work.

The release carries **one version** (`memoria.__version__`) and a
**content-addressable manifest** (SHA per file) over code plus release-owned
authored files. The manifest is one mechanism with per-layer verdicts: code
mismatch is tamper/reinstall, boundary mismatch is restore/apply-release, and PI
configuration mismatch is expected customization or conflict. It generalizes
[ADR-55](55-src-scaffold-populate-golden-copy.md) without pretending all files have
the same lifecycle.

The runtime is a real, single-rooted `memoria` package (`src/`-layout, `pyproject.toml` as the one source of truth for build, dependency tiers, pytest, ruff, and `[project.scripts]` console entry points; the three `requirements*.txt` collapse into named groups). **It is installed editable (`pip install -e .`) by default on the PI's machine** — editable is the principled default, not a debugging fallback: it delivers the entire import-hygiene payoff (one import root, console scripts on the venv `bin/`, deletion of the conftest `sys.path` block and the runtime `__file__`/`sys.path` bootstraps — 17 sites across 13 files at the time of writing — full type-checker/editor support) **while keeping deployed code plainly inspectable at the release root**. A non-editable copy-install is used only on the eventual no-checkout operator path. No prebuilt `.whl` is shipped; the wheel is built in CI solely as a packaging-correctness check (it exercises `package_data` and `__init__.py` gaps that editable installs do not).

### Load-bearing decision 2 — extract a genuine, tiny, standalone policy core

The policy-gate runs in the MCP host's process, whose interpreter the installer
does not pin. The small, dependency-free **policy core** (the `MUTATING_ACTIONS`
set and path matching) this decision calls for **already exists** —
`src/.memoria/memoria_runtime/policy/` (`__init__.py` + `paths.py`, stdlib-only),
imported by the MCP servers (`policy_mcp.py:51`). What remains is the gate shim:
today it reaches its decision *through* the MCP layer (`policy_hook → policy_mcp`)
via a `sys.path` insert into `.memoria/mcp`. That chain is organic growth, not
design.

The preferred implementation is for the gate to import the **single installed
policy core** from the vault venv's package install, not a committed duplicate. The
import chain from `memoria` to `memoria.runtime.policy` must stay stdlib-only and
is guarded by a bare-interpreter CI test. If the host cannot import the installed
core, the gate fails closed. A generated vendored fallback is allowed only if
in-process import proves infeasible; a hand-maintained vendored copy is rejected
because it can drift at authoring time.

This makes the hard-deny security boundary small and auditable while avoiding a
second policy copy. The failure mode is explicit: a boundary that cannot load its
policy denies rather than waves calls through.

### Delivery

Git tag now (`git checkout vX && ./install.sh <vault>`): versioned, reproducible, transparent, zero build pipeline. When an audience that cannot run a checkout appears, the *same* installer consumes a hash-verified (eventually signed) release tarball — the spine does not change, only the source of `release_root`. Rollback is `git checkout <prev-tag> && ./install.sh`; no wheel retention or `--force-reinstall` dance. Vault resolution stays a parameter (`resolve_vault()` is already arg→env, never `__file__`).

**Migration is staged and ordered:**

1. **Landed (alpha.4) ✅:** a repo-root `pyproject.toml` carried pytest and ruff
   tooling, and the `conftest.py` `sys.path` block was removed.
2. **Package spine (alpha.8, #727):** add the `[project]` table, introduce the
   `memoria.*` import root, install the checkout editable by default, and migrate the
   dependency-free policy path first. Legacy loose-module `pythonpath` entries remain
   until their modules move behind the package root in later slices.
3. **Packaging continuation:** delete the remaining runtime `__file__`/`sys.path`
   bootstraps as modules move, then wire console scripts where they replace existing
   file entrypoints. This half stands on its own import-hygiene merits, independent of
   the delivery change.
4. **Then (the spine):** flip deployment to the reconciling installer over a versioned release; have the gate shim import the installed policy core (decision 2) and drop its `sys.path` reach-through; introduce the release manifest and the tighten-only lane overlay.

## Consequences

- **The full deployable is modeled, not just the Python third.** Boundary authored content, PI configuration, host config, and state have different homes and upgrade paths instead of being smuggled through "data."
- **The headline invariant becomes true and honest:** *the runtime code* installs into the venv; profiles, the host-loaded gate shim, schemas, and cron wrappers remain vault-side authored content by design — no contradiction to chase.
- **The gate-reachability question becomes settled architecture, not an open blocker.** The policy-core extraction is a one-time refactor that removes version skew rather than parking it; the gate stays in-process (no hot-path IPC hop, no fail-closed availability dependency on a running server).
- **One manifest replaces scattered worries** with a content-addressable source of truth for "what should be on disk," while still reporting different verdicts for code, boundary files, and PI configuration.
- **The shipped-wheel's premature costs are dropped:** no shipped-artifact supply-chain trust surface, no non-transactional `pip --upgrade` rollback problem, no `site-packages` transparency regression on the primary machine.
- **Multi-machine falls out for free** ([ADR-63](63-multi-machine-deployment.md)): one versioned release, N vaults, state per-machine; more multi-machine-friendly than either rsync-from-checkout or a bare wheel.
- **Entry-point audit (carried forward):** several console scripts are notional — `memoria-lint` and `memoria-eval` are each "pick one canonical entry" decisions (the linter `main()` is in `detectors.py`; eval spans `eval_dispatch.py`/`eval_score.py`); the rest need `main()` signature/return confirmation (`reconcile.main()` returns an `int` exit code, which `[project.scripts]` handles correctly).
- **Costs:** the reconciling installer is more logic than `cp -R`/rsync; the boundary-vs-PI-config classification, tighten-only lane overlay, import-purity guard, and release manifest must be designed and verified in CI. **Tension with [ADR-26](26-repo-as-install-unit.md):** the install unit shifts from the rsynced repo subtree to a versioned release — the repo stays the source of truth, what is *deployed* changes; reconcile on execution.

## When this matters

Context for the cadence review, not a gate — pick this up when **any** holds:

- **Distribution:** Memoria ships to operators who cannot run from a Git checkout — the tarball delivery and copy-install path become live (the git-tag path needs none of this).
- **Support burden:** the `sys.path`/`__file__` bootstrapping (17 sites across 13 files) or the three-way `requirements*.txt` split becomes a recurring source of import/CI breakage — the package + editable-install half (step 2) is the relief and can land first.
- **Boundary risk:** any incident or near-miss where the gate and servers could run divergent policy — the policy-core extraction moves to the front.

**Guard:** the step-1 tooling `pyproject.toml` and the step-2 packaging (editable install, deleting the conftest/`__file__` import hacks) are safe to pursue on their own merits. Do **not** stand up tarball publishing, signing, or a copy-install path before a no-checkout audience is real — git-tag is the correct posture until then, and the rest costs nothing to defer.

## Alternatives considered

- **Package the runtime as a shipped wheel; vault holds data, not source.** The first-instinct framing, and correct about import hygiene — but wrong as the deployment spine: it models only the Python third, cannot carry the authored two-thirds (profiles, host-loaded gate shim, cron), makes "vault holds no source" unreachable, adds a supply-chain trust surface and non-atomic rollback before any audience needs them, and leaves gate-skew as an open execution blocker. This decision keeps its package work (as the code layer's install mechanism) and discards the wheel as the *shipped artifact*.
- **Status quo: rsync from a checkout.** Fine while the audience is the PI, but unversioned, prone to the renamed-file-lingering hazard the scoped `--delete` pass exists to paper over, and with no story for gate/server co-versioning beyond "they came from one tree." Git-tag + reconciling installer keeps the transparency while adding versioning and a real manifest.
- **Gate calls the policy server over IPC.** Structurally skew-free, but adds per-tool-call latency on the hot path and a fail-closed availability dependency (a crashed policy server bricks the agent). Importing the tiny installed core achieves skew-freedom without either cost; IPC remains a fallback only if in-process import proves infeasible in the host interpreter.

## Related

- **Tracking issue:** [#521](https://github.com/eranroseman/memoria-vault/issues/521) — proposal shaping and scheduling live on the issue.
- **Origin:** [#494](https://github.com/eranroseman/memoria-vault/issues/494) (research) and
  implementation tracker [#521](https://github.com/eranroseman/memoria-vault/issues/521).
- **Depends on:** [ADR-44](44-tests-in-pytest-tree.md) (the conftest `sys.path` block the package work deletes); [ADR-46](46-seven-layer-architecture.md) (the MCP-only sandbox that *is* integrity protection); [ADR-55](55-src-scaffold-populate-golden-copy.md) (the golden manifest this generalizes into the release manifest); [ADR-69](69-operations-layer-naming.md) (operations layout, now landed); [ADR-73](73-docs-reference-conventions.md) (reference conventions for moved paths).
- **In tension with:** [ADR-26](26-repo-as-install-unit.md) (install unit becomes a versioned release, not the repo subtree).
- **Strengthens:** [ADR-63](63-multi-machine-deployment.md) — one versioned release across N vaults is the natural multi-machine substrate.
