"""Contract tests for multi-entry import parsing and adapter normalization.

The first test pins the shipped defect the splitters fix: the shipped
single-entry builder silently truncates a multi-entry BibTeX file to its
first entry (parse_bibtex_entry stops at the first balanced container).
The splitters cut the file into per-entry chunks; the shipped builders
stay untouched and receive one chunk each. The adapter tests pin the O2
section-4 type normalization separately, before a later integration seam
wires it into the bulk driver.
"""

from __future__ import annotations

import json
import sqlite3
from pathlib import Path

import pytest

from memoria_vault.runtime import state
from memoria_vault.runtime.bulk_import import (
    detect_identifier_collisions,
    entry_capture_request,
    entry_fetch,
    entry_item_type,
    entry_type_mapped,
    is_doi_collision_error,
    split_bibtex_entries,
    split_csl_entries,
)
from memoria_vault.runtime.capture import bibtex_capture_payload, csl_capture_payload
from tests.helpers import call_with_context, copy_memoria_dirs, init_git

pytestmark = pytest.mark.contract

TWO_ENTRIES = """@article{alpha2026,
  title = {Alpha Import},
  doi = {10.1000/alpha.2026},
  abstract = {First fixture entry.}
}

@article{beta2026,
  title = {Beta Import {With Nested Braces}},
  doi = {10.1000/beta.2026},
  abstract = {Second fixture entry, reachable at beta@example.org.}
}
"""


def test_shipped_builder_truncates_a_multi_entry_file_to_its_first_entry() -> None:
    payload = bibtex_capture_payload(TWO_ENTRIES)

    assert payload["citekey"] == "alpha2026"
    assert payload["identifiers"] == {"doi": "10.1000/alpha.2026"}


def test_split_bibtex_entries_yields_one_payload_per_entry() -> None:
    chunks = split_bibtex_entries(TWO_ENTRIES)

    assert len(chunks) == 2
    assert chunks[0].startswith("@article{alpha2026,")
    assert chunks[1].startswith("@article{beta2026,")
    payloads = [bibtex_capture_payload(chunk) for chunk in chunks]
    assert [payload["citekey"] for payload in payloads] == ["alpha2026", "beta2026"]
    assert payloads[1]["title"] == "Beta Import With Nested Braces"
    assert payloads[1]["identifiers"] == {"doi": "10.1000/beta.2026"}


def test_split_bibtex_entries_handles_paren_containers_and_inter_entry_junk() -> None:
    text = (
        "Comments outside entries are BibTeX junk and are ignored.\n"
        "@article(paren2026,\n"
        "  title = {Paren Container},\n"
        "  doi = {10.1000/paren.2026}\n"
        ")\n"
        "trailing junk without an at-sign\n" + TWO_ENTRIES
    )

    chunks = split_bibtex_entries(text)

    assert len(chunks) == 3
    assert chunks[0].startswith("@article(paren2026,")
    assert bibtex_capture_payload(chunks[0])["citekey"] == "paren2026"


def test_split_bibtex_entries_ignores_at_signs_in_external_comments() -> None:
    text = "% contact: user@example.org\n" + TWO_ENTRIES

    chunks = split_bibtex_entries(text)

    assert len(chunks) == 2
    assert [bibtex_capture_payload(chunk)["citekey"] for chunk in chunks] == [
        "alpha2026",
        "beta2026",
    ]


def test_split_bibtex_entries_keeps_an_unclosed_tail_as_a_failing_chunk() -> None:
    text = TWO_ENTRIES + "\n@article{broken2026,\n  title = {Unclosed\n"

    chunks = split_bibtex_entries(text)

    assert len(chunks) == 3
    assert chunks[2].startswith("@article{broken2026,")
    with pytest.raises(ValueError):
        bibtex_capture_payload(chunks[2])


