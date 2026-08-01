#!/usr/bin/env python3
"""Attention-card lifecycle: journal the closed cards the review gate honors, compact them.

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

**Resolved cards are then compacted** into an append-only monthly digest under
`inbox/archive/` so the hot scan stays flat. The archive is untouched by
construction, not by filtering: the two code paths that read attention cards glob
`inbox/*.md` non-recursively (`loudness.open_blockers`, `engine.api._attention_cards`)
and never descend into `archive/`, and the work-prompt dedupe checks one direct path
in `inbox/`. Belt and braces for a reader that does descend -- the seeded
`inbox.base` view selects a folder -- the digest carries no YAML frontmatter, so no
`projection: attention` match is possible even for a recursive scan.

**Removing a card is itself journaled.** `inbox/` filenames are reused -- both
writers in `inbox.py` refuse an occupied name and take the freed one -- so "this
path was disposed of" stops being true the moment compaction deletes the card. Each
archived card therefore gets an `EVENT_ATTENTION_ARCHIVED` release row, and the
disposition set is folded from both event types in journal order rather than
filtered from one. Every code path that removes an `inbox/*.md` card owes a release
row; `compact_resolved_cards` is currently the only `.unlink()` in `src/` that
touches `inbox/`, and nothing enforces the rest.
"""

from __future__ import annotations

import datetime
import platform
import re
import subprocess
from collections.abc import Mapping
from pathlib import Path
from typing import Any

from memoria_vault.runtime import state
from memoria_vault.runtime.time import now_iso
from memoria_vault.runtime.trusted_writer import (
    EVENT_RESOLVED,
    append_explicit_event_batch,
    commit_explicit_writer_changes,
)
from memoria_vault.runtime.vaultio import (
    append_text_durable,
    read_frontmatter,
    safe_read,
    split_frontmatter,
)

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


def _held_disposition_targets(vault: Path) -> set[str]:
    """Return the paths whose closing disposition the journal holds *and has not released*.

    A path, not a card: `inbox/` filenames are reused. `inbox.py`'s dedupe slot and
    its collision loop both refuse an occupied name, so before compaction a resolved
    card sat on its path forever and this set only ever grew. Compaction deletes the
    card, so the same path can carry a second, different card -- and a set that only
    grew would suppress that card's disposition and hand the gate back the silent
    clear this module exists to remove.

    So it is an ordered fold, not a filter: a disposition claims the path, the
    archival release row hands it back. `read_event_log` orders by `event_id`, and
    the journal forbids UPDATE and DELETE, so the fold is deterministic and replays
    identically forever.

    An acknowledgement is an `EVENT_RESOLVED` row too, but it closes nothing and
    leaves the card open -- a later edit closing it is still unrecorded. Note
    curation, moves, and rollbacks emit that event type with their own `resolution`
    vocabulary, and `EVENT_ATTENTION_ARCHIVED` is this module's own, so the `source`
    guard is hoisted over both: only attention rows speak for an attention card.
    """
    held: set[str] = set()
    for event in state.read_event_log(
        vault, event_types=(EVENT_RESOLVED, EVENT_ATTENTION_ARCHIVED)
    ):
        if event.get("source") != ATTENTION_SOURCE:
            continue
        target = str(event.get("target_id") or "")
        if event.get("event") == EVENT_ATTENTION_ARCHIVED:
            held.discard(target)
        elif event.get("resolution") == RESOLUTION_RESOLVED:
            held.add(target)
    return held


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
        if str(frontmatter.get("projection") or "").strip().lower() != ATTENTION_PROJECTION:
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
    """Journal every closed `attention_status` the journal does not currently hold.

    "Currently", not "already": compaction can hand a path back, so a second card at
    a reused `inbox/` name gets its own row. See `_held_disposition_targets`.
    """
    vault = Path(vault)
    inbox = vault / "inbox"
    if not inbox.is_dir():
        return []
    if not _closed_cards(inbox, vault):  # nothing to record, so no reason to lock
        return []
    # One critical section over *both* reads that decide what is missing and the
    # write that fills it. Reading the journal outside it let concurrent sessions --
    # AGENTS.md documents several per checkout, and the call site is a per-write
    # hook -- each see an empty journal and append the same permanent row.
    #
    # The card read is inside for a reason that only exists once compaction can
    # delete a card: the held set is a fold now, so it shrinks. A card list read
    # before the lock and used inside it can name a path a rival journaled,
    # archived, and unlinked while this call waited -- and because the release row
    # un-held that path, the stale entry is no longer suppressed. It would append a
    # permanent disposition built from the deleted card's frontmatter and re-claim
    # the slot, so the live card that now sits there never gets one. That is the
    # exact defect the release row exists to fix, reintroduced through the back door.
    with state.workspace_lock(vault):
        closed = _closed_cards(inbox, vault)
        held = _held_disposition_targets(vault)
        decided_at = now_iso()
        rows = [
            _disposition_row(rel, status, frontmatter, decided_at)
            for rel, status, frontmatter in closed
            if rel not in held
        ]
        if not rows:
            return []
        # One batch is one durable write cycle, whatever N is.
        return append_explicit_event_batch(
            vault, rows, actor=JOURNAL_ACTOR, machine=_machine(machine)
        )


