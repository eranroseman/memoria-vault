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

import pytest

from memoria_vault.runtime.bulk_import import (
    entry_item_type,
    entry_type_mapped,
    split_bibtex_entries,
    split_csl_entries,
)
from memoria_vault.runtime.capture import bibtex_capture_payload, csl_capture_payload

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
