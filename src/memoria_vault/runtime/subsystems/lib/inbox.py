#!/usr/bin/env python3
"""Write Inbox attention projections.

Attention is generated visibility, not a durable Concept type. These helpers keep
the old filenames and bodies useful while writing projection frontmatter instead
of deleted `candidate`/`gap`/`flag`/`work-prompt` schemas.
"""

from __future__ import annotations

import datetime
import re
from pathlib import Path

from memoria_vault.runtime.subsystems.lib import loudness as loudness_routing
from memoria_vault.runtime.vaultio import frontmatter_doc

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
    """Write a candidate/gap card with the honesty body (D49). Returns the path."""
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
    return _write(vault, card_type, title, frontmatter_doc(frontmatter, body), loudness=loudness)


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
) -> Path:
    """Write a flag/alert card that leads with the finding (ADR-51)."""
    if card_type not in VERIFICATION_TYPES:
        raise ValueError(f"not a verification type: {card_type}")
    if agent_recommendation not in RECOMMENDATION:
        raise ValueError(f"agent_recommendation must be one of {RECOMMENDATION}")
    if loudness not in LOUDNESS:
        raise ValueError(f"loudness must be one of {LOUDNESS}")
    if card_type == "flag" and not (target or citekey):
        raise ValueError("a flag must point at a target or citekey")
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
    frontmatter.update({"raised_by": raised_by, "loudness": loudness, "created": today})
    body = f"# Finding\n\n{finding}\n"
    if evidence:
        body += f"\n# Evidence\n\n{evidence}\n"
    return _write(vault, card_type, title, frontmatter_doc(frontmatter, body), loudness=loudness)


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
    """Write a `work-prompt` card (ADR-51 honesty rules: action + what happened +
    where to look — never a verdict). A prompt must point somewhere: `target`
    (output path) and/or `request_id`. With `dedupe_slug` the filename
    is stable (`work-prompt-<slug>.md`) and an already-present card is left
    untouched — returns None instead of a path (idempotent emit)."""
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
        path.write_text(content, encoding="utf-8")
        loudness_routing.push_card(vault, path, {"title": title, "loudness": loudness})
        return path
    return _write(vault, "work-prompt", title, content, loudness=loudness)


def _write(vault: Path, card_type: str, title: str, content: str, loudness: str = "notice") -> Path:
    inbox = vault / "inbox"
    inbox.mkdir(parents=True, exist_ok=True)
    base = f"{card_type}-{_slug(title)}"
    path = inbox / f"{base}.md"
    n = 1
    while path.exists():
        n += 1
        path = inbox / f"{base}-{n}.md"
    path.write_text(content, encoding="utf-8")
    loudness_routing.push_card(
        vault, path, {"title": title, "loudness": loudness, "type": card_type}
    )
    return path


if __name__ == "__main__":
    print(__doc__)
