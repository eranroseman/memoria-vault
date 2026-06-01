#!/usr/bin/env python3
"""Metrics aggregator -- roll fleet run-history + audit into lane-metric notes.

Writes `00-meta/08-metrics/lane-<lane>-<period>.md` (one per lane per ISO week),
which the [fleet-health dashboard] reads for the per-lane **trust score** (0-100).

Inputs (all best-effort -- missing sources degrade gracefully):
  - 00-meta/02-logs/audit.jsonl          deny rate (policy-MCP decisions, this period)
  - Hermes board (`hermes kanban list --json`)   success rate + retry rate per lane
  - 00-meta/02-logs/lint-findings.jsonl  drift incidents (Linter), if present

Trust score (glossary "Trust score"): combines audit **deny rate**, **retry rate**,
**success rate**, **drift incidents**, **secret hits**, and accept/reject ratios;
bands **90+ healthy / 70-89 watch / <70 act**. The docs pin the inputs and bands
but NOT the weights, so the composition below is Memoria's own -- documented and
tunable at the top of the file. The CRS-shaped `pass^k` consistency target needs
repeated-run data per task and is a TODO (noted in the dashboard design).

    python metrics_aggregate.py --vault <path>                 # reads `hermes kanban list --json`
    python metrics_aggregate.py --vault <path> --from-json cards.json
    python metrics_aggregate.py --self-test

[fleet-health dashboard]: docs/explanation/dashboards/fleet-health.md
"""
from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

METRICS_RELDIR = "00-meta/08-metrics"
AUDIT_RELPATH = "00-meta/02-logs/audit.jsonl"
LINT_RELPATH = "00-meta/02-logs/lint-findings.jsonl"
DISPOSITION_RELPATH = "00-meta/02-logs/disposition.jsonl"        # accept | edit | reject per review
COST_RELPATH = "00-meta/02-logs/cost.jsonl"                      # API spend + tokens per card
TRANSITIONS_RELPATH = "00-meta/02-logs/board-transitions.jsonl"  # status/review transitions (for decision time)
TERMINAL_REVIEW = frozenset({"approved", "rejected", "changes-requested"})
MUTATING = frozenset({"write", "append", "move", "delete", "mkdir", "auto_fix"})
LANES = ("memoria-librarian", "memoria-mapper", "memoria-socratic", "memoria-writer",
         "memoria-verifier", "memoria-coder", "memoria-linter")
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


def _parse_ts(s: str) -> datetime | None:
    try:
        return datetime.fromisoformat(str(s).replace("Z", "+00:00"))
    except (ValueError, TypeError):
        return None


def read_audit(vault: Path, period: str) -> dict[str, dict]:
    """Per-profile mutating-decision counts for `period` from audit.jsonl."""
    out: dict[str, dict] = {}
    audit = vault / AUDIT_RELPATH
    if not audit.is_file():
        return out
    for line in audit.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            e = json.loads(line)
        except json.JSONDecodeError:
            continue
        if e.get("action") not in MUTATING:
            continue
        ts = _parse_ts(e.get("timestamp", ""))
        if ts is None or iso_period(ts) != period:
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
    lint = vault / LINT_RELPATH
    if not lint.is_file():
        return out
    for line in lint.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            e = json.loads(line)
        except json.JSONDecodeError:
            continue
        ts = _parse_ts(e.get("timestamp", ""))
        if ts is not None and iso_period(ts) != period:
            continue
        lane = e.get("lane") or e.get("profile") or "fleet"
        out[lane] = out.get(lane, 0) + 1
    return out


def _iter_jsonl(vault: Path, relpath: str, period: str | None):
    """Yield JSON rows from a JSONL log, filtered to `period` (None = all)."""
    p = vault / relpath
    if not p.is_file():
        return
    for line in p.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            e = json.loads(line)
        except json.JSONDecodeError:
            continue
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
              ""]
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
    return {"period": period, "lanes": written}


