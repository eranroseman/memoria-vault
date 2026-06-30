"""Alpha.11 note-candidate and gap-analysis helpers."""

from __future__ import annotations

import hashlib
import json
from collections import defaultdict
from collections.abc import Iterable
from pathlib import Path
from typing import Any

from memoria_vault.runtime.operations import load_operation_policy, required_promotion_checks
from memoria_vault.runtime.paths import safe_filename
from memoria_vault.runtime.policy.audit import sha256_file
from memoria_vault.runtime.policy.paths import normalize_path
from memoria_vault.runtime.trusted_writer import (
    append_journal_event,
    commit_writer_changes,
    promote_checked,
    stage_concept,
)
from memoria_vault.runtime.vaultio import (
    concept_text,
    iter_markdown,
    read_frontmatter,
    split_frontmatter,
    write_frontmatter_doc,
)


def emit_note_candidates(
    vault: Path,
    digest_path: str,
    candidates: Iterable[dict[str, Any]],
    *,
    operation_id: str = "propose-note-candidates",
    machine: str | None = None,
    run_id: str | None = None,
) -> dict[str, Any]:
    """Promote checked note candidates derived from one checked digest."""
    vault = Path(vault)
    policy = load_operation_policy(vault, operation_id)
    _require_tool(policy, "trusted_writer")
    promotion_checks = required_promotion_checks(policy)

    digest_rel = _digest_rel(digest_path)
    _require_path(policy, digest_rel)
    digest_fm = _checked_frontmatter(vault, digest_rel, "digest")
    rows = list(candidates)
    if not rows:
        raise ValueError("at least one note candidate is required")

    run_id = run_id or f"{operation_id}:{Path(digest_rel).stem}"
    started = append_journal_event(
        vault,
        {"event": "run", "run_id": run_id, "workflow": operation_id, "status": "started"},
        machine=machine,
    )
    model_call = append_journal_event(
        vault,
        {
            "event": "model_call",
            "run_id": run_id,
            "runner": policy["runner"],
            "provider": policy.get("provider", "local"),
            "model": policy["model"],
            "route": policy.get("route", "note-candidates"),
            "purpose": "note_candidates",
            "prompt_version": policy["prompt_version"],
            "toolset": policy["allowed_tools"],
            "fallback_used": False,
            "compression_used": False,
            "input_hash": sha256_file(vault / digest_rel),
            "output_hash": _sha256_text(repr(rows)),
        },
        machine=machine,
    )

    staged = []
    checked = []
    note_paths = []
    for row in rows:
        title = _required_text(row, "title")
        body = _required_text(row, "body")
        note_rel = _unique_note_rel(vault, title)
        _require_path(policy, note_rel)
        frontmatter = {
            "type": "note",
            "check_status": "unchecked",
            "title": title,
            "status": "candidate",
            "source_id": row.get("source_id") or digest_fm.get("source_id"),
            "evidence_set": row.get("evidence_set") or digest_fm.get("evidence_set") or [],
            "extraction_confidence": str(row.get("extraction_confidence") or "medium"),
            "tags": _string_list(row.get("tags")),
        }
        if row.get("description"):
            frontmatter["description"] = str(row["description"])
        if row.get("claim_text"):
            frontmatter["claim_text"] = str(row["claim_text"])
        if row.get("quote"):
            frontmatter["quote"] = str(row["quote"])
        if isinstance(row.get("annotation_ref"), dict):
            frontmatter["annotation_ref"] = dict(row["annotation_ref"])
        citations = row.get("citations") or digest_fm.get("citations")
        if isinstance(citations, list):
            frontmatter["citations"] = [dict(item) for item in citations if isinstance(item, dict)]

        stage = stage_concept(
            vault,
            note_rel,
            concept_text(frontmatter, title, body),
            inputs=[{"id": digest_rel, "sha256": sha256_file(vault / digest_rel)}],
            operation=operation_id,
            run_id=run_id,
            machine=machine,
        )
        check = promote_checked(vault, note_rel, checks=promotion_checks, machine=machine)
        staged.append(stage)
        checked.append(check)
        note_paths.append(note_rel)

    finished = append_journal_event(
        vault,
        {
            "event": "run",
            "run_id": run_id,
            "workflow": operation_id,
            "status": "done",
            "outputs": note_paths,
        },
        machine=machine,
    )
    commit = commit_writer_changes(
        vault, f"propose notes {Path(digest_rel).stem}", note_paths, machine=machine
    )
    return {
        "run_id": run_id,
        "note_paths": note_paths,
        "started": started,
        "model_call": model_call,
        "derived": staged,
        "checked": checked,
        "finished": finished,
        "commit": commit,
    }


