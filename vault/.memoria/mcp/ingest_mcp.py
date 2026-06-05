#!/usr/bin/env python3
"""ingest_mcp.py — the deterministic ingest pipeline, exposed as an MCP tool.

The Librarian's capability allowlist (ADR-27) disables code_execution / terminal /
file, so the worker agent cannot run `pipeline.py` as a CLI. The deterministic
spine therefore reaches the agent the same way vault access and the policy gate
do — over **MCP**. This thin server wraps `pipeline.run()` as a single tool:

    ingest_pipeline(citekey, enrich=True) -> the draft bundle (with two holes)

The tool **reads + computes** (Tier-0 assembly + Tier-1 enrich/extract/link). It
writes no vault notes — but it does persist the *un-gated derived artifacts* the
agent can't: the full-text extract under `90-assets/extracts/` (outside the
librarian write lane) and the capture-intake anchor (see `append_intake_anchor`).
The agent fills the two holes (_proposed_classification and the [!brief]) and
writes the notes through the gated obsidian MCP, exactly as before.

    python ingest_mcp.py --vault <path>      # run the server over stdio
    python ingest_mcp.py --self-test         # synthetic, offline; no mcp pkg needed
"""
from __future__ import annotations

import argparse
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

# pipeline.py (and the modules it imports) live in the skill's scripts dir, which
# sits beside this mcp/ dir under .memoria/. Resolve it relative to __file__ so the
# import works identically in the repo and in a deployed vault.
SCRIPTS_DIR = (Path(__file__).resolve().parent.parent
               / "profiles/memoria-librarian/skills/obsidian-paper-note/scripts")
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

INTAKE_LOG = "99-system/logs/capture-intake.jsonl"


def append_intake_anchor(vault: Path, citekey: str, note_path: str) -> bool:
    """Append a capture-intake durability anchor for a citekey, idempotently.

    The Zotero macro writes this anchor at capture (before the note). For ingest
    that did NOT come through the macro (a board re-ingest or a manual card), this
    backstops it so the reconcile sweep can recover the citekey. Append-only and
    de-duped by citekey; this is the explicitly *un-gated* durability log, the one
    write this server makes. Returns True if a line was appended."""
    log = vault / INTAKE_LOG
    if log.is_file():
        for line in log.read_text(encoding="utf-8", errors="ignore").splitlines():
            try:
                if json.loads(line).get("citekey") == citekey:
                    return False  # already anchored
            except json.JSONDecodeError:
                continue
    rec = {"ts": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
           "citekey": citekey, "source": "ingest-tool", "note_path": note_path}
    log.parent.mkdir(parents=True, exist_ok=True)
    with log.open("a", encoding="utf-8") as f:
        f.write(json.dumps(rec) + "\n")
    return True


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
        holes=[_proposed_classification, brief] for the agent to fill. Writes no
        vault notes; it does persist the un-gated derived artifacts (the full-text
        extract under 90-assets/ and the capture-intake anchor). Set enrich=False
        for the Tier-0 floor."""
        if not bib_path.is_file():
            return {"error": "bib-not-found", "bib": str(bib_path)}
        bib_text = bib_path.read_text(encoding="utf-8", errors="ignore")
        try:
            bundle = pipeline.run(citekey, bib_text, vault, pdf_path or None, enrich=enrich)
        except KeyError:
            return {"error": "citekey-not-found", "citekey": citekey}
        except Exception as exc:
            print(f"[ingest_mcp] pipeline.run failed for {citekey}: "
                  f"{type(exc).__name__}: {exc}", file=sys.stderr)
            return {"error": "pipeline-error",
                    "citekey": citekey,
                    "detail": f"{type(exc).__name__}: {exc}"}
        # persist the full-text extract to 90-assets/ (outside the agent's write lane,
        # so the tool writes it, not the worker) and strip the bulk text from the reply
        ex = bundle.get("extract")
        if isinstance(ex, dict):
            text = ex.pop("text", "")
            if text:
                safe_ck = citekey.replace("/", "_").replace("..", "_").replace("\\", "_")
                dest = vault / "90-assets" / "extracts" / f"{safe_ck}.md"
                if not dest.resolve().is_relative_to((vault / "90-assets").resolve()):
                    return {"error": "invalid-citekey", "citekey": citekey,
                            "message": "citekey would escape the assets directory"}
                dest.parent.mkdir(parents=True, exist_ok=True)
                dest.write_text(text, encoding="utf-8")
        # backstop the durability anchor for non-macro ingest (board / manual cards)
        append_intake_anchor(vault, citekey, bundle.get("path", ""))
        return bundle

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

    # capture-intake anchor: appended once, idempotent on a second call
    import tempfile
    with tempfile.TemporaryDirectory() as td:
        v = Path(td)
        first = append_intake_anchor(v, "x2024Test", "20-sources/01-papers/x2024Test.md")
        second = append_intake_anchor(v, "x2024Test", "20-sources/01-papers/x2024Test.md")
        lines = (v / INTAKE_LOG).read_text().splitlines()
        anchor_ok = first and not second and len(lines) == 1 and json.loads(lines[0])["citekey"] == "x2024Test"

    # citekey sanitization: slashes and '..' are replaced so the path stays inside 90-assets/
    safe_ck = "../../etc/passwd".replace("/", "_").replace("..", "_").replace("\\", "_")
    sanitize_ok = "/" not in safe_ck and ".." not in safe_ck

    checks = [
        ("scripts dir importable", SCRIPTS_DIR.is_dir()),
        ("pipeline runs Tier-0", b["lifecycle"] == "captured" and b["ingest_status"] == "tier0"),
        ("bundle declares the two holes", b["holes"] == ["_proposed_classification", "brief"]),
        ("identity assembled", b["frontmatter"]["title"] == "A Test"),
        ("intake anchor appended once + idempotent", anchor_ok),
        ("citekey sanitization strips traversal chars", sanitize_ok),
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
