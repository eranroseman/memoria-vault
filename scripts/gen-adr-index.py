#!/usr/bin/env python3
"""gen-adr-index — regenerate the ADR table in project/adr/README.md from frontmatter.

The ADR README is a hand-written navigation hub; the per-decision listing is the
one part that rots (a renamed title, a new ADR, a supersession) if maintained by
hand. This reads every `project/adr/NN-*.md`, and rewrites the table between the
`<!-- ADR-INDEX:START -->` / `<!-- ADR-INDEX:END -->` markers — sorted by number,
with each status (and supersession arrow) taken straight from frontmatter.

Modes:
  (default)     rewrite the table in place
  --check       exit 1 if the committed table is stale (CI / pre-commit gate)
  --self-test   run the internal tests

Usage: python scripts/gen-adr-index.py [--check | --self-test]
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
ADR_DIR = ROOT / "project" / "adr"
README = ADR_DIR / "README.md"

START = "<!-- ADR-INDEX:START -->"
END = "<!-- ADR-INDEX:END -->"

FRONTMATTER_RE = re.compile(r"^---\n(.*?)\n---", re.DOTALL)
ADR_FILE_RE = re.compile(r"^\d+-.+\.md$")


def parse_adr(text: str) -> dict[str, object]:
    """Pull id, title, status, and superseded_by from an ADR's frontmatter."""
    m = FRONTMATTER_RE.match(text.replace("\r\n", "\n"))
    fm = m.group(1) if m else ""
    out: dict[str, object] = {"id": None, "title": "", "status": "", "superseded_by": []}
    for line in fm.splitlines():
        key, sep, val = line.partition(":")
        if not sep:
            continue
        key, val = key.strip(), val.strip()
        if key == "id":
            out["id"] = int(val) if val.isdigit() else None
        elif key == "title":
            out["title"] = val.strip('"').strip("'")
        elif key == "status":
            out["status"] = val
        elif key == "superseded_by":
            out["superseded_by"] = [int(n) for n in re.findall(r"\d+", val)]
    return out


def status_cell(adr: dict[str, object]) -> str:
    """Render the status column, appending a supersession arrow when present."""
    status = str(adr["status"])
    by = adr["superseded_by"]
    if isinstance(by, list) and by:
        arrow = ", ".join(f"ADR-{n}" for n in by)
        return f"{status} → {arrow}"
    return status


def render_table(adrs: list[dict[str, object]]) -> str:
    """Build the Markdown table body (header + one row per ADR, sorted by id)."""
    rows = ["| # | Decision | Status |", "|---|---|---|"]
    for adr in sorted(adrs, key=lambda a: a["id"]):
        num = adr["id"]
        link = f"[{num:02d}]({num:02d}-{adr['slug']}.md)"
        rows.append(f"| {link} | {adr['title']} | {status_cell(adr)} |")
    return "\n".join(rows)


def collect_adrs(adr_dir: Path) -> list[dict[str, object]]:
    """Parse every NN-*.md ADR file in adr_dir (skips README.md and _template.md)."""
    adrs: list[dict[str, object]] = []
    for path in sorted(adr_dir.glob("*.md")):
        if not ADR_FILE_RE.match(path.name):
            continue
        adr = parse_adr(path.read_text(encoding="utf-8"))
        if adr["id"] is None:
            raise SystemExit(f"gen-adr-index: {path.name} has no numeric 'id' in frontmatter")
        adr["slug"] = path.stem.split("-", 1)[1]
        adrs.append(adr)
    return adrs


def splice(readme_text: str, table: str) -> str:
    """Replace the content between the index markers with the freshly-built table."""
    text = readme_text.replace("\r\n", "\n")
    if START not in text or END not in text:
        raise SystemExit(f"gen-adr-index: {README} is missing the {START} / {END} markers")
    pre, _, rest = text.partition(START)
    _, _, post = rest.partition(END)
    return f"{pre}{START}\n\n{table}\n\n{END}{post}"


def build(adr_dir: Path, readme: Path) -> str:
    """Compute what README's content should be from the ADRs on disk."""
    return splice(readme.read_text(encoding="utf-8"), render_table(collect_adrs(adr_dir)))


