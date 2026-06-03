---
title: How-to guides
nav_order: 3
has_children: true
permalink: /how-to-guides/
---

# How-to guides

Task-oriented recipes for getting specific things done with Memoria. Each guide assumes you already know the system — if you're new, start with the [Tutorials](../tutorials/).

For the *why* behind any design choice, see [Explanation](../explanation/). For exact field names, schemas, and command flags, see [Reference](../reference/).

---

## Two operating modes

Memoria has two distinct modes of use, each with its own tooling:

**Day-to-day use — Obsidian is the UI.**
Reading, classifying, discussing, distilling, drafting, and reviewing all happen inside Obsidian. The command palette and agent-client pane are your primary controls. The guides in [Sources](sources/) and [Writing](writing/) are written for this mode.

**Setup and maintenance — terminal (Linux/Ubuntu, WSL2, or PowerShell).**
Installing profiles, configuring environments, rebuilding indexes, and recovering from failures happen in the terminal. The guides in [Setup](setup/), [Maintenance](maintenance/), and [Recovery](recovery/) are written for this mode.

---

## Guide map

### Setup

One-time configuration tasks. Run once per machine or after a major system change.

| Guide | What it covers |
| --- | --- |
| [Quickstart](setup/quickstart.md) | Five-step fast path for a new machine |
| [Set up the vault](setup/set-up-the-vault.md) | Clone the repo and run the install script |
| [Set up Obsidian](setup/set-up-obsidian.md) | Open the vault and install required plugins |
| [Set up Zotero](setup/set-up-zotero.md) | Better BibTeX, citekey format, autosync to `.bib` |
| [Set up Hermes](setup/set-up-hermes.md) | Install profiles and fill `.env` secrets |
| [Configure project hints](setup/configure-project-hints.md) | Optional per-project topic hints for Librarian classification |
| [Set up the messaging gateway](setup/set-up-messaging.md) | Telegram capture for mobile fleeting notes |
| [Set up a VPS for always-on operation](setup/set-up-vps.md) | Move Hermes to a persistent server with systemd + Syncthing |
| [Add a second vault](setup/add-a-second-vault.md) | Fork the starter for a separate project |

### Using Obsidian

| Guide | What it covers |
| --- | --- |
| [Vault homepage](using-obsidian/use-the-vault-homepage.md) | Open the front door, navigate dashboards, update research focus |
| [Navigate the dashboards](using-obsidian/navigate-the-dashboards.md) | Which dashboard to open for each situation, workspace shortcuts |
| [Workspaces](using-obsidian/use-workspaces.md) | Set up and switch between the three cognitive-mode workspace layouts |
| [Agent-client pane](using-obsidian/use-the-acp-pane.md) | Open the pane, select profiles, attach context, read responses, clear sessions |
| [Command palette](using-obsidian/obsidian-command-palette.md) | Set up QuickAdd entries, invoke commands by type, assign hotkeys |

### Using Hermes Agent

Operational guides for the Hermes CLI — profile management, chat sessions, and configuration. These cover the tasks that happen in the terminal, not in Obsidian.

| Guide | What it covers |
| --- | --- |
| [Configure a profile](using-hermes-agent/configuration.md) | Model routing, write permissions, skills, API keys |
| [Chat with Hermes](using-hermes-agent/chat-with-hermes.md) | Start a session, run skill commands, use dry-run mode |

Administrative CLI commands (profile list/install, kanban management, skills, cron) are reference material: [Hermes CLI](../reference/hermes-cli.md).

### Sources (Compile)

Day-to-day tasks for moving sources from discovery to durable knowledge. Performed inside Obsidian.

| Guide | What it covers | Cycle stage |
| --- | --- | --- |
| [Find new sources](sources/find-new-sources.md) | Forward/backward citation search, concept queries, candidate queue | Find |
| [Triage fleeting notes](sources/triage-fleeting-notes.md) | Clear `10-inbox/01-fleeting/`: promote, attach, or discard | Triage (on-ramp) |
| [Capture and ingest a source](sources/capture-and-ingest.md) | Zotero → vault: the complete intake path | Capture + Enrich |
| [Classify a source](sources/classify-a-source.md) | Review proposed metadata and promote to canonical | Classify |
| [Pin a citekey](sources/pin-a-citekey.md) | Lock the Better BibTeX key before ingest so it never drifts | Capture (prep) |
| [Discuss a paper](sources/discuss-a-paper.md) | Socratic session via the agent-client pane | Discuss |
| [Read a paper through a Socratic lens](sources/read-through-a-lens.md) | Question a paper through a named theoretical frame | Discuss |
| [Write a claim note](sources/write-a-claim-note.md) | Distill a source into a durable claim | Distill |
| [Link related claims](sources/link-related-claims.md) | Add typed `supports` / `contradicts` relations between claims | Link |
| [Review link suggestions](sources/review-link-suggestions.md) | Triage the Librarian's `[!suggestions]` callout — approve / reject candidate links | Link |
| [Promote a claim to canonical reference](sources/promote-a-claim.md) | Move evergreen claims to `30-synthesis/02-reference/` | Maintenance |
| [Archive a source](sources/archive-a-source.md) | Retire an outdated or superseded source | Maintenance |
| [Run a systematic review](sources/run-a-systematic-review.md) | PRISMA-compliant protocol → screening → ingest for defensible literature searches | Screen (opt-in) |

