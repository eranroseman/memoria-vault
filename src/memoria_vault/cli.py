"""Stdlib CLI entry point."""

from __future__ import annotations

import argparse
import base64
import json
import os
import secrets
import shutil
import subprocess
import sys
import time
import uuid
from contextlib import contextmanager
from importlib.resources import files
from pathlib import Path
from typing import Any

import yaml

from memoria_vault import __version__
from memoria_vault.engine import api as engine_api
from memoria_vault.engine.surface_contract import actions_by_id
from memoria_vault.runtime import state
from memoria_vault.runtime.paths import safe_filename
from memoria_vault.runtime.worker import (
    PROTECTED_OPERATION_ACTORS,
    _workspace_lock,
    enqueue_operation,
    enqueue_trusted_write,
    run_pending_jobs,
    run_request,
)

DEFAULT_DIGEST_TOPICS = ["Framing", "Methods", "Findings", "Gaps", "Implications"]
WORKSPACE_SEED_PACKAGE = "memoria_vault.product.workspace_seed"
SEED_TREES = (
    (".githooks", ".githooks"),
    (".memoria/config", ".memoria/config"),
    (".memoria/eval", ".memoria/eval"),
    (".memoria/patterns", ".memoria/patterns"),
    (".memoria/schemas", ".memoria/schemas"),
    (".obsidian", ".obsidian"),
)
SEED_FILES = (
    (".gitignore", ".gitignore"),
    ("steering.md", "steering.md"),
    ("system/vocabulary.md", "system/vocabulary.md"),
)
SURFACE_ACTION = actions_by_id()


def main(argv: list[str] | None = None) -> int:
    parser = _build_parser()
    args = parser.parse_args(argv)
    try:
        return args.handler(args)
    except BrokenPipeError:
        return 1
    except Exception as exc:  # noqa: BLE001 -- CLI boundary turns failures into stable exits.
        return _fail(str(exc), json_output=bool(getattr(args, "json", False)))


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="memoria",
        description="Memoria standalone engine control surface.",
    )
    parser.add_argument("--version", action="version", version=f"memoria {_package_version()}")
    sub = parser.add_subparsers(dest="command", required=True)

    init = sub.add_parser("init")
    _common(init, workspace_required=False)
    init.add_argument("--yes", action="store_true")
    init.add_argument("--dry-run", action="store_true")
    init.add_argument(
        "--no-obsidian",
        action="store_true",
        help="Skip seeded Obsidian settings and the Memoria Obsidian plugin.",
    )
    init.set_defaults(handler=_cmd_init)

    status = sub.add_parser("status", **_surface_help("status.read"))
    _common(status)
    status.set_defaults(handler=_cmd_status)

    doctor = sub.add_parser("doctor")
    doctor_sub = doctor.add_subparsers(dest="doctor_command")
    _common(doctor, workspace_required=False)
    doctor.add_argument("--check", choices=("search", "runner"), default=None)
    doctor.add_argument("--provider", default=None)
    doctor.add_argument("--live", action="store_true")
    doctor.add_argument("--repair", action="store_true")
    doctor.set_defaults(handler=_cmd_doctor)
    bundle = doctor_sub.add_parser("bundle")
    _common(bundle)
    bundle.add_argument("--redacted", action="store_true")
    bundle.set_defaults(handler=_cmd_doctor_bundle)
    self_test = doctor_sub.add_parser("self-test")
    _common(self_test)
    self_test.set_defaults(handler=_cmd_doctor_self_test)

    ask = sub.add_parser("ask")
    _common(ask)
    ask.add_argument("--question", required=True)
    ask.set_defaults(handler=_cmd_ask)

    serve = sub.add_parser("serve")
    _common(serve)
    serve.add_argument("--watch", action="store_true")
    serve.add_argument("--http", action="store_true")
    serve.add_argument("--host", default="127.0.0.1")
    serve.add_argument("--port", type=int, default=8765)
    serve.add_argument("--read-scope", action="append", default=[])
    serve.add_argument("--once", action="store_true")
    serve.add_argument("--poll-interval", type=float, default=1.0)
    serve.set_defaults(handler=_cmd_serve)

    migrate = sub.add_parser("migrate")
    _common(migrate)
    migrate.add_argument("--from-alpha15", required=True)
    migrate.set_defaults(handler=_cmd_migrate)

    mcp = sub.add_parser("mcp")
    mcp.add_argument("--workspace", required=True)
    mcp.add_argument("--read-scope", action="append", default=[])
    mcp.add_argument("--actor", default="agent")
    mcp.set_defaults(handler=_cmd_mcp)

    _surface_commands(sub)
    _new_commands(sub)
    _work_commands(sub)
    _lifecycle_commands(sub)
    _project_commands(sub)
    _request_commands(sub)
    _attention_commands(sub)
    _operation_commands(sub)
    _simple_resource(sub, "steering", {"show", "edit"})
    _simple_resource(sub, "vocab", {"list", "add", "merge", "rename"})
    _simple_resource(sub, "journal", {"show", "tail", "verify"})
    _workspace_commands(sub)
    _eval_commands(sub)
    return parser


def _new_commands(sub: argparse._SubParsersAction[argparse.ArgumentParser]) -> None:
    new = sub.add_parser("new")
    new_sub = new.add_subparsers(dest="new_command", required=True)

    note = new_sub.add_parser("note")
    _common(note)
    note.add_argument("title")
    note.add_argument("--description", default="")
    body = note.add_mutually_exclusive_group(required=True)
    body.add_argument("--body")
    body.add_argument("--file")
    note.add_argument("--mode", choices=("claim", "question", "definition", "work"))
    note.add_argument("--work-id")
    note.add_argument("--tag", action="append", default=[])
    note.set_defaults(handler=_cmd_new_note)

    hub = new_sub.add_parser("hub")
    _common(hub)
    hub.add_argument("tag")
    hub.add_argument("--title")
    hub.add_argument("--description", default="")
    hub.add_argument("--body", default="")
    hub.set_defaults(handler=_cmd_new_hub)

    project = new_sub.add_parser("project")
    _common(project)
    project.add_argument("name")
    project.add_argument("--description", default="")
    project.add_argument("--direction", default="")
    project.set_defaults(handler=_cmd_new_project)


def _surface_commands(sub: argparse._SubParsersAction[argparse.ArgumentParser]) -> None:
    surface = sub.add_parser(
        "surface",
        help="Inspect Memoria surface contracts.",
        description="Inspect Memoria surface contracts.",
    )
    surface_sub = surface.add_subparsers(dest="surface_command", required=True)
    schema = surface_sub.add_parser("schema", **_surface_help("surface.schema"))
    _common(schema, workspace_required=False)
    schema.set_defaults(handler=_cmd_surface_schema)


def _work_commands(sub: argparse._SubParsersAction[argparse.ArgumentParser]) -> None:
    work = sub.add_parser("work")
    work_sub = work.add_subparsers(dest="work_command", required=True)

    add = work_sub.add_parser("add")
    _common(add)
    source = add.add_mutually_exclusive_group(required=True)
    source.add_argument("--doi")
    source.add_argument("--url")
    source.add_argument("--pdf")
    source.add_argument("--file")
    add.add_argument("--title")
    add.add_argument("--description")
    add.add_argument("--text")
    add.set_defaults(handler=_cmd_work_add)

    import_cmd = work_sub.add_parser("import")
    _common(import_cmd)
    import_cmd.add_argument("--format", choices=("bibtex", "csl"), required=True)
    import_cmd.add_argument("--file", required=True)
    import_cmd.set_defaults(handler=_cmd_work_import)

    enrich = work_sub.add_parser("enrich")
    _common(enrich)
    enrich.add_argument("work_id")
    enrich.add_argument("--provider-replay")
    enrich.set_defaults(handler=_cmd_work_enrich)

    digest = work_sub.add_parser("digest")
    _common(digest)
    digest.add_argument("work_id")
    digest.add_argument("--hub-topic", action="append", default=[])
    digest.add_argument("--mode", choices=("test", "live"), default="test")
    digest.set_defaults(handler=_cmd_work_digest)

    interview = work_sub.add_parser("interview")
    _common(interview)
    interview.add_argument("work_id")
    response = interview.add_mutually_exclusive_group(required=True)
    response.add_argument("--response")
    response.add_argument("--fixture")
    interview.add_argument("--prompt", default="What matters about this source?")
    interview.add_argument("--project-id", default="")
    interview.set_defaults(handler=_cmd_work_interview)

    update = work_sub.add_parser("update")
    _common(update)
    update.add_argument("work_id")
    update.add_argument("--title")
    update.add_argument("--description")
    update.add_argument("--resource")
    update.add_argument("--doi")
    update.add_argument("--citekey")
    update.add_argument("--provider-coverage", choices=("full", "partial", "degraded"))
    update.add_argument("--check-status", choices=("unchecked", "checked", "quarantined"))
    update.add_argument("--standing", choices=("current", "archived", "retracted", "superseded"))
    update.add_argument("--research-area", action="append", default=[])
    update.add_argument("--methodology", action="append", default=[])
    update.set_defaults(handler=_cmd_work_update)

    export = work_sub.add_parser("export")
    _common(export)
    export.add_argument("work_id")
    export.add_argument("--output")
    export.set_defaults(handler=_cmd_work_export)


def _lifecycle_commands(sub: argparse._SubParsersAction[argparse.ArgumentParser]) -> None:
    link = sub.add_parser("link")
    _common(link)
    link.add_argument("source_path")
    link.add_argument("target_path")
    link.add_argument("--rel", required=True, choices=("supports", "contradicts", "extends"))
    link.add_argument("--reason", default="")
    link.set_defaults(handler=_cmd_link)

    check = sub.add_parser("check")
    _common(check)
    check.add_argument("target_path", nargs="?")
    check.add_argument("--shadow", action="store_true", default=True)
    check.set_defaults(handler=_cmd_check)

    show = sub.add_parser("show", **_surface_help("concepts.get"))
    _common(show)
    show.add_argument("target")
    show.set_defaults(handler=_cmd_show)

    list_cmd = sub.add_parser("list", **_surface_help("concepts.list"))
    _common(list_cmd)
    list_cmd.add_argument("--type", choices=("note", "work", "hub", "project"))
    list_cmd.set_defaults(handler=_cmd_list)

    export = sub.add_parser("export")
    _common(export)
    export.add_argument("target")
    export.add_argument("--output")
    export.set_defaults(handler=_cmd_export)


def _project_commands(sub: argparse._SubParsersAction[argparse.ArgumentParser]) -> None:
    project = sub.add_parser("project")
    project_sub = project.add_subparsers(dest="project_command", required=True)
    ask = project_sub.add_parser("ask")
    _common(ask)
    ask.add_argument("project_id")
    ask.add_argument("--question", required=True)
    ask.set_defaults(handler=_cmd_project_ask)
    gaps = project_sub.add_parser("gaps")
    _common(gaps)
    gaps.add_argument("project_path")
    gaps.add_argument("--seed-term", action="append", default=[])
    gaps.add_argument("--dense-threshold", type=int, default=2)
    gaps.set_defaults(handler=_cmd_project_gaps)
    frame = project_sub.add_parser("frame-paper")
    _common(frame)
    frame.add_argument("project_path")
    frame.add_argument("--frame-file", required=True)
    frame.set_defaults(handler=_cmd_project_frame_paper)
    trace = project_sub.add_parser("trace")
    _common(trace)
    trace.add_argument("project_path")
    trace.set_defaults(handler=_cmd_project_trace)
    slice_cmd = project_sub.add_parser("slice")
    _common(slice_cmd)
    slice_cmd.add_argument("project_path")
    slice_cmd.add_argument("--query", default="")
    slice_cmd.add_argument("--limit", type=int, default=20)
    slice_cmd.set_defaults(handler=_cmd_project_slice)
    compose = project_sub.add_parser("compose")
    _common(compose)
    compose.add_argument("project_path")
    compose.add_argument("--token-budget", type=int, default=4000)
    compose.set_defaults(handler=_cmd_project_compose)
    verify = project_sub.add_parser("verify")
    _common(verify)
    verify.add_argument("project_path")
    verify.set_defaults(handler=_cmd_project_verify)
    resolve_evidence = project_sub.add_parser("resolve-evidence")
    _common(resolve_evidence)
    resolve_evidence.add_argument("project_path")
    resolve_evidence.add_argument("--evidence-id", required=True)
    resolve_evidence.add_argument("--decision", choices=("accept", "reject"), required=True)
    resolve_evidence.add_argument("--reason", default="")
    resolve_evidence.set_defaults(handler=_cmd_project_resolve_evidence)
    promote = project_sub.add_parser("promote")
    _common(promote)
    promote.add_argument("project_path")
    promote.add_argument("--title", required=True)
    promote.add_argument("--passage", required=True)
    promote.add_argument("--work-id", default="")
    promote.set_defaults(handler=_cmd_project_promote)
    export = project_sub.add_parser("export")
    _common(export)
    export.add_argument("project_path")
    export.add_argument("--format", choices=("markdown", "docx", "pdf", "odt"), default="markdown")
    export.add_argument("--output")
    export.add_argument("--ready-only", action="store_true")
    export.add_argument("--draft", action="store_true")
    export.set_defaults(handler=_cmd_project_export)
    explore = project_sub.add_parser("explore")
    _common(explore)
    explore.add_argument("--limit", type=int, default=10)
    explore.set_defaults(handler=_cmd_project_explore)
    suggest = project_sub.add_parser("suggest-hubs")
    _common(suggest)
    suggest.add_argument("--min-count", type=int, default=2)
    suggest.set_defaults(handler=_cmd_project_suggest_hubs)


