#!/usr/bin/env python3
"""ingest_mcp.py — the deterministic ingest pipeline, exposed as an MCP tool.

The Librarian's capability allowlist (ADR-27) disables code_execution / terminal /
file, so the worker agent cannot run `pipeline.py` as a CLI. The deterministic
spine therefore reaches the agent the same way vault access and the policy gate
do — over **MCP**. This thin server wraps `pipeline.run()` as a single tool:

    ingest_pipeline(citekey, enrich=True) -> the draft bundle (with two holes)

The tool only **reads + computes** (Tier-0 assembly + Tier-1 enrich/extract/link);
it performs no vault writes. The agent fills the two holes (_proposed_classification
and the [!brief]) and writes through the gated obsidian MCP, exactly as before.

    python ingest_mcp.py --vault <path>      # run the server over stdio
    python ingest_mcp.py --self-test         # synthetic, offline; no mcp pkg needed
"""
from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

# pipeline.py (and the modules it imports) live in the skill's scripts dir, which
# sits beside this mcp/ dir under .memoria/. Resolve it relative to __file__ so the
# import works identically in the repo and in a deployed vault.
SCRIPTS_DIR = (Path(__file__).resolve().parent.parent
               / "profiles/memoria-librarian/skills/obsidian-paper-note/scripts")
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))


def build_server(vault: Path):
    """Wrap the pipeline as an MCP server. Imported lazily so the self-test
    doesn't require the `mcp` package."""
    import pipeline  # from SCRIPTS_DIR
    from mcp.server.fastmcp import FastMCP  # type: ignore

    server = FastMCP("memoria-ingest")
    bib_path = vault / ".memoria" / "memoria.bib"

    @server.tool()
    def ingest_pipeline(citekey: str, enrich: bool = True, pdf_path: str = "") -> dict:
        """Run the deterministic ingest pipeline for a citekey and return the draft
        bundle: the assembled paper/item note (lifecycle: captured), merged
        metadata + _enrichment, the extract status, the link plan, and
        holes=[_proposed_classification, brief] for the agent to fill. Reads and
        computes only — writes nothing. Set enrich=False for the Tier-0 floor."""
        if not bib_path.is_file():
            return {"error": "bib-not-found", "bib": str(bib_path)}
        bib_text = bib_path.read_text(encoding="utf-8", errors="ignore")
        try:
            return pipeline.run(citekey, bib_text, vault, pdf_path or None, enrich=enrich)
        except KeyError:
            return {"error": "citekey-not-found", "citekey": citekey}

    return server


def resolve_vault(arg: str | None) -> Path:
    raw = arg or os.environ.get("OBSIDIAN_VAULT_PATH") or os.environ.get("MEMORIA_VAULT_PATH")
    if not raw:
        sys.exit("no vault path: pass --vault <path> or set OBSIDIAN_VAULT_PATH")
    vault = Path(raw).expanduser().resolve()
    if not vault.is_dir():
        sys.exit(f"not a directory: {vault}")
    return vault


def self_test() -> int:
    """Offline: the module imports the pipeline and runs a Tier-0 fixture through it."""
    import pipeline
    fixture = ("@article{x2024Test,\n  title = {A Test},\n  author = {Doe, Jane},\n"
               "  year = {2024},\n  doi = {10.1/x},\n  journal = {J Tests},\n}\n")
    b = pipeline.run("x2024Test", fixture, enrich=False)
    checks = [
        ("scripts dir importable", SCRIPTS_DIR.is_dir()),
        ("pipeline runs Tier-0", b["lifecycle"] == "captured" and b["ingest_status"] == "tier0"),
        ("bundle declares the two holes", b["holes"] == ["_proposed_classification", "brief"]),
        ("identity assembled", b["frontmatter"]["title"] == "A Test"),
    ]
    bad = [n for n, ok in checks if not ok]
    for n, ok in checks:
        print(f"  {'PASS' if ok else 'FAIL'}  {n}")
    print(f"\n{'OK' if not bad else f'{len(bad)} FAILING'}: ingest_mcp.py self-test")
    return 1 if bad else 0


def main() -> None:
    ap = argparse.ArgumentParser(description="Deterministic ingest pipeline as an MCP server (ADR-30)")
    ap.add_argument("--vault", help="vault root (or set OBSIDIAN_VAULT_PATH)")
    ap.add_argument("--self-test", action="store_true", help="run unit tests and exit")
    args = ap.parse_args()
    if args.self_test:
        sys.exit(1 if self_test() else 0)
    build_server(resolve_vault(args.vault)).run()


if __name__ == "__main__":
    main()
