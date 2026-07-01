"""Alpha.14 stdlib CLI entry point."""

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
    run_next_job,
    run_pending_jobs,
    run_request,
)

DEFAULT_DIGEST_TOPICS = ["Framing", "Methods", "Findings", "Gaps", "Implications"]


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
    doctor.set_defaults(handler=_cmd_doctor)
    bundle = doctor_sub.add_parser("bundle")
    _common(bundle)
    bundle.add_argument("--redacted", action="store_true")
    bundle.set_defaults(handler=_not_implemented("doctor bundle"))
    self_test = doctor_sub.add_parser("self-test")
    _common(self_test)
    self_test.set_defaults(handler=_not_implemented("doctor self-test"))

    ask = sub.add_parser("ask")
    _common(ask)
    ask.add_argument("--question", required=True)
    ask.set_defaults(handler=_cmd_ask)

    _work_commands(sub)
    _note_commands(sub)
    _project_commands(sub)
    _request_commands(sub)
    _attention_commands(sub)
    _operation_commands(sub)
    _simple_resource(sub, "steering", {"show", "edit"})
    _simple_resource(sub, "vocabulary", {"list", "add", "rename"})
    _simple_resource(sub, "journal", {"list", "show"})
    _workspace_commands(sub)
    _eval_commands(sub)
    return parser


def _work_commands(sub: argparse._SubParsersAction[argparse.ArgumentParser]) -> None:
    work = sub.add_parser("work")
    work_sub = work.add_subparsers(dest="work_command", required=True)

    capture = work_sub.add_parser("capture")
    _common(capture)
    source = capture.add_mutually_exclusive_group(required=True)
    source.add_argument("--doi")
    source.add_argument("--url")
    source.add_argument("--pdf")
    source.add_argument("--file")
    capture.add_argument("--title")
    capture.add_argument("--description")
    capture.add_argument("--text")
    capture.set_defaults(handler=_cmd_work_capture)

    import_cmd = work_sub.add_parser("import")
    _common(import_cmd)
    import_cmd.add_argument("--format", choices=("bibtex", "csl", "zotero-export"), required=True)
    import_cmd.add_argument("--file", required=True)
    import_cmd.set_defaults(handler=_cmd_work_import)

    enrich = work_sub.add_parser("enrich")
    _common(enrich)
    enrich.add_argument("--work-id", required=True)
    enrich.add_argument("--provider-replay")
    enrich.set_defaults(handler=_cmd_work_enrich)

    digest = work_sub.add_parser("digest")
    _common(digest)
    digest.add_argument("--work-id", required=True)
    digest.add_argument("--hub-topic", action="append", default=[])
    digest.set_defaults(handler=_cmd_work_digest)

    interview = work_sub.add_parser("interview")
    _common(interview)
    interview.add_argument("--work-id", required=True)
    interview.add_argument("--response", required=True)
    interview.add_argument("--prompt", default="What matters about this source?")
    interview.add_argument("--project-id", default="")
    interview.set_defaults(handler=_cmd_work_interview)

    for name in ("update",):
        cmd = work_sub.add_parser(name)
        _common(cmd)
        cmd.set_defaults(handler=_not_implemented(f"work {name}"))


def _note_commands(sub: argparse._SubParsersAction[argparse.ArgumentParser]) -> None:
    note = sub.add_parser("note")
    note_sub = note.add_subparsers(dest="note_command", required=True)
    propose = note_sub.add_parser("propose")
    _common(propose)
    propose.add_argument("--digest-path", required=True)
    candidates = propose.add_mutually_exclusive_group(required=True)
    candidates.add_argument("--candidate-json", action="append")
    candidates.add_argument("--candidates-file")
    propose.set_defaults(handler=_cmd_note_propose)
    accept = note_sub.add_parser("accept")
    _common(accept)
    accept.add_argument("note_path")
    accept.add_argument("--reason", default="")
    accept.set_defaults(handler=_cmd_note_accept)
    reject = note_sub.add_parser("reject")
    _common(reject)
    reject.add_argument("note_path")
    reject.add_argument("--reason", default="")
    reject.set_defaults(handler=_cmd_note_reject)
    link = note_sub.add_parser("link")
    _common(link)
    link.add_argument("source_note_path")
    link.add_argument("--type", choices=("supports", "contradicts", "extends"), required=True)
    link.add_argument("--target", required=True)
    link.add_argument("--reason", default="")
    link.set_defaults(handler=_cmd_note_link)
    for name in ("capture",):
        cmd = note_sub.add_parser(name)
        _common(cmd)
        cmd.set_defaults(handler=_not_implemented(f"note {name}"))


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
    export.set_defaults(handler=_cmd_project_export)
    for name in ("suggest-hubs",):
        cmd = project_sub.add_parser(name)
        _common(cmd)
        cmd.set_defaults(handler=_not_implemented(f"project {name}"))


