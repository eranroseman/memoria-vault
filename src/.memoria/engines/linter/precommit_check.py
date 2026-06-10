#!/usr/bin/env python3
"""precommit_check — schema-validate staged notes (the D50 commit gate).

Called by the pre-commit hook with the staged .md paths. Each typed note must
pass its schema; untyped system infra and vault-root nav pages are exempt,
mirroring the Linter's frontmatter_schema_check. Exit 1 blocks the commit.

Usage: precommit_check.py --vault V [--self-test] PATH ...
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

_HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(_HERE))
sys.path.insert(0, str(_HERE.parent / "lib"))

import schema  # noqa: E402
from detectors import is_untyped_infra, parse_frontmatter  # noqa: E402


def check_paths(vault: Path, paths: list[str]) -> list[str]:
    """Return error strings for staged notes that fail their schema."""
    types = schema.load_types()
    errors: list[str] = []
    for raw in paths:
        p = (vault / raw) if not Path(raw).is_absolute() else Path(raw)
        try:
            rel = p.resolve().relative_to(vault.resolve()).as_posix()
        except ValueError:
            continue  # outside the vault (repo docs etc.) — not gated here
        if p.suffix != ".md" or not p.is_file():
            continue
        if rel.startswith((".memoria/", ".obsidian/")):
            continue  # hidden runtime (golden copies, profile SKILLs) — never typed notes
        if is_untyped_infra(rel) or "/" not in rel:
            continue
        fm = parse_frontmatter(p.read_text(encoding="utf-8"))
        if not fm:
            continue
        ntype = fm.get("type")
        if not ntype:
            errors.append(f"{rel}: missing required 'type' field")
            continue
        sc = types.get(ntype)
        if sc is None:
            errors.append(f"{rel}: unknown type '{ntype}'")
            continue
        for err in schema.validate_frontmatter(fm, sc):
            errors.append(f"{rel}: {ntype}: {err}")
    return errors


def _self_test() -> int:
    import tempfile
    failures = 0

    def ck(label: str, ok: bool) -> None:
        nonlocal failures
        print(("  ok " if ok else "  FAIL ") + label)
        if not ok:
            failures += 1

    with tempfile.TemporaryDirectory() as td:
        v = Path(td)
        (v / "notes/claims").mkdir(parents=True)
        good = v / "notes/claims/good.md"
        good.write_text("---\ntype: claim\nlifecycle: current\ntitle: T\n"
                        "maturity: seedling\nsources: ['@x2020']\n---\nBody.\n",
                        encoding="utf-8")
        bad = v / "notes/claims/bad.md"
        bad.write_text("---\ntype: claim\nlifecycle: proposed\ntitle: T\n---\nBody.\n",
                       encoding="utf-8")
        (v / "system").mkdir()
        infra = v / "system/vocab.md"
        infra.write_text("---\nnothing: here\n---\n", encoding="utf-8")
        ck("clean note passes", check_paths(v, ["notes/claims/good.md"]) == [])
        errs = check_paths(v, ["notes/claims/bad.md"])
        ck("invalid lifecycle + missing fields block", len(errs) >= 2)
        ck("system infra exempt", check_paths(v, ["system/vocab.md"]) == [])
        ck("outside-vault path skipped", check_paths(v, ["/etc/hostname"]) == [])
    print("self-test:", "PASS" if failures == 0 else f"{failures} FAILURE(S)")
    return 1 if failures else 0


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--vault", type=Path)
    ap.add_argument("--self-test", action="store_true")
    ap.add_argument("paths", nargs="*")
    args = ap.parse_args()
    if args.self_test:
        sys.exit(_self_test())
    if not args.vault:
        ap.error("provide --vault")
    errors = check_paths(args.vault, args.paths)
    for e in errors:
        print(f"  ✗ {e}")
    if errors:
        print(f"pre-commit: {len(errors)} schema error(s) — commit blocked "
              "(fix the notes, or commit non-vault changes separately)")
        sys.exit(1)


if __name__ == "__main__":
    main()
