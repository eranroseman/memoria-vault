"""Verify-on-commit hook behavior."""

import os
import shutil
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
HOOK = ROOT / "vault-template/.githooks/post-commit"
GIT_HOOK_ENV = ("GIT_DIR", "GIT_WORK_TREE", "GIT_INDEX_FILE", "GIT_PREFIX")


def _clean_env(extra: dict[str, str] | None = None) -> dict[str, str]:
    env = os.environ.copy()
    for key in GIT_HOOK_ENV:
        env.pop(key, None)
    if extra:
        env |= extra
    return env


def _git(repo: Path, *args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["git", *args],
        cwd=repo,
        check=True,
        text=True,
        capture_output=True,
        env=_clean_env(),
    )


def _commit(repo: Path, message: str, env: dict[str, str]) -> None:
    subprocess.run(
        ["git", "add", "."],
        cwd=repo,
        check=True,
        text=True,
        capture_output=True,
        env=env,
    )
    subprocess.run(
        ["git", "commit", "-m", message],
        cwd=repo,
        check=True,
        text=True,
        capture_output=True,
        env=env,
    )


def _repo_with_hook(tmp_path: Path) -> tuple[Path, Path, dict[str, str]]:
    repo = tmp_path / "vault"
    bin_dir = tmp_path / "bin"
    log = tmp_path / "hermes.log"
    repo.mkdir()
    bin_dir.mkdir()
    _git(repo, "init")
    _git(repo, "config", "user.email", "memoria@example.invalid")
    _git(repo, "config", "user.name", "Memoria Test")
    hooks = repo / ".git/hooks"
    hooks.mkdir(exist_ok=True)
    shutil.copy2(HOOK, hooks / "post-commit")
    (hooks / "post-commit").chmod(0o755)
    hermes = bin_dir / "hermes"
    hermes.write_text(
        '#!/usr/bin/env bash\nprintf \'%s\\n\' "$*" >> "$HERMES_LOG"\n',
        encoding="utf-8",
    )
    hermes.chmod(0o755)
    env = _clean_env({"HERMES_LOG": str(log)})
    env["PATH"] = f"{bin_dir}{os.pathsep}{env['PATH']}"
    return repo, log, env


def test_hook_script_ships_executable():
    assert HOOK.is_file()
    assert HOOK.stat().st_mode & 0o111, "post-commit hook must be executable"


def test_project_draft_commit_creates_verify_card(tmp_path):
    repo, log, env = _repo_with_hook(tmp_path)
    draft = repo / "projects/paper/section.md"
    draft.parent.mkdir(parents=True)
    draft.write_text("# Section\n\nA cited claim.\n", encoding="utf-8")

    _commit(repo, "draft", env)

    output = log.read_text(encoding="utf-8")
    commit = _git(repo, "rev-parse", "HEAD").stdout.strip()
    assert "kanban create" in output
    assert "--lane verify" in output
    assert "--assignee memoria-peer-reviewer" in output
    assert "--skill verify-check-citation" in output
    assert "Verify draft: projects/paper/section.md" in output
    assert f"verify-on-commit-{commit}-projects-paper-section.md" in output


def test_non_project_commit_does_not_create_verify_card(tmp_path):
    repo, log, env = _repo_with_hook(tmp_path)
    note = repo / "notes/claims/c.md"
    note.parent.mkdir(parents=True)
    note.write_text("# Claim\n", encoding="utf-8")

    _commit(repo, "claim", env)

    assert not log.exists()
