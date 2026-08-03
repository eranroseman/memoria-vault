# Packaging Gate and Structure Repairs — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make packaging failures visible to the one gate, close the namespace-package hole, fix the single
module-level layer inversion, make the test suite move-safe, and extract the two self-contained blocks from
`runtime/state.py` — stages 1–5 of the 2026-08-02 structure audit
(`docs/superpowers/specs/2026-08-02-src-tests-structure-audit.md`), as amended by its review.

**Architecture:** Seven tasks, strictly ordered, each independently mergeable and green under
`python scripts/verify` on its own. Tasks 1–2 give the gate eyes on the built artifact *before* anything moves;
tasks 4–5 convert silent late test failures into loud collection-time failures *before* the only move (tasks
6–7) happens. No task leaves a module reachable at two dotted paths.

**Tech Stack:** Python 3.12, setuptools (pyproject), pip wheel, pytest (+xdist), AST-based static tests.

## Global Constraints

- **The one gate:** every task ends with `PYTEST_XDIST_AUTO_NUM_WORKERS=2 python scripts/verify` → `verify: OK`.
- **Goldens must not move in any task.** After the gate, `git status --porcelain tests/fixtures/floor/goldens/`
  must print nothing. No task here touches seeded vault content — task 2's identifier rule exists precisely to
  keep `__init__.py` out of `product/workspace_seed/` data directories.
- **Schema rung 19 is untouched.** No task reads or writes `SCHEMA_VERSION`, `schema.sql` content, or any table.
- **No dual dotted paths, ever:** a move lands whole in one commit; no compatibility shim at an old path.
  (That coexistence is what produced the `subsystems/` namespace hole.)
- **Stage 6 of the audit (the `integrity` name collision) is deliberately out of scope** — deferred per the
  review's answer to open question 3. Stage 7+ (remaining §5 seams) is gated behind this plan and out of scope.
- **Stage order is load-bearing:** task 1 verifies task 2; tasks 4–5 protect tasks 6–7. Do not reorder.
- Commit messages follow the repo's plain style (`area: what changed`). Stage explicit paths only — never
  unbounded `git add` (a PreToolUse hook rejects it).
- Audit facts corrected by this plan (record, don't re-derive): the implicit-directory count is **nine**, not
  seven (§2.1 counted only leaf dirs); the inversion fix is a **deferred import**, not a parameterised seam
  (`engine_api` is used only by `main()` — deletion beats mechanism); PI-only operations are golden-free, so
  nothing here can move a floor golden.

---

### Task 1: The wheel build-and-probe gate

Stage 1 of the audit, strengthened per review finding 2. `scripts/verify` never builds an artifact, which is
why the namespace hole (task 2) shipped green indefinitely — and issue **#1689** (the dead editable install:
`memoria --version` raising `ModuleNotFoundError` while every gate stayed green) is this class live. The gate
must therefore do three things, not one: **build** the wheel, **assert its contents** against the source tree,
and **install it into a scratch venv and run it** — the entry point, the packaged schema resource, and the
deepest `-m`-published module path.

**Files:**
- Create: `scripts/checks/wheel_gate.py`
- Modify: `scripts/verify` (the `GATES` roster, ~line 48; `_DOCS_SKIP`, ~line 103)
- Modify: `tests/test_verify_script.py` (the roster pin)
- Modify: `.gitignore` (add `build/` — in-tree PEP 517 builds create it; `*.egg-info/` is already covered)

**Interfaces:**
- Consumes: `pyproject.toml` `[project] version`, `[project.scripts] memoria`.
- Produces: gate command `python3 scripts/checks/wheel_gate.py`, present in `GATES` and skipped under
  `VERIFY_DOCS_ONLY=1`. Task 2's acceptance rests on this gate existing; task 6 relies on it to prove the
  `state/` package ships.

- [ ] **Step 1: Write the failing roster pin**

In `tests/test_verify_script.py`, extend the tuple in `test_roster_covers_lint_tests_and_product_gates` and add
a docs-narrowing assert at the end of `test_docs_only_scope_narrows_the_roster`:

```python
    # in test_roster_covers_lint_tests_and_product_gates, add to the existing tuple:
    for gate in (
        "python3 scripts/checks/schema_doc_drift.py",
        "python3 scripts/checks/removed_surface_gate.py",
        "python3 scripts/checks/checked_terminology_gate.py",
        "python3 scripts/checks/plugin_provenance_doctor.py",
        "python3 scripts/checks/doc_claims_gate.py",
        "python3 scripts/checks/wheel_gate.py",
        "python3 scripts/test_vault/e2e_smoke.py",
    ):
        assert gate in flat
```

```python
    # at the end of test_docs_only_scope_narrows_the_roster:
    # a docs-only diff provably cannot change packaging, so the wheel gate is skipped
    assert not any("wheel_gate" in f for f in docs)
```

- [ ] **Step 2: Run the pin to verify it fails**

Run: `PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 python -m pytest tests/test_verify_script.py -q`
Expected: FAIL — `assert 'python3 scripts/checks/wheel_gate.py' in flat`.

- [ ] **Step 3: Write `scripts/checks/wheel_gate.py`**

