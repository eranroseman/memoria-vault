#!/usr/bin/env python3
"""Build the wheel and prove the installed artifact works.

Named failure (#1689; audit §2.0): nothing in the gate exercised packaging or
the installed entry point, so a dropped package, a stale package-data glob, a
moved data file, or a broken console script all shipped green. This gate
builds the wheel with the repo's own build backend, asserts every shippable
source file is in it (and nothing else), installs it into a scratch venv, and
probes the three bindings the repo relies on: the ``memoria`` entry point,
the packaged ``schema.sql`` resource, and the deepest ``-m``-published
module path.

POSIX-only paths (``bin/``): verify runs on Linux locally and in CI; the
PowerShell leg of verify covers the one Windows artifact separately.
"""

from __future__ import annotations

import shutil
import subprocess
import sys
import tempfile
import tomllib
import venv
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / "src" / "memoria_vault"

# Non-packaging directories to skip when copying ROOT into the tempdir for a
# pristine build (see _build_wheel). Root-scoped only -- see
# _ignore_root_only for why a name match can't apply at every depth.
_COPY_SKIP_AT_ROOT = {
    "build",
    ".git",
    ".venv",
    "test-vault",
    "node_modules",
    ".worktrees",
    ".claude",
    ".superpowers",
    "docs",
    "tests",
    "design-history",
    ".pytest_cache",
    ".ruff_cache",
}

# The deepest documented ``python -m`` path (audit §4.1). If this import works
# from the installed wheel, the whole subsystems subtree shipped.
_DEEP_MODULE = "memoria_vault.runtime.subsystems.integrity.linter.detectors"


def _expected_members() -> set[str]:
    """Every tracked file under src/memoria_vault/ that must appear in the wheel.

    Everything ships: .py by packaging, everything else by a package-data
    glob — and a source file matching *no* glob is a bug this gate exists to
    catch (``memoria init`` seeds from packaged resources, so an unshipped
    seed file breaks fresh vaults, silently).

    ``git ls-files`` rather than a working-tree walk: an untracked scratch
    file under src/ (a merge-conflict ``.orig``, an editor backup, a
    ``.DS_Store``) is not shippable source and must never turn this gate red
    for a packaging reason it isn't.
    """
    listing = subprocess.run(
        ["git", "ls-files", "--", SRC.relative_to(ROOT).as_posix()],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=True,
    )
    prefix = SRC.relative_to(ROOT).as_posix() + "/"
    # splitlines, not split(): some package-data filenames contain spaces
    # (e.g. "Start here.md"), and git ls-files separates entries by newline.
    expected = {
        "memoria_vault/" + line.removeprefix(prefix) for line in listing.stdout.splitlines() if line
    }
    if not expected:
        sys.exit("wheel-gate: git ls-files returned nothing under src/memoria_vault/")
    return expected


def _ignore_root_only(path: str, names: list[str]) -> set[str]:
    """copytree ignore callback: skip dev-only dirs, but only at ROOT itself.

    ``src/memoria_vault/product/workspace_seed/.claude/`` is a package-data
    directory -- the packaged seed ships a ``.claude/`` for fresh vaults --
    so a bare name match against ``.claude`` (or ``docs``, ``tests``, ...)
    would silently drop it from the pristine copy at every depth, which is
    the exact class of self-inflicted packaging bug this rebuild exists to
    stop. Caches and egg-info are safe to skip anywhere; nothing packaging
    reads ever lives inside one.
    """
    skip = {n for n in names if n == "__pycache__" or n.endswith(".egg-info")}
    if Path(path) == ROOT:
        skip |= _COPY_SKIP_AT_ROOT & set(names)
    return skip


def _build_wheel(tmp: Path) -> Path:
    # Build from a pristine copy, not in-tree: `pip wheel ROOT` leaves
    # build/lib/ behind, and setuptools' build_py copies into it but never
    # prunes it -- so on a second run, a file that stops being covered by a
    # package or package-data rule still ships from the stale copy and
    # _check_contents sees it as present. Nothing built in-tree means
    # nothing to go stale.
    source = tmp / "source"
    shutil.copytree(ROOT, source, ignore=_ignore_root_only)
    run = subprocess.run(
        [
            sys.executable,
            "-m",
            "pip",
            "wheel",
            str(source),
            "--no-deps",
            "--no-build-isolation",
            "--wheel-dir",
            str(tmp),
        ],
        capture_output=True,
        text=True,
    )
    if run.returncode != 0:
        sys.exit(f"wheel-gate: build failed:\n{run.stdout}\n{run.stderr}")
    wheels = list(tmp.glob("memoria_vault-*.whl"))
    if len(wheels) != 1:
        sys.exit(f"wheel-gate: expected exactly one wheel, found {sorted(w.name for w in wheels)}")
    return wheels[0]


def _check_contents(wheel: Path) -> None:
    expected = _expected_members()
    with zipfile.ZipFile(wheel) as zf:
        shipped = set(zf.namelist())

    missing = sorted(m for m in expected if m not in shipped)
    if missing:
        sys.exit(
            "wheel-gate: source files missing from the wheel "
            "(package or package-data gap):\n  " + "\n  ".join(missing)
        )

    # The reverse leg: the wheel must carry nothing under memoria_vault/ that
    # isn't tracked source. Catches an overbroad package-data glob and, just
    # as importantly, makes a stale build/lib/ leak self-announcing instead
    # of silently masking the leg above.
    extra = sorted(m for m in shipped if m.startswith("memoria_vault/") and m not in expected)
    if extra:
        sys.exit(
            "wheel-gate: wheel ships files with no tracked source under "
            "src/memoria_vault/ (stale build artifact or overbroad "
            "package-data glob):\n  " + "\n  ".join(extra)
        )


def _run_or_exit(cmd: list[str], *, step: str) -> str:
    """Run `cmd`, exiting in this file's own idiom instead of a raw traceback.

    Catches OSError as well as a nonzero return code: a missing entry-point
    script (e.g. a renamed ``[project.scripts]`` binary) makes Popen itself
    raise FileNotFoundError before there is any CompletedProcess to check.
    """
    try:
        result = subprocess.run(cmd, capture_output=True, text=True)
    except OSError as exc:
        sys.exit(f"wheel-gate: {step} failed: {exc}")
    if result.returncode != 0:
        sys.exit(f"wheel-gate: {step} failed:\n{result.stdout}\n{result.stderr}")
    return result.stdout


def _probe_install(wheel: Path, tmp: Path) -> None:
    venv_dir = tmp / "venv"
    # system-site-packages so third-party deps resolve from the dev env while
    # memoria_vault itself comes from the wheel; the __file__ assert below is
    # what proves the wheel copy shadows any editable install.
    venv.EnvBuilder(with_pip=True, system_site_packages=True).create(venv_dir)
    py = venv_dir / "bin" / "python"
    _run_or_exit(
        [str(py), "-m", "pip", "install", "--quiet", "--no-deps", "--no-index", str(wheel)],
        step="installing the wheel",
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
    _run_or_exit([str(py), "-c", probe], step="probing the installed package")
    out = _run_or_exit(
        [str(venv_dir / "bin" / "memoria"), "--version"],
        step="running the memoria entry point",
    ).strip()
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
