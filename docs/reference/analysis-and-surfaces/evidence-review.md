---
title: Evidence-set review
parent: Analysis and surfaces
nav_order: 6
grand_parent: Reference
---

# Evidence-set review

The evidence-set review surface routes the grounds contract's PI-clearable
holds to one queue with two fronts: the Obsidian evidence-review pane
(command: `Memoria: Open evidence review`) and the `memoria review` CLI
cockpit. The pane reads the nested `view-spec.v1` payload from
`GET /v1/views/evidence-review` and enqueues the PI-only `resolve-evidence`
worker operation. The CLI reads the same queue engine-direct through
`engine_api.evidence_review_queue` (no HTTP) and calls the disposition seam
directly through its PI-gated command. Both fronts write through one seam, so
a decision recorded in either is the same recorded decision.

## Queue

Rows are evidence sets whose findings are `evidence-incomplete` or
`review-required` and that carry no hold-clearing disposition. Rejected rows
stay queued, rendered rejected; deferred rows are suppressed until the next
UTC calendar day. Permanent blocks (`evidence-text-drift`,
`evidence-text-unbound`, duplicates) are not reviewable: they render read-only,
naming their cure — edit the draft or the grounds, then re-verify.

Unresolved SRD gaps ride the same queue as read-only cards. They carry no
evidence decision and appear only on an unfiltered read.

Facets are `routing_type` (`implicit`, `multi-hop`, `incomplete`), `project`,
and `min_age_days`; `batch` sizes the page. Facet denominators count the whole
scope-visible queue before filtering and batching.

## Row schema (fixed order)

1. Claim text (the bound draft block, verbatim)
2. Grounds items with resolved previews
3. Why routed (the derivation rule, verbatim)
4. Machine's argument-for / argument-against (both or neither)
5. Tipped-by (the single routing factor)
6. Coarse certainty (three levels)
7. No verdict line; no pre-selected action

Fields 1–3 (evidence) always render before fields 4–6 (machine analysis), and
the analysis is collapsed by default behind a disclosure control that
re-collapses every time a row is opened — the PI reads the grounds before the
machine's opinion, by construction. A read-only cure row carries no analysis
at all.

Fields 4–6 are present-only: the queue passes them through and never invents
them. Nothing in the shipped pipeline writes the argument pair yet, so today a
reviewable row's analysis is its deterministic tipping factor and, when
recorded, its certainty.

## Dispositions

| Action | Effect | Event |
| --- | --- | --- |
| Accept | clears the hold; bound to the items content — voided if items later change | `disposition.v1`, `decision=accept` |
| Reject | the hold **stays blocking**; the row renders rejected | `disposition.v1`, `decision=reject` |
| Edit | records fix-the-marker intent and deep-links the draft block; the hold clears only when the edit lands | `disposition.v1`, `decision=edit` |
| Defer | the hold stays; the row is suppressed until the next UTC day | `disposition.v1`, `decision=defer` |

Only accept clears holds. A rejected evidence set keeps blocking its project's
draft export, which refuses naming the finding.

## Related

- The CLI verbs and their PI-only status: [CLI surfaces](../commands-and-transports/cli.md)
- The pane's read route: [Local HTTP transport](../commands-and-transports/local-http-transport.md)
- Export gates and refusal states: [Export routes and formats](../pipelines-and-io/export.md)
- The works-cited projection behind the fence: [Bibliography](../evidence-and-integrations/bibliography.md)
