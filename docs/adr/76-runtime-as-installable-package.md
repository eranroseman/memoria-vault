---
topic: decisions
id: 76
title: Package the Python runtime as an installable wheel; vault holds data, not source
status: deferred
nav_exclude: true
date_proposed: 2026-06-14
date_resolved:
assumes: [44, 46, 69, 73]
supersedes: []
superseded_by: []
parent: Decisions
grand_parent: Explanation
nav_order: 76
---

# ADR-76: Package the Python runtime as an installable wheel; vault holds data, not source

## Context

The repo's source tree and the deployment location are **the same dotted directory**: `src/.memoria` is both "the code we author" and "the thing rsynced into `<vault>/.memoria/`." Conflating them forces three standing costs:

- a **dotted, un-importable** top-level name (`.memoria` — a leading dot is a syntax error in `import`, and the name can't be a wheel distribution); only `memoria_runtime/` (and the policy-gate plugin) are real packages, the rest are loose script dirs;
- **two parallel import mechanisms that must agree**: 8 `sys.path` entries in `tests/conftest.py`, and **11** per-entry-point `Path(__file__)…` bootstraps in the deployed runtime (a 12th `sys.path` insert in the policy-gate plugin, via `{{VAULT_PATH}}`);
- a **two-phase rsync** deploy that mirrors a source tree (bulk copy, then a `--delete` pass scoped to 7 infra subtrees to prune renamed files), and dependencies split across three `requirements*.txt`.

This makes imports fragile, complicates static analysis, blocks reliable console entry points, and makes moves like the `engines → operations` rename ([operations-layer naming](69-operations-layer-naming.md)) harder. Issue [#494](https://github.com/eranroseman/memoria-vault/issues/494) asked whether `src/.memoria` should become an installable package; the full analysis is in the design note [install a real package](../releasing/0.1.0-alpha.4/tmp/install-a-real-package.md).

The target is settled here but **deferred**: reaching it changes the deployment mechanism and the on-disk vault shape (real blast radius), and it must not churn the tree before the operations rename lands. The incremental tooling step (below) is issue work and needs no ADR.

This decision does **not** touch code integrity. A common misconception — that ADR-55's golden copy protects the runtime code — is false: `golden.py`'s manifest covers `system/{templates,dashboards,patterns,eval,scripts}/`, three system files, and three `.obsidian` config files, with **no `.memoria/` prefix**. Code integrity is the MCP-only sandbox (agents cannot write files; [seven-layer architecture](46-seven-layer-architecture.md)) plus Git as source of truth. Packaging changes neither, so [src scaffold, populate, golden copy](55-src-scaffold-populate-golden-copy.md) is **untouched** and is not an assumption of this ADR.

## Decision

Make the Python runtime a normal, single-rooted, installed package named `memoria`; let `<vault>/.memoria/` hold only vault state and a venv — never source.

- **One import root, in both worlds.** A `src/`-layout package `memoria` (subpackages `operations/` [the renamed engines], `mcp/`, `runtime/policy/`, `lib/`). Every import is `memoria.*`; the 8 conftest entries and 11 `__file__` bootstraps are deleted. The dotted, un-importable `.memoria` package name is retired.
- **`pyproject.toml` is the single source of truth** — build (hatchling), `dynamic = ["version"]` from `src/memoria/__init__.py`, the three dependency tiers named as groups (runtime `dependencies`, `optional-dependencies.dev`, `optional-dependencies.cluster`, replacing three `requirements*.txt`), `[tool.pytest.ini_options]`, `[tool.ruff]`, and `[project.scripts]` console entry points.
- **Deploy installs a wheel, not source.** The installer creates `<vault>/.memoria/.venv` and `pip install`s a wheel (preferably a **prebuilt release asset with a pinned SHA256 verified before install**; `python -m build` only for dev-from-checkout). Code lands in `site-packages/memoria/`; `.memoria/` keeps the venv, rendered config, `lane-overrides/`, `logs/`, `golden/`, `.env`.
- **Console scripts replace path invocation.** The MCP host and cron wrappers launch `<vault>/.memoria/.venv/bin/memoria-policy-mcp --vault <vault>` (etc.) instead of an absolute `.py` path. This is what makes #494's "Option 3" runnable; it was un-runnable only because there was no installed distribution. Vault resolution stays a parameter (`resolve_vault()` is already arg→env, never `__file__`).
- **Schemas ship as package data by default.** The type vocabulary under `schemas/` is authored, runtime-static, and already resolved relative to `__file__` (`schema.py:25`), so shipping it in the wheel is continuity. *If* per-vault schema extensions are later wanted, schemas stay vault-side and `schema.py:25` must be rewritten from `__file__`-relative to `--vault`-relative — a named code cost on that branch only.
- **The policy-gate boundary resolves the policy core without version skew.** Today the gate (the MCP-only sandbox boundary) runs in the Hermes process, whose interpreter the installer does not pin, and reaches the core via an in-vault `sys.path` insert — which breaks once code is in site-packages. Because the gate is a hard-deny security boundary, **version skew is a correctness/security property, not a deployment chore**: an independently-installed gate running a stale policy could wave through a call the runtime treats as mutating. The **lean is to have the gate call the running policy MCP over the wire** (no second policy copy to drift — structurally skew-free), accepting per-call latency; falling back to "host installs the wheel **plus** a startup version assertion" only if that latency proves unacceptable. Locking this choice is the one prerequisite before execution.

**Migration is staged and ordered:**

1. **Now (issue work, no ADR):** a repo-root `pyproject.toml` scoped strictly to tooling — `[tool.pytest.ini_options]` (`testpaths` + `pythonpath`) and `[tool.ruff]` only; **keep `requirements-dev.txt`**, add no `[project]` table. Deletes the `conftest.py` `sys.path` block. Independent of everything else.
2. **With the `engines → operations` rename:** fold the tree into `src/memoria/operations/…` in that pass rather than renaming loose dirs twice.
3. **Then (this ADR):** flip deployment to wheel-install + console scripts, delete the runtime `__file__` bootstraps, make `.memoria/` data-only — after the policy-gate skew decision is locked.

**Sequencing rule: never repackage the runtime before the operations rename lands** — that is the "churn before naming settles" risk #494 flags.

## Consequences

- **Wins:** one import root; an importable name; the operations rename becomes a subpackage move; dependency tiers named in one file; atomic-feeling versioned installs replace delete-pruned mirroring; console scripts and full editor/type-checker/ruff support; a wheel (build once, install on N machines) materially strengthens [multi-machine deployment](63-multi-machine-deployment.md).
- **Transparency cost (the one real regression):** deployed code moves from plainly-inspectable files under `.memoria/` to `site-packages/` — harder to read or hand-edit in place. Mitigation: `pip install -e` against a checkout when live-tweaking. This is a debuggability cost, **not** an integrity one.
- **Wheel provenance is a new trust surface** absent from the rsync-from-checkout model: pin and verify the wheel's SHA256 (sign it when a signing story exists).
- **`pip install --upgrade` is not transactional** — a mid-install failure can leave a partial venv. A rollback path is required (retain the prior wheel and `--force-reinstall memoria==<previous>`, or snapshot the venv).
- **CI must build the wheel and smoke-import every entry point** — required, not optional. Packaging is a new failure surface (missing `__init__.py`, undeclared package data) that editable installs do not exercise.
- **Entry-point audit:** several console scripts are notional. `memoria-lint` and `memoria-eval` are each "pick one canonical entry" decisions (the linter `main()` is in `detectors.py`; eval spans `eval_dispatch.py`/`eval_score.py`); the rest need `main()` signature/return confirmation.
- **Tension with [repo as install unit](26-repo-as-install-unit.md):** the install unit shifts from the rsynced repo subtree to a built wheel. The repo remains the source of truth; what is *deployed* changes. Reconcile the two when this executes.

## When this matters

Context for the cadence review, not a gate — pick this up when **any** holds:

- **Distribution:** Memoria ships to operators who cannot run from a Git checkout, so rsync-from-source stops being viable.
- **Sequencing:** the `engines → operations` rename lands and the tree is being moved anyway — packaging rides along.
- **Support burden:** the `sys.path`/`__file__` bootstrapping (11 sites) or the three-way `requirements*.txt` split becomes a recurring source of import/CI breakage.
- **Prerequisite cleared:** the policy-gate version-skew resolution is locked (until then, do not start step 3).

**Guard:** the step-1 tooling `pyproject.toml` is safe to land anytime, but do **not** add a `[project]` table or change the deployment mechanism early — that drags target-stage risk forward with no benefit.

## Related

- **Tracking issue / origin:** [#494](https://github.com/eranroseman/memoria-vault/issues/494); full analysis in the design note [install a real package](../releasing/0.1.0-alpha.4/tmp/install-a-real-package.md).
- **Depends on:** [L1 component tests live in the pytest tree](44-tests-in-pytest-tree.md) (the conftest `sys.path` block this deletes); [seven-layer architecture](46-seven-layer-architecture.md) (the MCP-only sandbox that *is* the code-integrity story); [operations-layer naming](69-operations-layer-naming.md) (sequence packaging with the rename); [docs reference conventions](73-docs-reference-conventions.md) (land before path-pinned links move).
- **In tension with:** [repo as install unit](26-repo-as-install-unit.md) (install unit becomes a wheel).
- **Explicitly untouched:** [src scaffold, populate, golden copy](55-src-scaffold-populate-golden-copy.md) — golden never covered `.memoria/` code; this design does not change its scope.
- **Strengthens:** [multi-machine deployment](63-multi-machine-deployment.md) — build-once/install-on-N is more multi-machine-friendly than rsync-from-checkout.
