#!/usr/bin/env python3
"""§0 frozen-model probe — does frozen qwen2.5:7b clear Memoria's extraction tasks,
or is CrossTrace's "~0% structural compliance" real for us? (adjudicates the QLoRA budget)

Needs Ollama running locally with qwen2.5:7b. No Python deps (urllib).
  python3 probe-qwen-compliance.py            # abstracts (default)
  python3 probe-qwen-compliance.py --body     # full-body passages (the harder re-test the doc asks for)

RESULTS (alpha.9, abstracts): aspect extraction 6/6 clean JSON (Ollama format=schema);
verbatim warrant quotes 18/20 = 90% are exact substrings (§3.2's checker rejects the rest).
=> CrossTrace's 0% does not reproduce on our tasks; no QLoRA budgeted. Re-run with --body to confirm.
ponytail: structure + substring grounding only — not a faithfulness audit. Smoke test, not a benchmark.
"""
import glob
import json
import re
import sys
import urllib.request

OLLAMA = "http://localhost:11434/api/generate"
ASPECTS = ["context", "key_idea", "method", "outcome", "projected_impact"]
ASPECT_SCHEMA = {"type": "object", "properties": {k: {"type": "string"} for k in ASPECTS}, "required": ASPECTS}
WARRANT_SCHEMA = {"type": "object", "properties": {"claims": {"type": "array", "items": {
    "type": "object", "properties": {"claim": {"type": "string"}, "quote": {"type": "string"}},
    "required": ["claim", "quote"]}}}, "required": ["claims"]}


def norm(s):
    return re.sub(r"\s+", " ", s).strip().lower()


def gen(prompt, schema):
    body = {"model": "qwen2.5:7b", "prompt": prompt, "stream": False,
            "format": schema, "options": {"temperature": 0}}
    req = urllib.request.Request(OLLAMA, json.dumps(body).encode(), {"Content-Type": "application/json"})
    return json.loads(json.loads(urllib.request.urlopen(req, timeout=180).read())["response"])


def passages(body_mode, n=6):
    out = []
    for f in sorted(glob.glob("/home/eranr/memoria-vault/_papers/*.md")):
        t = re.sub(r"!\[[^\]]*\]\([^)]*\)", "", open(f, encoding="utf-8", errors="ignore").read())
        if body_mode:
            m = re.search(r"(?is)introduction\*{0,2}\s*\n+(.{800,})", t)
            text = re.sub(r"\n{2,}", "\n", m.group(1))[:3000] if m else None
        else:
            m = re.search(r"(?is)abstract\*{0,2}\s*\n+(.+?)(?:\n#|\n\*\*1|\Z)", t)
            text = re.sub(r"\s+", " ", m.group(1)).strip()[:1500] if m and 250 < len(m.group(1)) else None
        if text:
            out.append((f.split("/")[-1][:38], text))
        if len(out) >= n:
            break
    return out


def main():
    docs = passages("--body" in sys.argv)
    print(f"{len(docs)} passages ({'body' if '--body' in sys.argv else 'abstract'})\n")

    ok = 0
    for name, p in docs:
        try:
            d = gen("Extract these five aspects. Return JSON with exactly these string keys: "
                    + ", ".join(ASPECTS) + ". Use \"N/A\" if absent.\n\n" + p, ASPECT_SCHEMA)
            ok += set(d) == set(ASPECTS) and all(isinstance(v, str) for v in d.values())
        except Exception as e:
            print(f"  aspect fail {name}: {e}")
    print(f"ASPECT extraction (schema-clean): {ok}/{len(docs)}")

    tot = vb = 0
    for name, p in docs:
        np = norm(p)
        try:
            claims = gen("Extract 5 atomic claims. For each, \"quote\" = the EXACT verbatim span from "
                         "the passage (character-for-character, not paraphrased). "
                         "JSON {\"claims\":[{\"claim\":..,\"quote\":..}]}.\n\n" + p, WARRANT_SCHEMA).get("claims", [])
        except Exception as e:
            print(f"  warrant fail {name}: {e}")
            continue
        hits = sum(1 for c in claims if norm(c.get("quote", "")) and norm(c["quote"]) in np)
        tot += len(claims)
        vb += hits
    print(f"WARRANT quotes verbatim (§3.2 substring-gate pass): {vb}/{tot} = {vb / tot:.0%}" if tot else "no claims")


if __name__ == "__main__":
    main()
