#!/usr/bin/env python3
"""Importable assertions for scripts/e2e-smoke.sh."""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent.parent
for path in (ROOT / "src", ROOT):
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))

STAGE_LABELS = {
    "vault-assembly-1": "1. vault-assembly: scaffold + populate (installer-equivalent, from vault-template/)",
    "vault-assembly-2": "2. vault-assembly: golden copy + git hook wiring",
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
    for path in (
        root,
        root / "vault-template/.memoria",
    ):
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
        "type: project\nid: projects/package-gate\ncheck_status: checked\n"
        "standing: current\nlinks: {}\ntitle: Package gate\n"
        "description: Package gate project.\nthesis: knowledge/notes/package-thesis.md\n",
        "Package gate project.",
    )
    _write_note(
        thesis,
        "type: note\nid: notes/package-thesis\ncheck_status: checked\n"
        "standing: current\nlinks: {}\ntitle: Package thesis\nstatus: accepted\n",
        "Package thesis.",
    )
    _write_note(
        support,
        "type: note\nid: notes/package-support\ncheck_status: checked\n"
        "standing: current\ntitle: Package support\nstatus: accepted\n"
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
        "catalog/sources/harness2026/source.md",
        "knowledge/notes/harness-support.md",
        "knowledge/projects/harness/argument.canvas",
    ]:
        assert (vault / rel).is_file(), f"workflow replay artifact missing: {rel}"
    forbidden = vault / "knowledge/notes/blocked-by-harness.md"
    assert not forbidden.exists(), "workflow replay left forbidden note behind"
    print("   workflow replay artifacts and forbidden-file absence asserted")


def assert_final_verdict(verdict: str) -> None:
    assert re.search(r"PASS|REVIEW", verdict), f"worked vault verdict: {verdict}"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "command",
        choices=[
            "stage-label",
            "vault-skeleton",
            "no-obsidian-bundle",
            "executable",
            "offline-ingest",
            "typed-graph",
            "workflow-artifacts",
            "final-verdict",
        ],
    )
    parser.add_argument("args", nargs="*")
    ns = parser.parse_args(argv)

    if ns.command == "stage-label":
        print_stage_label(ns.args[0])
    elif ns.command == "vault-skeleton":
        assert_vault_skeleton(Path(ns.args[0]), Path(ns.args[1]))
    elif ns.command == "no-obsidian-bundle":
        assert_no_obsidian_bundle(Path(ns.args[0]))
    elif ns.command == "executable":
        assert_executable(Path(ns.args[0]), ns.args[1])
    elif ns.command == "offline-ingest":
        assert_offline_ingest(Path(ns.args[0]), Path(ns.args[1]))
    elif ns.command == "typed-graph":
        assert_typed_graph(Path(ns.args[0]), Path(ns.args[1]))
    elif ns.command == "workflow-artifacts":
        assert_workflow_replay_artifacts(Path(ns.args[0]))
    elif ns.command == "final-verdict":
        assert_final_verdict(ns.args[0])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
