from __future__ import annotations

import hashlib
import time
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


def test_direct_and_hidden_duplicate_cannot_mint_a_fresh_binding(tmp_path: Path) -> None:
    draft = tmp_path / "projects/project-alpha/draft.md"
    draft.parent.mkdir(parents=True)
    draft.write_text(
        "---\n"
        f"Hidden claim. ^blk-11111111 {_MARKER}\n"
        "...\n\n"
        f"Visible claim. ^blk-11111111 {_MARKER}\n",
        encoding="utf-8",
    )

    result = state.rebuild_evidence_sets_from_markers(tmp_path)

    assert result["duplicate_ids"] == [_EVIDENCE_ID]
    assert [row["id"] for row in state.evidence_sets(tmp_path)] == [_EVIDENCE_ID]
    with state.connect(tmp_path) as conn:
        assert (
            conn.execute(
                "SELECT id FROM evidence_bindings WHERE id = ?", (_EVIDENCE_ID,)
            ).fetchone()
            is None
        )


def test_hidden_only_fresh_duplicates_cannot_mint_a_binding(tmp_path: Path) -> None:
    hidden = f"<!-- Hidden claim. ^blk-11111111 {_MARKER} -->\n"
    for name in ("one.md", "two.md"):
        path = tmp_path / "notes" / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(hidden, encoding="utf-8")

    state.rebuild_evidence_sets_from_markers(tmp_path)

    assert state.evidence_sets(tmp_path) == []
    with state.connect(tmp_path) as conn:
        assert (
            conn.execute(
                "SELECT id FROM evidence_bindings WHERE id = ?", (_EVIDENCE_ID,)
            ).fetchone()
            is None
        )


def test_malformed_raw_evidence_marker_does_not_abort_a_rebuild(tmp_path: Path) -> None:
    draft = tmp_path / "projects/project-alpha/draft.md"
    draft.parent.mkdir(parents=True)
    draft.write_text("Visible claim. %%ev: nope%%\n", encoding="utf-8")

    result = state.rebuild_evidence_sets_from_markers(tmp_path)

    assert result == {"deleted": 0, "inserted": 0}
    assert state.evidence_sets(tmp_path) == []


def test_hidden_existing_id_after_an_interim_rebuild_remains_unbound(tmp_path: Path) -> None:
    draft = tmp_path / "projects/project-alpha/draft.md"
    draft.parent.mkdir(parents=True)
    draft.write_text(f"Original claim. ^blk-11111111 {_MARKER}\n", encoding="utf-8")
    state.rebuild_evidence_sets_from_markers(tmp_path)

    draft.write_text("The original marker was removed.\n", encoding="utf-8")
    state.rebuild_evidence_sets_from_markers(tmp_path)

    hidden = tmp_path / "notes/hidden.md"
    hidden.parent.mkdir(parents=True)
    hidden.write_text(
        f"<!-- Hidden claim. ^blk-11111111 {_MARKER} -->\n",
        encoding="utf-8",
    )
    state.rebuild_evidence_sets_from_markers(tmp_path)

    [row] = state.evidence_sets(tmp_path)
    assert row["id"] == _EVIDENCE_ID
    assert row["block_text_sha256"] is None


@pytest.mark.parametrize("opener", ["<", "[", "("])
def test_markdown_control_parsing_is_bounded_for_repeated_unclosed_delimiters(
    opener: str,
) -> None:
    content = opener * 8_000

    started = time.monotonic()
    visible = state._markdown_control_text(content)

    assert visible == content
    assert time.monotonic() - started < 2


def test_markdown_control_parsing_is_bounded_for_increasing_backtick_runs() -> None:
    content = "".join("`" * width + "x" for width in range(1, 151))

    started = time.monotonic()
    visible = state._markdown_control_text(content)

    assert len(visible) == len(content)
    assert time.monotonic() - started < 2


