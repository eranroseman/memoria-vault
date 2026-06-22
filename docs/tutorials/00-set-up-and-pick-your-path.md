---
title: "Tutorial 00: Set up and pick your path"
parent: Tutorials
---

# Tutorial 00: Set up and pick your path

**You will end with:** a working Memoria vault open in Obsidian, the Co-PI answering in the Agent Client pane, a one-line *Produce goal* written down where you can see it, and — recommended — the sample vault loaded so you have something to finish.

**Time:** 25–35 minutes.

**You will use:** a terminal for the installer and API keys, then Obsidian.

**Prerequisite:** none — this is where you start.

---

Memoria is a loop, not a pipeline. You **accumulate** — turn what you read into durable, connected, traceable knowledge — and you **produce** — write something defensible from what you know. This tutorial gets the vault running, then has you pick how you want to learn the loop and name what you are aiming at.

## Step 1 — Run the installer

Download the installer for your platform, read it, then run it.

For Windows production:

```powershell
Invoke-WebRequest https://raw.githubusercontent.com/eranroseman/memoria-vault/main/scripts/install.ps1 -OutFile install.ps1
Get-Content .\install.ps1     # read what it will do
.\install.ps1
```

For Linux/WSL2:

```bash
curl -fsSL https://raw.githubusercontent.com/eranroseman/memoria-vault/main/scripts/install.sh -o install.sh
less install.sh        # read what it will do
bash install.sh
```

The installer confirms every external step before running it. On screen you'll watch it check prerequisites, then **scaffold → populate → golden-copy** your runtime vault (default `~/Memoria` — pick a folder outside any cloud-synced tree). It deploys the **five profiles** (`memoria-copi` plus the four background lanes) and wires the maintenance crons. When it asks about the optional clustering stack (~2 GB), skip it unless you already know you need topic modeling; you can add it later.

When it finishes it prints a **Next steps** checklist. Full flag and step reference: [Installer (bootstrap)](../reference/installer.md).

---

## Step 2 — Add your API keys

Open the shared Hermes env file and fill in the keys you have: model access and the discovery key. On Windows the file is `%LOCALAPPDATA%\hermes\.env`; on Linux/WSL2 it is `~/.hermes/.env`. You'll add the Obsidian Local REST API key and port after opening Obsidian in Step 3. Canonical key names and where each comes from: [Set up Hermes](../how-to-guides/setup/set-up-hermes.md).

Then propagate them into every profile (profile runs read only their own `.env` — there is no global fallback):

```powershell
.\install.ps1 -ProfilesOnly -Vault "$env:USERPROFILE\Memoria"
```

```bash
bash install.sh --profiles-only --vault ~/Memoria
```

Re-run that command any time you add or rotate a key.

---

## Step 3 — Open the vault and meet the Co-PI

1. Open Obsidian → **Open folder as vault** → choose the folder the installer reported (default `~/Memoria`).
2. Turn off Restricted mode when prompted (**Settings → Community plugins**) so the bundled plugins load — they ship pre-installed and pre-configured.
3. Copy the API key from **Settings → Local REST API** into `OBSIDIAN_API_KEY` in the shared Hermes env file, set `OBSIDIAN_MCP_PORT` to the plugin's HTTPS port and `OBSIDIAN_MCP_SSL_VERIFY` to the exported certificate path, then re-run the `--profiles-only` command from Step 2.
4. Make the vault a git repo — obsidian-git and the pre-commit hook need one. The init/add/commit commands are in [Set up the vault](../how-to-guides/setup/set-up-the-vault.md).

Now open the one agent you'll talk to. Press the command palette (`Cmd-P` on Mac, `Ctrl-P` on Windows/Linux) → **Agent Client: Open chat view**. The pane defaults to the **Co-PI**. Say hello and ask *"explain how this vault is organized."*

This is the only agent you converse with. The Co-PI questions your thinking, explains the system, and delegates durable work to the four background lanes — but it never writes your vault itself, and you never address a background lane directly ([The Co-PI](../explanation/profiles/co-pi.md)). Everything you do in these tutorials, you do in conversation with it.

---

## Step 4 — Pick your path

Here the tutorials fork. Done for real, accumulating a corpus dense enough to write from takes weeks of reading — too long for one sitting. So you have a choice of where to start from.

**Recommended — load the sample vault.** A small, labeled starter corpus on one neutral topic: **whether a Mediterranean diet protects the heart**. It is deliberately *half-built* — a few sources are fully worked into claims and links, and a few pieces are left unfinished on purpose. You finish them (that *is* the core lesson) and then extend the corpus with a source of your own. Loading it lets you reach the Produce payoff today instead of after weeks of reading.

To load it, press `Cmd/Ctrl-P` and run **Memoria: load sample vault**. The command copies the bundled sample into `catalog/` and `notes/`; every sample note is labeled `sample: true` so it stays visibly separate from your own work. The full contents and how to remove it later: [the sample vault](sample-vault/README.md).

**Or — start with your own source.** If you already have a paper you're reading and a question you're chasing, skip the sample and bring your own. The sample is **optional and skippable** — an experienced researcher loses nothing by starting from their own material.

> One honest note about the sample: a cluster that dense is weeks of reading, compressed. You finish a few reps on it to learn the moves, then repeat them on your own sources. It is a teaching scaffold, and when you're done **Memoria: remove sample vault** archives it without breaking a single link.

Whichever you pick, you converse with the same Co-PI and learn the same loop. The next tutorial has you bring in a source of **your own** either way; the sample sits alongside as worked examples to copy the shape from.

---

## Step 5 — Write your Produce goal

Before you accumulate anything, name what you're accumulating *toward*. Write one line — the thing you want to be able to defend at the end:

> *A verified 200-word section on whether a Mediterranean diet protects the heart.*

If you're bringing your own source, write the equivalent for your topic — one concrete, writable deliverable, not a vague area ("learn about X"). The goal is what keeps Accumulate honest: you're not collecting notes, you're building toward a claim you'll have to stand behind.

Keep it visible. Capture it from the palette as a fleeting note (`Cmd/Ctrl-P` → **Memoria: capture fleeting**), or pin it in a scratch note — anywhere you'll see it while you work. You'll come back to this exact line in Tutorial 03 when you draft from your claims.

---

## What you have

- A runtime vault at `~/Memoria`, scaffolded, populated, and golden-copied
- Five profiles installed and the maintenance crons wired
- The Co-PI answering in the Agent Client pane
- A one-line Produce goal written down where you can see it
- Recommended: the sample vault loaded — a half-built corpus waiting for you to finish

---

## What's next

[Tutorial 01: Bring in your first source](01-bring-in-your-first-source.md) — capture a real source of your own, judge its candidate card, and write its source note in your own words.

**See also:** [Quickstart](../how-to-guides/setup/quickstart.md) for the condensed install path, and [What Memoria is](../explanation/overview/what-memoria-is.md) for what you just installed.

---

[Tutorial 01: Bring in your first source](01-bring-in-your-first-source.md) →
