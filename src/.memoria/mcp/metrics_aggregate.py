#!/usr/bin/env python3
"""Metrics aggregator -- roll fleet run-history + audit into lane-metric notes.

Writes `system/metrics/lane-<lane>-<period>.md` (one per lane per ISO week),
which the [fleet-health dashboard] reads for the per-lane **trust score** (0-100).

Inputs (all best-effort -- missing sources degrade gracefully):
  - system/logs/audit.jsonl          deny rate (policy-MCP decisions, this period)
  - Hermes board (`hermes kanban list --json`)   success rate + retry rate per lane
  - system/logs/lint-findings.jsonl  drift incidents (Linter), if present

Trust score (glossary "Trust score"): combines audit **deny rate**, **retry rate**,
**success rate**, **drift incidents**, **secret hits**, and accept/reject ratios;
bands **90+ healthy / 70-89 watch / <70 act**. The docs pin the inputs and bands
but NOT the weights, so the composition below is Memoria's own -- documented and
tunable at the top of the file. The CRS-shaped `pass^k` consistency target needs
repeated-run data per task and is a TODO (noted in the dashboard design).

    python metrics_aggregate.py --vault <path>                 # reads `hermes kanban list --json`
    python metrics_aggregate.py --vault <path> --from-json cards.json

[fleet-health dashboard]: docs/explanation/dashboards/operational-health/fleet-health.md
"""
from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

from _shared import (
    iter_jsonl as _iter_jsonl_raw,
)
from _shared import (
    parse_iso,
    resolve_vault,
)

METRICS_RELDIR = "system/metrics"
AUDIT_RELPATH = "system/logs/audit.jsonl"
LINT_RELPATH = "system/logs/lint-findings.jsonl"
DISPOSITION_RELPATH = "system/logs/disposition.jsonl"        # accept | edit | reject per review
COST_RELPATH = "system/logs/cost.jsonl"                      # API spend + tokens per card
TRANSITIONS_RELPATH = "system/logs/board-transitions.jsonl"  # status/review transitions (for decision time)
TERMINAL_REVIEW = frozenset({"approved", "rejected", "changes-requested"})
MUTATING = frozenset({"write", "append", "move", "delete", "mkdir", "auto_fix"})
LANES = ("memoria-librarian", "memoria-writer", "memoria-peer-reviewer",
         "memoria-engineer")   # the background agents (ADR-48); no co-PI/engine lanes
LOW_CONFIDENCE_SAMPLES = 5          # below this, the score is flagged insufficient-data

# --- Trust-score weights (tunable; bands are fixed by the glossary) ---------- #
W_DENY = 40        # denials are the strongest negative signal (injection / misconfig)
W_FAIL = 40        # (1 - success_rate)
W_RETRY = 20       # per average-retry, capped
RETRY_CAP = 30
W_DRIFT = 2        # per drift incident, capped
DRIFT_CAP = 20
W_SECRET = 10      # per secret hit, capped
SECRET_CAP = 30
W_RATIO = 10       # rubber-stamping (>90% accept) or prompt-drift (<20% accept)


# --------------------------------------------------------------------------- #
def iso_period(dt: datetime) -> str:
    y, w, _ = dt.isocalendar()
    return f"{y}-W{w:02d}"


# _parse_ts: delegate to _shared.parse_iso
_parse_ts = parse_iso


def read_audit(vault: Path, period: str) -> dict[str, dict]:
    """Per-profile mutating-decision counts for `period` from audit.jsonl."""
    out: dict[str, dict] = {}
    for e in _iter_jsonl(vault, AUDIT_RELPATH, period):
        if e.get("action") not in MUTATING:
            continue
        lane = e.get("profile", "unknown")
        rec = out.setdefault(lane, {"total": 0, "deny": 0, "dry_run": 0})
        rec["total"] += 1
        if e.get("decision") == "deny":
            rec["deny"] += 1
        elif e.get("decision") == "dry_run":
            rec["dry_run"] += 1
    return out


def read_board(cards: list[dict]) -> dict[str, dict]:
    """Per-lane done/blocked + retry totals, via board_export's normalizer."""
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    import board_export
    out: dict[str, dict] = {}
    for raw in cards:
        c = board_export.normalize(raw)
        rec = out.setdefault(c["assignee"], {"done": 0, "blocked": 0, "retry_total": 0})
        if c["status"] == "done":
            rec["done"] += 1
        elif c["status"] == "blocked":
            rec["blocked"] += 1
        try:
            rec["retry_total"] += int(c["retry_count"])
        except (TypeError, ValueError):
            pass
    return out


