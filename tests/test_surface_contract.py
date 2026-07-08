from __future__ import annotations

import argparse

from memoria_vault.cli import _build_parser
from memoria_vault.engine import api as engine_api
from memoria_vault.engine.surface_contract import (
    SURFACE_ACTIONS,
    SURFACE_CONTRACT_VERSION,
    actions_by_id,
    cli_commands,
    http_routes,
    mcp_tools,
)


def test_surface_contract_registry_is_minimal_and_unique() -> None:
    expected = {
        "status.read",
        "operations.list",
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
        ("GET", "/requests"),
        ("GET", "/request"),
        ("GET", "/attention"),
        ("GET", "/attention/card"),
        ("GET", "/concepts"),
        ("GET", "/concept"),
        ("GET", "/work"),
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
        "operation_run",
    }


def test_surface_contract_keeps_future_reads_unbound_until_transports_land() -> None:
    actions = actions_by_id()

    for action_id in ("exploration.list", "project.slice.read", "project.draft.read"):
        assert "http" not in actions[action_id]
        assert "mcp" not in actions[action_id]
    assert [action["id"] for action in SURFACE_ACTIONS if action["kind"] == "write"] == [
        "operation.run"
    ]


def test_surface_contract_cli_commands_are_current_parser_commands() -> None:
    commands = cli_commands()

    assert commands <= _cli_command_surface()
    assert "memoria workspace scan" not in commands


def _cli_command_surface() -> set[str]:
    parser = _build_parser()
    command_action = next(
        action for action in parser._actions if getattr(action, "dest", None) == "command"
    )
    commands: set[str] = set()
    for name, subparser in command_action.choices.items():
        child_action = next(
            (
                action
                for action in subparser._actions
                if isinstance(action, argparse._SubParsersAction)
            ),
            None,
        )
        if child_action is None:
            commands.add(f"memoria {name}")
            continue
        if not getattr(child_action, "required", False):
            commands.add(f"memoria {name}")
        commands.update(f"memoria {name} {child}" for child in child_action.choices)
    return commands
