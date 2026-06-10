"""Every engine/lane writes Inbox cards through one schema-shaped writer (ADR-51)."""

import re

import pytest
import yaml

import inbox
import schema


def _frontmatter(path) -> dict:
    text = path.read_text(encoding="utf-8")
    m = re.match(r"^---\n(.*?)\n---\n", text, re.S)
    return yaml.safe_load(m.group(1))


def test_proposal_card_is_schema_valid(tmp_path):
    p = inbox.write_proposal(
        tmp_path, "candidate", "Smith 2024 on X", "Accept this source into the catalog",
        "fills the X gap", "venue is low-signal", "the gap outweighs the venue",
        "likely", "librarian", citekey="@smith2024")
    fm = _frontmatter(p)
    types = schema.load_types()
    assert schema.validate_frontmatter(fm, types["candidate"]) == []
    assert fm["lifecycle"] == "proposed"


def test_proposal_carries_no_verdict(tmp_path):
    p = inbox.write_proposal(tmp_path, "gap", "Missing RCTs on Y", "Search for sources",
                             "for", "against", "tipped", "unsure", "librarian")
    fm = _frontmatter(p)
    assert "agent_recommendation" not in fm  # D49: the verdict is a given — omitted
    assert "finding" not in fm


def test_finding_card_is_schema_valid(tmp_path):
    p = inbox.write_finding(tmp_path, "flag", "Broken citekey",
                            "citekey @ghost resolves nowhere", "linter",
                            target="notes/claims/c.md", evidence="grep output")
    fm = _frontmatter(p)
    types = schema.load_types()
    assert schema.validate_frontmatter(fm, types["flag"]) == []
    body = p.read_text(encoding="utf-8")
    assert "# Finding" in body and "# Evidence" in body


def test_flag_requires_a_pointer(tmp_path):
    with pytest.raises(ValueError):
        inbox.write_finding(tmp_path, "flag", "t", "f", "linter")


def test_collision_appends_not_overwrites(tmp_path):
    a = inbox.write_proposal(tmp_path, "candidate", "Same Title", "a", "b", "c", "d",
                             "likely", "librarian")
    b = inbox.write_proposal(tmp_path, "candidate", "Same Title", "a", "b", "c", "d",
                             "likely", "librarian")
    assert a != b and a.exists() and b.exists()


def test_invalid_enums_rejected(tmp_path):
    with pytest.raises(ValueError):
        inbox.write_proposal(tmp_path, "candidate", "T", "a", "b", "c", "d",
                             "very-sure", "librarian")
    with pytest.raises(ValueError):
        inbox.write_finding(tmp_path, "alert", "T", "f", "linter",
                            agent_recommendation="fine")
