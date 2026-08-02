"""Stdlib CLI entry point."""

from __future__ import annotations

import argparse
import base64
import json
import math
import os
import secrets
import shutil
import sqlite3
import subprocess
import sys
import time
import uuid
from collections.abc import Callable
from contextlib import contextmanager
from importlib.resources import files
from pathlib import Path
from typing import Any

import yaml

from memoria_vault import __version__
from memoria_vault.engine import api as engine_api
from memoria_vault.engine import cockpit as engine_cockpit
from memoria_vault.engine.empirical_events import REASON_CODES
from memoria_vault.engine.surface_contract import SURFACE_ACTIONS, SURFACE_JOBS, actions_by_id
from memoria_vault.runtime import evidence_review, onboarding_steps, state
from memoria_vault.runtime.evidence_review import EVIDENCE_REVIEW_ROUTING_TYPES
from memoria_vault.runtime.paths import safe_filename
from memoria_vault.runtime.subsystems.lib.edges import LINK_RELATIONS
from memoria_vault.runtime.time import now_iso
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
    ("Start here.md", "Start here.md"),
    ("steering.md", "steering.md"),
    ("system/vocabulary.md", "system/vocabulary.md"),
    ("catalog.base", "catalog.base"),
    ("claims.base", "claims.base"),
    ("inbox.base", "inbox.base"),
    ("projects.base", "projects.base"),
    ("sources.base", "sources.base"),
    ("system/templates/session-diary.md", "system/templates/session-diary.md"),
)
# The agent bundle is a first-install bootstrap, not a repair-managed runtime
# seed: it is absent from the rosters above, so a later doctor repair cannot
# recreate or overwrite PI-owned agent configuration and perimeter policy.
# `runtime.bundles` is the single init-path writer of every bundle path
# (write-if-absent) and feeds `.memoria/vault.json` — see `_seed_write_allowed`.
# Seeded-config lifecycle — two classes (consolidation 2026-07-12, line 105).
# View preferences are seeded once and PI-owned afterwards: repair/upgrade must
# not clobber an existing copy (it does reseed a deleted one). Data projections
# are never seeded — they are regenerated always via
# runtime.projections.TRACKED_PROJECTION_PATHS (+ argument canvases). Every
# seeded path absent from this manifest is a runtime seed and is repair-restored.
SEED_CLASS_VIEW_PREFERENCE: str = "view-preference"
SEED_CLASSES: dict[str, str] = {
    "catalog.base": SEED_CLASS_VIEW_PREFERENCE,
    "claims.base": SEED_CLASS_VIEW_PREFERENCE,
    "inbox.base": SEED_CLASS_VIEW_PREFERENCE,
    "projects.base": SEED_CLASS_VIEW_PREFERENCE,
    "sources.base": SEED_CLASS_VIEW_PREFERENCE,
    ".obsidian/graph.json": SEED_CLASS_VIEW_PREFERENCE,
    ".obsidian/types.json": SEED_CLASS_VIEW_PREFERENCE,
    "steering.md": SEED_CLASS_VIEW_PREFERENCE,
    "system/vocabulary.md": SEED_CLASS_VIEW_PREFERENCE,
}
VIEW_PREFERENCE_PATHS: frozenset[str] = frozenset(
    rel for rel, cls in SEED_CLASSES.items() if cls == SEED_CLASS_VIEW_PREFERENCE
)
SURFACE_ACTION = actions_by_id()
PROJECT_EXPLORE_HELP = (
    "List exploration-channel candidates. Distinct from memoria explore <topic>, "
    "which surfaces a checked topic neighborhood."
)


def main(argv: list[str] | None = None) -> int:
    from memoria_vault.runtime.secrets import load_secrets

    secrets_report = load_secrets()
    if secrets_report["warning"]:
        print(f"memoria: {secrets_report['warning']}", file=sys.stderr)
    parser = _build_parser()
    args = parser.parse_args(argv)
    args._secrets_loaded_from_file = frozenset(secrets_report["loaded"])
    args._secrets_warning = secrets_report["warning"]
    args._secrets_path = secrets_report["path"]
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
    parser.add_argument("--version", action="version", version=f"memoria {__version__}")
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
    init.add_argument(
        "--onboard",
        action="store_true",
        help="Run the interactive onboarding runway after initialization.",
    )
    init.set_defaults(handler=_cmd_init)

    onboard_help = "Walk from installed engine to the tutorial open in Obsidian."
    onboard = sub.add_parser("onboard", description=onboard_help, help=onboard_help)
    _common(onboard, workspace_required=False)
    onboard.set_defaults(handler=_cmd_onboard)

    status = sub.add_parser("status", **_surface_help("status.read"))
    _common(status)
    status.set_defaults(handler=_cmd_status)

    context = sub.add_parser("context", **_surface_help("context.read"))
    _common(context)
    context.set_defaults(handler=_cmd_context)

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
    bundle.set_defaults(handler=_cmd_doctor_bundle)
    self_test = doctor_sub.add_parser("self-test")
    _common(self_test)
    self_test.set_defaults(handler=_cmd_doctor_self_test)

    ask = sub.add_parser("ask")
    _common(ask)
    ask.add_argument("--question", required=True)
    ask.add_argument("--trace", action="store_true")
    ask.set_defaults(handler=_cmd_ask)

    secrets_cmd = sub.add_parser("secrets")
    secrets_sub = secrets_cmd.add_subparsers(dest="secrets_command", required=True)
    secrets_set = secrets_sub.add_parser("set")
    _common(secrets_set, workspace_required=False)
    secrets_set.add_argument("name")
    secrets_set.set_defaults(handler=_cmd_secrets_set)
    secrets_list = secrets_sub.add_parser("list")
    _common(secrets_list, workspace_required=False)
    secrets_list.set_defaults(handler=_cmd_secrets_list)

    explore = sub.add_parser("explore", **_surface_help("explore.read"))
    _common(explore)
    explore.add_argument("topic")
    explore.add_argument("--versus", default="")
    explore.add_argument("--project", default="")
    explore.add_argument("--depth", type=int, default=1)
    explore.add_argument("--trace", action="store_true")
    explore.set_defaults(handler=_cmd_explore)

    serve = sub.add_parser("serve")
    _common(serve)
    serve.add_argument("--watch", action="store_true")
    serve.add_argument("--http", action="store_true")
    serve.add_argument("--host", default="127.0.0.1")
    serve.add_argument("--port", type=int, default=8765)
    serve.add_argument("--read-scope", action="append", default=[])
    serve.add_argument("--once", action="store_true")
    serve.add_argument("--poll-interval", type=float, default=1.0)
    serve.add_argument("--on-demand", action="store_true")
    serve.add_argument("--ephemeral", action="store_true")
    serve.add_argument("--idle-exit", type=float, default=900.0)
    serve.add_argument("--stop", action="store_true")
    serve.set_defaults(handler=_cmd_serve)

    handshake = sub.add_parser("handshake")
    handshake.add_argument("--vault", required=True)
    handshake.add_argument("--spawn", action="store_true")
    handshake.add_argument("--json", action="store_true")
    handshake.add_argument("--quiet", action="store_true")
    handshake.set_defaults(handler=_cmd_handshake)

    mcp = sub.add_parser("mcp")
    mcp.add_argument("--workspace", required=True)
    mcp.add_argument("--read-scope", action="append", default=[])
    mcp.add_argument("--actor", default="agent")
    mcp.set_defaults(handler=_cmd_mcp)

    help_cmd = sub.add_parser(
        "help",
        help="Show Memoria surfaces grouped by the five workspace jobs.",
        description="Show Memoria surfaces grouped by the five workspace jobs.",
    )
    help_cmd.set_defaults(handler=_cmd_help)

    # U2 T.3 registered cockpit.read, so the help comes from the row rather
    # than the literal C.4 parked here while the command had no registry entry.
    cockpit_cmd = sub.add_parser("cockpit", **_surface_help("cockpit.read"))
    _common(cockpit_cmd)
    cockpit_cmd.add_argument("--project", default="")
    cockpit_cmd.add_argument("--triage", action="store_true")
    cockpit_cmd.set_defaults(handler=_cmd_cockpit)

    # U2 T.3 registered `dashboard.read` for this command, so the help comes
    # from that row rather than the literal I1 H.2 parked here while the command
    # had none. `views.dashboard` remains the separate HTTP view row.
    dashboard_cmd = sub.add_parser("dashboard", **_surface_help("dashboard.read"))
    _common(dashboard_cmd)
    dashboard_cmd.set_defaults(handler=_cmd_dashboard)

    _surface_commands(sub)
    _new_commands(sub)
    _work_commands(sub)
    _seed_commands(sub)
    _lifecycle_commands(sub)
    _project_commands(sub)
    _request_commands(sub)
    _attention_commands(sub)
    _operation_commands(sub)
    _review_commands(sub)
    _simple_resource(sub, "steering", {"show", "edit"})
    _simple_resource(sub, "vocab", {"list", "add", "merge", "rename"})
    _simple_resource(sub, "journal", {"revert-preview", "show", "tail", "verify"})
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
    import_cmd.add_argument("--enrich", action="store_true")
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


