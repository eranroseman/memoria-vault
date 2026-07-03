"""Alpha.15 stdlib CLI entry point."""

from __future__ import annotations

import argparse
import base64
import json
import os
import shutil
import subprocess
import sys
import uuid
from importlib.metadata import PackageNotFoundError, version
from pathlib import Path
from typing import Any

from memoria_vault.runtime import state
from memoria_vault.runtime.worker import (
    enqueue_operation,
    run_pending_jobs,
    run_request,
)

DEFAULT_DIGEST_TOPICS = ["Framing", "Methods", "Findings", "Gaps", "Implications"]
JOURNAL_OPERATION_ALIASES = {"work.digest": ("compile-source-digest",)}
SEED_TREES = (
    ("vault-template/.memoria/schemas", ".memoria/schemas"),
    ("vault-template/capabilities", "capabilities"),
    ("vault-template/.memoria/config", ".memoria/config"),
    ("vault-template/system/eval", "system/eval"),
)
SEED_FILES = (
    ("vault-template/steering.md", "steering.md"),
    ("vault-template/system/vocabulary.md", "system/vocabulary.md"),
)


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
    parser = argparse.ArgumentParser(prog="memoria")
    parser.add_argument("--version", action="version", version=f"memoria {_package_version()}")
    sub = parser.add_subparsers(dest="command", required=True)

    init = sub.add_parser("init")
    _common(init, workspace_required=False)
    init.add_argument("--yes", action="store_true")
    init.add_argument("--dry-run", action="store_true")
    init.set_defaults(handler=_cmd_init)

    status = sub.add_parser("status")
    _common(status)
    status.set_defaults(handler=_cmd_status)

    doctor = sub.add_parser("doctor")
    doctor_sub = doctor.add_subparsers(dest="doctor_command")
    _common(doctor, workspace_required=False)
    doctor.add_argument("--check", choices=("qmd", "runner"), default=None)
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

    _new_commands(sub)
    _work_commands(sub)
    _lifecycle_commands(sub)
    _project_commands(sub)
    _request_commands(sub)
    _attention_commands(sub)
    _operation_commands(sub)
    _simple_resource(sub, "steering", {"show", "edit"})
    _simple_resource(sub, "vocab", {"list", "add", "merge", "rename"})
    _simple_resource(sub, "journal", {"show", "tail"})
    _workspace_commands(sub)
    _eval_commands(sub)
    return parser


def _new_commands(sub: argparse._SubParsersAction[argparse.ArgumentParser]) -> None:
    new = sub.add_parser("new")
    new_sub = new.add_subparsers(dest="new_command", required=True)

    note = new_sub.add_parser("note")
    _common(note)
    note.add_argument("title")
    body = note.add_mutually_exclusive_group(required=True)
    body.add_argument("--body")
    body.add_argument("--file")
    note.add_argument("--mode", choices=("claim", "question"), default="claim")
    note.add_argument("--tag", action="append", default=[])
    note.set_defaults(handler=_cmd_new_note)

    hub = new_sub.add_parser("hub")
    _common(hub)
    hub.add_argument("tag")
    hub.add_argument("--title")
    hub.add_argument("--description", default="")
    hub.set_defaults(handler=_cmd_new_hub)

    project = new_sub.add_parser("project")
    _common(project)
    project.add_argument("name")
    project.add_argument("--description", default="")
    project.set_defaults(handler=_cmd_new_project)


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
    update.add_argument(
        "--metadata-status", choices=("verified", "partial", "unverified", "not-indexed")
    )
    update.add_argument("--check-status", choices=("unchecked", "checked", "quarantined"))
    update.add_argument("--standing", choices=("current", "archived", "retracted", "superseded"))
    update.add_argument("--research-area", action="append", default=[])
    update.add_argument("--topic", action="append", default=[])
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
    check.add_argument(
        "--assert",
        dest="assertions",
        action="append",
        choices=("no-legacy-work-markdown",),
        default=[],
    )
    check.set_defaults(handler=_cmd_check)

    show = sub.add_parser("show")
    _common(show)
    show.add_argument("target")
    show.set_defaults(handler=_cmd_show)

    list_cmd = sub.add_parser("list")
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
    trace = project_sub.add_parser("trace")
    _common(trace)
    trace.add_argument("project_path")
    trace.set_defaults(handler=_cmd_project_trace)
    export = project_sub.add_parser("export")
    _common(export)
    export.add_argument("project_path")
    export.add_argument("--format", choices=("markdown", "docx", "pdf", "odt"), default="markdown")
    export.add_argument("--output")
    export.set_defaults(handler=_cmd_project_export)
    suggest = project_sub.add_parser("suggest-hubs")
    _common(suggest)
    suggest.add_argument("--min-count", type=int, default=2)
    suggest.set_defaults(handler=_cmd_project_suggest_hubs)


def _request_commands(sub: argparse._SubParsersAction[argparse.ArgumentParser]) -> None:
    request = sub.add_parser("request")
    request_sub = request.add_subparsers(dest="request_command", required=True)
    list_cmd = request_sub.add_parser("list")
    _common(list_cmd)
    list_cmd.add_argument("--status", choices=("pending", "running", "done", "failed", "cancelled"))
    list_cmd.set_defaults(handler=_cmd_request_list)
    show = request_sub.add_parser("show")
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
    list_cmd = attention_sub.add_parser("list")
    _common(list_cmd)
    list_cmd.add_argument("--status")
    list_cmd.add_argument("--kind")
    list_cmd.set_defaults(handler=_cmd_attention_list)
    show = attention_sub.add_parser("show")
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
    worklist = attention_sub.add_parser("worklist")
    _common(worklist)
    worklist.set_defaults(handler=_cmd_attention_worklist)


def _operation_commands(sub: argparse._SubParsersAction[argparse.ArgumentParser]) -> None:
    operation = sub.add_parser("operation")
    operation_sub = operation.add_subparsers(dest="operation_command", required=True)
    list_cmd = operation_sub.add_parser("list")
    _common(list_cmd)
    list_cmd.set_defaults(handler=_cmd_operation_list)
    run = operation_sub.add_parser("run")
    _common(run)
    run.add_argument("operation_id")
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
    for name in ("scan", "rollback", "check", "rebuild", "export"):
        cmd = workspace_sub.add_parser(name)
        _common(cmd)
        if name == "rebuild":
            cmd.add_argument("--search", action="store_true")
            cmd.add_argument("--embeddings", action="store_true")
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
            cmd.add_argument(
                "--assert",
                dest="assertions",
                action="append",
                choices=("no-legacy-work-markdown",),
                default=[],
            )
            cmd.set_defaults(handler=_cmd_workspace_check)
        elif name == "export":
            cmd.add_argument("--output")
            cmd.set_defaults(handler=_cmd_workspace_export)


