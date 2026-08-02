"""generate-questions: Toulmin-taxonomy question proposals over one checked scope."""

from __future__ import annotations

import json
from copy import deepcopy
from pathlib import Path

import pytest

from memoria_vault.runtime import state
from memoria_vault.runtime.jsonl import iter_jsonl
from memoria_vault.runtime.operations import (
    QUESTION_TAXONOMY_ROLES,
    _generate_questions_fixture,
    _validated_questions,
    load_operation_policy,
)
from memoria_vault.runtime.operations import generate_questions as _generate_questions
from memoria_vault.runtime.vaultio import read_frontmatter
from tests.cli_test_helpers import write_runner_provider_config
from tests.helpers import (
    call_with_context,
    copy_memoria_dirs,
    git,
    init_git,
    patch_pydantic_ai,
    worker_workspace,
    write_note,
)

pytestmark = pytest.mark.runtime


def workspace(tmp_path: Path) -> Path:
    copy_memoria_dirs(tmp_path, "schemas", "config")
    init_git(tmp_path, "questions@example.invalid", "Questions")
    return tmp_path


def generate_questions(vault: Path, *args, **kwargs):
    return call_with_context(_generate_questions, vault, *args, **kwargs)


def enable_production(monkeypatch: pytest.MonkeyPatch, **updates) -> dict:
    """Flip the shipped shadow-first flag the way promotion will: policy only, no code change."""
    policy = deepcopy(load_operation_policy(Path(), "generate-questions"))
    policy["production_enabled"] = True
    runner = updates.pop("runner", None)
    if runner:
        for mode, branch in runner.items():
            policy["runner"][mode].update(branch)
    policy.update(updates)
    monkeypatch.setattr(
        "memoria_vault.runtime.operations.load_operation_policy",
        lambda _vault, _operation_id: policy,
    )
    return policy


# --- manifest ------------------------------------------------------------


def test_manifest_declares_shadow_first_call_site() -> None:
    policy = load_operation_policy(Path(), "generate-questions")

    assert policy["operation_id"] == "generate-questions"
    assert policy["prompt_version"] == "generate-questions.v1"
    assert policy["production_enabled"] is False
    assert policy["allowed_tools"] == ["trusted_writer"]
    assert policy["allowed_network"] == []
    for scope_root in ("notes/", "hubs/", "digests/", "projects/", "inbox/"):
        assert scope_root in policy["allowed_paths"]
    assert policy["untrusted_fields"] == ["input"]
    # Runner branches injected by capabilities._manifest_frontmatter defaults:
    assert policy["runner"]["test"]["model"] == "deterministic-fixture"
    assert policy["runner"]["test"]["provider"] == "local"
    assert policy["runner"]["live"]["provider"] == "gateway"


# --- fixture and structural validation -----------------------------------


def test_fixture_returns_deterministic_taxonomy_questions() -> None:
    first = _generate_questions_fixture("notes/alpha.md")

    assert first == _generate_questions_fixture("notes/alpha.md")
    items = json.loads(first)
    assert len(items) == 4
    assert [item["role"] for item in items] == list(QUESTION_TAXONOMY_ROLES)
    for item in items:
        assert item["question"].endswith("?")
        assert item["target"] == "notes/alpha.md"


def test_validated_questions_keep_a_well_formed_item(tmp_path: Path) -> None:
    vault = workspace(tmp_path)
    write_note(vault, "alpha", "checked", "Alpha claims a causal effect.")

    valid, rejected = _validated_questions(
        vault,
        json.dumps(
            [
                {
                    "question": "What checked evidence\n  grounds notes/alpha.md?",
                    "role": "grounds-seeking",
                    "target": "notes/./alpha.md",
                }
            ]
        ),
    )

    assert rejected == 0
    assert valid == [
        {
            "question": "What checked evidence grounds notes/alpha.md?",
            "role": "grounds-seeking",
            "target": "notes/alpha.md",
        }
    ]


