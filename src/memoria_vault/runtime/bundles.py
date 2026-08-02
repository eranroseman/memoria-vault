"""Vault bundle manifest: seeded agent/Obsidian bundles and .memoria/vault.json.

``memoria init`` writes the static agent bundle (Claude/Codex perimeter config,
the MCP wiring, and CLAUDE.md) and, unless ``--no-obsidian`` is set, the
Obsidian plugin bundle, then records what the vault was created with.

**One writer, one policy.** This module is the only writer of the bundle paths
on the init path — ``cli._seed_write_allowed`` declines them, so the seed-class
copy cannot write them a second time with a different policy — and everything
it writes is **write-if-absent**, the bundle files and ``.memoria/vault.json``
alike. An existing file is PI-owned and is never overwritten, so re-running the
installer (``scripts/install.sh`` runs ``memoria init --yes`` unconditionally)
can neither destroy edited perimeter policy nor churn the vault identity that
``runtime.json`` publishes. ``doctor --repair`` never calls this module; it
restores ``.obsidian/plugins/*`` as a runtime seed. Within one engine version
those are the bytes the receipt recorded, so repair moves disk back onto the
manifest — but **the manifest is not authoritative after a repair on a newer
engine**: repair reseeds from whatever the installed package ships, and nothing
here refreshes the record.

Files this module creates land 0600 (``write_bytes_durable``'s ``mkstemp``),
matching the other engine-written control files rather than the seed-class
copy's 0644. A file it adopts keeps the mode the PI's copy already had. The
mode is a property of the *writer*, never of the path: the same bundle path is
0644 when ``doctor --repair`` recreates a deleted ``.obsidian/plugins/*`` file
through the seed-class copy. Nothing reads the mode.

**The manifest is an as-created receipt** (BOOT-C.6, 2026-08-01): vault
identity plus the SHA-256 of each bundle file as the vault received it. It is
deliberately not refreshed by a later run — refreshing it re-minted the vault
id and left a spurious ``' M .memoria/vault.json'`` in vault history on every
installer re-run.

**These hashes are not an as-seeded baseline.** A file already present when the
vault was created records the PI's bytes, and a bundle seeded by a later run is
not recorded at all. A future drift, skew, or tamper check needs its own
as-seeded record and must not be pointed at this field.
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
    # `main.js` requires every sibling module by relative path, so a module
    # missing from this roster is not merely absent from the vault -- the
    # entrypoint throws MODULE_NOT_FOUND and the plugin does not load at all.
    "obsidian": (
        ".obsidian/plugins/memoria-obsidian/handshake.js",
        ".obsidian/plugins/memoria-obsidian/main.js",
        ".obsidian/plugins/memoria-obsidian/manifest.json",
        ".obsidian/plugins/memoria-obsidian/pill.js",
        ".obsidian/plugins/memoria-obsidian/relate.js",
        ".obsidian/plugins/memoria-obsidian/schema.js",
        ".obsidian/plugins/memoria-obsidian/styles.css",
        ".obsidian/plugins/memoria-obsidian/viewspec.js",
    ),
}
# Membership test for the seed-class writer's one-writer refusal (cli.py).
BUNDLE_PATHS: frozenset[str] = frozenset(rel for rels in BUNDLE_FILES.values() for rel in rels)


def seed_bytes(rel: str) -> bytes:
    """Return the current package template bytes for a bundle-relative path."""
    return files(WORKSPACE_SEED_PACKAGE).joinpath(*rel.split("/")).read_bytes()


def bundle_files(bundle_names: list[str] | None = None) -> list[str]:
    """Return the seeded paths of the named bundles, sorted."""
    names = list(BUNDLE_FILES) if bundle_names is None else bundle_names
    return sorted(rel for name in names for rel in BUNDLE_FILES[name])


def bundle_write_targets(bundle_names: list[str] | None = None) -> list[str]:
    """Return every workspace-relative path this module may write."""
    return sorted({MANIFEST_REL, *bundle_files(bundle_names)})


def write_manifest(workspace: Path, manifest: dict[str, Any]) -> None:
    """Durably write the vault manifest as pretty-printed, sorted JSON."""
    write_text_durable(
        workspace / MANIFEST_REL,
        json.dumps(manifest, indent=2, sort_keys=True) + "\n",
        create_parent=True,
    )


def seed_bundles(workspace: Path, *, bundle_names: list[str] | None = None) -> None:
    """Write the absent bundle files, then the manifest when it too is absent.

    Records the SHA-256 of the file that is actually present, never of a
    template that was skipped. A manifest already on disk is this vault's
    identity and creation receipt: it is left exactly as written, so the
    ``vault_id`` in ``runtime.json`` is minted once and pinned.
    """
    names = list(BUNDLE_FILES) if bundle_names is None else bundle_names
    for name in names:
        for rel in BUNDLE_FILES[name]:
            target = workspace / rel
            if not target.exists():
                write_bytes_durable(target, seed_bytes(rel), create_parent=True)
    if (workspace / MANIFEST_REL).exists():
        return
    write_manifest(
        workspace,
        {
            "schema": MANIFEST_SCHEMA,
            "vault_id": uuid.uuid4().hex,
            "bundles": {
                name: {"files": {rel: sha256_file(workspace / rel) for rel in BUNDLE_FILES[name]}}
                for name in names
            },
        },
    )
