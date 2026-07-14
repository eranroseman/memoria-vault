"""Generated workspace projection helpers."""

from __future__ import annotations

import json
import subprocess
from pathlib import Path
from typing import Any

from memoria_vault.runtime import state
from memoria_vault.runtime.policy.paths import normalize_path
from memoria_vault.runtime.trusted_writer import (
    OperationContext,
    append_explicit_journal_event,
    append_journal_event,
    commit_explicit_writer_changes,
    commit_writer_changes,
    validate_operation_context,
)

BUNDLE_ROOTS = ("notes", "hubs", "projects", "digests", "fulltexts")
INDEX_PATHS = ("index.md",)
TRACKED_PROJECTION_PATHS = (
    *INDEX_PATHS,
    "bibliography.bib",
)
TRACKED_PROJECTION_GLOBS = ("projects/*/argument.canvas",)


def render_workspace_index(vault: Path, index_path: str) -> str:
    """Render one generated OKF-style index.md projection."""
    rel = normalize_path(index_path)
    if rel != "index.md":
        raise ValueError(f"unsupported index projection: {index_path}")
    return _workspace_index()


def render_tracked_projection(vault: Path, projection_path: str) -> str:
    """Render one tracked generated projection."""
    rel = normalize_path(projection_path)
    if rel in INDEX_PATHS:
        return render_workspace_index(vault, rel)
    if rel == "bibliography.bib":
        from memoria_vault.runtime.capture import render_references_bib

        return render_references_bib(vault)
    if _is_argument_canvas(rel):
        from memoria_vault.runtime.knowledge import render_project_argument_canvas

        canvas = render_project_argument_canvas(vault, Path(rel).parent.name)
        return json.dumps(canvas, indent=2, sort_keys=True) + "\n"
    raise ValueError(f"unsupported tracked projection: {projection_path}")


def check_tracked_projections(vault: Path) -> dict[str, Any]:
    """Regenerate tracked projections and report drift."""
    vault = Path(vault)
    projection_paths = _tracked_projection_paths(vault)
    findings = []
    for rel in projection_paths:
        expected = render_tracked_projection(vault, rel)
        actual = vault / rel
        if not actual.is_file():
            findings.append({"path": rel, "status": "missing"})
        elif actual.read_text(encoding="utf-8") != expected:
            findings.append({"path": rel, "status": "stale"})
    return {
        "ok": not findings,
        "paths": projection_paths,
        "findings": findings,
    }


def changed_tracked_projection_paths(vault: Path) -> list[str]:
    """Return tracked generated projections changed in git status."""
    vault = Path(vault)
    proc = subprocess.run(
        [
            "git",
            "status",
            "--porcelain",
            "--untracked-files=all",
            "--",
            *TRACKED_PROJECTION_PATHS,
            *TRACKED_PROJECTION_GLOBS,
        ],
        cwd=vault,
        check=False,
        text=True,
        capture_output=True,
    )
    if proc.returncode:
        detail = proc.stderr.strip() or proc.stdout.strip()
        raise RuntimeError(f"git status failed: {detail}")
    changed: list[str] = []
    for line in proc.stdout.splitlines():
        if len(line) < 4:
            continue
        path = line[3:]
        if " -> " in path:
            path = path.rsplit(" -> ", 1)[1]
        if _is_tracked_projection_path(path):
            changed.append(path)
    return sorted(set(changed))


def write_tracked_projections(
    vault: Path,
    *,
    context: OperationContext,
    commit: bool = False,
    projection_paths: list[str] | None = None,
) -> dict[str, Any]:
    """Write all tracked generated projections."""
    validate_operation_context(vault, context)
    return _write_tracked_projections(
        vault,
        commit=commit,
        context=context,
        actor=context.actor,
        machine=context.machine,
        projection_paths=projection_paths,
    )


def write_tracked_projections_explicit(
    vault: Path,
    *,
    actor: str,
    machine: str,
    commit: bool = False,
    projection_paths: list[str] | None = None,
) -> dict[str, Any]:
    """Write tracked projections outside an operation envelope."""
    if actor not in state.ACTORS:
        raise ValueError(f"projection actor must be one of {sorted(state.ACTORS)}")
    if not isinstance(machine, str) or not machine.strip():
        raise ValueError("projection machine must be nonblank")
    return _write_tracked_projections(
        vault,
        commit=commit,
        context=None,
        actor=actor,
        machine=machine,
        projection_paths=projection_paths,
    )


