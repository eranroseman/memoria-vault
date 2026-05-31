# Common pitfalls

Failure modes that recur across users of this kind of system. Most of them look like nothing is wrong — which is what makes them worth naming.

## Unpinned citekeys

**What happens:** You add a paper to Zotero, the agent ingests it, wikilinks form across the vault pointing to `mamykina2010sense`. Then you correct a metadata field in Zotero — the author's name, the year, a typo in the title — and Better BibTeX regenerates the citekey. Every wikilink in the vault is now broken, silently.

**The fix:** Pin all citekeys immediately after import, before doing anything else. In Zotero: select the item → right-click → Better BibTeX → Pin BibTeX key. A pinned key never regenerates.

**Why it's silent:** Obsidian doesn't warn you about broken wikilinks; it just shows them as unresolved. If you don't run the Linter's `graph-analyze` check, you won't notice until you're looking for the note.

## Vocabulary drift

**What happens:** You classify paper A with `topic: receptivity-detection` and paper B with `topic: opportune-moments`, not noticing they're the same concept. Your Dataview query for `receptivity-detection` then shows half your corpus on the topic, and you believe coverage is thin when it's actually adequate.

**The fix:** Before classifying a new paper, search for existing uses of the term you're about to use. Standardize before adding. See [vocabulary-discipline.md](vocabulary-discipline.md) for the full discipline.

## Synthesizing before triaging

**What happens:** You get excited by a paper and immediately write a claim note from it, before reviewing the `_proposed_classification` block. The Librarian's classification often surfaces project connections you hadn't noticed — connections that should appear in the claim note's `sources:` frontmatter and `relations:` links. Writing the claim first means you miss those connections.

**The fix:** Triage first (review and promote `_proposed_classification`, set `lifecycle: current`), then synthesize.

## Treating agent output as verified content

**What happens:** The Writer produces an answer note in response to a query. You read it, it looks good, and you copy a paragraph into your draft. Later you discover the agent cited paper X for a claim that paper X does not actually make — the semantic similarity was there, but the specific claim wasn't.

**The fix:** Agent output is a proposal, not a fact. Every citekey in an agent-generated note must be verified against the actual source before that claim appears in a draft. The Verifier's `cite-check` automates part of this, but it checks that the citekey resolves to a note, not that the note actually supports the claim.

## Inbox accumulation

**What happens:** The inbox (`10-inbox/`) grows week over week. Paper-notes sit at `lifecycle: proposed` for months. Answer notes accumulate without review. The system is capturing without synthesizing.

**Why it looks fine:** The dashboards are showing activity. Papers are being ingested. But the claim-note layer — which is where the actual knowledge is — isn't growing.

**The fix:** The inbox is a processing queue, not storage. Anything in `10-inbox/` older than 7 days is either worth promoting or worth discarding. During the weekly review, treat the reading-pipeline dashboard as an action queue, not a status display.

## Schema-migrate without dry-run

**What happens:** You run `schema-migrate` to rename a field across the vault. It applies silently to hundreds of notes. You discover the rename was wrong or incomplete only when Dataview queries start returning unexpected results.

**The fix:** Always run `schema-migrate` with `--dry-run` first. Review the proposed changes before applying. Run the migrate on a single folder first if uncertain. See [how-to-guides/maintenance/run-the-linter.md](../how-to-guides/maintenance/run-the-linter.md).

## MOC-as-folder-dump

**What happens:** You create a MOC for a topic and add every related note to it as a flat list. Over time it becomes hundreds of lines with no structure, annotations, or curation. You stop opening it because it takes too long to parse.

**The fix:** A MOC curates; it doesn't index. Each entry in a MOC's member list should have a brief annotation explaining why it belongs and what it contributes. The Dataview query handles volume; the static list handles meaning. If the static list is growing past 20–30 entries without structure, the MOC needs child MOCs or heavy pruning.

## Summary without synthesis

**What happens:** The Summary section of a paper-note contains: "This paper found that receptivity decreases when users are cognitively loaded. Methods were EMA. Sample was 23 participants." This is a summary, not synthesis. In 6 months it will be useless because it doesn't connect the finding to anything you already know.

**The fix:** Synthesis means connecting what the paper says to what you already know. If the Summary section contains no wikilinks to other notes, no tension with alternative views, and no statement of why this finding matters to your project, no synthesis has happened. At minimum: add the relation to the claim you hold going in, and add the question this finding opens up.

## What to automate vs what not to

A recurring mistake is asking the agent to do things that require judgment:

| Automate | Do not automate |
| --- | --- |
| API enrichment (`_enrichment` block) | Classification promotion (always human) |
| Cross-link candidate proposals | Merge and archive decisions |
| Lint checks (structural quality) | Synthesis quality assessment |
| Citation trace checks (Verifier) | Which papers to actually read |
| Discovery candidates (Librarian) | Whether a candidate is worth reading |

The agent reduces friction at the mechanical layer. Judgment remains with the human at every decision point.
