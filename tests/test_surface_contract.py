from __future__ import annotations

from memoria_vault.engine import api as engine_api
from memoria_vault.engine.surface_contract import (
    SURFACE_ACTIONS,
    SURFACE_CONTRACT_VERSION,
    actions_by_id,
    cli_commands,
    http_routes,
    mcp_tools,
)
from tests.cli_test_helpers import _cli_command_surface


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
        "project.slice.read",
        "project.draft.read",
        "operation.run",
    }

    assert SURFACE_CONTRACT_VERSION == "surface-contract.v1"
    assert set(actions_by_id()) == expected
    assert len(SURFACE_ACTIONS) == len(expected)
    assert all(hasattr(engine_api, action["engine"]) for action in SURFACE_ACTIONS)


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


def test_surface_contract_cli_commands_are_current_parser_commands() -> None:
    commands = cli_commands()

    assert commands <= _cli_command_surface()
    assert "memoria surface schema" in commands
    assert "memoria workspace scan" not in commands
