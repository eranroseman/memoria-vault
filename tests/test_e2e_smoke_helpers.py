from __future__ import annotations

from pathlib import Path

import pytest

from scripts.test_vault import e2e_smoke


def test_stage_labels_preserve_e2e_smoke_order() -> None:
    assert e2e_smoke.STAGE_ORDER == (
        "vault-assembly-1",
        "vault-assembly-2",
        "vault-assembly-3",
        "commit-gate",
        "offline-ingest-1",
        "offline-ingest-2",
        "workflow-replay",
        "final-integrity",
    )
    assert [e2e_smoke.STAGE_LABELS[name].split(":", 1)[0] for name in e2e_smoke.STAGE_ORDER] == [
        "1. vault-assembly",
        "2. vault-assembly",
        "3. vault-assembly",
        "4. commit-gate",
        "5. offline-ingest",
        "6. offline-ingest",
        "7. workflow-replay",
        "8. final-integrity",
    ]


def test_final_verdict_accepts_pass_or_review_only() -> None:
    e2e_smoke.assert_final_verdict("8 finding(s) -- verdict: REVIEW")
    e2e_smoke.assert_final_verdict("0 finding(s) -- verdict: PASS")
    with pytest.raises(AssertionError):
        e2e_smoke.assert_final_verdict("1 finding(s) -- verdict: FAIL")


def test_assert_executable_reports_missing_path(tmp_path) -> None:
    with pytest.raises(AssertionError, match="missing helper"):
        e2e_smoke.assert_executable(tmp_path / "missing", "missing helper")


def test_test_vault_root_defaults_to_named_test_vault(monkeypatch) -> None:
    monkeypatch.delenv("MEMORIA_TEST_ROOT", raising=False)

    assert e2e_smoke._test_vault_root() == Path("~/memoria-vault/test-vault").expanduser()


def test_test_vault_root_honors_memoria_test_root(monkeypatch, tmp_path) -> None:
    monkeypatch.setenv("MEMORIA_TEST_ROOT", str(tmp_path))

    assert e2e_smoke._test_vault_root() == tmp_path


def test_run_smoke_rebuilds_and_leaves_named_test_vault_root(monkeypatch, tmp_path) -> None:
    test_vault = tmp_path / "test_vault"
    test_vault.mkdir()
    (test_vault / "stale.txt").write_text("old", encoding="utf-8")
    seen: list[Path] = []

    def record_stage(root: Path, vault: Path, env: dict[str, str]) -> None:
        seen.append(vault)
        (vault / "smoke-marker.txt").write_text("new", encoding="utf-8")

    monkeypatch.setattr(e2e_smoke, "_test_vault_root", lambda: test_vault)
    monkeypatch.setattr(e2e_smoke, "_env", lambda root: {})
    monkeypatch.setattr(e2e_smoke, "_vault_assembly", record_stage)
    monkeypatch.setattr(e2e_smoke, "_commit_gate", lambda vault, env: None)
    monkeypatch.setattr(e2e_smoke, "_offline_ingest", lambda root, vault: None)
    monkeypatch.setattr(e2e_smoke, "_workflow_replay", lambda root, vault, env: None)
    monkeypatch.setattr(e2e_smoke, "_final_integrity", lambda vault, env: None)

    e2e_smoke.run_smoke(root=tmp_path)

    assert seen == [test_vault]
    assert not (test_vault / "stale.txt").exists()
    assert (test_vault / "smoke-marker.txt").read_text(encoding="utf-8") == "new"
