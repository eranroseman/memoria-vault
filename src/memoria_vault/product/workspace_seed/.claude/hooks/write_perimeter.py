"""Memoria write-perimeter PreToolUse hook.

Stdlib-only and unconditional: it never needs the engine to say no. The host's
deny rules (.claude/settings.json) are layer 1; this hook is layer 2 and denies
every Edit/Write/NotebookEdit call it receives with exit code 2.
"""

import sys

MESSAGE = (
    "Memoria write perimeter: vault notes are engine-mediated — a direct edit "
    "would be recorded as the human's work by the provenance layer. "
    "Use the MCP tool `operation_run` or the `memoria` CLI."
)


def main() -> int:
    sys.stdin.read()  # Consume the hook payload; the deny is unconditional.
    print(MESSAGE, file=sys.stderr)
    return 2


if __name__ == "__main__":
    sys.exit(main())
