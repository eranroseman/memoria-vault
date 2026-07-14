---
title: Evidence sets
parent: Control and policy
nav_order: 3
grand_parent: Reference
---

# Evidence sets

Evidence sets are the draft-time warrant contract for composed project prose.
The durable source is the inline marker on a draft claim:

```text
%%ev: ev-1234abcd type=single-span state=complete review=false items=source-alpha#^p0001%%
```

Only a plain, top-level Markdown paragraph claim can establish a new binding.
Markers and block anchors inside Markdown code, headings, HTML comments or
elements, frontmatter, title metadata, reference definitions, fenced Divs,
multiline inline constructs, tables, line blocks, blockquote, list, or
definition-list containers cannot mint a new evidence ID. If they repeat an
existing ID, Memoria retains them as unbound and blocks draft export.
A duplicate group containing a direct visible marker or an ID already in the
immutable ledger is unbound and blocks export for every draft that contains it.
Hidden-only, never-bound occurrences stay nonbinding and cannot mint an ID.

Memoria fails closed when renderer syntax can make a line ambiguous: raw HTML
elements, raw TeX or math syntax, Pandoc attributes, footnote definitions,
initial MultiMarkdown-style metadata, abbreviation definitions, and table
syntax make the whole draft ineligible to mint a new binding. This conservative
rule also applies when the syntax appears in otherwise literal code. Ordinary
literal-code delimiters do not taint unrelated visible prose, but controls
inside code are never direct evidence. These rules avoid giving a hidden
renderer construct an evidence binding that only visible prose may establish.

The marker owns the ordered `items=` list. SQLite table `evidence_sets` is
derived active state rebuilt from those markers. A separate `evidence_bindings`
ledger records the first observed appearance of each evidence ID: its anchored
claim hash when resolvable, or `null` when it is not. The ledger survives marker
removal, so a reappearing ID always retains its original binding.

| Field | Meaning |
| --- | --- |
| `id` | Mint-once `ev-<8hex>` identifier. |
| `items` | `work_id#^pNNNN` source-span refs, nested `ev-<8hex>` ids, or `code-warrant:<run_id>:<artifact_id>:<sha256>` refs. |
| `type` | Derived as `single-span`, `multi-span`, `multi-hop`, `implicit`, or `computed`. |
| `state` | `complete` only when every item resolves. |
| `review_required` | `true` for implicit or multi-hop evidence, independent of `state`. |
| `block_text_sha256` | The mint-once SHA-256 binding copied from the immutable `evidence_bindings` ledger; nullable only to represent an unbound, fail-closed row. |

The hash covers the Markdown paragraph or block containing the matching
`^blk-<8hex>` anchor. Before hashing, Memoria removes that anchor and its
`%%ev: ... %%` control marker, then trims outer whitespace. The first observed
ID records that hash, or `null` if the block cannot resolve. Later rebuilds,
including removal and reappearance of the marker, never refresh that value.
Changing the claim therefore cannot silently bless the edit with a new binding.

The ledger establishes only this identity-to-text binding. Markers remain the
source for active evidence items; making SQLite authoritative for all evidence
truth is deferred and unshipped.

Source-span refs use stable `work_id`, never citekeys. Citekeys are rendered
only during export.

`computed` is derived when a marker contains a `code-warrant` item. It is
`complete` only while the referenced code run succeeded and the current output
hash still matches the marker. Running code warrants the output provenance; it
does not make the research claim true.

Draft verification reports `evidence-incomplete` and `review-required` markers.
It also reports `evidence-text-drift` when current claim text differs from the
stored binding, and `evidence-text-unbound` when the stored binding or current
anchor cannot resolve. Either hash finding blocks draft export.

Only the PI can record a disposition:

```bash
memoria project resolve-evidence <project> --evidence-id ev-1234abcd --decision accept
```

The disposition is journal provenance; it does not edit the marker or assert
that the claim is true. It can clear evidence-completeness review, but it cannot
clear text drift or an unbound claim.

## Related

- Where markers are minted and resolved during drafting: [Compose a draft](../../how-to-guides/project/compose-a-draft.md)
- How resolved markers become citations at export, and what blocks export: [Export routes and formats](../pipelines-and-io/export.md)
- Why the engine may verify markers but not decide a claim is true: [Why the write half is bounded](../../explanation/rationale/boundaries/why-write-half-is-bounded.md)
- The principle behind the immutable binding ledger: [Design principles](../../explanation/rationale/foundations/design-principles.md) (Provenance everywhere)
