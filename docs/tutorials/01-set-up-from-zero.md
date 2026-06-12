---
title: "Tutorial 01: Set up from zero"
parent: Tutorials
---

# Tutorial 01: Set up from zero

**You will end with:** a working Memoria vault open in Obsidian, the five profiles installed, the co-PI answering in the Agent Client pane, and the Library workspace loaded.

**Time:** 20–30 minutes.

**You will use:** a terminal (for the installer and your API keys), then Obsidian.

---

## Prerequisites

- Linux or WSL2 (on Windows, `install.ps1` gates WSL2 and runs the same installer inside it)
- [Git](https://git-scm.com/) installed (the installer checks and tells you if anything is missing — it provisions the rest itself, including Hermes)
- [Obsidian](https://obsidian.md/) installed, or let the installer guide you through it

You do **not** need Zotero for setup. It is an optional bibliographic backbone, covered where you first use it — [Tutorial 03: Bring in a paper](03-bring-in-a-paper.md).

---

## Step 1 — Run the installer

The recommended invocation is inspect-first:

```bash
curl -fsSL https://raw.githubusercontent.com/eranroseman/memoria-vault/main/scripts/install.sh -o install.sh
less install.sh        # read what it will do
bash install.sh
```

Or the convenience one-liner:

```bash
curl -fsSL https://raw.githubusercontent.com/eranroseman/memoria-vault/main/scripts/install.sh | bash
```

The installer confirms every external step before running it (`--dry-run` previews everything and changes nothing). On screen you'll watch it check prerequisites, then **scaffold → populate → golden-copy** your runtime vault (default `~/Memoria` — pick a folder outside any cloud-synced tree). It deploys the **five profiles** (`memoria-copi` plus the four background lanes) and wires the maintenance crons. Decline the optional clustering stack (~2 GB) when prompted — graph tools still work, and you can add it later with `--profiles-only`.

When it finishes it prints a **Next steps** checklist. The rest of this tutorial walks that checklist.

Full flag and step reference: [Installer (bootstrap)](../reference/installer.md).

---

## Step 2 — Add your API keys

Open `~/.hermes/.env` and fill in:

```bash
KILOCODE_API_KEY=...      # model access
OBSIDIAN_API_KEY=...      # from the Local REST API plugin (Step 3 below)
OPENALEX_API_KEY=...      # openalex.org/settings/api — required for discovery
```

Then propagate them into every profile (profile runs read only their own `.env` — there is no global fallback):

```bash
bash scripts/install.sh --profiles-only --vault ~/Memoria
```

Re-run that command any time you add or rotate a key.

---

## Step 3 — Open the vault in Obsidian

1. Open Obsidian → **Open folder as vault** → choose the folder the installer reported (default `~/Memoria`).
2. Turn off Restricted mode when prompted (**Settings → Community plugins**) so the bundled plugins load — they ship pre-installed and pre-configured.
3. Copy the API key from **Settings → Local REST API** into `OBSIDIAN_API_KEY` in `~/.hermes/.env` (then re-run the `--profiles-only` command from Step 2).
4. Make the vault a git repo — obsidian-git and the pre-commit gate need one, and the installer deliberately doesn't `git init` for you:

```bash
cd ~/Memoria && git init && git add -A && git commit -m "Initial Memoria vault"
```

`home.md` opens as the front door: the **What needs me** Inbox view, the dashboard index, and your research focus.

---

## Step 4 — Open the co-PI pane

The co-PI is the one agent you converse with. Open it either way:

- **In Obsidian:** command palette (`Cmd/Ctrl+P`) → **Agent Client: Open chat view**. The pane defaults to the co-PI.
- **In a terminal:** `hermes -p memoria-copi acp`

Verify the profiles installed first if you like: `hermes profile list` should show all five `memoria-*` profiles.

Say hello and ask it something — "explain how this vault is organized" is a good first question. It questions, explains the system, and delegates tasks to the background lanes; it never writes your vault itself ([The co-PI](../explanation/profiles/co-pi.md)).

---

## Step 5 — Switch to the Library workspace

Two saved layouts ship with the vault: **Home** (the launchpad) and **Library** (the reading layout). Switch via the command palette: **Workspaces: Load workspace** → `Library`. See [Obsidian workspaces](../reference/obsidian-workspaces.md).

The Library workspace opens the reading pipeline, the discuss queue, and the Catalog view — empty for now. They fill as you work through the next tutorials.

---

## What you have

- A runtime vault at `~/Memoria`, scaffolded, populated, and golden-copied
- Five profiles installed and the maintenance crons wired
- API keys in `~/.hermes/.env`, propagated to every profile
- The co-PI answering in the Agent Client pane
- The Library workspace loaded

---

## What's next

[Tutorial 02: Your first note](02-your-first-note.md) — capture a fleeting thought from the palette and learn the distill-or-archive discipline.

**See also:** [Quickstart](../how-to-guides/setup/quickstart.md) for the condensed install path, and [What Memoria is](../explanation/overview/what-memoria-is.md) for what you just installed.

---

[Tutorial 02: Your first note](02-your-first-note.md) →
