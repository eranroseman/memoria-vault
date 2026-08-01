"""Hub Candidates block: the machine half of the wiki-ZK bridge (NODES §5).

Hub files end with a delimited, machine-owned terminal section:

    ## Candidates
    %%candidates: run=<run_id>%%
    - [[digests/x.md]] — reason %%run=<run_id>%%
    %%end-candidates%%

Writers replace the section wholesale; the curated body above it is never
touched. Revert = delete the section (it regenerates). Accept = the PI moves
a line into the body — a plain edit, observed as a PI edit.
"""

from __future__ import annotations

from collections.abc import Iterable, Sequence
from pathlib import Path
from typing import Any

from memoria_vault.runtime import state
from memoria_vault.runtime.content_security import neutralize_untrusted_markdown_fragment
from memoria_vault.runtime.trusted_writer import (
    OperationContext,
    mark_checked,
    materialize_unchecked,
    stage_concept,
)
from memoria_vault.runtime.vaultio import frontmatter_doc, split_frontmatter

CANDIDATES_HEADING = "## Candidates"
CANDIDATES_OPEN_PREFIX = "%%candidates: run="
CANDIDATES_END = "%%end-candidates%%"


def candidate_entry(target_rel: str, reason: str, run_id: str) -> str:
    """One Candidates line: wikilink target, neutralized reason, run attribution."""
    safe_reason = neutralize_untrusted_markdown_fragment(reason)
    return f"- [[{target_rel}]] — {safe_reason} %%run={run_id}%%"


def render_candidates_section(run_id: str, entries: Sequence[str]) -> str:
    """Render the delimited terminal section for one run's entries."""
    lines = "".join(f"{entry}\n" for entry in entries)
    return f"{CANDIDATES_HEADING}\n{CANDIDATES_OPEN_PREFIX}{run_id}%%\n{lines}{CANDIDATES_END}\n"


def split_candidates_section(body: str) -> tuple[str, str]:
    """Split a hub body into (curated part, terminal Candidates section)."""
    opener = f"{CANDIDATES_HEADING}\n{CANDIDATES_OPEN_PREFIX}"
    if body.startswith(opener):
        index = 0
    else:
        found = body.rfind(f"\n{opener}")
        if found == -1:
            return body, ""
        index = found + 1
    section = body[index:]
    if not section.rstrip("\n").endswith(CANDIDATES_END):
        return body, ""
    return body[:index], section


def write_hub_candidates(
    vault: Path,
    hub_rel: str,
    entries: Sequence[str],
    *,
    context: OperationContext,
    checks: Iterable[str] | None = None,
    inputs: Iterable[str | dict[str, Any]] = (),
) -> dict[str, Any]:
    """Replace hub_rel's terminal Candidates section wholesale.

    The curated body above the section is preserved byte-for-byte (a missing
    final newline is normalized once, as every trusted write already does).
    A checked hub is re-written checked; any other live hub is re-staged and
    materialized unchecked, so the block write never changes trust status.
    """
    vault = Path(vault)
    path = vault / hub_rel
    frontmatter, body = split_frontmatter(path.read_text(encoding="utf-8"))
    if frontmatter.get("type") != "hub":
        raise ValueError(f"candidates block target is not a hub: {hub_rel}")
    curated, _stale = split_candidates_section(body)
    if curated and not curated.endswith("\n"):
        curated += "\n"
    new_body = curated + render_candidates_section(context.run_id, entries)
    status = state.concept_check_status(vault, hub_rel)
    if status == "quarantined":
        # Staging would rewrite the verdict row to "unchecked", silently
        # releasing content the runtime quarantined.
        raise ValueError(f"cannot write candidates into quarantined hub: {hub_rel}")
    if status == "checked":
        return mark_checked(vault, hub_rel, context=context, checks=checks, body=new_body)
    # Frontmatter is passed through unchanged: stage_concept validates it and
    # fails closed if it carries a retired field.
    event = stage_concept(
        vault,
        hub_rel,
        frontmatter_doc(frontmatter, new_body),
        context=context,
        inputs=inputs,
    )
    materialize_unchecked(vault, hub_rel, context=context)
    return event