def _request_commands(sub: argparse._SubParsersAction[argparse.ArgumentParser]) -> None:
    request = sub.add_parser("request")
    request_sub = request.add_subparsers(dest="request_command", required=True)
    list_cmd = request_sub.add_parser("list")
    _common(list_cmd)
    list_cmd.add_argument("--status", choices=("pending", "running", "done", "failed"))
    list_cmd.set_defaults(handler=_cmd_request_list)
    show = request_sub.add_parser("show")
    _common(show)
    show.add_argument("request_id")
    show.set_defaults(handler=_cmd_request_show)
    resume = request_sub.add_parser("resume")
    _common(resume)
    resume.add_argument("request_id")
    resume.set_defaults(handler=_cmd_request_resume)
    for name in ("answer", "amend", "cancel", "retry"):
        cmd = request_sub.add_parser(name)
        _common(cmd)
        cmd.set_defaults(handler=_not_implemented(f"request {name}"))


def _attention_commands(sub: argparse._SubParsersAction[argparse.ArgumentParser]) -> None:
    attention = sub.add_parser("attention")
    attention_sub = attention.add_subparsers(dest="attention_command", required=True)
    for name in ("list", "show", "resolve", "worklist"):
        cmd = attention_sub.add_parser(name)
        _common(cmd)
        cmd.set_defaults(handler=_not_implemented(f"attention {name}"))


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
        else:
            cmd.set_defaults(handler=_not_implemented(f"workspace {name}"))


def _eval_commands(sub: argparse._SubParsersAction[argparse.ArgumentParser]) -> None:
    eval_cmd = sub.add_parser("eval")
    eval_sub = eval_cmd.add_subparsers(dest="eval_command", required=True)
    seeded = eval_sub.add_parser("seeded-error-verdict")
    _common(seeded)
    seeded.set_defaults(handler=_cmd_eval_seeded_error_verdict)
    run = eval_sub.add_parser("run")
    _common(run)
    run.set_defaults(handler=_not_implemented("eval run"))


def _simple_resource(
    sub: argparse._SubParsersAction[argparse.ArgumentParser], name: str, actions: set[str]
) -> None:
    resource = sub.add_parser(name)
    resource_sub = resource.add_subparsers(dest=f"{name}_command", required=True)
    for action in sorted(actions):
        cmd = resource_sub.add_parser(action)
        _common(cmd)
        cmd.set_defaults(handler=_not_implemented(f"{name} {action}"))


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
        return _emit({"workspace": str(workspace), "would_create": created}, args)
    if not args.yes and workspace.exists() and any(workspace.iterdir()):
        return _fail("init on a non-empty workspace requires --yes", json_output=args.json)
    workspace.mkdir(parents=True, exist_ok=True)
    for rel in created:
        (workspace / rel).mkdir(parents=True, exist_ok=True)
    _copy_seed_tree("vault-template/.memoria/schemas", workspace / ".memoria/schemas")
    _copy_seed_tree("vault-template/capabilities", workspace / "capabilities")
    _copy_seed_tree("vault-template/.memoria/enrichment", workspace / ".memoria/enrichment")
    _copy_seed_tree("vault-template/system/eval", workspace / "system/eval")
    _seed_provider_config(workspace)
    state.connect(workspace).close()
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
                "node_version": status["node_version"],
            },
            args,
        )
    return _emit({"ok": all(checks.values()), "workspace": str(workspace), "checks": checks}, args)


def _cmd_ask(args: argparse.Namespace) -> int:
    result = _enqueue_and_run(
        args,
        "answer-query",
        {"query": args.question, "k": 5},
    )
    return _emit(result, args)


