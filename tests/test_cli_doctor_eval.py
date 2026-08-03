from __future__ import annotations

import json
import os
import shutil
import sqlite3
import subprocess
from contextlib import contextmanager
from pathlib import Path

import pytest

import memoria_vault.cli as cli_module
from memoria_vault.cli import main
from memoria_vault.runtime import backup, operations, state
from tests.cli_test_helpers import write_runner_provider_config
from tests.helpers import LIVE_USAGE, WORKSPACE_SEED, git, patch_pydantic_ai

pytestmark = pytest.mark.contract


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


def test_cli_doctor_reports_credential_registry_rows(
    tmp_path: Path, capsys: pytest.CaptureFixture[str], monkeypatch: pytest.MonkeyPatch
) -> None:
    workspace = tmp_path / "workspace"
    monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path / "config"))
    assert main(["init", "--workspace", str(workspace), "--yes", "--json"]) == 0
    capsys.readouterr()
    for name in (
        "KILOCODE_API_KEY",
        "OPENALEX_API_KEY",
        "SEMANTIC_SCHOLAR_API_KEY",
        "PUBMED_API_KEY",
        "GITHUB_TOKEN",
        "NCBI_EMAIL",
    ):
        monkeypatch.delenv(name, raising=False)
    monkeypatch.setenv("OPENALEX_API_KEY", "env-key")

    rc = main(["doctor", "--workspace", str(workspace), "--json"])
    report = json.loads(capsys.readouterr().out)

    assert rc == 0
    rows = {row["name"]: row for row in report["credentials"]}
    required = rows["KILOCODE_API_KEY"]
    assert required["class"] == "required-for-operation"
    assert required["status"] == "unset"
    assert "memoria secrets set KILOCODE_API_KEY" in required["effect_when_unset"]
    assert rows["OPENALEX_API_KEY"] == {
        "name": "OPENALEX_API_KEY",
        "class": "enhancing",
        "status": "set",
        "source": "env",
        "effect_when_unset": "openalex keyless polite-pool mode (lower rate limits)",
    }
    assert rows["NCBI_EMAIL"]["class"] == "identity"
    assert report["ok"] is True


def test_cli_doctor_reports_refused_secrets_warning_without_secret(
    tmp_path: Path, capsys: pytest.CaptureFixture[str], monkeypatch: pytest.MonkeyPatch
) -> None:
    workspace = tmp_path / "workspace"
    monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path / "config"))
    assert main(["init", "--workspace", str(workspace), "--yes", "--json"]) == 0
    capsys.readouterr()
    secret_file = tmp_path / "config" / "memoria" / "secrets.env"
    secret_file.parent.mkdir(parents=True, exist_ok=True)
    secret_file.write_text("OPENALEX_API_KEY=private-secret\n", encoding="utf-8")
    secret_file.chmod(0o644)

    rc = main(["doctor", "--workspace", str(workspace), "--json"])

    captured = capsys.readouterr()
    report = json.loads(captured.out)
    assert rc == 0
    assert "world-readable" in report["warning"]
    assert "world-readable" in captured.err
    assert "private-secret" not in captured.out
    assert "private-secret" not in captured.err


@pytest.mark.parametrize(
    ("command", "expected_rc"),
    [
        (["doctor"], 0),
        (["doctor", "--check", "search"], 1),
        (["doctor", "--check", "runner", "--provider", "local"], 0),
        (["doctor", "bundle"], 0),
        (["doctor", "self-test"], 0),
    ],
)
def test_cli_doctor_report_modes_include_credential_rows(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
    monkeypatch: pytest.MonkeyPatch,
    command: list[str],
    expected_rc: int,
) -> None:
    workspace = tmp_path / "workspace"
    monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path / "config"))
    for name in (
        "KILOCODE_API_KEY",
        "OPENALEX_API_KEY",
        "SEMANTIC_SCHOLAR_API_KEY",
        "PUBMED_API_KEY",
        "GITHUB_TOKEN",
        "NCBI_EMAIL",
    ):
        monkeypatch.delenv(name, raising=False)
    assert main(["init", "--workspace", str(workspace), "--yes", "--json"]) == 0
    capsys.readouterr()
    secret_file = tmp_path / "config" / "memoria" / "secrets.env"
    secret_file.parent.mkdir(parents=True, exist_ok=True)
    secret_file.write_text("OPENALEX_API_KEY=private-secret\n", encoding="utf-8")
    secret_file.chmod(0o644)
    monkeypatch.setattr(
        cli_module,
        "_runner_status",
        lambda *_args, **_kwargs: {
            "checks": {
                "runner_dependency": True,
                "runner_base_url": True,
                "runner_agent_constructed": True,
            },
            "provider": "local",
            "base_url": "http://127.0.0.1:11434/v1",
            "model": "doctor",
            "error": None,
        },
    )

    rc = main([*command, "--workspace", str(workspace), "--json"])
    captured = capsys.readouterr()
    report = json.loads(captured.out)

    assert rc == expected_rc
    assert report["credentials"]
    assert "world-readable" in report["warning"]
    assert "world-readable" in captured.err
    assert "private-secret" not in captured.out + captured.err
    assert all(
        {"name", "class", "status", "source", "effect_when_unset"} <= row.keys()
        for row in report["credentials"]
    )


