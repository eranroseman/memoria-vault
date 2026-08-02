from __future__ import annotations

import json
from pathlib import Path

import pytest

from memoria_vault.runtime import state
from memoria_vault.runtime.indexing import rebuild_passage_index_explicit
from memoria_vault.runtime.integrity import NLI_NOTENOUGHINFO, NLI_REFUTED
from memoria_vault.runtime.integrity import resolve_attention as _resolve_attention
from memoria_vault.runtime.integrity import surface_tensions as _surface_tensions
from memoria_vault.runtime.policy.audit import sha256_file
from memoria_vault.runtime.subsystems.lib.edges import concept_edge_path_records
from memoria_vault.runtime.trusted_writer import (
    promote_checked as _promote_checked,
)
from memoria_vault.runtime.trusted_writer import (
    stage_concept as _stage_concept,
)
from memoria_vault.runtime.vaultio import read_frontmatter
from tests.helpers import call_with_context, copy_memoria_dirs, init_git

pytestmark = pytest.mark.runtime


def stage_concept(vault: Path, *args, **kwargs):
    return call_with_context(_stage_concept, vault, *args, **kwargs)


def promote_checked(vault: Path, *args, **kwargs):
    return call_with_context(_promote_checked, vault, *args, **kwargs)


def surface_tensions(vault: Path, *args, **kwargs):
    return call_with_context(_surface_tensions, vault, *args, **kwargs)


def resolve_attention(vault: Path, *args, **kwargs):
    return call_with_context(_resolve_attention, vault, *args, **kwargs)


def workspace(tmp_path: Path) -> Path:
    copy_memoria_dirs(tmp_path, "schemas", "config")
    init_git(tmp_path, "integrity@example.invalid", "Integrity")
    return tmp_path


def _stage_checked_note(vault: Path, rel: str, title: str, body: str) -> None:
    content = f"---\ntype: note\ntitle: {title}\ntags: []\nlinks: {{}}\n---\n# {title}\n\n{body}\n"
    stage_concept(vault, rel, content, machine="writer")
    promote_checked(vault, rel, machine="writer")
    state.mark_materialized(vault, rel)


def test_surface_tensions_degraded_gate_writes_attention_without_links(tmp_path: Path) -> None:
    vault = workspace(tmp_path)
    left = "notes/recall-up.md"
    right = "notes/recall-not-up.md"
    _stage_checked_note(vault, left, "Recall up", "The intervention improved recall.")
    _stage_checked_note(vault, right, "Recall not up", "The intervention did not improve recall.")

    def abstain(_premise: str, _hypothesis: str) -> dict:
        return {
            "verdict": NLI_NOTENOUGHINFO,
            "confidence": 0.0,
            "warrant": "fixture abstain",
        }

    result = surface_tensions(
        vault,
        comparator=abstain,
        commit=True,
        machine="integrity-machine",
        tier2=False,
    )

    assert result["degraded"] is True
    assert result["finding"]["route"] == "ask"
    assert result["candidate_count"] == 1
    assert result["candidates"][0]["verdict"] == "DEGRADED"
    assert result["candidates"][0]["tier"] == "degraded"
    assert (vault / result["attention_path"]).is_file()
    assert (
        "contradiction detection degraded"
        in (vault / result["attention_path"]).read_text(encoding="utf-8").lower()
    )
    assert read_frontmatter(vault / left)["links"] == {}
    assert read_frontmatter(vault / right)["links"] == {}


def test_surface_tensions_tier2_runs_on_tier1_abstain_without_links(tmp_path: Path) -> None:
    vault = workspace(tmp_path)
    left = "notes/recall-up.md"
    right = "notes/recall-down.md"
    left_text = "The field trial improved recall for novice readers."
    right_text = "The field trial reduced recall for novice readers."
    _stage_checked_note(vault, left, "Recall up", left_text)
    _stage_checked_note(vault, right, "Recall down", right_text)

    def judge(left_row: dict, right_row: dict) -> dict:
        return {
            "verdict": NLI_REFUTED,
            "confidence": 0.84,
            "warrant": "The same field trial cannot both improve and reduce recall.",
            "left_quote": left_row["text"].split("\n\n")[-1],
            "right_quote": right_row["text"].split("\n\n")[-1],
        }

    result = surface_tensions(vault, tier2_judge=judge, machine="integrity-machine")

    assert result["degraded"] is False
    assert result["abstain_count"] == 1
    assert result["tier2_evaluated_count"] == 1
    assert result["tier2_candidate_count"] == 1
    assert result["tier2_abstain_count"] == 0
    assert result["candidate_count"] == 1
    [candidate] = result["candidates"]
    assert candidate["tier"] == "tier2"
    assert candidate["verdict"] == NLI_REFUTED
    assert candidate["route"] == "ask"
    assert "field trial" in candidate["evidence"]["left_quote"]
    assert "field trial" in candidate["evidence"]["right_quote"]
    assert read_frontmatter(vault / left)["links"] == {}
    assert read_frontmatter(vault / right)["links"] == {}


