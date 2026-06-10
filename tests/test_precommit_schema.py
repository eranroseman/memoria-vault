"""The D50 commit gate: staged typed notes must pass their schema."""

from pathlib import Path

import precommit_check


def _vault(tmp_path: Path) -> Path:
    (tmp_path / "notes/claims").mkdir(parents=True)
    (tmp_path / "system").mkdir()
    return tmp_path


def test_clean_note_passes(tmp_path):
    v = _vault(tmp_path)
    (v / "notes/claims/c.md").write_text(
        "---\ntype: claim\nlifecycle: current\ntitle: T\nmaturity: seedling\n"
        "sources: ['@x2020']\n---\nBody.\n", encoding="utf-8")
    assert precommit_check.check_paths(v, ["notes/claims/c.md"]) == []


def test_schema_violation_blocks(tmp_path):
    v = _vault(tmp_path)
    # claims never start in `proposed` (ADR-50 subset), and required fields missing
    (v / "notes/claims/bad.md").write_text(
        "---\ntype: claim\nlifecycle: proposed\ntitle: T\n---\nBody.\n", encoding="utf-8")
    errors = precommit_check.check_paths(v, ["notes/claims/bad.md"])
    assert any("lifecycle" in e for e in errors)
    assert any("maturity" in e for e in errors)


def test_unknown_type_blocks(tmp_path):
    v = _vault(tmp_path)
    (v / "notes/claims/odd.md").write_text(
        "---\ntype: reference-note\nlifecycle: current\n---\n", encoding="utf-8")
    errors = precommit_check.check_paths(v, ["notes/claims/odd.md"])
    assert any("unknown type" in e for e in errors)


def test_untyped_infra_and_outside_paths_exempt(tmp_path):
    v = _vault(tmp_path)
    (v / "system/vocab.md").write_text("---\nfoo: bar\n---\n", encoding="utf-8")
    assert precommit_check.check_paths(v, ["system/vocab.md"]) == []
    assert precommit_check.check_paths(v, ["/etc/hostname"]) == []


def test_hook_script_ships_executable():
    hook = Path(__file__).resolve().parent.parent / "src/.memoria/engines/linter/pre-commit"
    assert hook.is_file()
    assert hook.stat().st_mode & 0o111, "pre-commit hook must be executable"


def test_hidden_runtime_exempt(tmp_path):
    """Golden copies and profile files under .memoria/ are never gated."""
    v = _vault(tmp_path)
    (v / ".memoria/golden/system/templates").mkdir(parents=True)
    tpl = v / ".memoria/golden/system/templates/claim.md"
    tpl.write_text("---\ntype: claim\ncreated: {{DATE}}\n---\n", encoding="utf-8")
    assert precommit_check.check_paths(v, [".memoria/golden/system/templates/claim.md"]) == []
