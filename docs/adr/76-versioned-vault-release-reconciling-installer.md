---
topic: decisions
id: 76
title: Distribute Memoria as a versioned vault release; deploy via a source-agnostic reconciling installer
status: deferred
nav_exclude: true
date_proposed: 2026-06-14
date_resolved:
assumes: [44, 46, 55, 69, 73]
supersedes: []
superseded_by: []
parent: Decisions
grand_parent: Explanation
nav_order: 76
---

# ADR-76: Distribute Memoria as a versioned vault release; deploy via a source-agnostic reconciling installer

## Context

The thing Memoria deploys is **a configured vault, not a Python package**. The seven subtrees the installer lays down today are three different things wearing one rsync: importable Python (`operations/`, `mcp/`, `memoria_runtime/`, `lib/`), authored non-Python content that Obsidian and the MCP host read directly (the five `profiles/` with their `SOUL.md`/`SKILL.md`/`config.yaml`, `schemas/`, `system/` templates and dashboards, the policy-gate plugin shim, `*-cron.sh` wrappers), and per-vault state (`lane-overrides/`, `logs/`, rendered config, `.env`, the golden store).

The obvious framing — "make the runtime an installable wheel; the vault holds data, not source" — optimizes only the first of those three and lets that artifact define the whole deployment story. It does not hold up: a wheel cannot carry `SOUL.md`/`SKILL.md`, the `plugin.yaml` gate shim (loaded **by the MCP host in its own interpreter**, not the venv), or the cron wrappers, so "vault holds data, not source" is unreachable — much of what stays in the vault is authored source by necessity. It also imports costs the audience does not yet justify (a prebuilt-wheel supply-chain trust surface, non-transactional `pip --upgrade` rollback) and turns the policy-gate reachability question into an open execution blocker. (The `engines → operations` rename that earlier framings sequenced *before* packaging has since landed in [#536](https://github.com/eranroseman/memoria-vault/issues/494), so that sequencing concern is already spent.)

Designing from scratch, the spine inverts: the unit is a **versioned vault release**, and the installer is a **pure function of `(release_root, vault_path)`** that reconciles each layer idempotently. The Python-package work the wheel framing wanted is still right — it is just *how the code layer lands inside the release*, not the spine itself.

This decision does **not** change integrity *protection*. A common misconception — that [ADR-55](55-src-scaffold-populate-golden-copy.md)'s golden copy protects the runtime code — is false: `golden_restore.py`'s manifest covers `system/{templates,dashboards,patterns,eval,scripts}/`, three system files, and three `.obsidian` config files, with **no `.memoria/` prefix**. Code-integrity protection is the MCP-only sandbox (agents cannot write files; [ADR-46](46-seven-layer-architecture.md)) plus Git as source of truth. This design *extends* ADR-55's manifest idea to cover the code and authored layers for **verification**, but leaves the protection mechanism untouched.

## Decision

Memoria is distributed as a single versioned vault release and deployed by a source-agnostic reconciling installer. Two decisions are load-bearing; everything else follows from them.

### Load-bearing decision 1 — one versioned release, laid down by a reconciling installer that is layered by lifecycle

The installer is `install(release_root, vault_path)`: an idempotent function that does not care whether `release_root` is a checked-out Git tag or an unpacked tarball. It reconciles three layers, each by its own lifecycle:

| Layer | Examples | Lifecycle | How the installer handles it |
|---|---|---|---|
| **Code** | runtime (`operations`, `mcp`, `runtime`, `lib`), the extracted policy core | versioned; never hand-edited; recovery = reinstall | installed into `<vault>/.memoria/.venv` as the `memoria` package |
| **Authored content** | `profiles/` (`SOUL.md`/`SKILL.md`/`config.yaml`), `schemas/`, `system/` templates and dashboards, the gate shim, cron wrappers | versioned **but** the PI may customize | laid down, then three-way reconciled (old-release vs new-release vs live) so customizations surface, not clobber |
| **Per-vault state** | notes, `lane-overrides/`, `logs/`, rendered config, `.env`, golden store | never touched by an upgrade | left untouched; defined as *everything not in the release manifest* |

The release carries **one version** (`memoria.__version__`) and a **content-addressable manifest** (SHA per file) covering the code and authored-content layers. That single manifest does triple duty: golden-style drift detection for authored content (generalizing [ADR-55](55-src-scaffold-populate-golden-copy.md) from `system/` to the whole authored layer), the gate-vs-runtime version assertion (below), and tamper *verification* of code.

The runtime is a real, single-rooted `memoria` package (`src/`-layout, `pyproject.toml` as the one source of truth for build, dependency tiers, pytest, ruff, and `[project.scripts]` console entry points; the three `requirements*.txt` collapse into named groups). **It is installed editable (`pip install -e .`) by default on the PI's machine** — editable is the principled default, not a debugging fallback: it delivers the entire import-hygiene payoff (one import root, console scripts on the venv `bin/`, deletion of the conftest `sys.path` block and the runtime `__file__`/`sys.path` bootstraps — 17 sites across 13 files at the time of writing — full type-checker/editor support) **while keeping deployed code plainly inspectable at the release root**. A non-editable copy-install is used only on the eventual no-checkout operator path. No prebuilt `.whl` is shipped; the wheel is built in CI solely as a packaging-correctness check (it exercises `package_data` and `__init__.py` gaps that editable installs do not).

### Load-bearing decision 2 — extract a genuine, tiny, standalone policy core

The policy-gate runs in the MCP host's process, whose interpreter the installer does not pin. The small, dependency-free **policy core** (the `MUTATING_ACTIONS` set and path matching) this decision calls for **already exists** — `src/.memoria/memoria_runtime/policy/` (`__init__.py` + `paths.py`, stdlib-only), imported by the MCP servers (`policy_mcp.py:51`). What remains is the gate shim: today it reaches its decision *through* the MCP layer (`policy_hook → policy_mcp`) via a `sys.path` insert into `.memoria/mcp`. That chain is organic growth, not design. The residual work is to have the gate vendor only the standalone core and assert its version against the release manifest at startup, refusing to run on mismatch — dropping the `sys.path` reach-through.

This makes the hard-deny security boundary small, auditable, and **interpreter-portable** — it carries no transitive runtime dependency, so it runs correctly in the MCP host's interpreter without the venv. It dissolves version skew structurally (there is no fat chain left to fall out of sync), and because the whole release installs from one root in one installer run, the gate and servers are co-versioned by construction — exactly as the rsync model co-versioned them, without the rsync.

### Delivery

Git tag now (`git checkout vX && ./install.sh <vault>`): versioned, reproducible, transparent, zero build pipeline. When an audience that cannot run a checkout appears, the *same* installer consumes a hash-verified (eventually signed) release tarball — the spine does not change, only the source of `release_root`. Rollback is `git checkout <prev-tag> && ./install.sh`; no wheel retention or `--force-reinstall` dance. Vault resolution stays a parameter (`resolve_vault()` is already arg→env, never `__file__`).

**Migration is staged and ordered:**

1. **Landed (alpha.4) ✅:** a repo-root `pyproject.toml` scoped strictly to tooling — `[tool.pytest.ini_options]` (`testpaths` + `pythonpath`) and `[tool.ruff]` only; `requirements-dev.txt` retained, no `[project]` table. The `conftest.py` `sys.path` block is gone (the `pythonpath` now lives in `pyproject.toml`).
2. **Packaging:** add the `[project]` table and `src/`-layout, install editable, delete the runtime `__file__`/`sys.path` bootstraps (17 sites across 13 files), wire console scripts. This half stands on its own import-hygiene merits, independent of the delivery change.
3. **Then (the spine):** flip deployment to the reconciling installer over a versioned release; have the gate shim vendor the already-extracted policy core (decision 2) and drop its `sys.path` reach-through; introduce the release manifest.

## Consequences

- **The full deployable is modeled, not just the Python third.** Authored content and the gate shim have a defined home and upgrade path instead of being smuggled through "data."
- **The headline invariant becomes true and honest:** *the runtime code* installs into the venv; profiles, the host-loaded gate shim, schemas, and cron wrappers remain vault-side authored content by design — no contradiction to chase.
- **The gate-reachability question becomes settled architecture, not an open blocker.** The policy-core extraction is a one-time refactor that removes version skew rather than parking it; the gate stays in-process (no hot-path IPC hop, no fail-closed availability dependency on a running server).
- **One manifest replaces three scattered worries** (golden drift, gate version, code-integrity verification) with a single content-addressable source of truth for "what should be on disk."
- **The shipped-wheel's premature costs are dropped:** no shipped-artifact supply-chain trust surface, no non-transactional `pip --upgrade` rollback problem, no `site-packages` transparency regression on the primary machine.
- **Multi-machine falls out for free** ([ADR-63](63-multi-machine-deployment.md)): one versioned release, N vaults, state per-machine; more multi-machine-friendly than either rsync-from-checkout or a bare wheel.
- **Entry-point audit (carried forward):** several console scripts are notional — `memoria-lint` and `memoria-eval` are each "pick one canonical entry" decisions (the linter `main()` is in `detectors.py`; eval spans `eval_dispatch.py`/`eval_score.py`); the rest need `main()` signature/return confirmation (`reconcile.main()` returns an `int` exit code, which `[project.scripts]` handles correctly).
- **Costs:** the reconciling installer is more logic than `cp -R`/rsync (three-way merge for the authored layer); the policy-core extraction is real refactor work and must precede the gate dropping its reach-through; the release manifest must be built and verified in CI. **Tension with [ADR-26](26-repo-as-install-unit.md):** the install unit shifts from the rsynced repo subtree to a versioned release — the repo stays the source of truth, what is *deployed* changes; reconcile on execution.

## When this matters

Context for the cadence review, not a gate — pick this up when **any** holds:

- **Distribution:** Memoria ships to operators who cannot run from a Git checkout — the tarball delivery and copy-install path become live (the git-tag path needs none of this).
- **Support burden:** the `sys.path`/`__file__` bootstrapping (17 sites across 13 files) or the three-way `requirements*.txt` split becomes a recurring source of import/CI breakage — the package + editable-install half (step 2) is the relief and can land first.
- **Boundary risk:** any incident or near-miss where the gate and servers could run divergent policy — the policy-core extraction moves to the front.

**Guard:** the step-1 tooling `pyproject.toml` and the step-2 packaging (editable install, deleting the conftest/`__file__` import hacks) are safe to pursue on their own merits. Do **not** stand up tarball publishing, signing, or a copy-install path before a no-checkout audience is real — git-tag is the correct posture until then, and the rest costs nothing to defer.

## Alternatives considered

- **Package the runtime as a shipped wheel; vault holds data, not source.** The first-instinct framing, and correct about import hygiene — but wrong as the deployment spine: it models only the Python third, cannot carry the authored two-thirds (profiles, host-loaded gate shim, cron), makes "vault holds no source" unreachable, adds a supply-chain trust surface and non-atomic rollback before any audience needs them, and leaves gate-skew as an open execution blocker. This decision keeps its package work (as the code layer's install mechanism) and discards the wheel as the *shipped artifact*.
- **Status quo: rsync from a checkout.** Fine while the audience is the PI, but unversioned, prone to the renamed-file-lingering hazard the scoped `--delete` pass exists to paper over, and with no story for gate/server co-versioning beyond "they came from one tree." Git-tag + reconciling installer keeps the transparency while adding versioning and a real manifest.
- **Gate calls the policy server over IPC.** Structurally skew-free, but adds per-tool-call latency on the hot path and a fail-closed availability dependency (a crashed policy server bricks the agent). Extracting a tiny in-process core achieves skew-freedom without either cost; IPC remains a fallback only if in-process import proves infeasible in the host interpreter.

## Related

- **Tracking issue:** [#521](https://github.com/eranroseman/memoria-vault/issues/521) — revisit at each release cadence.
- **Origin:** [#494](https://github.com/eranroseman/memoria-vault/issues/494) (research) and
  deferred implementation tracker [#521](https://github.com/eranroseman/memoria-vault/issues/521).
- **Depends on:** [ADR-44](44-tests-in-pytest-tree.md) (the conftest `sys.path` block the package work deletes); [ADR-46](46-seven-layer-architecture.md) (the MCP-only sandbox that *is* integrity protection); [ADR-55](55-src-scaffold-populate-golden-copy.md) (the golden manifest this generalizes into the release manifest); [ADR-69](69-operations-layer-naming.md) (operations layout, now landed); [ADR-73](73-docs-reference-conventions.md) (reference conventions for moved paths).
- **In tension with:** [ADR-26](26-repo-as-install-unit.md) (install unit becomes a versioned release, not the repo subtree).
- **Strengthens:** [ADR-63](63-multi-machine-deployment.md) — one versioned release across N vaults is the natural multi-machine substrate.
