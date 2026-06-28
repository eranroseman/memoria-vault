"""L1 component test for detectors — extracted from its former --self-test (ADR-44)."""

import hashlib
import json as _json
from datetime import UTC
from pathlib import Path as _Path

from _util import CheckHarness
from operations.integrity.linter import detectors as _m

Path = _m.Path
run_all = _m.run_all
sys = _m.sys
time = _m.time
verdict = _m.verdict


def test_detectors():
    def _run():
        __file__ = _m.__file__
        import tempfile

        sys.path.insert(0, str(Path(__file__).resolve().parents[5] / "mcp"))

        t = CheckHarness()
        check = t.check

        with tempfile.TemporaryDirectory() as td:
            v = Path(td)
            # folder skeleton
            for d in (
                "notes/fleeting",
                "catalog/papers",
                "notes/claims",
                "system/dashboards",
                "system/templates",
                "inbox/_answers",
            ):
                (v / d).mkdir(parents=True, exist_ok=True)

            # clean claim note (no findings)
            (v / "notes/claims/good.md").write_text(
                "---\ntype: claim\nlifecycle: current\nmaturity: seedling\ntitle: Good\nsources: ['@smith2020']\n---\nA claim. [[good]]\n",
                encoding="utf-8",
            )
            # claim note missing 'maturity' -> schema finding
            (v / "notes/claims/bad.md").write_text(
                "---\ntype: claim\nlifecycle: current\n---\nClaim with a [[ghost]] link.\n",
                encoding="utf-8",
            )
            # leftover file outside transient zone -> orphan finding
            (v / "notes/claims/notes.md.bak").write_text("x", encoding="utf-8")
            # stale fleeting note (8 days old) -> stale finding
            fl = v / "notes/fleeting/old.md"
            fl.write_text("idea", encoding="utf-8")
            old = time.time() - 8 * 86400
            import os

            os.utime(fl, (old, old))
            # stale answer draft (100 days old) -> stale-answer-drafts finding
            ad = v / "inbox/_answers/old-answer.md"
            ad.parent.mkdir(parents=True, exist_ok=True)
            ad.write_text("draft answer", encoding="utf-8")
            old_ad = time.time() - 100 * 86400
            os.utime(ad, (old_ad, old_ad))
            # paper note with broken extract_path -> extract finding
            (v / "catalog/papers/p.md").write_text(
                "---\ntype: paper\ncitekey: smith2020\nextract_path: system/extracts/missing.md\n---\n",
                encoding="utf-8",
            )
            # superseded claim + a draft that cites it -> fama-exposure finding
            (v / "notes/claims/oldclaim.md").write_text(
                "---\ntype: claim\nlifecycle: archived\nsuperseded_by: newclaim\n---\nOld claim.\n",
                encoding="utf-8",
            )
            dft = v / "projects/proj/draft.md"
            dft.parent.mkdir(parents=True, exist_ok=True)
            dft.write_text(
                "---\ntype: draft\n---\nWe still rely on [[oldclaim]] here.\n", encoding="utf-8"
            )
            # current thesis without promotion provenance -> schema finding
            (v / "projects/proj/thesis.md").write_text(
                "---\ntype: thesis\nlifecycle: current\ntitle: T\nproject: '[[proj]]'\nsources: []\n---\n",
                encoding="utf-8",
            )
            # template + dashboard referencing an unknown field -> dashboard finding.
            # The template body carries a placeholder [[link]] (templates are raw notes):
            # broken-wikilink must ignore it now that templates live in system/.
            (v / "system/templates/claim.md").write_text(
                "---\ntype: claim\nlifecycle: current\nmaturity: seedling\n---\n"
                "Example link: [[placeholder-target]]\n",
                encoding="utf-8",
            )
            # vault-root navigation page: has frontmatter, no type -> NOT a typed document
            (v / "home.md").write_text(
                "---\ncreated: 2026-01-01\ncssclasses:\n  - dashboard\n---\n# Home\n",
                encoding="utf-8",
            )
            # a real note with a table-escaped aliased link to an existing note ([[good]]):
            # the "\|" must resolve, not read as a broken "good\" target.
            (v / "notes/claims/tablelink.md").write_text(
                "---\ntype: claim\nlifecycle: current\nmaturity: seedling\n---\n"
                "| col | [[good\\|Good]] |\n",
                encoding="utf-8",
            )
            (v / "system/dashboards/d.md").write_text(
                '```dataview\nTABLE maturity, projct\nFROM "notes"\nSORT file.mtime DESC\n```\n',
                encoding="utf-8",
            )
            # claim sitting under catalog/ -> misplaced-note finding. The
            # correctly-placed claims above (good.md/bad.md) must NOT fire.
            (v / "catalog/papers/stray-claim.md").write_text(
                "---\ntype: claim\nlifecycle: current\nmaturity: seedling\n---\nClaim in the wrong home.\n",
                encoding="utf-8",
            )
            # stray top-level folder -> misplaced-note LOW finding
            (v / "70-misc").mkdir(parents=True, exist_ok=True)
            (v / "70-misc/scratch.md").write_text("notes", encoding="utf-8")
            # shipped hidden implementation folders are not authored vault homes
            (v / ".githooks").mkdir(parents=True, exist_ok=True)
            (v / ".githooks/post-commit").write_text("#!/usr/bin/env bash\n", encoding="utf-8")
            # audit chain: an unpaired mutating allow older than 1h -> MEDIUM
            # finding; a paired one and a fresh (<1h) unpaired one stay silent.
            import json as _json
            from datetime import datetime, timedelta

            _ts = lambda hours: (datetime.now(UTC) - timedelta(hours=hours)).strftime(
                "%Y-%m-%dT%H:%M:%SZ"
            )
            (v / "system/logs").mkdir(parents=True, exist_ok=True)
            # the completed write's file exists with its audited content, so
            # vault-hash-drift stays silent over this fixture (tested separately)
            import hashlib as _hashlib

            (v / "projects/x").mkdir(parents=True, exist_ok=True)
            (v / "projects/x/ok.md").write_text("ok body", encoding="utf-8")
            _ok_hash = "sha256:" + _hashlib.sha256(b"ok body").hexdigest()
            (v / "system/logs/audit.jsonl").write_text(
                "\n".join(
                    _json.dumps(r)
                    for r in [
                        # unpaired, 2h old -> fires
                        {
                            "timestamp": _ts(2),
                            "profile": "memoria-writer",
                            "action": "write",
                            "path": "projects/x/lost.md",
                            "task_id": "T-LOST",
                            "decision": "allow_with_log",
                            "before_hash": "sha256:" + "a" * 64,
                        },
                        # paired (same path+task_id completed) -> silent
                        {
                            "timestamp": _ts(2),
                            "profile": "memoria-writer",
                            "action": "write",
                            "path": "projects/x/ok.md",
                            "task_id": "T-OK",
                            "decision": "allow_with_log",
                            "before_hash": "sha256:" + "b" * 64,
                        },
                        {
                            "timestamp": _ts(2),
                            "profile": "memoria-writer",
                            "action": "write",
                            "path": "projects/x/ok.md",
                            "task_id": "T-OK",
                            "decision": "write_complete",
                            "before_hash": "sha256:" + "b" * 64,
                            "after_hash": _ok_hash,
                        },
                        # unpaired but fresh (10 min) -> still within the grace window
                        {
                            "timestamp": _ts(0.17),
                            "profile": "memoria-writer",
                            "action": "write",
                            "path": "projects/x/fresh.md",
                            "task_id": "T-FRESH",
                            "decision": "allow_with_log",
                            "before_hash": "sha256:" + "d" * 64,
                        },
                    ]
                )
                + "\n",
                encoding="utf-8",
            )

            f = run_all(v)
            by = lambda name: [x for x in f if x.detector == name]

            check(
                "orphan-working-files fires on .bak",
                any("notes.md.bak" in x.path for x in by("orphan-working-files")),
            )
            check(
                "stale-fleeting fires on 8d note",
                any("old.md" in x.path for x in by("stale-fleeting")),
            )
            check(
                "stale-answer-drafts fires on 100d draft",
                any("old-answer.md" in x.path for x in by("stale-answer-drafts")),
            )
            check(
                "extract-path-broken fires",
                any("p.md" in x.path for x in by("extract-path-broken")),
            )
            check(
                "schema-check flags missing maturity",
                any("bad.md" in x.path for x in by("schema-check")),
            )
            check(
                "schema-check flags unstamped current thesis",
                any(
                    "thesis.md" in x.path and "promoted_at" in x.message for x in by("schema-check")
                ),
            )
            check(
                "schema-check clean note not flagged",
                not any("good.md" in x.path for x in by("schema-check")),
            )
            check(
                "broken-wikilink flags [[ghost]]",
                any("ghost" in x.message for x in by("broken-wikilink")),
            )
            check(
                "broken-wikilink ignores valid [[good]]",
                not any("[[good]]" in x.message for x in by("broken-wikilink")),
            )
            check(
                "broken-wikilink ignores template placeholder link",
                not any("placeholder-target" in x.message for x in by("broken-wikilink")),
            )
            check(
                "broken-wikilink resolves a table-escaped alias [[good\\|Good]]",
                not any("tablelink.md" in x.path for x in by("broken-wikilink")),
            )
            check(
                "schema-check exempts vault-root nav page (home.md)",
                not any("home.md" in x.path for x in by("schema-check")),
            )
            check(
                "dashboard-field-drift flags 'projct'",
                any("projct" in x.message for x in by("dashboard-field-drift")),
            )
            check(
                "dashboard-field-drift ignores 'maturity'",
                not any("'maturity'" in x.message for x in by("dashboard-field-drift")),
            )
            check(
                "graph-analyze flags orphan bad.md",
                any("bad.md" in x.path for x in by("graph-analyze")),
            )
            check(
                "graph-analyze ignores linked good.md",
                not any("good.md" in x.path for x in by("graph-analyze")),
            )
            check(
                "fama-exposure flags draft citing superseded claim",
                any("oldclaim" in x.message for x in by("fama-exposure")),
            )
            check(
                "fama-exposure ignores live claim good",
                not any("good" in x.message for x in by("fama-exposure")),
            )
            check(
                "misplaced-note flags claim under 20-sources/",
                any("stray-claim.md" in x.path for x in by("misplaced-note")),
            )
            check(
                "misplaced-note ignores correctly-placed claim",
                not any("01-claims/good.md" in x.path for x in by("misplaced-note")),
            )
            check(
                "misplaced-note flags stray top-level folder",
                any(x.path == "70-misc" for x in by("misplaced-note")),
            )
            check(
                "misplaced-note ignores shipped hidden implementation folder",
                not any(x.path == ".githooks" for x in by("misplaced-note")),
            )
            check(
                "audit-unpaired-writes flags the stale unpaired allow",
                any(
                    x.path == "projects/x/lost.md" and "T-LOST" in x.message
                    for x in by("audit-unpaired-writes")
                ),
            )
            check(
                "audit-unpaired-writes ignores the paired write",
                not any("ok.md" in x.path for x in by("audit-unpaired-writes")),
            )
            check(
                "audit-unpaired-writes ignores the fresh (<1h) unpaired write",
                not any("fresh.md" in x.path for x in by("audit-unpaired-writes")),
            )
            check("verdict is REVIEW (HIGH+MEDIUM, no CRITICAL)", verdict(f) == "REVIEW")

        return t.summary(label="detectors")

    assert _run() == 0


