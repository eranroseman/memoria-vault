---
title: Common pitfalls
parent: Knowledge
grand_parent: Explanation
nav_order: 6
---

# Common pitfalls

Failure modes that recur in research vaults built this way. Most of them look like nothing is wrong — which is what makes them worth naming. They are ordered by **severity of outcome**: the ones that silently corrupt checked content come first; the localized, recoverable ones come last. The closing section names the general principle underneath the worst of them.

## Treating agent output as verified content

**Failure:** generated prose cites a real paper for a claim the paper does not
make. The draft looks polished because semantic similarity was enough to fool
the generator.

**Why it happens:** citation-resolution checks prove that citekeys resolve. They
do not prove that a source supports the exact claim in the prose.

**What prevents it:** the Peer-reviewer posture and verification operations
surface trace problems, but the PI still owns the final support judgment.
Machine output remains a proposal, not checked content waiting only for polish.

## Unpinned citekeys

You import a BibTeX or CSL export from Zotero, the ingest operation catalogs it,
and draft citations or bibliography exports use `mamykina2010sense` as the
citekey alias. Then you correct a metadata field in Zotero — the author's name,
the year, a typo in the title — and Better BibTeX regenerates the citekey. The
stable `work_id` still points at the Work row, but citation/export workflows that
depend on the old alias can miss or render unresolved citations until you
re-import or repair the alias.

**Failure:** a corrected Zotero record regenerates a citekey, and citation or
export workflows keep looking for the old alias.

**Why it happens:** the durable Work identity still works, so the graph looks
healthy. The break appears only at the citation/export edge.

**What prevents it:** pin citekeys in Better BibTeX so the key is treated as an
identifier, not a metadata derivation. See [Set up Zotero](../../how-to-guides/setup/set-up-zotero.md).

## Vocabulary drift

**Failure:** the same concept gets two names, such as
`topics: receptivity-detection` and `topics: opportune-moments`, so filtered
queries return only part of the corpus.

**Why it happens:** off-vocabulary values are well-formed strings. They produce
incomplete results, not errors.

**What prevents it:** maintain the controlled vocabulary and consolidate variants
once the intended term is clear. The staged stabilization model is in
[Vocabulary discipline](vocabulary-discipline.md).

## Summary without synthesis

**Failure:** a source summary records findings and methods but links to nothing,
names no tension, and says nothing about why the finding matters.

**Why it happens:** summary and synthesis look similar while writing. Over time
they diverge: summary stores what the source says; synthesis connects it to what
the vault already knows.

**What prevents it:** make every durable note earn its place through links,
tensions, or a claim about current work.

## Distilling before triaging

**Failure:** a note cites a paper but misses the `work_id`, `topics`, typed
links, evidence markers, or citation payloads that would connect it to current
work.

**Why it happens:** classification is where the system discovers how a Work
touches the existing graph. Writing before reviewing that proposal bypasses the
integration step.

**What prevents it:** review classification before distilling. It is automated,
audited, and correctable; skipping it turns a claim into an isolated citation.

## Queue accumulation

**Failure:** the Inbox grows, source rows sit unchecked, and candidate attention
ages without triage while dashboards still show catalog activity.

**Why it happens:** Inbox and reading queues are processing surfaces, not
storage. A queue that grows without shrinking is capture without synthesis.

**What prevents it:** the weekly review keeps queues moving before they become a
months-long reading list.

## Hub-as-folder-dump

**Failure:** a hub grows into hundreds of unstructured lines and takes too long
to parse.

**Why it happens:** the hub has become an index. Query surfaces already handle
volume; a hub should curate meaning.

**What prevents it:** prune hard, annotate what remains, or create child hubs
when a curated list grows past roughly 20-30 entries.

## The automation boundary

The failures above share one root: asking agents to make judgment calls.

API enrichment, link-candidate proposals, structural lint checks, and citation
trace checks are deterministic or checkable. Promotion, merge/archive decisions,
synthesis quality, and reading priorities require epistemic judgment. Agents can
prepare those decisions; they cannot make them on behalf of the PI. That is why
Memoria separates checked materialization from PI attention and curation.

For the explicit mapping of current operation surfaces, see
[Operations](../../reference/commands-and-transports/operations.md).

---

## Related

- Why promotion is gated: [Why promotion is gated](promotion-and-gated-zones.md)
- The repair surface for overloaded note graphs: [Link checked notes](../../how-to-guides/knowledge/link-checked-notes.md)
- Catching unverified agent output: [Run a retraction sweep](../../how-to-guides/operate/run-a-retraction-sweep.md)
- Current operation surfaces: [Operations](../../reference/commands-and-transports/operations.md)
