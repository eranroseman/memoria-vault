# Common pitfalls

Failure modes that recur in research vaults built this way. Most of them look like nothing is wrong — which is what makes them worth naming. They are ordered by **severity of outcome**: the ones that silently corrupt trusted content come first; the localized, recoverable ones come last. The closing section names the general principle underneath the worst of them.

## Treating agent output as verified content

The Writer produces an answer note in response to a query. It looks good. A paragraph gets copied into a draft. Later it emerges that the agent cited paper X for a claim that paper X does not actually make — the semantic similarity was there, but the specific claim wasn't.

This is the failure the Verifier exists to catch, but the Verifier's `cite-check` only verifies that citekeys resolve to notes — it doesn't verify that the note actually supports the specific claim in the prose. That final check is irreducibly human. The system's design treats agent output as a proposal that requires verification, not a draft that requires only polish.

## Unpinned citekeys

You add a paper to Zotero, the agent ingests it, wikilinks form across the vault pointing to `mamykina2010sense`. Then you correct a metadata field in Zotero — the author's name, the year, a typo in the title — and Better BibTeX regenerates the citekey. Every wikilink in the vault is now broken, silently.

The reason this is silent: Obsidian doesn't warn about broken wikilinks; it just shows them as unresolved. Without the Linter's `graph-analyze` check, the breakage is invisible until you're actively looking for a specific note. The failure compounds over time because new notes continue linking to the broken citekey, not knowing it has changed.

The root cause is that Better BibTeX treats citekeys as derived from metadata, not as stable identifiers. Pinning a key tells it to treat the key as the identifier, not the derivation. See [how-to-guides/sources/capture-and-ingest.md](../../how-to-guides/sources/capture-and-ingest.md) for the pinning procedure.

## Vocabulary drift

You classify paper A with `topic: receptivity-detection` and paper B with `topic: opportune-moments`, not noticing they name the same concept. The Dataview query for `receptivity-detection` returns half the corpus on the topic. You conclude coverage is thin; it isn't.

The failure is invisible because it produces no errors — just incomplete query results. Research directions get shaped by a false gap signal. The Linter's `schema-check` detector can catch drift from a defined vocabulary, but only after the vocabulary is defined. Drift before that point is entirely silent. See [vocabulary-discipline.md](vocabulary-discipline.md) for the reasoning behind deferred vocabulary consolidation.

## Summary without synthesis

A paper-note Summary section records findings and methods but contains no wikilinks to related notes, no tension with alternative views, and no statement of why the finding matters to current work. In six months it is useless because it doesn't connect to anything.

The failure is that summary and synthesis look identical in the moment of writing but diverge drastically in usefulness over time. A summary records what the paper says. Synthesis connects what the paper says to what you already believe — it is what makes the note compounding rather than merely stored.

## Synthesizing before triaging

The Librarian's `_proposed_classification` block often surfaces project connections that weren't obvious at ingest time — connections that should appear in the claim note's `sources:` frontmatter and `relations:` links. Writing the claim note before reviewing that block means missing those connections, because the classification pass is also when the system discovers what the source has to do with your existing work.

The deeper reason: classification is how the system integrates a source into the existing graph. Bypassing it produces a claim note that cites a paper but isn't connected to the web of context that would have been visible from the `_proposed_classification` review.

## Inbox accumulation

The inbox (`10-inbox/`) grows week over week. Paper-notes sit at `lifecycle: proposed` for months. Answer notes accumulate without review. The dashboards show activity — papers are being ingested — but the claim-note layer isn't growing.

This is a systemic failure because the inbox is a processing queue, not storage. The vault is compounding only when sources move through classification into claim notes. An inbox that grows without shrinking is capture without synthesis — a sophisticated reading list, not a knowledge system. The weekly review exists precisely to catch this before it hardens into months of backlog.

## MOC-as-folder-dump

A MOC grows to hundreds of lines with no structure, annotations, or curation. It becomes unusable because it takes too long to parse.

The structural issue is a confusion between indexing and curating. A MOC's value is in what it leaves out and how it annotates what it keeps — it is a perspective on a topic, not an enumeration. When a MOC becomes an index, it duplicates what Dataview already does automatically. The Dataview query in the MOC body handles volume; the static curated list handles meaning. When the curated list grows past 20–30 entries without structure, the MOC needs child MOCs or heavy pruning.

## The automation boundary

The failures above share a root, and naming it directly is the best defense. A recurring class of mistake is asking agents to make judgment calls. The distinction between what the agent can do reliably and what requires human judgment is not a question of capability — it is a question of what kind of decision is being made.

Tasks like API enrichment, link-candidate proposals, structural lint checks, and citation trace checks are deterministic or can be checked deterministically. Classification promotion, merge and archive decisions, synthesis quality assessment, and decisions about which papers to read are not — they require epistemic judgment that the agent cannot claim on behalf of the human. Asking the agent to do the latter produces outputs that look authoritative but aren't, which is the failure mode the system's review gate exists to prevent.

For the explicit mapping of tasks to their appropriate owner, see [reference/profiles.md](../../reference/profiles.md).
