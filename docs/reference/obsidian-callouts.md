---
title: Obsidian callouts
parent: Reference
---

# Obsidian callouts

Three inline callout types defined via the [Callout Manager](obsidian-plugins.md) plugin. In the current shipped system only `[!brief]` has a producer; `[!suggestions]` and `[!verification]` are styled/reserved callout types whose producers are deferred.

---

## The three callout types

| Callout | Location | Producer | Purpose |
| --- | --- | --- | --- |
| `[!brief]` | Top of every source note in `notes/sources/` | Librarian (composed during ingest by `catalog-enrich-record`) | Comparative read — what this source overlaps with, what it may contradict, what new constructs it introduces |
| `[!suggestions]` | Deferred | None shipped yet ([#376](https://github.com/eranroseman/memoria-vault/issues/376)) | Intended bounded candidate links (5 forward + 5 backward, hard cap) |
| `[!verification]` | Deferred | None shipped yet ([#376](https://github.com/eranroseman/memoria-vault/issues/376), [#377](https://github.com/eranroseman/memoria-vault/issues/377)) | Intended per-claim trace back to claim notes |

---

## Example shape

```markdown
> [!brief] Comparative read
> Overlaps with: [[mamykina2010sense]], [[veinot2018good]]
> May contradict: [[chen2021pipeline]]
> New construct: "prosodic mimicry safety"
> 5 candidate links queued for review.
```

---

## Behavior

| Property | Value |
| --- | --- |
| Default collapse state | `[!brief]` expanded; deferred `[!suggestions]` is designed to collapse, and deferred `[!verification]` is designed to expand |
| Re-run on edited callout | `[!brief]` is producer-owned during ingest; deferred producers must preserve edited callouts rather than overwriting them |
| Write path | Policy-MCP gated — logged with SHA-256 hashes, reversible from the audit log |

For why each behaves this way, see [Callouts](../explanation/obsidian/callouts.md).

---

## How content is produced (hybrid pattern)

The shipped `[!brief]` producer uses a deterministic candidate-selection step followed by an LLM composition step. The deferred producers are designed to follow the same hybrid pattern when built.

| Callout | Deterministic step | LLM step |
| --- | --- | --- |
| `[!brief]` | Top-5 candidates ranked by: shared-citation overlap + embedding similarity + topic-tag intersection | Composes the "overlaps with / may contradict / new construct" narrative over the 5 candidates |
| `[!suggestions]` (deferred) | Intended top-10 candidates ranked by: embedding similarity (0.4) + shared citations (0.3) + topic-tag overlap (0.2) + recency boost (0.1); truncated to 5 forward + 5 backward | Optional one-line explanation per candidate |
| `[!verification]` (deferred) | Intended per-claim trace via regex citation extraction + embedding similarity; auto-clean above ~0.75, auto-fail below ~0.4 | Judges only the middle ambiguous band (0.4–0.75 similarity) |

For `[!brief]`, the audit-relevant part is the deterministic candidate set that the Librarian composes over. For the deferred callouts, the same principle applies as design intent: the LLM's prose is the visible presentation, but the deterministic scoring is what later dashboard signals should measure.

---

## Drift signals

No shipped dashboard tracks `[!suggestions]` accept/reject ratios yet because the producer is deferred. The intended drift signal is documented here so the future producer has a contract: ratio extremes should flag rubber-stamping versus over-strict scoring in fleet health. How to read and respond to these signals is covered in [Callouts](../explanation/obsidian/callouts.md).

---

## Related

- Callout Manager plugin: [Obsidian plugins](obsidian-plugins.md)
- Computational toolbox (scoring functions): [Retrieval and analysis methods](computational-toolbox.md)
- Fleet-health dashboard: [explanation/dashboards/](../explanation/dashboards)
- The callout explanation page: [Callouts](../explanation/obsidian/callouts.md)
