"""The skill-state dashboard stays in sync with the files it renders (ADR-43).

The dashboard is pure dataviewjs with no YAML library, so it reads the two
controlled formats with minimal line parsers. These tests pin the contract from
the Python side: the lane-override files and SKILL.md frontmatter keep the simple
shape the JS parsers assume (mirrored here line-for-line and checked against a
real YAML load), and the runtime layer itself is internally consistent — so a
restructuring fails CI instead of silently blanking or skewing the dashboard.
"""

import re
from pathlib import Path

import yaml

SRC = Path(__file__).resolve().parent.parent / "src"
DASHBOARD = SRC / "system" / "dashboards" / "skill-state.md"
LANES = SRC / ".memoria" / "lane-overrides"
PROFILES = SRC / ".memoria" / "profiles"

FRONTMATTER = re.compile(r"^---\n(.*?)\n---", re.S)


# --- Python mirrors of the dashboard's dataviewjs parsers -------------------

def _lane_skills_js(text: str) -> dict:
    """Mirror of the dashboard's laneSkills() line parser."""
    out = {"allow": [], "deny": []}
    section, in_skills = None, False
    for raw in text.split("\n"):
        line = re.sub(r"(^|\s)#.*$", "", raw)
        if not line.strip():
            continue
        indent = len(line) - len(line.lstrip(" "))
        t = line.strip()
        if indent == 2 and t in ("allow:", "deny:"):
            section, in_skills = t[:-1], False
            continue
        if indent <= 2:
            section, in_skills = None, False
        if section and indent == 4:
            in_skills = t == "skills:"
        elif section and in_skills and t.startswith("- "):
            out[section].append(t[2:].strip())
    return out


def _skill_meta_js(text: str) -> dict:
    """Mirror of the dashboard's skillMeta() frontmatter parser."""
    m = FRONTMATTER.match(text)
    fm = m.group(1) if m else ""

    def grab(pattern):
        g = re.search(pattern, fm, re.M)
        return g.group(1).strip() if g else None

    rel = re.search(r"related_skills:\s*\[([^\]]*)\]", fm)
    return {
        "name": grab(r"^name:\s*(.+)$"),
        "skill_id": grab(r'skill_id:\s*"?([^"\n]+?)"?\s*$'),
        "profile": grab(r"^\s+profile:\s*(\S+)"),
        "lane": grab(r"^\s+lane:\s*(\S+)"),
        "related": [s.strip() for s in rel.group(1).split(",") if s.strip()] if rel else [],
    }


def _skill_files():
    return sorted(PROFILES.glob("memoria-*/skills/*/SKILL.md"))


# --- the dashboard ships and reads the right paths ---------------------------

def test_dashboard_ships_and_reads_the_runtime_layer():
    assert DASHBOARD.is_file(), "skill-state.md missing from src/system/dashboards/"
    text = DASHBOARD.read_text(encoding="utf-8")
    assert "```dataviewjs" in text
    assert '".memoria/lane-overrides"' in text, "dashboard no longer reads lane-overrides"
    assert '".memoria/profiles"' in text, "dashboard no longer reads the profile packages"


# --- lane-override files keep the shape the JS parser assumes ----------------

def test_lane_override_skills_parse_identically_to_yaml():
    files = sorted(LANES.glob("*.yaml"))
    assert files, "no lane-override files found"
    for f in files:
        text = f.read_text(encoding="utf-8")
        data = yaml.safe_load(text)
        policy = data.get("policy") or {}
        for section in ("allow", "deny"):
            expected = (policy.get(section) or {}).get("skills") or []
            assert all(isinstance(s, str) for s in expected), (
                f"{f.name}: policy.{section}.skills must be flat strings "
                "(the dashboard's line parser can't read nested values)")
            got = _lane_skills_js(text)[section]
            assert got == expected, (
                f"{f.name}: dashboard parser reads policy.{section}.skills as "
                f"{got}, YAML says {expected} — the file's indentation/format "
                "drifted from what skill-state.md assumes")


# --- SKILL.md frontmatter keeps the shape the JS parser assumes,
#     and the runtime layer is internally consistent --------------------------

def test_skill_frontmatter_matches_js_parser_and_is_consistent():
    skills = _skill_files()
    assert skills, "no SKILL.md files found under the profiles"
    seen_ids = {}
    for sk in skills:
        meta = _skill_meta_js(sk.read_text(encoding="utf-8"))
        folder, profile = sk.parent.name, sk.parent.parent.parent.name
        where = f"{profile}/skills/{folder}"
        assert meta["name"] == folder, f"{where}: frontmatter name != folder"
        assert meta["profile"] == profile, f"{where}: frontmatter profile != shipping profile"
        assert meta["lane"], f"{where}: no metadata.memoria.lane the dashboard can show"
        assert meta["skill_id"], f"{where}: no skill_id the dashboard can show"
        assert meta["skill_id"] not in seen_ids, (
            f"{where}: skill_id duplicates {seen_ids[meta['skill_id']]}")
        seen_ids[meta["skill_id"]] = where


def test_copi_desk_skill_names_match_their_direct_load_names():
    expected = {
        "ask-question-source": "ask-question-source",
        "ask-read-lens": "ask-read-lens",
        "explore-framings": "explore-framings",
        "route-task": "route-task",
        "explain-system": "explain-system",
    }
    found = {}
    for sk in sorted((PROFILES / "memoria-copi" / "skills").glob("*/SKILL.md")):
        meta = _skill_meta_js(sk.read_text(encoding="utf-8"))
        found[sk.parent.name] = meta["skill_id"]
    assert found == expected


def test_every_skill_shipping_profile_has_a_lane_override():
    for sk in _skill_files():
        profile = sk.parent.parent.parent.name
        lane_file = LANES / (profile.removeprefix("memoria-") + ".yaml")
        assert lane_file.is_file(), (
            f"{profile} ships skills but has no lane-override — "
            "the dashboard would show it as a consistency finding")