def _eval_commands(sub: argparse._SubParsersAction[argparse.ArgumentParser]) -> None:
    eval_cmd = sub.add_parser("eval")
    eval_sub = eval_cmd.add_subparsers(dest="eval_command", required=True)
    seeded = eval_sub.add_parser("seeded-error-verdict")
    _common(seeded)
    seeded.set_defaults(handler=_cmd_eval_seeded_error_verdict)
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
        cmd = resource_sub.add_parser(action)
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
            cmd.add_argument("--operation")
            cmd.add_argument("--request-id")
            cmd.add_argument("--path")
            cmd.add_argument("--decision")
            cmd.add_argument("--date")
            cmd.add_argument("--limit", type=int, default=50)
            cmd.set_defaults(handler=_cmd_journal_tail)
        elif name == "journal" and action == "show":
            cmd.add_argument("event_id", type=int)
            cmd.set_defaults(handler=_cmd_journal_show)
        else:
            raise ValueError(f"unsupported resource action: {name} {action}")


def _common(parser: argparse.ArgumentParser, *, workspace_required: bool = True) -> None:
    parser.add_argument("--workspace", required=workspace_required)
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--quiet", action="store_true")
    parser.add_argument("--verbose", action="store_true")
    parser.add_argument("--idempotency-key")
    parser.add_argument("--schedule-id")


def _cmd_init(args: argparse.Namespace) -> int:
    workspace = Path(args.workspace or ".").resolve()
    created = _workspace_plan(workspace)
    if args.dry_run:
        return _emit(_init_dry_run_report(workspace, created), args)
    if not args.yes and workspace.exists() and any(workspace.iterdir()):
        return _fail("init on a non-empty workspace requires --yes", json_output=args.json)
    workspace.mkdir(parents=True, exist_ok=True)
    for rel in created:
        (workspace / rel).mkdir(parents=True, exist_ok=True)
    _seed_workspace(workspace, overwrite=False)
    state.connect(workspace).close()
    from memoria_vault.runtime.projections import write_tracked_projections

    write_tracked_projections(workspace)
    _ensure_git(workspace)
    return _emit({"ok": True, "workspace": str(workspace), "created": created}, args)


def _cmd_status(args: argparse.Namespace) -> int:
    workspace = _workspace(args)
    with state.connect(workspace) as conn:
        requests = conn.execute(
            "SELECT status, COUNT(*) AS count FROM operation_requests GROUP BY status"
        ).fetchall()
    return _emit(
        {
            "workspace": str(workspace),
            "db": state.db_path(workspace).relative_to(workspace).as_posix(),
            "requests": {row["status"]: row["count"] for row in requests},
        },
        args,
    )


def _cmd_doctor(args: argparse.Namespace) -> int:
    workspace = Path(args.workspace).resolve() if args.workspace else Path.cwd()
    repaired: list[str] = []
    if args.repair:
        if not workspace.is_dir():
            return _fail("doctor --repair requires an existing workspace", json_output=args.json)
        repaired = _repair_workspace(workspace)
    checks: dict[str, Any] = {
        "workspace_exists": workspace.is_dir(),
        "state_db": state.db_path(workspace).is_file(),
        "git": shutil.which("git") is not None,
    }
    if args.check == "qmd":
        status = _qmd_status(workspace)
        checks.update(status["checks"])
        return _emit(
            {
                "ok": all(checks.values()),
                "workspace": str(workspace),
                "checks": checks,
                "qmd_path": status["qmd_path"],
                "qmd_source": status["qmd_source"],
                "qmd_error": status["qmd_error"],
                "node_version": status["node_version"],
                "qmd_doctor_output": status["qmd_doctor_output"],
                "qmd_collection_output": status["qmd_collection_output"],
                "repaired": repaired,
            },
            args,
        )
    if args.live and args.check != "runner":
        return _fail("doctor --live is only valid with --check runner", json_output=args.json)
    if args.check == "runner":
        status = _runner_status(args.provider, live=args.live)
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
    return _emit(
        {
            "ok": all(checks.values()),
            "workspace": str(workspace),
            "checks": checks,
            "repaired": repaired,
        },
        args,
    )


def _cmd_doctor_bundle(args: argparse.Namespace) -> int:
    workspace = _workspace(args)
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
    return _emit(
        {
            "ok": True,
            "workspace": str(workspace),
            "redacted": bool(args.redacted),
            "doctor": _doctor_checks(workspace),
            "requests": requests,
            "journal_head": state.journal_head(workspace),
        },
        args,
    )


def _cmd_doctor_self_test(args: argparse.Namespace) -> int:
    workspace = _workspace(args)
    checks = _doctor_checks(workspace)
    checks["operation_catalog"] = bool(_operation_rows(workspace))
    return _emit({"ok": all(checks.values()), "workspace": str(workspace), "checks": checks}, args)


def _cmd_ask(args: argparse.Namespace) -> int:
    result = _enqueue_and_run(
        args,
        "answer-query",
        {"query": args.question, "k": 5},
    )
    return _emit(result, args)


def _cmd_new_note(args: argparse.Namespace) -> int:
    return _write_new_concept(
        args,
        "note",
        args.title,
        body=args.body if args.body is not None else Path(args.file).read_text(encoding="utf-8"),
        tags=args.tag,
        extra={"mode": args.mode},
    )


def _cmd_new_hub(args: argparse.Namespace) -> int:
    title = args.title or args.tag
    body = f"# {title}\n\n"
    return _write_new_concept(
        args,
        "hub",
        title,
        body=body,
        tags=[args.tag],
        extra={"tag": args.tag, "description": args.description},
    )


def _cmd_new_project(args: argparse.Namespace) -> int:
    body = f"# {args.name}\n\n"
    return _write_new_concept(
        args,
        "project",
        args.name,
        body=body,
        tags=[],
        extra={"description": args.description},
    )


