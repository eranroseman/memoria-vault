"""L1 component test for sweeps — extracted from its former --self-test (ADR-44)."""
import reconcile as _m
globals().update({k: getattr(_m, k) for k in dir(_m) if not k.startswith("__")})


def test_reconcile_intake():
    def _run():
        import tempfile
        with tempfile.TemporaryDirectory() as td:
            v = Path(td)
            papers = v / "catalog/papers"
            papers.mkdir(parents=True)
            # one tier0 note (a retry target) + one already-enriched + one complete;
            # paper entities are lifecycle: current from creation (ADR-50) — the
            # retry sweep keys on ingest_status, not lifecycle.
            (papers / "stuck2024A.md").write_text(
                "---\ncitekey: stuck2024A\nlifecycle: current\ningest_status: tier0\n---\n")
            (papers / "done2024B.md").write_text(
                "---\ncitekey: done2024B\nlifecycle: current\ningest_status: enriched\n---\n")
            (papers / "live2024C.md").write_text(
                "---\ncitekey: live2024C\nlifecycle: current\ningest_status: complete\n---\n")
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


def test_stamp_chat_exports(tmp_path):
    """Pass (c): bare ACP chat exports get valid fleeting frontmatter, once (#185)."""
    import schema

    v = tmp_path
    chats = v / "notes/fleeting/chats"
    chats.mkdir(parents=True)
    # a bare export (no frontmatter) — the stamp target
    bare = chats / "chat_2026-06-10_09-00.md"
    bare.write_text("# co-PI session\n\nUser: hello\nAgent: hi\n", encoding="utf-8")
    # an already-stamped export — must be left byte-identical
    stamped = chats / "chat_2026-06-09_15-30.md"
    stamped_text = ("---\ntitle: \"old chat\"\ntype: fleeting\nlifecycle: proposed\n"
                    "origin: chat\ncreated: 2026-06-09\n---\n\nbody\n")
    stamped.write_text(stamped_text, encoding="utf-8")
    # a non-chat fleeting note (parent folder) — out of scope, untouched
    other = v / "notes/fleeting" / "idea.md"
    other_text = "a raw human capture without frontmatter\n"
    other.write_text(other_text, encoding="utf-8")

    res = stamp_chats(v)
    assert res["stamped"] == ["notes/fleeting/chats/chat_2026-06-10_09-00.md"]
    assert res["skipped"] == 1

    # the stamped file now schema-validates as fleeting
    fm = read_frontmatter(bare)
    fleeting = schema.load_types()["fleeting"]
    assert fm.get("type") == "fleeting"
    assert fm.get("origin") == "chat"
    assert schema.validate_frontmatter(fm, fleeting) == []
    body = bare.read_text(encoding="utf-8")
    assert "User: hello" in body  # original content preserved

    # idempotent: second sweep touches nothing
    res2 = stamp_chats(v)
    assert res2["stamped"] == [] and res2["skipped"] == 2
    assert bare.read_text(encoding="utf-8") == body
    assert stamped.read_text(encoding="utf-8") == stamped_text
    assert other.read_text(encoding="utf-8") == other_text

    # dry-run reports but does not write
    extra = chats / "chat_new.md"
    extra.write_text("raw\n", encoding="utf-8")
    res3 = stamp_chats(v, dry_run=True)
    assert res3["stamped"] == ["notes/fleeting/chats/chat_new.md"]
    assert extra.read_text(encoding="utf-8") == "raw\n"
