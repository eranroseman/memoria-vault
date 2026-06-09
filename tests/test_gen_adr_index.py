"""L1 component test for gen-adr-index — extracted from its former --self-test (ADR-44)."""
from _util import load_script
_m = load_script("scripts/gen-adr-index.py")
globals().update({k: getattr(_m, k) for k in dir(_m) if not k.startswith("__")})


def test_gen_adr_index():
    def _run():
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
    assert _run() == 0
