#!/usr/bin/env python3
"""classify.py — automated, audited classification (D21 / ADR-54).

classify is not a gate: it is low-stakes metadata a human would rubber-stamp, so
the ingest path applies it mechanically from the OpenAlex topics **already in the
enrichment payload** (no new network call) and logs every decision. The doctrine:

  - clear winner       -> apply `research_area` (and a `methodology` facet when
                          derivable from the S2 publication types) silently
  - near-tie / below
    the calibration
    floor              -> leave the field unset and raise ONE Inbox `flag` card
                          (honesty rules: what was ambiguous + the top candidates
                          with scores — never a verdict)
  - enrichment off /
    no topic data      -> no-op

Thresholds live in `.memoria/schemas/calibration.yaml` under `classify:`
(`confidence_floor`, `near_tie_margin`), mirroring `entity_resolution` (ADR-56).
Every applied/flagged decision appends one JSONL line to
`system/logs/classify.jsonl` — the audit trail that makes the automation
correctable (same provenance pattern as `system/logs/patterns.jsonl`).

This module writes only the audit log; notes and cards stay with the gated
writing layer, exactly like the rest of the ingest engine.
"""
from __future__ import annotations

import datetime
import json
import uuid
from pathlib import Path

AUDIT_RELPATH = "system/logs/classify.jsonl"
DEFAULT_FLOOR = 0.60
DEFAULT_MARGIN = 0.15

# S2 publicationTypes -> methodology facet. Deterministic and conservative: only
# types that *are* a methodology are mapped; venue-ish types (JournalArticle,
# Editorial, News, ...) are not a methodology and stay unmapped.
METHODOLOGY_FROM_PUBTYPE = {
    "review": "review",
    "metaanalysis": "meta-analysis",
    "clinicaltrial": "clinical-trial",
    "casereport": "case-report",
    "dataset": "dataset",
}


def thresholds(vault: Path | None) -> tuple[float, float]:
    """(confidence_floor, near_tie_margin) from calibration.yaml, with defaults."""
    try:
        import yaml

        f = Path(vault) / ".memoria" / "schemas" / "calibration.yaml"
        c = yaml.safe_load(f.read_text(encoding="utf-8"))["classify"]
        return float(c["confidence_floor"]), float(c["near_tie_margin"])
    except Exception:
        return DEFAULT_FLOOR, DEFAULT_MARGIN


def candidates(merged: dict) -> list[tuple[str, float]]:
    """Research-area candidates from the scored OpenAlex topics, best first.

    Topics roll up to their subfield (the research-area granularity — several
    topics of one paper usually share it), keeping the best score per area;
    a topic without a subfield falls back to its own display name."""
    best: dict[str, float] = {}
    for t in merged.get("topics_scored") or []:
        name = (t.get("subfield") or t.get("name") or "").strip()
        if not name:
            continue
        score = float(t.get("score") or 0.0)
        if score > best.get(name, -1.0):
            best[name] = score
    return sorted(best.items(), key=lambda kv: (-kv[1], kv[0]))


def methodology(merged: dict) -> list[str]:
    """Methodology facet from the S2 publication types (deterministic map)."""
    out: list[str] = []
    for pt in merged.get("publication_types") or []:
        m = METHODOLOGY_FROM_PUBTYPE.get(str(pt).lower())
        if m and m not in out:
            out.append(m)
    return out


def decide(merged: dict, floor: float = DEFAULT_FLOOR,
           margin: float = DEFAULT_MARGIN) -> dict:
    """The classify decision for one merged record. Pure — no I/O.

    status: applied (clear winner) | ambiguous (near-tie / below floor; field
    stays unset) | no_data (nothing to classify — a no-op, not audited)."""
    cands = candidates(merged)
    meth = methodology(merged)
    d = {"research_area": [], "methodology": meth,
         "candidates": [{"name": n, "score": round(s, 4)} for n, s in cands[:5]]}
    if not cands:
        return {**d, "status": "no_data",
                "reason": "no scored topics in the enrichment payload"}
    top_name, top = cands[0]
    if top < floor:
        return {**d, "status": "ambiguous",
                "reason": f"top candidate {top_name!r} scores {top:.2f}, "
                          f"below the confidence floor {floor:.2f}"}
    if len(cands) > 1 and (top - cands[1][1]) < margin:
        return {**d, "status": "ambiguous",
                "reason": f"near-tie: {top_name!r} ({top:.2f}) vs "
                          f"{cands[1][0]!r} ({cands[1][1]:.2f}) is within the "
                          f"margin {margin:.2f}"}
    return {**d, "status": "applied", "research_area": [top_name],
            "reason": f"clear winner: {top_name!r} ({top:.2f}) >= floor "
                      f"{floor:.2f} with margin >= {margin:.2f}"}


def flag_payload(citekey: str, decision: dict) -> dict:
    """The ONE Inbox flag for an ambiguous decision — finding + candidates with
    scores, no verdict (ADR-51 honesty rules). The writing layer raises the card."""
    tops = "; ".join(f"{c['name']} ({c['score']:.2f})"
                     for c in decision["candidates"][:3]) or "none"
    return {
        "title": f"Ambiguous classification for {citekey}",
        "finding": (f"research_area left unset: {decision['reason']}. "
                    f"Top candidates: {tops}."),
        "citekey": citekey,
    }


def append_audit(vault: Path, citekey: str, decision: dict,
                 floor: float, margin: float) -> dict:
    """Append one JSONL audit line per classify decision (applied or flagged) to
    system/logs/classify.jsonl — the patterns.jsonl provenance pattern."""
    record = {
        "timestamp": datetime.datetime.now(datetime.timezone.utc)
                       .strftime("%Y-%m-%dT%H:%M:%SZ"),
        "run_id": str(uuid.uuid4())[:8], "stage": "classify",
        "citekey": citekey, "decision": decision["status"],
        "research_area": decision["research_area"],
        "methodology": decision["methodology"],
        "candidates": decision["candidates"],
        "reason": decision["reason"],
        "confidence_floor": floor, "near_tie_margin": margin,
        "source": "openalex.topics",
    }
    log = Path(vault) / AUDIT_RELPATH
    log.parent.mkdir(parents=True, exist_ok=True)
    with log.open("a", encoding="utf-8") as f:
        f.write(json.dumps(record, ensure_ascii=False) + "\n")
    return record


if __name__ == "__main__":
    print(__doc__)
