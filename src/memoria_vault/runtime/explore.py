"""Pure-read Shape-2 topic surfacing for ``memoria explore``."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from memoria_vault.runtime import graph_sql, retrieval_pipeline, state
from memoria_vault.runtime.policy.paths import normalize_path
from memoria_vault.runtime.search_index import _bm25, _tokens, checked_search_universe

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
    trace: bool = False,
) -> dict[str, Any]:
    """Surface a topic from the checked universe without emitting telemetry."""
    if depth < 1:
        raise ValueError(f"explore depth must be at least 1: got {depth}")
    if depth > DEPTH_CAP:
        raise ValueError(f"explore depth {depth} exceeds the hard cap of {DEPTH_CAP}")

    vault = Path(vault)
    universe = checked_search_universe(vault, enqueue_scan=False)
    documents = list(universe["documents"])
    strata = dict(universe["excluded_strata"])
    displayable = _displayable_documents(documents)

    if not versus:
        payload, _ids, seed_hits = _explore_side(
            vault,
            topic,
            documents=documents,
            displayable=displayable,
            strata=strata,
            project=project,
            depth=depth,
        )
        if trace:
            payload["trace"] = retrieval_pipeline.build_trace(payload["pipeline_counts"], seed_hits)
        return payload

    side_a, ids_a, seed_hits_a = _explore_side(
        vault,
        topic,
        documents=documents,
        displayable=displayable,
        strata=strata,
        project=project,
        depth=depth,
    )
    side_b, ids_b, seed_hits_b = _explore_side(
        vault,
        versus,
        documents=documents,
        displayable=displayable,
        strata=strata,
        project=project,
        depth=depth,
    )
    titles = _payload_titles(side_a) | _payload_titles(side_b)
    shared = sorted(ids_a & ids_b)
    crossing = _tension_pairs(vault, ids_a, ids_b, titles)
    payload = {
        "topic": topic,
        "versus": versus,
        "a": side_a,
        "b": side_b,
        "intersection": {
            "ids": shared,
            "count": len(shared),
            "a_count": len(ids_a),
            "b_count": len(ids_b),
        },
        "crossing_tensions": {"pairs": crossing, "count": len(crossing)},
    }
    if trace:
        payload["trace"] = {
            "a": retrieval_pipeline.build_trace(side_a["pipeline_counts"], seed_hits_a),
            "b": retrieval_pipeline.build_trace(side_b["pipeline_counts"], seed_hits_b),
        }
    return payload


def _explore_side(
    vault: Path,
    topic: str,
    *,
    documents: list[dict[str, Any]],
    displayable: list[dict[str, Any]],
    strata: dict[str, Any],
    project: str,
    depth: int,
) -> tuple[dict[str, Any], set[str], list[tuple[str, float]]]:
    stages = retrieval_pipeline.PipelineStages(len(documents))
    stages.add_filter("displayable-kind", len(displayable))
    candidates = displayable
    if project:
        project_ids = _vetted_project_slice_ids(vault, project, documents)
        candidates = [document for document in candidates if _concept_id(document) in project_ids]
        stages.add_filter("project-slice", len(candidates))

    by_id = {_concept_id(document): document for document in candidates}
    ranked = _bm25(
        [(concept_id, _tokens(str(document["text"]))) for concept_id, document in by_id.items()],
        topic,
    )
    stages.add_ranked(len(ranked))
    seed_hits = [
        (str(concept_id), float(score))
        for concept_id, score in retrieval_pipeline.rerank(ranked[:SEED_K])
    ]
    seed_scores = dict(seed_hits)
    seed_ids = set(seed_scores)
    expanded = set(seed_ids)
    if seed_ids:
        expanded = {
            str(concept_id)
            for concept_id in graph_sql.neighborhood(vault, sorted(seed_ids), depth=depth)["ids"]
        }
    returned_ids = expanded & set(by_id)

    stages.add_returned(len(returned_ids))
    pipeline_counts = stages.rows()
    pipeline_counts[-1:-1] = [
        {"stage": "seed", "count": len(seed_ids)},
        {"stage": "neighborhood", "count": len(returned_ids)},
    ]

    titles = {concept_id: _title(document) for concept_id, document in by_id.items()}
    edges_by_id = _edges_by_concept(vault, returned_ids)
    grounds = _complete_grounds_by_claim(vault)
    groups: dict[str, list[dict[str, Any]]] = {group: [] for group in KIND_GROUPS}
    for concept_id in sorted(returned_ids):
        document = by_id[concept_id]
        kind = _kind(document)
        entry: dict[str, Any] = {
            "id": concept_id,
            "title": titles[concept_id],
            "seed_score": seed_scores.get(concept_id, 0.0),
            "edges": edges_by_id.get(concept_id, []),
        }
        if kind == "claims":
            grounds_count = grounds.get(concept_id, 0)
            entry["grounds_count"] = grounds_count
            entry["zero_grounds"] = grounds_count == 0
        groups[kind].append(entry)
    for group in ("claims", "questions", "works", "hubs"):
        groups[group].sort(key=_entry_order)
    groups["tensions"] = _tension_pairs(vault, returned_ids, returned_ids, titles)

    payload: dict[str, Any] = {
        "topic": topic,
        "depth": depth,
        **groups,
        "pipeline_counts": pipeline_counts,
        "excluded_strata": dict(strata),
    }
    if not returned_ids:
        payload["honest_empty"] = retrieval_pipeline.honest_empty(pipeline_counts, strata)
    safe_seed_hits = [
        (concept_id, score) for concept_id, score in seed_hits if concept_id in returned_ids
    ]
    return payload, returned_ids, safe_seed_hits


def _displayable_documents(documents: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Filter pre-rank to Shape-2 kinds, keeping one document per concept id."""
    displayable: list[dict[str, Any]] = []
    seen: set[str] = set()
    for document in documents:
        if not _kind(document):
            continue
        concept_id = _concept_id(document)
        if concept_id in seen:
            continue
        seen.add(concept_id)
        displayable.append(document)
    return displayable


