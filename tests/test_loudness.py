"""Graded-loudness routing helpers."""

import pytest

from memoria_vault.runtime.subsystems.lib import inbox, loudness

pytestmark = pytest.mark.unit


def test_alert_card_writes_no_push_log(tmp_path):
    inbox.write_finding(
        tmp_path, "alert", "Critical drift", "system is stopped", "linter", loudness="alert"
    )

    assert not list(tmp_path.rglob("*push*.jsonl"))


def test_deduped_alert_finding_writes_no_push_log(tmp_path):
    card = inbox.write_finding(
        tmp_path,
        "alert",
        "Critical drift",
        "system is stopped",
        "linter",
        loudness="alert",
        dedupe_slug="no-push-finding",
    )

    assert card is not None
    assert not list(tmp_path.rglob("*push*.jsonl"))


def test_deduped_alert_work_prompt_writes_no_push_log(tmp_path):
    inbox.write_work_prompt(
        tmp_path,
        "Review the affected work",
        "Review the affected work and decide what to do next.",
        "A review gate needs PI attention.",
        "test",
        request_id="REQ-NO-PUSH",
        loudness="alert",
        dedupe_slug="no-push-work-prompt",
    )

    assert not list(tmp_path.rglob("*push*.jsonl"))


def test_notice_card_writes_no_push_log(tmp_path):
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

    assert not list(tmp_path.rglob("*push*.jsonl"))


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
    from memoria_vault.runtime.subsystems.lib import worklists

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
    """Every literal `loudness:` in the runtime is one of the four bands.

    `inbox.write_*` validates its argument, but five producers assemble card
    frontmatter directly and reach no validator at all -- which is how
    `loudness: normal` shipped and stayed. An unrostered band is invisible rather
    than loud: it ranks with the default in `engine.api._order_key` and counts as
    its own bucket on the dashboard, so nothing fails and the card just never
    behaves as its author meant.
    """
    import re

    from tests.helpers import ROOT

    source = ROOT / "src/memoria_vault"
    written = {
        match.group(1)
        for path in source.rglob("*.py")
        for match in re.finditer(
            r"""["']loudness["']\s*:\s*["']([a-z-]+)["']""", path.read_text(encoding="utf-8")
        )
    }

    assert written, "the scan found no literal bands at all -- it has stopped matching"
    assert written <= set(inbox.LOUDNESS), (
        f"unrostered band(s): {sorted(written - set(inbox.LOUDNESS))}"
    )


def _card_loudness(path) -> str:
    from memoria_vault.runtime.vaultio import read_frontmatter

    return str(read_frontmatter(path)["loudness"])
