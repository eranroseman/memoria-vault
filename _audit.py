#!/usr/bin/env python3
import re, sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
from pathlib import Path
from urllib.parse import unquote
from functools import lru_cache
ROOT = Path(__file__).resolve().parent
LINK = re.compile(r"\[([^\]]*)\]\(([^)]+)\)"); INLINE = re.compile(r"`[^`]*`")
HEAD = re.compile(r"^(#{1,6})\s+(.*?)\s*#*\s*$")
def slug(t):
    t=re.sub(r"`([^`]+)`",r"\1",t); t=re.sub(r"\[([^\]]*)\]\([^)]*\)",r"\1",t)
    t=t.strip().lower(); t=re.sub(r"[^\w\s-]","",t); return re.sub(r"\s+","-",t)
@lru_cache(None)
def slugs(p):
    if not p.exists() or p.suffix.lower()!=".md": return frozenset()
    out=[];seen={};f=False
    for ln in p.read_text(encoding="utf-8",errors="replace").splitlines():
        s=ln.strip()
        if s.startswith(("```","~~~")): f=not f;continue
        if f: continue
        m=HEAD.match(ln)
        if m:
            b=slug(m.group(2))
            if not b: continue
            if b in seen: seen[b]+=1;out.append(f"{b}-{seen[b]}")
            else: seen[b]=0;out.append(b)
    return frozenset(out)
ex=[];an=[];ok=0
for base in (ROOT/"docs",ROOT/"project-files"):
    for md in sorted(base.rglob("*.md")):
        f=False
        for ln,line in enumerate(md.read_text(encoding="utf-8",errors="replace").splitlines(),1):
            s=line.strip()
            if s.startswith(("```","~~~")): f=not f;continue
            if f: continue
            for m in LINK.finditer(INLINE.sub("",line)):
                raw=m.group(2).strip()
                if raw.startswith(("http://","https://","mailto:","tel:")) or not raw: continue
                if raw.startswith("#"):
                    a=unquote(raw[1:]).lower()
                    if a and a not in slugs(md): an.append((md.relative_to(ROOT).as_posix(),ln,raw))
                    continue
                tgt=unquote(raw.split()[0].split("#",1)[0])
                if not tgt: continue
                r=(md.parent/tgt).resolve()
                if not r.exists(): ex.append((md.relative_to(ROOT).as_posix(),ln,raw)); continue
                ok+=1
                if "#" in raw:
                    a=unquote(raw.split()[0].split("#",1)[1]).lower()
                    if a and r.suffix.lower()==".md" and a not in slugs(r): an.append((md.relative_to(ROOT).as_posix(),ln,raw))
print(f"examined: {ok} | BROKEN existence: {len(ex)} | BROKEN anchor: {len(an)}")
for it in ex: print(f"  EX: {it}")
for it in an: print(f"  AN: {it}")