def _cmd_work_capture(args: argparse.Namespace) -> int:
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
    raw_text = None
    raw_filename = "source.txt"
    resource = args.url or (f"https://doi.org/{args.doi}" if args.doi else "")
    source_id = _work_id(args)
    identifiers = {"doi": args.doi} if args.doi else {}
    if args.file:
        path = Path(args.file)
        text = path.read_text(encoding="utf-8")
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
            },
        ),
        args,
    )


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
    else:
        return _fail("work import --format zotero-export is not wired yet", json_output=args.json)
    return _emit(_enqueue_and_run(args, "capture-source", payload), args)


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
            {
                "source_id": args.work_id,
                "prompt": args.prompt,
                "response": args.response,
                "project_id": args.project_id,
            },
        ),
        args,
    )


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
            {"seed_terms": args.seed_term, "dense_threshold": args.dense_threshold},
        ),
        args,
    )


def _cmd_project_trace(args: argparse.Namespace) -> int:
    return _emit(
        _enqueue_and_run(args, "analyze-project-argument", {"project_path": args.project_path}),
        args,
    )


def _cmd_project_export(args: argparse.Namespace) -> int:
    return _emit(
        _enqueue_and_run(
            args,
            "render-project-argument-canvas",
            {"project_path": args.project_path},
        ),
        args,
    )


def _cmd_note_propose(args: argparse.Namespace) -> int:
    return _emit(
        _enqueue_and_run(
            args,
            "propose-note-candidates",
            {"digest_path": args.digest_path, "candidates": _note_candidates(args)},
        ),
        args,
    )


def _cmd_note_accept(args: argparse.Namespace) -> int:
    return _cmd_note_curate(args, "accepted")


def _cmd_note_reject(args: argparse.Namespace) -> int:
    return _cmd_note_curate(args, "rejected")


def _cmd_note_curate(args: argparse.Namespace, status: str) -> int:
    return _emit(
        _enqueue_and_run(
            args,
            "curate-note-candidate",
            {"note_path": args.note_path, "status": status, "reason": args.reason},
        ),
        args,
    )


def _cmd_note_link(args: argparse.Namespace) -> int:
    return _emit(
        _enqueue_and_run(
            args,
            "curate-note-link",
            {
                "source_note_path": args.source_note_path,
                "link_type": args.type,
                "target_path": args.target,
                "reason": args.reason,
            },
        ),
        args,
    )


def _cmd_operation_list(args: argparse.Namespace) -> int:
    from memoria_vault.runtime.vaultio import read_frontmatter

    operations = []
    for path in sorted((_workspace(args) / "capabilities/operations").glob("*.md")):
        frontmatter = read_frontmatter(path)
        if frontmatter.get("type") != "operation":
            continue
        operations.append(
            {
                "operation_id": frontmatter.get("operation_id") or path.stem,
                "title": frontmatter.get("title") or path.stem,
                "check_status": frontmatter.get("check_status") or "",
                "risk_class": frontmatter.get("risk_class") or "",
                "runner": frontmatter.get("runner") or "",
            }
        )
    return _emit({"ok": True, "operations": operations}, args)


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


def _cmd_eval_seeded_error_verdict(args: argparse.Namespace) -> int:
    return _emit(_enqueue_and_run(args, "run-seeded-error-verdict", {}), args)


def _cmd_workspace_run(args: argparse.Namespace) -> int:
    results = run_pending_jobs(_workspace(args), limit=args.limit, machine="memoria-cli")
    return _emit({"ok": True, "ran": len(results), "results": results}, args)


def _cmd_workspace_recover(args: argparse.Namespace) -> int:
    restored = state.recover_pending_materializations(_workspace(args))
    return _emit({"ok": True, "restored": restored}, args)


def _cmd_workspace_rebuild(args: argparse.Namespace) -> int:
    if args.embeddings and not args.search:
        return _fail("workspace rebuild --embeddings requires --search", json_output=args.json)
    workspace = _workspace(args)
    from memoria_vault.runtime.capture import write_references_bib

    references = write_references_bib(workspace)
    payload: dict[str, Any] = {"ok": True, "references": references}
    if args.search:
        from memoria_vault.runtime.search_index import rebuild_checked_qmd_source

        manifest = rebuild_checked_qmd_source(workspace)
        payload["qmd"] = _run_qmd_rebuild(workspace, embeddings=args.embeddings)
        payload["qmd"]["manifest"] = manifest
    return _emit(payload, args)