def _concept_id(document: dict[str, Any]) -> str:
    path = str(document["path"])
    frontmatter = _frontmatter(document)
    if str(frontmatter.get("type") or "") == "fulltext" or path.startswith("fulltexts/"):
        work_id = str(frontmatter.get("work_id") or Path(path).stem)
        return f"catalog/sources/{work_id}"
    return path


def _kind(document: dict[str, Any]) -> str:
    frontmatter = _frontmatter(document)
    concept_type = str(frontmatter.get("type") or "")
    mode = str(frontmatter.get("mode") or "")
    if concept_type == "note" and mode == "claim":
        return "claims"
    if concept_type == "note" and mode == "question":
        return "questions"
    if concept_type == "hub":
        return "hubs"
    if concept_type in {"work", "digest", "fulltext"}:
        return "works"
    return ""


def _frontmatter(document: dict[str, Any]) -> dict[str, Any]:
    frontmatter = document.get("frontmatter")
    return frontmatter if isinstance(frontmatter, dict) else {}


def _title(document: dict[str, Any]) -> str:
    return str(_frontmatter(document).get("title") or Path(str(document["path"])).stem)


def _entry_order(entry: dict[str, Any]) -> tuple[float, str, str]:
    return (-float(entry["seed_score"]), str(entry["title"]), str(entry["id"]))


def _edges_by_concept(vault: Path, ids: set[str]) -> dict[str, list[dict[str, str]]]:
    """Return only safe, displayed edges, treated as undirected for presentation."""
    # Mixed key spaces: `source_concept_id` is identity space, `target_path` is
    # path space, and both are matched against one `ids` set. Correct only while
    # file Concepts key by path; NID-B.2's ULIDs break the coincidence and ERP-A.6
    # owns the identity-safe path projection this should read.
    touching: dict[str, set[tuple[str, str]]] = {concept_id: set() for concept_id in ids}
    for edge in state.concept_edges(vault):
        source = str(edge["source_concept_id"])
        target = str(edge["target_path"])
        if source not in ids or target not in ids:
            continue
        relation = str(edge["relation_type"])
        touching[source].add((relation, target))
        touching[target].add((relation, source))
    return {
        concept_id: [
            {"relation_type": relation, "target": target} for relation, target in sorted(pairs)
        ]
        for concept_id, pairs in touching.items()
    }


