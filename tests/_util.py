"""Helpers for the L1 pytest tree (ADR-44)."""
import importlib.util
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

def load_script(rel: str):
    """Import a hyphenated-name script (e.g. scripts/status-doctor.py) by path."""
    name = Path(rel).stem.replace("-", "_")
    spec = importlib.util.spec_from_file_location(name, ROOT / rel)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


class TestHarness:
    """Minimal pass/fail harness for the extracted L1 tests (ADR-44; formerly _shared.py)."""

    __test__ = False  # tell pytest this is not a test class

    def __init__(self) -> None:
        self.failures = 0
        self.total = 0

    def check(self, name: str, cond: bool) -> None:
        self.total += 1
        self.failures += not cond
        print(f"  {'PASS' if cond else 'FAIL'}  {name}")

    def summary(self, label: str = "") -> int:
        tag = f" [{label}]" if label else ""
        status = "FAILED" if self.failures else "OK"
        print(f"\n{status}: {self.failures} failing check(s){tag}.")
        return self.failures
