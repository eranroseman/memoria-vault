"""Runtime-local gate replay tests."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from memoria_vault.cli import main
from memoria_vault.runtime import state
from memoria_vault.runtime.trusted_writer import (
    commit_writer_changes as _commit_writer_changes,
)
from memoria_vault.runtime.trusted_writer import (
    promote_checked as _promote_checked,
)
from memoria_vault.runtime.trusted_writer import (
    stage_concept as _stage_concept,
)
from tests.helpers import call_with_context, operation_context, patch_pydantic_ai


def stage_concept(vault: Path, *args, **kwargs):
    context = operation_context(
        vault,
        operation_id=str(kwargs.pop("operation", "runtime-gate-fixture")),
        machine=str(kwargs.pop("machine", "memoria-cli")),
        run_id=str(kwargs.pop("run_id", "runtime-gate-fixture")),
    )
    return _stage_concept(vault, *args, context=context, **kwargs)


def promote_checked(vault: Path, *args, **kwargs):
    return call_with_context(_promote_checked, vault, *args, **kwargs)


def commit_writer_changes(vault: Path, *args, **kwargs):
    return call_with_context(_commit_writer_changes, vault, *args, **kwargs)


def test_runtime_gate_replays_user_facing_commands(
    tmp_path: Path, capsys: pytest.CaptureFixture[str], monkeypatch: pytest.MonkeyPatch
) -> None:
    workspace = tmp_path / "workspace-runtime-gate"
    provider_replay = tmp_path / "providers.json"
    provider_replay.write_text(json.dumps(_provider_payloads()), encoding="utf-8")
    interview = tmp_path / "interview.json"
    interview.write_text(
        json.dumps(
            {
                "prompt": "What matters?",
                "response": "The PI cares about the methods caveat.",
                "project_id": "projects/project-alpha/project.md",
            }
        ),
        encoding="utf-8",
    )
    _fake_runner(monkeypatch)
    _fake_seeded_verdict(monkeypatch, workspace)

    dry_run = _run_json(capsys, "init", "--workspace", str(workspace), "--dry-run")
    assert dry_run["dry_run"] is True
    assert not workspace.exists()

    _run_json(capsys, "init", "--workspace", str(workspace), "--yes")
    _write_project_fixture(workspace)
    doctor = _run_json(capsys, "doctor", "--workspace", str(workspace))
    assert doctor["checks"]["state_db"] is True

    _run_json(
        capsys,
        "work",
        "add",
        "--workspace",
        str(workspace),
        "--doi",
        "10.1000/alpha",
        "--title",
        "Alpha Source",
        "--text",
        "Alpha full text about framing, methods, outcomes, gaps, and impact.",
        "--idempotency-key",
        "gate-capture",
    )
    _run_json(
        capsys,
        "work",
        "enrich",
        "--workspace",
        str(workspace),
        "doi-10.1000_alpha",
        "--provider-replay",
        str(provider_replay),
        "--idempotency-key",
        "gate-enrich",
    )
    _run_json(
        capsys,
        "work",
        "update",
        "--workspace",
        str(workspace),
        "doi-10.1000_alpha",
        "--research-area",
        "framing",
        "--idempotency-key",
        "gate-update",
    )
    _run_json(
        capsys,
        "work",
        "interview",
        "--workspace",
        str(workspace),
        "doi-10.1000_alpha",
        "--fixture",
        str(interview),
        "--idempotency-key",
        "gate-interview",
    )
    digest = _run_json(
        capsys,
        "work",
        "digest",
        "--workspace",
        str(workspace),
        "doi-10.1000_alpha",
        "--idempotency-key",
        "gate-digest",
    )
    digest_path = digest["result"]["digest_path"]

    note = _run_json(
        capsys,
        "new",
        "note",
        "Gate note",
        "--workspace",
        str(workspace),
        "--body",
        "Framing changes which outcomes matter.",
        "--tag",
        "framing",
        "--idempotency-key",
        "gate-note-new",
    )
    note_path = str(note["path"])
    _run_json(
        capsys,
        "check",
        "--workspace",
        str(workspace),
        note_path,
        "--idempotency-key",
        "gate-note-check",
    )
    _run_json(
        capsys,
        "link",
        "--workspace",
        str(workspace),
        note_path,
        "notes/thesis.md",
        "--rel",
        "supports",
        "--reason",
        "PI linked",
        "--idempotency-key",
        "gate-note-link",
    )

    recovered = _run_json(
        capsys,
        "workspace",
        "recover",
        "--workspace",
        str(workspace),
        "--fixture",
        "crash-before-materialization",
    )
    assert recovered["restored"] == ["notes/crash-before-materialization.md"]

    runner = _run_json(
        capsys,
        "doctor",
        "--workspace",
        str(workspace),
        "--check",
        "runner",
        "--provider",
        "local",
    )
    assert runner["checks"]["runner_agent_constructed"] is True
    _run_json(capsys, "doctor", "self-test", "--workspace", str(workspace))
    backup_target = tmp_path / "runtime-gate-backup"
    backup = _run_json(
        capsys,
        "workspace",
        "backup",
        str(backup_target),
        "--workspace",
        str(workspace),
    )
    assert Path(backup["target"]) == backup_target.resolve()
    bundle = _run_json(capsys, "doctor", "bundle", "--workspace", str(workspace), "--redacted")
    assert bundle["redacted"] is True

    scan = _run_json(
        capsys,
        "workspace",
        "scan",
        "--workspace",
        str(workspace),
        "--fixture",
        "direct-write-generated-projection",
    )
    assert scan["quarantine"]["finding_count"] == 1
    assert scan["needs_check_count"] == 0
    assert (workspace / ".memoria/quarantine/index.md").is_file()

    _run_json(
        capsys,
        "workspace",
        "run",
        "--workspace",
        str(workspace),
        "--schedule-id",
        "queue-drain",
    )
    structural = _run_json(
        capsys,
        "workspace",
        "check",
        "--workspace",
        str(workspace),
        "--schedule-id",
        "structural-check",
    )
    assert structural["schedule_id"] == "structural-check"
    rebuild = _run_json(
        capsys,
        "workspace",
        "rebuild",
        "--workspace",
        str(workspace),
        "--search",
    )
    assert rebuild["search"]["engine"] == "bm25"
    assert len(rebuild["search"]["manifest"]["documents"]) >= 1
    search = _run_json(capsys, "doctor", "--workspace", str(workspace), "--check", "search")
    assert search["checks"]["search_checked_root"] is True
    assert search["checks"]["search_manifest"] is True

    status = _run_json(capsys, "status", "--workspace", str(workspace), ok_key=False)
    assert status["requests"]["done"] >= 1
    answer = _run_json(
        capsys,
        "ask",
        "--workspace",
        str(workspace),
        "--question",
        "framing outcomes",
        "--idempotency-key",
        "gate-ask",
    )
    assert {source["path"] for source in answer["result"]["sources"]} & {digest_path, note_path}
    project_answer = _run_json(
        capsys,
        "project",
        "ask",
        "--workspace",
        str(workspace),
        "project-alpha",
        "--question",
        "status",
        "--idempotency-key",
        "gate-project-ask",
    )
    assert project_answer["result"]["project_context"]["project_path"] == (
        "projects/project-alpha/project.md"
    )
    export = _run_json(
        capsys,
        "project",
        "export",
        "--workspace",
        str(workspace),
        "project-alpha",
        "--format",
        "markdown",
        "--output",
        str(tmp_path / "project-alpha.md"),
        "--idempotency-key",
        "gate-project-export",
    )
    assert Path(export["result"]["output_path"]).is_file()

    journal = _run_json(
        capsys,
        "journal",
        "tail",
        "--workspace",
        str(workspace),
        "--operation",
        "work.digest",
        ok_key=False,
    )
    assert journal["events"]

    verdict = _run_json(
        capsys,
        "eval",
        "seeded-error-verdict",
        "--workspace",
        str(workspace),
        "--idempotency-key",
        "gate-seeded-verdict",
    )
    assert verdict["result"]["passed"] is True

    with state.connect(workspace) as conn:
        requests = {
            row["operation_id"]
            for row in conn.execute("SELECT operation_id FROM operation_requests")
        }
    assert {
        "capture-source",
        "enrich-source",
        "compile-source-digest",
        "answer-query",
        "export-project",
        "run-seeded-error-verdict",
    } <= requests


def _run_json(
    capsys: pytest.CaptureFixture[str], *argv: str, ok_key: bool = True
) -> dict[str, object]:
    rc = main([*argv, "--json"])
    output = json.loads(capsys.readouterr().out)
    assert rc == 0, output
    if ok_key:
        assert output["ok"] is True
    return output


def _fake_runner(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("MEMORIA_MODEL_BASE_URL", "http://127.0.0.1:11434/v1")
    monkeypatch.setenv("MEMORIA_MODEL", "local-test-model")
    patch_pydantic_ai(monkeypatch)


def _fake_seeded_verdict(monkeypatch: pytest.MonkeyPatch, workspace: Path) -> None:
    def fake_verdict(
        vault: Path,
        *,
        template_root: Path,
        bundle_path: Path,
        runner: dict,
        operation_id: str,
        context,
    ) -> dict[str, object]:
        assert vault != workspace
        assert template_root == workspace
        assert bundle_path == workspace / ".memoria/eval/alpha15-seeded-errors.json"
        assert operation_id == "run-seeded-error-verdict"
        assert runner["mode"] == "test"
        assert context.machine == "memoria-cli"
        return {"passed": True, "metrics": {"expected_errors": 1, "detected_errors": 1}}

    monkeypatch.setattr(
        "memoria_vault.runtime.seeded_errors.run_seeded_error_verdict",
        fake_verdict,
    )


def _write_project_fixture(workspace: Path) -> None:
    project = (
        "---\n"
        "type: project\n"
        "title: Alpha project\n"
        "description: Runtime gate project\n"
        "tags: []\n"
        "links: {}\n"
        "thesis: notes/thesis.md\n"
        "---\n"
        "Body.\n"
    )
    note = "---\ntype: note\ntitle: Thesis\ntags: []\nlinks: {}\n---\nBody.\n"
    stage_concept(
        workspace,
        "projects/project-alpha/project.md",
        project,
        operation="runtime-gate-fixture",
        machine="memoria-cli",
    )
    promote_checked(workspace, "projects/project-alpha/project.md", machine="memoria-cli")
    stage_concept(
        workspace,
        "notes/thesis.md",
        note,
        operation="runtime-gate-fixture",
        machine="memoria-cli",
    )
    promote_checked(workspace, "notes/thesis.md", machine="memoria-cli")
    commit_writer_changes(
        workspace,
        "runtime gate project fixture",
        ["projects/project-alpha/project.md", "notes/thesis.md"],
        machine="memoria-cli",
    )


def _provider_payloads() -> dict[str, object]:
    return {
        "crossref": {
            "message": {
                "DOI": "10.1000/alpha",
                "URL": "https://doi.org/10.1000/alpha",
                "type": "journal-article",
                "title": ["Alpha Source"],
                "container-title": ["Journal of Testable Systems"],
                "author": [{"given": "Ada", "family": "River"}],
                "issued": {"date-parts": [[2026]]},
                "relation": {},
            }
        },
        "openalex": {
            "id": "https://openalex.org/W123",
            "doi": "https://doi.org/10.1000/alpha",
            "title": "Alpha Source",
            "authorships": [
                {
                    "author": {
                        "id": "https://openalex.org/A123",
                        "display_name": "Ada River",
                    },
                    "institutions": [],
                }
            ],
            "primary_location": {"source": {"display_name": "Journal of Testable Systems"}},
            "topics": [{"display_name": "Research workflows"}],
        },
        "unpaywall": {
            "doi": "10.1000/alpha",
            "is_oa": True,
            "oa_status": "gold",
            "best_oa_location": {"url_for_pdf": "https://example.test/alpha.pdf"},
        },
    }
