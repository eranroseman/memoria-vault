"""The PreToolUse gate that rejects sweep staging.

The git index is shared per checkout (AGENTS.md, Ground truth), so unbounded
staging can sweep another session's work into a commit. These pin the two
halves of the gate's promise: every sweep form is blocked, and every targeted
form still runs — a gate that blocks real work gets disabled, which is the
same as not having one.
"""

from __future__ import annotations

import json
import subprocess
import sys

import pytest

from tests.paths import ROOT

pytestmark = pytest.mark.static

HOOK = ROOT / ".claude/hooks/block-git-add-all.py"
BLOCK = 2


def _run(command: str) -> int:
    """Return the hook's exit code for one Bash command. 2 blocks it."""
    return subprocess.run(
        [sys.executable, str(HOOK)],
        input=json.dumps({"tool_input": {"command": command}}),
        text=True,
        capture_output=True,
        check=False,
    ).returncode


@pytest.mark.parametrize(
    "command",
    [
        "git add -A",
        "git add .",
        "git add -u",
        "git add --all",
        "git add --update",
        "git add -A .",
        "git add -- .",
        "git -C /repo add -A",
        "cd sub && git add -A",
        "git commit -m x && git add -A",
        "(git add -A)",
    ],
)
def test_sweep_staging_is_blocked(command: str) -> None:
    assert _run(command) == BLOCK, f"sweep not blocked: {command}"


@pytest.mark.xfail(reason="accepted gap — closing it costs more than it saves", strict=True)
@pytest.mark.parametrize(
    "command",
    ['git add ":(exclude)foo" .', "git add ':(exclude)*.lock' ."],
)
def test_pathspec_magic_sweep_is_a_known_gap(command: str) -> None:
    """A sweep whose own pathspec carries parentheses gets through.

    The gate splits on `()` to catch a sweep inside a subshell, so
    `:(exclude)…` severs the sweeping `.` from its `git add`. Closing it by
    also scanning the unsplit command was tried and reverted: it blocks any
    command whose *text* documents a sweep — a PR body or commit message
    describing this very hook — and a gate that blocks real work gets
    disabled, which is the same as not having one.

    The traded risks are not symmetric. This gap needs someone to type an
    exotic pathspec sweep on purpose; the false positive fires whenever
    anyone writes about the command. See `test_prose_about_a_sweep_still_runs`.
    """
    assert _run(command) == BLOCK


@pytest.mark.parametrize(
    "command",
    [
        "git add src/foo.py",
        "git add -A src/",
        "git add -u src/",
        "git add docs/ tests/",
        'git add ":(exclude)foo" src/',
        # Prose about the sweep is not the sweep.
        'echo "git add -A"',
        "git status",
        "git commit -m 'add everything'",
    ],
)
def test_targeted_staging_is_allowed(command: str) -> None:
    assert _run(command) == 0, f"targeted staging wrongly blocked: {command}"


def test_prose_about_a_sweep_still_runs() -> None:
    """Writing about the gate must not trip the gate.

    This repo documents its own hooks, so a PR body or commit message quoting
    a sweep form travels inside a Bash command. Scanning the unsplit command —
    the obvious way to close `test_pathspec_magic_sweep_is_a_known_gap` —
    blocks exactly this, which is why that gap stays open.
    """
    body = 'gh pr create --body "Fixed: git add \\":(exclude)foo\\" . was allowed (should block)"'
    assert _run(body) == 0


def test_unparseable_input_fails_open() -> None:
    """A gate that wedges the agent on malformed input is worse than no gate."""
    result = subprocess.run(
        [sys.executable, str(HOOK)],
        input="not json",
        text=True,
        capture_output=True,
        check=False,
    )
    assert result.returncode == 0


def test_block_explains_itself() -> None:
    """The agent only recovers if stderr names the alternative."""
    result = subprocess.run(
        [sys.executable, str(HOOK)],
        input=json.dumps({"tool_input": {"command": "git add -A"}}),
        text=True,
        capture_output=True,
        check=False,
    )
    assert result.returncode == BLOCK
    assert "explicit paths" in result.stderr
