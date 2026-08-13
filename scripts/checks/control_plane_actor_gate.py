"""Fail when the published Actor Authority Guard table drifts from the shipped roster.

`docs/reference/control-and-policy/control-plane.md` is the published statement
of which worker operations are actor-reserved; the live roster is
`PROTECTED_OPERATION_ACTORS` in `worker.py`. The table drifted twice in one
release (#1594), and a reader auditing the write perimeter reasons from it --
so the two surfaces are pinned equal.
"""

from __future__ import annotations

import contextlib
import re
import sys
from collections.abc import Iterator
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DOC_REL = "docs/reference/control-and-policy/control-plane.md"
HEADING = "## Actor Authority Guard"


def documented_rosters(text: str) -> dict[str, set[str]]:
    """Parse the guard section's actor rows into {actor: {operation, ...}}."""
    start = text.index(HEADING)
    end = text.find("\n## ", start + len(HEADING))
    section = text[start : end if end != -1 else len(text)]
    rosters: dict[str, set[str]] = {}
    for match in re.finditer(r"^\| `([a-z]+)` \| (.+) \|$", section, flags=re.MULTILINE):
        rosters[match.group(1)] = set(re.findall(r"`([a-z0-9-]+)`", match.group(2)))
    return rosters


@contextlib.contextmanager
def _importable(source_root: Path) -> Iterator[None]:
    """Put `source_root` on `sys.path` for one import, then take it back off.

    Run as a bare script -- how `scripts/verify` invokes this gate -- `sys.path`
    has no worktree-relative `src` on it, only whatever editable install sits in
    site-packages. In a git-worktree checkout that install can point at a
    different worktree's `src` entirely (each worktree has its own `src`, but
    they share one venv), so an unqualified `import memoria_vault` would grade
    the wrong `worker.py` with no error to signal it. See `doc_claims_gate.py`'s
    `_importable` for the pytest-side reason this stays scoped to one import
    instead of a permanent `sys.path.insert`.
    """
    entry = str(source_root)
    sys.path.insert(0, entry)
    try:
        yield
    finally:
        with contextlib.suppress(ValueError):
            sys.path.remove(entry)


def shipped_rosters() -> dict[str, set[str]]:
    with _importable(ROOT / "src"):
        from memoria_vault.runtime.worker import PROTECTED_OPERATION_ACTORS

    shipped: dict[str, set[str]] = {}
    for operation_id, actor in PROTECTED_OPERATION_ACTORS.items():
        shipped.setdefault(actor, set()).add(operation_id)
    return shipped


def drift_errors(documented: dict[str, set[str]], shipped: dict[str, set[str]]) -> list[str]:
    errors: list[str] = []
    for actor in sorted(set(documented) | set(shipped)):
        for missing in sorted(shipped.get(actor, set()) - documented.get(actor, set())):
            errors.append(f"{DOC_REL}: `{actor}` row is missing `{missing}`")
        for stale in sorted(documented.get(actor, set()) - shipped.get(actor, set())):
            errors.append(
                f"{DOC_REL}: `{actor}` row lists `{stale}`, "
                "which is not in PROTECTED_OPERATION_ACTORS"
            )
    return errors


def main() -> int:
    text = (ROOT / DOC_REL).read_text(encoding="utf-8")
    errors = drift_errors(documented_rosters(text), shipped_rosters())
    for error in errors:
        print(error, file=sys.stderr)
    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