def _not_implemented(command: str):
    def handler(args: argparse.Namespace) -> int:
        return _fail(f"{command} is not wired yet", json_output=args.json)

    return handler


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
    result = run_next_job(workspace, machine="memoria-cli")
    return {
        "ok": result is not None and result.get("status") == "done",
        "job": job,
        "result": result,
    }


def _workspace(args: argparse.Namespace) -> Path:
    return Path(args.workspace).resolve()


def _workspace_plan(workspace: Path) -> list[str]:
    return [
        "knowledge",
        "capabilities",
        "system/eval",
        ".memoria/blobs",
        ".memoria/config",
        ".memoria/index/qmd/checked",
        ".memoria/index/qmd/config",
        ".memoria/index/qmd/cache",
    ]


def _copy_seed_tree(source_rel: str, target: Path) -> None:
    source = _repo_root() / source_rel
    if not source.is_dir():
        return
    if target.exists() and any(target.iterdir()):
        return
    shutil.copytree(source, target, dirs_exist_ok=True)


def _seed_provider_config(workspace: Path) -> None:
    source = workspace / ".memoria/enrichment/providers.yaml"
    target = workspace / ".memoria/config/providers.yaml"
    if source.is_file() and not target.exists():
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


def _note_candidates(args: argparse.Namespace) -> list[dict[str, Any]]:
    if args.candidates_file:
        data = json.loads(Path(args.candidates_file).read_text(encoding="utf-8"))
        rows = data if isinstance(data, list) else [data]
    else:
        rows = [json.loads(raw) for raw in args.candidate_json or []]
    if not rows or not all(isinstance(row, dict) for row in rows):
        raise ValueError("note candidates must be JSON objects")
    return rows


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
        "target_path": row["target_path"],
        "target_hash": row["target_hash"],
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


def _qmd_status(workspace: Path) -> dict[str, Any]:
    qmd = shutil.which("qmd")
    node = shutil.which("node")
    node_version = _node_version(node) if node else ""
    checks = {
        "node": node is not None,
        "node_22": _node_major(node_version) >= 22,
        "qmd": qmd is not None,
        "qmd_absolute": bool(qmd and Path(qmd).is_absolute()),
        "qmd_checked_root": (workspace / ".memoria/index/qmd/checked").is_dir(),
        "qmd_config_home": (workspace / ".memoria/index/qmd/config").is_dir(),
        "qmd_cache_home": (workspace / ".memoria/index/qmd/cache").is_dir(),
    }
    return {
        "checks": checks,
        "qmd_path": str(Path(qmd).resolve()) if qmd else "",
        "node_version": node_version,
    }


def _run_qmd_rebuild(workspace: Path, *, embeddings: bool) -> dict[str, Any]:
    status = _qmd_status(workspace)
    if not all(status["checks"].values()):
        failed = [key for key, ok in status["checks"].items() if not ok]
        raise RuntimeError(f"qmd is not ready: {', '.join(failed)}")
    qmd = status["qmd_path"]
    env = _qmd_env(workspace)
    checked = workspace / ".memoria/index/qmd/checked"
    commands = [
        [qmd, "collection", "add", str(checked), "--name", "memoria-checked", "--mask", "**/*.md"],
        [qmd, "update"],
    ]
    if embeddings:
        commands.append([qmd, "embed", "--chunk-strategy", "auto"])
    for command in commands:
        _run(command, cwd=workspace, env=env)
    return {
        "qmd_path": qmd,
        "config_home": env["XDG_CONFIG_HOME"],
        "cache_home": env["XDG_CACHE_HOME"],
        "commands": [" ".join(command) for command in commands],
    }


def _qmd_env(workspace: Path) -> dict[str, str]:
    env = dict(os.environ)
    config = workspace / ".memoria/index/qmd/config"
    cache = workspace / ".memoria/index/qmd/cache"
    config.mkdir(parents=True, exist_ok=True)
    cache.mkdir(parents=True, exist_ok=True)
    env["XDG_CONFIG_HOME"] = str(config)
    env["XDG_CACHE_HOME"] = str(cache)
    return env


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
