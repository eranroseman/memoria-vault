
# How to find new sources

Run a discovery search — forward citations, backward citations, or concept-driven — and route candidates to the inbox for your review.

## Prerequisites

- At least one ingested paper note to use as a seed (`--source` flag)
- The Librarian profile installed with `OPENALEX_EMAIL` and API keys filled

## Steps

**1. Start a Librarian session with the `find` skill.**

```bash
hermes -p memoria-librarian chat -s find
```

**2. Choose a search mode and run it.**

**Forward citations** — papers that *cite* your seed (what built on this work):

```text
/find --source <citekey> --depth 1
```

**Backward citations** — papers *cited by* your seed (what this work builds on):

```text
/find --source <citekey> --direction backward --depth 1
```

**Concept search** — papers matching a research question (uses query rewrite + hybrid retrieval):

```text
/find --query "just-in-time adaptive interventions receptivity" --limit 20
```

Use `--depth 1` for first-order connections; `--depth 2` for broader sweeps (significantly more candidates).

**3. Review the candidates queue.**

After the session exits, open `10-inbox/03-candidates/` in Obsidian. Each candidate is a lightweight note with a title, abstract snippet, and the reason it was surfaced.

**4. Triage each candidate — include or exclude.**

For each candidate note:

- **Include:** Add the source to Zotero, pin the citekey, let the `.bib` auto-export trigger ingest. Delete the candidate note once the real source note exists.
- **Exclude:** Add `excluded: true` and a brief reason to the candidate note's frontmatter. The Linter tracks exclusion coverage — an empty `reason` field is flagged as incomplete.

Don't leave candidates undecided indefinitely. The weekly review surfaces the count.

## Verify

- `10-inbox/03-candidates/` contains candidate notes from the search
- Each candidate has been either added to Zotero or marked `excluded: true` with a reason

## Related

- After including: [Capture and ingest a source](capture-and-ingest.md)
- Gap candidates from Verify also land here: [Verify and revise a draft](../writing/verify-and-revise.md)
- Weekly review (step 3 — process discovery candidates): [run-the-weekly-review.md](../maintenance/run-the-weekly-review.md)
- The profile running the find: [librarian.md](../../explanation/profiles/librarian.md)
- Pre-ingest screening (now part of adopt-on-demand): [ADR-16](../../../project-files/decisions/16-adopt-on-demand-for-reviews.md)
