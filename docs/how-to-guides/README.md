---
title: How-to guides
nav_order: 3
has_children: true
permalink: /how-to-guides/
---

# How-to guides

Task-oriented recipes for getting specific things done with Memoria. Each guide assumes you already know the system — if you're new, start with the [Tutorials](../tutorials).

For the *why* behind any design choice, see [Explanation](../explanation). For exact field names, schemas, and command flags, see [Reference](../reference).

---

## Two operating modes

Memoria has two distinct modes of use, each with its own tooling:

**Day-to-day use — Obsidian is the UI.**
Reading, classifying, discussing, distilling, drafting, and reviewing all happen inside Obsidian — the command palette, the Co-PI's agent-client pane, and the Inbox are your primary controls. The guides in [Sources](compile), [Writing](compose), and [Curate](curate) are written for this mode.

**Setup and maintenance — terminal (Linux/Ubuntu, WSL2, or PowerShell).**
Installing profiles, configuring environments, rebuilding indexes, and recovering from failures happen in the terminal. The guides in [Setup](setup), [Operate](operate), and [Troubleshooting](troubleshooting) are written for this mode.

---

## Guide map

### Setup

One-time configuration tasks. Run once per machine or after a major system change.

| Guide | What it covers |
| --- | --- |
| [Quickstart](setup/quickstart.md) | Five-step fast path for a new machine |
| [Set up the vault](setup/set-up-the-vault.md) | Run the bootstrap installer and git-init the runtime vault |
| [Set up Obsidian](setup/set-up-obsidian.md) | Open the vault and activate the bundled plugins |
| [Set up Zotero](zotero/set-up-zotero.md) | Better BibTeX, citekey format, autosync to `.bib` |
| [Set up Hermes](setup/set-up-hermes.md) | Fill `.env` secrets and propagate them into the five profiles |
| [Configure project hints](setup/configure-project-hints.md) | Optional per-project topic hints for Librarian classification |
| [Set up messaging](setup/set-up-messaging.md) | Telegram capture for mobile fleeting notes — deferred ([#382](https://github.com/eranroseman/memoria-vault/issues/382)) |
| [Set up a VPS](setup/set-up-vps.md) | Always-on Hermes with systemd + Syncthing — deferred ([#383](https://github.com/eranroseman/memoria-vault/issues/383)) |
| [Add a second vault](setup/add-a-second-vault.md) | Fork the starter for a separate project |

### Using Obsidian

| Guide | What it covers |
| --- | --- |
| [Vault homepage](using-obsidian/use-the-vault-homepage.md) | Open the front door, work the Inbox, update research focus |
| [Navigate the dashboards](using-obsidian/navigate-the-dashboards.md) | Which dashboard to open for each situation, and which workspace carries it |
| [Workspaces](using-obsidian/use-workspaces.md) | Load and switch between the three shipped pane layouts — Desk, Library, and Studio |
| [Agent-client pane](using-obsidian/use-the-acp-pane.md) | Open the Co-PI pane, attach context, read responses, clear sessions |
| [Command palette](using-obsidian/obsidian-command-palette.md) | The shipped `Memoria:` capture and per-task commands, invoking by type, assigning hotkeys |

### Using Hermes Agent

Operational guides for the Hermes CLI — profile management, chat sessions, and configuration. These cover the tasks that happen in the terminal, not in Obsidian.

| Guide | What it covers |
| --- | --- |
| [Configure a profile](hermes-agent/configuration.md) | Model routing, write permissions, skills, API keys |
| [Run a CLI chat session](hermes-agent/chat-with-hermes.md) | The Co-PI from the terminal; lane chats as a debugging posture |

Administrative CLI commands (profile list/install, kanban management, skills, cron) are reference material: [Hermes CLI](../reference/hermes-cli.md).

### Sources (Compile)

Day-to-day tasks for moving sources from discovery to durable knowledge. Performed inside Obsidian.

| Guide | What it covers | Cycle phase |
| --- | --- | --- |
| [Find new sources](compile/find-new-sources.md) | Forward/backward citation search, concept queries, candidate cards | Find |
| [Triage fleeting notes](compile/triage-fleeting-notes.md) | Clear `notes/fleeting/`: promote, attach, or discard | Triage (on-ramp) |
| [Capture and ingest a source](compile/capture-and-ingest.md) | Palette/Zotero capture → Catalog entity + candidate card: the complete intake path | Capture + Enrich |
| [Classify a source](compile/classify-a-source.md) | Handle classify flags, review what the automation applied, promote proposals | Classify |
| [Discuss a paper](compile/discuss-a-paper.md) | A questioning pass with the Co-PI in the agent-client pane | Discuss |
| [Read a paper through a lens](compile/read-through-a-lens.md) | Question a paper through a named theoretical frame | Discuss |
| [Write a claim note](compile/write-a-claim-note.md) | Distill a source into a durable claim | Distill |
| [Link related claims](compile/link-related-claims.md) | Add typed `supports` / `contradicts` relations between claims | Connect |
| [Review link suggestions](compile/review-link-suggestions.md) | Triage link-lane candidate cards — approve / reject proposed links | Connect |
| [Advance a claim to evergreen](compile/promote-a-claim.md) | Mark a settled claim by advancing its `maturity` — no move, no folder | Maintenance |
| [Archive a source](compile/archive-a-source.md) | Retire a source with `lifecycle: archived` — a state, not a folder | Maintenance |
| [Run a systematic review](compile/run-a-systematic-review.md) | PRISMA-compliant protocol → screening → ingest for defensible literature searches | Screen (opt-in) |

### Writing (Compose)

Day-to-day tasks for turning accumulated knowledge into written output. Performed inside Obsidian.

| Guide | What it covers | Cycle phase |
| --- | --- | --- |
| [Start a writing project](compose/start-a-writing-project.md) | What to build today; the project workflow ships in v0.1.0-alpha.3 | — |
| [Assess your corpus](compose/assess-your-corpus.md) | Delegate a `map` task: dense clusters, thin coverage, gaps | Assess |
| [Frame a project](compose/frame-a-project.md) | Generate competing outlines, choose one framing | Frame |
| [Use canvas for argument mapping](compose/use-canvas-for-argument-mapping.md) | Arrange claim notes spatially to find argument structure before drafting | Sketch |
| [Query the vault](compose/query-the-vault.md) | Ask the Co-PI, get a cited synthesis from your own notes | Query (aid) |
| [Draft with the Writer](compose/draft-with-writer.md) | Delegate prose and outlines to the Writer's `draft` lane | Draft |
| [Verify and revise a draft](compose/verify-and-revise.md) | Delegate a `verify` pass, read the findings, close gaps | Verify |
| [Work the review queue](compose/work-the-review-queue.md) | Approve or reject agent writes held at the review gate | Review (gate) |
| [Export a draft](compose/export-a-draft.md) | Pandoc export to Word, PDF, or plain Markdown | Export |
| [Create a code artifact](compose/create-a-code-artifact.md) | Scaffold a code-note and delegate to the Engineer's `code` lane | Code (branch) |

### Curate

Human curation of the knowledge base — recurring rituals performed inside Obsidian.

| Guide | What it covers |
| --- | --- |
| [Run the weekly review](curate/run-the-weekly-review.md) | Friday ritual: classify debt, synthesis agenda, structural health |
| [Refactor claim notes](curate/refactor-a-note.md) | Merge near-duplicates or split compound claims |
| [Build a hub](curate/build-a-moc.md) | Create a navigational hub when a claim cluster crosses 15–20 notes |
| [Manage your topic vocabulary](curate/manage-vocabulary.md) | Add terms, rename safely, prune the active list |
| [Return to work](curate/return-to-work.md) | Three pre-session checks after any break — takes under two minutes |

### Operate

Terminal-side system upkeep. Run on a schedule or when prompted by a failure.

| Guide | What it covers |
| --- | --- |
| [Run the Linter](operate/run-the-linter.md) | On-demand or scheduled structural health check — an engine, not an agent |
| [Run a retraction sweep](operate/run-a-retraction-sweep.md) | Check ingested papers against retraction registries; update affected claims |
| [Run a schema migration](operate/run-a-schema-migration.md) | Rewrite a frontmatter field across many notes, dry-run first |
| [Redeploy profiles](operate/redeploy-profiles.md) | Push vault source edits out to `~/.hermes/profiles/` |
| [Rebuild the search index](operate/rebuild-the-search-index.md) | Re-run the `qmd` embedding when vault search returns stale results |

### Recovery

Detect-Fix-Verify recipes for specific failures. Each guide covers exactly one failure mode.

| Guide | What it covers |
| --- | --- |
| [Safe mode](troubleshooting/safe-mode.md) | Minimal working paths for ingest, triage, and export when optional tooling is down |
| [Fix a stuck card](troubleshooting/fix-stuck-card.md) | Card won't advance on the Kanban board |
| [Fix broken frontmatter](troubleshooting/fix-broken-frontmatter.md) | YAML parse error; note missing from Dataview queries |
| [Diagnose a denied or blocked write](troubleshooting/diagnose-a-denied-write.md) | Trace a missing write: policy denial vs. wiring failure |
| [Fix a stale .bib](zotero/fix-stale-bib.md) | Citekey not found at ingest |
| [Fix profile drift](troubleshooting/fix-profile-drift.md) | Deployed profile doesn't match vault source |
