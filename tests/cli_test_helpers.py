from __future__ import annotations

import argparse
from pathlib import Path

from memoria_vault.cli import _build_parser


def write_runner_provider_config(
    workspace: Path, *, local_url: str = "http://model.test/v1"
) -> None:
    config = workspace / ".memoria/config/providers.yaml"
    config.parent.mkdir(parents=True, exist_ok=True)
    config.write_text(
        "\n".join(
            [
                "version: 1",
                "runner_providers:",
                f"  local: {{url: {local_url}, key_env: null}}",
                "  gateway: {url: https://gateway.test/v1, key_env: KILOCODE_API_KEY}",
                "",
            ]
        ),
        encoding="utf-8",
    )


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
