from __future__ import annotations

import json
from pathlib import Path

from memoria_vault.runtime import state
from memoria_vault.runtime.integrity import NLI_NOTENOUGHINFO, NLI_REFUTED
from memoria_vault.runtime.integrity import surface_tensions as _surface_tensions
from memoria_vault.runtime.policy.audit import sha256_file
from memoria_vault.runtime.trusted_writer import (
    promote_checked as _promote_checked,
)
from memoria_vault.runtime.trusted_writer import (
    stage_concept as _stage_concept,
)
from memoria_vault.runtime.vaultio import read_frontmatter
from tests.helpers import call_with_context, copy_memoria_dirs, init_git


def stage_concept(vault: Path, *args, **kwargs):
    return call_with_context(_stage_concept, vault, *args, **kwargs)


def promote_checked(vault: Path, *args, **kwargs):
    return call_with_context(_promote_checked, vault, *args, **kwargs)


def surface_tensions(vault: Path, *args, **kwargs):
    return call_with_context(_surface_tensions, vault, *args, **kwargs)


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
