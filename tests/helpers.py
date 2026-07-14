"""Shared helpers for repo-side tests."""

from __future__ import annotations

import shutil
import subprocess
import uuid
from pathlib import Path
from types import SimpleNamespace
from typing import Any

from memoria_vault.runtime import state
from memoria_vault.runtime.policy.audit import sha256_file
from memoria_vault.runtime.trusted_writer import OperationContext
from memoria_vault.runtime.vaultio import read_frontmatter

ROOT = Path(__file__).resolve().parents[1]
WORKSPACE_SEED = ROOT / "src/memoria_vault/product/workspace_seed"


def operation_context(
    vault: Path,
    *,
    actor: str = "operation",
    operation_id: str = "test-operation",
    machine: str = "test-machine",
    run_id: str = "test-run",
) -> OperationContext:
    """Persist a real request envelope and return its matching test context."""
    request_id = f"test-{uuid.uuid4().hex}"
    envelope = state.request_envelope(
        request_id=request_id,
        operation_id=operation_id,
        actor=actor,
        args={"run_id": run_id},
        provenance={"surface": "pytest"},
    )
    job = {
        "job_id": request_id,
        "kind": "operation",
        "operation_id": operation_id,
        "status": "running",
        "bound_context": {
            "actor": actor,
            "run_id": run_id,
            "request_id": request_id,
            "operation_id": operation_id,
            "machine": machine,
        },
    }
    saved = state.save_request(
        vault,
        envelope,
        job,
    )
    saved["status"] = "running"
    state.set_request_running(vault, request_id, saved)
    return OperationContext(actor, run_id, request_id, operation_id, machine)


def _assert_request_columns(columns: set[str]) -> None:
    assert {
        "input_refs_json",
        "output_intents_json",
        "primary_target",
        "precondition_hashes_json",
    } <= columns
    assert {"trigger_type", "target_path", "target_hash"}.isdisjoint(columns)


def call_with_context(function: Any, vault: Path, *args: Any, **kwargs: Any) -> Any:
    """Call a context-required request seam from a direct-call unit test."""
    actor = str(kwargs.pop("actor", "operation"))
    machine = str(kwargs.pop("machine", "test-machine") or "test-machine")
    run_id = str(kwargs.pop("run_id", "test-run") or "test-run")
    context = operation_context(
        vault,
        actor=actor,
        operation_id=function.__name__.replace("_", "-"),
        machine=machine,
        run_id=run_id,
    )
    return function(vault, *args, context=context, **kwargs)


def capture_bibtex_source_checked(
    vault: Path,
    bibtex: str,
    *,
    context: OperationContext,
    content_text: str | None = None,
    work_id: str | None = None,
    description: str | None = None,
) -> dict[str, Any]:
    """Seed one checked BibTeX source directly, bypassing the worker queue.

    The worker's own capture-bibtex-source dispatch always leaves
    check_status unchecked by design (new sources route through human
    review before promotion -- see AGENTS.md's catalog trust model), so
    fixtures that need an already-checked row call the payload builder and
    stage_capture_payload directly instead of going through the queue.
    """
    from memoria_vault.runtime.capture import bibtex_capture_payload, stage_capture_payload

    payload = bibtex_capture_payload(
        bibtex,
        content_text=content_text,
        work_id=work_id,
        description=description,
    )
    return stage_capture_payload(
        vault,
        payload,
        context=context,
        workflow="capture_bibtex_source",
        check_status="checked",
    )


def capture_url_source_checked(
    vault: Path,
    url: str,
    *,
    context: OperationContext,
    title: str | None = None,
    description: str | None = None,
    timeout: float = 10.0,
) -> dict[str, Any]:
    """Seed one checked URL snapshot directly, bypassing the worker queue.

    Mirrors capture_bibtex_source_checked's rationale, for the URL capture
    path: stage_url_source only ever writes unchecked rows, so this reaches
    the same shared `_store_url_source` core that capture.py's own
    stage_url_source uses, just with check_status="checked".
    """
    from memoria_vault.runtime.capture import _store_url_source

    return _store_url_source(
        vault,
        url,
        context=context,
        title=title,
        description=description,
        timeout=timeout,
        check_status="checked",
    )


def capture_pdf_source_checked(
    vault: Path,
    work_id: str,
    title: str,
    description: str,
    raw_bytes: bytes,
    *,
    context: OperationContext,
    raw_filename: str = "source.pdf",
    resource: str = "",
    item_type: str = "article",
    identifiers: dict[str, Any] | None = None,
    csl_json: dict[str, Any] | None = None,
    provider_coverage: str = "partial",
    citekey: str = "",
) -> dict[str, Any]:
    """Seed one checked PDF source directly, bypassing the worker queue.

    Mirrors capture_bibtex_source_checked's rationale, for the PDF capture
    path: stage_pdf_source only ever writes unchecked rows, so this reaches
    the same shared `_store_pdf_source` core that capture.py's own
    stage_pdf_source uses, just with check_status="checked".
    """
    from memoria_vault.runtime.capture import _store_pdf_source

    return _store_pdf_source(
        vault,
        work_id,
        title,
        description,
        raw_bytes,
        context=context,
        raw_filename=raw_filename,
        resource=resource,
        item_type=item_type,
        identifiers=identifiers,
        csl_json=csl_json,
        provider_coverage=provider_coverage,
        citekey=citekey,
        check_status="checked",
    )


def init_cli_workspace(tmp_path: Path, capsys: Any) -> Path:
    from memoria_vault.cli import main

    workspace = tmp_path / "workspace"
    assert main(["init", "--workspace", str(workspace), "--yes", "--json"]) == 0
    capsys.readouterr()
    return workspace


