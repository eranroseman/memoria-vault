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
"""

from __future__ import annotations

import argparse
import datetime
import json
import re
import sys
import uuid
from pathlib import Path

_RUNTIME_ROOT = Path(__file__).resolve().parent.parent
if str(_RUNTIME_ROOT) not in sys.path:
    sys.path.insert(0, str(_RUNTIME_ROOT))

from memoria_vault.runtime.paths import resolve_vault
from memoria_vault.runtime.policy import REVIEW_GATED_PREFIXES

PATTERNS_RELDIR = "system/patterns"
PROVENANCE_RELPATH = "system/logs/patterns.jsonl"
_FM_RE = re.compile(r"^---\n(.*?)\n---\n?", re.S)


def _gated_prefixes(vault: Path) -> tuple:
    try:
        import yaml

        f = vault / ".memoria" / "schemas" / "folders.yaml"
        return tuple(yaml.safe_load(f.read_text(encoding="utf-8"))["gated_prefixes"])
    except Exception:  # noqa: BLE001
        return REVIEW_GATED_PREFIXES


def _parse(path: Path) -> tuple[dict, str]:
    import yaml

    text = path.read_text(encoding="utf-8")
    m = _FM_RE.match(text)
    if not m:
        return {}, text
    return (yaml.safe_load(m.group(1)) or {}), text[m.end() :]


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
        out.append(
            {
                "id": p.stem,
                "title": fm.get("title", p.stem),
                "mode": fm.get("mode"),
                "action": fm.get("action"),
                "posture": fm.get("posture"),
                "output_target": fm.get("output_target"),
            }
        )
    return out


def run_pattern(vault: Path, pattern_id: str, input_text: str, input_ref: str = "") -> dict:
    """Compose preamble + pattern + input; enforce the gated-zone rule; log provenance."""
    path = vault / PATTERNS_RELDIR / f"{pattern_id}.md"
    if not path.is_file():
        return {
            "error": "unknown-pattern",
            "pattern": pattern_id,
            "available": [p["id"] for p in list_patterns(vault)],
        }
    fm, body = _parse(path)
    if fm.get("lifecycle") != "current":
        return {
            "error": "pattern-not-current",
            "pattern": pattern_id,
            "lifecycle": fm.get("lifecycle"),
        }
    target = (fm.get("output_target") or "").lstrip("/")
    gated = _gated_prefixes(vault)
    dry_run = (not target) or target.startswith(gated)
    preamble_file = vault / PATTERNS_RELDIR / "_preamble.md"
    preamble = preamble_file.read_text(encoding="utf-8") if preamble_file.is_file() else ""
    prompt = body.replace("{{input}}", input_text or f"[see {input_ref}]")
    run_id = str(uuid.uuid4())[:8]
    record = {
        "timestamp": datetime.datetime.now(datetime.UTC).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "run_id": run_id,
        "pattern": pattern_id,
        "version": str(fm.get("version", "")),
        "input_ref": input_ref,
        "input_chars": len(input_text or ""),
        "output_target": target,
        "dry_run": dry_run,
    }
    provenance_logged = True
    try:
        log = vault / PROVENANCE_RELPATH
        log.parent.mkdir(parents=True, exist_ok=True)
        with log.open("a", encoding="utf-8") as f:
            f.write(json.dumps(record) + "\n")
    except Exception as exc:  # noqa: BLE001
        # The run is still returned (the prompt is the product), but the caller —
        # and the operator, via stderr — must know this run left no provenance.
        provenance_logged = False
        print(
            f"[patterns_mcp] WARNING: provenance write to {PROVENANCE_RELPATH} "
            f"failed for run {run_id} ({pattern_id}): {type(exc).__name__}: {exc}",
            file=sys.stderr,
        )
    result = {
        "run_id": run_id,
        "pattern": pattern_id,
        "prompt": f"{preamble}\n\n---\n\n{prompt}".strip(),
        "output_target": target,
        "dry_run": dry_run,
        "posture": fm.get("posture"),
        "model_hint": fm.get("model_hint") or None,
    }
    if not provenance_logged:
        result["provenance_logged"] = False
    if dry_run:
        result["note"] = (
            "output_target is missing or review-gated — the run is "
            "dry-run only; fix the pattern file (the Linter flags it)"
        )
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


def main() -> None:
    ap = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    ap.add_argument("--vault", help="vault root (or MEMORIA_VAULT_PATH)")
    ap.add_argument("--list", action="store_true", help="one-shot: list runnable patterns")
    args = ap.parse_args()
    vault = resolve_vault(args.vault)
    if args.list:
        print(json.dumps(list_patterns(vault), indent=2))
        return
    build_server(vault).run()


if __name__ == "__main__":
    main()
