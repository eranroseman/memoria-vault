"""The pre-commit hook validates staged Concepts against their schema."""

from pathlib import Path

from memoria_vault.runtime.subsystems.integrity.linter import precommit_check
from tests.helpers import WORKSPACE_SEED


def _vault(tmp_path: Path) -> Path:
    for rel in ("notes", "system", "inbox"):
        (tmp_path / rel).mkdir(parents=True)
    return tmp_path


def test_clean_note_passes(tmp_path):
    vault = _vault(tmp_path)
    (vault / "notes/n.md").write_text(
        "---\ntype: note\nid: 01ARZ3NDEKTSV4RRFFQ69G5FAV\n"
        "tags: []\nlinks: {}\ntitle: T\n---\nBody.\n",
        encoding="utf-8",
    )
    assert precommit_check.check_paths(vault, ["notes/n.md"]) == []


def test_generated_note_fields_pass(tmp_path):
    vault = _vault(tmp_path)
    (vault / "notes/n.md").write_text(
        "---\n"
        "type: note\n"
        "id: 01ARZ3NDEKTSV4RRFFQ69G5FAV\n"
        "tags: []\n"
        "links: {}\n"
        "title: T\n"
        "topics: [personal-informatics]\n"
        "work_id: catalog/sources/source-alpha\n"
        "extraction_confidence: medium\n"
        "claim_text: Framing changes which outcomes matter.\n"
        "quote: outcome framing\n"
        "annotation_ref:\n"
        "  selector: paragraph-1\n"
        "---\n"
        "Body.\n",
        encoding="utf-8",
    )
    assert precommit_check.check_paths(vault, ["notes/n.md"]) == []


def test_generated_digest_and_hub_fields_pass(tmp_path):
    vault = _vault(tmp_path)
    (vault / "digests").mkdir(parents=True)
    (vault / "hubs").mkdir(parents=True)
    (vault / "digests/source-alpha.md").write_text(
        "---\n"
        "type: digest\n"
        "id: 01ARZ3NDEKTSV4RRFFQ69G5FAV\n"
        "title: Digest\n"
        "tags: []\n"
        "links: {}\n"
        "work_id: source-alpha\n"
        "---\n"
        "Body.\n",
        encoding="utf-8",
    )
    (vault / "hubs/topic.md").write_text(
        "---\n"
        "type: hub\n"
        "id: 01BRZ3NDEKTSV4RRFFQ69G5FAV\n"
        "title: Topic\n"
        "tags: []\n"
        "links: {}\n"
        "tag: topic\n"
        "---\n"
        "Body.\n",
        encoding="utf-8",
    )
    assert (
        precommit_check.check_paths(
            vault,
            ["digests/source-alpha.md", "hubs/topic.md"],
        )
        == []
    )


def test_schema_violation_blocks(tmp_path):
    vault = _vault(tmp_path)
    (vault / "notes/bad.md").write_text(
        "---\ntype: note\nid: notes/bad\ncheck_status: pending\nlinks: []\ntitle: T\n---\nBody.\n",
        encoding="utf-8",
    )
    errors = precommit_check.check_paths(vault, ["notes/bad.md"])
    assert any("check_status" in error for error in errors)
    assert any("id" in error for error in errors)
    assert any("tags" in error for error in errors)
    assert any("links" in error for error in errors)


def test_declared_frontmatter_field_shape_blocks(tmp_path):
    vault = _vault(tmp_path)
    (vault / "notes/bad.md").write_text(
        "---\ntype: note\nid: 01ARZ3NDEKTSV4RRFFQ69G5FAV\n"
        "tags: []\nlinks: {}\ntitle: T\ntopics: personal-informatics\n---\nBody.\n",
        encoding="utf-8",
    )
    errors = precommit_check.check_paths(vault, ["notes/bad.md"])
    assert any("topics: expected list" in error for error in errors)


def test_nested_link_shape_blocks(tmp_path):
    vault = _vault(tmp_path)
    (vault / "notes/bad.md").write_text(
        "---\ntype: note\nid: 01ARZ3NDEKTSV4RRFFQ69G5FAV\n"
        "tags: []\nlinks:\n  related:\n    - notes/target.md\ntitle: T\n---\nBody.\n",
        encoding="utf-8",
    )
    errors = precommit_check.check_paths(vault, ["notes/bad.md"])
    assert any("links.related: unknown relation" in error for error in errors)


def test_unknown_type_blocks(tmp_path):
    vault = _vault(tmp_path)
    (vault / "notes/odd.md").write_text(
        "---\ntype: reference-note\ncheck_status: checked\n---\n",
        encoding="utf-8",
    )
    errors = precommit_check.check_paths(vault, ["notes/odd.md"])
    assert any("unknown type" in e for e in errors)


def test_vault_local_schema_overrides_packaged_default(tmp_path):
    vault = _vault(tmp_path)
    schemas = vault / ".memoria/schemas/types"
    schemas.mkdir(parents=True)
    (schemas / "local-note.yaml").write_text(
        "type: local-note\nrequired:\n  type: literal:local-note\n  title: str\n",
        encoding="utf-8",
    )
    (vault / "notes/local.md").write_text(
        "---\ntype: local-note\ntitle: Local\n---\nBody.\n",
        encoding="utf-8",
    )

    assert precommit_check.check_paths(vault, ["notes/local.md"]) == []


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
    hook = WORKSPACE_SEED / ".githooks/pre-commit"
    assert hook.is_file()
    assert hook.stat().st_mode & 0o111, "pre-commit hook must be executable"


def test_hidden_runtime_exempt(tmp_path):
    vault = _vault(tmp_path)
    (vault / ".memoria/staging/templates").mkdir(parents=True)
    tpl = vault / ".memoria/staging/templates/note.md"
    tpl.write_text("---\ntype: note\ncreated: {{DATE}}\n---\n", encoding="utf-8")
    assert precommit_check.check_paths(vault, [".memoria/staging/templates/note.md"]) == []