ARCHIVE_RELDIR = "inbox/archive"
COMPACT_COMMIT_MESSAGE = "compact resolved attention cards"
# The scan that runs compaction is already actor `integrity`; this is the runtime's
# own hygiene write, so it names itself rather than borrowing the card's author.
COMPACTION_ACTOR = "integrity"
# Subsystem-named and local to this module. `event_log.event_type` is bare TEXT with
# no CHECK and no registry (`runtime/schema.sql:30`), and the house precedent for a
# subsystem transition is an inline literal in the owning module (`move-reverted` at
# `runtime/knowledge.py:513`, `workspace-restored` at `runtime/backup.py:792`). Bare
# `archived` was rejected: it already names a note lifecycle (`integrity.py:1782`), a
# source standing (`:1800`), a worklist decision (`worklists.py:30`) and a steering
# flag. A journal event type can never be renamed once rows carry it.
EVENT_ATTENTION_ARCHIVED = "attention-card-archived"
ARCHIVE_REASON = "appended this attention card to the monthly archive digest"
# A match is sliced to its first seven characters, so the month key is always
# `\d{4}-\d{2}`: a card's own `resolved_at` picks which digest it lands in and can
# never name a path outside the archive.
_MONTH_RE = re.compile(r"^\d{4}-\d{2}")
_DIGEST_FIELDS = (
    "attention_kind",
    "attention_status",
    "loudness",
    "raised_by",
    "created",
    "resolved_at",
    "resolution_outcome",
    "target",
    "citekey",
    "fingerprint",
)


def _archive_month(frontmatter: Mapping[str, Any], today: datetime.date) -> str:
    """Return the digest month for a card: its own stamp, else the compaction's.

    Nothing writes `resolved_at` when a card is closed by hand, so the fallback is
    the ordinary case for exactly the cards this exists to sweep up.
    """
    resolved_at = str(frontmatter.get("resolved_at") or "")
    if _MONTH_RE.match(resolved_at):
        return resolved_at[:7]
    return today.strftime("%Y-%m")


def _digest_section(rel: str, frontmatter: Mapping[str, Any], body: str) -> str:
    title = str(frontmatter.get("title") or Path(rel).stem)
    meta = "\n".join(
        f"- {field}: {frontmatter[field]}" for field in _DIGEST_FIELDS if frontmatter.get(field)
    )
    return f"\n## {title} ({Path(rel).name})\n\n{meta}\n\n{body.strip()}\n"


def _resolved_cards(inbox: Path) -> list[tuple[Path, dict[str, Any], str]]:
    """Return `(path, frontmatter, body)` for every resolved attention card in `inbox/`.

    Non-recursive, like every other reader of this directory: `archive/` holds this
    function's own output. `safe_read` also means a card that disappeared between
    the probe and the lock parses as no card at all rather than raising.
    """
    cards: list[tuple[Path, dict[str, Any], str]] = []
    for path in sorted(inbox.glob("*.md")):
        frontmatter, body = split_frontmatter(safe_read(path))
        if str(frontmatter.get("projection") or "").strip().lower() != ATTENTION_PROJECTION:
            continue
        if str(frontmatter.get("attention_status") or "").strip().lower() != RESOLUTION_RESOLVED:
            continue
        cards.append((path, frontmatter, body))
    return cards


def _release_row(rel: str, digest_rel: str) -> dict[str, Any]:
    """Return the row that hands a card's `inbox/` path back to the next card.

    No `via`, `resolution`, or `outcome`: those fields name a decision and its
    maker, and this row records neither. `actor: integrity` is the whole truth,
    because unlike the disposition it sits beside, the runtime *is* the author of
    the removal. No `archived_at` either -- `_prepare_explicit_journal_event`
    already stamps `timestamp`, and a second time field in a log that forbids
    UPDATE and DELETE could never be corrected.

    `outputs` rather than a bespoke key so the digest travels the same scoping path
    as any other written output: `_journal_paths` sweeps it (`engine/api.py:940`)
    and `_journal_in_scope` requires *all* swept paths in scope (`:923`), so an
    `inbox/**` reader sees this row and a `notes/**` reader does not -- and
    `memoria journal --path inbox/alert-x.md` returns that path's whole life.
    """
    return {
        "event": EVENT_ATTENTION_ARCHIVED,
        "source": ATTENTION_SOURCE,
        "target_id": rel,
        "outputs": [digest_rel],
        "reason": ARCHIVE_REASON,
    }


def _tracked(vault: Path, rel: str) -> bool:
    proc = subprocess.run(
        ["git", "ls-files", "--error-unmatch", "--", rel],
        cwd=vault,
        check=False,
        capture_output=True,
    )
    return proc.returncode == 0


