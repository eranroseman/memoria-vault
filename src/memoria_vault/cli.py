"""Alpha.14 stdlib CLI entry point."""

from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
import uuid
from importlib.metadata import PackageNotFoundError, version
from pathlib import Path
from typing import Any

from memoria_vault.runtime import state
from memoria_vault.runtime.worker import enqueue_operation, run_next_job, run_pending_jobs


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
    import_cmd.set_defaults(handler=_not_implemented("work import"))

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

    for name in ("interview", "update"):
        cmd = work_sub.add_parser(name)
        _common(cmd)
        cmd.set_defaults(handler=_not_implemented(f"work {name}"))


def _note_commands(sub: argparse._SubParsersAction[argparse.ArgumentParser]) -> None:
    note = sub.add_parser("note")
    note_sub = note.add_subparsers(dest="note_command", required=True)
    for name in ("capture", "propose", "accept", "reject", "link"):
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
    for name in ("trace", "gaps", "suggest-hubs", "export"):
        cmd = project_sub.add_parser(name)
        _common(cmd)
        cmd.set_defaults(handler=_not_implemented(f"project {name}"))


def _request_commands(sub: argparse._SubParsersAction[argparse.ArgumentParser]) -> None:
    request = sub.add_parser("request")
    request_sub = request.add_subparsers(dest="request_command", required=True)
    for name in ("answer", "amend", "cancel", "retry", "resume", "list", "show"):
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
    for name in ("list", "run"):
        cmd = operation_sub.add_parser(name)
        _common(cmd)
        cmd.set_defaults(handler=_not_implemented(f"operation {name}"))


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
        cmd.set_defaults(handler=_not_implemented(f"workspace {name}"))


def _eval_commands(sub: argparse._SubParsersAction[argparse.ArgumentParser]) -> None:
    eval_cmd = sub.add_parser("eval")
    eval_sub = eval_cmd.add_subparsers(dest="eval_command", required=True)
    for name in ("run", "seeded-error-verdict"):
        cmd = eval_sub.add_parser(name)
        _common(cmd)
        cmd.set_defaults(handler=_not_implemented(f"eval {name}"))


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
        checks.update(_qmd_checks(workspace))
    return _emit({"ok": all(checks.values()), "workspace": str(workspace), "checks": checks}, args)


def _cmd_ask(args: argparse.Namespace) -> int:
    result = _enqueue_and_run(
        args,
        "answer-query",
        {"query": args.question, "k": 5},
    )
    return _emit(result, args)


def _cmd_work_capture(args: argparse.Namespace) -> int:
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
    if args.pdf:
        path = Path(args.pdf)
        raw_text = path.read_bytes().decode("latin-1")
        raw_filename = path.name
        text = text or title
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
            },
        ),
        args,
    )


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
            {"source_id": args.work_id, "hub_topics": args.hub_topic},
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


def _cmd_workspace_run(args: argparse.Namespace) -> int:
    results = run_pending_jobs(_workspace(args), limit=args.limit, machine="memoria-cli")
    return _emit({"ok": True, "ran": len(results), "results": results}, args)


def _cmd_workspace_recover(args: argparse.Namespace) -> int:
    restored = state.recover_pending_materializations(_workspace(args))
    return _emit({"ok": True, "restored": restored}, args)


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


def _qmd_checks(workspace: Path) -> dict[str, bool]:
    qmd = shutil.which("qmd")
    node = shutil.which("node")
    return {
        "node": node is not None,
        "qmd": qmd is not None,
        "qmd_checked_root": (workspace / ".memoria/index/qmd/checked").is_dir(),
        "qmd_config_home": (workspace / ".memoria/index/qmd/config").is_dir(),
        "qmd_cache_home": (workspace / ".memoria/index/qmd/cache").is_dir(),
    }


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
