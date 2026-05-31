---
topic: general
---

# ADRs grouped by topic

The flat numbered list in [README.md](README.md) is the authoritative order (ADRs are append-only and keep their original number). This file is a *secondary view* that groups the same ADRs by the topic folder they most affect, so a reader exploring `vault/` or `workflows/` can find the related decisions quickly.

Status legend: **proposed** (under discussion) · **accepted** (adopted into the design) · **superseded** (replaced by a later ADR) · **retired** (withdrawn without replacement — kept for context).

> Four deferred ADRs — 12, 18, 19, 20 — form the [adopt-on-demand systematic-review cluster](adopt-on-demand-for-reviews.md). Each is listed under its primary topic below, but they share one rationale.

## Vault & schema

Note types, frontmatter, naming, and the controlled vocabularies that govern them.

- [04-citekey-naming-convention.md](04-citekey-naming-convention.md) — Citekey naming convention · **accepted**
- [09-typed-relations-frontmatter.md](09-typed-relations-frontmatter.md) — Typed relations frontmatter · **accepted**
- [15-dedicated-review-note-type.md](15-dedicated-review-note-type.md) — Dedicated review-note type · proposed
- [18-evidence-quality-fields.md](18-evidence-quality-fields.md) — Evidence quality fields layer · proposed
- [21-shared-candidate-frontmatter.md](21-shared-candidate-frontmatter.md) — Shared candidate frontmatter format · proposed
- [22-claim-supersession.md](22-claim-supersession.md) — Claim supersession relation · **accepted**
- [28-frozen-evaluator-deferred.md](28-frozen-evaluator-deferred.md) — Frozen-evaluator acceptance checklists (deferred) · proposed
- [30-project-auto-classification.md](30-project-auto-classification.md) — Project-membership auto-proposal from a topic hint · **accepted**

## Workflows

Upstream / downstream / maintenance pipelines and their stage-specific design choices.

- [02-auto-promotion-threshold.md](02-auto-promotion-threshold.md) — Auto-promotion threshold · proposed
- [03-answer-draft-retention.md](03-answer-draft-retention.md) — Answer-draft retention · proposed
- [10-code-artifact-autopilot.md](10-code-artifact-autopilot.md) — Code-artifact autopilot · proposed
- [12-systematic-review-mode.md](12-systematic-review-mode.md) — Systematic-review mode · proposed
- [19-pre-ingest-screening.md](19-pre-ingest-screening.md) — Pre-ingest screening layer (PRISMA + ASReview) · proposed
- [20-dual-rater-workflow.md](20-dual-rater-workflow.md) — Dual-rater workflow for inter-rater reliability · proposed
- [26-advisor-review-vs-frozen-deliverable.md](26-advisor-review-vs-frozen-deliverable.md) — Advisor-review vs. frozen deliverable · **accepted**
- [27-ratchet-duplicate-gate.md](27-ratchet-duplicate-gate.md) — Ratchet duplicate gate (deferred) · proposed

## Profiles

The seven Hermes workers — missions, attachment, cross-run memory.

- [06-code-agent-attachment.md](06-code-agent-attachment.md) — Code agent attachment · **accepted**
- [14-cross-run-skill-insights.md](14-cross-run-skill-insights.md) — Cross-run skill-insights memory · proposed
- [17-retriever-scout-profile.md](17-retriever-scout-profile.md) — Retriever / Scout as a separate profile · proposed

## Dashboards & UI

Persistent dashboards and how the human sees board / vault state.

- [16-contradictions-dashboard.md](16-contradictions-dashboard.md) — Contradictions / tensions dashboard · **accepted**
- [23-vault-eval-integration.md](23-vault-eval-integration.md) — vault-eval as a maintenance capability · **accepted**
- [25-homepage-front-door.md](25-homepage-front-door.md) — Homepage front-door note, auto-opened by obsidian-homepage · **accepted**
- [29-admin-gui-surface.md](29-admin-gui-surface.md) — Admin/forensic GUI surface (deferred — tool too immature) · proposed

## Plugins & tooling

Obsidian community plugins and external formatters — what's in the install set and why.

- [24-obsidian-linter-reference-only.md](24-obsidian-linter-reference-only.md) — obsidian-linter is reference-only, not a control-plane formatter · **accepted**

## Retired

Kept for historical context; withdrawn without replacement (the problem dissolved).

- [05-moc-depth.md](05-moc-depth.md) — MOC depth · retired
- [07-session-log-granularity.md](07-session-log-granularity.md) — Session log granularity · retired
- [13-method-unit-vocabulary.md](13-method-unit-vocabulary.md) — Method-unit vocabulary · retired

## Gaps

ADR numbers 01, 08, and 11 have no file because they were resolved **index-only** — `accepted`, but small enough to record in the [README index](README.md#numbering-gaps-and-the-graveyard) without a standalone file. Nothing was rejected outright. The numbering is append-only; new ADRs take the next unused number (see [`_template.md`](_template.md)).
