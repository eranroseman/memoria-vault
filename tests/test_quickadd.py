"""The QuickAdd palette config is internally consistent.

Every Macro choice in the shipped quickadd data.json points at a user script
that actually exists under system/scripts/, and every macro a choice embeds
carries an id (Obsidian resolves commands by these ids — a dangling reference
makes the palette entry a silent no-op). The per-task lane scripts (#203)
must also stay in sync with the delegation model: each script's lane/assignee
pair matches LANE_PROFILE in tasks_mcp.py, and each named skill is a real
skill directory under the assignee's profile.
"""

import json
import re
from pathlib import Path

SRC = Path(__file__).resolve().parent.parent / "src"
DATA = SRC / ".obsidian" / "plugins" / "quickadd" / "data.json"
SCRIPTS = SRC / "system" / "scripts"
PROFILES = SRC / ".memoria" / "profiles"
TASKS_MCP = SRC / ".memoria" / "mcp" / "tasks_mcp.py"

# The six per-task lane commands (one script per lane task).
LANE_SCRIPTS = [
    "catalog-source.js",
    "extract-claims.js",
    "link-claim.js",
    "map-corpus.js",
    "draft-section.js",
    "verify-draft.js",
]


def _choices():
    return json.loads(DATA.read_text(encoding="utf-8"))["choices"]


def test_macro_choices_reference_existing_scripts():
    macros = [c for c in _choices() if c["type"] == "Macro"]
    assert macros, "no Macro choices found in quickadd data.json"
    for choice in macros:
        for cmd in choice["macro"]["commands"]:
            if cmd["type"] != "UserScript":
                continue
            script = SRC / cmd["path"]
            assert script.is_file(), (
                f"{choice['name']}: script {cmd['path']} missing under src/")
            assert cmd["path"].startswith("system/scripts/"), (
                f"{choice['name']}: script {cmd['path']} outside system/scripts/")


def test_macro_ids_exist_and_are_unique():
    seen = set()
    for choice in _choices():
        ids = [choice["id"]]
        if choice["type"] == "Macro":
            assert choice["macro"].get("id"), f"{choice['name']}: macro has no id"
            ids.append(choice["macro"]["id"])
            ids += [cmd["id"] for cmd in choice["macro"]["commands"]]
        for i in ids:
            assert i not in seen, f"duplicate QuickAdd id {i}"
            seen.add(i)


def _lane_profile():
    """Parse LANE_PROFILE out of tasks_mcp.py (regex — no import, no deps)."""
    src = TASKS_MCP.read_text(encoding="utf-8")
    block = re.search(r"LANE_PROFILE\s*=\s*\{(.*?)\}", src, re.S).group(1)
    return dict(re.findall(r'"([\w-]+)":\s*"([\w-]+)"', block))


def _const(script_text, name):
    m = re.search(rf'const {name} = "([^"]+)"', script_text)
    return m.group(1) if m else None


def test_lane_scripts_match_lane_profile_and_skills():
    lane_profile = _lane_profile()
    seen_lanes = set()
    for fname in LANE_SCRIPTS:
        text = (SCRIPTS / fname).read_text(encoding="utf-8")
        lane, assignee, skill = (_const(text, n) for n in ("LANE", "ASSIGNEE", "SKILL"))
        assert lane and assignee and skill, f"{fname}: missing LANE/ASSIGNEE/SKILL const"
        assert lane in lane_profile, f"{fname}: lane '{lane}' not in tasks_mcp LANE_PROFILE"
        assert assignee == lane_profile[lane], (
            f"{fname}: assignee {assignee} != LANE_PROFILE[{lane}] ({lane_profile[lane]})")
        skill_dir = PROFILES / assignee / "skills" / skill
        assert skill_dir.is_dir(), f"{fname}: skill dir {skill_dir} missing"
        seen_lanes.add(lane)
    assert seen_lanes == set(lane_profile) - {"code"}, (
        f"lane scripts cover {sorted(seen_lanes)}, expected every non-code lane")


def test_zotero_capture_writes_intake_log_where_readers_look():
    """capture-from-zotero.js must append its durability anchor to the same
    capture-intake.jsonl path the readers use (ingest_mcp INTAKE_LOG and the
    reconcile sweep) — a stale path silently drops the anchor (#427)."""
    ingest = (SRC / ".memoria" / "mcp" / "ingest_mcp.py").read_text(encoding="utf-8")
    intake_log = re.search(r'INTAKE_LOG\s*=\s*"([^"]+)"', ingest).group(1)
    script = (SCRIPTS / "capture-from-zotero.js").read_text(encoding="utf-8")
    log = _const(script, "LOG")
    assert log == intake_log, (
        f"capture-from-zotero.js writes {log!r} but ingest_mcp.py reads {intake_log!r}")


def test_lane_scripts_and_pattern_runner_are_wired_into_the_palette():
    wired = {
        cmd["path"]
        for c in _choices() if c["type"] == "Macro"
        for cmd in c["macro"]["commands"] if cmd["type"] == "UserScript"
    }
    for fname in [*LANE_SCRIPTS, "run-pattern.js", "delegate-task.js"]:
        assert f"system/scripts/{fname}" in wired, f"{fname} not wired into quickadd data.json"
