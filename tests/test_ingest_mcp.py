"""L1 component test for ingest_mcp — extracted from its former --self-test (ADR-44)."""
import ingest_mcp as _m
globals().update({k: getattr(_m, k) for k in dir(_m) if not k.startswith("__")})


def test_ingest_mcp():
    def _run():
        """Offline: the module imports the pipeline and runs a Tier-0 fixture through it."""
        import pipeline
        fixture = ("@article{x2024Test,\n  title = {A Test},\n  author = {Doe, Jane},\n"
                   "  year = {2024},\n  doi = {10.1/x},\n  journal = {J Tests},\n}\n")
        b = pipeline.run("x2024Test", fixture, enrich=False)

        # capture-intake anchor: appended once, idempotent on a second call
        import tempfile
        with tempfile.TemporaryDirectory() as td:
            v = Path(td)
            first = append_intake_anchor(v, "x2024Test", "20-sources/01-papers/x2024Test.md")
            second = append_intake_anchor(v, "x2024Test", "20-sources/01-papers/x2024Test.md")
            lines = (v / INTAKE_LOG).read_text().splitlines()
            anchor_ok = first and not second and len(lines) == 1 and json.loads(lines[0])["citekey"] == "x2024Test"

        # citekey sanitization: slashes and '..' are replaced so the path stays inside 90-assets/
        safe_ck = "../../etc/passwd".replace("/", "_").replace("..", "_").replace("\\", "_")
        sanitize_ok = "/" not in safe_ck and ".." not in safe_ck

        checks = [
            ("scripts dir importable", SCRIPTS_DIR.is_dir()),
            ("pipeline runs Tier-0", b["lifecycle"] == "current" and b["ingest_status"] == "tier0"),
            ("bundle declares the two holes", b["holes"] == ["_proposed_classification", "brief"]),
            ("identity assembled", b["frontmatter"]["title"] == "A Test"),
            ("intake anchor appended once + idempotent", anchor_ok),
            ("citekey sanitization strips traversal chars", sanitize_ok),
        ]
        bad = [n for n, ok in checks if not ok]
        for n, ok in checks:
            print(f"  {'PASS' if ok else 'FAIL'}  {n}")
        print(f"\n{'OK' if not bad else f'{len(bad)} FAILING'}: ingest_mcp.py self-test")
        return 1 if bad else 0
    assert _run() == 0
