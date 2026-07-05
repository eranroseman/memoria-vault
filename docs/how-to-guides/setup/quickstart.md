---
title: Quickstart
parent: Setup
grand_parent: How-to guides
nav_order: 1
---


# Quickstart

Four steps from zero to an installed standalone CLI/runtime workspace. For the
full walkthrough with explanations, see [Set up the vault](set-up-the-vault.md).

## Prerequisites

- Git and Python 3 with venv support on your `PATH`; sandbox images must include Git too.
- Runtime provider keys for the CLI features you plan to use.
- Optional adapters come later and are not part of the bootstrap. Generic
  BibTeX/CSL files exported from Zotero can be imported when you need them
  ([Set up Zotero](set-up-zotero.md)).

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

The installer scaffolds your runtime vault (default `~/Memoria` on Linux/WSL, `%USERPROFILE%\Memoria` on Windows), installs the `memoria` CLI into `.memoria/.venv`, and wires local hooks. It does not install external search tooling.

**2. Verify the CLI runtime.**

```bash
~/Memoria/.memoria/.venv/bin/memoria doctor bundle --workspace ~/Memoria
~/Memoria/.memoria/.venv/bin/memoria workspace rebuild --workspace ~/Memoria --search
```

```powershell
& "$env:USERPROFILE\Memoria\.memoria\.venv\Scripts\memoria.exe" doctor bundle --workspace "$env:USERPROFILE\Memoria"
& "$env:USERPROFILE\Memoria\.memoria\.venv\Scripts\memoria.exe" workspace rebuild --workspace "$env:USERPROFILE\Memoria" --search
```

**3. Make the first checkpoint.** The installer initializes Git and wires hooks, but it does not create the first commit or set a remote:

```bash
cd ~/Memoria && git add -A && git commit -m "Initial Memoria vault"
```

The remote-and-backup details are in [Set up the vault](set-up-the-vault.md).

On a fresh vault, empty tables are normal. The Inbox, Library, Knowledge, and
Project spaces each show a **First actions** callout above their Bases views; use
those commands as the day-1 path for the space you are in.

## Verify

- `~/Memoria/.memoria/.venv/bin/memoria status --workspace ~/Memoria` returns workspace status
- `~/Memoria/.memoria/.venv/bin/memoria ask --workspace ~/Memoria --question "What needs attention?"` reaches the CLI ask path once provider keys are configured
- The runtime vault has a `.git/` directory after install

## Related

- Full install walkthrough: [Set up the vault](set-up-the-vault.md)
- Optional plain-editor setup: [Set up Obsidian](set-up-obsidian.md)
- First source task: [Capture and ingest a source](../library/capture-and-ingest.md)
- Optional Zotero export setup: [Set up Zotero](set-up-zotero.md)
