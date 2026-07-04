#!/usr/bin/env python3
"""gen-adr-index — regenerate the ADR table in docs/adr/README.md from frontmatter.

The ADR README is a hand-written navigation hub; the per-decision listing is the
one part that rots (a renamed title, a new ADR, a supersession) if maintained by
hand. This reads every `docs/adr/NN-*.md`, and rewrites the table between the
`<!-- ADR-INDEX:START -->` / `<!-- ADR-INDEX:END -->` markers — sorted by number,
with each status (and supersession arrow) taken straight from frontmatter.

Modes:
  (default)     rewrite the table in place
  --check       exit 1 if the committed table is stale (CI / pre-commit gate)
  --self-test   run the internal tests

Usage: python scripts/gen_adr_index.py [--check | --self-test]
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
ADR_DIR = ROOT / "docs" / "adr"
README = ADR_DIR / "README.md"

START = "<!-- ADR-INDEX:START -->"
END = "<!-- ADR-INDEX:END -->"

FRONTMATTER_RE = re.compile(r"^---\n(.*?)\n---", re.DOTALL)
ADR_FILE_RE = re.compile(r"^\d+-.+\.md$")
ADR_STATUSES = {"proposed", "accepted", "rejected"}
REQUIRED_KEYS = (
    "topic",
    "id",
    "title",
    "nav_exclude",
    "status",
    "date_proposed",
    "date_resolved",
    "assumes",
    "supersedes",
    "superseded_by",
)
RESOLVED_STATUSES = {"accepted", "rejected"}
UNRESOLVED_STATUSES = {"proposed"}


def parse_adr(text: str) -> dict[str, object]:
    """Pull id, title, status, and superseded_by from an ADR's frontmatter."""
    m = FRONTMATTER_RE.match(text.replace("\r\n", "\n"))
    fm = m.group(1) if m else ""
    out: dict[str, object] = {
        "id": None,
        "title": "",
        "nav_exclude": False,
        "status": "",
        "date_proposed": "",
        "date_resolved": "",
        "assumes": [],
        "supersedes": [],
        "superseded_by": [],
        "_keys": set(),
    }
    for line in fm.splitlines():
        key, sep, val = line.partition(":")
        if not sep:
            continue
        key, val = key.strip(), val.strip()
        out["_keys"].add(key)
        if key == "id":
            out["id"] = int(val) if val.isdigit() else None
        elif key == "title":
            out["title"] = val.strip('"').strip("'")
        elif key == "nav_exclude":
            out["nav_exclude"] = val.split("#", 1)[0].strip().lower() == "true"
        elif key == "status":
            # drop any trailing YAML inline comment (e.g. "accepted  # rationale …")
            out["status"] = val.split("#", 1)[0].strip()
        elif key in {"date_proposed", "date_resolved"}:
            out[key] = val.split("#", 1)[0].strip()
        elif key in {"assumes", "supersedes", "superseded_by"}:
            # parse only the IDs inside the [...] list — never digits in a trailing
            # "# … (D18) …" comment, which would invent phantom supersessors
            bracket = re.search(r"\[([^\]]*)\]", val)
            ids = bracket.group(1) if bracket else val.split("#", 1)[0]
            out[key] = [int(n) for n in re.findall(r"\d+", ids)]
    return out


def validate_adr(path: Path, adr: dict[str, object]) -> list[str]:
    """Return frontmatter/schema drift findings for one ADR."""
    errs: list[str] = []
    try:
        rel = path.relative_to(ROOT)
    except ValueError:
        rel = path
    keys = adr.get("_keys", set())
    if isinstance(keys, set):
        for key in REQUIRED_KEYS:
            if key not in keys:
                errs.append(f"{rel}: missing frontmatter key `{key}`")
    if adr.get("nav_exclude") is not True:
        errs.append(f"{rel}: nav_exclude must be true so ADR pages stay out of site nav")

    status = str(adr["status"])
    if status not in ADR_STATUSES:
        allowed = ", ".join(sorted(ADR_STATUSES))
        errs.append(f"{rel}: invalid status `{status}` — expected one of: {allowed}")

    date_proposed = str(adr.get("date_proposed", ""))
    date_resolved = str(adr.get("date_resolved", ""))
    if not _dateish(date_proposed):
        errs.append(f"{rel}: date_proposed must be YYYY-MM-DD")
    if status in RESOLVED_STATUSES and not _dateish(date_resolved):
        errs.append(f"{rel}: {status} ADR must set date_resolved")
    if status in UNRESOLVED_STATUSES and date_resolved:
        errs.append(f"{rel}: {status} ADR must leave date_resolved blank")
    return errs


def _dateish(value: str) -> bool:
    return bool(re.fullmatch(r"\d{4}-\d{2}-\d{2}", value))


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
    ids: dict[int, Path] = {}
    for path in sorted(adr_dir.glob("*.md")):
        if not ADR_FILE_RE.match(path.name):
            continue
        adr = parse_adr(path.read_text(encoding="utf-8"))
        if adr["id"] is None:
            raise SystemExit(f"gen-adr-index: {path.name} has no numeric 'id' in frontmatter")
        adr_id = int(adr["id"])
        if adr_id in ids:
            raise SystemExit(
                f"gen-adr-index: duplicate ADR id {adr_id}: {ids[adr_id].name} and {path.name}"
            )
        ids[adr_id] = path
        errors = validate_adr(path, adr)
        if errors:
            raise SystemExit("gen-adr-index: ADR frontmatter invalid\n  ✗ " + "\n  ✗ ".join(errors))
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
    current = README.read_text(encoding="utf-8")
    updated = build(ADR_DIR, README)
    if "--check" in sys.argv:
        if current != updated:
            print("gen-adr-index: ADR index is stale — run `python scripts/gen_adr_index.py`")
            return 1
        print("gen-adr-index: ADR index is current ✓")
        return 0
    if current != updated:
        README.write_text(updated, encoding="utf-8")
        print(f"gen-adr-index: rewrote {README.relative_to(ROOT)}")
    else:
        print("gen-adr-index: ADR index already current ✓")
    return 0


def _written(path: Path, text: str) -> Path:
    """Write text to path and return it — a tiny helper for the idempotence check."""
    path.write_text(text, encoding="utf-8")
    return path


if __name__ == "__main__":
    sys.exit(main())