def curate_note_candidate(
    vault: Path,
    note_path: str,
    status: str,
    *,
    reason: str = "",
    machine: str | None = None,
) -> dict[str, Any]:
    """Record PI acceptance or rejection of a checked candidate note."""
    vault = Path(vault)
    note_rel = _note_rel(note_path)
    status = status.strip().lower()
    if status not in {"accepted", "rejected"}:
        raise ValueError("note candidate status must be accepted or rejected")

    note = vault / note_rel
    if not note.is_file():
        raise FileNotFoundError(note)
    frontmatter, body = split_frontmatter(note.read_text(encoding="utf-8"))
    if frontmatter.get("type") != "note" or frontmatter.get("check_status") != "checked":
        raise ValueError(f"{note_rel} is not a checked note")
    if frontmatter.get("status") != "candidate":
        raise ValueError(f"{note_rel} is not a candidate note")

    frontmatter["status"] = status
    write_frontmatter_doc(note, frontmatter, body)
    event = append_journal_event(
        vault,
        {
            "event": "resolved",
            "actor": "pi",
            "operation": "curate-note-candidate",
            "target_id": note_rel,
            "target_sha256": sha256_file(note),
            "resolution": status,
            "reason": reason.strip(),
        },
        machine=machine,
    )
    commit = commit_writer_changes(
        vault, f"{status} note candidate {Path(note_rel).stem}", [note_rel], machine=machine
    )
    return {"note_path": note_rel, "status": status, "event": event, "commit": commit}


def curate_note_link(
    vault: Path,
    source_note_path: str,
    link_type: str,
    target_path: str,
    *,
    reason: str = "",
    machine: str | None = None,
) -> dict[str, Any]:
    """Record one PI-authored typed link on a checked note."""
    vault = Path(vault)
    source_rel = _note_rel(source_note_path)
    target_rel = _concept_rel(target_path)
    link_type = link_type.strip().lower()
    if link_type not in {"supports", "contradicts", "extends"}:
        raise ValueError("note link_type must be supports, contradicts, or extends")

    source_note = vault / source_rel
    if not source_note.is_file():
        raise FileNotFoundError(source_note)
    frontmatter, body = split_frontmatter(source_note.read_text(encoding="utf-8"))
    if frontmatter.get("type") != "note" or frontmatter.get("check_status") != "checked":
        raise ValueError(f"{source_rel} is not a checked note")
    _checked_concept(vault, target_rel)

    links = frontmatter.get("links")
    if links is None:
        links = {}
    if not isinstance(links, dict):
        raise ValueError(f"{source_rel} links must be a map")
    bucket = links.setdefault(link_type, [])
    if not isinstance(bucket, list):
        raise ValueError(f"{source_rel} links.{link_type} must be a list")
    changed = target_rel not in bucket
    if changed:
        bucket.append(target_rel)
        frontmatter["links"] = links
        write_frontmatter_doc(source_note, frontmatter, body)

    event = append_journal_event(
        vault,
        {
            "event": "resolved",
            "actor": "pi",
            "operation": "curate-note-link",
            "target_id": source_rel,
            "linked_id": target_rel,
            "link_type": link_type,
            "target_sha256": sha256_file(source_note),
            "changed": changed,
            "reason": reason.strip(),
        },
        machine=machine,
    )
    commit = commit_writer_changes(
        vault, f"link note {Path(source_rel).stem}", [source_rel], machine=machine
    )
    return {
        "source_note_path": source_rel,
        "target_path": target_rel,
        "link_type": link_type,
        "changed": changed,
        "event": event,
        "commit": commit,
    }


