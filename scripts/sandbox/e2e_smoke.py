#!/usr/bin/env python3
"""Offline end-to-end smoke gate and importable assertions."""

from __future__ import annotations

import os
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[2]
for path in (ROOT / "src", ROOT):
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))

STAGE_LABELS = {
    "vault-assembly-1": "1. vault-assembly: scaffold + populate (installer-equivalent, from vault-template/)",
    "vault-assembly-2": "2. vault-assembly: git hook wiring",
    "vault-assembly-3": "3. vault-assembly: fresh-vault integrity",
    "commit-gate": "4. commit-gate: malformed note blocks, valid note passes",
    "offline-ingest-1": "5. offline-ingest: checked source + references projection",
    "offline-ingest-2": "6. offline-ingest: argument graph projection",
    "workflow-replay": "7. workflow-replay: package-gate test-env harness",
    "final-integrity": "8. final-integrity: lint over the worked vault",
}
STAGE_ORDER = tuple(STAGE_LABELS)


def print_stage_label(name: str) -> None:
    print(STAGE_LABELS[name])


def assert_vault_skeleton(root: Path, vault: Path) -> None:
    folders = yaml.safe_load((root / "vault-template/.memoria/schemas/folders.yaml").read_text())
    for folder in folders["skeleton"]:
        (vault / folder).mkdir(parents=True, exist_ok=True)
    missing = [folder for folder in folders["skeleton"] if not (vault / folder).is_dir()]
    assert not missing, f"skeleton missing {missing}"
    print(f"   skeleton ensured ({len(folders['skeleton'])} dirs); tree matches folders.yaml")


def assert_no_obsidian_bundle(vault: Path) -> None:
    assert not (vault / ".obsidian").exists(), "standalone vault shipped .obsidian payload"
    assert not (vault / "system/scripts").exists(), "standalone vault shipped QuickAdd scripts"
    print("   git repo, hooks, and standalone no-Obsidian baseline asserted")


def assert_executable(path: Path, label: str) -> None:
    assert path.exists() and path.stat().st_mode & 0o111, (
        f"{label} is missing or not executable: {path}"
    )


def add_repo_paths(root: Path) -> None:
    for path in (root, root / "vault-template/.memoria"):
        if str(path) not in sys.path:
            sys.path.insert(0, str(path))


def assert_offline_ingest(root: Path, vault: Path) -> None:
    add_repo_paths(root)

    from memoria_vault.runtime import state
    from memoria_vault.runtime.capture import capture_bibtex_source, write_references_bib

    bib = (
        "@article{x2024demo,\n"
        "  title = {Demo Work},\n"
        "  author = {Doe, Jane},\n"
        "  year = {2024},\n"
        "  journal = {Demo Journal},\n"
        "}\n"
    )
    result = capture_bibtex_source(
        vault,
        bib,
        source_id="demo-work",
        content_text="Demo Work package-gate source.",
        machine="e2e",
    )
    source = state.catalog_source(vault, result["source_id"])
    assert result["source_path"] == "catalog/sources/demo-work"
    assert source is not None
    assert source["check_status"] == "checked"
    assert source["source_id"] == "demo-work"
    assert not (vault / "catalog/sources/demo-work/source.md").exists()
    assert (vault / result["content_path"]).is_file()
    assert (vault / result["raw_path"]).is_file()
    write_references_bib(vault)
    assert "@article{x2024demo" in (vault / "references.bib").read_text(encoding="utf-8")
    print("   checked source + references projection asserted")


def assert_typed_graph(root: Path, vault: Path) -> None:
    add_repo_paths(root)

    from memoria_vault.runtime import state
    from memoria_vault.runtime.knowledge import write_project_argument_canvas
    from memoria_vault.runtime.policy.audit import sha256_file

    project = vault / "knowledge/projects/package-gate.md"
    thesis = vault / "knowledge/notes/package-thesis.md"
    support = vault / "knowledge/notes/package-support.md"
    _write_note(
        project,
        "type: project\nid: 01KBN6V6KX0000000000000001\nlinks: {}\ntitle: Package gate\n"
        "description: Package gate project.\nthesis: knowledge/notes/package-thesis.md\n",
        "Package gate project.",
    )
    _write_note(
        thesis,
        "type: note\nid: 01KBN6V6KX0000000000000002\nlinks: {}\ntitle: Package thesis\n",
        "Package thesis.",
    )
    _write_note(
        support,
        "type: note\nid: 01KBN6V6KX0000000000000003\ntitle: Package support\n"
        "links:\n  supports:\n    - knowledge/notes/package-thesis.md\n",
        "Package support.",
    )
    for path, concept_type in ((project, "project"), (thesis, "note"), (support, "note")):
        rel = path.relative_to(vault).as_posix()
        state.record_observed_file_edit(
            vault,
            output_id=rel,
            concept_type=concept_type,
            output_sha256=sha256_file(path),
        )
        state.set_concept_verdict(vault, rel, "checked")
    result = write_project_argument_canvas(vault, "package-gate")
    assert result["node_count"] == 2
    assert result["edge_count"] == 1
    assert (vault / result["canvas_path"]).is_file()
    print(f"   argument canvas: {result['node_count']} nodes / {result['edge_count']} edge")


