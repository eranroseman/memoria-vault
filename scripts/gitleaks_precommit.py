#!/usr/bin/env python3
"""Block common high-risk secret shapes before commit."""

from __future__ import annotations

import re
import sys
from pathlib import Path

PATTERNS = (
    ("AWS access key", re.compile(r"\b(?:AKIA|ASIA)[0-9A-Z]{16}\b")),
    ("OpenAI API key", re.compile(r"\bsk-[A-Za-z0-9_-]{32,}\b")),
    ("Google API key", re.compile(r"\bAIza[0-9A-Za-z_-]{35}\b")),
    ("private key", re.compile(r"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----")),
)


def findings(paths: list[str]) -> list[str]:
    hits = []
    for raw in paths:
        path = Path(raw)
        if not path.is_file():
            continue
        text = path.read_text(encoding="utf-8", errors="ignore")
        for name, pattern in PATTERNS:
            for match in pattern.finditer(text):
                line = text.count("\n", 0, match.start()) + 1
                hits.append(f"{path}:{line}: {name}")
    return hits


def main(argv: list[str] | None = None) -> int:
    hits = findings(argv if argv is not None else sys.argv[1:])
    if hits:
        print("gitleaks: possible secret(s) found", file=sys.stderr)
        for hit in hits:
            print(f"  {hit}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