# --------------------------------------------------------------------------- #
def self_test() -> int:
    import tempfile

    failures = 0

    def check(name: str, cond: bool) -> None:
        nonlocal failures
        failures += not cond
        print(f"  {'PASS' if cond else 'FAIL'}  {name}")

    # trust-score math + bands
    check("clean lane -> healthy 100", trust_score(0, 0, 1.0) == (100, "healthy"))
    check("high deny -> act band", trust_score(0.8, 0, 1.0)[1] == "act")
    s_watch, b_watch = trust_score(0.0, 0.0, 0.8)               # 100 - 40*0.2 = 92? -> healthy
    check("20% failure -> 92 healthy", (s_watch, b_watch) == (92, "healthy"))
    check("50% failure -> watch", trust_score(0.0, 0.0, 0.5)[1] == "watch")
    check("rubber-stamp down-weight", trust_score(0, 0, 1.0, accept_ratio=0.95)[0] == 90)

    now = datetime(2026, 5, 28, tzinfo=timezone.utc)            # 2026-W22
    period = iso_period(now)
    check("iso_period format", period == "2026-W22")

    with tempfile.TemporaryDirectory() as td:
        vault = Path(td)
        (vault / "00-meta" / "02-logs").mkdir(parents=True)
        # audit: writer made 6 writes, 1 deny, this period
        audit_lines = []
        for i in range(5):
            audit_lines.append(json.dumps({"timestamp": "2026-05-28T10:00:00Z",
                                           "profile": "memoria-writer", "action": "write", "decision": "allow"}))
        audit_lines.append(json.dumps({"timestamp": "2026-05-28T10:00:00Z",
                                       "profile": "memoria-writer", "action": "write", "decision": "deny"}))
        # an out-of-period entry that must be ignored
        audit_lines.append(json.dumps({"timestamp": "2026-01-01T10:00:00Z",
                                       "profile": "memoria-writer", "action": "write", "decision": "deny"}))
        (vault / AUDIT_RELPATH).write_text("\n".join(audit_lines), encoding="utf-8")

        cards = [
            {"task_id": "t1", "status": "done", "assignee": "memoria-writer", "metadata": {"retry_count": 1}},
            {"task_id": "t2", "status": "done", "assignee": "memoria-writer"},
            {"task_id": "t3", "status": "blocked", "assignee": "memoria-writer"},
            {"task_id": "t4", "status": "running", "assignee": "memoria-linter"},  # no done/blocked, no audit -> skipped
        ]

        res = aggregate(vault, cards, now=now)
        check("aggregated the writer lane", any(l["lane"] == "memoria-writer" for l in res["lanes"]))
        check("inactive lane skipped", not any(l["lane"] == "memoria-mapper" for l in res["lanes"]))
        note = (vault / METRICS_RELDIR / "lane-writer-2026-W22.md").read_text(encoding="utf-8")
        check("lane note has type: lane-metric", "type: \"lane-metric\"" in note)
        check("deny_rate computed in-period only (1/6)", "deny_rate: 0.167" in note)
        check("success_rate 2/3", "success_rate: 0.667" in note)
        check("note has trust_score frontmatter", "trust_score:" in note)

    # --- new telemetry: disposition, cost, decision-time --------------------
    with tempfile.TemporaryDirectory() as td:
        vault = Path(td)
        logs = vault / "00-meta" / "02-logs"
        logs.mkdir(parents=True)
        disp_rows = ([{"timestamp": "2026-05-28T10:00:00Z", "lane": "memoria-writer", "disposition": "accepted"}] * 3
                     + [{"timestamp": "2026-05-28T10:00:00Z", "lane": "memoria-writer", "disposition": "edited"}]
                     + [{"timestamp": "2026-05-28T10:00:00Z", "lane": "memoria-writer", "disposition": "rejected"}]
                     + [{"timestamp": "2026-01-01T00:00:00Z", "lane": "memoria-writer", "disposition": "accepted"}])  # out-of-period
        (logs / "disposition.jsonl").write_text("\n".join(json.dumps(r) for r in disp_rows), encoding="utf-8")
        d = read_disposition(vault, period)
        check("disposition counts in-period only", d["memoria-writer"] == {"accepted": 3, "edited": 1, "rejected": 1})
        check("accept_ratio 3/5", round(accept_ratio_of(d["memoria-writer"]), 2) == 0.6)

        (logs / "cost.jsonl").write_text("\n".join(json.dumps(r) for r in [
            {"timestamp": "2026-05-28T10:00:00Z", "lane": "memoria-writer", "cost": 0.10, "tokens_in": 100, "tokens_out": 200},
            {"timestamp": "2026-05-28T11:00:00Z", "lane": "memoria-writer", "cost": 0.30, "tokens_in": 50, "tokens_out": 80},
        ]), encoding="utf-8")
        c = read_cost(vault, period)
        check("cost summed per lane", round(c["memoria-writer"]["cost"], 2) == 0.40 and c["memoria-writer"]["tokens_out"] == 280)

        (logs / "board-transitions.jsonl").write_text("\n".join(json.dumps(r) for r in [
            {"timestamp": "2026-05-28T10:00:00Z", "task_id": "x", "lane": "memoria-writer", "kind": "review", "from": "unreviewed", "to": "requested"},
            {"timestamp": "2026-05-28T10:30:00Z", "task_id": "x", "lane": "memoria-writer", "kind": "review", "from": "requested", "to": "approved"},
        ]), encoding="utf-8")
        check("decision time 30 min", read_decision_time(vault, period).get("memoria-writer") == 30.0)

        aggregate(vault, [], now=now)   # disposition alone (5 reviews) yields enough samples
        note = (vault / METRICS_RELDIR / "lane-writer-2026-W22.md").read_text(encoding="utf-8")
        check("note carries accept_ratio", "accept_ratio: 0.6" in note)
        check("note carries decision_time_min", "decision_time_min: 30.0" in note)
        check("note carries cost", "cost: 0.4" in note)
        check("note carries pass^k null placeholder", "consistency_passk: null" in note)

    print(f"\n{'OK' if not failures else 'FAILED'}: {failures} failing check(s).")
    return failures


# --------------------------------------------------------------------------- #
def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--vault", help="vault root")
    ap.add_argument("--from-json", type=Path, help="read cards from a JSON file instead of `hermes kanban list --json`")
    ap.add_argument("--self-test", action="store_true")
    args = ap.parse_args()

    if args.self_test:
        sys.exit(1 if self_test() else 0)
    if not args.vault:
        ap.error("provide --vault <path> or --self-test")
    vault = Path(args.vault).expanduser().resolve()
    if not vault.is_dir():
        sys.exit(f"not a directory: {vault}")

    sys.path.insert(0, str(Path(__file__).resolve().parent))
    import board_export
    cards = board_export.load_cards(args.from_json)
    print(json.dumps(aggregate(vault, cards), indent=2))


if __name__ == "__main__":
    main()