def test_surface_tensions_tier2_not_called_for_tier1_refuted(tmp_path: Path) -> None:
    vault = workspace(tmp_path)
    left = "notes/recall-up.md"
    right = "notes/recall-not-up.md"
    _stage_checked_note(vault, left, "Recall up", "The intervention improved recall.")
    _stage_checked_note(vault, right, "Recall not up", "The intervention did not improve recall.")

    def judge(_left_row: dict, _right_row: dict) -> dict:
        raise AssertionError("Tier-2 must not run after a Tier-1 REFUTED verdict")

    result = surface_tensions(vault, tier2_judge=judge, machine="integrity-machine")

    assert result["candidate_count"] == 1
    assert result["candidates"][0]["tier"] == "tier1"
    assert result["tier2_evaluated_count"] == 0
    assert read_frontmatter(vault / left)["links"] == {}
    assert read_frontmatter(vault / right)["links"] == {}


def test_surface_tensions_tier2_runs_for_degraded_hard_cases(tmp_path: Path) -> None:
    vault = workspace(tmp_path)
    left = "notes/recall-up.md"
    right = "notes/recall-not-up.md"
    _stage_checked_note(vault, left, "Recall up", "The intervention improved recall.")
    _stage_checked_note(vault, right, "Recall not up", "The intervention did not improve recall.")

    def abstain(_premise: str, _hypothesis: str) -> dict:
        return {
            "verdict": NLI_NOTENOUGHINFO,
            "confidence": 0.0,
            "warrant": "fixture abstain",
        }

    def judge(left_row: dict, right_row: dict) -> dict:
        return {
            "verdict": NLI_REFUTED,
            "confidence": 0.9,
            "warrant": "The same intervention cannot both improve and not improve recall.",
            "left_quote": left_row["text"].split("\n\n")[-1],
            "right_quote": right_row["text"].split("\n\n")[-1],
        }

    result = surface_tensions(
        vault,
        comparator=abstain,
        tier2_judge=judge,
        commit=True,
        machine="integrity-machine",
    )

    assert result["degraded"] is True
    assert result["finding"]["route"] == "ask"
    assert result["tier2_evaluated_count"] == 1
    assert result["tier2_candidate_count"] == 1
    assert result["candidate_count"] == 1
    assert result["candidates"][0]["tier"] == "tier2"
    assert result["candidates"][0]["escalation"] == "tier1-degraded"
    assert (vault / result["attention_path"]).is_file()
    assert read_frontmatter(vault / left)["links"] == {}
    assert read_frontmatter(vault / right)["links"] == {}


def test_surface_tensions_tier2_requires_grounded_quotes(tmp_path: Path) -> None:
    vault = workspace(tmp_path)
    left = "notes/recall-up.md"
    right = "notes/recall-down.md"
    _stage_checked_note(vault, left, "Recall up", "The field trial improved recall.")
    _stage_checked_note(vault, right, "Recall down", "The field trial reduced recall.")

    def judge(_left_row: dict, _right_row: dict) -> dict:
        return {
            "verdict": NLI_REFUTED,
            "confidence": 0.99,
            "warrant": "Ungrounded fixture.",
            "left_quote": "This quote is not in the checked note.",
            "right_quote": "The field trial reduced recall.",
        }

    result = surface_tensions(vault, tier2_judge=judge, machine="integrity-machine")

    assert result["candidate_count"] == 0
    assert result["tier2_evaluated_count"] == 1
    assert result["tier2_candidate_count"] == 0
    assert result["tier2_abstain_count"] == 1
    assert read_frontmatter(vault / left)["links"] == {}
    assert read_frontmatter(vault / right)["links"] == {}


