#!/usr/bin/env python3
"""verify_mcp.py — retraction lookup by DOI, exposed as an MCP tool.

The Verifier's capability allowlist disables code_execution / terminal, so the
worker agent cannot make the HTTP calls itself. Retraction status therefore
reaches the agent the same way vault access and the policy gate do — over **MCP**.

No mature off-the-shelf MCP covers retraction-by-DOI (Retraction Watch's only MCP
is an unproven solo repo; Open Retractions is stale; CrossRef's `update-to` flags
are exposed by no server), so this thin, pure-stdlib server fills the gap with two
corroborating sources:

  - CrossRef   GET https://api.crossref.org/works/{doi}
               -> message.update-to[] (type: retraction) + message.relation.is-retracted-by
               (real-time, key-less; the authoritative publisher signal)
  - Open Retractions  GET https://openretractions.com/api/doi/{doi}/data.json
               -> .retracted (a stale-but-independent cross-check; data ~2020)

The tool is **deterministic and read-only** — HTTP GET + field inspection + boolean
combine. It writes nothing and never flips a note; the agent reports the verdict and
the human decides (flag-don't-fix). It uses only the stdlib (urllib), so the
self-test runs offline against fixtures with no `mcp` package or network.

    python verify_mcp.py --serve        # run the server over stdio
    python verify_mcp.py --self-test    # offline fixture tests; no mcp pkg, no network
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import urllib.error
import urllib.request

CROSSREF_URL = "https://api.crossref.org/works/{doi}"
OPEN_RETRACTIONS_URL = "https://openretractions.com/api/doi/{doi}/data.json"
TIMEOUT = 12


def _contact() -> str:
    """Polite-pool contact for CrossRef (optional). Reused from the vault env."""
    return (os.environ.get("MEMORIA_CONTACT_EMAIL")
            or os.environ.get("CROSSREF_MAILTO")
            or os.environ.get("NCBI_EMAIL") or "")


def _get_json(url: str) -> tuple[int, dict | None, str | None]:
    """GET a URL, return (status, parsed_json_or_None, error_or_None). Stdlib only."""
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
# Pure parsers (deterministic; unit-tested offline)                           #
# --------------------------------------------------------------------------- #
def _date_parts_to_iso(dp: dict) -> str | None:
    parts = (dp or {}).get("date-parts") or [[]]
    p = parts[0] if parts else []
    if not p:
        return None
    return "-".join(f"{int(x):02d}" if i else str(int(x)) for i, x in enumerate(p))


def crossref_retraction(message: dict) -> dict:
    """Inspect a CrossRef work `message` for retraction signals. Returns a
    {retracted, retraction_doi, date, via} verdict (retracted is True/False)."""
    for upd in message.get("update-to", []) or []:
        if "retraction" in str(upd.get("type", "")).lower():
            return {"retracted": True, "retraction_doi": upd.get("DOI"),
                    "date": _date_parts_to_iso(upd.get("updated", {})), "via": "update-to"}
    relation = message.get("relation", {}) or {}
    rb = relation.get("is-retracted-by") or relation.get("is_retracted_by")
    if rb:
        first = rb[0] if isinstance(rb, list) and rb else {}
        return {"retracted": True, "retraction_doi": first.get("id"),
                "date": None, "via": "relation"}
    return {"retracted": False, "retraction_doi": None, "date": None, "via": None}


def open_retractions_verdict(status: int, data: dict | None) -> dict:
    """Map an Open Retractions response to {retracted, date, retraction_doi}.
    404 = the DOI is unknown to OR (treat as not-retracted-per-this-source)."""
    if status == 404:
        return {"retracted": False, "date": None, "retraction_doi": None}
    if status and 200 <= status < 300 and isinstance(data, dict):
        retracted = bool(data.get("retracted"))
        return {"retracted": retracted,
                "date": (data.get("retractions") or [{}])[0].get("date") if retracted else None,
                "retraction_doi": (data.get("retractions") or [{}])[0].get("doi") if retracted else None}
    return {"retracted": None, "date": None, "retraction_doi": None}


def combine(doi: str, cr: dict | None, cr_err: str | None,
            orr: dict | None, orr_err: str | None) -> dict:
    """Combine the two source verdicts into one deterministic result."""
    cr_r = cr.get("retracted") if cr else None
    or_r = orr.get("retracted") if orr else None
    votes = [v for v in (cr_r, or_r) if v is not None]
    if not votes:
        overall, agreement = None, "no-data"
    elif any(votes):
        overall = True
        agreement = "agree" if all(votes) else "disagree"  # disagree = one source missed it
    else:
        overall = False
        agreement = "agree" if len(votes) == 2 else "single-source"

    retraction_doi = (cr or {}).get("retraction_doi") or (orr or {}).get("retraction_doi")
    date = (cr or {}).get("date") or (orr or {}).get("date")
    return {
        "doi": doi,
        "retracted": overall,                 # True / False / None(unknown)
        "agreement": agreement,
        "retraction_doi": retraction_doi,
        "retraction_date": date,
        "sources": {
            "crossref": {"checked": cr is not None, "error": cr_err, **(cr or {})},
            "open_retractions": {"checked": orr is not None, "error": orr_err, **(orr or {})},
        },
        "note": _summary(doi, overall, agreement),
    }


def _summary(doi: str, overall: bool | None, agreement: str) -> str:
    if overall is True:
        base = f"{doi} is RETRACTED"
        return base + (" (both sources agree)" if agreement == "agree"
                       else " (flagged by one source; cross-check disagrees — verify before acting)")
    if overall is False:
        return f"{doi}: no retraction found" + (" (both sources)" if agreement == "agree" else " (single source)")
    return f"{doi}: retraction status UNKNOWN — both sources errored; do not assume clean"


def check_doi(doi: str) -> dict:
    """Fetch both sources for a DOI and return the combined verdict. Read-only."""
    doi = (doi or "").strip().removeprefix("https://doi.org/").removeprefix("doi:").strip()
    if not doi:
        return {"error": "no-doi", "note": "pass a non-empty DOI"}
    cr_status, cr_json, cr_err = _get_json(CROSSREF_URL.format(doi=doi))
    cr = crossref_retraction(cr_json["message"]) if cr_json and "message" in cr_json else None
    if cr is None and cr_err is None and cr_status == 404:
        cr_err = "doi-not-in-crossref"
    or_status, or_json, or_err = _get_json(OPEN_RETRACTIONS_URL.format(doi=doi))
    orr = open_retractions_verdict(or_status, or_json) if or_err is None else None
    return combine(doi, cr, cr_err, orr, or_err)


def build_server():
    """Wrap check_doi as an MCP server. mcp imported lazily so self-test needs no pkg."""
    from mcp.server.fastmcp import FastMCP  # type: ignore

    server = FastMCP("memoria-verify")

    @server.tool()
    def retraction_check(doi: str) -> dict:
        """Check whether a DOI has been retracted, using CrossRef (update-to /
        is-retracted-by) and Open Retractions as corroborating sources. Returns a
        deterministic verdict {retracted: true|false|null, agreement, retraction_doi,
        retraction_date, sources}. Read-only — reports only; never flips a note's
        pub_status. `retracted: null` means both sources errored (status unknown)."""
        return check_doi(doi)

    return server


# --------------------------------------------------------------------------- #
# Self-test — offline, fixtures only                                          #
# --------------------------------------------------------------------------- #
def self_test() -> int:
    cr_upd = {"update-to": [{"type": "retraction", "DOI": "10.1/retraction",
                             "updated": {"date-parts": [[2021, 5, 3]]}}]}
    cr_rel = {"relation": {"is-retracted-by": [{"id-type": "doi", "id": "10.1/rb"}]}}
    cr_clean = {"title": ["A fine paper"]}

    checks = [
        ("crossref update-to → retracted", crossref_retraction(cr_upd)["retracted"] is True),
        ("crossref update-to → date parsed", crossref_retraction(cr_upd)["date"] == "2021-05-03"),
        ("crossref relation → retracted via relation",
         crossref_retraction(cr_rel) == {"retracted": True, "retraction_doi": "10.1/rb", "date": None, "via": "relation"}),
        ("crossref clean → not retracted", crossref_retraction(cr_clean)["retracted"] is False),
        ("open-retractions 404 → not retracted", open_retractions_verdict(404, None)["retracted"] is False),
        ("open-retractions 200 retracted → True",
         open_retractions_verdict(200, {"retracted": True, "retractions": [{"date": "2020-01-01", "doi": "10.1/r"}]})["retracted"] is True),
        ("open-retractions error → unknown(None)", open_retractions_verdict(0, None)["retracted"] is None),
        # combine logic
        ("combine both-clean → False/agree",
         (lambda r: r["retracted"] is False and r["agreement"] == "agree")(
             combine("10.1/x", {"retracted": False}, None, {"retracted": False}, None))),
        ("combine one-retracted → True/disagree",
         (lambda r: r["retracted"] is True and r["agreement"] == "disagree")(
             combine("10.1/x", {"retracted": True, "retraction_doi": "10.1/r"}, None, {"retracted": False}, None))),
        ("combine both-retracted → True/agree",
         (lambda r: r["retracted"] is True and r["agreement"] == "agree")(
             combine("10.1/x", {"retracted": True}, None, {"retracted": True}, None))),
        ("combine no-data → None/no-data",
         (lambda r: r["retracted"] is None and r["agreement"] == "no-data")(
             combine("10.1/x", None, "err", None, "err"))),
        ("combine single-source clean → False/single-source",
         (lambda r: r["retracted"] is False and r["agreement"] == "single-source")(
             combine("10.1/x", {"retracted": False}, None, None, "err"))),
    ]
    bad = [n for n, ok in checks if not ok]
    for n, ok in checks:
        print(f"  {'PASS' if ok else 'FAIL'}  {n}")
    print(f"\n{'OK' if not bad else f'{len(bad)} FAILING'}: verify_mcp.py self-test ({len(checks)} checks)")
    return 1 if bad else 0


def main() -> None:
    ap = argparse.ArgumentParser(description="Retraction lookup (CrossRef + Open Retractions) as an MCP server")
    ap.add_argument("--serve", action="store_true", help="run the MCP server over stdio")
    ap.add_argument("--self-test", action="store_true", help="run offline fixture tests and exit")
    ap.add_argument("--doi", help="one-off CLI lookup (makes live HTTP calls)")
    args = ap.parse_args()
    if args.self_test:
        sys.exit(1 if self_test() else 0)
    if args.doi:
        print(json.dumps(check_doi(args.doi), indent=2))
        return
    if args.serve:
        build_server().run()
        return
    ap.error("pass --serve, --self-test, or --doi <doi>")


if __name__ == "__main__":
    main()