def _tension_pairs(
    vault: Path,
    left_ids: set[str],
    right_ids: set[str],
    titles: dict[str, str],
) -> list[dict[str, Any]]:
    """Return deduplicated tension pairs whose endpoints are both safe ids."""
    # Mixed key spaces: `source_concept_id` is identity space, `target_path` is
    # path space, and both are matched against `safe_ids`. Correct only while file
    # Concepts key by path; ERP-A.6 owns the projection that survives NID-B.2.
    safe_ids = left_ids | right_ids
    pairs: dict[tuple[str, str], dict[str, Any]] = {}
    for edge in state.concept_edges(vault):
        if str(edge["relation_type"]) != "tension":
            continue
        source = str(edge["source_concept_id"])
        target = str(edge["target_path"])
        if source not in safe_ids or target not in safe_ids:
            continue
        crosses = (source in left_ids and target in right_ids) or (
            source in right_ids and target in left_ids
        )
        if not crosses:
            continue
        pair = tuple(sorted((source, target)))
        pairs[pair] = {
            "pair": list(pair),
            "titles": [titles[pair[0]], titles[pair[1]]],
            "relation_type": "tension",
        }
    return [pairs[pair] for pair in sorted(pairs)]


def _complete_grounds_by_claim(vault: Path) -> dict[str, int]:
    grounds: dict[str, int] = {}
    for evidence_set in state.evidence_sets(vault):
        if str(evidence_set.get("state") or "") != "complete":
            continue
        claim_path = str(evidence_set.get("block_ref") or "").partition("#")[0]
        if claim_path:
            grounds[claim_path] = grounds.get(claim_path, 0) + 1
    return grounds


def _vetted_project_slice_ids(
    vault: Path, project: str, documents: list[dict[str, Any]]
) -> set[str]:
    """Use active slices or traverse links using only vetted frontmatter."""
    by_path = {str(document["path"]): document for document in documents}
    project_rel = _vetted_project_rel(vault, project)
    project_document = by_path.get(project_rel)
    if project_document is None:
        return set()

    active_slices = graph_sql._active_project_slices(vault)
    if active_slices is not None:
        return {
            _active_member_id(member)
            for member in active_slices.get(project_rel, set())
            if _active_member_id(member)
        }

    seen: set[str] = set()
    queue = sorted(_link_targets(_frontmatter(project_document)))
    thesis = _link_target(_frontmatter(project_document).get("thesis"))
    if thesis:
        queue.append(thesis)
    while queue:
        relpath = queue.pop(0)
        if relpath in seen:
            continue
        seen.add(relpath)
        document = by_path.get(relpath)
        if document is not None:
            queue.extend(sorted(_link_targets(_frontmatter(document)) - seen))
    return seen


def _vetted_project_rel(vault: Path, project: str) -> str:
    relpath = normalize_path(str(project))
    if "/" not in relpath:
        nested = f"projects/{relpath}/project.md"
        return nested if (Path(vault) / nested).is_file() else f"projects/{relpath}.md"
    if not relpath.endswith(".md"):
        relpath += ".md"
    if not relpath.startswith("projects/"):
        raise ValueError(f"project must live under projects: {relpath}")
    return relpath


def _active_member_id(member: object) -> str:
    if isinstance(member, dict):
        member = member.get("concept_id") or member.get("path") or member.get("id") or ""
    text = str(member).strip()
    if not text:
        return ""
    try:
        return normalize_path(text)
    except ValueError:
        return ""


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


def _link_target(value: object) -> str:
    if isinstance(value, dict):
        value = value.get("target") or value.get("path") or value.get("id") or value.get("note")
    if not isinstance(value, str) or not value.strip():
        return ""
    raw = value.strip()
    if raw.startswith("[[") and raw.endswith("]]"):
        raw = raw[2:-2].split("|", 1)[0].split("#", 1)[0].strip()
    try:
        relpath = normalize_path(raw)
    except ValueError:
        return ""
    if "/" not in relpath:
        relpath = f"notes/{relpath}"
    if relpath.startswith("catalog/sources/"):
        relpath = relpath.rstrip("/")
        if relpath.count("/") != 2:
            return ""
    elif not relpath.endswith(".md"):
        relpath += ".md"
    if not relpath.startswith(("catalog/sources/", "notes/", "hubs/", "digests/", "fulltexts/")):
        return ""
    return relpath


def _payload_titles(payload: dict[str, Any]) -> dict[str, str]:
    return {
        str(entry["id"]): str(entry["title"])
        for group in ("claims", "questions", "works", "hubs")
        for entry in payload[group]
    }
