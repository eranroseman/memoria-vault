"""L1 component test for sweeps — extracted from its former --self-test (ADR-44)."""
import reconcile as _m
globals().update({k: getattr(_m, k) for k in dir(_m) if not k.startswith("__")})


def test_sweeps():
    def _run():
        import tempfile
        with tempfile.TemporaryDirectory() as td:
            v = Path(td)
            papers = v / "catalog/papers"
            papers.mkdir(parents=True)
            # one captured/tier0 note (a retry target) + one already-enriched + one proposed
            (papers / "stuck2024A.md").write_text(
                "---\ncitekey: stuck2024A\nlifecycle: captured\ningest_status: tier0\n---\n")
            (papers / "done2024B.md").write_text(
                "---\ncitekey: done2024B\nlifecycle: captured\ningest_status: enriched\n---\n")
            (papers / "live2024C.md").write_text(
                "---\ncitekey: live2024C\nlifecycle: proposed\ningest_status: complete\n---\n")
            # capture log: A + B present on disk, ghost2024Z never landed
            log = v / "capture-intake.jsonl"
            log.write_text(
                '{"citekey": "stuck2024A", "note_path": "catalog/papers/stuck2024A.md"}\n'
                '{"citekey": "done2024B"}\n'
                '{"citekey": "ghost2024Z"}\n'
                "not-json-skip-me\n")

            recs = read_log(log)
            rec = reconcile(log, v, dry_run=True)
            ret = retry(v, dry_run=True)
            checks = [
                ("log parses, bad line skipped", set(recs) == {"stuck2024A", "done2024B", "ghost2024Z"}),
                ("note_for finds on-disk note", note_for("stuck2024A", v) is not None),
                ("note_for misses ghost", note_for("ghost2024Z", v) is None),
                ("reconcile flags only the orphan", [e["citekey"] for e in rec["enqueued"]] == ["ghost2024Z"]),
                ("retry selects only captured+tier0", [e["citekey"] for e in ret["enqueued"]] == ["stuck2024A"]),
                ("dry-run enqueues nothing live", all(e["card"] == "DRY" for e in rec["enqueued"] + ret["enqueued"])),
            ]
        bad = [n for n, ok in checks if not ok]
        for n, ok in checks:
            print(f"  {'PASS' if ok else 'FAIL'}  {n}")
        print(f"\n{'OK' if not bad else f'{len(bad)} FAILING'}: sweeps.py self-test")
        return 1 if bad else 0
    assert _run() == 0
