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
from memoria_vault.runtime.policy.paths import normalize_path, within_scope
from memoria_vault.runtime.trusted_writer import EVENT_DERIVED


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
        "review": _review_panel(vault, read_scope=read_scope),
        "flow": _flow_panel(vault),
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


TRACE_PANEL_LIMIT = 8


def trace_panel(
    vault: Path,
    project_path: str,
    *,
    limit: int = TRACE_PANEL_LIMIT,
    read_scope: list[str] | None = None,
) -> dict[str, Any]:
    """Panel 5 (U2 spec §1): the recent machine changes inside one project slice.

    *What "in this slice" means for a journal row.* The ids
    `project.slice.read` exposes — the project, its outline, each resolved
    outline member — become the `journal.list` read scope, so the shipped
    journal predicate decides membership instead of a second one written here:
    a row is in the slice exactly when it names at least one path and *every*
    path it names is in the slice (`engine.api._journal_in_scope`'s `all(...)`
    over `_journal_paths`, which sweeps `output_id`/`target_id`/`target_path`/
    `new_path`/`linked_id`/`quarantined_id` plus the `outputs`/`paths`/`targets`
    lists). A run that also wrote outside the slice is not a change *to* this
    slice, and a row naming no path at all is not a change to any. The caller's
    own `read_scope` narrows the slice ids first, so the read can only ever see
    rows inside both bounds (scoped-trace amendment §1).

    *Which rows are previewable.* Only `derived` rows are shown. `derived` is
    the only journal event that writes the `outputs` record T.2's
    `read_revert_preview(workspace, event_id)` resolves —
    `state.record_file_output` has exactly two call sites, both trusted-writer
    derivations — so `check-fired` (which carries `target_id` and no output
    record) and the PI-edit observation would be refs the preview cannot
    preview. The trace is deliberately *not* filtered by `actor`:
    `OperationContext.actor` is authority, not authorship, so a PI-authorized
    machine derivation is still a machine change.

    Newest first, because `journal.list` orders by `event_id DESC`. `total` is
    every in-slice derived row; `shown` is only what the limit left.
    """
    vault = Path(vault)
    project_slice = engine_api.read_slice(vault, project_path, read_scope=read_scope)["slice"]
    events = [
        {
            "event_id": int(row["event_id"]),
            "timestamp": str(row["timestamp"]),
            "event_type": str(row["event_type"]),
            # A derived row that named a path other than its output still
            # belongs on the trace; naming which record is missing is the
            # preview's job (U2 spec §3), not a reason to hide the change.
            "output_id": str(row["payload"].get("output_id") or ""),
        }
        for row in engine_api.read_journal(
            vault,
            limit=_journal_depth(vault),
            read_scope=_slice_scope(project_slice, read_scope),
        )["events"]
        if row["event_type"] == EVENT_DERIVED
    ]
    shown = events[:limit]
    return {
        "source_action": "journal.list",
        "events": shown,
        "total": len(events),
        "shown": len(shown),
    }


def _slice_scope(project_slice: dict[str, Any], read_scope: list[str] | None) -> list[str]:
    """The project slice as a journal read scope, narrowed by the caller's own.

    `read_slice` scope-checks only the outline, so a member can sit outside the
    caller's scope; carrying it into the journal read would let the panel widen
    a bounded read. The narrowing calls the shared `within_scope` predicate —
    the one `engine.api._scope_allows` wraps and `http_transport` narrows
    request scopes with — rather than a second copy of it. `normalize_path`
    cannot raise here: `read_slice` ran the same normalization over the same
    `read_scope` first and turned a traversal into `project slice not found`.
    """
    ids = [
        path
        for path in (
            normalize_path(str(project_slice["project_path"])),
            normalize_path(str(project_slice["outline_path"])),
            *(normalize_path(str(member["path"])) for member in project_slice["members"]),
        )
        if path
    ]
    if read_scope is None:
        return ids
    bounds = [normalize_path(scope) for scope in read_scope]
    return [path for path in ids if within_scope(path, bounds)]