def test_split_csl_entries_array_yields_per_item_dumps() -> None:
    items = [
        {
            "id": "alpha-csl",
            "type": "article-journal",
            "title": "Alpha CSL",
            "DOI": "10.1000/alpha.csl",
        },
        {"id": "beta-csl", "type": "book", "title": "Beta CSL", "ISBN": "9780000000009"},
    ]

    chunks = split_csl_entries(json.dumps(items))

    assert len(chunks) == 2
    payloads = [csl_capture_payload(json.loads(chunk), raw_text=chunk) for chunk in chunks]
    assert [payload["work_id"] for payload in payloads] == ["alpha-csl", "beta-csl"]
    assert json.loads(chunks[1])["ISBN"] == "9780000000009"


def test_split_csl_entries_single_object_is_a_one_item_list_of_the_original_text() -> None:
    text = json.dumps({"id": "solo-csl", "type": "article-journal", "title": "Solo"})

    assert split_csl_entries(text) == [text]


def test_split_csl_entries_rejects_non_object_members_and_scalars() -> None:
    with pytest.raises(ValueError, match="item 2 must be a JSON object"):
        split_csl_entries('[{"id": "ok", "title": "OK"}, "not-an-object"]')
    with pytest.raises(ValueError, match="object or array"):
        split_csl_entries("42")


def test_build_entry_payload_dispatches_per_format() -> None:
    from memoria_vault.runtime.bulk_import import build_entry_payload

    chunks = split_bibtex_entries(TWO_ENTRIES)
    assert build_entry_payload("bibtex", chunks[1])["citekey"] == "beta2026"

    csl_chunk = json.dumps({"id": "solo-csl", "type": "article-journal", "title": "Solo"})
    payload = build_entry_payload("csl", csl_chunk)
    assert payload["work_id"] == "solo-csl"
    assert payload["raw_text"] == csl_chunk + "\n"


def test_entry_ref_names_citekey_csl_id_or_entry_index() -> None:
    from memoria_vault.runtime.bulk_import import entry_ref

    assert entry_ref("bibtex", "@article{broken2026,\n  title = {Unclosed\n", 4) == "broken2026"
    assert entry_ref("bibtex", "@article-type{hyphenated2026,\n  title = {Hyphenated}\n}", 4) == (
        "hyphenated2026"
    )
    assert entry_ref("bibtex", "@custom:type{recoverable-key,\n  title = {Custom}\n}", 4) == (
        "recoverable-key"
    )
    assert entry_ref("bibtex", "@ {not-a-citekey,\n  title = {Invalid}\n}", 4) == "entry-4"
    assert entry_ref("bibtex", "@ not an entry at all", 4) == "entry-4"
    assert entry_ref("csl", '{"id": "beta-csl", "title": ""}', 2) == "beta-csl"
    assert entry_ref("csl", "not json", 2) == "entry-2"


def test_entry_item_type_maps_bibtex_and_csl_types_onto_shipped_vocabulary() -> None:
    cases = (
        ({"type": "article"}, "article"),
        ({"type": "inproceedings"}, "article"),
        ({"type": "incollection"}, "article"),
        ({"type": "book"}, "book"),
        ({"type": "techreport"}, "report"),
        ({"type": "phdthesis"}, "report"),
        ({"type": "online", "url": "https://example.test/post"}, "webpage"),
        ({"type": "article-journal"}, "article"),
        ({"type": "paper-conference"}, "article"),
        ({"type": "chapter"}, "article"),
        ({"type": "thesis"}, "report"),
        ({"type": "post-weblog"}, "webpage"),
        ({"type": "webpage"}, "webpage"),
        ({"type": "software"}, "software"),
        ({"type": "dataset"}, "dataset"),
        ({"type": "report"}, "report"),
    )

    for fields, expected in cases:
        assert entry_item_type(fields) == expected
        assert entry_type_mapped(fields) is True