def _uncommittable(vault: Path) -> str:
    """Return why the trusted writer cannot commit here now, or `""` if it can.

    Checked before the first durable write, because a digest is durable only once
    committed. `.git` existing is neither necessary nor sufficient: a vault with no
    repo cannot reach compaction through `workspace scan` at all (the scan's own
    `git status` fails first), while the failures that *are* reachable -- a crashed
    git leaving `index.lock`, an unconfigured identity -- all pass an existence
    check and then blow up at the commit, with the tail already appended to an
    uncommitted digest and unlinked from `inbox/`. Racy by nature, so the commit
    still guards itself; this only stops the two states that are already true when
    compaction starts.
    """
    if not (vault / ".git").exists():
        return "it has no git repo"
    if (vault / ".git/index.lock").exists():
        return "another git process holds .git/index.lock"
    proc = subprocess.run(
        ["git", "var", "GIT_COMMITTER_IDENT"],
        cwd=vault,
        check=False,
        capture_output=True,
        text=True,
    )
    if proc.returncode:
        # `splitlines()[0]` on an empty stderr would raise IndexError, which is not
        # in the caller's catch and would take the watch loop down with it.
        detail = next(iter(proc.stderr.strip().splitlines()), "git var failed")
        return f"git has no committer identity: {detail}"
    return ""


def compact_resolved_cards(vault: Path, *, machine: str = "") -> dict[str, Any]:
    """Move resolved attention cards into the append-only monthly archive digest.

    Journals unattributed dispositions first, so no card leaves `inbox/` without a
    journaled disposition, and appends an `EVENT_ATTENTION_ARCHIVED` release row for
    each card before unlinking it, so no card leaves `inbox/` without the journal
    recording that it left and which digest now holds it. Each card file is then
    deleted in the same trusted-writer commit that records the digest append.
    Deferred and open cards stay put.

    The release row is what makes an `inbox/` path reusable safely. Without it the
    disposition set only grows, so the second card to occupy a freed name is read as
    already-disposed and is deleted with no record of its own -- silently, and
    whether the first card's row named the PI or named nobody.

    The deciding read and the writes are one critical section, for the reason the
    journaling half took one: `workspace scan` is a file-watch tick as well as a
    command the PI runs, so two of them overlap, and a card both read is appended to
    the digest twice and unlinked twice. The probe that decides whether to lock at
    all stays outside, so the ordinary scan -- nothing resolved -- neither contends
    on the lock nor needs a git repository.
    """
    vault = Path(vault)
    result: dict[str, Any] = {
        "adopted": journal_unattributed_dispositions(vault, machine=machine),
        "archived": [],
        "digests": [],
        "commit": "",
    }
    inbox = vault / "inbox"
    if not _resolved_cards(inbox):
        return result
    blocked = _uncommittable(vault)
    if blocked:
        raise RuntimeError(f"cannot archive resolved attention cards: {blocked}")
    archived: list[str] = []
    digests: list[str] = []
    tracked: list[str] = []
    pending: list[tuple[Path, str, str]] = []
    today = datetime.date.today()
    with state.workspace_lock(vault):
        for path, frontmatter, body in _resolved_cards(inbox):
            rel = path.relative_to(vault).as_posix()
            month = _archive_month(frontmatter, today)
            digest_rel = f"{ARCHIVE_RELDIR}/{month}.md"
            digest_path = vault / digest_rel
            if not digest_path.exists():
                append_text_durable(digest_path, f"# Inbox archive {month}\n", create_parent=True)
            append_text_durable(digest_path, _digest_section(rel, frontmatter, body))
            if _tracked(vault, rel):
                tracked.append(rel)  # an untracked deletion has nothing to stage
            pending.append((path, rel, digest_rel))
            if digest_rel not in digests:
                digests.append(digest_rel)
        if not pending:  # a rival compacted the tail between the probe and the lock
            return result
        # Release rows before the unlinks, never after. A crash between them costs
        # one redundant disposition row on the next scan, which inspection can see
        # and the journal can carry; the other order costs whichever card lands on
        # the freed path next its disposition, permanently and invisibly.
        append_explicit_event_batch(
            vault,
            [_release_row(rel, digest_rel) for _, rel, digest_rel in pending],
            actor=COMPACTION_ACTOR,
            machine=_machine(machine),
        )
        for path, rel, _digest_rel in pending:
            path.unlink()
            archived.append(rel)
        result["archived"] = archived
        result["digests"] = digests
        try:
            result["commit"] = commit_explicit_writer_changes(
                vault,
                COMPACT_COMMIT_MESSAGE,
                [*digests, *tracked],
                actor=COMPACTION_ACTOR,
                machine=_machine(machine),
            )
        except RuntimeError as exc:
            # The cards are already gone and the digest already holds them; the
            # caller's payload cannot report a return value it never receives, so
            # the loss goes in the message it does report.
            raise RuntimeError(
                f"{exc} -- {len(archived)} card(s) already archived into "
                f"{', '.join(digests)} and removed from inbox/; commit them by hand"
            ) from exc
    return result
