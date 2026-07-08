#!/usr/bin/env python3
"""Fail when dropped alpha.14 runtime package homes reappear."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SEED = "src/memoria_vault/product/workspace_seed"
FORBIDDEN_PATHS = (
    "vault-template",
    f"{SEED}/.memoria/operations",
    f"{SEED}/.memoria/mcp",
    f"{SEED}/.memoria/profiles",
    f"{SEED}/.memoria/lane-overrides",
    f"{SEED}/.memoria/tool-registry.yaml",
    f"{SEED}/system/dashboards/fleet-health.md",
    f"{SEED}/system/scripts",
    f"{SEED}/.githooks/post-commit",
    f"{SEED}/capabilities/operations/capture-zotero-source.md",
)
FORBIDDEN_TEXT = (
    f"{SEED}/.memoria/operations",
    ".memoria/operations/",
    f"{SEED}/.memoria/mcp",
    ".memoria/mcp/",
    "QuickAdd: Memoria",
    "system/scripts/capture-note.js",
    "system/scripts/open-inbox.js",
    "system/scripts/record-exploration-trace.js",
    "system/scripts/resolve-inbox-card.js",
    "system/scripts/restore-memoria-shell.js",
    "system/dashboards/fleet-health",
    "system/metrics/lane-",
    'type = "lane-metric"',
    "capture-zotero-source",
    "capture_zotero_source",
    "zotero-export",
    "LANE_OVERRIDE_RELDIR",
    "LanePolicy",
    "load_lane(",
    "parse_lane(",
    "tool-registry allowlist",
    ".githooks/post-commit",
    "hermes kanban create",
    "--lane verify",
    '"task_id": "HARNESS-PACKAGE"',
    '"lane": "memoria-writer"',
    'fm.get("lane")',
)
SEARCH_ROOTS = (
    ".agents",
    ".github",
    ".pre-commit-config.yaml",
    "AGENTS.md",
    "CONTRIBUTING.md",
    "SECURITY.md",
    "docs",
    "scripts",
    "src",
    "tests",
)
SKIP_PARTS = {
    ".git",
    ".venv",
    "__pycache__",
}
SKIP_SUFFIXES = {".pyc", ".sqlite", ".png", ".jpg", ".jpeg", ".gif", ".ico", ".pdf"}
ALLOW_TEXT_FILES = {
    "scripts/checks/alpha14_negative_gate.py",
    "scripts/checks/plugin_provenance_doctor.py",
    "tests/test_plugin_provenance.py",
}


def iter_files(root: Path):
    if root.is_file():
        yield root
        return
    for path in sorted(root.rglob("*")):
        if not path.is_file():
            continue
        rel_parts = set(path.relative_to(ROOT).parts)
        rel = path.relative_to(ROOT).as_posix()
        if rel in ALLOW_TEXT_FILES:
            continue
        if rel_parts & SKIP_PARTS:
            continue
        if path.suffix.lower() in SKIP_SUFFIXES:
            continue
        yield path


def main() -> int:
    errors: list[str] = []
    for rel in FORBIDDEN_PATHS:
        if (ROOT / rel).exists():
            errors.append(f"forbidden path exists: {rel}")
    for rel in SEARCH_ROOTS:
        root = ROOT / rel
        if not root.exists():
            continue
        for path in iter_files(root):
            text = path.read_text(encoding="utf-8", errors="ignore")
            for needle in FORBIDDEN_TEXT:
                if needle in text:
                    errors.append(f"{path.relative_to(ROOT).as_posix()}: contains {needle}")
    if errors:
        print("alpha14-negative-gate: FAIL", file=sys.stderr)
        for error in errors:
            print(f"  {error}", file=sys.stderr)
        return 1
    print("alpha14-negative-gate: clean")
    return 0


if __name__ == "__main__":
    sys.exit(main())