### Writing (Compose)

Day-to-day tasks for turning accumulated knowledge into written output. Performed inside Obsidian.

| Guide | What it covers | Cycle stage |
| --- | --- | --- |
| [Start a writing project](writing/start-a-writing-project.md) | Scaffold a workbench project folder | — |
| [Assess your corpus](writing/assess-your-corpus.md) | Mapper corpus map: dense clusters, thin coverage, gaps | Assess |
| [Frame a project](writing/frame-a-project.md) | Generate competing outlines, choose one framing | Frame |
| [Use canvas for argument mapping](writing/use-canvas-for-argument-mapping.md) | Arrange claim notes spatially to find argument structure before drafting | Canvas |
| [Query the vault](writing/query-the-vault.md) | Ask a question, get a cited synthesis in your inbox | Query (aid) |
| [Draft with the Writer](writing/draft-with-writer.md) | Use the Writer profile for prose and outlines | Draft |
| [Verify and revise a draft](writing/verify-and-revise.md) | Run Verify, read the callout, close gaps | Verify ⇄ revise |
| [Work the review queue](writing/work-the-review-queue.md) | Approve or reject agent writes held at the review gate | Review (gate) |
| [Export a draft](writing/export-a-draft.md) | Pandoc export to Word, PDF, or plain Markdown | Export |
| [Create a code artifact](writing/create-a-code-artifact.md) | Scaffold a code-note and delegate to an external coding agent | Code (branch) |

### Maintenance

Recurring operational tasks. Run on a schedule or when prompted by a failure.

| Guide | What it covers |
| --- | --- |
| [Run the weekly review](maintenance/run-the-weekly-review.md) | Friday ritual: classify debt, promote claims, run lint |
| [Run the Linter](maintenance/run-the-linter.md) | On-demand or scheduled structural health check |
| [Refactor claim notes](maintenance/refactor-a-note.md) | Merge near-duplicates or split compound claims using the Verifier |
| [Build a Map of Content](maintenance/build-a-moc.md) | Create a navigational hub when a claim cluster crosses 15–20 notes |
| [Manage your topic vocabulary](maintenance/manage-vocabulary.md) | Add terms, rename safely, prune the active list |
| [Run a retraction sweep](maintenance/run-a-retraction-sweep.md) | Check ingested papers against retraction registries; update affected claims |
| [Run a schema migration](maintenance/run-a-schema-migration.md) | Rewrite a frontmatter field across many notes, dry-run first |
| [Redeploy profiles](maintenance/redeploy-profiles.md) | Push vault source edits out to `~/.hermes/profiles/` |
| [Rebuild the search index](maintenance/rebuild-the-search-index.md) | Re-run `qmd embed` when Writer search returns stale results |
| [Return to work](maintenance/return-to-work.md) | Three pre-session checks after any break — takes under two minutes |

### Recovery

Detect-Fix-Verify recipes for specific failures. Each guide covers exactly one failure mode.

| Guide | What it covers |
| --- | --- |
| [Safe mode](recovery/safe-mode.md) | Minimal working paths for ingest, triage, and export when optional tooling is down |
| [Fix a stuck card](recovery/fix-stuck-card.md) | Card won't advance on the Kanban board |
| [Fix broken frontmatter](recovery/fix-broken-frontmatter.md) | YAML parse error; note missing from Dataview queries |
| [Diagnose a denied or blocked write](recovery/diagnose-a-denied-write.md) | Trace a missing write: policy denial vs. wiring failure |
| [Fix a stale `.bib`](recovery/fix-stale-bib.md) | Citekey not found at ingest |
| [Fix profile drift](recovery/fix-profile-drift.md) | Deployed profile doesn't match vault source |
