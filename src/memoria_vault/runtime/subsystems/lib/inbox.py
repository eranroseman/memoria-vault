#!/usr/bin/env python3
"""Write Inbox attention projections.

Attention is generated visibility, not a durable Concept type. These helpers keep
the old filenames and bodies useful while writing projection frontmatter instead
of deleted `candidate`/`gap`/`flag`/`work-prompt` schemas.
"""

from __future__ import annotations

import contextlib
import datetime
import re
from pathlib import Path
from typing import Any

from memoria_vault.runtime import state
from memoria_vault.runtime.vaultio import (
    frontmatter_doc,
    safe_read,
    split_frontmatter,
    write_frontmatter_doc,
    write_text_durable,
)

PROPOSAL_TYPES = {"candidate", "gap"}
VERIFICATION_TYPES = {"flag", "alert"}
CERTAINTY = ("confident", "likely", "unsure")
RECOMMENDATION = ("inconclusive", "issues-found", "clean")
LOUDNESS = ("quiet", "notice", "alert", "block")


def _slug(text: str) -> str:
    s = re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")
    return s[:60] or "card"


def write_proposal(
    vault: Path,
    card_type: str,
    title: str,
    action: str,
    argument_for: str,
    argument_against: str,
    what_tipped_it: str,
    certainty: str,
    raised_by: str,
    loudness: str = "notice",
    citekey: str = "",
    url: str = "",
) -> Path:
    """Write a candidate/gap card with the honesty body."""
    if card_type not in PROPOSAL_TYPES:
        raise ValueError(f"not a proposal type: {card_type}")
    if certainty not in CERTAINTY:
        raise ValueError(f"certainty must be one of {CERTAINTY}")
    if loudness not in LOUDNESS:
        raise ValueError(f"loudness must be one of {LOUDNESS}")
    today = datetime.date.today().isoformat()
    frontmatter = {
        "title": title,
        "projection": "attention",
        "attention_kind": card_type,
        "attention_status": "open",
        "action": action,
        "argument_for": argument_for,
        "argument_against": argument_against,
        "what_tipped_it": what_tipped_it,
        "certainty": certainty,
    }
    if citekey:
        frontmatter["citekey"] = citekey
    if url:
        frontmatter["url"] = url
    frontmatter.update({"raised_by": raised_by, "loudness": loudness, "created": today})
    body = (
        f"# Action\n\n{action}\n\n# For\n\n{argument_for}\n\n"
        f"# Against\n\n{argument_against}\n\n# What tipped it\n\n{what_tipped_it}\n"
    )
    return _write(vault, card_type, title, frontmatter_doc(frontmatter, body))


def write_finding(
    vault: Path,
    card_type: str,
    title: str,
    finding: str,
    raised_by: str,
    agent_recommendation: str = "issues-found",
    target: str = "",
    citekey: str = "",
    loudness: str = "alert",
    evidence: str = "",
    dedupe_slug: str = "",
    fingerprint: str = "",
) -> Path | None:
    """Write a flag/alert card that leads with the finding.

    With ``dedupe_slug`` the filename is stable and an already-present card is
    left untouched — returns None instead of a path.

    With ``fingerprint`` the card is deduped against the **open** cards only: a
    standing card for the same condition has its ``last_seen`` touched and None is
    returned, and a recurrence after the PI resolved that card (and compaction
    archived it) writes a fresh open one. That is the difference from
    ``dedupe_slug``, which suppresses for as long as the file is there whatever its
    status. The two are orthogonal and the fingerprint is checked first.
    """
    if card_type not in VERIFICATION_TYPES:
        raise ValueError(f"not a verification type: {card_type}")
    if agent_recommendation not in RECOMMENDATION:
        raise ValueError(f"agent_recommendation must be one of {RECOMMENDATION}")
    if loudness not in LOUDNESS:
        raise ValueError(f"loudness must be one of {LOUDNESS}")
    if card_type == "flag" and not (target or citekey):
        raise ValueError("a flag must point at a target or citekey")
    # Canonical from here on, so producers that disagree about padding still match.
    fingerprint = fingerprint.strip()
    today = datetime.date.today().isoformat()
    frontmatter = {
        "title": title,
        "projection": "attention",
        "attention_kind": card_type,
        "attention_status": "open",
        "finding": finding,
        "agent_recommendation": agent_recommendation,
    }
    if target:
        frontmatter["target"] = target
    if citekey:
        frontmatter["citekey"] = citekey
    if fingerprint:
        frontmatter["fingerprint"] = fingerprint
        frontmatter["last_seen"] = today
    frontmatter.update({"raised_by": raised_by, "loudness": loudness, "created": today})
    body = f"# Finding\n\n{finding}\n"
    if evidence:
        body += f"\n# Evidence\n\n{evidence}\n"
    content = frontmatter_doc(frontmatter, body)
    # The read that decides and the write it drives are one critical section, the
    # shape `lifecycle` settled on for the same directory. Two sweeps that overlap
    # would otherwise both read an inbox with no standing card and both write one --
    # the duplicate this parameter exists to stop. Worse, `_touch_last_seen` renames
    # a temp file into place, so a touch racing compaction's unlink would resurrect a
    # card the journal has already recorded as archived; compaction takes this same
    # lock, so it cannot. No probe outside the lock, unlike `lifecycle`: every
    # fingerprinted call intends to write or to touch, so there is no no-op case for
    # a probe to keep off it. Unfingerprinted callers are untouched.
    guard = state.workspace_lock(vault) if fingerprint else contextlib.nullcontext()
    with guard:
        if fingerprint:
            match = _open_fingerprint_match(vault, fingerprint)
            if match is not None:
                _touch_last_seen(*match)
                return None
        if dedupe_slug:
            inbox = vault / "inbox"
            inbox.mkdir(parents=True, exist_ok=True)
            path = inbox / f"{card_type}-{_slug(dedupe_slug)}.md"
            if path.exists():
                return None
            write_text_durable(path, content)
            return path
        return _write(vault, card_type, title, content)