def test_entry_item_type_agrees_with_shipped_item_type_for_bibtex_aliases() -> None:
    """Parity pin: the bulk map may not drift from capture.py's _item_type."""
    from memoria_vault.runtime.capture import _item_type

    bibtex_aliases = (
        "article",
        "inproceedings",
        "conference",
        "incollection",
        "book",
        "inbook",
        "booklet",
        "online",
        "webpage",
        "www",
        "dataset",
        "data",
        "software",
        "manual",
        "techreport",
        "report",
        "phdthesis",
        "mastersthesis",
    )

    for alias in bibtex_aliases:
        assert entry_item_type({"type": alias}) == _item_type(alias), alias


def test_normalization_covers_the_shipped_csl_raw_type_passthrough() -> None:
    """The driver will stamp normalized type over the unchanged raw CSL type."""
    payload = csl_capture_payload(
        {"id": "x", "type": "article-journal", "title": "T"}, raw_text="{}"
    )

    assert payload["item_type"] == "article-journal"
    assert entry_item_type(payload["csl_json"]) == "article"


def test_misc_repo_host_url_maps_to_software_and_wins_over_dataset_doi() -> None:
    fields = {
        "type": "misc",
        "url": "https://github.com/org/tool",
        "doi": "10.5281/zenodo.123",
    }

    assert entry_item_type(fields) == "software"
    assert entry_type_mapped(fields) is True
    assert entry_item_type({"type": "misc", "url": "https://gitlab.com/o/r"}) == "software"
    assert entry_item_type({"type": "misc", "url": "https://codeberg.org/o/r"}) == "software"
    assert entry_item_type({"type": "misc", "url": "https://gist.github.com/o/1"}) == "software"
    csl_fields = {"type": "misc", "URL": "https://github.com/o/r"}
    assert entry_item_type(csl_fields) == "software"
    assert entry_type_mapped(csl_fields) is True
    assert entry_item_type({"type": "misc", "url": "github.com/o/r"}) == "software"
    assert entry_item_type({"type": "misc", "url": "github.com.evil/o/r"}) == "webpage"
    assert entry_item_type({"type": "misc", "url": "github.com:thing"}) == "webpage"


def test_misc_datacite_doi_prefix_maps_to_dataset() -> None:
    for prefix in (
        "10.5281",
        "10.5061",
        "10.6084",
        "10.7910",
        "10.17632",
        "10.3886",
        "10.15468",
        "10.24432",
    ):
        fields = {"type": "misc", "doi": f"{prefix}/fixture"}
        assert entry_item_type(fields) == "dataset", prefix
        assert entry_type_mapped(fields) is True, prefix
    csl_fields = {"type": "misc", "DOI": "10.5061/dryad.abc123"}
    assert entry_item_type(csl_fields) == "dataset"
    assert entry_type_mapped(csl_fields) is True


def test_misc_with_plain_url_maps_to_webpage() -> None:
    fields = {"type": "misc", "url": "https://example.org/page"}

    assert entry_item_type(fields) == "webpage"
    assert entry_type_mapped(fields) is True
    csl_fields = {"type": "misc", "URL": "https://example.org/page"}
    assert entry_item_type(csl_fields) == "webpage"
    assert entry_type_mapped(csl_fields) is True


def test_unknown_types_fall_back_to_article_and_are_flagged() -> None:
    for fields in (
        {"type": "patent"},
        {"type": "misc"},
        {"type": ""},
        {"type": "misc", "doi": "10.1234/x"},
    ):
        assert entry_item_type(fields) == "article", fields
        assert entry_type_mapped(fields) is False, fields


OA_URL = "https://www.ncbi.nlm.nih.gov/pmc/utils/oa/oa.fcgi?id=PMC6099118"
ARXIV_URL = "https://export.arxiv.org/pdf/2411.14199v1"
DIRECT_PDF_URL = "https://aclanthology.org/2024.findings-acl.123.pdf"


