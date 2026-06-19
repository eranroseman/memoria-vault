#!/usr/bin/env python3
"""tasks_mcp.py — the Co-PI's delegation path (ADR-48).

One tool: `delegate_route_task`. The Co-PI converses and **delegates every
write** — this server turns a delegation into a Hermes kanban card on the right
lane, after validating the handoff against the lane's ceiling: `allowed_paths`
may *narrow* but never *widen* the lane's write scope (lane = ceiling, payload
= floor). Card creation shells out to `hermes kanban create` — the same proven
path the sweeps operation uses — so board semantics (WIP, dedup, dispatch) stay
Hermes-native.

    python tasks_mcp.py --vault <path>            # run the MCP server (needs `mcp`)
"""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from pathlib import Path

_RUNTIME_ROOT = Path(__file__).resolve().parent.parent
_OPERATIONS_LIB = _RUNTIME_ROOT / "operations" / "lib"
for _path in (_RUNTIME_ROOT, _OPERATIONS_LIB):
    if str(_path) not in sys.path:
        sys.path.insert(0, str(_path))

import loudness  # noqa: E402
from memoria_runtime.policy import within_scope  # noqa: E402

# task lane -> the background agent that owns it (ADR-48 §4.1)
LANE_PROFILE = {
    "catalog": "memoria-librarian",
    "extract": "memoria-librarian",
    "link": "memoria-librarian",
    "map": "memoria-librarian",
    "draft": "memoria-writer",
    "verify": "memoria-peer-reviewer",
    "code": "memoria-engineer",
}


def _lane_override(vault: Path, profile: str) -> dict:
    import yaml

    name = profile.removeprefix("memoria-")
    f = vault / ".memoria" / "lane-overrides" / f"{name}.yaml"
    if not f.is_file():
        return {}
    try:
        return yaml.safe_load(f.read_text(encoding="utf-8")) or {}
    except yaml.YAMLError as exc:
        # Fail-closed (an empty override means every delegated path exceeds the
        # ceiling), but never silently: a corrupt lane file is config drift the
        # operator must see, not a quiet hard-deny of a whole lane.
        print(f"[tasks_mcp] WARNING: cannot parse lane-override {f}: {exc} — "
              f"treating the lane as having no write scope (fail-closed)",
              file=sys.stderr)
        return {}


def _within_scope(path: str, scopes: list[str]) -> bool:
    """True if `path` sits under any lane write_scope entry.

    write_scope entries are PREFIX-GLOBS, not plain prefixes — the engineer's
    lane carries `projects/*/code/`, which must admit `projects/x/code/main.py`.
    Reuse policy_mcp.within_scope (a trailing-slash scope matches `scope + **`)
    so the delegation ceiling and the write gate agree on semantics."""
    return within_scope(path.lstrip("/"), scopes)


def validate(vault: Path, lane: str, allowed_paths: list[str]) -> list[str]:
    """Ceiling check: every requested path prefix must sit inside the lane's
    write_scope. Returns error strings (empty = valid)."""
    errors: list[str] = []
    profile = LANE_PROFILE.get(lane)
    if not profile:
        return [f"unknown lane '{lane}' (one of {sorted(LANE_PROFILE)})"]
    override = _lane_override(vault, profile)
    scopes = (override.get("routing") or {}).get("write_scope") or []
    if scopes == [] and "write_scope" in (override.get("routing") or {}):
        # an explicitly empty scope (the Co-PI pattern) can never receive writes
        return [f"lane '{lane}' has an empty write scope — nothing may be delegated to it"]
    for p in allowed_paths:
        if not _within_scope(p, scopes):
            errors.append(f"allowed_path '{p}' exceeds the {lane} lane ceiling {scopes}")
    return errors


def create_card(
    lane: str,
    goal: str,
    body: str,
    idempotency_key: str = "",
    runner=subprocess.run,
) -> dict:
    """Shell out to `hermes kanban create` (the proven path; board stays Hermes-native)."""
    cmd = ["hermes", "kanban", "create", goal,
           "--assignee", LANE_PROFILE[lane],
           "--created-by", "memoria-copi", "--body", body, "--json"]
    if idempotency_key:
        cmd += ["--idempotency-key", idempotency_key]
    try:
        r = runner(cmd, capture_output=True, text=True, timeout=30, check=True)
        obj = json.loads(r.stdout or "{}")
        return {"created": True, "card_id": str(obj.get("id") or obj.get("task_id") or "queued"),
                "lane": lane, "assignee": LANE_PROFILE[lane]}
    except FileNotFoundError:
        return {"created": False, "error": "hermes-cli-not-found",
                "fallback": f"run the palette command for the '{lane}' task, or "
                            f"`hermes kanban create {goal!r} --assignee {LANE_PROFILE[lane]}`"}
    except subprocess.CalledProcessError as e:
        return {"created": False, "error": f"kanban-create-exit-{e.returncode}",
                "detail": (e.stderr or e.stdout or "").strip()[:300]}
    except subprocess.TimeoutExpired:
        return {"created": False, "error": "kanban-create-timeout"}


def delegate(vault: Path, lane: str, goal: str, context: str = "",
             allowed_paths: list[str] | None = None, expected_outputs: str = "",
             review_checks: str = "", idempotency_key: str = "",
             card_runner=subprocess.run) -> dict:
    """Validate the handoff payload against the lane ceiling, then create the card."""
    blockers = loudness.open_blockers(vault)
    if blockers:
        return {"created": False, "error": "loudness-block-active",
                "detail": loudness.blocker_message(blockers), "blockers": blockers}
    allowed_paths = allowed_paths or []
    errors = validate(vault, lane, allowed_paths)
    if errors:
        return {"created": False, "error": "ceiling-violation", "detail": errors}
    body_parts = [f"## Goal\n{goal}"]
    if context:
        body_parts.append(f"## Context\n{context}")
    if allowed_paths:
        body_parts.append("## Allowed paths\n" + "\n".join(f"- {p}" for p in allowed_paths))
    if expected_outputs:
        body_parts.append(f"## Expected outputs\n{expected_outputs}")
    if review_checks:
        body_parts.append(f"## Review checks\n{review_checks}")
    return create_card(lane, goal, "\n\n".join(body_parts), idempotency_key, runner=card_runner)


def build_server(vault: Path):
    from mcp.server.fastmcp import FastMCP  # type: ignore

    server = FastMCP("memoria-tasks")

    @server.tool()
    def delegate_route_task(lane: str, goal: str, context: str = "",
                            allowed_paths: list[str] | None = None,
                            expected_outputs: str = "", review_checks: str = "",
                            idempotency_key: str = "") -> dict:
        """Delegate a task to a background lane (catalog · extract · link · map ·
        draft · verify · code). The handoff is validated against the lane's
        write-scope ceiling before a kanban card is created."""
        return delegate(vault, lane, goal, context, allowed_paths,
                        expected_outputs, review_checks, idempotency_key)

    return server


def resolve_vault(arg: str | None) -> Path:
    raw = arg or os.environ.get("MEMORIA_VAULT_PATH") or os.environ.get("OBSIDIAN_VAULT_PATH")
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
    args = ap.parse_args()
    build_server(resolve_vault(args.vault)).run()


if __name__ == "__main__":
    main()
