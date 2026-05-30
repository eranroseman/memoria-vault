---
topic: obsidian-ui
---

# Dashboards

Dashboards are the operational view layer — Dataview-rendered notes that surface what is in flight on the board, what is overdue in the vault, and what needs human judgment.

Each dashboard lives in its own file under [`dashboards/`](../../explanation/dashboards/). The vault implementation places these in `00-meta/01-dashboards/`.

## Dashboards by use frequency

Every dashboard except `skill-lifecycle` (deferred) exists in the vault. The question is how often it's opened.

| Frequency | Dashboard | Purpose |
| --- | --- | --- |
| **Daily** | [Daily Health](../../explanation/dashboards/daily-health.md) (ships in vault as `00-meta/01-dashboards/index.md`) | Always-on health monitor. Open before any large operation. |
| **Reading session** | [`discuss-queue`](../../explanation/dashboards/discuss-queue.md) | "What should I think about today?" — paper notes classified but not yet processed via Socratic. The upstream-discipline dashboard. |
| **Weekly** | [`weekly-review`](../../explanation/dashboards/weekly-review.md) | Weekly ritual entry point (see [workflows/README.md](../../how-to/workflows/README.md) workflow Lint). |
| **Weekly** | [`reading-pipeline`](../../explanation/dashboards/reading-pipeline.md) | "What to read next?" — papers by processing stage. |
| **Weekly** | [`loose-ends`](../../explanation/dashboards/loose-ends.md) | Catch TODO / tmp / untitled filenames and leftover junk — no `draft`. |
| **Weekly** | [`drift-watch`](../../explanation/dashboards/drift-watch.md) | Linter's structural detector findings + [verdict band](../glossary.md#observability-and-verdicts). Open when the lint pass passed but something still feels off. |
| **Per board op** | [`board-state`](../../explanation/dashboards/board-state.md) | Active cards, review queue, retry watch. |
| **Forensic** | [`audit-log`](../../explanation/dashboards/audit-log.md) | Policy-MCP write decisions. Open when something feels off. |
| **Planning** | [`open-questions`](../../explanation/dashboards/open-questions.md) | Research agenda view — surface all explicit Open Questions sections. |
| **Planning** | [`contradictions`](../../explanation/dashboards/contradictions.md) | Surface claim notes that disagree (human-set `relations.contradicts`) — a synthesis starting point. |
| **Scale-dependent** | [`skill-lifecycle`](../../explanation/dashboards/skill-lifecycle.md) | Hermes skill registry view. Deferred — maybe later if needed; see [roadmap/future-directions.md](../../project/roadmap/future-directions.md#skill-governance). |
| **Scale-dependent** | [`fleet-health`](../../explanation/dashboards/fleet-health.md) | Cost and reliability trends for the worker fleet. Phase 6 (post-MVS) — see [roadmap/future-directions.md](../../project/roadmap/future-directions.md). |

The "scale-dependent" dashboards are designed to be present from day one but only carry meaningful data once the corpus is large enough that human eyes stop noticing slow regressions. Until then they're inert.

## Design rules for dashboards

- **One decision per query.** Each query should tell the human what to do next, not just what exists.
- **Filter out the boring cases.** Exclude already-promoted, already-archived, or seedling-stage notes from active queues.
- **Sort by oldest first** in maintenance queues — the longest-stalled items are the most urgent.
- **Keep each dashboard short.** If a single dashboard has more than ~10 queries, split it into specialized dashboards.

## Performance discipline

Dataview reads Obsidian's metadata cache. Queries are usually fast, but as the vault grows past a few thousand notes, broad queries become the dominant render cost. These rules keep dashboards responsive without restructuring the vault.

- **Scope queries with `FROM "folder"`** instead of `FROM ""` (vault-wide). Use the narrowest folder that holds the candidates — e.g., `FROM "10-inbox"` for triage queues, `FROM "30-synthesis"` for promotion backlogs.
- **Keep property types stable.** If `lifecycle` is sometimes a string and sometimes a list, sort and filter behave unpredictably. Use the Linter's `safe-and-unambiguous` Templater script to coerce types on every note touch (see [profiles/linter.md](../../explanation/profiles/linter.md#implementing-safe-and-unambiguous-fixes-via-templater)).
- **Keep frontmatter compact.** Long prose belongs in the note body. Frontmatter is for fields that get queried.
- **`LIMIT` long lists.** A dashboard rarely needs more than the top 20–30 rows. Add `LIMIT 30` and trust the sort.
- **Reuse queries.** If two dashboards ask the same question, write the query once and embed it from both — duplicate queries scan the same metadata twice.
- **Prefer `TABLE` and `LIST`** over `dataviewjs` for plain frontmatter views. Drop to `dataviewjs` only when cross-record aggregation or external file I/O is needed (e.g., reading `audit.jsonl`).

A useful sanity check: open the dashboard, time it, then run the same queries on a folder-scoped version. If the folder-scoped version is twice as fast, the original was the wrong shape.

## Graceful degradation

A query depends on a field, a folder, or a decision that may not exist yet — `candidate-note` requires [Decision 21](../../project/decisions/21-shared-candidate-frontmatter.md), `lane-metric` requires the [fleet-observability aggregator](../../project/roadmap/future-directions.md#fleet-observability), `_proposed_classification` requires the Librarian to have run. A query that throws or returns an unexplained empty table when its dependency is missing is worse than the missing feature itself: it teaches the human to distrust the dashboard.

The rule:

- **Empty result + explanation beats error.** A `TABLE` that returns zero rows should be paired with a one-line markdown note explaining what would populate it. Example: "Empty until Decision 21 is adopted and a `candidate-note` template exists" (see [weekly-review](../../explanation/dashboards/weekly-review.md)).
- **Detect dependency, not absence of data.** A query on a brand-new vault returns zero rows because there is no data yet — that is the right behavior. A query that returns zero rows because the *field doesn't exist anywhere* is a capability gap, not an empty queue. The explanatory note distinguishes the two cases.
- **`dataviewjs` should guard explicit reads.** Queries that load external files (`audit.jsonl`, `state.json`) must handle the missing-file case and render a placeholder, not throw a stack trace into the dashboard.
- **Surface dependencies at the top of the dashboard.** Each dashboard's frontmatter or intro paragraph should name the decisions, files, or aggregators it depends on. If the human already knows what's missing, an empty query isn't a mystery.

This is the dashboards' version of the policy MCP's `dry_run` decision: when the gate isn't met, the system stays useful and explains itself instead of breaking quietly. The cost — a few lines of placeholder prose per dashboard — is trivial relative to the trust it preserves.

## Reference: `00-meta/04-reference/dataview-cheatsheet.md`

For dashboard authors, the vault ships with a Dataview cheatsheet at `00-meta/04-reference/dataview-cheatsheet.md` (see the [vault skeleton](../../explanation/vault/README.md#vault-skeleton-human-facing-notes)). It contains definitive examples of the patterns above — TABLE, LIST, TASK, FLATTEN, multi-field SORT, folder-scoped FROM, FILTER BY FIELD — each with a one-line "when to use" header and a runnable block.

The cheatsheet is the operational complement to this section. This document says *what discipline* to follow; the cheatsheet shows *what the syntax looks like* when writing a new dashboard. Update the cheatsheet whenever a new query pattern proves itself useful across two or more dashboards — that's the bar for promotion from "one-off" to "reference."

## What dashboards do not do

- **Not workflow automation.** They surface state; they don't change it.
- **Not the source of truth for review.** Review state is on the board, not in a query result.
- **Not a replacement for the Linter.** Lint reports identify structural issues the dashboard cannot detect (e.g., schema drift, broken links).

## Frontmatter compatibility note

The queries in each dashboard assume the frontmatter conventions in [vault/README.md](../../explanation/vault/README.md). If type names or folder paths migrate, update the queries to match — aliases (e.g., keeping `research-wiki` as a deprecated name) help during transition but the queries themselves must reflect the authoritative structure.
