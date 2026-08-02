"""Contract tests for the R2 section-7 retrieval-fixture preregistration form.

The loader IS the R3 impl-start check: it refuses unfrozen rows in spike
mode. Granularity mapping is pinned here too - Shape-1 span-ref gold maps
to containing-document paths for evaluate_bm25 (the baseline metric is
document-level hit@k until R1's passage-granular rows land, stated, never
silently degraded), and Shape-2 scores as present@depth membership over a
grouped explore payload.
"""

from __future__ import annotations

import datetime
from datetime import date
from pathlib import Path
from typing import Any

import pytest
import yaml

from memoria_vault.runtime import state
from memoria_vault.runtime.explore import explore_topic
from memoria_vault.runtime.search_index import evaluate_bm25
from tests import retrieval_fixtures
from tests.helpers import copy_memoria_dirs, write_checked_concept
from tests.retrieval_fixtures import (
    FIXTURES_DIR,
    load_retrieval_fixtures,
    metric_cutoff,
    score_present_at_depth,
    shape1_bm25_cases,
    validate_retrieval_fixture_rows,
)

GOLD_TENSION_IDS = [
    "catalog/sources/chen-2018-undesirable-difficulty",
    "catalog/sources/moreira-2019-retrieval-practice",
]

# The one date every registered row froze on (R2 F.3). Read from the file, never
# written back into it — a self-comparison would pin nothing.
FREEZE_DATE = "2026-08-02"

# Reached from `chen-2018` only through `moreira-2019`, so it is two hops from
# the Shape-2 seed and one hop from nothing the seed ranks.
TWO_HOP_CLAIM = "notes/claim-element-interactivity.md"


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


def seed_checked_edge(vault: Path, source: str, relation: str, target: str) -> None:
    """Insert one checked edge in identity space — the seam `explore` reads.

    Written by hand rather than through `replace_concept_edges` because that
    reconciler skips `tension` outright (PI-owned rows are exempt from the
    mirror pass), and the Shape-2 case this corpus serves *is* a tension.
    """
    with state.connect(vault) as conn:
        conn.execute(
            "INSERT INTO concept_edges("
            " source_concept_id, relation_type, target_concept_id, target_path,"
            " check_status, source_path, updated_at)"
            " VALUES (?, ?, ?, ?, 'checked', '', '2026-08-02T00:00:00Z')",
            (
                state.resolve_concept_id(conn, source),
                relation,
                state.resolve_concept_id(conn, target),
                target,
            ),
        )


def seed_retrieval_corpus(tmp_path: Path) -> Path:
    """Build the disposable vault the registered cases are evaluated over.

    Three works and five notes, which is what makes the declared cuts mean
    something: `hit@5` over a corpus where fewer than five documents score is
    not a cut at all, and a Shape-2 case whose gold is entirely BM25-seeded is
    a `hit@k` wearing `present@N`'s name. So `moreira-2019` is written to share
    no term with the Shape-2 topic — it can only arrive over the checked
    tension edge — and `TWO_HOP_CLAIM` can only arrive through `moreira-2019`.
    """
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
        "Desirable difficulties reverse for high element interactivity materials. ^p0004\n"
        "The testing effect has boundary conditions once intrinsic load is high.\n",
    )
    seed_fulltext_source(
        vault,
        "moreira-2019-retrieval-practice",
        "Retrieval Practice Across an Undergraduate Semester",
        "Retrieval practice schedules were compared across two undergraduate semesters.\n",
    )
    for rel, title, body in (
        (
            "notes/claim-interleaving.md",
            "Interleaving beats blocking",
            "Interleaved practice schedules improved delayed recall in the motor domain.",
        ),
        (
            "notes/claim-generation.md",
            "Generation aids retention",
            "The generation effect improves retention when the cue supports partial recall.",
        ),
        (
            "notes/question-lag.md",
            "How long should the lag be?",
            "Open question about optimal lag between repetition sessions in a model.",
        ),
        (
            "notes/claim-worked-examples.md",
            "Worked examples suit novices",
            "Worked examples reduce load for novices working difficult material.",
        ),
        (
            TWO_HOP_CLAIM,
            "Element interactivity moderates practice",
            "Element interactivity moderates how much a learner gains from practice.",
        ),
    ):
        mode = "question" if "question" in rel else "claim"
        write_checked_concept(
            vault,
            rel,
            f"type: note\ntitle: {title}\nmode: {mode}\ntags: []\nlinks: {{}}\n",
            body=body,
        )
    seed_checked_edge(
        vault,
        "catalog/sources/chen-2018-undesirable-difficulty",
        "tension",
        "catalog/sources/moreira-2019-retrieval-practice",
    )
    seed_checked_edge(
        vault,
        "catalog/sources/moreira-2019-retrieval-practice",
        "supports",
        TWO_HOP_CLAIM,
    )
    return vault


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
    assert [case["frozen"] for case in fixtures] == [True, True, True]
    assert {case["frozen_on"] for case in fixtures} == {FREEZE_DATE}
    assert fixtures[2]["gold"] == GOLD_TENSION_IDS
    assert fixtures[2]["metric"] == "present@1"


