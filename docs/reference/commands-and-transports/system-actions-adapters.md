---
title: System action adapters
parent: Commands and transports
nav_order: 4
grand_parent: Reference
---

# System action adapters

Optional adapters wrap the CLI/runtime package. They do not own workspace
authority. For the guarded operation ID list, see [System actions](system-actions.md).

## Optional external adapters

| Action | Performer | What it does |
| --- | --- | --- |
| Vault read / gated write | optional editor or BYO-agent adapter | Reads may inspect workspace files; writes must call the runtime policy hook and then enter the same checked request/journal boundary as CLI work. |
| Literature discovery | provider-backed runtime operations | Uses configured provider allowlists and replay fixtures for tests; no live Zotero or required external agent server is authoritative. |

Two commands that are sometimes mistaken for adapter surfaces are plain core
CLI, with no optional adapter involved: vault search (`memoria ask` / search
debug commands, over the checked-only search tree and runtime read barrier)
and portable bibliography import (`memoria work import --format bibtex` or
`--format csl`, reading local files as input data only). Both ship with the
standalone CLI/runtime package and need no external operation API or
reference-manager DB/API — see [CLI](cli.md).

## Skills and prompts

The standalone runtime does not ship installed profile skill bundles or per-lane
task routing. Reusable prompt behavior lives as package-owned operation
manifests and runs through `memoria operation run`.