@pytest.mark.parametrize(
    "content",
    [
        f"Hidden claim. <!-- ^blk-11111111 {_MARKER} -->\n",
        f"Hidden claim. <!-- ^blk-11111111\n{_MARKER} -->\n",
        f"prefix\n~~~\n<!--\n~~~\nHidden claim. ^blk-11111111 {_MARKER}\n-->\n",
        f"prefix\n~~~\n<?x\n~~~\nHidden claim. ^blk-11111111 {_MARKER}\n?>\n",
        f"<script>Hidden claim. ^blk-11111111 {_MARKER}</script>\n",
        f"<span hidden>Hidden claim. ^blk-11111111 {_MARKER}</span>\n",
        f"<span hidden/>Hidden claim. ^blk-11111111 {_MARKER}</span>\n",
        f'<span hidden data="\\">Hidden claim. ^blk-11111111 {_MARKER}</span>\n',
        f"<span hidden data='\\'>Hidden claim. ^blk-11111111 {_MARKER}</span>\n",
        f'<span\n  hidden\n  data="\\">Hidden claim. ^blk-11111111 {_MARKER}</span>\n',
        f"<?hidden Hidden claim. ^blk-11111111 {_MARKER} ?>\n",
        f"---\nhidden: |\n  Hidden claim. ^blk-11111111 {_MARKER}\n---\n",
        f"\ufeff---\nhidden: |\n  Hidden claim. ^blk-11111111 {_MARKER}\n---\n",
        f"\n---\nhidden: |\n  Hidden claim. ^blk-11111111 {_MARKER}\n---\n",
        f"Title: Hidden claim. ^blk-11111111 {_MARKER}\n",
        f"\ufeffFoo: first metadata field\nBar: Hidden claim. ^blk-11111111 {_MARKER}\n",
        f"    Foo: first metadata field\nBar: Hidden claim. ^blk-11111111 {_MARKER}\n",
        f"foo\tbar: harmless metadata\nOther: Hidden claim. ^blk-11111111 {_MARKER}\n",
        f"# Hidden claim. ^blk-11111111 {_MARKER}\n",
        f"Hidden claim. ^blk-11111111 {_MARKER}\n===\n",
        f"Hidden claim. ^blk-11111111 {_MARKER}\n---\n",
        f"*[H]: Hidden claim. ^blk-11111111 {_MARKER}\n",
        f"*[H\n]: Hidden claim. ^blk-11111111 {_MARKER}\n",
        f"left | Hidden claim. ^blk-11111111 {_MARKER}\n--- | ---\na | b\n",
        f"Left      Right\n----      -----\na         b\n\nHidden claim. ^blk-11111111 {_MARKER}\n",
        f"Heading\n ---\nHidden claim. ^blk-11111111 {_MARKER}\n",
        f"---\nHead\n---\nHidden claim. ^blk-11111111 {_MARKER}\n\n---\n",
        f"---\n10:00 Header\n---\nHidden claim. ^blk-11111111 {_MARKER}\n\n---\n",
        f"+---+---+\n| a | b |\n+===+===+\n| c | d |\n+---+---+\n\nHidden claim. ^blk-11111111 {_MARKER}\n",
        f"----\nHeader\n----\nbody\n----\n\nHidden claim. ^blk-11111111 {_MARKER}\n",
        f"One | Two\n-----+-------\nx | Hidden claim. ^blk-11111111 {_MARKER}\n",
        f"Prose.\n\nTable: Hidden claim. ^blk-11111111 {_MARKER}\n\n| One | Two |\n|-----+-------|\n| a | b |\n",
        f'[hidden]: https://example.invalid "Hidden claim. ^blk-11111111 {_MARKER}"\n',
        f"[hidden\\]]: https://example.invalid Hidden claim. ^blk-11111111 {_MARKER}\n",
        f"[hidden\n]: https://example.invalid Hidden claim. ^blk-11111111 {_MARKER}\n",
        f"[^n]:\nHidden claim. ^blk-11111111 {_MARKER}\n",
        f"[r]: <\nHidden claim. ^blk-11111111 {_MARKER}\n>\n\n[r]\n",
        f"[r]: https://example.invalid (\nHidden claim. ^blk-11111111 {_MARKER}\n)\n\n[r]\n",
        f"[^n]: First paragraph.\n\n    Second footnote paragraph.\nHidden claim. ^blk-11111111 {_MARKER}\n",
        f'[\nHidden claim. ^blk-11111111 {_MARKER}\n]{{style="display:none"}}\n',
        '[visible]{data-x="hidden ^blk-11111111 ' + _MARKER + '\n"}\n',
        '[visible]{\ndata-x="hidden ^blk-11111111 ' + _MARKER + '\n"}\n',
        f"[visible](https://example.invalid (\nHidden claim. ^blk-11111111 {_MARKER}\n))\n",
        f'::: {{style="display:none"}}\nHidden claim. ^blk-11111111 {_MARKER}\n:::\n',
        f"::: foo\nouter\n:::\v\nHidden claim. ^blk-11111111 {_MARKER}\n:::\n",
        f"% Hidden claim. ^blk-11111111 {_MARKER}\n\nVisible claim.\n",
        f"\\begin{{comment}}\nHidden claim. ^blk-11111111 {_MARKER}\n\\end{{comment}}\n",
        f"\\begin {{comment-env}}\nHidden claim. ^blk-11111111 {_MARKER}\n\\end {{comment-env}}\n",
        f"\\endinput\nHidden claim. ^blk-11111111 {_MARKER}\n",
        f"\\phantom{{\nHidden claim. ^blk-11111111 {_MARKER}\n}}\n",
        "\\" * 3 + f"endinput\nHidden claim. ^blk-11111111 {_MARKER}\n",
        f"\\\u03b1{{\nHidden claim. ^blk-11111111 {_MARKER}\n}}\n",
        f"prefix \\begin{{comment}}\nHidden claim. ^blk-11111111 {_MARKER}\n\\end{{comment}}\n",
        f"$$\nHidden claim. ^blk-11111111 {_MARKER}\n$$\n",
        f"$x + % Hidden claim. ^blk-11111111 {_MARKER}\n+ y$\n",
        "\\" * 2 + f"$x + % Hidden claim. ^blk-11111111 {_MARKER}\n+ y" + "\\" * 2 + "$\n",
        f"prefix\n~~~foo\n\\phantom{{\n~~~\nHidden claim. ^blk-11111111 {_MARKER}\n}}\n",
        f"\\[\nHidden claim. ^blk-11111111 {_MARKER}\n\\]\n",
        f"\\(\nHidden claim. ^blk-11111111 {_MARKER}\n\\)\n",
        f"```tex\n\\endinput\n```\n\nHidden claim. ^blk-11111111 {_MARKER}\n",
        chr(96)
        + f"prefix {chr(96) * 3} Hidden claim. ^blk-11111111 {_MARKER}"
        + chr(96) * 2
        + "\n",
        "\\" + chr(96) * 2 + f"prefix Hidden claim. ^blk-11111111 {_MARKER}" + chr(96) + "\n",
        f"<style>p {{ display:none }}</style>\nHidden claim. ^blk-11111111 {_MARKER}\n",
        f"::: {{.x}}\n<style>p {{ display:none }}</style>\n:::\nHidden claim. ^blk-11111111 {_MARKER}\n",
        f"<script>document.body.style.display = 'none'</script>\nHidden claim. ^blk-11111111 {_MARKER}\n",
        f'<\u03b1 style="display:none">Hidden claim. ^blk-11111111 {_MARKER}\n',
        f"</? hidden\nHidden claim. ^blk-11111111 {_MARKER}\n>\n",
        f"`<style>p {{ display:none }}</style>`{{=html}}\nHidden claim. ^blk-11111111 {_MARKER}\n",
        f"```{{=html}}\n<style>p {{ display:none }}</style>\n```\nHidden claim. ^blk-11111111 {_MARKER}\n",
        f"> ```markdown\n> Hidden claim. ^blk-11111111 {_MARKER}\n> ```\n",
        f"- ```markdown\nHidden claim. ^blk-11111111 {_MARKER}\n  ```\n",
        f"(@) ```markdown\nHidden claim. ^blk-11111111 {_MARKER}\n    ```\n",
        f"(ii) Hidden claim. ^blk-11111111 {_MARKER}\n",
        f"(@foo) Hidden claim. ^blk-11111111 {_MARKER}\n",
        f"(@foo) prefix\nHidden claim. ^blk-11111111 {_MARKER}\n",
        f"@foo. Hidden claim. ^blk-11111111 {_MARKER}\n",
        f"@foo) Hidden claim. ^blk-11111111 {_MARKER}\n",
        f'> ::: {{style="display:none"}}\nHidden claim. ^blk-11111111 {_MARKER}\n> :::\n',
        f"Term\n: \\begin{{comment}}\nHidden claim. ^blk-11111111 {_MARKER}\n  \\end{{comment}}\n",
        f"Hidden claim. ^blk-11111111 {_MARKER}\n: definition\n",
        f"Hidden claim. ^blk-11111111 {_MARKER}\n\n: definition\n",
        f"Hidden claim. ^blk-11111111 {_MARKER}\n\n~ definition\n",
        f"Hidden claim. ^blk-11111111 {_MARKER}\n\n  : definition\n",
        f"| Hidden claim. ^blk-11111111 {_MARKER}\n",
        f"> Visible quoted claim. ^blk-11111111 {_MARKER}\n",
        f">\v\nHidden claim. ^blk-11111111 {_MARKER}\n",
        f"- Visible list claim. ^blk-11111111 {_MARKER}\n",
        f"-\n\u00a0\nHidden claim. ^blk-11111111 {_MARKER}\n",
        f"Term\n: Visible definition claim. ^blk-11111111 {_MARKER}\n",
        f"{'1' * 10}. Hidden claim. ^blk-11111111 {_MARKER}\n",
        f"({'1' * 10}) Hidden claim. ^blk-11111111 {_MARKER}\n",
        f"-\nHidden claim. ^blk-11111111 {_MARKER}\n",
        f"+\nHidden claim. ^blk-11111111 {_MARKER}\n",
        f"*\nHidden claim. ^blk-11111111 {_MARKER}\n",
        f"1.\nHidden claim. ^blk-11111111 {_MARKER}\n",
        f"1)\nHidden claim. ^blk-11111111 {_MARKER}\n",
        f"a.\nHidden claim. ^blk-11111111 {_MARKER}\n",
        f"(1)\nHidden claim. ^blk-11111111 {_MARKER}\n",
        f"(a)\nHidden claim. ^blk-11111111 {_MARKER}\n",
        f"(@foo)\nHidden claim. ^blk-11111111 {_MARKER}\n",
        f"#.\nHidden claim. ^blk-11111111 {_MARKER}\n",
        f"@.\nHidden claim. ^blk-11111111 {_MARKER}\n",
    ],
)
def test_nonbinding_controls_cannot_create_evidence_bindings(
    tmp_path: Path,
    content: str,
) -> None:
    draft = tmp_path / "projects/project-alpha/draft.md"
    draft.parent.mkdir(parents=True)
    draft.write_text(content, encoding="utf-8")

    assert state._block_text_sha256(tmp_path, _BLOCK_REF) is None
    state.rebuild_evidence_sets_from_markers(tmp_path)

    assert state.evidence_sets(tmp_path) == []
    with state.connect(tmp_path) as conn:
        assert (
            conn.execute(
                "SELECT id FROM evidence_bindings WHERE id = ?", (_EVIDENCE_ID,)
            ).fetchone()
            is None
        )


