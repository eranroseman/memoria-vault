"""The pre-commit hook validates staged alpha.11 Concepts against their schema."""

from pathlib import Path

from memoria_vault.runtime.subsystems.integrity.linter import precommit_check


def _vault(tmp_path: Path) -> Path:
    for rel in ("catalog/sources/s1", "knowledge/notes", "system", "inbox"):
        (tmp_path / rel).mkdir(parents=True)
    return tmp_path


def test_clean_note_passes(tmp_path):
    vault = _vault(tmp_path)
    (vault / "knowledge/notes/n.md").write_text(
        "---\ntype: note\nid: notes/n\ncheck_status: unchecked\n"
        "standing: current\nlinks: {}\ntitle: T\n---\nBody.\n",
        encoding="utf-8",
    )
    assert precommit_check.check_paths(vault, ["knowledge/notes/n.md"]) == []


def test_schema_violation_blocks(tmp_path):
    vault = _vault(tmp_path)
    (vault / "catalog/sources/s1/source.md").write_text(
        "---\ntype: source\ncheck_status: pending\ntitle: T\n---\nBody.\n",
        encoding="utf-8",
    )
    errors = precommit_check.check_paths(vault, ["catalog/sources/s1/source.md"])
    assert any("check_status" in error for error in errors)
    assert any("description" in error for error in errors)
    assert any("source_id" in error for error in errors)


def test_unknown_type_blocks(tmp_path):
    vault = _vault(tmp_path)
    (vault / "knowledge/notes/odd.md").write_text(
        "---\ntype: reference-note\ncheck_status: checked\n---\n",
        encoding="utf-8",
    )
    errors = precommit_check.check_paths(vault, ["knowledge/notes/odd.md"])
    assert any("unknown type" in e for e in errors)


def test_untyped_infra_and_outside_paths_exempt(tmp_path):
    vault = _vault(tmp_path)
    (vault / "system/vocab.md").write_text("---\nfoo: bar\n---\n", encoding="utf-8")
    assert precommit_check.check_paths(vault, ["system/vocab.md"]) == []
    assert precommit_check.check_paths(vault, ["/etc/hostname"]) == []


def test_untyped_inbox_attention_projection_exempt(tmp_path):
    vault = _vault(tmp_path)
    (vault / "inbox/gap-map-corpus.md").write_text(
        "---\ntitle: Gap\nprojection: attention\nattention_kind: gap\nattention_status: open\n---\n",
        encoding="utf-8",
    )
    assert precommit_check.check_paths(vault, ["inbox/gap-map-corpus.md"]) == []


def test_hook_script_ships_executable():
    hook = Path(__file__).resolve().parent.parent / "vault-template/.githooks/pre-commit"
    assert hook.is_file()
    assert hook.stat().st_mode & 0o111, "pre-commit hook must be executable"


def test_hidden_runtime_exempt(tmp_path):
    vault = _vault(tmp_path)
    (vault / ".memoria/golden/system/templates").mkdir(parents=True)
    tpl = vault / ".memoria/golden/system/templates/note.md"
    tpl.write_text("---\ntype: note\ncreated: {{DATE}}\n---\n", encoding="utf-8")
    assert precommit_check.check_paths(vault, [".memoria/golden/system/templates/note.md"]) == []
