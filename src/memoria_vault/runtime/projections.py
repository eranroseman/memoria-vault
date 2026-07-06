"""Generated workspace projection helpers."""

from __future__ import annotations

import subprocess
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import Any

from memoria_vault.runtime.policy.paths import normalize_path
from memoria_vault.runtime.trusted_writer import append_journal_event, commit_writer_changes

BUNDLE_ROOTS = ("works", "sources", "notes", "hubs", "projects")
INDEX_PATHS = ("index.md",)
TRACKED_PROJECTION_PATHS = (
    *INDEX_PATHS,
    "bibliography.bib",
)


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
    raise ValueError(f"unsupported tracked projection: {projection_path}")


def check_tracked_projections(vault: Path) -> dict[str, Any]:
    """Regenerate tracked projections into a temp tree and report drift."""
    vault = Path(vault)
    findings = []
    with TemporaryDirectory(prefix="memoria-projections-") as tmp:
        generated_root = Path(tmp)
        for rel in TRACKED_PROJECTION_PATHS:
            expected = render_tracked_projection(vault, rel)
            generated = generated_root / rel
            generated.parent.mkdir(parents=True, exist_ok=True)
            generated.write_text(expected, encoding="utf-8")

            actual = vault / rel
            if not actual.is_file():
                findings.append({"path": rel, "status": "missing"})
            elif actual.read_text(encoding="utf-8") != generated.read_text(encoding="utf-8"):
                findings.append({"path": rel, "status": "stale"})
    return {
        "ok": not findings,
        "paths": list(TRACKED_PROJECTION_PATHS),
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
        if len(line) < 4 or "D" in line[:2]:
            continue
        path = line[3:]
        if " -> " in path:
            path = path.rsplit(" -> ", 1)[1]
        if path in TRACKED_PROJECTION_PATHS:
            changed.append(path)
    return sorted(set(changed))


def write_tracked_projections(
    vault: Path,
    *,
    commit: bool = False,
    machine: str | None = None,
) -> dict[str, Any]:
    """Write all tracked generated projections."""
    from memoria_vault.runtime.capture import write_references_bib

    vault = Path(vault)
    index_result = write_workspace_indexes(vault)
    references_result = write_references_bib(vault)
    changed = [
        *index_result["changed"],
        *([references_result["path"]] if references_result["changed"] else []),
    ]
    event = None
    commit_id = ""
    if commit:
        event = append_journal_event(
            vault,
            {
                "event": "run",
                "run_id": "projection:tracked",
                "workflow": "generate_tracked_projections",
                "status": "done",
                "outputs": list(TRACKED_PROJECTION_PATHS),
            },
            machine=machine,
        )
        commit_id = commit_writer_changes(
            vault,
            "regenerate tracked projections",
            TRACKED_PROJECTION_PATHS,
            machine=machine,
        )
    return {
        "paths": list(TRACKED_PROJECTION_PATHS),
        "changed": changed,
        "event": event,
        "commit": commit_id,
    }


def write_workspace_indexes(
    vault: Path,
    *,
    commit: bool = False,
    machine: str | None = None,
) -> dict[str, Any]:
    """Write generated root and bundle index.md projections."""
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
        event = append_journal_event(
            vault,
            {
                "event": "run",
                "run_id": "projection:index.md",
                "workflow": "generate_workspace_indexes",
                "status": "done",
                "outputs": list(INDEX_PATHS),
            },
            machine=machine,
        )
        commit_id = commit_writer_changes(
            vault,
            "regenerate workspace indexes",
            INDEX_PATHS,
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
        "works": "Works corpus",
        "sources": "Source notes",
        "notes": "Claim and question notes",
        "hubs": "Topic hubs",
        "projects": "Projects",
    }
    rows = "\n".join(f"- [{labels[root]}]({root}/)" for root in BUNDLE_ROOTS)
    return _generated(
        "Memoria workspace index",
        "Generated workspace projection. Edit catalog rows or Concept files, not this file.",
        rows,
    )


def _generated(title: str, note: str, body: str) -> str:
    return (
        "<!-- Generated by memoria_vault.runtime.projections; edit source records instead. -->\n"
        f"# {title}\n\n"
        f"{note}\n\n"
        f"{body}\n"
    )