def _cmd_work_add(args: argparse.Namespace) -> int:
    if args.url:
        payload = {
            "url": args.url,
            "title": args.title,
            "description": args.description,
            "stage_only": True,
        }
        return _emit(_enqueue_and_run(args, "capture-url-source", payload), args)
    if args.pdf:
        path = Path(args.pdf)
        source_id = path.stem
        payload = {
            "source_id": source_id,
            "title": args.title or source_id,
            "description": args.description or f"Captured PDF: {path.name}",
            "raw_pdf_base64": base64.b64encode(path.read_bytes()).decode(),
            "raw_filename": path.name,
            "stage_only": True,
        }
        return _emit(_enqueue_and_run(args, "capture-pdf-source", payload), args)
    title = args.title or args.doi or args.url or Path(args.file or args.pdf).stem
    description = args.description or f"Captured work: {title}"
    text = args.text or ""
    text_status = "full-text" if args.text else "metadata-only"
    raw_text = None
    raw_filename = "source.txt"
    resource = args.url or (f"https://doi.org/{args.doi}" if args.doi else "")
    source_id = _work_id(args)
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
                "source_id": source_id,
                "title": title,
                "description": description,
                "content_text": text,
                "raw_text": raw_text if raw_text is not None else text,
                "raw_filename": raw_filename,
                "resource": resource,
                "identifiers": identifiers,
                "csl_json": _csl_json(source_id, title, args.doi, resource),
                "stage_only": bool(args.file),
                "text_status": text_status,
            },
        ),
        args,
    )


def _cmd_work_export(args: argparse.Namespace) -> int:
    workspace = _workspace(args)
    work = state.catalog_source(workspace, args.work_id)
    if work is None:
        return _fail(f"work not found: {args.work_id}", json_output=args.json)
    payload = {"ok": True, "work": work}
    if args.output:
        output = workspace / args.output
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(json.dumps(work, indent=2, sort_keys=True) + "\n", encoding="utf-8")
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
    payload: dict[str, Any] = {"source_id": args.work_id}
    if args.provider_replay:
        payload["provider_payloads"] = _read_provider_replay(Path(args.provider_replay))
    return _emit(_enqueue_and_run(args, "enrich-source", payload), args)