```python
#!/usr/bin/env python3
"""Build the wheel and prove the installed artifact works.

Named failure (#1689; audit §2.0): nothing in the gate exercised packaging or
the installed entry point, so a dropped package, a stale package-data glob, a
moved data file, or a broken console script all shipped green. This gate
builds the wheel with the repo's own build backend, asserts every shippable
source file is in it, installs it into a scratch venv, and probes the three
bindings the repo relies on: the ``memoria`` entry point, the packaged
``schema.sql`` resource, and the deepest ``-m``-published module path.

POSIX-only paths (``bin/``): verify runs on Linux locally and in CI; the
PowerShell leg of verify covers the one Windows artifact separately.
"""

from __future__ import annotations

import subprocess
import sys
import tempfile
import tomllib
import venv
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / "src" / "memoria_vault"

_SKIP_DIR_NAMES = {"__pycache__"}
_SKIP_SUFFIXES = {".pyc"}

# The deepest documented ``python -m`` path (audit §4.1). If this import works
# from the installed wheel, the whole subsystems subtree shipped.
_DEEP_MODULE = "memoria_vault.runtime.subsystems.integrity.linter.detectors"


def _expected_members() -> set[str]:
    """Every file under src/memoria_vault/ that must appear in the wheel.

    Everything ships: .py by packaging, everything else by a package-data
    glob — and a source file matching *no* glob is a bug this gate exists to
    catch (``memoria init`` seeds from packaged resources, so an unshipped
    seed file breaks fresh vaults, silently).
    """
    members: set[str] = set()
    for path in SRC.rglob("*"):
        if not path.is_file():
            continue
        if path.suffix in _SKIP_SUFFIXES or _SKIP_DIR_NAMES & set(path.parts):
            continue
        members.add((Path("memoria_vault") / path.relative_to(SRC)).as_posix())
    return members


def _build_wheel(tmp: Path) -> Path:
    run = subprocess.run(
        [
            sys.executable, "-m", "pip", "wheel", str(ROOT),
            "--no-deps", "--no-build-isolation", "--wheel-dir", str(tmp),
        ],
        capture_output=True, text=True,
    )
    if run.returncode != 0:
        sys.exit(f"wheel-gate: build failed:\n{run.stdout}\n{run.stderr}")
    wheels = list(tmp.glob("memoria_vault-*.whl"))
    if len(wheels) != 1:
        sys.exit(f"wheel-gate: expected exactly one wheel, found {sorted(w.name for w in wheels)}")
    return wheels[0]


def _check_contents(wheel: Path) -> None:
    with zipfile.ZipFile(wheel) as zf:
        shipped = set(zf.namelist())
    missing = sorted(m for m in _expected_members() if m not in shipped)
    if missing:
        sys.exit(
            "wheel-gate: source files missing from the wheel "
            "(package or package-data gap):\n  " + "\n  ".join(missing)
        )


def _probe_install(wheel: Path, tmp: Path) -> None:
    venv_dir = tmp / "venv"
    # system-site-packages so third-party deps resolve from the dev env while
    # memoria_vault itself comes from the wheel; the __file__ assert below is
    # what proves the wheel copy shadows any editable install.
    venv.EnvBuilder(with_pip=True, system_site_packages=True).create(venv_dir)
    py = venv_dir / "bin" / "python"
    subprocess.run(
        [str(py), "-m", "pip", "install", "--quiet", "--no-deps", "--no-index", str(wheel)],
        check=True,
    )
    version = tomllib.loads((ROOT / "pyproject.toml").read_text("utf-8"))["project"]["version"]
    probe = (
        "import importlib\n"
        "import memoria_vault\n"
        f"assert memoria_vault.__file__.startswith({str(venv_dir)!r}), memoria_vault.__file__\n"
        f"assert memoria_vault.__version__ == {version!r}, memoria_vault.__version__\n"
        "from importlib.resources import files\n"
        "schema = files('memoria_vault.runtime').joinpath('schema.sql').read_text('utf-8')\n"
        "assert 'PRAGMA user_version' in schema\n"
        f"importlib.import_module({_DEEP_MODULE!r})\n"
    )
    subprocess.run([str(py), "-c", probe], check=True)
    out = subprocess.run(
        [str(venv_dir / "bin" / "memoria"), "--version"],
        check=True, capture_output=True, text=True,
    ).stdout.strip()
    if out != f"memoria {version}":
        sys.exit(f"wheel-gate: entry point reported {out!r}, expected 'memoria {version}'")


def main() -> None:
    with tempfile.TemporaryDirectory(prefix="memoria-wheel-gate-") as tmp:
        tmpdir = Path(tmp)
        wheel = _build_wheel(tmpdir)
        _check_contents(wheel)
        _probe_install(wheel, tmpdir)
    print("wheel-gate: OK")


if __name__ == "__main__":
    main()
```

- [ ] **Step 4: Run the gate script directly — treat any red as a finding, not a fixture problem**

Run: `python3 scripts/checks/wheel_gate.py`
Expected: `wheel-gate: OK`.

If `_check_contents` reports missing members on this first run, **that is the gate catching a live packaging
gap on day one** (audit §2.0 lists the candidate classes). Fix it by extending the matching
`[tool.setuptools.package-data]` glob in `pyproject.toml` — and mirror the change in
`tests/test_package_spine.py::test_pyproject_declares_installable_memoria_package`, which pins the glob lists
exactly. Do not weaken `_expected_members`.

- [ ] **Step 5: Wire the gate into `scripts/verify`**

In `GATES`, insert after the `doc_claims_gate.py` entry (packaging breaks should surface before the 3-minute
pytest stage):

```python
    ["python3", "scripts/checks/doc_claims_gate.py"],
    ["python3", "scripts/checks/wheel_gate.py"],
```

In `_DOCS_SKIP`, add the marker:

```python
_DOCS_SKIP = ("e2e_smoke.py", "-m compileall", "bash -n", "wheel_gate.py")
```

Append `build/` to `.gitignore` (in-tree PEP 517 builds create it; `*.egg-info/` is already ignored at line 10).

- [ ] **Step 6: Run the pin to verify it passes**

Run: `PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 python -m pytest tests/test_verify_script.py -q`
Expected: PASS (all tests).

- [ ] **Step 7: Kill-check the probe (the gate must be able to fail)**

Temporarily rename the entry point in `pyproject.toml` (`memoria =` → `memoria_broken =`), run
`python3 scripts/checks/wheel_gate.py`, and confirm it exits nonzero (the `bin/memoria` probe fails). Revert
byte-for-byte and re-run to green. A gate never seen red is decoration.

- [ ] **Step 8: Full gate**

Run: `PYTEST_XDIST_AUTO_NUM_WORKERS=2 python scripts/verify`
Expected: `verify: OK`. Then `git status --porcelain tests/fixtures/floor/goldens/` → empty.

- [ ] **Step 9: Commit**

```bash
git add scripts/checks/wheel_gate.py scripts/verify tests/test_verify_script.py .gitignore
git commit -m "gate: build the wheel, assert its contents, install and probe it (closes #1689's class)"
```

