---
title: Common pitfalls
parent: Knowledge
grand_parent: Explanation
nav_order: 6
---

# Common pitfalls

Failure modes that recur in research vaults built this way. Most of them look like nothing is wrong — which is what makes them worth naming. They are ordered by **severity of outcome**: the ones that silently corrupt trusted content come first; the localized, recoverable ones come last. The closing section names the general principle underneath the worst of them.

## Treating agent output as verified content

The Writer (the background agent that drafts prose — see [Glossary](../../reference/glossary.md)) produces a draft in response to a query. It looks good. A paragraph gets copied into a composition. Later it emerges that the agent cited paper X for a claim that paper X does not actually make — the semantic similarity was there, but the specific claim wasn't.

This is the failure the Peer-reviewer (the background agent that checks drafts and citations — see [Glossary](../../reference/glossary.md)) exists to catch, but its `verify-check-citation` pass only verifies that citekeys resolve — it doesn't verify that the source actually supports the specific claim in the prose. That final check is irreducibly human. The system's design treats agent output as a proposal that requires verification, not a draft that requires only polish.

## Unpinned citekeys

You add a paper to Zotero, the ingest operation catalogs it, wikilinks form across the vault pointing to `mamykina2010sense`. Then you correct a metadata field in Zotero — the author's name, the year, a typo in the title — and Better BibTeX regenerates the citekey. Every wikilink in the vault is now broken, silently.

The reason this is silent: Obsidian doesn't warn about broken wikilinks; it just shows them as unresolved. Without the Linter's `lint:analyze-graph` check, the breakage is invisible until you're actively looking for a specific note. The failure compounds over time because new notes continue linking to the broken citekey, not knowing it has changed.

The root cause is that Better BibTeX treats citekeys as derived from metadata, not as stable identifiers. Pinning a key tells it to treat the key as the identifier, not the derivation. See [Capture and ingest a source](../../how-to-guides/library/capture-and-ingest.md) for the pinning procedure.

## Vocabulary drift

The same concept gets two names across notes — `topics: receptivity-detection` on one claim, `topics: opportune-moments` on another — so a query returns half the corpus and the PI infers thin coverage that isn't real. The failure is invisible because it produces no errors, only incomplete results, and the Linter cannot catch it until a canonical vocabulary exists. The full scenario, why consolidation is deliberately deferred, and how the failure compounds are in [Vocabulary discipline](vocabulary-discipline.md).

## Summary without synthesis

A source note's Summary section records findings and methods but contains no wikilinks to related notes, no tension with alternative views, and no statement of why the finding matters to current work. In six months it is useless because it doesn't connect to anything.

The failure is that summary and synthesis look identical in the moment of writing but diverge drastically in usefulness over time. A summary records what the source says. Synthesis connects what the source says to what you already believe — it is what makes the note compounding rather than merely stored.

## Distilling before triaging

The **Librarian** (the background agent that catalogs and classifies sources — see [Glossary](../../reference/glossary.md)) proposes a classification that often surfaces project connections that weren't obvious at intake — connections that should appear in the claim's `sources:` frontmatter and `links:`. Writing the claim before reviewing that proposal means missing those connections, because the classification pass is also when the system discovers what the source has to do with your existing work.

The deeper reason: classification (automated, audited, correctable) is how the system integrates a source into the existing graph. Bypassing it produces a claim that cites a paper but isn't connected to the web of context that would have been visible from the review.

## Queue accumulation

The Inbox grows week over week. Source notes sit at `lifecycle: proposed` for months. Candidate cards accumulate without triage. The dashboards show activity — sources are being catalogued — but the claim layer isn't growing.

This is a systemic failure because the Inbox and the reading queue are processing surfaces, not storage. The vault is compounding only when sources move through reading into claims. A queue that grows without shrinking is capture without synthesis — a sophisticated reading list, not a knowledge system. The weekly review exists precisely to catch this before it hardens into months of backlog.

## Hub-as-folder-dump

A hub grows to hundreds of lines with no structure, annotations, or curation. It becomes unusable because it takes too long to parse.

The structural issue is a confusion between indexing and curating. A hub's value is in what it leaves out and how it annotates what it keeps — it is a perspective on a topic, not an enumeration. When a hub becomes an index, it duplicates what a Base already does automatically. The embedded query handles volume; the static curated list handles meaning. When the curated list grows past 20–30 entries without structure, the hub needs child hubs or heavy pruning.

## The automation boundary

The failures above share a root, and naming it directly is the best defense. A recurring class of mistake is asking agents to make judgment calls. The distinction between what the agent can do reliably and what requires human judgment is not a question of capability — it is a question of what kind of decision is being made.

Tasks like API enrichment, link-candidate proposals, structural lint checks, and citation trace checks are deterministic or can be checked deterministically. Promotion, merge and archive decisions, synthesis quality assessment, and decisions about which papers to read are not — they require epistemic judgment that the agent cannot claim on behalf of the PI. Asking the agent to do the latter produces outputs that look authoritative but aren't, which is the failure mode the system's review gate (the human approval step before content is trusted — see [Glossary](../../reference/glossary.md)) exists to prevent.

For the explicit mapping of tasks to their appropriate owner, see [Profile capabilities](../../reference/profile-capabilities.md).

---

## Related

- Why promotion is gated: [Why promotion is gated](promotion-and-gated-zones.md)
- The fix for compound notes: [Refactor claim notes](../../how-to-guides/knowledge/refactor-claim-notes.md)
- Catching unverified agent output: [Run a retraction sweep](../../how-to-guides/operate/run-a-retraction-sweep.md)
- Lane (a background agent's execution path on the board — see [Glossary](../../reference/glossary.md)) permissions referenced here: [Profile capabilities](../../reference/profile-capabilities.md)
