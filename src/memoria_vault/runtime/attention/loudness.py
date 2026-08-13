"""Graded loudness helpers.

`loudness` is pull-only Inbox card metadata. Open block cards pause delegation
and review-gated promotion until the PI acknowledges them by resolving the card.
"""

from __future__ import annotations

from collections.abc import Mapping
from pathlib import Path
from typing import Any

from memoria_vault.runtime.vaultio import read_frontmatter

BLOCK_LOUDNESS = "block"
ATTENTION_PROJECTION = "attention"
OPEN_ATTENTION_STATUS = "open"
# `grounding.resolve_attention` validates against exactly this roster and raises on
# anything else, so it is the vocabulary a card's `routing_class` may hold.
ROUTING_CLASSES = frozenset({"act", "ask", "log"})
DEFAULT_ROUTING_CLASS = "ask"


def attention_status(frontmatter: Mapping[str, Any]) -> str:
    """The one reader of a card's `attention_status`: stripped and case-folded.

    Named rather than repeated because, unlike `projection`, this value does not stay
    in the function that reads it -- `engine.api._attention_card` carries it into the
    card payload as `status`, and three callers (`read_attention`'s worklist and
    `--status` filters, `read_attention_view`, and the CLI's workspace-export
    `attention_open` count) compare it to `"open"` a layer away. A fold at each of
    those comparisons cannot work: by then the raw spelling is already in the payload.
    So the fold belongs at every *frontmatter* read, which makes the payload's `status`
    canonical and every later comparison correct by construction.

    It lives here because this is the only attention module that is a leaf -- stdlib
    plus `vaultio` -- so the gate, the journal, the compactor, the inbox writer, and
    the read API can all import it at module scope without a cycle.

    `inbox/**` is the one write target the reference actor policy grants a non-PI
    actor, so `attention_status: " Open "` -- an ordinary YAML quoting accident, not an
    exotic input -- is reachable through the documented perimeter. Unfolded, that card
    gates writes here in `is_open_blocker` while staying invisible to `memoria
    attention view` and `attention list --status open`: the PI is blocked by a card the
    CLI will not show them.
    """
    return str(frontmatter.get("attention_status") or "").strip().lower()


def routing_class(frontmatter: Mapping[str, Any]) -> str:
    """The one reader of a card's `routing_class`: folded to the roster, else `ask`.

    Third field to diverge this way, after `projection` (#1617) and `attention_status`
    (#1633), and it diverged for their reason: `lifecycle` folded its own read while
    `engine.api._attention_card` carried the raw string into the card payload, where
    no later reader can tell `Act` from `act` because the spelling is already gone.

    Filed as display-only. It was not. The payload field is not only rendered -- it is
    the `routing_class` `engine.api.resolve_attention` puts in the `resolve-attention`
    operation payload, which `worker` hands to `grounding.resolve_attention`, which
    validates against `ROUTING_CLASSES` and raises. So `routing_class: Act` on an open
    card made `memoria attention resolve` return `ok: false` and leave the card open:
    if it also carried `loudness: block`, it gated delegation and review-gated
    promotion with no way to clear it through the CLI, while `lifecycle` folded the
    same card to `act` and journaled a disposition for it. That is #1633's harm
    exactly, one hop further from the frontmatter.

    So the fold belongs at every *frontmatter* read, which makes the payload's
    `routing_class` canonical and both the operation payload and the rendered field
    correct by construction. Narrowed to exactly the vocabulary
    `grounding.resolve_attention` accepts, never to a new term.

    `inbox/**` is the one write target the reference actor policy grants a non-PI
    actor, so `routing_class: " ask "` -- an ordinary YAML quoting accident -- is
    reachable through the documented perimeter.
    """
    written = str(frontmatter.get("routing_class") or "").strip().lower()
    return written if written in ROUTING_CLASSES else DEFAULT_ROUTING_CLASS


def is_open_blocker(frontmatter: dict[str, Any]) -> bool:
    """Read the three gating fields the way `lifecycle` reads them: `.strip().lower()`.

    One unstripped read is all it took for the gate and the journal to disagree about
    what an attention card is. `inbox/**` is the one write target the reference actor
    policy grants a non-PI actor, so `projection: " attention "` -- an ordinary YAML
    quoting accident, not an exotic input -- is reachable through the documented
    perimeter, and an unstripped read makes it a `block` card that gates nothing.
    """
    return (
        str(frontmatter.get("projection") or "").strip().lower() == ATTENTION_PROJECTION
        and attention_status(frontmatter) == OPEN_ATTENTION_STATUS
        and str(frontmatter.get("loudness") or "").strip().lower() == BLOCK_LOUDNESS
    )


def open_blockers(vault: Path) -> list[dict[str, str]]:
    blockers: list[dict[str, str]] = []
    for path in sorted((vault / "inbox").glob("*.md")):
        fm = read_frontmatter(path)
        if is_open_blocker(fm):
            blockers.append(
                {
                    "path": str(path.relative_to(vault)).replace("\\", "/"),
                    "title": str(fm.get("title") or path.stem),
                    "type": str(fm.get("attention_kind") or fm.get("type") or "card"),
                }
            )
    return blockers


def blocker_message(blockers: list[dict[str, str]]) -> str:
    if not blockers:
        return ""
    names = ", ".join(f"{b['path']} ({b['title']})" for b in blockers[:3])
    more = "" if len(blockers) <= 3 else f"; +{len(blockers) - 3} more"
    return f"open block-loudness card(s) require PI acknowledgement before dispatch/promotion: {names}{more}"
