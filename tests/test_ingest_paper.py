"""L1 component test for ingest_paper — extracted from its former --self-test (ADR-44)."""
import ingest_paper as _m
globals().update({k: getattr(_m, k) for k in dir(_m) if not k.startswith("__")})


def test_ingest_paper():
    def _run():
        fails = 0
        for ck, ntype, stype, want in _EXPECT:
            fm = ingest_text(ck, _FIXTURE)["frontmatter"]
            checks = [
                ("captured", fm["lifecycle"] == "captured"),
                ("title", bool(fm["title"])),
                ("note_type", fm["type"] == ntype),
                ("source_type", fm["source_type"] == stype),
                ("authors", len(fm["authors"]) == want["authors"]),
            ]
            for key in ("arxiv_id", "pmcid", "isbn"):
                if key in want:
                    checks.append((key, fm[key] == want[key]))
            bad = [name for name, ok in checks if not ok]
            print(f"  {'PASS' if not bad else 'FAIL'}  {ck:18} -> {fm['type']:9} {fm['source_type']:8}"
                  + (f"  BAD: {bad}" if bad else ""))
            fails += bool(bad)
        print(f"\n{'OK' if not fails else f'{fails} FAILING'}: ingest_paper Tier-0 self-test")
        return 1 if fails else 0
    assert _run() == 0