def test_cli_doctor_passes_startup_secret_snapshot_to_credential_report(
    tmp_path: Path, capsys: pytest.CaptureFixture[str], monkeypatch: pytest.MonkeyPatch
) -> None:
    from memoria_vault.runtime import secrets as secrets_module

    workspace = tmp_path / "workspace"
    monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path / "config"))
    monkeypatch.delenv("OPENALEX_API_KEY", raising=False)
    assert main(["init", "--workspace", str(workspace), "--yes", "--json"]) == 0
    capsys.readouterr()
    secret_file = tmp_path / "config" / "memoria" / "secrets.env"
    secret_file.parent.mkdir(parents=True, exist_ok=True)
    secret_file.write_text("OPENALEX_API_KEY=file-secret\n", encoding="utf-8")
    secret_file.chmod(0o600)
    seen: list[tuple[Path | None, object]] = []
    real_report = secrets_module.credential_report

    def report_spy(
        report_workspace: Path | None, *, loaded_from_file: object = None
    ) -> list[dict[str, str]]:
        seen.append((report_workspace, loaded_from_file))
        return real_report(report_workspace, loaded_from_file=loaded_from_file)

    monkeypatch.setattr(secrets_module, "credential_report", report_spy)
    assert main(["doctor", "--workspace", str(workspace), "--json"]) == 0
    captured = capsys.readouterr()
    report = json.loads(captured.out)

    assert seen == [(workspace, frozenset({"OPENALEX_API_KEY"}))]
    assert {row["name"]: row for row in report["credentials"]}["OPENALEX_API_KEY"][
        "source"
    ] == "file"
    assert "file-secret" not in captured.out + captured.err


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


