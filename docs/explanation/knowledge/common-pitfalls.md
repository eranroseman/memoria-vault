---
title: Common pitfalls
parent: Knowledge
grand_parent: Explanation
nav_order: 6
---

# Common pitfalls

Failure modes that recur in research vaults built this way. Most of them look like nothing is wrong — which is what makes them worth naming. They are ordered by **severity of outcome**: the ones that silently corrupt checked content come first; the localized, recoverable ones come last. The closing section names the general principle underneath the worst of them.

## Treating agent output as verified content

The future Writer posture or a generative draft operation produces prose from
checked evidence. It looks good. A paragraph gets copied into a composition.
Later it emerges that the draft cited paper X for a claim that paper X does not
actually make - the semantic similarity was there, but the specific claim
wasn't.

This is the failure the Peer-reviewer posture and verification operations exist
to catch, but citation-resolution checks only verify that citekeys resolve; they
do not prove that the source actually supports the specific claim in the prose.
That final check is irreducibly human. The system's design treats machine output
as a proposal that requires verification, not a draft that requires only polish.

## Unpinned citekeys

You add a paper to Zotero, the ingest operation catalogs it, wikilinks form across the vault pointing to `mamykina2010sense`. Then you correct a metadata field in Zotero — the author's name, the year, a typo in the title — and Better BibTeX regenerates the citekey. Every wikilink in the vault is now broken, silently.

The reason this is silent: Obsidian doesn't warn about broken wikilinks; it just shows them as unresolved. Without the Linter's `lint:analyze-graph` check, the breakage is invisible until you're actively looking for a specific note. The failure compounds over time because new notes continue linking to the broken citekey, not knowing it has changed.

The root cause is that Better BibTeX treats citekeys as derived from metadata, not as stable identifiers. Pinning a key tells it to treat the key as the identifier, not the derivation. See [Capture and ingest a source](../../how-to-guides/library/capture-and-ingest.md) for the pinning procedure.

## Vocabulary drift

The same concept gets two names across notes — `topics: receptivity-detection` on one claim, `topics: opportune-moments` on another — so a query returns half the corpus and the PI infers thin coverage that isn't real. The failure is invisible because it produces no errors, only incomplete results, and the Linter cannot catch it until a canonical vocabulary exists. The full scenario, why consolidation is deliberately deferred, and how the failure compounds are in [Vocabulary discipline](vocabulary-discipline.md).

## Summary without synthesis

A source summary records findings and methods but contains no wikilinks to
related notes, no tension with alternative views, and no statement of why the
finding matters to current work. In six months it is useless because it doesn't
connect to anything.

The failure is that summary and synthesis look identical in the moment of writing but diverge drastically in usefulness over time. A summary records what the source says. Synthesis connects what the source says to what you already believe — it is what makes the note compounding rather than merely stored.

## Distilling before triaging

The Librarian operation posture proposes a classification that often surfaces
project connections that were not obvious at intake - connections that should
appear in the note's `source_id`, `evidence_set`, `citations`, `topics`, and
typed `links`. Writing the note before reviewing that proposal means missing
those connections, because the classification pass is also when the system
discovers what the Work has to do with your existing graph.

The deeper reason: classification (automated, audited, correctable) is how the system integrates a source into the existing graph. Bypassing it produces a claim that cites a paper but isn't connected to the web of context that would have been visible from the review.

## Queue accumulation

The Inbox grows week over week. Source rows sit unchecked for months. Candidate
attention accumulates without triage. The dashboards show activity - sources are
being catalogued - but the claim layer is not growing.

This is a systemic failure because the Inbox and the reading queue are processing surfaces, not storage. The vault is compounding only when sources move through reading into claims. A queue that grows without shrinking is capture without synthesis — a sophisticated reading list, not a knowledge system. The weekly review exists precisely to catch this before it hardens into months of backlog.

## Hub-as-folder-dump

A hub grows to hundreds of lines with no structure, annotations, or curation. It becomes unusable because it takes too long to parse.

The structural issue is a confusion between indexing and curating. A hub's value is in what it leaves out and how it annotates what it keeps — it is a perspective on a topic, not an enumeration. When a hub becomes an index, it duplicates what a Base already does automatically. The embedded query handles volume; the static curated list handles meaning. When the curated list grows past 20–30 entries without structure, the hub needs child hubs or heavy pruning.

## The automation boundary

The failures above share a root, and naming it directly is the best defense. A recurring class of mistake is asking agents to make judgment calls. The distinction between what the agent can do reliably and what requires human judgment is not a question of capability — it is a question of what kind of decision is being made.

Tasks like API enrichment, link-candidate proposals, structural lint checks, and citation trace checks are deterministic or can be checked deterministically. Promotion, merge and archive decisions, synthesis quality assessment, and decisions about which papers to read are not — they require epistemic judgment that the agent cannot claim on behalf of the PI. Asking the agent to do the latter produces outputs that look authoritative but aren't, which is why Memoria separates checked materialization from PI attention and curation.

For the explicit mapping of current operation surfaces, see
[Operations](../../reference/operations.md). For the no-installed-profile
boundary, see Installed profiles.

---

## Related

- Why promotion is gated: [Why promotion is gated](promotion-and-gated-zones.md)
- The repair surface for overloaded note graphs: [Link checked notes](../../how-to-guides/knowledge/link-related-claims.md)
- Catching unverified agent output: [Run a retraction sweep](../../how-to-guides/operate/run-a-retraction-sweep.md)
- Current operation surfaces: [Operations](../../reference/operations.md)
