---
topic: roadmap
---

# Implementation roadmap

This document is the phased plan for taking Memoria from design to running system. It assumes the design choices in [vision.md](../../explanation/vision.md) through [obsidian-ui/README.md](../../explanation/obsidian-ui/README.md) are settled.

The roadmap is ordered so each phase produces a working, useful slice. You should not need to complete phase 4 before phase 1 is paying off.

## How this folder is organized

The narrative spine (Memoria v0.1, configuration tiers, expansion-threshold rule, what to defer, success metrics) stays here. The substantive content — timeline, decisions, deployment, future directions, pilots — lives in dedicated files alongside this README.

| File | What it covers |
|---|---|
| [timeline.md](timeline.md) | Week-by-week ramp from Memoria v0.1 to production; the six implementation phases (naming, vault structure, profiles, board, pilot corpus, scale) |
| [deployment-options.md](deployment-options.md) | Four deployment patterns (`local-only`, `local-mesh`, `obsidian-sync`, `always-on`); secondary-device patterns; per-device install sets |
| [secret-management.md](secret-management.md) | `.env` vs Bitwarden Secrets Manager; when not to centralize |
| [sync-and-coordination.md](sync-and-coordination.md) | The 5–15 second sync window; `.agent-lock` write-coordination; bib watcher |
| [skill-governance.md](skill-governance.md) | **(deferred)** Skill state machine (intake → archived); registry; onboarding checklist; passthrough-to-dedicated graduation |
| [standard-cron-tasks.md](standard-cron-tasks.md) | The four standard scheduled tasks; `cron_mode` migration order |
| [design-tensions.md](design-tensions.md) | Five tensions that won't resolve cleanly (autonomy/control, schema strictness/flexibility, etc.) |
| [future-directions.md](future-directions.md) | Discovery loop, propagation debts, LLM-judge gate, retry reflection, literate code-notes, open-design integration, and more — each with adopt-when triggers |
| [hermes-capability-adoption.md](hermes-capability-adoption.md) | Disposition of the ~29 upstream Hermes capabilities — adopt-now / defer-to-trigger / consciously-rejected — the *platform-feature* axis complementing `future-directions.md` |
| [autonomy-progression.md](autonomy-progression.md) | The 15 within-boundary autonomy patterns from the [paper survey](../../explanation/architecture/why-pattern-provenance.md), organized as a 5-layer dependency roadmap (plus the orthogonal Coder-lane exception). Cross-cuts `future-directions.md`. |
| [success-metrics.md](success-metrics.md) | Time-from-capture-to-claim, promotion rate, review backlog, orphan rate, reuse rate |
| [evaluation.md](evaluation.md) | Two-layer evaluation (vault-native gold set + external benchmarks by adoption mode); the design changes the benchmark review warrants (claim supersession, verify entailment, reasoning-augmented query); and what the literature validates |
| [evaluation-benchmarks.md](evaluation-benchmarks.md) | The full capability-mapped benchmark taxonomy: scoping principles, per-capability tables (arXiv IDs, verdicts, repos, adoption mode), out-of-scope categories, and the suggested minimal suite |
| [profile-compilation.md](profile-compilation.md) | **(deferred)** Kustomize-style profile compiler — `memoria-base` + per-profile overrides, build-time validation, drift detection (forward-looking; not the current direct-managed model) |
| [decisions/](../decisions/) | 30 numbered decision records (ADRs 1–30); see [decisions/README.md](../decisions/README.md) for the index |
| [pilots/](pilots/) | Active pilots with explicit rollback criteria. Currently: [E1 — Open Notebook as comparative-brief back-end](pilots/01-open-notebook.md) |
| [non-llm-tools.md](non-llm-tools.md) | The non-LLM tools that Memoria uses to do its job, and the jobs they do |

## Memoria v0.1

