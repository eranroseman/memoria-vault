"""Canonical path and glob semantics shared by Memoria policy consumers."""

from __future__ import annotations

import re

ACTIONS = frozenset({"read", "write", "append", "move", "delete", "mkdir", "auto_fix", "report"})
MUTATING_ACTIONS = frozenset({"write", "append", "move", "delete", "mkdir", "auto_fix"})
REVIEW_GATED_PREFIXES = ("notes/claims/", "notes/hubs/")


def normalize_path(path: str) -> str:
    """Return a normalized vault-relative POSIX path, rejecting traversal."""
    value = (path or "").strip().replace("\\", "/")
    while value.startswith("./"):
        value = value[2:]
    value = value.lstrip("/")
    parts: list[str] = []
    for segment in value.split("/"):
        if segment == "..":
            if not parts:
                raise ValueError(f"path escapes vault root: {path!r}")
            parts.pop()
        elif segment and segment != ".":
            parts.append(segment)
    return "/".join(parts)


def glob_to_regex(pattern: str) -> str:
    """Translate Memoria's lane glob syntax to an anchored regular expression."""
    index, length, output = 0, len(pattern), ["^"]
    while index < length:
        char = pattern[index]
        if char == "*":
            if index + 1 < length and pattern[index + 1] == "*":
                if index + 2 < length and pattern[index + 2] == "/":
                    output.append("(?:.*/)?")
                    index += 3
                else:
                    output.append(".*")
                    index += 2
            else:
                output.append("[^/]*")
                index += 1
        elif char == "?":
            output.append("[^/]")
            index += 1
        else:
            output.append(re.escape(char))
            index += 1
    output.append("$")
    return "".join(output)


def path_matches(path: str, patterns: list[str]) -> bool:
    """Return whether a path matches any lane glob."""
    return any(re.match(glob_to_regex(pattern), path) for pattern in patterns or [])


def within_scope(path: str, scopes: list[str]) -> bool:
    """Return whether a path is the given scope prefix or lies beneath it."""
    for scope in scopes or []:
        prefix = scope if scope.endswith("/") else scope + "/"
        if re.match(glob_to_regex(prefix + "**"), path) or re.match(
            glob_to_regex(prefix.rstrip("/")), path.rstrip("/")
        ):
            return True
    return False
