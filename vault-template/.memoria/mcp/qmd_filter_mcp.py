#!/usr/bin/env python3
"""Filtered qmd MCP wrapper for Memoria claim currency (ADR-10).

qmd is the local hybrid search backend. Memoria owns one extra rule over it:
claim notes with a non-empty ``superseded_by`` relation are hidden from normal
query/write retrieval. Callers can set ``include_superseded=True`` for explicit
historical lookup.
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


def _vault_relative(ref: str, vault: Path) -> str:
    text = ref or ""
    if text.startswith("qmd://"):
        parts = text.split("/", 3)
        return parts[3] if len(parts) > 3 else ""
    text = text.split(":", 1)[0]
    path = Path(text.removeprefix("./"))
    if path.is_absolute():
        try:
            return str(path.resolve().relative_to(vault.resolve())).replace("\\", "/")
        except (OSError, ValueError):
            return ""
    return str(path).replace("\\", "/")


def _frontmatter(path: Path) -> dict[str, Any]:
    try:
        text = path.read_text(encoding="utf-8", errors="ignore")
    except OSError:
        return {}
    if not text.startswith("---\n"):
        return {}
    end = text.find("\n---", 4)
    if end == -1:
        return {}
    import yaml

    return yaml.safe_load(text[4:end]) or {}


def is_superseded_claim(vault: Path, ref: str) -> bool:
    rel = _vault_relative(ref, vault)
    if not rel.startswith("notes/claims/"):
        return False
    value = _frontmatter(vault / rel).get("superseded_by")
    return bool(value)


def filter_results(
    vault: Path, rows: list[dict[str, Any]], include_superseded: bool = False
) -> list[dict[str, Any]]:
    if include_superseded:
        return rows
    return [row for row in rows if not is_superseded_claim(vault, str(row.get("file", "")))]


def _run(qmd: str, *args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run([qmd, *args], check=False, text=True, capture_output=True)


def _json_search(
    vault: Path,
    qmd: str,
    command: str,
    query_text: str,
    n: int,
    include_superseded: bool,
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
    return filter_results(vault, rows, include_superseded)


def build_server(vault: Path, qmd: str):
    from mcp.server.fastmcp import FastMCP  # type: ignore

    server = FastMCP("qmd")

    @server.tool()
    def search(query: str, n: int = 5, include_superseded: bool = False):
        """BM25 keyword search. Superseded claims are excluded unless requested."""
        return _json_search(vault, qmd, "search", query, n, include_superseded)

    @server.tool()
    def query(query: str, n: int = 5, include_superseded: bool = False):
        """Hybrid qmd query. Superseded claims are excluded unless requested."""
        return _json_search(vault, qmd, "query", query, n, include_superseded)

    @server.tool()
    def vsearch(query: str, n: int = 5, include_superseded: bool = False):
        """Vector search. Superseded claims are excluded unless requested."""
        return _json_search(vault, qmd, "vsearch", query, n, include_superseded)

    @server.tool()
    def deep_search(query: str, n: int = 5, include_superseded: bool = False):
        """Compatibility alias for hybrid qmd query."""
        return _json_search(vault, qmd, "query", query, n, include_superseded)

    @server.tool()
    def get(file: str, include_superseded: bool = False) -> str | dict[str, str]:
        """Fetch a document. Superseded claims require explicit historical lookup."""
        if is_superseded_claim(vault, file) and not include_superseded:
            return {
                "error": "superseded-claim",
                "file": file,
                "message": "superseded claim hidden by default; retry with include_superseded=True",
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
