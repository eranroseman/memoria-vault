"""Onboarding-step telemetry (O1 spec §5): five step events, emitted as observers, never gates.

Each row's own ``ts`` is the timestamp; every delta (the <=30-min bar) is
computed at read time from the first row per step. No duration field, no
cross-process t0 state.
"""

from __future__ import annotations

from pathlib import Path

from memoria_vault.runtime import state

ONBOARDING_STEPS = frozenset(
    {"init-done", "onboard-done", "project-framed", "seed-installed", "first-answer"}
)

_STEP_QUERY = (
    "SELECT 1 FROM telemetry_events"
    " WHERE event_type = 'onboarding-step'"
    " AND json_extract(payload_json, '$.step') = ? LIMIT 1"
)


def _known(step: str) -> str:
    if step not in ONBOARDING_STEPS:
        raise ValueError(f"unknown onboarding step: {step}")
    return step


def emit_onboarding_step(vault: Path, step: str) -> str | None:
    """Record one onboarding-step event; return None instead of raising on any sink failure."""
    _known(step)
    try:
        from memoria_vault.runtime.telemetry import record_telemetry_event
    except ImportError:
        return None
    try:
        return record_telemetry_event(vault, "onboarding-step", {"step": step})
    except Exception:  # noqa: BLE001 -- telemetry is an observer, never a gate (O1 spec §5).
        return None


def has_onboarding_step(vault: Path, step: str) -> bool:
    """True when a prior row for ``step`` exists; False on any sink failure."""
    _known(step)
    try:
        with state.connect(vault) as conn:
            return conn.execute(_STEP_QUERY, (step,)).fetchone() is not None
    except Exception:  # noqa: BLE001 -- absent table reads as "no prior step".
        return False


def emit_onboarding_step_once(vault: Path, step: str) -> str | None:
    """Emit only when no prior row for ``step`` exists — deterministic deltas (O1 spec §5)."""
    if has_onboarding_step(vault, step):
        return None
    return emit_onboarding_step(vault, step)
