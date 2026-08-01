"""Contract tests for R2's pure-read topic-surfacing engine."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from memoria_vault.runtime import explore, graph_sql, state
from memoria_vault.runtime.policy.audit import sha256_file
from tests.floor_lib import read_only_guard
from tests.helpers import copy_memoria_dirs


def _vault(tmp_path: Path) -> Path:
    copy_memoria_dirs(tmp_path, "schemas")
    return tmp_path


def _concept(
    vault: Path,
    relpath: str,
    title: str,
    body: str,
    *,
    mode: str = "",
    status: str = "checked",
    links: list[str] | None = None,
) -> Path:
    path = vault / relpath
    path.parent.mkdir(parents=True, exist_ok=True)
    concept_type = (
        "hub"
        if relpath.startswith("hubs/")
        else "project"
        if relpath.startswith("projects/")
        else "note"
    )
    frontmatter = [
        "---",
        f"type: {concept_type}",
        f"check_status: {status}",
        f"title: {title}",
    ]
    if mode:
        frontmatter.append(f"mode: {mode}")
    if links:
        frontmatter.extend(["links:", "  related:", *[f"    - {link}" for link in links]])
    frontmatter.append("---")
    path.write_text("\n".join([*frontmatter, body, ""]), encoding="utf-8")
    state.record_observed_file_edit(
        vault,
        output_id=relpath,
        concept_type=concept_type,
        output_sha256=sha256_file(path),
    )
    state.set_concept_verdict(vault, relpath, status)
    return path


def _work(vault: Path, work_id: str, title: str, body: str) -> None:
    content = vault / f".memoria/blobs/source-content/{work_id}/full-text/{work_id}.txt"
    content.parent.mkdir(parents=True, exist_ok=True)
    content.write_text(body, encoding="utf-8")
    state.upsert_catalog_record(
        vault,
        work_id=work_id,
        title=title,
        text_status="full-text",
        check_status="checked",
        content_path=content.relative_to(vault).as_posix(),
    )


def _insert_tensions(vault: Path) -> None:
    with state.connect(vault) as conn:
        conn.executemany(
            "INSERT INTO concept_edges("
            " source_concept_id, relation_type, target_concept_id, target_path,"
            " check_status, source_path, updated_at)"
            " VALUES (?, ?, ?, ?, ?, ?, ?)",
            [
                (
                    "notes/claim-spacing.md",
                    "tension",
                    "notes/claim-massed.md",
                    "notes/claim-massed.md",
                    "checked",
                    "",
                    "2026-07-17T00:00:00Z",
                ),
                (
                    "notes/claim-massed.md",
                    "tension",
                    "notes/claim-spacing.md",
                    "notes/claim-spacing.md",
                    "checked",
                    "",
                    "2026-07-17T00:00:00Z",
                ),
            ],
        )


def _fixture_vault(tmp_path: Path) -> Path:
    vault = _vault(tmp_path)
    _concept(
        vault,
        "notes/claim-spacing.md",
        "Spacing beats cramming",
        "The spacing effect improves retention.",
        mode="claim",
    )
    _concept(
        vault,
        "notes/claim-massed.md",
        "Massed practice is superior",
        "Massed practice wins in short-horizon tests.",
        mode="claim",
    )
    _concept(
        vault,
        "notes/question-spacing.md",
        "Where does spacing break down?",
        "Open question about spacing boundary conditions.",
        mode="question",
    )
    _concept(
        vault,
        "hubs/memory.md",
        "Memory hub",
        "Retrieval practice and memory.",
    )
    _concept(vault, "hubs/consolidation.md", "Consolidation hub", "Consolidation pathways.")
    _concept(vault, "notes/generic.md", "Generic note", "GENERIC SPACING CANARY")
    _concept(
        vault,
        "projects/memory.md",
        "Memory project",
        "PROJECT SPACING CANARY",
        links=["notes/claim-spacing.md", "hubs/memory.md"],
    )
    _concept(
        vault,
        "notes/unchecked.md",
        "Unchecked note",
        "Unchecked spacing noise.",
        status="unchecked",
    )
    _work(
        vault,
        "settles-2016",
        "A spaced repetition model",
        "A spacing study of retention schedules.",
    )
    state.replace_concept_edges(
        vault,
        [
            {
                "source_concept_id": "notes/claim-spacing.md",
                "relation_type": "supports",
                "target_concept_id": "catalog/sources/settles-2016",
                "check_status": "checked",
            },
            {
                "source_concept_id": "notes/claim-massed.md",
                "relation_type": "supports",
                "target_concept_id": "catalog/sources/settles-2016",
                "check_status": "checked",
            },
            {
                "source_concept_id": "notes/claim-spacing.md",
                "relation_type": "extends",
                "target_concept_id": "hubs/memory.md",
                "check_status": "checked",
            },
            {
                "source_concept_id": "hubs/memory.md",
                "relation_type": "extends",
                "target_concept_id": "hubs/consolidation.md",
                "check_status": "checked",
            },
        ],
    )
    _insert_tensions(vault)
    state.replace_evidence_sets(
        vault,
        [
            {
                "id": "ev-0001",
                "block_ref": "notes/claim-massed.md#^blk-0001",
                "items": ["settles-2016#^p0001"],
                "type": "single-span",
                "state": "complete",
                "review_required": False,
                "bind": False,
            },
            {
                "id": "ev-0002",
                "block_ref": "notes/claim-massed.md#^blk-0002",
                "items": [],
                "type": "single-span",
                "state": "evidence-incomplete",
                "review_required": True,
                "bind": False,
            },
        ],
    )
    return vault


def _stages(payload: dict) -> dict[str, int]:
    return {str(row["stage"]): int(row["count"]) for row in payload["pipeline_counts"]}


def _returned_ids(payload: dict) -> set[str]:
    return {
        str(entry["id"])
        for group in ("claims", "questions", "works", "hubs")
        for entry in payload[group]
    }


def test_explore_topic_rejects_depth_outside_hard_cap(tmp_path: Path) -> None:
    vault = _fixture_vault(tmp_path)

    for depth, expected in ((0, "at least 1"), (3, "hard cap of 2")):
        with pytest.raises(ValueError, match=expected):
            explore.explore_topic(vault, "spacing", depth=depth)


def test_explore_groups_safe_displayable_kinds_with_grounds_and_trace(tmp_path: Path) -> None:
    vault = _fixture_vault(tmp_path)

    payload = explore.explore_topic(vault, "spacing", trace=True)

    assert payload["topic"] == "spacing"
    assert payload["depth"] == 1
    assert payload["excluded_strata"] == {"unchecked": 1, "stale": 0, "gated": 0}
    assert payload["pipeline_counts"] == [
        {"stage": "universe", "count": 8},
        {"stage": "displayable-kind", "count": 6},
        {"stage": "ranked", "count": 3},
        {"stage": "seed", "count": 3},
        {"stage": "neighborhood", "count": 5},
        {"stage": "returned", "count": 5},
    ]
    claims = {entry["id"]: entry for entry in payload["claims"]}
    assert set(claims) == {"notes/claim-massed.md", "notes/claim-spacing.md"}
    assert claims["notes/claim-spacing.md"]["grounds_count"] == 0
    assert claims["notes/claim-spacing.md"]["zero_grounds"] is True
    assert claims["notes/claim-massed.md"]["grounds_count"] == 1
    assert claims["notes/claim-massed.md"]["zero_grounds"] is False
    assert claims["notes/claim-spacing.md"]["edges"] == [
        {"relation_type": "extends", "target": "hubs/memory.md"},
        {"relation_type": "supports", "target": "catalog/sources/settles-2016"},
        {"relation_type": "tension", "target": "notes/claim-massed.md"},
    ]
    assert [entry["id"] for entry in payload["questions"]] == ["notes/question-spacing.md"]
    assert [entry["id"] for entry in payload["works"]] == ["catalog/sources/settles-2016"]
    assert [entry["id"] for entry in payload["hubs"]] == ["hubs/memory.md"]
    assert payload["tensions"] == [
        {
            "pair": ["notes/claim-massed.md", "notes/claim-spacing.md"],
            "titles": ["Massed practice is superior", "Spacing beats cramming"],
            "relation_type": "tension",
        }
    ]
    assert payload["trace"]["rerank"] == "off"
    assert payload["trace"]["pipeline_counts"] == payload["pipeline_counts"]
    assert {row["path"] for row in payload["trace"]["scores"]} <= _returned_ids(payload)
    serialized = json.dumps(payload, sort_keys=True)
    assert "notes/generic.md" not in serialized
    assert "projects/memory.md" not in serialized
    assert "GENERIC SPACING CANARY" not in serialized
    assert "PROJECT SPACING CANARY" not in serialized


def test_explore_project_filter_depth_and_versus_share_one_universe(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    vault = _fixture_vault(tmp_path)
    calls: list[dict[str, object]] = []
    original = explore.checked_search_universe

    def observed(*args: object, **kwargs: object) -> dict:
        calls.append(dict(kwargs))
        return original(*args, **kwargs)

    monkeypatch.setattr(explore, "checked_search_universe", observed)
    versus = explore.explore_topic(vault, "spacing", versus="massed", trace=True)

    assert calls == [{"enqueue_scan": False}]
    assert versus["a"]["excluded_strata"] == versus["b"]["excluded_strata"]
    assert "catalog/sources/settles-2016" in versus["intersection"]["ids"]
    assert versus["crossing_tensions"]["count"] == 1
    assert set(versus["trace"]) == {"a", "b"}
    assert versus["trace"]["a"]["rerank"] == "off"
    assert versus["trace"]["b"]["rerank"] == "off"

    project = explore.explore_topic(vault, "spacing", project="memory")
    assert _stages(project)["project-slice"] == 2
    assert _returned_ids(project) == {"notes/claim-spacing.md", "hubs/memory.md"}
    assert project["tensions"] == []

    monkeypatch.setattr(
        explore.graph_sql,
        "_active_project_slices",
        lambda _vault: {"projects/memory.md": {"hubs/consolidation.md"}},
    )
    active = explore.explore_topic(vault, "consolidation", project="memory")
    assert _returned_ids(active) == {"hubs/consolidation.md"}

    one_hop = explore.explore_topic(vault, "massed", depth=1)
    two_hop = explore.explore_topic(vault, "massed", depth=2)
    assert "hubs/memory.md" not in _returned_ids(one_hop)
    assert "hubs/memory.md" in _returned_ids(two_hop)


def test_explore_honest_empty_and_gated_neighbor_are_pure_reads(tmp_path: Path) -> None:
    vault = _fixture_vault(tmp_path)
    empty = explore.explore_topic(vault, "zeppelin", trace=True)

    assert (
        empty["honest_empty"]
        == "0 of 6 candidates matched; 1 unchecked documents were not searched"
    )
    assert _stages(empty)["ranked"] == 0
    assert _stages(empty)["returned"] == 0
    assert all(empty[group] == [] for group in ("claims", "questions", "tensions", "works", "hubs"))
    versus = explore.explore_topic(vault, "spacing", versus="zeppelin", trace=True)
    assert versus["b"]["honest_empty"] == empty["honest_empty"]
    assert versus["trace"]["b"]["scores"] == []

    gated = _concept(
        vault,
        "notes/gated.md",
        "Gated claim",
        "GATED NEIGHBOR CANARY",
        mode="claim",
    )
    with state.connect(vault) as conn:
        conn.execute(
            "INSERT INTO concept_edges("
            " source_concept_id, relation_type, target_concept_id,"
            " check_status, source_path, updated_at)"
            " VALUES (?, ?, ?, ?, ?, ?)",
            (
                "notes/claim-spacing.md",
                "supports",
                gated.relative_to(vault).as_posix(),
                "checked",
                "",
                "2026-07-17T00:00:00Z",
            ),
        )
        before = conn.execute("SELECT COUNT(*) FROM operation_requests").fetchone()[0]
    gated.write_text(
        "---\ntype: note\ncheck_status: checked\ntitle: Gated claim\nmode: claim\n---\n"
        "GATED NEIGHBOR TAMPERED CANARY\n",
        encoding="utf-8",
    )

    with read_only_guard(vault):
        payload = explore.explore_topic(vault, "spacing", trace=True)

    serialized = json.dumps(payload, sort_keys=True)
    assert gated.relative_to(vault).as_posix() not in serialized
    assert "Gated claim" not in serialized
    assert "GATED NEIGHBOR TAMPERED CANARY" not in serialized
    assert payload["excluded_strata"]["gated"] == 1
    assert gated.relative_to(vault).as_posix() not in _returned_ids(payload)
    assert all(
        gated.relative_to(vault).as_posix() not in {edge["target"] for edge in entry["edges"]}
        for entry in payload["claims"]
    )
    assert {row["path"] for row in payload["trace"]["scores"]} <= _returned_ids(payload)
    with state.connect(vault) as conn:
        after = conn.execute("SELECT COUNT(*) FROM operation_requests").fetchone()[0]
    assert after == before


def test_explore_project_slice_never_traverses_gated_link_closures(tmp_path: Path) -> None:
    vault = _fixture_vault(tmp_path)
    claim = vault / "notes/claim-spacing.md"
    claim.write_text(
        "---\n"
        "type: note\n"
        "check_status: checked\n"
        "title: Spacing beats cramming\n"
        "mode: claim\n"
        "links:\n"
        "  related:\n"
        "    - hubs/consolidation.md\n"
        "---\n"
        "TAMPERED PROJECT-LINK CANARY\n",
        encoding="utf-8",
    )
    with state.connect(vault) as conn:
        before = conn.execute("SELECT COUNT(*) FROM operation_requests").fetchone()[0]

    with read_only_guard(vault):
        payload = explore.explore_topic(vault, "consolidation", project="memory", trace=True)

    serialized = json.dumps(payload, sort_keys=True)
    assert payload["excluded_strata"]["gated"] == 1
    assert (
        payload["honest_empty"]
        == "0 of 1 candidates matched; 1 unchecked documents were not searched"
    )
    assert _stages(payload)["project-slice"] == 1
    assert "hubs/consolidation.md" not in serialized
    assert "TAMPERED PROJECT-LINK CANARY" not in serialized
    with state.connect(vault) as conn:
        after = conn.execute("SELECT COUNT(*) FROM operation_requests").fetchone()[0]
    assert after == before


def test_explore_refuses_a_gated_nested_project_without_flat_fallback(tmp_path: Path) -> None:
    vault = _fixture_vault(tmp_path)
    nested = _concept(
        vault,
        "projects/collision/project.md",
        "Nested project",
        "Nested project content.",
        links=["hubs/consolidation.md"],
    )
    _concept(
        vault,
        "projects/collision.md",
        "Flat project",
        "Flat project content.",
        links=["hubs/memory.md"],
    )
    nested.write_text(
        nested.read_text(encoding="utf-8") + "TAMPERED NESTED PROJECT CANARY\n",
        encoding="utf-8",
    )

    with read_only_guard(vault):
        payload = explore.explore_topic(vault, "memory", project="collision", trace=True)

    serialized = json.dumps(payload, sort_keys=True)
    assert payload["excluded_strata"]["gated"] == 1
    assert _stages(payload)["project-slice"] == 0
    assert (
        payload["honest_empty"]
        == "0 of 0 candidates matched; 1 unchecked documents were not searched"
    )
    assert "hubs/memory.md" not in serialized
    assert "TAMPERED NESTED PROJECT CANARY" not in serialized


def test_project_slice_shares_one_links_resolver_with_graph_sql(tmp_path: Path) -> None:
    """One resolver, not a second copy — and it rejects what `links` validation rejects.

    `notes/../claim-spacing.md` normalizes back inside the vault, so the duplicated
    resolver these modules used to carry followed it into a real note that the
    validator refuses to accept as a target.
    """
    assert explore._link_target is graph_sql._link_target
    assert explore._link_targets is graph_sql._link_targets

    vault = _fixture_vault(tmp_path)
    _concept(
        vault,
        "projects/escape.md",
        "Escape project",
        "Escape project body.",
        links=["notes/../claim-spacing.md"],
    )

    payload = explore.explore_topic(vault, "spacing", project="escape")

    assert _stages(payload)["project-slice"] == 0
