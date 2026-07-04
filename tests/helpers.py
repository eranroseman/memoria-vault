"""Shared helpers for repo-side tests."""

from __future__ import annotations

import shutil
import subprocess
from pathlib import Path
from types import SimpleNamespace
from typing import Any

from memoria_vault.runtime import state
from memoria_vault.runtime.policy.audit import sha256_file

ROOT = Path(__file__).resolve().parents[1]


def copy_memoria_dirs(vault: Path, *names: str) -> None:
    for name in names:
        shutil.copytree(
            ROOT / "vault-template/.memoria" / name,
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
