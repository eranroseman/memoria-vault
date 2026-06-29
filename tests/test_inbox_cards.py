"""Inbox helpers write alpha.11 attention projections, not Concept cards."""

import re

import pytest
import yaml
from operations.lib import inbox


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
    assert "agent_recommendation" not in fm  # D49: the verdict is a given — omitted
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
        'Lane memoria-writer finished "Draft answer" (card t_b2).',
        "board-export",
        target="projects/p1/draft.md",
        task_id="t_b2",
        lane="memoria-writer",
    )
    fm = _frontmatter(p)
    assert fm["projection"] == "attention"
    assert fm["attention_kind"] == "work-prompt"
    assert fm["attention_status"] == "open"
    assert "type" not in fm
    body = p.read_text(encoding="utf-8")
    assert "# Action" in body and "# What happened" in body and "# Where to look" in body


def test_work_prompt_carries_no_verdict(tmp_path):
    p = inbox.write_work_prompt(
        tmp_path, "Review: X", "review it", "lane finished X", "board-export", task_id="t_1"
    )
    text = p.read_text(encoding="utf-8")
    assert "agent_recommendation" not in text  # ADR-51: never a verdict
    assert "finding" not in _frontmatter(p)


def test_work_prompt_requires_a_pointer(tmp_path):
    with pytest.raises(ValueError):
        inbox.write_work_prompt(tmp_path, "t", "a", "w", "board-export")


def test_work_prompt_dedupe_slug_is_idempotent(tmp_path):
    a = inbox.write_work_prompt(
        tmp_path, "Review: X", "a", "w", "board-export", task_id="t_1", dedupe_slug="review-t_1"
    )
    b = inbox.write_work_prompt(
        tmp_path, "Review: X", "a", "w", "board-export", task_id="t_1", dedupe_slug="review-t_1"
    )
    assert a is not None and a.name == "work-prompt-review-t-1.md"
    assert b is None  # second emit for the same card id writes nothing
    assert len(list((tmp_path / "inbox").glob("*.md"))) == 1


def test_invalid_enums_rejected(tmp_path):
    with pytest.raises(ValueError):
        inbox.write_proposal(
            tmp_path, "candidate", "T", "a", "b", "c", "d", "very-sure", "librarian"
        )
    with pytest.raises(ValueError):
        inbox.write_finding(tmp_path, "alert", "T", "f", "linter", agent_recommendation="fine")
