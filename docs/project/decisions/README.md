---
topic: decisions
---

# Architecture Decision Records

This folder holds Memoria's Architecture Decision Records (ADRs) — one file per non-trivial design choice the implementer needs to be aware of. Each ADR follows the template in [`_template.md`](_template.md).

**Status vocabulary** (deliberately small to force clarity):

- `proposed` — under discussion; no action taken yet.
- `accepted` — decided; the codebase follows this rule.
- `superseded` — replaced by a later ADR (see `superseded_by` field).
- `retired` — withdrawn without replacement (e.g., the problem dissolved into another doc, or the deferral lost its trigger).

## Index of all decisions

The list below is the authoritative chronological index. For a grouped view by topic (vault / workflows / profiles / dashboards / retired), see [by-topic.md](by-topic.md). Four deferred ADRs (12, 18, 19, 20) share one rationale, documented once in [adopt-on-demand: systematic-review tooling](adopt-on-demand-for-reviews.md).

The **Resolution / location** column records the one-line outcome for every decision. Decisions with their own ADR file are linked from the Title column; decisions resolved index-only (no separate file) have their full historical context preserved here.

| # | Title | Status | Resolution / location |
|---|---|---|---|
| 1 | Reviewer profile vs. human-only review | `accepted` (2026-05) | Index-only. Neither exactly — mechanical checks live in **Verifier** (workflow Verify); judgment is always human-driven. Verifier translates `verify-clean` / `verify-needs-revision` / `verify-needs-attention` into the human's `approve` / `reject` / `escalate` decisions. |
| 2 | [Auto-promotion threshold](02-auto-promotion-threshold.md) | `proposed` | Manual flagging via `maturity: evergreen`; no auto-promotion to reference. |
| 3 | [Answer-draft retention](03-answer-draft-retention.md) | `proposed` | Surface in weekly dashboard; Linter flags drafts >90 days for human decision. |
| 4 | [Citekey naming convention](04-citekey-naming-convention.md) | `accepted` (2026-05) | `authoryearword` via Better BibTeX format string. Pin keys immediately on import. |
| 5 | [MOC depth](05-moc-depth.md) | `retired` (2026-05) | Folded into [linking-patterns MOC thresholds](../../reference/linking-patterns.md#moc-creation-thresholds). |
| 6 | [Code agent attachment](06-code-agent-attachment.md) | `accepted` (2026-05) | Delegate to external coding agent (Claude Code, Aider, Codex, Kilocode); Coder profile scaffolds + documents. |
| 7 | [Session log granularity](07-session-log-granularity.md) | `retired` (2026-05) | Per-session log files in `00-meta/02-logs/`; convention already settled by deployment options. |
| 8 | Automation tier | `accepted` (2026-05) | Index-only. Three tiers — `strict` (default; propose-only), `standard` (safe auto-fixes + low-stakes triage), `minimal` (scheduled answer drafting). Named for security posture, not opaque integers. See [glossary: Automation tier](../../reference/glossary.md). |
| 9 | [Typed `relations:` frontmatter](09-typed-relations-frontmatter.md) | `accepted` (2026-05) | Nested `relations:` block on claim-notes for associative links — v1 `supports` / `contradicts`, human-set and opt-in; untyped wikilinks coexist. `supersedes`/`superseded_by` stay top-level (ADR-22). Vocabulary extends on felt need; NLI proposer deferred. |
| 10 | [Code-artifact autopilot](10-code-artifact-autopilot.md) | `proposed` | Defer. Manual triggers until a specific recurring analysis makes the case. |
| 11 | Confidence scoring on `_proposed_classification` | `accepted` (2026-05) | Index-only. Multi-label classifier trained on human's past decisions; LLM fallback below 0.85 confidence. Resolved via [computational-methods classifier-with-LLM-fallback](../../explanation/architecture/why-computational-methods.md). |
| 12 | [Systematic-review mode](12-systematic-review-mode.md) | `proposed` | Adopt only when actively running a systematic review. |
| 13 | [Method-unit vocabulary](13-method-unit-vocabulary.md) | `retired` (2026-05) | Premature ontology; no triggering pattern emerged. |
| 14 | [Cross-run skill-insights memory](14-cross-run-skill-insights.md) | `proposed` | Defer. Significant architecture for a single-user vault. |
| 15 | [Dedicated review-note type](15-dedicated-review-note-type.md) | `proposed` | Defer. Card's review_status / handoff summary carries enough provenance. |
| 16 | [Contradictions / tensions dashboard](16-contradictions-dashboard.md) | `accepted` (2026-05) | `contradictions` dashboard reads human-set `relations.contradicts` (ADR-9); lists conflicting claim pairs — diagnostic, no LLM in the rollup. NLI candidate-proposer deferred to future-directions. |
| 17 | [Retriever / Scout as a separate profile](17-retriever-scout-profile.md) | `proposed` | Keep Librarian unified until discovery volume overwhelms it. |
| 18 | [Evidence quality fields layer](18-evidence-quality-fields.md) | `proposed` | Per-project activation when a protocol or journal requires it. |
| 19 | [Pre-ingest screening layer (PRISMA + ASReview)](19-pre-ingest-screening.md) | `proposed` | Adopt when starting a formal scoping or systematic review. |
| 20 | [Dual-rater workflow for inter-rater reliability](20-dual-rater-workflow.md) | `proposed` | Activate only when the chapter / paper requires it. |
| 21 | [Shared candidate frontmatter format](21-shared-candidate-frontmatter.md) | `proposed` | Defer. Would standardize a `type: candidate-note` schema across candidate sources and add `candidate-note` as a 16th note type (the current 15 are authoritative in [vault/note-types.md](../../reference/note-types.md#note-types)). |
| 22 | [Claim supersession relation](22-claim-supersession.md) | `accepted` (2026-05) | `superseded_by: [[newer-claim]]` typed relation on claim-notes; currency derived from the link, human-set; `query`/`write` filter superseded claims; Linter FAMA-style check. One relation adopted concurrently with ADR-9. |
| 23 | [vault-eval as a maintenance capability](23-vault-eval-integration.md) | `accepted` (2026-05) | Diagnostic eval from existing machinery: board-dispatched `eval` card, non-committing Policy-MCP writes, Linter scoring; gold tasks in `00-meta/05-eval/`, results in `00-meta/08-metrics/eval/`. Diagnostic, not gating. |
| 24 | [obsidian-linter is reference-only](24-obsidian-linter-reference-only.md) | `accepted` (2026-05) | obsidian-linter is documented but not installed/recommended — a GUI on-save formatter writes outside the Policy-MCP audit trail and would be a second frontmatter authority; the Memoria Linter + markdownlint own this. Moved `recommended/` → `reference/`. |
| 25 | [Homepage front-door note](25-homepage-front-door.md) | `accepted` (2026-05) | Ship a vault-root `Home.md` Dataview front door, auto-opened by obsidian-homepage (`recommended/`, view-only). A launchpad that surfaces the dashboards; obsidian-startpage rejected (plugin-rendered, not a note). |
| 26 | [Advisor-review vs. frozen deliverable](26-advisor-review-vs-frozen-deliverable.md) | `accepted` (2026-05) | Advisor-review exports are live-citation working artifacts, **outside** the frozen-deliverable contract; routes + failure modes in [export-targets.md](../../how-to/workflows/downstream/export-targets.md). |
| 27 | [Ratchet duplicate gate](27-ratchet-duplicate-gate.md) | `proposed` | Defer. A `qmd` similarity gate at synthesis-filing time; revisit when a live `qmd` index and a dense synthesis corpus exist. Pairs with ADR-28. |
| 28 | [Frozen-evaluator checklist](28-frozen-evaluator-deferred.md) | `proposed` | Defer. Per-note-type acceptance checklists; revisit at 50+ claim-notes. Pairs with ADR-27. |
| 29 | [Admin/forensic GUI surface](29-admin-gui-surface.md) | `proposed` | Defer/watch. The admin-forensic gap is real, but `hermes-workspace` (v0.1.0, single-contributor) is too immature to adopt or document; the CLI fills the gap. |
| 30 | [Project-membership auto-proposal](30-project-auto-classification.md) | `accepted` (2026-05) | Librarian proposes `projects` from a lightweight per-project `primary_topics` hint (`.memoria/project-hints.yaml`), human-confirmed; the full corpus-profile matrix is rejected. |

## Numbering gaps and the graveyard

The index above is gap-free — every number 1–30 has a row — but the *directory* is not, and a reader browsing the files will notice the missing numbers. They are accounted for here so the gaps read as intentional, not as lost work:

- **No `01.md`, `08.md`, `11.md`.** ADRs 1, 8, and 11 are recorded **index-only**: `accepted`, but small enough to resolve in the Resolution column without a standalone file. The missing files are deliberate.
- **Retired ADRs keep their files.** ADRs 5, 7, and 13 reached `retired` (withdrawn without replacement) but their files remain as history — see the `retired` rows above and the grouped view in [by-topic.md](by-topic.md).
- **Nothing was rejected outright.** The [status vocabulary](#architecture-decision-records) has no `rejected` state by design: a proposal that doesn't survive becomes `retired` (the problem dissolved) rather than being deleted, so no number is ever reused or orphaned.

## Adding a new ADR

1. Copy [`_template.md`](_template.md) to `NN-kebab-case-title.md` where `NN` is the next available integer.
2. Fill in the frontmatter (id, title, status, date_proposed).
3. Write the Context / Decision / Consequences / Alternatives / Related sections.
4. Add a row to the index table above.
5. If this ADR supersedes another, set `superseded_by` on the old one and `supersedes` on the new one.

**Naming exception — cluster-rationale documents.** [`adopt-on-demand-for-reviews.md`](adopt-on-demand-for-reviews.md) deliberately lacks a numeric prefix. It is not a decision record; it is a shared rationale document that explains why a cluster of ADRs (12, 18, 19, 20) all resolve to "adopt on demand." Cluster-rationale documents do not get a number because they are not decisions — they are the prose backing for a group of related decisions that share one rationale.

## Closing an ADR

When a `proposed` decision is acted on:

1. Update `status` to `accepted` (or `retired` if the problem dissolved).
2. Set `date_resolved`.
3. Update the index table's status column.

If a later ADR replaces this one, set the old ADR's `status` to `superseded` and link to the replacement via `superseded_by`. Both files stay — superseded ADRs are valuable history.