def _write_design_spec(v: _Path):
    (v / ".memoria").mkdir(parents=True, exist_ok=True)
    (v / ".memoria/design-system.md").write_text(
        '```yaml\npalette:\n  primary: "#5B7EC2"\n  warning: "#C47F00"\n\n'
        "typography:\n  scale:\n    body: 15px / 24px / 400\n    h2: 22px / 30px / 600\n```\n",
        encoding="utf-8",
    )


def test_design_system_drift_detects_visual_anti_patterns(tmp_path):
    v = tmp_path
    _write_design_spec(v)
    (v / ".obsidian/snippets").mkdir(parents=True, exist_ok=True)
    (v / ".obsidian/snippets/bad.css").write_text(
        ".x { color: #FF00FF; font-size: 18.5px; }\n",
        encoding="utf-8",
    )
    (v / "notes/fleeting").mkdir(parents=True, exist_ok=True)
    (v / "notes/fleeting/🔥-idea.md").write_text(
        "---\ntitle: Claim Note 🔥\ntype: fleeting\nlifecycle: proposed\n---\n"
        "> [!warning|red] Warning\n\nThis permanent note says paper note.\n",
        encoding="utf-8",
    )

    findings = _m.design_system_drift(v)
    messages = "\n".join(f.message for f in findings)
    assert any(f.detector == "design-system-drift" for f in findings)
    assert "off-palette color #ff00ff" in messages
    assert "font-size 18.5px" in messages
    assert "emoji in note title" in messages
    assert "rainbow/ad-hoc callout" in messages
    assert "terminology/capitalization drift" in messages