def _write_note(path: Path, frontmatter: str, body: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(f"---\n{frontmatter}---\n{body}\n", encoding="utf-8")


def assert_workflow_replay_artifacts(vault: Path) -> None:
    for rel in [
        "knowledge/projects/harness.md",
        "knowledge/notes/harness-thesis.md",
        "knowledge/notes/harness-support.md",
        "knowledge/notes/harness-refutation.md",
        "knowledge/projects/harness/argument.canvas",
    ]:
        assert (vault / rel).is_file(), f"workflow replay artifact missing: {rel}"
    forbidden = vault / "knowledge/notes/blocked-by-harness.md"
    assert not forbidden.exists(), "workflow replay left forbidden note behind"
    print("   workflow replay artifacts and forbidden-file absence asserted")


def assert_final_verdict(verdict: str) -> None:
    assert re.search(r"PASS|REVIEW", verdict), f"worked vault verdict: {verdict}"


def _fail(message: str) -> None:
    print(f"e2e-smoke: FAIL - {message}", file=sys.stderr)
    raise SystemExit(1)


def _stage(name: str) -> None:
    print(f"== {STAGE_LABELS[name]} ==")


def _env(root: Path) -> dict[str, str]:
    env = os.environ.copy()
    env["PYTHONPATH"] = (
        f"{root / 'src'}{os.pathsep}{env['PYTHONPATH']}"
        if env.get("PYTHONPATH")
        else str(root / "src")
    )
    return env


def _run(
    command: list[str],
    *,
    env: dict[str, str] | None = None,
    stdout: int | None = None,
    stderr: int | None = None,
) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        command,
        cwd=ROOT,
        env=env,
        text=True,
        stdout=stdout,
        stderr=stderr,
        check=False,
    )