---

### Task 2: Close the namespace hole — every import-chain directory is an explicit package

Stage 2, with the review's corrected acceptance test. **Nine** directories lack `__init__.py`, not seven — and
four of them (`subsystems/`, `subsystems/processing/`, `subsystems/integrity/`, `subsystems/telemetry/`)
contain no `.py` directly, so a test that only checks module-bearing directories would leave them as namespace
packages and the hole open. The rule that closes it: **every directory on a valid import chain must be a
regular package.** Data directories under `product/workspace_seed/` (e.g. `.claude/hooks/`, which holds a
seeded `.py`) are *excluded by construction* — their names are not Python identifiers, they are shipped by
package-data globs, and an `__init__.py` there would be seeded into user vaults and move every floor golden.

**Files:**
- Create (docstring-only, one line each):
  - `src/memoria_vault/runtime/subsystems/__init__.py`
  - `src/memoria_vault/runtime/subsystems/integrity/__init__.py`
  - `src/memoria_vault/runtime/subsystems/integrity/linter/__init__.py`
  - `src/memoria_vault/runtime/subsystems/integrity/retraction/__init__.py`
  - `src/memoria_vault/runtime/subsystems/lib/__init__.py`
  - `src/memoria_vault/runtime/subsystems/processing/__init__.py`
  - `src/memoria_vault/runtime/subsystems/processing/project/__init__.py`
  - `src/memoria_vault/runtime/subsystems/telemetry/__init__.py`
  - `src/memoria_vault/runtime/subsystems/telemetry/eval/__init__.py`
- Modify: `pyproject.toml` (`[tool.setuptools.packages.find]` gains `namespaces = false`)
- Test: `tests/test_package_spine.py` (new test)

**Interfaces:**
- Consumes: task 1's wheel gate (proves the subtree still ships once `namespaces = false` makes implicit
  packages non-shipping).
- Produces: the invariant later moves rely on — a directory dropped from packaging fails the gate instead of
  vanishing from the wheel.

- [ ] **Step 1: Write the failing test**

Append to `tests/test_package_spine.py`:

```python
def test_every_import_chain_directory_is_an_explicit_package():
    """A directory reachable by import must carry __init__.py (audit §2.1).

    Implicit namespace packages ship only while packages.find defaults
    namespaces=true; an explicit package list, namespaces=false, or a move
    drops them from the wheel silently. Scope: directories whose every path
    segment under src/ is a Python identifier and that either lead to a .py
    file or are named as a dotted package-data key. Data directories such as
    product/workspace_seed/.claude/hooks are excluded by the identifier rule
    -- an __init__.py there would be seeded into user vaults.
    """
    src = ROOT / "src"
    src_root = src / "memoria_vault"

    def importable(d: Path) -> bool:
        return all(part.isidentifier() for part in d.relative_to(src).parts)

    required: set[Path] = set()
    for py in src_root.rglob("*.py"):
        if "__pycache__" in py.parts:
            continue
        d = py.parent
        while d != src and importable(d):
            required.add(d)
            d = d.parent
    data = tomllib.loads((ROOT / "pyproject.toml").read_text(encoding="utf-8"))
    for key in data["tool"]["setuptools"]["package-data"]:
        p = src / Path(*key.split("."))
        if p.is_dir():
            required.add(p)

    missing = sorted(
        str(d.relative_to(ROOT)) for d in required if not (d / "__init__.py").is_file()
    )
    assert missing == [], f"implicit namespace directories: {missing}"
```

- [ ] **Step 2: Run it to verify it fails, listing exactly the nine directories**

Run: `PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 python -m pytest tests/test_package_spine.py::test_every_import_chain_directory_is_an_explicit_package -q`
Expected: FAIL, `missing` naming the nine `subsystems` directories and nothing else. If it names anything
under `product/workspace_seed/`, the identifier exclusion is broken — stop and fix the test, do not create
that file.

- [ ] **Step 3: Create the nine `__init__.py` files**

Each is a single line. Contents, respectively:

```python
"""Runtime subsystems: filed implementations behind the flat runtime modules."""
```
```python
"""Integrity subsystems: the vault-tree linter and the retraction sweep."""
```
```python
"""The zero-LLM, report-only vault linter; every module here ships a main()."""
```
```python
"""The retraction sweep over the derivation graph."""
```
```python
"""Shared library helpers for the subsystems."""
```
```python
"""Processing subsystems."""
```
```python
"""Project-level processing: structural impact over the substrate projection."""
```
```python
"""Telemetry subsystems."""
```
```python
"""The quarterly eval loop: dispatch and scoring."""
```

- [ ] **Step 4: Pin the packaging mode**

In `pyproject.toml`, extend the find table:

```toml
[tool.setuptools.packages.find]
where = ["src"]
include = ["memoria_vault*"]
namespaces = false
```

(`test_pyproject_declares_installable_memoria_package` asserts `where` and `include` by key, so the added key
breaks nothing.)

- [ ] **Step 5: Run the new test and the wheel gate**

Run: `PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 python -m pytest tests/test_package_spine.py -q` → PASS.
Run: `python3 scripts/checks/wheel_gate.py` → `wheel-gate: OK`. This is the belt-and-braces pair: the test
fails at source, the gate fails at artifact, and under `namespaces = false` a future implicit directory now
fails **both**.

- [ ] **Step 6: Full gate, goldens check**

Run: `PYTEST_XDIST_AUTO_NUM_WORKERS=2 python scripts/verify` → `verify: OK`.
Run: `git status --porcelain tests/fixtures/floor/goldens/ src/memoria_vault/product/workspace_seed/` → empty
apart from nothing: the seed tree must be untouched.

- [ ] **Step 7: Commit**

```bash
git add src/memoria_vault/runtime/subsystems tests/test_package_spine.py pyproject.toml
git commit -m "packaging: make all nine subsystems directories explicit packages, pin namespaces=false"
```

---

### Task 3: Fix the one layer inversion — `eval_dispatch` stops importing the engine at module level

