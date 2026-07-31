"""Agent-bundle seeding, vault.json manifest, upgrade, and skew detection."""

from __future__ import annotations

import json
import subprocess
import sys

from tests.helpers import WORKSPACE_SEED

PERIMETER_MESSAGE = (
    "Memoria write perimeter: vault notes are engine-mediated — a direct edit "
    "would be recorded as the human's work by the provenance layer. "
    "Use the MCP tool `operation_run` or the `memoria` CLI."
)
PROTECTED_PATTERNS = (
    "**/*.md",
    ".claude/**",
    ".codex/**",
    ".mcp.json",
    ".memoria/**",
    ".obsidian/**",
)
AGENT_BUNDLE_FILES = (
    ".claude/hooks/write_perimeter.py",
    ".claude/settings.json",
    ".codex/hooks.json",
    ".mcp.json",
    "CLAUDE.md",
)


def test_seed_claude_settings_deny_rules_cover_every_protected_path():
    settings = json.loads((WORKSPACE_SEED / ".claude/settings.json").read_text("utf-8"))
    expected = {
        f"{tool}({pattern})"
        for tool in ("Edit", "Write", "NotebookEdit")
        for pattern in PROTECTED_PATTERNS
    }
    assert set(settings["permissions"]["deny"]) == expected
    assert len(settings["permissions"]["deny"]) == 18


def test_seed_claude_settings_registers_the_perimeter_hook():
    settings = json.loads((WORKSPACE_SEED / ".claude/settings.json").read_text("utf-8"))
    entries = settings["hooks"]["PreToolUse"]
    assert len(entries) == 1
    assert entries[0]["matcher"] == "Edit|Write|NotebookEdit"
    assert entries[0]["hooks"] == [
        {
            "type": "command",
            "command": 'python3 "$CLAUDE_PROJECT_DIR/.claude/hooks/write_perimeter.py"',
        }
    ]


def test_write_perimeter_hook_denies_unconditionally_with_exit_2():
    hook = WORKSPACE_SEED / ".claude/hooks/write_perimeter.py"
    result = subprocess.run(
        [sys.executable, str(hook)],
        input='{"tool_name": "Write", "tool_input": {"file_path": "notes/x.md"}}',
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 2
    assert PERIMETER_MESSAGE in result.stderr
    assert result.stdout == ""


def test_write_perimeter_hook_is_stdlib_only():
    source = (WORKSPACE_SEED / ".claude/hooks/write_perimeter.py").read_text("utf-8")
    for forbidden in ("memoria_vault", "import requests", "import yaml"):
        assert forbidden not in source


def test_seed_mcp_json_wires_memoria_mcp_stdio():
    config = json.loads((WORKSPACE_SEED / ".mcp.json").read_text("utf-8"))
    server = config["mcpServers"]["memoria"]
    assert server["command"] == "memoria"
    assert server["args"][:3] == ["mcp", "--workspace", "."]
    scopes = [
        server["args"][index + 1]
        for index, arg in enumerate(server["args"])
        if arg == "--read-scope"
    ]
    assert scopes == ["notes", "hubs", "projects", "digests", "fulltexts", "inbox"]


def test_seed_claude_md_is_an_agents_md_loader():
    assert (WORKSPACE_SEED / "CLAUDE.md").read_text("utf-8") == "@AGENTS.md\n"


def test_seed_codex_hooks_mirror_the_deny_rules():
    mirror = json.loads((WORKSPACE_SEED / ".codex/hooks.json").read_text("utf-8"))
    assert mirror["schema"] == 1
    assert mirror["deny"]["tools"] == ["edit", "write"]
    assert mirror["deny"]["paths"] == list(PROTECTED_PATTERNS)
