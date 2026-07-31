"""Contract tests for the R2 section-7 retrieval-fixture preregistration form.

The loader IS the R3 impl-start check: it refuses unfrozen rows in spike
mode. Granularity mapping is pinned here too - Shape-1 span-ref gold maps
to containing-document paths for evaluate_bm25 (the baseline metric is
document-level hit@k until R1's passage-granular rows land, stated, never
silently degraded), and Shape-2 scores as present@depth membership over a
grouped explore payload.
"""

from __future__ import annotations

from datetime import date
from pathlib import Path
from typing import Any

import yaml

from memoria_vault.runtime import state
from memoria_vault.runtime.search_index import evaluate_bm25
from tests.helpers import copy_memoria_dirs
from tests.retrieval_fixtures import (
    FIXTURES_DIR,
    load_retrieval_fixtures,
    score_present_at_depth,
    shape1_bm25_cases,
    validate_retrieval_fixture_rows,
)

GOLD_TENSION_IDS = [
    "catalog/sources/chen-2018-undesirable-difficulty",
    "catalog/sources/moreira-2019-retrieval-practice",
]


def workspace(tmp_path: Path) -> Path:
    copy_memoria_dirs(tmp_path, "schemas")
    return tmp_path


def seed_fulltext_source(vault: Path, work_id: str, title: str, text: str) -> None:
    content = vault / f".memoria/blobs/source-content/{work_id}/full-text/paper.txt"
    content.parent.mkdir(parents=True)
    content.write_text(text, encoding="utf-8")
    state.upsert_catalog_record(
        vault,
        work_id=work_id,
        title=title,
        provider_coverage="full",
        text_status="full-text",
        check_status="checked",
        content_path=content.relative_to(vault).as_posix(),
    )


def valid_row(**overrides: Any) -> dict[str, Any]:
    row: dict[str, Any] = {
        "id": "shape1-example",
        "shape": 1,
        "query": "example query",
        "gold": ["settles-2016-spaced-repetition#^p0007"],
        "metric": "hit@5",
        "registered": "2026-07-17",
        "frozen": False,
    }
    row.update(overrides)
    return row


def test_seeded_fixture_file_loads_with_the_registered_form() -> None:
    assert sorted(path.name for path in FIXTURES_DIR.glob("*.yaml")) == ["cases.yaml"]

    fixtures = load_retrieval_fixtures()

    assert [case["id"] for case in fixtures] == [
        "shape1-spacing-effect-lookup",
        "shape1-undesirable-difficulty-boundary",
        "shape2-testing-effect-tension",
    ]
    assert [case["shape"] for case in fixtures] == [1, 1, 2]
    assert {case["registered"] for case in fixtures} == {"2026-07-17"}
    assert [case["frozen"] for case in fixtures] == [False, False, False]
    assert fixtures[2]["gold"] == GOLD_TENSION_IDS
    assert fixtures[2]["metric"] == "present@1"


def test_spike_mode_refuses_unfrozen_fixtures() -> None:
    try:
        load_retrieval_fixtures(spike_mode=True)
    except ValueError as exc:
        message = str(exc)
    else:
        raise AssertionError("spike mode must refuse the seeded unfrozen fixtures")

    assert "spike mode refuses unfrozen retrieval fixtures" in message
    assert "shape1-spacing-effect-lookup" in message


def test_fixture_form_validation_names_the_broken_row() -> None:
    checks = [
        (valid_row(shape=3), "shape must be 1 or 2"),
        (valid_row(metric="present@1"), "invalid for shape 1"),
        (valid_row(shape=2, gold=["catalog/sources/x"], metric="present@3"), "invalid for shape 2"),
        (valid_row(gold=["not a span ref"]), "invalid source-span ref"),
        (valid_row(frozen=True), "must record frozen_on"),
        (valid_row(frozen_on="2026-07-17"), "frozen_on requires frozen: true"),
        (valid_row(extra="field"), "unknown ['extra']"),
    ]
    for broken, fragment in checks:
        try:
            validate_retrieval_fixture_rows([broken])
        except ValueError as exc:
            assert fragment in str(exc)
        else:
            raise AssertionError(f"row must be refused: {fragment}")


def test_fixture_form_refuses_scalar_coercion_and_non_integer_shape() -> None:
    checks = [
        (valid_row(id=42), "id must be a nonblank string"),
        (valid_row(query=["example query"]), "query must be a nonblank string"),
        (valid_row(metric=5), "metric must be a string"),
        (valid_row(shape=True), "shape must be 1 or 2"),
        (valid_row(shape=1.0), "shape must be 1 or 2"),
    ]
    for broken, fragment in checks:
        try:
            validate_retrieval_fixture_rows([broken])
        except ValueError as exc:
            assert fragment in str(exc)
        else:
            raise AssertionError(f"row must be refused: {fragment}")


