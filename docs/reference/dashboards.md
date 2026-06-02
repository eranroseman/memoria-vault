---
title: Dashboards
parent: Reference
---

# Dashboards

The ten dashboards shipped in `00-meta/01-dashboards/`: source file, sort order, and what each reads. For *why* each exists and when to open it, see [explanation/dashboards/](../explanation/dashboards/) — this page is the lookup.

Dashboards are Dataview / DataviewJS views. They render existing vault state and logs; they never write. A dashboard with no data yet shows a placeholder, not an error.

---

## Dashboard inventory

| Dashboard | File | Reads from | Sort | Group |
| --- | --- | --- | --- | --- |
| Daily Health | `daily-health.md` | `board-state`, `lint-findings.jsonl`, fleet metrics, `cron-history.jsonl` (filtered subsets) | per-section | Daily glance |
| Board state | `board-state.md` | `99-system/board/` markdown card projections | by lane / queue | Daily glance |
| Reading pipeline | `reading-pipeline.md` | `20-sources/01-papers/` (`lifecycle`), `30-synthesis/01-claims/` (`maturity`) | modification time | Synthesis agenda |
| Discuss queue | `discuss-queue.md` | `20-sources/01-papers/` (`lifecycle: current`, no Socratic pass) | oldest first | Synthesis agenda |
| Open questions | `open-questions.md` | `30-synthesis/01-claims/` + `20-sources/01-papers/` (`## Open questions` sections) | most-recently-modified | Synthesis agenda |
| Contradictions | `contradictions.md` | `claim-note` `relations.contradicts` links (deduplicated pairs) | most-recently-modified | Synthesis agenda |
| Drift watch | `drift-watch.md` | `99-system/logs/lint-findings.jsonl` | by detector | Structural health |
| Loose ends | `loose-ends.md` | whole-vault filename scan (`TODO`/`tmp`/`untitled`) | most-recently-modified | Structural health |
| Weekly review | `weekly-review.md` | inbox, candidates, synthesis, orphans, projects, metrics (multi-section) | top-to-bottom workflow order | Structural health |
| Fleet health | `fleet-health.md` | `99-system/metrics/lane-metric-*` aggregates | by trust score | Operational health |
| Audit log | `audit-log.md` | `99-system/logs/audit.jsonl` (current week) | newest first, cap 30 | Operational health |

> The "Daily Health" view is the `daily-health.md` dashboard (Obsidian has no special "index" file, so it's named for what it is).

---

## Verdict band (drift-watch, surfaced on Daily Health)

Rollup of the Linter's eight structural detectors:

| Band | Condition | Effect |
| --- | --- | --- |
| `PASS` | No HIGH or CRITICAL findings | — |
| `REVIEW` | MEDIUM findings present, no HIGH | Advisory |
| `FAIL` | Any HIGH or CRITICAL finding | Scheduled work pauses until resolved |

Daily Health shows only the last-24h HIGH/CRITICAL subset; drift-watch shows the full per-detector view.

---

## Trust score (fleet-health, surfaced on Daily Health)

A 0–100 composite per lane. Inputs: audit deny rate, structural-drift incidents, secret-field access attempts, retry rate, success rate, and (for lanes producing `[!suggestions]`) accept/reject ratios. No single signal dominates.

| Band | Range | Action |
| --- | --- | --- |
| Healthy | 90+ | None |
| Watch | 70–89 | Something is slipping |
| Act | < 70 | Pause scheduled work for that lane |

Suggestion-ratio extremes both down-weight the score: accept rate **> ~90%** = rubber-stamping; **< ~20%** = candidate scoring needs tuning. Full formula and band definitions: [glossary.md](glossary.md).

---

## Board-state queue counters

The four sections board-state projects (also summarized on the [status line](obsidian-status-line.md)):

| Section | Shows |
| --- | --- |
| Active | Cards in `running`, per lane |
| Review queue | `done` cards with `review_status: requested` |
| Retry watch | Cards accumulating retries |
| Claim maturity | `seedling → budding → evergreen` histogram |

Board-state is a **read view** — state changes happen through Hermes commands or by editing card files, never through the dashboard. If Hermes is the sole source of truth with no markdown card export, board-state is intentionally empty (use the Hermes Workspace instead).

---

## Design rules (apply to all dashboards)

- **One decision per dashboard.** Mixed queries produce lists the human can't batch-act on.
- **Empty is success.** A healthy vault produces empty or near-empty dashboards; always-busy tables train the eye to ignore them.
- **Sort by decision type.** Queues sort oldest-first (longest-waiting acted on first); logs sort newest-first (most recent is most actionable).
- **Graceful degradation.** Missing dependency (plugin, log file, low volume) → explanatory placeholder, never an error or blank table.

---

## Query patterns (for dashboard authors)

Reference shapes for authoring dashboards. For full Dataview syntax see the [Dataview docs](https://blacksmithgu.github.io/obsidian-dataview/).

- **TABLE** — the workhorse: `TABLE file.mtime AS "Modified", lifecycle AS "Status" FROM "20-sources/01-papers" WHERE lifecycle = "proposed" SORT file.mtime DESC LIMIT 20`
- **LIST** — just links: `LIST FROM "30-synthesis/01-claims" WHERE maturity = "seedling"`
- **TASK** — inline TODOs: `TASK FROM "10-inbox" WHERE !completed`
- **FLATTEN** — one row per array item: `... FLATTEN sources AS flat-source`
- **Field presence** — `WHERE topic` (has it) · `WHERE !topic` (lacks it) · `WHERE contains(topic, "hci")`
- **dataviewjs** — only for external-file reads (logs); **must guard the load** so a missing file degrades gracefully, never throws:

  ```js
  const text = await dv.io.load("99-system/logs/audit.jsonl");
  if (!text || !text.trim()) { dv.paragraph("_No data yet._"); return; }
  const events = text.trim().split("\n").filter(Boolean).map(l => JSON.parse(l));
  ```

Common Memoria patterns: pending review (`WHERE review_status = "requested" SORT file.mtime ASC`); stale enrichment (`WHERE _enrichment AND enriched_date < date(today) - dur(30 days)`); orphan claims (`FROM "30-synthesis/01-claims" WHERE length(file.inlinks) = 0`).

## Performance

Keep dashboards responsive as the vault grows:

- **Scope `FROM "folder"`** (narrow), never `FROM ""` (vault-wide) unless truly required.
- **`LIMIT`** every query (~30); dashboards rarely need more.
- **Stable field types** — a field that is sometimes a string and sometimes a list slows (and breaks) every query that touches it.
- **Push string-parsing out of `WHERE`** into a frontmatter field.
- **Promote queried fields to top-level** (e.g. `enriched_date`, not buried in `_enrichment`).
- When one dashboard carries 10+ queries, split it into two specialized ones.

---

## Related

- Why each dashboard exists and when to open it: [explanation/dashboards/](../explanation/dashboards/)
- The structural detectors behind the verdict band: [linter.md](linter.md)
- The audit-log event schema and rotation: [memory.md](memory.md#audit-log-event-fields)
- The status-line counters board-state feeds: [obsidian-status-line.md](obsidian-status-line.md)
- Operating the dashboards: [how-to-guides/using-obsidian/navigate-the-dashboards.md](../how-to-guides/using-obsidian/navigate-the-dashboards.md)
