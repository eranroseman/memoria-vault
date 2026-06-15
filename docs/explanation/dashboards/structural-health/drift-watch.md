---
title: drift-watch dashboard
parent: Structural health
nav_order: 1
grand_parent: Dashboards
---

# `drift-watch` dashboard

Surfaces active and imminent drift — the Linter's and the verification sweeps' **open findings** — as one consolidated view. Open it when something feels wrong but the system looks clean: a lint pass came back clear yet things still seem off.

## What it shows

The dashboard (`system/dashboards/drift-watch.md`) lists the open **`flag` and `alert` cards** — Inbox cards still in `proposed`, sorted loudest-first. Every detector finding becomes a card through the shared card-writer ([ADR-51](../../../adr/51-inbox-category-and-honesty-card.md)), so the dashboard is a filtered view of the same queue everything else uses: a `flag` is a verification/integrity issue (leading with its `finding` and `agent_recommendation`), an `alert` is a drift or retraction notice. The producing engines are the **Linter** (schema validation, link/relationship resolvability, orphans, golden-copy drift — daily cron + the pre-commit gate) and the **verification sweeps** (retraction lookups, near-duplicate and broken-citation detection).

Loudness is the headline: `alert`-level findings also push to the Inbox's "Needs me" queue (the Desk workspace), and `block`-level findings stop the gated action until acknowledged. Everything below that waits here and in the weekly review. (The four-level loudness model and the "next 30 minutes" test it follows are owned by [Interaction channels](../../architecture/human-channels.md).)

## What it is not

**Not audit-log or fleet-health.** Drift-watch is the *structural* view — open integrity findings, headlined by the verdict band; audit-log is per-write forensics and fleet-health is the operational aggregate. For the full three-way distinction, see [Operational health](../operational-health/README.md#audit-log-vs-fleet-health-vs-drift-watch).

**Not for content hygiene.** Stale literature and unfinished-looking filenames surface in weekly-review and loose-ends, not here. Drift-watch is reserved for what the engines can *detect mechanically* — the "silent" failures the human wouldn't notice by reading content.

## When drift-watch becomes relevant

Drift-watch is most useful after changes that could desynchronize the deployed system from its source: a release refresh, edits to profile files, plugin upgrades, or anything that appears in the audit log as an anomaly. The detectors exist precisely because these desynchronizations are invisible at the content level — the vault looks clean because the content is unchanged, but a system file has drifted from the golden copy or a schema no longer matches its records. (Detected golden-copy drift comes with a restore path: `lint:restore`, propose-only.)

The Friday weekly review includes a drift-watch pass because a week of ordinary operation also accumulates small `notice`-level findings that are not individually urgent but benefit from regular review.

## Before it has real data

Until the daily lint cron and the sweeps have run, this dashboard is empty — which on a fresh vault means "nothing checked yet," not "all clear." After the first pass, empty means clean: the queue of open findings converges to zero as the PI acts on or archives the cards. (Why an empty dashboard is the healthy state at all is the cross-cutting [empty-is-success principle](../README.md#why-the-dashboards-are-designed-the-way-they-are).)

## Related

- [Operations](../../operations/README.md) — the Linter and the sweeps, and what each catches
- [audit-log dashboard](../operational-health/audit-log.md) — per-decision forensics layer below structural drift
- [The honesty card](../../kanban-board/card-schema.md) — the `flag`/`alert` card format and loudness levels
- [Linter: detectors and auto-fix](../../../reference/linter.md) — detector severity reference
