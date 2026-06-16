# Install a real package — runtime packaging & deployment design

**Issue:** [#494](https://github.com/eranroseman/memoria-vault/issues/494) — *Research packaging `src/.memoria` as an installable Python package*
**Status:** design note (greenfield target + migration sketch) — long-form analysis behind [ADR-76](../../../adr/76-versioned-vault-release-reconciling-installer.md), now recast around a **versioned vault release**, not a shipped wheel
**Date:** 2026-06-15 (recast; original 2026-06-14)
**Scope:** how Memoria should be distributed and deployed for (1) the repo's tests/CI and (2) a deployed vault, if we were designing from scratch — and what it would take to move the existing repo toward it.

> **What changed in this recast.** The first draft framed the answer as *"package the runtime as an installable wheel; the vault holds data, not source."* A red-team of that draft found the framing optimizes only the Python third of the deployable and breaks on the other two-thirds (authored profiles, the host-loaded gate shim, cron), so "vault holds no source" is unreachable. It also rested on a stale tree state. The spine is now **a versioned vault release + a source-agnostic reconciling installer**; the Python-package work survives as *how the code layer lands* (editable by default), not as the deployment artifact. Corrections from the red-team are folded in inline and flagged ⟲.

---

## 1. The problem in one sentence

**The thing Memoria deploys is a configured vault, not a Python package** — yet the source tree and the deployment location are **the same dotted directory**: `src/.memoria` is simultaneously "the code we author" and "the thing rsynced into `<vault>/.memoria/`." That conflation forces:

- a **dotted, un-importable** top-level name (`.memoria` — a leading dot is a syntax error in `import`, and the name can't be a wheel distribution),
- **two parallel import mechanisms** that must agree: **10** `sys.path` entries in `tests/conftest.py` for the repo ⟲ (8 under `src/.memoria` **plus** `scripts` and `.github/scripts`), and **11** per-entry-point `Path(__file__).resolve().parent…` bootstraps for the deployed vault (a 12th `sys.path` insert, in the policy-gate plugin, is anchored on `{{VAULT_PATH}}`, not `__file__`),
- a **two-phase rsync** deploy that mirrors a source tree: a bulk copy (excluding `.git` and the golden-covered system files, **without** `--delete`), then a `--delete` pass scoped to **7** named infra subtrees (`.env` excluded) to prune renamed files — instead of installing a versioned artifact.

But un-conflating source from deployment is only half the problem. The deeper issue the first draft missed: **the deployable is three different things wearing one rsync** (§1.2). A wheel addresses one of them. The real fix is a versioned *release* and an installer that reconciles all three.

### 1.1 What is true today (inventory) ⟲ corrected against HEAD

The `engines → operations` rename is **already landed** ([#536](https://github.com/eranroseman/memoria-vault/issues/494), commit `aa7b894`). On disk, all 30 `.py` files live under `operations/`; `engines/` is an untracked husk containing only `__pycache__`. The first draft's inventory described the pre-#536 tree — that framing is retired.

| Fact | Detail | Source |
|---|---|---|
| Real packages | **3** `__init__.py`: `src/.memoria/memoria_runtime/` (+ `policy/`) **and** `plugins/memoria-policy-gate/` (the sandbox boundary; hyphenated → un-importable dir name) | repo scan |
| Loose script dirs | `operations/{processing,integrity,cleanup,telemetry,lib}`, `mcp/` — **no** `__init__.py`; reached via `sys.path` ⟲ (was `engines/…`) | repo scan |
| Repo import root | **10** dirs inserted in `tests/conftest.py` ⟲ (8 `src/.memoria/…` + `scripts` + `.github/scripts`); pytest run as `python -m pytest tests/ -q` (no `pyproject`/`pytest.ini`) | `tests/conftest.py:7-16` |
| Runtime import root | **11** files self-bootstrap `sys.path` from `__file__`; the policy-gate plugin adds a 12th insert via `{{VAULT_PATH}}`, not `__file__` | `mcp/policy_mcp.py`, `mcp/ingest_mcp.py`, … |
| Code count | 30 `.py` under `src/.memoria`; 7 repo-tooling scripts in `scripts/`; 1 in `.github/scripts/` | repo scan |
| Deploy | `scripts/install.sh` rsyncs `src/.memoria/` → `<vault>/.memoria/` (two-phase); creates `<vault>/.memoria/.venv`; `pip install`s **deps only**, never the code; ~36 hardcoded `.memoria` references | [scripts/install.sh](../../../../scripts/install.sh) |
| Runtime launch | MCP host runs absolute paths: `command: <vault>/.memoria/.venv/bin/python`, `args: [<vault>/.memoria/mcp/policy_mcp.py, --vault, <vault>]` | rendered `config.yaml` |
| Vault resolution | already explicit: `_shared.resolve_vault()` is pure arg→env (`--vault` → `MEMORIA_VAULT_PATH` → `OBSIDIAN_VAULT_PATH`), **no `__file__` fallback** | `mcp/_shared.py:39` |
| Code integrity | **Not golden.** Protected by the **MCP-only sandbox** (agents cannot write files; [[mcp-only-agent-sandbox]]) + **git**. ADR-55 golden covers *vault system files only* — manifest = `system/{templates,dashboards,patterns,eval,scripts}/` + `home.md`/`system/vocabulary.md`/`AGENTS.md` + 3 `.obsidian` config files; **no `.memoria/` prefix** | `golden_restore.py:30-50`, [ADR-55](../../../adr/55-src-scaffold-populate-golden-copy.md) |
| Deps, three files | `requirements-dev.txt`, `src/.memoria/mcp/requirements.txt`, `…/requirements-cluster.txt` | repo scan |
| `engines → operations` | **landed** (#536). The first draft treated this as a pending precondition — it is done. ⟲ | [ADR-69](../../../adr/69-operations-layer-naming.md), `git log` |

### 1.2 The deployable is three layers, not one ⟲ the key red-team finding

The seven subtrees `install.sh` lays down are three different things with different lifecycles:

- **Code** — `operations/`, `mcp/`, `memoria_runtime/`, `lib/`. Importable Python; versioned; never hand-edited.
- **Authored content** — `profiles/memoria-*/` (`SOUL.md`, `SKILL.md`, `config.yaml`, `distribution.yaml`), `schemas/`, `system/` templates and dashboards, the `plugins/memoria-policy-gate/` shim (`__init__.py` + `plugin.yaml`, **loaded by the MCP host in its own interpreter**), `*-cron.sh` wrappers. Versioned, **but the PI may customize**, and **most of it is not Python** — a wheel cannot carry it.
- **Per-vault state** — notes, `lane-overrides/`, `logs/`, rendered `config/`, `.env`, the golden store. Never touched by an upgrade.

This is why the first draft's headline "vault holds data, not source" is false: the gate shim, the agent profiles, the skills, the cron wrappers are *authored source* that must stay vault-side. The honest invariant is "**runtime code** leaves the vault into a venv; the authored layer stays as managed content; state is never touched."

---

## 2. The one decision everything follows from ⟲ recast

> **Distribute Memoria as a single versioned vault release, and deploy it with a source-agnostic reconciling installer `install(release_root, vault_path)` that handles each layer by its lifecycle. The runtime becomes a real `memoria` package installed *into the venv* (editable by default) — the package is how the code layer lands, not the shipped artifact.**

Two decisions are load-bearing; everything else follows.

### 2.1 Load-bearing decision 1 — one versioned release + a reconciling installer, layered by lifecycle

`install(release_root, vault_path)` is idempotent and does **not** care whether `release_root` is a checked-out Git tag or an unpacked tarball. It reconciles the three layers from §1.2:

| Layer | Examples | Lifecycle | Installer handling |
|---|---|---|---|
| **Code** | runtime (`operations`, `mcp`, `runtime`, `lib`), the extracted policy core | versioned; never hand-edited; recovery = reinstall | installed into `<vault>/.memoria/.venv` as the `memoria` package |
| **Authored content** | `profiles/` (`SOUL.md`/`SKILL.md`/`config.yaml`), `schemas/`, `system/` templates/dashboards, the gate shim, cron wrappers | versioned **but** PI may customize | laid down, then **three-way reconciled** (old-release vs new-release vs live) so customizations surface, not clobber |
| **Per-vault state** | notes, `lane-overrides/`, `logs/`, rendered config, `.env`, golden store | never touched on upgrade | left untouched; defined as *everything not in the release manifest* |

The release carries **one version** (`memoria.__version__`) and a **content-addressable manifest** (SHA per file) over the code and authored layers. That single manifest does triple duty:

1. **golden-style drift detection** for authored content (generalizing [ADR-55](../../../adr/55-src-scaffold-populate-golden-copy.md) from `system/` to the whole authored layer),
2. the **gate-vs-runtime version assertion** (§4.5),
3. **tamper *verification*** of code.

Integrity *protection* is unchanged — the MCP-only sandbox + git ([[mcp-only-agent-sandbox]]). The manifest adds verification, never a new protection mechanism, and `site-packages` is **not** claimed as read-only.

### 2.2 Load-bearing decision 2 — extract a genuine, tiny, standalone policy core

The policy-gate is the security boundary (it hard-denies tool calls). Today its real import chain is **`policy_hook → policy_mcp → memoria_runtime.policy`** — it reaches its decision *through* the MCP layer, an accident of organic growth. Extract a small, dependency-free **policy core** (the `MUTATING_ACTIONS` set + path matching, today in `memoria_runtime/policy/paths.py`) that **both** the gate shim and the MCP servers import. The gate vendors only that core and asserts its version against the release manifest at startup.

This makes the boundary small, auditable, and **interpreter-portable** — it carries no transitive runtime dependency, so it runs in the host's interpreter without the venv. It dissolves version skew structurally (no fat chain to fall out of sync), and one-release-from-one-root co-versions the gate and servers by construction. §4.5 makes this precise.

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
dependencies = ["mcp>=1.27.2", "PyYAML>=6.0.3", "pymupdf4llm>=1.27.2.3"]

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

This **names** the three dependency worlds (runtime / dev / cluster) in one file, replacing three `requirements*.txt`.

**Entry-point audit (verified).** Every named `main()` exists and is zero-arg; `reconcile.main()` returns an `int` exit code, which `[project.scripts]` maps to the process exit status correctly. Two are "pick one canonical entry" decisions, not just confirmations:
- `memoria-lint` → `…linter.cli:main` **doesn't exist yet**; the linter's `main()` lives in `detectors.py`, alongside `golden_restore.py`/`session_summary.py`/`precommit_check.py` mains — pick one canonical entry.
- `memoria-eval` → **two** files (`eval_dispatch.py`, `eval_score.py`) — same call.

The rest (`board_export.py`, `metrics_aggregate.py`, `retraction.py`) have confirmed zero-arg mains.

### 3.3 Dev & CI workflow

```bash
pip install -e ".[dev]"          # editable: tests import EXACTLY what ships, code stays inspectable
python -m pytest                 # config from pyproject; conftest = fixtures only
ruff check .
```

- **Tests run against one import root**, killing the conftest path-ordering fragility. *Caveat:* an editable install imports the **working tree**, not a built wheel — so it does **not** catch packaging errors (missing `__init__.py`, undeclared package data).
- **`conftest.py` shrinks to fixtures**; the 10-entry `sys.path` block is deleted.
- **CI builds the wheel and smoke-imports it — required, not optional.** Even though no `.whl` is *shipped* (§4.1), building one in CI and importing every entry point in a clean venv is the only thing that exercises `package_data`/`__init__.py` gaps before they reach a vault. This is a packaging-correctness check, not a deployment artifact.

### 3.4 Repo tooling (`scripts/`, `.github/scripts/`)

These are **repo-dev** tools (doctors, `pr_policy.py`) that never deploy. Recommend keeping them as standalone scripts run from the repo, importing `memoria.*` since the package is installed in dev. Fold them under `memoria.tooling` with their own `[project.scripts]` only if a tool ever needs to ship.

---

## 4. World 2 — In a deployed vault (runtime)

### 4.1 The reconciling installer (replacing the rsync mirror)

```
<vault>/.memoria/
  .venv/                 ← editable (or copy) install of the `memoria` package
  profiles/              ← authored content: SOUL/SKILL/config (host + Obsidian read these)
  plugins/               ← the policy-gate shim (host loads it in ITS interpreter)
  schemas/  system/      ← authored content (manifest-covered)
  config/                ← rendered profiles' config.yaml (host-specific paths) — state
  lane-overrides/        ← per-vault policy data — state
  logs/  golden/         ← per-vault state
```

Installer flow:

1. **Resolve `release_root`** — a checked-out Git tag (default) or an unpacked, hash-verified release tarball (the no-checkout path; §6).
2. Create/keep `<vault>/.memoria/.venv` (per-vault isolation stays).
3. **Install the code layer:** `pip install -e "$release_root"` on the PI's machine (editable — transparency kept); a non-editable copy-install on the operator path. Add `.[cluster]` when clustering is enabled.
4. **Reconcile the authored layer:** lay down `profiles/`, `schemas/`, `system/`, the gate shim, cron wrappers; three-way merge against the manifest so PI customizations surface instead of being clobbered (generalizes today's golden staging).
5. **Render** `config/*.yaml` and the cron wrappers with the venv python and vault path (the existing `{{PYTHON}}`/`{{VAULT_PATH}}`/`{{PROFILE}}` substitution, now pointing at console scripts).
6. **Never touch state:** `lane-overrides/`, `logs/`, rendered `config/`, `.env`, golden store.

No prebuilt `.whl` is shipped. Editable install means the code is the working tree under `release_root`, so it stays plainly inspectable — the one real ergonomic regression of the wheel framing disappears.

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

> **Why console scripts fit now but not today.** They require an *installed distribution* exposing entry points on the venv's `bin/`. Today the host invokes a `.py` file by absolute path against a source tree. An **installed (even editable) package** gives the venv `bin/memoria-policy-mcp` for free — no shipped wheel needed. #494's "Option 3 (package all + console scripts)" wasn't wrong — it was un-runnable on a rsync'd source tree. The blocker was the deployment mechanism, not packaging.

### 4.3 Delete the `__file__` import-root bootstraps

- **Import-root discovery** — the 11 `_RUNTIME_ROOT = Path(__file__)…; sys.path.insert(...)` bootstraps exist only to find sibling modules. Packaging **deletes all 11**; imports become `memoria.*`.
- **Vault resolution** — *already* explicit. `_shared.resolve_vault()` is pure arg→env with no `__file__` fallback. It stays as-is.

Hardcoded *data* relpaths (`system/logs/audit.jsonl`, `.memoria/lane-overrides`, `.memoria/golden`) stay — they're relative to `--vault`, which is correct. **Exception: `schemas/`.** `schema.py:25` resolves schemas from **code location** (`SCHEMAS_DIR = Path(__file__).resolve().parent.parent.parent / "schemas"`, with an optional `schemas_dir` override). That makes schemas behave like package data; the ship-vs-stay choice has a code consequence — §6.7.

### 4.4 Upgrades and integrity

**Integrity protection is unchanged.** Verified against `golden_restore.py:30-50`: the ADR-55 manifest is `system/{templates,dashboards,patterns,eval,scripts}/`, the files `home.md`/`system/vocabulary.md`/`AGENTS.md`, and three `.obsidian` config files. **No `.memoria/` prefix** is covered — runtime code, `schemas/`, and `lane-overrides/` were **never** golden. (The lone `.memoria/` string is `GOLDEN_RELDIR = ".memoria/golden"`, the *store* path.) Code-integrity protection is the MCP-only sandbox + git, and this design touches neither.

What the release manifest **adds** is *verification* over code + authored content (§2.1) — a strict superset of golden's old scope, but still verification, not protection. There is **no ADR-55 reconciliation blocker**; this design *extends* ADR-55 rather than colliding with it.

**Upgrade & rollback.** Editable install means an upgrade re-points the working tree (`git checkout vX`) and re-reconciles the authored layer — no `pip --upgrade` non-atomicity to fear. **Rollback is `git checkout <prev-tag> && ./install.sh`** — the same path, no retained-wheel `--force-reinstall` dance. (On the operator copy-install path, retain the previous release tarball as the equivalent net.)

### 4.5 The policy-gate boundary — resolved by the policy-core extraction (§2.2)

The gate runs in the **host process, whose interpreter the installer does not pin** — only the MCP servers it spawns get `{{PYTHON}}` (the venv); the operator launches the host and the repo doesn't own that interpreter (corroborated at `install.sh:542`: *"the plugin runs in the Hermes process, so no PYTHON"*). Today the gate does `sys.path.insert({{VAULT_PATH}}/.memoria/mcp)` and reaches the core via the fat chain `policy_hook → policy_mcp → memoria_runtime.policy`. That `sys.path` insert is exactly what breaks when code moves into the venv.

**Version skew is a security property, not a deployment chore.** If the gate runs a stale `MUTATING_ACTIONS`, a call the new runtime treats as mutating can be waved through by an out-of-date hard-deny boundary.

| Option | How the gate reaches the core | Skew safety | Verdict |
|---|---|---|---|
| **Extract a tiny standalone core (§2.2)** — both gate and servers import it; gate vendors only it, version-asserts at startup | in-process import of a dependency-free core | **✓ skew-free** — one release, one root, co-versioned; no fat chain to drift | **chosen** — small, auditable, interpreter-portable; no hot-path cost |
| Gate calls the policy MCP over the wire (IPC) | IPC to the running `policy` server | ✓ skew-free | **fallback only** — adds per-tool-call latency **and** a fail-closed availability dependency (a crashed policy server bricks the agent) |
| Host installs the full `memoria` wheel too | `import memoria.runtime.policy` | ✗ skew-prone | rejected — two independent installs of the boundary code can drift; needs a version assertion that is itself a slice of the IPC it's avoiding |

**Lean:** the core extraction (option 1) is the structural fix — it eliminates skew without a runtime hop or an availability dependency, and the same in-process import works in the host's interpreter precisely because the core has no transitive deps. IPC stays a fallback only if in-process import proves infeasible. Whichever ships, the hyphenated dir name (`memoria-policy-gate`) must become an importable module name. **The fat chain `policy_hook → policy_mcp → memoria_runtime.policy` must be cut to a real `policy` core first** — that refactor is the precondition for the gate dropping its `sys.path` reach-through.

---

## 5. How this scores vs. today

| Concern | Today | This design |
|---|---|---|
| Import roots | 10 (conftest) + 11 `__file__` inserts | **1** (installed package) |
| Top-level name | `.memoria` (un-importable) | `memoria` |
| Test import root | divergent `sys.path` ordering | single root (editable install) + a **required CI wheel-smoke** (§3.3) |
| Deployable unit | one rsync mirroring source | **a versioned release**, three layers reconciled by lifecycle |
| "Vault holds no source" | n/a | **honest version:** code → venv; authored content stays as managed content; state untouched |
| Dependency split | 3 `requirements*.txt`, blurred | one `pyproject`, **named groups** |
| Deploy | two-phase rsync (bulk + scoped `--delete`) | source-agnostic reconciling installer |
| Upgrade / rollback | mirror + prune; recovery = re-run installer | `git checkout vX && ./install.sh` / `checkout <prev-tag>` — no pip-atomicity worry |
| Console scripts | don't fit (path invocation) | **fit** (venv `bin/`, editable is enough) |
| Vault resolution | already explicit | unchanged — stays a parameter |
| Code integrity | sandbox + git — **not golden** | **protection unchanged**; manifest adds *verification* over code + authored layers |
| Policy-gate import | `{{VAULT_PATH}}/.memoria/mcp` on `sys.path`, fat chain | **tiny standalone core**, version-asserted, skew-free (§2.2/§4.5) |
| Transparency | code plainly inspectable in vault | **kept** (editable install; no shipped wheel) |
| Multi-machine ([ADR-63](../../../adr/63-multi-machine-deployment.md)) | rsync-from-checkout per machine | one versioned release, N vaults — natural substrate |

---

## 6. Honest trade-offs & mitigations

1. **The reconciling installer is more logic than `cp -R`/rsync** — three-way merge for the authored layer. But it's the same shape as today's golden staging, generalized, and replaces the fragile delete-pruned mirror.
2. **The policy-core extraction is real refactor work** and must precede the gate dropping its `sys.path` reach-through (§4.5). It's the one genuine prerequisite before the spine ships.
3. **The release manifest must be built and verified in CI** — a new artifact, but it subsumes three prior concerns (golden drift, gate version, code verification) into one source of truth.
4. **No shipped wheel removes a trust surface the first draft added.** Git-tag deploy carries no fetch-and-trust step. *When* the operator tarball path appears (§6 below), pin its SHA256 and verify before unpacking (sign when a signing story exists) — but that cost is deferred to the audience that needs it, not paid now.
5. **Build backend + version source.** hatchling + dynamic version from `src/memoria/__init__.py:__version__` (§3.2).
6. **Transparency is *preserved*, not traded.** Editable install keeps deployed code as the inspectable working tree. (The wheel framing's §6.2 regression is gone.)
7. **Data-file ship/stay boundary (the ADR needs the list).** None of these are golden-covered, so the split is "authored-static vs per-vault," not integrity:
   - **Ship in the release, manifest-covered (authored-static):** the type vocabulary under `schemas/` — **18** `types/*.yaml` + `calibration.yaml` + `folders.yaml` — today `--delete`-mirrored authored infra, already resolved relative to `__file__` (`schema.py:25`). As package data the `__file__` resolution survives (a `.parent`-depth tweak, or a clean switch to `importlib.resources`).
   - **Stay vault-side (per-vault/per-machine state):** `lane-overrides/`, rendered `config/`, `logs/`, `golden/`, `.env`.
   - **Open question — per-vault schema extensions?** If **no**, schemas ship as above. If **yes**, schemas stay under `<vault>/.memoria/schemas/` and **`schema.py:25` must move from `__file__`-relative to `--vault`-relative** (and the `len(types) == 18` self-test must relax) — the concrete price of the "stay" branch.

---

## 7. Migration path & blast radius

This note is the **target**, not an immediate migration. The spine changes the *deployment mechanism* (reconciling release-install vs rsync) and the *on-disk vault shape* (code moves into the venv). Full blast radius:

- `install.sh` (rewrite as the reconciling installer; deploy path, authored-layer staging, `{{PYTHON}}` substitution),
- every rendered `config.yaml` **and the cron wrappers** (both carry `{{PYTHON}}`/`{{VAULT_PATH}}`, both repoint at console scripts),
- the policy-gate boundary (§4.5 — extract the core),
- the **`src/.memoria` → `src/memoria` un-hiding** (the dotted path is hardcoded ~36× in `install.sh`).

*Not* in the blast radius: ADR-55 golden / `tests/test_golden_restore.py` — golden never covered `.memoria/` code; the release manifest *extends* golden's scope rather than reworking it (§4.4).

Staged path:

1. **Now (issue work, no ADR):** a repo-root `pyproject.toml` scoped **strictly to tooling** — `[tool.pytest.ini_options]` (`testpaths` + `pythonpath`) and `[tool.ruff]` only. **Keep `requirements-dev.txt`** — no `[project]` table yet. Deletes the conftest `sys.path` block. Independent of everything; the `operations` rename is already done, so nothing blocks this.
2. **Packaging:** add `[project]` + `src/`-layout, install editable, delete the 11 `__file__` bootstraps, wire console scripts. Stands on its own import-hygiene merits.
3. **The spine:** reconciling installer over a versioned release; extract the policy core (§2.2) **first**; introduce the release manifest; vault becomes code-in-venv + authored-content + state.

Sequencing note: step 2 (the package, editable) banks nearly all the import-hygiene wins **without** touching the deployment mechanism — pursue it independently. Step 3 is gated only on the policy-core extraction.

---

## 8. ADR status

This note backs **[ADR-76](../../../adr/76-versioned-vault-release-reconciling-installer.md)** (deferred). The two load-bearing decisions (§2.1 release + reconciling installer, §2.2 policy-core extraction) are the ADR's spine. ADR-76:

- carries **`assumes: [44, 46, 55, 69, 73]`** — ADR-44 (the conftest `sys.path` block we delete), ADR-46 (MCP-only sandbox = integrity protection), **ADR-55** (golden manifest, *generalized* into the release manifest — now an assumption, not merely "untouched"), ADR-69 (operations naming, landed), ADR-73 (docs-reference conventions),
- sits at `status: deferred` with `nav_exclude: true` and a *When this matters* section, re-judged each release per the [ADR-only decision model](../../../adr/),
- is **in tension with [ADR-26](../../../adr/26-repo-as-install-unit.md)** (install unit becomes a versioned release) and **strengthens [ADR-63](../../../adr/63-multi-machine-deployment.md)**,
- marks #494's "Option 3 (package all + console scripts)" as the eventual direction, with the deployment-mechanism change as its precondition.

***When this matters*** — pick up when **any** holds:

- **distribution:** Memoria ships to operators who can't run from a Git checkout → the tarball delivery + copy-install path go live (the git-tag path needs none of it);
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

# Step 2 (package, editable):
pip install -e ".[dev]"
python -c "import memoria; print(memoria.__version__)"
memoria-policy-mcp --vault /path/to/Memoria-test --help   # console script resolves
python -m build && pip install dist/memoria-*.whl   # CI-only: wheel-smoke catches package_data gaps

# Step 3 (the spine — reconciling installer over a release):
git checkout v<ver> && ./install.sh /path/to/Memoria-test   # reconciles code + authored; leaves state
# deployed-vault smoke: launch each MCP server via its venv console script and
# confirm it answers a tool list against the sandbox vault (Memoria-test).

# Rollback: checkout the prior tag and re-run (no pip-atomicity worry)
git checkout v<previous> && ./install.sh /path/to/Memoria-test

# Policy-gate (§4.5): confirm the extracted core lets the host-process gate resolve policy
# WITHOUT version-skew, that gate.__core_version__ == manifest version, and that the gate
# still hard-denies a blocked call.
# (No golden step for code: golden never covered .memoria/; code integrity = sandbox + git.)
```