def test_surface_tensions_refuses_tampered_checked_file_before_tier2(tmp_path: Path) -> None:
    vault = workspace(tmp_path)
    left = "notes/recall-up.md"
    right = "notes/recall-down.md"
    _stage_checked_note(vault, left, "Recall up", "The field trial improved recall.")
    _stage_checked_note(vault, right, "Recall down", "The field trial reduced recall.")
    (vault / left).write_text(
        "---\ntype: note\ntitle: Recall up\ntags: []\nlinks: {}\n---\nTampered text.\n",
        encoding="utf-8",
    )

    def judge(_left_row: dict, _right_row: dict) -> dict:
        raise AssertionError("Tier-2 must not receive tampered checked file text")

    result = surface_tensions(vault, tier2_judge=judge, machine="integrity-machine")

    assert result["candidate_count"] == 0
    assert result["tier2_evaluated_count"] == 0
    with state.connect(vault) as conn:
        row = conn.execute(
            """
            SELECT operation_id, status, schedule_id, args_json
            FROM operation_requests
            WHERE operation_id = 'observe-pi-edits'
            """
        ).fetchone()
    assert row is not None
    assert row["status"] == "pending"
    assert row["schedule_id"] == "read-guard"
    assert json.loads(row["args_json"])["target_path"] == left


def test_surface_tensions_dedupes_same_canonical_id(tmp_path: Path) -> None:
    vault = workspace(tmp_path)
    shared_id = "01ARZ3NDEKTSV4RRFFQ69G5FAV"
    for rel, body in {
        "notes/recall-up.md": "The intervention improved recall.",
        "notes/recall-not-up.md": "The intervention did not improve recall.",
    }.items():
        path = vault / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(
            "---\n"
            "type: note\n"
            f"id: {shared_id}\n"
            f"title: {Path(rel).stem}\n"
            "tags: []\n"
            "links: {}\n"
            "---\n"
            f"# {Path(rel).stem}\n\n{body}\n",
            encoding="utf-8",
        )
        state.record_observed_file_edit(
            vault,
            output_id=rel,
            concept_type="note",
            output_sha256=sha256_file(path),
        )
        state.set_concept_verdict(vault, rel, "checked")

    result = surface_tensions(vault)

    assert result["candidate_count"] == 0


def _unsorted_pair_vault(tmp_path: Path) -> Path:
    """A vault whose one candidate pair arrives in reverse lexical order.

    `_checked_tension_rows` walks `iter_markdown`, which yields a directory's own
    files before descending, so a note beside a subdirectory is emitted *before* a
    note inside it while sorting after it. Flat `notes/a.md` + `notes/b.md`
    fixtures arrive pre-sorted, which is what lets a dropped `sorted()` survive.
    """
    vault = workspace(tmp_path)
    _stage_checked_note(vault, "notes/zzz.md", "Recall up", "The intervention improved recall.")
    _stage_checked_note(
        vault, "notes/aaa/x.md", "Recall not up", "The intervention did not improve recall."
    )
    return vault


def test_surface_tensions_commit_writes_confirmable_tension_prompts(tmp_path: Path) -> None:
    """Each candidate gets its own card carrying the pair the PI would confirm."""
    vault = _unsorted_pair_vault(tmp_path)

    result = surface_tensions(vault, commit=True, tier2=False, machine="integrity-machine")

    # Name the producer state: the gate passed, so this is the Tier-1 REFUTED
    # candidate path, not the degraded lexical one.
    assert result["degraded"] is False
    assert result["candidate_count"] == 1
    assert result["candidates"][0]["tier"] == "tier1"
    [prompt_rel] = result["tension_prompts"]
    frontmatter = read_frontmatter(vault / prompt_rel)
    assert frontmatter["prompt_kind"] == "tension-candidate"
    # Lexicographically sorted (cross-section contract 6), which for this fixture
    # is the reverse of the order the candidate arrived in.
    assert frontmatter["payload"] == {"source": "notes/aaa/x.md", "target": "notes/zzz.md"}
    assert frontmatter["attention_kind"] == "work-prompt"
    assert frontmatter["attention_status"] == "open"


def test_surface_tensions_tension_prompts_dedupe_across_sweeps(tmp_path: Path) -> None:
    """The same unordered pair keeps one open card however often the sweep runs."""
    vault = _unsorted_pair_vault(tmp_path)

    first = surface_tensions(vault, commit=True, tier2=False, machine="integrity-machine")
    second = surface_tensions(vault, commit=True, tier2=False, machine="integrity-machine")

    assert len(first["tension_prompts"]) == 1
    assert second["candidate_count"] == 1
    assert second["tension_prompts"] == []
    cards = sorted(path.name for path in (vault / "inbox").glob("work-prompt-tension-*.md"))
    assert len(cards) == 1


