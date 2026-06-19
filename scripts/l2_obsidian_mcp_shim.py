#!/usr/bin/env python3
"""Filesystem-backed Obsidian MCP shim for the opt-in live L2 smoke.

The tool names intentionally mirror the Obsidian MCP write shape so the Memoria
policy-gate plugin sees `obsidian_*` writes and audits the disposable vault.
"""

from __future__ import annotations

import argparse
from pathlib import Path


def safe_vault_path(vault: Path, relpath: str) -> Path:
    candidate = Path(relpath)
    if candidate.is_absolute() or ".." in candidate.parts:
        raise ValueError(f"path must stay inside the vault: {relpath}")
    resolved = (vault / candidate).resolve()
    try:
        resolved.relative_to(vault.resolve())
    except ValueError as exc:
        raise ValueError(f"path escapes the vault: {relpath}") from exc
    return resolved


def put_content(vault: Path, path: str, content: str) -> dict[str, str]:
    target = safe_vault_path(vault, path)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(content, encoding="utf-8")
    return {"path": path, "status": "written"}


def append_content(vault: Path, path: str, content: str) -> dict[str, str]:
    target = safe_vault_path(vault, path)
    target.parent.mkdir(parents=True, exist_ok=True)
    with target.open("a", encoding="utf-8") as handle:
        handle.write(content)
    return {"path": path, "status": "appended"}


def get_content(vault: Path, path: str) -> str:
    return safe_vault_path(vault, path).read_text(encoding="utf-8")


def serve(vault: Path) -> None:
    try:
        from mcp.server.fastmcp import FastMCP  # type: ignore
    except ImportError as exc:
        raise SystemExit(
            "Missing MCP SDK. Install runtime deps first: "
            "python -m pip install -r src/.memoria/mcp/requirements.txt"
        ) from exc

    mcp = FastMCP("l2-obsidian-shim")

    @mcp.tool(name="obsidian_put_content")
    def _put(path: str, content: str) -> dict[str, str]:
        """Write a complete vault-relative file."""
        return put_content(vault, path, content)

    @mcp.tool(name="obsidian_append_content")
    def _append(path: str, content: str) -> dict[str, str]:
        """Append text to a vault-relative file."""
        return append_content(vault, path, content)

    @mcp.tool(name="obsidian_get_content")
    def _get(path: str) -> str:
        """Read a vault-relative file."""
        return get_content(vault, path)

    mcp.run()


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--vault", required=True, type=Path, help="disposable vault root")
    args = parser.parse_args(argv)
    serve(args.vault.resolve())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