Stage 3. [eval_dispatch.py:29](../../../src/memoria_vault/runtime/subsystems/telemetry/eval/eval_dispatch.py#L29)
imports `engine.api` at module level while `worker.py` (domain) imports `eval_dispatch` — the only such
inversion in the tree. **Deviation from the audit, recorded here:** the audit says "parameterise the run seam",
but `engine_api` is referenced *only inside `main()`* (the `python -m` CLI entry) — `dispatch()` never touches
it. A deferred import inside `main()` removes the inversion with zero new surface; deletion beats mechanism.
The two transports (`http_transport`, `mcp_transport`) also import the engine at module level but have zero
fan-in from `src/` — they are entry points, and the guard below encodes that distinction so the audit's claim
stays checkable instead of grep-refutable.

**Files:**
- Modify: `src/memoria_vault/runtime/subsystems/telemetry/eval/eval_dispatch.py` (lines 29, ~220)
- Create: `tests/test_import_layering.py`

**Interfaces:**
- Consumes: nothing from earlier tasks (independent; ordered here because it is small and revertible).
- Produces: the layering invariant tasks 6–7 inherit: no module under `runtime/` except the two zero-fan-in
  transports may import `memoria_vault.engine` at module level.

- [ ] **Step 1: Write the failing test**

Create `tests/test_import_layering.py`:

```python
"""Runtime modules must not depend on the engine layer at import time."""

from __future__ import annotations

import ast
from pathlib import Path

import pytest

pytestmark = pytest.mark.static

ROOT = Path(__file__).resolve().parents[1]
RUNTIME = ROOT / "src" / "memoria_vault" / "runtime"

# Entry-point transports: zero fan-in from src/ (nothing imports them), so an
# engine import there is a door binding, not an inversion. Anything else under
# runtime/ importing the engine at module level makes a surface module a
# dependency of a domain module (audit §2.3).
ENTRY_POINTS = {"http_transport.py", "mcp_transport.py"}


def _module_level_engine_imports(path: Path) -> list[int]:
    tree = ast.parse(path.read_text(encoding="utf-8"))
    lines = []
    for node in tree.body:  # module level only: deferred imports are the sanctioned idiom
        if isinstance(node, ast.ImportFrom) and (node.module or "").startswith(
            "memoria_vault.engine"
        ):
            lines.append(node.lineno)
        if isinstance(node, ast.Import) and any(
            alias.name.startswith("memoria_vault.engine") for alias in node.names
        ):
            lines.append(node.lineno)
    return lines


def test_runtime_never_imports_the_engine_at_module_level() -> None:
    offenders = {}
    for path in sorted(RUNTIME.rglob("*.py")):
        if "__pycache__" in path.parts or path.name in ENTRY_POINTS:
            continue
        lines = _module_level_engine_imports(path)
        if lines:
            offenders[str(path.relative_to(ROOT))] = lines
    assert offenders == {}, f"module-level engine imports in runtime: {offenders}"


def test_the_entry_point_exemption_is_still_earned() -> None:
    """The two exempt transports must keep zero fan-in from src/.

    The day something under src/ imports a transport, its exemption above is
    a hole, not a door binding — this is the check that notices.
    """
    importers = []
    for path in sorted((ROOT / "src").rglob("*.py")):
        if "__pycache__" in path.parts or path.name in ENTRY_POINTS:
            continue
        text = path.read_text(encoding="utf-8")
        for name in ("http_transport", "mcp_transport"):
            if f"import {name}" in text or f"import memoria_vault.runtime.{name}" in text:
                importers.append(f"{path.relative_to(ROOT)} -> {name}")
    assert importers == [], importers


def test_the_guard_itself_can_fail() -> None:
    """Kill-check: the detector flags a synthetic module-level engine import."""
    bad = "from memoria_vault.engine import api as engine_api\n"
    tree = ast.parse(bad)
    assert isinstance(tree.body[0], ast.ImportFrom)
    probe = Path(__file__).parent / "_layering_probe.py"
    probe.write_text(bad, encoding="utf-8")
    try:
        assert _module_level_engine_imports(probe) == [1]
    finally:
        probe.unlink()
```

- [ ] **Step 2: Run it to verify it fails**

Run: `PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 python -m pytest tests/test_import_layering.py -q`
Expected: FAIL — `offenders` contains `eval_dispatch.py: [29]` and nothing else.

- [ ] **Step 3: Move the import**

In `eval_dispatch.py`, delete line 29 (`from memoria_vault.engine import api as engine_api`) and insert the
deferred import as the first statement of `main()`:

```python
def main() -> None:
    # Deferred: the engine is a surface layer; only this CLI entry uses it, and
    # a module-level import made every importer of this module (worker.py) a
    # transitive engine dependent (audit §2.3).
    from memoria_vault.engine import api as engine_api

    ap = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
```

The rest of `main()` is unchanged (`engine_api.run_operation(...)` now binds to the local name).

- [ ] **Step 4: Run the layering test and the eval suite**

Run: `PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 python -m pytest tests/test_import_layering.py tests/test_eval.py tests/test_eval_score.py -q`
Expected: PASS. (`test_main_dry_run_uses_persisted_operation_context` and its live twin execute the real
`main()` → real `engine_api.run_operation`, so the deferred import is exercised, not just parsed.)

- [ ] **Step 5: Full gate, then commit**

Run: `PYTEST_XDIST_AUTO_NUM_WORKERS=2 python scripts/verify` → `verify: OK`.

```bash
git add src/memoria_vault/runtime/subsystems/telemetry/eval/eval_dispatch.py tests/test_import_layering.py
git commit -m "runtime: defer eval_dispatch's engine import into main(), pin the layering rule"
```

---

### Task 4: Harden the testing-level gate and centralise the repo-root constants

Stage 4, first half. Two silent-vacuity risks: `test_testing_levels.py` uses non-recursive `glob` with its
asserts inside the loop, so a future `tests/` subdirectory passes vacuously (zero paths, zero asserts); and 19
test files each compute the repo root from their own `__file__` depth, so any relocation silently repoints
fixtures (`floor_lib` would resolve goldens at `tests/tests/fixtures/...`).

**Files:**
- Modify: `tests/test_testing_levels.py` (lines 45, 53: `glob` → `rglob`, plus a non-empty assert)
- Modify: `tests/helpers.py` (gains the single `REPO_ROOT`)
- Modify (root-constant conversion, 18 files): `tests/floor_lib.py`, `tests/test_attention_view.py`,
  `tests/test_cspell_scope.py`, `tests/test_exploration_trace.py`, `tests/test_install_test_vault_local_llm.py`,
  `tests/test_memoria_obsidian_package.py`, `tests/test_node_tooling.py`, `tests/test_package_spine.py`,
  `tests/test_patterns.py`, `tests/test_plugin_provenance.py`, `tests/test_policy_gate_completeness.py`,
  `tests/test_profiles.py`, `tests/test_refresh_test_vault.py`, `tests/test_schema_doc_drift.py`,
  `tests/test_test_env_harness.py`, `tests/test_testing_levels.py`, `tests/test_verify_script.py`,
  `tests/test_workspace_seed_links.py`

**Interfaces:**
- Consumes: nothing.
- Produces: `tests.helpers.REPO_ROOT` (a `Path`; the one place test code derives the repo root), and a level
  gate that cannot pass on an empty iteration. Task 5 imports nothing from here but assumes the level gate is
  recursive when it registers its own file.

- [ ] **Step 1: Demonstrate the vacuity (kill-check before the fix)**

```bash
mkdir -p tests/_probe_subdir && printf 'import pytest\n\ndef test_x():\n    assert True\n' > tests/_probe_subdir/test_probe_no_level.py
PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 python -m pytest tests/test_testing_levels.py -q
```
Expected today: **PASS** — the file has no `pytestmark` and the gate does not see it. That pass is the defect.
Remove the probe: `rm -r tests/_probe_subdir`.

- [ ] **Step 2: Fix the gate**

In `tests/test_testing_levels.py`, both call sites (lines 45 and 53), replace the iteration and make emptiness
loud:

```python
def test_each_pytest_file_declares_exactly_one_testing_level() -> None:
    levels = _registered_levels()
    files = sorted((ROOT / "tests").rglob("test_*.py"))
    assert files, "level gate found no test files; the glob is broken"

    for path in files:
        declared = [name for name in _module_marks(path) if name in levels]
        assert len(declared) == 1, (
            f"{path.name} declares levels {declared}; expected exactly one registered level"
        )
```

Apply the same `rglob` + non-empty assert to the second site (line 53's
`test_pytest_files_are_named_by_behavior_not_release_checkpoint` keeps its negative form:
`assert not list((ROOT / "tests").rglob("test_alpha*.py"))`).

- [ ] **Step 3: Re-run the probe to verify the gate now bites**

Recreate the probe from step 1, run the gate test — Expected: **FAIL** naming
`test_probe_no_level.py declares levels []`. Remove the probe again (`rm -r tests/_probe_subdir`).

- [ ] **Step 4: Centralise the root constant**

In `tests/helpers.py`, add at module level (keeping its existing content):

```python
# The one place test code derives the repo root. Everything else imports this:
# a file that computes the root from its own __file__ breaks silently when it
# moves (audit §4.6).
REPO_ROOT = Path(__file__).resolve().parents[1]
```

Then in each of the other 17 files, replace the local computation — the two shapes in the tree are
`ROOT = Path(__file__).resolve().parent.parent` and `ROOT = Path(__file__).resolve().parents[1]` — with:

```python
from tests.helpers import REPO_ROOT as ROOT
```

(keep each file's existing local alias name; `tests.helpers` is the established import style — cf.
`from tests import floor_lib` already in the suite). In `tests/floor_lib.py` the constant is `ROOT` at line 19;
same substitution.

- [ ] **Step 5: Verify no stragglers**

Run: `grep -rn 'resolve().parent.parent\|resolve().parents\[1\]' tests/ --include='*.py'`
Expected: exactly one hit — `tests/helpers.py`.

- [ ] **Step 6: Full gate, then commit**

Run: `PYTEST_XDIST_AUTO_NUM_WORKERS=2 python scripts/verify` → `verify: OK`.

```bash
git add tests/test_testing_levels.py tests/helpers.py tests/floor_lib.py tests/test_attention_view.py \
  tests/test_cspell_scope.py tests/test_exploration_trace.py tests/test_install_test_vault_local_llm.py \
  tests/test_memoria_obsidian_package.py tests/test_node_tooling.py tests/test_package_spine.py \
  tests/test_patterns.py tests/test_plugin_provenance.py tests/test_policy_gate_completeness.py \
  tests/test_profiles.py tests/test_refresh_test_vault.py tests/test_schema_doc_drift.py \
  tests/test_test_env_harness.py tests/test_verify_script.py tests/test_workspace_seed_links.py
git commit -m "tests: recursive level gate that cannot pass empty; one REPO_ROOT in helpers"
```

---

### Task 5: Collection-time guard over dotted `memoria_vault.` string literals

Stage 4, second half, strengthened per review finding 5. 97 dotted-string literals across 31 test files
(monkeypatch targets, `sys.modules` keys) fail *late* after a move — or worse, keep passing while patching a
key nothing imports. The guard resolves every such literal at test time: the module prefix via import, **and
the attribute tail via `getattr`** — a module that resolves with a renamed symbol still fails late, which is
exactly the vacuous-pass class the audit's own §5.1 caution describes. The guard ships with its own kill test:
a checker with a dead detector reads green forever.

**Files:**
- Create: `tests/test_dotted_target_literals.py`

**Interfaces:**
- Consumes: `tests.helpers.REPO_ROOT` (task 4).
- Produces: the invariant tasks 6–7 rely on — after any move or rename, every stale dotted literal in the
  suite fails this one static test with the literal named, instead of 97 tests failing (or vacuously passing)
  individually.

- [ ] **Step 1: Write the guard (and its kill tests) in one file**

Create `tests/test_dotted_target_literals.py`:

```python
"""Every dotted memoria_vault literal in the suite resolves to a live object.

Monkeypatch targets and sys.modules keys are strings; after a move they fail
late (or pass while patching a key nothing imports). This resolves each one at
static-test time: longest importable module prefix, then the attribute tail.
"""

from __future__ import annotations

import ast
import importlib
import re
from importlib.util import find_spec
from pathlib import Path

import pytest

from tests.helpers import REPO_ROOT

pytestmark = pytest.mark.static

_DOTTED = re.compile(r"^memoria_vault(\.[A-Za-z_][A-Za-z0-9_]*)+$")

# Literals that intentionally name absent objects (e.g. a negative test that
# proves something retired stays retired). Every entry carries a reason.
ALLOWLIST: dict[str, str] = {}


def _call_string_literals(path: Path) -> list[tuple[str, int]]:
    """Dotted literals appearing as arguments in call expressions.

    Restricting to calls skips docstrings and prose while catching every
    monkeypatch.setattr / setitem / patch-style target.
    """
    found: list[tuple[str, int]] = []
    tree = ast.parse(path.read_text(encoding="utf-8"))
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        for arg in [*node.args, *(kw.value for kw in node.keywords)]:
            if (
                isinstance(arg, ast.Constant)
                and isinstance(arg.value, str)
                and _DOTTED.match(arg.value)
            ):
                found.append((arg.value, arg.lineno))
    return found


def _unresolvable(literal: str) -> str | None:
    """None if the literal names a live module or module attribute; else why."""
    parts = literal.split(".")
    for cut in range(len(parts), 0, -1):
        module_name = ".".join(parts[:cut])
        try:
            if find_spec(module_name) is None:
                continue
        except (ImportError, ModuleNotFoundError):
            continue
        obj = importlib.import_module(module_name)
        for attr in parts[cut:]:
            if not hasattr(obj, attr):
                return f"{module_name!r} has no attribute chain {'.'.join(parts[cut:])!r}"
            obj = getattr(obj, attr)
        return None
    return "no importable module prefix"


def test_every_dotted_literal_resolves() -> None:
    failures = []
    for path in sorted((REPO_ROOT / "tests").rglob("test_*.py")):
        if path.name == Path(__file__).name:
            continue
        for literal, lineno in _call_string_literals(path):
            if literal in ALLOWLIST:
                continue
            why = _unresolvable(literal)
            if why is not None:
                failures.append(f"{path.name}:{lineno}: {literal} -- {why}")
    assert failures == [], "\n".join(failures)


def test_the_resolver_flags_a_missing_module() -> None:
    assert _unresolvable("memoria_vault.runtime.no_such_module.attr") is not None


def test_the_resolver_flags_a_missing_attribute() -> None:
    assert _unresolvable("memoria_vault.runtime.state.no_such_symbol") is not None


def test_the_resolver_accepts_a_live_module_and_attribute() -> None:
    assert _unresolvable("memoria_vault.runtime.state") is None
    assert _unresolvable("memoria_vault.runtime.state.SCHEMA_VERSION") is None


def test_the_collector_sees_call_arguments_not_docstrings() -> None:
    src = (
        '"""memoria_vault.runtime.in_a_docstring is prose, not a target."""\n'
        'monkeypatch.setitem(sys.modules, "memoria_vault.runtime.telemetry", None)\n'
    )
    probe = Path(__file__).parent / "_dotted_probe.py"
    probe.write_text(src, encoding="utf-8")
    try:
        literals = [text for text, _ in _call_string_literals(probe)]
    finally:
        probe.unlink()
    assert literals == ["memoria_vault.runtime.telemetry"]
```

- [ ] **Step 2: Run it — expect either PASS or a real finding**

Run: `PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 python -m pytest tests/test_dotted_target_literals.py -q`
Expected: PASS. If `test_every_dotted_literal_resolves` fails, each named literal is a **live stale target
already in the suite** — fix the test that owns it (retarget the literal), or, only where the absence is the
tested claim, add it to `ALLOWLIST` with a one-line reason. Do not blanket-allow.

- [ ] **Step 3: Full gate, then commit**

Run: `PYTEST_XDIST_AUTO_NUM_WORKERS=2 python scripts/verify` → `verify: OK`.

```bash
git add tests/test_dotted_target_literals.py
git commit -m "tests: resolve every dotted memoria_vault target literal at static-test time"
```

---

### Task 6: `state.py` becomes a package; `workspace_lock.py` is the first extraction

Stage 5, first half — the smaller block first, as the dry run for the mechanics. The workspace-lock block is
lines 101–487 of `state.py` (from `_WORKSPACE_LOCKS_GUARD` through the end of `workspace_lock()`, immediately
before `db_path` at 489): ten symbols, 385 LOC, referencing zero module-level names defined outside the block.
All 107 importers use `from memoria_vault.runtime import state` + attribute access (verified: zero
`from ...state import` hits repo-wide), so re-exports leave every read call site unedited. The real risk is
monkeypatch efficacy: after the move, a patch on `state.<name>` rebinds the facade's alias but **not** the name
the submodule's own code calls — every such site must be retargeted and kill-checked.

**Files:**
- Move: `src/memoria_vault/runtime/state.py` → `src/memoria_vault/runtime/state/__init__.py`
- Create: `src/memoria_vault/runtime/state/workspace_lock.py`
- Modify: `tests/test_package_spine.py` (two source-as-text reads), `tests/test_schema_version.py` (one)
- Modify: any test that monkeypatches a moved name (enumerated in step 4)

**Interfaces:**
- Consumes: tasks 1–2 (the wheel gate + explicit-package test prove `state/` ships); task 5 (a stale dotted
  literal fails loudly).
- Produces: package `memoria_vault.runtime.state` whose `__init__` re-exports the full existing surface;
  submodule `memoria_vault.runtime.state.workspace_lock` with `workspace_lock(vault)` and the nine private
  lock helpers. Task 7 repeats exactly this shape for `markdown.py`.

- [ ] **Step 1: Convert to a package (one commit-atomic move, no dual path)**

```bash
mkdir src/memoria_vault/runtime/state
git mv src/memoria_vault/runtime/state.py src/memoria_vault/runtime/state/__init__.py
```

- [ ] **Step 2: Extract the block**

Create `src/memoria_vault/runtime/state/workspace_lock.py` containing, verbatim from `__init__.py`:
the module docstring line `"""Cross-process workspace lock (one writer per vault)."""`, the imports the block
needs (`contextlib`, `ctypes`, `errno`, `os`, `stat`, `threading`, `time`, `pathlib.Path`, and the existing
platform-conditional `fcntl`/`msvcrt` import block from lines 43–52), then the moved lines 101–487:
`_WORKSPACE_LOCKS_GUARD`, `_WORKSPACE_LOCKS`, `_WORKSPACE_LOCK_DEPTH`, `_WORKSPACE_LOCK_PID`,
`_workspace_lock_key`, `_WindowsLockFile`, `_open_workspace_lock_file_windows`,
`_open_workspace_lock_file`, `_workspace_thread_lock`, `workspace_lock`.

In `__init__.py`, replace the moved block with the re-export (private names included — external patchers
target them today):

```python
from memoria_vault.runtime.state.workspace_lock import (
    _open_workspace_lock_file,
    _open_workspace_lock_file_windows,
    _workspace_lock_key,
    _workspace_thread_lock,
    workspace_lock,
)
```

Then remove imports `__init__.py` no longer uses (`ctypes`, `stat`, and the `fcntl`/`msvcrt` block if nothing
else references them) — `ruff check src/memoria_vault/runtime/state/` reports exactly which; delete what it
flags, nothing more.

Insurance against a stale coupling claim: if the first suite run raises `NameError` on a lock-private name
(`_WORKSPACE_LOCKS`, `_WORKSPACE_LOCK_DEPTH`, …), the `__init__` remainder referenced it and the audit's
zero-coupling measurement had drifted — add that name to the re-export list rather than moving code back.

- [ ] **Step 3: Repoint the three source-as-text tests**

These read `state.py` as a file and raise `FileNotFoundError` the moment it is a package (audit §4.3). The
claims are about *all* of state's source, so read the package:

In `tests/test_package_spine.py`, both readers:

```python
def _state_source() -> str:
    state_dir = ROOT / "src/memoria_vault/runtime/state"
    return "\n".join(
        p.read_text(encoding="utf-8") for p in sorted(state_dir.glob("*.py"))
    )
```

- `test_runtime_sqlite_schema_is_packaged_resource`: `source = _state_source()` (assertions unchanged).
- `test_retired_citation_source_ref_helpers_are_absent`: `source = _state_source()`.

In `tests/test_schema_version.py::test_state_has_no_schema_migration_ladder`, same substitution (define the
same `_state_source()` helper locally there — two lines beat a cross-file test import).

- [ ] **Step 4: Enumerate and retarget monkeypatch sites, with a kill-check each**

```bash
grep -rn "monkeypatch.*state.*\(workspace_lock\|_open_workspace\|_workspace_thread\|_workspace_lock_key\)" tests/
```

For each hit: retarget the patch to the submodule —

```python
from memoria_vault.runtime.state import workspace_lock as state_lock
monkeypatch.setattr(state_lock, "_open_workspace_lock_file", fake_open)
```

— then **kill-check it**: with the patch in place, temporarily invert the behavior the test asserts (or run
the patched function directly) and confirm the test *fails*; restore. A retargeted patch that no test can
fail on is the vacuous pass the audit budgeted for (its two named examples, `state.safe_filename` and
`state.read_event_log`, are *not* moved by this task — `safe_filename` is imported from `runtime.paths` and
`read_event_log` stays in `__init__` — so any hit outside the lock names is out of scope here).

If the grep returns zero hits, record that in the commit message and move on — do not invent retargets.

- [ ] **Step 5: Prove the package ships and behaves**

Run: `python3 scripts/checks/wheel_gate.py` → `wheel-gate: OK` (the new `state/` dir ships; the schema
resource still resolves — `files("memoria_vault.runtime")` is untouched since `schema.sql` did not move).
Run: `PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 python -m pytest tests/test_package_spine.py tests/test_schema_version.py tests/test_journal_trust.py tests/test_worker_queue.py tests/test_backup_restore.py tests/test_dotted_target_literals.py -q`
Expected: PASS.

- [ ] **Step 6: Full gate, goldens check, then commit**

Run: `PYTEST_XDIST_AUTO_NUM_WORKERS=2 python scripts/verify` → `verify: OK`;
`git status --porcelain tests/fixtures/floor/goldens/` → empty.

```bash
git add src/memoria_vault/runtime/state tests/test_package_spine.py tests/test_schema_version.py
# plus any retargeted test files from step 4
git commit -m "state: become a package; extract the cross-process workspace lock"
```

---

### Task 7: Extract `state/markdown.py` — the masking and evidence-marker block

Stage 5, second half: the audit's single highest-value change (§5.1 — "worth doing even if everything else
here is abandoned"). The block is `__init__.py` lines 3604–4783 in pre-task-6 numbering (`_mask_markdown_code`
through `evidence_markers_from_markdown`, ending immediately before `resolve_concept_id`), plus the
markdown/marker regex constants at former lines 67–100 (`_DIRECT_EVIDENCE_MARKER_RE` …
`_MAX_YAML_FRONTMATTER_INDENT`) and the `EvidenceMarker` import. Pure text processing — zero SQLite. Public
surface used outside `state`: `markdown_code_literals_masked`, `markdown_visible_code_literals_masked`,
`markdown_citation_visibility_is_ambiguous`, `evidence_markers_from_markdown`,
`direct_evidence_marker_spans_from_markdown` (readers: `runtime/knowledge.py`, `tests/test_mc_hash_binding.py`,
`tests/test_export_acceptance.py` — all via `state.` attribute access, so re-exports cover them).