def test_spike_mode_takes_the_frozen_file_and_still_refuses_an_unfrozen_row(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """F.3 freezes the shipped rows; it does not relax the rule that froze them."""
    frozen = load_retrieval_fixtures(spike_mode=True)

    assert frozen
    assert all(case["frozen"] for case in frozen)
    assert {case["frozen_on"] for case in frozen} == {FREEZE_DATE}

    unfrozen = tmp_path / "retrieval"
    unfrozen.mkdir()
    (unfrozen / "cases.yaml").write_text(yaml.safe_dump([valid_row()]), encoding="utf-8")
    monkeypatch.setattr(retrieval_fixtures, "FIXTURES_DIR", unfrozen)
    assert load_retrieval_fixtures()  # outside spike mode the same row loads
    try:
        load_retrieval_fixtures(spike_mode=True)
    except ValueError as exc:
        message = str(exc)
    else:
        raise AssertionError("spike mode must still refuse an unfrozen row")

    assert "spike mode refuses unfrozen retrieval fixtures" in message
    assert "shape1-example" in message


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


def test_fixture_form_refuses_datetime_values_for_calendar_dates() -> None:
    yaml_timestamp = yaml.safe_load(
        """
        - id: yaml-timestamp
          shape: 1
          query: example query
          gold: [settles-2016-spaced-repetition#^p0007]
          metric: hit@5
          registered: 2026-07-17T12:30:00
          frozen: false
        """
    )
    assert isinstance(yaml_timestamp[0]["registered"], datetime.datetime)

    for broken in [
        valid_row(registered=datetime.datetime(2026, 7, 17, 12, 30, tzinfo=datetime.UTC)),
        yaml_timestamp[0],
    ]:
        try:
            validate_retrieval_fixture_rows([broken])
        except ValueError as exc:
            assert "registered must be a valid ISO calendar date" in str(exc)
        else:
            raise AssertionError("datetime calendar values must be refused")


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


def test_metric_cutoff_parses_the_declared_threshold_and_refuses_the_rest() -> None:
    assert metric_cutoff("hit@5") == ("hit", 5)
    assert metric_cutoff("recall@10") == ("recall", 10)
    assert metric_cutoff("present@2") == ("present", 2)

    for unsupported in ("hit", "hit@", "@5", "ndcg@5", "hit@0", "hit@k", "present@two"):
        try:
            metric_cutoff(unsupported)
        except ValueError as exc:
            assert "unsupported retrieval metric" in str(exc)
        else:
            raise AssertionError(f"metric must be refused, never defaulted: {unsupported!r}")


def test_registered_shape1_cases_hit_their_declared_cut(tmp_path: Path) -> None:
    """Each Shape-1 row is evaluated alone, against the threshold it declared."""
    vault = seed_retrieval_corpus(tmp_path)
    shape1 = [case for case in load_retrieval_fixtures() if case["shape"] == 1]

    assert [case["id"] for case in shape1] == [
        "shape1-spacing-effect-lookup",
        "shape1-undesirable-difficulty-boundary",
    ]
    for case in shape1:
        family, cut = metric_cutoff(case["metric"])
        assert family == "hit"
        baseline = evaluate_bm25(vault, shape1_bm25_cases(vault, [case]), k=cut)
        (result,) = baseline["results"]
        assert result["hit"] is True, (
            f"{case['id']}: {case['metric']} missed over {baseline['documents']} documents"
            f" - gold {result['relevant']} absent from top-{cut} {result['hits']}"
        )
        # The cut has to bite: over a corpus where fewer than `cut` documents
        # score at all, `hit@cut` is "the gold scored nonzero" wearing a
        # threshold's name.
        assert len(result["hits"]) == cut, (
            f"{case['id']}: only {len(result['hits'])} documents scored, so"
            f" {case['metric']} is not a threshold over this corpus"
        )


def test_registered_shape2_case_is_present_at_its_declared_depth(tmp_path: Path) -> None:
    """The Shape-2 row is scored by running explore at the depth its metric declares.

    Half of the gold is not retrievable: `moreira-2019` shares no term with the
    registered topic, so it reaches the payload only across the checked tension
    edge. That is the assertion below with `seed_score == 0.0`, and it is what
    keeps `present@1` from collapsing into `hit@k` over the seed ranking.
    """
    vault = seed_retrieval_corpus(tmp_path)
    (case,) = [row for row in load_retrieval_fixtures() if row["shape"] == 2]
    family, depth = metric_cutoff(case["metric"])

    assert (family, depth) == ("present", 1)
    payload = explore_topic(vault, case["query"], depth=depth)

    assert payload["depth"] == depth
    assert score_present_at_depth(payload, case["gold"]) is True, (
        f"{case['id']}: {case['metric']} for topic {case['query']!r} at depth"
        f" {payload['depth']} missed {sorted(set(case['gold']))}"
    )
    works = {str(entry["id"]): entry for entry in payload["works"]}
    assert set(case["gold"]) <= set(works)
    assert works["catalog/sources/chen-2018-undesirable-difficulty"]["seed_score"] > 0.0
    assert works["catalog/sources/moreira-2019-retrieval-practice"]["seed_score"] == 0.0
    assert payload["tensions"] == [
        {
            "pair": GOLD_TENSION_IDS,
            "titles": [
                "Undesirable Difficulty Effects in High-Element Interactivity Materials",
                "Retrieval Practice Across an Undergraduate Semester",
            ],
            "relation_type": "tension",
        }
    ]


def test_a_present_at_2_case_is_not_satisfied_by_a_depth_1_payload(tmp_path: Path) -> None:
    """`present@N` is scored at N, and a runner that ignored N would look green.

    The trap this closes: the registered `present@1` gold *is* in the depth-1
    payload, so a runner that hard-coded depth 1 passes every shipped case. It
    is only the two-hop probe that separates "scored at the declared depth"
    from "scored at whatever depth the runner happened to use".
    """
    vault = seed_retrieval_corpus(tmp_path)
    (registered,) = [row for row in load_retrieval_fixtures() if row["shape"] == 2]
    (probe,) = validate_retrieval_fixture_rows(
        [
            valid_row(
                id="shape2-two-hop-probe",
                shape=2,
                query=registered["query"],
                gold=[TWO_HOP_CLAIM],
                metric="present@2",
            )
        ]
    )
    family, depth = metric_cutoff(probe["metric"])

    assert (family, depth) == ("present", 2)
    shallow = explore_topic(vault, probe["query"], depth=1)
    deep = explore_topic(vault, probe["query"], depth=depth)

    assert shallow["depth"] == 1
    assert deep["depth"] == depth
    assert score_present_at_depth(shallow, probe["gold"]) is False, (
        f"{probe['id']}: {probe['metric']} scored True at depth {shallow['depth']}"
    )
    assert score_present_at_depth(deep, probe["gold"]) is True
    # The membership that *does* look right at depth 1 — which is exactly why
    # the probe above is the only thing that can catch a depth-blind runner.
    assert score_present_at_depth(shallow, registered["gold"]) is True
