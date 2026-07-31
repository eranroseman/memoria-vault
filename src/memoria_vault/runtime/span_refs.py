"""Source-span ref resolution - the R2 section-5 anchor-locator rule, once.

``work_id#^pNNNN`` is the reference syntax (the shipped
``passages.passage_id`` column is a content hash and keeps its name).
Resolution: split on ``#``, strip ``^`` (via the shipped
``parse_source_span_ref``), match ``passages`` rows on
``(work_id, anchor)``. Shipped passages are one row per document
(``indexing._passage_row``), so only a document's first anchor has a row;
every other anchor resolves through the interim file scan (the
``state._source_span_pages`` rule) until R1's passage-granular rows land.
Shared by the R1-gated extractive composer and the retrieval-fixture
loader - one resolution rule, two consumers.
"""

from __future__ import annotations

import re
from pathlib import Path

from memoria_vault.runtime import state
from memoria_vault.runtime.evidence import parse_source_span_ref
from memoria_vault.runtime.paths import safe_filename
from memoria_vault.runtime.policy.paths import normalize_path

_ANCHOR_RE = re.compile(r"\^p\d{4,}")


def resolve_span_ref(vault: Path, ref: str) -> dict[str, str] | None:
    """Resolve a source-span ref to ``{work_id, anchor, path}``, or None."""
    vault = Path(vault)
    try:
        span = parse_source_span_ref(ref)
    except ValueError:
        return None
    source = state.catalog_source(vault, span.work_id)
    if source is None or source.get("check_status") != "checked":
        return None
    path = f"fulltexts/{safe_filename(span.work_id)}.md"
    if state.db_path(vault).is_file():
        with state.connect(vault) as conn:
            row = conn.execute(
                """
                SELECT path
                FROM passages
                WHERE work_id = ?
                  AND anchor = ?
                  AND origin = 'generated'
                  AND concept_id = ?
                  AND path = ?
                """,
                (span.work_id, span.page, f"catalog/sources/{span.work_id}", path),
            ).fetchone()
        if row is not None:
            return {"work_id": span.work_id, "anchor": span.page, "path": str(row["path"])}
    return _file_scan_resolution(vault, span.work_id, span.page, source=source)


def _file_scan_resolution(
    vault: Path, work_id: str, anchor: str, *, source: dict[str, object] | None = None
) -> dict[str, str] | None:
    """Interim resolution: scan the work's content file for the anchor."""
    source = source or state.catalog_source(vault, work_id)
    if source is None:
        return None
    content_path = vault / normalize_path(str(source.get("content_path") or ""))
    if not content_path.is_file():
        return None
    try:
        text = content_path.read_text(encoding="utf-8")
    except (OSError, UnicodeError):
        return None
    anchors = {match.removeprefix("^") for match in _ANCHOR_RE.findall(text)}
    if anchor not in anchors:
        return None
    return {
        "work_id": work_id,
        "anchor": anchor,
        "path": f"fulltexts/{safe_filename(work_id)}.md",
    }
