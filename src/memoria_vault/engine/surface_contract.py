"""Shared action registry for Memoria control surfaces."""

from __future__ import annotations

from typing import Any

SURFACE_CONTRACT_VERSION = "surface-contract.v1"
ENGINE_READ_API_VERSION = "engine-read-api.v1"
SURFACE_JOBS: tuple[str, ...] = ("read", "knowledge", "project", "review", "upkeep")

SURFACE_ACTIONS: tuple[dict[str, Any], ...] = (
    # status-paths-action (U1 spec §3): MAPPED here, not reserved — this
    # row's payload already carries the workspace-paths disclosure
    # (workspace root + relative state-db path; engine/api.py read_status).
    # Enforced by tests/test_surface_contract.py::
    # test_surface_contract_status_paths_maps_to_status_read.
    {
        "id": "status.read",
        "job": "read",
        "summary": "Read engine status.",
        "engine": "read_status",
        "kind": "read",
        "scope": "workspace",
        "params": {},
        "http": {"method": "GET", "path": "/status"},
        "mcp": {"tool": "status"},
        "cli": {"commands": ["memoria status"]},
        "response_version": ENGINE_READ_API_VERSION,
    },
    {
        "id": "operations.list",
        "job": "read",
        "summary": "List packaged operations.",
        "engine": "read_operations",
        "kind": "read",
        "scope": "workspace",
        "params": {},
        "http": {"method": "GET", "path": "/operations"},
        "mcp": {"tool": "operations"},
        "cli": {"commands": ["memoria operation list"]},
        "response_version": ENGINE_READ_API_VERSION,
    },
    {
        "id": "surface.openapi",
        "job": "read",
        "summary": "Read the local HTTP OpenAPI schema.",
        "engine": "read_surface_schema",
        "kind": "read",
        "scope": "workspace",
        "params": {},
        "http": {"method": "GET", "path": "/openapi.json"},
        # No response_version: the http handler (http_transport.openapi_schema)
        # returns a raw OpenAPI 3.1 document for external tooling, not a
        # Memoria read-API envelope, so it intentionally carries no
        # api_version key. response_version is optional in this contract
        # precisely for actions like this one — see actions_by_id() callers
        # and tests/test_floor_sweep_reads.py for how the absence is handled.
    },
    {
        "id": "surface.schema",
        "job": "read",
        "summary": "Print the shared surface contract schema.",
        "engine": "read_surface_schema",
        "kind": "read",
        "scope": "workspace",
        "params": {},
        "cli": {"commands": ["memoria surface schema"]},
        "response_version": ENGINE_READ_API_VERSION,
    },
    {
        "id": "requests.list",
        "job": "review",
        "summary": "List operation requests.",
        "engine": "read_requests",
        "kind": "read",
        "scope": "optional-read-scope",
        "params": {"status": {"type": "string", "default": ""}},
        "http": {"method": "GET", "path": "/requests"},
        "mcp": {"tool": "requests"},
        "cli": {"commands": ["memoria request list"]},
        "response_version": ENGINE_READ_API_VERSION,
    },
    {
        "id": "requests.get",
        "job": "review",
        "summary": "Read one operation request.",
        "engine": "read_request",
        "kind": "read",
        "scope": "optional-read-scope",
        "params": {"request_id": {"type": "string", "required": True}},
        "http": {
            "method": "GET",
            "path": "/request",
            "params": {"id": {"type": "string", "required": True}},
        },
        "mcp": {"tool": "request"},
        "cli": {"commands": ["memoria request show"]},
        "response_version": ENGINE_READ_API_VERSION,
    },
    {
        "id": "attention.list",
        "job": "review",
        "summary": "List attention items.",
        "engine": "read_attention",
        "kind": "read",
        "scope": "optional-read-scope",
        "params": {
            "status": {"type": "string", "default": ""},
            "kind": {"type": "string", "default": ""},
            "worklist": {"type": "boolean", "default": False},
        },
        "http": {"method": "GET", "path": "/attention"},
        "mcp": {"tool": "attention"},
        "cli": {"commands": ["memoria attention list", "memoria attention worklist"]},
        "response_version": ENGINE_READ_API_VERSION,
    },
    {
        "id": "attention.get",
        "job": "review",
        "summary": "Read one attention item.",
        "engine": "read_attention_card",
        "kind": "read",
        "scope": "optional-read-scope",
        "params": {"path": {"type": "string", "required": True}},
        "http": {"method": "GET", "path": "/attention/card"},
        "mcp": {"tool": "attention_card"},
        "cli": {"commands": ["memoria attention show"]},
        "response_version": ENGINE_READ_API_VERSION,
    },
    {
        "id": "views.attention",
        "job": "review",
        "summary": "Render the attention pane view.",
        "engine": "read_attention_view",
        "kind": "read",
        "scope": "optional-read-scope",
        "params": {"summary": {"type": "boolean", "default": False}},
        "http": {"method": "GET", "path": "/v1/views/attention"},
        "response_version": ENGINE_READ_API_VERSION,
    },
    {
        "id": "views.evidence_review",
        "job": "review",
        "summary": "Render the evidence-review queue view.",
        "engine": "read_evidence_review_view",
        "kind": "read",
        "scope": "optional-read-scope",
        "params": {
            "routing_type": {"type": "string", "default": ""},
            "project": {"type": "string", "default": ""},
            "min_age_days": {"type": "integer", "default": 0},
            "batch": {"type": "integer", "default": 10},
        },
        "http": {"method": "GET", "path": "/v1/views/evidence-review"},
        "response_version": ENGINE_READ_API_VERSION,
    },
    # No cli/mcp binding: this row is the HTTP view only. The engine-direct
    # `memoria dashboard` front is a separate command reading through U2 T.3's
    # `dashboard.read` row below — two rows over one assembler, each declaring
    # the transport it actually serves.
    # Workspace scope with no params: the panels are vault-wide raw counts, so
    # there is nothing for a read_scope to narrow and no filter to accept.
    {
        "id": "views.dashboard",
        "job": "review",
        "summary": "Render the raw-count instrumentation dashboard view.",
        "engine": "read_dashboard_view",
        "kind": "read",
        "scope": "workspace",
        "params": {},
        "http": {"method": "GET", "path": "/v1/views/dashboard"},
        "response_version": ENGINE_READ_API_VERSION,
    },
    {
        "id": "concepts.list",
        "job": "read",
        "summary": "List scoped Concept summaries.",
        "engine": "read_concepts",
        "kind": "read",
        "scope": "optional-read-scope",
        "params": {"concept_type": {"type": "string", "default": ""}},
        "http": {"method": "GET", "path": "/concepts", "params": {"type": {"type": "string"}}},
        "mcp": {"tool": "concepts"},
        "cli": {"commands": ["memoria list"]},
        "response_version": ENGINE_READ_API_VERSION,
    },
    {
        "id": "concepts.get",
        "job": "read",
        "summary": "Read one Concept.",
        "engine": "read_concept",
        "kind": "read",
        "scope": "optional-read-scope",
        "params": {"target": {"type": "string", "required": True}},
        "http": {"method": "GET", "path": "/concept"},
        "mcp": {"tool": "concept"},
        "cli": {"commands": ["memoria show"]},
        "response_version": ENGINE_READ_API_VERSION,
    },
    {
        "id": "work.get",
        "job": "read",
        "summary": "Read one Work catalog record.",
        "engine": "read_work",
        "kind": "read",
        "scope": "optional-read-scope",
        "params": {"work_id": {"type": "string", "required": True}},
        "http": {
            "method": "GET",
            "path": "/work",
            "params": {"id": {"type": "string", "required": True}},
        },
        "mcp": {"tool": "work"},
        "response_version": ENGINE_READ_API_VERSION,
    },
    {
        "id": "journal.list",
        "job": "read",
        "summary": "List journal events.",
        "engine": "read_journal",
        "kind": "read",
        "scope": "optional-read-scope",
        "params": {
            "operation": {"type": "string", "default": ""},
            "request_id": {"type": "string", "default": ""},
            "path": {"type": "string", "default": ""},
            "decision": {"type": "string", "default": ""},
            "date": {"type": "string", "default": ""},
            "limit": {"type": "integer", "default": 50},
        },
        "http": {"method": "GET", "path": "/journal"},
        "mcp": {"tool": "journal"},
        "cli": {"commands": ["memoria journal tail"]},
        "response_version": ENGINE_READ_API_VERSION,
    },
    {
        "id": "journal.get",
        "job": "read",
        "summary": "Read one journal event.",
        "engine": "read_journal_event",
        "kind": "read",
        "scope": "optional-read-scope",
        "params": {"event_id": {"type": "integer", "required": True}},
        "http": {"method": "GET", "path": "/journal/event"},
        "mcp": {"tool": "journal_event"},
        "cli": {"commands": ["memoria journal show"]},
        "response_version": ENGINE_READ_API_VERSION,
    },
    {
        "id": "exploration.list",
        "job": "read",
        "summary": "Read recent exploration channel events.",
        "engine": "read_exploration",
        "kind": "read",
        "scope": "optional-read-scope",
        "params": {"limit": {"type": "integer", "default": 10}},
        "http": {"method": "GET", "path": "/exploration"},
        "mcp": {"tool": "exploration"},
        "response_version": ENGINE_READ_API_VERSION,
    },
    {
        "id": "explore.read",
        "job": "read",
        "summary": (
            "Surface a checked topic neighborhood. Distinct from memoria project explore, "
            "which lists exploration-channel candidates."
        ),
        "engine": "read_explore",
        "kind": "read",
        "scope": "workspace",
        "params": {
            "topic": {"type": "string", "required": True},
            "versus": {"type": "string", "default": ""},
            "project": {"type": "string", "default": ""},
            "depth": {"type": "integer", "default": 1},
            "trace": {"type": "boolean", "default": False},
        },
        "cli": {"commands": ["memoria explore"]},
        "response_version": ENGINE_READ_API_VERSION,
    },
    {
        "id": "project.slice.read",
        "job": "project",
        "summary": "Read a project slice.",
        "engine": "read_slice",
        "kind": "read",
        "scope": "optional-read-scope",
        "params": {"project_path": {"type": "string", "required": True}},
        "http": {"method": "GET", "path": "/project/slice"},
        "mcp": {"tool": "project_slice"},
        "response_version": ENGINE_READ_API_VERSION,
    },
    {
        "id": "project.draft.read",
        "job": "project",
        "summary": "Read a project draft.",
        "engine": "read_draft",
        "kind": "read",
        "scope": "optional-read-scope",
        "params": {"project_path": {"type": "string", "required": True}},
        "http": {"method": "GET", "path": "/project/draft"},
        "mcp": {"tool": "project_draft"},
        "response_version": ENGINE_READ_API_VERSION,
    },
    {
        # context-read-set-action / situated-context-read: U1 spec §3 RESERVED
        # this row for its first-needing surface; U2 spec §1 panel 6 is that
        # surface, so U2 T.3 wired it. U1 still owns the ownership narrative —
        # U2 added only the engine binding and the CLI transport, and U4
        # consumes the same bundle. The situated-context bundle is computed
        # from shipped reads only (engine/api.py read_context).
        "id": "context.read",
        "job": "read",
        "summary": "Read the situated context bundle for the active session.",
        "engine": "read_context",
        "kind": "read",
        "scope": "optional-read-scope",
        "params": {},
        "cli": {"commands": ["memoria context"]},
        "response_version": ENGINE_READ_API_VERSION,
    },
    {
        # U2 spec §5: the cockpit composer's own row — cli-only; --triage is
        # a flag documented on this same row (one composer, two screens).
        "id": "cockpit.read",
        "job": "project",
        "summary": "Compose the deep-work or triage cockpit screens from registry reads.",
        "engine": "read_cockpit",
        "kind": "read",
        "scope": "optional-read-scope",
        "params": {
            "project_path": {"type": "string", "default": ""},
            "triage": {"type": "boolean", "default": False},
        },
        "cli": {"commands": ["memoria cockpit"]},
        "response_version": ENGINE_READ_API_VERSION,
    },
    {
        # U2 spec §3: read-only cascade-rollback preview over a trace ref. The
        # ref is a journal event id — the datum `cockpit.trace_panel` puts on
        # every line (U2 scoped-trace amendment §2).
        "id": "trace.revert_preview",
        "job": "project",
        "summary": "Preview what cascade-rollback would quarantine or flag for a journal event.",
        "engine": "read_revert_preview",
        "kind": "read",
        "scope": "optional-read-scope",
        "params": {"event_id": {"type": "integer", "required": True}},
        "cli": {"commands": ["memoria journal revert-preview"]},
        "response_version": ENGINE_READ_API_VERSION,
    },
    {
        # U2 spec §1 (triage note): I1 H.2 ships the assembler and the HTTP
        # view above; this is the registry entry for its engine-direct CLI
        # front, so `memoria dashboard` reads *through* a row rather than
        # reaching past it into `engine.dashboard`. Two rows over one
        # assembler — U2 owns only this one and changes neither
        # `views.dashboard` nor `read_dashboard_view`.
        # Workspace scope with no params, inherited from the assembler: the
        # panels are vault-wide raw counts, so there is nothing a read_scope
        # could narrow and no filter to accept.
        "id": "dashboard.read",
        "job": "review",
        "summary": "Read the honest dashboard panels (raw counts, no score).",
        "engine": "read_dashboard",
        "kind": "read",
        "scope": "workspace",
        "params": {},
        "cli": {"commands": ["memoria dashboard"]},
        "response_version": ENGINE_READ_API_VERSION,
    },
    {
        "id": "operation.run",
        "job": "upkeep",
        "summary": "Run one packaged operation.",
        "engine": "run_operation",
        "kind": "write",
        "scope": "workspace",
        "params": {
            "operation_id": {"type": "string", "required": True},
            "payload": {"type": "object", "default": {}},
            "idempotency_key": {"type": "string", "default": ""},
        },
        "http": {"method": "POST", "path": "/operation/run"},
        "mcp": {"tool": "operation_run"},
        "cli": {"commands": ["memoria operation run"]},
        "response_version": ENGINE_READ_API_VERSION,
    },
)


def actions_by_id() -> dict[str, dict[str, Any]]:
    return {str(action["id"]): action for action in SURFACE_ACTIONS}


def http_routes() -> set[tuple[str, str]]:
    return {
        (str(action["http"]["method"]), str(action["http"]["path"]))
        for action in SURFACE_ACTIONS
        if isinstance(action.get("http"), dict)
    }


def mcp_tools() -> set[str]:
    return {
        str(action["mcp"]["tool"])
        for action in SURFACE_ACTIONS
        if isinstance(action.get("mcp"), dict)
    }


def cli_commands() -> set[str]:
    commands: set[str] = set()
    for action in SURFACE_ACTIONS:
        cli = action.get("cli")
        if isinstance(cli, dict):
            commands.update(str(command) for command in cli.get("commands") or [])
    return commands
