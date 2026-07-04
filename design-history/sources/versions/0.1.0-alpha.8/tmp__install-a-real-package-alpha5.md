# Install a real package — runtime packaging & deployment design

**Issue:** [#494](https://github.com/eranroseman/memoria-vault/issues/494) — *Research packaging `src/.memoria` as an installable Python package*
**Status:** design note (greenfield target + migration sketch) — long-form analysis behind [ADR-76](../../../adr/76-versioned-vault-release-reconciling-installer.md), recast around a **versioned vault release**, not a shipped wheel
**Date:** 2026-06-15 (recast; revised same day after a second red-team round; original 2026-06-14)
**Scope:** how Memoria should be distributed and deployed for (1) the repo's tests/CI and (2) a deployed vault, if we were designing from scratch — and what it would take to move the existing repo toward it.

> **Revision history.**
> - **Recast (⟲):** the first draft framed the answer as *"package the runtime as an installable wheel; the vault holds data, not source."* A red-team found that optimizes only the Python third of the deployable and breaks on the other two-thirds (authored profiles, the host-loaded gate shim, cron), so "vault holds no source" is unreachable; it also rested on a stale tree. The spine became **a versioned vault release + a source-agnostic reconciling installer**.
> - **Second round (⟲²):** a follow-up red-team found four things presented as settled that weren't. Folded in here: (1) the authored layer is **not** one bucket — boundary/contract files need *release-wins*, only true config gets *customize-preserve* (§2.1, §4.1); (2) "three-way merge" was the wrong word — golden's existing `upgrade()` is a *surface-for-human reconcile*, and the manifest's verdict is **per sub-layer**, not one meaning (§2.1, §4.4); (3) editable install is demoted from the deployment default to a PI-box dev convenience — the canonical deploy is a standard installed artifact (§2.1, §4.1, §5); (4) the gate imports the **single installed** core rather than vendoring a copy, which makes "skew-free by construction" actually true and the startup assertion redundant (§2.2, §4.5). Plus schemas resolved to vault-side (§6.7) and a lockfile requirement (§6).

---

## 1. The problem in one sentence

**The thing Memoria deploys is a configured vault, not a Python package** — yet the source tree and the deployment location are **the same dotted directory**: `src/.memoria` is simultaneously "the code we author" and "the thing rsynced into `<vault>/.memoria/`." That conflation forces:

- a **dotted, un-importable** top-level name (`.memoria` — a leading dot is a syntax error in `import`, and the name can't be a wheel distribution),
- **two parallel import mechanisms** that must agree: **10** `sys.path` entries in `tests/conftest.py` for the repo (8 under `src/.memoria` **plus** `scripts` and `.github/scripts`), and **11** per-entry-point `Path(__file__).resolve().parent…` bootstraps for the deployed vault (a 12th `sys.path` insert, in the policy-gate plugin, is anchored on `{{VAULT_PATH}}`, not `__file__`),
- a **two-phase rsync** deploy that mirrors a source tree: a bulk copy (excluding `.git` and the golden-covered system files, **without** `--delete`), then a `--delete` pass scoped to **7** named infra subtrees (`.env` excluded) to prune renamed files — instead of installing a versioned artifact.

But un-conflating source from deployment is only half the problem. The deeper issue the first draft missed: **the deployable is several different things wearing one rsync** (§1.2). A wheel addresses one of them. The real fix is a versioned *release* and an installer that reconciles each by its lifecycle.

### 1.1 What is true today (inventory)

The `engines → operations` rename is **already landed** ([#536](https://github.com/eranroseman/memoria-vault/issues/494), commit `aa7b894`). On disk, all 30 `.py` files live under `operations/`; `engines/` is an untracked husk containing only `__pycache__`.

| Fact | Detail | Source |
|---|---|---|
| Real packages | **3** `__init__.py`: `src/.memoria/memoria_runtime/` (+ `policy/`) **and** `plugins/memoria-policy-gate/` (the sandbox boundary; hyphenated → un-importable dir name) | repo scan |
| Loose script dirs | `operations/{processing,integrity,cleanup,telemetry,lib}`, `mcp/` — **no** `__init__.py`; reached via `sys.path` | repo scan |
| Repo import root | **10** dirs inserted in `tests/conftest.py` (8 `src/.memoria/…` + `scripts` + `.github/scripts`); pytest run as `python -m pytest tests/ -q` (no `pyproject`/`pytest.ini`) | `tests/conftest.py:7-16` |
| Runtime import root | **11** files self-bootstrap `sys.path` from `__file__`; the policy-gate plugin adds a 12th insert via `{{VAULT_PATH}}`, not `__file__` | `mcp/policy_mcp.py`, `mcp/ingest_mcp.py`, … |
| Code count | 30 `.py` under `src/.memoria`; 7 repo-tooling scripts in `scripts/`; 1 in `.github/scripts/` | repo scan |
| Deploy | `scripts/install.sh` rsyncs `src/.memoria/` → `<vault>/.memoria/` (two-phase); creates `<vault>/.memoria/.venv`; `pip install`s **deps only**, never the code; **39** hardcoded `.memoria` references ⟲² | [scripts/install.sh](../../../../scripts/install.sh) |
| Runtime launch | MCP host runs absolute paths: `command: <vault>/.memoria/.venv/bin/python`, `args: [<vault>/.memoria/mcp/policy_mcp.py, --vault, <vault>]` | rendered `config.yaml` |
| Vault resolution | already explicit: `_shared.resolve_vault()` is pure arg→env (`--vault` → `MEMORIA_VAULT_PATH` → `OBSIDIAN_VAULT_PATH`), **no `__file__` fallback** | `mcp/_shared.py:39` |
| Code integrity | **Not golden.** Protected by the **MCP-only sandbox** (agents cannot write files; [[mcp-only-agent-sandbox]]) + **git**. ADR-55 golden covers *vault system files only* — manifest = `system/{templates,dashboards,patterns,eval,scripts}/` + `home.md`/`system/vocabulary.md`/`AGENTS.md` + 3 `.obsidian` config files; **no `.memoria/` prefix** | `golden_restore.py:30-50`, [ADR-55](../../../adr/55-src-scaffold-populate-golden-copy.md) |
| Golden has **two** modes ⟲² | `restore` = **release-wins** (restore drifted/missing system files from the golden copy); `upgrade` = a **three-way reconcile** (src vs old-golden vs live) that *preserves* customizations and routes a PI-edited-and-release-also-changed file to a `conflicts` bucket (exit 2, install.sh warns "run check to review") — **surface-for-human, never auto-merge** | `golden_restore.py:137` (`restore`), `:154-214` (`upgrade`); `install.sh:386` |
| Authored subtrees are **mirrored today** ⟲² | the 7 `--delete` rsync subtrees (`profiles operations mcp memoria_runtime schemas scripts plugins`) are **release-wins** today — PI edits under them are clobbered on refresh. Only the golden-covered `system/` files get the `upgrade` reconcile | `install.sh:342-346` |
| Policy lives in `lane-overrides/`, **not** `config.yaml` ⟲³ | `config.yaml` holds only `model`/`mcp_servers` (a policy *server* declaration; the "allowlist" hits in it are ADR-27 comments). The **enforced** policy — `policy.allow/deny.{skills,write,read}`, `require: [audit_log,…]`, `routing` — is in `lane-overrides/<lane>.yaml`, parsed by `policy_mcp.parse_lane` | `profiles/*/config.yaml`, `policy_mcp.py:134-168` |
| `lane-overrides/` is **release-wins today** (latent bug) ⟲³ | it is **not** in the 7 delete-scoped subtrees, but the phase-1 `rsync -a` (no `--delete`) overwrites it from the shipped copy — so a PI edit to a lane file is silently clobbered on the next install | `install.sh:322`, ships `lane-overrides/librarian.yaml` |
| Rendered `config.yaml` lives **outside the vault** ⟲³ | `hermes profile install` deploys the substituted `config.yaml` to `~/.hermes/profiles/<name>/` — there is **no `<vault>/.memoria/config/`** dir | `install.sh:595-616` |
| Deps, three files | `requirements-dev.txt`, `src/.memoria/mcp/requirements.txt`, `…/requirements-cluster.txt`; runtime deps are **all `>=`** today (`mcp>=1.27.2`, `PyYAML>=6.0.3`, `pymupdf4llm>=1.27.2.3`) — no pinning, no lockfile ⟲² | repo scan |

### 1.2 The deployable is several layers, not one — and the authored layer is itself split ⟲²

The seven subtrees `install.sh` lays down have **different lifecycles and different reconcile needs**. The first recast got the three coarse layers right but lumped all authored content together; the security-relevant split is finer:

- **Code** — `operations/`, `mcp/`, `memoria_runtime/`, `lib/`. Importable Python; versioned; never hand-edited.
- **Authored — boundary / contract** — the `plugins/memoria-policy-gate/` shim (the security boundary, host-loaded), the **shipped `lane-overrides/<lane>.yaml`** (⟲³ *this* is the enforced policy — allow/deny/require/routing — **not** `config.yaml`, which has no policy block), and the **baseline** `schemas/` type vocabulary (the validation contract), plus cron wrappers. A release that patches any of these **must** land.
- **Authored — PI config** — `SOUL.md`, `SKILL.md`, **PI-added** schema types, and **per-vault lane deltas** (⟲³ the PI's lane tuning — today there is *no* preserved channel for these, and the rsync clobbers in-file edits; §2.1 proposes a tighten-only overlay). Genuine preference the PI may customize.
- **Host-side config** ⟲³ — the rendered `config.yaml` Hermes actually reads lives in `~/.hermes/profiles/<name>/`, **outside the vault**, deployed by `hermes profile install` (`install.sh:595-616`). It is rendered at install from the profile template; the design must treat it as a managed-at-install layer, not pretend it lives in `<vault>/.memoria/config/` (which doesn't exist).
- **Per-vault state** — notes, `logs/`, `.env`, the golden store, and the PI lane overlay (above). Never touched by an upgrade.

This split is the crux. "Vault holds data, not source" is false — the gate shim, the shipped lane policy, profiles, skills, and cron wrappers are *authored source* that must stay vault-side. The honest invariant is: **runtime code installs into a venv; boundary/contract authored files (gate shim, shipped lane policy, baseline schemas) track the release (release-wins); PI-config authored files are preserved; host config is rendered at install into `~/.hermes/`; state is never touched.**

---

## 2. The one decision everything follows from ⟲ recast

> **Distribute Memoria as a single versioned vault release, and deploy it with a source-agnostic reconciling installer `install(release_root, vault_path)` that handles each layer by its lifecycle. The runtime becomes a real `memoria` package; the canonical deploy installs it as a standard artifact, with editable install offered only as a PI-box dev convenience.**

Two decisions are load-bearing; everything else follows.

### 2.1 Load-bearing decision 1 — one versioned release + a reconciling installer, layered by lifecycle

`install(release_root, vault_path)` is idempotent and does **not** care whether `release_root` is a checked-out Git tag or an unpacked tarball. It reconciles each sub-layer by the right policy — using mechanisms golden **already has** (`restore` = release-wins, `upgrade` = customize-preserve), so this is routing, not a new merge engine:

| Sub-layer | Examples | Reconcile policy | Manifest verdict on SHA mismatch |
|---|---|---|---|
| **Code** | runtime, the policy core | install into the venv (replace) | **tamper** → block/reinstall |
| **Boundary / contract** | gate shim, **shipped `lane-overrides/<lane>.yaml`** (the enforced policy), baseline schema types, cron wrappers | **release-wins** (golden `restore` semantics) — apply the release, back up + report the prior file; **never preserve-live** | **restore** → release wins |
| **PI config** | `SOUL.md`, `SKILL.md`, PI-added schema types, **per-vault lane deltas (tighten-only overlay — see below)** | **customize-preserve + surface** (golden `upgrade`): release change applies only where live still matches the old baseline; a real conflict is preserved and reported, never auto-merged | **customization** (expected; *allow-add* / tighten-only) |
| **State** | notes, `logs/`, `.env`, golden store, PI lane overlay | never touched | not in the manifest |

Two consequences of getting this split right:

- **The boundary row closes a security hole the flat model opened.** If the gate shim, the **shipped lane policy**, and schemas were customize-preserved, a release that patches a gate bypass *or tightens a lane's write-deny after a finding* would be defeated by incidental PI drift (the [[mcp-only-agent-sandbox]] still holds against *agents*, but the *upgrade meant to fix the boundary* wouldn't land). Release-wins on boundary files is mandatory. This is **not a regression**: those files are release-wins today (§1.1) — the latent bug is that PI lane edits are clobbered with no preserved channel.
- **The policy store needs an overlay — the security crux. ⟲³** The enforced policy is the shipped `lane-overrides/<lane>.yaml`, so it must be **release-wins** (a tightening after a finding has to land). But the PI also needs to tune their lane per-vault ([[pi-direct-access-rule]]) — impossible today, since the rsync clobbers in-file edits. Resolution: a **separate per-vault lane *overlay*** merged over the shipped baseline at `load_lane` time, with a **tighten-only merge** — an overlay may add a `deny` or drop an `allow`, but a release's `deny` is final and an overlay can **never widen** the boundary. This keeps the gate patchable while giving the PI a real, preserved tuning channel, and mirrors [ADR-63](../../../adr/63-multi-machine-deployment.md)'s structural-over-behavioral stance. **This merge rule is the most security-sensitive decision in the design; the ADR must specify it** (load-time merge in `policy_mcp`, tighten-only semantics, overlay file location). Whether any PI *widening* is permitted within a release-defined ceiling is the open sub-question.

The release carries **one version** (`memoria.__version__`) and a **content-addressable manifest** (SHA per file) over the code and authored layers. The manifest is **one baseline-comparison mechanism with a per-sub-layer verdict** (the table's right column) — *not* a single meaning. The first recast over-claimed "triple duty including drift detection for all authored content"; once PI customization is allowed, a SHA mismatch on a PI-config file is *expected*, so "drift = bad" has no teeth there. The coherent split: **code = tamper-verify; boundary = restore-verify; PI config = customization-classify** (golden's `upgrade` already encodes exactly these buckets — `unchanged`/`customized`/`conflicts`).

Integrity *protection* is unchanged — the MCP-only sandbox + git ([[mcp-only-agent-sandbox]]). The manifest adds verification, never a new protection mechanism, and `site-packages` is **not** claimed as read-only.

### 2.2 Load-bearing decision 2 — extract a genuine, tiny, standalone policy core

The policy-gate is the security boundary (it hard-denies tool calls). Today its real import chain is **`policy_hook → policy_mcp → memoria_runtime.policy`** — it reaches its decision *through* the MCP layer, an accident of organic growth. Extract a small, dependency-free **policy core** (the `MUTATING_ACTIONS` set + path matching, today in `memoria_runtime/policy/paths.py`, which imports only `re`) that **both** the gate shim and the MCP servers import.

**The gate imports the single installed core — it does not vendor a copy.** ⟲² This is the decisive correction. Vendoring a committed duplicate of `paths.py` would let it drift from the real one at *authoring* time (someone edits the real module, forgets the vendor), and "one release, one root" can't catch skew that entered before the release was cut. Because the core is pure-stdlib, the gate can instead `sys.path`-insert the venv's `site-packages` and import the *one* installed `memoria.runtime.policy` — co-versioned **by construction**, with no second copy to drift and no IPC. This makes the startup version-assertion genuinely **redundant** (drop it; the first recast leaned on it as the guarantee, but by-construction safety needs no assertion).

Two constraints to state. First, the host interpreter must be **≥ the package's minimum Python** (pure-source import requires compatible syntax). Second — and this is "by construction" vs "by luck" — an **import-purity invariant ⟲³**: nothing in the chain `memoria/__init__.py` → `runtime/__init__.py` → `runtime/policy/__init__.py` → `paths.py` may carry a **module-level non-stdlib import** (today `paths.py` imports only `re`). The day someone adds `import yaml` to a package `__init__`, the host-process gate breaks at import. Guard it with a **CI test that imports `memoria.runtime.policy` from a bare interpreter with no venv deps on the path** — cheap, and the only thing keeping the design "by construction" going forward. And specify the failure mode the first recast left blank: if the gate cannot import its core, it **fails closed** (deny) — a boundary that can't load its policy must never wave calls through.

If a future host makes in-process import infeasible and vendoring becomes unavoidable, then the copy must be **generated from `paths.py` at build time, never committed**, and the version assertion (otherwise redundant) returns, **fail-closed** — a *version mismatch* is rare and upgrade-time (acceptable to refuse-start), unlike IPC's *server crash*, which is operational (why IPC's fail-closed was rejected). §4.5 makes this precise.

---

## 3. World 1 — In the repo (tests / CI)

### 3.1 Layout (`src/`-layout package)

The `operations/` tree already exists (post-#536); the remaining move is the `src/.memoria` → `src/memoria` un-hiding and the `pyproject`.

```
pyproject.toml                 ← single source of truth: build, deps, scripts, pytest, ruff
src/
  memoria/
    __init__.py                ← __version__
    operations/                ← already exists (ADR-69 / #536)
      processing/ingest/…
      integrity/{linter,golden}/…
      cleanup/{reconcile,…}/…
      telemetry/{board,metrics,eval}/…
    mcp/
      policy.py                ← def main(): … (was policy_mcp.py)
      ingest.py  tasks.py  patterns.py  cluster.py
      _shared.py
    runtime/
      policy/                  ← the shared decision core (gate + servers import THIS; §2.2)
    lib/                       ← inbox, schema (shared helpers)
tests/
  conftest.py                  ← FIXTURES ONLY (no sys.path surgery)
scripts/                       ← repo-dev tooling (doctors); see §3.4
```

Imports become explicit and stable:

```python
from memoria.operations.processing.ingest import runner
from memoria.runtime.policy import MUTATING_ACTIONS
from memoria.lib import inbox
```

No bare `import runner`, no sibling-magic `import classify`, no `sys.path.insert`.

### 3.2 `pyproject.toml` — one source of truth

```toml
[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[tool.hatch.version]
path = "src/memoria/__init__.py"

[project]
name = "memoria"
dynamic = ["version"]
requires-python = ">=3.11"
dependencies = ["mcp>=1.27.2", "PyYAML>=6.0.3", "pymupdf4llm>=1.27.2.3"]  # see §6.8 — pair with a lockfile

[project.optional-dependencies]
dev     = ["pytest==9.1.0", "ruff==0.15.17", "yamllint==1.38.0", "pre-commit==4.6.0"]
cluster = ["networkx>=3.6.1", "bertopic>=0.17.4"]

[project.scripts]
memoria-policy-mcp   = "memoria.mcp.policy:main"
memoria-ingest-mcp   = "memoria.mcp.ingest:main"
memoria-tasks-mcp    = "memoria.mcp.tasks:main"
memoria-patterns-mcp = "memoria.mcp.patterns:main"
memoria-cluster-mcp  = "memoria.mcp.cluster:main"
memoria-lint         = "memoria.operations.integrity.linter.cli:main"
# … board-export, metrics, eval, retraction, reconcile

[tool.pytest.ini_options]
testpaths = ["tests"]
addopts = "-q"

[tool.ruff]
# moved verbatim from ruff.toml
```

The `[project.scripts]` block keeps the three dependency worlds (runtime / dev / cluster) named in one file. **It does not, by itself, fix reproducibility** — the `>=` ranges match today's `requirements.txt` exactly (parity, not a regression), but a security-boundary system should pin; pair the `pyproject` with a lockfile (§6.8).

**Entry-point audit (verified).** Every named `main()` exists and is zero-arg; `reconcile.main()` returns an `int` exit code, which `[project.scripts]` maps to the process exit status correctly. Two are genuinely unresolved "pick one canonical entry" decisions:
- `memoria-lint` → `…linter.cli:main` **doesn't exist yet**; the linter's `main()` lives in `detectors.py`, alongside `golden_restore.py`/`session_summary.py`/`precommit_check.py` mains — pick one canonical entry.
- `memoria-eval` → **two** files (`eval_dispatch.py`, `eval_score.py`) — same call.

The rest (`board_export.py`, `metrics_aggregate.py`, `retraction.py`) have confirmed zero-arg mains.

### 3.3 Dev & CI workflow

```bash
pip install -e ".[dev]"          # editable for dev/test only (see §4.1 — NOT the deploy default)
python -m pytest                 # config from pyproject; conftest = fixtures only
ruff check .
```

- **Tests run against one import root**, killing the conftest path-ordering fragility. *Caveat:* an editable install imports the **working tree**, not a built artifact — so it does **not** catch packaging errors (missing `__init__.py`, undeclared package data).
- **`conftest.py` shrinks to fixtures**; the 10-entry `sys.path` block is deleted.
- **CI builds the artifact and smoke-imports it — required, not optional.** Build the wheel, install it into a clean venv, and import every entry point. This is the gate for the *canonical* deploy artifact (§4.1), so here CI **does** test what ships. The editable dev path is a *different* artifact, covered by the test suite — see §4.1 on the two-artifact reality.

### 3.4 Repo tooling (`scripts/`, `.github/scripts/`)

These are **repo-dev** tools (doctors, `pr_policy.py`) that never deploy. Recommend keeping them as standalone scripts run from the repo, importing `memoria.*` since the package is installed in dev. Fold them under `memoria.tooling` with their own `[project.scripts]` only if a tool ever needs to ship.

---

## 4. World 2 — In a deployed vault (runtime)

### 4.1 The reconciling installer (replacing the rsync mirror)

```
<vault>/.memoria/
  .venv/                 ← the `memoria` package installed as a standard artifact (copy-install)
  profiles/              ← authored: SOUL/SKILL = PI-config; config.yaml = template (model/mcp_servers, NO policy)
  plugins/               ← the policy-gate shim (boundary; host loads it in ITS interpreter)
  schemas/  system/      ← authored: baseline = boundary/contract; PI-added types = config
  lane-overrides/        ← shipped <lane>.yaml = the ENFORCED policy (boundary/release-wins); PI overlay = preserved
  logs/  golden/         ← per-vault state
# rendered config.yaml is NOT in the vault — `hermes profile install` deploys it to
# ~/.hermes/profiles/<name>/config.yaml (host-side config layer, outside the vault)
```

Installer flow:

1. **Resolve `release_root`** — a checked-out Git tag (default) or an unpacked, hash-verified release tarball (the no-checkout path; §6). The installer **owns where `release_root` lives** and its lifecycle (see the self-containment note below).
2. Create/keep `<vault>/.memoria/.venv` (per-vault isolation stays).
3. **Install the code layer (canonical = copy-install):** `pip install "$release_root"` lands the package in the venv's `site-packages`, leaving a **self-contained vault** — the live runtime does not depend on an external checkout. Add `.[cluster]` when clustering is enabled. *Editable (`pip install -e`) is an opt-in for the PI's own box* when live-tweaking; it trades self-containment for inspectability (see below).
4. **Reconcile the authored layer by sub-class (§2.1):** boundary/contract files (gate shim, **shipped `lane-overrides/<lane>.yaml`**, baseline schemas, cron wrappers) are laid down **release-wins** (back up + report any prior); PI-config files (`SOUL.md`/`SKILL.md`, PI-added types, **the per-vault lane overlay**) go through golden's `upgrade` **customize-preserve + surface**.
5. **Render host config:** substitute the venv console-script paths + vault path into each profile's `config.yaml` (the existing `{{PYTHON}}`/`{{VAULT_PATH}}`/`{{PROFILE}}` substitution) and let `hermes profile install` deploy it to **`~/.hermes/profiles/<name>/`** (the host-side config layer, §1.2 — *not* the vault). Render the cron wrappers the same way.
6. **Never touch state:** `logs/`, `.env`, golden store, and the PI lane overlay. (The shipped `lane-overrides/<lane>.yaml` baseline is release-wins per step 4; only the per-vault overlay is preserved.)

**Self-containment vs inspectability — two artifacts, named honestly.** ⟲² The canonical copy-install keeps the *vault* self-contained (like today's rsync, but as a proper install) and is the artifact CI smoke-tests (§3.3) — *test-what-you-ship holds on this path*. Editable install gives plain inspectability but leaves a `.pth` from `.venv` into `release_root`: move, delete, or `git checkout` that checkout and the live runtime breaks. So editable is a **PI-box dev convenience, not the deploy default** — the first recast over-generalized it. Inspectability on a copy-installed vault is recovered the normal way (read `site-packages/memoria/`, or re-install editable temporarily).

**Caveat — "self-contained" is the vault, not the whole install. ⟲³** Hermes reads its config from `~/.hermes/profiles/<name>/config.yaml`, rendered at install (step 5), **outside the vault**. So a deployed Memoria is *vault (code + data) + host config in `~/.hermes/`*; the demotion of editable buys vault self-containment, not a single self-contained artifact. This host-config layer exists today and is unchanged here — but the design must name it (it's where the console-script paths and `${OBSIDIAN_MCP_PORT}`/`${OBSIDIAN_API_KEY}` env refs resolve), not let "self-contained vault" imply the runtime needs nothing outside `<vault>/`.

### 4.2 Runtime launch — console scripts

```yaml
# rendered config.yaml
mcp_servers:
  policy:
    command: "<vault>/.memoria/.venv/bin/memoria-policy-mcp"
    args:    ["--vault", "<vault>"]
    timeout: 30
# equivalently: <vault>/.memoria/.venv/bin/python -m memoria.mcp.policy --vault <vault>
```

> **Why console scripts fit now but not today.** They require an *installed distribution* exposing entry points on the venv's `bin/`. Today the host invokes a `.py` file by absolute path against a source tree. An installed package gives the venv `bin/memoria-policy-mcp` for free. #494's "Option 3 (package all + console scripts)" wasn't wrong — it was un-runnable on a rsync'd source tree. The blocker was the deployment mechanism, not packaging.

### 4.3 Delete the `__file__` import-root bootstraps

- **Import-root discovery** — the 11 `_RUNTIME_ROOT = Path(__file__)…; sys.path.insert(...)` bootstraps exist only to find sibling modules. Packaging **deletes all 11**; imports become `memoria.*`.
- **Vault resolution** — *already* explicit. `_shared.resolve_vault()` is pure arg→env with no `__file__` fallback. It stays as-is.

Hardcoded *data* relpaths (`system/logs/audit.jsonl`, `.memoria/lane-overrides`, `.memoria/golden`) stay — they're relative to `--vault`, which is correct. **Exception: `schemas/`.** `schema.py:25` resolves schemas from **code location** (`SCHEMAS_DIR = Path(__file__).resolve().parent.parent.parent / "schemas"`). §6.7 resolves this — schemas stay vault-side, which carries a named code cost.

### 4.4 Upgrades and integrity

**Integrity protection is unchanged.** Verified against `golden_restore.py:30-50`: the ADR-55 manifest is `system/{templates,dashboards,patterns,eval,scripts}/`, the files `home.md`/`system/vocabulary.md`/`AGENTS.md`, and three `.obsidian` config files. **No `.memoria/` prefix** is covered — runtime code, `schemas/`, and `lane-overrides/` were **never** golden. Code-integrity protection is the MCP-only sandbox + git, and this design touches neither.

What the release manifest **adds** is *verification* over code + authored content with a per-sub-layer verdict (§2.1) — a superset of golden's old scope, but still verification, not protection. There is **no ADR-55 reconciliation blocker**; this design *extends* ADR-55's `upgrade` mechanism rather than colliding with it.

**Upgrade & rollback.** `pip` **does** run on every up/down-grade ⟲² — entry-point wrappers and deps are generated at install time, so any release that adds/renames a console script or bumps a dep needs a `pip` re-run (install.sh does this). The point is *not* "no pip"; it's that **rollback safety comes from the source-of-truth being the versioned release, not from pip being transactional**: `git checkout <prev-tag> && ./install.sh` re-installs the prior version cleanly, so a partial mid-install pip failure is recoverable by re-running, not by unwinding a half-applied transaction. (On the operator copy-install path, retain the previous release tarball as the equivalent net.)

### 4.5 The policy-gate boundary — resolved by the policy-core extraction (§2.2)

The gate runs in the **host process, whose interpreter the installer does not pin** — only the MCP servers it spawns get `{{PYTHON}}` (the venv); the operator launches the host and the repo doesn't own that interpreter (corroborated at `install.sh:542`: *"the plugin runs in the Hermes process, so no PYTHON"*). Today the gate does `sys.path.insert({{VAULT_PATH}}/.memoria/mcp)` and reaches the core via the fat chain `policy_hook → policy_mcp → memoria_runtime.policy`.

**Version skew is a security property, not a deployment chore.** If the gate runs a stale `MUTATING_ACTIONS`, a call the new runtime treats as mutating can be waved through by an out-of-date hard-deny boundary.

| Option | How the gate reaches the core | Skew safety | Verdict |
|---|---|---|---|
| **Import the single installed core (§2.2)** — gate `sys.path`-inserts the venv `site-packages` and imports `memoria.runtime.policy`; **no vendored copy** | in-process import of the *one* installed, dependency-free core | **✓ skew-free by construction** — one install, no second copy to drift; assertion redundant | **chosen** — smallest change from today (re-point the existing insert at the install, not the source tree); requires host interpreter ≥ package min-Python, the **import-purity invariant + CI gate**, and **fail-closed on import failure** (§2.2) |
| Vendor a *generated* copy + fail-closed assertion | gate imports its own copy, generated from `paths.py` at build | ✓ if generated, ✗ if committed | **fallback** — only if in-process import is infeasible; copy must be build-generated, never committed; assertion fail-closed (mismatch is rare/upgrade-time) |
| Gate calls the policy MCP over the wire (IPC) | IPC to the running `policy` server | ✓ skew-free | rejected — per-call latency **and** a fail-closed availability dependency (a *crashed server* bricks the agent, unlike a rare version mismatch) |
| Host installs the full `memoria` wheel too | `import memoria.runtime.policy` from a second install | ✗ skew-prone | rejected — two independent installs of the boundary code can drift |

**Lean:** import the single installed core (option 1) — it makes "skew-free by construction" *actually* true (no second copy anywhere), needs no assertion, and is the smallest delta from today's mechanism (the gate already does a `sys.path` insert + import; just point it at the install). Whichever ships, the hyphenated dir name (`memoria-policy-gate`) must become an importable module name, and **the fat chain `policy_hook → policy_mcp → memoria_runtime.policy` must be cut to a real `policy` core first** — that refactor is the precondition for the gate dropping its source-tree reach-through.

---

## 5. How this scores vs. today

| Concern | Today | This design |
|---|---|---|
| Import roots | 10 (conftest) + 11 `__file__` inserts | **1** (installed package) |
| Top-level name | `.memoria` (un-importable) | `memoria` |
| Test import root | divergent `sys.path` ordering | single root + a **required CI artifact-smoke** that tests the canonical deploy artifact (§3.3) |
| Deployable unit | one rsync mirroring source | **a versioned release**, sub-layers reconciled by lifecycle (§2.1) |
| "Vault holds no source" | n/a | **honest version:** code → venv; boundary authored = release-wins; PI-config authored = preserved; state untouched |
| Authored reconcile | `system/` reconciled; the 7 subtrees **mirrored** (clobber) | boundary = release-wins (parity); **PI config = preserved + surfaced** (upgrade for SOUL/SKILL) |
| Policy store (`lane-overrides/`) | release-wins via phase-1 rsync; **PI edits silently clobbered** (latent bug) | shipped baseline = release-wins (security patches land); **PI tuning = preserved, tighten-only overlay** (§2.1) |
| Host config (`~/.hermes/`) | rendered `config.yaml` deployed by `hermes profile install` | **unchanged** — acknowledged as a host-side layer rendered at install (§1.2); the "self-contained vault" claim is scoped to code + data |
| Dependency split | 3 `requirements*.txt`, blurred | one `pyproject`, named groups + **a lockfile** (§6.8) |
| Deploy | two-phase rsync (bulk + scoped `--delete`) | source-agnostic reconciling installer |
| Upgrade / rollback | mirror + prune; recovery = re-run installer | `git checkout <tag> && ./install.sh` (pip re-runs; recovery = re-run, not transaction-unwind) |
| Console scripts | don't fit (path invocation) | **fit** (venv `bin/`) |
| Code integrity | sandbox + git — **not golden** | **protection unchanged**; manifest adds *per-sub-layer verification* |
| Policy-gate import | `{{VAULT_PATH}}/.memoria/mcp` on `sys.path`, fat chain | imports the **single installed core**, skew-free by construction (§2.2/§4.5) |
| Transparency | code plainly inspectable in vault | **canonical copy-install:** read `site-packages/`; **opt-in editable** on the PI box for in-place inspection — not pure upside |
| Multi-machine ([ADR-63](../../../adr/63-multi-machine-deployment.md)) | rsync-from-checkout per machine | **the versioned release + copy-install** is the natural N-vault substrate; **editable does *not* generalize** (a shared `release_root` means one `git checkout` mutates all N runtimes; per-machine checkouts are rsync-per-machine again) |

---

## 6. Honest trade-offs & mitigations

1. **The reconciling installer is more logic than `cp -R`/rsync** — but it is *routing over golden's existing two modes* (`restore` release-wins, `upgrade` customize-preserve), not a new merge engine. The hard part is the **sub-layer classification** (§2.1): which authored files are boundary/contract vs preference. The ADR must enumerate that mapping; it's the single most security-sensitive list in this design.
2. **The policy-core extraction is real refactor work** and must precede the gate dropping its reach-through (§4.5). It's the one genuine prerequisite before the spine ships.
3. **The release manifest must be built and verified in CI** — a new artifact whose verdict is per-sub-layer (code = tamper, boundary = restore, PI-config = customization).
4. **No shipped wheel removes a trust surface the first draft added.** Git-tag deploy carries no fetch-and-trust step. *When* the operator tarball path appears, pin its SHA256 and verify before unpacking (sign when a signing story exists) — deferred to the audience that needs it.
5. **Build backend + version source.** hatchling + dynamic version from `src/memoria/__init__.py:__version__` (§3.2).
6. **Transparency is a PI-box opt-in, not a default win.** ⟲² The canonical copy-install puts code in `site-packages/`; editable install (inspectable in place) is available on the PI's machine but breaks vault self-containment, so it isn't the deploy default. Don't claim "transparency kept" as pure upside.
7. **Schemas stay vault-side — `[[pi-direct-access-rule]]` forces it (not a coin-flip).** ⟲² If schemas shipped as package data, a PI couldn't add a note type without cutting a release — which is not "PI-accessible from the Obsidian UI." So schemas **stay under `<vault>/.memoria/schemas/`**, with the named code cost: **`schema.py:25` moves from `__file__`-relative to `--vault`-relative**, and the **`len(types) == 18` self-test relaxes** to a baseline-subset check (PI additions allowed). Reconcile: baseline types are boundary (release-wins); PI-added types are config (allow-add, preserved).
8. **Dependency reproducibility needs a lockfile (net-new improvement).** ⟲² Today's runtime deps are all `>=` (no pinning) — so moving to `pyproject` `>=` is parity, *not* a regression. But two vaults installed a week apart can resolve different trees, which is poor for a security boundary. Adopt a lockfile with hashes (`pip-compile`/`uv lock` + `--require-hashes`) as the actual reproducibility win; the `pyproject` ranges stay the human-edited source, the lock is the installed truth.

---

## 7. Migration path & blast radius

This note is the **target**, not an immediate migration. The spine changes the *deployment mechanism* (reconciling release-install vs rsync) and the *on-disk vault shape* (code moves into the venv). Full blast radius:

- `install.sh` (rewrite as the reconciling installer; the **sub-layer classification** of §2.1; authored staging; `{{PYTHON}}` substitution),
- every rendered `config.yaml` **and the cron wrappers** (both carry `{{PYTHON}}`/`{{VAULT_PATH}}`, both repoint at console scripts),
- the policy-gate boundary (§4.5 — extract the core, re-point the import at the install),
- the **`src/.memoria` → `src/memoria` un-hiding** (the dotted path is hardcoded **39×** in `install.sh`),
- `schema.py` (the `__file__`→`--vault` rewrite and the self-test relax; §6.7).

*Not* in the blast radius: ADR-55 golden / `tests/test_golden_restore.py` — golden never covered `.memoria/` code; the release manifest *extends* golden's `upgrade` mechanism rather than reworking it (§4.4).

Staged path:

1. **Now (issue work, no ADR):** a repo-root `pyproject.toml` scoped **strictly to tooling** — `[tool.pytest.ini_options]` (`testpaths` + `pythonpath`) and `[tool.ruff]` only. **Keep `requirements-dev.txt`** — no `[project]` table yet. Deletes the conftest `sys.path` block. Independent of everything; the `operations` rename is already done, so nothing blocks this.
2. **Packaging:** add `[project]` + `src/`-layout, install editable *for dev/test*, delete the 11 `__file__` bootstraps, wire console scripts, add the lockfile. Stands on its own import-hygiene merits.
3. **The spine:** reconciling installer over a versioned release (with the §2.1 sub-layer classification); extract the policy core and re-point the gate (§2.2) **first**; canonical copy-install; introduce the release manifest; vault becomes code-in-venv + reconciled-authored + state.

Sequencing note: step 2 banks nearly all the import-hygiene wins **without** touching the deployment mechanism — pursue it independently. Step 3 is gated on the policy-core extraction and on the authored sub-layer classification.

---

## 8. ADR status

This note backs **[ADR-76](../../../adr/76-versioned-vault-release-reconciling-installer.md)** (deferred). The two load-bearing decisions (§2.1 release + reconciling installer, §2.2 policy-core extraction) are the ADR's spine. ADR-76:

- carries **`assumes: [44, 46, 55, 69, 73]`** — ADR-44 (the conftest `sys.path` block we delete), ADR-46 (MCP-only sandbox = integrity protection), **ADR-55** (golden's `restore`/`upgrade` mechanism, *generalized* into the per-sub-layer release manifest), ADR-69 (operations naming, landed), ADR-73 (docs-reference conventions),
- sits at `status: deferred` with `nav_exclude: true` and a *When this matters* section, re-judged each release per the [ADR-only decision model](../../../adr/),
- is **in tension with [ADR-26](../../../adr/26-repo-as-install-unit.md)** (install unit becomes a versioned release) and **strengthens [ADR-63](../../../adr/63-multi-machine-deployment.md)** *via the release + copy-install path* (not via editable),
- marks #494's "Option 3 (package all + console scripts)" as the eventual direction, with the deployment-mechanism change as its precondition.

**Three pieces must be resolved in the ADR before it converts** (rounds two and three surfaced these):

1. **The `lane-overrides` overlay merge rule (§2.1) — the gating item.** The enforced policy is the shipped lane file (boundary/release-wins), so security tightenings land; the PI tunes via a preserved, **tighten-only overlay** merged at `load_lane`. This is the most security-sensitive decision in the design — round three caught the prior draft filing the policy store under "state, never touched," which would have re-opened the silent-security-patch-drop hole. Specify the merge semantics, the overlay location, and whether any PI widening is allowed within a release-defined ceiling.
2. **The authored sub-layer classification (§2.1)** — the full boundary-vs-PI-config file list, of which #1 is the sharpest case.
3. **The policy-gate import resolution (§2.2/§4.5)** — confirm in-process import of the installed core works in the host interpreter, add the **import-purity invariant + bare-interpreter CI test**, and lock **fail-closed** on import failure.

***When this matters*** — pick up when **any** holds:

- **distribution:** Memoria ships to operators who can't run from a Git checkout → the tarball delivery + copy-install path go live;
- **support burden:** the `sys.path`/`__file__` bootstrapping (11 sites) or the three-way `requirements*.txt` split becomes a recurring import/CI breakage source → step 2 is the relief and can land first;
- **boundary risk:** any near-miss where the gate and servers could run divergent policy → the policy-core extraction moves to the front.

The step-1 tooling `pyproject.toml` (tooling-only, `requirements-dev.txt` retained) remains **issue work, no ADR**.

---

## 9. Validation commands (for whichever step ships)

```bash
# Step 1 (tooling-only pyproject; requirements-dev.txt retained):
python -m pytest -q          # green without the conftest sys.path block
ruff check .
scripts/test.sh all

# Step 2 (packaging, editable for dev/test):
pip install -e ".[dev]"
python -c "import memoria; print(memoria.__version__)"
memoria-policy-mcp --vault /path/to/Memoria-test --help   # console script resolves
python -m build && pip install dist/memoria-*.whl   # CI: smoke the CANONICAL artifact (test-what-you-ship)

# Step 3 (the spine — reconciling installer over a release; canonical copy-install):
git checkout v<ver> && ./install.sh /path/to/Memoria-test
#  - boundary files (gate shim, SHIPPED lane-overrides/<lane>.yaml, baseline schemas) are release-wins
#  - PI-config (SOUL/SKILL, added types, the per-vault lane OVERLAY) preserved + conflicts surfaced
#  - state (logs, .env, golden store) untouched; host config rendered to ~/.hermes/profiles/<name>/
#  - verify: a release-added lane `deny` lands even over a PI overlay (tighten-only; security patch not droppable)
# deployed-vault smoke: launch each MCP server via its venv console script and
# confirm it answers a tool list against the sandbox vault (Memoria-test).

# Rollback: checkout the prior tag and re-run (recovery = re-run, not transaction-unwind)
git checkout v<previous> && ./install.sh /path/to/Memoria-test

# Policy-gate (§4.5): confirm the host-process gate imports the SINGLE installed core
# (memoria.runtime.policy from the venv site-packages — no vendored copy), that the host
# interpreter is >= the package min-Python, and that the gate still hard-denies a blocked call.
# (No golden step for code: golden never covered .memoria/; code integrity = sandbox + git.)
```
