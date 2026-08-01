"""Cockpit assembly (U2 spec §1): a read-only composer over U1 registry actions.

Two screens, one composer: `assemble_deep` (panels 1-6, fixed keys) and
`assemble_triage` (worklist / review / flow). Every panel carries
`source_action` — the registry row id of the read it wraps, or `""` for a
named-pending panel whose producer is not registered yet. Seams owned by later
sections or sibling plans (section T's `trace_panel` and the `context.read`
transport; T.3's `dashboard.read` row; V2's evidence-review queue) are consumed
both-branch: wrapped when live, an honest named line when absent. The composer
holds no state, re-sorts nothing, and never writes.
"""

from __future__ import annotations

import json
import textwrap
from collections import Counter
from pathlib import Path
from typing import Any

from memoria_vault.engine import api as engine_api
from memoria_vault.engine.surface_contract import actions_by_id


def active_projects(vault: Path, *, read_scope: list[str] | None = None) -> list[dict[str, Any]]:
    """The active predicate, named once (U2 spec §1): a `type: project` concept
    whose frontmatter `archived` is not True. `lifecycle` is schema-retired
    (RETIRED_FRONTMATTER_FIELDS, vaultio.py) and is deliberately not consulted.
    Wraps concepts.list + concepts.get only."""
    vault = Path(vault)
    listing = engine_api.read_concepts(vault, concept_type="project", read_scope=read_scope)
    projects: list[dict[str, Any]] = []
    for row in listing["concepts"]:
        concept = engine_api.read_concept(vault, row["path"], read_scope=read_scope)
        if concept["frontmatter"].get("archived") is True:
            continue
        projects.append({"path": row["path"], "title": row["title"]})
    return projects


def resolve_active_project(vault: Path, *, read_scope: list[str] | None = None) -> dict[str, Any]:
    projects = active_projects(vault, read_scope=read_scope)
    if len(projects) == 1:
        return {"resolution": "active", "project": projects[0]["path"]}
    return {"resolution": "ambiguous", "projects": projects}


def assemble_deep(
    vault: Path, project: str, *, read_scope: list[str] | None = None
) -> dict[str, Any]:
    """Panels 1-6 in the U2 §1 fixed order, each wrapping one registry action:
    concepts.get, project.slice.read, project.draft.read (x2), journal.list (via
    section T's trace_panel), context.read."""
    vault = Path(vault)
    slice_payload = engine_api.read_slice(vault, project, read_scope=read_scope)
    draft_payload = engine_api.read_draft(vault, project, read_scope=read_scope)
    return {
        "project": _project_panel(vault, project, read_scope=read_scope),
        "slice": _slice_panel(slice_payload),
        "draft": _draft_panel(slice_payload, draft_payload),
        "grounds": _grounds_panel(draft_payload, slice_payload),
        "trace": _trace_panel_entry(vault, project, read_scope=read_scope),
        "context": _context_panel(vault, read_scope=read_scope),
    }


def assemble_triage(vault: Path, *, read_scope: list[str] | None = None) -> dict[str, Any]:
    """Triage panels in the U2 §1 fixed order: worklist / review / flow."""
    vault = Path(vault)
    return {
        "worklist": _worklist_panel(vault, read_scope=read_scope),
        "review": _review_panel(),
        "flow": _flow_panel(),
    }


def _project_panel(
    vault: Path, project: str, *, read_scope: list[str] | None = None
) -> dict[str, Any]:
    concept = engine_api.read_concept(vault, project, read_scope=read_scope)
    frontmatter = concept["frontmatter"]
    return {
        "source_action": "concepts.get",
        "path": str(concept["path"]),
        "title": str(frontmatter.get("title") or ""),
        "thesis": str(frontmatter.get("thesis") or ""),
        "archived": frontmatter.get("archived") is True,
    }


def _slice_panel(slice_payload: dict[str, Any]) -> dict[str, Any]:
    data = slice_payload["slice"]
    return {
        "source_action": "project.slice.read",
        "outline_path": data["outline_path"],
        "members": len(data["members"]),
        "edges_by_type": dict(sorted(Counter(e["type"] for e in data["edges"]).items())),
        "missing": len(data["missing"]),
    }