def _seed_commands(sub: argparse._SubParsersAction[argparse.ArgumentParser]) -> None:
    seed = sub.add_parser("seed")
    seed_sub = seed.add_subparsers(dest="seed_command", required=True)

    install = seed_sub.add_parser("install")
    _common(install)
    install.set_defaults(handler=_cmd_seed_install)


def _lifecycle_commands(sub: argparse._SubParsersAction[argparse.ArgumentParser]) -> None:
    link = sub.add_parser("link")
    _common(link)
    link.add_argument("source_path")
    link.add_argument("target_path")
    link.add_argument("--rel", required=True, choices=tuple(sorted(LINK_RELATIONS)))
    link.add_argument("--reason", default="")
    link.set_defaults(handler=_cmd_link)

    mv = sub.add_parser("mv")
    _common(mv)
    mv.add_argument("old_path")
    mv.add_argument("new_path")
    mv.add_argument("--reason", default="")
    mv.set_defaults(handler=_cmd_mv)

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
    resolve_evidence.add_argument(
        "--decision", choices=("accept", "reject", "edit", "defer"), required=True
    )
    resolve_evidence.add_argument("--reason", default="")
    resolve_evidence.add_argument("--warrant", default="")
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
    export.add_argument("--allow-not-ready", dest="allow_unready", action="store_true")
    export.add_argument("--draft", action="store_true")
    export.set_defaults(handler=_cmd_project_export)
    explore = project_sub.add_parser(
        "explore",
        help=PROJECT_EXPLORE_HELP,
        description=PROJECT_EXPLORE_HELP,
    )
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
    list_cmd.add_argument(
        "--order-by",
        default="",
        help=(
            "Comma-separated ranking factors for this listing "
            "(priority, loudness, impact, staleness, age); overrides attention.yaml. "
            "The block pin always sorts first."
        ),
    )
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


def _nonnegative_int(value: str) -> int:
    parsed = int(value)
    if parsed < 0:
        raise argparse.ArgumentTypeError("must be nonnegative")
    return parsed


def _positive_int(value: str) -> int:
    parsed = int(value)
    if parsed <= 0:
        raise argparse.ArgumentTypeError("must be positive")
    return parsed


def _review_commands(sub: argparse._SubParsersAction[argparse.ArgumentParser]) -> None:
    review = sub.add_parser("review")
    review_sub = review.add_subparsers(dest="review_command", required=True)
    list_cmd = review_sub.add_parser("list")
    _common(list_cmd)
    list_cmd.add_argument("--type", choices=EVIDENCE_REVIEW_ROUTING_TYPES, default="")
    list_cmd.add_argument("--project", default="")
    # Stricter than the collector: `batch=0` is the engine-direct id lookup.
    list_cmd.add_argument("--min-age-days", type=_nonnegative_int, default=0)
    list_cmd.add_argument("--batch", type=_positive_int, default=10)
    list_cmd.set_defaults(handler=_cmd_review_list)
    show = review_sub.add_parser("show")
    _common(show)
    show.add_argument("evidence_id")
    show.add_argument("--show-analysis", action="store_true")
    show.set_defaults(handler=_cmd_review_show)
    for decision in ("accept", "reject", "edit", "defer"):
        action = review_sub.add_parser(decision)
        _common(action)
        action.add_argument("evidence_id")
        action.add_argument("--reason", default="")
        action.add_argument("--reason-code", choices=sorted(REASON_CODES), default="other")
        if decision == "accept":
            # The seam raises on a warrant riding any other decision, so the
            # parser never offers one.
            action.add_argument("--warrant", default="")
        action.set_defaults(handler=_cmd_review_action, review_decision=decision)
    stats = review_sub.add_parser("stats")
    _common(stats)
    stats.set_defaults(handler=_cmd_review_stats)


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
        elif name == "journal" and action == "revert-preview":
            cmd.description = _surface_summary("trace.revert_preview")
            cmd.add_argument("event_id", type=int)
            cmd.set_defaults(handler=_cmd_journal_revert_preview)
        else:
            raise ValueError(f"unsupported resource action: {name} {action}")


def _resource_action_help(name: str, action: str) -> dict[str, str]:
    if name == "journal" and action == "tail":
        return _surface_help("journal.list")
    if name == "journal" and action == "show":
        return _surface_help("journal.get")
    if name == "journal" and action == "revert-preview":
        return _surface_help("trace.revert_preview")
    return {}


def _common(parser: argparse.ArgumentParser, *, workspace_required: bool = True) -> None:
    parser.add_argument("--workspace", required=workspace_required)
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--quiet", action="store_true")
    parser.add_argument("--idempotency-key")
    parser.add_argument("--schedule-id")
    parser.add_argument("--actor", choices=("pi", "agent"), default="pi")


def _surface_help(action_id: str) -> dict[str, str]:
    summary = _surface_summary(action_id)
    return {"description": summary, "help": summary}


def _surface_summary(action_id: str) -> str:
    return str(SURFACE_ACTION[action_id]["summary"])


def _render_job_console() -> str:
    """U1 §3 cli-console: the CLI organized by the surface contract.

    One heading per SURFACE_JOBS entry, in order; one line per registered
    CLI command; rows without a CLI binding render as `<id> (<transports>)`
    and reserved rows as `<id> (reserved)` so the console discloses the
    whole contract, not just the CLI slice of it.
    """
    lines = ["Memoria console — surfaces by workspace job", ""]
    for job in SURFACE_JOBS:
        lines.append(f"{job}:")
        entries: list[tuple[str, str]] = []
        for action in SURFACE_ACTIONS:
            if action.get("job") != job:
                continue
            summary = str(action["summary"])
            cli = action.get("cli")
            commands: list[str] = []
            if isinstance(cli, dict):
                commands = [str(command) for command in cli.get("commands") or []]
            if commands:
                entries.extend((command, summary) for command in commands)
            else:
                transports = [t for t in ("http", "mcp") if isinstance(action.get(t), dict)]
                suffix = ", ".join(transports) if transports else "reserved"
                entries.append((f"{action['id']} ({suffix})", summary))
        if entries:
            width = max(len(left) for left, _ in entries)
            lines.extend(f"  {left.ljust(width)}  {summary}" for left, summary in entries)
        else:
            lines.append("  (no registered surfaces yet)")
        lines.append("")
    return "\n".join(lines).rstrip("\n") + "\n"


def _cmd_help(args: argparse.Namespace) -> int:
    sys.stdout.write(_render_job_console())
    return 0


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
    from memoria_vault.runtime import backup as runtime_backup

    runtime_backup.validate_workspace_write_targets(workspace, [".git"])
    _validate_workspace_git_metadata(workspace)
    runtime_backup.validate_workspace_write_targets(
        workspace,
        _repair_write_targets(
            workspace, include_obsidian=include_obsidian, include_agent_bundle=True
        ),
    )
    _initialize_workspace_files(
        workspace, include_obsidian=include_obsidian, include_agent_bundle=True
    )
    onboarding_steps.emit_onboarding_step(workspace, "init-done")
    payload: dict[str, Any] = {"ok": True, "workspace": str(workspace), "created": created}
    if args.onboard:
        payload["onboard"] = _run_onboarding_for_args(workspace, args)
    return _emit(payload, args)


def _cmd_onboard(args: argparse.Namespace) -> int:
    workspace = Path(args.workspace or ".").resolve()
    return _emit(_run_onboarding_for_args(workspace, args), args)


def _run_onboarding_for_args(workspace: Path, args: argparse.Namespace) -> dict[str, Any]:
    from memoria_vault.runtime import onboarding

    interactive = not (args.quiet or args.json)

    def say(line: str) -> None:
        if interactive:
            print(line)

    def ask(prompt: str) -> str:
        if not interactive:
            return ""
        try:
            return input(prompt)
        except (EOFError, RuntimeError, ValueError, OSError):
            # `ask` is not total: `run_onboarding` only guards its own call
            # sites against EOFError/RuntimeError (builtin `input()` raises
            # RuntimeError("input(): lost sys.stdin") when stdin is
            # detached). A closed stdin fd raises OSError and an in-process
            # `sys.stdin.close()` raises ValueError; neither is caught
            # there, so this real `input()`-based `ask` -- the first
            # production caller -- must swallow every unusable-stdin shape
            # itself. Otherwise a plain `memoria onboard` with no
            # `--json`/`--quiet` run under CI or `< /dev/null` degrades from
            # an honest "no consent obtained" outcome to an uncaught
            # traceback. Treat every such shape as run_onboarding already
            # treats EOFError: a declined prompt, never a crash.
            return ""

    payload = onboarding.run_onboarding(
        workspace,
        sys_platform=sys.platform,
        env=os.environ,
        home=Path.home(),
        ask=ask,
        say=say,
        # Thread the hardened, proxy-free/redirect-free opener explicitly
        # rather than relying on run_onboarding's own default staying
        # correct: BOOT-D.4 replaced a bare `urllib.request.urlopen`
        # default specifically because it honors `http_proxy`/`https_proxy`
        # even for a `127.0.0.1` target, so an unguarded default drift here
        # would silently send a loopback Zotero probe through an ambient
        # proxy. This CLI command is the production call site that fix
        # exists for.
        url_open=onboarding._open_zotero_probe,
    )
    # Spec §5 gap resolution 3: "onboard done" is a *completed* runway, and this
    # is the single choke point for both `memoria onboard` and `init --onboard`.
    if payload.get("completed"):
        onboarding_steps.emit_onboarding_step(workspace, "onboard-done")
    return payload


