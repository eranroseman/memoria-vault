"""Shared utilities for the Memoria MCP + detector tooling.

Dependency-free (stdlib only) so every module that imports this can still run and
self-test without PyYAML, ``mcp``, or any other optional runtime dependency.
"""

from __future__ import annotations

from memoria.runtime.jsonl import append_jsonl, iter_jsonl
from memoria.runtime.paths import load_json, resolve_vault, safe_filename
from memoria.runtime.time import now_iso, parse_iso

__all__ = [
    "append_jsonl",
    "iter_jsonl",
    "load_json",
    "now_iso",
    "parse_iso",
    "resolve_vault",
    "safe_filename",
]
