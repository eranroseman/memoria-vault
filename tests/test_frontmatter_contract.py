"""Frontmatter normalization contract tests."""

from __future__ import annotations

from memoria_vault.runtime.subsystems.lib import schema

ULID = "01KBN6V6KX0000000000000001"


def _base_note(**extra: object) -> dict[str, object]:
    payload: dict[str, object] = {
        "type": "note",
        "id": ULID,
        "title": "Note",
        "tags": [],
        "links": {},
    }
    payload.update(extra)
    return payload


def test_note_mode_required_when_contract() -> None:
    note = schema.load_types()["note"]

    assert any(
        "claim_text: required when mode is 'claim'" in error
        for error in schema.validate_frontmatter(_base_note(mode="claim"), note)
    )
    assert schema.validate_frontmatter(_base_note(mode="claim", claim_text="A claim."), note) == []
    assert any(
        "question_status: required when mode is 'question'" in error
        for error in schema.validate_frontmatter(_base_note(mode="question"), note)
    )
    assert (
        schema.validate_frontmatter(_base_note(mode="question", question_status="open"), note) == []
    )
    assert any(
        "work_id: required when mode is 'work'" in error
        for error in schema.validate_frontmatter(_base_note(mode="work"), note)
    )
    assert (
        schema.validate_frontmatter(
            _base_note(
                mode="work",
                work_id="catalog/sources/source-alpha",
                description="Source note folded into note.",
                item_type="paper",
                topics=["personal-informatics"],
            ),
            note,
        )
        == []
    )


def test_note_modes_certainty_item_type_and_retired_fields() -> None:
    note = schema.load_types()["note"]

    assert (
        schema.validate_frontmatter(
            _base_note(mode="definition", certainty="hypothesized", todo=["review"]),
            note,
        )
        == []
    )
    assert any(
        "value 'hypothesis' not in enum mode" in error
        for error in schema.validate_frontmatter(_base_note(mode="hypothesis"), note)
    )
    assert any(
        "value 'book' not in enum item_type" in error
        for error in schema.validate_frontmatter(_base_note(item_type="book"), note)
    )
    for field in ("citations", "evidence_set", "citekey", "project"):
        assert any(
            f"{field}: field is retired" in error
            for error in schema.validate_frontmatter(_base_note(**{field: []}), note)
        )


def test_digest_hub_project_current_fields() -> None:
    types = schema.load_types()
    digest = {
        "type": "digest",
        "id": "source-alpha",
        "title": "Digest",
        "tags": [],
        "links": {},
        "work_id": "source-alpha",
        "todo": ["review"],
    }
    hub = {
        "type": "hub",
        "id": ULID,
        "title": "Hub",
        "tags": [],
        "links": {},
        "tag": "hub",
        "todo": ["review"],
    }
    project = {
        "type": "project",
        "id": ULID,
        "title": "Project",
        "tags": [],
        "links": {},
        "todo": ["review"],
    }

    assert schema.validate_frontmatter(digest, types["digest"]) == []
    assert schema.validate_frontmatter(hub, types["hub"]) == []
    assert schema.validate_frontmatter(project, types["project"]) == []
    assert any(
        "citations: field is retired" in error
        for error in schema.validate_frontmatter(dict(digest, citations=[]), types["digest"])
    )
    assert any(
        "evidence_set: field is retired" in error
        for error in schema.validate_frontmatter(dict(digest, evidence_set=[]), types["digest"])
    )
    assert any(
        "citations: field is retired" in error
        for error in schema.validate_frontmatter(dict(hub, citations=[]), types["hub"])
    )
