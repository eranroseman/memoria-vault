#!/usr/bin/env python3
"""Entrypoint for the Memoria policy MCP.

The behavior-preserving policy implementation is split under
``memoria_vault.runtime.policy``:

- ``model``: LanePolicy and Decision data models
- ``paths``: path normalization and glob semantics
- ``lanes``: lane YAML loading and gated-prefix discovery
- ``decision``: pure allow/deny/dry_run decisions
- ``audit``: SHA-256 and append-only audit helpers
- ``engine``: stateful lane cache, hash, audit, loudness, and skill narrowing

This file remains the installed/deployed CLI path. Import policy internals from
``memoria_vault.runtime.policy`` instead of this script.
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

from memoria_vault.runtime.policy.decision import set_gated_prefixes
from memoria_vault.runtime.policy.engine import PolicyEngine
from memoria_vault.runtime.policy.lanes import load_gated_prefixes


def main() -> None:
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument("--vault", help="vault root (or set MEMORIA_VAULT_PATH)")
    parser.add_argument(
        "--decide",
        metavar="JSON",
        help='one-shot decision request, e.g. \'{"profile":"memoria-librarian",'
        '"action":"write","path":"knowledge/notes/x.md","task_id":"T1"}\'',
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
