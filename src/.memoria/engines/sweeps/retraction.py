#!/usr/bin/env python3
"""retraction.py — the retraction sweep engine (ADR-46/D41: cron-only, no MCP facade).

The Verifier reaches every external service over MCP (code_execution / terminal /
web are disabled on the lane), so retraction status arrives the same way vault
access and the policy gate do — over **MCP**, gated and audited.

No mature off-the-shelf MCP covers retraction-by-DOI, so this thin, pure-stdlib
server fills the gap with three sources, most-authoritative first:

  1. Retraction Watch DB — the authoritative dataset, Crossref-owned and freely
     distributed as a CSV (gitlab.com/crossref/retraction-watch-data, CC). Loaded
     locally and indexed by OriginalPaperDOI; complete, offline, deterministic.
     `--refresh` downloads/refreshes the CSV (run it on a cron).
  2. CrossRef API  GET https://api.crossref.org/works/{doi}
     -> message.update-to[] (type: retraction) + message.relation.is-retracted-by.
     Real-time delta: catches retractions newer than the local CSV snapshot.
  3. Open Retractions  GET https://openretractions.com/api/doi/{doi}/data.json
     -> .retracted (an independent cross-check; data ~2020).

The tool is **deterministic and read-only** — index/HTTP lookup + boolean combine.
It writes nothing and never flips a note; the agent reports the verdict and the
human decides (flag-don't-fix). Stdlib only (urllib, csv), so the self-test runs
offline against fixtures with no `mcp` package and no network. If the RW CSV is
absent the server still works, degraded to the two live-API sources.

    python retraction.py --refresh               # download/refresh the RW CSV
    python retraction.py --doi 10.x/y            # one-off CLI lookup (live)
    python retraction.py --sweep --vault V       # scan catalog DOIs; alert on retractions
"""
from __future__ import annotations

import argparse
import csv
import re
import json
import os
import sys
import urllib.error
import urllib.request
from pathlib import Path

CROSSREF_URL = "https://api.crossref.org/works/{doi}"
OPEN_RETRACTIONS_URL = "https://openretractions.com/api/doi/{doi}/data.json"
RW_CSV_URL = "https://gitlab.com/crossref/retraction-watch-data/-/raw/main/retraction_watch.csv"
TIMEOUT = 12

_RW_INDEX: dict[str, dict] | None = None  # module-level cache, keyed by normalized DOI


# --------------------------------------------------------------------------- #
# Helpers                                                                      #
# --------------------------------------------------------------------------- #
def normalize_doi(doi: str) -> str:
    return ((doi or "").strip().removeprefix("https://doi.org/")
            .removeprefix("http://doi.org/").removeprefix("doi:").strip().lower())


def _contact() -> str:
    return (os.environ.get("MEMORIA_CONTACT_EMAIL")
            or os.environ.get("CROSSREF_MAILTO")
            or os.environ.get("NCBI_EMAIL") or "")


def rw_csv_path() -> Path:
    raw = (os.environ.get("MEMORIA_RW_CSV")
           or os.environ.get("OBSIDIAN_VAULT_PATH", "") + "/.memoria/data/retraction_watch.csv")
    return Path(raw).expanduser()


