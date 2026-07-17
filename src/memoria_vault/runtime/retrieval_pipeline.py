"""Shared retrieval-pipeline staging for R2 design sections 1, 4, and 6.

Stage accounting carries ordered pipeline counts, named excluded strata, the
explicit no-op rerank seam, and a deterministic trace. The module is pure
stdlib so both ask and explore can consume it without vault I/O.
"""

from __future__ import annotations

from collections import Counter
from typing import Any

RERANK_MODE = "off"

_RESERVED_STAGES = frozenset({"universe", "ranked", "returned"})


class PipelineStages:
    """Ordered stage accounting: universe, filters, ranked, then returned."""

    def __init__(self, universe: int) -> None:
        self._rows: list[dict[str, Any]] = [{"stage": "universe", "count": int(universe)}]
        self._filters: Counter[str] = Counter()
        self._stage_names = {"universe"}
        self._ranked = False
        self._returned = False

    def add_filter(self, name: str, count: int) -> None:
        """Append a pre-rank filter, suffixing repeat names deterministically."""
        if self._ranked:
            raise ValueError("filters must precede the ranked stage")
        clean = name.strip()
        if not clean or clean in _RESERVED_STAGES:
            raise ValueError(f"invalid filter stage name: {name!r}")
        self._filters[clean] += 1
        occurrence = self._filters[clean]
        stage = clean if occurrence == 1 else f"{clean}#{occurrence}"
        while stage in self._stage_names:
            occurrence += 1
            stage = f"{clean}#{occurrence}"
        self._filters[clean] = occurrence
        self._stage_names.add(stage)
        self._rows.append({"stage": stage, "count": int(count)})

    def add_ranked(self, count: int) -> None:
        """Record the sole ranked stage."""
        if self._ranked:
            raise ValueError("ranked stage recorded twice")
        self._ranked = True
        self._rows.append({"stage": "ranked", "count": int(count)})

    def add_returned(self, count: int) -> None:
        """Record the terminal returned stage."""
        if not self._ranked:
            raise ValueError("returned stage requires a ranked stage first")
        if self._returned:
            raise ValueError("returned stage recorded twice")
        self._returned = True
        self._rows.append({"stage": "returned", "count": int(count)})

    def rows(self) -> list[dict[str, Any]]:
        """Return a defensive copy once the pipeline has both terminal stages."""
        if not self._returned:
            raise ValueError("pipeline_counts requires ranked and returned stages")
        return [dict(row) for row in self._rows]


def excluded_strata(*, unchecked: int = 0, stale: int = 0, gated: int = 0) -> dict[str, int]:
    """Return named excluded strata with all three keys present."""
    return {"unchecked": int(unchecked), "stale": int(stale), "gated": int(gated)}


def candidate_count(pipeline_counts: list[dict[str, Any]]) -> int:
    """Return the candidate count immediately entering the ranked stage."""
    previous: int | None = None
    for row in pipeline_counts:
        if row["stage"] == "ranked":
            if previous is None:
                raise ValueError("ranked stage has no preceding candidate stage")
            return previous
        previous = int(row["count"])
    raise ValueError("pipeline_counts has no ranked stage")


def honest_empty(pipeline_counts: list[dict[str, Any]], strata: dict[str, int]) -> str:
    """Render the deterministic honest-empty sentence from actual counts."""
    unchecked = int(strata.get("unchecked", 0))
    return (
        f"0 of {candidate_count(pipeline_counts)} candidates matched; "
        f"{unchecked} unchecked documents were not searched"
    )


def rerank(hits: list[Any]) -> list[Any]:
    """Return a copy through the explicit off-by-default reranking seam."""
    if RERANK_MODE != "off":
        raise NotImplementedError(f"rerank mode {RERANK_MODE!r} has no shipped implementation")
    return list(hits)


def build_trace(
    pipeline_counts: list[dict[str, Any]],
    returned: list[tuple[str, float]],
    *,
    fusion_inputs: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    """Build counts, scores, and rerank state without invented explanation."""
    trace: dict[str, Any] = {
        "pipeline_counts": [dict(row) for row in pipeline_counts],
        "scores": [{"path": path, "score": score} for path, score in returned],
        "rerank": RERANK_MODE,
    }
    if fusion_inputs and len(fusion_inputs) > 1:
        trace["fusion_inputs"] = [dict(leg) for leg in fusion_inputs]
    return trace