def _adapter_payload(item_type: str = "article", **overrides: object) -> dict:
    payload = {
        "work_id": "w-1",
        "title": "Fixture Work",
        "description": "Fixture description.",
        "resource": "",
        "item_type": item_type,
        "identifiers": {},
        "csl_json": {"id": "w-1"},
        "provider_coverage": "partial",
        "citekey": "w1",
    }
    payload.update(overrides)
    return payload


def test_entry_fetch_synthesizes_only_resolver_supported_methods() -> None:
    assert entry_fetch({}, {"pmcid": "PMC6099118"}) == {"method": "pmc-oa", "url": OA_URL}
    assert entry_fetch({}, {"pmcid": "6099118"}) == {"method": "pmc-oa", "url": OA_URL}
    assert entry_fetch({}, {"arxiv": "arXiv:2411.14199v1"}) == {
        "method": "arxiv-pdf",
        "url": ARXIV_URL,
    }
    assert entry_fetch({"url": "https://example.test/paper.PDF"}, {}) == {
        "method": "pdf-url",
        "url": "https://example.test/paper.PDF",
    }
    assert entry_fetch({"url": "https://doi.org/10.1234/x"}, {"doi": "10.1234/x"}) is None


def test_csl_remote_identifiers_survive_payload_normalization_and_fetch_synthesis() -> None:
    from memoria_vault.runtime.bulk_import import build_entry_payload

    pmc_item = {
        "id": "pmc-csl",
        "type": "article-journal",
        "title": "PMC CSL",
        "PMCID": "6099118",
    }
    pmc_payload = build_entry_payload("csl", json.dumps(pmc_item))
    assert pmc_payload["identifiers"] == {"pmcid": "6099118"}
    assert entry_fetch(pmc_item, pmc_payload["identifiers"]) == {"method": "pmc-oa", "url": OA_URL}

    arxiv_item = {
        "id": "arxiv-csl",
        "type": "article-journal",
        "title": "arXiv CSL",
        "arXiv": "arXiv:2411.14199v1",
    }
    arxiv_payload = build_entry_payload("csl", json.dumps(arxiv_item))
    assert arxiv_payload["identifiers"] == {"arxiv": "arXiv:2411.14199v1"}
    assert entry_fetch(arxiv_item, arxiv_payload["identifiers"]) == {
        "method": "arxiv-pdf",
        "url": ARXIV_URL,
    }


def test_entry_capture_request_routes_eligible_pdfs_without_fetching() -> None:
    payload = _adapter_payload(identifiers={"pmcid": "PMC6099118"})
    fetch = entry_fetch({}, payload["identifiers"])

    operation_id, request = entry_capture_request(payload, fetch)

    assert operation_id == "capture-remote-pdf-source"
    assert request == {
        "fetch": {"method": "pmc-oa", "url": OA_URL},
        "capture": {
            "work_id": "w-1",
            "title": "Fixture Work",
            "description": "Fixture description.",
            "resource": OA_URL,
            "item_type": "article",
            "identifiers": {"pmcid": "PMC6099118"},
            "csl_json": {"id": "w-1"},
            "citekey": "w1",
            "provider_coverage": "partial",
        },
    }
    assert "raw_pdf_base64" not in str(request)

    arxiv_payload = _adapter_payload(identifiers={"arxiv": "2411.14199v1"})
    arxiv_operation, arxiv_request = entry_capture_request(
        arxiv_payload, entry_fetch({}, arxiv_payload["identifiers"])
    )
    assert arxiv_operation == "capture-remote-pdf-source"
    assert arxiv_request["fetch"] == {"method": "arxiv-pdf", "url": ARXIV_URL}

    direct_payload = _adapter_payload(resource=DIRECT_PDF_URL)
    direct_operation, direct_request = entry_capture_request(
        direct_payload, entry_fetch({"url": DIRECT_PDF_URL}, {})
    )
    assert direct_operation == "capture-remote-pdf-source"
    assert direct_request["fetch"] == entry_fetch({"url": DIRECT_PDF_URL}, {})