def test_visible_controls_after_a_closed_html_comment_remain_bindable(tmp_path: Path) -> None:
    draft = tmp_path / "projects/project-alpha/draft.md"
    draft.parent.mkdir(parents=True)
    content = f"<!-- context -->\nVisible claim. ^blk-11111111 {_MARKER}\n"
    draft.write_text(content, encoding="utf-8")

    assert state._block_text_sha256(tmp_path, _BLOCK_REF) is not None
    state.rebuild_evidence_sets_from_markers(tmp_path)

    assert [row["id"] for row in state.evidence_sets(tmp_path)] == [_EVIDENCE_ID]


def test_raw_carriage_returns_fail_closed_for_direct_marker_parsing() -> None:
    content = "\rFoo: metadata\nHidden claim. ^blk-11111111 " + _MARKER + "\n"

    assert state.evidence_markers_from_markdown(content) == []


def test_escaped_markdown_bracket_remains_a_direct_visible_claim() -> None:
    content = f"\\[literal] visible claim. ^blk-11111111 {_MARKER}\n"

    assert [marker.evidence_id for marker in state.evidence_markers_from_markdown(content)] == [
        _EVIDENCE_ID
    ]
    assert state._block_text_sha256_from_text(content, _BLOCK_REF) is not None


def test_inline_tex_with_an_escaped_closer_remains_a_direct_visible_claim() -> None:
    content = f"\\(literal \\\\) visible claim. ^blk-11111111 {_MARKER}\n"

    assert [marker.evidence_id for marker in state.evidence_markers_from_markdown(content)] == [
        _EVIDENCE_ID
    ]
    assert state._block_text_sha256_from_text(content, _BLOCK_REF) is not None


