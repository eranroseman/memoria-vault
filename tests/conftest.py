"""Wire the module dirs onto sys.path so tests can import the modules under test.
(ADR-44: L1 tests live here, not inline in the shipped modules.)"""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
_DIRS = [
    "src/.memoria",
    "src/.memoria/mcp",
    "src/.memoria/engines/lib",
    "src/.memoria/engines/ingest",
    "src/.memoria/engines/sweeps",
    "src/.memoria/engines/linter",
    "scripts",
    ".github/scripts",
]
for _d in _DIRS:
    _p = str(ROOT / _d)
    if _p not in sys.path:
        sys.path.insert(0, _p)