def read_drift(vault: Path, period: str) -> dict[str, int]:
    """Per-lane drift-incident counts from lint-findings.jsonl, if present.
    Falls back to {} when the Linter hasn't produced findings yet."""
    out: dict[str, int] = {}
    for e in _iter_jsonl(vault, LINT_RELPATH, period):
        lane = e.get("lane") or e.get("profile") or "fleet"
        out[lane] = out.get(lane, 0) + 1
    return out


def read_lint_verdict(vault: Path, period: str) -> dict:
    """Severity counts + PASS/REVIEW/FAIL verdict from lint-findings.jsonl for `period`.

    Matches the Linter's verdict rule (detectors.py `verdict`): any CRITICAL -> FAIL;
    any HIGH/MEDIUM -> REVIEW; otherwise PASS."""
    counts = {"CRITICAL": 0, "HIGH": 0, "MEDIUM": 0, "LOW": 0}
    for e in _iter_jsonl(vault, LINT_RELPATH, period):
        sev = e.get("severity", "")
        if sev in counts:
            counts[sev] += 1
    if counts["CRITICAL"]:
        v = "FAIL"
    elif counts["HIGH"] or counts["MEDIUM"]:
        v = "REVIEW"
    else:
        v = "PASS"
    return {"verdict": v, "total": sum(counts.values()), **counts}


def lint_verdict_note(v: dict, period: str, now: datetime) -> str:
    fm = {
        "type": "lint-verdict", "period": period, "verdict": v["verdict"],
        "finding_count": v["total"], "critical_count": v["CRITICAL"],
        "high_count": v["HIGH"], "medium_count": v["MEDIUM"], "low_count": v["LOW"],
        "computed_at": now.strftime("%Y-%m-%dT%H:%M:%SZ"),
    }
    lines = ["---"]
    for k, val in fm.items():
        lines.append(f'{k}: "{val}"' if isinstance(val, str) else f"{k}: {val}")
    lines += ["---", "", f"# Lint verdict — {period}", "",
              f"**{v['verdict']}** · {v['total']} finding(s): {v['CRITICAL']} critical · "
              f"{v['HIGH']} high · {v['MEDIUM']} medium · {v['LOW']} low.", "",
              f"*Computed {fm['computed_at']} — rerunning the aggregator in the "
              f"same period overwrites this note.*", ""]
    return "\n".join(lines)


def _iter_jsonl(vault: Path, relpath: str, period: str | None):
    """Yield JSON rows from a JSONL log, filtered to `period` (None = all)."""
    for e in _iter_jsonl_raw(vault / relpath):
        if period is not None:
            ts = _parse_ts(e.get("timestamp", ""))
            if ts is None or iso_period(ts) != period:
                continue
        yield e


def read_disposition(vault: Path, period: str) -> dict[str, dict]:
    """Per-lane accept/edit/reject counts from disposition.jsonl for `period`."""
    out: dict[str, dict] = {}
    for e in _iter_jsonl(vault, DISPOSITION_RELPATH, period):
        rec = out.setdefault(e.get("lane", "unknown"),
                             {"accepted": 0, "edited": 0, "rejected": 0})
        d = e.get("disposition")
        if d in rec:
            rec[d] += 1
    return out


def accept_ratio_of(d: dict) -> float | None:
    """Accepted-as-is fraction (edits and rejects count against it) — the
    rubber-stamping / prompt-drift signal. None when no reviews yet."""
    total = d.get("accepted", 0) + d.get("edited", 0) + d.get("rejected", 0)
    return d["accepted"] / total if total else None


def read_cost(vault: Path, period: str) -> dict[str, dict]:
    """Per-lane API spend + token totals from cost.jsonl for `period`."""
    out: dict[str, dict] = {}
    for e in _iter_jsonl(vault, COST_RELPATH, period):
        rec = out.setdefault(e.get("lane", "unknown"),
                             {"cost": 0.0, "tokens_in": 0, "tokens_out": 0, "cards": 0})
        rec["cards"] += 1
        for k in ("cost", "tokens_in", "tokens_out"):
            try:
                rec[k] += float(e.get(k) or 0)
            except (TypeError, ValueError):
                pass
    return out


