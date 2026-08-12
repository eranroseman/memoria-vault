"""Contract tests for the shipped seed-corpus manifest (O1 spec sections 1-2).

test_license_impl_start_check IS the impl-start check the beta.1 decisions
ledger names: it re-asserts, on every run, that each row clears the license
floor, carries an https evidence URL, and pins its identifier. A row that
fails is replaced, never waived (spec section 1).
"""

from __future__ import annotations

import re

import pytest

from memoria_vault.product.seed_corpus import (
    SEED_FETCH_METHODS,
    SEED_LICENSE_FLOOR,
    load_seed_manifest,
    parse_seed_manifest,
)
from memoria_vault.runtime.paths import safe_filename

pytestmark = pytest.mark.contract

EXPECTED_IDS = [
    "chen-2018-undesirable-difficulty",
    "moreira-2019-retrieval-practice",
    "settles-2016-spaced-repetition",
    "hu-luo-fleming-2019-metamemory-offloading",
    "ose-askvik-2020-handwriting",
    "schmidt-2018-luhmann-card-index",
    "mirzababaei-2021-toulmin-agent",
    "asai-2024-openscholar",
]

EXPECTED_DIRECT_ROWS = {
    "chen-2018-undesirable-difficulty": {
        "identifier": "doi:10.3389/fpsyg.2018.01483",
        "license": "CC BY 4.0",
        "method": "pdf-url",
        "url": "https://www.frontiersin.org/journals/psychology/articles/10.3389/fpsyg.2018.01483/pdf",
    },
    "moreira-2019-retrieval-practice": {
        "identifier": "doi:10.3389/feduc.2019.00005",
        "license": "CC BY",
        "method": "pdf-url",
        "url": "https://www.frontiersin.org/journals/education/articles/10.3389/feduc.2019.00005/pdf",
    },
    "ose-askvik-2020-handwriting": {
        "identifier": "doi:10.3389/fpsyg.2020.01810",
        "license": "CC BY 4.0",
        "method": "pdf-url",
        "url": "https://www.frontiersin.org/journals/psychology/articles/10.3389/fpsyg.2020.01810/pdf",
    },
    "mirzababaei-2021-toulmin-agent": {
        "identifier": "doi:10.3389/frai.2021.645516",
        "license": "CC BY 4.0",
        "method": "pdf-url",
        "url": "https://www.frontiersin.org/journals/artificial-intelligence/articles/10.3389/frai.2021.645516/pdf",
    },
    "hu-luo-fleming-2019-metamemory-offloading": {
        "identifier": "doi:10.1016/j.cognition.2019.104012",
        "license": "CC BY 4.0",
        "method": "pdf-url",
        "url": "https://discovery.ucl.ac.uk/id/eprint/10077673/1/Fleming_A%20role%20for%20metamemory%20in%20cognitive%20offloading_VoR.pdf",
    },
}

UNCHANGED_ROWS = {
    "settles-2016-spaced-repetition": {
        "identifier": "doi:10.18653/v1/P16-1174",
        "license": "CC BY 4.0",
        "method": "pdf-url",
        "url": "https://aclanthology.org/P16-1174.pdf",
    },
    "schmidt-2018-luhmann-card-index": {
        "identifier": "doi:10.6092/issn.1971-8853/8350",
        "license": "CC BY 4.0",
        "method": "pdf-url",
        "url": "https://sociologica.unibo.it/article/download/8350/8272",
    },
    "asai-2024-openscholar": {
        "identifier": "arxiv:2411.14199v1",
        "license": "CC BY 4.0",
        "method": "arxiv-pdf",
        "url": "https://export.arxiv.org/pdf/2411.14199v1",
    },
}

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


def test_shipped_rows_pin_direct_sources() -> None:
    assert SEED_FETCH_METHODS == {"pmc-oa", "pdf-url", "arxiv-pdf"}
    rows = {row["id"]: row for row in load_seed_manifest()}
    assert set(rows) == set(EXPECTED_DIRECT_ROWS) | set(UNCHANGED_ROWS)
    for row_id, expected in {**EXPECTED_DIRECT_ROWS, **UNCHANGED_ROWS}.items():
        row = rows[row_id]
        assert row["identifier"] == expected["identifier"]
        assert row["license"] == expected["license"]
        assert row["fetch"] == {"method": expected["method"], "url": expected["url"]}
    assert "morrison-2020-offloading" not in rows
    assert rows["hu-luo-fleming-2019-metamemory-offloading"]["title"] == (
        "A role for metamemory in cognitive offloading"
    )
    assert rows["hu-luo-fleming-2019-metamemory-offloading"]["role"] == (
        "External-memory and cognitive-offloading anchor"
    )


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
