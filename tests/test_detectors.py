"""L1 component test for detectors — extracted from its former --self-test (ADR-44)."""

import hashlib
import json as _json
from datetime import UTC
from pathlib import Path as _Path

from memoria_vault.runtime.subsystems.integrity.linter import detectors as _m

Path = _m.Path
run_all = _m.run_all
sys = _m.sys
time = _m.time
verdict = _m.verdict


def test_detectors():
    def _run():
        import tempfile

        def check(name: str, cond: bool) -> None:
            assert cond, name

        with tempfile.TemporaryDirectory() as td:
            v = Path(td)
            for d in (
                "notes/fleeting",
                "inbox/_answers",
                "catalog/sources/s1",
                "knowledge/notes",
                "knowledge/hubs",
                "knowledge/projects/proj",
                "spaces",
                "system/dashboards",
                "system/templates",
            ):
                (v / d).mkdir(parents=True, exist_ok=True)

            (v / "knowledge/notes/good.md").write_text(
                "---\ntype: note\nid: 01ARZ3NDEKTSV4RRFFQ69G5FAV\n"
                "tags: []\nlinks: {}\ntitle: Good\n---\nA note. [[good]]\n",
                encoding="utf-8",
            )
            (v / "knowledge/notes/bad.md").write_text(
                "---\ntype: note\n---\nNote with a [[ghost]] link.\n",
                encoding="utf-8",
            )
            (v / "spaces/library.md").write_text(
                "---\ntitle: Library\nprojection: space\n---\n# Library\n",
                encoding="utf-8",
            )
            (v / "knowledge/notes/notes.md.bak").write_text("x", encoding="utf-8")
            fl = v / "notes/fleeting/old.md"
            fl.write_text("idea", encoding="utf-8")
            old = time.time() - 8 * 86400
            import os

            os.utime(fl, (old, old))
            ad = v / "inbox/_answers/old-answer.md"
            ad.write_text("draft answer", encoding="utf-8")
            old_ad = time.time() - 100 * 86400
            os.utime(ad, (old_ad, old_ad))
            (v / "catalog/sources/s1/source.md").write_text(
                "---\ntype: source\ncheck_status: checked\ntitle: S1\n"
                "description: Source one\nsource_id: s1\ncontent_path: missing/content.md\n---\n",
                encoding="utf-8",
            )
            (v / "knowledge/notes/oldnote.md").write_text(
                "---\ntype: note\nid: 01ARZ3NDEKTSV4RRFFQ69G5FAW\n"
                "tags: []\nlinks: {}\ntitle: Old\nstatus: superseded\n---\nOld note.\n",
                encoding="utf-8",
            )
            (v / "knowledge/projects/proj/project.md").write_text(
                "---\ntype: project\nid: 01ARZ3NDEKTSV4RRFFQ69G5FAX\n"
                "tags: []\nlinks: {}\ntitle: P\ndescription: Project\n---\n"
                "We still rely on [[oldnote]] here.\n",
                encoding="utf-8",
            )
            (v / "system/templates/note.md").write_text(
                "---\ntype: note\ncheck_status: unchecked\ntitle: T\n---\n"
                "Example link: [[placeholder-target]]\n",
                encoding="utf-8",
            )
            (v / "home.md").write_text(
                "---\ncreated: 2026-01-01\ncssclasses:\n  - dashboard\n---\n# Home\n",
                encoding="utf-8",
            )
            (v / "knowledge/notes/tablelink.md").write_text(
                "---\ntype: note\nid: 01ARZ3NDEKTSV4RRFFQ69G5FAY\n"
                "tags: []\nlinks: {}\ntitle: Table\n---\n"
                "| col | [[good\\|Good]] |\n",
                encoding="utf-8",
            )
            (v / "system/dashboards/d.md").write_text(
                '```dataview\nTABLE check_status, projct\nFROM "knowledge"\nSORT file.mtime DESC\n```\n',
                encoding="utf-8",
            )
            (v / "knowledge/hubs/stray-note.md").write_text(
                "---\ntype: note\nid: 01ARZ3NDEKTSV4RRFFQ69G5FAZ\n"
                "tags: []\nlinks: {}\ntitle: Stray\n---\nWrong home.\n",
                encoding="utf-8",
            )
            (v / "70-misc").mkdir(parents=True, exist_ok=True)
            (v / "70-misc/scratch.md").write_text("notes", encoding="utf-8")
            (v / ".githooks").mkdir(parents=True, exist_ok=True)
            (v / ".githooks/pre-commit").write_text("#!/usr/bin/env bash\n", encoding="utf-8")
            import json as _json
            from datetime import datetime, timedelta

            _ts = lambda hours: (datetime.now(UTC) - timedelta(hours=hours)).strftime(
                "%Y-%m-%dT%H:%M:%SZ"
            )
            (v / "system/logs").mkdir(parents=True, exist_ok=True)
            import hashlib as _hashlib

            (v / "knowledge/projects/x").mkdir(parents=True, exist_ok=True)
            (v / "knowledge/projects/x/ok.md").write_text("ok body", encoding="utf-8")
            _ok_hash = "sha256:" + _hashlib.sha256(b"ok body").hexdigest()
            (v / "system/logs/audit.jsonl").write_text(
                "\n".join(
                    _json.dumps(r)
                    for r in [
                        # unpaired, 2h old -> fires
                        {
                            "timestamp": _ts(2),
                            "actor": "adapter",
                            "action": "write",
                            "path": "knowledge/projects/x/lost.md",
                            "request_id": "REQ-LOST",
                            "decision": "allow_with_log",
                            "before_hash": "sha256:" + "a" * 64,
                        },
                        # paired (same path+request_id completed) -> silent
                        {
                            "timestamp": _ts(2),
                            "actor": "adapter",
                            "action": "write",
                            "path": "knowledge/projects/x/ok.md",
                            "request_id": "REQ-OK",
                            "decision": "allow_with_log",
                            "before_hash": "sha256:" + "b" * 64,
                        },
                        {
                            "timestamp": _ts(2),
                            "actor": "adapter",
                            "action": "write",
                            "path": "knowledge/projects/x/ok.md",
                            "request_id": "REQ-OK",
                            "decision": "write_complete",
                            "before_hash": "sha256:" + "b" * 64,
                            "after_hash": _ok_hash,
                        },
                        # unpaired but fresh (10 min) -> still within the grace window
                        {
                            "timestamp": _ts(0.17),
                            "actor": "adapter",
                            "action": "write",
                            "path": "knowledge/projects/x/fresh.md",
                            "request_id": "REQ-FRESH",
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
                any("source.md" in x.path for x in by("extract-path-broken")),
            )
            check(
                "schema-check flags malformed note",
                any("bad.md" in x.path for x in by("schema-check")),
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
                "schema-check exempts navigation spaces",
                not any("spaces/library.md" in x.path for x in by("schema-check")),
            )
            check(
                "dashboard-field-drift flags 'projct'",
                any("projct" in x.message for x in by("dashboard-field-drift")),
            )
            check(
                "dashboard-field-drift ignores 'check_status'",
                not any("'check_status'" in x.message for x in by("dashboard-field-drift")),
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
                "fama-exposure flags project citing superseded note",
                any("oldnote" in x.message for x in by("fama-exposure")),
            )
            check(
                "fama-exposure ignores live note good",
                not any("good" in x.message for x in by("fama-exposure")),
            )
            check(
                "misplaced-note flags note under the wrong knowledge home",
                any("knowledge/hubs/stray-note.md" in x.path for x in by("misplaced-note")),
            )
            check(
                "misplaced-note ignores correctly-placed note",
                not any("knowledge/notes/good.md" in x.path for x in by("misplaced-note")),
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
                "misplaced-note ignores spaces root",
                not any(x.path == "spaces" for x in by("misplaced-note")),
            )
            check(
                "audit-unpaired-writes flags the stale unpaired allow",
                any(
                    x.path == "knowledge/projects/x/lost.md" and "REQ-LOST" in x.message
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

    _run()


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
    src = _Path(__file__).resolve().parent.parent / "vault-template"
    assert _m.design_system_drift(src) == []


# --------------------------------------------------------------------------- #
# vault-hash-drift (#392), audit-log-size (#393), hub-threshold (#426),
# skeleton-drift (#394)
# --------------------------------------------------------------------------- #
_EMPTY = "sha256:" + hashlib.sha256(b"").hexdigest()


def _sha(b: bytes) -> str:
    return "sha256:" + hashlib.sha256(b).hexdigest()


def _wc(path, after, action="write", request="REQ1", ts="2026-01-01T10:00:00Z"):
    return {
        "timestamp": ts,
        "actor": "adapter",
        "action": action,
        "path": path,
        "request_id": request,
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
    (v / "knowledge/notes").mkdir(parents=True)
    (v / "knowledge/notes/off-topic.md").write_text(
        "---\ntype: note\nid: 01ARZ3NDEKTSV4RRFFQ69G5FB0\n"
        "tags: []\nlinks: {}\ntitle: Off topic\ntopics: [not-a-topic]\n---\n",
        encoding="utf-8",
    )

    findings = _m.frontmatter_schema_check(v)
    messages = "\n".join(f.message for f in findings)
    assert "topics: off-vocabulary" in messages


def _topic_note(v, name, topics):
    (v / "knowledge/notes").mkdir(parents=True, exist_ok=True)
    (v / f"knowledge/notes/{name}.md").write_text(
        "---\ntype: note\nid: 01ARZ3NDEKTSV4RRFFQ69G5FB1\n"
        f"tags: []\nlinks: {{}}\ntitle: {name}\ntopics: {topics}\n---\nBody.\n",
        encoding="utf-8",
    )


def test_hub_threshold(tmp_path):
    v = tmp_path
    for i in range(2):
        _topic_note(v, f"sleep-{i}", "[Sleep]")
    (v / "catalog/sources/p1").mkdir(parents=True, exist_ok=True)
    (v / "catalog/sources/p1/source.md").write_text(
        "---\ntype: source\ncheck_status: checked\ntitle: P1\n"
        "description: Source\nsource_id: p1\nresearch_area: [sleep]\n---\n",
        encoding="utf-8",
    )
    # below threshold -> no finding
    assert _m.hub_threshold(v, threshold=4) == []
    # above threshold (3 records, sources + notes, case-insensitive) -> finding
    f = _m.hub_threshold(v, threshold=3)
    assert len(f) == 1 and f[0].severity == "LOW" and "sleep" in f[0].message.lower()
    # an existing hub for the topic suppresses the alert
    (v / "knowledge/hubs").mkdir(parents=True, exist_ok=True)
    (v / "knowledge/hubs/sleep.md").write_text(
        "---\ntype: hub\nid: hubs/sleep\ncheck_status: checked\nstanding: current\n"
        "links: {}\ntitle: Sleep\ndescription: Sleep topic\n---\n",
        encoding="utf-8",
    )
    assert _m.hub_threshold(v, threshold=3) == []


def test_hub_threshold_default_threshold_is_15(tmp_path):
    v = tmp_path
    for i in range(14):
        _topic_note(v, f"t-{i}", "[memory]")
    assert _m.hub_threshold(v) == []
    _topic_note(v, "t-14", "[memory]")
    f = _m.hub_threshold(v)
    assert len(f) == 1 and "15 notes" in f[0].message


def test_inbox_attention_projection_is_not_typed_or_stray(tmp_path):
    v = tmp_path
    (v / "inbox").mkdir()
    (v / "inbox/gap-map-corpus.md").write_text(
        "---\ntitle: Gap\nprojection: attention\nattention_kind: gap\nattention_status: open\n---\n",
        encoding="utf-8",
    )

    schema = _m.frontmatter_schema_check(v)
    misplaced = _m.misplaced_note(v)

    assert not any(f.path == "inbox/gap-map-corpus.md" for f in schema)
    assert not any(f.path == "inbox/gap-map-corpus.md" for f in misplaced)
    assert not any(f.path == "inbox" for f in misplaced)


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
    """No golden manifest = never scaffolded (e.g. vault-template/) -> silent."""
    assert _m.skeleton_drift(tmp_path) == []
