---
title: loose-ends dashboard
parent: Structural health
nav_order: 2
grand_parent: Dashboards
---

# `loose-ends` dashboard

Batches the lowest-stakes structural debt — the `flag` cards the Linter raised at **Notice** loudness, which never push to Home. Run it during the weekly review or whenever you want to clear cosmetic findings in one pass. The dashboard lists; you decide the action per card.

## What it shows

The `flag` cards in `inbox/` still in `proposed` with `loudness = notice`, sorted oldest-first (`file.ctime ASC`) — each row carrying its `type`, `finding`, and `raised_by`. Older findings have lingered longest and lead the list. These are cosmetic and low-stakes integrity findings the Linter deliberately did not push to Home or block on; they wait here for the weekly batch.

## Why Notice loudness and not louder findings

Loudness, not finding type, is what routes a card here. `alert`-level drift and `block`-level findings surface in `drift-watch` and push to Home — they need attention sooner. Loose-ends is reserved for the `notice` tail: real findings, but none worth interrupting the PI for. Batching them into the weekly pass keeps the daily glance quiet without losing the debt.

## What it is not

**Not drift-watch.** Drift-watch shows the open `flag`/`alert` cards loud enough to act on now (`alert` also pushes to Home). Loose-ends shows only the `notice`-loudness `flag` tail. Same card queue, different loudness slice.

**Not data-quality validation itself.** The Linter detects the issues — empty frontmatter, weak naming, soft integrity smells — and writes the cards. Loose-ends is the *view* over the Notice-level subset, not the detector.

## Works once the Linter has run

Loose-ends reads the Inbox card queue, so it's empty until the Linter's first pass writes `notice`-level `flag` cards. After that, an empty dashboard means the Notice-level debt is clear — the cards converge to zero as the PI acts on or archives them.

## Related

- [The weekly-review dashboard](weekly-review.md) — the Friday ritual that includes a loose-ends pass
- [drift-watch dashboard](drift-watch.md) — the louder `flag`/`alert` findings; loose-ends is the Notice-level tail
- [The honesty card](../../kanban-board/card-schema.md) — the `flag` card format and loudness levels