def test_fixture_form_validates_calendar_dates_and_normalizes_yaml_dates() -> None:
    for broken in [
        valid_row(registered="2026-02-30"),
        valid_row(frozen=True, frozen_on="2026-02-30"),
    ]:
        try:
            validate_retrieval_fixture_rows([broken])
        except ValueError as exc:
            assert "must be a valid ISO calendar date" in str(exc)
        else:
            raise AssertionError("impossible calendar date must be refused")

    native_dates = yaml.safe_load(
        """
        - id: native-yaml-date
          shape: 1
          query: example query
          gold: [settles-2016-spaced-repetition#^p0007]
          metric: hit@5
          registered: 2026-07-17
          frozen: true
          frozen_on: 2026-07-18
        """
    )
    assert native_dates[0]["registered"] == date(2026, 7, 17)
    assert validate_retrieval_fixture_rows(native_dates) == [
        {
            "id": "native-yaml-date",
            "shape": 1,
            "query": "example query",
            "gold": ["settles-2016-spaced-repetition#^p0007"],
            "metric": "hit@5",
            "registered": "2026-07-17",
            "frozen": True,
            "frozen_on": "2026-07-18",
        }
    ]


def test_shape1_gold_maps_to_document_paths_and_feeds_evaluate_bm25(tmp_path: Path) -> None:
    vault = workspace(tmp_path)
    seed_fulltext_source(
        vault,
        "settles-2016-spaced-repetition",
        "A Trainable Spaced Repetition Model for Language Learning",
        "The spaced repetition model measured lag effects on recall half-life. ^p0007\n",
    )
    seed_fulltext_source(
        vault,
        "chen-2018-undesirable-difficulty",
        "Undesirable Difficulty Effects in High-Element Interactivity Materials",
        "Desirable difficulties reverse for high element interactivity materials. ^p0004\n",
    )

    shape1 = [case for case in load_retrieval_fixtures() if case["shape"] == 1]
    cases = shape1_bm25_cases(vault, shape1)

    assert cases == [
        {
            "query": "what did the spaced-repetition model find about lag effects",
            "relevant": ["fulltexts/settles-2016-spaced-repetition.md"],
        },
        {
            "query": "when do desirable difficulties reverse for high element interactivity material",
            "relevant": ["fulltexts/chen-2018-undesirable-difficulty.md"],
        },
    ]

    baseline = evaluate_bm25(vault, cases)

    assert baseline["engine"] == "bm25"
    assert baseline["queries"] == 2
    assert baseline["hits"] == 2
    assert baseline["recall_at_k"] == 1.0


def test_shape1_mapping_refuses_an_unresolvable_gold_ref(tmp_path: Path) -> None:
    vault = workspace(tmp_path)

    try:
        shape1_bm25_cases(vault, [valid_row()])
    except ValueError as exc:
        message = str(exc)
    else:
        raise AssertionError("unresolvable gold must fail loud, never silently degrade")

    assert "shape1-example" in message
    assert "settles-2016-spaced-repetition#^p0007" in message


def test_present_at_depth_scores_membership_over_the_grouped_payload() -> None:
    payload = {
        "topic": "testing effect boundary conditions",
        "depth": 1,
        "groups": {
            "claims": [{"id": "knowledge/claims/testing-effect.md", "edges": []}],
            "question_notes": [],
            "tensions": [
                {
                    "id": "knowledge/tensions/complex-material.md",
                    "edges": [
                        {
                            "source": "catalog/sources/chen-2018-undesirable-difficulty",
                            "relation": "tension",
                            "target": "catalog/sources/moreira-2019-retrieval-practice",
                        }
                    ],
                }
            ],
            "works": [
                {"id": "catalog/sources/chen-2018-undesirable-difficulty", "edges": []},
                {"id": "catalog/sources/moreira-2019-retrieval-practice", "edges": []},
            ],
            "hubs": [],
        },
    }

    assert score_present_at_depth(payload, GOLD_TENSION_IDS) is True
    absent = [*GOLD_TENSION_IDS, "catalog/sources/absent-work"]
    assert score_present_at_depth(payload, absent) is False
    assert score_present_at_depth({}, GOLD_TENSION_IDS) is False
