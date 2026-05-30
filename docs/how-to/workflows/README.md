---
topic: workflows
---

# Using the workflows

This document is the *usage* guide for Memoria's operational workflows: the named workflows you can run, how a human triggers them from inside Obsidian, the steering input that shapes them, the default operating rhythm, and the anti-patterns to avoid.

For the *design* behind the workflows — the two pipelines with full stage tables, the role × stage matrices, why the Kanban is the event bus, and why there are two pipelines rather than one — see [pipeline-design.md](../../explanation/workflows/pipeline-design.md).

For each workflow, "owner" means *who has decision authority* — not just who executes. Hermes can execute many steps; the human owns the decisions that determine whether the work moves forward.

## What's in this document

**Triggering work** — [How the human triggers work: the Command Palette](#how-the-human-triggers-work-the-command-palette), [Research directions (steering input)](#research-directions-steering-input).

**The named workflows** — [Workflow inventory](#workflow-inventory) (the 18 named workflows, grouped upstream / downstream / maintenance).

**Discipline** — [Cross-cutting ownership rules](#cross-cutting-ownership-rules), [Default operating model](#default-operating-model), [Anti-patterns](#anti-patterns).

## Workflow inventory

Workflows are listed in execution order within each pipeline. Refer to a workflow by name (e.g., "Discuss workflow", "Verify workflow") — there are no numeric IDs. Per-workflow detail lives in the [upstream/](upstream/), [downstream/](downstream/), and [maintenance/](maintenance/) subfolders.

### Upstream (9)

| Workflow | Goal | Main owner |
| --- | --- | --- |
| [Zotero Capture](upstream/zotero-capture.md) | Make Zotero the source of truth for references and PDFs. | Human |
| [Fleeting Triage](upstream/fleeting-triage.md) | Promote or discard raw captures in `10-inbox/01-fleeting/`. | Human (Linter surfaces stale ones) |
| [Find](upstream/find.md) | Find related papers, tools, people, venues worth adding. | Librarian surfaces; human confirms |
| [Ingest](upstream/ingest.md) | Create the right note in the right folder with enrichment. | Librarian; human resolves ambiguity |
| [Classify](upstream/classify.md) | Promote agent-proposed fields into canonical metadata. | Human |
| [Discuss](upstream/discuss.md) | Sharpen thinking on a classified source via Socratic conversation before writing a claim note. | Human (Socratic profile, write-denied) |
| [Distill](upstream/distill.md) | Distill literature into durable claims. | Human authors; Writer drafts |
| [Promote](upstream/promote.md) | Turn stable claim notes into reference pages. | Human; Linter may flag candidates |
| [Archive](upstream/archive.md) | Preserve deprecated material without deleting it. | Human only |

### Downstream (8)

| Workflow | Goal | Main owner |
| --- | --- | --- |
| [Assess](downstream/assess.md) | Map the corpus for a project; decide if it's ready to write. | Mapper (`scope-project`); human decides |
| [Frame](downstream/frame.md) | Generate 2–3 competing project framings before drafting; commit to one. | Writer (with `counter-outline`, scratch-only); Socratic (with `lens-reading`); human chooses |
| [Write](downstream/write.md) | Build manuscripts from synthesized knowledge (umbrella). | Human; Writer assists |
| [Verify](downstream/verify.md) | Trace draft claims back to claim notes; spawn gap cards for failed traces. | Verifier; human decides |
| [Revise](downstream/revise.md) | Close the gap-loop: address verification findings before export. | Human |
| [Export](downstream/export.md) | Run Pandoc to produce the final, frozen deliverable. | Coder runs Pandoc; human decides to ship |
| [Query](downstream/query.md) | Get a cited synthesis from the vault. | Writer / Librarian; human verifies |
| [Code](downstream/code.md) | Treat code as a research output with provenance. | Human; Coder scaffolds (external agent implements) |

### Maintenance (4)

| Workflow | Goal | Main owner |
| --- | --- | --- |
| [Lint](maintenance/lint.md) | Keep structure, links, queues healthy. | Linter; human decides on fixes |
| [Refactor](maintenance/refactor.md) | Keep notes atomic and remove duplication. | Verifier identifies; human decides |
| [Retraction Sweep](maintenance/retraction-sweep.md) | Stop retracted / superseded sources from influencing synthesis. | Verifier flags; human decides |
| [Maintain MOCs](maintenance/moc.md) | Create and grow Maps of Content as clusters mature. | Human authors; agents propose |

## How the human triggers work: the Command Palette

The board state machine, profile contracts, and lane policies are all *passive* — they describe what *can* happen. Workflows still need a *trigger*. For the daily human, that trigger is the Obsidian Command Palette.

The authoritative catalog of `Memoria:` commands (capture, processing, interactive retrieval, project, maintenance, lens-reading) and their implementation lives in [obsidian-ui/command-palette.md](../../reference/command-catalog.md). This section describes the control flow that fires whenever any command is invoked.

### Control flow

Every command follows the same six-step shape:

1. **User invokes the command** from the palette.
2. **Plugin reads frontmatter** from the active note. No business logic; just field extraction.
3. **Plugin calls the Hermes API** with a small JSON payload. No persistent state.
4. **The Hermes API translates** the call into one or more MCP tool invocations.
5. **MCP servers** validate, record, and dispatch. Policy MCP checks permissions; tasks MCP updates the board.
6. **Audit log is appended.** The decision and result are durable.

See [architecture/control-plane.md](../../explanation/architecture/control-plane.md) for the layer architecture, and [obsidian-ui/command-palette.md](../../reference/command-catalog.md) for per-command implementation (QuickAdd / Templater / Hermes API / agent-client).

If a step fails, the failure is visible at exactly one layer — the plugin shows a status notice, the Hermes API returns an HTTP error, or the MCP returns a `deny` / `dry_run` payload. There is no place for a silent failure to hide.

### Hotkey discipline

Most commands are palette-only — `Cmd-P → M → <2–3 letters>` is the primary input mode. A small set of high-frequency commands earn dedicated hotkeys or [Commander](../../explanation/obsidian-plugins/cmdr.md) buttons; see the [recommended Commander set in command-palette.md](../obsidian-ui/command-palette.md#setting-up-the-bindings) for the recommended top five. Hotkey real estate is scarce; everything outside that set stays palette-only.

### What this section is not

- **Not a plugin spec.** The TypeScript implementation and HTTP endpoint schemas live outside the design — there is no custom Memoria HTTP code. Command dispatch goes through Hermes's built-in API (`hermes gateway`), and vault read/write goes through the `obsidian-local-rest-api` community plugin. See [architecture/control-plane.md](../../explanation/architecture/control-plane.md) for the layer architecture and the Hermes MCP reference for the wire formats.
- **Not the only trigger.** Cron jobs, the discovery loop (see [roadmap/future-directions.md](../../project/roadmap/future-directions.md#the-discovery-loop)), and Hermes-side `delegate_task` all also fire workflow steps. The Command Palette is the *human-facing* channel; the others are scheduled or agent-driven.

## Research directions (steering input)

`00-meta/research-directions.md` is a single human-edited Markdown file that tells Hermes what to weight. It is not a rule (`AGENTS.md`) or a vocabulary (`schema-decisions.md`) — it's a *steering* file. The agent reads it at session start and uses it to prioritize discovery queries and flag relevance during classify.

### What goes in it

Four sections, updated weekly (or whenever priorities shift):

```markdown
## Current research priorities
- Deepen the receptivity-detection literature
- Map the JITAI timing-effects debate

## Open questions
- Does cognitive load moderate JITAI timing effects?
- Is there evidence linking sensemaking practices to JITAI design?

## Synthesis gaps
- Topics with literature but no claim notes:
  - therapeutic alliance in digital coaching
  - implementation science for mHealth

## Papers to prioritize in discovery
- Anything citing mamykina2010sense
- Recent CHI / CSCW work on JITAI receptivity
```

### How Hermes uses it

- **At session start** every profile reads `research-directions.md` and surfaces it as context for the session.
- **In `find`** the Librarian weights candidate generation toward priorities and listed authors.
- **In `classify`** the human weights `_proposed_classification` proposals against listed projects and topics. (The Librarian already proposed the proposed fields; weighting them against priorities is a human judgment.)
- **In `draft`** the Writer cites it as the active research agenda — answer notes that don't address any listed priority are flagged for human review.
- **In `scope-project`** the Mapper treats the priorities list as a relevance signal when computing the corpus map.

### Maintenance

- Update weekly during the dashboard ritual (step 0).
- A stale directions file is worse than none — it pulls the agent toward yesterday's priorities. Delete sections that have shipped.
- Keep it short — under ~200 words per section. The agent reads it as context, not as a long brief.

### Why a file, not just frontmatter or tags

The current schema encodes *what notes are about* (frontmatter). The directions file encodes *what the human is working on right now*. These are different. Topics persist; priorities turn over. Mixing them into a single `tags` or `topics` field loses both.

## Cross-cutting ownership rules

These rules apply across all workflows:

- **Human owns judgment.** Selection, triage, synthesis, promotion, merge / split, and archive decisions are human-owned.
- **Hermes owns bookkeeping.** Type detection, routing, enrichment, candidate generation, cross-link suggestions, linting, and session logging are agent-owned.
- **Coding agents own code execution.** The Coder scaffolds and coordinates; the implementation may be delegated to Kilocode, Aider, Claude Code, or the human depending on the task.
- **Nothing canonical is overwritten automatically.** The agent may propose, draft, or flag, but human review is the promotion gate.

## Default operating model

Memoria runs on rhythms layered by frequency. The skeleton cadence: **daily** capture and inbox skim; **twice a week** classify partial paper notes and run discovery; **weekly** the [ritual](maintenance/lint.md#weekly-ritual); **per-project** draft from `30-synthesis/01-claims/`, arrange in Canvas, and export via Pandoc. What that feels like hour-to-hour:

**Pre-morning, on phone over coffee (optional).** If overnight cron produced anything worth pushing — a retry threshold hit, a drift alarm, a substantive ingest summary — Telegram pushed a notification before the human opened the vault. Example: *"Overnight: 3 sources ingested, 12 link suggestions ready, 1 retry threshold hit on card-2026-05-26-042 (Librarian timeout fetching DOI for Tanaka 2024)."* The human glances, notes anything blocking, deals with it at the desk. If nothing pushed, nothing demands attention before opening the vault — that's the design.

**Morning glance (5–10 minutes).** Open the vault. The Human workspace appears by default (`Cmd-1`). Glance at [Daily Health](../../explanation/dashboards/daily-health.md): is any section red? Today's queue, drift signals, lane health, cron status. Most days nothing is red, and Daily Health closes again. If link suggestions accumulated overnight from Librarian's enrichment work, bulk-approve the ones that look right via `Memoria: approve all link suggestions` (see [command-palette.md](../../reference/command-catalog.md#maintenance-3-commands)). For retries flagged in the Telegram push, drop to CLI: `hermes kanban show <card-id>` to inspect, fix the underlying issue, `hermes kanban unblock <card-id>` to release it back to `ready` (re-dispatch resets the retry count). Total time: under ten minutes unless something demands attention.

**Reading session (1–2 hours, when scheduled).** Switch to the Reading & Processing workspace (`Cmd-2`). Open [`discuss-queue.md`](../../explanation/dashboards/discuss-queue.md): which paper note is ripest for processing? Read the source with the `[!brief]` callout in mind. When ready to process, ask Socratic about the active note (`Cmd-P → Memoria: ask about this note`) — the ACP pane opens on the right with the Socratic profile, which is architecturally write-denied. The conversation runs; the human writes the claim note themselves in `30-synthesis/01-claims/` (in their own words, in the left pane) as the conversation progresses. Save. The git hook fires; Librarian's enrichment runs overnight; the link suggestions appear in tomorrow's morning glance.

**Walking (whenever a thought hits).** Telegram: `/fleeting <thought>` drops the text into `10-inbox/01-fleeting/` with a timestamp. The thought is captured; the human doesn't have to remember it through to the next desk session. It surfaces in tomorrow's [`reading-pipeline.md`](../../explanation/dashboards/reading-pipeline.md) (or the weekly fleeting-triage step) for action. Source-URL capture works the same way: paste the link, get a confirmation, the actual ingest happens overnight.

**Writing session (project work).** Switch to the Drafting workspace (`Cmd-3`). Open the draft. The `[!verification]` callout at the top shows Verifier's last claim-trace report. Write. The Writer ACP pane is available on the right if local critique is wanted, but it's optional — most drafting happens in the human's head, with the pane silent. On significant edits, save and `git commit`. Verifier picks up the draft automatically ([Verify](downstream/verify.md)). Gap cards from Verifier appear in tomorrow's morning queue. If the gap loop suggests more reading before the draft can stabilize, switch back to a reading session.

**Friday ritual (90 minutes).** The [weekly ritual](maintenance/lint.md#weekly-ritual). Top to bottom in `weekly-review.md`.

**Evening (passive).** If the Linter's weekly drift sweep ran on schedule, Telegram pushes a short confirmation: *"Drift report for the week is ready."* If verdict is `PASS` (green), the human glances and ignores. If `REVIEW` or `FAIL`, the message is the signal to open [`drift-watch.md`](../../explanation/dashboards/drift-watch.md) next desk session. The push exists so the human knows the sweep happened — silence would be indistinguishable from a missed cron run.

**What the human does NOT do:**

- Manage agent state by hand. The Kanban dispatches; the human approves or redirects via card transitions.
- Re-decide policy questions. The lane-overrides and the policy MCP encode them once.
- Hunt for files. Folders encode lifecycle; search finds the rest.
- Switch between mental models for "what tool am I using." One vault, one keyboard, one set of Memoria commands.

If after three months of use the human's mouse hand barely moves and they've stopped consciously tracking which workspace they're in, the rhythm is right. The board surfaces what's stalled; the dashboards surface what's overdue.

## Anti-patterns

- **Skipping classification.** Letting auto-proposed classification become canonical without review. Symptom: drift between what the vault claims and what the literature actually says.
- **Distilling without source citation.** Claim notes that don't trace to a paper note. Symptom: the vault remembers claims it cannot defend.
- **Promoting before stability.** Moving a note to `30-synthesis/02-reference/` before it's evergreen. Symptom: reference pages that keep changing.
- **Treating archive as delete.** Archived notes are preserved for traceability; they should not be removed.
- **Running find without a corpus boundary.** Generates noise that never gets classified. Symptom: `10-inbox/03-candidates/` grows without bound.
- **Crossing pipelines mid-task.** Mixing upstream (classify, distill) work with downstream (draft, export) work in the same session. Each pipeline has its own rhythm; mixing them produces drafts that re-litigate filing decisions.
