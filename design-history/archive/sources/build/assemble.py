#!/usr/bin/env python3
"""Assemble the design-history workflow's 19 markdown results (from journal.jsonl)
into ordered body parts. Classify each by its leading heading; order
alpha.1 facets -> alpha.2..15 deltas -> synthesis."""
import json, re, sys, pathlib

JOURNAL = "/home/eranr/.claude/projects/-home-eranr-memoria-vault/479deddf-c861-470d-b2f4-432df1ca9140/subagents/workflows/wf_236f9755-269/journal.jsonl"
OUT = pathlib.Path("/home/eranr/memoria-vault/scratch/design-history")

results = []
for line in open(JOURNAL):
    line = line.strip()
    if not line:
        continue
    obj = json.loads(line)
    if obj.get("type") == "result" and isinstance(obj.get("result"), str):
        results.append(obj["result"])

def strip_preamble(t):
    m = re.search(r'(?m)^#{2,4} ', t)
    return t[m.start():] if m else t

def first_heading(t):
    m = re.search(r'(?m)^#{2,4} .+$', t)
    return m.group(0).strip() if m else "(no heading)"

a1, deltas, synth = [], [], []
manifest = []
for t in results:
    body = strip_preamble(t)
    fh = first_heading(body)
    md = re.search(r'(?m)^## alpha\.(\d+)\b', body)
    if md:
        n = int(md.group(1))
        deltas.append((n, body)); manifest.append(("delta", n, fh, len(body)))
    elif "evolution arc" in fh.lower() or "timeline" in fh.lower() or "evolution arc" in body[:400].lower():
        synth.append(body); manifest.append(("synth", 0, fh, len(body)))
    else:
        low = fh.lower()
        if "vault" in low or "knowledge model" in low:
            o = 1
        elif "profile" in low or "soul" in low or "runtime" in low or "hermes" in low:
            o = 2
        elif "gate" in low or "provenance" in low or "policy" in low:
            o = 3
        elif "pipeline" in low or "adr" in low or "distribution" in low or "discovery" in low:
            o = 4
        else:
            o = 9
        a1.append((o, body)); manifest.append(("a1", o, fh, len(body)))

a1.sort(key=lambda x: x[0])
deltas.sort(key=lambda x: x[0])

print(f"total results: {len(results)} | a1={len(a1)} deltas={len(deltas)} synth={len(synth)}")
print("--- manifest (kind, order, first-heading, chars) ---")
for kind, o, fh, n in sorted(manifest, key=lambda m: (m[0], m[1])):
    print(f"{kind:6} {o:3} {n:6}  {fh[:90]}")

def sep(sections):
    return "\n\n".join(s.strip() for s in sections) + "\n"

(OUT / "part-alpha1.md").write_text(sep([b for _, b in a1]))
(OUT / "part-deltas.md").write_text(sep([b for _, b in deltas]))
(OUT / "part-synth.md").write_text(sep(synth))
print("\nwrote: part-alpha1.md, part-deltas.md, part-synth.md")
print("delta versions present:", sorted(n for n, _ in deltas))