def test_cli_doctor_repair_restores_dropped_schema_objects(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """Repair heals a damaged current-version DB, not just seed files.

    connect() skips schema.sql when user_version is current, so a dropped
    table stays dropped until a repair path re-runs the DDL explicitly
    (state.ensure_schema, reached via _initialize_workspace_files).
    """
    workspace = tmp_path / "workspace"
    assert main(["init", "--workspace", str(workspace), "--yes", "--json"]) == 0
    capsys.readouterr()

    with sqlite3.connect(workspace / state.DB_REL) as conn:
        conn.execute("DROP TABLE evidence_bindings")

    rc = main(["doctor", "--workspace", str(workspace), "--repair", "--json"])
    output = json.loads(capsys.readouterr().out)

    assert rc == 0
    assert output["ok"] is True
    with state.connect(workspace) as conn:
        row = conn.execute(
            "SELECT name FROM sqlite_master WHERE type = 'table' AND name = 'evidence_bindings'"
        ).fetchone()
    assert row is not None


def test_cli_doctor_repair_does_not_overwrite_agent_bundle(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    workspace = tmp_path / "workspace"
    assert main(["init", "--workspace", str(workspace), "--yes", "--json"]) == 0
    capsys.readouterr()
    sentinels = {
        ".claude/hooks/write_perimeter.py": b"PI-owned hook\n",
        ".claude/settings.json": b'{"PI-owned": true}\n',
        ".codex/hooks.json": b'{"PI-owned": true}\n',
        ".mcp.json": b'{"PI-owned": true}\n',
        "CLAUDE.md": b"PI-owned instructions\n",
    }
    for rel, value in sentinels.items():
        (workspace / rel).write_bytes(value)

    assert main(["doctor", "--workspace", str(workspace), "--repair", "--json"]) == 0
    capsys.readouterr()

    assert {rel: (workspace / rel).read_bytes() for rel in sentinels} == sentinels


def test_cli_doctor_repair_does_not_create_agent_bundle(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    workspace = tmp_path / "workspace"
    assert main(["init", "--workspace", str(workspace), "--yes", "--json"]) == 0
    capsys.readouterr()
    shutil.rmtree(workspace / ".claude")
    shutil.rmtree(workspace / ".codex")
    (workspace / ".mcp.json").unlink()
    (workspace / "CLAUDE.md").unlink()

    assert main(["doctor", "--workspace", str(workspace), "--repair", "--json"]) == 0
    capsys.readouterr()

    assert not any(
        (workspace / rel).exists() for rel in (".claude", ".codex", ".mcp.json", "CLAUDE.md")
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
    assert output["search_backend"] == "bm25"
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
    assert seen["provider_kwargs"] == {
        "base_url": "http://127.0.0.1:11434/v1",
        "api_key": "api-key-not-set",
    }
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
    assert seen["provider_kwargs"] == {
        "base_url": "http://127.0.0.1:11434/v1",
        "api_key": "api-key-not-set",
    }
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
    assert seen["provider_kwargs"] == {
        "base_url": "http://model.test/v1",
        "api_key": "api-key-not-set",
    }
    assert seen["model_name"] == "live-test-model"
    assert len(seen["models"]) == 2
    assert "Memoria runner is reachable" in seen["prompt"]
    assert seen["model_settings"]["temperature"] == 0


def test_cli_doctor_live_spends_the_token_ceiling_and_then_reports_the_breaker(
    tmp_path: Path, capsys: pytest.CaptureFixture[str], monkeypatch: pytest.MonkeyPatch
) -> None:
    """Doctor is a live resource consumer, not durable model-call provenance."""
    workspace = tmp_path / "workspace"
    main(["init", "--workspace", str(workspace), "--yes", "--json"])
    capsys.readouterr()
    write_runner_provider_config(workspace)
    monkeypatch.setitem(operations._TOKEN_LEDGER, "total_tokens", 0)
    monkeypatch.setenv(operations.TOKEN_CEILING_ENV, str(LIVE_USAGE["total_tokens"]))
    seen = patch_pydantic_ai(monkeypatch, output="runner ok")
    command = [
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

    assert main(command) == 0
    first = json.loads(capsys.readouterr().out)

    assert first["checks"]["runner_live_dispatch"] is True
    assert first["error"] == ""
    assert operations._TOKEN_LEDGER["total_tokens"] == LIVE_USAGE["total_tokens"]
    assert seen["usage_calls"] == 1

    assert main(command) == 1
    second = json.loads(capsys.readouterr().out)

    # runner_agent_constructed stays True: the refusal came from the breaker
    # inside the dispatch seam, not from an earlier adapter or key failure.
    assert second["checks"]["runner_agent_constructed"] is True
    assert second["checks"]["runner_live_dispatch"] is False
    assert "model token ceiling reached" in second["error"]
    assert operations.TOKEN_CEILING_ENV in second["error"]
    # Nothing past the breaker ran: no second harvest, no second charge.
    assert seen["usage_calls"] == 1
    assert operations._TOKEN_LEDGER["total_tokens"] == LIVE_USAGE["total_tokens"]
    assert state.read_event_log(workspace, event_types=("model_call",)) == []


def test_cli_doctor_gateway_refuses_missing_key_before_adapter_construction(
    tmp_path: Path, capsys: pytest.CaptureFixture[str], monkeypatch: pytest.MonkeyPatch
) -> None:
    workspace = tmp_path / "workspace"
    assert main(["init", "--workspace", str(workspace), "--yes", "--json"]) == 0
    capsys.readouterr()
    write_runner_provider_config(workspace)
    sentinels = {
        "MEMORIA_MODEL_API_KEY": "legacy-model-secret",
        "OPENAI_API_KEY": "legacy-openai-secret",
        "KILOCODE_API_KEY": "",
    }
    for name, value in sentinels.items():
        monkeypatch.setenv(name, value)
    seen = patch_pydantic_ai(monkeypatch)
    loader_calls: list[None] = []

    def unexpected_loader() -> tuple[object, object, object]:
        loader_calls.append(None)
        raise AssertionError("pydantic-ai loader must not run without a configured gateway key")

    monkeypatch.setattr(
        "memoria_vault.runtime.operations._load_pydantic_ai_openai", unexpected_loader
    )

    rc = main(
        [
            "doctor",
            "--workspace",
            str(workspace),
            "--check",
            "runner",
            "--provider",
            "gateway",
            "--live",
            "--json",
        ]
    )
    captured = capsys.readouterr()
    payload = json.loads(captured.out)

    assert rc == 1
    assert payload["ok"] is False
    assert payload["error"] == (
        "provider gateway requires KILOCODE_API_KEY - set it: memoria secrets set KILOCODE_API_KEY"
    )
    assert payload["checks"]["runner_dependency"] is False
    assert payload["checks"]["runner_agent_constructed"] is False
    assert payload["checks"]["runner_live_dispatch"] is False
    assert seen == {}
    assert loader_calls == []
    assert "legacy-model-secret" not in captured.out + captured.err
    assert "legacy-openai-secret" not in captured.out + captured.err


def test_cli_doctor_gateway_uses_configured_key_for_construction_and_dispatch(
    tmp_path: Path, capsys: pytest.CaptureFixture[str], monkeypatch: pytest.MonkeyPatch
) -> None:
    workspace = tmp_path / "workspace"
    assert main(["init", "--workspace", str(workspace), "--yes", "--json"]) == 0
    capsys.readouterr()
    write_runner_provider_config(workspace)
    monkeypatch.setenv("MEMORIA_MODEL_API_KEY", "legacy-model-secret")
    monkeypatch.setenv("OPENAI_API_KEY", "legacy-openai-secret")
    monkeypatch.setenv("KILOCODE_API_KEY", "gateway-key")
    seen = patch_pydantic_ai(monkeypatch, output="runner ok")

    rc = main(
        [
            "doctor",
            "--workspace",
            str(workspace),
            "--check",
            "runner",
            "--provider",
            "gateway",
            "--live",
            "--json",
        ]
    )
    payload = json.loads(capsys.readouterr().out)

    expected = {"base_url": "https://gateway.test/v1", "api_key": "gateway-key"}
    assert rc == 0
    assert payload["ok"] is True
    assert payload["checks"]["runner_agent_constructed"] is True
    assert payload["checks"]["runner_live_dispatch"] is True
    assert seen["provider_kwargs_list"] == [expected, expected]


@pytest.mark.parametrize("failure_site", ["provider", "dispatch"])
def test_cli_doctor_gateway_sdk_failure_does_not_reflect_configured_key(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
    monkeypatch: pytest.MonkeyPatch,
    failure_site: str,
) -> None:
    workspace = tmp_path / "workspace"
    assert main(["init", "--workspace", str(workspace), "--yes", "--json"]) == 0
    capsys.readouterr()
    write_runner_provider_config(workspace)
    configured_key = "gateway-key"
    monkeypatch.setenv("KILOCODE_API_KEY", configured_key)

    class FakeProvider:
        def __init__(self, **kwargs: object) -> None:
            if failure_site == "provider":
                raise RuntimeError(f"provider rejected {configured_key}")

    class FakeModel:
        def __init__(self, model_name: str, *, provider: object) -> None:
            pass

    class FakeAgent:
        def __init__(self, model: object) -> None:
            pass

        def run_sync(self, prompt: str, *, model_settings: dict[str, object]) -> object:
            if failure_site == "dispatch":
                raise RuntimeError(f"downstream rejected {configured_key}")
            return object()

    monkeypatch.setattr(
        "memoria_vault.runtime.operations._load_pydantic_ai_openai",
        lambda: (FakeAgent, FakeModel, FakeProvider),
    )

    rc = main(
        [
            "doctor",
            "--workspace",
            str(workspace),
            "--check",
            "runner",
            "--provider",
            "gateway",
            "--live",
            "--json",
        ]
    )
    captured = capsys.readouterr()
    payload = json.loads(captured.out)

    assert rc == 1
    assert payload["error"] == "pydantic-ai model request failed"
    assert payload["checks"]["runner_dependency"] is True
    assert payload["checks"]["runner_agent_constructed"] is (failure_site == "dispatch")
    assert payload["checks"]["runner_live_dispatch"] is False
    assert configured_key not in captured.out + captured.err


def test_cli_doctor_live_requires_runner_check(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    workspace = tmp_path / "workspace"
    main(["init", "--workspace", str(workspace), "--yes", "--json"])
    capsys.readouterr()

    rc = main(["doctor", "--workspace", str(workspace), "--live", "--json"])
    output = json.loads(capsys.readouterr().out)

    assert rc == 2
    assert output == {
        "ok": False,
        "error": "doctor --live is only valid with --check runner",
    }
