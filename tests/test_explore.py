"""Contract tests for R2's pure-read topic-surfacing engine."""

from __future__ import annotations

import functools
import hashlib
import json
from pathlib import Path

import pytest

from memoria_vault.cli import main
from memoria_vault.runtime import explore, propagation, state
from memoria_vault.runtime.policy.audit import sha256_file
from memoria_vault.runtime.search_index import checked_search_universe
from tests.floor_lib import read_only_guard
from tests.helpers import copy_memoria_dirs


def _vault(tmp_path: Path) -> Path:
    copy_memoria_dirs(tmp_path, "schemas")
    return tmp_path


def _ulid_for(relpath: str) -> str:
    """A stable, valid ULID for one path that looks nothing like it."""
    alphabet = "0123456789ABCDEFGHJKMNPQRSTVWXYZ"
    digest = hashlib.sha256(relpath.encode("utf-8")).digest()
    return "".join(alphabet[byte % 32] for byte in digest[:26])


def _concept(
    vault: Path,
    relpath: str,
    title: str,
    body: str,
    *,
    mode: str = "",
    status: str = "checked",
    links: list[str] | None = None,
    thesis: str = "",
    ulid_keyed: bool = False,
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
    if ulid_keyed:
        # The identity `_concept_key_for_file` reads: from here the Concept's id
        # is a ULID and only `concepts.path` still says `relpath`.
        frontmatter.append(f"id: {_ulid_for(relpath)}")
    if mode:
        frontmatter.append(f"mode: {mode}")
    if thesis:
        frontmatter.append(f"thesis: {thesis}")
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


def _insert_tension_rows(vault: Path, rows: list[tuple[str, str, str]]) -> None:
    """Seed PI-owned tension rows by identity — the mirror writer never persists one."""
    with state.connect(vault) as conn:
        conn.executemany(
            "INSERT INTO concept_edges("
            " source_concept_id, relation_type, target_concept_id, target_path,"
            " check_status, source_path, updated_at)"
            " VALUES (?, ?, ?, ?, ?, ?, ?)",
            [
                (
                    state.resolve_concept_id(conn, source),
                    "tension",
                    state.resolve_concept_id(conn, target),
                    target,
                    status,
                    "",
                    "2026-07-17T00:00:00Z",
                )
                for source, target, status in rows
            ],
        )


def _insert_tensions(vault: Path) -> None:
    _insert_tension_rows(
        vault,
        [
            ("notes/claim-spacing.md", "notes/claim-massed.md", "checked"),
            ("notes/claim-massed.md", "notes/claim-spacing.md", "checked"),
            # Unchecked, between two Concepts this topic displays: the only thing
            # keeping it out of the `tensions` group is the checked gate. The
            # unchecked `extends` row seeded with the mirror edges cannot stand in
            # for it — `_tension_pairs` discards a non-tension relation before
            # that gate is reached.
            ("notes/question-spacing.md", "notes/claim-spacing.md", "unchecked"),
        ],
    )


_MIRROR_EDGES: list[dict[str, str]] = [
    # `projects/memory.md` joins the graph here, not through its `links:` block:
    # `active_project_slices` walks the `concept_edges` mirror, and this fixture
    # never reindexes, so frontmatter alone would slice every project to itself.
    {
        "source_concept_id": "projects/memory.md",
        "relation_type": "supports",
        "target_concept_id": "notes/claim-spacing.md",
        "check_status": "checked",
    },
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
    # Unchecked topology between two displayed Concepts: it must never reach the
    # payload, which only ever shows safe edges, and it must never carry
    # `notes/question-spacing.md` into a *vetted* project slice.
    {
        "source_concept_id": "notes/question-spacing.md",
        "relation_type": "extends",
        "target_concept_id": "notes/claim-spacing.md",
        "check_status": "unchecked",
    },
]


def _replace_mirror_edges(vault: Path, *extra: dict[str, str]) -> None:
    """Rewrite the links mirror as the fixture's rows plus ``extra``.

    ``replace_concept_edges`` is a full reconcile, so a test that wants one more
    edge has to re-state the fixture's. PI-owned tension rows are exempt from
    that pass and survive.
    """
    state.replace_concept_edges(vault, [*_MIRROR_EDGES, *extra])


def _fixture_vault(tmp_path: Path, *, ulid_keyed: bool = False) -> Path:
    vault = _vault(tmp_path)
    concept = functools.partial(_concept, vault, ulid_keyed=ulid_keyed)
    concept(
        "notes/claim-spacing.md",
        "Spacing beats cramming",
        "The spacing effect improves retention.",
        mode="claim",
    )
    concept(
        "notes/claim-massed.md",
        "Massed practice is superior",
        "Massed practice wins in short-horizon tests.",
        mode="claim",
    )
    concept(
        "notes/question-spacing.md",
        "Where does spacing break down?",
        "Open question about spacing boundary conditions.",
        mode="question",
    )
    concept(
        "hubs/memory.md",
        "Memory hub",
        "Retrieval practice and memory.",
    )
    concept("hubs/consolidation.md", "Consolidation hub", "Consolidation pathways.")
    concept("notes/generic.md", "Generic note", "GENERIC SPACING CANARY")
    concept(
        "projects/memory.md",
        "Memory project",
        "PROJECT SPACING CANARY",
        links=["notes/claim-spacing.md", "hubs/memory.md"],
    )
    concept(
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
    _replace_mirror_edges(vault)
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


def _cli_explore_json(
    capsys: pytest.CaptureFixture[str], vault: Path, *argv: str
) -> tuple[int, dict]:
    """Run the shipped command on the JSON front and return its exit code + envelope."""
    rc = main(["explore", *argv, "--workspace", str(vault), "--json"])
    return rc, json.loads(capsys.readouterr().out)


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


@pytest.mark.parametrize("ulid_keyed", [False, True], ids=["path-keyed", "ulid-keyed"])
def test_explore_serves_one_graph_whichever_space_keys_the_concepts(
    tmp_path: Path, ulid_keyed: bool
) -> None:
    """The NID-B.2 regression this surface owned, asserted from both namespaces.

    A machine-authored note keys by its frontmatter ULID and a catalog work by
    its bare `work_id`, so for a normal v16 vault no stored edge endpoint is a
    path at all. Reading those identity columns as ids served zero edges and zero
    tensions here — a silent, total loss for exactly the notes Memoria writes.
    Both arms must produce the same payload; the ULID arm is the one that failed.
    """
    vault = _fixture_vault(tmp_path, ulid_keyed=ulid_keyed)
    with state.connect(vault) as conn:
        stored = {
            str(row["source_concept_id"])
            for row in conn.execute("SELECT source_concept_id FROM concept_edges")
        }
    # Not a degenerate fixture: under ULID keying no stored identity is a path.
    assert any("/" in identity for identity in stored) is not ulid_keyed

    payload = explore.explore_topic(vault, "spacing")

    assert _returned_ids(payload) == {
        "catalog/sources/settles-2016",
        "hubs/memory.md",
        "notes/claim-massed.md",
        "notes/claim-spacing.md",
        "notes/question-spacing.md",
    }
    edges_by_id = {
        str(entry["id"]): entry["edges"]
        for group in ("claims", "questions", "works", "hubs")
        for entry in payload[group]
    }
    assert edges_by_id["notes/claim-spacing.md"] == [
        {"relation_type": "extends", "target": "hubs/memory.md"},
        {"relation_type": "supports", "target": "catalog/sources/settles-2016"},
        {"relation_type": "tension", "target": "notes/claim-massed.md"},
    ]
    # The bare `work_id` identity, rendered at the virtual path the surface uses.
    assert edges_by_id["catalog/sources/settles-2016"] == [
        {"relation_type": "supports", "target": "notes/claim-massed.md"},
        {"relation_type": "supports", "target": "notes/claim-spacing.md"},
    ]
    assert payload["tensions"] == [
        {
            "pair": ["notes/claim-massed.md", "notes/claim-spacing.md"],
            "titles": ["Massed practice is superior", "Spacing beats cramming"],
            "relation_type": "tension",
        }
    ]
    if ulid_keyed:
        # Only meaningful on this arm: path keying makes identity and path equal,
        # so the same check there would forbid the answer.
        serialized = json.dumps(payload)
        assert not [identity for identity in stored if identity in serialized]


def test_versus_crossing_tensions_exclude_a_same_side_pair(tmp_path: Path) -> None:
    """A tension inside one side is not a *crossing* tension.

    Seeded here rather than in the shared fixture on purpose: in this corpus side
    B is a subset of side A, so any same-side pair is also a pair of the
    single-topic run, and putting it in the fixture would rewrite that payload
    instead of testing this gate. Both halves are asserted, so the exclusion is
    provably the crossing test and not the safe-id gate that precedes it.
    """
    vault = _fixture_vault(tmp_path)
    _insert_tension_rows(vault, [("hubs/memory.md", "notes/question-spacing.md", "checked")])

    versus = explore.explore_topic(vault, "spacing", versus="massed")
    solo = explore.explore_topic(vault, "spacing")

    same_side = {"hubs/memory.md", "notes/question-spacing.md"}
    assert same_side <= _returned_ids(versus["a"])
    assert not same_side & _returned_ids(versus["b"])
    assert versus["crossing_tensions"]["count"] == 1
    assert [pair["pair"] for pair in solo["tensions"]] == [
        ["hubs/memory.md", "notes/question-spacing.md"],
        ["notes/claim-massed.md", "notes/claim-spacing.md"],
    ]


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
    # The vetted gate is what narrows this, not a smaller corpus:
    # `notes/question-spacing.md` is a strong match for "spacing" and reaches the
    # project only over an *unchecked* edge, so `checked_only=True` is the single
    # thing keeping it out of a slice that otherwise spans the whole component.
    assert _stages(project)["project-slice"] == 5
    assert "notes/question-spacing.md" in _returned_ids(explore.explore_topic(vault, "spacing"))
    assert _returned_ids(project) == {
        "catalog/sources/settles-2016",
        "hubs/memory.md",
        "notes/claim-massed.md",
        "notes/claim-spacing.md",
    }

    # A second project, so the filter is provably *this project's* slice and not
    # a constant or the whole universe: `projects/lonely.md` is an active project
    # the provider answers for, and its closure is the container alone.
    _concept(vault, "projects/lonely.md", "Lonely project", "Lonely body.")
    lonely = explore.explore_topic(vault, "spacing", project="lonely")
    assert _stages(lonely)["project-slice"] == 0

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


def test_explore_project_slice_never_readmits_a_gated_member(tmp_path: Path) -> None:
    """Slice membership does not put a gated Concept back in front of the researcher.

    The slice comes from the mirror now, and the mirror still lists a Concept
    whose file has drifted from its checked record — so the ordering is
    load-bearing: the universe gate runs first and the slice intersects what
    survives it. A reader that filtered the universe *by* the slice, or that
    took the slice as the candidate set, would serve the tampered bytes.
    """
    vault = _fixture_vault(tmp_path)
    claim = vault / "notes/claim-spacing.md"
    claim.write_text(
        "---\n"
        "type: note\n"
        "check_status: checked\n"
        "title: Spacing beats cramming\n"
        "mode: claim\n"
        "---\n"
        "TAMPERED PROJECT-LINK CANARY\n",
        encoding="utf-8",
    )
    slice_ids = explore._vetted_project_slice_ids(
        vault, "memory", checked_search_universe(vault, enqueue_scan=False)["documents"]
    )
    with state.connect(vault) as conn:
        before = conn.execute("SELECT COUNT(*) FROM operation_requests").fetchone()[0]

    with read_only_guard(vault):
        payload = explore.explore_topic(vault, "consolidation", project="memory", trace=True)

    serialized = json.dumps(payload, sort_keys=True)
    assert payload["excluded_strata"]["gated"] == 1
    # The gated Concept is a member — the exclusion is the gate's doing, not an
    # empty slice, which is what makes the two assertions below non-vacuous.
    assert "notes/claim-spacing.md" in slice_ids
    assert _stages(payload)["project-slice"] == 4
    assert "notes/claim-spacing.md" not in _returned_ids(payload)
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
    )
    _concept(vault, "projects/collision.md", "Flat project", "Flat project content.")
    # Both collision projects are given *real* mirror topology, and both must be
    # non-empty for this test to say anything. The gated nested project needs a
    # slice so that "a gated project slices to nothing" is the universe gate's
    # doing and not an empty graph; the flat one needs a slice so that the
    # refused fallback would have had something to leak.
    _replace_mirror_edges(
        vault,
        {
            "source_concept_id": "projects/collision.md",
            "relation_type": "supports",
            "target_concept_id": "hubs/memory.md",
            "check_status": "checked",
        },
        {
            "source_concept_id": "projects/collision/project.md",
            "relation_type": "supports",
            "target_concept_id": "hubs/consolidation.md",
            "check_status": "checked",
        },
    )
    assert propagation.active_project_slices(vault, checked_only=True)[
        "projects/collision/project.md"
    ] > {"projects/collision/project.md"}
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


def test_vetted_project_slice_seeds_the_thesis_through_the_shared_normalizer(
    tmp_path: Path,
) -> None:
    """The vetted slice takes its `thesis:` seed in path space (issue #1623).

    `edges.thesis_rel` owns the rule and `test_query_substrate` pins its table;
    this is the retrieval-side observer that the seed reaches an answer here.
    `projects/bare.md` touches the graph only through `thesis:`, so a bare stem
    that failed to complete under `notes/` would slice it to nothing.

    It is also where the project-file subtraction is visible: `title` and `dot`
    resolve to no seed and answer `set()`, not `{"projects/title.md"}` — a slice
    of one that reads like a hit. The subtraction drops *the project asked for*,
    which is why `projects/memory.md` stays in `bare`'s answer.
    """
    vault = _fixture_vault(tmp_path)
    _concept(vault, "projects/bare.md", "Bare thesis", "Body.", thesis="claim-spacing")
    _concept(
        vault, "projects/title.md", "Title thesis", "Body.", thesis="'Spacing: beats cramming'"
    )
    _concept(vault, "projects/dot.md", "Dot thesis", "Body.", thesis="'.'")

    bare = explore.explore_topic(vault, "spacing", project="bare")
    title = explore.explore_topic(vault, "spacing", project="title")

    assert "notes/claim-spacing.md" in _returned_ids(bare)
    assert _stages(bare)["project-slice"] == 5
    assert _stages(title)["project-slice"] == 0
    # The membership filter above cannot see a seed no document carries, so the
    # closure itself is the only observer of `notes/.md` — the absorbing sink a
    # `notes/` + `.md` completion over an empty path used to admit.
    documents = checked_search_universe(vault)["documents"]
    assert explore._vetted_project_slice_ids(vault, "dot", documents) == set()
    assert explore._vetted_project_slice_ids(vault, "bare", documents) == {
        "catalog/sources/settles-2016",
        "hubs/consolidation.md",
        "hubs/memory.md",
        "notes/claim-massed.md",
        "notes/claim-spacing.md",
        "projects/memory.md",
    }


def test_cli_explore_honest_empty_names_its_denominator_on_both_fronts(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """The §4 sentence reaches both shipped fronts, and it says *why* it is empty.

    An empty answer is an absorbing state: a swallowed crash, an index that was
    never built, and a filter that removed everything all render as "nothing
    found". So the pin is never `honest_empty == <string>` alone. Three
    observations separate an honest empty from a broken one:

    * the stage row shows the corpus *was* read (`universe` 8) and the kind
      filter *did* leave candidates (`displayable-kind` 6) — the zero enters at
      `ranked`, which is where "this topic has no answer" is supposed to enter;
    * the denominator moves with the last filter stage — 6 with no project, 5
      under `--project memory` — so it is the candidate set the query actually
      faced, not `universe`, not a constant;
    * the same vault, same command, a different topic returns five entries and
      carries **no** `honest_empty` key at all.
    """
    vault = _fixture_vault(tmp_path)
    sentence = "0 of 6 candidates matched; 1 unchecked documents were not searched"

    rc, output = _cli_explore_json(capsys, vault, "zeppelin")

    assert rc == 0
    assert output["ok"] is True
    empty = output["explore"]
    assert empty["honest_empty"] == sentence
    assert _stages(empty) == {
        "universe": 8,
        "displayable-kind": 6,
        "ranked": 0,
        "seed": 0,
        "neighborhood": 0,
        "returned": 0,
    }
    assert empty["excluded_strata"] == {"unchecked": 1, "stale": 0, "gated": 0}
    for group in ("claims", "questions", "tensions", "works", "hubs"):
        assert empty[group] == []

    # The text front prints the sentence and nothing else — never a bare
    # summary, never an empty page.
    rc = main(["explore", "zeppelin", "--workspace", str(vault)])
    assert rc == 0
    assert capsys.readouterr().out.strip() == sentence

    # Same corpus, one more filter stage: the denominator follows it.
    rc, output = _cli_explore_json(capsys, vault, "zeppelin", "--project", "memory")
    assert rc == 0
    sliced = output["explore"]
    assert _stages(sliced)["project-slice"] == 5
    assert (
        sliced["honest_empty"]
        == "0 of 5 candidates matched; 1 unchecked documents were not searched"
    )

    # The control that makes all of the above non-vacuous: this vault answers.
    rc, output = _cli_explore_json(capsys, vault, "spacing")
    answered = output["explore"]
    assert rc == 0
    assert _stages(answered)["returned"] == 5
    assert "honest_empty" not in answered


def test_cli_explore_acceptance_five_groups_versus_counts_and_depth_cap(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """R2 §9's acceptance criteria, restated once against the shipped command.

    Deliberately end-to-end and deliberately overlapping the engine pins above:
    §9 states its criteria about `memoria explore`, so the acceptance record is
    only worth what the *command* produces — the read envelope, the exit codes,
    a payload that survives JSON, and the refusal front. The counts below are
    measured, not copied from the plan; see the 2026-08-02 amendment in
    `docs/superpowers/plans/2026-07-17-r2-retrieval-modes.md` task E.3.
    """
    vault = _fixture_vault(tmp_path)
    ordered_a = [
        {"stage": "universe", "count": 8},
        {"stage": "displayable-kind", "count": 6},
        {"stage": "ranked", "count": 3},
        {"stage": "seed", "count": 3},
        {"stage": "neighborhood", "count": 5},
        {"stage": "returned", "count": 5},
    ]

    rc, output = _cli_explore_json(capsys, vault, "spacing")

    assert rc == 0
    assert output["ok"] is True
    assert output["api_version"] == "engine-read-api.v1"
    surfaced = output["explore"]
    for group in ("claims", "questions", "tensions", "works", "hubs"):
        assert surfaced[group], f"empty group: {group}"
    assert surfaced["pipeline_counts"] == ordered_a
    assert surfaced["excluded_strata"] == {"unchecked": 1, "stale": 0, "gated": 0}
    assert surfaced["tensions"][0]["pair"] == [
        "notes/claim-massed.md",
        "notes/claim-spacing.md",
    ]
    thin = next(entry for entry in surfaced["claims"] if entry["id"] == "notes/claim-spacing.md")
    assert thin["grounds_count"] == 0
    assert thin["zero_grounds"] is True
    grounded = next(entry for entry in surfaced["claims"] if entry["id"] == "notes/claim-massed.md")
    assert grounded["grounds_count"] == 1
    assert grounded["zero_grounds"] is False

    rc, output = _cli_explore_json(capsys, vault, "spacing", "--versus", "massed")

    assert rc == 0
    versus = output["explore"]
    assert versus["a"]["pipeline_counts"] == ordered_a
    assert versus["b"]["pipeline_counts"] == [
        {"stage": "universe", "count": 8},
        {"stage": "displayable-kind", "count": 6},
        {"stage": "ranked", "count": 1},
        {"stage": "seed", "count": 1},
        {"stage": "neighborhood", "count": 3},
        {"stage": "returned", "count": 3},
    ]
    assert versus["a"]["excluded_strata"] == {"unchecked": 1, "stale": 0, "gated": 0}
    assert versus["b"]["excluded_strata"] == versus["a"]["excluded_strata"]
    assert versus["intersection"] == {
        "ids": [
            "catalog/sources/settles-2016",
            "notes/claim-massed.md",
            "notes/claim-spacing.md",
        ],
        "count": 3,
        "a_count": 5,
        "b_count": 3,
    }
    assert versus["crossing_tensions"]["count"] == 1
    assert versus["crossing_tensions"]["pairs"][0]["pair"] == [
        "notes/claim-massed.md",
        "notes/claim-spacing.md",
    ]

    # The cap is a refusal, not a clamp: no payload, nonzero exit, and the
    # limit is named where the operator reads errors.
    rc = main(["explore", "spacing", "--depth", "3", "--workspace", str(vault)])
    captured = capsys.readouterr()
    assert rc == 2
    assert captured.out == ""
    assert "hard cap of 2" in captured.err

    rc, refusal = _cli_explore_json(capsys, vault, "spacing", "--depth", "3")
    assert rc == 2
    assert refusal["ok"] is False
    assert "hard cap of 2" in refusal["error"]
