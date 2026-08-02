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
