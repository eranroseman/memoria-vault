#!/usr/bin/env python3
"""Attention-card lifecycle: journal the closed cards the review gate honors.

`inbox/` is the hot attention surface and it sits outside every bundle root, so no
trusted-writer path observes an edit to it. An edit that flips `attention_status`
to a closed value is therefore a disposition nothing records: `open_blockers` stops
seeing the card and the review gate opens silently. These helpers record such a
flip as a journaled disposition before the gate honors it.

**The row names no author.** Memoria cannot observe who edited a file outside the
trusted writer: `platform.node()` is identical for the PI's hand and for a machine,
and `inbox/**` is the one write target the reference actor policy grants a
non-PI actor (`docs/reference/control-and-policy/policy-mcp.md`), so a perimeter
write reaches exactly the cards this scan reads. The disposition is therefore
journaled `via: unattributed-edit` under `actor: integrity` -- the actor Memoria
already uses for the runtime recording vault state it did not cause
(`observe-pi-edits`, `trace-integrity-scan`, the read barrier). This is
deliberately weaker than `observe_pi_edit`, which may name the PI because
`_bundle_for_target` confines it to bundle roots that same policy denies every
machine. The journal forbids UPDATE and DELETE, so a permanent row naming the
wrong author would be worse than one naming none; authorship can be added when the
product grows a way to observe it (see `OperationContext.machine_authored`, which
already splits authority from authorship for envelope-carrying writes).

Nothing read from a card's body reaches the journal. `target_id` is the card's own
vault-relative path -- file-derived, but bounded by NAME_MAX, JSON-escaped, and the
join key the row exists to carry. Every other field is a code constant, a
timestamp, or a value validated against a fixed vocabulary.
"""

from __future__ import annotations

import platform
from collections.abc import Mapping
from pathlib import Path
from typing import Any

from memoria_vault.runtime import state
from memoria_vault.runtime.time import now_iso
from memoria_vault.runtime.trusted_writer import EVENT_RESOLVED, append_explicit_event_batch
from memoria_vault.runtime.vaultio import read_frontmatter

ATTENTION_PROJECTION = "attention"
ATTENTION_SOURCE = "attention"
RESOLUTION_RESOLVED = "resolved"
UNATTRIBUTED_EDIT = "unattributed-edit"
# The runtime observed this; it did not cause it and cannot say who did.
JOURNAL_ACTOR = "integrity"
JOURNAL_REASON = "journaled an unattributed attention_status close"
# A closed status names its own outcome; `resolve_attention` writes the two in step.
CLOSED_STATUS_OUTCOMES = {"resolved": "apply", "deferred": "defer"}
RESOLVED_OUTCOMES = frozenset({"apply", "reject"})
ROUTING_CLASSES = frozenset({"act", "ask", "log"})
DEFAULT_ROUTING_CLASS = "ask"


def _machine(machine: str) -> str:
    return machine or platform.node() or "local"


def _journaled_disposition_targets(vault: Path) -> set[str]:
    """Return the cards whose closing disposition the journal already holds.

    An acknowledgement is an `EVENT_RESOLVED` row too, but it closes nothing and
    leaves the card open -- a later edit closing it is still unrecorded. Note
    curation, moves, and rollbacks emit that event type with their own `resolution`
    vocabulary. Only an attention row that resolved the card already speaks for it.
    """
    return {
        str(event.get("target_id") or "")
        for event in state.read_event_log(vault, event_types=(EVENT_RESOLVED,))
        if event.get("source") == ATTENTION_SOURCE
        and event.get("resolution") == RESOLUTION_RESOLVED
    }


def _closed_outcome(status: str, frontmatter: Mapping[str, Any]) -> str:
    """Return the card's outcome, kept consistent with the status written on it.

    `deferred` means `defer` and nothing else; a `resolved` card may still
    distinguish `apply` from `reject`. Any other written value is card text, not a
    decision this journal can carry, so the status speaks instead.
    """
    default = CLOSED_STATUS_OUTCOMES[status]
    if status != RESOLUTION_RESOLVED:
        return default
    written = str(frontmatter.get("resolution_outcome") or "").strip().lower()
    return written if written in RESOLVED_OUTCOMES else default


def _closed_routing_class(frontmatter: Mapping[str, Any]) -> str:
    written = str(frontmatter.get("routing_class") or "").strip().lower()
    return written if written in ROUTING_CLASSES else DEFAULT_ROUTING_CLASS


def _closed_cards(inbox: Path, vault: Path) -> list[tuple[str, str, Mapping[str, Any]]]:
    """Return `(relpath, status, frontmatter)` for every closed attention card."""
    closed: list[tuple[str, str, Mapping[str, Any]]] = []
    for path in sorted(inbox.glob("*.md")):
        frontmatter = read_frontmatter(path)
        if str(frontmatter.get("projection") or "").lower() != ATTENTION_PROJECTION:
            continue
        status = str(frontmatter.get("attention_status") or "").strip().lower()
        if status not in CLOSED_STATUS_OUTCOMES:
            continue
        closed.append((path.relative_to(vault).as_posix(), status, frontmatter))
    return closed


def _disposition_row(
    rel: str, status: str, frontmatter: Mapping[str, Any], decided_at: str
) -> dict[str, Any]:
    outcome = _closed_outcome(status, frontmatter)
    return {
        "event": EVENT_RESOLVED,
        "resolution": RESOLUTION_RESOLVED,
        "outcome": outcome,
        "resolution_outcome": outcome,
        "routing_class": _closed_routing_class(frontmatter),
        "decided_at": decided_at,
        "target_id": rel,
        "reason": JOURNAL_REASON,
        "source": ATTENTION_SOURCE,
        "via": UNATTRIBUTED_EDIT,
    }


def journal_unattributed_dispositions(vault: Path, *, machine: str = "") -> list[dict[str, Any]]:
    """Journal every closed `attention_status` the journal does not already hold."""
    vault = Path(vault)
    inbox = vault / "inbox"
    if not inbox.is_dir():
        return []
    closed = _closed_cards(inbox, vault)
    if not closed:  # no closed card, so nothing to record and no reason to lock
        return []
    # One critical section over the read that decides what is missing and the write
    # that fills it. Reading outside it let concurrent sessions -- AGENTS.md
    # documents several per checkout, and the call site is a per-write hook -- each
    # see an empty journal and append the same permanent row.
    with state.workspace_lock(vault):
        journaled = _journaled_disposition_targets(vault)
        decided_at = now_iso()
        rows = [
            _disposition_row(rel, status, frontmatter, decided_at)
            for rel, status, frontmatter in closed
            if rel not in journaled
        ]
        if not rows:
            return []
        # One batch is one durable write cycle, whatever N is.
        return append_explicit_event_batch(
            vault, rows, actor=JOURNAL_ACTOR, machine=_machine(machine)
        )
