from __future__ import annotations

import json
from pathlib import Path

import pytest

from memoria_vault.cli import main
from memoria_vault.runtime import state
from tests.helpers import WORKSPACE_SEED, git, patch_pydantic_ai


def write_runner_provider_config(
    workspace: Path, *, local_url: str = "http://model.test/v1"
) -> None:
    config = workspace / ".memoria/config/providers.yaml"
    config.parent.mkdir(parents=True, exist_ok=True)
    config.write_text(
        "\n".join(
            [
                "version: 1",
                "runner_providers:",
                f"  local: {{url: {local_url}, key_env: null}}",
                "  gateway: {url: https://gateway.test/v1, key_env: KILOCODE_API_KEY}",
                "",
            ]
        ),
        encoding="utf-8",
    )


def test_cli_doctor_reports_backup_contract(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    workspace = tmp_path / "workspace"
    assert main(["init", "--workspace", str(workspace), "--yes", "--json"]) == 0
    capsys.readouterr()

    assert main(["doctor", "--workspace", str(workspace), "--json"]) == 0
    report = json.loads(capsys.readouterr().out)

    assert report["ok"] is True
    assert report["backup"]["git_remote"]["configured"] is False
    assert report["backup"]["sqlite_replication"]["configured"] is False
    assert report["backup"]["sqlite_replication"]["runtime_dependency"] is False
    assert report["backup"]["blob_sync"]["configured"] is False
    assert report["backup"]["blob_sync"]["blob_root_exists"] is True

    git(workspace, "remote", "add", "origin", "https://example.invalid/memoria.git")
    (workspace / ".memoria/config/litestream.yaml").write_text("dbs: []\n", encoding="utf-8")
    (workspace / ".memoria/config/blob-sync.yaml").write_text("target: test\n", encoding="utf-8")

    assert main(["doctor", "bundle", "--workspace", str(workspace), "--json"]) == 0
    bundle = json.loads(capsys.readouterr().out)

    assert bundle["backup"]["git_remote"] == {"configured": True, "remotes": ["origin"]}
    assert bundle["backup"]["sqlite_replication"]["configured"] is True
    assert bundle["backup"]["blob_sync"]["configured"] is True


def test_cli_doctor_repair_restores_runtime_seed_files(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    workspace = tmp_path / "workspace"
    assert main(["init", "--workspace", str(workspace), "--yes", "--json"]) == 0
    capsys.readouterr()

    provider_config = workspace / ".memoria/config/providers.yaml"
    seed_provider_config = WORKSPACE_SEED / ".memoria/config/providers.yaml"
    provider_config.write_text("broken: true\n", encoding="utf-8")

    rc = main(["doctor", "--workspace", str(workspace), "--repair", "--json"])
    output = json.loads(capsys.readouterr().out)

    assert rc == 0
    assert output["ok"] is True
    assert output["checks"]["state_db"] is True
    assert "capabilities" not in output["repaired"]
    assert provider_config.read_text(encoding="utf-8") == seed_provider_config.read_text(
        encoding="utf-8"
    )


def test_cli_eval_seeded_error_verdict_uses_seeded_workspace_bundle(
    tmp_path: Path, capsys: pytest.CaptureFixture[str], monkeypatch: pytest.MonkeyPatch
) -> None:
    workspace = tmp_path / "workspace"
    main(["init", "--workspace", str(workspace), "--yes", "--json"])
    capsys.readouterr()
    assert (workspace / ".memoria/eval/alpha15-seeded-errors.json").is_file()

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
        assert runner["mode"] == "live"
        assert runner["provider"] == "gateway"
        assert context.machine == "memoria-cli"
        assert context.actor == "operation"
        return {"passed": True, "metrics": {"expected_errors": 1}}

    monkeypatch.setattr(
        "memoria_vault.runtime.seeded_errors.run_seeded_error_verdict",
        fake_verdict,
    )

    rc = main(
        [
            "eval",
            "seeded-error-verdict",
            "--workspace",
            str(workspace),
            "--mode",
            "live",
            "--json",
            "--idempotency-key",
            "seeded-verdict",
        ]
    )
    output = json.loads(capsys.readouterr().out)

    assert rc == 0
    assert output["ok"] is True
    assert output["result"]["passed"] is True
    with state.connect(workspace) as conn:
        row = conn.execute(
            "SELECT operation_id, args_json FROM operation_requests WHERE request_id = ?",
            ("seeded-verdict",),
        ).fetchone()
    assert row["operation_id"] == "run-seeded-error-verdict"
    assert json.loads(row["args_json"]) == {"mode": "live"}

    assert (
        main(
            [
                "eval",
                "run",
                "--workspace",
                str(workspace),
                "--json",
                "--idempotency-key",
                "eval-run",
            ]
        )
        == 0
    )
    eval_run = json.loads(capsys.readouterr().out)
    assert eval_run["ok"] is True
    assert eval_run["result"]["operation_id"] == "eval-run"
    assert eval_run["result"]["outputs"] == [".memoria/eval/last-run.md"]
    assert eval_run["result"]["dry_run"] is False
    assert (workspace / ".memoria/eval/last-run.md").is_file()


def test_cli_eval_select_models_requires_alpha15_seeded_bundle(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    workspace = tmp_path / "workspace"
    main(["init", "--workspace", str(workspace), "--yes", "--json"])
    capsys.readouterr()
    (workspace / ".memoria/eval/alpha15-seeded-errors.json").unlink()
    (workspace / ".memoria/eval/alpha12-seeded-errors.json").write_text("{}", encoding="utf-8")

    rc = main(
        [
            "eval",
            "select-models",
            "--workspace",
            str(workspace),
            "--operation",
            "run-seeded-error-verdict",
            "--json",
        ]
    )
    output = json.loads(capsys.readouterr().out)

    assert rc == 2
    assert ".memoria/eval/alpha15-seeded-errors.json" in output["error"]


def test_cli_eval_select_models_selects_manifest_runner(
    tmp_path: Path, capsys: pytest.CaptureFixture[str], monkeypatch: pytest.MonkeyPatch
) -> None:
    workspace = tmp_path / "workspace"
    main(["init", "--workspace", str(workspace), "--yes", "--json"])
    capsys.readouterr()
    calls = []

    def fake_verdict(
        vault: Path,
        *,
        template_root: Path,
        bundle_path: Path,
        runner: dict,
        operation_id: str,
        context,
    ) -> dict[str, object]:
        calls.append(
            {
                "vault": vault,
                "template_root": template_root,
                "bundle_path": bundle_path,
                "runner": runner,
                "operation_id": operation_id,
                "machine": context.machine,
            }
        )
        return {
            "passed": True,
            "bar_failures": [],
            "verdict_key": "sha256:pass",
            "non_sandbox_licensed": True,
        }

    monkeypatch.setattr(
        "memoria_vault.runtime.seeded_errors.run_seeded_error_verdict",
        fake_verdict,
    )

    rc = main(
        [
            "eval",
            "select-models",
            "--workspace",
            str(workspace),
            "--operation",
            "run-seeded-error-verdict",
            "--mode",
            "live",
            "--json",
        ]
    )
    output = json.loads(capsys.readouterr().out)

    assert rc == 0
    assert output["ok"] is True
    assert output["selection_count"] == 1
    assert output["failed_count"] == 0
    assert output["selection"]["candidate_count"] == 1
    assert output["selection"]["candidate_source"] == "operation_manifest_runner"
    assert output["selection"]["selected"]["mode"] == "live"
    assert output["selection"]["selected"]["provider"] == "gateway"
    assert output["selection"]["selected"]["model"] == "deterministic-fixture"
    assert output["selection"]["non_sandbox_licensed"] is True
    assert calls[0]["vault"] != workspace
    assert calls[0]["template_root"] == workspace
    assert calls[0]["bundle_path"] == workspace / ".memoria/eval/alpha15-seeded-errors.json"
    assert calls[0]["operation_id"] == "run-seeded-error-verdict"
    assert calls[0]["machine"] == "memoria-cli"


def test_cli_eval_select_models_refuses_failed_candidate(
    tmp_path: Path, capsys: pytest.CaptureFixture[str], monkeypatch: pytest.MonkeyPatch
) -> None:
    workspace = tmp_path / "workspace"
    main(["init", "--workspace", str(workspace), "--yes", "--json"])
    capsys.readouterr()

    monkeypatch.setattr(
        "memoria_vault.runtime.seeded_errors.run_seeded_error_verdict",
        lambda *args, **kwargs: {
            "passed": False,
            "bar_failures": ["recall"],
            "verdict_key": "sha256:fail",
            "non_sandbox_licensed": False,
        },
    )

    rc = main(
        [
            "eval",
            "select-models",
            "--workspace",
            str(workspace),
            "--operation",
            "run-seeded-error-verdict",
            "--json",
        ]
    )
    output = json.loads(capsys.readouterr().out)

    assert rc == 1
    assert output["ok"] is False
    assert output["selection_count"] == 0
    assert output["failed_count"] == 1
    assert output["selection"]["selected"] is None
    assert output["selection"]["attention_required"] is True
    assert output["selection"]["bar_failures"] == ["recall"]


def test_cli_doctor_search_checks_workspace_local_state(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    workspace = tmp_path / "workspace"
    main(["init", "--workspace", str(workspace), "--yes", "--json"])
    capsys.readouterr()

    rc = main(["doctor", "--workspace", str(workspace), "--check", "search", "--json"])
    output = json.loads(capsys.readouterr().out)

    assert rc == 1
    assert output["ok"] is False
    assert output["search_engine"] == "bm25"
    assert output["search_manifest"] == ".memoria/index/search/manifest.json"
    assert output["search_document_count"] == 0
    assert output["checks"]["search_checked_root"] is False
    assert output["checks"]["search_manifest"] is False


def test_cli_doctor_runner_constructs_local_pydantic_ai_agent(
    tmp_path: Path, capsys: pytest.CaptureFixture[str], monkeypatch: pytest.MonkeyPatch
) -> None:
    workspace = tmp_path / "workspace"
    seen = {}

    main(["init", "--workspace", str(workspace), "--yes", "--json"])
    capsys.readouterr()
    monkeypatch.setenv("MEMORIA_MODEL_BASE_URL", "http://127.0.0.1:11434/v1")
    monkeypatch.setenv("MEMORIA_MODEL", "local-test-model")
    patch_pydantic_ai(monkeypatch, seen=seen)

    rc = main(
        [
            "doctor",
            "--workspace",
            str(workspace),
            "--check",
            "runner",
            "--provider",
            "local",
            "--json",
        ]
    )
    output = json.loads(capsys.readouterr().out)

    assert rc == 0
    assert output["ok"] is True
    assert output["provider"] == "local"
    assert output["base_url"] == "http://127.0.0.1:11434/v1"
    assert output["model"] == "local-test-model"
    assert output["checks"]["runner_dependency"] is True
    assert output["checks"]["runner_base_url"] is True
    assert output["checks"]["runner_agent_constructed"] is True
    assert seen["provider_kwargs"] == {"base_url": "http://127.0.0.1:11434/v1"}
    assert seen["model_name"] == "local-test-model"
    assert seen["model"] is not None


def test_cli_doctor_runner_uses_local_default_base_url(
    tmp_path: Path, capsys: pytest.CaptureFixture[str], monkeypatch: pytest.MonkeyPatch
) -> None:
    workspace = tmp_path / "workspace"
    seen = {}

    main(["init", "--workspace", str(workspace), "--yes", "--json"])
    capsys.readouterr()
    for name in (
        "MEMORIA_MODEL_BASE_URL",
        "OPENAI_BASE_URL",
        "MEMORIA_MODEL_API_KEY",
        "OPENAI_API_KEY",
        "KILOCODE_API_KEY",
    ):
        monkeypatch.delenv(name, raising=False)
    patch_pydantic_ai(monkeypatch, seen=seen)

    rc = main(
        [
            "doctor",
            "--workspace",
            str(workspace),
            "--check",
            "runner",
            "--provider",
            "local",
            "--json",
        ]
    )
    output = json.loads(capsys.readouterr().out)

    assert rc == 0
    assert output["ok"] is True
    assert output["base_url"] == "http://127.0.0.1:11434/v1"
    assert output["checks"]["runner_base_url"] is True
    assert seen["provider_kwargs"] == {"base_url": "http://127.0.0.1:11434/v1"}
    assert seen["model_name"] == "doctor"


def test_cli_doctor_runner_live_dispatches_through_pydantic_ai(
    tmp_path: Path, capsys: pytest.CaptureFixture[str], monkeypatch: pytest.MonkeyPatch
) -> None:
    workspace = tmp_path / "workspace"
    seen = {}

    main(["init", "--workspace", str(workspace), "--yes", "--json"])
    capsys.readouterr()
    write_runner_provider_config(workspace)
    monkeypatch.setenv("MEMORIA_MODEL_BASE_URL", "http://model.test/v1")
    monkeypatch.setenv("MEMORIA_MODEL", "live-test-model")
    patch_pydantic_ai(monkeypatch, output="runner ok", seen=seen)

    rc = main(
        [
            "doctor",
            "--workspace",
            str(workspace),
            "--check",
            "runner",
            "--provider",
            "local",
            "--live",
            "--json",
        ]
    )
    output = json.loads(capsys.readouterr().out)

    assert rc == 0
    assert output["ok"] is True
    assert output["checks"]["runner_live_dispatch"] is True
    assert seen["provider_kwargs"] == {"base_url": "http://model.test/v1"}
    assert seen["model_name"] == "live-test-model"
    assert len(seen["models"]) == 2
    assert "Memoria runner is reachable" in seen["prompt"]
    assert seen["model_settings"]["temperature"] == 0


def test_cli_doctor_live_requires_runner_check(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    workspace = tmp_path / "workspace"
    main(["init", "--workspace", str(workspace), "--yes", "--json"])
    capsys.readouterr()

    rc = main(["doctor", "--workspace", str(workspace), "--live", "--json"])
    output = json.loads(capsys.readouterr().out)

    assert rc == 2
    assert output["ok"] is False
    assert output["error"] == "doctor --live is only valid with --check runner"