def _cmd_status(args: argparse.Namespace) -> int:
    return _emit(engine_api.read_status(_workspace(args)), args)


def _cmd_context(args: argparse.Namespace) -> int:
    return _emit(engine_api.read_context(_workspace(args)), args)


def _cmd_cockpit(args: argparse.Namespace) -> int:
    """U2 spec §1/§2: static text photograph, or the composed --json payload.

    The rendered screen is written verbatim -- no tty branching, no ANSI -- so
    `memoria cockpit | cat` is byte-identical to terminal output by
    construction.
    """
    if args.triage and args.project:
        return _fail(
            "the two screens never mix: pass --project (deep) or --triage, not both",
            json_output=bool(args.json),
        )
    payload = engine_api.read_cockpit(
        _workspace(args), project_path=args.project or "", triage=bool(args.triage)
    )
    if args.json:
        print(json.dumps(payload, ensure_ascii=False, sort_keys=True))
        return 0
    if payload.get("screen") == "triage":
        sys.stdout.write(engine_cockpit.render_triage(payload))
    else:
        sys.stdout.write(engine_cockpit.render_deep(payload))
    return 0


def _cmd_dashboard(args: argparse.Namespace) -> int:
    """I1 spec §4's engine-direct front, now through U2 T.3's `dashboard.read`.

    Still the assembler's payload whole rather than the view projection, so the
    CLI reads the same counts the HTTP view renders into text blocks — but via
    the row's engine binding, which is what lets the row promise a
    `response_version` and the floor sweep assert the envelope. Reaching for
    `assemble_dashboard` here again would put a second, unregistered route to
    the panels back in the CLI.
    """
    return _emit(engine_api.read_dashboard(_workspace(args)), args)


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


def _doctor_payload(
    payload: dict[str, Any], args: argparse.Namespace, workspace: Path
) -> dict[str, Any]:
    from memoria_vault.runtime.secrets import credential_report

    payload["credentials"] = credential_report(
        workspace,
        loaded_from_file=getattr(args, "_secrets_loaded_from_file", None),
    )
    if warning := getattr(args, "_secrets_warning", ""):
        payload["warning"] = warning
    return payload


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
        payload = {
            "ok": all(checks.values()),
            "workspace": str(workspace),
            "checks": checks,
            "search_engine": status["engine"],
            "search_manifest": status["manifest"],
            "search_document_count": status["document_count"],
            "repaired": repaired,
        }
        return _emit(_doctor_payload(payload, args, workspace), args)
    if args.live and args.check != "runner":
        return _fail("doctor --live is only valid with --check runner", json_output=args.json)
    if args.check == "runner":
        status = _runner_status(workspace, args.provider, live=args.live)
        checks.update(status["checks"])
        payload = {
            "ok": all(checks.values()),
            "workspace": str(workspace),
            "checks": checks,
            "provider": status["provider"],
            "base_url": status["base_url"],
            "model": status["model"],
            "error": status["error"],
            "repaired": repaired,
        }
        return _emit(_doctor_payload(payload, args, workspace), args)
    backup = _backup_report(workspace)
    payload = {
        "ok": all(checks.values()) and backup["ok"],
        "workspace": str(workspace),
        "checks": checks,
        "backup": backup,
        "repaired": repaired,
    }
    return _emit(_doctor_payload(payload, args, workspace), args)


def _cmd_doctor_bundle(args: argparse.Namespace) -> int:
    from memoria_vault.runtime.feedback import feedback_production_enabled

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
    payload = {
        "ok": all(doctor.values()) and backup["ok"],
        "workspace": str(workspace),
        "doctor": doctor,
        "backup": backup,
        "feedback": {"production_enabled": feedback_production_enabled(workspace)},
        "requests": requests,
        "journal_head": journal_head,
    }
    return _emit(_doctor_payload(payload, args, workspace), args)


def _cmd_doctor_self_test(args: argparse.Namespace) -> int:
    workspace = _workspace(args)
    checks = _doctor_checks(workspace)
    checks["operation_catalog"] = bool(engine_api.read_operations(workspace)["operations"])
    payload = {"ok": all(checks.values()), "workspace": str(workspace), "checks": checks}
    return _emit(_doctor_payload(payload, args, workspace), args)


def _cmd_ask(args: argparse.Namespace) -> int:
    payload: dict[str, Any] = {"query": args.question, "k": 5}
    if args.trace:
        payload["trace"] = True
    result = _enqueue_and_run(args, "answer-query", payload)
    if result.get("ok"):
        answer = result.get("result")
        onboarding_steps.emit_first_answer_if_seed_grounded(
            _workspace(args), answer if isinstance(answer, dict) else {}
        )
    return _emit_ask_result(result, args, print_trace=args.trace)


def _cmd_secrets_set(args: argparse.Namespace) -> int:
    from memoria_vault.runtime.secrets import validate_secret_name, write_secret

    validate_secret_name(args.name)
    if sys.stdin.isatty():
        import getpass

        value = getpass.getpass(f"{args.name}: ")
    else:
        value = sys.stdin.readline().rstrip("\n")
    path = write_secret(args.name, value)
    return _emit({"ok": True, "name": args.name, "path": str(path)}, args)


def _cmd_secrets_list(args: argparse.Namespace) -> int:
    from memoria_vault.runtime.secrets import credential_report, secrets_path

    workspace = Path(args.workspace).resolve() if args.workspace else None
    payload: dict[str, Any] = {
        "ok": True,
        "path": getattr(args, "_secrets_path", str(secrets_path())),
        "credentials": credential_report(
            workspace,
            loaded_from_file=getattr(args, "_secrets_loaded_from_file", None),
        ),
    }
    if warning := getattr(args, "_secrets_warning", ""):
        payload["warning"] = warning
    return _emit(payload, args)


def _cmd_explore(args: argparse.Namespace) -> int:
    result = engine_api.read_explore(
        _workspace(args),
        args.topic,
        versus=args.versus,
        project=args.project,
        depth=args.depth,
        trace=args.trace,
    )
    return _emit_explore_result(result, args, print_trace=args.trace)


def _emit_ask_result(
    result: dict[str, Any], args: argparse.Namespace, *, print_trace: bool = False
) -> int:
    raw = result.get("result")
    answer: dict[str, Any] = raw if isinstance(raw, dict) else {}
    text_front = bool(result.get("ok")) and not args.json and not args.quiet
    if text_front and not answer.get("sources") and answer.get("unknowns"):
        print(str(answer["unknowns"][0]))
        if print_trace:
            _print_ask_trace(answer)
        return 0
    code = _emit(result, args)
    if text_front and print_trace:
        _print_ask_trace(answer)
    return code


def _print_ask_trace(answer: dict[str, Any]) -> None:
    trace = answer.get("trace")
    if not isinstance(trace, dict):
        return
    for row in trace.get("pipeline_counts") or []:
        print(f"{row['stage']}: {row['count']}")
    print(f"rerank: {trace.get('rerank', 'off')}")


def _emit_explore_result(
    result: dict[str, Any], args: argparse.Namespace, *, print_trace: bool = False
) -> int:
    payload = result.get("explore")
    explore = payload if isinstance(payload, dict) else {}
    text_front = bool(result.get("ok")) and not args.json and not args.quiet
    if not text_front:
        return _emit(result, args)
    if "a" in explore and "b" in explore:
        sides = {
            side: value
            for side, value in explore.items()
            if side in {"a", "b"} and isinstance(value, dict)
        }
        nonempty = any(not side.get("honest_empty") for side in sides.values())
        code = _emit(result, args) if nonempty else 0
        for name in ("a", "b"):
            empty = str(sides.get(name, {}).get("honest_empty") or "")
            if empty:
                print(f"{name}: {empty}")
        if print_trace:
            traces = explore.get("trace")
            for name in ("a", "b"):
                _print_explore_trace(
                    traces.get(name) if isinstance(traces, dict) else None,
                    prefix=f"{name}: ",
                )
        return code
    empty = str(explore.get("honest_empty") or "")
    if empty:
        print(empty)
        if print_trace:
            _print_explore_trace(explore.get("trace"))
        return 0
    code = _emit(result, args)
    if print_trace:
        _print_explore_trace(explore.get("trace"))
    return code


def _print_explore_trace(trace: object, *, prefix: str = "") -> None:
    if not isinstance(trace, dict):
        return
    for row in trace.get("pipeline_counts") or []:
        if isinstance(row, dict):
            print(f"{prefix}{row['stage']}: {row['count']}")
    print(f"{prefix}rerank: {trace.get('rerank', 'off')}")