def _write_tracked_projections(
    vault: Path,
    *,
    commit: bool,
    context: OperationContext | None,
    actor: str,
    machine: str,
    projection_paths: list[str] | None,
) -> dict[str, Any]:
    from memoria_vault.runtime.capture import (
        write_references_bib,
        write_references_bib_explicit,
    )

    vault = Path(vault)
    paths = _tracked_projection_paths(vault, projection_paths)
    if context:
        index_result = write_workspace_indexes(vault, context=context)
        references_result = write_references_bib(vault, context=context)
    else:
        index_result = write_workspace_indexes_explicit(vault, actor=actor, machine=machine)
        references_result = write_references_bib_explicit(vault, actor=actor, machine=machine)
    changed = [
        *index_result["changed"],
        *([references_result["path"]] if references_result["changed"] else []),
    ]
    for rel in paths:
        if rel in TRACKED_PROJECTION_PATHS:
            continue
        output = vault / rel
        text = render_tracked_projection(vault, rel)
        old = output.read_text(encoding="utf-8") if output.is_file() else None
        if old == text:
            continue
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(text, encoding="utf-8")
        changed.append(rel)
    event = None
    commit_id = ""
    if commit:
        payload = {
            "event": "run",
            "workflow": "generate_tracked_projections",
            "status": "done",
            "outputs": paths,
        }
        if context:
            event = append_journal_event(vault, payload, context=context)
            commit_id = commit_writer_changes(
                vault,
                "regenerate tracked projections",
                paths,
                context=context,
            )
        else:
            event = append_explicit_journal_event(vault, payload, actor=actor, machine=machine)
            commit_id = commit_explicit_writer_changes(
                vault,
                "regenerate tracked projections",
                paths,
                actor=actor,
                machine=machine,
            )
    return {
        "paths": paths,
        "changed": changed,
        "event": event,
        "commit": commit_id,
    }


def _tracked_projection_paths(vault: Path, requested_paths: list[str] | None = None) -> list[str]:
    dynamic = set(
        regenerable_tracked_projection_paths(vault, _git_tracked_dynamic_projection_paths(vault))
    )
    dynamic.update(
        regenerable_tracked_projection_paths(
            vault,
            [
                path.relative_to(vault).as_posix()
                for pattern in TRACKED_PROJECTION_GLOBS
                for path in Path(vault).glob(pattern)
                if path.is_file()
            ],
        )
    )
    if (Path(vault) / ".git").exists():
        dynamic.update(
            path
            for path in regenerable_tracked_projection_paths(
                vault, changed_tracked_projection_paths(vault)
            )
            if path not in TRACKED_PROJECTION_PATHS
        )
    for raw_path in requested_paths or []:
        rel = normalize_path(raw_path)
        if not _is_tracked_projection_path(rel):
            raise ValueError(f"unsupported tracked projection: {raw_path}")
        if rel not in TRACKED_PROJECTION_PATHS and _is_regenerable_tracked_projection(vault, rel):
            dynamic.add(rel)
    return [*TRACKED_PROJECTION_PATHS, *sorted(dynamic)]


def _git_tracked_dynamic_projection_paths(vault: Path) -> set[str]:
    if not (Path(vault) / ".git").exists():
        return set()
    pathspecs = [f":(glob){pattern}" for pattern in TRACKED_PROJECTION_GLOBS]
    proc = subprocess.run(
        ["git", "ls-files", "--", *pathspecs],
        cwd=vault,
        check=False,
        text=True,
        capture_output=True,
    )
    if proc.returncode:
        detail = proc.stderr.strip() or proc.stdout.strip()
        raise RuntimeError(f"git ls-files failed: {detail}")
    return {
        normalize_path(path)
        for path in proc.stdout.splitlines()
        if path and _is_tracked_projection_path(path)
    }


def _is_tracked_projection_path(path: str) -> bool:
    rel = normalize_path(path)
    return rel in TRACKED_PROJECTION_PATHS or _is_argument_canvas(rel)


