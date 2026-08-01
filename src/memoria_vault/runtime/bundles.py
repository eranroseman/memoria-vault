"""Vault bundle manifest: seeded agent/Obsidian bundles and .memoria/vault.json.

``memoria init`` writes the static agent bundle (Claude/Codex perimeter config,
the MCP wiring, and CLAUDE.md) and, unless ``--no-obsidian`` is set, the
Obsidian plugin bundle, then records a content-hash manifest of what is on
disk. Writes are **write-if-absent**, mirroring ``cli._seed_write_allowed``: an
existing file is PI-owned and is never overwritten, so re-running the installer
(``scripts/install.sh`` runs ``memoria init --yes`` unconditionally) cannot
destroy edited perimeter policy. Nothing here regenerates or recovers an
existing bundle — that is out of scope for this module (see BOOT-C.2's binding
execution text).

The manifest is not authoritative after a repair: ``doctor --repair`` reseeds
``.obsidian/plugins/*`` through ``cli._seed_workspace`` (``overwrite=True``)
without updating ``.memoria/vault.json``.
"""

from __future__ import annotations

import json
import uuid
from importlib.resources import files
from pathlib import Path
from typing import Any

from memoria_vault.runtime.policy.audit import sha256_file
from memoria_vault.runtime.vaultio import write_bytes_durable, write_text_durable

WORKSPACE_SEED_PACKAGE = "memoria_vault.product.workspace_seed"
MANIFEST_REL = ".memoria/vault.json"
MANIFEST_SCHEMA = 1

BUNDLE_FILES: dict[str, tuple[str, ...]] = {
    "agent": (
        ".claude/hooks/write_perimeter.py",
        ".claude/settings.json",
        ".codex/hooks.json",
        ".mcp.json",
        "CLAUDE.md",
    ),
    "obsidian": (
        ".obsidian/plugins/memoria-obsidian/main.js",
        ".obsidian/plugins/memoria-obsidian/manifest.json",
        ".obsidian/plugins/memoria-obsidian/schema.js",
        ".obsidian/plugins/memoria-obsidian/styles.css",
    ),
}


def seed_bytes(rel: str) -> bytes:
    """Return the current package template bytes for a bundle-relative path."""
    return files(WORKSPACE_SEED_PACKAGE).joinpath(*rel.split("/")).read_bytes()


def read_manifest(workspace: Path) -> dict[str, Any] | None:
    """Return the parsed vault manifest, or ``None`` when it does not exist."""
    path = workspace / MANIFEST_REL
    if not path.is_file():
        return None
    return json.loads(path.read_text("utf-8"))


def write_manifest(workspace: Path, manifest: dict[str, Any]) -> None:
    """Durably write the vault manifest as pretty-printed, sorted JSON."""
    write_text_durable(
        workspace / MANIFEST_REL,
        json.dumps(manifest, indent=2, sort_keys=True) + "\n",
        create_parent=True,
    )


def seed_bundles(workspace: Path, *, bundle_names: list[str] | None = None) -> dict[str, Any]:
    """Write the named bundle templates that are absent and hash what is on disk.

    Mints a fresh ``vault_id`` and records the SHA-256 of the file that is
    actually present, never of the template that was skipped — hashing the
    template bytes would make the manifest describe content the vault does not
    hold. Defaults to every registered bundle when ``bundle_names`` is omitted.
    """
    names = bundle_names if bundle_names is not None else list(BUNDLE_FILES)
    bundles_manifest: dict[str, Any] = {}
    for name in names:
        file_hashes: dict[str, str] = {}
        for rel in BUNDLE_FILES[name]:
            target = workspace / rel
            if not target.exists():
                write_bytes_durable(target, seed_bytes(rel), create_parent=True)
            file_hashes[rel] = sha256_file(target)
        bundles_manifest[name] = {"files": file_hashes}
    manifest = {
        "schema": MANIFEST_SCHEMA,
        "vault_id": uuid.uuid4().hex,
        "bundles": bundles_manifest,
    }
    write_manifest(workspace, manifest)
    return manifest
