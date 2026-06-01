
# How to write a claim note

Distill a discussed source into a single, durable claim in `30-synthesis/01-claims/`. One claim per note; no more than 2–3 claims per source.

## Prerequisites

- The source has been discussed and you've decided it yields a claim ([discuss-a-paper.md](discuss-a-paper.md))
- The Writer profile is installed (for optional prose assistance)
- The Verifier profile is installed (for the similarity check)

## Steps

**1. Run the similarity check first.**

Before creating the note, check if a near-duplicate already exists:

```bash
hermes -p memoria-verifier chat -s similarity-check
# then, in the session:
/similarity-check "<one-sentence statement of your claim>"
```

If the top result is above ~0.8 similarity, review that existing note. Decide whether to extend it instead of creating a new one, or confirm the claim is genuinely distinct.

**2. Open the claim note template.**

Cmd-P → Memoria: write claim note

This opens `30-synthesis/01-claims/` with the claim-note template pre-populated.

**3. Name the file with the claim as the title.**

The filename *is* the claim: `receptivity-decreases-under-high-cognitive-load.md`, not `receptivity.md` or `mamykina-claim.md`. A topic stub is not a claim note.

**4. Write the claim in the note body.**

One to three sentences, in your own words. The claim should stand alone — a reader with no access to the source should understand what it asserts. Do not quote the paper directly.

**5. Cite the source.**

In the `Sources` section, link the source note: `[[mamykina2010sense]]`. If multiple sources support this claim, list them all.

**6. Set the maturity and lifecycle.**

```yaml
maturity: seedling
lifecycle: current
```

New claims start at `seedling`. As cross-links accumulate (other notes linking to or from this claim), maturity advances to `budding` and eventually `evergreen`.

**7. Add relations if applicable.**

If the claim contradicts an existing claim:

```yaml
relations:
  contradicts:
    - "[[other-claim-note]]"
```

If it supports an existing claim:

```yaml
relations:
  supports:
    - "[[other-claim-note]]"
```

If it supersedes an existing claim (replaces it as current belief):

```yaml
relations:
  superseded_by: "[[this-new-claim]]"   # add this to the OLD note, not this one
```

**8. Optionally, get Writer assistance for phrasing or cross-links.**

```bash
hermes -p memoria-writer chat -s draft
# then, in the session:
/draft "suggest related notes for: <claim statement>" --context 30-synthesis/01-claims/<new-note>.md
```

The Writer can suggest links to existing claim notes but cannot author the claim itself — that's yours.

## Verify

- The file exists at `30-synthesis/01-claims/<claim-title>.md`
- `maturity: seedling` and `lifecycle: current` are set
- At least one source citekey is linked in the `Sources` section
- The `discuss` card for the source is now closed (auto-closed by the git hook on file creation)
- The note appears in the "seedling claims" Dataview view

## Related

**How-to**

- Previous step: [Discuss a paper](discuss-a-paper.md)
- When the claim reaches `evergreen`: [Promote a claim](promote-a-claim.md)

**Reference**

- Linking patterns: [linking.md](../../reference/linking.md)
- Frontmatter schema: [frontmatter.md](../../reference/frontmatter.md)

**Explanation**

- Why each section functions as knowledge: [note-body-structure.md](../../explanation/knowledge/note-body-structure.md)
- The summary-without-synthesis pitfall: [common-pitfalls.md](../../explanation/knowledge/common-pitfalls.md)
