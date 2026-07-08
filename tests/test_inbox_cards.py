"""Inbox helpers write attention projections, not Concept cards."""

import re

import pytest
import yaml

from memoria_vault.runtime.subsystems.lib import inbox


def _frontmatter(path) -> dict:
    text = path.read_text(encoding="utf-8")
    m = re.match(r"^---\n(.*?)\n---\n", text, re.S)
    return yaml.safe_load(m.group(1))


def test_proposal_card_is_attention_projection(tmp_path):
    p = inbox.write_proposal(
        tmp_path,
        "candidate",
        "Smith 2024 on X",
        "Accept this source into the catalog",
        "fills the X gap",
        "venue is low-signal",
        "the gap outweighs the venue",
        "likely",
        "librarian",
        citekey="@smith2024",
    )
    fm = _frontmatter(p)
    assert fm["projection"] == "attention"
    assert fm["attention_kind"] == "candidate"
    assert fm["attention_status"] == "open"
    assert "type" not in fm


def test_proposal_carries_no_verdict(tmp_path):
    p = inbox.write_proposal(
        tmp_path,
        "gap",
        "Missing RCTs on Y",
        "Search for sources",
        "for",
        "against",
        "tipped",
        "unsure",
        "librarian",
    )
    fm = _frontmatter(p)
    assert "agent_recommendation" not in fm  # the verdict is a given — omitted
    assert "finding" not in fm


def test_finding_card_is_attention_projection(tmp_path):
    p = inbox.write_finding(
        tmp_path,
        "flag",
        "Broken citekey",
        "citekey @ghost resolves nowhere",
        "linter",
        target="notes/claims/c.md",
        evidence="grep output",
    )
    fm = _frontmatter(p)
    assert fm["projection"] == "attention"
    assert fm["attention_kind"] == "flag"
    assert fm["attention_status"] == "open"
    assert "type" not in fm
    body = p.read_text(encoding="utf-8")
    assert "# Finding" in body and "# Evidence" in body


def test_flag_requires_a_pointer(tmp_path):
    with pytest.raises(ValueError):
        inbox.write_finding(tmp_path, "flag", "t", "f", "linter")


def test_collision_appends_not_overwrites(tmp_path):
    a = inbox.write_proposal(
        tmp_path, "candidate", "Same Title", "a", "b", "c", "d", "likely", "librarian"
    )
    b = inbox.write_proposal(
        tmp_path, "candidate", "Same Title", "a", "b", "c", "d", "likely", "librarian"
    )
    assert a != b and a.exists() and b.exists()


def test_work_prompt_card_is_attention_projection(tmp_path):
    p = inbox.write_work_prompt(
        tmp_path,
        "Review: Draft answer",
        "Review the draft, then accept or archive",
        'Request REQ-b2 produced "Draft answer".',
        "request-control",
        target="projects/p1/draft.md",
        request_id="REQ-b2",
        posture="writer",
    )
    fm = _frontmatter(p)
    assert fm["projection"] == "attention"
    assert fm["attention_kind"] == "work-prompt"
    assert fm["attention_status"] == "open"
    assert fm["request_id"] == "REQ-b2"
    assert fm["posture"] == "writer"
    assert "task_id" not in fm
    assert "lane" not in fm
    assert "type" not in fm
    body = p.read_text(encoding="utf-8")
    assert "# Action" in body and "# What happened" in body and "# Where to look" in body


def test_work_prompt_carries_no_verdict(tmp_path):
    p = inbox.write_work_prompt(
        tmp_path,
        "Review: X",
        "review it",
        "request finished X",
        "request-control",
        request_id="REQ-1",
    )
    text = p.read_text(encoding="utf-8")
    assert "agent_recommendation" not in text  # work prompts never carry verdicts
    assert "finding" not in _frontmatter(p)


def test_work_prompt_requires_a_pointer(tmp_path):
    with pytest.raises(ValueError):
        inbox.write_work_prompt(tmp_path, "t", "a", "w", "board-export")


def test_work_prompt_dedupe_slug_is_idempotent(tmp_path):
    a = inbox.write_work_prompt(
        tmp_path,
        "Review: X",
        "a",
        "w",
        "request-control",
        request_id="REQ-1",
        dedupe_slug="review-REQ-1",
    )
    b = inbox.write_work_prompt(
        tmp_path,
        "Review: X",
        "a",
        "w",
        "request-control",
        request_id="REQ-1",
        dedupe_slug="review-REQ-1",
    )
    assert a is not None and a.name == "work-prompt-review-req-1.md"
    assert b is None  # second emit for the same card id writes nothing
    assert len(list((tmp_path / "inbox").glob("*.md"))) == 1


def test_invalid_enums_rejected(tmp_path):
    with pytest.raises(ValueError):
        inbox.write_proposal(
            tmp_path, "candidate", "T", "a", "b", "c", "d", "very-sure", "librarian"
        )
    with pytest.raises(ValueError):
        inbox.write_finding(tmp_path, "alert", "T", "f", "linter", agent_recommendation="fine")
