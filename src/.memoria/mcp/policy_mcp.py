#!/usr/bin/env python3
"""Compatibility entrypoint for the Memoria policy MCP.

The behavior-preserving policy implementation is split under
``memoria.runtime.policy``:

- ``model``: LanePolicy and Decision data models
- ``paths``: path normalization and glob semantics
- ``lanes``: lane YAML loading and gated-prefix discovery
- ``decision``: pure allow/deny/dry_run decisions
- ``audit``: SHA-256 and append-only audit helpers
- ``engine``: stateful lane cache, hash, audit, loudness, and skill narrowing

This file remains the installed/deployed CLI path and re-exports the old public
symbols so existing tests, hooks, and profile config do not move in the split PR.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

_RUNTIME_ROOT = Path(__file__).resolve().parent.parent
_OPERATIONS_LIB = _RUNTIME_ROOT / "operations" / "lib"
_RELEASE_ROOT = _RUNTIME_ROOT.parents[1]
for _path in (_RELEASE_ROOT, _RUNTIME_ROOT, _OPERATIONS_LIB):
    if str(_path) not in sys.path:
        sys.path.insert(0, str(_path))

from policy_server import build_server, resolve_vault

from memoria.runtime.policy.audit import (
    AUDIT_RELPATH,
    AUDIT_SCHEMA_VERSION,
    EMPTY_SHA256,
    REVIEW_MODE,
    append_audit,
    sha256_file,
)
from memoria.runtime.policy.decision import (
    AUTO_FIX_ALLOWED_CLASSES,
    AUTO_FIX_DENY_CLASSES,
    AUTO_FIX_DRY_RUN_CLASSES,
    compose_skill_deny,
    decide,
    is_review_gated,
    set_gated_prefixes,
)
from memoria.runtime.policy.engine import PolicyEngine
from memoria.runtime.policy.lanes import (
    LANE_OVERRIDE_RELDIR,
    load_gated_prefixes,
    load_lane,
    parse_lane,
    yaml,
)
from memoria.runtime.policy.model import Decision, LanePolicy
from memoria.runtime.policy.paths import (
    ACTIONS,
    MUTATING_ACTIONS,
    REVIEW_GATED_PREFIXES,
    glob_to_regex,
    normalize_path,
    path_matches,
    within_scope,
)

__all__ = [
    "ACTIONS",
    "AUDIT_RELPATH",
    "AUDIT_SCHEMA_VERSION",
    "AUTO_FIX_ALLOWED_CLASSES",
    "AUTO_FIX_DENY_CLASSES",
    "AUTO_FIX_DRY_RUN_CLASSES",
    "EMPTY_SHA256",
    "LANE_OVERRIDE_RELDIR",
    "MUTATING_ACTIONS",
    "REVIEW_GATED_PREFIXES",
    "REVIEW_MODE",
    "Decision",
    "LanePolicy",
    "PolicyEngine",
    "append_audit",
    "build_server",
    "compose_skill_deny",
    "decide",
    "glob_to_regex",
    "is_review_gated",
    "load_gated_prefixes",
    "load_lane",
    "normalize_path",
    "parse_lane",
    "path_matches",
    "resolve_vault",
    "set_gated_prefixes",
    "sha256_file",
    "within_scope",
    "yaml",
]


def main() -> None:
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument("--vault", help="vault root (or set MEMORIA_VAULT_PATH)")
    parser.add_argument(
        "--decide",
        metavar="JSON",
        help='one-shot decision request, e.g. \'{"profile":"memoria-librarian",'
        '"action":"write","path":"notes/claims/x.md","task_id":"T1"}\'',
    )
    args = parser.parse_args()

    vault = resolve_vault(args.vault)
    set_gated_prefixes(load_gated_prefixes(vault))

    if args.decide:
        req = json.loads(args.decide)
        engine = PolicyEngine(vault)
        print(
            json.dumps(
                engine.check(
                    req["profile"],
                    req["action"],
                    req["path"],
                    req.get("task_id", ""),
                    req.get("reason", ""),
                    req.get("flags"),
                ),
                indent=2,
            )
        )
        sys.exit(0)

    build_server(vault).run()


if __name__ == "__main__":
    main()
