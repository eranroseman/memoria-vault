from __future__ import annotations

import hashlib
from pathlib import Path

import pytest

from memoria_vault.runtime import state

_EVIDENCE_ID = "ev-11111111"
_BLOCK_REF = "projects/project-alpha/draft.md#^blk-11111111"
_MARKER = "%%ev: ev-11111111 type=implicit state=evidence-incomplete review=true items=%%"


def test_evidence_sets_schema_has_block_text_hash_binding(tmp_path: Path) -> None:
    with state.connect(tmp_path) as conn:
        columns = {row["name"] for row in conn.execute("PRAGMA table_info(evidence_sets)")}

    assert "block_text_sha256" in columns


def test_rebuild_binds_new_evidence_once_and_preserves_hash_after_edit(
    tmp_path: Path,
) -> None:
    draft = tmp_path / "projects/project-alpha/draft.md"
    draft.parent.mkdir(parents=True)
    original = "First line.\nSecond line."
    draft.write_text(f"{original} ^blk-11111111 {_MARKER}\n", encoding="utf-8")

    state.rebuild_evidence_sets_from_markers(tmp_path, run_id="compose-1")
    expected = "sha256:" + hashlib.sha256(original.encode()).hexdigest()
    [row] = state.evidence_sets(tmp_path)

    assert row["block_text_sha256"] == expected

    changed = "First line.\nChanged second line."
    draft.write_text(f"{changed} ^blk-11111111 {_MARKER}\n", encoding="utf-8")
    current = state._block_text_sha256(tmp_path, _BLOCK_REF)
    state.rebuild_evidence_sets_from_markers(tmp_path, run_id="verify-1")
    [rebuilt] = state.evidence_sets(tmp_path)

    assert current == "sha256:" + hashlib.sha256(changed.encode()).hexdigest()
    assert current != expected
    assert rebuilt["block_text_sha256"] == expected


def test_rebuild_preserves_binding_when_id_disappears_then_reappears(
    tmp_path: Path,
) -> None:
    draft = tmp_path / "projects/project-alpha/draft.md"
    draft.parent.mkdir(parents=True)
    original = "Original bound claim."
    draft.write_text(f"{original} ^blk-11111111 {_MARKER}\n", encoding="utf-8")

    state.rebuild_evidence_sets_from_markers(tmp_path, run_id="compose-1")
    expected = "sha256:" + hashlib.sha256(original.encode()).hexdigest()

    draft.write_text("Evidence marker deliberately removed.\n", encoding="utf-8")
    state.rebuild_evidence_sets_from_markers(tmp_path, run_id="remove-1")
    assert state.evidence_sets(tmp_path) == []

    changed = "Changed claim reusing the original evidence ID."
    draft.write_text(f"{changed} ^blk-11111111 {_MARKER}\n", encoding="utf-8")
    state.rebuild_evidence_sets_from_markers(tmp_path, run_id="reintroduce-1")
    [reintroduced] = state.evidence_sets(tmp_path)

    assert reintroduced["block_text_sha256"] == expected


def test_rebuild_preserves_an_existing_unbound_hash(tmp_path: Path) -> None:
    draft = tmp_path / "projects/project-alpha/draft.md"
    draft.parent.mkdir(parents=True)
    draft.write_text(f"Unbound claim. {_MARKER}\n", encoding="utf-8")

    state.rebuild_evidence_sets_from_markers(tmp_path)
    [unbound] = state.evidence_sets(tmp_path)
    assert unbound["block_text_sha256"] is None

    draft.write_text(
        f"Now anchored. ^blk-11111111 {_MARKER}\n",
        encoding="utf-8",
    )
    assert state._block_text_sha256(tmp_path, _BLOCK_REF) is not None
    state.rebuild_evidence_sets_from_markers(tmp_path)
    [rebuilt] = state.evidence_sets(tmp_path)

    assert rebuilt["id"] == _EVIDENCE_ID
    assert rebuilt["block_text_sha256"] is None


