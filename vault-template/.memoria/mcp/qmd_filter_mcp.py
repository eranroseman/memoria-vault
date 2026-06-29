#!/usr/bin/env python3
"""Filtered qmd MCP wrapper for the alpha.11 read barrier.

qmd is the local hybrid search backend. Memoria owns one extra rule over it:
normal retrieval returns only Concepts with ``check_status: checked``.
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path
from typing import Any

_RUNTIME_ROOT = Path(__file__).resolve().parent.parent
if str(_RUNTIME_ROOT) not in sys.path:
    sys.path.insert(0, str(_RUNTIME_ROOT))

from memoria_vault.runtime.paths import resolve_vault
from memoria_vault.runtime.search_index import (
    filter_checked_results,
    is_checked_concept,
    qmd_result_path,
)


def filter_results(vault: Path, rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return filter_checked_results(vault, rows)


def _run(qmd: str, *args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run([qmd, *args], check=False, text=True, capture_output=True)


def _json_search(
    vault: Path,
    qmd: str,
    command: str,
    query_text: str,
    n: int,
) -> list[dict[str, Any]] | dict[str, str]:
    result = _run(qmd, command, query_text, "--format", "json", "-n", str(n))
    if result.returncode != 0:
        return {"error": "qmd-failed", "detail": result.stderr.strip() or result.stdout.strip()}
    try:
        rows = json.loads(result.stdout)
    except json.JSONDecodeError as exc:
        return {"error": "qmd-invalid-json", "detail": str(exc)}
    if not isinstance(rows, list):
        return {"error": "qmd-invalid-json", "detail": "expected a JSON list"}
    return filter_results(vault, rows)


def build_server(vault: Path, qmd: str):
    from mcp.server.fastmcp import FastMCP  # type: ignore

    server = FastMCP("qmd")

    @server.tool()
    def search(query: str, n: int = 5):
        """BM25 keyword search over checked Concepts."""
        return _json_search(vault, qmd, "search", query, n)

    @server.tool()
    def query(query: str, n: int = 5):
        """Hybrid qmd query over checked Concepts."""
        return _json_search(vault, qmd, "query", query, n)

    @server.tool()
    def vsearch(query: str, n: int = 5):
        """Vector search over checked Concepts."""
        return _json_search(vault, qmd, "vsearch", query, n)

    @server.tool()
    def deep_search(query: str, n: int = 5):
        """Compatibility alias for hybrid qmd query."""
        return _json_search(vault, qmd, "query", query, n)

    @server.tool()
    def get(file: str) -> str | dict[str, str]:
        """Fetch a checked document."""
        rel = qmd_result_path(file, vault)
        if not is_checked_concept(vault, rel):
            return {
                "error": "unchecked-concept",
                "file": rel or file,
                "message": "Concept is not checked; retrieval is blocked by the read barrier.",
            }
        result = _run(qmd, "get", file)
        if result.returncode != 0:
            return {"error": "qmd-failed", "detail": result.stderr.strip() or result.stdout.strip()}
        return result.stdout

    @server.tool()
    def status() -> str | dict[str, str]:
        result = _run(qmd, "status")
        if result.returncode != 0:
            return {"error": "qmd-failed", "detail": result.stderr.strip() or result.stdout.strip()}
        return result.stdout

    return server


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--vault", help="vault root (or MEMORIA_VAULT_PATH)")
    ap.add_argument("--qmd", default="qmd", help="qmd executable path")
    args = ap.parse_args()
    build_server(resolve_vault(args.vault), args.qmd).run()


if __name__ == "__main__":
    main()
