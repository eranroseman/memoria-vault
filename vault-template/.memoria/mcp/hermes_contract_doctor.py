"""Hermes contract doctor — verify the gate's assumptions against the INSTALLED Hermes.

The policy gate (`policy_hook.DENY_DIRECT_TOOLS`) is a hand-maintained denylist that
*claims* to cover Hermes's direct filesystem/shell toolsets. Hermes ships new tools
over time (the `terminal` toolset gained `process`), so the list silently drifts and
the gate's "fail closed on direct-capability tools" promise rots. This doctor pins the
contract: it reads the toolset registry from the **installed** Hermes and fails when a
file/terminal/code_execution/history/egress tool is not hard-denied.

It is the generalisation of the ADR-106 cost doctor and the executable form of the
AGENTS.md rule "build on the installed version; upgrade by verifying." Run it in the
release runbook and after every Hermes upgrade.

Usage:
    python vault-template/.memoria/mcp/hermes_contract_doctor.py [--hermes <project_dir>] [--json]

Exit 0 = contract holds (or Hermes not found → SKIPPED). Exit 1 = drift (missing
direct-capability / egress denial, or stale deployed gate when --vault is given).
Warnings are limited to harmless dead denylist names.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

# Make policy_hook importable when run as a standalone script: it pulls in `_shared`
# (this dir) and the `memoria_vault` package (repo root/src). pytest provides these via the
# pyproject `pythonpath`; a bare `python …/hermes_contract_doctor.py` does not.
_HERE = Path(__file__).resolve().parent
for _p in (_HERE, _HERE.parents[0], _HERE.parents[2], _HERE.parents[2] / "src"):
    if str(_p) not in sys.path:
        sys.path.insert(0, str(_p))

# DENY_DIRECT_TOOLS is the single source of truth; import it, don't re-list it.
import policy_hook

COVERED_TOOL_FAMILIES = (
    "file",
    "terminal",
    "code_execution",
    "session_search",
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


def _deployment_errors(vault: Path | str | None) -> list[str]:
    if vault is None:
        return []
    deployed = Path(vault).expanduser() / ".memoria/mcp/policy_hook.py"
    source = _HERE / "policy_hook.py"
    if not deployed.is_file():
        return [f"deployed policy_hook.py missing at {deployed}"]
    if deployed.read_text(encoding="utf-8") != source.read_text(encoding="utf-8"):
        return [f"deployed policy_hook.py is stale: {deployed} differs from {source}"]
    return []


def run_contract_doctor(
    hermes_project: Path | str | None = None, vault: Path | str | None = None
) -> dict:
    project = Path(hermes_project) if hermes_project else _default_hermes_project()
    toolsets = _load_toolsets(project)
    deploy_errors = _deployment_errors(vault)
    if toolsets is None:
        return {
            "ok": not deploy_errors,
            "checked": False,
            "skipped": f"Hermes toolsets not importable at {project}",
            "hermes_project": str(project),
            "errors": deploy_errors,
        }

    denied = set(policy_hook.DENY_DIRECT_TOOLS)

    covered_tools: set[str] = set()
    for fam in COVERED_TOOL_FAMILIES:
        covered_tools |= _tools_of(toolsets, fam)
    missing = sorted(covered_tools - denied)
    errors = [
        f"covered tool {t!r} (in a {','.join(COVERED_TOOL_FAMILIES)} "
        f"toolset) is NOT in DENY_DIRECT_TOOLS — gate allows it"
        for t in missing
    ]
    errors.extend(deploy_errors)

    # WARN: denylist entries that are not a real tool in ANY installed toolset.
    all_real_tools: set[str] = set()
    for entry in toolsets.values():
        all_real_tools |= {t for t in (entry.get("tools") or []) if isinstance(t, str)}
    dead = sorted(denied - all_real_tools)

    warnings = []
    if dead:
        warnings.append(f"dead denylist names (not real Hermes tools): {dead}")

    return {
        "ok": not errors,
        "checked": True,
        "hermes_project": str(project),
        "covered_tools": sorted(covered_tools),
        "direct_capability_tools": sorted(covered_tools),
        "errors": errors,
        "warnings": warnings,
    }


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument(
        "--hermes", default=None, help="Hermes project dir (default: $HERMES_HOME/hermes-agent)"
    )
    ap.add_argument("--vault", default=None, help="optional deployed vault to freshness-check")
    ap.add_argument("--json", action="store_true", help="emit the full report as JSON")
    args = ap.parse_args(argv)

    report = run_contract_doctor(args.hermes, args.vault)
    if args.json:
        print(json.dumps(report, indent=2))
    elif not report.get("checked"):
        print(f"hermes-contract-doctor: SKIPPED — {report.get('skipped')}")
        for e in report.get("errors", []):
            print(f"hermes-contract-doctor: ERROR: {e}")
    else:
        for w in report.get("warnings", []):
            print(f"hermes-contract-doctor: WARN: {w}")
        if report["ok"]:
            print(
                f"hermes-contract-doctor: OK — all {len(report['covered_tools'])} "
                f"covered direct/egress tools are hard-denied"
            )
        else:
            for e in report["errors"]:
                print(f"hermes-contract-doctor: ERROR: {e}")
    return 0 if report["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
