#!/usr/bin/env python3
"""patterns_mcp.py — the one pattern runner (ADR-53).

Patterns are *data* (markdown prompt-transformations in `system/patterns/`); this
server is the single audited chokepoint that runs them. `patterns_run` loads a
pattern by id, refuses any `output_target` inside a review-gated zone (the run
degrades to dry-run and the Linter flags the pattern file), composes
preamble + pattern + input, logs per-run provenance, and returns the composed
prompt + target for the calling agent to execute and write through the gated path.
The runner itself never writes content — propose-not-dispose holds.

    python patterns_mcp.py --vault <path>            # run the MCP server (needs `mcp`)
    python patterns_mcp.py --vault <path> --list     # one-shot: list runnable patterns
    python patterns_mcp.py --self-test
"""

from __future__ import annotations

import argparse
import datetime
import json
import os
import re
import sys
import uuid
from pathlib import Path

PATTERNS_RELDIR = "system/patterns"
PROVENANCE_RELPATH = "system/logs/patterns.jsonl"
_FM_RE = re.compile(r"^---\n(.*?)\n---\n?", re.S)

FALLBACK_GATED = ("notes/claims/", "notes/hubs/")


def _gated_prefixes(vault: Path) -> tuple:
    try:
        import yaml

        f = vault / ".memoria" / "schemas" / "folders.yaml"
        return tuple(yaml.safe_load(f.read_text(encoding="utf-8"))["gated_prefixes"])
    except Exception:
        return FALLBACK_GATED


def _parse(path: Path) -> tuple[dict, str]:
    import yaml

    text = path.read_text(encoding="utf-8")
    m = _FM_RE.match(text)
    if not m:
        return {}, text
    return (yaml.safe_load(m.group(1)) or {}), text[m.end():]


def list_patterns(vault: Path, mode: str = "") -> list[dict]:
    """Runnable (lifecycle: current) patterns, optionally filtered by mode."""
    out = []
    d = vault / PATTERNS_RELDIR
    for p in sorted(d.glob("*.md")) if d.is_dir() else []:
        if p.name.startswith("_"):
            continue
        fm, _ = _parse(p)
        if fm.get("type") != "pattern" or fm.get("lifecycle") != "current":
            continue
        if mode and fm.get("mode") not in (mode, "both"):
            continue
        out.append({"id": p.stem, "title": fm.get("title", p.stem),
                    "mode": fm.get("mode"), "action": fm.get("action"),
                    "posture": fm.get("posture"),
                    "output_target": fm.get("output_target")})
    return out


def run_pattern(vault: Path, pattern_id: str, input_text: str,
                input_ref: str = "") -> dict:
    """Compose preamble + pattern + input; enforce the gated-zone rule; log provenance."""
    path = vault / PATTERNS_RELDIR / f"{pattern_id}.md"
    if not path.is_file():
        return {"error": "unknown-pattern", "pattern": pattern_id,
                "available": [p["id"] for p in list_patterns(vault)]}
    fm, body = _parse(path)
    if fm.get("lifecycle") != "current":
        return {"error": "pattern-not-current", "pattern": pattern_id,
                "lifecycle": fm.get("lifecycle")}
    target = (fm.get("output_target") or "").lstrip("/")
    gated = _gated_prefixes(vault)
    dry_run = (not target) or target.startswith(gated)
    preamble_file = vault / PATTERNS_RELDIR / "_preamble.md"
    preamble = preamble_file.read_text(encoding="utf-8") if preamble_file.is_file() else ""
    prompt = body.replace("{{input}}", input_text or f"[see {input_ref}]")
    run_id = str(uuid.uuid4())[:8]
    record = {
        "timestamp": datetime.datetime.now(datetime.timezone.utc)
                       .strftime("%Y-%m-%dT%H:%M:%SZ"),
        "run_id": run_id, "pattern": pattern_id,
        "version": str(fm.get("version", "")),
        "input_ref": input_ref, "input_chars": len(input_text or ""),
        "output_target": target, "dry_run": dry_run,
    }
    log = vault / PROVENANCE_RELPATH
    log.parent.mkdir(parents=True, exist_ok=True)
    with log.open("a", encoding="utf-8") as f:
        f.write(json.dumps(record) + "\n")
    result = {
        "run_id": run_id, "pattern": pattern_id,
        "prompt": f"{preamble}\n\n---\n\n{prompt}".strip(),
        "output_target": target,
        "dry_run": dry_run,
        "posture": fm.get("posture"),
        "model_hint": fm.get("model_hint") or None,
    }
    if dry_run:
        result["note"] = ("output_target is missing or review-gated — the run is "
                          "dry-run only; fix the pattern file (the Linter flags it)")
    return result


