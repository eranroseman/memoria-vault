"""Positive and negative cases for the checked-terminology gate.

Before this file, all six mutation sites in the gate survived the whole suite
-- including inverting the scan-root existence check, which makes the gate
scan nothing and print ok forever. Each test below names the mutation class
it kills.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from scripts.checks import checked_terminology_gate as gate

pytestmark = pytest.mark.static


def _tree(tmp_path: Path, files: dict[str, str]) -> Path:
    for rel, text in files.items():
        path = tmp_path / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")
    return tmp_path


def test_forward_order_violation_is_found(tmp_path: Path) -> None:
    """Kills: a never-matching first pattern, and the scan-root existence
    inversion (an existing root that gets skipped finds nothing)."""
    base = _tree(tmp_path, {"docs/a.md": "intro\nA checked concept is approved by the PI.\n"})

    assert gate.errors(base) == ["docs/a.md:2: checked must not mean approved/verified/trusted"]


def test_reversed_order_violation_is_found(tmp_path: Path) -> None:
    """Kills a dropped second pattern: bad word before 'checked'."""
    base = _tree(tmp_path, {"docs/a.md": "Approved once the item is checked.\n"})

    assert len(gate.errors(base)) == 1


def test_clean_wording_produces_no_finding(tmp_path: Path) -> None:
    """Kills a match-everything pattern."""
    base = _tree(
        tmp_path,
        {"docs/a.md": "A checked concept has passed the sha256 read barrier only.\n"},
    )

    assert gate.errors(base) == []


def test_trusted_writer_is_exempt_by_the_lookahead(tmp_path: Path) -> None:
    base = _tree(tmp_path, {"docs/a.md": "Every checked write goes through the trusted-writer.\n"})

    assert gate.errors(base) == []


def test_skip_parts_are_skipped(tmp_path: Path) -> None:
    """Kills an inverted _skip: a violation inside docs/superpowers must not count."""
    base = _tree(
        tmp_path,
        {
            "docs/superpowers/x.md": "checked means approved here, freely.\n",
            "docs/a.md": "clean\n",
        },
    )

    assert gate.errors(base) == []


def test_unrostered_suffixes_are_ignored(tmp_path: Path) -> None:
    base = _tree(tmp_path, {"docs/a.txt": "A checked concept is approved.\n"})

    assert gate.errors(base) == []


def test_a_missing_scan_root_contributes_nothing_but_an_existing_one_scans(
    tmp_path: Path,
) -> None:
    """The exists-check inversion: with only docs/ present, src/ and scripts/
    must be silently absent while docs/ is still genuinely scanned."""
    base = _tree(tmp_path, {"docs/a.md": "A checked concept is a verified concept.\n"})

    findings = gate.errors(base)

    assert len(findings) == 1 and findings[0].startswith("docs/a.md:1:")


def test_the_window_is_one_hundred_characters(tmp_path: Path) -> None:
    """Kills a widened window: the two words 150 chars apart must not match."""
    base = _tree(
        tmp_path,
        {"docs/a.md": "checked " + ("x" * 150) + " approved\n"},
    )

    assert gate.errors(base) == []


def test_matching_is_case_insensitive(tmp_path: Path) -> None:
    base = _tree(tmp_path, {"docs/a.md": "CHECKED items are APPROVED.\n"})

    assert len(gate.errors(base)) == 1