def _median(xs: list[float]) -> float | None:
    s = sorted(xs)
    n = len(s)
    if n == 0:
        return None
    return s[n // 2] if n % 2 else (s[n // 2 - 1] + s[n // 2]) / 2


def read_decision_time(vault: Path, period: str) -> dict[str, float]:
    """Per-lane median operator decision time (minutes) — the gap between a card's
    `review -> requested` transition and its terminal review transition, read from
    board-transitions.jsonl. Keyed to the period of the *terminal* transition."""
    requested: dict[str, datetime] = {}   # task_id -> requested ts (across all time)
    samples: dict[str, list[float]] = {}
    for e in _iter_jsonl(vault, TRANSITIONS_RELPATH, None):   # need full history to pair
        if e.get("kind") != "review":
            continue
        ts = _parse_ts(e.get("timestamp", ""))
        tid, lane, to = e.get("task_id"), e.get("lane", "unknown"), e.get("to")
        if ts is None or tid is None:
            continue
        if to == "requested":
            requested[tid] = ts
        elif to in TERMINAL_REVIEW and tid in requested:
            t0 = requested.pop(tid)
            if iso_period(ts) == period:
                samples.setdefault(lane, []).append((ts - t0).total_seconds() / 60.0)
    return {lane: round(_median(v), 1) for lane, v in samples.items() if v}


def trust_score(deny_rate: float, retry_rate: float, success_rate: float,
                drift: int = 0, secret_hits: int = 0,
                accept_ratio: float | None = None) -> tuple[int, str]:
    """Compose the 0-100 trust score from the glossary's inputs. Bands fixed:
    90+ healthy / 70-89 watch / <70 act."""
    score = 100.0
    score -= W_DENY * deny_rate
    score -= W_FAIL * (1.0 - success_rate)
    score -= min(RETRY_CAP, W_RETRY * retry_rate)
    score -= min(DRIFT_CAP, W_DRIFT * drift)
    score -= min(SECRET_CAP, W_SECRET * secret_hits)
    if accept_ratio is not None and (accept_ratio > 0.9 or accept_ratio < 0.2):
        score -= W_RATIO                       # rubber-stamping or prompt drift
    score = max(0, min(100, round(score)))
    band = "healthy" if score >= 90 else "watch" if score >= 70 else "act"
    return int(score), band


def compute_lane(lane: str, audit: dict, board: dict, drift: int,
                 disp: dict | None = None, cost: dict | None = None,
                 dtime: dict | None = None) -> dict | None:
    """Combine the inputs for one lane into a metric dict, or None if no activity."""
    a = audit.get(lane, {})
    b = board.get(lane, {})
    d = (disp or {}).get(lane, {})
    c = (cost or {}).get(lane, {})
    writes = a.get("total", 0)
    denies = a.get("deny", 0)
    done, blocked = b.get("done", 0), b.get("blocked", 0)
    runs = done + blocked
    reviews = d.get("accepted", 0) + d.get("edited", 0) + d.get("rejected", 0)
    samples = writes + runs + reviews
    if samples == 0:
        return None
    deny_rate = denies / writes if writes else 0.0
    success_rate = done / runs if runs else 1.0
    retry_rate = b.get("retry_total", 0) / runs if runs else 0.0
    accept_ratio = accept_ratio_of(d) if reviews else None
    score, band = trust_score(deny_rate, retry_rate, success_rate, drift=drift,
                              accept_ratio=accept_ratio)
    if samples < LOW_CONFIDENCE_SAMPLES:
        band = "insufficient-data"
    return {
        "lane": lane, "trust_score": score, "band": band,
        "deny_rate": round(deny_rate, 3), "success_rate": round(success_rate, 3),
        "retry_rate": round(retry_rate, 3), "drift_incidents": drift,
        "writes": writes, "denies": denies, "dry_runs": a.get("dry_run", 0),
        "done": done, "blocked": blocked, "samples": samples,
        # --- human-loop + cost telemetry (the publication-grade signals) ---
        "accepted": d.get("accepted", 0), "edited": d.get("edited", 0),
        "rejected": d.get("rejected", 0),
        "accept_ratio": round(accept_ratio, 3) if accept_ratio is not None else None,
        "decision_time_min": (dtime or {}).get(lane),
        "cost": round(c.get("cost", 0.0), 4),
        "tokens_in": int(c.get("tokens_in", 0)), "tokens_out": int(c.get("tokens_out", 0)),
        "consistency_passk": None,   # pass^k needs repeated-run data; harness TODO (see header)
    }


def lane_note(m: dict, period: str, now: datetime) -> str:
    fm = {
        "type": "lane-metric", "lane": m["lane"], "period": period,
        "trust_score": m["trust_score"], "band": m["band"],
        "deny_rate": m["deny_rate"], "success_rate": m["success_rate"],
        "retry_rate": m["retry_rate"], "drift_incidents": m["drift_incidents"],
        "accepted": m["accepted"], "edited": m["edited"], "rejected": m["rejected"],
        "accept_ratio": m["accept_ratio"], "decision_time_min": m["decision_time_min"],
        "cost": m["cost"], "tokens_in": m["tokens_in"], "tokens_out": m["tokens_out"],
        "consistency_passk": m["consistency_passk"],
        "samples": m["samples"], "computed_at": now.strftime("%Y-%m-%dT%H:%M:%SZ"),
    }
    lines = ["---"]
    for k, v in fm.items():
        if v is None:
            lines.append(f"{k}: null")
        elif isinstance(v, str):
            lines.append(f'{k}: "{v}"')
        else:
            lines.append(f"{k}: {v}")
    ratio = f" (accept_ratio {m['accept_ratio']})" if m["accept_ratio"] is not None else ""
    dtime = f"{m['decision_time_min']} min (median)" if m["decision_time_min"] is not None else "n/a"
    lines += ["---", "", f"# {m['lane']} — {period}", "",
              f"Trust score **{m['trust_score']}/100** ({m['band']}).", "",
              f"- writes: {m['writes']} (deny {m['denies']}, dry_run {m['dry_runs']})",
              f"- runs: done {m['done']}, blocked {m['blocked']}",
              f"- deny_rate {m['deny_rate']} · success_rate {m['success_rate']} · retry_rate {m['retry_rate']}",
              f"- review: accepted {m['accepted']} / edited {m['edited']} / rejected {m['rejected']}{ratio}",
              f"- decision time: {dtime} · cost: ${m['cost']} · tokens {m['tokens_in']}/{m['tokens_out']}",
              "",
              f"*Computed {fm['computed_at']} — rerunning the aggregator in the "
              f"same period overwrites this note.*", ""]
    if m["band"] == "insufficient-data":
        lines += [f"> Low confidence: only {m['samples']} samples this period "
                  f"(<{LOW_CONFIDENCE_SAMPLES}). Score is indicative, not actionable.", ""]
    return "\n".join(lines)


def aggregate(vault: Path, cards: list[dict], now: datetime | None = None) -> dict:
    now = now or datetime.now(timezone.utc)
    period = iso_period(now)
    audit = read_audit(vault, period)
    board = read_board(cards)
    drift = read_drift(vault, period)
    disp = read_disposition(vault, period)
    cost = read_cost(vault, period)
    dtime = read_decision_time(vault, period)
    outdir = vault / METRICS_RELDIR
    outdir.mkdir(parents=True, exist_ok=True)
    written = []
    for lane in LANES:
        m = compute_lane(lane, audit, board, drift.get(lane, 0), disp, cost, dtime)
        if m is None:
            continue
        (outdir / f"lane-{lane.replace('memoria-', '')}-{period}.md").write_text(
            lane_note(m, period, now), encoding="utf-8")
        written.append({"lane": lane, "trust_score": m["trust_score"], "band": m["band"]})
    verdict_out = None
    if (vault / LINT_RELPATH).is_file():                      # only once the Linter has run
        lv = read_lint_verdict(vault, period)
        (outdir / f"lint-verdict-{period}.md").write_text(
            lint_verdict_note(lv, period, now), encoding="utf-8")
        verdict_out = lv["verdict"]
    return {"period": period, "lanes": written, "verdict": verdict_out}


# --------------------------------------------------------------------------- #
# --------------------------------------------------------------------------- #
def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--vault", help="vault root")
    ap.add_argument("--from-json", type=Path, help="read cards from a JSON file instead of `hermes kanban list --json`")
    args = ap.parse_args()

    if not args.vault:
        ap.error("provide --vault <path>")
    vault = resolve_vault(args.vault)

    sys.path.insert(0, str(Path(__file__).resolve().parent))
    import board_export
    cards = board_export.load_cards(args.from_json)
    print(json.dumps(aggregate(vault, cards), indent=2))


if __name__ == "__main__":
    main()
