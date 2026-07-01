"""Graded-loudness routing helpers."""

import json

from memoria_vault.runtime.subsystems.lib import inbox, loudness


def test_alert_card_records_push_attempt_without_telegram_config(tmp_path, monkeypatch):
    monkeypatch.delenv("MEMORIA_TELEGRAM_BOT_TOKEN", raising=False)
    monkeypatch.delenv("TELEGRAM_BOT_TOKEN", raising=False)
    monkeypatch.delenv("MEMORIA_TELEGRAM_CHAT_ID", raising=False)
    monkeypatch.delenv("TELEGRAM_CHAT_ID", raising=False)

    inbox.write_finding(
        tmp_path, "alert", "Critical drift", "system is stopped", "linter", loudness="alert"
    )

    rows = (tmp_path / loudness.PUSH_LOG_RELPATH).read_text(encoding="utf-8").splitlines()
    assert len(rows) == 1
    row = json.loads(rows[0])
    assert row["loudness"] == "alert"
    assert row["status"] == "not-configured"


def test_notice_card_stays_pull_only_without_push_log(tmp_path):
    inbox.write_proposal(
        tmp_path,
        "candidate",
        "Maybe",
        "read it",
        "useful",
        "weak",
        "gap",
        "likely",
        "librarian",
        loudness="notice",
    )

    assert not (tmp_path / loudness.PUSH_LOG_RELPATH).exists()


def test_open_blockers_only_reads_proposed_block_cards(tmp_path):
    (tmp_path / "inbox").mkdir()
    (tmp_path / "inbox/open.md").write_text(
        "---\ntitle: Open block\ntype: alert\nlifecycle: proposed\nloudness: block\n---\n",
        encoding="utf-8",
    )
    (tmp_path / "inbox/resolved.md").write_text(
        "---\ntitle: Resolved block\ntype: alert\nlifecycle: current\nloudness: block\n---\n",
        encoding="utf-8",
    )
    (tmp_path / "inbox/notice.md").write_text(
        "---\ntitle: Notice\ntype: flag\nlifecycle: proposed\nloudness: notice\n---\n",
        encoding="utf-8",
    )

    blockers = loudness.open_blockers(tmp_path)
    assert blockers == [{"path": "inbox/open.md", "title": "Open block", "type": "alert"}]
