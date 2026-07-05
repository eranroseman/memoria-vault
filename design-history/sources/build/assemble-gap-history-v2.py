#!/usr/bin/env python3
"""Assemble the gap-design-history-v2 workflow's 17 results (16 subsystems + arcs)."""
import json, re, pathlib
JOURNAL = "/home/eranr/.claude/projects/-home-eranr-memoria-vault/b0bbb2c4-e9ce-4df2-8385-71b2a784518e/subagents/workflows/wf_eb907a35-728/journal.jsonl"
OUT = pathlib.Path("/home/eranr/memoria-vault/scratch/design-history")

results = []
for line in open(JOURNAL):
    line = line.strip()
    if not line: continue
    o = json.loads(line)
    if o.get("type") == "result" and isinstance(o.get("result"), str):
        results.append(o["result"])

def strip_pre(t):
    m = re.search(r'(?m)^## ', t)
    return t[m.start():] if m else t

subs, arcs, manifest = [], [], []
for t in results:
    b = strip_pre(t)
    m = re.match(r'## (\d+)\.', b)
    fh = re.search(r'(?m)^## .+$', b)
    head = fh.group(0) if fh else "(none)"
    if m:
        subs.append((int(m.group(1)), b)); manifest.append(("sub", int(m.group(1)), head, len(b)))
    elif re.search(r'cross-cutting|historical arc', b[:200], re.I):
        arcs.append(b); manifest.append(("arcs", 99, head, len(b)))
    else:
        subs.append((999, b)); manifest.append(("?", 999, head, len(b)))

subs.sort(key=lambda x: x[0])
print(f"results={len(results)} subs={len(subs)} arcs={len(arcs)}")
for k, n, h, ln in sorted(manifest, key=lambda z: z[1]):
    print(f"{k:5} {n:3} {ln:6}  {h[:78]}")
(OUT / "gh2-subs.md").write_text("\n\n".join(b for _, b in subs).strip() + "\n")
(OUT / "gh2-arcs.md").write_text(("\n\n".join(arcs)).strip() + "\n")
print("subsystems:", sorted(n for n, _ in subs))
