# R2 Retrieval Modes + Fusion + Shapes Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Implement the R2 spec — the graph-SQL filter/expander primitives, filter-before-rank pipeline staging with the ordered honesty counts and the off-by-default rerank seam, the new `memoria explore` Shape-2 surface, the grounded-synthesis contract tests with span-ref resolution, and the frozen-fixture preregistration form for R3 and LOOP.13.

**Architecture:** One primitives module (`runtime/graph_sql.py`, sets + counts, zero rank signal), one pipeline-staging module (`runtime/retrieval_pipeline.py`, ordered `pipeline_counts` + `excluded_strata` + `rerank: off`), one explore engine (`runtime/explore.py`, seed-5 → neighborhood → kind groups with evidence-set grounds marks), and the span-ref/fixture layer (`runtime/span_refs.py` + `tests/retrieval_fixtures.py`). Spec of record: `docs/superpowers/specs/2026-07-17-r2-retrieval-modes-design.md` (main @ `51395f15`).

**Tech Stack:** Python 3 / SQLite (JSON1) / pytest; no new dependencies; no network in tests.

## Global Constraints

- Correctness gate: `python scripts/verify`; PR + `verify`/`gitleaks`; squash merge; explicit-path staging; disposable vaults only.
- BM25 stays the default; the rerank stage ships as an explicit **off** no-op (R3's frozen-fixture spike owns any change — incumbent-until-beaten, verbatim posture).
- Structural output never enters fusion; primitives emit sets + counts, never scores.
- **Sequencing:** section G (and therefore E's expansion) executes after Plan 22 G2S1.1 fills the stubbed `concept_edges` (grep stop-note in the section header); tests are G2S1.1-independent via `state.replace_concept_edges` seeding.
- All line refs verified at origin/main `51395f15`; re-anchor by symbol if drifted.

## Cross-section contracts (BINDING — the manifests' seam resolutions)

1. **Primitives** (G produces): `graph_sql.DEPTH_CAP = 2`; `concept_edge_relations(vault) -> set[str]` (live-CHECK read; subset parity vs packaged schema — the graph plan's widening flows through); `neighborhood(vault, seeds, *, depth=1, relations=None) -> {"ids", "counts"}` (checked edges only; depth 1..2 rejected naming the cap); `co_citation` / `coupling` (over `references` rows); `degree_centrality(vault, ids) -> dict[str,int]` (orderer only); `project_slice(vault, project) -> {"ids", "counts", "source"}` (prefers `state.active_project_slices` via getattr; `links:` closure fallback).
2. **Pipeline staging** (P produces; E consumes): `retrieval_pipeline.PipelineStages` (`add_filter` unique-suffixing repeats, `rows() -> [{stage, count}]` ordered), `excluded_strata(*, unchecked=0, stale=0, gated=0)` (zeros always present), `RERANK_MODE = "off"` rendered in every trace.
3. **Explore** (E produces): `explore.explore_topic(vault, topic, *, project="", depth=1, versus="") -> dict` — kind groups `{claims, questions, tensions, works, hubs}`, per-entry edges + `grounds_count` (complete evidence-set rows via `block_ref`), `SEED_K = 5`, stage order `universe → [project-slice] → ranked → seed → neighborhood → returned`, per-side payloads + intersection + crossing tensions under `--versus`, `honest_empty` string on zero-return; CLI `memoria explore` with the pinned `test_cli_command_surface_is_exact` edit, both-direction help disambiguation vs `memoria project explore`, and the U1 registry row (grep-first both-branch).
4. **Span refs + fixtures** (F produces): `span_refs.resolve_span_ref(vault, ref) -> {work_id, anchor, path} | None` (passages `(work_id, anchor)` match; file-scan interim fallback); `tests/retrieval_fixtures.py` loader (`load_retrieval_fixtures(*, spike_mode=False)` refusing unfrozen rows in spike mode), `shape1_bm25_cases` (gold span refs → doc paths for `evaluate_bm25` — doc-level hit@k stated), `score_present_at_depth(payload, gold_ids) -> bool`, `FIXTURES_DIR = tests/fixtures/retrieval/`, the seeded `cases.yaml` (registered, unfrozen, over O1 seed-corpus work ids).
5. **Execution order:** G → P → E → F (F.1's contract tests touch only shipped ask surfaces and may run any time after P).
6. **TEST_LEVELS:** `test_graph_sql.py`, `test_explore.py`, `test_retrieval_fixtures.py` — `"contract"`; P extends registered files (exact registrations named in-section).

---
# G — graph_sql primitives (spec §2 · slice 1)

Implements the **structural mode primitive set** of `2026-07-17-r2-retrieval-modes-design.md` §2, the first entry of the §10 slice list: one new module, `src/memoria_vault/runtime/graph_sql.py` — deterministic SQL, set-shaped returns, no model judgment. Per the PI ruling in §1, everything here is a **filter + expander, never a ranker**: no function emits a rank signal and nothing here enters fusion. Every set-building primitive returns `{"ids": [...], "counts": {...}}` so denominators are built where sets are built (§4); the primitives return **raw counts dicts** — the ordered `pipeline_counts` list `[{stage, count}, …]` is slice 2's assembly, never emitted here.

**Sequencing stop-note (Plan 22 G2S1.1 — the hard dependency §2 names).** This section executes AFTER Plan 22 G2S1.1 (`2026-07-15-alpha22-substrate-trust.md`) fills the stubbed concept-edge extraction. Grep first:

```bash
grep -n "return \[\]" src/memoria_vault/runtime/indexing.py
```

- If `_concept_edges` still returns `[]` (indexing.py:133-136 at 51395f15): G2S1.1 has not landed, `state.concept_edges` returns no persisted rows, and `neighborhood` ranges over an empty table in every real vault — **stop; this section is out of order.**
- If the stub is replaced: proceed. Either way the tests below stay valid — they seed rows through `state.replace_concept_edges` (state.py:2026), the G2S1.1-independent path, and never depend on extraction.

**Cross-plan order tolerance (binding):** (a) the relation roster is read at runtime from the shipped `concept_edges` CHECK (four relations today, schema.sql:240-250); when the graph plan widens the CHECK to the seven-relation `EDGE_RELATIONS` roster, it flows through with **no code change here** — the parity test asserts subset, not equality. (b) `project_slice` prefers `state.active_project_slices` (ERP-C, graph plan) via `getattr` the moment it exists; until then the fallback is the project file's own `links:` closure (spec §2, Filters bullet).

**Implementation notes verified at 51395f15:**
- `work_graph_edges` CHECK admits `'references', 'related', 'topic', 'keyword', 'authorship', 'institution', 'published_in'` (schema.sql:171-186); `co_citation`/`coupling` operate on `references` rows only, as §2 specifies.
- Dynamic `IN (?…)` placeholder lists are expressed as static SQL via `json_each(?)`: the repo's lint gate keeps bandit S608 enabled (pyproject `[tool.ruff.lint]` — "SQL injection stays enabled") and rejects f-string SQL; JSON1 functions are established runtime precedent (`json_extract` at knowledge.py:3245, operations.py:1076) and the venv SQLite is 3.45.1. All module code below passes `ruff check` and `ruff format --check` under the repo config (verified).
- `neighborhood` traverses **checked edges only**, matching `state.concept_edges`' `checked_only=True` default (state.py:2055) and §4's check-gate-ride-through: an unchecked or quarantined edge never expands the candidate set (it surfaces later as a stratum count in slice 2).
- `state.replace_concept_edges` normalizes endpoints via `normalize_path` and validates relations through `_concept_edge_relation` (state.py:3420-3424 — hardcodes the four today; the graph plan widens it together with the CHECK).
- `concept_status` is a view over `concepts` LEFT JOIN `concept_verdicts` (schema.sql:72-79): an id absent from the concept mirror reads as `unchecked` — `filter_ids` relies on exactly that.

### Task G.1 — the four order-tolerant relation primitives

**Files:**
- `src/memoria_vault/runtime/graph_sql.py` (new)
- `tests/test_graph_sql.py` (new)
- `tests/conftest.py` (TEST_LEVELS registration — `test_testing_levels.py:10-14` pins exact-match, so it lands in the same commit)

**Interfaces:**
- `concept_edge_relations(vault: Path) -> set[str]` — roster read from the live table's CHECK via `sqlite_master`
- `neighborhood(vault: Path, seeds: list[str], *, depth: int = 1, relations: set[str] | None = None) -> dict[str, Any]` — `{"ids": list[str], "counts": {"seeds": int, "neighbors": int, "returned": int}}`; recursive CTE over `concept_edges`; depth validated 1..2 (`DEPTH_CAP = 2`), rejection names the cap
- `co_citation(vault: Path, work_id: str) -> dict[str, Any]` — `{"work_ids": list[str], "counts": {"citing_works": int, "co_cited": int}}`
- `coupling(vault: Path, work_id: str) -> dict[str, Any]` — `{"work_ids": list[str], "counts": {"references": int, "coupled": int}}`
- `degree_centrality(vault: Path, ids: list[str]) -> dict[str, int]` — orderer only, per the spec's own signature (the one non-counts return in §2)

- [ ] **G.1.1 — failing test.** Create `tests/test_graph_sql.py`:

```python
"""Contract tests for the deterministic graph-SQL primitives (R2 design §2, slice 1)."""

from __future__ import annotations

import re
from importlib.resources import files
from pathlib import Path

from memoria_vault.runtime import graph_sql, state

SHIPPED_RELATIONS = {"supports", "contradicts", "extends", "tension"}


def _seed_concept_edges(vault: Path) -> None:
    state.replace_concept_edges(
        vault,
        [
            {
                "source_concept_id": "notes/a.md",
                "relation_type": "supports",
                "target_concept_id": "notes/b.md",
                "check_status": "checked",
            },
            {
                "source_concept_id": "notes/b.md",
                "relation_type": "extends",
                "target_concept_id": "notes/c.md",
                "check_status": "checked",
            },
            {
                "source_concept_id": "notes/c.md",
                "relation_type": "tension",
                "target_concept_id": "notes/d.md",
                "check_status": "checked",
            },
            {
                "source_concept_id": "notes/a.md",
                "relation_type": "contradicts",
                "target_concept_id": "notes/x.md",
                "check_status": "unchecked",
            },
        ],
    )


def test_concept_edge_relations_matches_packaged_schema(tmp_path: Path) -> None:
    roster = graph_sql.concept_edge_relations(tmp_path)

    schema_text = files("memoria_vault.runtime").joinpath("schema.sql").read_text(encoding="utf-8")
    block = schema_text.split("CREATE TABLE IF NOT EXISTS concept_edges", 1)[1]
    match = re.search(r"relation_type\s+IN\s*\(([^)]*)\)", block)
    assert match is not None
    packaged = {value.strip().strip("'\"") for value in match.group(1).split(",") if value.strip()}

    # Parity: the live-DB read and the packaged schema.sql agree on a fresh vault.
    assert roster == packaged
    # Order-tolerant floor: the graph plan may widen the roster to seven, never shrink it.
    assert SHIPPED_RELATIONS <= roster


def test_neighborhood_rejects_depth_beyond_cap(tmp_path: Path) -> None:
    for depth in (0, 3):
        try:
            graph_sql.neighborhood(tmp_path, ["notes/a.md"], depth=depth)
        except ValueError as exc:
            assert "hard cap 2" in str(exc)
        else:
            raise AssertionError(f"depth {depth} must be rejected naming the cap")


def test_neighborhood_rejects_unknown_relations(tmp_path: Path) -> None:
    try:
        graph_sql.neighborhood(tmp_path, ["notes/a.md"], relations={"refutes"})
    except ValueError as exc:
        assert "unknown concept edge relations" in str(exc)
    else:
        raise AssertionError("an unadmitted relation must be rejected")


def test_neighborhood_depth_one_walks_checked_edges_undirected(tmp_path: Path) -> None:
    _seed_concept_edges(tmp_path)

    forward = graph_sql.neighborhood(tmp_path, ["notes/a.md"], depth=1)
    assert forward["ids"] == ["notes/a.md", "notes/b.md"]
    assert forward["counts"] == {"seeds": 1, "neighbors": 1, "returned": 2}

    # The unchecked contradicts edge to notes/x.md never rides through.
    assert "notes/x.md" not in forward["ids"]

    # supports is walked from either endpoint: b reaches a (reverse) and c (forward).
    reverse = graph_sql.neighborhood(tmp_path, ["notes/b.md"], depth=1)
    assert reverse["ids"] == ["notes/a.md", "notes/b.md", "notes/c.md"]


def test_neighborhood_depth_two_reaches_two_hops(tmp_path: Path) -> None:
    _seed_concept_edges(tmp_path)

    result = graph_sql.neighborhood(tmp_path, ["notes/a.md"], depth=2)

    assert result["ids"] == ["notes/a.md", "notes/b.md", "notes/c.md"]
    assert result["counts"] == {"seeds": 1, "neighbors": 2, "returned": 3}


def test_neighborhood_relations_filter_restricts_expansion(tmp_path: Path) -> None:
    _seed_concept_edges(tmp_path)

    tension_only = graph_sql.neighborhood(tmp_path, ["notes/c.md"], depth=1, relations={"tension"})

    assert tension_only["ids"] == ["notes/c.md", "notes/d.md"]
    assert tension_only["counts"] == {"seeds": 1, "neighbors": 1, "returned": 2}


def test_neighborhood_empty_seeds_returns_empty_with_counts(tmp_path: Path) -> None:
    result = graph_sql.neighborhood(tmp_path, [])

    assert result == {"ids": [], "counts": {"seeds": 0, "neighbors": 0, "returned": 0}}


def _seed_work_graph(vault: Path) -> None:
    state.replace_work_graph_edges(
        vault,
        "alpha",
        [
            {"relation_type": "references", "target_id": "W:t1"},
            {"relation_type": "references", "target_id": "W:t2"},
            {"relation_type": "topic", "target_id": "memory"},
        ],
    )
    state.replace_work_graph_edges(
        vault,
        "beta",
        [
            {"relation_type": "references", "target_id": "W:t1"},
            {"relation_type": "references", "target_id": "W:t2"},
            {"relation_type": "references", "target_id": "W:t3"},
        ],
    )
    state.replace_work_graph_edges(
        vault,
        "gamma",
        [{"relation_type": "references", "target_id": "W:t3"}],
    )


def test_co_citation_orders_by_shared_citing_works(tmp_path: Path) -> None:
    _seed_work_graph(tmp_path)

    result = graph_sql.co_citation(tmp_path, "W:t1")

    # W:t2 is cited alongside W:t1 by alpha and beta; W:t3 only by beta.
    assert result["work_ids"] == ["W:t2", "W:t3"]
    assert result["counts"] == {"citing_works": 2, "co_cited": 2}


def test_coupling_orders_by_shared_references(tmp_path: Path) -> None:
    _seed_work_graph(tmp_path)

    result = graph_sql.coupling(tmp_path, "alpha")
    assert result["work_ids"] == ["beta"]
    assert result["counts"] == {"references": 2, "coupled": 1}

    # beta couples with alpha (t1, t2) and gamma (t3); the topic row never counts.
    both = graph_sql.coupling(tmp_path, "beta")
    assert both["work_ids"] == ["alpha", "gamma"]
    assert both["counts"] == {"references": 3, "coupled": 2}


def test_degree_centrality_returns_zero_for_isolated_ids(tmp_path: Path) -> None:
    _seed_concept_edges(tmp_path)

    degrees = graph_sql.degree_centrality(tmp_path, ["notes/a.md", "notes/b.md", "notes/zzz.md"])

    # Checked edges only: a-b (supports); b also touches c (extends).
    assert degrees == {"notes/a.md": 1, "notes/b.md": 2, "notes/zzz.md": 0}
    assert graph_sql.degree_centrality(tmp_path, []) == {}
```

  Register the file in `tests/conftest.py` `TEST_LEVELS` (exact-match enforced by `test_testing_levels.py`). Edit — old:

```python
    "test_gate_calibration.py": "unit",
```

  new:

```python
    "test_gate_calibration.py": "unit",
    "test_graph_sql.py": "contract",
```

- [ ] **G.1.2 — run, expect the red import failure:**

```bash
python -m pytest tests/test_graph_sql.py -q
```

  Expected failure (collection error, verified wording):

```
E   ImportError: cannot import name 'graph_sql' from 'memoria_vault.runtime' (src/memoria_vault/runtime/__init__.py)
```

- [ ] **G.1.3 — minimal implementation.** Create `src/memoria_vault/runtime/graph_sql.py`:

```python
"""Deterministic graph-SQL primitives for structural retrieval (R2 design, section 2).

Set-shaped returns, no model judgment: every set-building primitive returns
``{"ids": [...], "counts": {...}}`` so denominators are built where sets are
built (design section 4). Structural output is a filter + expander, never a
ranker — nothing here emits a rank signal or enters fusion.

Production stop-note (hard dependency, named in the design): the shipped
concept-edge extraction is a stub returning ``[]`` (``indexing._concept_edges``),
so ``neighborhood`` ranges over an empty ``concept_edges`` table in real vaults
until Plan 22 G2S1.1 fill-and-persist lands. Tests seed rows through
``state.replace_concept_edges`` — the G2S1.1-independent path.
"""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

from memoria_vault.runtime import state
from memoria_vault.runtime.policy.paths import normalize_path

DEPTH_CAP = 2

_RELATION_CHECK_RE = re.compile(r"relation_type\s+IN\s*\(([^)]*)\)", re.IGNORECASE)


def concept_edge_relations(vault: Path) -> set[str]:
    """Relation types the vault's ``concept_edges`` CHECK admits.

    Read from the live table SQL (``sqlite_master``), so the graph plan's
    widening to the full ``EDGE_RELATIONS`` roster flows through with no
    change here — order-tolerant; four relations ship today.
    """
    with state.connect(vault) as conn:
        row = conn.execute(
            "SELECT sql FROM sqlite_master WHERE type = 'table' AND name = 'concept_edges'"
        ).fetchone()
    match = _RELATION_CHECK_RE.search(str(row["sql"])) if row is not None else None
    if match is None:
        raise ValueError("concept_edges relation CHECK not found")
    return {value.strip().strip("'\"") for value in match.group(1).split(",") if value.strip()}


def neighborhood(
    vault: Path,
    seeds: list[str],
    *,
    depth: int = 1,
    relations: set[str] | None = None,
) -> dict[str, Any]:
    """Seed ids plus everything within ``depth`` hops over checked concept edges.

    Filter + expander with zero rank signal; edges are walked undirected so a
    ``supports`` neighbor surfaces from either endpoint. ``relations`` defaults
    to every type the shipped CHECK admits — tension edges included, tensions
    stay first-class retrievable.
    """
    if not 1 <= depth <= DEPTH_CAP:
        raise ValueError(
            f"depth must be between 1 and {DEPTH_CAP} (hard cap {DEPTH_CAP}), got {depth}"
        )
    admitted = concept_edge_relations(vault)
    chosen = admitted if relations is None else set(relations)
    unknown = chosen - admitted
    if unknown:
        raise ValueError(f"unknown concept edge relations: {sorted(unknown)}")
    seed_ids = sorted({normalize_path(str(seed)) for seed in seeds if str(seed).strip()})
    if not seed_ids:
        return {"ids": [], "counts": {"seeds": 0, "neighbors": 0, "returned": 0}}
    relations_json = json.dumps(sorted(chosen))
    seeds_json = json.dumps(seed_ids)
    with state.connect(vault) as conn:
        rows = conn.execute(
            """
            WITH RECURSIVE
            edges(source_id, target_id) AS (
                SELECT source_concept_id, target_concept_id
                FROM concept_edges
                WHERE check_status = 'checked'
                  AND relation_type IN (SELECT value FROM json_each(?))
                UNION
                SELECT target_concept_id, source_concept_id
                FROM concept_edges
                WHERE check_status = 'checked'
                  AND relation_type IN (SELECT value FROM json_each(?))
            ),
            walk(concept_id, hops) AS (
                SELECT value, 0 FROM json_each(?)
                UNION
                SELECT edges.target_id, walk.hops + 1
                FROM edges
                JOIN walk ON walk.concept_id = edges.source_id
                WHERE walk.hops < ?
            )
            SELECT DISTINCT concept_id FROM walk ORDER BY concept_id
            """,
            (relations_json, relations_json, seeds_json, depth),
        ).fetchall()
    ids = [str(row["concept_id"]) for row in rows]
    return {
        "ids": ids,
        "counts": {
            "seeds": len(seed_ids),
            "neighbors": len(ids) - len(seed_ids),
            "returned": len(ids),
        },
    }


def co_citation(vault: Path, work_id: str) -> dict[str, Any]:
    """Works cited together with ``work_id`` by the vault's citing works.

    Standard bibliometric co-citation over ``work_graph_edges`` ``references``
    rows: every target sharing at least one citing work with ``work_id``,
    ordered by shared citing works (desc), then id.
    """
    target = str(work_id).strip()
    with state.connect(vault) as conn:
        citing = conn.execute(
            """
            SELECT COUNT(DISTINCT work_id) AS n
            FROM work_graph_edges
            WHERE relation_type = 'references' AND target_id = ?
            """,
            (target,),
        ).fetchone()
        rows = conn.execute(
            """
            SELECT other.target_id AS co_cited_id,
                   COUNT(DISTINCT other.work_id) AS shared
            FROM work_graph_edges AS anchor
            JOIN work_graph_edges AS other
              ON other.work_id = anchor.work_id
             AND other.relation_type = 'references'
             AND other.target_id <> anchor.target_id
            WHERE anchor.relation_type = 'references' AND anchor.target_id = ?
            GROUP BY other.target_id
            ORDER BY shared DESC, other.target_id
            """,
            (target,),
        ).fetchall()
    work_ids = [str(row["co_cited_id"]) for row in rows]
    return {
        "work_ids": work_ids,
        "counts": {"citing_works": int(citing["n"]), "co_cited": len(work_ids)},
    }


def coupling(vault: Path, work_id: str) -> dict[str, Any]:
    """Vault works bibliographically coupled to ``work_id``.

    Standard coupling over ``references`` rows: every other citing work that
    shares at least one reference with ``work_id``, ordered by shared
    references (desc), then id.
    """
    source = str(work_id).strip()
    with state.connect(vault) as conn:
        references = conn.execute(
            """
            SELECT COUNT(DISTINCT target_id) AS n
            FROM work_graph_edges
            WHERE relation_type = 'references' AND work_id = ?
            """,
            (source,),
        ).fetchone()
        rows = conn.execute(
            """
            SELECT other.work_id AS coupled_id,
                   COUNT(DISTINCT other.target_id) AS shared
            FROM work_graph_edges AS anchor
            JOIN work_graph_edges AS other
              ON other.target_id = anchor.target_id
             AND other.relation_type = 'references'
             AND other.work_id <> anchor.work_id
            WHERE anchor.relation_type = 'references' AND anchor.work_id = ?
            GROUP BY other.work_id
            ORDER BY shared DESC, other.work_id
            """,
            (source,),
        ).fetchall()
    work_ids = [str(row["coupled_id"]) for row in rows]
    return {
        "work_ids": work_ids,
        "counts": {"references": int(references["n"]), "coupled": len(work_ids)},
    }


def degree_centrality(vault: Path, ids: list[str]) -> dict[str, int]:
    """Distinct-neighbor degree per id over checked concept edges.

    An orderer within expansion only — which neighbors surface first when a
    cap applies. Never a relevance score and never fused (design section 2).
    """
    wanted = list(dict.fromkeys(normalize_path(str(v)) for v in ids if str(v).strip()))
    if not wanted:
        return {}
    with state.connect(vault) as conn:
        rows = conn.execute(
            """
            SELECT concept_id, COUNT(*) AS degree FROM (
                SELECT source_concept_id AS concept_id, target_concept_id AS neighbor
                FROM concept_edges WHERE check_status = 'checked'
                UNION
                SELECT target_concept_id AS concept_id, source_concept_id AS neighbor
                FROM concept_edges WHERE check_status = 'checked'
            )
            WHERE concept_id IN (SELECT value FROM json_each(?))
            GROUP BY concept_id
            """,
            (json.dumps(wanted),),
        ).fetchall()
    degrees = dict.fromkeys(wanted, 0)
    degrees.update({str(row["concept_id"]): int(row["degree"]) for row in rows})
    return degrees
```

- [ ] **G.1.4 — run to green** (the second file confirms TEST_LEVELS exact-match):

```bash
python -m pytest tests/test_graph_sql.py tests/test_testing_levels.py -q
```

  Expected: `12 passed` (10 new + 2 level-gate tests).

- [ ] **G.1.5 — commit (explicit paths, never `git add -A`):**

```bash
git add src/memoria_vault/runtime/graph_sql.py tests/test_graph_sql.py tests/conftest.py
git commit -m "feat(retrieval): add graph-SQL structural primitives (R2 slice 1, G.1)

Co-Authored-By: Claude Fable 5 <noreply@anthropic.com>"
```

### Task G.2 — project_slice + type/status filters composing with neighborhood

**Files:**
- `src/memoria_vault/runtime/graph_sql.py` (extend)
- `tests/test_graph_sql.py` (extend)

**Interfaces:**
- `project_slice(vault: Path, project: str) -> dict[str, Any]` — `{"ids": list[str], "counts": {"members": int}, "source": "active-project-slices" | "links-closure"}`; order-tolerant source per spec §2: `getattr(state, "active_project_slices", None)` wins the moment ERP-C lands it; fallback is the project file's `links:` closure (project path resolution mirrors `knowledge._project_rel`, knowledge.py:3074-3084; link-target semantics mirror `knowledge._link_target`, knowledge.py:3036-3047)
- `filter_ids(vault: Path, ids: list[str], *, types: set[str] | None = None, check_status: set[str] | None = None) -> dict[str, Any]` — `{"ids": list[str], "counts": {"before": int, "after": int}}` over the `concept_status` view (schema.sql:72-79)
- Composition is caller-side set intersection — slice 2 (pipeline assembly) owns stitching the per-stage counts into the ordered `pipeline_counts` list.

- [ ] **G.2.1 — failing tests.** Append to `tests/test_graph_sql.py`:

```python
def _seed_project_files(vault: Path) -> None:
    (vault / "projects").mkdir(exist_ok=True)
    (vault / "notes").mkdir(exist_ok=True)
    (vault / "projects/p1.md").write_text(
        "---\ntype: project\nlinks:\n  supports:\n    - notes/a.md\n---\nbody\n",
        encoding="utf-8",
    )
    (vault / "notes/a.md").write_text(
        "---\ntype: note\nlinks:\n  extends:\n    - '[[b]]'\n---\nalpha\n", encoding="utf-8"
    )
    (vault / "notes/b.md").write_text("---\ntype: note\n---\nbeta\n", encoding="utf-8")
    (vault / "notes/orphan.md").write_text("---\ntype: note\n---\norphan\n", encoding="utf-8")


def test_project_slice_falls_back_to_links_closure(tmp_path: Path) -> None:
    _seed_project_files(tmp_path)

    result = graph_sql.project_slice(tmp_path, "p1")

    # The project's own links: closure — wikilink [[b]] resolves to notes/b.md;
    # the unlinked orphan note stays outside the slice.
    assert result["ids"] == ["notes/a.md", "notes/b.md"]
    assert result["counts"] == {"members": 2}
    assert result["source"] == "links-closure"


def test_project_slice_prefers_active_project_slices_seam(tmp_path: Path) -> None:
    # Order-tolerant seam (spec §2): once the graph plan lands ERP-C's
    # state.active_project_slices, it wins over the links closure with no
    # change to graph_sql.
    state.active_project_slices = lambda vault, project: ["notes/z.md"]  # type: ignore[attr-defined]
    try:
        result = graph_sql.project_slice(tmp_path, "p1")
    finally:
        del state.active_project_slices  # type: ignore[attr-defined]

    assert result["ids"] == ["notes/z.md"]
    assert result["counts"] == {"members": 1}
    assert result["source"] == "active-project-slices"


def test_filter_ids_prunes_by_type_and_check_status(tmp_path: Path) -> None:
    state.rebuild_file_concept_mirror(
        tmp_path,
        [
            {"concept_id": "notes/a.md", "concept_type": "note"},
            {"concept_id": "notes/b.md", "concept_type": "note"},
            {"concept_id": "digests/d.md", "concept_type": "digest"},
        ],
    )
    state.set_concept_verdict(tmp_path, "notes/a.md", "checked")

    typed = graph_sql.filter_ids(
        tmp_path, ["notes/a.md", "notes/b.md", "digests/d.md"], types={"note"}
    )
    assert typed["ids"] == ["notes/a.md", "notes/b.md"]
    assert typed["counts"] == {"before": 3, "after": 2}

    checked = graph_sql.filter_ids(
        tmp_path, ["notes/a.md", "notes/b.md", "notes/ghost.md"], check_status={"checked"}
    )
    # notes/ghost.md is absent from the concept mirror: it counts as unchecked
    # and never rides through a checked filter.
    assert checked["ids"] == ["notes/a.md"]
    assert checked["counts"] == {"before": 3, "after": 1}

    assert graph_sql.filter_ids(tmp_path, []) == {"ids": [], "counts": {"before": 0, "after": 0}}


def test_primitives_compose_neighborhood_slice_filter(tmp_path: Path) -> None:
    _seed_concept_edges(tmp_path)
    _seed_project_files(tmp_path)
    state.rebuild_file_concept_mirror(
        tmp_path,
        [
            {"concept_id": "notes/a.md", "concept_type": "note"},
            {"concept_id": "notes/b.md", "concept_type": "note"},
            {"concept_id": "notes/c.md", "concept_type": "note"},
        ],
    )
    state.set_concept_verdict(tmp_path, "notes/a.md", "checked")

    # Shape-2 spine: expand -> slice -> status filter, counts carried per stage.
    hood = graph_sql.neighborhood(tmp_path, ["notes/a.md"], depth=2)
    sliced = sorted(set(hood["ids"]) & set(graph_sql.project_slice(tmp_path, "p1")["ids"]))
    final = graph_sql.filter_ids(tmp_path, sliced, check_status={"checked"})

    assert hood["counts"]["returned"] == 3
    assert sliced == ["notes/a.md", "notes/b.md"]
    assert final["ids"] == ["notes/a.md"]
    assert final["counts"] == {"before": 2, "after": 1}
```

- [ ] **G.2.2 — run, expect the red attribute failures:**

```bash
python -m pytest tests/test_graph_sql.py -q
```

  Expected: `4 failed, 10 passed`, each failure (verified wording):

```
E       AttributeError: module 'memoria_vault.runtime.graph_sql' has no attribute 'project_slice'
E       AttributeError: module 'memoria_vault.runtime.graph_sql' has no attribute 'filter_ids'
```

- [ ] **G.2.3 — minimal implementation.** In `src/memoria_vault/runtime/graph_sql.py`, extend the import block — old:

```python
from memoria_vault.runtime import state
from memoria_vault.runtime.policy.paths import normalize_path
```

  new:

```python
from memoria_vault.runtime import state
from memoria_vault.runtime.policy.paths import normalize_path
from memoria_vault.runtime.vaultio import read_frontmatter
```

  Then append at the end of the module:

```python
def project_slice(vault: Path, project: str) -> dict[str, Any]:
    """Concept ids in one project's slice (filter, zero rank signal).

    The source is order-tolerant (design section 2): once the graph plan lands
    ERP-C's ``state.active_project_slices`` it wins with no change here; until
    then the fallback is the project file's own ``links:`` closure.
    """
    slices = getattr(state, "active_project_slices", None)
    if callable(slices):
        ids = sorted({_member_id(row) for row in slices(vault, project)} - {""})
        return {"ids": ids, "counts": {"members": len(ids)}, "source": "active-project-slices"}
    ids = _links_closure(Path(vault), _project_rel(Path(vault), project))
    return {"ids": ids, "counts": {"members": len(ids)}, "source": "links-closure"}


def _member_id(row: Any) -> str:
    if isinstance(row, dict):
        row = row.get("concept_id") or row.get("path") or row.get("id") or ""
    value = str(row).strip()
    return normalize_path(value) if value else ""


def _project_rel(vault: Path, project: str) -> str:
    rel = normalize_path(str(project))
    if "/" not in rel:
        nested = f"projects/{rel}/project.md"
        return nested if (vault / nested).is_file() else f"projects/{rel}.md"
    if not rel.endswith(".md"):
        rel += ".md"
    if not rel.startswith("projects/"):
        raise ValueError(f"project must live under projects: {rel}")
    return rel


def _links_closure(vault: Path, project_rel: str) -> list[str]:
    frontmatter = read_frontmatter(vault / project_rel)
    seeds = _link_targets(frontmatter)
    thesis = _link_target(frontmatter.get("thesis"))
    if thesis:
        seeds.add(thesis)
    seen: set[str] = set()
    queue = sorted(seeds)
    while queue:
        rel = queue.pop(0)
        if rel in seen:
            continue
        seen.add(rel)
        path = vault / rel
        if not path.is_file():
            continue
        queue.extend(sorted(_link_targets(read_frontmatter(path)) - seen))
    return sorted(seen)


def _link_targets(frontmatter: dict[str, Any]) -> set[str]:
    links = frontmatter.get("links")
    if not isinstance(links, dict):
        return set()
    targets: set[str] = set()
    for values in links.values():
        for value in values if isinstance(values, list) else [values]:
            target = _link_target(value)
            if target:
                targets.add(target)
    return targets


def _link_target(value: Any) -> str:
    if isinstance(value, dict):
        value = value.get("target") or value.get("path") or value.get("id") or value.get("note")
    if not isinstance(value, str) or not value.strip():
        return ""
    raw = value.strip()
    if raw.startswith("[[") and raw.endswith("]]"):
        raw = raw[2:-2].split("|", 1)[0].split("#", 1)[0].strip()
    if not raw:
        return ""
    rel = normalize_path(raw)
    if "/" not in rel:
        rel = f"notes/{rel}"
    if not rel.startswith("catalog/sources/") and not rel.endswith(".md"):
        rel += ".md"
    return rel


def filter_ids(
    vault: Path,
    ids: list[str],
    *,
    types: set[str] | None = None,
    check_status: set[str] | None = None,
) -> dict[str, Any]:
    """Prune an id set by concept type and/or check status (``concept_status`` view).

    Ids absent from the concept mirror count as type ``""`` and status
    ``unchecked`` — an unregistered concept never rides through a checked
    filter.
    """
    wanted = list(dict.fromkeys(normalize_path(str(v)) for v in ids if str(v).strip()))
    if not wanted:
        return {"ids": [], "counts": {"before": 0, "after": 0}}
    if types is None and check_status is None:
        return {"ids": wanted, "counts": {"before": len(wanted), "after": len(wanted)}}
    with state.connect(vault) as conn:
        rows = conn.execute(
            """
            SELECT concept_id, concept_type, check_status
            FROM concept_status
            WHERE concept_id IN (SELECT value FROM json_each(?))
            """,
            (json.dumps(wanted),),
        ).fetchall()
    known = {
        str(row["concept_id"]): (str(row["concept_type"]), str(row["check_status"])) for row in rows
    }
    kept = []
    for concept_id in wanted:
        concept_type, status = known.get(concept_id, ("", "unchecked"))
        if types is not None and concept_type not in types:
            continue
        if check_status is not None and status not in check_status:
            continue
        kept.append(concept_id)
    return {"ids": kept, "counts": {"before": len(wanted), "after": len(kept)}}
```

- [ ] **G.2.4 — run to green:**

```bash
python -m pytest tests/test_graph_sql.py -q
```

  Expected: `14 passed` (verified against the shipped `state`/schema at 51395f15).

- [ ] **G.2.5 — section-final gate:**

```bash
python scripts/verify
```

  Expected: green (lint, product gates, tests, offline smoke, syntax). The module and test file as written pass `ruff check` and `ruff format --check` under the repo config — verified at both the G.1 and G.2 stage boundaries.

- [ ] **G.2.6 — commit (explicit paths):**

```bash
git add src/memoria_vault/runtime/graph_sql.py tests/test_graph_sql.py
git commit -m "feat(retrieval): add project-slice + type/status filters to graph_sql (G.2)

Co-Authored-By: Claude Fable 5 <noreply@anthropic.com>"
```
# P — Pipeline staging, honesty contract, trace

This section implements spec §1 (fixed stage order: filter-before-rank, fusion for ranked legs only, the explicit no-op rerank seam), §4 (the search-honesty denominator contract: ordered `pipeline_counts`, `excluded_strata` with always-present zeros, honest-empty, check-gate-ride-through), and §6 (the deterministic `ask-retrieval-trace`) of `docs/superpowers/specs/2026-07-17-r2-retrieval-modes-design.md` — i.e. implementation slices 2, 4, and 6 (spec §10).

**Sequencing and stop-notes.** P has **no** dependency on Plan 22 G2S1.1: nothing here touches `concept_edges` (that stop-note binds the graph_sql section only). P can start directly at `51395f15`. Section E (`memoria explore`) consumes the seams produced here (`PipelineStages`, `excluded_strata`, `rerank`, `honest_empty`, `build_trace`, and the `--trace` contract), so P merges before E's payload work. All line references below were verified at `51395f15`; if a file has drifted, re-anchor by symbol name, not line number.

**Module-location decision (required by the task): new file `src/memoria_vault/runtime/retrieval_pipeline.py`, not an extension of `search_index.py`.** Evidence: `wc -l` at `51395f15` gives `search_index.py` 606 lines (owns BM25, doc assembly, project-context expansion) and `retrieval.py` 184 lines (owns substrate capability checks and the fts/vector/hybrid legs). The staging contract is consumed by two fronts — ask (`search_index.answer_query`, `search_index.py:153`) and explore (section E's new module). Housing it in `search_index.py` would force explore to import a 600+-line module (plus `yaml`, `state`, `indexing`) for pure accounting; housing it in `retrieval.py` would conflate substrate legs with the honesty contract. The new module is pure stdlib (`collections.Counter`, `typing.Any`), so no import cycle is possible: `search_index` → `retrieval_pipeline` only.

**One resolved wording rule:** the honest-empty sentence is spec-verbatim plural (`"0 of 1 candidates matched; 1 unchecked documents were not searched"`) — deterministic, no smart pluralization. The trace carries no invented explanation: it is the §4 counts plus BM25 scores plus `rerank: off`, exactly (spec §6 closing line).

---

### Task P.1 — Shared retrieval-pipeline module: ordered counts, strata, no-op rerank, trace builder

**Files:**
- `src/memoria_vault/runtime/retrieval_pipeline.py` (new)
- `tests/test_retrieval_pipeline.py` (new)
- `tests/conftest.py` (register the new test file in `TEST_LEVELS`)

**Interfaces:**
- `RERANK_MODE: str = "off"` — the §1 stage-4 config, off by default, R3-owned.
- `class PipelineStages` — `__init__(self, universe: int)`, `add_filter(self, name: str, count: int) -> None` (unique-suffixes repeats: `type-filter`, `type-filter#2`), `add_ranked(self, count: int) -> None`, `add_returned(self, count: int) -> None`, `rows(self) -> list[dict[str, Any]]` (the ordered `pipeline_counts` list; refuses incomplete pipelines).
- `excluded_strata(*, unchecked: int = 0, stale: int = 0, gated: int = 0) -> dict[str, int]` — zeros always present.
- `candidate_count(pipeline_counts: list[dict[str, Any]]) -> int` — the §4 denominator (count entering `ranked`).
- `honest_empty(pipeline_counts: list[dict[str, Any]], strata: dict[str, int]) -> str` — the §4 sentence.
- `rerank(hits: list[Any]) -> list[Any]` — the explicit no-op stage.
- `build_trace(pipeline_counts: list[dict[str, Any]], returned: list[tuple[str, float]], *, fusion_inputs: list[dict[str, Any]] | None = None) -> dict[str, Any]` — the §6 trace; `fusion_inputs` emitted only when more than one ranked leg exists.

**Steps:**

- [ ] Register the new test file in `tests/conftest.py` (level `unit` — the module is pure, no vault, no network). Edit (`old_string` → `new_string`):

  ```python
      "test_retrieval_substrate.py": "contract",
  ```
  →
  ```python
      "test_retrieval_pipeline.py": "unit",
      "test_retrieval_substrate.py": "contract",
  ```

- [ ] Write the failing test — full content of `tests/test_retrieval_pipeline.py` (pytest-independent try/except/else style for refusals, matching the suite's CheckHarness convention noted in `pyproject.toml`'s ruff `ignore` comments):

  ```python
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

      trace = pipeline.build_trace(
          stages.rows(), [("notes/a.md", 1.5), ("notes/b.md", 0.5)]
      )

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
  ```

- [ ] Run `python -m pytest tests/test_retrieval_pipeline.py -q` — expected failure: collection error, `ModuleNotFoundError: No module named 'memoria_vault.runtime.retrieval_pipeline'`.

- [ ] Minimal implementation — full content of `src/memoria_vault/runtime/retrieval_pipeline.py`:

  ```python
  """Shared retrieval-pipeline staging (R2 design spec sections 1, 4, 6).

  Stage accounting for every retrieval read: the ordered ``pipeline_counts``
  list (universe -> named filters -> ranked -> returned), the named excluded
  strata with always-present zeros, the explicit no-op rerank seam, and the
  deterministic trace. Pure stdlib so both ask (``search_index``) and
  ``memoria explore`` consume it without dragging in vault I/O.
  """

  from __future__ import annotations

  from collections import Counter
  from typing import Any

  RERANK_MODE = "off"

  _RESERVED_STAGES = frozenset({"universe", "ranked", "returned"})


  class PipelineStages:
      """Ordered stage accounting: universe -> filters -> ranked -> returned."""

      def __init__(self, universe: int) -> None:
          self._rows: list[dict[str, Any]] = [{"stage": "universe", "count": int(universe)}]
          self._filters: Counter[str] = Counter()
          self._ranked = False
          self._returned = False

      def add_filter(self, name: str, count: int) -> None:
          if self._ranked:
              raise ValueError("filters must precede the ranked stage")
          clean = name.strip()
          if not clean or clean in _RESERVED_STAGES:
              raise ValueError(f"invalid filter stage name: {name!r}")
          self._filters[clean] += 1
          occurrence = self._filters[clean]
          stage = clean if occurrence == 1 else f"{clean}#{occurrence}"
          self._rows.append({"stage": stage, "count": int(count)})

      def add_ranked(self, count: int) -> None:
          if self._ranked:
              raise ValueError("ranked stage recorded twice")
          self._ranked = True
          self._rows.append({"stage": "ranked", "count": int(count)})

      def add_returned(self, count: int) -> None:
          if not self._ranked:
              raise ValueError("returned stage requires a ranked stage first")
          if self._returned:
              raise ValueError("returned stage recorded twice")
          self._returned = True
          self._rows.append({"stage": "returned", "count": int(count)})

      def rows(self) -> list[dict[str, Any]]:
          if not self._returned:
              raise ValueError("pipeline_counts requires ranked and returned stages")
          return [dict(row) for row in self._rows]


  def excluded_strata(*, unchecked: int = 0, stale: int = 0, gated: int = 0) -> dict[str, int]:
      """Named strata with counts; zeros always present (spec section 4)."""
      return {"unchecked": int(unchecked), "stale": int(stale), "gated": int(gated)}


  def candidate_count(pipeline_counts: list[dict[str, Any]]) -> int:
      """The denominator: the candidate count entering the ranked stage."""
      previous: int | None = None
      for row in pipeline_counts:
          if row["stage"] == "ranked":
              if previous is None:
                  raise ValueError("ranked stage has no preceding candidate stage")
              return previous
          previous = int(row["count"])
      raise ValueError("pipeline_counts has no ranked stage")


  def honest_empty(pipeline_counts: list[dict[str, Any]], strata: dict[str, int]) -> str:
      """The honest-empty sentence — counts, never a bare empty list."""
      unchecked = int(strata.get("unchecked", 0))
      return (
          f"0 of {candidate_count(pipeline_counts)} candidates matched; "
          f"{unchecked} unchecked documents were not searched"
      )


  def rerank(hits: list[Any]) -> list[Any]:
      """The explicit no-op reranking seam (spec section 1, stage 4).

      Off by default, fixture-gated: R3 decides none / LLM-listwise /
      cross-encoder over the frozen gold set. The stage exists so the trace
      can honestly say ``rerank: off``.
      """
      if RERANK_MODE != "off":
          raise NotImplementedError(f"rerank mode {RERANK_MODE!r} has no shipped implementation")
      return list(hits)


  def build_trace(
      pipeline_counts: list[dict[str, Any]],
      returned: list[tuple[str, float]],
      *,
      fusion_inputs: list[dict[str, Any]] | None = None,
  ) -> dict[str, Any]:
      """The retrieval trace: counts plus scores, never an invented explanation."""
      trace: dict[str, Any] = {
          "pipeline_counts": [dict(row) for row in pipeline_counts],
          "scores": [{"path": path, "score": score} for path, score in returned],
          "rerank": RERANK_MODE,
      }
      if fusion_inputs and len(fusion_inputs) > 1:
          trace["fusion_inputs"] = [dict(leg) for leg in fusion_inputs]
      return trace
  ```

- [ ] Run `python -m pytest tests/test_retrieval_pipeline.py tests/test_testing_levels.py -q` — expected: all pass (the second file proves the `TEST_LEVELS` registration is complete).

- [ ] Commit:

  ```bash
  git add src/memoria_vault/runtime/retrieval_pipeline.py tests/test_retrieval_pipeline.py tests/conftest.py
  git commit -m "$(cat <<'EOF'
  feat(retrieval): shared pipeline staging module (R2 P.1)

  Ordered pipeline_counts builder (universe -> filters -> ranked -> returned,
  unique-suffixed repeats), excluded_strata with always-present zeros, the
  explicit no-op rerank seam (rerank: off), the honest-empty sentence, and
  the deterministic trace builder. Pure stdlib; consumed by ask now and
  memoria explore in the explore section.

  Co-Authored-By: Claude Fable 5 <noreply@anthropic.com>
  EOF
  )"
  ```

---

### Task P.2 — Honest-empty + check-gate-ride-through on ask

**Files:**
- `src/memoria_vault/runtime/search_index.py` (universe/strata accounting; `answer_query`; `_answer_from_hits`)
- `src/memoria_vault/cli.py` (`_cmd_ask`, `cli.py:706-712` — text-front honest-empty)
- `tests/test_search_index.py` (two new tests + one pinned-assertion update at `:349-351`; registered `contract`)
- `tests/test_cli_honesty.py` (one new CLI-front test; registered `contract`)

**Interfaces:**
- `checked_search_universe(vault: Path, *, include_stale: bool = False) -> dict[str, Any]` (new, in `search_index.py`) — returns `{"documents": [...], "excluded_strata": {"unchecked": n, "stale": n, "gated": n}}`; denominators built where the set is built (spec §2 closing rule applied to the ask universe).
- `checked_search_documents` (`search_index.py:115`) becomes a thin delegate returning `checked_search_universe(...)["documents"]` — signature and document list unchanged (its other callers `indexing.py:69-71`, `_rebuild_checked_search_index` `:83`, `search_checked_index` `:192`, `evaluate_bm25` `:351` ride through untouched).
- `answer_query` (`search_index.py:153-177`) — same signature; payload gains `pipeline_counts` (ordered list) and `excluded_strata` (always present); zero-hit `unknowns[0]` becomes the honest-empty sentence.
- `_answer_from_hits` (`search_index.py:211-249`) — gains required keyword-only params `pipeline_counts: list[dict[str, Any]]`, `excluded_strata: dict[str, int]` (single call site).

**Where consumability gating lives (verified):** `read_barrier.is_consumable_checked_file` (`src/memoria_vault/runtime/read_barrier.py:14-30`), called from the checked walk at `search_index.py:145`; it refuses when the DB verdict is not `checked`, when the checked output record is missing, or when the file hash no longer matches the checked record (tamper), enqueuing an `observe-pi-edits` scan. Stratum classification (resolved spec gap, see open questions): DB verdict `quarantined` → **gated** (explicit negative gate); any other non-`checked` verdict (incl. no DB row) → **unchecked**; verdict `checked` but barrier-refused → **gated**; hard staleness (`_hard_staleness` `search_index.py:404-411`: lifecycle retracted/archived, note curation candidate/rejected) with `include_stale=False` → **stale**. Soft-stale flags (`_memoria_stale`) keep the shipped behavior: the doc stays ranked and surfaces in `staleness` rows — the strata count *excluded* documents only, matching §0's "never silently dropped".

**Steps — cycle A (seam):**

- [ ] Failing tests. Append to `tests/test_search_index.py`:

  ```python
  def test_zero_hit_answer_query_is_honest_about_denominators(tmp_path: Path) -> None:
      vault = workspace(tmp_path)
      note(vault, "checked", "checked", "alpha beta")
      note(vault, "pending", "unchecked", "poison alpha")

      answer = answer_query(vault, "absentterm")

      assert answer["sources"] == []
      assert answer["unknowns"] == [
          "0 of 1 candidates matched; 1 unchecked documents were not searched"
      ]
      assert answer["pipeline_counts"] == [
          {"stage": "universe", "count": 1},
          {"stage": "ranked", "count": 0},
          {"stage": "returned", "count": 0},
      ]
      assert answer["excluded_strata"] == {"unchecked": 1, "stale": 0, "gated": 0}


  def test_gated_document_rides_through_as_stratum_count_without_text(tmp_path: Path) -> None:
      vault = workspace(tmp_path)
      note(vault, "visible", "checked", "alpha beta")
      gated = note(vault, "gated", "checked", "alpha zzgatedsecret")
      gated.write_text(
          "---\ntype: note\ncheck_status: checked\ntitle: gated\n---\ntampered zzgatedsecret\n",
          encoding="utf-8",
      )
      note(vault, "quarantined", "quarantined", "alpha zzquarantinesecret")

      answer = answer_query(vault, "alpha")

      assert [source["path"] for source in answer["sources"]] == ["notes/visible.md"]
      assert answer["pipeline_counts"] == [
          {"stage": "universe", "count": 1},
          {"stage": "ranked", "count": 1},
          {"stage": "returned", "count": 1},
      ]
      assert answer["excluded_strata"] == {"unchecked": 0, "stale": 0, "gated": 2}
      payload = json.dumps(answer)
      assert "zzgatedsecret" not in payload
      assert "zzquarantinesecret" not in payload
      assert "notes/gated.md" not in payload
  ```

  And update the pinned zero-hit assertion inside `test_answer_query_contract_reports_sources_unknowns_and_contradictions` (shipped at `tests/test_search_index.py:349-351`). Edit (`old_string` → `new_string`):

  ```python
      missing = answer_query(vault, "absent")
      assert missing["sources"] == []
      assert missing["unknowns"] == ["No checked current sources matched: absent"]
  ```
  →
  ```python
      missing = answer_query(vault, "absent")
      assert missing["sources"] == []
      assert missing["unknowns"] == [
          "0 of 2 candidates matched; 0 unchecked documents were not searched"
      ]
      assert missing["excluded_strata"] == {"unchecked": 0, "stale": 1, "gated": 0}
  ```

  (That vault holds `checked` + soft-stale `superseded` in the universe = 2 candidates; the note-curation `candidate` doc is hard-stale-excluded = the `stale: 1` stratum.)

- [ ] Run `python -m pytest tests/test_search_index.py -q` — expected: 3 failures — the two new tests fail (`AssertionError` on the old `"No checked current sources matched: absentterm"` unknowns; `KeyError: 'pipeline_counts'`), and the edited pinned test fails comparing the old sentence.

- [ ] Minimal implementation in `src/memoria_vault/runtime/search_index.py`. Four edits, full code:

  1. Import line (`search_index.py:16`):
  ```python
  from memoria_vault.runtime import indexing, retrieval_pipeline, state
  ```

  2. Module constant next to `SEARCH_MANIFEST` (`:30`), and `_is_searchable_frontmatter` (`:379-382`) rewritten to use it:
  ```python
  SEARCHABLE_TYPES = frozenset({"work", "digest", "note", "hub", "project"})
  ```
  ```python
  def _is_searchable_frontmatter(frontmatter: dict[str, Any], *, include_stale: bool = False) -> bool:
      if frontmatter.get("type") not in SEARCHABLE_TYPES:
          return False
      return include_stale or not _hard_staleness("", frontmatter)
  ```

  3. Replace `checked_search_documents` (`:115-131`) with the universe function plus a delegate (`checked_concepts` at `:134` stays untouched — it is exported and pinned by tests):
  ```python
  def checked_search_documents(vault: Path, *, include_stale: bool = False) -> list[dict[str, Any]]:
      return checked_search_universe(vault, include_stale=include_stale)["documents"]


  def checked_search_universe(vault: Path, *, include_stale: bool = False) -> dict[str, Any]:
      """Return the searchable universe plus the excluded-strata counts.

      Strata: ``unchecked`` (no ``checked`` verdict yet), ``gated`` (a
      ``quarantined`` verdict, or a checked file the read barrier refuses),
      ``stale`` (hard staleness excluded when ``include_stale`` is false).
      Zeros are always present; gated content contributes counts only.
      """
      vault = Path(vault)
      strata = retrieval_pipeline.excluded_strata()
      docs: list[dict[str, Any]] = []
      for root in _bundle_roots(vault):
          base = vault / root
          if not base.exists():
              continue
          for path in iter_markdown(base, skip_dirs=frozenset()):
              rel = path.relative_to(vault).as_posix()
              status = state.concept_check_status(vault, rel)
              if status == "quarantined":
                  strata["gated"] += 1
                  continue
              if status != "checked":
                  strata["unchecked"] += 1
                  continue
              if not is_consumable_checked_file(vault, rel):
                  strata["gated"] += 1
                  continue
              text = safe_read(path)
              frontmatter = _frontmatter_with_flags(vault, rel, text)
              if frontmatter.get("type") not in SEARCHABLE_TYPES:
                  continue
              if not include_stale and _hard_staleness(rel, frontmatter):
                  strata["stale"] += 1
                  continue
              docs.append({"path": rel, "text": text, "frontmatter": frontmatter, "source": path})
      if not include_stale:
          docs.extend(_checked_work_documents(vault))
      return {
          "documents": sorted(docs, key=lambda row: str(row["path"])),
          "excluded_strata": strata,
      }
  ```

  4. `answer_query` (`:153-177`) and `_answer_from_hits` (`:211-249`) rewritten; note the shipped ask has no named filter stages (project context expands the *query*, spec §3 Shape-1), so its ordered counts are `universe -> ranked -> returned`, and the no-op rerank seam is exercised on the shared path between ranking and return:
  ```python
  def answer_query(
      vault: Path,
      query: str,
      *,
      context: OperationContext,
      k: int = 5,
      include_stale: bool = False,
      project_id: str = "",
  ) -> dict[str, Any]:
      """Return a deterministic Ask/Query contract over checked retrieval hits."""
      validate_operation_context(vault, context)
      vault = Path(vault)
      indexing.refresh_stale_passages(vault, context=context)
      universe = checked_search_universe(vault, include_stale=include_stale)
      docs = [
          (document["path"], document["text"], document["frontmatter"])
          for document in universe["documents"]
      ]
      project_context = _project_context(project_id, docs)
      retrieval_query = _project_query(query, project_context)
      tokenized = [(path, _tokens(text)) for path, text, _frontmatter in docs]
      frontmatter_by_path = {path: frontmatter for path, _text, frontmatter in docs}
      ranked = _bm25(tokenized, retrieval_query)
      hits = retrieval_pipeline.rerank(ranked[:k])
      stages = retrieval_pipeline.PipelineStages(len(docs))
      stages.add_ranked(len(ranked))
      stages.add_returned(len(hits))
      return _answer_from_hits(
          query,
          hits,
          frontmatter_by_path,
          engine="bm25",
          project_context=project_context,
          pipeline_counts=stages.rows(),
          excluded_strata=universe["excluded_strata"],
      )
  ```
  ```python
  def _answer_from_hits(
      query: str,
      hits: list[tuple[str, float]],
      frontmatter_by_path: dict[str, dict[str, Any]],
      *,
      engine: str,
      pipeline_counts: list[dict[str, Any]],
      excluded_strata: dict[str, int],
      project_context: dict[str, Any] | None = None,
  ) -> dict[str, Any]:
      sources = []
      staleness = []
      contradictions = []
      for path, score in hits:
          frontmatter = frontmatter_by_path.get(path)
          if frontmatter is None:
              continue
          source = {
              "path": path,
              "title": frontmatter.get("title") or Path(path).stem,
              "type": frontmatter.get("type"),
              "score": score,
          }
          sources.append(source)
          stale = _staleness(path, frontmatter)
          if stale:
              staleness.append(stale)
          if isinstance(frontmatter.get("contradictions"), list):
              for item in frontmatter["contradictions"]:
                  contradictions.append({"path": path, "contradiction": item})
      answer = {
          "query": query,
          "engine": engine,
          "sources": sources,
          "unknowns": (
              []
              if sources
              else [retrieval_pipeline.honest_empty(pipeline_counts, excluded_strata)]
          ),
          "staleness": staleness,
          "contradictions": contradictions,
          "pipeline_counts": pipeline_counts,
          "excluded_strata": excluded_strata,
      }
      if project_context:
          answer["project_context"] = project_context
      return answer
  ```

- [ ] Run `python -m pytest tests/test_search_index.py tests/test_query_substrate.py tests/test_worker_product_jobs.py -q` — expected: all pass (the additive payload keys break no worker/substrate pins; verified: only `tests/test_search_index.py:351` pinned the old literal).

**Steps — cycle B (CLI text front):**

- [ ] Failing test. Append to `tests/test_cli_honesty.py`:

  ```python
  def test_ask_zero_hit_renders_honest_empty_on_text_and_json(tmp_path, capsys):
      import json as jsonlib
      import re

      from memoria_vault.cli import main
      from tests.helpers import init_cli_workspace

      workspace = init_cli_workspace(tmp_path, capsys)

      args = ["ask", "--question", "zz-absent-canary", "--workspace", str(workspace)]
      assert main([*args, "--json"]) == 0
      answer = jsonlib.loads(capsys.readouterr().out)["result"]
      assert answer["sources"] == []
      sentence = answer["unknowns"][0]
      assert re.fullmatch(
          r"0 of \d+ candidates matched; \d+ unchecked documents were not searched",
          sentence,
      )
      assert [row["stage"] for row in answer["pipeline_counts"]] == [
          "universe",
          "ranked",
          "returned",
      ]
      assert sorted(answer["excluded_strata"]) == ["gated", "stale", "unchecked"]

      assert main(args) == 0
      assert sentence in capsys.readouterr().out
  ```

- [ ] Run `python -m pytest tests/test_cli_honesty.py -q` — expected: 1 failure at the final assertion (the `--json` front already carries the sentence after cycle A; the text front still prints `_success_detail`'s generic summary, not the sentence).

- [ ] Minimal implementation — replace `_cmd_ask` (`cli.py:706-712`) in full:

  ```python
  def _cmd_ask(args: argparse.Namespace) -> int:
      result = _enqueue_and_run(args, "answer-query", {"query": args.question, "k": 5})
      raw = result.get("result")
      answer: dict[str, Any] = raw if isinstance(raw, dict) else {}
      if (
          bool(result.get("ok"))
          and not args.json
          and not args.quiet
          and not answer.get("sources")
          and answer.get("unknowns")
      ):
          print(str(answer["unknowns"][0]))
          return 0
      return _emit(result, args)
  ```

- [ ] Run `python -m pytest tests/test_cli_honesty.py tests/test_cli.py tests/test_cli_work_project.py -q` — expected: all pass (`test_cli_command_surface_is_exact` at `tests/test_cli.py:73` is command-level, untouched here).

- [ ] Commit:

  ```bash
  git add src/memoria_vault/runtime/search_index.py src/memoria_vault/cli.py tests/test_search_index.py tests/test_cli_honesty.py
  git commit -m "$(cat <<'EOF'
  feat(ask): honest-empty denominators + check-gate ride-through (R2 P.2)

  answer_query now carries ordered pipeline_counts and excluded_strata
  (unchecked/stale/gated, zeros always present); zero-hit unknowns become
  the counted honest-empty sentence on both CLI text and --json; gated and
  quarantined documents ride through as stratum counts only and never leak
  text. checked_search_documents delegates to the new
  checked_search_universe walk; document membership is unchanged.

  Co-Authored-By: Claude Fable 5 <noreply@anthropic.com>
  EOF
  )"
  ```

---

### Task P.3 — `--trace` on ask + the explore consumer contract

**Files:**
- `src/memoria_vault/runtime/search_index.py` (`answer_query` gains `trace: bool = False`)
- `src/memoria_vault/runtime/worker.py` (`answer-query` dispatch, `worker.py:740-756` — thread `trace`)
- `src/memoria_vault/cli.py` (ask parser `cli.py:104-107`; `_cmd_ask`; new `_print_ask_trace`)
- `tests/test_search_index.py`, `tests/test_cli_honesty.py`

**Interfaces:**
- `answer_query(vault, query, *, context, k=5, include_stale=False, project_id="", trace=False)` — when `trace=True` the payload gains `trace = build_trace(pipeline_counts, hits)`: same ordered counts, `scores` for returned hits, `rerank: "off"`, and `fusion_inputs` only when more than one ranked leg exists (BM25 is the only leg today, so it is absent — honest by construction).
- `answer-query` worker payload accepts optional `trace: bool` (no capability-doc change needed — `answer-query.md` declares no per-arg schema; `k`/`include_stale`/`project_id` already ride undeclared).
- `memoria ask --trace` CLI flag; text front prints one `stage: count` line per pipeline row plus `rerank: off`.

**Steps — cycle A (seam):**

- [ ] Failing test. Append to `tests/test_search_index.py`:

  ```python
  def test_answer_query_trace_reports_counts_scores_and_rerank_off(tmp_path: Path) -> None:
      vault = workspace(tmp_path)
      note(vault, "checked", "checked", "alpha beta")

      traced = answer_query(vault, "alpha", trace=True)

      assert traced["trace"]["rerank"] == "off"
      assert traced["trace"]["pipeline_counts"] == traced["pipeline_counts"]
      assert traced["trace"]["scores"] == [
          {"path": source["path"], "score": source["score"]} for source in traced["sources"]
      ]
      assert "fusion_inputs" not in traced["trace"]
      assert "trace" not in answer_query(vault, "alpha")
  ```

- [ ] Run `python -m pytest tests/test_search_index.py -q` — expected failure: `TypeError: answer_query() got an unexpected keyword argument 'trace'`.

- [ ] Minimal implementation — `answer_query` final form (replaces the P.2 version; only the signature line, the tail, and the return change):

  ```python
  def answer_query(
      vault: Path,
      query: str,
      *,
      context: OperationContext,
      k: int = 5,
      include_stale: bool = False,
      project_id: str = "",
      trace: bool = False,
  ) -> dict[str, Any]:
      """Return a deterministic Ask/Query contract over checked retrieval hits."""
      validate_operation_context(vault, context)
      vault = Path(vault)
      indexing.refresh_stale_passages(vault, context=context)
      universe = checked_search_universe(vault, include_stale=include_stale)
      docs = [
          (document["path"], document["text"], document["frontmatter"])
          for document in universe["documents"]
      ]
      project_context = _project_context(project_id, docs)
      retrieval_query = _project_query(query, project_context)
      tokenized = [(path, _tokens(text)) for path, text, _frontmatter in docs]
      frontmatter_by_path = {path: frontmatter for path, _text, frontmatter in docs}
      ranked = _bm25(tokenized, retrieval_query)
      hits = retrieval_pipeline.rerank(ranked[:k])
      stages = retrieval_pipeline.PipelineStages(len(docs))
      stages.add_ranked(len(ranked))
      stages.add_returned(len(hits))
      answer = _answer_from_hits(
          query,
          hits,
          frontmatter_by_path,
          engine="bm25",
          project_context=project_context,
          pipeline_counts=stages.rows(),
          excluded_strata=universe["excluded_strata"],
      )
      if trace:
          answer["trace"] = retrieval_pipeline.build_trace(stages.rows(), hits)
      return answer
  ```

- [ ] Run `python -m pytest tests/test_search_index.py -q` — expected: all pass.

**Steps — cycle B (CLI flag threading + text render):**

- [ ] Failing test. Append to `tests/test_cli_honesty.py`:

  ```python
  def test_ask_trace_flag_threads_through_worker_and_prints_stage_lines(tmp_path, capsys):
      import json as jsonlib

      from memoria_vault.cli import main
      from tests.helpers import init_cli_workspace

      workspace = init_cli_workspace(tmp_path, capsys)
      args = ["ask", "--question", "zz-trace-canary", "--workspace", str(workspace)]

      assert main([*args, "--trace", "--json"]) == 0
      trace = jsonlib.loads(capsys.readouterr().out)["result"]["trace"]
      assert trace["rerank"] == "off"
      assert [row["stage"] for row in trace["pipeline_counts"]] == [
          "universe",
          "ranked",
          "returned",
      ]
      assert "fusion_inputs" not in trace

      assert main([*args, "--trace"]) == 0
      out = capsys.readouterr().out
      assert "rerank: off" in out
      for line in ("universe: ", "ranked: ", "returned: "):
          assert line in out

      assert main([*args, "--json"]) == 0
      assert "trace" not in jsonlib.loads(capsys.readouterr().out)["result"]
  ```

- [ ] Run `python -m pytest tests/test_cli_honesty.py -q` — expected failure: `SystemExit: 2` from argparse (`unrecognized arguments: --trace`).

- [ ] Minimal implementation, three edits:

  1. Ask parser (`cli.py:104-107`), old → new:
  ```python
      ask = sub.add_parser("ask")
      _common(ask)
      ask.add_argument("--question", required=True)
      ask.set_defaults(handler=_cmd_ask)
  ```
  →
  ```python
      ask = sub.add_parser("ask")
      _common(ask)
      ask.add_argument("--question", required=True)
      ask.add_argument("--trace", action="store_true")
      ask.set_defaults(handler=_cmd_ask)
  ```
  (No `test_cli_command_surface_is_exact` edit: that test pins subcommand names, not flags — verified against `tests/cli_test_helpers.py:_cli_command_surface`. The U1 surface-registry both-branch step belongs to the explore CLI row in section E, not here.)

  2. Worker dispatch (`worker.py:749-756`), old → new:
  ```python
          return answer_query(
              vault,
              query,
              context=context,
              k=k,
              include_stale=bool(payload.get("include_stale", False)),
              project_id=str(payload.get("project_id") or ""),
          )
  ```
  →
  ```python
          return answer_query(
              vault,
              query,
              context=context,
              k=k,
              include_stale=bool(payload.get("include_stale", False)),
              project_id=str(payload.get("project_id") or ""),
              trace=bool(payload.get("trace", False)),
          )
  ```

  3. `_cmd_ask` final form plus the render helper (replaces the P.2 version):
  ```python
  def _cmd_ask(args: argparse.Namespace) -> int:
      payload: dict[str, Any] = {"query": args.question, "k": 5}
      if args.trace:
          payload["trace"] = True
      result = _enqueue_and_run(args, "answer-query", payload)
      raw = result.get("result")
      answer: dict[str, Any] = raw if isinstance(raw, dict) else {}
      text_front = bool(result.get("ok")) and not args.json and not args.quiet
      if text_front and not answer.get("sources") and answer.get("unknowns"):
          print(str(answer["unknowns"][0]))
          _print_ask_trace(answer)
          return 0
      code = _emit(result, args)
      if text_front:
          _print_ask_trace(answer)
      return code


  def _print_ask_trace(answer: dict[str, Any]) -> None:
      trace = answer.get("trace")
      if not isinstance(trace, dict):
          return
      for row in trace.get("pipeline_counts") or []:
          print(f"{row['stage']}: {row['count']}")
      print(f"rerank: {trace.get('rerank', 'off')}")
  ```

- [ ] Run `python -m pytest tests/test_cli_honesty.py tests/test_search_index.py tests/test_cli.py -q` — expected: all pass.

- [ ] Section-final gate: run `python scripts/verify` — expected: green (lint, product gates, tests, offline smoke, syntax).

- [ ] Commit:

  ```bash
  git add src/memoria_vault/runtime/search_index.py src/memoria_vault/runtime/worker.py src/memoria_vault/cli.py tests/test_search_index.py tests/test_cli_honesty.py
  git commit -m "$(cat <<'EOF'
  feat(ask): --trace retrieval trace (R2 P.3)

  answer_query(trace=True) attaches the deterministic trace: the same
  ordered pipeline_counts, BM25 scores for returned hits, fusion_inputs
  only beyond one ranked leg (absent today), and rerank: off. Threaded
  through the answer-query worker payload and a new memoria ask --trace
  flag; the text front prints per-stage counts plus rerank: off.

  Co-Authored-By: Claude Fable 5 <noreply@anthropic.com>
  EOF
  )"
  ```

**Seam handoff to section E (explore) — the consumer contract, binding:** `memoria explore` builds its own `PipelineStages` per side (named filter stages such as `project-slice` and `depth-expansion` via `add_filter`, unique-suffixed automatically), passes its seed ranking through `retrieval_pipeline.rerank(...)` between rank and return, attaches `stages.rows()` / `retrieval_pipeline.excluded_strata(...)` to its payload (per side under `--versus`, spec §3), renders zero-seed results via `retrieval_pipeline.honest_empty(rows, strata)`, and implements `--trace` as `retrieval_pipeline.build_trace(stages.rows(), seed_hits)` with the identical CLI flag semantics shown here. E imports only `memoria_vault.runtime.retrieval_pipeline` for this — not `search_index`.
# E · `memoria explore` (spec §3 — slice 3)

Implements the R2 design's **Shape-2 topic surfacing** command (spec §3: seed stage BM25 top-5 over the same checked index ask uses, structural expansion via `graph_sql.neighborhood` with default depth 1 / hard cap 2, payload grouped by kind with the claim-grounds visibility mark, `--versus` juxtaposition with per-side counts, and the ruled name-collision handling against the shipped `memoria project explore`). The payload carries the §4 denominator contract (ordered `pipeline_counts`, always-present `excluded_strata`, honest-empty sentence) and E.3 wires the §9 acceptance fixture. `explore` is a **pure read that emits no telemetry** (spec §3 end): no `OperationContext`, no operation enqueue, no journal writes of its own.

Work in the r2-plan worktree (`/home/eranr/memoria-vault/.claude/worktrees/r2-plan`, origin/main `51395f15`). All line refs below verified at that commit; re-anchor by symbol if drifted.

**Sequencing stop-note (grep-first, binding):** this section executes after the graph_sql section (slice 1), which itself executes after Plan 22 G2S1.1. Before starting:

```bash
test -f src/memoria_vault/runtime/graph_sql.py \
  && grep -n "def neighborhood\|def project_slice" src/memoria_vault/runtime/graph_sql.py
```

Stop if missing — the shipped `concept_edges` extractor is a stub returning `[]` (`src/memoria_vault/runtime/indexing.py:133-136`), and without slice 1 there is no `neighborhood` to expand through. If the slice-1 section shipped the primitives under drifted names, re-anchor by symbol against spec §2's contract (`neighborhood(vault, seeds, *, depth, relations=None) -> {ids, counts}`, `project_slice(vault, project) -> {ids, counts}`). E's own tests seed edges directly via `state.replace_concept_edges` (`state.py:2026-2052`) so they are order-tolerant against G2S1.1's extractor details.

Shipped seams consumed (verified): `checked_search_documents` `search_index.py:115-131`; module-private ranking core `_bm25`/`_tokens` `search_index.py:580/:576` and `_bundle_roots` `:414` (intra-package reuse; `tests/test_search_index.py` already imports these privates — precedent); `state.concept_edges` `:2055-2076` (checked-only rows); `evidence_sets` schema `schema.sql:330-343` with `block_ref = <claim-relpath>#^blk-<id>` per `state._evidence_block_ref` `:2689-2690`; `replace_evidence_sets` `:2277-2332`; `memoria project explore` `cli.py:350-353`; pinned roster `tests/test_cli.py:73`; CLI plumbing `main`/`_fail` `cli.py:55-63/:3234`, `_common` `:560`, `_emit` `:3092`, `_workspace` `:2130`.

### Task E.1 — engine: `explore_topic` (seed → expand → group → mark)

**Files:** `src/memoria_vault/runtime/explore.py` (new), `tests/test_explore.py` (new), `tests/conftest.py` (register test level).
**Interfaces:** `explore_topic(vault: Path, topic: str, *, project: str = "", depth: int = 1, versus: str = "") -> dict[str, Any]`; constants `SEED_K = 5`, `DEPTH_CAP = 2`. Consumes `graph_sql.neighborhood` / `graph_sql.project_slice` (slice-1 seams), `state.concept_edges`, `checked_search_documents`, the `evidence_sets` table.

- [ ] Register the new test file (the `test_testing_levels.py` gate pins every `tests/test_*.py` into `TEST_LEVELS`). Edit `tests/conftest.py`:

  old:
  ```python
    "test_evidence_sets.py": "runtime",
    "test_exploration_channel.py": "runtime",
  ```
  new:
  ```python
    "test_evidence_sets.py": "runtime",
    "test_explore.py": "contract",
    "test_exploration_channel.py": "runtime",
  ```

- [ ] Write the failing test — create `tests/test_explore.py` (tmp_path vault only, no network; fixture helpers mirror `tests/test_search_index.py`'s `note()`/`upsert_catalog_record` idiom; tension edges seeded **in both directions** so the fixture is agnostic to slice 1's traversal-direction choice):

  ```python
  from __future__ import annotations

  from pathlib import Path

  from memoria_vault.runtime import state
  from memoria_vault.runtime.explore import explore_topic
  from memoria_vault.runtime.policy.audit import sha256_file
  from tests.helpers import copy_memoria_dirs


  def _vault(tmp_path: Path) -> Path:
      copy_memoria_dirs(tmp_path, "schemas")
      return tmp_path


  def _note(
      vault: Path,
      relpath: str,
      title: str,
      body: str,
      *,
      mode: str = "",
      status: str = "checked",
  ) -> None:
      path = vault / relpath
      path.parent.mkdir(parents=True, exist_ok=True)
      concept_type = "hub" if relpath.startswith("hubs/") else "note"
      mode_line = f"mode: {mode}\n" if mode else ""
      path.write_text(
          f"---\ntype: {concept_type}\ntitle: {title}\n{mode_line}---\n{body}\n",
          encoding="utf-8",
      )
      state.record_observed_file_edit(
          vault,
          output_id=relpath,
          concept_type=concept_type,
          output_sha256=sha256_file(path),
      )
      state.set_concept_verdict(vault, relpath, status)


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


  def _fixture_vault(tmp_path: Path) -> Path:
      """Post-G2S1.1-shaped vault: 5 checked docs, a tension pair, one thin claim.

      Tension edges are seeded in both directions so assertions hold whether
      slice 1's neighborhood traversal is directed or undirected.
      """
      vault = _vault(tmp_path)
      _note(
          vault,
          "notes/claim-spacing.md",
          "Spacing beats cramming",
          "The spacing effect improves retention.",
          mode="claim",
      )
      _note(
          vault,
          "notes/claim-massed.md",
          "Massed practice is superior",
          "Massed practice wins in short-horizon tests.",
          mode="claim",
      )
      _note(
          vault,
          "notes/question-spacing.md",
          "Where does spacing break down?",
          "Open question about spacing boundary conditions.",
          mode="question",
      )
      _note(vault, "hubs/memory.md", "Memory hub", "Spacing, retrieval practice, consolidation.")
      _note(
          vault,
          "notes/unchecked-noise.md",
          "Unchecked noise",
          "Unreviewed spacing chatter.",
          status="unchecked",
      )
      _work(
          vault,
          "settles-2016",
          "A trainable spaced repetition model",
          "Model of the spacing effect versus massed practice schedules. ^p0001",
      )
      state.replace_concept_edges(
          vault,
          [
              {
                  "source_concept_id": "notes/claim-spacing.md",
                  "relation_type": "tension",
                  "target_concept_id": "notes/claim-massed.md",
                  "check_status": "checked",
              },
              {
                  "source_concept_id": "notes/claim-massed.md",
                  "relation_type": "tension",
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
                  "source_concept_id": "notes/claim-spacing.md",
                  "relation_type": "extends",
                  "target_concept_id": "hubs/memory.md",
                  "check_status": "checked",
              },
          ],
      )
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


  def test_explore_topic_rejects_depth_beyond_cap_naming_it(tmp_path: Path) -> None:
      vault = _fixture_vault(tmp_path)
      try:
          explore_topic(vault, "spacing", depth=3)
      except ValueError as exc:
          assert "hard cap of 2" in str(exc)
          assert "3" in str(exc)
      else:
          raise AssertionError("depth=3 must be rejected naming the cap")
      try:
          explore_topic(vault, "spacing", depth=0)
      except ValueError as exc:
          assert "at least 1" in str(exc)
      else:
          raise AssertionError("depth=0 must be rejected")


  def test_explore_topic_groups_kinds_marks_thin_claims_and_counts(tmp_path: Path) -> None:
      vault = _fixture_vault(tmp_path)

      payload = explore_topic(vault, "spacing")

      assert payload["topic"] == "spacing"
      assert payload["depth"] == 1
      assert payload["pipeline_counts"] == [
          {"stage": "universe", "count": 5},
          {"stage": "ranked", "count": 4},
          {"stage": "seed", "count": 4},
          {"stage": "neighborhood", "count": 5},
          {"stage": "returned", "count": 6},
      ]
      assert payload["excluded_strata"] == {"unchecked": 1, "stale": 0, "gated": 0}

      claims = {entry["id"]: entry for entry in payload["claims"]}
      assert set(claims) == {"notes/claim-spacing.md", "notes/claim-massed.md"}
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
      assert payload["questions"][0]["edges"] == []
      assert [entry["id"] for entry in payload["works"]] == ["catalog/sources/settles-2016"]
      assert payload["works"][0]["title"] == "A trainable spaced repetition model"
      assert [entry["id"] for entry in payload["hubs"]] == ["hubs/memory.md"]
      assert payload["tensions"] == [
          {
              "pair": ["notes/claim-massed.md", "notes/claim-spacing.md"],
              "titles": ["Massed practice is superior", "Spacing beats cramming"],
              "relation_type": "tension",
          }
      ]


  def test_explore_topic_depth_two_reaches_second_hop(tmp_path: Path) -> None:
      vault = _fixture_vault(tmp_path)

      one_hop = explore_topic(vault, "massed", depth=1)
      two_hop = explore_topic(vault, "massed", depth=2)

      one_stage = {row["stage"]: row["count"] for row in one_hop["pipeline_counts"]}
      two_stage = {row["stage"]: row["count"] for row in two_hop["pipeline_counts"]}
      assert one_stage["neighborhood"] == 3
      assert two_stage["neighborhood"] == 4
      assert one_hop["hubs"] == []
      assert [entry["id"] for entry in two_hop["hubs"]] == ["hubs/memory.md"]
      assert two_hop["depth"] == 2
  ```

- [ ] Run: `python -m pytest tests/test_explore.py -q` — expected failure: `ModuleNotFoundError: No module named 'memoria_vault.runtime.explore'` at collection.
- [ ] Minimal implementation — create `src/memoria_vault/runtime/explore.py`. The grounds mark is the real SQL over `evidence_sets` (schema `schema.sql:330-343`): `block_ref` is `<claim-relpath>#^blk-<id>` (`state._evidence_block_ref`, `state.py:2689-2690`), so the claim path is the half before `#`, and only `state = 'complete'` rows count:

  ```python
  """Shape-2 topic surfacing (`memoria explore`) — a pure read, no telemetry.

  R2 design §3: seed with BM25 top-5 over the same checked index ask uses,
  expand through graph_sql.neighborhood (default depth 1, hard cap 2), group
  by kind, and mark every claim with its count of complete evidence sets.
  The candidate set defines the denominator (§1); every payload carries the
  ordered pipeline_counts and always-present excluded_strata (§4).
  """

  from __future__ import annotations

  from pathlib import Path
  from typing import Any

  from memoria_vault.runtime import graph_sql, state
  from memoria_vault.runtime.read_barrier import is_consumable_checked_file
  from memoria_vault.runtime.search_index import (
      _bm25,
      _bundle_roots,
      _tokens,
      checked_search_documents,
  )
  from memoria_vault.runtime.vaultio import iter_markdown

  SEED_K = 5
  DEPTH_CAP = 2
  KIND_GROUPS = ("claims", "questions", "tensions", "works", "hubs")


  def explore_topic(
      vault: Path,
      topic: str,
      *,
      project: str = "",
      depth: int = 1,
      versus: str = "",
  ) -> dict[str, Any]:
      """Return the grouped Shape-2 payload for one topic, or two under --versus."""
      if depth < 1:
          raise ValueError(f"explore depth must be at least 1: got {depth}")
      if depth > DEPTH_CAP:
          raise ValueError(f"explore depth {depth} exceeds the hard cap of {DEPTH_CAP}")
      vault = Path(vault)
      if not versus:
          side, _ids = _explore_side(vault, topic, project=project, depth=depth)
          return side
      side_a, a_ids = _explore_side(vault, topic, project=project, depth=depth)
      side_b, b_ids = _explore_side(vault, versus, project=project, depth=depth)
      titles = _titles(vault)
      shared = sorted(a_ids & b_ids)
      crossing = _tension_pairs(vault, a_ids, b_ids, titles)
      return {
          "topic": topic,
          "versus": versus,
          "a": side_a,
          "b": side_b,
          "intersection": {
              "ids": shared,
              "count": len(shared),
              "a_count": len(a_ids),
              "b_count": len(b_ids),
          },
          "crossing_tensions": {"pairs": crossing, "count": len(crossing)},
      }


  def _explore_side(
      vault: Path, topic: str, *, project: str, depth: int
  ) -> tuple[dict[str, Any], set[str]]:
      docs = checked_search_documents(vault)
      by_concept = {_concept_id(document): document for document in docs}
      pipeline_counts: list[dict[str, Any]] = [{"stage": "universe", "count": len(docs)}]
      candidates = docs
      if project:
          project_ids = graph_sql.project_slice(vault, project)["ids"]
          slice_ids = {str(concept_id) for concept_id in project_ids}
          candidates = [document for document in docs if _concept_id(document) in slice_ids]
          pipeline_counts.append({"stage": "project-slice", "count": len(candidates)})
      tokenized = [
          (str(document["path"]), _tokens(str(document["text"]))) for document in candidates
      ]
      ranked = _bm25(tokenized, topic)
      pipeline_counts.append({"stage": "ranked", "count": len(ranked)})
      concept_by_path = {str(document["path"]): _concept_id(document) for document in candidates}
      seed_scores: dict[str, float] = {}
      for path, score in ranked[:SEED_K]:
          seed_scores.setdefault(concept_by_path[path], float(score))
      pipeline_counts.append({"stage": "seed", "count": len(seed_scores)})
      expanded = set(seed_scores)
      if expanded:
          expanded |= {
              str(concept_id)
              for concept_id in graph_sql.neighborhood(vault, sorted(expanded), depth=depth)["ids"]
          }
      # The candidate set defines the denominator (§1); gated or unchecked ids
      # ride through as stratum counts only and never leak into groups (§4).
      expanded &= set(concept_by_path.values())
      pipeline_counts.append({"stage": "neighborhood", "count": len(expanded)})
      titles = {concept_id: _title(document) for concept_id, document in by_concept.items()}
      edges_by_id = _edges_by_concept(vault, expanded)
      grounds = _complete_grounds_by_claim(vault)
      groups: dict[str, list[dict[str, Any]]] = {group: [] for group in KIND_GROUPS}
      for concept_id in sorted(expanded):
          document = by_concept.get(concept_id)
          if document is None:
              continue
          kind = _kind(concept_id, _frontmatter(document))
          if kind not in groups:
              continue
          entry: dict[str, Any] = {
              "id": concept_id,
              "title": titles[concept_id],
              "seed_score": seed_scores.get(concept_id, 0.0),
              "edges": edges_by_id.get(concept_id, []),
          }
          if kind == "claims":
              count = int(grounds.get(concept_id, 0))
              entry["grounds_count"] = count
              entry["zero_grounds"] = count == 0
          groups[kind].append(entry)
      for entries in groups.values():
          entries.sort(key=_entry_order)
      groups["tensions"] = _tension_pairs(vault, expanded, expanded, titles)
      returned = sum(len(entries) for entries in groups.values())
      pipeline_counts.append({"stage": "returned", "count": returned})
      payload: dict[str, Any] = {
          "topic": topic,
          "depth": depth,
          **groups,
          "pipeline_counts": pipeline_counts,
          "excluded_strata": _excluded_strata(vault, {str(document["path"]) for document in docs}),
      }
      return payload, expanded


  def _entry_order(entry: dict[str, Any]) -> tuple[float, str, str]:
      # Within-group ordering: BM25 seed score, then title (§3), then id.
      return (-float(entry["seed_score"]), str(entry["title"]), str(entry["id"]))


  def _frontmatter(document: dict[str, Any]) -> dict[str, Any]:
      frontmatter = document.get("frontmatter")
      return frontmatter if isinstance(frontmatter, dict) else {}


  def _title(document: dict[str, Any]) -> str:
      return str(_frontmatter(document).get("title") or Path(str(document["path"])).stem)


  def _titles(vault: Path) -> dict[str, str]:
      return {
          _concept_id(document): _title(document) for document in checked_search_documents(vault)
      }


  def _concept_id(document: dict[str, Any]) -> str:
      """Map a checked search document to its concept id (§3 seed mapping).

      Mirrors indexing._passage_row: vault path, catalog/sources/<work_id>
      for generated fulltext work documents.
      """
      path = str(document["path"])
      if path.startswith("fulltexts/"):
          work_id = str(_frontmatter(document).get("work_id") or Path(path).stem)
          return f"catalog/sources/{work_id}"
      return path


  def _kind(concept_id: str, frontmatter: dict[str, Any]) -> str:
      if concept_id.startswith("catalog/sources/"):
          return "works"
      concept_type = str(frontmatter.get("type") or "")
      mode = str(frontmatter.get("mode") or "")
      if concept_type == "note" and mode == "claim":
          return "claims"
      if concept_type == "note" and mode == "question":
          return "questions"
      if concept_type in {"work", "digest", "fulltext"}:
          return "works"
      if concept_type == "hub":
          return "hubs"
      return ""


  def _edges_by_concept(vault: Path, ids: set[str]) -> dict[str, list[dict[str, str]]]:
      """Undirected display edges for every id in ``ids``, deduplicated."""
      touching: dict[str, set[tuple[str, str]]] = {}
      for edge in state.concept_edges(vault):
          source = str(edge["source_concept_id"])
          target = str(edge["target_concept_id"])
          relation = str(edge["relation_type"])
          if source in ids:
              touching.setdefault(source, set()).add((relation, target))
          if target in ids:
              touching.setdefault(target, set()).add((relation, source))
      return {
          concept_id: [
              {"relation_type": relation, "target": target} for relation, target in sorted(pairs)
          ]
          for concept_id, pairs in touching.items()
      }


  def _tension_pairs(
      vault: Path, left_ids: set[str], right_ids: set[str], titles: dict[str, str]
  ) -> list[dict[str, Any]]:
      """Tension edges spanning the two id sets, as deduplicated unordered pairs."""
      pairs: dict[tuple[str, str], dict[str, Any]] = {}
      for edge in state.concept_edges(vault):
          if str(edge["relation_type"]) != "tension":
              continue
          source = str(edge["source_concept_id"])
          target = str(edge["target_concept_id"])
          across = (source in left_ids and target in right_ids) or (
              source in right_ids and target in left_ids
          )
          if not across:
              continue
          key = (min(source, target), max(source, target))
          pairs[key] = {
              "pair": list(key),
              "titles": [titles.get(key[0], key[0]), titles.get(key[1], key[1])],
              "relation_type": "tension",
          }
      return [pairs[key] for key in sorted(pairs)]


  def _complete_grounds_by_claim(vault: Path) -> dict[str, int]:
      """Count ``complete`` evidence-set rows per claim path (§3 grounds mark).

      evidence_sets.block_ref is ``<claim-relpath>#^blk-<id>`` (see
      state._evidence_block_ref); the path half before ``#`` names the claim
      whose block the evidence set grounds.
      """
      if not state.db_path(vault).is_file():
          return {}
      with state.connect(vault) as conn:
          rows = conn.execute(
              """
              SELECT
                  CASE
                      WHEN instr(block_ref, '#') > 0
                          THEN substr(block_ref, 1, instr(block_ref, '#') - 1)
                      ELSE block_ref
                  END AS claim_path,
                  COUNT(*) AS complete_sets
              FROM evidence_sets
              WHERE state = 'complete'
              GROUP BY claim_path
              """
          ).fetchall()
      return {str(row["claim_path"]): int(row["complete_sets"]) for row in rows}


  def _excluded_strata(vault: Path, universe_paths: set[str]) -> dict[str, int]:
      """Named strata with counts, zeros included (§4): unchecked, stale, gated."""
      strata = {"unchecked": 0, "stale": 0, "gated": 0}
      for root in _bundle_roots(vault):
          base = vault / root
          if not base.exists():
              continue
          for path in iter_markdown(base, skip_dirs=frozenset()):
              rel = path.relative_to(vault).as_posix()
              if rel in universe_paths:
                  continue
              status = state.concept_check_status(vault, rel)
              if status == "quarantined":
                  strata["gated"] += 1
              elif status != "checked":
                  strata["unchecked"] += 1
              elif not is_consumable_checked_file(vault, rel):
                  strata["gated"] += 1
              else:
                  strata["stale"] += 1
      return strata
  ```

- [ ] Run to pass: `python -m pytest tests/test_explore.py -q` — 3 passed. Also run the neighbor contract file to catch import fallout: `python -m pytest tests/test_search_index.py -q`.
- [ ] Commit (explicit paths only — the git index is shared per checkout):

  ```bash
  git add src/memoria_vault/runtime/explore.py tests/test_explore.py tests/conftest.py
  git commit -m "feat(retrieval): explore_topic Shape-2 engine — BM25 seeds, neighborhood expansion, kind groups, grounds marks (R2 §3)" -m "Co-Authored-By: Claude Fable 5 <noreply@anthropic.com>"
  ```

### Task E.2 — CLI: `memoria explore <topic>` with the pinned surface edit and help disambiguation

**Files:** `src/memoria_vault/cli.py`, `tests/test_cli.py`.
**Interfaces:** `memoria explore <topic> [--versus B] [--project P] [--depth N] [--trace]` (plus `_common`'s `--workspace/--json/--quiet/--idempotency-key/--schedule-id/--actor`); handler `_cmd_explore` — a pure read calling `explore_topic` directly (no `_enqueue_and_run`, mirroring `_cmd_project_explore` `cli.py:1199-1205`); `--depth` > 2 exits 2 with the cap named (`main`'s CLI boundary, `cli.py:55-63`).

- [ ] **The pinned `test_cli_command_surface_is_exact` edit (named step, spec §3/§9).** Edit `tests/test_cli.py` (roster at `:73`):

  old:
  ```python
          "memoria ask",
          "memoria serve",
  ```
  new:
  ```python
          "memoria ask",
          "memoria explore",
          "memoria serve",
  ```

- [ ] **U1 surface-contract registry row (grep-first, both branches).** Run:

  ```bash
  ls src/memoria_vault/engine/ && grep -rln "registry" src/memoria_vault/engine/
  ```

  - **If a U1 surface-contract registry module has landed** (an `engine/` module beyond the shipped `api.py`/`empirical_events.py`/`surface_contract.py` that registers CLI command rows — the U1 gate owns it): add the `memoria explore` row there following that module's established row form and its own contract test, and include that file in this task's commit.
  - **Else (the shipped state at 51395f15):** the only registry is `SURFACE_ACTIONS` in `engine/surface_contract.py`, which registers engine *read actions* — `memoria ask` itself carries no row there, and the floor-coverage gate (`tests/test_floor_coverage.py`) keys off `actions_by_id()`, so adding an action row would demand ARG_TABLE floor entries this slice does not own. Add **nothing** to `surface_contract.py`; the pinned roster edit above is the entire surface registration.

- [ ] Add the two failing CLI tests — append to the end of `tests/test_cli.py` (all names used — `json`, `pytest`, `Path`, `main`, `_build_parser`, `_parser_for_command`, `_parser_dests`, `state` — are already imported at `:1-16`):

  ```python
  def test_cli_explore_help_disambiguates_project_explore_both_directions() -> None:
      parser = _build_parser()

      explore = _parser_for_command(parser, "memoria explore")
      project_explore = _parser_for_command(parser, "memoria project explore")

      assert "memoria project explore" in str(explore.description)
      assert "memoria explore" in str(project_explore.description)
      assert _parser_dests("memoria explore") >= {"topic", "versus", "project", "depth", "trace"}
      # memoria project explore keeps its name and semantics (spec §3 ruling).
      assert "limit" in _parser_dests("memoria project explore")


  def test_cli_explore_is_a_pure_read_with_trace_flag(
      tmp_path: Path, capsys: pytest.CaptureFixture[str]
  ) -> None:
      workspace = tmp_path / "workspace"
      main(["init", "--workspace", str(workspace), "--yes", "--json"])
      capsys.readouterr()
      with state.connect(workspace) as conn:
          before = conn.execute("SELECT COUNT(*) AS n FROM operation_requests").fetchone()["n"]

      rc = main(["explore", "anything", "--workspace", str(workspace), "--json", "--trace"])
      output = json.loads(capsys.readouterr().out)

      assert rc == 0
      assert output["ok"] is True
      assert output["explore"]["pipeline_counts"][0]["stage"] == "universe"
      assert output["explore"]["excluded_strata"].keys() == {"unchecked", "stale", "gated"}
      assert output["explore"]["trace"]["rerank"] == "off"
      with state.connect(workspace) as conn:
          after = conn.execute("SELECT COUNT(*) AS n FROM operation_requests").fetchone()["n"]
      assert after == before
  ```

- [ ] Run: `python -m pytest tests/test_cli.py -q` — expected failures: `test_cli_command_surface_is_exact` (roster mismatch: `memoria explore` missing from the parser), `KeyError: 'explore'` in both new tests.
- [ ] Minimal implementation — three edits to `src/memoria_vault/cli.py`:

  1. Help constants, after the `SURFACE_ACTION` assignment (`:52`):

     old:
     ```python
     SURFACE_ACTION = actions_by_id()
     ```
     new:
     ```python
     SURFACE_ACTION = actions_by_id()

     EXPLORE_HELP = (
         "Surface one topic's neighborhood across the whole vault: BM25 seeds, graph "
         "expansion, results grouped by kind (claims, questions, tensions, works, hubs). "
         "Distinct from 'memoria project explore', which lists uncaptured citation-graph "
         "coverage candidates (the exploration channel)."
     )
     PROJECT_EXPLORE_HELP = (
         "List uncaptured citation-graph coverage candidates (the exploration channel). "
         "Distinct from 'memoria explore <topic>', which surfaces a topic's neighborhood "
         "across the whole vault."
     )
     ```

  2. Parser wiring, after the `ask` block (`:104-107`):

     old:
     ```python
         ask = sub.add_parser("ask")
         _common(ask)
         ask.add_argument("--question", required=True)
         ask.set_defaults(handler=_cmd_ask)
     ```
     new:
     ```python
         ask = sub.add_parser("ask")
         _common(ask)
         ask.add_argument("--question", required=True)
         ask.set_defaults(handler=_cmd_ask)

         explore = sub.add_parser("explore", help=EXPLORE_HELP, description=EXPLORE_HELP)
         _common(explore)
         explore.add_argument("topic")
         explore.add_argument("--versus", default="")
         explore.add_argument("--project", default="")
         explore.add_argument("--depth", type=int, default=1)
         explore.add_argument("--trace", action="store_true")
         explore.set_defaults(handler=_cmd_explore)
     ```

     And the other direction of the disambiguation, at `memoria project explore` (`:350-351`):

     old:
     ```python
         explore = project_sub.add_parser("explore")
         _common(explore)
     ```
     new:
     ```python
         explore = project_sub.add_parser(
             "explore",
             help=PROJECT_EXPLORE_HELP,
             description=PROJECT_EXPLORE_HELP,
         )
         _common(explore)
     ```

  3. Handler + minimal trace baseline, after `_cmd_ask` (`:706-712`). The trace here is the honest §6 floor — the ordered stage counts plus `rerank: off`; the slice-6 (`ask-retrieval-trace`) section extends it with BM25 scores and per-filter before/after rows through this same payload key:

     old:
     ```python
     def _cmd_ask(args: argparse.Namespace) -> int:
         result = _enqueue_and_run(
             args,
             "answer-query",
             {"query": args.question, "k": 5},
         )
         return _emit(result, args)
     ```
     new:
     ```python
     def _cmd_ask(args: argparse.Namespace) -> int:
         result = _enqueue_and_run(
             args,
             "answer-query",
             {"query": args.question, "k": 5},
         )
         return _emit(result, args)


     def _cmd_explore(args: argparse.Namespace) -> int:
         from memoria_vault.runtime.explore import explore_topic

         payload = explore_topic(
             _workspace(args),
             args.topic,
             project=args.project,
             depth=args.depth,
             versus=args.versus,
         )
         if args.trace:
             payload["trace"] = _explore_trace(payload)
         return _emit({"ok": True, "explore": payload}, args)


     def _explore_trace(payload: dict[str, Any]) -> dict[str, Any]:
         if "pipeline_counts" in payload:
             stages: Any = payload["pipeline_counts"]
         else:
             stages = [
                 {"side": side, "stages": payload[side]["pipeline_counts"]} for side in ("a", "b")
             ]
         return {"stages": stages, "rerank": "off"}
     ```

- [ ] Run to pass: `python -m pytest tests/test_cli.py tests/test_explore.py -q` — all passed (including the re-pinned roster).
- [ ] Commit:

  ```bash
  git add src/memoria_vault/cli.py tests/test_cli.py
  git commit -m "feat(cli): memoria explore command — pinned surface roster edit, both-direction help disambiguation vs project explore, --trace baseline" -m "Co-Authored-By: Claude Fable 5 <noreply@anthropic.com>"
  ```

### Task E.3 — honest-empty explore + §9 acceptance wiring (section-final)

**Files:** `src/memoria_vault/runtime/explore.py`, `src/memoria_vault/cli.py`, `tests/test_explore.py`.
**Interfaces:** `payload["honest_empty"]: str` on any explore side with `returned == 0` — the §4 sentence `"0 of <candidates> candidates matched; <n> unchecked documents were not searched"` (candidates = the last filter-stage count before `ranked`, i.e. the denominator the candidate set defines); the CLI text front prints that sentence instead of a bare summary. The slice-4 (honest-empty/ride-through enforcement) section consumes this field for its cross-front tests.

- [ ] Extend `tests/test_explore.py` imports for the CLI-front tests:

  old:
  ```python
  from __future__ import annotations

  from pathlib import Path

  from memoria_vault.runtime import state
  ```
  new:
  ```python
  from __future__ import annotations

  import json
  from pathlib import Path

  import pytest

  from memoria_vault.cli import main
  from memoria_vault.runtime import state
  ```

- [ ] Write the failing honest-empty test — append to `tests/test_explore.py`:

  ```python
  def test_explore_honest_empty_renders_counts_on_text_and_json_fronts(
      tmp_path: Path, capsys: pytest.CaptureFixture[str]
  ) -> None:
      vault = _fixture_vault(tmp_path)
      sentence = "0 of 5 candidates matched; 1 unchecked documents were not searched"

      payload = explore_topic(vault, "zeppelin")

      assert payload["honest_empty"] == sentence
      stage = {row["stage"]: row["count"] for row in payload["pipeline_counts"]}
      assert stage["ranked"] == 0
      assert stage["returned"] == 0
      for group in ("claims", "questions", "tensions", "works", "hubs"):
          assert payload[group] == []
      assert payload["excluded_strata"] == {"unchecked": 1, "stale": 0, "gated": 0}

      rc = main(["explore", "zeppelin", "--workspace", str(vault)])
      assert rc == 0
      assert capsys.readouterr().out.strip() == sentence

      rc = main(["explore", "zeppelin", "--workspace", str(vault), "--json"])
      output = json.loads(capsys.readouterr().out)
      assert rc == 0
      assert output["explore"]["honest_empty"] == sentence
  ```

- [ ] Run: `python -m pytest tests/test_explore.py -q` — expected failure: `KeyError: 'honest_empty'`.
- [ ] Minimal implementation — two edits. In `src/memoria_vault/runtime/explore.py` (`_explore_side`, before the return):

  old:
  ```python
      payload: dict[str, Any] = {
          "topic": topic,
          "depth": depth,
          **groups,
          "pipeline_counts": pipeline_counts,
          "excluded_strata": _excluded_strata(vault, {str(document["path"]) for document in docs}),
      }
      return payload, expanded
  ```
  new:
  ```python
      payload: dict[str, Any] = {
          "topic": topic,
          "depth": depth,
          **groups,
          "pipeline_counts": pipeline_counts,
          "excluded_strata": _excluded_strata(vault, {str(document["path"]) for document in docs}),
      }
      if returned == 0:
          # Honest-empty (§4): never a bare empty list, on every front.
          payload["honest_empty"] = (
              f"0 of {len(candidates)} candidates matched; "
              f"{payload['excluded_strata']['unchecked']} unchecked documents were not searched"
          )
      return payload, expanded
  ```

  In `src/memoria_vault/cli.py` (`_cmd_explore`):

  old:
  ```python
      if args.trace:
          payload["trace"] = _explore_trace(payload)
      return _emit({"ok": True, "explore": payload}, args)
  ```
  new:
  ```python
      if args.trace:
          payload["trace"] = _explore_trace(payload)
      honest_empty = str(payload.get("honest_empty") or "")
      if honest_empty and not args.json and not args.quiet:
          print(honest_empty)
          return 0
      return _emit({"ok": True, "explore": payload}, args)
  ```

- [ ] Run to pass: `python -m pytest tests/test_explore.py -q`.
- [ ] Add the §9 acceptance pin — append to `tests/test_explore.py` (this drives the full fixture through the real CLI: five groups, tension listed, zero-grounds mark, exact ordered counts, per-side versus counts, intersection with the shared work, crossing tension, depth cap named on the CLI front). Expected: **pass immediately** — it pins E.1/E.2 behavior end-to-end; any failure is a defect in those tasks and must be fixed before commit:

  ```python
  def test_cli_explore_acceptance_five_groups_versus_counts_and_depth_cap(
      tmp_path: Path, capsys: pytest.CaptureFixture[str]
  ) -> None:
      vault = _fixture_vault(tmp_path)

      rc = main(["explore", "spacing", "--workspace", str(vault), "--json"])
      output = json.loads(capsys.readouterr().out)
      assert rc == 0
      assert output["ok"] is True
      explore = output["explore"]
      for group in ("claims", "questions", "tensions", "works", "hubs"):
          assert explore[group], f"empty group: {group}"
      assert explore["pipeline_counts"] == [
          {"stage": "universe", "count": 5},
          {"stage": "ranked", "count": 4},
          {"stage": "seed", "count": 4},
          {"stage": "neighborhood", "count": 5},
          {"stage": "returned", "count": 6},
      ]
      assert explore["tensions"][0]["pair"] == [
          "notes/claim-massed.md",
          "notes/claim-spacing.md",
      ]
      thin = next(
          entry for entry in explore["claims"] if entry["id"] == "notes/claim-spacing.md"
      )
      assert thin["grounds_count"] == 0
      assert thin["zero_grounds"] is True

      rc = main(
          ["explore", "spacing", "--versus", "massed", "--workspace", str(vault), "--json"]
      )
      output = json.loads(capsys.readouterr().out)
      assert rc == 0
      versus = output["explore"]
      assert versus["a"]["pipeline_counts"] == [
          {"stage": "universe", "count": 5},
          {"stage": "ranked", "count": 4},
          {"stage": "seed", "count": 4},
          {"stage": "neighborhood", "count": 5},
          {"stage": "returned", "count": 6},
      ]
      assert versus["b"]["pipeline_counts"] == [
          {"stage": "universe", "count": 5},
          {"stage": "ranked", "count": 2},
          {"stage": "seed", "count": 2},
          {"stage": "neighborhood", "count": 3},
          {"stage": "returned", "count": 4},
      ]
      assert versus["a"]["excluded_strata"] == {"unchecked": 1, "stale": 0, "gated": 0}
      assert versus["b"]["excluded_strata"] == {"unchecked": 1, "stale": 0, "gated": 0}
      assert "catalog/sources/settles-2016" in versus["intersection"]["ids"]
      assert versus["intersection"]["count"] == 3
      assert versus["intersection"]["a_count"] == 5
      assert versus["intersection"]["b_count"] == 3
      assert versus["crossing_tensions"]["count"] == 1
      assert versus["crossing_tensions"]["pairs"][0]["pair"] == [
          "notes/claim-massed.md",
          "notes/claim-spacing.md",
      ]

      rc = main(["explore", "spacing", "--depth", "3", "--workspace", str(vault), "--json"])
      refusal = json.loads(capsys.readouterr().out)
      assert rc == 2
      assert refusal["ok"] is False
      assert "hard cap of 2" in refusal["error"]
  ```

- [ ] Run: `python -m pytest tests/test_explore.py tests/test_cli.py -q` — all passed.
- [ ] Section-final gate: `python scripts/verify` — green (the roster gate `test_testing_levels.py` sees `test_explore.py` registered from E.1; the doc-claims gate is unaffected — it only fails on docs citing commands that do not exist, and `memoria explore` now exists).
- [ ] Commit:

  ```bash
  git add src/memoria_vault/runtime/explore.py src/memoria_vault/cli.py tests/test_explore.py
  git commit -m "test(explore): honest-empty sentence on both fronts + R2 §9 acceptance pins (versus per-side counts, zero-grounds, depth cap)" -m "Co-Authored-By: Claude Fable 5 <noreply@anthropic.com>"
  ```
# F — Synthesis contract + fixture preregistration

Implements spec §5 (grounded synthesis + the anchor-locator contract — **the composer itself is R1-gated new work and is not built here**; beta.1 ships the contract tests + refusal honesty) and §7 (retrieval-fixture preregistration: the form, the loader with granularity mapping and `present@depth`, freeze semantics, baseline wiring into `evaluate_bm25`) — slices 5 and 7 of §10. Spec: `docs/superpowers/specs/2026-07-17-r2-retrieval-modes-design.md`. All line refs verified at origin/main `51395f15`; re-anchor by symbol if drifted.

**Ordering and independence.** F has **no** dependency on Plan 22 G2S1.1 or this plan's graph_sql/explore sections: nothing here reads `concept_edges`, and `score_present_at_depth` scores a payload dict, not a live explore run. F may execute at any point in the section order. The one cross-section touch is refusal honesty (F.1c), which consumes section P's §4 honest-empty fields with **both-branch tolerance**: the asserts on `pipeline_counts`/`excluded_strata` fire iff the fields are present in the payload, so F is green whether it lands before or after P (P owns the strict, unconditional assertions of those fields). Grep-first note for the implementer: before running F.1, run `grep -n "excluded_strata" src/memoria_vault/runtime/search_index.py` — a hit means P landed first and both branches of the tolerant asserts will execute; an empty grep means only the shipped-core branch runs. Either way the test code below is used exactly as written.

**Deliberately not built here** (spec §8 + §7's last rule): the extractive composer (R1-gated), any model-synthesis path, and any `scripts/verify` wiring for the freeze check — the loader's own contract test IS the enforcement (spec §7: "enforced by the loader's own contract test, not scripts/verify wiring").

**SPEC GAPS (each resolved inline; none change spec mechanisms):**

1. **Span-ref helper home and return shape.** §5 fixes the resolution *rule* (split on `#`, strip `^`, match `passages` on `(work_id, anchor)`; file-scan interim per state.py:2676-2686) but not the helper's module or shape. Resolution: `src/memoria_vault/runtime/span_refs.py` with `resolve_span_ref(vault, ref) -> {work_id, anchor, path} | None` — runtime, not tests, because the R1 composer (product code) and the fixture loader (repo-side) both consume it; parsing reuses the shipped `parse_source_span_ref` (evidence.py:44-49) rather than reimplementing the syntax.
2. **Loader module home.** §7 fixes the fixtures home (`tests/fixtures/retrieval/*.yaml`) but not the loader's module. Resolution: `tests/retrieval_fixtures.py` (the `tests/helpers.py` precedent) — every consumer (the loader contract test, the R3 spike harness, LOOP.13's measurement) is repo-side, and product code must never read the repo's tests tree.
3. **Freeze date field.** §7 says "`frozen: true`, date recorded" without naming the field. Resolution: `frozen_on: YYYY-MM-DD`, required iff `frozen: true`, loader-enforced.
4. **Shape-2 depth declaration.** §7 scores "at the case's declared depth" but the schema example has no depth field. Resolution: depth is encoded in the metric string `present@N` with N ∈ {1, 2} (explore's hard cap, §3), loader-enforced — a `present@3` row is refused at load, mirroring the CLI's cap rejection.
5. **Explore payload id key for `present@depth`.** The explore section owns the grouped-payload layout. Resolution: `score_present_at_depth` collects every string value under an `"id"` key anywhere in the payload (recursive walk), binding only to the cross-section contract "payload entries carry `id` (the concept id: vault path; `catalog/sources/<work_id>` for works)" — never to group key names, so the explore section's exact layout cannot break F.
6. **The ask allowed-key set.** §5 says the shipped ask "emits no prose at all" and is trivially conformant; the pin needs a concrete key roster. Resolution: the shipped `answer_query` keys (search_index.py:239-249: `query/engine/sources/unknowns/staleness/contradictions` + optional `project_context`) plus the three R2 honesty fields other sections add — `pipeline_counts`, `excluded_strata` (§4, section P), `trace` (§6, the trace section) — so the pin is order-tolerant. Any future composer must widen `ALLOWED_ANSWER_KEYS` in `tests/test_grounded_synthesis.py` in the same change that satisfies §5: that edit is the contract gate.
7. **YAML date scalars.** PyYAML parses the spec form's unquoted `registered: 2026-07-17` into `datetime.date`. Resolution: the loader normalizes `registered`/`frozen_on` to ISO strings; the file keeps the spec's unquoted form.
8. **Seeded gold anchors.** The 2 shape-1 + 1 shape-2 cases are registered-unfrozen preregistration bets over the O1 seed corpus (work ids pinned in `docs/superpowers/plans/2026-07-16-o1-onboarding-seed.md` interface 1; the shape-1 anchors `^p0007`/`^p0004` are bets) — correctable until freeze, per §7's own rule; the wiring test builds its disposable corpus so it never depends on the bets being right.

---

### Task F.1: Grounded-synthesis contract tests + the shared span-ref resolution helper

**Files:**

- Create `src/memoria_vault/runtime/span_refs.py`
- Create `tests/test_grounded_synthesis.py`
- Modify `tests/conftest.py` — `TEST_LEVELS` dict at tests/conftest.py:18 (new test file registration)

**Interfaces:**

- Consumes: `answer_query(vault, query, *, context, k=5, include_stale=False, project_id="") -> dict` (search_index.py:153-177) and `_answer_from_hits` (:211-249, the shipped no-prose payload); `parse_source_span_ref(ref) -> SourceSpanRef(work_id, page)` (evidence.py:44-49); the `passages` table (schema.sql:199-220) via `state.db_path`/`state.connect` (state.py:460-482); `state.catalog_source(vault, work_id)` (state.py:1603-1612); the interim file-scan rule (`_source_span_pages`, state.py:2676-2686 — the rule is mirrored, the private helper is not imported); one-row-per-doc `_passage_row` (indexing.py:101-131) + `rebuild_passage_index_explicit(vault, *, actor, machine)` (indexing.py:25-31) as the test fixture; `safe_filename` (paths.py:15-17); `tests.helpers.call_with_context`/`copy_memoria_dirs`.
- Produces: `resolve_span_ref(vault: Path, ref: str) -> dict[str, str] | None` (keys `work_id`, `anchor`, `path`) in `memoria_vault.runtime.span_refs` — the one resolution rule the R1-gated composer and F.2's fixture loader share; the `ALLOWED_ANSWER_KEYS` pin any future composer must widen through this contract.

- [ ] **Step 1: Write the failing test** — create `tests/test_grounded_synthesis.py`:

```python
"""R2 section-5 grounded-synthesis contract, pinned before any composer exists.

The extractive composer is R1-gated (it needs passage-granular rows and
source-span-anchor); beta.1 ships the contract these tests pin: the ask
payload's allowed keys (any future prose must arrive by widening
ALLOWED_ANSWER_KEYS here, through the contract), the span-ref resolution
rule shared with the retrieval-fixture loader, and refusal honesty - when
nothing grounds, the output is the honest-empty payload, never prose
without anchors.
"""

from __future__ import annotations

from pathlib import Path

from memoria_vault.runtime import indexing, state
from memoria_vault.runtime.policy.audit import sha256_file
from memoria_vault.runtime.search_index import answer_query as _answer_query
from memoria_vault.runtime.span_refs import resolve_span_ref
from tests.helpers import call_with_context, copy_memoria_dirs

WORK_ID = "settles-2016-spaced-repetition"

# The full key set an ask payload may carry. query/engine/sources/unknowns/
# staleness/contradictions/project_context are the shipped answer_query
# contract (search_index.py _answer_from_hits); pipeline_counts and
# excluded_strata are the section-4 denominator fields (section P) and
# trace is the section-6 trace field - listed so this pin is order-tolerant
# against those sections. Composed prose is NOT here: a future composer
# must widen this set in the same change that satisfies section 5 (a
# resolvable span ref on every sentence). That edit is the contract gate.
ALLOWED_ANSWER_KEYS = frozenset(
    {
        "query",
        "engine",
        "sources",
        "unknowns",
        "staleness",
        "contradictions",
        "project_context",
        "pipeline_counts",
        "excluded_strata",
        "trace",
    }
)
ALLOWED_SOURCE_ROW_KEYS = frozenset({"path", "title", "type", "score"})
PROSE_KEYS = frozenset({"answer", "text", "sentences", "synthesis", "composition"})


def answer_query(vault: Path, *args, **kwargs):
    return call_with_context(_answer_query, vault, *args, **kwargs)


def workspace(tmp_path: Path) -> Path:
    copy_memoria_dirs(tmp_path, "schemas")
    return tmp_path


def checked_note(vault: Path, name: str, body: str) -> Path:
    path = vault / "notes" / f"{name}.md"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        f"---\ntype: note\ncheck_status: checked\ntitle: {name}\n---\n{body}\n",
        encoding="utf-8",
    )
    rel = path.relative_to(vault).as_posix()
    state.record_observed_file_edit(
        vault, output_id=rel, concept_type="note", output_sha256=sha256_file(path)
    )
    state.set_concept_verdict(vault, rel, "checked")
    return path


def checked_fulltext_source(vault: Path, work_id: str, text: str) -> Path:
    content = vault / f".memoria/blobs/source-content/{work_id}/full-text/paper.txt"
    content.parent.mkdir(parents=True)
    content.write_text(text, encoding="utf-8")
    state.upsert_catalog_record(
        vault,
        work_id=work_id,
        title="A Trainable Spaced Repetition Model",
        provider_coverage="full",
        text_status="full-text",
        check_status="checked",
        content_path=content.relative_to(vault).as_posix(),
    )
    return content


def test_ask_payload_carries_no_prose_fields_beyond_the_contract(tmp_path: Path) -> None:
    vault = workspace(tmp_path)
    checked_note(vault, "alpha", "alpha retrieval body")

    answer = answer_query(vault, "alpha retrieval")

    assert answer["sources"], "fixture must produce at least one hit"
    assert set(answer) <= ALLOWED_ANSWER_KEYS
    assert PROSE_KEYS.isdisjoint(answer)
    for row in answer["sources"]:
        assert set(row) <= ALLOWED_SOURCE_ROW_KEYS


def test_no_grounding_output_is_the_honest_empty_refusal(tmp_path: Path) -> None:
    vault = workspace(tmp_path)
    checked_note(vault, "alpha", "alpha retrieval body")

    refusal = answer_query(vault, "zzz-absent-topic")

    assert refusal["sources"] == []
    assert refusal["unknowns"] == ["No checked current sources matched: zzz-absent-topic"]
    assert set(refusal) <= ALLOWED_ANSWER_KEYS
    assert PROSE_KEYS.isdisjoint(refusal)
    # Section P's section-4 fields ride through when the denominator
    # contract has landed (both-branch order tolerance; section P owns the
    # strict, unconditional assertions of these fields):
    strata = refusal.get("excluded_strata")
    if strata is not None:
        assert set(strata) == {"unchecked", "stale", "gated"}
    counts = refusal.get("pipeline_counts")
    if counts is not None:
        assert [entry["stage"] for entry in counts[:1]] == ["universe"]


def test_resolve_span_ref_matches_passages_then_falls_back_to_file_scan(
    tmp_path: Path,
) -> None:
    vault = workspace(tmp_path)
    content = checked_fulltext_source(
        vault, WORK_ID, "First finding. ^p0007\n\nSecond finding. ^p0009\n"
    )
    indexing.rebuild_passage_index_explicit(vault, actor="operation", machine="test-machine")

    resolved = {
        "work_id": WORK_ID,
        "anchor": "p0007",
        "path": f"fulltexts/{WORK_ID}.md",
    }
    assert resolve_span_ref(vault, f"{WORK_ID}#^p0007") == resolved
    # Shipped passages are one row per document (indexing.py _passage_row):
    # only the document's first anchor has a row, so ^p0009 resolves via
    # the interim file scan (the state.py _source_span_pages rule).
    assert resolve_span_ref(vault, f"{WORK_ID}#^p0009") == {
        "work_id": WORK_ID,
        "anchor": "p0009",
        "path": f"fulltexts/{WORK_ID}.md",
    }
    assert resolve_span_ref(vault, f"{WORK_ID}#^p0042") is None

    # Deleting the content file removes the file-scan route: ^p0007 must
    # still resolve through its passages row; ^p0009 honestly cannot.
    content.unlink()
    assert resolve_span_ref(vault, f"{WORK_ID}#^p0007") == resolved
    assert resolve_span_ref(vault, f"{WORK_ID}#^p0009") is None


def test_resolve_span_ref_refuses_malformed_and_unknown_refs(tmp_path: Path) -> None:
    vault = workspace(tmp_path)

    assert resolve_span_ref(vault, "no-separator") is None
    assert resolve_span_ref(vault, "work#p0007") is None
    assert resolve_span_ref(vault, "work#^page7") is None
    assert resolve_span_ref(vault, "work#^p007") is None
    assert resolve_span_ref(vault, "ghost-work#^p0007") is None
```

- [ ] **Step 2: Run the test — expect the failure**:

```bash
python3 -m pytest tests/test_grounded_synthesis.py -q
```

Expected failure: collection error, `ModuleNotFoundError: No module named 'memoria_vault.runtime.span_refs'`.

- [ ] **Step 3: Minimal implementation** — create `src/memoria_vault/runtime/span_refs.py`:

```python
"""Source-span ref resolution - the R2 section-5 anchor-locator rule, once.

``work_id#^pNNNN`` is the reference syntax (the shipped
``passages.passage_id`` column is a content hash and keeps its name).
Resolution: split on ``#``, strip ``^`` (via the shipped
``parse_source_span_ref``), match ``passages`` rows on
``(work_id, anchor)``. Shipped passages are one row per document
(``indexing._passage_row``), so only a document's first anchor has a row;
every other anchor resolves through the interim file scan (the
``state._source_span_pages`` rule) until R1's passage-granular rows land.
Shared by the R1-gated extractive composer and the retrieval-fixture
loader - one resolution rule, two consumers.
"""

from __future__ import annotations

import re
from pathlib import Path

from memoria_vault.runtime import state
from memoria_vault.runtime.evidence import parse_source_span_ref
from memoria_vault.runtime.paths import safe_filename
from memoria_vault.runtime.policy.paths import normalize_path

_ANCHOR_RE = re.compile(r"\^p\d{4,}")


def resolve_span_ref(vault: Path, ref: str) -> dict[str, str] | None:
    """Resolve a source-span ref to ``{work_id, anchor, path}``, or None."""
    vault = Path(vault)
    try:
        span = parse_source_span_ref(ref)
    except ValueError:
        return None
    if state.db_path(vault).is_file():
        with state.connect(vault) as conn:
            row = conn.execute(
                """
                SELECT path
                FROM passages
                WHERE work_id = ? AND anchor = ?
                ORDER BY path
                LIMIT 1
                """,
                (span.work_id, span.page),
            ).fetchone()
        if row is not None:
            return {"work_id": span.work_id, "anchor": span.page, "path": str(row["path"])}
    return _file_scan_resolution(vault, span.work_id, span.page)


def _file_scan_resolution(vault: Path, work_id: str, anchor: str) -> dict[str, str] | None:
    """Interim resolution: scan the work's content file for the anchor."""
    source = state.catalog_source(vault, work_id)
    if source is None:
        return None
    content_path = vault / normalize_path(str(source.get("content_path") or ""))
    if not content_path.is_file():
        return None
    anchors = {
        match.removeprefix("^")
        for match in _ANCHOR_RE.findall(content_path.read_text(encoding="utf-8"))
    }
    if anchor not in anchors:
        return None
    return {
        "work_id": work_id,
        "anchor": anchor,
        "path": f"fulltexts/{safe_filename(work_id)}.md",
    }
```

- [ ] **Step 4: Register the new test file** — in `tests/conftest.py`, edit the `TEST_LEVELS` dict:

old:

```python
    "test_gate_calibration.py": "unit",
    "test_hub_handoff.py": "contract",
```

new:

```python
    "test_gate_calibration.py": "unit",
    "test_grounded_synthesis.py": "contract",
    "test_hub_handoff.py": "contract",
```

- [ ] **Step 5: Run to pass**:

```bash
python3 -m pytest tests/test_grounded_synthesis.py tests/test_testing_levels.py -q
```

Expected: all tests pass.

- [ ] **Step 6: Commit (explicit paths only)**:

```bash
git add src/memoria_vault/runtime/span_refs.py tests/test_grounded_synthesis.py tests/conftest.py
git commit -m "R2 F.1: grounded-synthesis contract tests + shared span-ref resolution (spec section 5)" -m "Co-Authored-By: Claude Fable 5 <noreply@anthropic.com>"
```

---

### Task F.2: The preregistration fixture form, loader, and baseline wiring

**Files:**

- Create `tests/fixtures/retrieval/cases.yaml` (the seeded 2 shape-1 + 1 shape-2 registered-unfrozen cases)
- Create `tests/retrieval_fixtures.py` (loader + granularity mapping + `present@depth` scorer)
- Create `tests/test_retrieval_fixtures.py`
- Modify `tests/conftest.py` — `TEST_LEVELS` dict at tests/conftest.py:18

**Interfaces:**

- Consumes: `resolve_span_ref` (F.1); `parse_source_span_ref` (evidence.py:44-49, load-time gold validation); `evaluate_bm25(vault, cases, *, k=5) -> dict` (search_index.py:344-376, case shape `{"query": str, "relevant": [paths]}`); `checked_search_documents`/`_checked_work_documents` (search_index.py:115-131, :425-480 — `fulltexts/<work_id>.md` by construction); `state.upsert_catalog_record` (state.py:1510); `yaml.safe_load` (PyYAML, pyproject.toml:15); the O1 seed-corpus work ids (`docs/superpowers/plans/2026-07-16-o1-onboarding-seed.md` interface 1). `evaluate_fixture` (retrieval.py:122-145) needs no wiring here: it already consumes the same `{query, relevant}` case shape via `evaluate_bm25`, so `shape1_bm25_cases` output feeds both evaluators unchanged.
- Produces: `load_retrieval_fixtures(*, spike_mode: bool = False) -> list[dict[str, Any]]`; `validate_retrieval_fixture_rows(rows: list[Any], *, source: str = "<memory>") -> list[dict[str, Any]]`; `shape1_bm25_cases(vault: Path, cases: list[dict[str, Any]]) -> list[dict[str, Any]]`; `score_present_at_depth(payload: dict[str, Any], gold_ids: list[str]) -> bool`; `FIXTURES_DIR`; the fixture row form `{id, shape, query, gold, metric, registered, frozen[, frozen_on]}` the R3 spike and LOOP.13 consume.

- [ ] **Step 1: Write the failing test** — create `tests/test_retrieval_fixtures.py`:

```python
"""Contract tests for the R2 section-7 retrieval-fixture preregistration form.

The loader IS the R3 impl-start check: it refuses unfrozen rows in spike
mode. Granularity mapping is pinned here too - Shape-1 span-ref gold maps
to containing-document paths for evaluate_bm25 (the baseline metric is
document-level hit@k until R1's passage-granular rows land, stated, never
silently degraded), and Shape-2 scores as present@depth membership over a
grouped explore payload.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

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
```

- [ ] **Step 2: Run the test — expect the failure**:

```bash
python3 -m pytest tests/test_retrieval_fixtures.py -q
```

Expected failure: collection error, `ModuleNotFoundError: No module named 'tests.retrieval_fixtures'`.

- [ ] **Step 3: Minimal implementation, part 1** — create `tests/fixtures/retrieval/cases.yaml`:

```yaml
# Preregistered retrieval fixtures - R2 section 7, the R3 spike's
# impl-start check. Rules (the spec's, enforced by
# tests/retrieval_fixtures.py, not scripts/verify wiring):
# - Rows freeze before the R3 spike runs (frozen: true + frozen_on date);
#   the spike may not add, drop, or edit frozen cases; the loader refuses
#   unfrozen rows in spike mode.
# - Shape-1 gold are source-span refs (work_id#^pNNNN). Until R1's
#   passage-granular rows land they are scored at DOCUMENT level: the
#   loader maps each ref to its containing document path for
#   evaluate_bm25, so the baseline metric is doc-level hit@k - stated
#   here, never silently degraded.
# - Shape-2 gold are concept ids scored as present@<depth> over the
#   memoria explore grouped payload (depth cap 2).
# - Gold anchors on unfrozen rows are preregistration bets over the O1
#   seed corpus and may be corrected until freeze.
- id: shape1-spacing-effect-lookup
  shape: 1
  query: "what did the spaced-repetition model find about lag effects"
  gold: ["settles-2016-spaced-repetition#^p0007"]
  metric: hit@5
  registered: 2026-07-17
  frozen: false
- id: shape1-undesirable-difficulty-boundary
  shape: 1
  query: "when do desirable difficulties reverse for high element interactivity material"
  gold: ["chen-2018-undesirable-difficulty#^p0004"]
  metric: hit@5
  registered: 2026-07-17
  frozen: false
- id: shape2-testing-effect-tension
  shape: 2
  query: "testing effect boundary conditions"
  gold:
    - catalog/sources/chen-2018-undesirable-difficulty
    - catalog/sources/moreira-2019-retrieval-practice
  metric: present@1
  registered: 2026-07-17
  frozen: false
```

- [ ] **Step 4: Minimal implementation, part 2** — create `tests/retrieval_fixtures.py`:

```python
"""Preregistered retrieval-fixture loader (R2 section 7).

tests/fixtures/retrieval/*.yaml is the preregistration form for the R3
spike and LOOP.13's Shape-1/2 measurement corpus - one form, two
consumers. Shape-1 gold are source-span refs scored at document level
(hit@k) until R1's passage-granular rows land; Shape-2 gold are concept
ids scored as present@depth over an explore payload (depth encoded in the
metric string, cap 2). The loader refuses unfrozen rows in spike mode -
the R3 impl-start check, enforced by this module's own contract test.
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any

import yaml

from memoria_vault.runtime.evidence import parse_source_span_ref
from memoria_vault.runtime.span_refs import resolve_span_ref

FIXTURES_DIR = Path(__file__).resolve().parent / "fixtures" / "retrieval"

_REQUIRED_KEYS = frozenset({"id", "shape", "query", "gold", "metric", "registered", "frozen"})
_OPTIONAL_KEYS = frozenset({"frozen_on"})
_DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")
_SHAPE1_METRIC_RE = re.compile(r"^(hit|recall)@[1-9]\d*$")
_SHAPE2_METRIC_RE = re.compile(r"^present@[12]$")  # explore's hard depth cap is 2


def load_retrieval_fixtures(*, spike_mode: bool = False) -> list[dict[str, Any]]:
    """Load every registered fixture; in spike mode, refuse any unfrozen row."""
    rows: list[dict[str, Any]] = []
    for path in sorted(FIXTURES_DIR.glob("*.yaml")):
        loaded = yaml.safe_load(path.read_text(encoding="utf-8")) or []
        if not isinstance(loaded, list):
            raise ValueError(f"retrieval fixture file must be a list of cases: {path.name}")
        rows.extend(validate_retrieval_fixture_rows(loaded, source=path.name))
    ids = [str(row["id"]) for row in rows]
    duplicates = sorted({case_id for case_id in ids if ids.count(case_id) > 1})
    if duplicates:
        raise ValueError(f"duplicate retrieval fixture id(s): {duplicates}")
    if spike_mode:
        unfrozen = [str(row["id"]) for row in rows if not row["frozen"]]
        if unfrozen:
            raise ValueError(
                f"spike mode refuses unfrozen retrieval fixtures (freeze first): {unfrozen}"
            )
    return rows


def validate_retrieval_fixture_rows(
    rows: list[Any], *, source: str = "<memory>"
) -> list[dict[str, Any]]:
    """Validate the registered form; return normalized rows (dates as ISO strings)."""
    validated: list[dict[str, Any]] = []
    for row in rows:
        if not isinstance(row, dict):
            raise ValueError(f"{source}: fixture case must be a mapping, got: {row!r}")
        case_id = str(row.get("id") or "")
        missing = sorted(_REQUIRED_KEYS - set(row))
        unknown = sorted(set(row) - _REQUIRED_KEYS - _OPTIONAL_KEYS)
        if missing or unknown or not case_id:
            raise ValueError(
                f"{source}: case {case_id or '<no id>'}: missing {missing}, unknown {unknown}"
            )
        shape = row["shape"]
        if shape not in (1, 2):
            raise ValueError(f"{source}: {case_id}: shape must be 1 or 2, got: {shape!r}")
        query = str(row["query"] or "").strip()
        if not query:
            raise ValueError(f"{source}: {case_id}: query must be nonblank")
        gold = row["gold"]
        if (
            not isinstance(gold, list)
            or not gold
            or not all(isinstance(item, str) and item.strip() for item in gold)
        ):
            raise ValueError(f"{source}: {case_id}: gold must be a nonempty list of refs/ids")
        metric = str(row["metric"] or "")
        metric_re = _SHAPE1_METRIC_RE if shape == 1 else _SHAPE2_METRIC_RE
        if not metric_re.fullmatch(metric):
            raise ValueError(f"{source}: {case_id}: metric {metric!r} is invalid for shape {shape}")
        if shape == 1:
            for ref in gold:
                parse_source_span_ref(ref)  # raises ValueError naming the bad ref
        registered = str(row["registered"])
        if not _DATE_RE.fullmatch(registered):
            raise ValueError(f"{source}: {case_id}: registered must be YYYY-MM-DD")
        frozen = row["frozen"]
        if not isinstance(frozen, bool):
            raise ValueError(f"{source}: {case_id}: frozen must be a bool")
        frozen_on = str(row.get("frozen_on") or "")
        if frozen and not _DATE_RE.fullmatch(frozen_on):
            raise ValueError(f"{source}: {case_id}: frozen rows must record frozen_on (YYYY-MM-DD)")
        if not frozen and frozen_on:
            raise ValueError(f"{source}: {case_id}: frozen_on requires frozen: true")
        normalized: dict[str, Any] = {
            "id": case_id,
            "shape": shape,
            "query": query,
            "gold": [str(item) for item in gold],
            "metric": metric,
            "registered": registered,
            "frozen": frozen,
        }
        if frozen_on:
            normalized["frozen_on"] = frozen_on
        validated.append(normalized)
    return validated


def shape1_bm25_cases(vault: Path, cases: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Map Shape-1 gold span refs to containing-document paths for evaluate_bm25.

    Interim granularity, stated: until R1's passage-granular rows land the
    baseline metric is document-level hit@k - the span ref names the gold
    passage, the scoreable unit is its containing document
    (fulltexts/<work_id>.md by construction). An unresolvable gold ref
    fails loud; preregistered gold is never silently degraded.
    """
    mapped: list[dict[str, Any]] = []
    for case in cases:
        if case["shape"] != 1:
            continue
        relevant = []
        for ref in case["gold"]:
            resolved = resolve_span_ref(vault, ref)
            if resolved is None:
                raise ValueError(f"{case['id']}: gold span ref does not resolve: {ref}")
            relevant.append(resolved["path"])
        mapped.append({"query": case["query"], "relevant": relevant})
    return mapped


def score_present_at_depth(payload: dict[str, Any], gold_ids: list[str]) -> bool:
    """present@depth: every gold id appears somewhere in the grouped payload.

    The caller runs explore at the case's declared depth (parsed from the
    metric string) and passes the returned payload; explore returns
    non-truncating kind groups, so set membership - not list rank - is the
    honest metric. Ids are collected from every "id" key in the payload,
    binding to the cross-section contract (entries carry their concept id)
    rather than to the payload's group key names.
    """
    found: set[str] = set()
    _collect_ids(payload, found)
    return set(gold_ids) <= found


def _collect_ids(node: object, found: set[str]) -> None:
    if isinstance(node, dict):
        value = node.get("id")
        if isinstance(value, str):
            found.add(value)
        for child in node.values():
            _collect_ids(child, found)
    elif isinstance(node, list):
        for child in node:
            _collect_ids(child, found)
```

- [ ] **Step 5: Register the new test file** — in `tests/conftest.py`, edit the `TEST_LEVELS` dict:

old:

```python
    "test_refresh_test_vault.py": "package",
    "test_retrieval_substrate.py": "contract",
```

new:

```python
    "test_refresh_test_vault.py": "package",
    "test_retrieval_fixtures.py": "contract",
    "test_retrieval_substrate.py": "contract",
```

- [ ] **Step 6: Run to pass**:

```bash
python3 -m pytest tests/test_retrieval_fixtures.py tests/test_testing_levels.py -q
```

Expected: all tests pass.

- [ ] **Step 7: Section-final gate**:

```bash
python scripts/verify
```

Expected: `verify: OK` (ruff/ruff-format cover the two new Python files; yamllint covers `cases.yaml` — the relaxed profile with line-length disabled; cspell scopes to `**/*.md` only, so no dictionary changes are needed).

- [ ] **Step 8: Commit (explicit paths only)**:

```bash
git add tests/retrieval_fixtures.py tests/fixtures/retrieval/cases.yaml tests/test_retrieval_fixtures.py tests/conftest.py
git commit -m "R2 F.2: retrieval-fixture preregistration form, loader, and baseline wiring (spec section 7)" -m "Co-Authored-By: Claude Fable 5 <noreply@anthropic.com>"
```