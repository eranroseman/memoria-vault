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


def note_text(title: str, *, status: str = "checked") -> str:
    return (
        "---\n"
        f"type: note\ncheck_status: {status}\ntitle: {title}\n"
        "status: accepted\n---\n"
        f"# {title}\n\nBody.\n"
    )


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