def _cmd_serve(args: argparse.Namespace) -> int:
    if args.stop:
        if args.watch:
            return _fail("serve accepts one transport at a time", json_output=args.json)
        return _cmd_serve_stop(args)
    if args.http or args.on_demand or args.ephemeral:
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


SERVE_PORT_DEFAULT = 8765
SERVE_PORT_WALK_END = 8785


def _serve_port_candidates(port: int) -> list[int]:
    """Return the conventional local-port walk or one explicit port."""
    if port == SERVE_PORT_DEFAULT:
        return list(range(SERVE_PORT_DEFAULT, SERVE_PORT_WALK_END + 1))
    return [port]


def _vault_id(workspace: Path) -> str:
    """Read the seeded vault ID when it is available."""
    try:
        data = json.loads((workspace / ".memoria/vault.json").read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return ""
    return str(data.get("vault_id") or "") if isinstance(data, dict) else ""


def _cmd_serve_http(args: argparse.Namespace) -> int:
    from memoria_vault.runtime import rendezvous
    from memoria_vault.runtime.http_transport import bind_http_server, start_idle_monitor

    if not math.isfinite(args.idle_exit) or args.idle_exit <= 0:
        return _fail("serve --idle-exit must be positive", json_output=args.json)
    if args.host not in {"127.0.0.1", "localhost"}:
        return _fail("serve --http only binds loopback hosts", json_output=args.json)
    workspace = _workspace(args)
    env_token = os.environ.get("MEMORIA_HTTP_TOKEN")
    token = env_token or secrets.token_urlsafe(32)
    boot_id = str(uuid.uuid4())
    candidates = [0] if args.ephemeral else _serve_port_candidates(args.port)
    state_dir = rendezvous.vault_state_dir(workspace)

    with rendezvous.serve_lock(state_dir) as acquired:
        if not acquired:
            return _fail(
                "serve could not acquire the exclusive admission lock", json_output=args.json
            )

        live = rendezvous.live_coordinates(state_dir)
        if live is not None:
            return _fail(
                "a memoria server is already running for this vault", json_output=args.json
            )

        server: Any | None = None
        runtime_published = False
        try:
            try:
                server = bind_http_server(
                    workspace,
                    host=args.host,
                    candidate_ports=candidates,
                    token=token,
                    read_scope=args.read_scope,
                    boot_id=boot_id,
                )
            except ValueError as exc:
                return _fail(str(exc), json_output=args.json)
            except OSError as exc:
                return _fail(f"serve --http could not bind a port: {exc}", json_output=args.json)

            port = int(server.server_address[1])
            try:
                rendezvous.write_runtime(
                    state_dir,
                    {
                        "vault_path": str(workspace),
                        "vault_id": _vault_id(workspace),
                        "port": port,
                        "pid": os.getpid(),
                        "boot_id": boot_id,
                        "token": token,
                        "engine_version": __version__,
                        "started_at": now_iso(),
                    },
                )
                runtime_published = True
            except (OSError, ValueError) as exc:
                return _fail(
                    f"serve --http could not publish runtime: {exc}", json_output=args.json
                )

            payload = {
                "ok": True,
                "url": f"http://{args.host}:{port}",
                "port": port,
                "boot_id": boot_id,
                "token": None if env_token else token,
                "token_source": "env" if env_token else "generated",
            }
            if args.once:
                try:
                    if runtime_published:
                        rendezvous.clear_runtime(state_dir)
                finally:
                    try:
                        server.server_close()
                    finally:
                        server = None
                return _emit(payload, args)
            if args.on_demand:
                start_idle_monitor(server, args.idle_exit)
            _emit(payload, args)
            try:
                server.serve_forever()
                return 0
            except KeyboardInterrupt:
                return 0
        finally:
            if server is not None:
                try:
                    if runtime_published:
                        rendezvous.clear_runtime(state_dir)
                finally:
                    server.server_close()


def _cmd_serve_stop(args: argparse.Namespace) -> int:
    from memoria_vault.runtime import rendezvous

    workspace = _workspace(args)
    state_dir = rendezvous.vault_state_dir(workspace)
    record = rendezvous.read_runtime(state_dir)
    if record is None:
        return _fail("no memoria server is running for this vault", json_output=args.json)
    if not rendezvous.pid_alive(int(record["pid"])):
        rendezvous.clear_runtime(state_dir)
        return _fail("no memoria server is running for this vault", json_output=args.json)
    port = int(record["port"])
    boot_id = str(record["boot_id"])
    if rendezvous.probe_boot_id(port) != boot_id:
        return _fail("no memoria server is running for this vault", json_output=args.json)
    response = rendezvous.post_shutdown(port, str(record["token"]), boot_id)
    if not (
        isinstance(response, dict)
        and response.get("ok") is True
        and response.get("stopping") is True
    ):
        return _fail("no memoria server is running for this vault", json_output=args.json)
    return _emit({"ok": True, "stopped": True, "port": int(record["port"])}, args)


def _handshake_fail(args: argparse.Namespace, message: str) -> int:
    if args.json:
        print(message, file=sys.stderr, flush=True)
    return _fail(message, json_output=args.json)


def _cmd_handshake(args: argparse.Namespace) -> int:
    from memoria_vault.runtime import rendezvous

    try:
        vault = Path(args.vault).expanduser().resolve()
        if not vault.is_dir():
            return _handshake_fail(args, f"vault path is not a directory: {vault}")
        coordinates = rendezvous.handshake(vault, spawn=args.spawn)
    except Exception as exc:  # noqa: BLE001 -- preserve the handshake JSON/stderr contract.
        return _handshake_fail(args, str(exc))
    return _emit({"ok": True, **coordinates}, args)


def _cmd_mcp(args: argparse.Namespace) -> int:
    from memoria_vault.runtime.mcp_transport import run_mcp_server

    if not args.read_scope:
        return _fail("mcp requires at least one --read-scope", json_output=False)
    run_mcp_server(_workspace(args), read_scope=args.read_scope, agent_identity=args.actor)
    return 0


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
    result = engine_api.write_new_concept(
        _workspace(args),
        "project",
        args.name,
        body=body,
        tags=[],
        extra={"description": args.description, "outcome_frame": {}, "paper_plan": {}},
        idempotency_key=args.idempotency_key,
        schedule_id=args.schedule_id,
        actor=args.actor,
    )
    if result.get("ok"):
        # Spec §5 gap resolution 1: once per vault, so project-framed - init-done is a
        # deterministic delta rather than a per-project stream.
        onboarding_steps.emit_onboarding_step_once(_workspace(args), "project-framed")
    return _emit(result, args)


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


def _cmd_seed_install(args: argparse.Namespace) -> int:
    output = _enqueue_and_run(args, "seed-install", {"install": True})
    result = output.get("result") if isinstance(output.get("result"), dict) else {}
    if not args.json and not args.quiet:
        for notice in result.get("notices") or []:
            print(f"notice: {notice}", file=sys.stderr)
        for entry in result.get("failed") or []:
            print(f"failed row {entry.get('id')}: {entry.get('error')}", file=sys.stderr)
    return _emit(output, args)


def _cmd_work_import(args: argparse.Namespace) -> int:
    from memoria_vault.runtime.bulk_import import split_bibtex_entries, split_csl_entries

    path = Path(args.file)
    text = path.read_text(encoding="utf-8")
    if args.format == "bibtex":
        entries = split_bibtex_entries(text)
    else:
        try:
            csl_data = json.loads(text)
        except ValueError:
            entries = [text]
        else:
            if isinstance(csl_data, list) and all(isinstance(item, dict) for item in csl_data):
                entries = split_csl_entries(text)
            else:
                entries = [text]
    return _emit(_bulk_work_import(args, entries), args)


def _bulk_work_import(args: argparse.Namespace, entries: list[str]) -> dict[str, Any]:
    from memoria_vault.runtime.bulk_import import (
        build_entry_payload,
        detect_identifier_collisions,
        entry_capture_request,
        entry_fetch,
        entry_item_type,
        entry_ref,
        entry_type_mapped,
        is_doi_collision_error,
        parse_entry_fields,
    )

    workspace = _workspace(args)
    run_id = uuid.uuid4().hex
    run_started = time.monotonic()
    admitted: list[str] = []
    skipped: list[str] = []
    failed: list[dict[str, str]] = []
    enrichment_jobs: list[str] = []
    judgments: list[dict[str, str]] = []
    for index, entry_text in enumerate(entries, start=1):
        ref = entry_ref(args.format, entry_text, index)
        try:
            payload = build_entry_payload(args.format, entry_text)
            fields = parse_entry_fields(args.format, entry_text)
            payload["item_type"] = entry_item_type(fields)
            mapped = entry_type_mapped(fields)
            work_id = str(payload["work_id"])
            if (existing := state.catalog_source(workspace, work_id)) is not None:
                skipped.append(str(existing["work_id"]))
                continue
            operation_id, request = entry_capture_request(
                payload, entry_fetch(fields, payload["identifiers"]), mapped=mapped
            )
            output = engine_api.run_operation(
                workspace,
                operation_id,
                request,
                idempotency_key=f"import-{run_id}-{work_id}",
                schedule_id=args.schedule_id,
                actor=args.actor,
                command=operation_id,
            )
        except ValueError as exc:
            failed.append({"ref": ref, "error": str(exc)})
            judgments.append(_import_judgment("failed", ref, ref, str(exc)))
            continue
        result = output.get("result") if isinstance(output.get("result"), dict) else {}
        if output["ok"]:
            catalog_id = str(result.get("work_id") or work_id)
            admitted.append(catalog_id)
            if not mapped:
                judgments.append(
                    _import_judgment(
                        "unmapped",
                        ref,
                        catalog_id,
                        f"entry type {str(fields.get('type') or 'unknown')!r} is outside the"
                        " shipped vocabulary; admitted as article",
                    )
                )
            judgments.extend(
                _import_judgment(
                    "duplicate",
                    ref,
                    catalog_id,
                    f"{collision['field']} matches admitted work {collision['other_work_id']}",
                )
                for collision in detect_identifier_collisions(
                    workspace, catalog_id, payload["identifiers"]
                )
            )
            if args.enrich and (enrichment := _queue_import_enrichment(args, payload, output)):
                enrichment_jobs.append(str(enrichment["job_id"]))
        else:
            error = str(result.get("error") or result.get("status") or "capture failed")
            failed.append({"ref": ref, "error": error})
            group = "duplicate" if is_doi_collision_error(error) else "failed"
            judgments.append(_import_judgment(group, ref, ref, error))
    index_refresh_s = 0.0
    if admitted:
        from memoria_vault.runtime.search_index import rebuild_checked_search_index_explicit

        refresh_started = time.monotonic()
        rebuild_checked_search_index_explicit(workspace, actor=args.actor, machine="memoria-cli")
        index_refresh_s = time.monotonic() - refresh_started
    duplicates_flagged = sum(row["group"] == "duplicate" for row in judgments)
    worklist = _finalize_import_run(
        workspace,
        run_id=run_id,
        entry_format=args.format,
        entries_total=len(entries),
        judgments=judgments,
        admitted=admitted,
        skipped=skipped,
        failed=failed,
        duplicates_flagged=duplicates_flagged,
        duration_s=time.monotonic() - run_started,
        index_refresh_s=index_refresh_s,
    )
    return {
        "ok": bool(admitted or skipped),
        "run_id": run_id,
        "format": args.format,
        "entries_total": len(entries),
        "admitted": admitted,
        "skipped": skipped,
        "failed": failed,
        "duplicates_flagged": duplicates_flagged,
        "enrichment_jobs": enrichment_jobs,
        "index_refresh_s": index_refresh_s,
        "worklist": worklist,
    }


_IMPORT_JUDGMENT_TITLES = {
    "duplicate": "Duplicate identifier",
    "failed": "Entry failed",
    "unmapped": "Unmapped entry type",
}


def _import_judgment(group: str, ref: str, item_ref: str, reason: str) -> dict[str, str]:
    """One bulk-admission judgment row in the worklist section's vocabulary."""
    return {
        "title": f"{_IMPORT_JUDGMENT_TITLES[group]}: {ref}",
        "item_ref": item_ref,
        "group": group,
        "reason": reason,
    }


def _finalize_import_run(
    workspace: Path,
    *,
    run_id: str,
    entry_format: str,
    entries_total: int,
    judgments: list[dict[str, str]],
    admitted: list[str],
    skipped: list[str],
    failed: list[dict[str, str]],
    duplicates_flagged: int,
    duration_s: float,
    index_refresh_s: float,
) -> str:
    """Write the run's two artifacts, once each, after the index-refresh boundary.

    The driver is the finalizer (#1517): no durable run state crosses commands, so
    a retry mints a new ``run_id`` and describes itself honestly. A zero-judgment
    run yields no worklist and no card, never a fabricated empty artifact.
    """
    from memoria_vault.runtime.subsystems.lib.worklists import emit_import_worklist
    from memoria_vault.runtime.telemetry import record_telemetry_event

    emitted = emit_import_worklist(
        workspace,
        run_id=run_id,
        rows=judgments,
        entries_total=entries_total,
        admitted=len(admitted),
    )
    record_telemetry_event(
        workspace,
        "import-run.v1",
        {
            "run_id": run_id,
            "format": entry_format,
            "entries_total": entries_total,
            "admitted": len(admitted),
            "skipped": len(skipped),
            "failed": len(failed),
            "duplicates_flagged": duplicates_flagged,
            "duration_s": duration_s,
            "index_refresh_s": index_refresh_s,
        },
    )
    return str(emitted["worklist"]) if emitted else ""


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
    return _emit_ask_result(
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
        if frontmatter.get("type") not in {"digest", "note"}:
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

    _require_pi_actor(args, "resolve-evidence-review")
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
        warrant=args.warrant,
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
            "allow_unready": args.allow_unready,
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


def _cmd_mv(args: argparse.Namespace) -> int:
    return _emit(
        _enqueue_and_run(
            args,
            "move-concept",
            {
                "old_path": args.old_path,
                "new_path": args.new_path,
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
    path = engine_api._resolve_concept_path(workspace, args.target)
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
    _require_pi_actor(args, "request control")
    result = run_request(_workspace(args), args.request_id, machine="memoria-cli")
    return _emit({"ok": result.get("status") == "done", "result": result}, args)


def _require_pi_actor(args: argparse.Namespace, action: str) -> None:
    if args.actor != "pi":
        raise ValueError(f"{action} requires PI actor authority")


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
        # Authorship is inherited from the source, not reset by PI authority: the
        # successor payload is `{**request["args"], ...}`, so a machine-authored
        # body survives `request amend`/`answer` verbatim unless the flag travels
        # with it (#1596). Tradeoff: a PI who genuinely rewrites `content` via
        # `--update` still gets a neutralized body. That is the safe direction —
        # an explicit authorship-claim affordance can be added later, but a
        # default of "trusted" cannot be un-shipped.
        machine_authored=bool(envelope.get("machine_authored", False)),
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


def _apply_request_mutation(
    workspace: Path,
    args: argparse.Namespace,
    *,
    command: str,
    event_name: str,
    build_payload: Callable[[dict[str, Any]], dict[str, Any]],
    event_payload_extra: dict[str, Any],
) -> int:
    """Shared tail for `_cmd_request_answer`/`_cmd_request_amend`: lock, load the
    request, mint a successor, idempotently journal the event, then reload and
    emit. Callers differ only in the successor payload and the journal event.
    """
    from memoria_vault.runtime.trusted_writer import append_explicit_journal_event

    with _workspace_lock(workspace):
        row = _request_control_row(workspace, args)
        request = state.request_detail(row)
        source_request_id = str(request["request_id"])
        successor = _request_successor(
            workspace,
            request,
            payload=build_payload(request),
            idempotency_key=args.idempotency_key,
            command=command,
        )
        if not _request_lifecycle_event_exists(workspace, event_name, str(successor["job_id"])):
            append_explicit_journal_event(
                workspace,
                {
                    "event": event_name,
                    "request_id": source_request_id,
                    "successor_request_id": successor["job_id"],
                    **event_payload_extra,
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


def _cmd_request_answer(args: argparse.Namespace) -> int:
    _require_pi_actor(args, "request control")
    workspace = _workspace(args)
    answers = _key_values(args.answers)

    def build_payload(request: dict[str, Any]) -> dict[str, Any]:
        current_answers = request["args"].get("answers", {})
        if not isinstance(current_answers, dict):
            raise ValueError("request answers must be a mapping")
        return {**request["args"], "answers": {**current_answers, **answers}}

    return _apply_request_mutation(
        workspace,
        args,
        command="answer",
        event_name="request_answered",
        build_payload=build_payload,
        event_payload_extra={"answers": sorted(answers)},
    )


def _cmd_request_amend(args: argparse.Namespace) -> int:
    _require_pi_actor(args, "request control")
    workspace = _workspace(args)
    updates = _key_values(args.updates)
    scoped = _scope_bearing_request_fields(updates)
    if scoped:
        raise ValueError(f"request amend cannot change scope-bearing field: {', '.join(scoped)}")

    return _apply_request_mutation(
        workspace,
        args,
        command="amend",
        event_name="request_amended",
        build_payload=lambda request: {**request["args"], **updates},
        event_payload_extra={"updates": sorted(updates)},
    )


def _cmd_request_cancel(args: argparse.Namespace) -> int:
    from memoria_vault.runtime.trusted_writer import append_explicit_journal_event

    _require_pi_actor(args, "request control")
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

    _require_pi_actor(args, "request control")
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
        engine_api.read_attention(
            _workspace(args),
            status=args.status or "",
            kind=args.kind or "",
            order_by=args.order_by or "",
        ),
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


# Presentation-only, and never renamed: the raw queue's own spellings
# (`routing_type`, `disposition`) are the CLI's too (V2 plan, 2026-07-29
# raw-queue amendment §3). `items` and analysis are deliberately absent —
# a list row is claim + item count + routing reason (spec §3).
_REVIEW_SUMMARY_FIELDS = (
    "evidence_id",
    "claim_text",
    "item_count",
    "routing_type",
    "reviewable",
    "cure",
    "age_days",
    "disposition",
    "warrant",
)


def _review_summary_row(row: dict[str, Any]) -> dict[str, Any]:
    """Project one raw queue row into its list summary.

    Both arms of the queue's discriminated union keep their `kind`, so an SRD
    gap stays a distinct read-only entry rather than an evidence row missing
    its fields.
    """
    if row["kind"] == "srd-gap":
        card = row["card_block"]
        return {"kind": "srd-gap", "title": str(card["title"]), "ref": str(card["ref"])}
    summary = {key: row[key] for key in _REVIEW_SUMMARY_FIELDS if key in row}
    summary["kind"] = "evidence-set"
    summary["project"] = row["project_path"]
    summary["routing_reason"] = evidence_review.routing_reason(row, row["item_previews"])
    return summary


def _truncate(text: str, width: int = 60) -> str:
    text = " ".join(str(text).split())
    return text if len(text) <= width else text[: width - 1] + "…"


def _review_summary_line(row: dict[str, Any]) -> str:
    if row["kind"] == "srd-gap":
        return f"{row['ref']}  {'srd-gap':<9}  {_truncate(row['title'])}  — read-only"
    if not row["reviewable"]:
        marker = f"  [read-only: {row['cure']}]"
    elif row["disposition"] != "open":
        marker = f"  [{row['disposition']}]"
    else:
        marker = ""
    return (
        f"{row['evidence_id']}  {row['routing_type'] or '-':<9}  "
        f"{row['item_count']} item(s)  {_truncate(row['claim_text'])}"
        f"  — {row['routing_reason']}{marker}"
    )


def _cmd_review_list(args: argparse.Namespace) -> int:
    queue = engine_api.evidence_review_queue(
        _workspace(args),
        routing_type=args.type,
        project=args.project,
        min_age_days=args.min_age_days,
        batch=args.batch,
    )
    rows = [_review_summary_row(row) for row in queue["rows"]]
    payload = {
        "ok": True,
        "rows": rows,
        "total": queue["total"],
        "batch": args.batch,
        "facet_totals": queue["facet_totals"],
    }
    if args.json or args.quiet:
        return _emit(payload, args)
    for row in rows:
        print(_review_summary_line(row))
    print(f"{len(rows)} of {queue['total']} row(s) shown (batch {args.batch})")
    return 0


# A show that did not record its required client event is not a successful show,
# and the CLI never invents a reason the operation did not give.
_VIEW_OPENED_UNRECORDED = "evidence detail was read but view.opened was not recorded"


def _review_queue_row(workspace: Path, evidence_id: str) -> dict[str, Any] | None:
    """The one raw queue row an evidence id names, or `None`.

    `batch=0` is the engine-direct unbounded lookup. Only the evidence arm of
    the discriminated union answers an evidence id: an SRD gap shares the queue
    and carries no `evidence_id` at all.
    """
    queue = engine_api.evidence_review_queue(workspace, batch=0)
    return next(
        (
            row
            for row in queue["rows"]
            if row["kind"] == "evidence-set" and row["evidence_id"] == evidence_id
        ),
        None,
    )


def _review_detail_row(row: dict[str, Any], *, show_analysis: bool) -> dict[str, Any]:
    """The list summary plus resolved grounds previews (spec §3, evidence-first).

    Analysis is folded by default, and absent entirely when the shared helper is
    empty — a permanently blocked row never shows analysis it cannot act on.
    """
    detail = _review_summary_row(row)
    detail["items"] = row["item_previews"]
    if show_analysis:
        analysis = evidence_review.analysis_fields(row, row["item_previews"])
        if analysis:
            detail["analysis"] = analysis
    return detail


def _emit_review_view_opened(
    args: argparse.Namespace, workspace: Path, evidence_id: str
) -> dict[str, Any]:
    """Record one `view.opened` client event through the empirical-event door.

    `empirical-event-record` is the only seam that writes client telemetry, and
    since I1 T.3 it lands in `telemetry_events`, never the journal.
    """
    event = {
        "event_id": str(uuid.uuid4()),
        "event_type": "view.opened",
        "timestamp": now_iso(),
        "session_id": uuid.uuid4().hex,
        "surface": "cli",
        "workflow": "evidence-review",
        "item_type": "evidence-set",
        "item_id": evidence_id,
    }
    result = engine_api.run_operation(
        workspace,
        "empirical-event-record",
        event,
        idempotency_key=f"empirical-event:{event['event_id']}",
        actor=args.actor,
        command="review-show",
    )
    telemetry: dict[str, Any] = {"ok": bool(result["ok"]), "event_id": event["event_id"]}
    if not telemetry["ok"]:
        telemetry["result"] = result["result"]  # the failed operation's own account
    return telemetry


def _review_item_line(preview: dict[str, Any]) -> str:
    resolves = "resolves" if preview["resolves"] else "does not resolve"
    line = f"  - {preview['ref']}  [{resolves}]"
    excerpt = str(preview.get("excerpt") or "")
    return f"{line}  {excerpt}" if excerpt else line


def _print_review_detail(row: dict[str, Any], *, show_analysis: bool) -> None:
    print(f"Claim ({row['evidence_id']}, {row['routing_type'] or '-'}):")
    # Verbatim, unlike the list's one-line collapse: a soft-wrapped block keeps
    # its own lines, indented into the claim body.
    for line in str(row["claim_text"]).splitlines():
        print(f"  {line}")
    print(f"Grounds items ({row['item_count']}):")
    for preview in row["items"]:
        print(_review_item_line(preview))
    print(f"Why routed: {row['routing_reason']}")
    print(f"Disposition: {row['disposition']}")
    if "cure" in row:
        print(f"Read-only: {row['cure']}")
    if "warrant" in row:
        print(f"Warrant: {row['warrant']}")
    analysis = row.get("analysis")
    if not show_analysis:
        print("Machine analysis folded — pass --show-analysis to expand.")
    elif analysis:
        print("Machine analysis:")
        # The helper's own order is the reading order — arguments, what tipped
        # it, then certainty — and re-sorting here would only scramble it.
        for key, value in analysis.items():
            print(f"  {key}: {value}")
    else:
        print("Machine analysis: none recorded for this row.")


def _cmd_review_show(args: argparse.Namespace) -> int:
    workspace = _workspace(args)
    row = _review_queue_row(workspace, args.evidence_id)
    if row is None:
        return _fail(
            f"evidence id is not in the review queue: {args.evidence_id}",
            json_output=args.json,
        )
    shown = _review_detail_row(row, show_analysis=args.show_analysis)
    telemetry = _emit_review_view_opened(args, workspace, args.evidence_id)
    payload: dict[str, Any] = {"ok": telemetry["ok"], "row": shown, "telemetry": telemetry}
    if not telemetry["ok"]:
        payload["error"] = (
            str((telemetry["result"] or {}).get("error") or "") or _VIEW_OPENED_UNRECORDED
        )
        return _emit(payload, args)
    if args.json or args.quiet:
        return _emit(payload, args)
    _print_review_detail(shown, show_analysis=args.show_analysis)
    return 0


# The decision itself is journaled and stays journaled; only the client-side
# record of it is missing, and the CLI says so rather than reporting success.
_DISPOSITION_UNRECORDED = "disposition succeeded but client telemetry was not recorded"


def _emit_review_disposition_recorded(
    args: argparse.Namespace, workspace: Path, dwell: float | None
) -> dict[str, Any]:
    """Record one `disposition.recorded` client event for this decision.

    `duration_s` rides only a dwell the journal can support: the schema refuses
    a nonpositive duration, and a sub-second gap is noise, never a real look.
    """
    event: dict[str, Any] = {
        "event_id": str(uuid.uuid4()),
        "event_type": "disposition.recorded",
        "timestamp": now_iso(),
        "session_id": uuid.uuid4().hex,
        "surface": "cli",
        "workflow": "evidence-review",
        "decision": args.review_decision,
        "reason_code": args.reason_code,
        "item_type": "evidence-set",
        "item_id": args.evidence_id,
    }
    if dwell is not None and dwell >= 1.0:
        event["duration_s"] = round(dwell, 1)
    result = engine_api.run_operation(
        workspace,
        "empirical-event-record",
        event,
        idempotency_key=f"empirical-event:{event['event_id']}",
        actor=args.actor,
        command=f"review-{args.review_decision}",
    )
    telemetry: dict[str, Any] = {"ok": bool(result["ok"]), "event_id": event["event_id"]}
    if "duration_s" in event:
        telemetry["duration_s"] = event["duration_s"]
    if not telemetry["ok"]:
        telemetry["result"] = result["result"]  # the failed operation's own account
    return telemetry


def _cmd_review_action(args: argparse.Namespace) -> int:
    from memoria_vault.runtime.knowledge import resolve_evidence_review, review_dwell_seconds

    _require_pi_actor(args, f"review-{args.review_decision}")
    workspace = _workspace(args)
    dwell = review_dwell_seconds(workspace, args.evidence_id)
    event = resolve_evidence_review(
        workspace,
        args.evidence_id,
        decision=args.review_decision,
        reason=args.reason,
        warrant=getattr(args, "warrant", ""),
        actor=args.actor,
        machine="memoria-cli",
    )
    telemetry = _emit_review_disposition_recorded(args, workspace, dwell)
    payload: dict[str, Any] = {
        "ok": telemetry["ok"],
        "evidence_id": args.evidence_id,
        "decision": args.review_decision,
        "event": event,
        "telemetry": telemetry,
    }
    if not telemetry["ok"]:
        payload["error"] = (
            str((telemetry["result"] or {}).get("error") or "") or _DISPOSITION_UNRECORDED
        )
        return _emit(payload, args)
    if args.json or args.quiet:
        return _emit(payload, args)
    # `_emit`'s generic success line says only "completed"; the cockpit front
    # names the decision it just recorded, in the list's own row grammar.
    line = f"{args.review_decision} {args.evidence_id}"
    print(f"{line}  — {args.reason}" if args.reason else line)
    return 0


def _cmd_review_stats(args: argparse.Namespace) -> int:
    from memoria_vault.runtime.knowledge import review_telemetry_summary

    summary = review_telemetry_summary(_workspace(args))
    if args.json or args.quiet:
        return _emit({"ok": True, "telemetry": summary}, args)
    # One line per metric, derived from the summary itself, so a metric added
    # to it reaches the human front without a second list to keep in step.
    for key, value in summary.items():
        if isinstance(value, dict):
            value = "  ".join(f"{name} {count}" for name, count in value.items())
        print(f"{key}: {value}")
    return 0


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
            str(item["frontmatter"]["operation_id"]) for item in iter_capability_manifests()
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

    _require_pi_actor(args, "workspace recover")
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

    _require_pi_actor(args, "workspace backup")
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

    _require_pi_actor(args, "workspace restore")
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


def _scoped_operation_args(base_args: argparse.Namespace, operation_id: str) -> argparse.Namespace:
    operation_args = argparse.Namespace(**vars(base_args))
    base_key = str(getattr(operation_args, "idempotency_key", "") or "")
    if base_key:
        operation_args.idempotency_key = f"{base_key}:{operation_id}"
    return operation_args


def _cmd_workspace_scan(args: argparse.Namespace) -> int:
    payload = _workspace_scan_payload(args)
    _print_scan_findings(payload, args)
    return _emit(payload, args)


def _print_scan_findings(payload: dict[str, Any], args: argparse.Namespace) -> None:
    if args.json or args.quiet:
        return
    result = payload.get("result")
    findings = result.get("findings") if isinstance(result, dict) else None
    for finding in findings or []:
        kind = str(finding.get("kind") or "finding")
        subject = str(finding.get("subject_id") or "")
        key = str(finding.get("key") or "")
        suffix = f" (key: {key})" if key else ""
        print(f"finding: {kind} {subject}{suffix}")


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
            _scoped_operation_args(scan_args, "trace-integrity-scan"),
            "trace-integrity-scan",
            {
                "paths": projection_paths,
                "reason": "workspace-scan-generated-projection",
            },
        )
        if regeneration_paths:
            regeneration = _enqueue_and_run(
                _scoped_operation_args(scan_args, "regenerate-tracked-projections"),
                "regenerate-tracked-projections",
                {"paths": regeneration_paths},
            )
    observed = _enqueue_and_run(scan_args, "observe-pi-edits", {})
    inbox_compaction = _compact_resolved_inbox(workspace)
    needs_check_paths = list(observed["result"].get("paths") or [])
    payload = {
        "ok": (
            observed["ok"]
            and (quarantine is None or quarantine["ok"])
            and (regeneration is None or regeneration["ok"])
            and not inbox_compaction.get("error")
        ),
        "job": observed["job"],
        "result": observed["result"],
        "needs_check_count": len(needs_check_paths),
        "needs_check_paths": needs_check_paths,
        "journal": journal,
        "journal_reconciled": journal_reconciled,
        "inbox_compaction": inbox_compaction,
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


def _compact_resolved_inbox(workspace: Path) -> dict[str, Any]:
    """Compact the resolved attention tail, reporting a failure instead of raising it.

    `workspace scan` is the file-watch tick as much as a command the PI runs, and
    its caller reads one JSON payload from stdout: an exception escaping the hygiene
    pass would end the watch loop and print no payload at all. A vault with no git
    repo, a read-only tree, or a busy journal is therefore a reported `error`, which
    the payload's `ok` carries -- a scan never reports success over a step that
    failed.

    `OSError` and `RuntimeError` both have producer tests at this seam. `sqlite3.Error`
    has none, and none that could be written without a stub: a database this scan
    cannot write is a database `verify_journal_chain` already refused several steps
    earlier, so reaching this arm means racing a barrier thread into the gap between
    the observe step and this call -- the same stubbing this seam's other arms were
    held back from. It stays because that gap is real on a live vault with a
    non-Memoria writer (the flock does not exclude one), and because
    `policy/engine.py` guards the same lib call the same way -- defence in depth,
    named as such rather than left looking covered.
    """
    # Lazy, like the journal and projection imports above: the scan path is the only
    # caller and `memoria --help` should not pay for the trusted writer.
    from memoria_vault.runtime.subsystems.lib import lifecycle

    try:
        return lifecycle.compact_resolved_cards(workspace)
    except (OSError, RuntimeError, sqlite3.Error) as exc:
        return {
            "adopted": [],
            "archived": [],
            "digests": [],
            "released": [],
            "commit": "",
            "error": str(exc),
        }


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

    results = [
        _enqueue_and_run(
            _scoped_operation_args(check_args, operation_id),
            operation_id,
            {"shadow": bool(args.shadow)},
        )
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
    from memoria_vault.runtime.steering import (
        effective_steering_provenance,
        steering_overrides,
    )

    workspace = _workspace(args)
    if not (workspace / "steering.md").is_file():
        return _fail("steering.md not found", json_output=args.json)
    tokens = effective_steering_provenance(workspace)
    _watch, mute = steering_overrides(workspace)
    payload = {"ok": True, "path": "steering.md", "tokens": tokens, "muted": sorted(mute)}
    if not args.json and not args.quiet:
        if tokens:
            width = max(len(str(row["token"])) for row in tokens)
            for row in tokens:
                print(f"{row['token']!s:<{width}}  {', '.join(row['sources'])}")
        else:
            print("no effective steering tokens - frame a project or add Watch for bullets")
        if payload["muted"]:
            print(f"muted: {', '.join(payload['muted'])}")
        return 0
    return _emit(payload, args)


def _cmd_steering_edit(args: argparse.Namespace) -> int:
    from memoria_vault.runtime.trusted_writer import (
        append_explicit_journal_event,
        commit_explicit_writer_changes,
    )
    from memoria_vault.runtime.vaultio import write_text_durable

    _require_pi_actor(args, "steering edit")
    workspace = _workspace(args)
    body = args.body if args.body is not None else Path(args.file).read_text(encoding="utf-8")
    path = workspace / "steering.md"
    write_text_durable(path, body if body.endswith("\n") else f"{body}\n")
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


def _cmd_journal_revert_preview(args: argparse.Namespace) -> int:
    try:
        return _emit(engine_api.read_revert_preview(_workspace(args), args.event_id), args)
    except FileNotFoundError as exc:
        return _fail(str(exc), json_output=args.json)


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


def _workspace_plan(workspace: Path) -> list[str]:
    from memoria_vault.runtime.subsystems.lib import schema

    return list(schema.load_folders()["skeleton"])


def _active_seed_trees(*, include_obsidian: bool) -> tuple[tuple[str, str], ...]:
    if include_obsidian:
        return SEED_TREES
    return tuple(pair for pair in SEED_TREES if pair[1] != ".obsidian")


def _active_seed_files(*, include_obsidian: bool) -> tuple[tuple[str, str], ...]:
    if include_obsidian:
        return SEED_FILES
    return tuple(pair for pair in SEED_FILES if not pair[1].endswith(".base"))


def _bundle_names(*, include_obsidian: bool) -> list[str]:
    return ["agent", "obsidian"] if include_obsidian else ["agent"]


def _init_dry_run_report(
    workspace: Path, planned_dirs: list[str], *, include_obsidian: bool = True
) -> dict[str, Any]:
    from memoria_vault.runtime import bundles
    from memoria_vault.runtime.projections import TRACKED_PROJECTION_PATHS

    seed_trees = [target for _, target in _active_seed_trees(include_obsidian=include_obsidian)]
    seed_files = [target for _, target in _active_seed_files(include_obsidian=include_obsidian)]
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
            "bundle_files": bundles.bundle_files(_bundle_names(include_obsidian=include_obsidian)),
            "version": __version__,
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
            "vault_manifest": bundles.MANIFEST_REL,
        },
    }


def _seed_workspace(workspace: Path, *, overwrite: bool, include_obsidian: bool = True) -> None:
    for source_rel, target_rel in _active_seed_trees(include_obsidian=include_obsidian):
        _copy_seed_tree(
            source_rel, workspace / target_rel, overwrite=overwrite, target_rel=target_rel
        )
    for source_rel, target_rel in _active_seed_files(include_obsidian=include_obsidian):
        _copy_seed_file(
            source_rel, workspace / target_rel, overwrite=overwrite, target_rel=target_rel
        )


def _repair_workspace(workspace: Path) -> list[str]:
    repaired = _repair_seed_write_targets(workspace)
    _initialize_workspace_files(workspace, overwrite=True, commit_created_repository=False)
    return repaired


def _repair_write_targets(
    workspace: Path,
    *,
    include_obsidian: bool = True,
    include_agent_bundle: bool = False,
) -> list[str]:
    from memoria_vault.runtime import bundles
    from memoria_vault.runtime.projections import _tracked_projection_paths

    targets = set(_workspace_plan(workspace))
    for source_rel, target_rel in _active_seed_trees(include_obsidian=include_obsidian):
        targets.update(_seed_tree_write_targets(source_rel, target_rel))
    targets.update(
        target for _source, target in _active_seed_files(include_obsidian=include_obsidian)
    )
    if include_agent_bundle:
        targets.update(
            bundles.bundle_write_targets(_bundle_names(include_obsidian=include_obsidian))
        )
    targets.update(
        {
            state.DB_REL,
            f"{state.DB_REL}-wal",
            f"{state.DB_REL}-shm",
            f"{state.DB_REL}-journal",
            state.JOURNAL_HEAD_REL,
            ".memoria/overrides.jsonl",
            "system/manifest.jsonl",
        }
    )
    targets.update(_tracked_projection_paths(workspace))
    targets.update(_existing_tree_targets(workspace, ".git"))
    return sorted(targets)


def _repair_seed_write_targets(workspace: Path) -> list[str]:
    targets: list[str] = []
    for source_rel, target_rel in SEED_TREES:
        targets.extend(_seed_tree_file_targets(source_rel, target_rel))
    targets.extend(target for _source, target in SEED_FILES)
    return sorted(
        target
        for target in targets
        if target not in VIEW_PREFERENCE_PATHS or not (workspace / target).exists()
    )


def _seed_tree_child_is_cache(name: str) -> bool:
    return name == "__pycache__" or name.endswith(".pyc")


def _seed_tree_file_targets(source_rel: str, target_rel: str) -> list[str]:
    source = _seed_resource(source_rel)
    if source.is_file():
        return [target_rel]
    if not source.is_dir():
        return []
    targets: list[str] = []
    for child in source.iterdir():
        if _seed_tree_child_is_cache(child.name):
            continue
        child_target = (Path(target_rel) / child.name).as_posix()
        targets.extend(_seed_tree_file_targets(f"{source_rel}/{child.name}", child_target))
    return targets


def _seed_tree_write_targets(source_rel: str, target_rel: str) -> list[str]:
    targets = [target_rel]
    source = _seed_resource(source_rel)
    if not source.is_dir():
        return targets
    for child in source.iterdir():
        if _seed_tree_child_is_cache(child.name):
            continue
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


def _validate_workspace_git_metadata(workspace: Path) -> None:
    git_path = workspace / ".git"
    if os.path.lexists(git_path) and not git_path.is_dir():
        raise ValueError("workspace Git metadata must be a directory")
    if os.path.lexists(git_path / "commondir"):
        raise ValueError("workspace Git common-directory indirection is not supported")


@contextmanager
def _doctor_maintenance(workspace: Path, *, repair: bool = False):
    from memoria_vault.runtime import backup as runtime_backup

    def preflight() -> None:
        runtime_backup.validate_maintenance_preconditions(workspace)
        if repair:
            runtime_backup.validate_workspace_write_targets(workspace, [".git"])
            _validate_workspace_git_metadata(workspace)
            runtime_backup.validate_workspace_write_targets(
                workspace, _repair_write_targets(workspace)
            )

    preflight()
    with _workspace_lock(workspace):
        preflight()
        yield


def _initialize_workspace_files(
    workspace: Path,
    *,
    overwrite: bool = False,
    include_obsidian: bool = True,
    include_agent_bundle: bool = False,
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
    if include_agent_bundle:
        from memoria_vault.runtime import bundles

        # `init` alone passes this: repair must never reach the bundle writer.
        # Before _ensure_git so the created repository's first commit tracks
        # .memoria/vault.json; otherwise a fresh vault starts dirty.
        bundles.seed_bundles(
            workspace, bundle_names=_bundle_names(include_obsidian=include_obsidian)
        )
    _ensure_git(workspace, commit_created_repository=commit_created_repository)


def _copy_seed_tree(source_rel: str, target: Path, *, overwrite: bool, target_rel: str) -> None:
    source = _seed_resource(source_rel)
    if not source.is_dir():
        return
    if target.exists() and any(target.iterdir()) and not overwrite:
        # Standing debt (flagged 2026-08-01, not BOOT-C.6's to fix): a
        # non-empty tree is skipped whole on the init path, so a file missing
        # from inside it is not restored — dropping this branch would restore
        # per-file instead, and no test covers the difference. BOOT-C.6 moved
        # the bundle paths out of the seed rosters, leaving `.obsidian` as the
        # only tree here that carries any.
        return
    target.mkdir(parents=True, exist_ok=True)
    for child in source.iterdir():
        if _seed_tree_child_is_cache(child.name):
            continue
        child_target = target / child.name
        child_rel = f"{target_rel}/{child.name}"
        if child.is_dir():
            _copy_seed_tree(
                f"{source_rel}/{child.name}",
                child_target,
                overwrite=overwrite,
                target_rel=child_rel,
            )
        elif _seed_write_allowed(child_rel, child_target, overwrite=overwrite):
            child_target.parent.mkdir(parents=True, exist_ok=True)
            child_target.write_bytes(child.read_bytes())


def _copy_seed_file(source_rel: str, target: Path, *, overwrite: bool, target_rel: str) -> None:
    source = _seed_resource(source_rel)
    if source.is_file() and _seed_write_allowed(target_rel, target, overwrite=overwrite):
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(source.read_bytes())


def _seed_write_allowed(target_rel: str, target: Path, *, overwrite: bool) -> bool:
    from memoria_vault.runtime import bundles

    if not overwrite and target_rel in bundles.BUNDLE_PATHS:
        # One writer on the init path: `runtime.bundles` writes every bundle
        # path write-if-absent and records it in `.memoria/vault.json`. Repair
        # still restores `.obsidian/plugins/*` as the runtime seed it is.
        return False
    if not target.exists():
        return True
    return overwrite and target_rel not in VIEW_PREFERENCE_PATHS


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
    from memoria_vault.runtime.vaultio import write_text_durable

    _require_pi_actor(args, f"vocabulary {mode}")
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
    write_text_durable(path, text)
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
        TokenCeilingReached,
        _load_pydantic_ai_openai,
        _pydantic_ai_chat,
        _resolve_runner_api_key,
        load_runner_provider_config,
    )

    provider_name = (provider or "local").strip() or "local"
    providers = load_runner_provider_config(workspace)
    if provider_name not in providers:
        raise ValueError(f"unknown runner provider: {provider_name}")
    provider_spec = providers[provider_name]
    base_url = str(provider_spec["url"])
    key_env = provider_spec.get("key_env")
    model_name = os.environ.get("MEMORIA_MODEL") or os.environ.get("OPENAI_MODEL") or "doctor"
    runner = {
        "mode": "live" if live else "test",
        "runner": "pydantic-ai",
        "provider": provider_name,
        "model": model_name,
        "base_url": base_url,
        "key_env": key_env,
        "params": {"temperature": 0},
    }
    checks = {
        "runner_dependency": False,
        "runner_base_url": bool(base_url),
        "runner_agent_constructed": False,
    }
    if live:
        checks["runner_live_dispatch"] = False
    error = ""
    try:
        api_key = _resolve_runner_api_key(runner)
    except (RuntimeError, ValueError) as exc:
        # The resolver's only failures are value-free, actionable credential messages.
        error = str(exc)
    else:
        try:
            Agent, OpenAIChatModel, OpenAIProvider = _load_pydantic_ai_openai()
            checks["runner_dependency"] = True
            provider_kwargs = {"base_url": base_url, "api_key": api_key}
            model = OpenAIChatModel(model_name, provider=OpenAIProvider(**provider_kwargs))
            Agent(model)
            checks["runner_agent_constructed"] = True
            if live:
                _pydantic_ai_chat(
                    {
                        "operation_id": "doctor-runner-live",
                        "allowed_network": [base_url],
                    },
                    runner,
                    "Reply with a short confirmation that the Memoria runner is reachable.",
                )
                checks["runner_live_dispatch"] = True
        except TokenCeilingReached as exc:
            # Refused before any dispatch, from our own constants and integers:
            # the diagnostic is actionable and reflects no adapter state.
            error = str(exc)
        except Exception:  # noqa: BLE001 -- adapter failures must not reflect credentials.
            error = "pydantic-ai model request failed"
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


if __name__ == "__main__":
    raise SystemExit(main())
