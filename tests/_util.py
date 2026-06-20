"""Helpers for the L1 pytest tree (ADR-44)."""


class CheckHarness:
    """Minimal pass/fail harness for the extracted L1 tests (ADR-44)."""

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