def test_surface_tensions_without_commit_writes_no_tension_prompts(tmp_path: Path) -> None:
    """A read-only sweep still finds the candidate and still writes nothing."""
    vault = _unsorted_pair_vault(tmp_path)

    result = surface_tensions(vault, tier2=False, machine="integrity-machine")

    assert result["candidate_count"] == 1
    assert result["tension_prompts"] == []
    assert not (vault / "inbox").exists()


def _tension_edges(vault: Path) -> list[tuple[str, str, str]]:
    """Tension edges in path space — v16 stores identities, never paths."""
    return [
        (record["source_path"], record["relation_type"], record["target_path"])
        for record in concept_edge_path_records(vault, checked_only=False)
        if record["relation_type"] == "tension"
    ]


def _tension_row_count(vault: Path) -> int:
    """Stored rows, counted before any projection can drop one it cannot render."""
    with state.connect(vault) as conn:
        return int(
            conn.execute(
                "SELECT COUNT(*) AS total FROM concept_edges WHERE relation_type = 'tension'"
            ).fetchone()["total"]
        )


def _dispositions(vault: Path) -> list[dict]:
    with state.connect(vault) as conn:
        rows = conn.execute("SELECT payload_json FROM event_log ORDER BY event_id").fetchall()
    return [
        payload
        for payload in (json.loads(row["payload_json"]) for row in rows)
        if payload.get("schema") == "disposition.v1"
    ]


def test_confirm_tension_outcome_mints_one_edge_row_surviving_reindex(tmp_path: Path) -> None:
    """The PI's confirmation IS the check: one checked row, and reindex spares it."""
    vault = _unsorted_pair_vault(tmp_path)
    surfaced = surface_tensions(vault, commit=True, tier2=False, machine="integrity-machine")
    [prompt_rel] = surfaced["tension_prompts"]

    result = resolve_attention(
        vault,
        prompt_rel,
        resolution="resolved",
        outcome="confirm-tension",
        reason="PI confirmed the tension",
        actor="pi",
        machine="curator",
    )

    expected = [("notes/aaa/x.md", "tension", "notes/zzz.md")]
    assert result["tension_edge"]["created"] is True
    assert result["tension_edge"]["edge_id"]
    assert _tension_row_count(vault) == 1
    assert _tension_edges(vault) == expected
    assert [row["decision"] for row in _dispositions(vault)] == ["accept"]

    # G2S1.1's upsert-and-prune spares tension rows: reindex must not eat it.
    rebuild_passage_index_explicit(vault, actor="operation", machine="reindex")

    assert _tension_row_count(vault) == 1
    assert _tension_edges(vault) == expected


def test_confirm_tension_outcome_is_idempotent_across_two_confirmations(tmp_path: Path) -> None:
    """ "Mints exactly one row" survives a second confirmation of the same card."""
    vault = _unsorted_pair_vault(tmp_path)
    surfaced = surface_tensions(vault, commit=True, tier2=False, machine="integrity-machine")
    [prompt_rel] = surfaced["tension_prompts"]

    first = resolve_attention(
        vault, prompt_rel, resolution="resolved", outcome="confirm-tension", actor="pi"
    )
    second = resolve_attention(
        vault, prompt_rel, resolution="resolved", outcome="confirm-tension", actor="pi"
    )

    assert first["tension_edge"]["created"] is True
    assert second["tension_edge"]["created"] is False
    assert second["tension_edge"]["edge_id"] == first["tension_edge"]["edge_id"]
    assert _tension_row_count(vault) == 1
    assert _tension_edges(vault) == [("notes/aaa/x.md", "tension", "notes/zzz.md")]


def test_confirm_tension_counts_its_edge_write_against_the_insert_concept_edge_path(
    tmp_path: Path,
) -> None:
    """The other half of the I1 touch budget: `tension` only ever arrives this way.

    `curate_note_link` cannot write it (`LINK_RELATIONS` excludes `tension`), so a
    counter wired to the curate seam alone reports zero for this relation forever.
    """
    from memoria_vault.runtime.operations import edge_write_counts

    vault = _unsorted_pair_vault(tmp_path)
    surfaced = surface_tensions(vault, commit=True, tier2=False, machine="integrity-machine")
    [prompt_rel] = surfaced["tension_prompts"]

    resolve_attention(
        vault, prompt_rel, resolution="resolved", outcome="confirm-tension", actor="pi"
    )

    assert edge_write_counts(vault) == {"tension": 1}
    with state.connect(vault) as conn:
        rows = conn.execute(
            "SELECT payload_json FROM telemetry_events WHERE event_type = 'edge-write.v1'"
        ).fetchall()
    # `edge_write_counts` projects `write_path` away, so assert it where it is written:
    # this seam and the curate seam must stay distinguishable in the raw stream.
    assert [json.loads(str(row["payload_json"])) for row in rows] == [
        {"relation_type": "tension", "write_path": "insert-concept-edge"}
    ]