def _request_commands(sub: argparse._SubParsersAction[argparse.ArgumentParser]) -> None:
    request = sub.add_parser("request")
    request_sub = request.add_subparsers(dest="request_command", required=True)
    list_cmd = request_sub.add_parser("list", **_surface_help("requests.list"))
    _common(list_cmd)
    list_cmd.add_argument("--status", choices=("pending", "running", "done", "failed", "cancelled"))
    list_cmd.set_defaults(handler=_cmd_request_list)
    show = request_sub.add_parser("show", **_surface_help("requests.get"))
    _common(show)
    show.add_argument("request_id")
    show.set_defaults(handler=_cmd_request_show)
    resume = request_sub.add_parser("resume")
    _common(resume)
    resume.add_argument("request_id")
    resume.set_defaults(handler=_cmd_request_resume)
    answer = request_sub.add_parser("answer")
    _common(answer)
    answer.add_argument("request_id")
    answer.add_argument("answers", nargs="*")
    answer.set_defaults(handler=_cmd_request_answer)
    amend = request_sub.add_parser("amend")
    _common(amend)
    amend.add_argument("request_id")
    amend.add_argument("updates", nargs="+")
    amend.set_defaults(handler=_cmd_request_amend)
    cancel = request_sub.add_parser("cancel")
    _common(cancel)
    cancel.add_argument("request_id")
    cancel.add_argument("--reason", default="PI cancelled request")
    cancel.set_defaults(handler=_cmd_request_cancel)
    retry = request_sub.add_parser("retry")
    _common(retry)
    retry.add_argument("request_id")
    retry.set_defaults(handler=_cmd_request_retry)


def _attention_commands(sub: argparse._SubParsersAction[argparse.ArgumentParser]) -> None:
    attention = sub.add_parser("attention")
    attention_sub = attention.add_subparsers(dest="attention_command", required=True)
    list_cmd = attention_sub.add_parser("list", **_surface_help("attention.list"))
    _common(list_cmd)
    list_cmd.add_argument("--status")
    list_cmd.add_argument("--kind")
    list_cmd.set_defaults(handler=_cmd_attention_list)
    show = attention_sub.add_parser("show", **_surface_help("attention.get"))
    _common(show)
    show.add_argument("attention_path")
    show.set_defaults(handler=_cmd_attention_show)
    resolve = attention_sub.add_parser("resolve")
    _common(resolve)
    resolve.add_argument("attention_path")
    outcome = resolve.add_mutually_exclusive_group(required=True)
    outcome.add_argument("--apply", action="store_const", const="apply", dest="resolution_outcome")
    outcome.add_argument(
        "--reject", action="store_const", const="reject", dest="resolution_outcome"
    )
    outcome.add_argument("--defer", action="store_const", const="defer", dest="resolution_outcome")
    resolve.add_argument("--reason")
    resolve.set_defaults(handler=_cmd_attention_resolve)
    worklist = attention_sub.add_parser("worklist", **_surface_help("attention.list"))
    _common(worklist)
    worklist.set_defaults(handler=_cmd_attention_worklist)


def _operation_commands(sub: argparse._SubParsersAction[argparse.ArgumentParser]) -> None:
    operation = sub.add_parser("operation")
    operation_sub = operation.add_subparsers(dest="operation_command", required=True)
    list_cmd = operation_sub.add_parser("list", **_surface_help("operations.list"))
    _common(list_cmd)
    list_cmd.set_defaults(handler=_cmd_operation_list)
    run = operation_sub.add_parser("run", **_surface_help("operation.run"))
    _common(run)
    run.add_argument("operation_id")
    run.add_argument("--mode", choices=("test", "live"), default="test")
    payload = run.add_mutually_exclusive_group()
    payload.add_argument("--payload-json", default="{}")
    payload.add_argument("--payload-file")
    run.set_defaults(handler=_cmd_operation_run)


def _workspace_commands(sub: argparse._SubParsersAction[argparse.ArgumentParser]) -> None:
    workspace = sub.add_parser("workspace")
    workspace_sub = workspace.add_subparsers(dest="workspace_command", required=True)
    run = workspace_sub.add_parser("run")
    _common(run)
    run.add_argument("--limit", type=int)
    run.set_defaults(handler=_cmd_workspace_run)
    recover = workspace_sub.add_parser("recover")
    _common(recover)
    recover.add_argument("--fixture")
    recover.set_defaults(handler=_cmd_workspace_recover)
    backup = workspace_sub.add_parser("backup")
    _common(backup)
    backup.add_argument("target")
    backup.set_defaults(handler=_cmd_workspace_backup)
    restore = workspace_sub.add_parser("restore")
    _common(restore)
    restore.add_argument("source")
    restore.add_argument("--force", action="store_true")
    restore.set_defaults(handler=_cmd_workspace_restore)
    for name in ("scan", "rollback", "check", "rebuild", "export"):
        cmd = workspace_sub.add_parser(name)
        _common(cmd)
        if name == "rebuild":
            cmd.add_argument("--search", action="store_true")
            cmd.set_defaults(handler=_cmd_workspace_rebuild)
        elif name == "scan":
            cmd.add_argument("--fixture")
            cmd.set_defaults(handler=_cmd_workspace_scan)
        elif name == "rollback":
            cmd.add_argument("target_id")
            cmd.add_argument("--reason", default="PI requested rollback")
            cmd.add_argument("--include-target", action="store_true")
            cmd.set_defaults(handler=_cmd_workspace_rollback)
        elif name == "check":
            cmd.add_argument("--shadow", action="store_true", default=True)
            cmd.set_defaults(handler=_cmd_workspace_check)
        elif name == "export":
            cmd.add_argument("--output")
            cmd.set_defaults(handler=_cmd_workspace_export)


def _eval_commands(sub: argparse._SubParsersAction[argparse.ArgumentParser]) -> None:
    eval_cmd = sub.add_parser("eval")
    eval_sub = eval_cmd.add_subparsers(dest="eval_command", required=True)
    seeded = eval_sub.add_parser("seeded-error-verdict")
    _common(seeded)
    seeded.add_argument("--mode", choices=("test", "live"), default="test")
    seeded.set_defaults(handler=_cmd_eval_seeded_error_verdict)
    select = eval_sub.add_parser("select-models")
    _common(select)
    select.add_argument("--operation")
    select.add_argument("--mode", choices=("test", "live"), default="test")
    select.set_defaults(handler=_cmd_eval_select_models)
    run = eval_sub.add_parser("run")
    _common(run)
    run.add_argument("--dry-run", action="store_true")
    run.set_defaults(handler=_cmd_eval_run)


def _simple_resource(
    sub: argparse._SubParsersAction[argparse.ArgumentParser], name: str, actions: set[str]
) -> None:
    resource = sub.add_parser(name)
    resource_sub = resource.add_subparsers(dest=f"{name}_command", required=True)
    for action in sorted(actions):
        parser_help = _resource_action_help(name, action)
        cmd = resource_sub.add_parser(action, **parser_help)
        _common(cmd)
        if name == "steering" and action == "show":
            cmd.set_defaults(handler=_cmd_steering_show)
        elif name == "steering" and action == "edit":
            body = cmd.add_mutually_exclusive_group(required=True)
            body.add_argument("--body")
            body.add_argument("--file")
            cmd.set_defaults(handler=_cmd_steering_edit)
        elif name == "vocab" and action == "list":
            cmd.set_defaults(handler=_cmd_vocabulary_list)
        elif name == "vocab" and action == "add":
            cmd.add_argument("field")
            cmd.add_argument("term")
            cmd.set_defaults(handler=_cmd_vocabulary_add)
        elif name == "vocab" and action == "rename":
            cmd.add_argument("field")
            cmd.add_argument("old")
            cmd.add_argument("new")
            cmd.set_defaults(handler=_cmd_vocabulary_rename)
        elif name == "vocab" and action == "merge":
            cmd.add_argument("field")
            cmd.add_argument("old")
            cmd.add_argument("new")
            cmd.set_defaults(handler=_cmd_vocabulary_merge)
        elif name == "journal" and action == "tail":
            cmd.description = _surface_summary("journal.list")
            cmd.add_argument("--operation")
            cmd.add_argument("--request-id")
            cmd.add_argument("--path")
            cmd.add_argument("--decision")
            cmd.add_argument("--date")
            cmd.add_argument("--limit", type=int, default=50)
            cmd.set_defaults(handler=_cmd_journal_tail)
        elif name == "journal" and action == "show":
            cmd.description = _surface_summary("journal.get")
            cmd.add_argument("event_id", type=int)
            cmd.set_defaults(handler=_cmd_journal_show)
        elif name == "journal" and action == "verify":
            cmd.description = "Verify the authoritative journal chain and head anchor."
            cmd.set_defaults(handler=_cmd_journal_verify)
        else:
            raise ValueError(f"unsupported resource action: {name} {action}")


def _resource_action_help(name: str, action: str) -> dict[str, str]:
    if name == "journal" and action == "tail":
        return _surface_help("journal.list")
    if name == "journal" and action == "show":
        return _surface_help("journal.get")
    return {}


def _common(parser: argparse.ArgumentParser, *, workspace_required: bool = True) -> None:
    parser.add_argument("--workspace", required=workspace_required)
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--quiet", action="store_true")
    parser.add_argument("--verbose", action="store_true")
    parser.add_argument("--idempotency-key")
    parser.add_argument("--schedule-id")
    parser.add_argument("--actor", choices=("pi", "agent"), default="pi")


def _surface_help(action_id: str) -> dict[str, str]:
    summary = _surface_summary(action_id)
    return {"description": summary, "help": summary}


def _surface_summary(action_id: str) -> str:
    return str(SURFACE_ACTION[action_id]["summary"])


def _cmd_init(args: argparse.Namespace) -> int:
    workspace = Path(args.workspace or ".").resolve()
    created = _workspace_plan(workspace)
    include_obsidian = not args.no_obsidian
    if args.dry_run:
        return _emit(
            _init_dry_run_report(workspace, created, include_obsidian=include_obsidian), args
        )
    if not args.yes and workspace.exists() and any(workspace.iterdir()):
        return _fail("init on a non-empty workspace requires --yes", json_output=args.json)
    _initialize_workspace_files(workspace, include_obsidian=include_obsidian)
    return _emit({"ok": True, "workspace": str(workspace), "created": created}, args)


def _cmd_status(args: argparse.Namespace) -> int:
    return _emit(engine_api.read_status(_workspace(args)), args)


def _cmd_surface_schema(args: argparse.Namespace) -> int:
    workspace = Path(args.workspace or ".").resolve()
    payload = engine_api.read_surface_schema(workspace)
    if not args.quiet:
        print(
            json.dumps(
                payload,
                ensure_ascii=False,
                indent=None if args.json else 2,
                sort_keys=True,
            )
        )
    return 0


def _cmd_doctor(args: argparse.Namespace) -> int:
    workspace = Path(args.workspace).resolve() if args.workspace else Path.cwd()
    repaired: list[str] = []
    if args.repair:
        if not workspace.is_dir():
            return _fail("doctor --repair requires an existing workspace", json_output=args.json)
        with _doctor_maintenance(workspace, repair=True):
            repaired = _repair_workspace(workspace)
    checks: dict[str, Any] = _doctor_checks(workspace)
    if args.check == "search":
        status = _search_status(workspace)
        checks.update(status["checks"])
        return _emit(
            {
                "ok": all(checks.values()),
                "workspace": str(workspace),
                "checks": checks,
                "search_engine": status["engine"],
                "search_manifest": status["manifest"],
                "search_document_count": status["document_count"],
                "repaired": repaired,
            },
            args,
        )
    if args.live and args.check != "runner":
        return _fail("doctor --live is only valid with --check runner", json_output=args.json)
    if args.check == "runner":
        status = _runner_status(workspace, args.provider, live=args.live)
        checks.update(status["checks"])
        return _emit(
            {
                "ok": all(checks.values()),
                "workspace": str(workspace),
                "checks": checks,
                "provider": status["provider"],
                "base_url": status["base_url"],
                "model": status["model"],
                "error": status["error"],
                "repaired": repaired,
            },
            args,
        )
    backup = _backup_report(workspace)
    return _emit(
        {
            "ok": all(checks.values()) and backup["ok"],
            "workspace": str(workspace),
            "checks": checks,
            "backup": backup,
            "repaired": repaired,
        },
        args,
    )


def _cmd_doctor_bundle(args: argparse.Namespace) -> int:
    workspace = _workspace(args)
    with _doctor_maintenance(workspace):
        doctor = _doctor_checks(workspace)
        backup = _backup_report(workspace)
        with state.connect(workspace) as conn:
            requests = [
                dict(row)
                for row in conn.execute(
                    """
                    SELECT request_id, operation_id, status, created_at, completed_at, error
                    FROM operation_requests
                    ORDER BY created_at, request_id
                    """
                )
            ]
        journal_head = state.journal_head(workspace)
    return _emit(
        {
            "ok": all(doctor.values()) and backup["ok"],
            "workspace": str(workspace),
            "redacted": bool(args.redacted),
            "doctor": doctor,
            "backup": backup,
            "requests": requests,
            "journal_head": journal_head,
        },
        args,
    )