def _draft_panel(slice_payload: dict[str, Any], draft_payload: dict[str, Any]) -> dict[str, Any]:
    """Panel 3 renders ONLY what the read actions expose (U2 spec §1): outline
    membership (project.slice.read), draft presence and per-record evidence
    states (project.draft.read's evidence_sets). Deliberately no
    verification-status line — that datum is transient and persisted nowhere
    readable (spec §6)."""
    draft = draft_payload["draft"]
    return {
        "source_action": "project.draft.read",
        # The panel composes two reads, and one string cannot say so. The
        # singular key keeps naming the primary read (it is what the `--json`
        # surface and the screen heading carry); the list is the honest full
        # attribution for a reader checking where `outline_members` came from.
        "source_actions": ["project.draft.read", "project.slice.read"],
        "draft_path": draft["draft_path"],
        "outline_members": len(slice_payload["slice"]["members"]),
        "draft_present": bool(draft["content"]),
        "evidence_states": dict(
            sorted(Counter(str(row["state"]) for row in draft["evidence_sets"]).items())
        ),
        "review_required": sum(1 for row in draft["evidence_sets"] if row["review_required"]),
    }


def _grounds_panel(draft_payload: dict[str, Any], slice_payload: dict[str, Any]) -> dict[str, Any]:
    """Panel 4 (R2's grounds marks over the shipped reads): `total` counts the
    grounds marks written in the draft (`evidence_markers`), `complete` counts
    the derived records that resolved (`evidence_sets` — only those carry
    `state`), zero-grounds marks become honesty-card findings, and unresolved
    outline ids (project.slice.read `missing`) are open gaps.

    Each finding names the read that produced it. The panel's own numbers come
    from `project.draft.read`, but every open gap comes from the slice — and a
    reader who follows the panel's attribution to check one would land on a read
    that never produced it. Attribution is the whole trust claim; per finding is
    the only granularity that keeps it true."""
    markers = draft_payload["draft"]["evidence_markers"]
    findings = [
        {
            "finding": (
                f"open gap: outline id {row['id']} resolves to no checked note (line {row['line']})"
            ),
            "what_tipped_it": f"{slice_payload['slice']['outline_path']} line {row['line']}",
            "source_action": "project.slice.read",
        }
        for row in slice_payload["slice"]["missing"]
    ]
    findings.extend(
        {
            "finding": f"thin claim: {marker['id']} has 0 grounds items",
            "what_tipped_it": "items=",
            "source_action": "project.draft.read",
        }
        for marker in markers
        if not marker["items"]
    )
    return {
        "source_action": "project.draft.read",
        "complete": sum(
            1 for row in draft_payload["draft"]["evidence_sets"] if row["state"] == "complete"
        ),
        "total": len(markers),
        "findings": findings,
    }


def _trace_panel_entry(
    vault: Path, project: str, *, read_scope: list[str] | None = None
) -> dict[str, Any]:
    builder = globals().get("trace_panel")
    if builder is None:
        # Section T lands trace_panel(vault, project_path, *, limit=8,
        # read_scope=None) in this module (ref = journal event_id, honest
        # total+shown). Until then the panel is a named pending line, never a
        # silent absence.
        return {
            "source_action": "journal.list",
            "pending": "engine.cockpit.trace_panel (U2 plan section T)",
        }
    return builder(vault, project, limit=8, read_scope=read_scope)


def _context_panel(vault: Path, *, read_scope: list[str] | None = None) -> dict[str, Any]:
    """Panel 6 both-branch (U2 spec §1 panel 6): wrap a live context.read
    transport when the row carries a bound engine; otherwise render the honest
    reserved placeholder naming the row. Section T owns the wiring and
    registration."""
    row = actions_by_id().get("context.read")
    if row is None:
        return {
            "source_action": "context.read",
            "reserved": "context.read is not in the surface-contract registry",
        }
    engine_name = str(row.get("engine") or "")
    if not engine_name or not hasattr(engine_api, engine_name):
        return {
            "source_action": "context.read",
            "reserved": str(row.get("reserved") or "reserved (no engine binding)"),
        }
    payload = getattr(engine_api, engine_name)(Path(vault), read_scope=read_scope)
    bundle = {key: value for key, value in payload.items() if key not in {"ok", "api_version"}}
    return {
        "source_action": "context.read",
        "bundle": bundle,
        "invocation": _invocation_line(row),
    }