def test_display_tex_math_closer_with_an_extra_backslash_cannot_mint_a_binding() -> None:
    content = f"\\[\nHidden claim. ^blk-11111111 {_MARKER}\n\\\\]\n"

    assert state.evidence_markers_from_markdown(content) == []
    assert state._block_text_sha256_from_text(content, _BLOCK_REF) is None


@pytest.mark.parametrize(
    ("opener", "closer", "active_closer_required"),
    [("[", "]", False), ("(", ")", True)],
)
@pytest.mark.parametrize("opening_run", range(7))
@pytest.mark.parametrize("closing_run", range(7))
def test_tex_math_pair_detection_matches_pandoc_delimiter_runs(
    opener: str,
    closer: str,
    active_closer_required: bool,
    opening_run: int,
    closing_run: int,
) -> None:
    content = "\\" * opening_run + opener + " hidden " + "\\" * closing_run + closer
    expected = (
        opening_run % 2 == 1
        and closing_run > 0
        and (not active_closer_required or closing_run % 2 == 1)
    )

    assert state._has_raw_tex_syntax(content) is expected


def test_tex_math_pair_scan_is_linear_for_unmatched_openers() -> None:
    content = "\\[ " * 80_000

    started = time.monotonic()
    assert state._has_raw_tex_syntax(content) is False
    assert time.monotonic() - started < 3


