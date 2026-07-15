---
title: Quickstart
parent: Setup
grand_parent: How-to guides
nav_order: 1
---


# Quickstart

Three steps from zero to an installed standalone CLI/runtime workspace. For the
full walkthrough with explanations, see [Set up the vault](set-up-the-vault.md).

## Prerequisites

- Git and Python 3.12+ with venv support on your `PATH`; sandbox images must include Git too.
- Native Windows 10/11, Ubuntu/Debian, or WSL2. **macOS is not supported.**
- Provider keys are optional and needed only for live model-backed operations.
  `memoria ask` uses the local checked-only BM25 index and needs no provider key.
- Obsidian is optional as an app; the workspace seed already includes Memoria's
  Obsidian adapter files and core settings. Generic BibTeX/CSL files exported
  from Zotero can be imported when you need them ([Set up Zotero](set-up-zotero.md)).

## Steps

**1. Install.** One line (inspect the script first if you like — see the raw URL):

```bash
# Linux / WSL2:
curl -fsSL https://raw.githubusercontent.com/eranroseman/memoria-vault/main/scripts/install.sh | bash
```

```powershell
# Windows:
irm https://raw.githubusercontent.com/eranroseman/memoria-vault/main/scripts/install.ps1 | iex
```

The installer scaffolds your runtime vault (default `~/Memoria` on Linux/WSL, `%USERPROFILE%\Memoria` on Windows), installs the `memoria` CLI into `.memoria/.venv`, seeds the Memoria Obsidian adapter/config, and wires local hooks. It does not install external search tooling or the Obsidian app.

**2. Verify the CLI runtime.**

```bash
~/Memoria/.memoria/.venv/bin/memoria doctor bundle --workspace ~/Memoria
~/Memoria/.memoria/.venv/bin/memoria workspace rebuild --workspace ~/Memoria --search
```

```powershell
& "$env:USERPROFILE\Memoria\.memoria\.venv\Scripts\memoria.exe" doctor bundle --workspace "$env:USERPROFILE\Memoria"
& "$env:USERPROFILE\Memoria\.memoria\.venv\Scripts\memoria.exe" workspace rebuild --workspace "$env:USERPROFILE\Memoria" --search
```

**3. First checkpoint already made.** The installer already committed the seeded workspace (`initialize memoria workspace`); the working tree is clean.

The remote-and-backup details are in [Set up the vault](set-up-the-vault.md).

On a fresh vault, empty results are normal. Start with the CLI commands above
and the top-level workspace folders: `inbox/`, `digests/`, `fulltexts/`,
`notes/`, `hubs/`, and `projects/`.

## Verify

- `~/Memoria/.memoria/.venv/bin/memoria status --workspace ~/Memoria` returns workspace status
- `~/Memoria/.memoria/.venv/bin/memoria ask --workspace ~/Memoria --question "What needs attention?"` queries the local checked-only BM25 index without provider keys
- The runtime vault has a `.git/` directory after install

## Related

- Full install walkthrough: [Set up the vault](set-up-the-vault.md)
- Obsidian adapter setup: [Set up Obsidian](set-up-obsidian.md)
- First source task: [Capture and ingest a source](../library/capture-and-ingest.md)
- Optional Zotero export setup: [Set up Zotero](set-up-zotero.md)
