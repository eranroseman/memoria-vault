import json
import os
import tarfile
from datetime import UTC, datetime
from pathlib import Path

import pytest

from memoria.runtime import diagnostics


def test_record_event_writes_content_light_outside_vault(tmp_path, monkeypatch):
    vault = tmp_path / "vault"
    state = tmp_path / "state"
    vault.mkdir()
    monkeypatch.setenv("MEMORIA_DIAGNOSTIC_LEVEL", "warn")

    event = diagnostics.record_event(
        component="ingest",
        level="error",
        code="provider_failure",
        payload={"title": "Secret Draft", "api_key": "0123456789abcdef"},
        details={"path": "projects/private-claim.md", "attempt": 2},
        vault_path=vault,
        state_dir=state,
        now=datetime(2026, 6, 19, 12, 0, tzinfo=UTC),
    )

    assert event is not None
    log = state / "diagnostics-2026-06-19.jsonl"
    row = json.loads(log.read_text(encoding="utf-8"))
    assert row["code"] == "provider_failure"
    assert row["payload_sha256"]
    assert row["payload_length"] > 0
    assert "Secret Draft" not in log.read_text(encoding="utf-8")
    assert row["details"]["path"]["sha256"]
    assert row["details"]["attempt"] == 2


def test_record_event_refuses_vault_state_dir(tmp_path):
    vault = tmp_path / "vault"
    vault.mkdir()

    with pytest.raises(ValueError):
        diagnostics.record_event(
            component="policy",
            level="error",
            code="bad_state_dir",
            state_dir=vault / "system" / "logs",
            vault_path=vault,
        )


def test_record_event_refuses_git_worktree_state_dir(tmp_path):
    repo = tmp_path / "repo"
    (repo / ".git").mkdir(parents=True)
    cwd = Path.cwd()

    try:
        os.chdir(repo)
        with pytest.raises(ValueError):
            diagnostics.record_event(
                component="policy",
                level="error",
                code="bad_state_dir",
                state_dir=repo / "diagnostics",
            )
    finally:
        os.chdir(cwd)


def test_raw_capture_is_ephemeral_and_redacted(tmp_path, monkeypatch):
    monkeypatch.setenv(diagnostics.RAW_ONCE_ENV, "1")
    first = diagnostics.record_event(
        component="mcp",
        level="error",
        code="raw_once",
        payload="Bearer abcdefghijklmnopqrstuvwxyz\nbody text",
        state_dir=tmp_path,
    )
    second = diagnostics.record_event(
        component="mcp",
        level="error",
        code="raw_once_again",
        payload="body text",
        state_dir=tmp_path,
    )

    assert first["raw_capture"] == "ephemeral-redacted"
    assert "abcdefghijklmnopqrstuvwxyz" not in first["payload_redacted"]
    assert "payload_redacted" not in second
    assert diagnostics.RAW_ONCE_ENV not in os.environ


def test_rotation_keeps_bounded_compressed_backups(tmp_path):
    log = tmp_path / "diagnostics-2026-06-19.jsonl"
    log.write_text("x" * 20, encoding="utf-8")
    diagnostics.rotate_logs(tmp_path, max_bytes=10, backups=2)
    log.write_text("y" * 20, encoding="utf-8")
    diagnostics.rotate_logs(tmp_path, max_bytes=10, backups=2)
    log.write_text("z" * 20, encoding="utf-8")
    diagnostics.rotate_logs(tmp_path, max_bytes=10, backups=2)

    backups = sorted(p.name for p in tmp_path.glob("*.gz"))
    assert backups == ["diagnostics-2026-06-19.jsonl.1.gz", "diagnostics-2026-06-19.jsonl.2.gz"]


def test_redacted_bundle_excludes_raw_by_default(tmp_path):
    diagnostics.record_event(
        component="bundle",
        level="error",
        code="with_raw",
        payload="api_key=0123456789abcdef",
        state_dir=tmp_path / "state",
        now=datetime(2026, 6, 19, 12, 0, tzinfo=UTC),
    )
    bundle = diagnostics.create_redacted_bundle(
        tmp_path / "bundle.tgz",
        state_dir=tmp_path / "state",
    )

    with tarfile.open(bundle, "r:gz") as tar:
        names = tar.getnames()
        payload = tar.extractfile("diagnostics-2026-06-19.redacted.jsonl")
        text = payload.read().decode("utf-8") if payload else ""

    assert "README.txt" in names
    assert "api_key" not in text
    assert "payload_sha256" in text


def test_redaction_self_test_blocks_known_sensitive_strings():
    diagnostics.redaction_self_test()
