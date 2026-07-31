"""Contract tests for the shipped seed-corpus manifest (O1 spec sections 1-2).

test_license_impl_start_check IS the impl-start check the beta.1 decisions
ledger names: it re-asserts, on every run, that each row clears the license
floor, carries an https evidence URL, and pins its identifier. A row that
fails is replaced, never waived (spec section 1).
"""

from __future__ import annotations

import re

from memoria_vault.product.seed_corpus import (
    SEED_FETCH_METHODS,
    SEED_LICENSE_FLOOR,
    load_seed_manifest,
    parse_seed_manifest,
)
from memoria_vault.runtime.paths import safe_filename

EXPECTED_IDS = [
    "chen-2018-undesirable-difficulty",
    "moreira-2019-retrieval-practice",
    "settles-2016-spaced-repetition",
    "morrison-2020-offloading",
    "ose-askvik-2020-handwriting",
    "schmidt-2018-luhmann-card-index",
    "mirzababaei-2021-toulmin-agent",
    "asai-2024-openscholar",
]

_BAD_ROW_TEMPLATE = """
- id: bad-row
  title: "Bad fixture row"
  identifier: "doi:10.1234/bad"
  license: {license}
  license_evidence: "https://example.test/license"
  fetch:
    method: {method}
    url: "{url}"
  role: "fixture"
"""


def _bad_row(
    license_value: str = "CC BY 4.0",
    method: str = "pdf-url",
    url: str = "https://example.test/bad.pdf",
) -> str:
    return _BAD_ROW_TEMPLATE.format(license=license_value, method=method, url=url)


def test_manifest_ships_all_eight_rows_in_spec_order() -> None:
    rows = load_seed_manifest()

    assert [row["id"] for row in rows] == EXPECTED_IDS


def test_license_impl_start_check() -> None:
    assert SEED_LICENSE_FLOOR == {"CC BY", "CC BY 4.0", "CC0"}
    for row in load_seed_manifest():
        assert row["license"] in {"CC BY", "CC BY 4.0", "CC0"}, row["id"]
        assert str(row["license_evidence"]).startswith("https://"), row["id"]
        identifier = str(row["identifier"])
        assert identifier.startswith(("doi:", "arxiv:")), row["id"]
        if identifier.startswith("arxiv:"):
            assert re.search(r"v\d+$", identifier), (
                f"{row['id']}: arXiv identifier must pin a version"
            )


def test_fetch_methods_match_spec_table() -> None:
    assert SEED_FETCH_METHODS == {"pmc-oa", "pdf-url", "arxiv-pdf"}
    rows = load_seed_manifest()
    methods = {row["id"]: row["fetch"]["method"] for row in rows}

    assert methods == {
        "chen-2018-undesirable-difficulty": "pmc-oa",
        "moreira-2019-retrieval-practice": "pdf-url",
        "settles-2016-spaced-repetition": "pdf-url",
        "morrison-2020-offloading": "pmc-oa",
        "ose-askvik-2020-handwriting": "pmc-oa",
        "schmidt-2018-luhmann-card-index": "pdf-url",
        "mirzababaei-2021-toulmin-agent": "pmc-oa",
        "asai-2024-openscholar": "arxiv-pdf",
    }
    urls = {row["id"]: row["fetch"]["url"] for row in rows}
    assert urls["asai-2024-openscholar"] == "https://export.arxiv.org/pdf/2411.14199v1"
    for row_id in (
        "chen-2018-undesirable-difficulty",
        "morrison-2020-offloading",
        "ose-askvik-2020-handwriting",
        "mirzababaei-2021-toulmin-agent",
    ):
        assert urls[row_id].startswith(
            "https://www.ncbi.nlm.nih.gov/pmc/utils/oa/oa.fcgi?id=PMC"
        ), row_id


def test_paper_repo_affordance_pairs() -> None:
    rows = {row["id"]: row for row in load_seed_manifest()}

    assert rows["asai-2024-openscholar"]["repo"] == "https://github.com/AkariAsai/OpenScholar"
    assert rows["asai-2024-openscholar"]["identifier"] == "arxiv:2411.14199v1"
    assert rows["settles-2016-spaced-repetition"]["repo"] == (
        "https://github.com/duolingo/halflife-regression"
    )


def test_ids_survive_catalog_work_id_normalization() -> None:
    # state._work_id / capture._work_id normalize via safe_filename().strip("._-");
    # the pre-check in seed_install only holds if manifest ids are fixed points.
    for row in load_seed_manifest():
        assert safe_filename(row["id"]).strip("._-") == row["id"]


def test_parse_rejects_license_floor_violation() -> None:
    try:
        parse_seed_manifest(_bad_row(license_value="CC BY-SA 4.0"))
    except ValueError as exc:
        assert "license floor" in str(exc)
    else:
        raise AssertionError("CC BY-SA must fail the license floor")


def test_parse_rejects_unknown_fetch_method() -> None:
    try:
        parse_seed_manifest(_bad_row(method="scrape"))
    except ValueError as exc:
        assert "fetch.method" in str(exc)
    else:
        raise AssertionError("unknown fetch methods must be rejected")


def test_parse_rejects_non_https_fetch_url() -> None:
    try:
        parse_seed_manifest(_bad_row(url="http://example.test/bad.pdf"))
    except ValueError as exc:
        assert "https" in str(exc)
    else:
        raise AssertionError("non-https fetch URLs must be rejected")