@pytest.mark.parametrize(
    ("item", "reason"),
    [
        (
            {"question": "Do X now.", "role": "grounds-seeking", "target": "notes/alpha.md"},
            "not a question",
        ),
        (
            {"question": "Warranted?", "role": "hunch-seeking", "target": "notes/alpha.md"},
            "role off taxonomy",
        ),
        (
            {"question": "Grounded?", "role": "rebuttal-probing", "target": "notes/missing.md"},
            "target unresolvable",
        ),
        (
            {"question": "Grounded?", "role": "rebuttal-probing", "target": "../escape.md"},
            "target escapes vault",
        ),
        ({"question": "Grounded?", "role": "rebuttal-probing", "target": ""}, "target empty"),
        ("not-an-object", "not an object"),
    ],
)
def test_validated_questions_drop_one_structural_failure_at_a_time(
    tmp_path: Path, item: object, reason: str
) -> None:
    """One bad item per case, so each rejection reason is proved on its own."""
    vault = workspace(tmp_path)
    write_note(vault, "alpha", "checked", "Alpha claims a causal effect.")
    good = {
        "question": "What checked evidence grounds notes/alpha.md?",
        "role": "grounds-seeking",
        "target": "notes/alpha.md",
    }

    valid, rejected = _validated_questions(vault, json.dumps([good, item]))

    assert rejected == 1, reason
    assert [entry["question"] for entry in valid] == [good["question"]], reason


def test_validated_questions_neutralize_untrusted_question_text(tmp_path: Path) -> None:
    """The question is model output landing in a card's frontmatter; it is untrusted."""
    vault = workspace(tmp_path)
    write_note(vault, "alpha", "checked", "Alpha claims a causal effect.")

    valid, rejected = _validated_questions(
        vault,
        json.dumps(
            [
                {
                    "question": "<script>alert(1)</script> Is [[notes/alpha.md]] grounded?",
                    "role": "grounds-seeking",
                    "target": "notes/alpha.md",
                }
            ]
        ),
    )

    assert rejected == 0
    assert "<script>" not in valid[0]["question"]


def test_validated_questions_resolve_targets_through_the_catalog(tmp_path: Path) -> None:
    """A work id is a resolvable target even though no file of that name exists.

    Without this case the catalog arm of target resolution is dead weight: every
    other fixture targets a vault file, which the file arm alone already accepts.
    """
    vault = workspace(tmp_path)
    state.upsert_catalog_record(vault, work_id="demo-work", title="Demo work")
    assert not (vault / "demo-work").exists()

    valid, rejected = _validated_questions(
        vault,
        json.dumps(
            [
                {
                    "question": "What in demo-work licenses the claim?",
                    "role": "warrant-challenging",
                    "target": "demo-work",
                }
            ]
        ),
    )

    assert rejected == 0
    assert valid[0]["target"] == "demo-work"


def test_validated_questions_reject_non_list_payload(tmp_path: Path) -> None:
    vault = workspace(tmp_path)

    with pytest.raises(ValueError, match="JSON list"):
        _validated_questions(vault, "not json at all")
    with pytest.raises(ValueError, match="JSON list"):
        _validated_questions(vault, json.dumps({"question": "solo?"}))


# --- the operation -------------------------------------------------------


