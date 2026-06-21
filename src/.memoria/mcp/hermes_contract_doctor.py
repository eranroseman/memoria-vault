"""Hermes contract doctor — verify the gate's assumptions against the INSTALLED Hermes.

The policy gate (`policy_hook.DENY_DIRECT_TOOLS`) is a hand-maintained denylist that
*claims* to cover Hermes's direct filesystem/shell toolsets. Hermes ships new tools
over time (the `terminal` toolset gained `process`), so the list silently drifts and
the gate's "fail closed on direct-capability tools" promise rots. This doctor pins the
contract: it reads the toolset registry from the **installed** Hermes and fails when a
file/terminal/code_execution tool is not hard-denied.

It is the generalisation of the ADR-106 cost doctor and the executable form of the
AGENTS.md rule "build on the installed version; upgrade by verifying." Run it in the
release runbook and after every Hermes upgrade.

Usage:
    python src/.memoria/mcp/hermes_contract_doctor.py [--hermes <project_dir>] [--json]

Exit 0 = contract holds (or Hermes not found → SKIPPED). Exit 1 = drift (missing
direct-capability denial). Warnings (dead names, the #22 egress surface) never fail.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

# Make policy_hook importable when run as a standalone script: it pulls in `_shared`
# (this dir) and the `memoria` package (repo root). pytest provides these via the
# pyproject `pythonpath`; a bare `python …/hermes_contract_doctor.py` does not.
_HERE = Path(__file__).resolve().parent
for _p in (_HERE, _HERE.parents[0], _HERE.parents[2]):  # mcp · src/.memoria · repo root
    if str(_p) not in sys.path:
        sys.path.insert(0, str(_p))

# DENY_DIRECT_TOOLS is the single source of truth; import it, don't re-list it.
import policy_hook

# Hermes toolsets whose every tool MUST be hard-denied (the gate's stated contract:
# "direct filesystem/shell access"). A tool here that is not in DENY_DIRECT_TOOLS is
# a hard error — that is the `process`-class drift.
DIRECT_CAPABILITY_FAMILIES = ("file", "terminal", "code_execution")

# Egress / side-effect families. The gate does NOT hard-deny these; the sandbox
# relies on `agent.disabled_toolsets` (schema-hiding on v0.14.0). Reported as the
# known allow-by-default surface, not a failure — tracked for the default-deny work.
EGRESS_FAMILIES = (
    "web",
    "browser",
    "messaging",
    "x_search",
    "computer_use",
    "delegation",
    "image_gen",
    "vision",
    "video",
    "video_gen",
    "tts",
    "homeassistant",
    "spotify",
    "cronjob",
)


def _default_hermes_project() -> Path:
    home = os.environ.get("HERMES_HOME") or str(Path.home() / ".hermes")
    return Path(home).expanduser() / "hermes-agent"


def _load_toolsets(hermes_project: Path) -> dict | None:
    """Import TOOLSETS from the installed Hermes. None if not importable."""
    ts_file = hermes_project / "toolsets.py"
    if not ts_file.exists():
        return None
    sys.path.insert(0, str(hermes_project))
    try:
        import toolsets  # type: ignore

        return dict(getattr(toolsets, "TOOLSETS", {})) or None
    except Exception:  # noqa: BLE001 — any import failure → degrade to SKIPPED, never crash the doctor
        return None
    finally:
        try:
            sys.path.remove(str(hermes_project))
        except ValueError:
            pass


def _tools_of(toolsets: dict, family: str) -> set[str]:
    entry = toolsets.get(family) or {}
    return {t for t in (entry.get("tools") or []) if isinstance(t, str)}


def run_contract_doctor(hermes_project: Path | str | None = None) -> dict:
    project = Path(hermes_project) if hermes_project else _default_hermes_project()
    toolsets = _load_toolsets(project)
    if toolsets is None:
        return {
            "ok": True,
            "checked": False,
            "skipped": f"Hermes toolsets not importable at {project}",
            "hermes_project": str(project),
        }

    denied = set(policy_hook.DENY_DIRECT_TOOLS)

    # ERROR: every direct-capability tool the installed Hermes ships must be denied.
    direct_tools: set[str] = set()
    for fam in DIRECT_CAPABILITY_FAMILIES:
        direct_tools |= _tools_of(toolsets, fam)
    missing = sorted(direct_tools - denied)
    errors = [
        f"direct-capability tool {t!r} (in a {','.join(DIRECT_CAPABILITY_FAMILIES)} "
        f"toolset) is NOT in DENY_DIRECT_TOOLS — gate allows it"
        for t in missing
    ]

    # WARN: denylist entries that are not a real tool in ANY installed toolset.
    all_real_tools: set[str] = set()
    for entry in toolsets.values():
        all_real_tools |= {t for t in (entry.get("tools") or []) if isinstance(t, str)}
    dead = sorted(denied - all_real_tools)

    # WARN: the egress/side-effect surface the gate does not deny (#22).
    egress_allowed: dict[str, list[str]] = {}
    for fam in EGRESS_FAMILIES:
        allowed = sorted(_tools_of(toolsets, fam) - denied)
        if allowed:
            egress_allowed[fam] = allowed

    warnings = []
    if dead:
        warnings.append(f"dead denylist names (not real Hermes tools): {dead}")
    if egress_allowed:
        n = sum(len(v) for v in egress_allowed.values())
        warnings.append(
            f"{n} egress/side-effect tools are allow-by-default (rely on "
            f"disabled_toolsets schema-hiding; see #22): {egress_allowed}"
        )

    return {
        "ok": not errors,
        "checked": True,
        "hermes_project": str(project),
        "direct_capability_tools": sorted(direct_tools),
        "errors": errors,
        "warnings": warnings,
    }


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument(
        "--hermes", default=None, help="Hermes project dir (default: $HERMES_HOME/hermes-agent)"
    )
    ap.add_argument("--json", action="store_true", help="emit the full report as JSON")
    args = ap.parse_args(argv)

    report = run_contract_doctor(args.hermes)
    if args.json:
        print(json.dumps(report, indent=2))
    elif not report.get("checked"):
        print(f"hermes-contract-doctor: SKIPPED — {report.get('skipped')}")
    else:
        for w in report.get("warnings", []):
            print(f"hermes-contract-doctor: WARN: {w}")
        if report["ok"]:
            print(
                f"hermes-contract-doctor: OK — all {len(report['direct_capability_tools'])} "
                f"direct-capability tools are hard-denied"
            )
        else:
            for e in report["errors"]:
                print(f"hermes-contract-doctor: ERROR: {e}")
    return 0 if report["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
