"""Project code-artifact markdown records."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from memoria_vault.runtime import state
from memoria_vault.runtime.paths import safe_filename
from memoria_vault.runtime.policy.paths import normalize_path
from memoria_vault.runtime.vaultio import frontmatter_doc, write_text_durable


def create_code_artifact(
    vault: Path,
    project_path: str,
    artifact_id: str,
    *,
    title: str = "",
    purpose: str = "warrant",
    approved_command: list[str],
    declared_inputs: list[str] | None = None,
    declared_outputs: list[str] | None = None,
    dependency_notes: str = "",
) -> dict[str, Any]:
    artifact = safe_filename(artifact_id).strip("._-")
    if not artifact:
        raise ValueError("artifact_id is required")
    project_rel = _project_rel(project_path)
    project_dir = Path(project_rel).parent
    record_rel = normalize_path(f"{project_dir}/code/{artifact}.md")
    source_dir = normalize_path(f"{project_dir}/code/{artifact}/src")
    output_dir = normalize_path(f"{project_dir}/code/{artifact}/outputs")
    (Path(vault) / source_dir).mkdir(parents=True, exist_ok=True)
    (Path(vault) / output_dir).mkdir(parents=True, exist_ok=True)
    frontmatter = {
        "type": "code-artifact",
        "id": artifact,
        "artifact_id": artifact,
        "title": title or artifact.replace("-", " ").title(),
        "tags": [],
        "links": {},
        "purpose": purpose,
        "approved_command": [str(part) for part in approved_command],
        "declared_inputs": [normalize_path(path) for path in declared_inputs or []],
        "declared_outputs": [normalize_path(path) for path in declared_outputs or []],
        "dependency_notes": dependency_notes,
        "source_dir": source_dir,
        "output_dir": output_dir,
    }
    body = (
        f"# {frontmatter['title']}\n\n"
        f"Approved command: `{' '.join(frontmatter['approved_command'])}`\n"
    )
    write_text_durable(
        Path(vault) / record_rel, frontmatter_doc(frontmatter, body), create_parent=True
    )
    return state.upsert_code_artifact(
        vault,
        artifact_id=artifact,
        project_path=project_rel,
        record_path=record_rel,
        source_dir=source_dir,
        output_dir=output_dir,
        purpose=purpose,
        approved_command=approved_command,
        declared_inputs=declared_inputs or [],
        declared_outputs=declared_outputs or [],
        dependency_notes=dependency_notes,
        status="ready",
    )


def _project_rel(project_path: str) -> str:
    rel = normalize_path(project_path)
    if "/" not in rel:
        rel = f"projects/{rel}/project.md"
    elif not rel.endswith(".md"):
        rel = f"{rel.rstrip('/')}/project.md"
    if not rel.startswith("projects/"):
        raise ValueError(f"project must live under projects/: {rel}")
    return rel
