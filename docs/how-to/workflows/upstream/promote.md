---
topic: workflows
---

# Promote

**Group.** Upstream
**Goal.** Convert stable claim knowledge into canonical reference notes.

## Steps

1. Human marks a claim note as `maturity: evergreen`.
2. Weekly dashboard surfaces the promotion queue.
3. Human moves the file to `30-synthesis/02-reference/`.
4. Sets `promoted_date`.
5. If applicable, the note becomes a MOC-linked reference page.

## Owners

Human owns the promotion decision and the file move. Hermes flags candidates and can compile draft reference notes for review.

## Card lifecycle

`ready` (weekly dashboard surfaces the claim as a promotion candidate) → `running` (human reviews and decides to promote) → `done` (file moved to `30-synthesis/02-reference/`, `promoted_date` set, MOC entry added) → `archived` (card closed after promotion is confirmed).

## Commands

No CLI command — performed directly in the vault or via the Obsidian interface.

## Example

`receptivity-decreases-under-high-cognitive-load.md` accumulates 4 source citations and 3 cross-links over six months → human marks `maturity: evergreen` → the weekly-review "Promotion queue" surfaces it → human writes a tight intro paragraph framing the claim for reference reading → moves the file to `30-synthesis/02-reference/receptivity-and-cognitive-load.md` → sets `promoted_date: 2026-11-12` → adds an entry to `[[jitai-design-moc]]` so the new reference page is discoverable from the topic hub.

## Related

- **Previous workflow:** [Distill](distill.md) (claim must reach `maturity: evergreen` first)
- **Auto-promotion policy:** [ADR-2 auto-promotion threshold](../../../project/decisions/02-auto-promotion-threshold.md) — manual only, surfaced via dashboard.
- **Superseded claims don't promote:** a claim carrying `superseded_by` is excluded from the promotion queue and from reference notes — see [ADR-22](../../../project/decisions/22-claim-supersession.md).
- **MOC creation thresholds:** [vault/linking-patterns.md](../../../reference/linking-patterns.md#moc-creation-thresholds)
