"""Typer console entry point that delegates to the current CLI handlers."""

from __future__ import annotations

import argparse
import sys
from collections.abc import Callable, Sequence
from typing import Any

from memoria_vault import cli as legacy_cli

_CONTEXT = {"allow_extra_args": True, "ignore_unknown_options": True, "help_option_names": []}
_APP: Any | None = None


def main(argv: Sequence[str] | None = None) -> int:
    args = list(sys.argv[1:] if argv is None else argv)
    if not args or any(arg in {"--help", "-h", "--version"} for arg in args):
        return legacy_cli.main(args)
    try:
        click, typer = _load_typer()
    except ModuleNotFoundError:
        return legacy_cli.main(args)

    global _APP
    if _APP is None:
        _APP = _build_app(typer)
    try:
        _APP(args=args, standalone_mode=False)
    except click.exceptions.Exit as exc:
        return int(exc.exit_code or 0)
    except click.ClickException as exc:
        exc.show()
        return int(exc.exit_code)
    return 0


def _load_typer() -> tuple[Any, Any]:
    import click
    import typer

    return click, typer


def _build_app(typer: Any) -> Any:
    app = typer.Typer(
        context_settings=_CONTEXT,
        add_completion=False,
        invoke_without_command=True,
        no_args_is_help=False,
    )
    app.callback(invoke_without_command=True)(_root_callback())

    command_action = _command_action(legacy_cli._build_parser())
    for name, subparser in command_action.choices.items():
        child_action = _child_action(subparser)
        if child_action is None:
            app.command(name=name, context_settings=_CONTEXT)(_delegate((name,)))
            continue

        group = typer.Typer(
            context_settings=_CONTEXT,
            add_completion=False,
            invoke_without_command=True,
            no_args_is_help=False,
        )
        group.callback(invoke_without_command=True)(_delegate_callback((name,)))
        for child in child_action.choices:
            group.command(name=child, context_settings=_CONTEXT)(_delegate((name, child)))
        app.add_typer(group, name=name)
    return app


def _root_callback() -> Callable[[Any], None]:
    _, typer = _load_typer()

    def callback(ctx) -> None:
        if ctx.invoked_subcommand is None:
            raise typer.Exit(legacy_cli.main(list(ctx.args)))

    callback.__annotations__["ctx"] = typer.Context
    callback.__name__ = "root"
    return callback


def _delegate_callback(prefix: tuple[str, ...]) -> Callable[[Any], None]:
    _, typer = _load_typer()

    def callback(ctx) -> None:
        if ctx.invoked_subcommand is None:
            raise typer.Exit(legacy_cli.main([*prefix, *ctx.args]))

    callback.__annotations__["ctx"] = typer.Context
    callback.__name__ = "_".join(prefix)
    return callback


def _delegate(prefix: tuple[str, ...]) -> Callable[[Any], None]:
    _, typer = _load_typer()

    def command(ctx) -> None:
        raise typer.Exit(legacy_cli.main([*prefix, *ctx.args]))

    command.__annotations__["ctx"] = typer.Context
    command.__name__ = "_".join(prefix)
    return command


def _command_action(
    parser: argparse.ArgumentParser,
) -> argparse._SubParsersAction[argparse.ArgumentParser]:
    return next(action for action in parser._actions if getattr(action, "dest", None) == "command")


def _child_action(
    parser: argparse.ArgumentParser,
) -> argparse._SubParsersAction[argparse.ArgumentParser] | None:
    return next(
        (action for action in parser._actions if isinstance(action, argparse._SubParsersAction)),
        None,
    )


if __name__ == "__main__":
    raise SystemExit(main())
