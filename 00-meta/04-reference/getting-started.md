# Getting started

First-time setup checklist. Five steps from clone to first ingest.

## 1. Prerequisites

- **Obsidian** ≥ 1.7.2
- **Hermes** installed (see [hermes-agent.nousresearch.com](https://hermes-agent.nousresearch.com/))
- **Python** ≥ 3.10 (for the Memoria MCP servers)
- **Zotero** with [Better BibTeX](https://retorque.re/zotero-better-bibtex/) plugin
- **Git** (used for version history)

## 2. Clone and install

```bash
git clone <vault-repo-url> my-vault
cd my-vault
./install.ps1   # Windows
./install.sh    # macOS / Linux
```

The installer copies the seven Hermes profile directories from `.memoria/profiles/` to `~/.hermes/profiles/`, substitutes `{{VAULT_PATH}}` in each `mcp.json` with the absolute vault path, and bootstraps `.env` files from `.env.EXAMPLE`.

## 3. Configure secrets

For each profile in `~/.hermes/profiles/memoria-<name>/`, edit `.env` with real API keys (Anthropic, OpenAI, Zotero, etc.). The `.env.EXAMPLE` file lists which keys each profile expects.

## 4. Open the vault in Obsidian

Open the vault root directly. Pin [[../index|the vault index]] in the sidebar. Set the default workspace.

## 5. First ingest

- Open Zotero
- Select a paper
- `Cmd-P → Memoria: capture from Zotero selection`
- Watch `10-inbox/03-candidates/` populate within 60 seconds
- After classification, the paper-note appears in `20-sources/01-papers/`

## What to read next

- [[../index|index]] — the daily landing page
- [[agent-roles]] — what each profile does
- [[profile-policies]] — who can write where
- [[safe-mode]] — what to do when something breaks
- [[../research-directions|research-directions]] — populate your current priorities

## Common first-week tasks

- **Populate `research-directions.md`** — without this, the Librarian has no targets
- **Try `Memoria: ask about this note`** on a paper-note — verify the ACP pane opens
- **Set up the Reading & Processing workspace** — see [[obsidian-config]]
- **Pin top 5 commands to Commander** — see [[obsidian-config]]

---

**For depth:** [tutorials/01-set-up-from-zero.md](../../../memoria-docs/tutorials/01-set-up-from-zero.md) — the authoritative setup walkthrough with troubleshooting notes.