def _cmd_work_digest(args: argparse.Namespace) -> int:
    return _emit(
        _enqueue_and_run(
            args,
            "compile-source-digest",
            {"source_id": args.work_id, "hub_topics": args.hub_topic or DEFAULT_DIGEST_TOPICS},
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
    payload = {"source_id": args.work_id, **_present_updates(args)}
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
        if frontmatter.get("type") not in {"work", "note"}:
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


def _cmd_project_export(args: argparse.Namespace) -> int:
    result = _enqueue_and_run(
        args,
        "export-project",
        {
            "project_path": args.project_path,
            "format": args.format,
            "output_path": args.output or "",
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


def _write_new_concept(
    args: argparse.Namespace,
    concept_type: str,
    title: str,
    *,
    body: str,
    tags: list[str],
    extra: dict[str, Any],
) -> int:
    from memoria_vault.runtime.paths import safe_filename
    from memoria_vault.runtime.policy.audit import sha256_file
    from memoria_vault.runtime.trusted_writer import append_journal_event, commit_writer_changes
    from memoria_vault.runtime.vaultio import (
        apply_universal_concept_frontmatter,
        write_frontmatter_doc,
    )

    workspace = _workspace(args)
    homes = {
        "note": "knowledge/notes",
        "hub": "knowledge/hubs",
        "project": "knowledge/projects",
    }
    slug = safe_filename(title.lower()).strip("._-") or concept_type
    rel = _unique_rel(workspace, f"{homes[concept_type]}/{slug}.md")
    frontmatter = {
        "type": concept_type,
        "title": title,
        "tags": tags,
        "links": {},
    }
    frontmatter.update({key: value for key, value in extra.items() if value not in (None, "")})
    apply_universal_concept_frontmatter(frontmatter, rel)
    write_frontmatter_doc(workspace / rel, frontmatter, body, create_parent=True)
    state.record_observed_file_edit(
        workspace,
        output_id=rel,
        concept_type=concept_type,
        output_sha256=sha256_file(workspace / rel),
    )
    event = append_journal_event(
        workspace,
        {
            "event": "concept_created",
            "operation": f"new-{concept_type}",
            "concept_type": concept_type,
            "output_id": rel,
            "actor": "pi",
        },
        machine="memoria-cli",
    )
    commit = commit_writer_changes(
        workspace, f"new {concept_type} {Path(rel).stem}", [rel], machine="memoria-cli"
    )
    return _emit(
        {"ok": True, "path": rel, "concept": frontmatter, "event": event, "commit": commit},
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
    workspace = _workspace(args)
    path = _resolve_concept_path(workspace, args.target)
    if path is None:
        work = state.catalog_source(workspace, args.target)
        if work is None:
            return _fail(f"target not found: {args.target}", json_output=args.json)
        return _emit({"ok": True, "target": args.target, "kind": "work", "work": work}, args)
    from memoria_vault.runtime.vaultio import split_frontmatter

    rel = path.relative_to(workspace).as_posix()
    frontmatter, body = split_frontmatter(path.read_text(encoding="utf-8"))
    return _emit(
        {
            "ok": True,
            "path": rel,
            "type": frontmatter.get("type"),
            "verdict": state.concept_check_status(workspace, rel),
            "frontmatter": frontmatter,
            "body": body,
        },
        args,
    )


def _cmd_list(args: argparse.Namespace) -> int:
    from memoria_vault.runtime.vaultio import iter_markdown, read_frontmatter

    workspace = _workspace(args)
    rows = []
    for path in iter_markdown(workspace):
        rel = path.relative_to(workspace).as_posix()
        frontmatter = read_frontmatter(path)
        concept_type = str(frontmatter.get("type") or "")
        if concept_type not in {"note", "work", "hub", "project"}:
            continue
        if args.type and concept_type != args.type:
            continue
        rows.append(
            {
                "path": rel,
                "type": concept_type,
                "title": frontmatter.get("title") or path.stem,
                "verdict": state.concept_check_status(workspace, rel),
            }
        )
    return _emit({"ok": True, "concepts": sorted(rows, key=lambda row: row["path"])}, args)


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
    return _emit({"ok": True, "operations": _operation_rows(_workspace(args))}, args)


def _cmd_operation_run(args: argparse.Namespace) -> int:
    return _emit(
        _enqueue_and_run(args, args.operation_id, _operation_payload(args)),
        args,
    )


def _cmd_request_list(args: argparse.Namespace) -> int:
    sql = """
        SELECT request_id, operation_id, status, created_at, completed_at, error
        FROM operation_requests
    """
    params: tuple[str, ...] = ()
    if args.status:
        sql += " WHERE status = ?"
        params = (args.status,)
    sql += " ORDER BY created_at, request_id"
    with state.connect(_workspace(args)) as conn:
        requests = [_request_summary(row) for row in conn.execute(sql, params)]
    return _emit({"ok": True, "requests": requests}, args)


def _cmd_request_show(args: argparse.Namespace) -> int:
    with state.connect(_workspace(args)) as conn:
        row = conn.execute(
            """
            SELECT *
            FROM operation_requests
            WHERE request_id = ?
            """,
            (args.request_id,),
        ).fetchone()
    if row is None:
        return _fail(f"request not found: {args.request_id}", json_output=args.json)
    return _emit({"ok": True, "request": _request_detail(row)}, args)


def _cmd_request_resume(args: argparse.Namespace) -> int:
    result = run_request(_workspace(args), args.request_id, machine="memoria-cli")
    return _emit({"ok": result.get("status") == "done", "result": result}, args)


def _cmd_request_answer(args: argparse.Namespace) -> int:
    workspace = _workspace(args)
    row = _request_row(workspace, args.request_id)
    if row is None:
        return _fail(f"request not found: {args.request_id}", json_output=args.json)
    answers = _key_values(args.answers)
    job = json.loads(row["job_json"])
    payload = job.get("payload") if isinstance(job.get("payload"), dict) else {}
    payload["answers"] = {**payload.get("answers", {}), **answers}
    job["payload"] = payload
    _write_request_job(workspace, args.request_id, row["status"], job)
    state.append_journal_event(
        workspace,
        {
            "event": "request_answered",
            "request_id": args.request_id,
            "answers": sorted(answers),
        },
        machine="memoria-cli",
    )
    return _emit(
        {"ok": True, "request": _request_detail(_request_row(workspace, args.request_id))}, args
    )


def _cmd_request_amend(args: argparse.Namespace) -> int:
    workspace = _workspace(args)
    row = _request_row(workspace, args.request_id)
    if row is None:
        return _fail(f"request not found: {args.request_id}", json_output=args.json)
    updates = _key_values(args.updates)
    job = json.loads(row["job_json"])
    payload = job.get("payload") if isinstance(job.get("payload"), dict) else {}
    payload.update(updates)
    job["payload"] = payload
    _write_request_job(
        workspace, args.request_id, "pending", {**job, "status": "pending", "error": ""}
    )
    state.append_journal_event(
        workspace,
        {
            "event": "request_amended",
            "request_id": args.request_id,
            "updates": sorted(updates),
        },
        machine="memoria-cli",
    )
    return _emit(
        {"ok": True, "request": _request_detail(_request_row(workspace, args.request_id))}, args
    )


def _cmd_request_cancel(args: argparse.Namespace) -> int:
    workspace = _workspace(args)
    row = _request_row(workspace, args.request_id)
    if row is None:
        return _fail(f"request not found: {args.request_id}", json_output=args.json)
    job = json.loads(row["job_json"])
    job["status"] = "cancelled"
    job["error"] = f"cancelled: {args.reason}"
    _write_request_job(workspace, args.request_id, "cancelled", job)
    state.append_journal_event(
        workspace,
        {
            "event": "request_cancelled",
            "request_id": args.request_id,
            "reason": args.reason,
        },
        machine="memoria-cli",
    )
    return _emit(
        {"ok": True, "request": _request_detail(_request_row(workspace, args.request_id))}, args
    )


def _cmd_request_retry(args: argparse.Namespace) -> int:
    workspace = _workspace(args)
    row = _request_row(workspace, args.request_id)
    if row is None:
        return _fail(f"request not found: {args.request_id}", json_output=args.json)
    if row["status"] not in {"failed", "cancelled"}:
        return _fail(
            f"request retry requires failed or cancelled status, got {row['status']}",
            json_output=args.json,
        )
    job = json.loads(row["job_json"])
    job["status"] = "pending"
    job.pop("error", None)
    _write_request_job(workspace, args.request_id, "pending", job)
    state.append_journal_event(
        workspace,
        {"event": "request_retried", "request_id": args.request_id},
        machine="memoria-cli",
    )
    return _emit(
        {"ok": True, "request": _request_detail(_request_row(workspace, args.request_id))}, args
    )


def _cmd_attention_list(args: argparse.Namespace) -> int:
    cards = [
        card
        for card in _attention_cards(_workspace(args))
        if (not args.status or card["status"] == args.status)
        and (not args.kind or card["kind"] == args.kind)
    ]
    return _emit({"ok": True, "attention": cards}, args)


def _cmd_attention_show(args: argparse.Namespace) -> int:
    workspace = _workspace(args)
    rel, path = _workspace_file(workspace, args.attention_path)
    card = _attention_card(path, workspace)
    if card is None:
        return _fail(f"attention projection not found: {rel}", json_output=args.json)
    return _emit({"ok": True, "attention": card}, args)


def _cmd_attention_resolve(args: argparse.Namespace) -> int:
    workspace = _workspace(args)
    rel, path = _workspace_file(workspace, args.attention_path)
    card = _attention_card(path, workspace)
    if card is None:
        return _fail(f"attention projection not found: {rel}", json_output=args.json)
    outcome = args.resolution_outcome
    reason = args.reason or f"PI chose to {outcome} attention"
    return _emit(
        _enqueue_and_run(
            args,
            "resolve-attention",
            {
                "target_id": rel,
                "reason": reason,
                "outcome": outcome,
                "routing_class": card["routing_class"],
            },
        ),
        args,
    )


def _cmd_attention_worklist(args: argparse.Namespace) -> int:
    work_kinds = {"candidate", "gap", "work-prompt"}
    cards = [
        card
        for card in _attention_cards(_workspace(args))
        if card["status"] == "open" and card["kind"] in work_kinds
    ]
    return _emit({"ok": True, "attention": cards}, args)


def _cmd_eval_seeded_error_verdict(args: argparse.Namespace) -> int:
    return _emit(_enqueue_and_run(args, "run-seeded-error-verdict", {}), args)


def _cmd_workspace_run(args: argparse.Namespace) -> int:
    results = run_pending_jobs(_workspace(args), limit=args.limit, machine="memoria-cli")
    payload = {"ok": True, "ran": len(results), "results": results}
    if args.schedule_id:
        payload["schedule_id"] = args.schedule_id
    return _emit(payload, args)


def _cmd_workspace_recover(args: argparse.Namespace) -> int:
    workspace = _workspace(args)
    fixture = _workspace_recover_fixture(workspace, args.fixture) if args.fixture else None
    restored = state.recover_pending_materializations(workspace)
    payload = {"ok": True, "restored": restored}
    if fixture is not None:
        payload["fixture"] = fixture
    return _emit(payload, args)


def _cmd_workspace_scan(args: argparse.Namespace) -> int:
    workspace = _workspace(args)
    fixture = _workspace_scan_fixture(workspace, args.fixture) if args.fixture else None
    projection_paths = _changed_generated_projection_paths(workspace)
    quarantine = None
    regeneration = None
    if projection_paths:
        quarantine = _enqueue_and_run(
            args,
            "trace-integrity-scan",
            {
                "paths": projection_paths,
                "reason": "workspace-scan-generated-projection",
            },
        )
        regeneration = _enqueue_and_run(args, "regenerate-tracked-projections", {})
    observed = _enqueue_and_run(args, "observe-pi-edits", {})
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
    }
    if quarantine is not None:
        payload["quarantine"] = quarantine["result"]
        payload["quarantine_job"] = quarantine["job"]
    if regeneration is not None:
        payload["regeneration"] = regeneration["result"]
        payload["regeneration_job"] = regeneration["job"]
    if fixture is not None:
        payload["fixture"] = fixture
    if args.schedule_id:
        payload["schedule_id"] = args.schedule_id
    return _emit(payload, args)


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
    assertions = _workspace_assertions(workspace, args.assertions)
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
                "ok": (
                    all(result["ok"] for result in results)
                    and projections["ok"]
                    and assertions["ok"]
                ),
                "schedule_id": args.schedule_id,
                "jobs": sweep["jobs"],
                "checks": results,
                "projections": projections,
                "assertions": assertions["checks"],
            },
            args,
        )
    results = [
        _enqueue_and_run(args, operation_id, {"shadow": bool(args.shadow)})
        for operation_id in INTEGRITY_SWEEP_OPERATIONS
    ]
    return _emit(
        {
            "ok": (
                all(result["ok"] for result in results) and projections["ok"] and assertions["ok"]
            ),
            "checks": results,
            "projections": projections,
            "assertions": assertions["checks"],
        },
        args,
    )


def _cmd_workspace_rebuild(args: argparse.Namespace) -> int:
    if args.embeddings and not args.search:
        return _fail("workspace rebuild --embeddings requires --search", json_output=args.json)
    workspace = _workspace(args)
    from memoria_vault.runtime.capture import write_references_bib
    from memoria_vault.runtime.trusted_writer import rebuild_concept_mirror_from_files

    mirror = rebuild_concept_mirror_from_files(workspace)
    references = write_references_bib(workspace)
    payload: dict[str, Any] = {"ok": True, "concept_mirror": mirror, "references": references}
    if args.search:
        from memoria_vault.runtime.search_index import rebuild_checked_qmd_source

        manifest = rebuild_checked_qmd_source(workspace, embeddings=args.embeddings)
        payload["qmd"] = _run_qmd_rebuild(workspace, embeddings=args.embeddings)
        payload["qmd"]["manifest"] = manifest
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
    from memoria_vault.runtime.trusted_writer import append_journal_event, commit_writer_changes

    workspace = _workspace(args)
    body = args.body if args.body is not None else Path(args.file).read_text(encoding="utf-8")
    path = workspace / "steering.md"
    path.write_text(body if body.endswith("\n") else f"{body}\n", encoding="utf-8")
    event = append_journal_event(
        workspace,
        {"event": "steering_updated", "operation": "steering-edit", "output_id": "steering.md"},
        machine="memoria-cli",
    )
    commit = commit_writer_changes(
        workspace, "update steering", ["steering.md"], machine="memoria-cli"
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
    workspace = _workspace(args)
    sql = """
        SELECT event_id, timestamp, event_type, machine, payload_json, prev_hash, row_hash
        FROM journal_events
    """
    clauses = []
    params: list[str] = []
    if args.operation:
        operations = _journal_operation_values(args.operation)
        placeholders = ", ".join("?" for _ in operations)
        clauses.append(
            "("
            f"json_extract(payload_json, '$.operation') IN ({placeholders}) OR "
            f"json_extract(payload_json, '$.workflow') IN ({placeholders})"
            ")"
        )
        params.extend(operations)
        params.extend(operations)
    if args.request_id:
        clauses.append("json_extract(payload_json, '$.request_id') = ?")
        params.append(args.request_id)
    if args.path:
        path_fields = ("output_id", "target_id", "target_path", "linked_id", "quarantined_id")
        clauses.append(
            "("
            + " OR ".join(f"json_extract(payload_json, '$.{field}') = ?" for field in path_fields)
            + ")"
        )
        params.extend([args.path] * len(path_fields))
    if args.decision:
        clauses.append("json_extract(payload_json, '$.decision') = ?")
        params.append(args.decision)
    if args.date:
        clauses.append("timestamp LIKE ?")
        params.append(f"{args.date}%")
    if clauses:
        sql += " WHERE " + " AND ".join(clauses)
    sql += " ORDER BY event_id DESC LIMIT ?"
    params.append(str(max(args.limit, 1)))
    with state.connect(workspace) as conn:
        events = [_journal_row(row) for row in conn.execute(sql, params)]
    return _emit({"ok": True, "events": events}, args)


def _cmd_journal_show(args: argparse.Namespace) -> int:
    with state.connect(_workspace(args)) as conn:
        row = conn.execute(
            """
            SELECT event_id, timestamp, event_type, machine, payload_json, prev_hash, row_hash
            FROM journal_events
            WHERE event_id = ?
            """,
            (args.event_id,),
        ).fetchone()
    if row is None:
        return _fail(f"journal event not found: {args.event_id}", json_output=args.json)
    return _emit({"ok": True, "event": _journal_row(row)}, args)


def _enqueue_and_run(
    args: argparse.Namespace, operation_id: str, payload: dict[str, Any]
) -> dict[str, Any]:
    workspace = _workspace(args)
    job = enqueue_operation(
        workspace,
        operation_id,
        payload=payload,
        idempotency_key=args.idempotency_key,
        provenance={"surface": "memoria-cli", "command": operation_id},
        schedule_id=args.schedule_id,
    )
    result = run_request(workspace, str(job["job_id"]), machine="memoria-cli")
    return {
        "ok": result is not None and result.get("status") == "done",
        "job": job,
        "result": result,
    }


def _queue_import_enrichment(
    args: argparse.Namespace, payload: dict[str, Any], output: dict[str, Any]
) -> dict[str, Any] | None:
    result = output.get("result")
    if not isinstance(result, dict) or result.get("status") != "done":
        return None
    if not _payload_doi(payload):
        return None
    source_id = str(result.get("source_id") or "").strip()
    if not source_id:
        return None
    workspace = _workspace(args)
    return enqueue_operation(
        workspace,
        "enrich-source",
        payload={"source_id": source_id},
        idempotency_key=f"enrich-{source_id}",
        input_refs=[{"id": source_id, "kind": "catalog_source"}],
        primary_target=f"catalog/sources/{source_id}",
        causal_refs=[str(output["job"]["job_id"])],
        provenance={"surface": "memoria-cli", "command": "work-import"},
        schedule_id=args.schedule_id,
    )


def _payload_doi(payload: dict[str, Any]) -> str:
    identifiers = payload.get("identifiers") if isinstance(payload.get("identifiers"), dict) else {}
    csl_json = payload.get("csl_json") if isinstance(payload.get("csl_json"), dict) else {}
    return str(identifiers.get("doi") or csl_json.get("DOI") or "").strip()


def _workspace(args: argparse.Namespace) -> Path:
    return Path(args.workspace).resolve()


def _workspace_scan_fixture(workspace: Path, fixture: str) -> dict[str, str]:
    if fixture != "direct-write-generated-projection":
        raise ValueError(f"unknown workspace scan fixture: {fixture}")
    rel = "knowledge/_views/index.md"
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
    from memoria_vault.runtime.trusted_writer import promote_checked, stage_concept

    rel = "knowledge/notes/crash-before-materialization.md"
    content = (
        "---\n"
        "type: note\n"
        "title: Crash-before-materialization fixture\n"
        "tags: []\n"
        "links: {}\n"
        "---\n\n"
        "This note exists to prove pending file materializations replay from SQLite.\n"
    )
    stage_concept(
        workspace,
        rel,
        content,
        operation="recover-fixture",
        run_id="fixture:crash-before-materialization",
        machine="memoria-cli",
    )
    promote_checked(workspace, rel, machine="memoria-cli")
    path = workspace / rel
    if path.is_file():
        path.unlink()
    return {"name": fixture, "path": rel}


def _changed_generated_projection_paths(workspace: Path) -> list[str]:
    from memoria_vault.runtime.projections import changed_tracked_projection_paths

    return changed_tracked_projection_paths(workspace)


def _workspace_file(workspace: Path, value: str) -> tuple[str, Path]:
    raw = Path(value)
    path = raw if raw.is_absolute() else workspace / raw
    resolved = path.resolve()
    try:
        rel = resolved.relative_to(workspace.resolve()).as_posix()
    except ValueError as exc:
        raise ValueError(f"path must be inside workspace: {value}") from exc
    return rel, resolved


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
        if frontmatter.get("type") not in {"note", "work", "hub", "project"}:
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


def _attention_cards(workspace: Path) -> list[dict[str, Any]]:
    return [
        card
        for path in sorted((workspace / "inbox").glob("*.md"))
        if (card := _attention_card(path, workspace)) is not None
    ]


def _attention_card(path: Path, workspace: Path) -> dict[str, Any] | None:
    from memoria_vault.runtime.vaultio import split_frontmatter

    if not path.is_file():
        return None
    text = path.read_text(encoding="utf-8")
    frontmatter, body = split_frontmatter(text)
    if frontmatter.get("projection") != "attention":
        return None
    rel = path.resolve().relative_to(workspace.resolve()).as_posix()
    return {
        "path": rel,
        "title": frontmatter.get("title") or path.stem,
        "kind": frontmatter.get("attention_kind") or "",
        "status": frontmatter.get("attention_status") or "",
        "routing_class": frontmatter.get("routing_class") or "ask",
        "target": frontmatter.get("target") or frontmatter.get("target_id") or "",
        "loudness": frontmatter.get("loudness") or "",
        "frontmatter": frontmatter,
        "body": body,
    }


def _workspace_plan(workspace: Path) -> list[str]:
    return [
        "knowledge",
        "capabilities",
        "system",
        "system/eval",
        ".memoria/blobs",
        ".memoria/config",
        ".memoria/index/qmd/checked",
        ".memoria/index/qmd/config",
    ]


def _init_dry_run_report(workspace: Path, planned_dirs: list[str]) -> dict[str, Any]:
    from memoria_vault.runtime.projections import TRACKED_PROJECTION_PATHS

    seed_trees = [target for _, target in SEED_TREES]
    seed_files = [target for _, target in SEED_FILES]
    qmd = {
        "collection": "memoria-checked",
        "checked_root": ".memoria/index/qmd/checked",
        "config_dir": ".memoria/index/qmd/config",
        "index_path": ".memoria/index/qmd/index.sqlite",
        "mask": "**/*.md",
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
        "qmd": qmd,
        "provider_config": {
            "path": ".memoria/config/providers.yaml",
            "seeded": ".memoria/config" in seed_trees,
            "exists": (workspace / ".memoria/config/providers.yaml").is_file(),
        },
    }


def _seed_workspace(workspace: Path, *, overwrite: bool) -> None:
    for source_rel, target_rel in SEED_TREES:
        _copy_seed_tree(source_rel, workspace / target_rel, overwrite=overwrite)
    for source_rel, target_rel in SEED_FILES:
        _copy_seed_file(source_rel, workspace / target_rel, overwrite=overwrite)


def _repair_workspace(workspace: Path) -> list[str]:
    for rel in _workspace_plan(workspace):
        (workspace / rel).mkdir(parents=True, exist_ok=True)
    _seed_workspace(workspace, overwrite=True)
    state.connect(workspace).close()
    from memoria_vault.runtime.projections import write_tracked_projections

    write_tracked_projections(workspace)
    _ensure_git(workspace)
    return sorted([target for _, target in (*SEED_TREES, *SEED_FILES)])


def _copy_seed_tree(source_rel: str, target: Path, *, overwrite: bool) -> None:
    source = _repo_root() / source_rel
    if not source.is_dir():
        return
    if target.exists() and any(target.iterdir()) and not overwrite:
        return
    shutil.copytree(source, target, dirs_exist_ok=True)


def _copy_seed_file(source_rel: str, target: Path, *, overwrite: bool) -> None:
    source = _repo_root() / source_rel
    if source.is_file() and (overwrite or not target.exists()):
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, target)


def _ensure_git(workspace: Path) -> None:
    if not (workspace / ".git").exists():
        _git(workspace, "init", "-q")
    if _git(workspace, "config", "user.email", check=False).returncode:
        _git(workspace, "config", "user.email", "memoria@example.invalid")
    if _git(workspace, "config", "user.name", check=False).returncode:
        _git(workspace, "config", "user.name", "Memoria")
    if _git(workspace, "rev-parse", "--verify", "HEAD", check=False).returncode:
        _git(workspace, "add", ".")
        if _git(workspace, "diff", "--cached", "--quiet", check=False).returncode:
            _git(workspace, "commit", "-m", "initialize memoria workspace")


def _git(workspace: Path, *args: str, check: bool = True) -> subprocess.CompletedProcess[str]:
    proc = subprocess.run(
        ["git", *args],
        cwd=workspace,
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


def _csl_json(source_id: str, title: str, doi: str | None, resource: str) -> dict[str, Any]:
    row = {"id": source_id, "type": "article-journal", "title": title}
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


def _operation_payload(args: argparse.Namespace) -> dict[str, Any]:
    raw = (
        Path(args.payload_file).read_text(encoding="utf-8")
        if args.payload_file
        else args.payload_json
    )
    payload = json.loads(raw)
    if not isinstance(payload, dict):
        raise ValueError("operation payload must be a JSON object")
    return payload


def _interview_payload(args: argparse.Namespace) -> dict[str, Any]:
    payload = {
        "source_id": args.work_id,
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


def _operation_rows(workspace: Path) -> list[dict[str, Any]]:
    from memoria_vault.runtime.capabilities import render_capability_index

    operations = []
    catalog = json.loads(render_capability_index(workspace))
    for row in catalog["capabilities"]:
        if row.get("type") != "operation":
            continue
        operations.append(
            {
                "operation_id": row.get("operation_id") or row["id"],
                "title": row.get("title") or row["id"],
                "check_status": row.get("check_status") or "",
                "risk_class": row.get("risk_class") or "",
                "runner": row.get("runner") or "",
            }
        )
    return operations


def _doctor_checks(workspace: Path) -> dict[str, Any]:
    return {
        "workspace_exists": workspace.is_dir(),
        "state_db": state.db_path(workspace).is_file(),
        "git": shutil.which("git") is not None,
    }


def _workspace_assertions(workspace: Path, assertions: list[str]) -> dict[str, Any]:
    checks = []
    for assertion in assertions:
        if assertion == "no-legacy-work-markdown":
            findings = [
                path.relative_to(workspace).as_posix()
                for path in sorted((workspace / "catalog/sources").glob("*/source.md"))
            ]
            checks.append({"assertion": assertion, "ok": not findings, "findings": findings})
    return {"ok": all(check["ok"] for check in checks), "checks": checks}


def _request_row(workspace: Path, request_id: str) -> Any | None:
    with state.connect(workspace) as conn:
        return conn.execute(
            """
            SELECT *
            FROM operation_requests
            WHERE request_id = ?
            """,
            (request_id,),
        ).fetchone()


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
    payload = job.get("payload")
    envelope = job.get("request_envelope")
    if isinstance(payload, dict):
        args = payload
    elif isinstance(envelope, dict) and isinstance(envelope.get("args"), dict):
        args = envelope["args"]
    else:
        args = {}
    if isinstance(envelope, dict):
        envelope["args"] = args
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


def _present_updates(args: argparse.Namespace) -> dict[str, Any]:
    fields = (
        "title",
        "description",
        "resource",
        "doi",
        "citekey",
        "metadata_status",
        "check_status",
        "standing",
        "research_area",
        "topic",
    )
    return {
        field: value
        for field in fields
        if (value := getattr(args, field, None)) not in (None, [], "")
    }


def _unique_rel(workspace: Path, rel: str) -> str:
    path = workspace / rel
    if not path.exists():
        return rel
    stem = path.with_suffix("")
    suffix = path.suffix
    index = 2
    while True:
        candidate = Path(f"{stem}-{index}{suffix}")
        if not candidate.exists():
            return candidate.relative_to(workspace).as_posix()
        index += 1


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
        journal_events = conn.execute("SELECT COUNT(*) AS count FROM journal_events").fetchone()[
            "count"
        ]
    return {
        "requests": requests,
        "concepts": concepts,
        "journal_events": journal_events,
        "operations": len(_operation_rows(workspace)),
        "attention_open": len(
            [card for card in _attention_cards(workspace) if card["status"] == "open"]
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
    return rows


def _update_vocabulary(args: argparse.Namespace, *, mode: str) -> int:
    from memoria_vault.runtime.trusted_writer import append_journal_event, commit_writer_changes

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
    event = append_journal_event(
        workspace,
        {"event": event_name, "operation": f"vocabulary-{mode}", **payload},
        machine="memoria-cli",
    )
    commit = commit_writer_changes(
        workspace,
        f"{mode} vocabulary {args.field}",
        ["system/vocabulary.md"],
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


def _journal_row(row: Any) -> dict[str, Any]:
    return {
        "event_id": row["event_id"],
        "timestamp": row["timestamp"],
        "event_type": row["event_type"],
        "machine": row["machine"],
        "payload": json.loads(row["payload_json"]),
        "prev_hash": row["prev_hash"],
        "row_hash": row["row_hash"],
    }


def _journal_operation_values(operation: str) -> list[str]:
    return sorted({operation, *JOURNAL_OPERATION_ALIASES.get(operation, ())})


def _request_summary(row: Any) -> dict[str, Any]:
    return {
        "request_id": row["request_id"],
        "operation_id": row["operation_id"],
        "status": row["status"],
        "created_at": row["created_at"],
        "completed_at": row["completed_at"],
        "error": row["error"],
    }


def _request_detail(row: Any) -> dict[str, Any]:
    return {
        **_request_summary(row),
        "args": json.loads(row["args_json"]),
        "idempotency_key": row["idempotency_key"],
        "input_refs": json.loads(row["input_refs_json"]),
        "output_intents": json.loads(row["output_intents_json"]),
        "primary_target": row["primary_target"],
        "precondition_hashes": json.loads(row["precondition_hashes_json"]),
        "causal_refs": json.loads(row["causal_refs_json"]),
        "actor": row["actor"],
        "provenance": json.loads(row["provenance_json"]),
        "schedule_id": row["schedule_id"],
        "kind": row["kind"],
        "job": json.loads(row["job_json"]),
    }


def _read_csl_item(text: str) -> dict[str, Any]:
    data = json.loads(text)
    if isinstance(data, list):
        if len(data) != 1 or not isinstance(data[0], dict):
            raise ValueError("CSL import expects one item")
        return data[0]
    if isinstance(data, dict):
        return data
    raise ValueError("CSL import expects a JSON object or one-item array")


def _qmd_status(workspace: Path, *, include_collection: bool = True) -> dict[str, Any]:
    from memoria_vault.runtime.search_index import resolve_qmd_executable

    qmd_info = resolve_qmd_executable()
    qmd = qmd_info["path"]
    node = shutil.which("node")
    node_version = _node_version(node) if node else ""
    doctor = _qmd_doctor_status(workspace, qmd) if qmd else {}
    collection = _qmd_collection_status(workspace, qmd) if qmd and include_collection else {}
    checks = {
        "node": node is not None,
        "node_22": _node_major(node_version) >= 22,
        "qmd": bool(qmd),
        "qmd_absolute": bool(qmd and Path(qmd).is_absolute()),
        "qmd_checked_root": (workspace / ".memoria/index/qmd/checked").is_dir(),
        "qmd_config_dir": (workspace / ".memoria/index/qmd/config").is_dir(),
        "qmd_index_home": (workspace / ".memoria/index/qmd").is_dir(),
        "qmd_doctor": bool(doctor.get("qmd_doctor", False)),
        "qmd_embedding_models": bool(doctor.get("qmd_embedding_models", False)),
    }
    checks.update(collection.get("checks", {}))
    return {
        "checks": checks,
        "qmd_path": qmd,
        "qmd_source": qmd_info["source"],
        "qmd_error": qmd_info["error"],
        "node_version": node_version,
        "qmd_doctor_output": doctor.get("qmd_doctor_output", ""),
        "qmd_collection_output": collection.get("qmd_collection_output", ""),
    }


def _runner_status(provider: str | None, *, live: bool = False) -> dict[str, Any]:
    from memoria_vault.runtime.operations import (
        _load_pydantic_ai_openai,
        _pydantic_ai_chat,
        model_base_url,
    )

    provider_name = (provider or "default").strip() or "default"
    base_url = model_base_url(provider_name)
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
                    "runner": "pydantic-ai",
                    "provider": provider_name,
                    "model": model_name,
                    "allowed_network": [base_url],
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


def _run_qmd_rebuild(workspace: Path, *, embeddings: bool) -> dict[str, Any]:
    status = _qmd_status(workspace, include_collection=False)
    checks = dict(status["checks"])
    if not embeddings:
        checks.pop("qmd_embedding_models", None)
    if not all(checks.values()):
        failed = [key for key, ok in checks.items() if not ok]
        if embeddings and "qmd_embedding_models" in failed:
            raise RuntimeError("qmd embedding models are missing; run `qmd pull` before embeddings")
        raise RuntimeError(f"qmd is not ready: {', '.join(failed)}")
    qmd = status["qmd_path"]
    env = _qmd_env(workspace)
    checked = workspace / ".memoria/index/qmd/checked"
    commands = [
        [qmd, "collection", "remove", "memoria-checked"],
        [qmd, "collection", "add", str(checked), "--name", "memoria-checked", "--mask", "**/*.md"],
        [qmd, "update"],
    ]
    if embeddings:
        commands.append([qmd, "embed", "--chunk-strategy", "auto"])
    for command in commands:
        try:
            _run(command, cwd=workspace, env=env)
        except RuntimeError as exc:
            if command[1:3] == ["collection", "remove"] and "Collection not found" in str(exc):
                continue
            raise
    return {
        "qmd_path": qmd,
        "config_home": env["QMD_CONFIG_DIR"],
        "cache_home": env.get("XDG_CACHE_HOME", ""),
        "index_path": env["INDEX_PATH"],
        "commands": [" ".join(command) for command in commands],
    }


def _qmd_env(workspace: Path) -> dict[str, str]:
    env = dict(os.environ)
    root = workspace / ".memoria/index/qmd"
    config = root / "config"
    index = root / "index.sqlite"
    config.mkdir(parents=True, exist_ok=True)
    env["QMD_CONFIG_DIR"] = str(config)
    env["INDEX_PATH"] = str(index)
    return env


def _qmd_doctor_status(
    workspace: Path, qmd: str, *, env: dict[str, str] | None = None
) -> dict[str, Any]:
    try:
        proc = subprocess.run(
            [qmd, "doctor"],
            cwd=workspace,
            env=env or _qmd_env(workspace),
            check=False,
            text=True,
            capture_output=True,
            timeout=15,
        )
    except subprocess.TimeoutExpired:
        return {
            "qmd_doctor": False,
            "qmd_embedding_models": False,
            "qmd_doctor_output": "qmd doctor timed out",
        }
    output = "\n".join(value for value in (proc.stdout, proc.stderr) if value).strip()
    return {
        "qmd_doctor": proc.returncode == 0,
        "qmd_embedding_models": proc.returncode == 0 and "model cache: missing" not in output,
        "qmd_doctor_output": output[-4000:],
    }


def _qmd_collection_status(workspace: Path, qmd: str) -> dict[str, Any]:
    expected_root = (workspace / ".memoria/index/qmd/checked").resolve()
    try:
        proc = subprocess.run(
            [qmd, "collection", "show", "memoria-checked"],
            cwd=workspace,
            env=_qmd_env(workspace),
            check=False,
            text=True,
            capture_output=True,
            timeout=15,
        )
    except subprocess.TimeoutExpired:
        output = "qmd collection show memoria-checked timed out"
        return {
            "checks": {
                "qmd_collection": False,
                "qmd_collection_root": False,
                "qmd_collection_mask": False,
            },
            "qmd_collection_output": output,
        }
    output = "\n".join(value for value in (proc.stdout, proc.stderr) if value).strip()
    root, mask = _parse_qmd_collection_show(output)
    root_ok = bool(root) and Path(root).expanduser().resolve() == expected_root
    mask_ok = mask == "**/*.md"
    return {
        "checks": {
            "qmd_collection": proc.returncode == 0,
            "qmd_collection_root": proc.returncode == 0 and root_ok,
            "qmd_collection_mask": proc.returncode == 0 and mask_ok,
        },
        "qmd_collection_output": output[-4000:],
    }


def _parse_qmd_collection_show(output: str) -> tuple[str, str]:
    root = ""
    mask = ""
    for line in output.splitlines():
        key, sep, value = line.strip().partition(":")
        if not sep:
            continue
        if key == "Path":
            root = value.strip()
        elif key in {"Pattern", "Mask"}:
            mask = value.strip()
    return root, mask


def _node_version(node: str) -> str:
    proc = subprocess.run([node, "--version"], check=False, text=True, capture_output=True)
    return proc.stdout.strip()


def _node_major(version_text: str) -> int:
    text = version_text.strip().removeprefix("v")
    major = text.split(".", 1)[0]
    return int(major) if major.isdigit() else 0


def _run(command: list[str], *, cwd: Path, env: dict[str, str]) -> None:
    proc = subprocess.run(command, cwd=cwd, env=env, check=False, text=True, capture_output=True)
    if proc.returncode:
        raise RuntimeError(proc.stderr.strip() or proc.stdout.strip())


def _emit(payload: dict[str, Any], args: argparse.Namespace) -> int:
    if args.json:
        print(json.dumps(payload, ensure_ascii=False, sort_keys=True))
    elif not args.quiet:
        print(payload.get("workspace") or payload.get("ok") or "ok")
    return 0 if payload.get("ok", True) else 1


def _fail(message: str, *, json_output: bool) -> int:
    if json_output:
        print(json.dumps({"ok": False, "error": message}, sort_keys=True))
    else:
        print(f"memoria: error: {message}", file=sys.stderr)
    return 2


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[2]


def _package_version() -> str:
    try:
        return version("memoria-vault")
    except PackageNotFoundError:
        return "0.0.0"


if __name__ == "__main__":
    raise SystemExit(main())