**Files:**
- Create: `src/memoria_vault/runtime/state/markdown.py`
- Modify: `src/memoria_vault/runtime/state/__init__.py`
- Modify: any test that monkeypatches a moved name (enumerated in step 4)

**Interfaces:**
- Consumes: task 6's package shape and its test repointing (the `_state_source()` readers already scan the
  whole `state/` dir, so this task needs no test-path edits).
- Produces: `memoria_vault.runtime.state.markdown` exposing the five public functions above plus the private
  helpers the `__init__` remainder still calls (exact list produced by the closure script in step 1).

- [ ] **Step 1: Compute the block's closure before cutting anything**

The audit claims the block references zero module-level names defined outside its ranges; line numbers have
drifted across a hundred merges, so **measure, don't trust**. Run this from the repo root:

```python
# scratch: block_closure.py -- run with: python3 block_closure.py
"""Report both directions of coupling for a named block of state/__init__.py."""
import ast
from pathlib import Path

SRC = Path("src/memoria_vault/runtime/state/__init__.py")
FIRST, LAST = "_mask_markdown_code", "evidence_markers_from_markdown"
CONSTANTS_FIRST, CONSTANTS_LAST = "_DIRECT_EVIDENCE_MARKER_RE", "_MAX_YAML_FRONTMATTER_INDENT"

tree = ast.parse(SRC.read_text(encoding="utf-8"))
spans, order = {}, []
for node in tree.body:
    names = []
    if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
        names = [node.name]
    elif isinstance(node, ast.Assign):
        names = [t.id for t in node.targets if isinstance(t, ast.Name)]
    for n in names:
        spans[n] = node
        order.append(n)

def block(first, last):
    i, j = order.index(first), order.index(last)
    return set(order[i : j + 1])

moved = block(FIRST, LAST) | block(CONSTANTS_FIRST, CONSTANTS_LAST)
module_names = set(order)

outward, inward = set(), set()
for name in order:
    refs = {
        n.id
        for n in ast.walk(spans[name])
        if isinstance(n, ast.Name) and isinstance(n.ctx, ast.Load)
    } & module_names
    if name in moved:
        outward |= refs - moved  # what the block needs from the remainder
    else:
        inward |= refs & moved  # what the remainder needs from the block

print("MOVED SYMBOLS:", len(moved))
print("BLOCK -> REMAINDER (must be empty or imports-only):", sorted(outward))
print("REMAINDER -> BLOCK (the __init__ re-import list):", sorted(inward))
```

