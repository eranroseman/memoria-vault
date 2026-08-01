#!/usr/bin/env python3
"""Attention-card lifecycle: adopt hand-edited dispositions into the journal.

`inbox/` is the hot attention surface and it sits outside every bundle root, so no
trusted-writer path observes an edit to it. A hand edit (Vim, Obsidian) that flips
`attention_status` to a closed value is therefore a PI disposition nothing records:
`open_blockers` stops seeing the card and the review gate opens silently. These
helpers adopt such a flip as a journaled disposition (`via: manual-edit`) before
the gate honors it.

Attributing that to the PI is the same basis `observe_pi_edit` already uses -- a
change the trusted writer did not make is the PI's hand. It holds here because no
product writer ever leaves a closed `attention_status` unjournaled: every card
generator writes `open`, and `resolve_attention`, the one writer of a closed
status, appends its journal row before it touches the file.

Nothing read from a card reaches the journal. The event log forbids UPDATE and
DELETE, so a field carrying card text would be permanent and uncleanable; every
adopted field is a code constant, a timestamp, the card's own path, or a value
validated against a fixed vocabulary.
"""

from __future__ import annotations

import platform
from collections.abc import Mapping
from pathlib import Path
from typing import Any

from memoria_vault.runtime import state
from memoria_vault.runtime.time import now_iso
from memoria_vault.runtime.trusted_writer import EVENT_RESOLVED, append_explicit_journal_event
from memoria_vault.runtime.vaultio import read_frontmatter

ATTENTION_PROJECTION = "attention"
ATTENTION_SOURCE = "attention"
RESOLUTION_RESOLVED = "resolved"
MANUAL_EDIT = "manual-edit"
ADOPTION_REASON = "adopted hand-edited attention_status"
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
    leaves the card open -- a later hand edit closing it is still unrecorded. Note
    curation, moves, and rollbacks emit that event type with their own `resolution`
    vocabulary. Only an attention row that resolved the card already speaks for it.
    """
    return {
        str(event.get("target_id") or "")
        for event in state.read_event_log(vault, event_types=(EVENT_RESOLVED,))
        if event.get("source") == ATTENTION_SOURCE
        and event.get("resolution") == RESOLUTION_RESOLVED
    }


def _adopted_outcome(status: str, frontmatter: Mapping[str, Any]) -> str:
    """Return the PI's outcome, kept consistent with the status they wrote.

    `deferred` means `defer` and nothing else; a `resolved` card may still
    distinguish `apply` from `reject`. Any other hand-written value is card text,
    not a decision this journal can carry, so the status speaks instead.
    """
    default = CLOSED_STATUS_OUTCOMES[status]
    if status != RESOLUTION_RESOLVED:
        return default
    written = str(frontmatter.get("resolution_outcome") or "").strip().lower()
    return written if written in RESOLVED_OUTCOMES else default


def _adopted_routing_class(frontmatter: Mapping[str, Any]) -> str:
    written = str(frontmatter.get("routing_class") or "").strip().lower()
    return written if written in ROUTING_CLASSES else DEFAULT_ROUTING_CLASS


def adopt_manual_dispositions(vault: Path, *, machine: str = "") -> list[dict[str, Any]]:
    """Journal hand-edited `attention_status` flips as `via: manual-edit` dispositions."""
    vault = Path(vault)
    inbox = vault / "inbox"
    if not inbox.is_dir():
        return []
    journaled: set[str] | None = None  # lazy: the journal is read only for a closed card
    adopted: list[dict[str, Any]] = []
    for path in sorted(inbox.glob("*.md")):
        frontmatter = read_frontmatter(path)
        if str(frontmatter.get("projection") or "").lower() != ATTENTION_PROJECTION:
            continue
        status = str(frontmatter.get("attention_status") or "").strip().lower()
        if status not in CLOSED_STATUS_OUTCOMES:
            continue
        rel = path.relative_to(vault).as_posix()
        if journaled is None:
            journaled = _journaled_disposition_targets(vault)
        if rel in journaled:
            continue
        outcome = _adopted_outcome(status, frontmatter)
        adopted.append(
            append_explicit_journal_event(
                vault,
                {
                    "event": EVENT_RESOLVED,
                    "resolution": RESOLUTION_RESOLVED,
                    "outcome": outcome,
                    "resolution_outcome": outcome,
                    "routing_class": _adopted_routing_class(frontmatter),
                    "decided_at": now_iso(),
                    "target_id": rel,
                    "reason": ADOPTION_REASON,
                    "source": ATTENTION_SOURCE,
                    "via": MANUAL_EDIT,
                },
                actor="pi",
                machine=_machine(machine),
            )
        )
        journaled.add(rel)
    return adopted
