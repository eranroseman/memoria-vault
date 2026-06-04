---
name: retraction-check
description: "Check each paper-note's DOI against retraction databases (Open Retractions + CrossRef) and flag disagreements with the note's pub_status. Deterministic; dry-run; never auto-flips."
version: 1.0.0
author: Memoria
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [Research, Retraction, CrossRef, Verification, Integrity]
    related_skills: [pyzotero]
---

# retraction-check

Scan paper-notes for retractions and flag any source whose retraction status disagrees with
its vault `pub_status`. **Fully deterministic** — HTTP lookups + DOI match + boolean
comparison; no LLM. **Dry-run by default; never silently updates a note.**

## When to Use

- **Before export** — sweep the paper-notes a draft references so a retraction or
  expression-of-concern surfaces before the draft leaves the workbench.
- **Monthly** — run a periodic sweep over `20-sources/01-papers/` (optionally `--since` the
  last sweep) to catch newly retracted sources in the existing library.
- **On a flagged DOI** — re-check a single source when a human flags it or when its
  `pub_status` is in doubt.

## Quick reference

| Action | Call |
|--------|------|
| Check one DOI (Open Retractions) | `GET https://openretractions.com/api/doi/{doi}/data.json` → `.retracted` (bool) |
| Cross-check (CrossRef) | `GET https://api.crossref.org/works/{doi}` → look for `update-to` with `type: retraction` |
| Resolve vault DOIs | the `pyzotero` skill / read `doi:` from paper-note frontmatter |

## Inputs

- `--scope <path>` (optional) — limit to a folder (default: all of `20-sources/01-papers/`).
- `--since <date>` (optional) — only notes with `enriched_date`/`updated` after this date.
- (Always report-only — there is no write mode.)

## Procedure

1. **Collect DOIs.** Read `doi` from each paper-note's frontmatter in scope (skip notes with no DOI).
2. **Query.** For each DOI, GET the Open Retractions API; on a hit (`retracted: true`) record it. Optionally cross-check CrossRef's retraction metadata for corroboration.
3. **Compare.** Diff each result against the note's `pub_status`:
   - external `retracted` but note is not `retracted`/`expression-of-concern` → **flag**;
   - note marked `retracted` but external says active → flag (possible stale/incorrect).
4. **Report.** Write a verification report to `40-workbench/*/05-verification/` (or surface as a board comment) listing each flagged citekey, DOI, the external status, and the current `pub_status`. **Never set `pub_status` yourself** — the human updates it.
5. Optionally spawn gap/attention cards in `10-inbox/03-candidates/` for flagged items.

## Rules

- **Flag, don't fix.** The agent never flips `pub_status: retracted`; that is a human decision (matches the Verifier's "mechanical first, interpretive never" rule).
- Deterministic: the same DOIs + same external state produce the same report every run.
- External HTTP is allowed only under the Verifier's `external_api_policy: explicit_only`.
- Be polite to the APIs (include a contact `mailto` on CrossRef; rate-limit batches).

## Verification

- A clean run reports **zero `pub_status` disagreements** — every in-scope DOI's external
  retraction state matches the note's `pub_status`, and nothing is flagged.
- **Deterministic** — re-running the same DOIs against the same external state yields
  identical output every time.
- **Never auto-flips a note** — the check only reports; a human updates `pub_status`. A run
  that wrote to a note would be a defect, not a pass.