Expected: `BLOCK -> REMAINDER` empty (the audit's claim — if it names anything, that symbol moves too or the
cut line shifts; stop and re-derive before proceeding). `REMAINDER -> BLOCK` is the exact list `__init__.py`
must import from `.markdown` — expect the five public names plus privates such as the marker regexes used by
`_evidence_marker_rows` and the masking helpers used by `_block_canonical_text_from_text`.

- [ ] **Step 2: Cut the block**

Create `src/memoria_vault/runtime/state/markdown.py` with: a docstring
(`"""Markdown masking and evidence-marker extraction. Pure text; zero SQLite."""`), imports `re` plus the
existing `EvidenceMarker` (and sibling names) import from `memoria_vault.runtime.evidence` and whatever
`content_security` names the closure script showed the block loading — copied from `__init__.py`'s import
block, not rewritten — then the constants block and the function block, moved verbatim.

In `__init__.py`, replace both moved regions with one import:

```python
from memoria_vault.runtime.state.markdown import (  # re-exported surface + internal callers
    # paste REMAINDER -> BLOCK output here, sorted, one per line, plus the five
    # public names if the script did not already list them:
    direct_evidence_marker_spans_from_markdown,
    evidence_markers_from_markdown,
    markdown_citation_visibility_is_ambiguous,
    markdown_code_literals_masked,
    markdown_visible_code_literals_masked,
)
```