def test_design_system_drift_accepts_shipped_vault_tree():
    src = _Path(__file__).resolve().parent.parent / "src"
    assert _m.design_system_drift(src) == []


# --------------------------------------------------------------------------- #
# vault-hash-drift (#392), audit-log-size (#393), hub-threshold (#426),
# skeleton-drift (#394)
# --------------------------------------------------------------------------- #
_EMPTY = "sha256:" + hashlib.sha256(b"").hexdigest()


def _sha(b: bytes) -> str:
    return "sha256:" + hashlib.sha256(b).hexdigest()


def _wc(path, after, action="write", task="T1", ts="2026-01-01T10:00:00Z"):
    return {
        "timestamp": ts,
        "profile": "memoria-writer",
        "action": action,
        "path": path,
        "task_id": task,
        "decision": "write_complete",
        "before_hash": _EMPTY,
        "after_hash": after,
    }


def _write_audit(v: _Path, records, extra_lines=()):
    (v / "system/logs").mkdir(parents=True, exist_ok=True)
    lines = [_json.dumps(r) for r in records] + list(extra_lines)
    (v / "system/logs/audit.jsonl").write_text("\n".join(lines) + "\n", encoding="utf-8")


def test_vault_hash_drift(tmp_path):
    v = tmp_path
    (v / "projects").mkdir()
    # match: on-disk bytes == latest after_hash -> silent
    (v / "projects/clean.md").write_bytes(b"CLEAN")
    # mismatch: edited out-of-band after the audited write -> CRITICAL
    (v / "projects/tampered.md").write_bytes(b"TAMPERED")
    # completed delete, file absent -> silent (empty-hash convention)
    # out-of-band delete: audited content but file missing -> CRITICAL
    # never-audited file on disk -> ignored
    (v / "projects/unaudited.md").write_bytes(b"whatever")
    _write_audit(
        v,
        [
            # last write wins: a stale earlier hash for clean.md must not fire
            _wc("projects/clean.md", _sha(b"OLD"), ts="2026-01-01T09:00:00Z"),
            _wc("projects/clean.md", _sha(b"CLEAN"), ts="2026-01-01T10:00:00Z"),
            _wc("projects/tampered.md", _sha(b"ORIGINAL")),
            _wc("projects/deleted.md", _EMPTY, action="delete"),
            _wc("projects/vanished.md", _sha(b"WAS HERE")),
        ],
        extra_lines=["{not json", ""],
    )  # malformed lines are skipped
    f = _m.vault_hash_drift(v)
    by_path = {x.path: x for x in f}
    assert all(x.severity == "CRITICAL" for x in f)
    assert "projects/clean.md" not in by_path
    assert "projects/deleted.md" not in by_path
    assert "projects/unaudited.md" not in by_path
    assert "edited" in by_path["projects/tampered.md"].message
    assert "missing" in by_path["projects/vanished.md"].message
    assert set(by_path) == {"projects/tampered.md", "projects/vanished.md"}