def copy_memoria_dirs(vault: Path, *names: str) -> None:
    for name in names:
        shutil.copytree(
            WORKSPACE_SEED / ".memoria" / name,
            vault / ".memoria" / name,
        )


def git(workspace: Path, *args: str) -> str:
    proc = subprocess.run(
        ["git", *args],
        cwd=workspace,
        check=False,
        text=True,
        capture_output=True,
    )
    if proc.returncode:
        raise AssertionError(proc.stderr or proc.stdout)
    return proc.stdout.strip()


def init_git(workspace: Path, email: str, name: str) -> None:
    git(workspace, "init", "-q")
    git(workspace, "config", "user.email", email)
    git(workspace, "config", "user.name", name)


def worker_workspace(
    tmp_path: Path,
    *,
    email: str = "worker@example.invalid",
    name: str = "Alpha Worker",
    message: str = "seed worker workspace",
) -> Path:
    """Seed a tmp_path with .memoria schemas/config and an initial git commit."""
    copy_memoria_dirs(tmp_path, "schemas", "config")
    init_git(tmp_path, email, name)
    git(tmp_path, "add", ".memoria/schemas", ".memoria/config")
    git(tmp_path, "commit", "-m", message)
    return tmp_path


def mark_file_status(
    workspace: Path,
    rel: str,
    concept_type: str = "note",
    status: str = "checked",
) -> None:
    state.record_observed_file_edit(
        workspace,
        output_id=rel,
        concept_type=concept_type,
        output_sha256=sha256_file(workspace / rel),
    )
    state.set_concept_verdict(workspace, rel, status)


def sync_file_verdicts(vault: Path) -> None:
    """Mark every checked/rejected concept file under vault with its recorded verdict."""
    for root in (
        "catalog",
        "knowledge",
        "notes",
        "hubs",
        "projects",
        "digests",
        "fulltext",
    ):
        base = vault / root
        if not base.exists():
            continue
        for path in base.rglob("*.md"):
            fm = read_frontmatter(path)
            status = fm.get("check_status")
            if status not in state.CHECK_STATUSES:
                continue
            if fm.get("type") == "source":
                continue
            rel = path.relative_to(vault).as_posix()
            mark_file_status(vault, rel, str(fm.get("type") or "note"), str(status))


def write_checked_concept(
    workspace: Path,
    rel: str,
    frontmatter: str,
    concept_type: str = "note",
    *,
    body: str = "Body.",
) -> None:
    path = workspace / rel
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(f"---\n{frontmatter}---\n{body}\n", encoding="utf-8")
    mark_file_status(workspace, rel, concept_type)


def write_checked_note(workspace: Path, rel: str, title: str) -> None:
    write_checked_concept(
        workspace,
        rel,
        f"type: note\ntitle: {title}\ntags: []\nlinks: {{}}\n",
    )


def _vault_root(path: Path) -> Path:
    for parent in path.parents:
        if parent.name in {
            "notes",
            "hubs",
            "projects",
            "digests",
            "fulltext",
            "capabilities",
        }:
            return parent.parent
    return path.parent


def _md(path: Path, frontmatter: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(f"---\n{frontmatter}---\nBody.\n", encoding="utf-8")
    fm = read_frontmatter(path)
    status = fm.get("check_status")
    if status in state.CHECK_STATUSES:
        vault = _vault_root(path)
        rel = path.relative_to(vault).as_posix()
        state.record_observed_file_edit(
            vault,
            output_id=rel,
            concept_type=str(fm.get("type") or "note"),
            output_sha256=sha256_file(path),
        )
        state.set_concept_verdict(vault, rel, str(status))


def note_text(title: str, *, status: str = "checked") -> str:
    return (
        "---\n"
        f"type: note\ncheck_status: {status}\ntitle: {title}\n"
        "status: accepted\n---\n"
        f"# {title}\n\nBody.\n"
    )


def work_text(title: str, body: str) -> str:
    return (
        f"---\ntype: digest\ntitle: {title}\ntags: []\nlinks: {{}}\nwork_id: {title}\n---\n{body}\n"
    )


def write_note(vault: Path, name: str, status: str, body: str) -> Path:
    path = vault / "notes" / f"{name}.md"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        f"---\ntype: note\ntitle: {name}\ntags: []\nlinks: {{}}\n---\n{body}\n",
        encoding="utf-8",
    )
    mark_file_status(vault, path.relative_to(vault).as_posix(), "note", status)
    return path


def patch_pydantic_ai(
    monkeypatch: Any,
    *,
    output: str = "",
    seen: dict[str, Any] | None = None,
) -> dict[str, Any]:
    seen = seen if seen is not None else {}

    class FakeProvider:
        def __init__(self, **kwargs: Any) -> None:
            seen["provider_kwargs"] = kwargs

    class FakeModel:
        def __init__(self, model_name: str, *, provider: object) -> None:
            seen["model_name"] = model_name
            seen["provider"] = provider

    class FakeAgent:
        def __init__(self, model: object) -> None:
            seen["model"] = model
            seen.setdefault("models", []).append(model)

        def run_sync(self, prompt: str, *, model_settings: dict[str, Any]) -> SimpleNamespace:
            seen["prompt"] = prompt
            seen["model_settings"] = model_settings
            return SimpleNamespace(output=output)

    monkeypatch.setattr(
        "memoria_vault.runtime.operations._load_pydantic_ai_openai",
        lambda: (FakeAgent, FakeModel, FakeProvider),
    )
    return seen
