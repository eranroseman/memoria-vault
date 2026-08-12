#!/usr/bin/env python3
"""PreToolUse(Bash) gate: reject sweep staging (`git add -A/--all/-u/.`).

The git index is shared per checkout (AGENTS.md, Ground truth): two sessions
in one checkout can sweep each other's staged files into a commit. Staging
must name explicit paths. Targeted forms (`git add -A src/`) stay allowed —
the sweep is only unbounded staging, not the flags themselves.

Exit 2 blocks the command and feeds stderr back to the agent; anything else
lets it through. Never blocks on unparseable input.
"""

import json
import re
import sys

SWEEP_FLAGS = {"-A", "--all", "-u", "--update"}
SWEEP_PATHS = {".", "./", "..", "*", ":/", ":/."}

MESSAGE = (
    "Blocked: unbounded staging (git add -A/--all/-u/.) can sweep another "
    "session's work into a commit — the git index is shared per checkout "
    "(AGENTS.md). Stage explicit paths instead.\n"
)


def is_sweep(arg_string: str) -> bool:
    args = arg_string.split()
    if "--" in args:
        split_at = args.index("--")
        flags = [a for a in args[:split_at] if a.startswith("-")]
        paths = args[split_at + 1 :] + [a for a in args[:split_at] if not a.startswith("-")]
    else:
        flags = [a for a in args if a.startswith("-")]
        paths = [a for a in args if not a.startswith("-")]
    if any(p in SWEEP_PATHS for p in paths):
        return True
    sweep_flag = any(f in SWEEP_FLAGS or re.fullmatch(r"-[a-zA-Z]*[Au][a-zA-Z]*", f) for f in flags)
    return sweep_flag and not paths


def main() -> int:
    try:
        payload = json.load(sys.stdin)
    except json.JSONDecodeError:
        return 0
    if not isinstance(payload, dict):
        return 0
    tool_input = payload.get("tool_input")
    if not isinstance(tool_input, dict):
        return 0
    command = tool_input.get("command")
    if not isinstance(command, str):
        return 0
    for segment in re.split(r"[|;&()`\n]+", command):
        match = re.search(r"(?:^|[\s(])git\s+(?:-C\s+\S+\s+)?add\s+(.*)", segment)
        if match and is_sweep(match.group(1)):
            sys.stderr.write(MESSAGE)
            return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
