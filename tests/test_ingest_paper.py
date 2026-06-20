"""L1 component tests for ingest_paper (ADR-44)."""

import pytest
from operations.processing.ingest import ingest_paper as _m

_EXPECT = _m._EXPECT
_FIXTURE = _m._FIXTURE
ingest_text = _m.ingest_text


@pytest.fixture(scope="module")
def frontmatter_by_citekey():
    return {ck: ingest_text(ck, _FIXTURE)["frontmatter"] for ck, *_ in _EXPECT}


@pytest.mark.parametrize(("citekey", "note_type", "source_type", "want"), _EXPECT)
def test_ingest_paper_sets_tier0_identity(frontmatter_by_citekey, citekey, note_type, source_type, want):
    fm = frontmatter_by_citekey[citekey]

    assert fm["lifecycle"] == "current"
    assert fm["ingest_status"] == "tier0"
    assert fm["title"]
    assert fm["type"] == note_type
    assert fm["source_type"] == source_type
    assert len(fm["authors"]) == want["authors"]


@pytest.mark.parametrize(("citekey", "_note_type", "_source_type", "want"), _EXPECT)
def test_ingest_paper_preserves_expected_external_ids(frontmatter_by_citekey, citekey, _note_type, _source_type, want):
    fm = frontmatter_by_citekey[citekey]

    for key in ("arxiv_id", "pmcid", "isbn"):
        if key in want:
            assert fm[key] == want[key]



def test_ingest_paper_frontmatter_order_surfaces_state():
    citekey = _EXPECT[0][0]
    note = ingest_text(citekey, _FIXTURE)
    keys = list(note["frontmatter"])
    assert keys[:5] == ["title", "name", "type", "lifecycle", "ingest_status"]
    assert keys.index("citekey") < keys.index("authors")
