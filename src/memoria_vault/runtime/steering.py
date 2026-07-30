"""Derived steering: the effective token set discovery ranking reads.

Effective steering is derived from the vault substrate -- active projects
(title + thesis + tags), hubs (title + tag + tags), and open question notes
(title) -- plus the thin ``steering.md`` override: ``## Watch for`` bullets
boost, ``## Muted`` bullets suppress. Suppression is token-set subtraction:
bullets run through :func:`relevance_tokens`, so a multi-word entry mutes
each of its words. Archived artifacts never contribute, so steering needs
no separate aging mechanism.
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any

from memoria_vault.runtime.vaultio import iter_markdown, read_frontmatter, split_frontmatter

# Flat expansion of knowledge.py's retired _DISCOVERY_RELEVANCE_STOPWORDS
# (its 11-word function-word base stays in knowledge.py as
# _TAG_CANDIDATE_STOPWORDS for the tag-candidate sweep).
RELEVANCE_STOPWORDS = frozenset(
    {
        "about",
        "also",
        "and",
        "are",
        "but",
        "for",
        "from",
        "into",
        "the",
        "this",
        "with",
        "candidate",
        "current",
        "paper",
        "papers",
        "priority",
        "question",
        "questions",
        "research",
        "source",
        "sources",
        "steering",
        "system",
        "work",
        "works",
    }
)

_HEADING = re.compile(r"^(#{1,6})\s+(.*?)\s*$")
_BULLET = re.compile(r"^\s*[-*]\s+(.+?)\s*$")


def relevance_tokens(*values: object) -> set[str]:
    """Tokenize values exactly the way discovery relevance always has."""
    text = " ".join(str(value) for value in values if value)
    return {
        token
        for token in re.findall(r"[a-z0-9]{3,}", text.casefold())
        if token not in RELEVANCE_STOPWORDS and not token.isdigit()
    }


def steering_overrides(vault: Path) -> tuple[set[str], set[str]]:
    """Return the (watch, mute) token sets from steering.md's override sections.

    Only bullets under ``## Watch for`` and ``## Muted`` contribute; prose,
    blockquote guidance, and bullets under any other heading never do.
    """
    path = Path(vault) / "steering.md"
    if not path.is_file():
        return set(), set()
    _frontmatter, body = split_frontmatter(path.read_text(encoding="utf-8"))
    watch: set[str] = set()
    mute: set[str] = set()
    target: set[str] | None = None
    for line in body.splitlines():
        heading = _HEADING.match(line)
        if heading:
            target = {"watch for": watch, "muted": mute}.get(heading.group(2).casefold())
            continue
        if target is None:
            continue
        bullet = _BULLET.match(line)
        if bullet:
            target.update(relevance_tokens(bullet.group(1)))
    return watch, mute


def _tags(frontmatter: dict[str, Any]) -> list[object]:
    tags = frontmatter.get("tags")
    return list(tags) if isinstance(tags, list) else []


def _token_sources(vault: Path) -> dict[str, set[str]]:
    """Map each candidate steering token to its contributing source labels.

    Labels: ``project:<rel>``, ``hub:<rel>``, ``question:<rel>``, ``watch``.
    Muted subtraction happens in the callers so provenance can also report
    what a mute removed.
    """
    vault = Path(vault)
    sources: dict[str, set[str]] = {}

    def contribute(tokens: set[str], label: str) -> None:
        for token in tokens:
            sources.setdefault(token, set()).add(label)

    for path in iter_markdown(vault):
        frontmatter = read_frontmatter(path)
        if not frontmatter or frontmatter.get("archived") is True:
            continue
        concept_type = frontmatter.get("type")
        if concept_type not in {"project", "hub", "note"}:
            continue
        rel = path.relative_to(vault).as_posix()
        if concept_type == "project":
            contribute(
                relevance_tokens(
                    frontmatter.get("title"), frontmatter.get("thesis"), *_tags(frontmatter)
                ),
                f"project:{rel}",
            )
        elif concept_type == "hub":
            contribute(
                relevance_tokens(
                    frontmatter.get("title"), frontmatter.get("tag"), *_tags(frontmatter)
                ),
                f"hub:{rel}",
            )
        elif frontmatter.get("mode") == "question":
            if frontmatter.get("question_status") == "resolved":
                continue
            contribute(relevance_tokens(frontmatter.get("title")), f"question:{rel}")
    watch, _mute = steering_overrides(vault)
    contribute(watch, "watch")
    return sources


def effective_steering_tokens(vault: Path) -> set[str]:
    """The steering token set discovery relevance ranks against.

    Union of active projects, hubs, open question notes, and ``## Watch
    for`` bullets, minus ``## Muted`` bullets (per-token subtraction).
    """
    _watch, mute = steering_overrides(vault)
    return set(_token_sources(vault)) - mute