def _invocation_line(row: dict[str, Any]) -> str:
    cli = row.get("cli")
    if isinstance(cli, dict) and cli.get("commands"):
        return str(cli["commands"][0])
    return f"{row['id']} via engine_api.{row.get('engine')}"


def _worklist_panel(vault: Path, *, read_scope: list[str] | None = None) -> dict[str, Any]:
    """attention-as-projection (U2 spec §1 triage 1): read_attention's payload
    order is preserved verbatim — no re-sort, no cockpit-owned queue (I1 owns
    ordering and any rank_factors the cards carry)."""
    payload = engine_api.read_attention(vault, worklist=True, read_scope=read_scope)
    return {"source_action": "attention.list", "cards": payload["attention"]}


def _review_panel() -> dict[str, Any]:
    # Both-branch live consumption lands with the triage renderer (C.3), which
    # calls engine_api.evidence_review_queue(batch=0, ...) engine-direct once the
    # views.evidence_review row is registered. Naming a future action id here
    # would whitelist an unregistered row, so the source stays empty.
    return {
        "source_action": "",
        "pending": (
            "engine_api.evidence_review_queue + the views.evidence_review registry row "
            "(V2 plan V2R-B.4)"
        ),
    }


def _flow_panel() -> dict[str, Any]:
    # Both-branch live consumption lands with the triage renderer (C.3) once
    # T.3 registers dashboard.read against a live engine binding.
    return {
        "source_action": "",
        "pending": "the dashboard.read registry row (U2 plan T.3)",
    }


LAYOUT_COLUMNS = 80


def render_findings(findings: list[dict[str, Any]]) -> list[str]:
    """cli-voice-findings (U2 spec §4): the honesty-card fields verbatim —
    finding/action, argument-for/against only when both sides are present
    (one-sided arguments drop — V2's card grammar), tipped-by, coarse
    certainty, and the read the card came from when it carries one. Never a
    verdict line, never a pre-selected action. One function, used by every panel
    (and by section T's preview screen)."""
    lines: list[str] = []
    for card in findings:
        headline = str(card.get("finding") or card.get("action") or "")
        if headline:
            lines.extend(_fit("  - ", headline))
        if card.get("argument_for") and card.get("argument_against"):
            lines.extend(_fit("    for: ", str(card["argument_for"])))
            lines.extend(_fit("    against: ", str(card["argument_against"])))
        if card.get("what_tipped_it"):
            lines.extend(_fit("    tipped by: ", str(card["what_tipped_it"])))
        if card.get("certainty"):
            lines.extend(_fit("    certainty: ", str(card["certainty"])))
        if card.get("source_action"):
            lines.extend(_fit("    from: ", str(card["source_action"])))
    return lines


