---
topic: workflows
---

# Classify

**Group.** Upstream
**Goal.** Turn provisional agent output into canonical metadata and a reviewed paper note.

## Steps

1. Human opens the paper note.
2. Reviews `_proposed_classification`.
3. Promotes selected fields into the main YAML.
4. Deletes the proposed block.
5. Sets `lifecycle: current` and `triage_completed`.
6. Fills the summary sections.

## Owners

The **Librarian** proposes classification (writing `_proposed_classification` during ingest). The human owns all promotion decisions.

## Card lifecycle

`done` (card arrives here from Ingest with `review_status: requested`) → `running` (human opens the note and begins review) → `done` (classification promoted to main YAML, `lifecycle: current` set, `triage_completed` written) → `archived` (card closed after human review is complete).

## Commands

No CLI command — performed directly in the vault or via the Obsidian interface.

## Example

`mamykina2010sense.md` is at `lifecycle: proposed` with `_proposed_classification: { topic: [receptivity-detection], methods: [field-study] }` → human opens the note, agrees with `topic`, refines `methods: [field-study, qualitative-interview]` for accuracy → promotes both fields into the main YAML and deletes the `_proposed_classification` block → sets `lifecycle: current` and `triage_completed: 2026-05-25` → writes 2–3 sentences in the Key findings section. The note is now canonical for queries and dashboards.

## Related

- **Previous workflow:** [Ingest](ingest.md)
- **Next workflow:** [Discuss](discuss.md)
- **Profile:** [profiles/librarian.md](../../../explanation/profiles/librarian.md)
- **Classifier confidence:** ADR-11 (confidence scoring on `_proposed_classification`) — an *index-only* decision recorded in the [decisions README](../../../project/decisions/README.md#index-of-all-decisions), not a standalone file.