def test_vault_hash_drift_no_log(tmp_path):
    assert _m.vault_hash_drift(tmp_path) == []


def test_audit_log_size(tmp_path):
    v = tmp_path
    _write_audit(v, [_wc("projects/a.md", _EMPTY)])
    assert _m.audit_log_size(v) == []  # tiny log: silent
    f = _m.audit_log_size(v, max_mb=0.000001)  # over threshold
    assert len(f) == 1 and f[0].severity == "LOW"
    assert f[0].detector == "audit-log-size"


def test_append_findings_jsonl_creates_append_only_signal(tmp_path):
    out = tmp_path / "system/logs/lint-findings.jsonl"
    findings = [
        _m.Finding("schema-check", "MEDIUM", "notes/fleeting/x.md", "bad lifecycle"),
        _m.Finding("broken-wikilink", "LOW", "notes/claims/y.md", "missing target"),
    ]
    for f in findings:
        f.timestamp = "2026-06-15T02:40:00Z"

    _m.append_findings_jsonl(out, findings[:1])
    _m.append_findings_jsonl(out, findings[1:])

    rows = [_json.loads(line) for line in out.read_text(encoding="utf-8").splitlines()]
    assert [row["detector"] for row in rows] == ["schema-check", "broken-wikilink"]
    assert rows[0]["timestamp"] == "2026-06-15T02:40:00Z"


def test_append_findings_jsonl_touches_empty_file_for_clean_runs(tmp_path):
    out = tmp_path / "system/logs/lint-findings.jsonl"
    _m.append_findings_jsonl(out, [])
    assert out.is_file()
    assert out.read_text(encoding="utf-8") == ""


