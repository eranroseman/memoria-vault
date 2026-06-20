from __future__ import annotations

import json
from datetime import UTC, datetime

from memoria.runtime.jsonl import append_jsonl, iter_jsonl
from memoria.runtime.time import parse_iso, utc_z
from memoria.runtime.vaultio import (
    iter_markdown,
    parse_frontmatter,
    read_frontmatter,
    safe_read,
)


def test_parse_frontmatter_accepts_nested_yaml() -> None:
    data = parse_frontmatter(
        '---\ntitle: Example\nlinks:\n  supports:\n    - "[[Claim A]]"\n---\nBody\n'
    )

    assert data == {
        "title": "Example",
        "links": {"supports": ["[[Claim A]]"]},
    }


def test_parse_frontmatter_returns_empty_for_absent_or_malformed() -> None:
    assert parse_frontmatter("No frontmatter\n") == {}
    assert parse_frontmatter("---\ntitle: [unterminated\n---\nBody\n") == {}
    assert parse_frontmatter("---\n- just\n- a list\n---\nBody\n") == {}


def test_read_frontmatter_and_safe_read_tolerate_missing_files(tmp_path) -> None:
    missing = tmp_path / "missing.md"

    assert safe_read(missing) == ""
    assert read_frontmatter(missing) == {}


def test_iter_jsonl_skips_missing_bad_and_non_object_lines(tmp_path) -> None:
    missing = tmp_path / "missing.jsonl"
    path = tmp_path / "events.jsonl"
    path.write_text(
        "\n".join(
            [
                json.dumps({"ok": 1}),
                "not-json",
                json.dumps(["not", "an", "object"]),
                json.dumps({"ok": 2}),
                "",
            ]
        ),
        encoding="utf-8",
    )

    assert list(iter_jsonl(missing)) == []
    assert list(iter_jsonl(path)) == [{"ok": 1}, {"ok": 2}]


def test_append_jsonl_creates_parent_directory(tmp_path) -> None:
    path = tmp_path / "system" / "logs" / "events.jsonl"

    append_jsonl(path, [{"name": "one"}, {"name": "two"}])

    assert list(iter_jsonl(path)) == [{"name": "one"}, {"name": "two"}]


def test_iter_markdown_prunes_skip_dirs_during_walk(tmp_path) -> None:
    (tmp_path / "notes").mkdir()
    (tmp_path / "notes" / "keep.md").write_text("ok", encoding="utf-8")
    (tmp_path / ".memoria").mkdir()
    (tmp_path / ".memoria" / "skip.md").write_text("skip", encoding="utf-8")
    (tmp_path / ".git").mkdir()
    (tmp_path / ".git" / "skip.md").write_text("skip", encoding="utf-8")

    assert [path.relative_to(tmp_path).as_posix() for path in iter_markdown(tmp_path)] == [
        "notes/keep.md"
    ]


def test_utc_z_and_parse_iso_round_trip() -> None:
    timestamp = utc_z(datetime(2026, 6, 19, 20, 10, 11, 123456, tzinfo=UTC))

    assert timestamp == "2026-06-19T20:10:11Z"
    assert parse_iso(timestamp) == datetime(2026, 6, 19, 20, 10, 11, tzinfo=UTC)