def _cmd_doctor_self_test(args: argparse.Namespace) -> int:
    workspace = _workspace(args)
    checks = _doctor_checks(workspace)
    checks["operation_catalog"] = bool(engine_api.read_operations(workspace)["operations"])
    return _emit({"ok": all(checks.values()), "workspace": str(workspace), "checks": checks}, args)


def _cmd_ask(args: argparse.Namespace) -> int:
    result = _enqueue_and_run(
        args,
        "answer-query",
        {"query": args.question, "k": 5},
    )
    return _emit(result, args)


def _cmd_serve(args: argparse.Namespace) -> int:
    if args.http:
        if args.watch:
            return _fail("serve accepts one transport at a time", json_output=args.json)
        return _cmd_serve_http(args)
    if not args.watch:
        return _fail("serve currently requires --watch or --http", json_output=args.json)
    if args.poll_interval <= 0:
        return _fail("serve --poll-interval must be positive", json_output=args.json)
    if args.once:
        return _emit(_workspace_scan_payload(args, schedule_id="file-watch"), args)

    workspace = _workspace(args)
    previous = ""
    try:
        while True:
            current = _workspace_change_signature(workspace)
            if current != previous:
                payload = _workspace_scan_payload(
                    args,
                    schedule_id="file-watch",
                    idempotency_key=f"file-watch-{uuid.uuid4()}",
                )
                _emit_scan_event(payload, args)
                previous = current
            time.sleep(args.poll_interval)
    except KeyboardInterrupt:
        return 0


def _cmd_serve_http(args: argparse.Namespace) -> int:
    from memoria_vault.runtime.http_transport import make_http_server

    if args.host not in {"127.0.0.1", "localhost", "::1"}:
        return _fail("serve --http only binds loopback hosts", json_output=args.json)
    env_token = os.environ.get("MEMORIA_HTTP_TOKEN")
    token = env_token or secrets.token_urlsafe(32)
    try:
        server = make_http_server(
            _workspace(args),
            host=args.host,
            port=args.port,
            token=token,
            read_scope=args.read_scope,
        )
    except ValueError as exc:
        return _fail(str(exc), json_output=args.json)
    port = int(server.server_address[1])
    payload = {
        "ok": True,
        "url": f"http://{args.host}:{port}",
        "token": None if env_token else token,
        "token_source": "env" if env_token else "generated",
    }
    if args.json:
        print(json.dumps(payload, ensure_ascii=False, sort_keys=True), flush=True)
    elif not args.quiet:
        print(f"Memoria HTTP serving {payload['url']}", flush=True)
        if env_token:
            print("Token loaded from MEMORIA_HTTP_TOKEN.", flush=True)
        else:
            print(f"Token: {token}", flush=True)
    if args.once:
        server.server_close()
        return 0
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        return 0
    finally:
        server.server_close()


def _cmd_mcp(args: argparse.Namespace) -> int:
    from memoria_vault.runtime.mcp_transport import run_mcp_server

    if not args.read_scope:
        return _fail("mcp requires at least one --read-scope", json_output=False)
    run_mcp_server(_workspace(args), read_scope=args.read_scope, agent_identity=args.actor)
    return 0


def _cmd_migrate(args: argparse.Namespace) -> int:
    workspace = _workspace(args)
    source = Path(args.from_alpha15).expanduser().resolve()
    if not source.is_dir():
        return _fail(f"alpha.15 workspace not found: {source}", json_output=args.json)
    if workspace == source:
        return _fail("migrate requires a separate target workspace", json_output=args.json)
    if not (workspace / ".memoria/schemas/folders.yaml").is_file():
        _initialize_workspace_files(workspace)
    result = _import_alpha15_workspace(source, workspace)
    return _emit({"ok": True, "workspace": str(workspace), **result}, args)


def _cmd_new_note(args: argparse.Namespace) -> int:
    body = args.body if args.body is not None else Path(args.file).read_text(encoding="utf-8")
    extra = {"mode": args.mode}
    if args.work_id:
        extra["work_id"] = args.work_id
    if args.mode == "claim":
        extra["claim_text"] = body.strip()
    elif args.mode == "question":
        extra["question_status"] = "open"
    return _emit(
        engine_api.write_new_concept(
            _workspace(args),
            "note",
            args.title,
            body=_concept_template_body(args.title, body),
            tags=args.tag,
            extra={"description": args.description, **extra},
            idempotency_key=args.idempotency_key,
            schedule_id=args.schedule_id,
            actor=args.actor,
        ),
        args,
    )


def _cmd_new_hub(args: argparse.Namespace) -> int:
    title = args.title or args.tag
    body = _concept_template_body(title, args.body)
    return _emit(
        engine_api.write_new_concept(
            _workspace(args),
            "hub",
            title,
            body=body,
            tags=[args.tag],
            extra={"tag": args.tag, "description": args.description},
            idempotency_key=args.idempotency_key,
            schedule_id=args.schedule_id,
            actor=args.actor,
        ),
        args,
    )


def _cmd_new_project(args: argparse.Namespace) -> int:
    body = _concept_template_body(args.name, args.direction)
    return _emit(
        engine_api.write_new_concept(
            _workspace(args),
            "project",
            args.name,
            body=body,
            tags=[],
            extra={"description": args.description, "outcome_frame": {}, "paper_plan": {}},
            idempotency_key=args.idempotency_key,
            schedule_id=args.schedule_id,
            actor=args.actor,
        ),
        args,
    )


def _concept_template_body(title: str, body: str) -> str:
    body = body.strip("\n")
    return f"# {title}\n\n{body}\n" if body else f"# {title}\n\n"


def _cmd_work_add(args: argparse.Namespace) -> int:
    if args.url:
        payload = {
            "url": args.url,
            "title": args.title,
            "description": args.description,
        }
        return _emit(_enqueue_and_run(args, "capture-url-source", payload), args)
    if args.pdf:
        path = Path(args.pdf)
        work_id = path.stem
        payload = {
            "work_id": work_id,
            "title": args.title or work_id,
            "description": args.description or f"Captured PDF: {path.name}",
            "raw_pdf_base64": base64.b64encode(path.read_bytes()).decode(),
            "raw_filename": path.name,
        }
        return _emit(_enqueue_and_run(args, "capture-pdf-source", payload), args)
    title = args.title or args.doi or args.url or Path(args.file or args.pdf).stem
    description = args.description or f"Captured work: {title}"
    text = args.text or ""
    text_status = "full-text" if args.text else "metadata-only"
    raw_text = None
    raw_filename = "source.txt"
    resource = args.url or (f"https://doi.org/{args.doi}" if args.doi else "")
    work_id = _work_id(args)
    identifiers = {"doi": args.doi} if args.doi else {}
    if args.file:
        path = Path(args.file)
        text = path.read_text(encoding="utf-8")
        text_status = "full-text"
        raw_text = text
        raw_filename = path.name
    if not text:
        text = title
    return _emit(
        _enqueue_and_run(
            args,
            "capture-source",
            {
                "work_id": work_id,
                "title": title,
                "description": description,
                "content_text": text,
                "raw_text": raw_text if raw_text is not None else text,
                "raw_filename": raw_filename,
                "resource": resource,
                "identifiers": identifiers,
                "csl_json": _csl_json(work_id, title, args.doi, resource),
                "text_status": text_status,
            },
        ),
        args,
    )


