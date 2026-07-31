"""R2 pipeline staging: ordered counts, strata, no-op rerank, trace (spec 1/4/6)."""

from __future__ import annotations

from memoria_vault.runtime import retrieval_pipeline as pipeline


def test_pipeline_counts_are_ordered_and_unique_suffix_repeated_filters() -> None:
    stages = pipeline.PipelineStages(40)
    stages.add_filter("type-filter", 25)
    stages.add_filter("project-slice", 12)
    stages.add_filter("type-filter", 9)
    stages.add_ranked(4)
    stages.add_returned(3)

    assert stages.rows() == [
        {"stage": "universe", "count": 40},
        {"stage": "type-filter", "count": 25},
        {"stage": "project-slice", "count": 12},
        {"stage": "type-filter#2", "count": 9},
        {"stage": "ranked", "count": 4},
        {"stage": "returned", "count": 3},
    ]
    assert pipeline.candidate_count(stages.rows()) == 9


def test_stage_order_is_enforced() -> None:
    stages = pipeline.PipelineStages(10)
    try:
        stages.add_returned(0)
    except ValueError as exc:
        assert "ranked" in str(exc)
    else:
        raise AssertionError("returned before ranked must be refused")
    stages.add_ranked(2)
    try:
        stages.add_filter("late-filter", 1)
    except ValueError as exc:
        assert "precede" in str(exc)
    else:
        raise AssertionError("filters after ranked must be refused")
    try:
        stages.add_ranked(2)
    except ValueError as exc:
        assert "twice" in str(exc)
    else:
        raise AssertionError("a second ranked stage must be refused")
    stages.add_returned(1)
    try:
        stages.add_returned(1)
    except ValueError as exc:
        assert "twice" in str(exc)
    else:
        raise AssertionError("a second returned stage must be refused")


def test_filter_stage_labels_remain_unique_when_a_name_uses_a_suffix() -> None:
    stages = pipeline.PipelineStages(5)
    stages.add_filter("type-filter#2", 4)
    stages.add_filter("type-filter", 3)
    stages.add_filter("type-filter", 2)
    stages.add_ranked(1)
    stages.add_returned(1)

    assert [row["stage"] for row in stages.rows()] == [
        "universe",
        "type-filter#2",
        "type-filter",
        "type-filter#3",
        "ranked",
        "returned",
    ]


def test_rows_require_terminal_stages() -> None:
    stages = pipeline.PipelineStages(3)
    try:
        stages.rows()
    except ValueError as exc:
        assert "ranked and returned" in str(exc)
    else:
        raise AssertionError("rows() without ranked/returned must be refused")


def test_reserved_filter_names_are_refused() -> None:
    stages = pipeline.PipelineStages(3)
    for bad in ("", "  ", "universe", "ranked", "returned"):
        try:
            stages.add_filter(bad, 1)
        except ValueError as exc:
            assert "filter stage name" in str(exc)
        else:
            raise AssertionError(f"filter name {bad!r} must be refused")


def test_excluded_strata_always_carries_all_three_names() -> None:
    assert pipeline.excluded_strata() == {"unchecked": 0, "stale": 0, "gated": 0}
    assert pipeline.excluded_strata(unchecked=2, gated=1) == {
        "unchecked": 2,
        "stale": 0,
        "gated": 1,
    }


def test_rerank_is_an_explicit_no_op_and_reports_off() -> None:
    hits = [("a.md", 2.0), ("b.md", 1.0)]
    assert pipeline.rerank(hits) == hits
    assert pipeline.rerank(hits) is not hits
    assert pipeline.RERANK_MODE == "off"


def test_honest_empty_uses_candidate_denominator_and_unchecked_count() -> None:
    stages = pipeline.PipelineStages(40)
    stages.add_ranked(0)
    stages.add_returned(0)
    strata = pipeline.excluded_strata(unchecked=12)

    assert pipeline.honest_empty(stages.rows(), strata) == (
        "0 of 40 candidates matched; 12 unchecked documents were not searched"
    )


def test_build_trace_carries_counts_scores_and_rerank_off() -> None:
    stages = pipeline.PipelineStages(5)
    stages.add_ranked(2)
    stages.add_returned(2)

    trace = pipeline.build_trace(stages.rows(), [("notes/a.md", 1.5), ("notes/b.md", 0.5)])

    assert trace == {
        "pipeline_counts": [
            {"stage": "universe", "count": 5},
            {"stage": "ranked", "count": 2},
            {"stage": "returned", "count": 2},
        ],
        "scores": [
            {"path": "notes/a.md", "score": 1.5},
            {"path": "notes/b.md", "score": 0.5},
        ],
        "rerank": "off",
    }


def test_build_trace_includes_fusion_inputs_only_beyond_one_leg() -> None:
    stages = pipeline.PipelineStages(5)
    stages.add_ranked(1)
    stages.add_returned(1)
    rows = stages.rows()

    single = pipeline.build_trace(rows, [], fusion_inputs=[{"leg": "bm25", "hits": 1}])
    assert "fusion_inputs" not in single

    fused = pipeline.build_trace(
        rows,
        [],
        fusion_inputs=[{"leg": "bm25", "hits": 1}, {"leg": "dense", "hits": 1}],
    )
    assert fused["fusion_inputs"] == [
        {"leg": "bm25", "hits": 1},
        {"leg": "dense", "hits": 1},
    ]