def _get_json(url: str) -> tuple[int, dict | None, str | None]:
    contact = _contact()
    ua = f"memoria-verify/1.0 (mailto:{contact})" if contact else "memoria-verify/1.0"
    req = urllib.request.Request(url, headers={"User-Agent": ua, "Accept": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=TIMEOUT) as resp:
            return resp.status, json.loads(resp.read().decode("utf-8", "ignore")), None
    except urllib.error.HTTPError as e:
        return e.code, None, None if e.code == 404 else f"http {e.code}"
    except (urllib.error.URLError, TimeoutError, ValueError) as e:
        return 0, None, str(e)


# --------------------------------------------------------------------------- #
# Source 1 — Retraction Watch CSV (authoritative, local)                      #
# --------------------------------------------------------------------------- #
def _nature_retracted(nature: str) -> bool:
    n = (nature or "").lower()
    return "retraction" in n and "reinstatement" not in n  # EoC / Correction are not retractions


def build_rw_index(rows) -> dict[str, dict]:
    """Index RW rows by normalized OriginalPaperDOI. A paper may have several
    records (e.g. an Expression of Concern then a Retraction) — keep the most
    severe (a real Retraction wins over a concern/correction)."""
    index: dict[str, dict] = {}
    for r in rows:
        doi = normalize_doi(r.get("OriginalPaperDOI", ""))
        if not doi or doi == "unavailable":
            continue
        rec = {"retracted": _nature_retracted(r.get("RetractionNature", "")),
               "nature": (r.get("RetractionNature") or "").strip(),
               "date": (r.get("RetractionDate") or "").strip() or None,
               "retraction_doi": normalize_doi(r.get("RetractionDOI", "")) or None}
        prev = index.get(doi)
        if prev is None or (rec["retracted"] and not prev["retracted"]):
            index[doi] = rec
    return index


def load_rw_index(path: Path | None = None) -> dict[str, dict]:
    global _RW_INDEX
    if _RW_INDEX is not None:
        return _RW_INDEX
    path = path or rw_csv_path()
    if not path.is_file():
        _RW_INDEX = {}
        return _RW_INDEX
    with path.open(encoding="utf-8", errors="ignore", newline="") as f:
        _RW_INDEX = build_rw_index(csv.DictReader(f))
    return _RW_INDEX


def rw_lookup(doi: str, path: Path | None = None) -> dict | None:
    """Return {retracted, nature, date, retraction_doi} for a DOI, or None when the
    CSV is absent (so the caller degrades to the live sources)."""
    index = load_rw_index(path)
    if not index:
        return None  # CSV not present -> this source is unavailable, not "clean"
    return index.get(normalize_doi(doi), {"retracted": False, "nature": None,
                                          "date": None, "retraction_doi": None})


def refresh_rw(path: Path | None = None, url: str = RW_CSV_URL) -> int:
    """Download the RW CSV to the local path. Returns row count, or -1 on failure."""
    path = path or rw_csv_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    req = urllib.request.Request(url, headers={"User-Agent": "memoria-verify/1.0"})
    try:
        with urllib.request.urlopen(req, timeout=120) as resp:
            data = resp.read()
    except (urllib.error.URLError, TimeoutError) as e:
        print(f"  refresh FAILED: {e}", file=sys.stderr)
        return -1
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_bytes(data)
    tmp.replace(path)
    n = max(0, data.count(b"\n") - 1)
    print(f"  refreshed {path} ({n} rows, {len(data)//1024} KB)")
    return n


# --------------------------------------------------------------------------- #
# Source 2/3 parsers (deterministic; unit-tested offline)                     #
# --------------------------------------------------------------------------- #
def _date_parts_to_iso(dp: dict) -> str | None:
    parts = (dp or {}).get("date-parts") or [[]]
    p = parts[0] if parts else []
    if not p:
        return None
    return "-".join(f"{int(x):02d}" if i else str(int(x)) for i, x in enumerate(p))


def crossref_retraction(message: dict) -> dict:
    for upd in message.get("update-to", []) or []:
        if "retraction" in str(upd.get("type", "")).lower():
            return {"retracted": True, "retraction_doi": upd.get("DOI"),
                    "date": _date_parts_to_iso(upd.get("updated", {})), "via": "update-to"}
    relation = message.get("relation", {}) or {}
    rb = relation.get("is-retracted-by") or relation.get("is_retracted_by")
    if rb:
        first = rb[0] if isinstance(rb, list) and rb else {}
        return {"retracted": True, "retraction_doi": first.get("id"), "date": None, "via": "relation"}
    return {"retracted": False, "retraction_doi": None, "date": None, "via": None}


def open_retractions_verdict(status: int, data: dict | None) -> dict:
    if status == 404:
        return {"retracted": False, "date": None, "retraction_doi": None}
    if status and 200 <= status < 300 and isinstance(data, dict):
        retracted = bool(data.get("retracted"))
        rs = (data.get("retractions") or [{}])[0]
        return {"retracted": retracted,
                "date": rs.get("date") if retracted else None,
                "retraction_doi": rs.get("doi") if retracted else None}
    return {"retracted": None, "date": None, "retraction_doi": None}


# --------------------------------------------------------------------------- #
# Combine                                                                     #
# --------------------------------------------------------------------------- #
def combine(doi: str, sources: dict[str, dict | None], errors: dict[str, str | None]) -> dict:
    """Combine source verdicts (most-authoritative first) into one result.
    A source contributes a vote only when its `retracted` is True/False (not None)."""
    votes = [v["retracted"] for v in sources.values() if v and v.get("retracted") is not None]
    if not votes:
        overall, agreement = None, "no-data"
    elif any(votes):
        overall = True
        agreement = "agree" if all(votes) else "disagree"  # disagree = a source missed it
    else:
        overall = False
        agreement = "agree" if len(votes) > 1 else "single-source"

    def pick(field):
        for v in sources.values():
            if v and v.get("retracted") and v.get(field):
                return v[field]
        return None

    return {
        "doi": normalize_doi(doi),
        "retracted": overall,                       # True / False / None(unknown)
        "agreement": agreement,
        "nature": pick("nature"),
        "retraction_doi": pick("retraction_doi"),
        "retraction_date": pick("date"),
        "sources": {k: {"checked": v is not None, "error": errors.get(k), **(v or {})}
                    for k, v in sources.items()},
        "note": _summary(doi, overall, agreement),
    }


def _summary(doi: str, overall: bool | None, agreement: str) -> str:
    d = normalize_doi(doi)
    if overall is True:
        return f"{d} is RETRACTED" + (" (sources agree)" if agreement == "agree"
                                      else " (flagged by one source; others disagree — verify before acting)")
    if overall is False:
        return f"{d}: no retraction found" + (" (multiple sources)" if agreement == "agree" else " (single source)")
    return f"{d}: retraction status UNKNOWN — no source returned data; do not assume clean"


def check_doi(doi: str, offline: bool = False) -> dict:
    """Fetch all sources for a DOI and return the combined verdict. Read-only.

    offline=True checks the local Retraction Watch CSV only — the cron-sweep mode
    (no per-DOI HTTP; the monthly --refresh keeps the CSV current)."""
    doi = normalize_doi(doi)
    if not doi:
        return {"error": "no-doi", "note": "pass a non-empty DOI"}
    sources: dict[str, dict | None] = {}
    errors: dict[str, str | None] = {}

    # 1. Retraction Watch (authoritative, local)
    sources["retraction_watch"] = rw_lookup(doi)
    errors["retraction_watch"] = None if sources["retraction_watch"] is not None else "csv-not-loaded"

    if offline:
        return combine(doi, sources, errors)

    # 2. CrossRef (real-time delta)
    cr_status, cr_json, cr_err = _get_json(CROSSREF_URL.format(doi=doi))
    sources["crossref"] = crossref_retraction(cr_json["message"]) if cr_json and "message" in cr_json else None
    errors["crossref"] = cr_err or ("doi-not-in-crossref" if cr_status == 404 else None)

    # 3. Open Retractions (fallback cross-check)
    or_status, or_json, or_err = _get_json(OPEN_RETRACTIONS_URL.format(doi=doi))
    sources["open_retractions"] = open_retractions_verdict(or_status, or_json) if or_err is None else None
    errors["open_retractions"] = or_err

    return combine(doi, sources, errors)



def sweep(vault: Path, offline: bool = True) -> dict:
    """Scan catalog paper/dataset DOIs against the local RW CSV; raise an Inbox
    `alert` for each retracted work (the writing half of the sweep engine)."""
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "lib"))
    import inbox as inbox_writer

    fm_re = re.compile(r"^---\n(.*?)\n---", re.S)
    doi_re = re.compile(r"^doi:\s*[\"']?([^\"'\n]+)", re.M)
    ck_re = re.compile(r"^citekey:\s*[\"']?([^\"'\n]+)", re.M)
    checked = hits = 0
    for folder in ("catalog/papers", "catalog/datasets"):
        d = vault / folder
        if not d.is_dir():
            continue
        for note in sorted(d.glob("*.md")):
            m = fm_re.match(note.read_text(encoding="utf-8"))
            if not m:
                continue
            doi_m = doi_re.search(m.group(1))
            if not doi_m or not doi_m.group(1).strip():
                continue
            checked += 1
            result = check_doi(doi_m.group(1).strip(), offline=offline)
            if result.get("retracted"):
                hits += 1
                ck = (ck_re.search(m.group(1)) or [None, ""])[1]
                inbox_writer.write_finding(
                    vault, "alert", f"Retraction: {note.stem}",
                    f"DOI {doi_m.group(1).strip()} is retracted "
                    f"({result.get('nature') or 'see retraction record'}); claims citing it "
                    "need re-adjudication.",
                    raised_by="sweep", agent_recommendation="issues-found",
                    target=f"{folder}/{note.name}", citekey=ck, loudness="alert")
    return {"checked": checked, "retracted": hits}


def main() -> None:
    ap = argparse.ArgumentParser(description="Retraction sweep engine (Retraction Watch CSV + CrossRef + Open Retractions)")
    ap.add_argument("--refresh", action="store_true", help="download/refresh the Retraction Watch CSV and exit")
    ap.add_argument("--doi", help="one-off CLI lookup (makes live HTTP calls)")
    ap.add_argument("--sweep", action="store_true", help="scan catalog DOIs; write Inbox alerts for retracted works")
    ap.add_argument("--vault", type=Path, help="vault root (for --sweep)")
    ap.add_argument("--offline", action="store_true", default=True,
                    help="local RW CSV only — the cron default")
    args = ap.parse_args()
    if args.refresh:
        sys.exit(0 if refresh_rw() >= 0 else 1)
    if args.doi:
        print(json.dumps(check_doi(args.doi), indent=2))
        return
    if args.sweep:
        if not args.vault:
            ap.error("--sweep needs --vault")
        print(json.dumps(sweep(args.vault, offline=args.offline)))
        return
    ap.error("pass --refresh, --doi <doi>, or --sweep --vault <path>")


if __name__ == "__main__":
    main()
