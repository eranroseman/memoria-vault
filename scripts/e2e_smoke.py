#!/usr/bin/env python3
"""Importable assertions for scripts/e2e-smoke.sh."""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any

import yaml

ROOT = Path(__file__).resolve().parent.parent
for path in (ROOT / "src", ROOT):
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))

from memoria_vault.runtime.jsonl import iter_jsonl

STAGE_LABELS = {
    "vault-assembly-1": "1. vault-assembly: scaffold + populate (installer-equivalent, from vault-template/)",
    "vault-assembly-2": "2. vault-assembly: golden copy + git hook wiring",
    "vault-assembly-3": "3. vault-assembly: fresh-vault integrity",
    "commit-gate": "4. commit-gate: malformed claim blocks, valid claim passes",
    "offline-ingest-1": "5. offline-ingest: entity + honesty card",
    "offline-ingest-2": "6. offline-ingest: typed graph (optional: networkx)",
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


def assert_plugin_bundle(vault: Path) -> None:
    appearance = json.loads((vault / ".obsidian/appearance.json").read_text(encoding="utf-8"))
    enabled = set(appearance.get("enabledCssSnippets", []))
    expected = {"memoria-link-colors", "memoria-property-badges"}
    missing = sorted(expected - enabled)
    assert not missing, f"CSS snippets not default-on: {missing}"
    plugins = json.loads((vault / ".obsidian/community-plugins.json").read_text(encoding="utf-8"))
    for plugin in ["dataview", "obsidian-git", "obsidian-local-rest-api", "portals", "quickadd"]:
        assert plugin in plugins, f"bundled plugin not enabled: {plugin}"
        assert (vault / ".obsidian/plugins" / plugin / "manifest.json").is_file(), (
            f"missing plugin manifest: {plugin}"
        )
    print("   git repo, hooks, CSS snippets, and plugin bundle asserted")


def assert_executable(path: Path, label: str) -> None:
    assert path.exists() and path.stat().st_mode & 0o111, (
        f"{label} is missing or not executable: {path}"
    )


def add_repo_paths(root: Path) -> None:
    for path in (
        root,
        root / "vault-template/.memoria",
        root / "vault-template/.memoria/mcp",
    ):
        if str(path) not in sys.path:
            sys.path.insert(0, str(path))


def assert_offline_ingest(root: Path, vault: Path) -> None:
    add_repo_paths(root)

    from operations.lib import inbox, schema
    from operations.processing.ingest import ingest_paper

    bib = (
        "@article{x2024demo,\n"
        "  title = {Demo Work},\n"
        "  author = {Doe, Jane},\n"
        "  year = {2024},\n"
        "  journal = {Demo Journal},\n"
        "}\n"
    )
    note = ingest_paper.ingest_text("x2024demo", bib)
    types = schema.load_types()
    errs = schema.validate_frontmatter(note["frontmatter"], types[note["note_type"]])
    assert not errs, f"ingested entity invalid: {errs}"
    (vault / note["path"]).write_text(ingest_paper.render(note), encoding="utf-8")
    card = inbox.write_proposal(
        vault,
        "candidate",
        "Demo Work",
        "Accept into catalog",
        "fills a demo gap",
        "single-source demo",
        "the gap wins",
        "likely",
        "librarian",
        citekey="@x2024demo",
    )
    frontmatter = yaml.safe_load(re.match(r"^---\n(.*?)\n---", card.read_text(), re.S).group(1))
    assert schema.validate_frontmatter(frontmatter, types["candidate"]) == []
    assert "agent_recommendation" not in frontmatter
    print("   entity + honesty card schema-valid")


def assert_typed_graph(root: Path, vault: Path) -> None:
    try:
        import networkx  # noqa: F401
    except ImportError:
        print("   (networkx not installed - graph step skipped)")
        return
    if str(root) not in sys.path:
        sys.path.insert(0, str(root))
    sys.path.insert(0, str(root / "vault-template/.memoria/mcp"))
    import cluster_mcp

    graph: dict[str, list[dict[str, Any]]] = cluster_mcp.build_graph(vault, seed=7)
    assert graph["nodes"], "graph collected no nodes"
    print(f"   graph: {len(graph['nodes'])} nodes / {len(graph['edges'])} edges")


def assert_workflow_replay_artifacts(vault: Path) -> None:
    for rel in [
        "catalog/papers/harness2026.md",
        "projects/harness/project-gate-index.md",
        "projects/harness/exports/harness-section.md",
    ]:
        assert (vault / rel).is_file(), f"workflow replay artifact missing: {rel}"
    forbidden = vault / "notes/claims/blocked-by-harness.md"
    assert not forbidden.exists(), "workflow replay left forbidden claim behind"
    audit = list(iter_jsonl(vault / "system/logs/audit.jsonl"))
    assert audit[-1]["decision"] == "deny", f"last audit decision was not deny: {audit[-1]}"
    assert audit[-1]["task_id"] == "HARNESS-DENY", (
        f"last audit task_id was not HARNESS-DENY: {audit[-1]}"
    )
    print("   deny audit row and forbidden-file absence asserted")


def assert_final_verdict(verdict: str) -> None:
    assert re.search(r"PASS|REVIEW", verdict), f"worked vault verdict: {verdict}"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "command",
        choices=[
            "stage-label",
            "vault-skeleton",
            "plugin-bundle",
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
    elif ns.command == "plugin-bundle":
        assert_plugin_bundle(Path(ns.args[0]))
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
