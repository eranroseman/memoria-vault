from __future__ import annotations

from pathlib import Path

import pytest

from memoria_vault.engine import api as engine_api
from memoria_vault.engine.surface_contract import (
    SURFACE_ACTIONS,
    SURFACE_CONTRACT_VERSION,
    SURFACE_JOBS,
    actions_by_id,
    cli_commands,
    http_routes,
    mcp_tools,
)
from tests.cli_test_helpers import _cli_command_surface
from tests.helpers import init_cli_workspace


def test_surface_contract_registry_is_minimal_and_unique() -> None:
    expected = {
        "status.read",
        "operations.list",
        "surface.openapi",
        "surface.schema",
        "requests.list",
        "requests.get",
        "attention.list",
        "attention.get",
        "concepts.list",
        "concepts.get",
        "work.get",
        "journal.list",
        "journal.get",
        "exploration.list",
        "explore.read",
        "project.slice.read",
        "project.draft.read",
        "context.read",
        "operation.run",
    }

    assert SURFACE_CONTRACT_VERSION == "surface-contract.v1"
    assert set(actions_by_id()) == expected
    assert len(SURFACE_ACTIONS) == len(expected)
    assert all(
        hasattr(engine_api, action["engine"])
        for action in SURFACE_ACTIONS
        if "reserved" not in action
    )
    assert all(
        isinstance(action.get("reserved"), str)
        and bool(action["reserved"])
        and action.get("engine") is None
        and not any(key in action for key in ("http", "mcp", "cli"))
        for action in SURFACE_ACTIONS
        if "reserved" in action
    )


def test_surface_contract_explore_is_cli_only_with_current_shape() -> None:
    action = actions_by_id()["explore.read"]

    assert action == {
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
        "response_version": engine_api.READ_API_VERSION,
    }


def test_surface_contract_matches_current_http_and_mcp_bindings() -> None:
    assert http_routes() == {
        ("GET", "/status"),
        ("GET", "/operations"),
        ("GET", "/openapi.json"),
        ("GET", "/requests"),
        ("GET", "/request"),
        ("GET", "/attention"),
        ("GET", "/attention/card"),
        ("GET", "/concepts"),
        ("GET", "/concept"),
        ("GET", "/work"),
        ("GET", "/journal"),
        ("GET", "/journal/event"),
        ("GET", "/project/slice"),
        ("GET", "/project/draft"),
        ("GET", "/exploration"),
        ("POST", "/operation/run"),
    }
    assert mcp_tools() == {
        "status",
        "operations",
        "requests",
        "request",
        "attention",
        "attention_card",
        "concepts",
        "concept",
        "work",
        "journal",
        "journal_event",
        "exploration",
        "project_slice",
        "project_draft",
        "operation_run",
    }


def test_surface_contract_binds_project_reads_to_http_and_mcp() -> None:
    actions = actions_by_id()

    assert actions["exploration.list"]["mcp"]["tool"] == "exploration"
    assert actions["project.slice.read"]["mcp"]["tool"] == "project_slice"
    assert actions["project.draft.read"]["mcp"]["tool"] == "project_draft"
    assert [action["id"] for action in SURFACE_ACTIONS if action["kind"] == "write"] == [
        "operation.run"
    ]