def _journal_depth(vault: Path) -> int:
    """A `journal.list` limit that its bounded tail cannot truncate.

    `read_journal` is `ORDER BY event_id DESC LIMIT ?` and applies its scope
    filter *after* the limit, so any fixed window — its own default is 50 —
    would quietly turn the panel's `total` into a count of the window instead of
    a count of the slice. Journal ids are assigned `last + 1` from 1
    (`state._insert_journal_row_conn`), so the newest id is an upper bound on
    the number of rows and a limit that large reads all of them.

    The sizing read keeps the id and never the row. `read_journal`'s own SQL is
    unscoped too: `read_scope` bounds what a caller is told, not what the engine
    may count.
    """
    newest = engine_api.read_journal(vault, limit=1)["events"]
    return int(newest[0]["event_id"]) if newest else 0


def _context_panel(vault: Path, *, read_scope: list[str] | None = None) -> dict[str, Any]:
    """Panel 6 (U2 spec §1 panel 6): wrap the live `context.read` transport.

    C.3 wrote this both-branch while `context.read` was U1's reserved row. T.3
    wired it, and the row's live shape is now pinned by
    test_surface_contract.py::test_surface_contract_context_read_row_is_wired
    (`"reserved" not in action`, engine `read_context`) and by the registry's
    own engine-binding sweep, so no producer state can put the panel back on
    a reserved branch without failing those first — the honest-absence branch
    was deleted rather than left as a line no fixture can reach. `_flow_panel`
    below keeps its both-branch form on INT.1's own instruction, even though
    `dashboard.read` has since landed: its fallback is the arm the *review*
    panel beside it still genuinely needs, and the two share one renderer.
    """
    row = actions_by_id()["context.read"]
    payload = getattr(engine_api, str(row["engine"]))(Path(vault), read_scope=read_scope)
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


QUEUE_ROW_KINDS = frozenset({"evidence-set", "srd-gap"})


def _review_panel(vault: Path, *, read_scope: list[str] | None = None) -> dict[str, Any]:
    """Triage panel 2 (U2 spec §1): V2's review queue, counted and linked with the
    `memoria review` invocation — never re-hosted.

    Both-branch, and the live branch needs both halves of V2R-B.4 (raw-counts
    amendment 2026-07-29 §1): the engine-direct `evidence_review_queue` collector
    it counts, and the registered `views.evidence_review` row, the only registry
    id this panel may name. Either half alone is not a seam — an unregistered id
    would be whitelisting a future row, and a row without the collector has
    nothing to count — so the panel stays pending and does not read.

    The counts come from the raw queue read once with `batch=0`; the view
    projection is deliberately never called, because counting cards means parsing
    a shape V2 owns and re-hosting the review surface.
    """
    queue = getattr(engine_api, "evidence_review_queue", None)
    if queue is None or "views.evidence_review" not in actions_by_id():
        return {
            "source_action": "",
            "pending": (
                "engine_api.evidence_review_queue + the views.evidence_review registry row "
                "(V2 plan V2R-B.4)"
            ),
        }
    rows = queue(Path(vault), batch=0, read_scope=read_scope)["rows"]
    if rows and not any(row.get("kind") in QUEUE_ROW_KINDS for row in rows):
        # A queue that returned rows, none of which carry a `kind` this panel
        # knows, is a *shape* mismatch — not an empty queue. Counting it anyway
        # renders a confident `open: 0  (none)` under the row's own heading:
        # honest about absence, structurally blind to shape. V2's raw-row
        # grammar is the discriminated union in its 2026-07-29 amendment §2,
        # but two superseded layers of that plan still describe a CLI DTO with
        # no `kind` at all, so this is a live way for the seam to land wrong.
        # Say so, the way the absent-producer branch says absence.
        return {
            "source_action": "views.evidence_review",
            "pending": (
                f"{len(rows)} queue rows carry no evidence-set/srd-gap kind — the raw "
                "queue shape changed (V2 plan amendment 2026-07-29 §2)"
            ),
        }
    counts = Counter(
        str(row.get("disposition") or "open") for row in rows if row.get("kind") == "evidence-set"
    )
    return {
        "source_action": "views.evidence_review",
        "open": counts.get("open", 0),
        "counts": dict(sorted(counts.items())),
        # SRD gaps carry no disposition — they are read-only in the queue, and
        # counting them among the review dispositions would claim decisions that
        # cannot be made.
        "srd_gaps": sum(1 for row in rows if row.get("kind") == "srd-gap"),
    }