def test_fixture_run_writes_proposal_cards_with_taxonomy_tags(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    vault = workspace(tmp_path)
    write_note(vault, "alpha", "checked", "Alpha claims a causal effect.")
    enable_production(monkeypatch)

    result = generate_questions(
        vault, "notes/alpha.md", machine="questions-machine", run_id="questions-alpha"
    )

    assert result["question_count"] == 4
    assert result["rejected_count"] == 0
    assert result["production_enabled"] is True
    assert len(result["proposal_paths"]) == 4
    roles = []
    for rel in result["proposal_paths"]:
        fm = read_frontmatter(vault / rel)
        assert fm["projection"] == "attention"
        assert fm["attention_kind"] == "gap"
        assert fm["attention_status"] == "open"
        assert fm["loudness"] == "notice"
        assert fm["raised_by"] == "generate-questions"
        assert fm["certainty"] == "unsure"
        assert fm["target"] == "notes/alpha.md"
        roles.append(fm["taxonomy_role"])
    assert sorted(roles) == sorted(QUESTION_TAXONOMY_ROLES)
    events = list(iter_jsonl(vault / ".memoria/journal/questions-machine.jsonl"))
    model_calls = [event for event in events if event.get("event") == "model_call"]
    assert len(model_calls) == 1
    assert model_calls[0]["call_id"] == "generate-questions.v1"
    assert model_calls[0]["prompt_version"] == "generate-questions.v1"
    assert model_calls[0]["model"] == "deterministic-fixture"
    assert model_calls[0]["route"] == "generate-questions"
    finished = [
        event for event in events if event.get("event") == "run" and event.get("status") == "done"
    ]
    assert finished[0]["question_count"] == 4
    assert finished[0]["rejected_count"] == 0
    assert finished[0]["outputs"] == result["proposal_paths"]
    committed = set(git(vault, "show", "--name-only", "--format=", result["commit"]).splitlines())
    assert set(result["proposal_paths"]) <= committed


def test_structural_rejections_are_counted_honestly(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    vault = workspace(tmp_path)
    write_note(vault, "alpha", "checked", "Alpha claims a causal effect.")
    enable_production(monkeypatch)
    mixed = json.dumps(
        [
            {
                "question": "What checked evidence grounds notes/alpha.md?",
                "role": "grounds-seeking",
                "target": "notes/alpha.md",
            },
            {"question": "Just do it.", "role": "grounds-seeking", "target": "notes/alpha.md"},
            {"question": "Really?", "role": "vibe-checking", "target": "notes/alpha.md"},
            {"question": "Grounded?", "role": "rebuttal-probing", "target": "notes/ghost.md"},
        ]
    )
    monkeypatch.setattr(
        "memoria_vault.runtime.operations._generate_questions_fixture",
        lambda _scope_rel: mixed,
    )

    result = generate_questions(vault, "notes/alpha.md", machine="reject-machine")

    assert result["question_count"] == 1
    assert result["rejected_count"] == 3
    assert len(result["proposal_paths"]) == 1
    events = list(iter_jsonl(vault / ".memoria/journal/reject-machine.jsonl"))
    finished = [
        event for event in events if event.get("event") == "run" and event.get("status") == "done"
    ]
    assert finished[0]["rejected_count"] == 3


def test_shipped_manifest_runs_shadow_first(tmp_path: Path) -> None:
    """No monkeypatch: the flag under test is the one the package actually ships."""
    vault = workspace(tmp_path)
    write_note(vault, "alpha", "checked", "Alpha claims a causal effect.")

    result = generate_questions(vault, "notes/alpha.md", machine="shadow-machine")

    assert result["production_enabled"] is False
    assert result["proposal_paths"] == []
    assert result["question_count"] == 4
    assert [item["role"] for item in result["questions"]] == list(QUESTION_TAXONOMY_ROLES)
    assert not list((vault / "inbox").glob("*.md"))
    events = list(iter_jsonl(vault / ".memoria/journal/shadow-machine.jsonl"))
    assert [event["event"] for event in events if event.get("event") == "model_call"] == [
        "model_call"
    ]
    finished = [
        event for event in events if event.get("event") == "run" and event.get("status") == "done"
    ]
    assert finished[0]["question_count"] == 4
    assert finished[0]["production_enabled"] is False
    assert finished[0]["outputs"] == []


def test_scope_must_be_checked(tmp_path: Path) -> None:
    vault = workspace(tmp_path)
    write_note(vault, "draft", "unchecked", "Unchecked draft body.")

    with pytest.raises(ValueError, match="not checked"):
        generate_questions(vault, "notes/draft.md", machine="unchecked-machine")


def test_scope_must_sit_inside_an_allowed_path(tmp_path: Path) -> None:
    vault = workspace(tmp_path)
    (vault / "system").mkdir(parents=True, exist_ok=True)
    (vault / "system/steering.md").write_text("# Steering\n", encoding="utf-8")

    with pytest.raises(PermissionError, match=r"system/steering\.md"):
        generate_questions(vault, "system/steering.md", machine="scope-machine")


def test_live_branch_routes_through_resolved_profile(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    vault = workspace(tmp_path)
    write_runner_provider_config(vault)
    write_note(vault, "alpha", "checked", "Alpha claims a causal effect.")
    enable_production(
        monkeypatch,
        allowed_network=["http://model.test/v1"],
        runner={"live": {"provider": "local", "model": "memoria-live-model"}},
    )
    seen: dict = {}
    patch_pydantic_ai(
        monkeypatch,
        output=json.dumps(
            [
                {
                    "question": "What checked evidence grounds notes/alpha.md?",
                    "role": "grounds-seeking",
                    "target": "notes/alpha.md",
                }
            ]
        ),
        seen=seen,
    )

    result = generate_questions(vault, "notes/alpha.md", mode="live", machine="live-machine")

    assert seen["model_name"] == "memoria-live-model"
    assert '<memoria_untrusted_data name="input">' in seen["prompt"]
    assert "Alpha claims a causal effect." in seen["prompt"]
    assert result["question_count"] == 1
    assert len(result["proposal_paths"]) == 1
    events = list(iter_jsonl(vault / ".memoria/journal/live-machine.jsonl"))
    model_calls = [event for event in events if event.get("event") == "model_call"]
    assert model_calls[0]["call_id"] == "generate-questions.v1"
    assert model_calls[0]["mode"] == "live"


def test_non_list_model_payload_fails_loudly(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    vault = workspace(tmp_path)
    write_note(vault, "alpha", "checked", "Alpha claims a causal effect.")
    monkeypatch.setattr(
        "memoria_vault.runtime.operations._generate_questions_fixture",
        lambda _scope_rel: "no questions today",
    )

    with pytest.raises(ValueError, match="JSON list"):
        generate_questions(vault, "notes/alpha.md", machine="garbage-machine")


# --- worker dispatch -----------------------------------------------------


def test_worker_dispatch_runs_generate_questions(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    from memoria_vault.runtime.worker import enqueue_operation, run_next_job

    vault = worker_workspace(tmp_path)
    write_note(vault, "alpha", "checked", "Alpha claims a causal effect.")
    enable_production(monkeypatch)
    enqueue_operation(
        vault,
        "generate-questions",
        payload={"scope": "notes/alpha.md"},
        idempotency_key="gq-worker-1",
        actor="agent",
    )

    done = run_next_job(vault, machine="gq-worker")

    assert done is not None and done["status"] == "done", done
    assert done["question_count"] == 4
    assert done["rejected_count"] == 0
    assert done["production_enabled"] is True
    assert len(done["proposal_paths"]) == 4
    for rel in done["proposal_paths"]:
        assert (vault / rel).is_file()
    # Both runner branches ship model `deterministic-fixture`, so the journal is
    # the only place the dispatch's default mode is observable at all.
    events = list(iter_jsonl(vault / ".memoria/journal/gq-worker.jsonl"))
    model_calls = [event for event in events if event.get("event") == "model_call"]
    assert model_calls[0]["mode"] == "test"


def test_worker_dispatch_passes_the_payload_mode_to_the_runner(tmp_path: Path) -> None:
    """An unsupported mode must surface from `normalize_run_mode`, not be swallowed."""
    from memoria_vault.runtime.worker import enqueue_operation, run_next_job

    vault = worker_workspace(tmp_path)
    write_note(vault, "alpha", "checked", "Alpha claims a causal effect.")
    enqueue_operation(
        vault,
        "generate-questions",
        payload={"scope": "notes/alpha.md", "mode": "sideways"},
        idempotency_key="gq-worker-3",
        actor="agent",
    )

    done = run_next_job(vault, machine="gq-worker")

    assert done is not None and done["status"] == "failed", done
    assert "unsupported run mode: sideways" in done["error"]


def test_worker_dispatch_requires_scope(tmp_path: Path) -> None:
    from memoria_vault.runtime.worker import enqueue_operation, run_next_job

    vault = worker_workspace(tmp_path)
    enqueue_operation(
        vault,
        "generate-questions",
        payload={},
        idempotency_key="gq-worker-2",
        actor="agent",
    )

    done = run_next_job(vault, machine="gq-worker")

    assert done is not None and done["status"] == "failed", done
    assert "generate-questions requires scope" in done["error"]