# Pure-CLI conveniences and write/maintenance commands that deliberately
# carry no SURFACE_ACTIONS row (U1 spec §1: CLI parity is EQUALITY against
# the pinned parser surface minus exactly this named list). A new parser
# command fails parity until it either registers a registry row or is added
# here deliberately. Rows arriving from merged specs (R2 ask/explore, V2
# review, I1 dashboard, O1 onboard) move their commands out of this list.
CLI_ONLY_COMMANDS: set[str] = {
    "memoria init",
    "memoria onboard",
    "memoria doctor",
    "memoria doctor bundle",
    "memoria doctor self-test",
    "memoria ask",
    "memoria secrets set",
    "memoria secrets list",
    "memoria serve",
    "memoria handshake",
    "memoria mcp",
    "memoria help",
    "memoria new hub",
    "memoria new note",
    "memoria new project",
    "memoria work add",
    "memoria work import",
    "memoria work enrich",
    "memoria work digest",
    "memoria work interview",
    "memoria work update",
    "memoria work export",
    "memoria link",
    "memoria check",
    "memoria export",
    "memoria project ask",
    "memoria project trace",
    "memoria project frame-paper",
    "memoria project gaps",
    "memoria project slice",
    "memoria project compose",
    "memoria project verify",
    "memoria project resolve-evidence",
    "memoria project promote",
    "memoria project explore",
    "memoria project suggest-hubs",
    "memoria project export",
    "memoria request answer",
    "memoria request amend",
    "memoria request cancel",
    "memoria request retry",
    "memoria request resume",
    "memoria attention resolve",
    "memoria steering show",
    "memoria steering edit",
    "memoria vocab list",
    "memoria vocab add",
    "memoria vocab merge",
    "memoria vocab rename",
    "memoria journal verify",
    "memoria workspace scan",
    "memoria workspace run",
    "memoria workspace recover",
    "memoria workspace rollback",
    "memoria workspace check",
    "memoria workspace backup",
    "memoria workspace restore",
    "memoria workspace rebuild",
    "memoria workspace export",
    "memoria eval run",
    "memoria eval seeded-error-verdict",
    "memoria eval select-models",
}


def test_surface_contract_cli_parity_is_equality_with_named_exemptions() -> None:
    registered = cli_commands()

    assert "memoria surface schema" in registered
    assert registered.isdisjoint(CLI_ONLY_COMMANDS)
    assert registered | CLI_ONLY_COMMANDS == _cli_command_surface()


def test_surface_contract_job_vocabulary_is_closed() -> None:
    assert SURFACE_JOBS == ("read", "knowledge", "project", "review", "upkeep")


def test_surface_contract_every_row_carries_a_valid_job() -> None:
    for action in SURFACE_ACTIONS:
        assert action.get("job") in SURFACE_JOBS, (
            f"{action['id']}: job={action.get('job')!r} is missing or outside SURFACE_JOBS"
        )


def test_surface_contract_job_mapping_is_pinned() -> None:
    assert {str(action["id"]): str(action["job"]) for action in SURFACE_ACTIONS} == {
        "status.read": "read",
        "operations.list": "read",
        "surface.openapi": "read",
        "surface.schema": "read",
        "requests.list": "review",
        "requests.get": "review",
        "attention.list": "review",
        "attention.get": "review",
        "concepts.list": "read",
        "concepts.get": "read",
        "work.get": "read",
        "journal.list": "read",
        "journal.get": "read",
        "exploration.list": "read",
        "explore.read": "read",
        "project.slice.read": "project",
        "project.draft.read": "project",
        "context.read": "read",
        "operation.run": "upkeep",
    }


def test_surface_contract_status_paths_maps_to_status_read(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """status-paths-action (U1 spec §3) is MAPPED, not reserved: the shipped
    status.read row already discloses the workspace paths (root + relative
    state db). This pin enforces the mapping — if read_status stops
    disclosing them, the unit falls out of 'mapped' and needs its own row."""
    workspace = init_cli_workspace(tmp_path, capsys)

    payload = engine_api.read_status(workspace)
    action = actions_by_id()["status.read"]

    assert payload["workspace"] == str(workspace)
    assert payload["db"] == ".memoria/memoria.sqlite"
    assert action["job"] == "read"
    assert action["engine"] == "read_status"
    assert "reserved" not in action


def test_surface_contract_reserved_context_read_row_is_declared_untransported() -> None:
    action = actions_by_id()["context.read"]

    assert action["job"] == "read"
    assert action["kind"] == "read"
    assert action["reserved"] == "U2"
    assert action["engine"] is None
    assert action["scope"] == "optional-read-scope"
    assert action["params"] == {}
    assert "http" not in action
    assert "mcp" not in action
    assert "cli" not in action


def test_surface_contract_reserved_rows_stay_out_of_transport_projections() -> None:
    """Negative guard: reserving a row must not leak a route, tool, command,
    or openapi path. Passes vacuously before the row lands and must KEEP
    passing after it does."""
    from memoria_vault.runtime.http_transport import openapi_schema

    assert not any(path.startswith("/context") for _method, path in http_routes())
    assert not any(tool.startswith("context") for tool in mcp_tools())
    assert not any(command.startswith("memoria context") for command in cli_commands())
    assert not any(path.startswith("/context") for path in openapi_schema()["paths"])
