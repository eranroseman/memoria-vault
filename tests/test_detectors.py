"""L1 component test for detectors — extracted from its former --self-test (ADR-44)."""
import detectors as _m
from _util import TestHarness
globals().update({k: getattr(_m, k) for k in dir(_m) if not k.startswith("__")})


def test_detectors():
    def _run():
        __file__ = _m.__file__
        import tempfile

        sys.path.insert(0, str(Path(__file__).resolve().parents[5] / "mcp"))
        from _util import TestHarness

        t = TestHarness()
        check = t.check

        with tempfile.TemporaryDirectory() as td:
            v = Path(td)
            # folder skeleton
            for d in ("10-inbox/01-fleeting", "20-sources/01-papers",
                      "30-synthesis/01-claims", "00-meta/01-dashboards",
                      "99-system/templates", "90-assets/extracts"):
                (v / d).mkdir(parents=True, exist_ok=True)

            # clean claim note (no findings)
            (v / "30-synthesis/01-claims/good.md").write_text(
                "---\ntype: claim-note\nlifecycle: current\nmaturity: seedling\n---\nA claim. [[good]]\n",
                encoding="utf-8")
            # claim note missing 'maturity' -> schema finding
            (v / "30-synthesis/01-claims/bad.md").write_text(
                "---\ntype: claim-note\nlifecycle: current\n---\nClaim with a [[ghost]] link.\n",
                encoding="utf-8")
            # leftover file outside transient zone -> orphan finding
            (v / "30-synthesis/01-claims/notes.md.bak").write_text("x", encoding="utf-8")
            # stale fleeting note (8 days old) -> stale finding
            fl = v / "10-inbox/01-fleeting/old.md"
            fl.write_text("idea", encoding="utf-8")
            old = time.time() - 8 * 86400
            import os
            os.utime(fl, (old, old))
            # stale answer draft (100 days old) -> stale-answer-drafts finding
            ad = v / "10-inbox/02-answers/old-answer.md"
            ad.parent.mkdir(parents=True, exist_ok=True)
            ad.write_text("draft answer", encoding="utf-8")
            old_ad = time.time() - 100 * 86400
            os.utime(ad, (old_ad, old_ad))
            # paper note with broken extract_path -> extract finding
            (v / "20-sources/01-papers/p.md").write_text(
                "---\ntype: paper-note\ncitekey: smith2020\nextract_path: 90-assets/extracts/missing.md\n---\n",
                encoding="utf-8")
            # superseded claim + a draft that cites it -> fama-exposure finding
            (v / "30-synthesis/01-claims/oldclaim.md").write_text(
                "---\ntype: claim-note\nlifecycle: archived\nsuperseded_by: newclaim\n---\nOld claim.\n",
                encoding="utf-8")
            dft = v / "40-workbench/proj/04-drafts/draft.md"
            dft.parent.mkdir(parents=True, exist_ok=True)
            dft.write_text("---\ntype: draft\n---\nWe still rely on [[oldclaim]] here.\n", encoding="utf-8")
            # template + dashboard referencing an unknown field -> dashboard finding.
            # The template body carries a placeholder [[link]] (templates are raw notes):
            # broken-wikilink must ignore it now that templates live in 99-system/.
            (v / "99-system/templates/claim-note.md").write_text(
                "---\ntype: claim-note\nlifecycle: current\nmaturity: seedling\n---\n"
                "Example link: [[placeholder-target]]\n", encoding="utf-8")
            # vault-root navigation page: has frontmatter, no type -> NOT a typed note
            (v / "home.md").write_text(
                "---\ncreated: 2026-01-01\ncssclasses:\n  - dashboard\n---\n# Home\n", encoding="utf-8")
            # a real note with a table-escaped aliased link to an existing note ([[good]]):
            # the "\|" must resolve, not read as a broken "good\" target.
            (v / "30-synthesis/01-claims/tablelink.md").write_text(
                "---\ntype: claim-note\nlifecycle: current\nmaturity: seedling\n---\n"
                "| col | [[good\\|Good]] |\n", encoding="utf-8")
            (v / "00-meta/01-dashboards/d.md").write_text(
                "```dataview\nTABLE maturity, projct\nFROM \"30-synthesis\"\nSORT file.mtime DESC\n```\n",
                encoding="utf-8")
            # claim-note sitting under 20-sources/ -> misplaced-note finding. The
            # correctly-placed claims above (good.md/bad.md) must NOT fire.
            (v / "20-sources/01-papers/stray-claim.md").write_text(
                "---\ntype: claim-note\nlifecycle: current\nmaturity: seedling\n---\nClaim in the wrong home.\n",
                encoding="utf-8")
            # stray top-level folder -> misplaced-note LOW finding
            (v / "70-misc").mkdir(parents=True, exist_ok=True)
            (v / "70-misc/scratch.md").write_text("notes", encoding="utf-8")

            f = run_all(v)
            by = lambda name: [x for x in f if x.detector == name]

            check("orphan-working-files fires on .bak", any("notes.md.bak" in x.path for x in by("orphan-working-files")))
            check("stale-fleeting fires on 8d note", any("old.md" in x.path for x in by("stale-fleeting")))
            check("stale-answer-drafts fires on 100d draft", any("old-answer.md" in x.path for x in by("stale-answer-drafts")))
            check("extract-path-broken fires", any("p.md" in x.path for x in by("extract-path-broken")))
            check("schema-check flags missing maturity", any("bad.md" in x.path for x in by("schema-check")))
            check("schema-check clean note not flagged", not any("good.md" in x.path for x in by("schema-check")))
            check("broken-wikilink flags [[ghost]]", any("ghost" in x.message for x in by("broken-wikilink")))
            check("broken-wikilink ignores valid [[good]]", not any("[[good]]" in x.message for x in by("broken-wikilink")))
            check("broken-wikilink ignores template placeholder link", not any("placeholder-target" in x.message for x in by("broken-wikilink")))
            check("broken-wikilink resolves a table-escaped alias [[good\\|Good]]", not any("tablelink.md" in x.path for x in by("broken-wikilink")))
            check("schema-check exempts vault-root nav page (home.md)", not any("home.md" in x.path for x in by("schema-check")))
            check("dashboard-field-drift flags 'projct'", any("projct" in x.message for x in by("dashboard-field-drift")))
            check("dashboard-field-drift ignores 'maturity'", not any("'maturity'" in x.message for x in by("dashboard-field-drift")))
            check("graph-analyze flags orphan bad.md", any("bad.md" in x.path for x in by("graph-analyze")))
            check("graph-analyze ignores linked good.md", not any("good.md" in x.path for x in by("graph-analyze")))
            check("fama-exposure flags draft citing superseded claim", any("oldclaim" in x.message for x in by("fama-exposure")))
            check("fama-exposure ignores live claim good", not any("good" in x.message for x in by("fama-exposure")))
            check("misplaced-note flags claim under 20-sources/", any("stray-claim.md" in x.path for x in by("misplaced-note")))
            check("misplaced-note ignores correctly-placed claim", not any("01-claims/good.md" in x.path for x in by("misplaced-note")))
            check("misplaced-note flags stray top-level folder", any(x.path == "70-misc" for x in by("misplaced-note")))
            check("verdict is REVIEW (HIGH+MEDIUM, no CRITICAL)", verdict(f) == "REVIEW")

        return t.summary(label="detectors")
    assert _run() == 0