def analyze_gaps(
    vault: Path,
    *,
    seed_terms: Iterable[str] = (),
    dense_threshold: int = 2,
) -> dict[str, Any]:
    """Classify simple source/note topic mismatches over checked Concepts."""
    counts: dict[str, dict[str, int]] = defaultdict(
        lambda: {"sources": 0, "digests": 0, "notes": 0}
    )
    labels: dict[str, str] = {}
    for rel, frontmatter in _checked_concepts(Path(vault)):
        bucket = _bucket(rel, frontmatter)
        if not bucket:
            continue
        for term in _terms(frontmatter):
            key = term.lower()
            counts[key][bucket] += 1
            labels.setdefault(key, term)
    for term in seed_terms:
        label = " ".join(str(term).split())
        if label:
            labels.setdefault(label.lower(), label)
            counts[label.lower()]

    gaps = []
    for key in sorted(counts):
        source_count = counts[key]["sources"] + counts[key]["digests"]
        note_count = counts[key]["notes"]
        if source_count == 0 and note_count == 0:
            gap_type = "new-topic"
            seed = "capture a seed source or project note"
        elif source_count >= dense_threshold and note_count == 0:
            gap_type = "undigested"
            seed = "distill note candidates from checked digests"
        elif note_count >= dense_threshold and source_count == 0:
            gap_type = "under-warranted"
            seed = "capture or link supporting sources"
        else:
            continue
        gaps.append(
            {
                "topic": labels[key],
                "gap_type": gap_type,
                "source_count": counts[key]["sources"],
                "digest_count": counts[key]["digests"],
                "note_count": note_count,
                "proposed_seed": seed,
            }
        )
    return {
        "checked_topics": len(counts),
        "dense_threshold": dense_threshold,
        "gaps": gaps,
    }


def analyze_project_argument(vault: Path, project_path: str) -> dict[str, Any]:
    """Return a small argument-health lens for one checked project."""
    vault = Path(vault)
    project_rel = _project_rel(vault, project_path)
    project = _checked_frontmatter(vault, project_rel, "project")
    thesis_raw = str(project.get("thesis") or "").strip()
    if not thesis_raw:
        return _project_argument_empty(project_rel, "", "missing-thesis")

    thesis_rel = _concept_rel(thesis_raw)
    notes = {
        rel: frontmatter
        for rel, frontmatter in _checked_concepts(vault)
        if frontmatter.get("type") == "note" and _is_current_note(frontmatter)
    }
    thesis = notes.get(thesis_rel)
    if thesis is None:
        return _project_argument_empty(project_rel, thesis_rel, "missing-or-unchecked-thesis")

    edges = _note_edges(notes)
    component = _argument_component(thesis_rel, edges)
    component_edges = [
        edge for edge in edges if edge["source"] in component and edge["target"] in component
    ]
    counts = {
        relation: sum(1 for edge in component_edges if edge["type"] == relation)
        for relation in ("supports", "contradicts", "extends")
    }
    relation_count = len(component_edges)
    findings = _argument_findings(counts, relation_count)
    saturation_conditions = _argument_saturation_conditions(counts, relation_count)
    return {
        "project_path": project_rel,
        "thesis_path": thesis_rel,
        "argument_stage": _argument_stage(counts, relation_count),
        "evidence_saturation": _argument_saturation(saturation_conditions, relation_count),
        "displayed_confidence": _argument_confidence(counts, relation_count),
        "saturation_conditions": saturation_conditions,
        "relation_count": relation_count,
        "supports_count": counts["supports"],
        "contradicts_count": counts["contradicts"],
        "extends_count": counts["extends"],
        "node_count": len(component),
        "findings": findings,
        "gap_findings": _argument_gap_findings(counts, relation_count),
        "advisories": _argument_advisories(counts, relation_count),
        "nodes": [
            {
                "path": rel,
                "title": str(notes[rel].get("title") or Path(rel).stem),
                "role": "thesis" if rel == thesis_rel else "note",
            }
            for rel in sorted(component)
        ],
        "edges": sorted(
            component_edges, key=lambda edge: (edge["type"], edge["source"], edge["target"])
        ),
    }


