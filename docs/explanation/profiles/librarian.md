---
topic: profiles
---

# Librarian — design summary

**Runtime contract.** Full prompt and operational details live at `.memoria/profiles/memoria-librarian/SOUL.md` in the starter vault.

## Mission

Librarian is the system's intake layer — the profile that decides what enters the vault. It fetches sources, enriches metadata, extracts PDFs, and proposes draft classifications. The defining trait is **optimistic-by-default**: when in doubt, Librarian includes the candidate and proposes the classification, letting Verifier and the human do the gatekeeping at filing time. This is intentional — the cost of a missing source is invisible (you don't know what you don't have), while the cost of a candidate that gets reviewed and rejected is just one human decision.

## What this profile is not

- **Not a synthesizer.** Librarian curates evidence; Writer composes claims from that evidence. Librarian never writes to `30-synthesis/01-claims/` or `30-synthesis/02-reference/`.
- **Not the gatekeeper.** Verifier is the system's quality bar — Librarian proposes optimistically, Verifier checks conservatively. The asymmetry is the design.
- **Not Mapper.** Same retrieval tooling (`qmd`), opposite direction — Librarian reaches outward to new sources, Mapper inward to the existing corpus (see [Profile boundaries](README.md#profile-boundaries)).
- **Not autonomous about classification.** The `_proposed_classification` block Librarian writes is *proposal*, not fact. It lives in an HTML comment so it's invisible until the human or Verifier promotes it.

## Design decisions

- **Optimistic vs conservative classification.** Librarian errs toward proposing classifications even when uncertain. The HTML-commented `_proposed_classification` block makes proposals cheap to ignore — humans see them only when they choose to review.
- **Mostly-deterministic core with one LLM step.** Citation graph walks (OpenAlex), metadata enrichment (Crossref / Unpaywall / PubMed), PDF extraction (Marker), classification rule dispatch — all deterministic. The only LLM step is composing the candidate-note relevance description when surfacing to the human. Keeps the cost surface small relative to the volume of work Librarian does.
- **Highest external API surface in the system.** Librarian is the only profile that talks to OpenAlex, Semantic Scholar, Crossref, PubMed, and Unpaywall regularly. Its lane-override gates external API calls via `external_api_policy: explicit_only`, requiring each skill to declare its API usage explicitly.
- **Ingest is one card per source, not one card per batch.** Librarian's unit of work is the source. A 30-paper ingest produces 30 cards. This keeps retries scoped (one broken PDF doesn't fail the batch), audit entries clean (one source = one trace), and policy decisions atomic.

## Permissions and commands

Folder permission matrix lives in [profile-matrices.md](../../reference/profile-matrices.md#folder-permission-matrix); the runtime contract (full command list, allowed/disallowed folders, exit conditions) lives in the SOUL.md.

## Related

- Workflows: [ingest](../../how-to/workflows/upstream/ingest.md), [find](../../how-to/workflows/upstream/find.md), [classify](../../how-to/workflows/upstream/classify.md), [zotero-capture](../../how-to/workflows/upstream/zotero-capture.md)
- ADRs: [19 pre-ingest screening](../../project/decisions/19-pre-ingest-screening.md), [17 retriever-scout profile](../../project/decisions/17-retriever-scout-profile.md), [21 shared candidate frontmatter](../../project/decisions/21-shared-candidate-frontmatter.md)
- Method class: [architecture/why-computational-methods.md](../architecture/why-computational-methods.md) — Librarian is on the hybrid side, with deterministic enrichment and an LLM-required classification-proposal step.
