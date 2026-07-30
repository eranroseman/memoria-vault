"""Contract tests for multi-entry import splitting (O2 spec section 2, slice 1).

The first test pins the shipped defect the splitters fix: the shipped
single-entry builder silently truncates a multi-entry BibTeX file to its
first entry (parse_bibtex_entry stops at the first balanced container).
The splitters cut the file into per-entry chunks; the shipped builders
stay untouched and receive one chunk each.
"""

from __future__ import annotations

import json

import pytest

from memoria_vault.runtime.bulk_import import split_bibtex_entries, split_csl_entries
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
