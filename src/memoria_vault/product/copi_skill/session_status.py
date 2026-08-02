"""Memoria SessionStart hook: inject engine and credential truth.

Seeded into vaults as `.claude/hooks/session_status.py` by the bootstrap
verbs; the packaged source of truth lives in
`memoria_vault.product.copi_skill`. Stdlib only — this file must run on
machines where the Memoria engine is absent. Stdout becomes agent context;
the hook always exits 0 (status is injected, never blocking).
"""

from __future__ import annotations

import json
import shutil
import subprocess
import sys

METHOD_POINTER_LINE = (
    "Memoria: co-PI method at .claude/skills/memoria-copi/SKILL.md — read it "
    "before answering questions about vault content."
)
ENGINE_MISSING_LINE = (
    "Memoria: engine missing — the Memoria CLI was not found (tried: `memoria`). "
    "Install it: `pipx install memoria`. This vault remains fully readable and "
    "editable; agent writes stay blocked until the engine exists."
)
DOCTOR_UNAVAILABLE_LINE = (
    "Memoria: `memoria doctor` did not return usable status — run `memoria doctor` manually."
)
DEFAULT_ENHANCING_EFFECT = "degraded keyless mode"


def _credential_lines(credentials: object) -> list[str]:
    lines: list[str] = []
    if not isinstance(credentials, list):
        return lines
    for cred in credentials:
        if not isinstance(cred, dict) or cred.get("status") != "unset":
            continue
        name = str(cred.get("name") or "").strip()
        if not name:
            continue
        cred_class = cred.get("class")
        if cred_class == "required-for-operation":
            lines.append(
                f"Memoria: credential {name} is unset (required-for-operation) — "
                "live-model calls refuse before the network; "
                f"run `memoria secrets set {name}`."
            )
        elif cred_class == "enhancing":
            effect = (
                str(cred.get("effect_when_unset") or DEFAULT_ENHANCING_EFFECT).strip().rstrip(".")
            )
            lines.append(f"Memoria: credential {name} is unset (enhancing) — {effect}.")
    return lines


def _doctor_lines() -> list[str]:
    try:
        proc = subprocess.run(
            ["memoria", "doctor", "--json"],
            capture_output=True,
            text=True,
            timeout=30,
            check=False,
        )
        report = json.loads(proc.stdout or "")
    except (OSError, subprocess.SubprocessError, ValueError):
        return [DOCTOR_UNAVAILABLE_LINE]
    if not isinstance(report, dict):
        return [DOCTOR_UNAVAILABLE_LINE]
    return _credential_lines(report.get("credentials"))


def main() -> int:
    """Write the session-start context lines to stdout; never block a session."""
    if shutil.which("memoria") is None:
        lines = [ENGINE_MISSING_LINE]
    else:
        lines = _doctor_lines()
    lines.append(METHOD_POINTER_LINE)
    sys.stdout.buffer.write(("\n".join(lines) + "\n").encode("utf-8"))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
