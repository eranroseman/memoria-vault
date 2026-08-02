"""CLI surfaces tell the truth."""

from __future__ import annotations

import argparse

import pytest

from memoria_vault.cli import _emit

pytestmark = pytest.mark.contract


def _args(*, json: bool = False, quiet: bool = False) -> argparse.Namespace:
    return argparse.Namespace(json=json, quiet=quiet)


def test_failed_payload_never_prints_ok(capsys):
    code = _emit({"ok": False, "error": "check failed: broken evidence"}, _args())

    out = capsys.readouterr().out
    assert code == 1
    assert "ok" != out.strip()
    assert "FAILED" in out
    assert "broken evidence" in out


def test_nested_worker_failure_surfaces_result_error(capsys):
    code = _emit(
        {
            "ok": False,
            "status": "failed",
            "result": {
                "status": "failed",
                "error": "note schema requires work_id when mode is work",
            },
        },
        _args(),
    )

    out = capsys.readouterr().out
    assert code == 1
    assert "FAILED" in out
    assert "requires work_id" in out


def test_success_prints_output_path_over_true(capsys):
    output_path = f"notes/{'x' * 220}  result.md"
    code = _emit({"ok": True, "output_path": output_path}, _args())

    assert code == 0
    assert capsys.readouterr().out == f"{output_path}\n"


def test_bare_success_still_prints_ok(capsys):
    assert _emit({"ok": True}, _args()) == 0
    assert capsys.readouterr().out.strip() == "ok"


def test_non_json_success_keeps_worker_and_read_payloads_out_of_stdout(tmp_path, capsys):
    from memoria_vault.engine import api as engine_api
    from tests.helpers import init_cli_workspace

    workspace = init_cli_workspace(tmp_path, capsys)
    worker_payload = engine_api.run_operation(
        workspace,
        "capture-source",
        {
            "work_id": "w-present",
            "title": "cli-output-title-canary",
            "description": "A real worker result.",
            "content_text": "cli-output-body-canary",
        },
        actor="pi",
        idempotency_key="capture-presenter-test",
    )

    assert _emit(worker_payload, _args()) == 0
    out = capsys.readouterr().out
    assert out.strip() == "work_id: w-present"
    assert "cli-output" not in out

    read_payload = engine_api.read_work(workspace, "w-present")
    assert _emit(read_payload, _args()) == 0
    out = capsys.readouterr().out
    assert out.strip() == "work_id: w-present"
    assert "cli-output" not in out

    collection_payload = engine_api.read_concepts(workspace, concept_type="work")
    assert _emit(collection_payload, _args()) == 0
    out = capsys.readouterr().out
    assert out.strip() == "concepts: 1"
    assert "cli-output" not in out


def test_non_json_success_hides_opaque_details_and_points_to_json(capsys):
    payload = {"ok": True, "answer": {"body": "cli-output-answer-canary"}}

    assert _emit(payload, _args()) == 0
    assert capsys.readouterr().out.strip() == "completed; details available with --json"

    assert _emit(payload, _args(json=True)) == 0
    assert "cli-output-answer-canary" in capsys.readouterr().out

    assert _emit(payload, _args(quiet=True)) == 0
    assert capsys.readouterr().out == ""


def test_ask_zero_hit_renders_honest_empty_on_text_and_json_fronts(tmp_path, capsys):
    import json as jsonlib
    import re

    from memoria_vault.cli import main
    from tests.helpers import init_cli_workspace

    workspace = init_cli_workspace(tmp_path, capsys)

    args = ["ask", "--question", "zz-absent-canary", "--workspace", str(workspace)]
    assert main([*args, "--json"]) == 0
    answer = jsonlib.loads(capsys.readouterr().out)["result"]
    assert answer["sources"] == []
    sentence = answer["unknowns"][0]
    assert re.fullmatch(
        r"0 of \d+ candidates matched; \d+ unchecked documents were not searched",
        sentence,
    )
    assert [row["stage"] for row in answer["pipeline_counts"]] == [
        "universe",
        "ranked",
        "returned",
    ]
    assert sorted(answer["excluded_strata"]) == ["gated", "stale", "unchecked"]

    assert main(args) == 0
    assert sentence in capsys.readouterr().out

    project_args = [
        "project",
        "ask",
        "--workspace",
        str(workspace),
        "missing-project",
        "--question",
        "zz-absent-canary",
    ]
    assert main(project_args) == 0
    assert sentence in capsys.readouterr().out