def build_server(vault: Path):
    from mcp.server.fastmcp import FastMCP  # type: ignore

    server = FastMCP("memoria-patterns")

    @server.tool()
    def patterns_list(mode: str = "") -> list[dict]:
        """Runnable patterns, optionally filtered by mode (library | project)."""
        return list_patterns(vault, mode)

    @server.tool()
    def patterns_run(pattern_id: str, input_text: str = "", input_ref: str = "") -> dict:
        """Compose a pattern run: preamble + pattern + input -> the prompt to execute,
        with the staging output_target. Gated targets degrade to dry-run. Every run
        is provenance-logged."""
        return run_pattern(vault, pattern_id, input_text, input_ref)

    return server


def _self_test() -> int:
    import tempfile
    failures = 0

    def ck(label: str, ok: bool) -> None:
        nonlocal failures
        print(("  ok " if ok else "  FAIL ") + label)
        if not ok:
            failures += 1

    with tempfile.TemporaryDirectory() as td:
        v = Path(td)
        pd = v / PATTERNS_RELDIR
        pd.mkdir(parents=True)
        (pd / "_preamble.md").write_text("VOICE RULES", encoding="utf-8")
        (pd / "good.md").write_text(
            "---\ntitle: Good\ntype: pattern\nlifecycle: current\nposture: librarian\n"
            "mode: library\naction: summarize\ninput: note\noutput_target: 'notes/fleeting/'\n---\n"
            "Do X with {{input}}.\n", encoding="utf-8")
        (pd / "gated.md").write_text(
            "---\ntitle: Bad\ntype: pattern\nlifecycle: current\nposture: librarian\n"
            "mode: library\naction: write\ninput: note\noutput_target: 'notes/claims/'\n---\nY {{input}}\n",
            encoding="utf-8")
        (pd / "draft.md").write_text(
            "---\ntitle: D\ntype: pattern\nlifecycle: proposed\nposture: librarian\n"
            "mode: library\naction: x\ninput: note\noutput_target: 'projects/'\n---\nZ\n",
            encoding="utf-8")
        ck("list shows only current patterns",
           [p["id"] for p in list_patterns(v)] == ["gated", "good"])
        ck("mode filter works", [p["id"] for p in list_patterns(v, "project")] == [])
        r = run_pattern(v, "good", "INPUT TEXT", "notes/source/s.md")
        ck("preamble + substitution composed",
           "VOICE RULES" in r["prompt"] and "Do X with INPUT TEXT." in r["prompt"])
        ck("staging target passes", r["dry_run"] is False and r["output_target"] == "notes/fleeting/")
        g = run_pattern(v, "gated", "x")
        ck("gated target degrades to dry-run", g["dry_run"] is True and "note" in g)
        d = run_pattern(v, "draft", "x")
        ck("non-current pattern refused", d.get("error") == "pattern-not-current")
        u = run_pattern(v, "ghost", "x")
        ck("unknown pattern lists available", u.get("error") == "unknown-pattern")
        log = (v / PROVENANCE_RELPATH).read_text(encoding="utf-8").splitlines()
        ck("provenance logged per run", len(log) == 2)  # good + gated (refusals don't run)
    print("self-test:", "PASS" if failures == 0 else f"{failures} FAILURE(S)")
    return 1 if failures else 0


def resolve_vault(arg: str | None) -> Path:
    raw = arg or os.environ.get("MEMORIA_VAULT_PATH", "")
    if not raw:
        sys.exit("provide --vault or set MEMORIA_VAULT_PATH")
    v = Path(raw).expanduser()
    if not v.is_dir():
        sys.exit(f"not a directory: {v}")
    return v


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--vault", help="vault root (or MEMORIA_VAULT_PATH)")
    ap.add_argument("--list", action="store_true", help="one-shot: list runnable patterns")
    ap.add_argument("--self-test", action="store_true")
    args = ap.parse_args()
    if args.self_test:
        sys.exit(_self_test())
    vault = resolve_vault(args.vault)
    if args.list:
        print(json.dumps(list_patterns(vault), indent=2))
        return
    build_server(vault).run()


if __name__ == "__main__":
    main()