def test_entry_capture_request_preserves_metadata_and_webpage_tiers() -> None:
    pdf_fetch = {"method": "pdf-url", "url": DIRECT_PDF_URL}
    for item_type in ("book", "software", "dataset"):
        payload = _adapter_payload(item_type)
        operation_id, request = entry_capture_request(payload, pdf_fetch)
        assert operation_id == "capture-source"
        assert request is payload

    unmapped = _adapter_payload(identifiers={"pmcid": "PMC6099118"})
    operation_id, request = entry_capture_request(
        unmapped, entry_fetch({}, unmapped["identifiers"]), mapped=False
    )
    assert operation_id == "capture-source"
    assert request is unmapped

    report = _adapter_payload("report", resource=DIRECT_PDF_URL)
    operation_id, request = entry_capture_request(report, pdf_fetch)
    assert operation_id == "capture-remote-pdf-source"
    assert request["fetch"] == pdf_fetch
    arxiv_report = _adapter_payload("report", identifiers={"arxiv": "2411.14199v1"})
    operation_id, request = entry_capture_request(
        arxiv_report, entry_fetch({}, arxiv_report["identifiers"])
    )
    assert operation_id == "capture-source"
    assert request is arxiv_report

    webpage = _adapter_payload("webpage", resource="https://example.test/post")
    operation_id, request = entry_capture_request(webpage, None)
    assert operation_id == "capture-url-source"
    assert request == {
        "url": "https://example.test/post",
        "title": "Fixture Work",
        "description": "Fixture description.",
    }


BIB_DOI_ARXIV = """@article{smith2024,
  title = {Admitted Work},
  author = {Smith, Ada},
  doi = {10.1234/admitted},
  arxiv = {2411.14199},
  year = {2024}
}
"""

BIB_PMCID = """@article{jones2023,
  title = {PMC Work},
  author = {Jones, Bo},
  doi = {10.1234/pmc-work},
  pmcid = {PMC7399101},
  year = {2023}
}
"""

BIB_SAME_DOI_A = """@article{alpha2024,
  title = {Shared DOI Entry One},
  doi = {10.7777/Same},
  year = {2024}
}
"""

BIB_SAME_DOI_B = """@article{beta2024,
  title = {Shared DOI Entry Two},
  doi = {10.7777/same},
  year = {2024}
}
"""


def _catalog_vault(tmp_path: Path) -> Path:
    copy_memoria_dirs(tmp_path, "schemas")
    init_git(tmp_path, "bulk@example.invalid", "Bulk Import")
    return tmp_path


def _admit(vault: Path, payload: dict) -> dict:
    from memoria_vault.runtime.capture import stage_capture_payload

    return call_with_context(stage_capture_payload, vault, payload)


def test_detect_identifier_collisions_matches_arxiv_and_pmcid_exactly(
    tmp_path: Path,
) -> None:
    vault = _catalog_vault(tmp_path)
    arxiv_work = _admit(vault, bibtex_capture_payload(BIB_DOI_ARXIV))["work_id"]
    pmc_work = _admit(vault, bibtex_capture_payload(BIB_PMCID))["work_id"]

    assert detect_identifier_collisions(vault, "citekey-2025", {"arxiv": "2411.14199"}) == [
        {"other_work_id": arxiv_work, "field": "arxiv"}
    ]
    assert detect_identifier_collisions(vault, "citekey-2025", {"pmcid": "PMC7399101"}) == [
        {"other_work_id": pmc_work, "field": "pmcid"}
    ]
    assert detect_identifier_collisions(vault, arxiv_work, {"arxiv": "2411.14199"}) == []
    assert detect_identifier_collisions(vault, "other", {"arxiv": "2411.9999"}) == []
    assert detect_identifier_collisions(vault, "other", {"doi": "10.1234/admitted"}) == []
    assert detect_identifier_collisions(tmp_path / "nowhere", "w", {"arxiv": "1"}) == []