def main() -> int:
    if "--self-test" in sys.argv:
        return _self_test()
    current = README.read_text(encoding="utf-8")
    updated = build(ADR_DIR, README)
    if "--check" in sys.argv:
        if current != updated:
            print("gen-adr-index: ADR index is stale — run `python scripts/gen-adr-index.py`")
            return 1
        print("gen-adr-index: ADR index is current ✓")
        return 0
    if current != updated:
        README.write_text(updated, encoding="utf-8")
        print(f"gen-adr-index: rewrote {README.relative_to(ROOT)}")
    else:
        print("gen-adr-index: ADR index already current ✓")
    return 0


def _self_test() -> int:
    import tempfile

    failures = 0

    def check(name: str, cond: bool) -> None:
        nonlocal failures
        print(f"  {'PASS' if cond else 'FAIL'}  {name}")
        failures += 0 if cond else 1

    # --- parse_adr ---
    fm = "---\ntopic: decisions\nid: 28\ntitle: Write gate, a plugin\nstatus: accepted\nsuperseded_by: []\n---\n# body"
    adr = parse_adr(fm)
    check("parse_adr: id", adr["id"] == 28)
    check("parse_adr: title with comma", adr["title"] == "Write gate, a plugin")
    check("parse_adr: status", adr["status"] == "accepted")
    check("parse_adr: empty superseded_by", adr["superseded_by"] == [])

    sup = parse_adr("---\nid: 27\ntitle: Old\nstatus: superseded\nsuperseded_by: [28]\n---\n")
    check("parse_adr: superseded_by list", sup["superseded_by"] == [28])
    check("status_cell: supersession arrow", status_cell(sup) == "superseded → ADR-28")
    check("status_cell: plain", status_cell(adr) == "accepted")

    # --- render_table (sorting + link form) ---
    table = render_table([
        {"id": 2, "slug": "second", "title": "Second", "status": "accepted", "superseded_by": []},
        {"id": 1, "slug": "first", "title": "First", "status": "accepted", "superseded_by": []},
    ])
    check("render_table: sorted by id", table.index("[01]") < table.index("[02]"))
    check("render_table: zero-padded link", "[01](01-first.md)" in table)

    # --- collect_adrs + splice + build round-trips against a temp tree ---
    with tempfile.TemporaryDirectory() as d:
        adr_dir = Path(d)
        (adr_dir / "01-alpha.md").write_text("---\nid: 1\ntitle: Alpha\nstatus: accepted\nsuperseded_by: []\n---\n")
        (adr_dir / "02-beta.md").write_text("---\nid: 2\ntitle: Beta\nstatus: superseded\nsuperseded_by: [1]\n---\n")
        (adr_dir / "_template.md").write_text("---\nid: 0\ntitle: T\nstatus: x\n---\n")
        readme = adr_dir / "README.md"
        readme.write_text(f"# Decisions\n\n{START}\n\nstale\n\n{END}\n\ntail\n")
        adrs = collect_adrs(adr_dir)
        check("collect_adrs: skips _template.md", len(adrs) == 2)
        out = splice(readme.read_text(), render_table(adrs))
        check("splice: marker fence preserved", out.count(START) == 1 and out.count(END) == 1)
        check("splice: tail preserved", out.endswith("tail\n"))
        check("splice: stale content gone", "stale" not in out)
        check("build: idempotent", build(adr_dir, _written(readme, out)) == out)
        readme.write_text("# Decisions\n\nno markers here\n")
        try:
            build(adr_dir, readme)
            check("build: missing markers raises", False)
        except SystemExit:
            check("build: missing markers raises", True)

    print(f"\n{'OK' if not failures else f'{failures} FAILING'}: gen-adr-index self-test")
    return 1 if failures else 0


def _written(path: Path, text: str) -> Path:
    """Write text to path and return it — a tiny helper for the idempotence check."""
    path.write_text(text, encoding="utf-8")
    return path


if __name__ == "__main__":
    sys.exit(main())
