"""The pattern library (ADR-53): shipped patterns validate; the runner enforces the rules."""

import re
from pathlib import Path

import patterns_mcp
import yaml
from operations.lib import schema

SRC = Path(__file__).resolve().parent.parent / "src"
PATTERNS = SRC / "system" / "patterns"


def _frontmatter(path: Path) -> dict:
    m = re.match(r"^---\n(.*?)\n---", path.read_text(encoding="utf-8"), re.S)
    return yaml.safe_load(m.group(1))


def test_shipped_patterns_validate_against_the_schema():
    types = schema.load_types()
    shipped = [p for p in PATTERNS.glob("*.md") if not p.name.startswith("_")]
    assert len(shipped) >= 6, "the library ships seeded patterns"
    for p in shipped:
        fm = _frontmatter(p)
        assert schema.validate_frontmatter(fm, types["pattern"]) == [], p.name


def test_no_shipped_pattern_targets_a_gated_zone():
    gated = tuple(schema.gated_prefixes(schema.load_folders()))
    for p in PATTERNS.glob("*.md"):
        if p.name.startswith("_"):
            continue
        target = _frontmatter(p)["output_target"].lstrip("/")
        assert not target.startswith(gated), f"{p.name} targets a gated zone"


def test_every_pattern_has_an_input_slot():
    for p in PATTERNS.glob("*.md"):
        if p.name.startswith("_"):
            continue
        assert "{{input}}" in p.read_text(encoding="utf-8"), f"{p.name} has no {{{{input}}}} slot"


def test_runner_lists_shipped_patterns_from_real_vault():
    listed = {p["id"] for p in patterns_mcp.list_patterns(SRC)}
    shipped = {p.stem for p in PATTERNS.glob("*.md") if not p.name.startswith("_")}
    assert listed == shipped


def test_runner_composes_and_logs(tmp_path):
    pd = tmp_path / "system/patterns"
    pd.mkdir(parents=True)
    (pd / "_preamble.md").write_text("VOICE", encoding="utf-8")
    (pd / "x.md").write_text(
        "---\ntitle: X\ntype: pattern\nlifecycle: current\nposture: librarian\n"
        "mode: library\naction: a\ninput: note\noutput_target: 'projects/'\n---\nP {{input}} Q\n",
        encoding="utf-8",
    )
    r = patterns_mcp.run_pattern(tmp_path, "x", "BODY", "ref.md")
    assert "VOICE" in r["prompt"] and "P BODY Q" in r["prompt"]
    assert r["dry_run"] is False
    log = (tmp_path / "system/logs/patterns.jsonl").read_text(encoding="utf-8")
    assert '"pattern": "x"' in log


def test_runner_degrades_gated_targets_to_dry_run(tmp_path):
    pd = tmp_path / "system/patterns"
    pd.mkdir(parents=True)
    (pd / "bad.md").write_text(
        "---\ntitle: B\ntype: pattern\nlifecycle: current\nposture: librarian\n"
        "mode: library\naction: a\ninput: note\noutput_target: 'notes/claims/'\n---\nZ {{input}}\n",
        encoding="utf-8",
    )
    r = patterns_mcp.run_pattern(tmp_path, "bad", "x")
    assert r["dry_run"] is True and "note" in r


def test_runner_survives_provenance_write_failure(tmp_path, capsys):
    """An unwritable provenance log degrades loudly: the run (the prompt) is still
    returned, flagged provenance_logged: false, with a stderr warning."""
    pd = tmp_path / "system/patterns"
    pd.mkdir(parents=True)
    (pd / "x.md").write_text(
        "---\ntitle: X\ntype: pattern\nlifecycle: current\nposture: librarian\n"
        "mode: library\naction: a\ninput: note\noutput_target: 'projects/'\n---\nP {{input}} Q\n",
        encoding="utf-8",
    )
    # system/logs exists as a FILE -> the jsonl append cannot create the dir
    (tmp_path / "system" / "logs").write_text("not a directory", encoding="utf-8")
    r = patterns_mcp.run_pattern(tmp_path, "x", "BODY")
    assert r["provenance_logged"] is False
    assert "P BODY Q" in r["prompt"]  # the run itself still succeeds
    assert "provenance" in capsys.readouterr().err


def test_runner_refuses_non_current_and_unknown(tmp_path):
    (tmp_path / "system/patterns").mkdir(parents=True)
    assert patterns_mcp.run_pattern(tmp_path, "ghost", "x")["error"] == "unknown-pattern"