@pytest.mark.parametrize(
    "content",
    [
        f"Supported claim. ` ^blk-11111111 ` {_MARKER}\n",
        f"Supported claim. {_MARKER}\n\n```markdown\n^blk-11111111\n```\n",
        f"Supported claim. ^blk-11111111\n\n` {_MARKER}`\n",
        f"Supported claim. ^blk-11111111\n\n```markdown\n{_MARKER}\n```\n",
    ],
)
def test_block_text_binding_rejects_control_tokens_in_code(
    tmp_path: Path,
    content: str,
) -> None:
    draft = tmp_path / "projects/project-alpha/draft.md"
    draft.parent.mkdir(parents=True)
    draft.write_text(content, encoding="utf-8")

    assert state._block_text_sha256(tmp_path, _BLOCK_REF) is None


@pytest.mark.parametrize(
    ("opener_backslashes", "closer_backslashes", "delimiter_length"),
    [
        (opener_backslashes, closer_backslashes, delimiter_length)
        for opener_backslashes in range(6)
        for closer_backslashes in range(6)
        for delimiter_length in range(1, 6)
    ],
)
def test_block_text_binding_follows_pandoc_inline_code_delimiter_rules(
    tmp_path: Path,
    opener_backslashes: int,
    closer_backslashes: int,
    delimiter_length: int,
) -> None:
    delimiter = "`" * delimiter_length
    opener_prefix = "\\" * opener_backslashes
    closer_prefix = "\\" * closer_backslashes
    content = (
        f"Unsupported claim. {opener_prefix}{delimiter} ^blk-11111111 "
        f"{_MARKER} {closer_prefix}{delimiter}\n"
    )
    draft = tmp_path / "projects/project-alpha/draft.md"
    draft.parent.mkdir(parents=True)
    draft.write_text(content, encoding="utf-8")

    visible = state._markdown_control_text(content)

    assert len(visible) == len(content)
    assert visible.count("\n") == content.count("\n")
    # Pandoc treats backslashes before a closer as literal code content. Only
    # the opener's contiguous-backslash parity determines whether this is code.
    assert (state._block_text_sha256(tmp_path, _BLOCK_REF) is not None) is (
        opener_backslashes % 2 == 1
    )


@pytest.mark.parametrize(("opening_length", "closing_length"), [(1, 2), (2, 3), (3, 4)])
def test_block_text_binding_does_not_match_partial_inline_code_delimiters(
    tmp_path: Path,
    opening_length: int,
    closing_length: int,
) -> None:
    content = (
        "Unsupported claim. "
        f"{'`' * opening_length} ^blk-11111111 {_MARKER} {'`' * closing_length}\n"
    )
    draft = tmp_path / "projects/project-alpha/draft.md"
    draft.parent.mkdir(parents=True)
    draft.write_text(content, encoding="utf-8")

    assert state._block_text_sha256(tmp_path, _BLOCK_REF) is not None


@pytest.mark.parametrize(
    ("content", "resolves"),
    [
        (f"Supported claim. ^blk-11111111 {_MARKER}\n", True),
        (
            f"# Supported claim ^blk-11111111 \nChanged unsupported claim. {_MARKER}\n",
            False,
        ),
    ],
)
def test_block_text_binding_requires_anchor_and_marker_on_one_line(
    tmp_path: Path,
    content: str,
    resolves: bool,
) -> None:
    draft = tmp_path / "projects/project-alpha/draft.md"
    draft.parent.mkdir(parents=True)
    draft.write_text(content, encoding="utf-8")

    assert (state._block_text_sha256(tmp_path, _BLOCK_REF) is not None) is resolves


@pytest.mark.parametrize(
    ("original", "changed"),
    [
        ("`%%ev: alpha%%`", "`%%ev: beta%%`"),
        (
            "%%ev: ev-22222222 type=implicit state=evidence-incomplete review=true items=%%",
            "%%ev: ev-22222222 type=implicit state=evidence-incomplete review=false items=%%",
        ),
    ],
)
def test_block_text_binding_hashes_nonbinding_marker_text(
    tmp_path: Path,
    original: str,
    changed: str,
) -> None:
    draft = tmp_path / "projects/project-alpha/draft.md"
    draft.parent.mkdir(parents=True)
    draft.write_text(
        f"Supported claim with {original}. ^blk-11111111 {_MARKER}\n",
        encoding="utf-8",
    )
    before = state._block_text_sha256(tmp_path, _BLOCK_REF)

    draft.write_text(
        f"Supported claim with {changed}. ^blk-11111111 {_MARKER}\n",
        encoding="utf-8",
    )
    after = state._block_text_sha256(tmp_path, _BLOCK_REF)

    assert before is not None
    assert after is not None
    assert after != before
