"""Shared action registry for Memoria control surfaces."""

from __future__ import annotations

from typing import Any

SURFACE_CONTRACT_VERSION = "surface-contract.v1"
ENGINE_READ_API_VERSION = "engine-read-api.v1"

SURFACE_ACTIONS: tuple[dict[str, Any], ...] = (
    {
        "id": "status.read",
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
        "summary": "Read the local HTTP OpenAPI schema.",
        "engine": "read_surface_schema",
        "kind": "read",
        "scope": "workspace",
        "params": {},
        "http": {"method": "GET", "path": "/openapi.json"},
        "response_version": ENGINE_READ_API_VERSION,
    },
    {
        "id": "requests.list",
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
        "id": "concepts.list",
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
        "id": "project.slice.read",
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
        "id": "operation.run",
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
