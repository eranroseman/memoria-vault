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
import subprocess
import sys
import tempfile
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


def from_pmc(pmcid: str, email: str = "", api_key: str = "") -> str | None:
    """PMCID -> JATS XML -> body text (open-access subset only)."""
    pid = pmcid.upper().replace("PMC", "")
    if not pid.isdigit():
        return None
    params = {"db": "pmc", "id": pid, "rettype": "xml", "email": email}
    if api_key:   # NCBI key raises the E-utilities limit from 3 to 10 req/s
        params["api_key"] = api_key
    q = urllib.parse.urlencode(params)
    xml = _get(f"{PMC_EFETCH}?{q}")
    if not xml:
        return None
    m = re.search(r"<body[ >].*?</body>", xml, re.S)
    if not m:
        return None
    text = re.sub(r"<[^>]+>", " ", m.group(0))
    text = re.sub(r"\s+", " ", text).strip()
    return text or None


# PDF parsing runs in a resource-limited subprocess (ADR-30): a malformed or
# malicious PDF is a known MuPDF CVE surface, so it must not parse in-process where
# a crash, infinite loop, or memory bomb would take down the agent. The child caps
# CPU + address space via rlimit; the parent caps wall-clock and isolates any temp
# files in a throwaway cwd.
PDF_CPU_SECONDS = 60
PDF_AS_BYTES = 4 * 1024 * 1024 * 1024   # 4 GiB address-space ceiling
PDF_WALL_TIMEOUT = 120                  # seconds

_PDF_CHILD = """
import sys, resource
try:
    resource.setrlimit(resource.RLIMIT_CPU, ({cpu}, {cpu}))
    resource.setrlimit(resource.RLIMIT_AS, ({asb}, {asb}))
except (ValueError, OSError):
    pass
import pymupdf4llm
sys.stdout.write(pymupdf4llm.to_markdown(sys.argv[1]))
"""


def from_pdf(path: Path) -> tuple[str | None, str]:
    """Local PDF -> markdown via pymupdf4llm, parsed in a resource-limited
    subprocess (ADR-30 -- MuPDF CVE surface). Returns (text, note)."""
    if not path or not path.is_file():
        return None, "no-pdf"
    child = _PDF_CHILD.format(cpu=PDF_CPU_SECONDS, asb=PDF_AS_BYTES)
    try:
        with tempfile.TemporaryDirectory() as td:
            proc = subprocess.run(
                [sys.executable, "-c", child, str(path)],
                capture_output=True, encoding="utf-8", errors="replace",
                timeout=PDF_WALL_TIMEOUT, cwd=td,
            )
    except subprocess.TimeoutExpired:
        return None, "pdf-timeout"
    except OSError as e:
        return None, f"pdf-spawn-error:{type(e).__name__}"
    if proc.returncode == 0:
        return proc.stdout, "pymupdf4llm"
    stderr = proc.stderr or ""
    if "ModuleNotFoundError" in stderr and "pymupdf4llm" in stderr:
        return None, "pymupdf4llm-not-installed"
    if proc.returncode < 0:                 # killed by a signal (rlimit / OOM / crash)
        return None, f"pdf-resource-exceeded:sig{-proc.returncode}"
    last = stderr.strip().splitlines()[-1] if stderr.strip() else ""
    print(f"[extract] PDF parse failed for {path}: rc={proc.returncode}: {last}",
          file=sys.stderr)
    return None, f"pdf-error:rc{proc.returncode}"


def extract(ids: dict, pdf_path: str | None = None, email: str = "", api_key: str = "") -> dict:
    """Try the tiers in order; return the first usable extract + provenance."""
    # 1. PMC (pre-extracted)
    if ids.get("pmcid"):
        t = from_pmc(ids["pmcid"], email, api_key)
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
def main() -> int:
    import argparse
    ap = argparse.ArgumentParser(description="Tier-1 full-text extraction (ADR-30)")
    ap.add_argument("--pmcid", default="")
    ap.add_argument("--pdf")
    ap.add_argument("--email", default="")
    ap.add_argument("--api-key", default="", help="NCBI E-utilities key (10 req/s vs 3)")
    a = ap.parse_args()
    r = extract({"pmcid": a.pmcid}, a.pdf, a.email, a.api_key)
    r_preview = {**r, "text": (r["text"][:300] + "...") if len(r.get("text", "")) > 300 else r.get("text", "")}
    print(json.dumps(r_preview, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