Memoria v0.1 is the full system on a **single device** (`local-only` deployment) — board, all profiles, all folders, all templates, all schema fields, all workflows, all dashboards. Stand it up completely from day 1. Every component below is load-bearing; omitting any of them creates gaps that are harder to backfill than to wire up correctly at the start. Multi-device is a Phase 3 expansion — see [deployment-options.md](deployment-options.md).

| Layer | Standard (Memoria v0.1) |
| --- | --- |
| **Deployment** | Single device, `local-only` |
| **Tools** | Zotero + Better BibTeX, Obsidian, Hermes (terminal), Git, Kanban board, ACP plugins, K-Dense skills |
| **Folders** | All: `00-meta/`, `10-inbox/`, `20-sources/` (papers, items, entities), `30-synthesis/` (claims, reference, MOCs), `40-workbench/`, `50-deliverables/`, `90-assets/`, `95-archive/` |
| **Templates** | All 15: answer, canvas, claim, code, deliverable, draft, fleeting, item, moc, organization, paper, person, project, reference, venue |
| **Schema fields** | All: `type`, `lifecycle`, `maturity`, `topic`, `projects`, `added`, `pub_status`, `full_text_reviewed`, `_proposed_classification`, `_enrichment`, MOC fields |
| **Workflow** | Full pipeline: ingest → classify → enrich → claim note → find → MOCs → code artifacts → Canvas → deliverables |
| **Dashboards** | Full suite: all 10 dashboards + `index.md` |
| **Profiles** | Seven-profile (full): Librarian, Mapper, Socratic, Writer, Verifier, Coder, Linter |

**The rule:** stand up the complete system on one machine first, then let corpus density drive which workflows activate and device count drive whether you expand. Don't pre-activate MOCs or advanced workflows without corpus density, and don't add a second device before the single-device system is stable.

## Implementation paths: configuration tiers

The system ships as a single, complete configuration. The only axis that varies is how much of the Kanban board and automation you activate during initial weeks:

| Path | Profiles | When to use |
| --- | --- | --- |
| **Seven-profile (standard)** | Librarian, Mapper, Socratic, Writer, Verifier, Coder, Linter — all installed from day 1. | The default. All permission boundaries and review gates active from the first ingest. |
| **Mode-based (fallback)** | One Hermes, with per-run `mode: ingest \| synthesize \| verify \| maintain`. | Only if Hermes profile wiring is blocked (e.g., v0.2 config files not yet shipped). Weakest safety properties; migrate to seven-profile as soon as the wiring lands. |

The target is always seven-profile. Mode-based is a temporary fallback while the v0.2 install wiring is being completed, not a long-term operating mode.

## Expansion threshold discipline

A general rule for adding structure:

> Add new structure only when the corpus justifies it. Introduce new MOCs, subagents, dashboards, vocabularies, or note types only when recurring work makes the added complexity worthwhile.

Concrete thresholds:

- **New MOC**: when a topic has ≥ 15–20 notes (papers + claim notes combined) that share it — the topic-MOC threshold in [linking-patterns.md](../../reference/linking-patterns.md#moc-creation-thresholds).
- **New subagent / profile**: when an existing profile is consistently overloaded *and* the overload comes from a distinct concern.
- **New dashboard**: when a recurring question is answered by ad-hoc grep more than 3 times.
- **New vocabulary or note type**: when at least 5 existing notes are forcing themselves into a wrong-shaped slot.

Below these thresholds, prefer to live with the friction.

## What to defer

Things that *sound* useful but should not be in the initial build:

- Cross-vault federation (multi-vault sync) — adds complexity disproportionate to benefit.
- Auto-generated reference notes from claim clusters — too easy to produce polished-but-untrusted content.
- Tree-search experiment automation — wrong domain for a knowledge-work system.
- A web UI — Obsidian is the UI.
- Real-time multi-user collaboration — Memoria is single-user by design.

If any of these become genuinely needed, they belong in a future major version, not in the initial roadmap.
