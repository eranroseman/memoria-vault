"""Graded-loudness routing helpers."""

import pytest

from memoria_vault.runtime.attention import inbox, loudness

pytestmark = pytest.mark.unit


def test_alert_finding_lands_on_the_card_at_alert(tmp_path):
    inbox.write_finding(
        tmp_path, "alert", "Critical drift", "system is stopped", "linter", loudness="alert"
    )

    [card] = list((tmp_path / "inbox").glob("*.md"))
    assert _card_loudness(card) == "alert"


def test_a_deduped_finding_writes_exactly_one_card(tmp_path):
    for _ in range(2):
        inbox.write_finding(
            tmp_path,
            "alert",
            "Critical drift",
            "system is stopped",
            "linter",
            loudness="alert",
            dedupe_slug="dedupe-probe",
        )

    cards = list((tmp_path / "inbox").glob("*.md"))
    assert len(cards) == 1
    assert _card_loudness(cards[0]) == "alert"


def test_a_deduped_work_prompt_writes_exactly_one_card_at_its_band(tmp_path):
    for _ in range(2):
        inbox.write_work_prompt(
            tmp_path,
            "Review the affected work",
            "Review the affected work and decide what to do next.",
            "A review gate needs PI attention.",
            "test",
            request_id="REQ-DEDUPE",
            loudness="alert",
            dedupe_slug="work-prompt-probe",
        )

    cards = list((tmp_path / "inbox").glob("*.md"))
    assert len(cards) == 1
    assert _card_loudness(cards[0]) == "alert"


def test_a_proposal_lands_at_notice(tmp_path):
    inbox.write_proposal(
        tmp_path,
        "candidate",
        "Maybe",
        "read it",
        "useful",
        "weak",
        "gap",
        "likely",
        "librarian",
        loudness="notice",
    )

    [card] = list((tmp_path / "inbox").glob("*.md"))
    assert _card_loudness(card) == "notice"


def test_open_blockers_only_reads_open_block_attention_projections(tmp_path):
    (tmp_path / "inbox").mkdir()
    (tmp_path / "inbox/open.md").write_text(
        "---\n"
        "title: Open block\n"
        "projection: attention\n"
        "attention_kind: alert\n"
        "attention_status: open\n"
        "loudness: block\n"
        "---\n",
        encoding="utf-8",
    )
    (tmp_path / "inbox/resolved.md").write_text(
        "---\n"
        "title: Resolved block\n"
        "projection: attention\n"
        "attention_kind: alert\n"
        "attention_status: resolved\n"
        "loudness: block\n"
        "---\n",
        encoding="utf-8",
    )
    (tmp_path / "inbox/notice.md").write_text(
        "---\n"
        "title: Notice\n"
        "projection: attention\n"
        "attention_kind: flag\n"
        "attention_status: open\n"
        "loudness: notice\n"
        "---\n",
        encoding="utf-8",
    )
    (tmp_path / "inbox/old-shape.md").write_text(
        "---\ntitle: Old shape\ntype: alert\nlifecycle: proposed\nloudness: block\n---\n",
        encoding="utf-8",
    )

    blockers = loudness.open_blockers(tmp_path)
    assert blockers == [{"path": "inbox/open.md", "title": "Open block", "type": "alert"}]


# --- I1 spec §3 loudness policy, applied to the shipped producers (A.5) ---------
#
# Each case drives the real producer and reads the band off the card it wrote, so
# a tier that moved back would fail here rather than in a table nobody runs. Only
# the producers whose shipped tier disagreed with the spec table are pinned; the
# agreeing ones (retraction sweeps and workspace scans at `alert`, `analyze-gaps`
# proposals and surfaced tensions at `notice`) are left to their own suites.


def test_batch_worklists_mint_at_quiet(tmp_path):
    """Bulk-admission volume never lands in the `notice`+ bands (spec §3)."""
    from memoria_vault.runtime.attention import worklists

    worklists.emit_worklist(tmp_path, "Screen batch", [{"title": "One", "item_ref": "ref-1"}])

    [prompt] = list((tmp_path / "inbox").glob("work-prompt-*.md"))
    assert _card_loudness(prompt) == "quiet"


def test_enrichment_notes_mint_at_quiet(tmp_path):
    """One of these lands per blocked work per check -- routine, so not `alert`."""
    from memoria_vault.runtime.enrichment import _write_attention_flag

    rel = _write_attention_flag(
        tmp_path,
        {"work_id": "source-alpha"},
        check="source-enrichment",
        finding="Provider returned no metadata.",
        evidence="HTTP 404",
    )

    assert _card_loudness(tmp_path / rel) == "quiet"


def test_discovered_work_candidates_mint_at_notice(tmp_path):
    """`normal` was never a band. Candidates sit at `notice` (spec §3)."""
    from memoria_vault.runtime.enrichment import _write_discovery_candidate

    rel = _write_discovery_candidate(
        tmp_path,
        {"work_id": "source-alpha"},
        {
            "target_id": "https://openalex.org/W999",
            "target_title": "A discovered work",
            "relation_type": "references",
        },
    )

    assert _card_loudness(tmp_path / rel) == "notice"


def test_no_shipped_producer_writes_an_unrostered_band():
    """Every literal band in the runtime is one of the four.

    An unrostered band is invisible rather than loud: it ranks with the default in
    `engine.api._order_key` and counts as its own bucket on the dashboard, so
    nothing fails and the card just never behaves as its author meant. That is how
    `loudness: normal` shipped and stayed.

    Where the literal lives moved in #1703. It used to sit in the frontmatter dict,
    because the five direct producers assembled the card themselves and reached no
    validator at all. They now name the band in the `inbox.throttled(vault,
    producer, band)` call, which validates it, and write the band that call returns.

    So the seam scan is the one that must always match, and the `assert seam` below
    is load-bearing: with the dict scan alone this test matched nothing after the
    move and would have gone on passing as a rule that checks nothing (escape class
    5). The dict scan stays even though it is legitimately empty today, because it
    is the only thing that would catch a producer that asks the seam for `alert` and
    then hard-codes something else onto the card -- a disagreement the seam cannot
    see and `tests/test_attention_flow.py`'s call-site rule does not read.
    """
    import re

    from tests.helpers import ROOT

    source = ROOT / "src/memoria_vault"
    sources = [path.read_text(encoding="utf-8") for path in source.rglob("*.py")]

    def _scan(pattern: str) -> set[str]:
        return {match.group(1) for text in sources for match in re.finditer(pattern, text)}

    # `inbox.throttled(vault, "analyze-gaps", "alert")` -- the seam's band argument
    seam = _scan(r"""throttled\([^)]*,\s*["'][a-z-]+["']\s*,\s*["']([a-z-]+)["']""")
    # `"loudness": "alert"` -- a band written straight onto the card
    written_directly = _scan(r"""["']loudness["']\s*:\s*["']([a-z-]+)["']""")

    assert seam, "the seam scan found no literal bands at all -- it has stopped matching"
    unrostered = (seam | written_directly) - set(inbox.LOUDNESS)
    assert not unrostered, f"unrostered band(s): {sorted(unrostered)}"


def _card_loudness(path) -> str:
    from memoria_vault.runtime.vaultio import read_frontmatter

    return str(read_frontmatter(path)["loudness"])