def regenerable_tracked_projection_paths(vault: Path, paths: list[str]) -> list[str]:
    """Return changed projections whose current owners can be rendered."""
    return sorted(
        {
            rel
            for path in paths
            if _is_tracked_projection_path(rel := normalize_path(path))
            and _is_regenerable_tracked_projection(vault, rel)
        }
    )


def _is_regenerable_tracked_projection(vault: Path, path: str) -> bool:
    rel = normalize_path(path)
    return rel in TRACKED_PROJECTION_PATHS or (
        _is_argument_canvas(rel) and (Path(vault) / Path(rel).parent / "project.md").is_file()
    )


def _is_argument_canvas(path: str) -> bool:
    parts = Path(path).parts
    return len(parts) == 3 and parts[0] == "projects" and parts[2] == "argument.canvas"


def write_workspace_indexes(
    vault: Path,
    *,
    context: OperationContext,
    commit: bool = False,
) -> dict[str, Any]:
    """Write generated root and bundle index.md projections."""
    validate_operation_context(vault, context)
    return _write_workspace_indexes(
        vault,
        commit=commit,
        context=context,
        actor=context.actor,
        machine=context.machine,
    )


def write_workspace_indexes_explicit(
    vault: Path,
    *,
    actor: str,
    machine: str,
    commit: bool = False,
) -> dict[str, Any]:
    """Write workspace indexes outside an operation envelope."""
    if actor not in state.ACTORS:
        raise ValueError(f"projection actor must be one of {sorted(state.ACTORS)}")
    if not isinstance(machine, str) or not machine.strip():
        raise ValueError("projection machine must be nonblank")
    return _write_workspace_indexes(
        vault,
        commit=commit,
        context=None,
        actor=actor,
        machine=machine,
    )


def _write_workspace_indexes(
    vault: Path,
    *,
    commit: bool,
    context: OperationContext | None,
    actor: str,
    machine: str,
) -> dict[str, Any]:
    vault = Path(vault)
    changed: list[str] = []
    for rel in INDEX_PATHS:
        output = vault / rel
        text = render_workspace_index(vault, rel)
        old = output.read_text(encoding="utf-8") if output.exists() else None
        if old == text:
            continue
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(text, encoding="utf-8")
        changed.append(rel)
    event = None
    commit_id = ""
    if commit:
        payload = {
            "event": "run",
            "workflow": "generate_workspace_indexes",
            "status": "done",
            "outputs": list(INDEX_PATHS),
        }
        if context:
            event = append_journal_event(vault, payload, context=context)
            commit_id = commit_writer_changes(
                vault, "regenerate workspace indexes", INDEX_PATHS, context=context
            )
        else:
            event = append_explicit_journal_event(vault, payload, actor=actor, machine=machine)
            commit_id = commit_explicit_writer_changes(
                vault,
                "regenerate workspace indexes",
                INDEX_PATHS,
                actor=actor,
                machine=machine,
            )
    return {"paths": list(INDEX_PATHS), "changed": changed, "event": event, "commit": commit_id}


def check_workspace_indexes(vault: Path) -> bool:
    vault = Path(vault)
    return all(
        (vault / rel).is_file()
        and (vault / rel).read_text(encoding="utf-8") == render_workspace_index(vault, rel)
        for rel in INDEX_PATHS
    )


def _workspace_index() -> str:
    labels = {
        "notes": "Claim and question notes",
        "hubs": "Topic hubs",
        "projects": "Projects",
        "digests": "Work digests",
        "fulltexts": "Full text",
    }
    rows = "\n".join(f"- [{labels[root]}]({root}/)" for root in BUNDLE_ROOTS)
    return _generated(
        "Memoria workspace index",
        "Generated workspace projection. Edit catalog rows or Concept files, not this file.",
        rows,
    )


def _generated(title: str, note: str, body: str) -> str:
    return (
        "---\n"
        "type: system\n"
        f"title: {title}\n"
        "---\n\n"
        "<!-- Generated by memoria_vault.runtime.projections; edit source records instead. -->\n"
        f"# {title}\n\n"
        f"{note}\n\n"
        f"{body}\n"
    )
