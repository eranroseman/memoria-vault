---
title: Obsidian callouts
parent: Obsidian and Zotero
grand_parent: Reference
---

# Obsidian callouts

Three inline callout types defined via the [Callout Manager](obsidian-plugins.md) plugin. All three now have shipped producers: `[!brief]` during ingest, `[!suggestions]` from the link-claim palette action, and `[!verification]` from the verify-draft palette action.

The fixed palette also applies to shipped navigation surfaces: the space dashboards use
`[!brief]` for their empty-state and orientation copy instead of generic Obsidian
callout types. The `design-system-drift` Linter detector reports any ad-hoc/rainbow
callout variants in shipped vault notes.

---

## The three callout types

| Callout | Location | Producer | Purpose |
| --- | --- | --- | --- |
| `[!brief]` | Top of every source note in `notes/sources/` | Librarian (composed during ingest by `catalog-enrich-record`) | Comparative read — what this source overlaps with, what it may contradict, what new constructs it introduces |
| `[!suggestions]` | Claim notes in `notes/claims/` | QuickAdd `Memoria: link claim` preflight, followed by Librarian `link-suggest-claim` | Bounded deterministic candidate links (5 forward + 5 backward, hard cap) |
| `[!verification]` | Drafts in `projects/` | QuickAdd `Memoria: verify draft` preflight, followed by Peer-reviewer `verify-check-citation` | Deterministic claim-link/citekey trace scaffold plus visible `gap` cards for ungrounded assertions; the lane performs support judgment |

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
| Default collapse state | `[!brief]` expanded; `[!suggestions]` collapsed; `[!verification]` expanded |
| Re-run on edited callout | Producers append a dated callout instead of overwriting existing human-edited callouts |
| Write path | Policy-MCP gated — logged with SHA-256 hashes, reversible from the audit log |

For why each behaves this way, see [Callouts](../explanation/obsidian/callouts.md).

---

## Producer mechanics

Producer steps by callout:

| Callout | Deterministic step | LLM step |
| --- | --- | --- |
| `[!brief]` | Top-5 candidates ranked by: shared-citation overlap + embedding similarity + topic-tag intersection | Composes the "overlaps with / may contradict / new construct" narrative over the 5 candidates |
| `[!suggestions]` | Top-10 local candidates ranked deterministically by claim/source token overlap, truncated to 5 forward + 5 backward | Optional Librarian one-line explanation per candidate on the delegated card |
| `[!verification]` | Regex extraction of claim links and citekeys from the draft; writes the trace scaffold inline | Peer-reviewer judges whether the cited material supports the draft claims |

For the rationale behind the hybrid pattern, see [Callouts](../explanation/obsidian/callouts.md).

---

## Related

- Callout Manager plugin: [Obsidian plugins](obsidian-plugins.md)
- Computational toolbox (scoring functions): [Retrieval and analysis methods](computational-toolbox.md)
- Fleet-health dashboard: [explanation/dashboards/](../explanation/dashboards)
- The callout explanation page: [Callouts](../explanation/obsidian/callouts.md)