def render_project_argument_canvas(vault: Path, project_path: str) -> dict[str, Any]:
    """Render the checked project argument graph as Obsidian JSON Canvas data."""
    result = analyze_project_argument(vault, project_path)
    node_ids = {
        node["path"]: f"n-{hashlib.sha256(node['path'].encode()).hexdigest()[:12]}"
        for node in result["nodes"]
    }
    nodes = []
    for index, node in enumerate(result["nodes"]):
        nodes.append(
            {
                "id": node_ids[node["path"]],
                "type": "file",
                "file": node["path"],
                "x": (index % 3) * 360,
                "y": (index // 3) * 240,
                "width": 300,
                "height": 180,
            }
        )
    edges = []
    for index, edge in enumerate(result["edges"]):
        source = node_ids.get(edge["source"])
        target = node_ids.get(edge["target"])
        if not source or not target:
            continue
        edges.append(
            {
                "id": f"e-{index}-{source}-{target}",
                "fromNode": source,
                "toNode": target,
                "label": edge["type"],
            }
        )
    return {"nodes": nodes, "edges": edges}


def write_project_argument_canvas(
    vault: Path,
    project_path: str,
    *,
    commit: bool = False,
    machine: str | None = None,
) -> dict[str, Any]:
    """Write the checked project argument graph as a generated Canvas projection."""
    vault = Path(vault)
    project_rel = _project_rel(vault, project_path)
    canvas_rel = _project_canvas_rel(project_rel)
    canvas = render_project_argument_canvas(vault, project_rel)
    canvas_path = vault / canvas_rel
    canvas_path.parent.mkdir(parents=True, exist_ok=True)
    canvas_path.write_text(json.dumps(canvas, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    event = None
    commit_id = ""
    if commit:
        event = append_journal_event(
            vault,
            {
                "event": "run",
                "run_id": f"projection:{canvas_rel}",
                "workflow": "render-project-argument-canvas",
                "status": "done",
                "inputs": [project_rel],
                "outputs": [canvas_rel],
            },
            machine=machine,
        )
        commit_id = commit_writer_changes(
            vault,
            "render project argument canvas",
            [canvas_rel],
            machine=machine,
        )
    return {
        "project_path": project_rel,
        "canvas_path": canvas_rel,
        "node_count": len(canvas["nodes"]),
        "edge_count": len(canvas["edges"]),
        "event": event,
        "commit": commit_id,
    }


def _checked_frontmatter(vault: Path, relpath: str, concept_type: str) -> dict[str, Any]:
    path = vault / relpath
    if not path.is_file():
        raise FileNotFoundError(path)
    frontmatter = read_frontmatter(path)
    if frontmatter.get("type") != concept_type or frontmatter.get("check_status") != "checked":
        raise ValueError(f"{relpath} is not a checked {concept_type}")
    return frontmatter


def _checked_concepts(vault: Path) -> Iterable[tuple[str, dict[str, Any]]]:
    for root in ("catalog/sources", "knowledge/digests", "knowledge/notes"):
        base = vault / root
        if not base.exists():
            continue
        for path in iter_markdown(base, skip_dirs=frozenset()):
            frontmatter = read_frontmatter(path)
            rel = path.relative_to(vault).as_posix()
            if frontmatter.get("check_status") == "checked" and _is_current_concept(
                rel, frontmatter
            ):
                yield rel, frontmatter


def _bucket(relpath: str, frontmatter: dict[str, Any]) -> str:
    concept_type = frontmatter.get("type")
    if relpath.startswith("catalog/sources/") and concept_type == "source":
        return "sources"
    if relpath.startswith("knowledge/digests/") and concept_type == "digest":
        return "digests"
    if relpath.startswith("knowledge/notes/") and concept_type == "note":
        return "notes"
    return ""


def _terms(frontmatter: dict[str, Any]) -> list[str]:
    out = []
    for field in ("tags", "topics", "research_area"):
        value = frontmatter.get(field)
        if isinstance(value, list):
            out.extend(item for item in value if isinstance(item, str) and item.strip())
        elif isinstance(value, str) and value.strip():
            out.append(value)
    massw = frontmatter.get("massw")
    if isinstance(massw, dict):
        out.extend(str(value) for value in massw.values() if str(value).strip())
    return sorted(set(out))


def _project_argument_empty(project_rel: str, thesis_rel: str, finding: str) -> dict[str, Any]:
    return {
        "project_path": project_rel,
        "thesis_path": thesis_rel,
        "argument_stage": "cold-start",
        "evidence_saturation": "unknown",
        "displayed_confidence": "below-threshold",
        "saturation_conditions": {
            "mature_graph": False,
            "has_support": False,
            "has_refutation": False,
        },
        "relation_count": 0,
        "supports_count": 0,
        "contradicts_count": 0,
        "extends_count": 0,
        "node_count": 0,
        "findings": [{"kind": finding, "severity": "high"}],
        "gap_findings": [
            {
                "kind": "structural",
                "severity": "high",
                "advice": "add a checked thesis note before argument analysis",
            }
        ],
        "advisories": [],
        "nodes": [],
        "edges": [],
    }


def _argument_stage(counts: dict[str, int], relation_count: int) -> str:
    if relation_count == 0:
        return "cold-start"
    if relation_count < 3:
        return "developing"
    if counts["contradicts"] > 0:
        return "contested"
    return "supported"


def _argument_findings(counts: dict[str, int], relation_count: int) -> list[dict[str, str]]:
    findings: list[dict[str, str]] = []
    if relation_count == 0:
        findings.append({"kind": "thin-argument", "severity": "high"})
    elif relation_count < 3:
        findings.append({"kind": "thin-argument", "severity": "medium"})
    if counts["supports"] == 0:
        findings.append({"kind": "no-support", "severity": "high"})
    if counts["contradicts"] == 0:
        findings.append({"kind": "no-refutation", "severity": "medium"})
    return findings


def _argument_saturation_conditions(counts: dict[str, int], relation_count: int) -> dict[str, bool]:
    return {
        "mature_graph": relation_count >= 3,
        "has_support": counts["supports"] > 0,
        "has_refutation": counts["contradicts"] > 0,
    }


def _argument_saturation(conditions: dict[str, bool], relation_count: int) -> str:
    if relation_count == 0:
        return "unknown"
    return "saturated" if all(conditions.values()) else "unsaturated"


def _argument_confidence(counts: dict[str, int], relation_count: int) -> str:
    if relation_count < 3:
        return "below-threshold"
    if counts["contradicts"] > 0:
        return "contested"
    if counts["supports"] > 0:
        return "supported"
    return "below-threshold"


def _argument_gap_findings(counts: dict[str, int], relation_count: int) -> list[dict[str, str]]:
    gaps: list[dict[str, str]] = []
    if relation_count == 0:
        gaps.append(
            {
                "kind": "structural",
                "severity": "high",
                "advice": "seed checked notes around the thesis",
            }
        )
    if counts["supports"] == 0:
        gaps.append(
            {
                "kind": "unstated-warrant",
                "severity": "high",
                "advice": "add supporting evidence notes",
            }
        )
    elif counts["supports"] == 1 and relation_count >= 3:
        gaps.append(
            {
                "kind": "fragility",
                "severity": "medium",
                "advice": "add independent support",
            }
        )
    if counts["contradicts"] > 0:
        gaps.append(
            {
                "kind": "conflict",
                "severity": "medium",
                "advice": "resolve or preserve the contradiction",
            }
        )
    return gaps


def _argument_advisories(counts: dict[str, int], relation_count: int) -> list[dict[str, str]]:
    advisories: list[dict[str, str]] = []
    if 0 < relation_count < 3:
        advisories.append(
            {
                "kind": "structural",
                "severity": "medium",
                "advice": "connect at least three checked notes before treating the argument as mature",
            }
        )
    if relation_count >= 3 and counts["contradicts"] == 0:
        advisories.append(
            {
                "kind": "refutation",
                "severity": "medium",
                "advice": "seek a counterargument before treating the thesis as saturated",
            }
        )
    return advisories


def _note_edges(notes: dict[str, dict[str, Any]]) -> list[dict[str, str]]:
    edges = []
    for source, frontmatter in notes.items():
        for link_type in ("supports", "contradicts", "extends"):
            for raw in _link_values(frontmatter, link_type):
                target = _link_target(raw)
                if target in notes and target != source:
                    edges.append({"source": source, "target": target, "type": link_type})
    return edges


def _argument_component(root: str, edges: list[dict[str, str]]) -> set[str]:
    graph: dict[str, set[str]] = defaultdict(set)
    for edge in edges:
        graph[edge["source"]].add(edge["target"])
        graph[edge["target"]].add(edge["source"])
    seen = {root}
    queue = [root]
    while queue:
        node = queue.pop(0)
        for neighbor in sorted(graph.get(node, set())):
            if neighbor not in seen:
                seen.add(neighbor)
                queue.append(neighbor)
    return seen


def _link_values(frontmatter: dict[str, Any], link_type: str) -> list[Any]:
    links = frontmatter.get("links")
    if not isinstance(links, dict):
        return []
    values = links.get(link_type) or []
    return values if isinstance(values, list) else [values]


def _link_target(value: Any) -> str:
    if isinstance(value, dict):
        value = value.get("target") or value.get("path") or value.get("id") or value.get("note")
    if not isinstance(value, str) or not value.strip():
        return ""
    raw = value.strip()
    if raw.startswith("[[") and raw.endswith("]]"):
        raw = raw[2:-2].split("|", 1)[0].split("#", 1)[0].strip()
    try:
        return _concept_rel(raw)
    except ValueError:
        return ""


def _is_current_concept(relpath: str, frontmatter: dict[str, Any]) -> bool:
    if not _is_current_frontmatter(frontmatter):
        return False
    return not relpath.startswith("knowledge/notes/") or _is_current_note(frontmatter)


def _is_current_frontmatter(frontmatter: dict[str, Any]) -> bool:
    return frontmatter.get("lifecycle") not in {"retracted", "archived"} and frontmatter.get(
        "status"
    ) not in {"rejected", "superseded"}


def _is_current_note(frontmatter: dict[str, Any]) -> bool:
    return _is_current_frontmatter(frontmatter) and frontmatter.get("status") not in {
        "candidate",
        "needs_review",
    }


def _digest_rel(path: str) -> str:
    rel = normalize_path(path)
    if "/" not in rel and not rel.endswith(".md"):
        rel = f"knowledge/digests/{rel}.md"
    if not rel.endswith(".md"):
        rel += ".md"
    return rel


def _project_rel(vault: Path, path: str) -> str:
    rel = normalize_path(path)
    if "/" not in rel:
        flat = f"knowledge/projects/{rel}.md"
        nested = f"knowledge/projects/{rel}/project.md"
        return nested if (Path(vault) / nested).is_file() else flat
    if not rel.endswith(".md"):
        rel += ".md"
    if not rel.startswith("knowledge/projects/"):
        raise ValueError(f"project must live under knowledge/projects: {rel}")
    return rel


def _project_canvas_rel(project_rel: str) -> str:
    if project_rel.endswith("/project.md"):
        return f"{project_rel.removesuffix('/project.md')}/argument.canvas"
    return f"knowledge/projects/{Path(project_rel).stem}/argument.canvas"


def _source_rel(path: str) -> str:
    rel = normalize_path(path)
    if "/" not in rel:
        rel = f"catalog/sources/{rel}/source.md"
    elif rel.startswith("catalog/sources/") and not rel.endswith(".md"):
        rel = f"{rel.rstrip('/')}/source.md"
    if not rel.startswith("catalog/sources/") or not rel.endswith("/source.md"):
        raise ValueError(f"source must be a catalog source Concept: {rel}")
    return rel


def _note_rel(path: str) -> str:
    rel = normalize_path(path)
    if "/" not in rel:
        rel = f"knowledge/notes/{rel}"
    if not rel.endswith(".md"):
        rel += ".md"
    if not rel.startswith("knowledge/notes/"):
        raise ValueError(f"note candidate must live under knowledge/notes: {rel}")
    return rel


def _concept_rel(path: str) -> str:
    rel = normalize_path(path)
    if "/" not in rel:
        rel = f"knowledge/notes/{rel}"
    if rel.startswith("catalog/sources/") and not rel.endswith(".md"):
        rel = f"{rel.rstrip('/')}/source.md"
    elif not rel.endswith(".md"):
        rel += ".md"
    if not rel.startswith(("catalog/sources/", "knowledge/notes/", "knowledge/hubs/")):
        raise ValueError(f"unsupported note link target: {rel}")
    return rel


def _checked_concept(vault: Path, relpath: str) -> dict[str, Any]:
    path = vault / relpath
    if not path.is_file():
        raise FileNotFoundError(path)
    frontmatter = read_frontmatter(path)
    if frontmatter.get("check_status") != "checked":
        raise ValueError(f"{relpath} is not checked")
    if not _is_current_frontmatter(frontmatter):
        raise ValueError(f"{relpath} is not current")
    return frontmatter


def _require_tool(policy: dict[str, Any], tool: str) -> None:
    if tool not in (policy.get("allowed_tools") or []):
        raise PermissionError(f"operation {policy['operation_id']} does not allow {tool}")


def _require_path(policy: dict[str, Any], path: str) -> None:
    rel = normalize_path(path)
    for raw_prefix in policy.get("allowed_paths") or []:
        prefix = normalize_path(str(raw_prefix)).rstrip("/")
        if rel == prefix or rel.startswith(prefix + "/"):
            return
    raise PermissionError(f"operation {policy['operation_id']} cannot access {rel}")


def _unique_note_rel(vault: Path, title: str) -> str:
    slug = safe_filename(title.lower().replace(" ", "-")).strip("._-") or "note"
    base = f"knowledge/notes/{slug}.md"
    candidate = base
    index = 1
    while (vault / candidate).exists() or (vault / ".memoria/staging" / candidate).exists():
        index += 1
        candidate = f"knowledge/notes/{slug}-{index}.md"
    return candidate


def _required_text(row: dict[str, Any], key: str) -> str:
    value = str(row.get(key) or "").strip()
    if not value:
        raise ValueError(f"note candidate requires {key}")
    return value


def _string_list(value: object) -> list[str]:
    if isinstance(value, list):
        return [item for item in value if isinstance(item, str) and item.strip()]
    if isinstance(value, str) and value.strip():
        return [value]
    return []


def _sha256_text(text: str) -> str:
    return "sha256:" + hashlib.sha256(text.encode()).hexdigest()
