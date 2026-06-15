"""L1 component tests for runner (ADR-44)."""

import runner as _m

_bib_local_pdf = _m._bib_local_pdf
run = _m.run


FIXTURE = (
    "@article{x2024Test,\n  title = {A Test},\n  author = {Doe, Jane},\n"
    "  year = {2024},\n  doi = {10.1/x},\n  journal = {J Tests},\n"
    "  zoteroselect = {zotero://select/library/items/ABCD1234},\n"
    "  file = {C:\\Users\\me\\Zotero\\storage\\WXYZ5678\\A Test.pdf},\n}\n"
)


def test_runner_builds_tier0_paper_bundle():
    bundle = run("x2024Test", FIXTURE, enrich=False)

    assert bundle["lifecycle"] == "current"
    assert bundle["ingest_status"] == "tier0"
    assert bundle["note_type"] == "paper"
    assert bundle["holes"] == ["_proposed_classification", "brief"]


def test_runner_frontmatter_includes_identity_and_local_uris():
    fm = run("x2024Test", FIXTURE, enrich=False)["frontmatter"]

    assert fm["title"] == "A Test"
    assert fm["doi"] == "10.1/x"
    assert fm["zotero_uri"] == "zotero://select/library/items/ABCD1234"
    assert fm["pdf_uri"] == "zotero://open-pdf/library/items/WXYZ5678"


def test_runner_skips_enrichment_when_disabled():
    bundle = run("x2024Test", FIXTURE, enrich=False)

    assert bundle["extract"] is None
    assert bundle["link_plan"] is None


def test_bib_local_pdf_returns_wsl_path_and_storage_key():
    pdf, key = _bib_local_pdf(
        "y2024Pdf",
        "@article{y2024Pdf,\n  title = {P},\n"
        "  file = {C:\\Users\\me\\Zotero\\storage\\ABCD1234\\My Paper - 2024.pdf},\n}\n",
    )

    assert key == "ABCD1234"
    assert pdf == "/mnt/c/Users/me/Zotero/storage/ABCD1234/My Paper - 2024.pdf"