def test_visible_control_after_yaml_mapping_remains_bindable(tmp_path: Path) -> None:
    draft = tmp_path / "projects/project-alpha/draft.md"
    draft.parent.mkdir(parents=True)
    draft.write_text(
        "---\ntype: draft\nproject: projects/project-alpha/project.md\n---\n"
        f"Visible claim. ^blk-11111111 {_MARKER}\n",
        encoding="utf-8",
    )

    assert state._block_text_sha256(tmp_path, _BLOCK_REF) is not None
    state.rebuild_evidence_sets_from_markers(tmp_path)

    assert [row["id"] for row in state.evidence_sets(tmp_path)] == [_EVIDENCE_ID]


def test_deep_initial_yaml_mapping_fails_closed_without_recursing() -> None:
    frontmatter = "".join("  " * depth + "x:\n" for depth in range(600))
    content = f"---\n{frontmatter}---\nVisible claim. ^blk-11111111 {_MARKER}\n"

    assert state.evidence_markers_from_markdown(content) == []
    assert state._block_text_sha256_from_text(content, _BLOCK_REF) is None


def test_top_level_control_after_a_closed_container_remains_bindable(tmp_path: Path) -> None:
    draft = tmp_path / "projects/project-alpha/draft.md"
    draft.parent.mkdir(parents=True)
    content = f"> Context only.\n\nVisible claim. ^blk-11111111 {_MARKER}\n"
    draft.write_text(content, encoding="utf-8")

    assert state._block_text_sha256(tmp_path, _BLOCK_REF) is not None
    state.rebuild_evidence_sets_from_markers(tmp_path)

    assert [row["id"] for row in state.evidence_sets(tmp_path)] == [_EVIDENCE_ID]


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