def test_schema_check_flags_off_vocabulary_values(tmp_path):
    v = tmp_path
    (v / "system").mkdir(parents=True)
    (v / "system/vocabulary.md").write_text(
        "# Vocabulary\n\n"
        "## research_area\n\n"
        "- mobile-health — Mobile health.\n\n"
        "## methodology\n\n"
        "- review — Review.\n\n"
        "## topics\n",
        encoding="utf-8",
    )
    (v / "notes/claims").mkdir(parents=True)
    (v / "notes/claims/off-topic.md").write_text(
        "---\ntype: claim\nlifecycle: current\nmaturity: seedling\n"
        "title: Off topic\nsources: []\ntopics: [Sleep]\n---\n",
        encoding="utf-8",
    )
    (v / "notes/sources").mkdir(parents=True)
    (v / "notes/sources/off-source.md").write_text(
        "---\ntype: source\nlifecycle: proposed\ntitle: Off source\nentity: '[[p]]'\n"
        "research_area: [Health Informatics]\nmethodology: [not-a-method]\n---\n",
        encoding="utf-8",
    )

    findings = _m.frontmatter_schema_check(v)
    messages = "\n".join(f.message for f in findings)
    assert "topics: off-vocabulary" in messages
    assert "research_area: off-vocabulary" in messages
    assert "methodology: off-vocabulary" in messages


def _claim(v, name, topics):
    (v / "notes/claims").mkdir(parents=True, exist_ok=True)
    (v / f"notes/claims/{name}.md").write_text(
        "---\ntype: claim\nlifecycle: current\nmaturity: seedling\n"
        f"title: {name}\nsources: ['@x2024']\ntopics: {topics}\n---\nBody.\n",
        encoding="utf-8",
    )


def test_hub_threshold(tmp_path):
    v = tmp_path
    for i in range(2):
        _claim(v, f"sleep-{i}", "[Sleep]")
    (v / "catalog/papers").mkdir(parents=True, exist_ok=True)
    (v / "catalog/papers/p1.md").write_text(
        "---\ntype: paper\nlifecycle: current\ncitekey: a2020\ntitle: P1\n"
        "research_area: [sleep]\n---\n",
        encoding="utf-8",
    )
    # below threshold -> no finding
    assert _m.hub_threshold(v, threshold=4) == []
    # above threshold (3 notes, papers + claims, case-insensitive) -> finding
    f = _m.hub_threshold(v, threshold=3)
    assert len(f) == 1 and f[0].severity == "LOW" and "sleep" in f[0].message.lower()
    # an existing hub for the topic suppresses the alert
    (v / "notes/hubs").mkdir(parents=True, exist_ok=True)
    (v / "notes/hubs/sleep.md").write_text(
        "---\ntype: hub\nlifecycle: current\ntitle: Sleep\ntopic: sleep\n---\n", encoding="utf-8"
    )
    assert _m.hub_threshold(v, threshold=3) == []


def test_hub_threshold_default_threshold_is_15(tmp_path):
    v = tmp_path
    for i in range(14):
        _claim(v, f"t-{i}", "[memory]")
    assert _m.hub_threshold(v) == []
    _claim(v, "t-14", "[memory]")
    f = _m.hub_threshold(v)
    assert len(f) == 1 and "15 notes" in f[0].message


def test_skeleton_drift(tmp_path):
    assert _m._FOLDERS is not None, "schema home must load in CI (PyYAML present)"
    skeleton = _m._FOLDERS["skeleton"]
    v = tmp_path
    for d in skeleton:
        (v / d).mkdir(parents=True, exist_ok=True)
    (v / ".memoria/golden").mkdir(parents=True)  # installed-vault marker
    (v / ".memoria/golden/manifest.json").write_text("{}", encoding="utf-8")
    assert _m.skeleton_drift(v) == []
    # remove one skeleton dir -> MEDIUM finding for exactly that path
    (v / "system/logs/sessions").rmdir()
    f = _m.skeleton_drift(v)
    assert [x.path for x in f] == ["system/logs/sessions"]
    assert f[0].severity == "MEDIUM" and f[0].detector == "skeleton-drift"


def test_skeleton_drift_skips_uninstalled_trees(tmp_path):
    """No golden manifest = never scaffolded (e.g. the repo's src/) -> silent."""
    assert _m.skeleton_drift(tmp_path) == []
