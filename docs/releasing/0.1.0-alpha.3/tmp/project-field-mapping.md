# Project #1 field-population map (confirm-and-click)

**For:** the table view of "Memoria Issue Tracker" (project #1). Set **Type / Area / Priority** on each open issue (these fields are new/empty); adjust **Status** only where it says *Deferred* (the field already exists with values).
**Date:** 2026-06-14 · 74 open issues.

**Bulk shortcut:** in the table view you can multi-select rows with the same value and set the field once. The biggest bulk groups: the **deferred-ADR trackers** (#370–374, #408–416) all = Type `Feature` · Priority `Low` · Status `Deferred`; the **alpha.4** issues all = Status `Deferred`.

**Legend** — Area: `capture · ingest · knowledge · obsidian-ui · operations · docs-site · installer · integrations · agents` (blank = meta/positioning, no good fit). Priority `High` is reserved for the tutorial-breaking core-loop defects. Status suggestions: `Backlog` = active/ready; `Deferred` = parked (alpha.4 / deferred ADRs / future).

> Status note: where a row says "needs-scoping" or "Blocked", those Status options don't exist yet — add them in Project settings → Status, or leave as Backlog for now.

| # | Type | Area | Priority | Status | Notes |
|---|---|---|---|---|---|
| 145 | Feature | obsidian-ui | Normal | Backlog | overlaps #378 (coloring) |
| 154 | Feature | knowledge | Normal | Deferred | project scaffold (alpha.4) |
| 175 | Docs | docs-site | Low | Backlog | deliverable already drafted in-thread |
| 181 | Feature | capture | Low | Deferred | mobile transport; blocked on #382 |
| 182 | Feature | installer | Low | Deferred | → ADR-60/#410, ADR-63/#413 |
| 183 | Feature | capture | High | Backlog | Modal Forms (ADR-71) — core |
| 187 | Decision | integrations | Low | Deferred | needs superseding ADR-05 |
| 188 | Research | agents | Normal | Backlog | per-profile model A/B |
| 192 | Research | agents | Low | Backlog | answered in-thread |
| 193 | Research | operations | Low | Backlog | answered (resolved-by-redesign) |
| 194 | Research | — | Low | Backlog | positioning research |
| 195 | Research | integrations | Low | Backlog | answered in-thread |
| 198 | Decision | — | Low | Backlog | superseded by D52 phasing |
| 212 | Docs | docs-site | Low | Backlog | needs-scoping |
| 220 | Research | integrations | Low | Backlog | needs-scoping; dup of #321 |
| 225 | Research | — | Low | Backlog | needs-scoping (no citation given) |
| 274 | Research | agents | Low | Backlog | code-lane prior art |
| 296 | Feature | installer | Normal | Deferred | WSL2→native (alpha.4) |
| 321 | Research | — | Low | Backlog | resource-review list; needs-scoping |
| 328 | Research | knowledge | Low | Backlog | needs-scoping |
| 329 | Research | knowledge | Normal | Deferred | feeds project workspace (alpha.4) |
| 336 | Feature | ingest | Normal | Deferred | batch worklists (alpha.4) |
| 337 | Feature | operations | Normal | Deferred | gate telemetry (alpha.4) |
| 339 | Feature | installer | Normal | Deferred | golden-copy upgrade (alpha.4) |
| 343 | Feature | operations | Normal | Deferred | sub-issue of #443; loudness routing |
| 344 | Feature | ingest | Low | Deferred | diversity reserve (alpha.4) |
| 369 | Decision | agents | Normal | Deferred | code lane (alpha.4) |
| 370 | Feature | knowledge | Low | Deferred | ADR-38 tracker |
| 371 | Feature | agents | Low | Deferred | ADR-35 tracker |
| 372 | Feature | knowledge | Low | Deferred | ADR-39 tracker |
| 373 | Feature | operations | Low | Deferred | ADR-40 tracker |
| 374 | Feature | operations | Low | Deferred | ADR-41 tracker |
| 375 | Feature | obsidian-ui | High | Backlog | sub-issue of #443; status bar |
| 376 | Feature | operations | Normal | Deferred | sub-issue of #443; callout producers |
| 377 | Feature | operations | Normal | Deferred | sub-issue of #443; verify-on-commit |
| 378 | Feature | obsidian-ui | Normal | Backlog | overlaps #145; consider split |
| 379 | Feature | ingest | Low | Deferred | calibration spec (alpha.4) |
| 380 | Feature | obsidian-ui | Normal | Backlog | assist surface |
| 381 | Feature | agents | Low | Deferred | map skills (alpha.4) |
| 382 | Feature | integrations | Low | Deferred | Telegram channel |
| 383 | Feature | installer | Low | Deferred | VPS/always-on |
| 408 | Feature | integrations | Low | Deferred | ADR-58 tracker |
| 409 | Feature | operations | Low | Deferred | ADR-59 tracker |
| 410 | Feature | knowledge | Low | Deferred | ADR-60 tracker |
| 411 | Feature | agents | Low | Deferred | ADR-61 tracker |
| 412 | Feature | operations | Low | Deferred | ADR-62 tracker |
| 413 | Feature | installer | Low | Deferred | ADR-63 tracker |
| 414 | Feature | installer | Low | Deferred | ADR-64 tracker |
| 415 | Feature | operations | Low | Deferred | ADR-65 tracker |
| 416 | Feature | ingest | Low | Deferred | ADR-66 tracker |
| 437 | Feature | ingest | Normal | Deferred | PubMed source (alpha.4) |
| 438 | Feature | ingest | Normal | Deferred | Unpaywall extract (alpha.4) |
| 439 | Feature | knowledge | Low | Deferred | ADR-19 Tier 2 (alpha.4) |
| 443 | Docs | docs-site | Normal | Backlog | **parent** of #375/#376/#377/#343 |
| 447 | Feature | integrations | Low | Backlog | needs-scoping; → code lane |
| 449 | Bug | knowledge | High | Backlog | card schema vs resolve script |
| 455 | Bug | capture | High | Backlog | core-loop defect |
| 456 | Bug | capture | High | Backlog | core-loop defect |
| 457 | Bug | obsidian-ui | High | Backlog | core-loop defect |
| 458 | Bug | capture | High | Backlog | core-loop defect |
| 459 | Bug | installer | High | Backlog | core-loop defect |
| 460 | Feature | agents | Normal | Backlog | delegate picker polish |
| 461 | Feature | obsidian-ui | Normal | Backlog | Commander (ADR-72) |
| 462 | Refactor | agents | Normal | Backlog | Co-PI rename + config |
| 463 | Bug | docs-site | Normal | Backlog | `.memoria/` leak |
| 464 | Docs | docs-site | Normal | Backlog | docs hygiene (ADR-73) |
| 465 | Decision | operations | Normal | Backlog | **parent** of #466/#472; ADR-69 |
| 466 | Refactor | operations | Normal | Backlog | sub-issue of #465 |
| 467 | Feature | obsidian-ui | Normal | Backlog | JTBD dashboards (ADR-70) |
| 468 | Docs | knowledge | Normal | Backlog | vocabulary.md |
| 469 | Feature | agents | Normal | Backlog | librarian source note |
| 470 | Feature | knowledge | Normal | Backlog | claim-note button |
| 471 | Refactor | obsidian-ui | Low | Backlog | QuickAdd labels + skill names |
| 472 | Refactor | operations | Low | Deferred | sub-issue of #465 (alpha.4) |

## Quick bulk passes (multi-select in table view)

1. **Filter `milestone:0.1.0-alpha.4`** → set Status `Deferred` for all (16 rows).
2. **Select #370–374, #408–416** (deferred-ADR trackers) → Type `Feature`, Priority `Low`, Status `Deferred` in one shot (14 rows).
3. **Select #455–459 + #449** → Priority `High` (the core-loop defects).
4. Then set **Area** per the table (the one field that has no shortcut — but you can multi-select by subsystem, e.g. all `ingest` rows: #336/#344/#379/#416/#437/#438).

After Type is populated everywhere, retire the `enhancement`, `question`, `research`, `needs-scoping` labels (keep `bug`/`documentation` + the bot set).
