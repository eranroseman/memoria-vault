# Install a real package — runtime packaging & deployment design

**Issue:** [#494](https://github.com/eranroseman/memoria-vault/issues/494) — *Research packaging `src/.memoria` as an installable Python package*
**Status:** design note (greenfield target + migration sketch) — input for a deferred ADR, not yet a decision
**Date:** 2026-06-14
**Scope:** how the Python runtime should be structured for (1) the repo's tests/CI and (2) a deployed vault, if we were designing from scratch — and what it would take to move the existing repo toward it.

---

## 1. The problem in one sentence

The source tree and the deployment location are **the same dotted directory**: `src/.memoria` is simultaneously "the code we author" and "the thing rsynced into `<vault>/.memoria/`." Conflating them forces:

- a **dotted, un-importable** top-level name (`.memoria` — a leading dot is a syntax error in `import`, and the name can't be a PyPI/wheel distribution),
- **two parallel import mechanisms** that must agree: 8 `sys.path` entries in `tests/conftest.py` for the repo, and **11** per-entry-point `Path(__file__).resolve().parent…` bootstraps for the deployed vault (a 12th `sys.path` insert, in the policy-gate plugin, is anchored on `{{VAULT_PATH}}`, not `__file__`),
- a **two-phase rsync** deploy that mirrors a source tree: a bulk copy (excluding `.git`, **without** `--delete`), then a `--delete` pass scoped to 7 named infra subtrees (`.env` excluded) to prune renamed files — instead of installing a versioned artifact. (The installer also stages the ADR-55 golden copy, but that covers vault *system files*, not the runtime code — see §1.1.)

Everything below follows from **un-conflating those two concerns**: a normal importable package that gets *installed*, and a vault data directory that holds *state + a venv*, never source.

### 1.1 What is true today (inventory)

| Fact | Detail | Source |
|---|---|---|
| Real packages | **3** `__init__.py`: `src/.memoria/memoria_runtime/` (+ `policy/`) **and** `plugins/memoria-policy-gate/` (the sandbox boundary; hyphenated → un-importable dir name) | repo scan |
| Loose script dirs | `engines/{ingest,lib,linter,sweeps}`, `mcp/` — **no** `__init__.py`; reached via `sys.path` | repo scan |
| Repo import root | 8 dirs inserted in `tests/conftest.py`; pytest run as `python -m pytest tests/ -q` (no `pyproject`/`pytest.ini`) | `tests/conftest.py` |
| Runtime import root | **11** files self-bootstrap `sys.path` from `__file__` (e.g. `_RUNTIME_ROOT = Path(__file__).resolve().parent.parent`); the policy-gate plugin adds a 12th insert via `{{VAULT_PATH}}`, not `__file__` | `mcp/policy_mcp.py`, `mcp/ingest_mcp.py`, … |
| Code count | 30 `.py` under `src/.memoria`; 7 repo-tooling scripts in `scripts/`; 1 in `.github/scripts/` | repo scan |
| Deploy | `scripts/install.sh` rsyncs `src/.memoria/` → `<vault>/.memoria/` (two-phase, see §1); creates `<vault>/.memoria/.venv`; `pip install`s **deps only**, never the code | [scripts/install.sh](../../../../scripts/install.sh) |
| Runtime launch | MCP host runs absolute paths: `command: <vault>/.memoria/.venv/bin/python`, `args: [<vault>/.memoria/mcp/policy_mcp.py, --vault, <vault>]` | rendered `config.yaml` |
| Vault resolution | already explicit: `_shared.resolve_vault()` is pure arg→env (`--vault` → `MEMORIA_VAULT_PATH` → `OBSIDIAN_VAULT_PATH`), **no `__file__` fallback** | `mcp/_shared.py:39` |
| Code integrity | **Not golden.** Code is protected by the **MCP-only sandbox** (agents cannot write files; [[mcp-only-agent-sandbox]]) + **git** as source of truth. ADR-55 golden covers *vault system files only* — `golden_restore.py` manifest = `system/{templates,dashboards,patterns,eval,scripts}/` + `home.md`/`system/vocabulary.md`/`AGENTS.md` + 3 `.obsidian` config files; **no `.memoria/` prefix** (not code, not `schemas/`, not `lane-overrides/`) | `golden_restore.py:30-50`, [ADR-55](../../../adr/55-src-scaffold-populate-golden-copy.md) |
| Deps, three files | `requirements-dev.txt`, `src/.memoria/mcp/requirements.txt`, `…/requirements-cluster.txt` | repo scan |
| Pending rename | `engines → operations` **accepted**; code-tree rename *sequenced* after [ADR-73](../../../adr/73-docs-reference-conventions.md) (not "deferred" — the decision is settled, only execution waits) | [ADR-69](../../../adr/69-operations-layer-naming.md) |

---

## 2. The one decision everything follows from

> **Make the runtime a normal, single-rooted Python package named `memoria`, and install it. Let `<vault>/.memoria/` hold only vault state + a venv — never source.**

```
memoria            ← importable package name (no dot, no hyphen, ONE import root)
<vault>/.memoria   ← data dir: venv, rendered config, lane-overrides, logs, golden  (NOT code)
```

This single change dissolves the dotted-package problem, the conftest path block, and the 11 `__file__` bootstraps at once — because there is exactly **one import root in both worlds**, and it is a properly installed package, so it is location-independent by construction.

The `.memoria` directory **stays in the vault** (Obsidian and plugins expect it there) — but it stops being source. Crucially, moving code out of the vault costs **no integrity property**: code is *not* golden-covered today (ADR-55's golden copy protects vault *system files* — templates, dashboards, `.obsidian` config — never `.memoria/` code). Code integrity is the MCP-only sandbox (agents can't write files) + git, and packaging changes neither. The only real delta is that code moves from plainly-inspectable files in the vault to `site-packages/` — a transparency/debuggability change (§6.2), not an integrity one. §4.4 makes this precise.

---

## 3. World 1 — In the repo (tests / CI)

### 3.1 Layout (`src/`-layout package)

```
pyproject.toml                 ← single source of truth: build, deps, scripts, pytest, ruff
src/
  memoria/
    __init__.py                ← __version__
    operations/                ← was "engines"; ADR-69 rename becomes a subpackage move
      processing/ingest/…
      integrity/{linter,golden}/…
      cleanup/{reconcile,…}/…
      telemetry/{board,metrics,eval}/…
    mcp/
      policy.py                ← def main(): … (was policy_mcp.py)
      ingest.py                ← def main(): …
      tasks.py  patterns.py  cluster.py
      _shared.py
    runtime/
      policy/                  ← the current memoria_runtime.policy (shared decision core)
    lib/                       ← inbox, schema (shared helpers)
tests/
  conftest.py                  ← FIXTURES ONLY (no sys.path surgery)
  test_pipeline.py …
scripts/                       ← repo-dev tooling (doctors); see §3.4
```

Imports become explicit and stable everywhere:

```python
from memoria.operations.processing.ingest import runner
from memoria.runtime.policy import MUTATING_ACTIONS
from memoria.lib import inbox
```

No bare `import runner`, no `import classify` sibling magic, no `sys.path.insert`.

### 3.2 `pyproject.toml` — one source of truth

```toml
[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[tool.hatch.version]
path = "src/memoria/__init__.py"  # reads __version__ — companion to `dynamic = ["version"]`

[project]
name = "memoria"
dynamic = ["version"]            # sourced from src/memoria/__init__.py:__version__
requires-python = ">=3.11"
dependencies = [                  # RUNTIME deps (was mcp/requirements.txt)
  "mcp>=1.27.2",
  "PyYAML>=6.0.3",
  "pymupdf4llm>=1.27.2.3",
]

[project.optional-dependencies]
dev = [                           # was requirements-dev.txt
  "pytest==9.1.0", "ruff==0.15.17", "yamllint==1.38.0", "pre-commit==4.6.0",
]
cluster = [                       # was requirements-cluster.txt (heavy: torch)
  "networkx>=3.6.1", "bertopic>=0.17.4",
]

[project.scripts]                 # console entry points — see §4.2 for why these now FIT
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
# no pythonpath needed: the package is installed (editable); tests import `memoria.*`

[tool.ruff]
# moved verbatim from ruff.toml (linter-only policy preserved)
```

This **names** the three dependency worlds the issue worried would blur — runtime / dev / cluster — in one file, and replaces three `requirements*.txt`.

The `[project.scripts]` targets above are the **post-rename** module names; today's files are `policy_mcp.py`, `ingest_mcp.py`, `tasks_mcp.py`, `patterns_mcp.py`, `cluster_mcp.py`, and `metrics_aggregate.py` / `board_export.py`. Each already exposes a zero-arg `main()` (verified), so the entry points wire up with no signature changes — one caveat: `reconcile.main()` returns an `int` exit code, which `[project.scripts]` handles correctly (the return value becomes the process exit status). **Every notional script's `main()` must be audited as part of the move**, and **two are "pick one canonical entry" decisions, not just `main()` confirmations**, because they're multiple files behind a single planned script:
- `memoria-lint` → `…linter.cli:main` doesn't exist yet; the linter's `main()` lives in `detectors.py`, alongside `golden_restore.py`/`session_summary.py`/`precommit_check.py` mains — pick one canonical linter entry.
- `memoria-eval` → **two** files (`eval_dispatch.py`, `eval_score.py`) for one planned eval script — same "pick one canonical entry" call as the linter.

The remainder (`board-export`, `metrics`, `retraction`) are single oddly-named files (`board_export.py`, `metrics_aggregate.py`, `retraction.py`) whose `main()` presence, signature, and return type just need confirming before they become declared console scripts.

### 3.3 Dev & CI workflow

```bash
pip install -e ".[dev]"          # editable install: tests import EXACTLY what ships
python -m pytest                 # config from pyproject; conftest = fixtures only
ruff check .
```

- **Tests run against one import root, not divergent `sys.path` ordering.** Editable install means `import memoria.x` resolves through the installed package, killing the conftest path-ordering fragility. *Caveat (don't overclaim):* an editable install imports the **working tree**, not the built wheel — so it does **not** catch packaging errors (missing `__init__.py`, undeclared package data, MANIFEST gaps). The "works-in-tests-breaks-in-vault" gap for *packaging* is exactly what editable installs leave open.
- **`conftest.py` shrinks to fixtures.** The 8-entry `sys.path` block is deleted.
- **CI must build the wheel and smoke-import it — required, not optional.** Packaging is a *new* failure surface (it doesn't exist today — there's no wheel to mis-build), and editable installs don't exercise it. A CI step that `pip install`s the *built wheel* into a clean venv and imports every entry point (`memoria-policy-mcp --help`, etc.) is the only thing that catches packaging gaps (missing `__init__.py`, undeclared package data) before they reach a vault. Run alongside `pip install -e ".[dev]"` + pytest/ruff.

### 3.4 Repo tooling (`scripts/`, `.github/scripts/`)

These are **repo-dev** tools (doctors, `pr_policy.py`) that never deploy to a vault. Two clean options:

- **(a)** keep them as standalone scripts run from the repo (they don't need packaging), but let them `import memoria.*` since the package is installed in dev; or
- **(b)** fold them under `memoria.tooling` with their own `[project.scripts]` (`memoria-docs-doctor`, …) if we want them invokable post-install.

Recommend **(a)** now — minimal churn; revisit (b) only if a tool needs to ship.

---

## 4. World 2 — In a deployed vault (runtime)

### 4.1 Installer builds + installs a wheel (not rsync of source)

```
<vault>/.memoria/
  .venv/                 ← `pip install memoria-<ver>.whl` lands code in site-packages
  config/                ← rendered profiles' config.yaml (host-specific paths)
  lane-overrides/        ← vault-specific policy data (stays; not golden-covered — §1.1)
  schemas/               ← only if per-vault extensions are supported (else ships in wheel — §6.7)
  logs/  golden/         ← vault state
```

Installer flow (replacing the rsync mirror):

1. **Obtain the wheel.** *Prefer a prebuilt `memoria-<ver>.whl` shipped as a release asset* — it adds no build-time deps to the installer and fits ADR-55's fresh-install model. `python -m build` on the host is the **dev-only** fallback (installing from a local checkout).
2. Create `<vault>/.memoria/.venv` (unchanged from today — per-vault isolation stays).
3. `"$venv/bin/pip" install memoria-<ver>.whl` (add `.[cluster]` when clustering is enabled).
4. Render `config/*.yaml` with the venv python path and vault path (the existing `{{PYTHON}}`/`{{VAULT_PATH}}` substitution, now pointing at console scripts). **The cron wrappers carry the same `{{PYTHON}}`/`{{VAULT_PATH}}` substitution and must be repointed at console scripts too** (see §7 blast radius).
5. Copy **vault-side data** (`lane-overrides/` seeds, profile templates, and `schemas/` *only if* per-vault extensions are supported — otherwise schemas ship in the wheel; see §6.7).

Source code now lives in `<vault>/.memoria/.venv/lib/python3.x/site-packages/memoria/`, not loose under `.memoria/`.

### 4.2 Runtime launch — console scripts (now a natural fit)

```yaml
# rendered config.yaml
mcp_servers:
  policy:
    command: "<vault>/.memoria/.venv/bin/memoria-policy-mcp"
    args:    ["--vault", "<vault>"]
    timeout: 30
# equivalently: <vault>/.memoria/.venv/bin/python -m memoria.mcp.policy --vault <vault>
```

> **Why console scripts fit now but not today.** They require an *installed distribution* exposing entry points on the venv's `bin/`. Today there is no installed dist — the host invokes a `.py` file by absolute path against a source tree. Install a real wheel and the venv gets `bin/memoria-policy-mcp` for free. **Option 3 in #494 ("package all + console scripts") wasn't wrong — it was un-runnable on a rsync'd source tree.** The blocker was the deployment mechanism, not packaging.

### 4.3 Delete the `__file__` import-root bootstraps (vault resolution already a parameter)

Two unrelated things must not be conflated here:

- **Import-root discovery** — the `_RUNTIME_ROOT = Path(__file__).resolve().parent.parent; sys.path.insert(...)` bootstraps. These exist *only* to find sibling modules to import; they have nothing to do with the vault. Packaging **deletes all 11** of them — imports become `memoria.*`, resolved by the installed package.
- **Vault resolution** — *already* explicit today. `_shared.resolve_vault()` is pure arg→env (`--vault` → `MEMORIA_VAULT_PATH` → `OBSIDIAN_VAULT_PATH`) with **no `__file__` fallback**. It stays exactly as-is; the vault was never derived from code location.

So packaging changes the *import* mechanism, not vault resolution. Hardcoded *data* relpaths (`system/logs/audit.jsonl`, `.memoria/lane-overrides`, `.memoria/golden`) also stay — they're relative to `--vault`, which is correct. **Exception: `schemas/`.** Unlike those, `schema.py:25` resolves schemas from **code location**, not the vault: `SCHEMAS_DIR = Path(__file__).resolve().parent.parent.parent / "schemas"` (with an optional `schemas_dir` override). That makes schemas behave like *package data*, and the ship-vs-stay choice for them has a code consequence — see §6.7.

### 4.4 Upgrades and integrity (golden never covered code — the real delta is small)

**Integrity is mostly a non-issue — correcting an earlier draft.** A prior version of this note claimed moving code to site-packages takes it "out of golden's coverage" and framed it as an integrity model swap. **That was wrong, and it's worth stating plainly so it isn't re-introduced.** Verified against `golden_restore.py:30-50`: the ADR-55 manifest is `system/{templates,dashboards,patterns,eval,scripts}/`, the files `home.md`/`system/vocabulary.md`/`AGENTS.md`, and three `.obsidian` config files. **No `.memoria/` prefix appears in the covered set** — the runtime code (`mcp/`, `engines/`, `memoria_runtime/`) and even `schemas/`/`lane-overrides/` were **never** in golden. (The lone `.memoria/` string in `golden_restore.py` is `GOLDEN_RELDIR = ".memoria/golden"` — the *store* path where the manifest is written, not a covered prefix.) ADR-55 exists for the #179 template-protection problem (system-file drift / accidental human overwrite), not code.

So the actual code-integrity story today, unchanged by packaging:

- **MCP-only sandbox** — agents cannot write files at all ([[mcp-only-agent-sandbox]]), so an agent can't tamper the runtime in the first place.
- **git** is the source of truth; recovery for code is "re-run the installer / reinstall," exactly as today.

Packaging touches **neither**. There is no golden coverage to "preserve over site-packages," no `tests/test_golden_restore.py` rework for code, and **no ADR-55 reconciliation blocker** (this dissolves §8's former blocker #1; `assumes:` drops `55`). The one genuine change is transparency: code goes from plainly-inspectable files under `.memoria/` to `site-packages/memoria/` — handled as a debuggability trade in §6.2, not an integrity one. (Aside: `site-packages` is *not* "read-only" either — don't claim filesystem immutability as a property; it was never the mechanism.)

**Upgrade.** `pip install --upgrade memoria-<new>.whl` replaces the rsync `--delete` "renamed engines linger" hazard with versioned installs — but **"atomic" is too strong**: pip upgrades are *not* transactional, so a failure mid-install can leave the venv with a partially-installed package. Today's recovery from a bad deploy is "re-run the installer from the git checkout"; the wheel model must keep an equivalent net. The ADR should specify a **rollback path** — e.g. retain the previous wheel and `pip install --force-reinstall memoria==<previous>` on failure, or snapshot the venv pre-upgrade. This is a real (if mundane) deployment requirement, independent of golden.

### 4.5 The policy-gate plugin — how the sandbox boundary resolves the policy core post-wheel

This is an **open design question the target must answer before it ships**, because the gate is the security boundary (it hard-denies tool calls — the MCP-only sandbox; [[mcp-only-agent-sandbox]]). Today `plugins/memoria-policy-gate/__init__.py` does `VAULT = Path("{{VAULT_PATH}}")`, inserts `{{VAULT_PATH}}/.memoria/mcp` on `sys.path`, then lazily `import policy_hook`. It runs in the **Hermes process, whose interpreter this installer does not pin** — only the MCP servers it spawns get `{{PYTHON}}` (the venv); the operator launches Hermes and the repo doesn't own that interpreter (corroborated at `install.sh:498`: *"the plugin runs in the Hermes process, so no PYTHON"*). The `sys.path` insert is precisely how the gate sidesteps the interpreter question today — and it is exactly what breaks when code moves to site-packages.

Note the **real import chain is not a thin core**: `policy_hook → policy_mcp → memoria_runtime.policy`. The gate reaches *through* the MCP layer (`policy_mcp`), not into a clean standalone policy core. That shapes the options.

**Version-skew is the deciding axis, and it's a security property — not a deployment chore.** Today the gate and the MCP servers are rsynced from one tree, so they *always* run identical policy code. Once the gate imports its *own* install of `memoria` (options i/ii), the gate's copy and the servers' copy are two independent installs that can drift — and if the gate runs a stale `MUTATING_ACTIONS`/policy, a call the new runtime treats as mutating can be **waved through by an out-of-date hard-deny boundary**. So the table scores skew safety explicitly:

| Option | How the gate reaches the policy core | Version-skew safety | Pro | Con |
|---|---|---|---|---|
| **(i)** Host installs the `memoria` wheel too | plain `import memoria.runtime.policy` (or the `policy_hook` entry) | **✗ skew-prone** — gate's install is independent of the servers' (installer doesn't pin the Hermes interpreter, `install.sh:498`); a stale gate can mis-classify a mutating call | simplest code; no core-extraction refactor | **security divergence**, not just provisioning coupling: two installs of the boundary code that can drift |
| **(ii)** Ship a separate `memoria-policy-gate` distribution the host installs | gate imports a published core | **✗ skew-prone** — *worse*: a second artifact with its own version, must be lock-stepped to the runtime | gate versioned independently | **not "thin" as-is** — the chain runs through `policy_mcp`, so (ii) requires *first extracting a genuine `policy` core*; otherwise the "separate" gate drags the MCP module with it |
| **(iii)** Gate calls the policy MCP over the wire (no shared-process import) | IPC to the running `policy` server | **✓ skew-free** — the running server is the single source of truth; gate holds no policy copy to drift | closes the skew hole **and** gives strongest isolation; no host install at all | adds a runtime hop on the **hot path** (every tool call) |

**Lean (revised):** for a hard-deny security boundary, **(iii)** is the strongest because it *structurally* eliminates version skew — there is no second copy of the policy to fall behind. Its cost is per-tool-call latency, which must be measured against the security value of a single source of truth. **(i)** is the lowest-effort path but accepts a real skew hazard on the boundary; if chosen, it **must** be backed by a gate-vs-runtime version assertion at startup (gate refuses to run if its `memoria.__version__` ≠ the servers'). Note this assertion isn't free: to learn the servers' version the gate must read a shared on-disk version stamp or query a server — i.e. a thin slice of exactly the IPC that option (iii) generalizes, so "(i) + assertion" is less of a clean win over (iii) than it first looks. **(ii)** only *after* extracting a real `policy` core from `policy_mcp`, and even then inherits the two-install skew problem. Whichever is chosen, the hyphenated dir name (`memoria-policy-gate`) must become an importable module name under packaging.

---

## 5. How this scores vs. today

| Concern | Today | This design |
|---|---|---|
| Import roots | 8 (conftest) + 11 `__file__` inserts | **1** (installed package) |
| Top-level name | `.memoria` (un-importable) | `memoria` |
| Test import root | divergent `sys.path` ordering | single root (editable install) — but a **required CI wheel-smoke** catches packaging gaps editable installs miss (§3.3) |
| `engines → operations` (ADR-69) | cross-cuts conftest, install.sh, tests, docs | **subpackage move** inside `memoria/` |
| Dependency split | 3 `requirements*.txt`, blurred | one `pyproject`, **named groups** (runtime/dev/cluster) |
| Deploy | two-phase rsync (bulk copy + scoped `--delete`) | `pip install` one wheel |
| Upgrade | mirror + prune renamed files (recovery = re-run installer from checkout) | `pip install --upgrade` (versioned; **not** atomic — needs an explicit rollback path, §4.4) |
| Console scripts | don't fit (path invocation) | **fit** (venv `bin/`) |
| Vault resolution | already explicit (`resolve_vault`, arg→env) | unchanged — stays a parameter |
| Code integrity | sandbox (agents can't write) + git — **not golden** (golden = system files only) | **unchanged** — packaging touches neither (§4.4) |
| Policy-gate import | `{{VAULT_PATH}}/.memoria/mcp` on `sys.path` | **open** — resolve via §4.5 (i/ii/iii) before shipping |
| Editor / type-checker / ruff | partial (sys.path-dependent) | full (real package) |

---

## 6. Honest trade-offs & mitigations

1. **`.memoria` must remain in the vault.** Fine — it holds the venv + data now, not source. No regression; just stops doubling as the source tree.
2. **Deployed runtime is no longer plainly inspectable / hand-editable in place** (it's in `site-packages/`, not loose under `.memoria/`). This is a **transparency/debuggability** cost — *not* an integrity one (code was never golden-covered; §4.4). For a single-researcher debugging workflow it's the one real ergonomic regression. *Mitigation:* `pip install -e` against a local checkout when live-tweaking is needed.
3. **Wheel-build step added to the installer.** More moving parts than `cp -R`/rsync, but standard tooling and less fragile than delete-pruned mirroring.
4. **Wheel provenance is a new trust surface (not present today).** Today you deploy exactly the code in your git checkout — there is no fetch-and-trust step. A downloaded release-asset wheel introduces supply-chain trust the rsync model never had. Since ADR-55's whole model is content-addressable hashing, map it onto the wheel: **pin the wheel's SHA256 in the installer and verify before `pip install`** (and sign the release asset if/when a signing story exists). Don't let "prefer prebuilt wheel" (§4.1) quietly add an unverified download.
5. **Failed-upgrade / rollback.** `pip install --upgrade` is not transactional, so a mid-install failure can leave a partially-installed venv. Today's recovery is "re-run the installer from the git checkout"; the wheel model must keep an equivalent. *Mitigation:* retain the previous wheel and `pip install --force-reinstall memoria==<previous>` on failure, or snapshot the venv pre-upgrade (§4.4). (Note: this is plain deployment hygiene — *not* tied to golden, which never covered code.)
6. **Build backend + version source.** *Decision:* hatchling + **dynamic version from `src/memoria/__init__.py:__version__`** (§3.2). Boilerplate, but commit to it rather than leaving it open.
7. **Data-file ship/stay boundary must be enumerated (the ADR needs the list).** Two regimes — note **none of these are golden-covered** (golden = `system/...` + `.obsidian/...`, never `.memoria/`; §1.1), so the split is purely "authored-static vs per-vault," not an integrity question:
   - **Ship in the wheel (runtime-static, authored) — the low-risk default, and it's *continuity* not a new behavior:** the type vocabulary under `schemas/` — **18** `types/*.yaml` + `calibration.yaml` + `folders.yaml` — is today `--delete`-mirrored *authored* infra, **already resolved relative to `__file__`** (`schema.py:25`) and read from a code-adjacent dir. Shipping it as package data preserves exactly that: the `__file__` resolution survives (a `.parent`-depth tweak, or a clean switch to `importlib.resources`). No loader rewrite.
   - **Stay vault-side (per-vault / per-machine):** `lane-overrides/`, rendered `config/`, `logs/`, `golden/` (the golden store for *system files*), `.env`, profile templates the operator edits.
   - **Open question that decides schemas' gray zone — with a named code cost:** are per-vault *schema extensions* supported? If **no**, schemas ship (above) and nothing changes. If **yes**, schemas stay under `<vault>/.memoria/schemas/` — and **`schema.py:25` must be rewritten from `__file__`-relative to `--vault`-relative** (thread the vault through `_schemas_dir`/`load_*`, or ship-defaults-then-overlay-vault). With code in site-packages, the current `__file__` default points *into the wheel*, so it can't find a vault-side schemas dir at all — the loader change is the concrete price of the "stay" branch, and the ADR must pay it explicitly. §4.1's schemas line reflects this.

---

## 7. Relationship to #494's incremental recommendation

This note describes the **target**, not an immediate migration. Reaching it changes the *deployment mechanism* (wheel vs. rsync) and the *on-disk vault shape* (code leaves `.memoria/`). Full blast radius:

- `install.sh` (deploy path, golden staging, `{{PYTHON}}` substitution),
- every rendered `config.yaml` **and the cron wrappers** (both carry `{{PYTHON}}`/`{{VAULT_PATH}}`, both repoint at console scripts),
- the policy-gate plugin import path (§4.5),
- the **`src/.memoria` → `src/memoria` un-hiding** itself — a discrete cross-cutting change (the dotted path is hardcoded throughout `install.sh`), *not* a free side effect of the operations fold-in.

*Not* in the blast radius (corrected from an earlier draft): ADR-55 golden / `tests/test_golden_restore.py` — golden never covered `.memoria/` code, so moving code doesn't touch it (§4.4).

So the staged path stays as in the #494 research:

1. **Now (issue work, no ADR):** add a repo-root `pyproject.toml` scoped **strictly to tooling** — `[tool.pytest.ini_options]` (`testpaths` + `pythonpath` listing the same dirs) and `[tool.ruff]` only. **Keep `requirements-dev.txt` as-is** — do *not* add a `[project]`/`[project.optional-dependencies]` table, since that declares the `memoria` distribution, which belongs to the target. This lets us delete the `conftest.py` `sys.path` block (the path declaration **moves** into `pyproject`; it does *not* reduce the import-root count — that drops to 1 only at the target). **Does not** touch runtime `__file__` bootstraps (still load-bearing while we rsync source). Independent of ADR-69 — can land anytime.
2. **After `engines → operations` executes** ([ADR-69](../../../adr/69-operations-layer-naming.md) — **accepted**; only the code-tree rename is *sequenced* after the docs→source link convention / [ADR-73](../../../adr/73-docs-reference-conventions.md)): the tree is already being moved — fold it into `src/memoria/operations/…` in the same pass rather than renaming loose dirs.
3. **Then (this design):** flip deployment to wheel-install + console scripts; delete the runtime `__file__` bootstraps; vault becomes data-only `.memoria/` + venv; resolve §4.5 (policy-gate version-skew) first.

Sequencing rule: **never repackage runtime before the operations rename lands** — that's the "churn before naming settles" risk #494 flags. This note is the destination those steps aim at.

---

## 8. Does this need an ADR?

**Yes — a deferred ADR**, because it changes runtime/package *architecture* and deployment shape (not mere test/tooling cleanup). **One** substantive piece must be resolved **in the note before it converts to an ADR**:

- the **policy-gate resolution** (§4.5) — pick among options (i)/(ii)/(iii) for how the sandbox boundary reaches the policy core post-wheel without version-skew.

(An earlier draft listed a second blocker — an "ADR-55 integrity reconciliation." That is **dissolved**: golden never covered `.memoria/` code, so packaging doesn't touch ADR-55 at all; §4.4. One fewer hard problem.)

The ADR should then:

- record the target (this note's §2–§5),
- carry **`assumes: [44, 46, 69, 73]`** — ADR-44 (the conftest L1-test layout whose `sys.path` block we delete), ADR-46 (seven-layer architecture incl. the MCP-only sandbox that *is* the code-integrity story), ADR-69 (operations naming), ADR-73 (docs-reference conventions). **Not** ADR-55 — this design leaves golden's scope untouched,
- set **`nav_exclude: true`** in the frontmatter (required for deferred/proposed ADRs per `_template.md`); use **[ADR-63](../../../adr/63-multi-machine-deployment.md)** (deferred, deployment-adjacent) as the format template — and note the **substantive synergy**, not just the format: a wheel (build once, install on N machines, version-pinned) is materially more multi-machine-friendly than rsync-from-a-checkout, so this design strengthens ADR-63's case,
- sit at `status: deferred` with a *When this matters* section and per-release re-judgement (per the [ADR-only decision model](../../../adr/)),
- explicitly mark **Option 3 of #494 ("package all + console scripts") as the eventual direction**, with the deployment-mechanism change as its precondition — so it isn't re-litigated as "rejected" when #494's *incremental* answer was only "not now."

Pre-drafted ***When this matters*** trigger (so the deferred-ADR review has a concrete test) — pick this up when **any** of these holds:

- **distribution:** Memoria ships to operators who *can't* run from a git checkout (the rsync-from-source model stops being viable);
- **sequencing:** the `engines → operations` rename (ADR-69) lands — the tree is being moved anyway, so packaging rides along instead of churning twice;
- **support burden:** the `sys.path`/`__file__` bootstrapping (11 sites) or three-way `requirements*.txt` split becomes a recurring source of import/CI breakage;
- **prerequisites cleared:** the §4.5 policy-gate resolution is answered (until then, don't start).

The step-1 tooling `pyproject.toml` (tooling-only, `requirements-dev.txt` retained) remains **issue work, no ADR**.

---

## 9. Validation commands (for whichever step ships)

```bash
# Step 1 (tooling-only pyproject; requirements-dev.txt retained):
# tests still green without the conftest sys.path block
python -m pytest -q
ruff check .
scripts/test.sh all

# Target design (install from the shipped wheel; python -m build only for dev)
pip install memoria-<ver>.whl          # prebuilt release asset (preferred)
python -c "import memoria; print(memoria.__version__)"
memoria-policy-mcp --vault /path/to/Memoria-test --help   # console script resolves
# deployed-vault smoke: launch each MCP server via its venv console script and
# confirm it answers a tool list against the sandbox vault (Memoria-test).

# Rollback (pip is not atomic): on a failed upgrade, restore the pinned prior wheel
pip install --force-reinstall memoria==<previous>     # ; `memoria --version` attests
# (No golden step for code: golden never covered .memoria/ — §4.4. Code integrity is
#  the MCP-only sandbox + git, unchanged by packaging.)
# Policy-gate (§4.5): confirm the chosen option (i/ii/iii) lets the Hermes-host process
# resolve the policy core WITHOUT version-skew, and that the gate still hard-denies a blocked call.
```
