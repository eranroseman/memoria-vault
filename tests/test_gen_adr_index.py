"""L1 component test for gen-adr-index — extracted from its former --self-test (ADR-44)."""
from _util import load_script

_m = load_script("scripts/gen-adr-index.py")
END = _m.END
Path = _m.Path
START = _m.START
_dateish = _m._dateish
_written = _m._written
build = _m.build
collect_adrs = _m.collect_adrs
parse_adr = _m.parse_adr
render_table = _m.render_table
splice = _m.splice
status_cell = _m.status_cell
validate_adr = _m.validate_adr


def test_gen_adr_index():
    def _run():
        import tempfile

        failures = 0

        def check(name: str, cond: bool) -> None:
            nonlocal failures
            print(f"  {'PASS' if cond else 'FAIL'}  {name}")
            failures += 0 if cond else 1

        # --- parse_adr ---
        fm = "---\ntopic: decisions\nid: 28\ntitle: Write gate, a plugin\nstatus: accepted\ndate_proposed: 2026-06-01\ndate_resolved: 2026-06-01\nassumes: []\nsupersedes: []\nsuperseded_by: []\n---\n# body"
        adr = parse_adr(fm)
        check("parse_adr: id", adr["id"] == 28)
        check("parse_adr: title with comma", adr["title"] == "Write gate, a plugin")
        check("parse_adr: status", adr["status"] == "accepted")
        check("parse_adr: empty superseded_by", adr["superseded_by"] == [])
        check("validate_adr: full frontmatter passes", validate_adr(Path("docs/adr/28-x.md"), adr) == [])

        sup = parse_adr("---\ntopic: decisions\nid: 27\ntitle: Old\nstatus: superseded\ndate_proposed: 2026-06-01\ndate_resolved: 2026-06-02\nassumes: []\nsupersedes: []\nsuperseded_by: [28]\n---\n")
        check("parse_adr: superseded_by list", sup["superseded_by"] == [28])
        check("status_cell: supersession arrow", status_cell(sup) == "superseded → ADR-28")
        check("status_cell: plain", status_cell(adr) == "accepted")

        bad = parse_adr("---\nid: 3\ntitle: Bad\nstatus: deferred\ndate_proposed: 2026-06-01\ndate_resolved: 2026-06-02\n---\n")
        bad_errs = validate_adr(Path("docs/adr/03-bad.md"), bad)
        check("validate_adr: missing keys flagged", any("missing frontmatter key `assumes`" in e for e in bad_errs))
        check("validate_adr: unresolved date_resolved flagged", any("must leave date_resolved blank" in e for e in bad_errs))

        malformed = parse_adr("---\ntopic: decisions\nid: xx\ntitle: Bad\nstatus: banana\ndate_proposed: soon\ndate_resolved:\nassumes: []\nsupersedes: []\nsuperseded_by: []\n---\n")
        malformed_errs = validate_adr(Path("docs/adr/bad.md"), malformed)
        check("parse_adr: nonnumeric id -> None", malformed["id"] is None)
        check("validate_adr: invalid status flagged", any("invalid status `banana`" in e for e in malformed_errs))
        check("validate_adr: bad date_proposed flagged", any("date_proposed must be" in e for e in malformed_errs))

        accepted_open = parse_adr("---\ntopic: decisions\nid: 4\ntitle: Bad\nstatus: accepted\ndate_proposed: 2026-06-01\ndate_resolved:\nassumes: []\nsupersedes: []\nsuperseded_by: []\n---\n")
        check("validate_adr: accepted must resolve",
              any("accepted ADR must set date_resolved" in e for e in validate_adr(Path("docs/adr/04-bad.md"), accepted_open)))

        superseded_missing_by = parse_adr("---\ntopic: decisions\nid: 5\ntitle: Bad\nstatus: superseded\ndate_proposed: 2026-06-01\ndate_resolved: 2026-06-02\nassumes: []\nsupersedes: []\nsuperseded_by: []\n---\n")
        check("validate_adr: superseded must point forward",
              any("superseded ADR must set superseded_by" in e
                  for e in validate_adr(Path("docs/adr/05-bad.md"), superseded_missing_by)))

        proposed = parse_adr("---\ntopic: decisions\nid: 6\ntitle: Proposal\nstatus: proposed\ndate_proposed: 2026-06-01\ndate_resolved:\nassumes: [1]\nsupersedes: []\nsuperseded_by: []\n---\n")
        check("validate_adr: proposed unresolved passes", validate_adr(Path("docs/adr/06-proposed.md"), proposed) == [])
        check("_dateish: valid date", _dateish("2026-06-14"))
        check("_dateish: invalid date", not _dateish("2026-6-14"))

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
            (adr_dir / "01-alpha.md").write_text("---\ntopic: decisions\nid: 1\ntitle: Alpha\nstatus: accepted\ndate_proposed: 2026-06-01\ndate_resolved: 2026-06-01\nassumes: []\nsupersedes: []\nsuperseded_by: []\n---\n")
            (adr_dir / "02-beta.md").write_text("---\ntopic: decisions\nid: 2\ntitle: Beta\nstatus: superseded\ndate_proposed: 2026-06-01\ndate_resolved: 2026-06-02\nassumes: []\nsupersedes: []\nsuperseded_by: [1]\n---\n")
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

            (adr_dir / "03-no-id.md").write_text("---\ntopic: decisions\nid: xx\ntitle: No ID\nstatus: accepted\ndate_proposed: 2026-06-01\ndate_resolved: 2026-06-01\nassumes: []\nsupersedes: []\nsuperseded_by: []\n---\n")
            try:
                collect_adrs(adr_dir)
                check("collect_adrs: nonnumeric id raises", False)
            except SystemExit as e:
                check("collect_adrs: nonnumeric id raises", "no numeric 'id'" in str(e))
            (adr_dir / "03-no-id.md").unlink()

            (adr_dir / "03-invalid.md").write_text("---\ntopic: decisions\nid: 3\ntitle: Invalid\nstatus: accepted\ndate_proposed: 2026-06-01\ndate_resolved:\nassumes: []\nsupersedes: []\nsuperseded_by: []\n---\n")
            try:
                collect_adrs(adr_dir)
                check("collect_adrs: invalid frontmatter raises", False)
            except SystemExit as e:
                check("collect_adrs: invalid frontmatter raises", "ADR frontmatter invalid" in str(e))
            (adr_dir / "03-invalid.md").unlink()

            readme.write_text("# Decisions\n\nno markers here\n")
            try:
                build(adr_dir, readme)
                check("build: missing markers raises", False)
            except SystemExit:
                check("build: missing markers raises", True)

        print(f"\n{'OK' if not failures else f'{failures} FAILING'}: gen-adr-index self-test")
        return 1 if failures else 0
    assert _run() == 0