def render_deep(payload: dict[str, Any]) -> str:
    """The deep screen (U2 spec §1/§2): fixed panel order, plain sequential
    text, static per invocation. No curses, no ANSI, no tty branching —
    `memoria cockpit | cat` is byte-identical by construction."""
    if payload.get("resolution") == "ambiguous":
        return _render_ambiguous(payload)
    panels = payload["panels"]
    lines: list[str] = ["memoria cockpit: deep work"]
    lines.extend(_fit("project: ", str(payload.get("project") or "")))
    lines.append("")

    project = panels["project"]
    lines.append(_heading("project", project))
    lines.extend(_fit("  title: ", project["title"]))
    if project["thesis"]:
        lines.extend(_fit("  thesis: ", project["thesis"]))
    lines.append(f"  archived: {'yes' if project['archived'] else 'no'}")
    lines.append("")

    slice_panel = panels["slice"]
    lines.append(_heading("slice", slice_panel))
    lines.append(f"  members: {slice_panel['members']}")
    edges = " ".join(f"{kind}={count}" for kind, count in slice_panel["edges_by_type"].items())
    lines.extend(_fit("  edges: ", edges or "none"))
    lines.append(f"  unresolved outline ids: {slice_panel['missing']}")
    lines.append("")

    draft = panels["draft"]
    lines.append(_heading("draft", draft))
    lines.extend(_fit("  draft path: ", draft["draft_path"]))
    lines.append(f"  draft present: {'yes' if draft['draft_present'] else 'no'}")
    lines.append(f"  outline members: {draft['outline_members']}")
    states = " ".join(f"{state}={count}" for state, count in draft["evidence_states"].items())
    lines.extend(_fit("  evidence states: ", states or "none"))
    lines.append(f"  review required: {draft['review_required']}")
    lines.append("")

    grounds = panels["grounds"]
    lines.append(_heading("grounds", grounds))
    lines.append(f"  complete evidence sets: {grounds['complete']}/{grounds['total']}")
    lines.extend(render_findings(grounds["findings"]) or ["  (no gaps or thin claims)"])
    lines.append("")

    trace = panels["trace"]
    lines.append(_heading("recent machine changes", trace))
    lines.extend(_trace_lines(trace))
    lines.append("")

    context = panels["context"]
    lines.append(_heading("context handoff", context))
    lines.extend(_context_lines(context))
    return _buffer(lines)


def _trace_lines(trace: dict[str, Any]) -> list[str]:
    if "pending" in trace:
        return _fit("  pending: ", str(trace["pending"]))
    lines: list[str] = []
    for event in trace.get("events") or []:
        ref = str(event.get("event_id", ""))
        summary = " ".join(
            str(event[key]) for key in ("timestamp", "event_type", "output_id") if event.get(key)
        )
        lines.extend(_fit(f"  ref {ref}: ", summary or "(no summary fields)"))
    if not lines:
        lines.append("  (no machine changes recorded)")
    if "total" in trace and "shown" in trace:
        lines.append(f"  showing {trace['shown']} of {trace['total']}")
    if trace.get("events"):
        # Only advertise the preview when there is a ref to preview with.
        lines.append("  refs preview via trace.revert_preview")
    return lines


def _context_lines(context: dict[str, Any]) -> list[str]:
    if "reserved" in context:
        return _fit("  reserved: ", str(context["reserved"]))
    lines: list[str] = []
    for key in sorted(context.get("bundle") or {}):
        lines.extend(_fit(f"  {key}: ", _scalar(context["bundle"][key])))
    lines.extend(_fit("  invocation: ", str(context["invocation"])))
    return lines


def _render_ambiguous(payload: dict[str, Any]) -> str:
    projects = payload.get("projects") or []
    lines = ["memoria cockpit: active-project resolution", ""]
    if projects:
        lines.append(f"{len(projects)} active projects; pass --project <path>:")
        for row in projects:
            lines.extend(_fit("  ", f"{row['path']}  ({row['title']})"))
    else:
        lines.append("no active projects (type: project, archived not True)")
        lines.append("pass --project <path> to open one directly")
    return _buffer(lines)


def _heading(label: str, panel: dict[str, Any]) -> str:
    source = str(panel.get("source_action") or "")
    return f"{label} ({source})" if source else f"{label} (no registry row yet)"


def _fit(prefix: str, value: str) -> list[str]:
    """80-column layout target; identifiers are never wrapped
    mid-identifier — a token longer than the layout renders whole on its
    own line (keep-test, U2 spec §2)."""
    line = f"{prefix}{value}"
    if len(line) <= LAYOUT_COLUMNS:
        return [line]
    return textwrap.wrap(
        line,
        width=LAYOUT_COLUMNS,
        subsequent_indent=" " * len(prefix),
        break_long_words=False,
        break_on_hyphens=False,
    )


def _scalar(value: Any) -> str:
    if isinstance(value, str):
        return value
    return json.dumps(value, ensure_ascii=False, sort_keys=True)


def _buffer(lines: list[str]) -> str:
    return "\n".join(lines).rstrip("\n") + "\n"
