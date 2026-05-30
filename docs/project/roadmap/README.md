---
topic: roadmap
---

# Implementation roadmap

This document is the phased plan for taking Memoria from design to running system. It assumes the design choices in [vision.md](../../explanation/vision.md) through [obsidian-ui/README.md](../../explanation/obsidian-ui/README.md) are settled.

The roadmap is ordered so each phase produces a working, useful slice. You should not need to complete phase 4 before phase 1 is paying off.

## How this folder is organized

The narrative spine (minimum viable system, graduated start, expansion-threshold rule, what to defer, success metrics) stays here. The substantive content — timeline, decisions, deployment, future directions, pilots — lives in dedicated files alongside this README.

| File | What it covers |
|---|---|
| [timeline.md](timeline.md) | Week-by-week ramp from MVS to production; the six implementation phases (naming, vault structure, profiles, board, pilot corpus, scale) |
| [deployment-options.md](deployment-options.md) | Four deployment patterns (`local-only`, `local-mesh`, `obsidian-sync`, `always-on`); secondary-device patterns; per-device install sets |
| [secret-management.md](secret-management.md) | `.env` vs Bitwarden Secrets Manager; when not to centralize |
| [sync-and-coordination.md](sync-and-coordination.md) | The 5–15 second sync window; `.agent-lock` write-coordination; bib watcher |
| [skill-governance.md](skill-governance.md) | **(deferred)** Skill state machine (intake → archived); registry; onboarding checklist; passthrough-to-dedicated graduation |
| [standard-cron-tasks.md](standard-cron-tasks.md) | The four standard scheduled tasks; `cron_mode` migration order |
| [design-tensions.md](design-tensions.md) | Five tensions that won't resolve cleanly (autonomy/control, schema strictness/flexibility, etc.) |
| [future-directions.md](future-directions.md) | Discovery loop, propagation debts, LLM-judge gate, retry reflection, literate code-notes, open-design integration, and more — each with adopt-when triggers |
| [autonomy-progression.md](autonomy-progression.md) | The 15 within-boundary autonomy patterns from the [paper survey](../../explanation/architecture/why-pattern-provenance.md), organized as a 5-layer dependency roadmap (plus the orthogonal Coder-lane exception). Cross-cuts `future-directions.md`. |
| [success-metrics.md](success-metrics.md) | Time-from-capture-to-claim, promotion rate, review backlog, orphan rate, reuse rate |
| [evaluation.md](evaluation.md) | Two-layer evaluation (vault-native gold set + external benchmarks by adoption mode); the design changes the benchmark review warrants (claim supersession, verify entailment, reasoning-augmented query); and what the literature validates |
| [evaluation-benchmarks.md](evaluation-benchmarks.md) | The full capability-mapped benchmark taxonomy: scoping principles, per-capability tables (arXiv IDs, verdicts, repos, adoption mode), out-of-scope categories, and the suggested minimal suite |
| [profile-compilation.md](profile-compilation.md) | **(deferred)** Kustomize-style profile compiler — `memoria-base` + per-profile overrides, build-time validation, drift detection (forward-looking; not the current direct-managed model) |
| [decisions/](../decisions/) | 25 numbered decision records (ADRs 1–25); see [decisions/README.md](../decisions/README.md) for the index |
| [pilots/](pilots/) | Active pilots with explicit rollback criteria. Currently: [E1 — Open Notebook as comparative-brief back-end](pilots/01-open-notebook.md) |
| [non-llm-tools.md](non-llm-tools.md) | The non-LLM tools that Memoria uses to do its job, and the jobs they do |

## Minimum viable system

If the full setup feels heavy, start with this subset. It delivers most of the long-term value with a fraction of the configuration overhead.

| Layer | Minimum viable | Defer until needed |
| --- | --- | --- |
| **Tools** | Zotero + Better BibTeX, Obsidian, Hermes (terminal only), Git | Kanban board, ACP plugins, Scite, ASReview, K-Dense skills |
| **Folders** | `00-meta/`, `10-inbox/`, `20-sources/01-papers/`, `30-synthesis/01-claims/`, `30-synthesis/02-reference/` | items, entities, projects, drafts, deliverables, archive |
| **Templates** | `paper-note.md`, `claim-note.md` | All others (13 more) |
| **Schema fields** | `type`, `lifecycle`, `maturity`, `topic`, `projects`, `added` | `pub_status`, `full_text_reviewed`, `_proposed_classification`, `_enrichment`, MOCs |
| **Workflow** | Ingest → classify → claim note | find, enrich, MOCs, code artifacts, Canvas, deliverables |
| **Dashboard** | One Dataview query for classification debt | The full weekly dashboard |
| **Profile** | Mode-based Hermes (one tool, per-run mode) | Four-profile, seven-profile |

**The rule:** add complexity only when you feel the absence of the missing piece. If you're not running into a problem, you don't need the solution yet.

## Implementation paths: graduated start

Don't start with seven profiles if seven profiles will block you from starting. The system supports three graduated configurations:

| Path | Profiles | When to use |
| --- | --- | --- |
| **Mode-based** | One Hermes, with per-run `mode: ingest \| synthesize \| verify \| maintain`. | Single tool, single config. Simplest start. Good for exploration; weakest safety properties. |
| **Four-profile minimal** | Librarian + Writer + Verifier + Linter (see [profiles/README.md](../../explanation/profiles/README.md)). | Solo workflow at low volume. Mapper and Socratic capabilities fold into Librarian and Writer respectively, with care. |
| **Seven-profile (full)** | The full design: Librarian, Mapper, Socratic, Writer, Verifier, Coder, Linter. | When volume makes the human's review queue a bottleneck, or you want strong architectural separation between thinking (Socratic, write-denied) and producing (Writer, review-gated). |

The migration path is *up*: start with mode-based or four-profile; promote to the full seven once the bottleneck makes the cost worth paying.

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
