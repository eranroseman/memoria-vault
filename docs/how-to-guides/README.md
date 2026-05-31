
# How-to guides

Task-oriented recipes for getting specific things done with Memoria. Each guide assumes you already know the system — if you're new, start with the [tutorials](../tutorials/).

For the *why* behind any design choice, see [explanation](../explanation/). For exact field names, schemas, and command flags, see [reference](../reference/).

---

## Two operating modes

Memoria has two distinct modes of use, each with its own tooling:

**Day-to-day use — Obsidian is the UI.**
Reading, classifying, discussing, distilling, drafting, and reviewing all happen inside Obsidian. The command palette and agent-client pane are your primary controls. The guides in [sources/](sources/) and [writing/](writing/) are written for this mode.

**Setup and maintenance — Hermes CLI and PowerShell.**
Installing profiles, configuring environments, rebuilding indexes, and recovering from failures happen in the terminal. The guides in [setup/](setup/), [maintenance/](maintenance/), and [recovery/](recovery/) are written for this mode.

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
| [Set up the messaging gateway](setup/set-up-messaging.md) | Telegram capture for mobile fleeting notes |
| [Add a second vault](setup/add-a-second-vault.md) | Fork the starter for a separate project |

### Using Obsidian

| Guide | What it covers |
| --- | --- |
| [Command palette](command-palette.md) | Set up QuickAdd entries, invoke commands by type, assign hotkeys |

### Using Hermes Agent

Operational guides for the Hermes CLI — profile management, chat sessions, and configuration. These cover the tasks that happen in the terminal, not in Obsidian.

| Guide | What it covers |
| --- | --- |
| [Chat with Hermes](hermes/chat-with-hermes.md) | Start a session, run skill commands, use dry-run mode |
| [Configure a profile](hermes/configuration.md) | Model routing, write permissions, skills, API keys |

Administrative CLI commands (profile list/install, kanban management, skills, cron) are reference material: [reference/hermes-admin.md](../reference/hermes-admin.md).

### Sources (upstream)

Day-to-day tasks for moving sources from discovery to durable knowledge. Performed inside Obsidian.

| Guide | What it covers | Pipeline stage |
| --- | --- | --- |
| [Find new sources](sources/find-new-sources.md) | Forward/backward citation search, concept queries, candidate queue | Find |
| [Triage fleeting notes](sources/triage-fleeting-notes.md) | Clear `10-inbox/01-fleeting/`: promote, attach, or discard | Fleeting triage |
| [Capture and ingest a source](sources/capture-and-ingest.md) | Zotero → vault: the complete intake path | Zotero capture + Ingest |
| [Classify a source](sources/classify-a-source.md) | Review proposed metadata and promote to canonical | Classify |
| [Discuss a paper](sources/discuss-a-paper.md) | Socratic session via the agent-client pane | Discuss |
| [Write a claim note](sources/write-a-claim-note.md) | Distill a source into a durable claim | Distill |
| [Promote a claim to canonical reference](sources/promote-a-claim.md) | Move evergreen claims to `30-synthesis/02-reference/` | Promote |
| [Archive a source](sources/archive-a-source.md) | Retire an outdated or superseded source | Archive |

### Writing (downstream)

Day-to-day tasks for turning accumulated knowledge into written output. Performed inside Obsidian.

| Guide | What it covers | Pipeline stage |
| --- | --- | --- |
| [Query the vault](writing/query-the-vault.md) | Ask a question, get a cited synthesis in your inbox | Query |
| [Start a writing project](writing/start-a-writing-project.md) | Scaffold a workbench project folder | — |
| [Assess your corpus](writing/assess-your-corpus.md) | Mapper corpus map: dense clusters, thin coverage, gaps | Assess |
| [Frame a project](writing/frame-a-project.md) | Generate competing outlines, choose one framing | Frame |
| [Draft with the Writer](writing/draft-with-writer.md) | Use the Writer profile for prose and outlines | Write |
| [Verify and revise a draft](writing/verify-and-revise.md) | Run Verify, read the callout, close gaps | Verify + Revise |
| [Export a draft](writing/export-a-draft.md) | Pandoc export to Word, PDF, or plain Markdown | Export |
| [Create a code artifact](writing/create-a-code-artifact.md) | Scaffold a code-note and delegate to an external coding agent | Code |

### Maintenance

Recurring operational tasks. Run on a schedule or when prompted by a failure.

| Guide | What it covers |
| --- | --- |
| [Run the weekly review](maintenance/run-the-weekly-review.md) | Friday ritual: classify debt, promote claims, run lint |
| [Run the Linter](maintenance/run-the-linter.md) | On-demand or scheduled structural health check |
| [Rebuild the search index](maintenance/rebuild-the-search-index.md) | Re-run `qmd embed` when Writer search returns stale results |
| [Redeploy profiles](maintenance/redeploy-profiles.md) | Push vault source edits out to `~/.hermes/profiles/` |
| [Manage your topic vocabulary](maintenance/manage-vocabulary.md) | Add terms, rename safely, prune the active list |

### Recovery

Detect-Fix-Verify recipes for specific failures. Each guide covers exactly one failure mode.

| Guide | What it covers |
| --- | --- |
| [Fix a stale `.bib`](recovery/fix-stale-bib.md) | Citekey not found at ingest |
| [Fix broken frontmatter](recovery/fix-broken-frontmatter.md) | YAML parse error; note missing from Dataview queries |
| [Fix a stuck card](recovery/fix-stuck-card.md) | Card won't advance on the Kanban board |
| [Fix profile drift](recovery/fix-profile-drift.md) | Deployed profile doesn't match vault source |

---

## If you're looking for the old how-to folder

The `memoria-vault/docs/how-to/` folder contains the previous generation of guides — one recipe per named workflow, useful as detailed reference. These guides supersede that structure and are organized around user tasks rather than system workflows.