def test_ask_trace_flag_threads_through_worker_and_prints_stage_lines(tmp_path, capsys):
    import json as jsonlib

    from memoria_vault.cli import main
    from tests.helpers import init_cli_workspace

    workspace = init_cli_workspace(tmp_path, capsys)
    args = ["ask", "--question", "zz-trace-canary", "--workspace", str(workspace)]

    assert main([*args, "--trace", "--json"]) == 0
    trace = jsonlib.loads(capsys.readouterr().out)["result"]["trace"]
    assert trace["rerank"] == "off"
    assert [row["stage"] for row in trace["pipeline_counts"]] == [
        "universe",
        "ranked",
        "returned",
    ]
    assert "fusion_inputs" not in trace

    assert main([*args, "--trace"]) == 0
    out = capsys.readouterr().out
    assert "rerank: off" in out
    for line in ("universe: ", "ranked: ", "returned: "):
        assert line in out

    assert main([*args, "--json"]) == 0
    assert "trace" not in jsonlib.loads(capsys.readouterr().out)["result"]


def test_list_type_work_returns_catalog_rows(tmp_path, capsys):
    from memoria_vault.engine import api as engine_api
    from tests.helpers import init_cli_workspace

    workspace = init_cli_workspace(tmp_path, capsys)
    captured = engine_api.run_operation(
        workspace,
        "capture-source",
        {
            "work_id": "w-listtest",
            "title": "List test",
            "description": "A catalog-list fixture.",
            "content_text": "body",
        },
        actor="pi",
        idempotency_key="capture-listtest",
    )
    assert captured["ok"] is True

    payload = engine_api.read_concepts(workspace, concept_type="work")

    assert payload["concepts"] == [
        {
            "path": "catalog/sources/w-listtest",
            "type": "work",
            "title": "List test",
            "check_status": "unchecked",
            "verdict": "unchecked",
        }
    ]


def test_new_note_mode_work_roundtrip(tmp_path, capsys):
    import json

    from memoria_vault.cli import main
    from memoria_vault.engine import api as engine_api
    from memoria_vault.runtime.vaultio import read_frontmatter
    from tests.helpers import init_cli_workspace

    workspace = init_cli_workspace(tmp_path, capsys)
    captured = engine_api.run_operation(
        workspace,
        "capture-source",
        {
            "work_id": "w-listtest",
            "title": "List test",
            "description": "A Work-note fixture.",
            "content_text": "body",
        },
        actor="pi",
        idempotency_key="capture-work-note",
    )
    assert captured["ok"] is True

    code = main(
        [
            "new",
            "note",
            "Work note",
            "--workspace",
            str(workspace),
            "--mode",
            "work",
            "--work-id",
            "w-listtest",
            "--body",
            "Judgment about the work.",
            "--json",
        ]
    )
    output = json.loads(capsys.readouterr().out)

    assert code == 0
    frontmatter = read_frontmatter(workspace / output["path"])
    assert frontmatter["mode"] == "work"
    assert frontmatter["work_id"] == "w-listtest"


def test_new_note_mode_work_without_work_id_surfaces_schema_failure(tmp_path, capsys):
    from memoria_vault.cli import main
    from tests.helpers import init_cli_workspace

    workspace = init_cli_workspace(tmp_path, capsys)

    code = main(
        [
            "new",
            "note",
            "Unlinked work note",
            "--workspace",
            str(workspace),
            "--mode",
            "work",
            "--body",
            "This must not be created.",
        ]
    )
    output = capsys.readouterr().out

    assert code == 1
    assert "FAILED" in output
    assert "work_id" in output
