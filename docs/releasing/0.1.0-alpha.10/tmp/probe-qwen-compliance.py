#!/usr/bin/env python3
"""Smoke-test local qwen structured extraction and warrant substrings.

Needs Ollama with qwen2.5:7b. This is a go/no-go probe, not a benchmark.
"""

import glob
import json
import re
import sys
import urllib.request

OLLAMA = "http://localhost:11434/api/generate"
ASPECTS = ["context", "key_idea", "method", "outcome", "projected_impact"]
ASPECT_SCHEMA = {
    "type": "object",
    "properties": {k: {"type": "string"} for k in ASPECTS},
    "required": ASPECTS,
}
WARRANT_SCHEMA = {
    "type": "object",
    "properties": {
        "claims": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {"claim": {"type": "string"}, "quote": {"type": "string"}},
                "required": ["claim", "quote"],
            },
        }
    },
    "required": ["claims"],
}


def norm(s):
    return re.sub(r"\s+", " ", s).strip().lower()


def gen(prompt, schema):
    body = {
        "model": "qwen2.5:7b",
        "prompt": prompt,
        "stream": False,
        "format": schema,
        "options": {"temperature": 0},
    }
    req = urllib.request.Request(
        OLLAMA, json.dumps(body).encode(), {"Content-Type": "application/json"}
    )
    return json.loads(json.loads(urllib.request.urlopen(req, timeout=180).read())["response"])


def passages(body_mode, n=6):
    out = []
    for f in sorted(glob.glob("/home/eranr/memoria-vault/_papers/*.md")):
        text = open(f, encoding="utf-8", errors="ignore").read()
        text = re.sub(r"!\[[^\]]*\]\([^)]*\)", "", text)
        if body_mode:
            match = re.search(r"(?is)introduction\*{0,2}\s*\n+(.{800,})", text)
            passage = re.sub(r"\n{2,}", "\n", match.group(1))[:3000] if match else None
        else:
            match = re.search(r"(?is)abstract\*{0,2}\s*\n+(.+?)(?:\n#|\n\*\*1|\Z)", text)
            passage = (
                re.sub(r"\s+", " ", match.group(1)).strip()[:1500]
                if match and 250 < len(match.group(1))
                else None
            )
        if passage:
            out.append((f.split("/")[-1][:38], passage))
        if len(out) >= n:
            break
    return out


def main():
    docs = passages("--body" in sys.argv)
    print(f"{len(docs)} passages ({'body' if '--body' in sys.argv else 'abstract'})")

    ok = 0
    for _, passage in docs:
        data = gen(
            "Extract these five aspects. Return JSON with exactly these string keys: "
            + ", ".join(ASPECTS)
            + '. Use "N/A" if absent.\n\n'
            + passage,
            ASPECT_SCHEMA,
        )
        ok += set(data) == set(ASPECTS) and all(isinstance(v, str) for v in data.values())
    print(f"ASPECT extraction schema-clean: {ok}/{len(docs)}")

    total = verbatim = 0
    for _, passage in docs:
        passage_norm = norm(passage)
        claims = gen(
            'Extract 5 atomic claims. For each, "quote" = the exact verbatim span. '
            'JSON {"claims":[{"claim":..,"quote":..}]}.\n\n'
            + passage,
            WARRANT_SCHEMA,
        ).get("claims", [])
        total += len(claims)
        verbatim += sum(1 for c in claims if norm(c.get("quote", "")) in passage_norm)
    print(f"WARRANT quotes verbatim: {verbatim}/{total}" if total else "no claims")


if __name__ == "__main__":
    main()