def test_doi_unique_collision_raises_and_is_classified(tmp_path: Path) -> None:
    vault = _catalog_vault(tmp_path)
    first = csl_capture_payload(
        {"id": "alpha-2020", "type": "article-journal", "title": "Alpha", "DOI": "10.9999/dup"},
        raw_text="{}",
    )
    _admit(vault, first)

    second = csl_capture_payload(
        {"id": "beta-2021", "type": "article-journal", "title": "Beta", "DOI": "10.9999/dup"},
        raw_text="{}",
    )
    with pytest.raises(sqlite3.IntegrityError) as excinfo:
        _admit(vault, second)

    assert is_doi_collision_error(str(excinfo.value))
    assert not is_doi_collision_error("UNIQUE constraint failed: catalog_sources.work_id")
    assert not is_doi_collision_error("capture refusal: no text")
    assert state.catalog_source(vault, "alpha-2020") is not None
    assert len(state.catalog_sources(vault, checked_only=False)) == 1


def test_same_doi_entries_collapse_structurally_to_one_row(tmp_path: Path) -> None:
    """Same DOI derives one work ID, so the driver's pre-check skips the second."""
    vault = _catalog_vault(tmp_path)
    first = bibtex_capture_payload(BIB_SAME_DOI_A)
    second = bibtex_capture_payload(BIB_SAME_DOI_B)

    assert first["work_id"] == second["work_id"] == "doi-10.7777/same"
    _admit(vault, first)

    assert state.catalog_source(vault, second["work_id"]) is not None
    assert len(state.catalog_sources(vault, checked_only=False)) == 1
    assert detect_identifier_collisions(vault, second["work_id"], second["identifiers"]) == []


def test_parse_entry_fields_derives_the_adapter_shape_from_one_entry_chunk() -> None:
    """The one seam that feeds `entry_item_type` / `entry_fetch` from a raw chunk.

    Without it the driver would re-implement BibTeX/CSL extraction in cli.py and the
    adapter helpers would be fed a differently-shaped dict than the one their own
    contract tests use.
    """
    from memoria_vault.runtime.bulk_import import parse_entry_fields

    bib = """@techreport{report2026,
  title = {Field Shape},
  doi = {10.1000/report.2026},
  url = {https://example.test/report.pdf}
}
"""
    fields = parse_entry_fields("bibtex", bib)

    assert fields == {
        "type": "techreport",
        "title": "Field Shape",
        "doi": "10.1000/report.2026",
        "url": "https://example.test/report.pdf",
    }
    # The derived shape is the one A.1/A.2 were contract-tested against, not a
    # look-alike: the adapters must read `type` and `url` straight out of it.
    assert entry_item_type(fields) == "report"
    assert entry_type_mapped(fields) is True
    assert entry_fetch(fields, {}) == {
        "method": "pdf-url",
        "url": "https://example.test/report.pdf",
    }

    item = {"id": "solo-csl", "type": "article-journal", "title": "Solo", "PMCID": "6099118"}
    csl_fields = parse_entry_fields("csl", json.dumps(item))
    assert csl_fields == item
    assert entry_item_type(csl_fields) == "article"
    assert entry_fetch(csl_fields, {}) == {"method": "pmc-oa", "url": OA_URL}


def test_parse_entry_fields_raises_on_the_chunks_the_driver_must_name_as_failed() -> None:
    from memoria_vault.runtime.bulk_import import parse_entry_fields

    with pytest.raises(ValueError):
        parse_entry_fields("bibtex", "@article{broken2026,\n  title {Missing Equals}\n}\n")
    with pytest.raises(ValueError):
        parse_entry_fields("csl", "not json")
    with pytest.raises(ValueError, match="CSL entry must be a JSON object"):
        parse_entry_fields("csl", "[1, 2]")
