---
title: Manage your topic vocabulary
parent: Maintenance
nav_order: 5
---


# Manage your topic vocabulary

This guide shows you how to keep the `topic`, `study_design`, and `methods` fields consistent across your corpus — so Dataview queries stay reliable and classification stays navigable as your vault grows.

## Prerequisites

- A vault with at least a handful of classified source notes
- Obsidian open with the vault

---

## When to do each task

| Trigger | Task |
| --- | --- |
| Starting a new corpus or project | Define your initial vocabulary list |
| Active `topic` list exceeds ~30 terms | Prune and consolidate |
| A term's meaning has drifted or split | Rename it safely |
| Annually, or after a major reading batch | Full vocabulary review |

---

## Step 1 — Create your vocabulary reference note

If it doesn't exist yet, create `00-meta/vocabulary.md`. This note is the single source of truth for your allowed values.

Structure it with one section per field:

```yaml
type: reference-note
lifecycle: current
```

```markdown
## topic
- sensemaking
- jitai-design
- ecological-momentary-assessment
...

## study_design
- rct
- observational
- field-study
- meta-analysis
...

## methods
- experience-sampling
- thematic-analysis
- regression
...
```

Keep the `topic` list to **~30 terms**. A tighter vocabulary produces more consistent classification and more reliable Dataview queries.

### Worked example — HCI + digital health (copy, edit, discard)

*One* example, not a Memoria default — `topic`/`study_design`/`methods` are deliberately open. Copy what fits, rename the rest, delete the remainder; nothing here is enforced.

```yaml
## topic — ~30 terms
# Intervention design
- jitai                     # Just-in-Time Adaptive Interventions
- ema-experience-sampling   # Ecological momentary assessment
- receptivity-detection     # Optimal-moment detection for delivery
- behavior-change
- implementation-science
# Health domains
- self-management
- health-coaching
- motivational-interviewing
- mental-health-wellbeing
- chronic-disease
- mhealth
# Research methods (conceptual)
- hci-methods
- design-science
- causal-inference
- qualitative-methods
# Systems and technology
- conversational-agents
- wearables-sensors
- digital-phenotyping
- ubicomp
- llm-ai-health
# Knowledge and equity
- sensemaking
- health-equity
- health-informatics
- patient-provider

## study_design — one value per note, most specific that applies
- RCT
- controlled-experiment
- quasi-experimental
- observational
- systematic-review
- meta-analysis
- qualitative
- mixed-methods
- design-science
- technical          # algorithm/model/benchmark — no human participants
- theoretical        # framework / conceptual / position paper
- secondary-analysis

## methods — list-valued
# Data collection
- semi-structured-interview
- survey
- diary-study
- ema-probe
- log-analysis
- biometric-sensing
- think-aloud
# Analysis
- thematic-analysis
- grounded-theory
- content-analysis
- statistical-modelling
- machine-learning
- nlp-text-analysis
- causal-dag
# Design and evaluation
- participatory-design
- usability-testing
- field-deployment
- wizard-of-oz
- ab-test
```

(`maturity` and MOC `scope` are *fixed* Memoria vocabularies, not open — see [Frontmatter fields](../../reference/frontmatter.md).)

---

## Step 2 — Add a new term

Before adding a term, check your vocabulary note to confirm it doesn't already exist under a different name.

1. Add the term to the relevant section in `vocabulary.md`.
2. Use it in the note you're classifying.
3. If you're adding a `topic` term and the list is already at 30, first check whether an existing term could cover the same ground.

---

## Step 3 — Rename a term safely

Never search-replace topic values manually across notes — it bypasses the Linter and leaves no audit trail.

**Option A — Obsidian tag-wrangler (for small corpora):**

1. Install the Tag Wrangler plugin if not present.
2. Open the Tags panel (Cmd-P → Tag Wrangler: Rename tag).
3. Rename the old value to the new value. Tag Wrangler updates every occurrence.
4. Update `vocabulary.md` to reflect the new term.

**Option B — Linter schema-migrate (for large corpora or automated runs):**

```bash
hermes -p memoria-linter chat -s lint
```

```text
/schema-migrate --field topic --from old-term --to new-term --dry-run
```

Review the dry-run output. If it looks correct, remove `--dry-run` and run again.

After either option, run a lint check to confirm no stale values remain:

```text
/lint --check schema
```

---

## Step 4 — Annual vocabulary review

Once a year (or after a major reading batch), open `vocabulary.md` and walk through each list:

1. **Prune.** Remove terms that appear on fewer than 3 notes — they're not load-bearing.
2. **Consolidate.** Merge terms that have drifted to mean the same thing (use Option A or B above to rename the smaller into the larger).
3. **Split.** If a term has grown ambiguous (covering two distinct concepts), add both new terms, rename existing notes, and remove the old term.
4. After changes, run `/lint --check schema` to catch any notes still using retired values.

---

## Verify

- `vocabulary.md` reflects the current active term list
- No notes use values not in `vocabulary.md` (confirmed by lint schema check)
- Active `topic` list is ≤ 30 terms

## Related

- Classify a source: [Classify a source](../sources/classify-a-source.md)
- Run the Linter: [Run the Linter](run-the-linter.md)
- Field definitions: [reference/linking.md#vocabulary-discipline](../../reference/linking.md#vocabulary-discipline)
- Vocabulary discipline (why three fields, why open): [Vocabulary discipline](../../explanation/knowledge/vocabulary-discipline.md)
