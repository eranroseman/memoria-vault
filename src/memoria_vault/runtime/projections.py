"""Generated alpha.12 workspace projection helpers."""

from __future__ import annotations

from pathlib import Path
from tempfile import TemporaryDirectory
from typing import Any

from memoria_vault.runtime.policy.paths import normalize_path
from memoria_vault.runtime.trusted_writer import append_journal_event, commit_writer_changes
from memoria_vault.runtime.vaultio import read_frontmatter

BUNDLE_ROOTS = ("catalog", "knowledge", "capabilities")
INDEX_PATHS = ("index.md", "catalog/index.md", "knowledge/index.md", "capabilities/index.md")
TRACKED_PROJECTION_PATHS = (*INDEX_PATHS, "references.bib")


def render_workspace_index(vault: Path, index_path: str) -> str:
    """Render one generated OKF-style index.md projection."""
    rel = normalize_path(index_path)
    if rel == "index.md":
        return _workspace_index()
    if rel not in INDEX_PATHS:
        raise ValueError(f"unsupported index projection: {index_path}")
    bundle = rel.split("/", 1)[0]
    return _bundle_index(Path(vault), bundle)


def render_tracked_projection(vault: Path, projection_path: str) -> str:
    """Render one tracked generated projection."""
    rel = normalize_path(projection_path)
    if rel in INDEX_PATHS:
        return render_workspace_index(vault, rel)
    if rel == "references.bib":
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
    rows = "\n".join(f"- [{root}]({root}/index.md)" for root in BUNDLE_ROOTS)
    return _generated(
        "Memoria workspace index",
        "Generated workspace projection. Edit Concept files, not this file.",
        rows,
    )


def _bundle_index(vault: Path, bundle: str) -> str:
    bundle_root = vault / bundle
    rows = [_concept_row(bundle_root, path) for path in _concept_paths(bundle_root)]
    body = "\n".join(rows) if rows else "_No checked Concepts._"
    return _generated(
        f"{bundle.title()} index",
        "Generated bundle projection. Edit Concept files, not this file.",
        body,
    )


def _concept_paths(root: Path) -> list[Path]:
    if not root.is_dir():
        return []
    return sorted(
        path
        for path in root.rglob("*.md")
        if path.name != "index.md" and read_frontmatter(path).get("check_status") == "checked"
    )


def _concept_row(bundle_root: Path, path: Path) -> str:
    frontmatter = read_frontmatter(path)
    rel = path.relative_to(bundle_root).as_posix()
    title = str(frontmatter.get("title") or path.stem)
    concept_type = str(frontmatter.get("type") or "concept")
    description = str(frontmatter.get("description") or "").strip()
    suffix = f" — {description}" if description else ""
    return f"- [{title}]({rel}) `{concept_type}`{suffix}"


def _generated(title: str, note: str, body: str) -> str:
    return (
        "<!-- Generated by memoria_vault.runtime.projections; edit source Concepts instead. -->\n"
        f"# {title}\n\n"
        f"{note}\n\n"
        f"{body}\n"
    )
