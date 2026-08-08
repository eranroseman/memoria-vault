"""Published docs must not cite repo files that no longer exist."""

from __future__ import annotations

from pathlib import Path

import pytest

from scripts.checks.doc_cited_paths import find_violations

pytestmark = pytest.mark.static


def _write_root(tmp_path: Path, page: str, *, rel: str = "docs/guide.md") -> Path:
    """A tiny repo: a real `src/` file, a real `docs/` page, plus `page`."""
    root = tmp_path / "repo"
    (root / "src/memoria_vault").mkdir(parents=True)
    (root / "src/memoria_vault/cli.py").write_text("x\n", encoding="utf-8")
    (root / "docs/reference").mkdir(parents=True)
    (root / "docs/reference/glossary.md").write_text("x\n", encoding="utf-8")
    target = root / rel
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(page, encoding="utf-8")
    return root


def test_missing_src_citation_fails(tmp_path: Path) -> None:
    root = _write_root(tmp_path, "The writer lives in `src/memoria_vault/gone.py`.\n")

    violations = find_violations(root)

    assert [(v.file, v.line, v.path) for v in violations] == [
        ("docs/guide.md", 1, "src/memoria_vault/gone.py")
    ]


def test_existing_citation_is_clean(tmp_path: Path) -> None:
    root = _write_root(tmp_path, "The entry point is `src/memoria_vault/cli.py`.\n")

    assert find_violations(root) == []


def test_symbol_suffix_is_stripped_before_the_existence_check(tmp_path: Path) -> None:
    root = _write_root(tmp_path, "See `src/memoria_vault/cli.py::main` for the parser.\n")

    assert find_violations(root) == []


def test_symbol_suffix_does_not_excuse_a_missing_file(tmp_path: Path) -> None:
    root = _write_root(tmp_path, "See `src/memoria_vault/gone.py::main`.\n")

    assert [v.path for v in find_violations(root)] == ["src/memoria_vault/gone.py"]


def test_directory_citation_with_trailing_slash_is_clean(tmp_path: Path) -> None:
    root = _write_root(tmp_path, "Seeds live under `src/memoria_vault/`.\n")

    assert find_violations(root) == []


def test_directory_citation_with_trailing_slash_can_still_fail(tmp_path: Path) -> None:
    root = _write_root(tmp_path, "Seeds live under `src/memoria_vault/nowhere/`.\n")

    assert [v.path for v in find_violations(root)] == ["src/memoria_vault/nowhere"]


def test_glob_and_placeholder_spans_are_not_citations(tmp_path: Path) -> None:
    root = _write_root(
        tmp_path,
        "Globs: `src/memoria_vault/**`, `tests/test_*.py`, `docs/a?.md`.\n"
        "Placeholders: `docs/<area>/page.md`, `src/{pkg}/mod.py`.\n"
        "Prose: `docs/guide.md and more`.\n",
    )

    assert find_violations(root) == []


def test_fenced_code_blocks_are_exempt(tmp_path: Path) -> None:
    root = _write_root(
        tmp_path,
        "Run it:\n\n```bash\npython3 src/memoria_vault/gone.py\n"
        "echo `src/memoria_vault/gone.py`\n```\n\nDone.\n",
    )

    assert find_violations(root) == []


def test_docs_to_docs_citation_is_checked(tmp_path: Path) -> None:
    root = _write_root(
        tmp_path,
        "Terms live in `docs/reference/glossary.md`, not `docs/reference/lexicon.md`.\n",
    )

    assert [(v.line, v.path) for v in find_violations(root)] == [(1, "docs/reference/lexicon.md")]


def test_superpowers_pages_are_not_part_of_the_published_set(tmp_path: Path) -> None:
    root = _write_root(
        tmp_path,
        "Working note citing `src/memoria_vault/gone.py`.\n",
        rel="docs/superpowers/plans/plan.md",
    )

    assert find_violations(root) == []


def test_line_numbers_track_the_page(tmp_path: Path) -> None:
    root = _write_root(
        tmp_path,
        "intro\n\n`src/memoria_vault/cli.py` is fine.\n\n`scripts/gone.py` is not.\n",
    )

    assert [(v.line, v.path) for v in find_violations(root)] == [(5, "scripts/gone.py")]
