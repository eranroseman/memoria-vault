"""Graded-loudness routing helpers."""

from memoria_vault.runtime.subsystems.lib import inbox, loudness


def test_alert_card_writes_no_push_log(tmp_path):
    inbox.write_finding(
        tmp_path, "alert", "Critical drift", "system is stopped", "linter", loudness="alert"
    )

    assert not list(tmp_path.rglob("*push*.jsonl"))


def test_notice_card_writes_no_push_log(tmp_path):
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

    assert not list(tmp_path.rglob("*push*.jsonl"))


def test_open_blockers_only_reads_open_block_attention_projections(tmp_path):
    (tmp_path / "inbox").mkdir()
    (tmp_path / "inbox/open.md").write_text(
        "---\n"
        "title: Open block\n"
        "projection: attention\n"
        "attention_kind: alert\n"
        "attention_status: open\n"
        "loudness: block\n"
        "---\n",
        encoding="utf-8",
    )
    (tmp_path / "inbox/resolved.md").write_text(
        "---\n"
        "title: Resolved block\n"
        "projection: attention\n"
        "attention_kind: alert\n"
        "attention_status: resolved\n"
        "loudness: block\n"
        "---\n",
        encoding="utf-8",
    )
    (tmp_path / "inbox/notice.md").write_text(
        "---\n"
        "title: Notice\n"
        "projection: attention\n"
        "attention_kind: flag\n"
        "attention_status: open\n"
        "loudness: notice\n"
        "---\n",
        encoding="utf-8",
    )
    (tmp_path / "inbox/old-shape.md").write_text(
        "---\ntitle: Old shape\ntype: alert\nlifecycle: proposed\nloudness: block\n---\n",
        encoding="utf-8",
    )

    blockers = loudness.open_blockers(tmp_path)
    assert blockers == [{"path": "inbox/open.md", "title": "Open block", "type": "alert"}]
