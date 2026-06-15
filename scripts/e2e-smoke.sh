#!/usr/bin/env bash
# e2e-smoke.sh — the offline end-to-end gate (added after it caught two real
# bugs the unit suite missed). Builds a vault from src/ exactly as the installer
# would (scaffold + populate + golden), then walks the Library loop:
#   tree==schemas -> golden clean -> detectors PASS -> the commit hooks wire ->
#   the schema gate blocks a malformed claim and passes a valid one -> offline Tier-0 ingest -> a
#   schema-valid Catalog entity -> an honesty candidate card -> lint PASS.
# Pure-local: no Hermes, no network. The cluster-graph step runs only if
# networkx is installed.
#
# Usage: bash scripts/e2e-smoke.sh   (exit 0 = gate green)
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
V="$(mktemp -d "${TMPDIR:-/tmp}/memoria-e2e-XXXXXXXX")"
trap 'rm -rf "$V"' EXIT
PY="${PYTHON:-python3}"
fail() { echo "e2e-smoke: FAIL — $1" >&2; exit 1; }

echo "== 1. scaffold + populate (installer-equivalent, from src/) =="
if command -v rsync >/dev/null; then rsync -a --exclude '.git' "$ROOT/src/" "$V/"; else cp -R "$ROOT/src/." "$V/"; fi
"$PY" - "$ROOT" "$V" <<'PYEOF'
import sys, yaml, pathlib
root, vault = pathlib.Path(sys.argv[1]), pathlib.Path(sys.argv[2])
folders = yaml.safe_load((root / "src/.memoria/schemas/folders.yaml").read_text())
for d in folders["skeleton"]:
    (vault / d).mkdir(parents=True, exist_ok=True)
missing = [d for d in folders["skeleton"] if not (vault / d).is_dir()]
assert not missing, f"skeleton missing {missing}"
print(f"   skeleton ensured ({len(folders['skeleton'])} dirs); tree matches folders.yaml")
PYEOF

echo "== 2. golden copy + git hook wiring =="
"$PY" "$V/.memoria/operations/integrity/linter/golden_restore.py" --vault "$V" stage
git -C "$V" init -q
cp "$V/.memoria/operations/integrity/linter/pre-commit" "$V/.git/hooks/pre-commit" && chmod +x "$V/.git/hooks/pre-commit"
cp "$V/.githooks/post-commit" "$V/.git/hooks/post-commit" && chmod +x "$V/.git/hooks/post-commit"

echo "== 3. fresh-vault integrity =="
"$PY" "$V/.memoria/operations/integrity/linter/detectors.py" --vault "$V" | tail -1 | grep -q "PASS" || fail "detectors not clean on the fresh vault"
"$PY" "$V/.memoria/operations/integrity/linter/golden_restore.py" --vault "$V" check || fail "golden drift on a fresh vault"

echo "== 4. the commit gate =="
git -C "$V" add -A
git -C "$V" -c user.email=e2e@ci -c user.name=e2e commit -qm init || fail "baseline commit blocked"
printf -- '---\ntype: claim\nlifecycle: proposed\ntitle: "Bad"\n---\nx\n' > "$V/notes/claims/bad.md"
git -C "$V" add notes/claims/bad.md
if git -C "$V" -c user.email=e2e@ci -c user.name=e2e commit -qm bad 2>/dev/null; then
  fail "the gate let a malformed claim through"
fi
echo "   malformed claim blocked at commit"
git -C "$V" reset -q HEAD notes/claims/bad.md && rm "$V/notes/claims/bad.md"
printf -- '---\ntype: claim\nlifecycle: current\ntitle: "Good"\nmaturity: seedling\nsources: ["@x2024"]\n---\nBody.\n' > "$V/notes/claims/good.md"
git -C "$V" add notes/claims/good.md
git -C "$V" -c user.email=e2e@ci -c user.name=e2e commit -qm good || fail "valid claim blocked"
echo "   valid claim passes"

echo "== 5. offline ingest -> entity -> honesty card =="
"$PY" - "$ROOT" "$V" <<'PYEOF'
import sys, pathlib, re, yaml
root, vault = pathlib.Path(sys.argv[1]), pathlib.Path(sys.argv[2])
sys.path.insert(0, str(root / "src/.memoria/operations/processing/ingest"))
sys.path.insert(0, str(root / "src/.memoria/operations/lib"))
import ingest_paper, schema, inbox
BIB = "@article{x2024demo,\n  title = {Demo Work},\n  author = {Doe, Jane},\n  year = {2024},\n  journal = {Demo Journal},\n}\n"
note = ingest_paper.ingest_text("x2024demo", BIB)
types = schema.load_types()
errs = schema.validate_frontmatter(note["frontmatter"], types[note["note_type"]])
assert not errs, f"ingested entity invalid: {errs}"
(vault / note["path"]).write_text(ingest_paper.render(note), encoding="utf-8")
card = inbox.write_proposal(vault, "candidate", "Demo Work", "Accept into catalog",
                            "fills a demo gap", "single-source demo", "the gap wins",
                            "likely", "librarian", citekey="@x2024demo")
fm = yaml.safe_load(re.match(r"^---\n(.*?)\n---", card.read_text(), re.S).group(1))
assert schema.validate_frontmatter(fm, types["candidate"]) == []
assert "agent_recommendation" not in fm   # proposals carry no verdict (ADR-51)
print("   entity + honesty card schema-valid")
PYEOF

echo "== 6. typed graph (optional: networkx) =="
"$PY" - "$ROOT" "$V" <<'PYEOF'
import sys, pathlib
root, vault = pathlib.Path(sys.argv[1]), pathlib.Path(sys.argv[2])
try:
    import networkx  # noqa: F401
except ImportError:
    print("   (networkx not installed — graph step skipped)")
    raise SystemExit(0)
sys.path.insert(0, str(root / "src/.memoria/mcp"))
import cluster_mcp
g = cluster_mcp.build_graph(vault, seed=7)
assert g["nodes"], "graph collected no nodes"
print(f"   graph: {len(g['nodes'])} nodes / {len(g['edges'])} edges")
PYEOF

echo "== 7. final lint over the worked vault =="
verdict=$("$PY" "$V/.memoria/operations/integrity/linter/detectors.py" --vault "$V" | tail -1)
echo "   $verdict"
echo "$verdict" | grep -qE "PASS|REVIEW" || fail "worked vault verdict: $verdict"
"$PY" "$V/.memoria/operations/integrity/linter/golden_restore.py" --vault "$V" check || fail "golden drift after the loop"

echo "e2e-smoke: ✅ all gates green"
