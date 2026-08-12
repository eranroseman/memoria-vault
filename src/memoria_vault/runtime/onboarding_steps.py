"""Onboarding-step telemetry (O1 spec §5): five step events, emitted as observers, never gates.

Each row's own ``ts`` is the timestamp; every delta (the <=30-min bar) is
computed at read time from the first row per step. No duration field, no
cross-process t0 state.
"""

from __future__ import annotations

from collections.abc import Callable
from pathlib import Path, PurePosixPath
from typing import Any

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


_ANSWER_WORK_ROOTS = frozenset({"digests", "fulltexts", "graph-neighborhoods"})


def answer_work_ids(answer: dict[str, Any]) -> frozenset[str]:
    """Work ids an answer's sources resolve to, via the generated work-document path shapes.

    `_answer_from_hits` sources carry no ``work_id`` field (search_index.py), so the
    work id is the stem of a two-segment path under one of the generated work-document
    roots. Anything else in ``sources`` — notes, hubs, project pages — is not a work.
    """
    ids: set[str] = set()
    sources = answer.get("sources")
    for source in sources if isinstance(sources, list) else []:
        if not isinstance(source, dict):
            continue
        parts = PurePosixPath(str(source.get("path") or "")).parts
        if len(parts) == 2 and parts[0] in _ANSWER_WORK_ROOTS and parts[1].endswith(".md"):
            ids.add(parts[1].removesuffix(".md"))
    return frozenset(ids)


def seed_manifest_work_ids(
    manifest_loader: Callable[[], list[dict[str, Any]]] | None = None,
) -> frozenset[str]:
    """Manifest work ids; empty when no seed manifest exists (then nothing is seed-grounded)."""
    if manifest_loader is None:
        try:
            from memoria_vault.product.seed_corpus import load_seed_manifest
        except ImportError:
            return frozenset()
        loader = load_seed_manifest
    else:
        loader = manifest_loader
    try:
        rows = loader()
    except Exception:  # noqa: BLE001 -- an unreadable manifest must not gate the answer.
        return frozenset()
    return frozenset(
        work_id
        for row in rows
        if isinstance(row, dict) and (work_id := str(row.get("id") or "").strip())
    )


def emit_first_answer_if_seed_grounded(
    vault: Path,
    answer: dict[str, Any],
    *,
    manifest_loader: Callable[[], list[dict[str, Any]]] | None = None,
) -> str | None:
    """O1 spec §5 first-answer rule: seed-grounded sources AND no prior first-answer row."""
    if not answer_work_ids(answer) & seed_manifest_work_ids(manifest_loader):
        return None
    return emit_onboarding_step_once(vault, "first-answer")
