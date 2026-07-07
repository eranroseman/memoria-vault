---
title: Evidence sets
parent: Agents and control
grand_parent: Reference
nav_order: 21
---

# Evidence sets

Evidence sets are the draft-time warrant contract for composed project prose.
The durable source is the inline marker on a draft claim:

```text
%%ev: ev-1234abcd type=single-span state=complete review=false items=source-alpha#^p0001%%
```

The marker owns the ordered `items=` list. SQLite table `evidence_sets` is
derived state rebuilt from those markers.

| Field | Meaning |
| --- | --- |
| `id` | Mint-once `ev-<8hex>` identifier. |
| `items` | `work_id#^pNNNN` source-span refs, nested `ev-<8hex>` ids, or `code-warrant:<run_id>:<artifact_id>:<sha256>` refs. |
| `type` | Derived as `single-span`, `multi-span`, `multi-hop`, `implicit`, or `computed`. |
| `state` | `complete` only when every item resolves. |
| `review_required` | `true` for implicit or multi-hop evidence, independent of `state`. |

Source-span refs use stable `work_id`, never citekeys. Citekeys are rendered
only during export.

`computed` is derived when a marker contains a `code-warrant` item. It is
`complete` only while the referenced code run succeeded and the current output
hash still matches the marker. Running code warrants the output provenance; it
does not make the research claim true.

Draft verification reports `evidence-incomplete` and `review_required` markers.
The PI records a disposition with:

```bash
memoria project resolve-evidence <project> --evidence-id ev-1234abcd --decision accept
```

The disposition is journal provenance; it does not edit the marker or assert
that the claim is true.
