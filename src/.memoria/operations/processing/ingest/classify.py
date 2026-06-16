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

ADR-15 addition: when an optional `.memoria/project-hints.yaml` exists, the
classify step also PROPOSES project membership by simple topic overlap — the
proposal lands in `_proposed_classification.projects` for human confirmation
at triage, never in the `projects` frontmatter field. Absent file = fully
manual project tagging (silent no-op). Same audit trail.
"""
from __future__ import annotations

import datetime
import json
import re
import sys
import uuid
from pathlib import Path

AUDIT_RELPATH = "system/logs/classify.jsonl"
HINTS_RELPATH = ".memoria/project-hints.yaml"
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


_warned_calibration = False     # warn once per process, not per ingest
_warned_hints = False           # ditto, for a malformed project-hints.yaml


def thresholds(vault: Path | None) -> tuple[float, float]:
    """(confidence_floor, near_tie_margin) from calibration.yaml, with defaults.

    A parse/read failure degrades to the defaults — but loudly (one stderr
    warning per process), so a miscalibrated vault is visible, not silent."""
    global _warned_calibration
    try:
        import yaml

        f = Path(vault) / ".memoria" / "schemas" / "calibration.yaml"
        c = yaml.safe_load(f.read_text(encoding="utf-8"))["classify"]
        return float(c["confidence_floor"]), float(c["near_tie_margin"])
    except Exception as exc:
        if not _warned_calibration:
            _warned_calibration = True
            print(f"[classify] WARNING: cannot read classify thresholds from "
                  f"calibration.yaml ({type(exc).__name__}: {exc}) — using defaults "
                  f"floor={DEFAULT_FLOOR}, margin={DEFAULT_MARGIN}", file=sys.stderr)
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
    if decision["status"] == "ambiguous":
        record["classify_miss"] = True
        record["miss_kind"] = (
            "below_floor" if "below the confidence floor" in decision["reason"]
            else "near_tie"
        )
    log = Path(vault) / AUDIT_RELPATH
    log.parent.mkdir(parents=True, exist_ok=True)
    with log.open("a", encoding="utf-8") as f:
        f.write(json.dumps(record, ensure_ascii=False) + "\n")
    return record


# --------------------------------------------------------------------------- #
# project membership proposal (ADR-15)
# --------------------------------------------------------------------------- #
# A lightweight, optional `.memoria/project-hints.yaml` (one `primary_topics`
# list per project) lets the classify step PROPOSE a `projects` value by simple
# topic overlap. The proposal lands in `_proposed_classification` for the human
# to confirm at triage — it is never applied to the `projects` frontmatter
# field. Absent hints file = project membership is fully manual (silent no-op).


def load_project_hints(vault: Path | None) -> list[dict]:
    """The project list from .memoria/project-hints.yaml ([] if unusable).

    An ABSENT file is the documented opt-out (ADR-15) — silent, no warning.
    A present-but-malformed file degrades to [] loudly (one stderr warning per
    process, the thresholds() pattern), so a broken config is visible."""
    global _warned_hints
    if vault is None:
        return []
    f = Path(vault) / HINTS_RELPATH
    if not f.is_file():
        return []
    try:
        import yaml

        data = yaml.safe_load(f.read_text(encoding="utf-8"))
        out = []
        for p in data["projects"]:
            pid = str(p["id"]).strip()
            topics = [str(t).strip() for t in p["primary_topics"] if str(t).strip()]
            if pid and topics:
                out.append({"id": pid, "primary_topics": topics})
        return out
    except Exception as exc:
        if not _warned_hints:
            _warned_hints = True
            print(f"[classify] WARNING: cannot read project hints from "
                  f"{HINTS_RELPATH} ({type(exc).__name__}: {exc}) — project "
                  f"membership stays manual for this run", file=sys.stderr)
        return []


def _norm_topic(term: str) -> str:
    """Kebab-case normalization: 'mHealth Apps' -> 'mhealth-apps'."""
    return re.sub(r"[^a-z0-9]+", "-", str(term).lower()).strip("-")


def paper_topic_terms(merged: dict) -> list[str]:
    """The paper's normalized topic signals: OpenAlex topic names + subfields."""
    seen: list[str] = []
    for t in merged.get("topics_scored") or []:
        for raw in (t.get("name"), t.get("subfield")):
            n = _norm_topic(raw or "")
            if n and n not in seen:
                seen.append(n)
    return seen


def _hint_matches(hint: str, terms: list[str]) -> bool:
    """A hint topic matches a paper term when the normalized forms are equal or
    the hint's tokens all appear in the term ('mhealth' ~ 'mhealth-apps')."""
    toks = set(hint.split("-"))
    return any(hint == term or toks <= set(term.split("-")) for term in terms)


def propose_projects(merged: dict, hints: list[dict]) -> dict:
    """The ADR-15 project-membership proposal for one merged record. Pure.

    Simple overlap: a project's score is how many of its `primary_topics`
    match the paper's topic signals. Every project with >= 1 overlap is
    proposed, ranked by overlap (then id) — a conservative rule, safe because
    this is a proposal the human confirms at triage, never an auto-apply.

    status: proposed (>=1 overlap) | no_match (hints + topics, zero overlap)
            | no_data (no topic signals — a no-op, not audited)."""
    terms = paper_topic_terms(merged)
    if not terms:
        return {"projects": [], "candidates": [], "status": "no_data",
                "reason": "no scored topics in the enrichment payload"}
    cands = []
    for p in hints:
        matched = [t for t in p["primary_topics"]
                   if _hint_matches(_norm_topic(t), terms)]
        if matched:
            cands.append({"id": p["id"], "score": len(matched),
                          "matched": matched})
    cands.sort(key=lambda c: (-c["score"], c["id"]))
    if not cands:
        return {"projects": [], "candidates": [], "status": "no_match",
                "reason": "no project's primary_topics overlap the paper's "
                          "topic signals"}
    return {"projects": [c["id"] for c in cands], "candidates": cands,
            "status": "proposed",
            "reason": "topic overlap: " + "; ".join(
                f"{c['id']} ({c['score']} hint topic(s) matched)"
                for c in cands)}


def append_project_audit(vault: Path, citekey: str, decision: dict) -> dict:
    """One JSONL audit line per project-membership proposal (proposed or
    no_match) in system/logs/classify.jsonl — same trail as append_audit().
    Honesty rules (ADR-51): candidates carry overlap counts, never confidence."""
    record = {
        "timestamp": datetime.datetime.now(datetime.timezone.utc)
                       .strftime("%Y-%m-%dT%H:%M:%SZ"),
        "run_id": str(uuid.uuid4())[:8], "stage": "project_hints",
        "citekey": citekey, "decision": decision["status"],
        "projects_proposed": decision["projects"],
        "candidates": decision["candidates"],
        "reason": decision["reason"],
        "source": "project-hints.yaml x openalex.topics",
    }
    log = Path(vault) / AUDIT_RELPATH
    log.parent.mkdir(parents=True, exist_ok=True)
    with log.open("a", encoding="utf-8") as f:
        f.write(json.dumps(record, ensure_ascii=False) + "\n")
    return record


if __name__ == "__main__":
    print(__doc__)
