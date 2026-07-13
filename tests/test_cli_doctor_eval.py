from __future__ import annotations

import json
import os
import shutil
import subprocess
from contextlib import contextmanager
from pathlib import Path

import pytest

import memoria_vault.cli as cli_module
from memoria_vault.cli import main
from memoria_vault.runtime import backup, state
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


def test_cli_doctor_repair_rejects_symlinked_runtime_before_seed_writes(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    workspace = tmp_path / "workspace"
    assert main(["init", "--workspace", str(workspace), "--yes", "--json"]) == 0
    capsys.readouterr()
    outside_runtime = tmp_path / "outside-runtime"
    (workspace / ".memoria").rename(outside_runtime)
    provider_config = outside_runtime / "config/providers.yaml"
    provider_config.write_text("outside sentinel\n", encoding="utf-8")
    (workspace / ".memoria").symlink_to(outside_runtime, target_is_directory=True)

    rc = main(["doctor", "--workspace", str(workspace), "--repair", "--json"])
    output = json.loads(capsys.readouterr().out)

    assert rc == 2
    assert output["error"] == "workspace runtime path must not be a symlink: .memoria"
    assert provider_config.read_text(encoding="utf-8") == "outside sentinel\n"


def test_cli_doctor_bundle_rejects_symlinked_runtime_before_connect(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    workspace = tmp_path / "workspace"
    workspace.mkdir()
    outside_runtime = tmp_path / "outside-runtime"
    outside_runtime.mkdir()
    (workspace / ".memoria").symlink_to(outside_runtime, target_is_directory=True)
    outside_database = outside_runtime / "memoria.sqlite"

    rc = main(["doctor", "bundle", "--workspace", str(workspace), "--json"])
    output = json.loads(capsys.readouterr().out)

    assert rc == 2
    assert output["error"] == "workspace runtime path must not be a symlink: .memoria"
    assert not outside_database.exists()


@pytest.mark.parametrize("bundle", [False, True])
def test_cli_doctor_maintenance_rejects_redirected_sqlite_rollback_journal(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
    bundle: bool,
) -> None:
    workspace = tmp_path / "workspace"
    assert main(["init", "--workspace", str(workspace), "--yes", "--json"]) == 0
    capsys.readouterr()
    rollback_journal = Path(f"{workspace / state.DB_REL}-journal")
    rollback_journal.unlink(missing_ok=True)
    outside_journal = tmp_path / "outside-journal"
    rollback_journal.symlink_to(outside_journal)
    command = ["doctor"]
    if bundle:
        command.append("bundle")
    command.extend(["--workspace", str(workspace), "--json"])
    if not bundle:
        command.append("--repair")

    rc = main(command)
    output = json.loads(capsys.readouterr().out)

    assert rc == 2
    assert output["error"] == (
        "workspace runtime path must not be a symlink: .memoria/memoria.sqlite-journal"
    )
    assert not outside_journal.exists()


def test_cli_doctor_repair_rejects_symlinked_seed_file(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    workspace = tmp_path / "workspace"
    assert main(["init", "--workspace", str(workspace), "--yes", "--json"]) == 0
    capsys.readouterr()
    provider_config = workspace / ".memoria/config/providers.yaml"
    outside_config = tmp_path / "outside-providers.yaml"
    outside_config.write_text("outside sentinel\n", encoding="utf-8")
    provider_config.unlink()
    provider_config.symlink_to(outside_config)

    rc = main(["doctor", "--workspace", str(workspace), "--repair", "--json"])
    output = json.loads(capsys.readouterr().out)

    assert rc == 2
    assert "symlink" in output["error"]
    assert outside_config.read_text(encoding="utf-8") == "outside sentinel\n"


@pytest.mark.parametrize(
    "redirect_rel",
    [
        ".memoria/eval",
        ".memoria/patterns",
        ".memoria/schemas",
        ".githooks/pre-commit",
        ".obsidian",
        "system",
        "index.md",
        ".git/config",
    ],
)
def test_cli_doctor_repair_preflights_every_write_target(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
    monkeypatch: pytest.MonkeyPatch,
    redirect_rel: str,
) -> None:
    workspace = tmp_path / "workspace"
    assert main(["init", "--workspace", str(workspace), "--yes", "--json"]) == 0
    capsys.readouterr()
    redirected = workspace / redirect_rel
    real_is_junction = Path.is_junction
    real_repair = cli_module._repair_workspace
    repair_called = False

    def fake_is_junction(path: Path) -> bool:
        return Path(path) == redirected or real_is_junction(path)

    def record_repair(candidate: Path) -> list[str]:
        nonlocal repair_called
        repair_called = True
        return real_repair(candidate)

    monkeypatch.setattr(Path, "is_junction", fake_is_junction)
    monkeypatch.setattr("memoria_vault.cli._repair_workspace", record_repair)

    rc = main(["doctor", "--workspace", str(workspace), "--repair", "--json"])
    output = json.loads(capsys.readouterr().out)

    assert rc == 2
    assert "redirect" in output["error"]
    assert repair_called is False


@pytest.mark.parametrize("transaction_type", ["backup", "restore"])
@pytest.mark.parametrize("bundle", [False, True])
def test_cli_doctor_maintenance_rejects_pending_transactions(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
    transaction_type: str,
    bundle: bool,
) -> None:
    workspace = tmp_path / "workspace"
    assert main(["init", "--workspace", str(workspace), "--yes", "--json"]) == 0
    capsys.readouterr()
    if transaction_type == "restore":
        rollback = tmp_path / ".workspace.restore-rollback-doctor"
        stage = tmp_path / ".workspace.restore-stage-doctor"
        rollback.mkdir()
        stage.mkdir()
        backup._write_restore_transaction(workspace, rollback, stage)
    else:
        target = tmp_path / "doctor-backup-target"
        rollback = tmp_path / ".doctor-backup-target.rollback-doctor"
        stage = tmp_path / ".doctor-backup-target.stage-doctor"
        assert (
            backup.create_backup(workspace, stage, actor="pi", machine="test-doctor")["ok"] is True
        )
        backup._write_backup_transaction(workspace, target, rollback, stage)

    command = ["doctor"]
    if bundle:
        command.append("bundle")
    command.extend(["--workspace", str(workspace), "--json"])
    if not bundle:
        command.append("--repair")

    rc = main(command)
    output = json.loads(capsys.readouterr().out)

    assert rc == 2
    assert output["error"] == f"interrupted {transaction_type} requires memoria workspace recover"


def test_cli_doctor_repair_rechecks_write_targets_after_lock(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    workspace = tmp_path / "workspace"
    assert main(["init", "--workspace", str(workspace), "--yes", "--json"]) == 0
    capsys.readouterr()
    outside_index = tmp_path / "outside-index.md"
    outside_index.write_text("outside sentinel\n", encoding="utf-8")
    repair_called = False

    @contextmanager
    def redirecting_lock(_workspace: Path):
        index = workspace / "index.md"
        index.unlink()
        index.symlink_to(outside_index)
        yield

    def record_repair(_workspace: Path) -> list[str]:
        nonlocal repair_called
        repair_called = True
        return []

    monkeypatch.setattr(cli_module, "_workspace_lock", redirecting_lock)
    monkeypatch.setattr(cli_module, "_repair_workspace", record_repair)

    rc = main(["doctor", "--workspace", str(workspace), "--repair", "--json"])
    output = json.loads(capsys.readouterr().out)

    assert rc == 2
    assert "symlink or junction" in output["error"]
    assert repair_called is False
    assert outside_index.read_text(encoding="utf-8") == "outside sentinel\n"


def test_cli_doctor_bundle_rechecks_pending_transaction_after_lock(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    workspace = tmp_path / "workspace"
    assert main(["init", "--workspace", str(workspace), "--yes", "--json"]) == 0
    capsys.readouterr()
    rollback = tmp_path / ".workspace.restore-rollback-doctor-race"
    stage = tmp_path / ".workspace.restore-stage-doctor-race"
    rollback.mkdir()
    stage.mkdir()
    connect_called = False
    real_connect = state.connect

    @contextmanager
    def transaction_starting_lock(_workspace: Path):
        backup._write_restore_transaction(workspace, rollback, stage)
        yield

    def record_connect(_workspace: Path):
        nonlocal connect_called
        connect_called = True
        return real_connect(_workspace)

    monkeypatch.setattr(cli_module, "_workspace_lock", transaction_starting_lock)
    monkeypatch.setattr(cli_module.state, "connect", record_connect)

    rc = main(["doctor", "bundle", "--workspace", str(workspace), "--json"])
    output = json.loads(capsys.readouterr().out)

    assert rc == 2
    assert output["error"] == "interrupted restore requires memoria workspace recover"
    assert connect_called is False


def test_cli_doctor_repair_rejects_gitfile_redirect(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    workspace = tmp_path / "workspace"
    assert main(["init", "--workspace", str(workspace), "--yes", "--json"]) == 0
    capsys.readouterr()
    outside_git = tmp_path / "outside-git"
    (workspace / ".git").rename(outside_git)
    (workspace / ".git").write_text(f"gitdir: {outside_git}\n", encoding="utf-8")
    repair_called = False

    def record_repair(_workspace: Path) -> list[str]:
        nonlocal repair_called
        repair_called = True
        return []

    monkeypatch.setattr(cli_module, "_repair_workspace", record_repair)

    rc = main(["doctor", "--workspace", str(workspace), "--repair", "--json"])
    output = json.loads(capsys.readouterr().out)

    assert rc == 2
    assert output["error"] == "workspace Git metadata must be a directory"
    assert repair_called is False


def test_cli_doctor_repair_rejects_git_common_directory_indirection(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    workspace = tmp_path / "workspace"
    assert main(["init", "--workspace", str(workspace), "--yes", "--json"]) == 0
    capsys.readouterr()
    (workspace / ".git/commondir").write_text(str(tmp_path / "outside-git"), encoding="utf-8")
    repair_called = False

    def record_repair(_workspace: Path) -> list[str]:
        nonlocal repair_called
        repair_called = True
        return []

    monkeypatch.setattr(cli_module, "_repair_workspace", record_repair)

    rc = main(["doctor", "--workspace", str(workspace), "--repair", "--json"])
    output = json.loads(capsys.readouterr().out)

    assert rc == 2
    assert output["error"] == "workspace Git common-directory indirection is not supported"
    assert repair_called is False


def test_cli_doctor_repair_ignores_git_environment_redirects(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    workspace = tmp_path / "workspace"
    assert main(["init", "--workspace", str(workspace), "--yes", "--json"]) == 0
    capsys.readouterr()
    outside_git = tmp_path / "outside.git"
    subprocess.run(
        ["git", "init", "--bare", "-q", str(outside_git)],
        check=True,
        text=True,
        capture_output=True,
    )
    outside_config = outside_git / "config"
    subprocess.run(
        ["git", "--git-dir", str(outside_git), "remote", "add", "outside", "test://outside"],
        check=True,
    )
    original_config = outside_config.read_bytes()
    monkeypatch.setenv("GIT_DIR", str(outside_git))
    monkeypatch.setenv("GIT_WORK_TREE", str(workspace))
    monkeypatch.setenv("GIT_CONFIG_NOSYSTEM", "1")
    monkeypatch.setenv("GIT_CONFIG_GLOBAL", os.devnull)

    rc = main(["doctor", "--workspace", str(workspace), "--repair", "--json"])
    output = json.loads(capsys.readouterr().out)

    assert rc == 0
    assert outside_config.read_bytes() == original_config
    assert output["backup"]["git_remote"] == {"configured": False, "remotes": []}


@pytest.mark.skipif(os.name == "nt", reason="uses a POSIX Git clean-filter command")
def test_cli_doctor_repair_does_not_run_repository_clean_filters(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    workspace = tmp_path / "workspace"
    assert main(["init", "--workspace", str(workspace), "--yes", "--json"]) == 0
    capsys.readouterr()
    shutil.rmtree(workspace / ".git")
    git(workspace, "init", "-q")
    sentinel = tmp_path / "clean-filter-ran"
    (workspace / ".gitattributes").write_text("* filter=doctorprobe\n", encoding="utf-8")
    git(
        workspace,
        "config",
        "filter.doctorprobe.clean",
        f"sh -c 'touch {sentinel}; cat'",
    )

    rc = main(["doctor", "--workspace", str(workspace), "--repair", "--json"])

    assert rc == 0
    assert not sentinel.exists()


def test_cli_doctor_repair_does_not_commit_existing_files_when_creating_git(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    workspace = tmp_path / "workspace"
    assert main(["init", "--workspace", str(workspace), "--yes", "--json"]) == 0
    capsys.readouterr()
    shutil.rmtree(workspace / ".git")
    (workspace / "operator-notes.md").write_text("private draft\n", encoding="utf-8")

    rc = main(["doctor", "--workspace", str(workspace), "--repair", "--json"])
    head = subprocess.run(
        ["git", "rev-parse", "--verify", "HEAD"],
        cwd=workspace,
        check=False,
        text=True,
        capture_output=True,
    )

    assert rc == 0
    assert (workspace / ".git").is_dir()
    assert head.returncode != 0
    assert (workspace / "operator-notes.md").read_text(encoding="utf-8") == "private draft\n"


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