def _cmd_work_export(args: argparse.Namespace) -> int:
    workspace = _workspace(args)
    try:
        payload = engine_api.read_work(workspace, args.work_id)
    except FileNotFoundError:
        return _fail(f"work not found: {args.work_id}", json_output=args.json)
    if args.output:
        output = workspace / args.output
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(
            json.dumps(payload["work"], indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
        payload["output_path"] = args.output
    return _emit(payload, args)


def _cmd_work_import(args: argparse.Namespace) -> int:
    path = Path(args.file)
    text = path.read_text(encoding="utf-8")
    if args.format == "bibtex":
        from memoria_vault.runtime.capture import bibtex_capture_payload

        payload = bibtex_capture_payload(text)
    elif args.format == "csl":
        from memoria_vault.runtime.capture import csl_capture_payload

        csl_item = _read_csl_item(text)
        payload = csl_capture_payload(csl_item, raw_text=text)
    output = _enqueue_and_run(args, "capture-source", payload)
    if enrichment := _queue_import_enrichment(args, payload, output):
        output["enrichment_job"] = enrichment
    return _emit(output, args)


def _cmd_work_enrich(args: argparse.Namespace) -> int:
    payload: dict[str, Any] = {"work_id": args.work_id}
    if args.provider_replay:
        payload["provider_payloads"] = _read_provider_replay(Path(args.provider_replay))
    return _emit(_enqueue_and_run(args, "enrich-source", payload), args)


def _cmd_work_digest(args: argparse.Namespace) -> int:
    return _emit(
        _enqueue_and_run(
            args,
            "compile-source-digest",
            {
                "work_id": args.work_id,
                "hub_topics": args.hub_topic or DEFAULT_DIGEST_TOPICS,
                "mode": args.mode,
            },
        ),
        args,
    )


def _cmd_work_interview(args: argparse.Namespace) -> int:
    return _emit(
        _enqueue_and_run(
            args,
            "record-copi-interview",
            _interview_payload(args),
        ),
        args,
    )


def _cmd_work_update(args: argparse.Namespace) -> int:
    workspace = _workspace(args)
    if state.catalog_source(workspace, args.work_id) is None:
        return _fail(f"work not found: {args.work_id}", json_output=args.json)
    payload = {"work_id": args.work_id, **_present_updates(args)}
    return _emit(_enqueue_and_run(args, "update-work", payload), args)


def _cmd_project_ask(args: argparse.Namespace) -> int:
    return _emit(
        _enqueue_and_run(
            args,
            "answer-query",
            {"query": args.question, "project_id": args.project_id, "k": 5},
        ),
        args,
    )


def _cmd_project_gaps(args: argparse.Namespace) -> int:
    return _emit(
        _enqueue_and_run(
            args,
            "analyze-gaps",
            {
                "project_path": args.project_path,
                "seed_terms": args.seed_term,
                "dense_threshold": args.dense_threshold,
            },
        ),
        args,
    )


def _cmd_project_frame_paper(args: argparse.Namespace) -> int:
    try:
        frame = _read_json_object(Path(args.frame_file), "frame file")
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        return _fail(str(exc), json_output=args.json)
    return _emit(
        _enqueue_and_run(args, "frame-paper", {"project_path": args.project_path, **frame}),
        args,
    )


def _cmd_project_suggest_hubs(args: argparse.Namespace) -> int:
    from collections import Counter

    from memoria_vault.runtime.vaultio import iter_markdown, read_frontmatter

    workspace = _workspace(args)
    counts: Counter[str] = Counter()
    existing: set[str] = set()
    for path in iter_markdown(workspace):
        frontmatter = read_frontmatter(path)
        rel = path.relative_to(workspace).as_posix()
        if state.concept_check_status(workspace, rel) != "checked":
            continue
        if frontmatter.get("type") == "hub":
            existing.add(str(frontmatter.get("title") or path.stem).lower())
            for tag in _string_list(frontmatter.get("tags")):
                existing.add(tag.lower())
            continue
        if frontmatter.get("type") not in {"work", "digest", "note"}:
            continue
        for term in _concept_terms(frontmatter):
            counts[term] += 1
    suggestions = [
        {"topic": term, "count": count}
        for term, count in sorted(counts.items())
        if count >= args.min_count and term.lower() not in existing
    ]
    return _emit({"ok": True, "suggestions": suggestions}, args)


def _cmd_project_trace(args: argparse.Namespace) -> int:
    return _emit(
        _enqueue_and_run(args, "analyze-project-argument", {"project_path": args.project_path}),
        args,
    )


def _cmd_project_slice(args: argparse.Namespace) -> int:
    return _emit(
        _enqueue_and_run(
            args,
            "write-project-slice",
            {
                "project_path": args.project_path,
                "query": args.query,
                "limit": args.limit,
            },
        ),
        args,
    )


def _cmd_project_compose(args: argparse.Namespace) -> int:
    return _emit(
        _enqueue_and_run(
            args,
            "compose-project-draft",
            {
                "project_path": args.project_path,
                "token_budget": args.token_budget,
            },
        ),
        args,
    )


def _cmd_project_verify(args: argparse.Namespace) -> int:
    return _emit(
        _enqueue_and_run(args, "verify-project-draft", {"project_path": args.project_path}),
        args,
    )


def _cmd_project_resolve_evidence(args: argparse.Namespace) -> int:
    from memoria_vault.runtime.knowledge import read_project_draft, resolve_evidence_review

    if args.actor != "pi":
        raise ValueError("resolve-evidence-review requires PI actor authority")
    workspace = _workspace(args)
    verification_request = _enqueue_and_run(
        args,
        "verify-project-draft",
        {"project_path": args.project_path},
    )
    if not verification_request.get("ok"):
        return _emit(verification_request, args)
    verification = read_project_draft(workspace, args.project_path)
    evidence_ids = {str(row["id"]) for row in verification["evidence_sets"]}
    if args.evidence_id not in evidence_ids:
        return _fail(
            f"evidence id is not in this project draft: {args.evidence_id}",
            json_output=args.json,
        )
    event = resolve_evidence_review(
        workspace,
        args.evidence_id,
        decision=args.decision,
        reason=args.reason,
        actor=args.actor,
        machine="memoria-cli",
    )
    return _emit(
        {
            "ok": True,
            "project_path": verification["project_path"],
            "draft_path": verification["draft_path"],
            "evidence_id": args.evidence_id,
            "decision": args.decision,
            "event": event,
        },
        args,
    )


def _cmd_project_promote(args: argparse.Namespace) -> int:
    return _emit(
        _enqueue_and_run(
            args,
            "promote-draft-passage",
            {
                "project_path": args.project_path,
                "title": args.title,
                "passage": args.passage,
                "work_id": args.work_id,
            },
        ),
        args,
    )


def _cmd_project_export(args: argparse.Namespace) -> int:
    result = _enqueue_and_run(
        args,
        "export-project",
        {
            "project_path": args.project_path,
            "format": args.format,
            "output_path": args.output or "",
            "ready_only": args.ready_only,
            "draft": args.draft,
        },
    )
    if result.get("ok") and not args.json and not args.quiet:
        export_result = result.get("result") or {}
        content = str(export_result.get("content") or "")
        if content and not args.output:
            print(content, end="" if content.endswith("\n") else "\n")
        else:
            print(export_result.get("output_path") or "ok")
        return 0
    return _emit(result, args)


def _cmd_project_explore(args: argparse.Namespace) -> int:
    from memoria_vault.runtime.knowledge import exploration_channel

    return _emit(
        {"ok": True, "exploration": exploration_channel(_workspace(args), limit=args.limit)},
        args,
    )


def _cmd_link(args: argparse.Namespace) -> int:
    return _emit(
        _enqueue_and_run(
            args,
            "curate-note-link",
            {
                "source_note_path": args.source_path,
                "link_type": args.rel,
                "target_path": args.target_path,
                "reason": args.reason,
            },
        ),
        args,
    )


def _cmd_check(args: argparse.Namespace) -> int:
    if args.target_path:
        return _emit(
            _enqueue_and_run(args, "mark-checked", {"target_path": args.target_path}),
            args,
        )
    return _cmd_workspace_check(args)


def _cmd_show(args: argparse.Namespace) -> int:
    try:
        return _emit(engine_api.read_concept(_workspace(args), args.target), args)
    except FileNotFoundError:
        return _fail(f"target not found: {args.target}", json_output=args.json)


def _cmd_list(args: argparse.Namespace) -> int:
    return _emit(engine_api.read_concepts(_workspace(args), concept_type=args.type or ""), args)


def _cmd_export(args: argparse.Namespace) -> int:
    workspace = _workspace(args)
    path = _resolve_concept_path(workspace, args.target)
    if path is None:
        return _fail(f"target not found: {args.target}", json_output=args.json)
    content = path.read_text(encoding="utf-8")
    payload = {"ok": True, "path": path.relative_to(workspace).as_posix(), "content": content}
    if args.output:
        output = workspace / args.output
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(content, encoding="utf-8")
        payload["output_path"] = args.output
    if not args.json and not args.quiet:
        if args.output:
            print(payload["output_path"])
        else:
            print(content, end="" if content.endswith("\n") else "\n")
        return 0
    return _emit(payload, args)


def _cmd_operation_list(args: argparse.Namespace) -> int:
    return _emit(engine_api.read_operations(_workspace(args)), args)


def _cmd_operation_run(args: argparse.Namespace) -> int:
    return _emit(
        _enqueue_and_run(args, args.operation_id, _operation_payload(args)),
        args,
    )


def _cmd_request_list(args: argparse.Namespace) -> int:
    return _emit(engine_api.read_requests(_workspace(args), status=args.status or ""), args)


def _cmd_request_show(args: argparse.Namespace) -> int:
    try:
        return _emit(engine_api.read_request(_workspace(args), args.request_id), args)
    except FileNotFoundError:
        return _fail(f"request not found: {args.request_id}", json_output=args.json)


def _cmd_request_resume(args: argparse.Namespace) -> int:
    _require_pi_request_control(args)
    result = run_request(_workspace(args), args.request_id, machine="memoria-cli")
    return _emit({"ok": result.get("status") == "done", "result": result}, args)


def _require_pi_request_control(args: argparse.Namespace) -> None:
    if args.actor != "pi":
        raise ValueError("request control requires PI actor authority")


def _request_control_row(workspace: Path, args: argparse.Namespace) -> Any:
    row = state.request_row(workspace, args.request_id)
    if row is None:
        raise FileNotFoundError(f"request not found: {args.request_id}")
    return row


def _request_successor(
    workspace: Path,
    request: dict[str, Any],
    *,
    payload: dict[str, Any],
    idempotency_key: str | None,
    command: str,
) -> dict[str, Any]:
    if not idempotency_key:
        raise ValueError(f"request {command} requires --idempotency-key")
    if request["kind"] != "operation":
        raise ValueError(f"request {command} supports operation requests only")
    if required_actor := PROTECTED_OPERATION_ACTORS.get(request["operation_id"]):
        if required_actor != "pi":
            raise ValueError(
                f"request {command} cannot create a PI successor requiring "
                f"{required_actor} actor authority"
            )
    if request["status"] not in {"pending", "done", "failed", "cancelled"}:
        raise ValueError("request amendment requires a non-running request")
    envelope = request["job"].get("request_envelope")
    if not isinstance(envelope, dict) or envelope.get("args") != request["args"]:
        raise ValueError("request envelope arguments do not match the stored request")
    if request["job"].get("payload") != request["args"]:
        raise ValueError("request payload does not match the stored request envelope")
    successor_id = safe_filename(idempotency_key)
    if successor_id == request["request_id"]:
        raise ValueError("request amendment requires a new idempotency key")
    prior_successor = str(request["job"].get("superseded_by_request_id") or "")
    if prior_successor and safe_filename(prior_successor) != successor_id:
        raise ValueError(f"request already superseded by request {prior_successor}")
    return enqueue_operation(
        workspace,
        request["operation_id"],
        payload=payload,
        idempotency_key=idempotency_key,
        input_refs=request["input_refs"],
        output_intents=request["output_intents"],
        primary_target=request["primary_target"],
        precondition_hashes=request["precondition_hashes"],
        causal_refs=[*request["causal_refs"], request["request_id"]],
        actor="pi",
        provenance={
            "surface": "memoria-cli",
            "command": f"request-{command}",
            "supersedes_request_id": request["request_id"],
        },
        schedule_id=None,
        supersede_request_id=request["request_id"],
    )


def _request_lifecycle_event_exists(workspace: Path, event: str, successor_request_id: str) -> bool:
    with state.connect(workspace) as conn:
        row = conn.execute(
            """
            SELECT 1
            FROM event_log
            WHERE event_type = ?
              AND json_extract(payload_json, '$.successor_request_id') = ?
            LIMIT 1
            """,
            (event, successor_request_id),
        ).fetchone()
    return row is not None


def _request_attempt_event_exists(
    workspace: Path,
    event: str,
    request_id: str,
    attempt_key: str,
    attempt: int,
) -> bool:
    with state.connect(workspace) as conn:
        row = conn.execute(
            """
            SELECT 1
            FROM event_log
            WHERE event_type = ?
              AND json_extract(payload_json, '$.request_id') = ?
              AND json_extract(payload_json, ?) = ?
            LIMIT 1
            """,
            (event, request_id, f"$.{attempt_key}", attempt),
        ).fetchone()
    return row is not None


def _cmd_request_answer(args: argparse.Namespace) -> int:
    from memoria_vault.runtime.trusted_writer import append_explicit_journal_event

    _require_pi_request_control(args)
    workspace = _workspace(args)
    answers = _key_values(args.answers)
    with _workspace_lock(workspace):
        row = _request_control_row(workspace, args)
        request = state.request_detail(row)
        source_request_id = str(request["request_id"])
        current_answers = request["args"].get("answers", {})
        if not isinstance(current_answers, dict):
            raise ValueError("request answers must be a mapping")
        successor = _request_successor(
            workspace,
            request,
            payload={**request["args"], "answers": {**current_answers, **answers}},
            idempotency_key=args.idempotency_key,
            command="answer",
        )
        if not _request_lifecycle_event_exists(
            workspace, "request_answered", str(successor["job_id"])
        ):
            append_explicit_journal_event(
                workspace,
                {
                    "event": "request_answered",
                    "request_id": source_request_id,
                    "successor_request_id": successor["job_id"],
                    "answers": sorted(answers),
                },
                actor="pi",
                machine="memoria-cli",
            )
    updated = state.request_row(workspace, str(successor["job_id"]))
    return _emit(
        {
            "ok": True,
            "request": state.request_detail(updated),
            "supersedes_request_id": source_request_id,
        },
        args,
    )


def _cmd_request_amend(args: argparse.Namespace) -> int:
    from memoria_vault.runtime.trusted_writer import append_explicit_journal_event

    _require_pi_request_control(args)
    workspace = _workspace(args)
    updates = _key_values(args.updates)
    scoped = _scope_bearing_request_fields(updates)
    if scoped:
        raise ValueError(f"request amend cannot change scope-bearing field: {', '.join(scoped)}")
    with _workspace_lock(workspace):
        row = _request_control_row(workspace, args)
        request = state.request_detail(row)
        source_request_id = str(request["request_id"])
        successor = _request_successor(
            workspace,
            request,
            payload={**request["args"], **updates},
            idempotency_key=args.idempotency_key,
            command="amend",
        )
        if not _request_lifecycle_event_exists(
            workspace, "request_amended", str(successor["job_id"])
        ):
            append_explicit_journal_event(
                workspace,
                {
                    "event": "request_amended",
                    "request_id": source_request_id,
                    "successor_request_id": successor["job_id"],
                    "updates": sorted(updates),
                },
                actor="pi",
                machine="memoria-cli",
            )
    updated = state.request_row(workspace, str(successor["job_id"]))
    return _emit(
        {
            "ok": True,
            "request": state.request_detail(updated),
            "supersedes_request_id": source_request_id,
        },
        args,
    )


def _cmd_request_cancel(args: argparse.Namespace) -> int:
    from memoria_vault.runtime.trusted_writer import append_explicit_journal_event

    _require_pi_request_control(args)
    workspace = _workspace(args)
    with _workspace_lock(workspace):
        row = _request_control_row(workspace, args)
        request_id = str(row["request_id"])
        job = json.loads(row["job_json"])
        expected_error = f"cancelled: {args.reason}"
        if row["status"] == "pending":
            attempt = int(job.get("cancel_attempt") or 0) + 1
            job.update(
                {
                    "status": "cancelled",
                    "error": expected_error,
                    "cancel_attempt": attempt,
                }
            )
            _write_request_job(workspace, request_id, "cancelled", job)
        elif row["status"] == "cancelled":
            attempt = int(job.get("cancel_attempt") or 0)
            if (
                not attempt
                or job.get("error") != expected_error
                or job.get("superseded_by_request_id")
                or _request_attempt_event_exists(
                    workspace,
                    "request_cancelled",
                    request_id,
                    "cancel_attempt",
                    attempt,
                )
            ):
                raise ValueError(f"request cancel requires pending status, got {row['status']}")
        else:
            raise ValueError(f"request cancel requires pending status, got {row['status']}")
        if not _request_attempt_event_exists(
            workspace,
            "request_cancelled",
            request_id,
            "cancel_attempt",
            attempt,
        ):
            append_explicit_journal_event(
                workspace,
                {
                    "event": "request_cancelled",
                    "request_id": request_id,
                    "reason": args.reason,
                    "cancel_attempt": attempt,
                },
                actor="pi",
                machine="memoria-cli",
            )
    updated = state.request_row(workspace, request_id)
    return _emit({"ok": True, "request": state.request_detail(updated)}, args)


def _cmd_request_retry(args: argparse.Namespace) -> int:
    from memoria_vault.runtime.trusted_writer import append_explicit_journal_event

    _require_pi_request_control(args)
    workspace = _workspace(args)
    with _workspace_lock(workspace):
        row = _request_control_row(workspace, args)
        request_id = str(row["request_id"])
        job = json.loads(row["job_json"])
        attempt = int(job.get("retry_attempt") or 0)
        event_exists = attempt > 0 and _request_attempt_event_exists(
            workspace,
            "request_retried",
            request_id,
            "retry_attempt",
            attempt,
        )
        if attempt and not event_exists:
            append_explicit_journal_event(
                workspace,
                {
                    "event": "request_retried",
                    "request_id": request_id,
                    "retry_attempt": attempt,
                    "from_status": str(job.get("retry_from_status") or ""),
                },
                actor="pi",
                machine="memoria-cli",
            )
            updated = state.request_row(workspace, request_id)
            return _emit({"ok": True, "request": state.request_detail(updated)}, args)
        if row["status"] not in {"failed", "cancelled"}:
            return _fail(
                f"request retry requires failed or cancelled status, got {row['status']}",
                json_output=args.json,
            )
        if superseded_by := str(job.get("superseded_by_request_id") or ""):
            raise ValueError(f"request was superseded by request {superseded_by}")
        attempt += 1
        job["status"] = "pending"
        job["retry_attempt"] = attempt
        job["retry_from_status"] = str(row["status"])
        job.pop("error", None)
        _write_request_job(workspace, request_id, "pending", job)
        if not _request_attempt_event_exists(
            workspace,
            "request_retried",
            request_id,
            "retry_attempt",
            attempt,
        ):
            append_explicit_journal_event(
                workspace,
                {
                    "event": "request_retried",
                    "request_id": request_id,
                    "retry_attempt": attempt,
                    "from_status": str(job["retry_from_status"]),
                },
                actor="pi",
                machine="memoria-cli",
            )
    updated = state.request_row(workspace, request_id)
    return _emit({"ok": True, "request": state.request_detail(updated)}, args)


def _cmd_attention_list(args: argparse.Namespace) -> int:
    return _emit(
        engine_api.read_attention(_workspace(args), status=args.status or "", kind=args.kind or ""),
        args,
    )


def _cmd_attention_show(args: argparse.Namespace) -> int:
    try:
        return _emit(engine_api.read_attention_card(_workspace(args), args.attention_path), args)
    except FileNotFoundError as exc:
        return _fail(str(exc), json_output=args.json)


def _cmd_attention_resolve(args: argparse.Namespace) -> int:
    outcome = args.resolution_outcome
    reason = args.reason or f"PI chose to {outcome} attention"
    try:
        return _emit(
            engine_api.resolve_attention(
                _workspace(args),
                args.attention_path,
                outcome=outcome,
                reason=reason,
                idempotency_key=args.idempotency_key,
                schedule_id=args.schedule_id,
                actor=args.actor,
            ),
            args,
        )
    except FileNotFoundError as exc:
        return _fail(str(exc), json_output=args.json)


def _cmd_attention_worklist(args: argparse.Namespace) -> int:
    return _emit(engine_api.read_attention(_workspace(args), worklist=True), args)


def _cmd_eval_seeded_error_verdict(args: argparse.Namespace) -> int:
    operation_args = argparse.Namespace(**{**vars(args), "actor": "operation"})
    return _emit(
        _enqueue_and_run(operation_args, "run-seeded-error-verdict", {"mode": args.mode}),
        args,
    )


def _cmd_eval_select_models(args: argparse.Namespace) -> int:
    from memoria_vault.runtime.capabilities import iter_capability_manifests
    from memoria_vault.runtime.operations import load_operation_policy, resolve_operation_runner

    workspace = _workspace(args)
    _seeded_error_bundle_path(workspace)
    operation_ids = (
        [args.operation]
        if args.operation
        else sorted(
            str(item["frontmatter"]["operation_id"])
            for item in iter_capability_manifests("operation")
        )
    )
    selections = []
    for operation_id in operation_ids:
        policy = load_operation_policy(workspace, operation_id)
        runner = resolve_operation_runner(workspace, policy, args.mode)
        request = enqueue_operation(
            workspace,
            "run-seeded-error-verdict",
            payload={
                "mode": args.mode,
                "target_operation_id": operation_id,
            },
            idempotency_key=f"select-model-{operation_id}-{args.mode}",
            actor="operation",
            provenance={"surface": "memoria-cli", "command": "eval-select-models"},
        )
        verdict = run_request(workspace, request["job_id"], machine="memoria-cli")
        passed = bool(verdict.get("passed"))
        selections.append(
            {
                "operation_id": operation_id,
                "mode": runner["mode"],
                "candidate_count": 1,
                "candidate_source": "operation_manifest_runner",
                "selected": runner if passed else None,
                "attention_required": not passed,
                "bar_failures": verdict.get("bar_failures") or [],
                "verdict_key": verdict.get("verdict_key", ""),
                "non_sandbox_licensed": bool(verdict.get("non_sandbox_licensed", False)),
            }
        )
    payload = {
        "ok": all(item["selected"] for item in selections),
        "mode": args.mode,
        "selection_count": sum(1 for item in selections if item["selected"]),
        "failed_count": sum(1 for item in selections if not item["selected"]),
        "selections": selections,
    }
    if args.operation:
        payload["operation_id"] = args.operation
        payload["selection"] = selections[0]
    return _emit(payload, args)


def _cmd_workspace_run(args: argparse.Namespace) -> int:
    results = run_pending_jobs(_workspace(args), limit=args.limit, machine="memoria-cli")
    payload = {"ok": True, "ran": len(results), "results": results}
    if args.schedule_id:
        payload["schedule_id"] = args.schedule_id
    return _emit(payload, args)


def _cmd_workspace_recover(args: argparse.Namespace) -> int:
    from memoria_vault.runtime import backup as runtime_backup

    if args.actor != "pi":
        raise ValueError("workspace recover requires PI actor authority")
    workspace = _workspace(args)
    runtime_backup.validate_runtime_root(workspace)
    fixture = _workspace_recover_fixture(workspace, args.fixture) if args.fixture else None
    with _workspace_lock(workspace):
        restore_recovery = runtime_backup.recover_interrupted_restore(workspace)
        backup_recovery = runtime_backup.recover_interrupted_backup(workspace)
        restored = state.recover_pending_materializations(workspace)
        failed_requests = state.recover_running_requests(workspace)
    payload = {
        "ok": True,
        "restored": restored,
        "restore_rollbacks": (
            [restore_recovery["rollback"]] if restore_recovery["recovered"] else []
        ),
        "backup_targets": [backup_recovery["target"]] if backup_recovery["recovered"] else [],
        "failed_requests": failed_requests,
    }
    if fixture is not None:
        payload["fixture"] = fixture
    if not args.json and not args.quiet:
        print(
            "workspace recovery: "
            f"{len(payload['restore_rollbacks'])} restore rollbacks, "
            f"{len(payload['backup_targets'])} backup targets, "
            f"{len(restored)} materializations, "
            f"{len(failed_requests)} interrupted requests"
        )
        return 0
    return _emit(payload, args)


def _cmd_workspace_backup(args: argparse.Namespace) -> int:
    from memoria_vault.runtime import backup as runtime_backup

    if args.actor != "pi":
        raise ValueError("workspace backup requires PI actor authority")
    return _emit(
        runtime_backup.create_backup(
            _workspace(args),
            Path(args.target),
            actor=args.actor,
            machine="memoria-cli",
        ),
        args,
    )


def _cmd_workspace_restore(args: argparse.Namespace) -> int:
    from memoria_vault.runtime import backup as runtime_backup

    if args.actor != "pi":
        raise ValueError("workspace restore requires PI actor authority")
    return _emit(
        runtime_backup.restore_backup(
            _workspace(args),
            Path(args.source),
            force=bool(args.force),
            actor=args.actor,
            machine="memoria-cli",
        ),
        args,
    )


def _cmd_workspace_scan(args: argparse.Namespace) -> int:
    return _emit(_workspace_scan_payload(args), args)


def _workspace_scan_payload(
    args: argparse.Namespace,
    *,
    schedule_id: str | None = None,
    idempotency_key: str | None = None,
) -> dict[str, Any]:
    scan_args = argparse.Namespace(**vars(args))
    scan_args.actor = "integrity"
    if schedule_id is not None:
        scan_args.schedule_id = schedule_id
    if idempotency_key is not None:
        scan_args.idempotency_key = idempotency_key

    def auxiliary_args(operation_id: str) -> argparse.Namespace:
        operation_args = argparse.Namespace(**vars(scan_args))
        base_key = str(getattr(operation_args, "idempotency_key", "") or "")
        if base_key:
            operation_args.idempotency_key = f"{base_key}:{operation_id}"
        return operation_args

    workspace = _workspace(args)
    with _workspace_lock(workspace):
        journal = state.verify_journal_chain(workspace)
        if not journal["ok"]:
            return {
                "ok": False,
                "journal": journal,
                "needs_check_count": 0,
                "needs_check_paths": [],
            }
        from memoria_vault.runtime.trusted_writer import reconcile_journal_export

        journal_reconciled = reconcile_journal_export(workspace)
    fixture_name = getattr(args, "fixture", "")
    fixture = _workspace_scan_fixture(workspace, fixture_name) if fixture_name else None
    projection_paths = _changed_generated_projection_paths(workspace)
    from memoria_vault.runtime.projections import regenerable_tracked_projection_paths

    regeneration_paths = regenerable_tracked_projection_paths(workspace, projection_paths)
    quarantine = None
    regeneration = None
    if projection_paths:
        quarantine = _enqueue_and_run(
            auxiliary_args("trace-integrity-scan"),
            "trace-integrity-scan",
            {
                "paths": projection_paths,
                "reason": "workspace-scan-generated-projection",
            },
        )
        if regeneration_paths:
            regeneration = _enqueue_and_run(
                auxiliary_args("regenerate-tracked-projections"),
                "regenerate-tracked-projections",
                {"paths": regeneration_paths},
            )
    observed = _enqueue_and_run(scan_args, "observe-pi-edits", {})
    needs_check_paths = list(observed["result"].get("paths") or [])
    payload = {
        "ok": (
            observed["ok"]
            and (quarantine is None or quarantine["ok"])
            and (regeneration is None or regeneration["ok"])
        ),
        "job": observed["job"],
        "result": observed["result"],
        "needs_check_count": len(needs_check_paths),
        "needs_check_paths": needs_check_paths,
        "journal": journal,
        "journal_reconciled": journal_reconciled,
    }
    if quarantine is not None:
        payload["quarantine"] = quarantine["result"]
        payload["quarantine_job"] = quarantine["job"]
    if regeneration is not None:
        payload["regeneration"] = regeneration["result"]
        payload["regeneration_job"] = regeneration["job"]
    if fixture is not None:
        payload["fixture"] = fixture
    if scan_args.schedule_id:
        payload["schedule_id"] = scan_args.schedule_id
    return payload


def _workspace_change_signature(workspace: Path) -> str:
    proc = subprocess.run(
        ["git", "status", "--porcelain=v1", "--untracked-files=all"],
        cwd=workspace,
        check=False,
        text=True,
        capture_output=True,
    )
    return proc.stdout if proc.returncode == 0 else str(uuid.uuid4())


def _emit_scan_event(payload: dict[str, Any], args: argparse.Namespace) -> None:
    if args.quiet:
        return
    if args.json:
        print(json.dumps(payload, ensure_ascii=False, sort_keys=True), flush=True)
    else:
        count = payload.get("needs_check_count", 0)
        print(f"file-watch scan: {count} path(s) need check", flush=True)


def _cmd_workspace_rollback(args: argparse.Namespace) -> int:
    return _emit(
        _enqueue_and_run(
            args,
            "cascade-rollback",
            {
                "target_id": args.target_id,
                "reason": args.reason,
                "include_target": args.include_target,
            },
        ),
        args,
    )


def _cmd_workspace_check(args: argparse.Namespace) -> int:
    from memoria_vault.runtime.projections import check_tracked_projections
    from memoria_vault.runtime.worker import INTEGRITY_SWEEP_OPERATIONS

    workspace = _workspace(args)
    projections = check_tracked_projections(workspace)
    if args.schedule_id:
        from memoria_vault.runtime.worker import run_integrity_sweep

        sweep = run_integrity_sweep(
            workspace,
            shadow=bool(args.shadow),
            sweep_id=args.schedule_id,
            machine="memoria-cli",
        )
        results = [
            {"ok": result.get("status") == "done", "result": result} for result in sweep["results"]
        ]
        return _emit(
            {
                "ok": (all(result["ok"] for result in results) and projections["ok"]),
                "schedule_id": args.schedule_id,
                "jobs": sweep["jobs"],
                "checks": results,
                "projections": projections,
                "assertions": [],
            },
            args,
        )
    check_args = argparse.Namespace(**vars(args))
    check_args.actor = "integrity"

    def operation_args(operation_id: str) -> argparse.Namespace:
        item_args = argparse.Namespace(**vars(check_args))
        base_key = str(getattr(item_args, "idempotency_key", "") or "")
        if base_key:
            item_args.idempotency_key = f"{base_key}:{operation_id}"
        return item_args

    results = [
        _enqueue_and_run(operation_args(operation_id), operation_id, {"shadow": bool(args.shadow)})
        for operation_id in INTEGRITY_SWEEP_OPERATIONS
    ]
    return _emit(
        {
            "ok": all(result["ok"] for result in results) and projections["ok"],
            "checks": results,
            "projections": projections,
            "assertions": [],
        },
        args,
    )


def _cmd_workspace_rebuild(args: argparse.Namespace) -> int:
    workspace = _workspace(args)
    from memoria_vault.runtime.capture import write_references_bib_explicit
    from memoria_vault.runtime.trusted_writer import rebuild_concept_mirror_from_files

    mirror = rebuild_concept_mirror_from_files(workspace)
    references = write_references_bib_explicit(workspace, actor=args.actor, machine="memoria-cli")
    payload: dict[str, Any] = {"ok": True, "concept_mirror": mirror, "references": references}
    if args.search:
        from memoria_vault.runtime.search_index import rebuild_checked_search_index_explicit

        manifest = rebuild_checked_search_index_explicit(
            workspace, actor=args.actor, machine="memoria-cli"
        )
        payload["search"] = {"engine": "bm25", "manifest": manifest}
    return _emit(payload, args)


def _cmd_workspace_export(args: argparse.Namespace) -> int:
    workspace = _workspace(args)
    payload = _workspace_export_payload(workspace)
    if args.output:
        output = Path(args.output)
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(
            json.dumps(payload, ensure_ascii=False, sort_keys=True, indent=2) + "\n",
            encoding="utf-8",
        )
        payload["output"] = str(output)
    return _emit({"ok": True, "workspace": str(workspace), "export": payload}, args)


def _cmd_eval_run(args: argparse.Namespace) -> int:
    return _emit(_enqueue_and_run(args, "eval-run", {"dry_run": bool(args.dry_run)}), args)


def _cmd_steering_show(args: argparse.Namespace) -> int:
    path = _workspace(args) / "steering.md"
    if not path.is_file():
        return _fail("steering.md not found", json_output=args.json)
    return _emit(
        {"ok": True, "path": "steering.md", "body": path.read_text(encoding="utf-8")}, args
    )


def _cmd_steering_edit(args: argparse.Namespace) -> int:
    from memoria_vault.runtime.trusted_writer import (
        append_explicit_journal_event,
        commit_explicit_writer_changes,
    )

    if args.actor != "pi":
        raise ValueError("steering edit requires PI actor authority")
    workspace = _workspace(args)
    body = args.body if args.body is not None else Path(args.file).read_text(encoding="utf-8")
    path = workspace / "steering.md"
    path.write_text(body if body.endswith("\n") else f"{body}\n", encoding="utf-8")
    event = append_explicit_journal_event(
        workspace,
        {"event": "steering_updated", "operation": "steering-edit", "output_id": "steering.md"},
        actor=args.actor,
        machine="memoria-cli",
    )
    commit = commit_explicit_writer_changes(
        workspace,
        "update steering",
        ["steering.md"],
        actor=args.actor,
        machine="memoria-cli",
    )
    return _emit({"ok": True, "path": "steering.md", "event": event, "commit": commit}, args)


def _cmd_vocabulary_list(args: argparse.Namespace) -> int:
    path = _workspace(args) / "system/vocabulary.md"
    if not path.is_file():
        return _fail("system/vocabulary.md not found", json_output=args.json)
    return _emit(
        {"ok": True, "path": "system/vocabulary.md", "vocabulary": _read_vocabulary(path)}, args
    )


def _cmd_vocabulary_add(args: argparse.Namespace) -> int:
    return _update_vocabulary(args, mode="add")


def _cmd_vocabulary_rename(args: argparse.Namespace) -> int:
    return _update_vocabulary(args, mode="rename")


def _cmd_vocabulary_merge(args: argparse.Namespace) -> int:
    return _update_vocabulary(args, mode="merge")


def _cmd_journal_tail(args: argparse.Namespace) -> int:
    return _emit(
        engine_api.read_journal(
            _workspace(args),
            operation=args.operation or "",
            request_id=args.request_id or "",
            path=args.path or "",
            decision=args.decision or "",
            date=args.date or "",
            limit=args.limit,
        ),
        args,
    )


def _cmd_journal_show(args: argparse.Namespace) -> int:
    try:
        return _emit(engine_api.read_journal_event(_workspace(args), args.event_id), args)
    except FileNotFoundError:
        return _fail(f"journal event not found: {args.event_id}", json_output=args.json)


def _cmd_journal_verify(args: argparse.Namespace) -> int:
    workspace = _workspace(args)
    with _workspace_lock(workspace):
        report = state.verify_journal_chain(workspace)
    return _emit(report, args)


def _enqueue_and_run(
    args: argparse.Namespace, operation_id: str, payload: dict[str, Any]
) -> dict[str, Any]:
    return engine_api.run_operation(
        _workspace(args),
        operation_id,
        payload,
        idempotency_key=args.idempotency_key,
        schedule_id=args.schedule_id,
        actor=args.actor,
        command=operation_id,
    )


def _queue_import_enrichment(
    args: argparse.Namespace, payload: dict[str, Any], output: dict[str, Any]
) -> dict[str, Any] | None:
    from memoria_vault.runtime.capture import payload_doi

    result = output.get("result")
    if not isinstance(result, dict) or result.get("status") != "done":
        return None
    if not payload_doi(payload):
        return None
    work_id = str(result.get("work_id") or "").strip()
    if not work_id:
        return None
    workspace = _workspace(args)
    parent_request_id = str(output["job"]["job_id"])
    return enqueue_operation(
        workspace,
        "enrich-source",
        payload={"work_id": work_id},
        idempotency_key=f"enrich-{work_id}:{parent_request_id}",
        input_refs=[{"id": work_id, "kind": "catalog_source"}],
        primary_target=f"catalog/sources/{work_id}",
        causal_refs=[parent_request_id],
        actor="operation",
        provenance={"surface": "memoria-cli", "command": "work-import"},
        schedule_id=args.schedule_id,
    )


def _workspace(args: argparse.Namespace) -> Path:
    return Path(args.workspace).resolve()


def _seeded_error_bundle_path(workspace: Path) -> Path:
    path = workspace / ".memoria/eval/alpha15-seeded-errors.json"
    if path.is_file():
        return path
    raise FileNotFoundError(path)


def _workspace_scan_fixture(workspace: Path, fixture: str) -> dict[str, str]:
    if fixture != "direct-write-generated-projection":
        raise ValueError(f"unknown workspace scan fixture: {fixture}")
    rel = "index.md"
    path = workspace / rel
    if not path.is_file():
        raise FileNotFoundError(path)
    marker = "\n<!-- direct-write-generated-projection fixture -->\n"
    text = path.read_text(encoding="utf-8")
    if marker.strip() not in text:
        path.write_text(text.rstrip() + marker, encoding="utf-8")
    return {"name": fixture, "path": rel}


def _workspace_recover_fixture(workspace: Path, fixture: str) -> dict[str, str]:
    if fixture != "crash-before-materialization":
        raise ValueError(f"unknown workspace recover fixture: {fixture}")
    rel = "notes/crash-before-materialization.md"
    content = (
        "---\n"
        "type: note\n"
        "title: Crash-before-materialization fixture\n"
        "tags: []\n"
        "links: {}\n"
        "---\n\n"
        "This note exists to prove pending file materializations recover from Git and SQLite.\n"
    )
    request = enqueue_trusted_write(
        workspace,
        rel,
        content,
        actor="operation",
        operation="recover-fixture",
        run_id="fixture:crash-before-materialization",
        idempotency_key="fixture-crash-before-materialization",
    )
    result = run_request(workspace, request["job_id"], machine="memoria-cli")
    if result.get("status") != "done":
        raise RuntimeError(str(result.get("error") or "recover fixture request failed"))
    with state.connect(workspace) as conn:
        conn.execute(
            "UPDATE outputs SET materialization_status = 'pending', materialized_commit = ''"
            " WHERE output_id = ?",
            (rel,),
        )
    path = workspace / rel
    if path.is_file():
        path.unlink()
    return {"name": fixture, "path": rel}


def _changed_generated_projection_paths(workspace: Path) -> list[str]:
    from memoria_vault.runtime.projections import changed_tracked_projection_paths

    return changed_tracked_projection_paths(workspace)


def _resolve_concept_path(workspace: Path, target: str) -> Path | None:
    from memoria_vault.runtime.paths import safe_filename
    from memoria_vault.runtime.vaultio import iter_markdown, read_frontmatter

    raw = Path(target)
    direct = raw if raw.is_absolute() else workspace / raw
    if direct.is_file():
        return direct.resolve()
    slug = safe_filename(target.strip().lower())
    for path in iter_markdown(workspace):
        frontmatter = read_frontmatter(path)
        if frontmatter.get("type") not in {
            "note",
            "digest",
            "hub",
            "project",
        }:
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


def _workspace_plan(workspace: Path) -> list[str]:
    from memoria_vault.runtime.subsystems.lib import schema

    return list(schema.load_folders()["skeleton"])


def _active_seed_trees(*, include_obsidian: bool) -> tuple[tuple[str, str], ...]:
    if include_obsidian:
        return SEED_TREES
    return tuple(pair for pair in SEED_TREES if pair[1] != ".obsidian")


def _init_dry_run_report(
    workspace: Path, planned_dirs: list[str], *, include_obsidian: bool = True
) -> dict[str, Any]:
    from memoria_vault.runtime.projections import TRACKED_PROJECTION_PATHS

    seed_trees = [target for _, target in _active_seed_trees(include_obsidian=include_obsidian)]
    seed_files = [target for _, target in SEED_FILES]
    search = {
        "engine": "bm25",
        "checked_root": ".memoria/index/search/checked",
        "manifest": ".memoria/index/search/manifest.json",
    }
    return {
        "ok": True,
        "dry_run": True,
        "workspace": str(workspace),
        "workspace_exists": workspace.exists(),
        "would_create": planned_dirs,
        "skeleton": {
            "directories": planned_dirs,
            "existing": [rel for rel in planned_dirs if (workspace / rel).is_dir()],
            "missing": [rel for rel in planned_dirs if not (workspace / rel).is_dir()],
        },
        "db": {
            "path": state.db_path(workspace).relative_to(workspace).as_posix(),
            "exists": state.db_path(workspace).is_file(),
        },
        "package": {
            "seed_trees": seed_trees,
            "seed_files": seed_files,
            "version": _package_version(),
        },
        "generated_targets": list(TRACKED_PROJECTION_PATHS),
        "concepts": {
            "steering": "steering.md",
            "vocabulary": "system/vocabulary.md",
        },
        "search": search,
        "provider_config": {
            "path": ".memoria/config/providers.yaml",
            "seeded": ".memoria/config" in seed_trees,
            "exists": (workspace / ".memoria/config/providers.yaml").is_file(),
        },
        "git": {
            "repo": ".git",
            "would_init": not (workspace / ".git").exists(),
            "journal_head": state.JOURNAL_HEAD_REL,
            "overrides": ".memoria/overrides.jsonl",
            "gitignore": ".gitignore",
        },
    }


def _seed_workspace(workspace: Path, *, overwrite: bool, include_obsidian: bool = True) -> None:
    for source_rel, target_rel in _active_seed_trees(include_obsidian=include_obsidian):
        _copy_seed_tree(source_rel, workspace / target_rel, overwrite=overwrite)
    for source_rel, target_rel in SEED_FILES:
        _copy_seed_file(source_rel, workspace / target_rel, overwrite=overwrite)


def _repair_workspace(workspace: Path) -> list[str]:
    _initialize_workspace_files(workspace, overwrite=True, commit_created_repository=False)
    return sorted([target for _, target in (*SEED_TREES, *SEED_FILES)])


def _repair_write_targets(workspace: Path) -> list[str]:
    from memoria_vault.runtime.projections import TRACKED_PROJECTION_PATHS

    targets = set(_workspace_plan(workspace))
    for source_rel, target_rel in SEED_TREES:
        targets.update(_seed_tree_write_targets(source_rel, target_rel))
    targets.update(target for _source, target in SEED_FILES)
    targets.update(
        {
            state.DB_REL,
            f"{state.DB_REL}-wal",
            f"{state.DB_REL}-shm",
            f"{state.DB_REL}-journal",
            state.JOURNAL_HEAD_REL,
            ".memoria/overrides.jsonl",
            "system/manifest.jsonl",
            *TRACKED_PROJECTION_PATHS,
        }
    )
    targets.update(_existing_tree_targets(workspace, ".git"))
    return sorted(targets)


def _seed_tree_write_targets(source_rel: str, target_rel: str) -> list[str]:
    targets = [target_rel]
    source = _seed_resource(source_rel)
    if not source.is_dir():
        return targets
    for child in source.iterdir():
        child_target = (Path(target_rel) / child.name).as_posix()
        targets.append(child_target)
        if child.is_dir():
            targets.extend(_seed_tree_write_targets(f"{source_rel}/{child.name}", child_target))
    return targets


def _existing_tree_targets(workspace: Path, root_rel: str) -> list[str]:
    targets = [root_rel]
    root = workspace / root_rel
    if root.is_symlink() or root.is_junction() or not root.is_dir():
        return targets
    for child in root.iterdir():
        child_rel = child.relative_to(workspace).as_posix()
        targets.append(child_rel)
        if not child.is_symlink() and not child.is_junction() and child.is_dir():
            targets.extend(_existing_tree_targets(workspace, child_rel))
    return targets


@contextmanager
def _doctor_maintenance(workspace: Path, *, repair: bool = False):
    from memoria_vault.runtime import backup as runtime_backup

    def preflight() -> None:
        runtime_backup.validate_maintenance_preconditions(workspace)
        if repair:
            runtime_backup.validate_workspace_write_targets(
                workspace, _repair_write_targets(workspace)
            )
            git_path = workspace / ".git"
            if os.path.lexists(git_path) and not git_path.is_dir():
                raise ValueError("workspace Git metadata must be a directory")
            if os.path.lexists(git_path / "commondir"):
                raise ValueError("workspace Git common-directory indirection is not supported")

    preflight()
    with _workspace_lock(workspace):
        preflight()
        yield


def _initialize_workspace_files(
    workspace: Path,
    *,
    overwrite: bool = False,
    include_obsidian: bool = True,
    commit_created_repository: bool = True,
) -> None:
    workspace.mkdir(parents=True, exist_ok=True)
    for rel in _workspace_plan(workspace):
        (workspace / rel).mkdir(parents=True, exist_ok=True)
    _seed_workspace(workspace, overwrite=overwrite, include_obsidian=include_obsidian)
    state.connect(workspace).close()
    _ensure_control_files(workspace)
    from memoria_vault.runtime.projections import write_tracked_projections_explicit

    write_tracked_projections_explicit(workspace, actor="operation", machine="memoria-init")
    _ensure_git(workspace, commit_created_repository=commit_created_repository)


def _import_alpha15_workspace(source: Path, workspace: Path) -> dict[str, Any]:
    copied: list[str] = []
    copied.extend(_copy_alpha15_tree(source, workspace, "knowledge/notes", "notes"))
    copied.extend(_copy_alpha15_tree(source, workspace, "knowledge/hubs", "hubs"))
    copied.extend(_copy_alpha15_projects(source, workspace))
    copied.extend(_copy_alpha15_works(source, workspace))
    bibliography = source / "references.bib"
    if bibliography.is_file():
        target = workspace / "bibliography.bib"
        if target.exists() and target.read_text(encoding="utf-8").strip():
            raise FileExistsError(target)
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(bibliography, target)
        copied.append("bibliography.bib")
    return {"imported": sorted(copied), "imported_count": len(copied)}


def _copy_alpha15_tree(source: Path, workspace: Path, old_root: str, new_root: str) -> list[str]:
    root = source / old_root
    if not root.is_dir():
        return []
    copied: list[str] = []
    for path in sorted(root.rglob("*.md")):
        rel = path.relative_to(root).as_posix()
        target = workspace / new_root / rel
        _copy_no_overwrite(path, target)
        copied.append(target.relative_to(workspace).as_posix())
    return copied


def _copy_alpha15_projects(source: Path, workspace: Path) -> list[str]:
    root = source / "knowledge/projects"
    if not root.is_dir():
        return []
    copied: list[str] = []
    for path in sorted(root.rglob("*.md")):
        rel = path.relative_to(root)
        if len(rel.parts) == 1:
            target = workspace / "projects" / path.stem / "project.md"
        else:
            target = workspace / "projects" / rel
        _copy_no_overwrite(path, target)
        copied.append(target.relative_to(workspace).as_posix())
    return copied


def _copy_alpha15_works(source: Path, workspace: Path) -> list[str]:
    from memoria_vault.runtime.paths import safe_filename
    from memoria_vault.runtime.vaultio import split_frontmatter

    root = source / "knowledge/works"
    if not root.is_dir():
        return []
    copied: list[str] = []
    for path in sorted(root.glob("*.md")):
        frontmatter, body = split_frontmatter(path.read_text(encoding="utf-8"))
        work_id = safe_filename(str(frontmatter.get("work_id") or path.stem)).strip("._-")
        if not work_id:
            work_id = path.stem
        digest_path = workspace / "digests" / f"{work_id}.md"
        digest = dict(frontmatter)
        digest.update({"type": "digest", "id": work_id, "work_id": work_id})
        digest.setdefault("title", str(frontmatter.get("title") or path.stem))
        digest.setdefault("tags", [])
        digest.setdefault("links", {})
        _write_no_overwrite(digest_path, digest, body)
        copied.append(digest_path.relative_to(workspace).as_posix())
    return copied


def _copy_no_overwrite(source: Path, target: Path) -> None:
    if target.exists():
        raise FileExistsError(target)
    target.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(source, target)


def _write_no_overwrite(target: Path, frontmatter: dict[str, Any], body: str) -> None:
    from memoria_vault.runtime.vaultio import write_frontmatter_doc

    if target.exists():
        raise FileExistsError(target)
    write_frontmatter_doc(target, frontmatter, body, create_parent=True)


def _copy_seed_tree(source_rel: str, target: Path, *, overwrite: bool) -> None:
    source = _seed_resource(source_rel)
    if not source.is_dir():
        return
    if target.exists() and any(target.iterdir()) and not overwrite:
        return
    target.mkdir(parents=True, exist_ok=True)
    for child in source.iterdir():
        child_target = target / child.name
        if child.is_dir():
            _copy_seed_tree(f"{source_rel}/{child.name}", child_target, overwrite=overwrite)
        elif overwrite or not child_target.exists():
            child_target.parent.mkdir(parents=True, exist_ok=True)
            child_target.write_bytes(child.read_bytes())


def _copy_seed_file(source_rel: str, target: Path, *, overwrite: bool) -> None:
    source = _seed_resource(source_rel)
    if source.is_file() and (overwrite or not target.exists()):
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(source.read_bytes())


def _seed_resource(source_rel: str):
    return files(WORKSPACE_SEED_PACKAGE).joinpath(*source_rel.split("/"))


def _ensure_control_files(workspace: Path) -> None:
    from memoria_vault.runtime.vaultio import write_text_durable

    state.write_journal_head_anchor(workspace)
    overrides = workspace / ".memoria/overrides.jsonl"
    if not overrides.exists():
        write_text_durable(overrides, "", create_parent=True)
    manifest = workspace / "system/manifest.jsonl"
    if not manifest.exists():
        write_text_durable(manifest, "", create_parent=True)


def _ensure_git(workspace: Path, *, commit_created_repository: bool = True) -> None:
    git_path = workspace / ".git"
    created_repository = not os.path.lexists(git_path)
    if created_repository:
        _git(workspace, "init", "-q")
    if _git(workspace, "config", "user.email", check=False).returncode:
        _git(workspace, "config", "user.email", "memoria@example.invalid")
    if _git(workspace, "config", "user.name", check=False).returncode:
        _git(workspace, "config", "user.name", "Memoria")
    if (
        created_repository
        and commit_created_repository
        and _git(workspace, "rev-parse", "--verify", "HEAD", check=False).returncode
    ):
        _git(workspace, "add", ".")
        if _git(workspace, "diff", "--cached", "--quiet", check=False).returncode:
            _git(workspace, "commit", "-m", "initialize memoria workspace")


def _git(workspace: Path, *args: str, check: bool = True) -> subprocess.CompletedProcess[str]:
    workspace = Path(workspace).resolve()
    env = {name: value for name, value in os.environ.items() if not name.startswith("GIT_")}
    env["GIT_CONFIG_NOSYSTEM"] = "1"
    env["GIT_CONFIG_GLOBAL"] = os.devnull
    proc = subprocess.run(
        [
            "git",
            f"--git-dir={workspace / '.git'}",
            f"--work-tree={workspace}",
            "-c",
            f"core.hooksPath={os.devnull}",
            "-c",
            "core.fsmonitor=false",
            *args,
        ],
        cwd=workspace,
        env=env,
        check=False,
        text=True,
        capture_output=True,
    )
    if check and proc.returncode:
        raise RuntimeError(proc.stderr.strip() or proc.stdout.strip())
    return proc


def _work_id(args: argparse.Namespace) -> str:
    if args.doi:
        return f"doi-{args.doi.lower()}"
    if args.url:
        return f"url-{uuid.uuid5(uuid.NAMESPACE_URL, args.url).hex[:16]}"
    path = Path(args.file or args.pdf)
    return path.stem


def _csl_json(work_id: str, title: str, doi: str | None, resource: str) -> dict[str, Any]:
    row = {"id": work_id, "type": "article-journal", "title": title}
    if doi:
        row["DOI"] = doi
    if resource:
        row["URL"] = resource
    return row


def _read_provider_replay(path: Path) -> dict[str, Any]:
    if path.is_file():
        data = json.loads(path.read_text(encoding="utf-8"))
        if not isinstance(data, dict):
            raise ValueError("provider replay file must contain a JSON object")
        return data
    payloads: dict[str, Any] = {}
    for child in sorted(path.glob("*.json")):
        payloads[child.stem] = json.loads(child.read_text(encoding="utf-8"))
    return payloads


def _read_json_object(path: Path, label: str) -> dict[str, Any]:
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError(f"{label} must contain a JSON object")
    return data


def _operation_payload(args: argparse.Namespace) -> dict[str, Any]:
    raw = (
        Path(args.payload_file).read_text(encoding="utf-8")
        if args.payload_file
        else args.payload_json
    )
    payload = json.loads(raw)
    if not isinstance(payload, dict):
        raise ValueError("operation payload must be a JSON object")
    payload.setdefault("mode", args.mode)
    return payload


def _interview_payload(args: argparse.Namespace) -> dict[str, Any]:
    payload = {
        "work_id": args.work_id,
        "prompt": args.prompt,
        "response": args.response or "",
        "project_id": args.project_id,
    }
    if args.fixture:
        fixture = json.loads(Path(args.fixture).read_text(encoding="utf-8"))
        if not isinstance(fixture, dict):
            raise ValueError("interview fixture must contain a JSON object")
        payload.update(
            {
                key: str(fixture[key])
                for key in ("prompt", "response", "project_id")
                if key in fixture
            }
        )
    return payload


def _doctor_checks(workspace: Path) -> dict[str, Any]:
    return {
        "workspace_exists": workspace.is_dir(),
        "state_db": state.db_path(workspace).is_file(),
        "git": shutil.which("git") is not None,
    }


def _backup_report(workspace: Path) -> dict[str, Any]:
    from memoria_vault.runtime import backup as runtime_backup

    litestream_configs = [
        ".memoria/config/litestream.yml",
        ".memoria/config/litestream.yaml",
    ]
    backup_configs = [
        ".memoria/config/backup.yaml",
        ".memoria/config/backup.json",
    ]
    blob_sync_configs = [
        ".memoria/config/blob-sync.yaml",
        ".memoria/config/blob-sync.json",
    ]
    remotes = _git_remotes(workspace)
    local_backup = runtime_backup.local_backup_status(workspace)
    runtime_valid = bool(local_backup["inventory_ok"])
    blob_configured = runtime_valid and _valid_blob_backup_config(
        workspace, [*blob_sync_configs, *backup_configs]
    )
    blob_files = int(local_backup["blob_files"])
    ok = bool(local_backup["inventory_ok"]) and (
        blob_files == 0 or blob_configured or bool(local_backup["valid"])
    )
    return {
        "ok": ok,
        "git_remote": {
            "configured": bool(remotes),
            "remotes": remotes,
        },
        "sqlite_replication": {
            "configured": runtime_valid
            and _any_workspace_file(workspace, [*litestream_configs, *backup_configs]),
            "config_paths": [*litestream_configs, *backup_configs],
            "runtime_dependency": False,
        },
        "blob_sync": {
            "configured": blob_configured,
            "blob_root": ".memoria/blobs",
            "blob_root_exists": runtime_valid and (workspace / ".memoria/blobs").is_dir(),
            "files": blob_files,
            "sha256": local_backup["blob_sha256"],
            "config_paths": [*blob_sync_configs, *backup_configs],
        },
        "local_backup": local_backup,
    }


def _git_remotes(workspace: Path) -> list[str]:
    git_dir = workspace / ".git"
    if (
        git_dir.is_symlink()
        or git_dir.is_junction()
        or not git_dir.is_dir()
        or os.path.lexists(git_dir / "commondir")
        or shutil.which("git") is None
    ):
        return []
    proc = _git(workspace, "remote", check=False)
    if proc.returncode:
        return []
    return sorted(line.strip() for line in proc.stdout.splitlines() if line.strip())


def _any_workspace_file(workspace: Path, relpaths: list[str]) -> bool:
    return any(
        not (workspace / rel).is_symlink() and (workspace / rel).is_file() for rel in relpaths
    )


def _valid_blob_backup_config(workspace: Path, relpaths: list[str]) -> bool:
    for rel in relpaths:
        path = workspace / rel
        if path.is_symlink() or not path.is_file():
            continue
        try:
            raw = path.read_text(encoding="utf-8")
            value = json.loads(raw) if path.suffix == ".json" else yaml.safe_load(raw)
        except (OSError, UnicodeError, json.JSONDecodeError, yaml.YAMLError):
            continue
        if not isinstance(value, dict):
            continue
        if "enabled" in value and value["enabled"] is not True:
            continue
        target = value.get("target")
        if isinstance(target, str) and target.strip():
            return True
    return False


def _write_request_job(workspace: Path, request_id: str, status: str, job: dict[str, Any]) -> None:
    args = _request_job_args(job)
    with state.connect(workspace) as conn:
        conn.execute(
            """
            UPDATE operation_requests
            SET status = ?,
                args_json = ?,
                job_json = ?,
                error = ?,
                completed_at = CASE
                    WHEN ? IN ('done', 'failed', 'cancelled') THEN datetime('now')
                    ELSE NULL
                END
            WHERE request_id = ?
            """,
            (
                status,
                json.dumps(args, ensure_ascii=False, sort_keys=True),
                json.dumps(job, ensure_ascii=False, sort_keys=True),
                str(job.get("error") or ""),
                status,
                request_id,
            ),
        )


def _request_job_args(job: dict[str, Any]) -> dict[str, Any]:
    envelope = job.get("request_envelope")
    if not isinstance(envelope, dict) or not isinstance(envelope.get("args"), dict):
        raise ValueError("request job requires immutable envelope arguments")
    args = envelope["args"]
    if job.get("kind") == "operation" and job.get("payload") != args:
        raise ValueError("operation request payload must match immutable envelope arguments")
    return args


def _key_values(values: list[str]) -> dict[str, Any]:
    rows: dict[str, Any] = {}
    for value in values:
        key, sep, item = value.partition("=")
        if not sep or not key.strip():
            raise ValueError(f"expected key=value, got {value!r}")
        try:
            rows[key.strip()] = json.loads(item)
        except json.JSONDecodeError:
            rows[key.strip()] = item
    return rows


def _scope_bearing_request_fields(updates: dict[str, Any]) -> list[str]:
    exact = {
        "id",
        "ids",
        "input",
        "inputs",
        "output",
        "outputs",
        "path",
        "paths",
        "ref",
        "refs",
        "target",
        "targets",
    }
    suffixes = ("_id", "_ids", "_path", "_paths", "_ref", "_refs")
    return sorted(
        key
        for key in updates
        if (normalized := key.strip().lower().replace("-", "_")) in exact
        or normalized.endswith(suffixes)
    )


def _present_updates(args: argparse.Namespace) -> dict[str, Any]:
    fields = (
        "title",
        "description",
        "resource",
        "doi",
        "citekey",
        "provider_coverage",
        "check_status",
        "standing",
        "research_area",
        "methodology",
    )
    return {
        field: value
        for field in fields
        if (value := getattr(args, field, None)) not in (None, [], "")
    }


def _concept_terms(frontmatter: dict[str, Any]) -> list[str]:
    terms = [*_string_list(frontmatter.get("tags"))]
    facets = frontmatter.get("facets") if isinstance(frontmatter.get("facets"), dict) else {}
    for key in ("research_area", "methodology", "topics"):
        terms.extend(_string_list(frontmatter.get(key)))
        terms.extend(_string_list(facets.get(key)))
    return sorted({term for term in terms if term})


def _string_list(value: Any) -> list[str]:
    if isinstance(value, str):
        return [value] if value.strip() else []
    if isinstance(value, list):
        return [item.strip() for item in value if isinstance(item, str) and item.strip()]
    return []


def _workspace_export_payload(workspace: Path) -> dict[str, Any]:
    with state.connect(workspace) as conn:
        requests = {
            row["status"]: row["count"]
            for row in conn.execute(
                "SELECT status, COUNT(*) AS count FROM operation_requests GROUP BY status"
            )
        }
        concepts = {
            row["concept_type"]: row["count"]
            for row in conn.execute(
                "SELECT concept_type, COUNT(*) AS count FROM concepts GROUP BY concept_type"
            )
        }
        event_log = conn.execute("SELECT COUNT(*) AS count FROM event_log").fetchone()["count"]
    return {
        "requests": requests,
        "concepts": concepts,
        "event_log": event_log,
        "operations": len(engine_api.read_operations(workspace)["operations"]),
        "attention_open": len(
            [
                card
                for card in engine_api.read_attention(workspace)["attention"]
                if card["status"] == "open"
            ]
        ),
    }


def _read_vocabulary(path: Path) -> dict[str, list[str]]:
    field = ""
    rows: dict[str, list[str]] = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.startswith("## "):
            field = line.removeprefix("## ").strip()
            rows.setdefault(field, [])
            continue
        if field and line.startswith("- "):
            term = line.removeprefix("- ").split(" — ", 1)[0].strip()
            if term:
                rows[field].append(term)
    rows["topics"] = list(rows.get("research_area", []))
    return rows


def _update_vocabulary(args: argparse.Namespace, *, mode: str) -> int:
    from memoria_vault.runtime.trusted_writer import (
        append_explicit_journal_event,
        commit_explicit_writer_changes,
    )

    if args.actor != "pi":
        raise ValueError(f"vocabulary {mode} requires PI actor authority")
    if args.field not in {"research_area", "methodology"}:
        raise ValueError(
            "vocabulary mutations support research_area and methodology; "
            "topics inherit research_area"
        )
    workspace = _workspace(args)
    path = workspace / "system/vocabulary.md"
    if not path.is_file():
        return _fail("system/vocabulary.md not found", json_output=args.json)
    text = path.read_text(encoding="utf-8")
    if mode == "add":
        text = _vocabulary_add(text, args.field, args.term)
        event_name = "vocabulary_added"
        payload = {"field": args.field, "term": args.term}
    elif mode == "rename":
        text = _vocabulary_rename(text, args.field, args.old, args.new)
        event_name = "vocabulary_renamed"
        payload = {"field": args.field, "old": args.old, "new": args.new}
    else:
        text = _vocabulary_merge(text, args.field, args.old, args.new)
        event_name = "vocabulary_merged"
        payload = {"field": args.field, "old": args.old, "new": args.new}
    path.write_text(text, encoding="utf-8")
    event = append_explicit_journal_event(
        workspace,
        {"event": event_name, "operation": f"vocabulary-{mode}", **payload},
        actor=args.actor,
        machine="memoria-cli",
    )
    commit = commit_explicit_writer_changes(
        workspace,
        f"{mode} vocabulary {args.field}",
        ["system/vocabulary.md"],
        actor=args.actor,
        machine="memoria-cli",
    )
    return _emit(
        {"ok": True, "path": "system/vocabulary.md", "event": event, "commit": commit},
        args,
    )


def _vocabulary_add(text: str, field: str, term: str) -> str:
    lines = text.splitlines()
    start = _heading_index(lines, field)
    if start is None:
        raise ValueError(f"vocabulary field not found: {field}")
    end = _next_heading(lines, start)
    existing = {
        line.removeprefix("- ").split(" — ", 1)[0].strip()
        for line in lines[start + 1 : end]
        if line.startswith("- ")
    }
    if term in existing:
        return text if text.endswith("\n") else f"{text}\n"
    lines.insert(end, f"- {term} — ")
    return "\n".join(lines) + "\n"


def _vocabulary_rename(text: str, field: str, old: str, new: str) -> str:
    lines = text.splitlines()
    start = _heading_index(lines, field)
    if start is None:
        raise ValueError(f"vocabulary field not found: {field}")
    end = _next_heading(lines, start)
    for index in range(start + 1, end):
        if not lines[index].startswith("- "):
            continue
        term, sep, rest = lines[index].removeprefix("- ").partition(" — ")
        if term.strip() == old:
            lines[index] = f"- {new}{f' — {rest}' if sep else ''}"
            return "\n".join(lines) + "\n"
    raise ValueError(f"vocabulary term not found in {field}: {old}")


def _vocabulary_merge(text: str, field: str, old: str, new: str) -> str:
    lines = text.splitlines()
    start = _heading_index(lines, field)
    if start is None:
        raise ValueError(f"vocabulary field not found: {field}")
    end = _next_heading(lines, start)
    found_old = False
    found_new = False
    out = lines[: start + 1]
    for line in lines[start + 1 : end]:
        if not line.startswith("- "):
            out.append(line)
            continue
        term = line.removeprefix("- ").split(" — ", 1)[0].strip()
        if term == new:
            if not found_new:
                found_new = True
                out.append(line)
        elif term == old:
            found_old = True
            if not found_new:
                out.append(line.replace(f"- {old}", f"- {new}", 1))
                found_new = True
        else:
            out.append(line)
    if not found_old:
        raise ValueError(f"vocabulary term not found in {field}: {old}")
    return "\n".join([*out, *lines[end:]]) + "\n"


def _heading_index(lines: list[str], heading: str) -> int | None:
    marker = f"## {heading}"
    for index, line in enumerate(lines):
        if line.strip() == marker:
            return index
    return None


def _next_heading(lines: list[str], start: int) -> int:
    for index in range(start + 1, len(lines)):
        if lines[index].startswith("## "):
            return index
    return len(lines)


def _read_csl_item(text: str) -> dict[str, Any]:
    data = json.loads(text)
    if isinstance(data, list):
        if len(data) != 1 or not isinstance(data[0], dict):
            raise ValueError("CSL import expects one item")
        return data[0]
    if isinstance(data, dict):
        return data
    raise ValueError("CSL import expects a JSON object or one-item array")


def _search_status(workspace: Path) -> dict[str, Any]:
    from memoria_vault.runtime.search_index import SEARCH_INPUT_ROOT, SEARCH_MANIFEST

    manifest_path = workspace / SEARCH_MANIFEST
    document_count = 0
    if manifest_path.is_file():
        try:
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            manifest = {}
        documents = manifest.get("documents")
        document_count = len(documents) if isinstance(documents, list) else 0
    checks = {
        "search_checked_root": (workspace / SEARCH_INPUT_ROOT).is_dir(),
        "search_manifest": manifest_path.is_file(),
    }
    return {
        "checks": checks,
        "engine": "bm25",
        "manifest": SEARCH_MANIFEST,
        "document_count": document_count,
    }


def _runner_status(workspace: Path, provider: str | None, *, live: bool = False) -> dict[str, Any]:
    from memoria_vault.runtime.operations import (
        _load_pydantic_ai_openai,
        _pydantic_ai_chat,
        load_runner_provider_config,
    )

    provider_name = (provider or "local").strip() or "local"
    providers = load_runner_provider_config(workspace)
    if provider_name not in providers:
        raise ValueError(f"unknown runner provider: {provider_name}")
    provider_spec = providers[provider_name]
    base_url = str(provider_spec["url"])
    key_env = provider_spec.get("key_env")
    api_key = os.environ.get(key_env) if isinstance(key_env, str) and key_env else None
    if not api_key:
        api_key = (
            os.environ.get("MEMORIA_MODEL_API_KEY")
            or os.environ.get("OPENAI_API_KEY")
            or os.environ.get("KILOCODE_API_KEY")
        )
    model_name = os.environ.get("MEMORIA_MODEL") or os.environ.get("OPENAI_MODEL") or "doctor"
    checks = {
        "runner_dependency": False,
        "runner_base_url": bool(base_url),
        "runner_agent_constructed": False,
    }
    if live:
        checks["runner_live_dispatch"] = False
    error = ""
    try:
        Agent, OpenAIChatModel, OpenAIProvider = _load_pydantic_ai_openai()
        checks["runner_dependency"] = True
        provider_kwargs = {"base_url": base_url}
        if api_key:
            provider_kwargs["api_key"] = api_key
        model = OpenAIChatModel(model_name, provider=OpenAIProvider(**provider_kwargs))
        Agent(model)
        checks["runner_agent_constructed"] = True
        if live:
            _pydantic_ai_chat(
                {
                    "operation_id": "doctor-runner-live",
                    "allowed_network": [base_url],
                },
                {
                    "mode": "live" if live else "test",
                    "runner": "pydantic-ai",
                    "provider": provider_name,
                    "model": model_name,
                    "base_url": base_url,
                    "key_env": key_env,
                    "params": {"temperature": 0},
                },
                "Reply with a short confirmation that the Memoria runner is reachable.",
            )
            checks["runner_live_dispatch"] = True
    except Exception as exc:  # noqa: BLE001 -- doctor reports adapter failures as data.
        error = str(exc)
    return {
        "checks": checks,
        "provider": provider_name,
        "base_url": base_url,
        "model": model_name,
        "error": error,
    }


def _emit(payload: dict[str, Any], args: argparse.Namespace) -> int:
    ok = bool(payload.get("ok", True))
    if args.json:
        print(json.dumps(payload, ensure_ascii=False, sort_keys=True))
    elif not args.quiet:
        if not ok:
            result = payload.get("result")
            nested = result if isinstance(result, dict) else {}
            detail = str(
                payload.get("error")
                or nested.get("error")
                or payload.get("evidence")
                or nested.get("evidence")
                or payload.get("status")
                or nested.get("status")
                or "operation failed"
            )
            print(f"FAILED: {detail}")
        else:
            for key in ("workspace", "output_path", "path"):
                value = payload.get(key)
                if isinstance(value, str) and value:
                    print(value)
                    break
            else:
                print(_success_detail(payload))
    return 0 if ok else 1


def _success_detail(payload: dict[str, Any]) -> str:
    containers = [payload]
    for key in (
        "result",
        "request",
        "work",
        "event",
        "attention",
        "exploration",
        "export",
        "journal",
        "search",
        "projections",
    ):
        value = payload.get(key)
        if isinstance(value, dict):
            containers.append(value)

    for container in containers:
        for key in (
            "output_path",
            "path",
            "note_path",
            "draft_path",
            "project_path",
            "outline_path",
            "source_path",
            "record_path",
            "target",
            "restored_from",
        ):
            value = container.get(key)
            if isinstance(value, str) and value:
                return value

    for container in containers:
        for key in (
            "work_id",
            "project_id",
            "request_id",
            "job_id",
            "artifact_id",
            "event_id",
            "operation_id",
            "run_id",
        ):
            summary = _summary_value(container.get(key))
            if summary:
                return f"{key}: {summary}"

    for container in containers:
        value = container.get("content_path")
        if isinstance(value, str) and value:
            return value

    for container in containers:
        for key, value in container.items():
            if (
                key.endswith("_count")
                and isinstance(value, (int, float))
                and not isinstance(value, bool)
            ):
                return f"{key}: {value}"
        for key in (
            "concepts",
            "works",
            "requests",
            "operations",
            "events",
            "attention",
            "suggestions",
            "findings",
            "results",
            "outputs",
            "restored",
        ):
            value = container.get(key)
            if isinstance(value, (list, tuple, set)):
                return f"{key}: {len(value)}"

    safe_statuses = {
        "complete",
        "completed",
        "created",
        "done",
        "passed",
        "pending",
        "restored",
        "running",
        "succeeded",
        "success",
        "updated",
        "verified",
    }
    for container in containers:
        status = _summary_value(container.get("status"))
        if status.lower() in safe_statuses:
            return f"status: {status}"

    if any(key not in {"api_version", "ok"} for key in payload):
        return "completed; details available with --json"
    return "ok"


def _summary_value(value: Any) -> str:
    if isinstance(value, bool) or not isinstance(value, (str, int)):
        return ""
    text = " ".join(str(value).split())
    if len(text) > 200:
        return f"{text[:197]}..."
    return text


def _fail(message: str, *, json_output: bool) -> int:
    if json_output:
        print(json.dumps({"ok": False, "error": message}, sort_keys=True))
    else:
        print(f"memoria: error: {message}", file=sys.stderr)
    return 2


def _package_version() -> str:
    return __version__


if __name__ == "__main__":
    raise SystemExit(main())
