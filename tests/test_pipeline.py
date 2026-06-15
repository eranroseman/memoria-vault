"""L1 component test for pipeline — extracted from its former --self-test (ADR-44)."""
import runner as _m

_bib_local_pdf = _m._bib_local_pdf
run = _m.run


def test_pipeline():
    def _run():
        """Offline test of the assembly: Tier-0 only (no network)."""
        fixture = ("@article{x2024Test,\n  title = {A Test},\n  author = {Doe, Jane},\n"
                   "  year = {2024},\n  doi = {10.1/x},\n  journal = {J Tests},\n"
                   "  zoteroselect = {zotero://select/library/items/ABCD1234},\n"
                   "  file = {C:\\Users\\me\\Zotero\\storage\\WXYZ5678\\A Test.pdf},\n}\n")
        b = run("x2024Test", fixture, enrich=False)
        fm = b["frontmatter"]
        checks = [
            ("tier0 floor", b["lifecycle"] == "current" and b["ingest_status"] == "tier0"),
            ("routes to paper", b["note_type"] == "paper"),
            ("two holes declared", b["holes"] == ["_proposed_classification", "brief"]),
            ("frontmatter has identity", fm["title"] == "A Test" and fm["doi"] == "10.1/x"),
            ("zotero_uri from zoteroselect (no API)", fm["zotero_uri"] == "zotero://select/library/items/ABCD1234"),
            ("pdf_uri from bib file storage key", fm["pdf_uri"] == "zotero://open-pdf/library/items/WXYZ5678"),
            ("no enrichment without --enrich", b["extract"] is None and b["link_plan"] is None),
        ]
        pdf, key = _bib_local_pdf(
            "y2024Pdf",
            "@article{y2024Pdf,\n  title = {P},\n"
            "  file = {C:\\Users\\me\\Zotero\\storage\\ABCD1234\\My Paper - 2024.pdf},\n}\n")
        checks.append(("bib file -> wsl path + zotero storage key",
                       key == "ABCD1234"
                       and pdf == "/mnt/c/Users/me/Zotero/storage/ABCD1234/My Paper - 2024.pdf"))
        bad = [n for n, ok in checks if not ok]
        for n, ok in checks:
            print(f"  {'PASS' if ok else 'FAIL'}  {n}")
        print(f"\n{'OK' if not bad else f'{len(bad)} FAILING'}: runner.py self-test")
        return 1 if bad else 0
    assert _run() == 0