Run `ruff check src/memoria_vault/runtime/state/` and remove exactly the imports it flags as unused in
`__init__.py` (`yaml` and several `re`-adjacent names may or may not survive — the remainder still uses `re`;
delete only what ruff names).

- [ ] **Step 3: Re-run the closure script**

Expected: `BLOCK -> REMAINDER` still empty against the *new* `__init__.py` (the moved names are no longer
module-level there, so `MOVED SYMBOLS` drops to 0 and both lists print empty — that is the done signal).

- [ ] **Step 4: Enumerate and retarget monkeypatch sites, kill-check each**

```bash
grep -rn "monkeypatch.*state.*\(mask\|markdown\|evidence_marker\)" tests/
```

Same procedure and same standard as task 6 step 4: retarget to
`from memoria_vault.runtime.state import markdown as state_markdown`, then prove each retargeted patch can
still fail its test. Zero hits → record and move on.

- [ ] **Step 5: Targeted proof, then the whole gate**

Run: `PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 python -m pytest tests/test_mc_hash_binding.py tests/test_export_acceptance.py tests/test_runtime_state.py tests/test_package_spine.py tests/test_dotted_target_literals.py -q`
Expected: PASS.
Run: `python3 scripts/checks/wheel_gate.py` → `wheel-gate: OK`.
Run: `PYTEST_XDIST_AUTO_NUM_WORKERS=2 python scripts/verify` → `verify: OK`;
`git status --porcelain tests/fixtures/floor/goldens/` → empty.

- [ ] **Step 6: Commit**

```bash
git add src/memoria_vault/runtime/state
# plus any retargeted test files from step 4
git commit -m "state: extract markdown masking and evidence-marker extraction into state/markdown.py"
```

---

## Self-review record

- **Spec coverage:** audit stages 1 (task 1), 2 (task 2), 3 (task 3), 4 (tasks 4–5), 5 (tasks 6–7). Stage 6
  deferred and stage 7+ out of scope — stated in Global Constraints with the review's reasoning. Review
  findings folded in: install-and-probe leg (finding 2), nine-directory identifier rule (finding 1),
  attribute-tail resolution + kill tests (finding 5), the docs-skip wiring, and the `.claude/hooks` seeding
  hazard the audit did not name.
- **Known count corrections vs the audit:** 9 implicit dirs (not 7); 19 root-constant files (not 18); the
  inversion fix is a deferred import (not a parameterised seam) because `engine_api` is `main()`-only.
- **Type consistency:** `REPO_ROOT` (task 4) is consumed by task 5's guard; `wheel_gate.py`'s command string
  matches task 1's roster pin; task 6's `_state_source()` covers task 7 without edits; the re-export names in
  tasks 6–7 match the symbol map measured from the tree at `c03d9556`.