def _flow_panel(vault: Path) -> dict[str, Any]:
    """Triage panel 3 (U2 spec §1): the dashboard flow line — open total,
    inflow/drain, oldest non-empty age bucket.

    Registered-only composition (amendment 2026-07-29 §2/§3): the panel calls
    whatever engine the `dashboard.read` row binds and never `assemble_dashboard`
    directly, which would reconstruct a view I1 owns. A row without a live engine
    binding is a reservation, not a producer, so it names nothing. The row is
    workspace-scope (I1 H.2: no params), which is why this is the one panel that
    takes no `read_scope`.
    """
    row = actions_by_id().get("dashboard.read") or {}
    engine_name = str(row.get("engine") or "")
    if not engine_name or not hasattr(engine_api, engine_name):
        return {
            "source_action": "",
            "pending": "the dashboard.read registry row (U2 plan T.3)",
        }
    flow = getattr(engine_api, engine_name)(Path(vault))["dashboard"]["attention_flow"]
    ages = flow.get("age_distribution") or {}
    oldest = next((bucket for bucket in (">30d", "8-30d", "0-7d") if ages.get(bucket)), "none")
    return {
        "source_action": "dashboard.read",
        "open_total": int(flow.get("open_total") or 0),
        "inflow": sum((flow.get("inflow_by_day") or {}).values()),
        "drain": sum((flow.get("drain_by_day") or {}).values()),
        "oldest": oldest,
    }


LAYOUT_COLUMNS = 80


def render_findings(findings: list[dict[str, Any]]) -> list[str]:
    """cli-voice-findings (U2 spec §4): the honesty-card fields verbatim —
    finding/action, argument-for/against only when both sides are present
    (one-sided arguments drop — V2's card grammar), tipped-by, coarse
    certainty, and the read the card came from when it carries one. Never a
    verdict line, never a pre-selected action.

    One function for every panel whose rows *are* honesty cards: panel 4 today,
    and section T's preview screen. The triage panels deliberately do not call
    it — attention cards carry the honesty fields only inside
    `card["frontmatter"]`, so reaching for them would couple the composer to a
    card shape no contract names, and spec §1 triage 1 names exactly one per-row
    disclosure (`rank_factors`). See C.3's amendment 8 in the U2 plan."""
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
    # No `reserved` arm: `_context_panel` is the only producer of this panel
    # and stopped emitting one when T.3 wired the row. A renderer branch whose
    # producer is gone is the same unfixturable line, one layer down.
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


def render_triage(payload: dict[str, Any]) -> str:
    """The triage screen (U2 spec §1/§2): worklist / review / flow in fixed order,
    worklist rows in the projection's payload order verbatim, static plain text.

    The two screens never mix — this one shows no draft, and the deep screen shows
    no queue. Review is *counted and linked*, never re-hosted: the `memoria review`
    line is the invocation, V2 owns the cards.
    """
    panels = payload["panels"]
    lines: list[str] = ["memoria cockpit: triage", ""]

    worklist = panels["worklist"]
    lines.append(_heading("attention worklist", worklist))
    cards = worklist["cards"]
    if not cards:
        lines.append("  (worklist empty)")
    for index, card in enumerate(cards, start=1):
        lines.extend(_fit(f"  {index}. ", f"{card['title']}  [{card['kind']}]  {card['path']}"))
        factors = card.get("rank_factors")
        if isinstance(factors, dict) and factors:
            # I1 owns the rank; the cockpit discloses the factors the card
            # carries, in the renderer's own fixed key order.
            disclosed = " ".join(f"{key}={factors[key]}" for key in sorted(factors))
            lines.extend(_fit("     rank: ", disclosed))
    lines.append("")

    review = panels["review"]
    lines.append(_heading("review queue", review))
    if "pending" in review:
        lines.extend(_fit("  pending: ", str(review["pending"])))
    else:
        counts = " ".join(f"{key}={value}" for key, value in review["counts"].items())
        lines.extend(_fit("  open: ", f"{review['open']}  ({counts or 'none'})"))
        lines.append(f"  srd gaps: {review['srd_gaps']}")
    lines.append("  hosted by: memoria review (V2)")
    lines.append("")

    flow = panels["flow"]
    lines.append(_heading("flow", flow))
    if "pending" in flow:
        lines.extend(_fit("  pending: ", str(flow["pending"])))
    else:
        lines.extend(
            _fit(
                "  ",
                f"open {flow['open_total']} | inflow {flow['inflow']} / "
                f"drain {flow['drain']} | oldest {flow['oldest']}",
            )
        )
    return _buffer(lines)


def _buffer(lines: list[str]) -> str:
    return "\n".join(lines).rstrip("\n") + "\n"