def write_work_prompt(
    vault: Path,
    title: str,
    action: str,
    what_happened: str,
    raised_by: str,
    target: str = "",
    request_id: str = "",
    posture: str = "",
    loudness: str = "notice",
    dedupe_slug: str = "",
    prompt_kind: str = "",
) -> Path | None:
    """Write a `work-prompt` card.

    Honesty rules: action + what happened + where to look, never a verdict. A
    prompt must point somewhere: `target` (output path) and/or `request_id`.
    With `dedupe_slug` the filename is stable (`work-prompt-<slug>.md`) and an
    already-present card is left untouched — returns None instead of a path.
    """
    if loudness not in LOUDNESS:
        raise ValueError(f"loudness must be one of {LOUDNESS}")
    if not (target or request_id):
        raise ValueError("a work-prompt must point at a target or request_id")
    today = datetime.date.today().isoformat()
    frontmatter = {
        "title": title,
        "projection": "attention",
        "attention_kind": "work-prompt",
        "attention_status": "open",
        "action": action,
        "what_happened": what_happened,
    }
    if target:
        frontmatter["target"] = target
    if request_id:
        frontmatter["request_id"] = request_id
    if posture:
        frontmatter["posture"] = posture
    if prompt_kind:
        frontmatter["prompt_kind"] = prompt_kind
    frontmatter.update({"raised_by": raised_by, "loudness": loudness, "created": today})
    body = f"# Action\n\n{action}\n\n# What happened\n\n{what_happened}\n"
    where = " · ".join(filter(None, (target, request_id and f"request `{request_id}`")))
    if where:
        body += f"\n# Where to look\n\n{where}\n"
    content = frontmatter_doc(frontmatter, body)
    if dedupe_slug:
        inbox = vault / "inbox"
        inbox.mkdir(parents=True, exist_ok=True)
        path = inbox / f"work-prompt-{_slug(dedupe_slug)}.md"
        if path.exists():
            return None
        write_text_durable(path, content)
        return path
    return _write(vault, "work-prompt", title, content)


def _open_fingerprint_match(
    vault: Path, fingerprint: str
) -> tuple[Path, dict[str, Any], str] | None:
    """Return the standing open attention card carrying ``fingerprint``, else None.

    Non-recursive, like every other reader of this directory (cross-section contract
    12). `inbox/archive/` is where an archived card's `fingerprint` survives --
    `lifecycle._DIGEST_FIELDS` carries it into the digest -- so a recursive glob here
    would let an archived card suppress the re-raise this parameter exists to allow,
    permanently, since nothing removes what the digest holds.

    Read once and read the way `lifecycle` reads: `.strip().lower()` on the two
    vocabulary fields, because one unstripped read is all it took for journaling and
    compaction to disagree about what an attention card is. `fingerprint` is stripped
    and *not* folded -- it is an identity like the journal's `target_id`, not a term
    from a fixed vocabulary, and folding it would merge conditions whose producer
    distinguishes them. Returning the parsed card, rather than re-reading it at the
    touch, is `_resolved_cards`' discipline, and so is `safe_read`: an `inbox/` file
    that is gone or not text parses as no card rather than raising out of a sweep.
    """
    for path in sorted((vault / "inbox").glob("*.md")):
        frontmatter, body = split_frontmatter(safe_read(path))
        if str(frontmatter.get("projection") or "").strip().lower() != "attention":
            continue
        if str(frontmatter.get("attention_status") or "").strip().lower() != "open":
            continue
        if str(frontmatter.get("fingerprint") or "").strip() != fingerprint:
            continue
        return path, frontmatter, body
    return None


def _touch_last_seen(path: Path, frontmatter: dict[str, Any], body: str) -> None:
    """Record that the condition was observed again, and change no other field.

    `created` stays put -- it is the standing card's birthday, and the age it measures
    is the PI's reason to act -- and so does everything the PI added by hand. Chiefly
    `loudness`: `is_open_blocker` reads it to hold delegation and review-gated
    promotion, so a touch that rebuilt the card from the new observation would reset a
    hand-escalated `block` to `alert` and open the gate on a schedule.

    It does reformat. This is `split_frontmatter` -> mutate -> `write_frontmatter_doc`,
    the same round trip `integrity.resolve_attention` performs, so the first touch
    drops YAML comments, normalizes quoting and reflows indentation. The delta from
    house behaviour is that this one happens unbidden, on the surface the PI is
    invited to edit by hand.
    """
    frontmatter["last_seen"] = datetime.date.today().isoformat()
    write_frontmatter_doc(path, frontmatter, body)


def _write(vault: Path, card_type: str, title: str, content: str) -> Path:
    inbox = vault / "inbox"
    inbox.mkdir(parents=True, exist_ok=True)
    base = f"{card_type}-{_slug(title)}"
    path = inbox / f"{base}.md"
    n = 1
    while path.exists():
        n += 1
        path = inbox / f"{base}-{n}.md"
    write_text_durable(path, content)
    return path


if __name__ == "__main__":
    print(__doc__)
