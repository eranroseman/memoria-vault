from __future__ import annotations

import sqlite3
from pathlib import Path

from memoria_vault.runtime import state
from memoria_vault.runtime.code.records import create_code_artifact
from memoria_vault.runtime.code.runner import Availability, run_artifact
from memoria_vault.runtime.policy.audit import sha256_file


def test_code_artifact_default_purpose_is_grounds_in_database_and_markdown(
    tmp_path: Path,
) -> None:
    try:
        artifact = create_code_artifact(
            tmp_path,
            "project-alpha",
            "analysis",
            approved_command=["python3", "main.py"],
        )
    except sqlite3.IntegrityError as exc:
        raise AssertionError("the default code artifact purpose must be valid") from exc

    assert artifact["purpose"] == "grounds"
    assert "purpose: grounds\n" in (tmp_path / artifact["record_path"]).read_text(encoding="utf-8")


def test_code_artifact_record_and_unavailable_runner_fail_closed(
    tmp_path: Path,
    monkeypatch,
) -> None:
    artifact = create_code_artifact(
        tmp_path,
        "project-alpha",
        "analysis",
        approved_command=["python3", "main.py"],
        declared_outputs=["projects/project-alpha/code/analysis/outputs/result.txt"],
    )
    monkeypatch.setattr(
        "memoria_vault.runtime.code.runner.execution_availability",
        lambda vault: Availability("unsupported", "test sandbox unavailable"),
    )

    run = run_artifact(tmp_path, "analysis", run_id="run-1")

    assert Path(tmp_path, artifact["record_path"]).is_file()
    assert artifact["source_dir"] == "projects/project-alpha/code/analysis/src"
    assert run["state"] == "unavailable"
    assert run["timeout_result"] == "test sandbox unavailable"


def test_computed_evidence_tracks_code_run_output_hash(tmp_path: Path) -> None:
    output = tmp_path / "projects/project-alpha/code/analysis/outputs/result.txt"
    output.parent.mkdir(parents=True)
    output.write_text("42\n", encoding="utf-8")
    output_rel = output.relative_to(tmp_path).as_posix()
    output_hash = sha256_file(output)
    create_code_artifact(
        tmp_path,
        "project-alpha",
        "analysis",
        approved_command=["python3", "main.py"],
        declared_outputs=[output_rel],
    )
    state.record_code_run(
        tmp_path,
        run_id="run-1",
        artifact_id="analysis",
        command=["python3", "main.py"],
        cwd="projects/project-alpha/code/analysis/src",
        output_hashes={output_rel: output_hash},
        exit_status=0,
        sandbox_backend="bwrap",
        sandbox_profile_hash="sha256:" + "0" * 64,
        run_state="succeeded",
    )
    draft = tmp_path / "projects/project-alpha/draft.md"
    draft.parent.mkdir(parents=True, exist_ok=True)
    draft.write_text(
        f"Computed. %%ev: ev-11111111 items=code-grounds:run-1:analysis:{output_hash}%%\n",
        encoding="utf-8",
    )

    state.rebuild_evidence_sets_from_markers(tmp_path)
    row = state.evidence_sets(tmp_path)[0]
    assert row["type"] == "computed"
    assert row["state"] == "complete"

    output.write_text("43\n", encoding="utf-8")
    state.rebuild_evidence_sets_from_markers(tmp_path)
    assert state.evidence_sets(tmp_path)[0]["state"] == "evidence-incomplete"


def test_run_artifact_rejects_unknown_artifact_and_malformed_command(tmp_path: Path) -> None:
    try:
        run_artifact(tmp_path, "missing")
    except ValueError as exc:
        assert "unknown code artifact: missing" in str(exc)
    else:
        raise AssertionError("run_artifact accepted an unknown artifact_id")

    create_code_artifact(
        tmp_path,
        "project-alpha",
        "empty-argv",
        approved_command=[],
    )
    create_code_artifact(
        tmp_path,
        "project-alpha",
        "blank-part",
        approved_command=["python3", ""],
    )
    for artifact_id in ("empty-argv", "blank-part"):
        try:
            run_artifact(tmp_path, artifact_id)
        except ValueError as exc:
            assert "approved_command must be a non-empty argv list" in str(exc)
        else:
            raise AssertionError(f"run_artifact executed malformed command {artifact_id!r}")