def _run_or_fail(command: list[str], message: str, *, env: dict[str, str] | None = None) -> None:
    result = _run(command, env=env, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    if result.returncode != 0:
        _fail(f"{message}\n{result.stdout}")


def _git(
    vault: Path, *args: str, env: dict[str, str] | None = None
) -> subprocess.CompletedProcess[str]:
    return _run(
        ["git", "-C", str(vault), *args],
        env=env,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
    )


def _git_or_fail(vault: Path, *args: str, message: str, env: dict[str, str] | None = None) -> None:
    result = _git(vault, *args, env=env)
    if result.returncode != 0:
        _fail(f"{message}\n{result.stdout}")


def _python() -> str:
    return os.environ.get("PYTHON", sys.executable)


def _detector_verdict(vault: Path, env: dict[str, str]) -> str:
    result = _run(
        [
            _python(),
            "-m",
            "memoria_vault.runtime.subsystems.integrity.linter.detectors",
            "--vault",
            str(vault),
        ],
        env=env,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
    )
    if result.returncode != 0:
        _fail(f"detectors failed\n{result.stdout}")
    return (result.stdout or "").strip().splitlines()[-1]


def _copy_vault_template(root: Path, vault: Path) -> None:
    shutil.copytree(
        root / "vault-template",
        vault,
        dirs_exist_ok=True,
        ignore=shutil.ignore_patterns(".git"),
    )


def _vault_assembly(root: Path, vault: Path, env: dict[str, str]) -> None:
    _stage("vault-assembly-1")
    if shutil.which("git") is None:
        _fail("git is required for vault-assembly and commit-gate checks")
    _copy_vault_template(root, vault)
    assert_vault_skeleton(root, vault)

    _stage("vault-assembly-2")
    _git_or_fail(vault, "init", "-q", message="git init failed")
    _git_or_fail(vault, "config", "user.email", "e2e@example.invalid", message="git config failed")
    _git_or_fail(vault, "config", "user.name", "Memoria E2E Smoke", message="git config failed")
    _git_or_fail(vault, "rev-parse", "--is-inside-work-tree", message="not a git repository")
    hook = vault / ".git/hooks/pre-commit"
    hook.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(vault / ".githooks/pre-commit", hook)
    hook.chmod(0o755)
    assert_executable(hook, "pre-commit hook")
    assert_no_obsidian_bundle(vault)

    _stage("vault-assembly-3")
    if "PASS" not in _detector_verdict(vault, env):
        _fail("detectors not clean on the fresh vault")


def _commit_gate(vault: Path, env: dict[str, str]) -> None:
    _stage("commit-gate")
    _git_or_fail(
        vault, "rev-parse", "--is-inside-work-tree", message="commit-gate needs git", env=env
    )
    assert_executable(vault / ".git/hooks/pre-commit", "pre-commit hook")
    _git_or_fail(vault, "add", "-A", message="baseline add failed", env=env)
    _git_or_fail(
        vault,
        "-c",
        "user.email=e2e@ci",
        "-c",
        "user.name=e2e",
        "commit",
        "-qm",
        "init",
        message="baseline commit blocked",
        env=env,
    )
    bad = vault / "knowledge/notes/bad.md"
    bad.write_text('---\ntype: note\ntitle: "Bad"\n---\nx\n', encoding="utf-8")
    _git_or_fail(vault, "add", "knowledge/notes/bad.md", message="bad note add failed", env=env)
    result = _git(
        vault,
        "-c",
        "user.email=e2e@ci",
        "-c",
        "user.name=e2e",
        "commit",
        "-qm",
        "bad",
        env=env,
    )
    if result.returncode == 0:
        _fail("the gate let a malformed note through")
    print("   malformed note blocked at commit")
    _git_or_fail(
        vault, "reset", "-q", "HEAD", "knowledge/notes/bad.md", message="reset failed", env=env
    )
    bad.unlink()
    good = vault / "knowledge/notes/good.md"
    good.write_text(
        "---\ntype: note\nid: 01ARZ3NDEKTSV4RRFFQ69G5FAV\ntags: []\nlinks: {}\n"
        'title: "Good"\n---\nBody.\n',
        encoding="utf-8",
    )
    _git_or_fail(vault, "add", "knowledge/notes/good.md", message="good note add failed", env=env)
    _git_or_fail(
        vault,
        "-c",
        "user.email=e2e@ci",
        "-c",
        "user.name=e2e",
        "commit",
        "-qm",
        "good",
        message="valid note blocked",
        env=env,
    )
    print("   valid note passes")


def _offline_ingest(root: Path, vault: Path) -> None:
    _stage("offline-ingest-1")
    assert_offline_ingest(root, vault)
    _stage("offline-ingest-2")
    assert_typed_graph(root, vault)


def _workflow_replay(root: Path, vault: Path, env: dict[str, str]) -> None:
    _stage("workflow-replay")
    _run_or_fail(
        [
            _python(),
            str(root / "scripts/sandbox/test_env_harness.py"),
            "replay",
            "--root",
            str(root),
            "--vault",
            str(vault),
        ],
        "test-env harness replay failed",
        env=env,
    )
    assert_workflow_replay_artifacts(vault)
    print("   cassette replay reached the model-free package-gate path")


def _final_integrity(vault: Path, env: dict[str, str]) -> None:
    _stage("final-integrity")
    verdict = _detector_verdict(vault, env)
    print(f"   {verdict}")
    assert_final_verdict(verdict)


def run_smoke(root: Path = ROOT) -> None:
    root = root.resolve()
    env = _env(root)
    vault = Path(
        tempfile.mkdtemp(prefix="memoria-e2e-", dir=os.environ.get("TMPDIR", tempfile.gettempdir()))
    )
    try:
        _vault_assembly(root, vault, env)
        _commit_gate(vault, env)
        _offline_ingest(root, vault)
        _workflow_replay(root, vault, env)
        _final_integrity(vault, env)
    finally:
        shutil.rmtree(vault, ignore_errors=True)
    print("e2e-smoke: all gates green")


def main() -> int:
    run_smoke()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