def test_resolving_an_attention_without_confirming_a_tension_writes_no_edge_counter(
    tmp_path: Path,
) -> None:
    """The counter hangs on the edge mint, not on `resolve_attention` returning."""
    from memoria_vault.runtime.operations import edge_write_counts

    vault = _unsorted_pair_vault(tmp_path)
    surfaced = surface_tensions(vault, commit=True, tier2=False, machine="integrity-machine")
    [prompt_rel] = surfaced["tension_prompts"]

    resolve_attention(vault, prompt_rel, resolution="acknowledged", actor="pi")

    assert _tension_row_count(vault) == 0
    assert edge_write_counts(vault) == {}


def _write_card(vault: Path, rel: str, frontmatter: str) -> str:
    (vault / rel).parent.mkdir(parents=True, exist_ok=True)
    (vault / rel).write_text(f"---\n{frontmatter}---\nBody.\n", encoding="utf-8")
    return rel


@pytest.mark.parametrize(
    ("label", "frontmatter", "match"),
    [
        (
            "no prompt_kind at all",
            "projection: attention\nattention_kind: work-prompt\n",
            "tension-candidate",
        ),
        (
            "the right prompt_kind, no payload",
            "projection: attention\nattention_kind: work-prompt\nprompt_kind: tension-candidate\n",
            "missing its tension payload",
        ),
        (
            "a payload naming only one endpoint",
            "projection: attention\nattention_kind: work-prompt\n"
            "prompt_kind: tension-candidate\npayload:\n  source: ''\n  target: notes/zzz.md\n",
            "must carry source and target",
        ),
    ],
    ids=["no-prompt-kind", "no-payload", "blank-endpoint"],
)
def test_confirm_tension_rejects_cards_it_cannot_mint_from(
    tmp_path: Path, label: str, frontmatter: str, match: str
) -> None:
    """Each refusal branch alone: a card that names no confirmable pair mints nothing."""
    vault = workspace(tmp_path)
    rel = _write_card(vault, "inbox/work-prompt-other.md", frontmatter)

    with pytest.raises(ValueError, match=match):
        resolve_attention(
            vault,
            rel,
            resolution="resolved",
            outcome="confirm-tension",
            actor="pi",
            machine="curator",
        )

    assert _tension_row_count(vault) == 0


def test_resolving_any_other_outcome_returns_no_tension_edge_key(tmp_path: Path) -> None:
    """`tension_edge` is present only for confirm-tension, so its key is a signal."""
    vault = workspace(tmp_path)
    rel = _write_card(
        vault,
        "inbox/work-prompt-other.md",
        "projection: attention\nattention_kind: work-prompt\nprompt_kind: tension-candidate\n"
        "payload:\n  source: notes/aaa/x.md\n  target: notes/zzz.md\n",
    )

    result = resolve_attention(
        vault, rel, resolution="resolved", outcome="apply", actor="pi", machine="curator"
    )

    assert "tension_edge" not in result
    assert _tension_row_count(vault) == 0


def test_confirm_tension_refusal_precedes_the_disposition_it_would_record(
    tmp_path: Path,
) -> None:
    """The mint is ordered ahead of the journal, so a refusal records no decision.

    `append_journal_event` and `emit_disposition_event` both commit before
    `resolve_attention` returns, so a mint placed after them leaves an accepted
    disposition standing for a confirmation that raised — a decision the PI never
    made, in the one log that is append-only by trigger and cannot be repaired.
    """
    vault = workspace(tmp_path)
    rel = _write_card(
        vault,
        "inbox/work-prompt-other.md",
        "projection: attention\nattention_kind: work-prompt\n",
    )

    with pytest.raises(ValueError, match="tension-candidate"):
        resolve_attention(
            vault,
            rel,
            resolution="resolved",
            outcome="confirm-tension",
            actor="pi",
            machine="curator",
        )

    assert _dispositions(vault) == []
    with state.connect(vault) as conn:
        events = conn.execute("SELECT event_type FROM event_log").fetchall()
    assert [row["event_type"] for row in events] == []
    assert read_frontmatter(vault / rel).get("attention_status") is None
