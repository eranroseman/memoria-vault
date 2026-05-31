
# How to verify and revise a draft

Read the verification callout after each commit, address the flagged gaps, and loop until the draft is clean or remaining gaps are accepted.

## Prerequisites

- A draft section committed to git in `40-workbench/<project>/04-drafts/`
- The Verifier profile installed

## Steps

**1. Open the draft in Obsidian after committing.**

After a `git commit`, the Verify hook fires automatically and updates the `[!verification]` callout at the top of the draft file. Open the draft.

**2. Read the verification callout.**

The callout shows one of three statuses:

| Status | Meaning |
| --- | --- |
| `status: clean` | All citations are supported and traceable |
| `status: gaps` | One or more claims lack supporting source notes |
| `status: superseded` | A cited note is marked `superseded_by` — the draft cites outdated thinking |

**3. Address each gap.**

For each flagged item:

- **Missing source note:** The draft cites a citekey that has no note in `20-sources/`. Ingest the source first ([capture-and-ingest.md](../sources/capture-and-ingest.md)), or remove the citation if it was a placeholder.
- **Unsupported claim:** A statement has no citekey. Either add a citation or rewrite the claim as explicitly stated as the author's view (no citation needed).
- **Superseded citation:** The draft cites `[[old-claim]]` which has `superseded_by: [[new-claim]]`. Update the draft to cite the new claim note instead.

**4. Run Revise for larger gaps** (optional).

For systematic gap-closing rather than line edits, use the Revise workflow:

```bash
hermes -p memoria-writer chat -s revise
# then, in the session:
/revise --draft 40-workbench/<project>/04-drafts/<section>.md \
        --verification 40-workbench/<project>/04-drafts/<section>.md
```

The Writer reads the verification callout and suggests specific edits to close each gap. Review and accept edits manually.

**5. Re-commit after revisions.**

```bash
git add 40-workbench/<project>/04-drafts/<section>.md
git commit -m "revise: address verification gaps in <section>"
```

The verify hook fires again. Repeat steps 2–5 until the callout shows `status: clean` or you explicitly accept remaining gaps.

**6. Accept a gap without closing it** (when appropriate).

If a gap represents a genuine open question you're flagging in the paper rather than a failure, add to the draft's frontmatter:

```yaml
accepted_gaps:
  - "no empirical support for X — acknowledged as a limitation"
```

The Verifier will not flag accepted gaps on subsequent commits.

## Verify

- `[!verification]` callout shows `status: clean` or lists only accepted gaps
- No `superseded_by` citations remain in active drafts

## Related

- Previous step: [Draft with the Writer](draft-with-writer.md)
- Next step: [Export a draft](export-a-draft.md)
- Verify workflow reference: [how-to/workflows/downstream/verify.md](../../how-to-guides/writing/verify-and-revise.md)
- Revise workflow reference: [how-to/workflows/downstream/revise.md](../../how-to-guides/writing/verify-and-revise.md)
