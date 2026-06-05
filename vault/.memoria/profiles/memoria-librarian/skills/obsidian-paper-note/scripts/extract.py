#!/usr/bin/env python3
"""extract.py — Tier-1 full-text extraction (ADR-30).

Pre-extracted-first, parse-last. For a capture you always hold the local PDF, so
the tiers are tried in order:

    PMC (PMCID -> JATS full text, pre-extracted, no key)
    -> local Zotero PDF -> pymupdf4llm (markdown)
    -> [OCR / CORE / Unpaywall — follow-ups]

The OCR/usability decision is the **script's**, not the LLM's: a deterministic
text-layer + coherence check (chars/page, replacement-char ratio, word ratio)
gatekeeps so only good text reaches the model. The coherence heuristic is
English-biased — non-English text must not be auto-failed (flagged, not dropped).

Returns the extract text + which tier produced it + a `degraded` flag; does NOT
write to the vault. `pymupdf4llm` is imported lazily so the module loads (and
self-tests) without it.
"""
from __future__ import annotations

import json
import re
import sys
import urllib.parse
import urllib.request
from pathlib import Path

PMC_EFETCH = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi"
MIN_CHARS_PER_PAGE = 200       # below this a "PDF" is likely scanned / no text layer
MIN_WORD_RATIO = 0.55          # fraction of tokens that look like words
MAX_REPLACEMENT_RATIO = 0.02   # U+FFFD / control-char soup => garbled


def coherence(text: str, pages: int = 1) -> dict:
    """Deterministic text-layer + coherence check. Returns {ok, reason, ...}."""
    n = len(text)
    if n == 0:
        return {"ok": False, "reason": "empty", "chars": 0}
    repl = (text.count("�") + sum(c < " " and c not in "\n\r\t" for c in text)) / n
    tokens = re.findall(r"[^\W\d_]{2,}", text, re.UNICODE)  # word-ish tokens (unicode letters)
    word_ratio = (len(tokens) and
                  sum(1 for t in tokens if len(t) <= 30) / len(tokens)) or 0.0
    chars_per_page = n / max(pages, 1)
    # English-biased word-ratio is advisory: low ratio is "suspect", not auto-fail,
    # unless the text is also tiny or full of replacement chars.
    if chars_per_page < MIN_CHARS_PER_PAGE:
        return {"ok": False, "reason": "too-few-chars", "chars": n, "chars_per_page": round(chars_per_page)}
    if repl > MAX_REPLACEMENT_RATIO:
        return {"ok": False, "reason": "garbled", "chars": n, "replacement_ratio": round(repl, 3)}
    suspect = word_ratio < MIN_WORD_RATIO
    return {"ok": True, "reason": "ok", "chars": n, "word_ratio": round(word_ratio, 2),
            "suspect_nonenglish_or_garbled": suspect}


def _get(url: str, timeout: int = 25) -> str | None:
    try:
        with urllib.request.urlopen(url, timeout=timeout) as r:
            return r.read().decode("utf-8", errors="ignore")
    except Exception as exc:
        print(f"[extract] GET {url}: {type(exc).__name__}: {exc}", file=sys.stderr)
        return None


def from_pmc(pmcid: str, email: str = "") -> str | None:
    """PMCID -> JATS XML -> body text (open-access subset only)."""
    pid = pmcid.upper().replace("PMC", "")
    if not pid.isdigit():
        return None
    q = urllib.parse.urlencode({"db": "pmc", "id": pid, "rettype": "xml", "email": email})
    xml = _get(f"{PMC_EFETCH}?{q}")
    if not xml:
        return None
    m = re.search(r"<body[ >].*?</body>", xml, re.S)
    if not m:
        return None
    text = re.sub(r"<[^>]+>", " ", m.group(0))
    text = re.sub(r"\s+", " ", text).strip()
    return text or None


def from_pdf(path: Path) -> tuple[str | None, str]:
    """Local PDF -> markdown via pymupdf4llm (lazy import). Returns (text, note)."""
    if not path or not path.is_file():
        return None, "no-pdf"
    try:
        import pymupdf4llm
    except ImportError:
        return None, "pymupdf4llm-not-installed"
    try:
        return pymupdf4llm.to_markdown(str(path)), "pymupdf4llm"
    except Exception as e:
        print(f"[extract] PDF parse failed for {path}: {type(e).__name__}: {e}",
              file=sys.stderr)
        return None, f"pdf-error:{type(e).__name__}:{e}"


def extract(ids: dict, pdf_path: str | None = None, email: str = "") -> dict:
    """Try the tiers in order; return the first usable extract + provenance."""
    # 1. PMC (pre-extracted)
    if ids.get("pmcid"):
        t = from_pmc(ids["pmcid"], email)
        if t:
            c = coherence(t, pages=max(1, len(t) // 3000))
            if c["ok"]:
                return {"text": t, "source": "pmc", "chars": c["chars"], "degraded": False, "coherence": c}
    # 2. local Zotero PDF -> pymupdf4llm
    if pdf_path:
        t, note = from_pdf(Path(pdf_path))
        if t:
            c = coherence(t, pages=max(1, t.count("\f") + 1))
            return {"text": t if c["ok"] else "", "source": "pymupdf4llm" if c["ok"] else "needs-ocr",
                    "chars": c["chars"], "degraded": not c["ok"], "coherence": c, "note": note}
    # 3. nothing usable -> degraded (abstract-only ingest downstream)
    return {"text": "", "source": "none", "chars": 0, "degraded": True,
            "coherence": {"ok": False, "reason": "no-source"}}


# --------------------------------------------------------------------------- #
def _self_test() -> int:
    good = ("This is a perfectly ordinary paragraph of English prose describing a "
            "study, its methods, and the results obtained over a long evaluation. ") * 6
    garbled = "�� ab � cd � " * 80
    tiny = "short."
    checks = [
        ("coherent prose -> ok", coherence(good, pages=1)["ok"]),
        ("garbled -> not ok (garbled)", coherence(garbled, pages=1)["reason"] == "garbled"),
        ("tiny -> not ok (too-few-chars)", coherence(tiny, pages=1)["reason"] == "too-few-chars"),
        ("empty -> not ok (empty)", coherence("", pages=1)["reason"] == "empty"),
        ("no source & no pdf -> degraded", extract({}, None)["degraded"] is True
         and extract({}, None)["source"] == "none"),
        ("missing pdf path -> from_pdf no-pdf", from_pdf(Path("/no/such.pdf"))[1] == "no-pdf"),
    ]
    bad = [n for n, ok in checks if not ok]
    for n, ok in checks:
        print(f"  {'PASS' if ok else 'FAIL'}  {n}")
    print(f"\n{'OK' if not bad else f'{len(bad)} FAILING'}: extract.py self-test")
    return 1 if bad else 0


def main() -> int:
    import argparse
    ap = argparse.ArgumentParser(description="Tier-1 full-text extraction (ADR-30)")
    ap.add_argument("--pmcid", default="")
    ap.add_argument("--pdf")
    ap.add_argument("--email", default="")
    ap.add_argument("--self-test", action="store_true")
    a = ap.parse_args()
    if a.self_test:
        return _self_test()
    r = extract({"pmcid": a.pmcid}, a.pdf, a.email)
    r_preview = {**r, "text": (r["text"][:300] + "...") if len(r.get("text", "")) > 300 else r.get("text", "")}
    print(json.dumps(r_preview, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
