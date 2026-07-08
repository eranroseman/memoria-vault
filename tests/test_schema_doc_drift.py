"""Schema-documentation drift tests."""

from __future__ import annotations

from pathlib import Path

from scripts.checks.schema_doc_drift import check_schema_docs


def _write_fixture(root: Path, *, enum_values: str = "claim, question") -> tuple[Path, Path]:
    schemas = root / "schemas"
    docs = root / "docs"
    (schemas / "types").mkdir(parents=True)
    docs.mkdir()
    (schemas / "types" / "note.yaml").write_text(
        "type: note\n"
        "category: notes\n"
        "gated: false\n"
        "enums:\n"
        "  mode: [claim, question]\n"
        "required:\n"
        "  type: literal:note\n"
        "  title: str\n"
        "optional:\n"
        "  mode: enum:mode\n",
        encoding="utf-8",
    )
    (docs / "document-types.md").write_text(
        "The current schema defines 1 document type: `note`.\n",
        encoding="utf-8",
    )
    (docs / "frontmatter.md").write_text(
        "```yaml\n"
        "type: note\n"
        "category: notes\n"
        "gated: false\n"
        "enums:\n"
        f"  mode: [{enum_values}]\n"
        "required:\n"
        "  type: literal:note\n"
        "  title: str\n"
        "optional:\n"
        "  mode: enum:mode\n"
        "```\n",
        encoding="utf-8",
    )
    return schemas, docs


def test_schema_doc_lint_passes_on_aligned_synthetic_docs(tmp_path: Path) -> None:
    schemas, docs = _write_fixture(tmp_path)

    assert check_schema_docs(schemas, docs) == []


def test_schema_doc_lint_fails_on_seeded_enum_mismatch(tmp_path: Path) -> None:
    schemas, docs = _write_fixture(tmp_path, enum_values="claim, hypothesis")

    errors = check_schema_docs(schemas, docs)

    assert any("note.enums.mode" in error for error in errors)


def test_schema_doc_lint_fails_on_seeded_type_roster_mismatch(tmp_path: Path) -> None:
    schemas, docs = _write_fixture(tmp_path)
    (docs / "document-types.md").write_text(
        "The current schema defines 2 document types: `note`, `hub`.\n",
        encoding="utf-8",
    )

    errors = check_schema_docs(schemas, docs)

    assert any("document type count" in error for error in errors)
    assert any("document types" in error for error in errors)
