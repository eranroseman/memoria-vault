"""Verdict-tagged engine API used by CLI and optional transports."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from memoria_vault.runtime import state
from memoria_vault.runtime.capabilities import render_capability_index
from memoria_vault.runtime.knowledge import exploration_channel as _exploration_channel
from memoria_vault.runtime.knowledge import read_project_draft as _read_project_draft
from memoria_vault.runtime.knowledge import read_project_slice as _read_project_slice
from memoria_vault.runtime.paths import safe_filename
from memoria_vault.runtime.policy.paths import normalize_path, within_scope
from memoria_vault.runtime.read_barrier import is_consumable_checked_file
from memoria_vault.runtime.vaultio import (
    apply_universal_concept_frontmatter,
    frontmatter_doc,
    iter_markdown,
    read_frontmatter,
    split_frontmatter,
)
from memoria_vault.runtime.worker import enqueue_operation, run_request

JOURNAL_OPERATION_ALIASES = {"work.digest": ("compile-source-digest",)}
CONCEPT_TYPES = {"note", "digest", "hub", "project"}
CONCEPT_HOMES = {
    "note": "notes",
    "hub": "hubs",
    "project": "projects",
}
VIEW_SPEC_VERSION = "view-spec.v1"
READ_API_VERSION = "engine-read-api.v1"


def read_status(workspace: Path) -> dict[str, Any]:
    workspace = Path(workspace)
    with state.connect(workspace) as conn:
        rows = conn.execute(
            "SELECT status, COUNT(*) AS count FROM operation_requests GROUP BY status"
        ).fetchall()
    return _read_payload(
        workspace=str(workspace),
        db=state.db_path(workspace).relative_to(workspace).as_posix(),
        requests={row["status"]: row["count"] for row in rows},
    )


def read_operations(workspace: Path) -> dict[str, Any]:
    operations = []
    catalog = json.loads(render_capability_index(Path(workspace)))
    for row in catalog["capabilities"]:
        if row.get("type") != "operation":
            continue
        operations.append(
            {
                "operation_id": row.get("operation_id") or row["id"],
                "title": row.get("title") or row["id"],
                "risk_class": row.get("risk_class") or "",
                "runner": row.get("runner") or "",
            }
        )
    return _read_payload(operations=operations)


def read_surface_schema(workspace: Path) -> dict[str, Any]:
    from memoria_vault.engine.surface_contract import SURFACE_ACTIONS, SURFACE_CONTRACT_VERSION

    return _read_payload(
        surface_contract_version=SURFACE_CONTRACT_VERSION,
        actions=[dict(action) for action in SURFACE_ACTIONS],
    )


def read_exploration(
    workspace: Path, *, limit: int = 10, read_scope: list[str] | None = None
) -> dict[str, Any]:
    workspace = Path(workspace)
    exploration = _exploration_channel(workspace, limit=limit)
    if read_scope is not None:
        items = [
            item
            for item in exploration.get("items") or []
            if _exploration_item_in_scope(workspace, item, read_scope)
        ]
        contrary_items = [
            item
            for item in exploration.get("contrary_items") or []
            if _contrary_item_in_scope(item, read_scope)
        ]
        exploration = {**exploration, "items": items, "contrary_items": contrary_items}
        exploration["empty"] = not items and not contrary_items
    return _read_payload(exploration=exploration)


def read_requests(
    workspace: Path, *, status: str = "", read_scope: list[str] | None = None
) -> dict[str, Any]:
    sql = """
        SELECT request_id, operation_id, status, created_at, completed_at, error,
               input_refs_json, output_intents_json, primary_target, args_json
        FROM operation_requests
    """
    params: tuple[str, ...] = ()
    if status:
        sql += " WHERE status = ?"
        params = (status,)
    sql += " ORDER BY created_at, request_id"
    with state.connect(workspace) as conn:
        requests = [
            state.request_summary(row)
            for row in conn.execute(sql, params)
            if _request_in_scope(row, read_scope, require_all=False)
        ]
    return _read_payload(requests=requests)


def read_request(
    workspace: Path, request_id: str, *, read_scope: list[str] | None = None
) -> dict[str, Any]:
    row = state.request_row(Path(workspace), request_id)
    if row is None:
        raise FileNotFoundError(f"request not found: {request_id}")
    if not _request_in_scope(row, read_scope, require_all=True):
        raise FileNotFoundError(f"request not found: {request_id}")
    return _read_payload(request=state.request_detail(row))


def read_attention(
    workspace: Path,
    *,
    status: str = "",
    kind: str = "",
    worklist: bool = False,
    read_scope: list[str] | None = None,
) -> dict[str, Any]:
    cards = _attention_cards(Path(workspace))
    cards = [card for card in cards if _attention_in_scope(card, read_scope)]
    if worklist:
        cards = [
            card
            for card in cards
            if card["status"] == "open" and card["kind"] in {"candidate", "gap", "work-prompt"}
        ]
    else:
        cards = [
            card
            for card in cards
            if (not status or card["status"] == status) and (not kind or card["kind"] == kind)
        ]
    return _read_payload(attention=cards, view=_attention_table_view(cards, worklist=worklist))


def read_attention_card(
    workspace: Path, attention_path: str, *, read_scope: list[str] | None = None
) -> dict[str, Any]:
    rel, path = _workspace_file(Path(workspace), attention_path)
    card = _attention_card(path, Path(workspace))
    if card is None:
        raise FileNotFoundError(f"attention projection not found: {rel}")
    if not _attention_in_scope(card, read_scope):
        raise FileNotFoundError(f"attention projection not found: {rel}")
    return _read_payload(attention=card, view=_attention_card_view(card))


def read_concept(
    workspace: Path, target: str, *, read_scope: list[str] | None = None
) -> dict[str, Any]:
    workspace = Path(workspace)
    path = _resolve_concept_path(workspace, target)
    if path is None:
        work = state.catalog_source(workspace, target)
        if work is None:
            raise FileNotFoundError(f"target not found: {target}")
        _require_scope(
            work.get("concept_path") or target, read_scope, f"target not found: {target}"
        )
        return _read_payload(target=target, kind="work", work=_tag_work(work))
    rel = path.relative_to(workspace).as_posix()
    _require_scope(rel, read_scope, f"target not found: {target}")
    check_status = state.concept_check_status(workspace, rel)
    if check_status == "checked" and not is_consumable_checked_file(workspace, rel):
        raise PermissionError(f"checked Concept is not consumable until scan runs: {rel}")
    frontmatter, body = split_frontmatter(path.read_text(encoding="utf-8"))
    return _read_payload(
        path=rel,
        type=frontmatter.get("type"),
        check_status=check_status,
        verdict=check_status,
        frontmatter=frontmatter,
        body=body,
        body_data=_untrusted_text(body),
    )


def read_concepts(
    workspace: Path, *, concept_type: str = "", read_scope: list[str] | None = None
) -> dict[str, Any]:
    workspace = Path(workspace)
    rows = []
    for path in iter_markdown(workspace):
        rel = path.relative_to(workspace).as_posix()
        if not _scope_allows(rel, read_scope):
            continue
        frontmatter = read_frontmatter(path)
        item_type = str(frontmatter.get("type") or "")
        if item_type not in CONCEPT_TYPES:
            continue
        if concept_type and item_type != concept_type:
            continue
        check_status = state.concept_check_status(workspace, rel)
        rows.append(
            {
                "path": rel,
                "type": item_type,
                "title": frontmatter.get("title") or path.stem,
                "check_status": check_status,
                "verdict": check_status,
            }
        )
    return _read_payload(concepts=sorted(rows, key=lambda row: row["path"]))


def read_work(
    workspace: Path, work_id: str, *, read_scope: list[str] | None = None
) -> dict[str, Any]:
    work = state.catalog_source(Path(workspace), work_id)
    if work is None:
        raise FileNotFoundError(f"work not found: {work_id}")
    _require_any_scope(_work_paths(work), read_scope, f"work not found: {work_id}")
    return _read_payload(work=_tag_work(work))


def read_slice(
    workspace: Path, project_path: str, *, read_scope: list[str] | None = None
) -> dict[str, Any]:
    project_slice = _read_project_slice(Path(workspace), project_path)
    _require_scope(
        project_slice["outline_path"], read_scope, f"project slice not found: {project_path}"
    )
    return _read_payload(slice=project_slice, view=_slice_table_view(project_slice))


def read_draft(
    workspace: Path, project_path: str, *, read_scope: list[str] | None = None
) -> dict[str, Any]:
    draft = _read_project_draft(Path(workspace), project_path)
    _require_scope(draft["draft_path"], read_scope, f"project draft not found: {project_path}")
    return _read_payload(draft=draft, view=_draft_view(draft))


def compose_draft(
    workspace: Path,
    project_path: str,
    *,
    token_budget: int = 4000,
    idempotency_key: str | None = None,
    schedule_id: str | None = None,
    actor: str = "pi",
) -> dict[str, Any]:
    return run_operation(
        workspace,
        "compose-project-draft",
        {"project_path": project_path, "token_budget": token_budget},
        idempotency_key=idempotency_key,
        schedule_id=schedule_id,
        actor=actor,
        command="compose-project-draft",
    )


def verify_draft(
    workspace: Path,
    project_path: str,
    *,
    idempotency_key: str | None = None,
    schedule_id: str | None = None,
    actor: str = "pi",
) -> dict[str, Any]:
    return run_operation(
        workspace,
        "verify-project-draft",
        {"project_path": project_path},
        idempotency_key=idempotency_key,
        schedule_id=schedule_id,
        actor=actor,
        command="verify-project-draft",
    )


def promote_draft_passage(
    workspace: Path,
    project_path: str,
    *,
    title: str,
    passage: str,
    work_id: str = "",
    idempotency_key: str | None = None,
    schedule_id: str | None = None,
    actor: str = "pi",
) -> dict[str, Any]:
    return run_operation(
        workspace,
        "promote-draft-passage",
        {
            "project_path": project_path,
            "title": title,
            "passage": passage,
            "work_id": work_id,
        },
        idempotency_key=idempotency_key,
        schedule_id=schedule_id,
        actor=actor,
        command="promote-draft-passage",
    )


def read_journal(
    workspace: Path,
    *,
    operation: str = "",
    request_id: str = "",
    path: str = "",
    decision: str = "",
    date: str = "",
    limit: int = 50,
    read_scope: list[str] | None = None,
) -> dict[str, Any]:
    sql = """
        SELECT event_id, timestamp, event_type, machine, payload_json, prev_hash, row_hash
        FROM event_log
    """
    clauses = []
    params: list[str] = []
    if operation:
        operations = _journal_operation_values(operation)
        placeholders = ", ".join("?" for _ in operations)
        clauses.append(
            "("
            f"json_extract(payload_json, '$.operation') IN ({placeholders}) OR "
            f"json_extract(payload_json, '$.workflow') IN ({placeholders})"
            ")"
        )
        params.extend(operations)
        params.extend(operations)
    if request_id:
        clauses.append("json_extract(payload_json, '$.request_id') = ?")
        params.append(request_id)
    if path:
        fields = ("output_id", "target_id", "target_path", "linked_id", "quarantined_id")
        clauses.append(
            "("
            + " OR ".join(f"json_extract(payload_json, '$.{field}') = ?" for field in fields)
            + ")"
        )
        params.extend([path] * len(fields))
    if decision:
        clauses.append("json_extract(payload_json, '$.decision') = ?")
        params.append(decision)
    if date:
        clauses.append("timestamp LIKE ?")
        params.append(f"{date}%")
    if clauses:
        sql += " WHERE " + " AND ".join(clauses)
    sql += " ORDER BY event_id DESC LIMIT ?"
    params.append(str(max(limit, 1)))
    with state.connect(workspace) as conn:
        events = [
            event
            for row in conn.execute(sql, params)
            if _journal_in_scope(event := _journal_row(row), read_scope)
        ]
    return _read_payload(events=events)


def read_journal_event(
    workspace: Path, event_id: int, *, read_scope: list[str] | None = None
) -> dict[str, Any]:
    with state.connect(workspace) as conn:
        row = conn.execute(
            """
            SELECT event_id, timestamp, event_type, machine, payload_json, prev_hash, row_hash
            FROM event_log
            WHERE event_id = ?
            """,
            (event_id,),
        ).fetchone()
    if row is None:
        raise FileNotFoundError(f"journal event not found: {event_id}")
    event = _journal_row(row)
    if not _journal_in_scope(event, read_scope):
        raise FileNotFoundError(f"journal event not found: {event_id}")
    return _read_payload(event=event)


def _read_payload(**payload: Any) -> dict[str, Any]:
    return {"ok": True, "api_version": READ_API_VERSION, **payload}


def run_operation(
    workspace: Path,
    operation_id: str,
    payload: dict[str, Any],
    *,
    idempotency_key: str | None = None,
    schedule_id: str | None = None,
    actor: str = "pi",
    command: str = "",
    surface: str = "memoria-cli",
    machine: str = "memoria-cli",
) -> dict[str, Any]:
    job = enqueue_operation(
        workspace,
        operation_id,
        payload=payload,
        idempotency_key=idempotency_key,
        provenance={"surface": surface, "command": command or operation_id},
        schedule_id=schedule_id,
        actor=actor,
    )
    result = (
        job
        if job.get("status") != "pending"
        else run_request(workspace, str(job["job_id"]), machine=machine)
    )
    return {
        "ok": result is not None and result.get("status") == "done",
        "job": job,
        "result": result,
    }


def write_new_concept(
    workspace: Path,
    concept_type: str,
    title: str,
    *,
    body: str,
    tags: list[str],
    extra: dict[str, Any],
    idempotency_key: str | None = None,
    schedule_id: str | None = None,
    actor: str = "pi",
) -> dict[str, Any]:
    workspace = Path(workspace)
    if concept_type not in CONCEPT_HOMES:
        raise ValueError(f"unsupported concept type: {concept_type}")
    slug = safe_filename(title.lower()).strip("._-") or concept_type
    if concept_type == "project":
        rel = _unique_rel(workspace, f"{CONCEPT_HOMES[concept_type]}/{slug}/project.md")
    else:
        rel = _unique_rel(workspace, f"{CONCEPT_HOMES[concept_type]}/{slug}.md")
    frontmatter = {"type": concept_type, "title": title, "tags": tags, "links": {}}
    frontmatter.update({key: value for key, value in extra.items() if value not in (None, "")})
    apply_universal_concept_frontmatter(frontmatter, rel)
    content = frontmatter_doc(frontmatter, body)
    job = enqueue_operation(
        workspace,
        "create-concept",
        payload={
            "target_path": rel,
            "content": content,
            "concept_type": concept_type,
            "title": title,
        },
        idempotency_key=idempotency_key,
        output_intents=[{"id": rel, "kind": concept_type}],
        primary_target=rel,
        actor=actor,
        provenance={"surface": "memoria-cli", "command": f"new-{concept_type}"},
        schedule_id=schedule_id,
    )
    envelope = job.get("request_envelope") if isinstance(job.get("request_envelope"), dict) else {}
    args = envelope.get("args") if isinstance(envelope.get("args"), dict) else {}
    if isinstance(args.get("target_path"), str) and args["target_path"]:
        rel = args["target_path"]
    if isinstance(args.get("content"), str) and args["content"]:
        saved_frontmatter, _body = split_frontmatter(args["content"])
        if saved_frontmatter:
            frontmatter = saved_frontmatter
    result = (
        job
        if job.get("status") != "pending"
        else run_request(workspace, str(job["job_id"]), machine="memoria-cli")
    )
    return {
        "ok": result is not None and result.get("status") == "done",
        "path": rel,
        "concept": frontmatter,
        "job": job,
        "result": result,
        "commit": result.get("commit") if isinstance(result, dict) else "",
    }


def resolve_attention(
    workspace: Path,
    attention_path: str,
    *,
    outcome: str,
    reason: str,
    idempotency_key: str | None = None,
    schedule_id: str | None = None,
    actor: str = "pi",
) -> dict[str, Any]:
    card_payload = read_attention_card(workspace, attention_path)
    card = card_payload["attention"]
    return run_operation(
        Path(workspace),
        "resolve-attention",
        {
            "target_id": card["path"],
            "reason": reason,
            "outcome": outcome,
            "routing_class": card["routing_class"],
        },
        idempotency_key=idempotency_key,
        schedule_id=schedule_id,
        actor=actor,
        command="resolve-attention",
    )


def _tag_work(work: dict[str, Any]) -> dict[str, Any]:
    tagged = dict(work)
    for key in ("content_text", "abstract", "description"):
        if isinstance(tagged.get(key), str) and tagged[key]:
            tagged[f"{key}_data"] = _untrusted_text(tagged[key])
    return tagged


def _scope_allows(path: str, read_scope: list[str] | None) -> bool:
    if read_scope is None:
        return True
    try:
        return within_scope(normalize_path(path), [normalize_path(scope) for scope in read_scope])
    except ValueError:
        return False


def _require_scope(path: str, read_scope: list[str] | None, message: str) -> None:
    if not _scope_allows(path, read_scope):
        raise FileNotFoundError(message)


def _require_any_scope(paths: list[str], read_scope: list[str] | None, message: str) -> None:
    if read_scope is None:
        return
    if not any(_scope_allows(path, read_scope) for path in paths if path):
        raise FileNotFoundError(message)


def _work_paths(work: dict[str, Any]) -> list[str]:
    return [
        str(work.get("concept_path") or ""),
        str(work.get("content_path") or ""),
        str(work.get("raw_path") or ""),
    ]


def _exploration_item_in_scope(
    workspace: Path, item: dict[str, Any], read_scope: list[str] | None
) -> bool:
    work = state.catalog_source(workspace, str(item.get("work_id") or ""))
    return work is not None and any(_scope_allows(path, read_scope) for path in _work_paths(work))


def _contrary_item_in_scope(item: dict[str, Any], read_scope: list[str] | None) -> bool:
    paths = [str(item.get("path") or ""), str(item.get("target") or "")]
    return all(_scope_allows(path, read_scope) for path in paths if path)


def _untrusted_text(text: str) -> dict[str, str]:
    return {"kind": "untrusted_text", "text": text}


def _unique_rel(workspace: Path, rel: str) -> str:
    path = workspace / rel
    if not path.exists():
        return rel
    stem = path.with_suffix("")
    suffix = path.suffix
    index = 2
    while True:
        candidate = Path(f"{stem}-{index}{suffix}")
        if not candidate.exists():
            return candidate.relative_to(workspace).as_posix()
        index += 1


def _resolve_concept_path(workspace: Path, target: str) -> Path | None:
    raw = Path(target)
    direct = raw if raw.is_absolute() else workspace / raw
    if direct.is_file():
        return direct.resolve()
    slug = safe_filename(target.strip().lower())
    for path in iter_markdown(workspace):
        frontmatter = read_frontmatter(path)
        if frontmatter.get("type") not in CONCEPT_TYPES:
            continue
        if target in {
            str(frontmatter.get("id") or ""),
            str(frontmatter.get("title") or ""),
            path.stem,
            path.relative_to(workspace).as_posix(),
        }:
            return path.resolve()
        if slug and slug == safe_filename(str(frontmatter.get("title") or "").lower()):
            return path.resolve()
    return None


def _attention_cards(workspace: Path) -> list[dict[str, Any]]:
    return [
        card
        for path in sorted((workspace / "inbox").glob("*.md"))
        if (card := _attention_card(path, workspace)) is not None
    ]


def _attention_card(path: Path, workspace: Path) -> dict[str, Any] | None:
    if not path.is_file():
        return None
    frontmatter, body = split_frontmatter(path.read_text(encoding="utf-8"))
    if frontmatter.get("projection") != "attention":
        return None
    rel = path.resolve().relative_to(workspace.resolve()).as_posix()
    return {
        "path": rel,
        "title": frontmatter.get("title") or path.stem,
        "kind": frontmatter.get("attention_kind") or "",
        "status": frontmatter.get("attention_status") or "",
        "routing_class": frontmatter.get("routing_class") or "ask",
        "target": frontmatter.get("target") or frontmatter.get("target_id") or "",
        "loudness": frontmatter.get("loudness") or "",
        "check_status": frontmatter.get("check_status") or "unchecked",
        "frontmatter": frontmatter,
        "body": body,
        "body_data": _untrusted_text(body),
    }


def _attention_in_scope(card: dict[str, Any], read_scope: list[str] | None) -> bool:
    return read_scope is None or any(
        _scope_allows(str(card.get(key) or ""), read_scope) for key in ("path", "target")
    )


def _attention_table_view(cards: list[dict[str, Any]], *, worklist: bool) -> dict[str, Any]:
    rows = [
        {
            "ref": card["path"],
            "check_status": _view_check_status(card),
            "cells": {
                "title": card["title"],
                "kind": card["kind"],
                "status": card["status"],
                "target": card["target"],
            },
        }
        for card in cards
    ]
    return {
        "version": VIEW_SPEC_VERSION,
        "kind": "attention",
        "blocks": [
            {
                "id": "attention-table",
                "kind": "table",
                "title": "Attention worklist" if worklist else "Attention",
                "check_status": _combined_check_status(row["check_status"] for row in rows),
                "refs": [row["ref"] for row in rows],
                "columns": ["title", "kind", "status", "target"],
                "rows": rows,
            }
        ],
    }


def _attention_card_view(card: dict[str, Any]) -> dict[str, Any]:
    return {
        "version": VIEW_SPEC_VERSION,
        "kind": "attention-card",
        "blocks": [
            {
                "id": safe_filename(card["path"]),
                "kind": "card",
                "title": card["title"],
                "check_status": _view_check_status(card),
                "refs": [card["path"]],
                "fields": {
                    "kind": card["kind"],
                    "status": card["status"],
                    "target": card["target"],
                    "routing_class": card["routing_class"],
                    "loudness": card["loudness"],
                },
                "body_data": card["body_data"],
            }
        ],
    }


def _slice_table_view(project_slice: dict[str, Any]) -> dict[str, Any]:
    rows = [
        {
            "ref": member["path"],
            "check_status": member["check_status"],
            "cells": {
                "order": member["order"],
                "title": member["title"],
                "reasoning": member["reasoning"],
            },
        }
        for member in project_slice["members"]
    ]
    return {
        "version": VIEW_SPEC_VERSION,
        "kind": "project-slice",
        "blocks": [
            {
                "id": safe_filename(project_slice["outline_path"]),
                "kind": "table",
                "title": "Project slice",
                "check_status": "checked" if rows and not project_slice["missing"] else "unchecked",
                "refs": [row["ref"] for row in rows],
                "columns": ["order", "title", "reasoning"],
                "rows": rows,
            }
        ],
    }


def _draft_view(draft: dict[str, Any]) -> dict[str, Any]:
    rows = [
        {
            "ref": str(row["block_ref"]),
            "check_status": "unchecked" if row["state"] != "complete" else "checked",
            "cells": {
                "id": row["id"],
                "type": row["type"],
                "state": row["state"],
                "review_required": row["review_required"],
            },
        }
        for row in draft["evidence_sets"]
    ]
    ready = bool(rows) and all(row["check_status"] == "checked" for row in rows)
    return {
        "version": VIEW_SPEC_VERSION,
        "kind": "project-draft",
        "blocks": [
            {
                "id": safe_filename(draft["draft_path"]),
                "kind": "table",
                "title": "Project draft evidence",
                "check_status": "checked" if ready else "unchecked",
                "refs": [draft["draft_path"]],
                "columns": ["id", "type", "state", "review_required"],
                "rows": rows,
            }
        ],
    }


def _view_check_status(card: dict[str, Any]) -> str:
    return str(card.get("check_status") or "unchecked")


def _combined_check_status(statuses: Any) -> str:
    values = {str(status or "unchecked") for status in statuses}
    if len(values) == 1:
        return values.pop()
    return "mixed" if values else "unchecked"


def _workspace_file(workspace: Path, value: str) -> tuple[str, Path]:
    raw = Path(value)
    path = raw if raw.is_absolute() else workspace / raw
    resolved = path.resolve()
    try:
        rel = resolved.relative_to(workspace.resolve()).as_posix()
    except ValueError as exc:
        raise ValueError(f"path must be inside workspace: {value}") from exc
    return rel, resolved


def _request_in_scope(row: Any, read_scope: list[str] | None, *, require_all: bool) -> bool:
    if read_scope is None:
        return True
    paths = _request_paths(row)
    if not paths:
        return False
    if require_all:
        return all(_scope_allows(path, read_scope) for path in paths)
    return any(_scope_allows(path, read_scope) for path in paths)


def _request_paths(row: Any) -> list[str]:
    paths = [str(row["primary_target"] or "")]
    for key in ("input_refs_json", "output_intents_json"):
        for item in json.loads(row[key] or "[]"):
            if isinstance(item, dict):
                paths.append(str(item.get("id") or item.get("path") or ""))
            else:
                paths.append(str(item or ""))
    args = json.loads(row["args_json"] or "{}")
    if isinstance(args, dict):
        for key in ("target_path", "target_id", "path"):
            paths.append(str(args.get(key) or ""))
        work_id = str(args.get("work_id") or "").strip()
        if work_id:
            paths.extend([work_id, f"catalog/sources/{work_id}"])
    return [path for path in paths if path]


def _journal_row(row: Any) -> dict[str, Any]:
    return {
        "event_id": row["event_id"],
        "timestamp": row["timestamp"],
        "event_type": row["event_type"],
        "machine": row["machine"],
        "payload": json.loads(row["payload_json"]),
        "prev_hash": row["prev_hash"],
        "row_hash": row["row_hash"],
    }


def _journal_in_scope(event: dict[str, Any], read_scope: list[str] | None) -> bool:
    if read_scope is None:
        return True
    paths = _journal_paths(event.get("payload") or {})
    return bool(paths) and all(_scope_allows(path, read_scope) for path in paths)


def _journal_paths(payload: Any) -> list[str]:
    if not isinstance(payload, dict):
        return []
    paths = []
    for key in ("output_id", "target_id", "target_path", "linked_id", "quarantined_id"):
        paths.append(str(payload.get(key) or ""))
    for key in ("outputs", "paths", "targets"):
        value = payload.get(key)
        if isinstance(value, list):
            paths.extend(str(item) for item in value)
    return [path for path in paths if path]


def _journal_operation_values(operation: str) -> list[str]:
    return sorted({operation, *JOURNAL_OPERATION_ALIASES.get(operation, ())})
