#!/usr/bin/env python3
"""precommit_check — schema-validate staged documents (the D50 pre-commit hook).

Called by the pre-commit hook with the staged .md paths. Each typed document must
pass its schema; untyped system infra and vault-root nav pages are exempt,
mirroring the Linter's frontmatter_schema_check. Exit 1 blocks the commit.

Usage: precommit_check.py --vault V PATH ...
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from memoria_vault.runtime.subsystems.integrity.linter.detectors import (
    is_untyped_infra,
    parse_frontmatter,
)
from memoria_vault.runtime.subsystems.lib import schema
from memoria_vault.runtime.vaultio import retired_frontmatter_field_errors


def check_paths(vault: Path, paths: list[str]) -> list[str]:
    """Return error strings for staged documents that fail their schema."""
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
            continue  # hidden runtime (golden copies, profile SKILLs) — never typed documents
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
        for err in retired_frontmatter_field_errors(fm):
            errors.append(f"{rel}: {ntype}: {err}")
        for err in schema.validate_frontmatter(fm, sc):
            errors.append(f"{rel}: {ntype}: {err}")
    return errors


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--vault", type=Path)
    ap.add_argument("paths", nargs="*")
    args = ap.parse_args()
    if not args.vault:
        ap.error("provide --vault")
    errors = check_paths(args.vault, args.paths)
    for e in errors:
        print(f"  ✗ {e}")
    if errors:
        print(
            f"pre-commit: {len(errors)} schema error(s) — commit blocked "
            "(fix the notes, or commit non-vault changes separately)"
        )
        sys.exit(1)


if __name__ == "__main__":
    main()
