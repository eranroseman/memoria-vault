---
title: The Librarian
parent: Profiles
---


# The Librarian

The Librarian is Memoria's intake layer — the profile responsible for deciding what enters the vault. It fetches sources, enriches metadata, extracts PDF text, proposes draft classifications, and composes the inline `[!brief]` comparative read on each new paper note. Its defining posture is **optimistic-by-default**: when in doubt, include the candidate and propose a classification, letting Verifier and the human do the gatekeeping at filing time.

This posture is a deliberate design choice, not a shortcut. The cost of a missing source is invisible — you don't know what you don't have. The cost of an over-inclusive candidate that gets reviewed and rejected is just one human decision. Given that asymmetry, optimism is the right policy for an intake profile.

---

## Why it's designed this way

**One card per source, not one card per batch.** Librarian's unit of work is the source, not the batch. A 30-paper import produces 30 cards. This keeps retries scoped (one broken PDF doesn't fail the batch), audit entries clean, and policy decisions atomic. Batching might feel efficient but it hides failures and makes provenance tracing harder.

**Mostly deterministic, two LLM steps at ingest.** Citation graph walks, metadata enrichment, PDF extraction, classification rule dispatch, and the `[!brief]`'s top-5 candidate selection (shared-citation + embedding + topic overlap via `qmd`) — all deterministic. Only two steps are generative: proposing the classification, and composing the `[!brief]` comparative narrative over those 5 candidates. Keeping selection deterministic and prose-only generative keeps costs proportionate to a high-volume profile and most of Librarian's behavior reproducible and auditable.

**Why the Librarian owns the `[!brief]`, not the Mapper.** The comparative read lives at the top of a paper note in `20-sources/01-papers/` — and only the Librarian may write `20-sources/` (the Mapper is read-only across the vault). Since ingest is already a Librarian operation and the Librarian holds `qmd`, composing the brief in the same pass avoids a cross-zone write and a separate hand-off. The Mapper owns *corpus-level* maps (scope, gaps, clusters); the Librarian owns the *per-source* intake read.

**Highest external API surface in the system.** Librarian is the only profile that regularly calls OpenAlex, Semantic Scholar, Crossref, PubMed, and Unpaywall. This concentration is intentional: isolating all external API calls in one profile makes the external surface visible, auditable, and controllable. The lane policy requires each skill to declare its API usage explicitly.

> **Browser fallback (available, not wired in v0.1).** Some discovery targets — publisher landing pages, lab sites, preprint servers, research GitHub repos — expose no structured API the calls above can reach. Hermes's browser capability covers that long tail by rendering the page and extracting elements. If adopted, it is scoped to the discovery (`find`) path only and never to canonical-zone writes — it surfaces candidates, it does not file them.

---

## What the Librarian is not

**Not a synthesizer.** Librarian curates evidence; Writer composes claims from that evidence. Librarian never writes to `30-synthesis/`. The boundary is firm: curation is about fidelity to source material; synthesis is about argument — different cognitive operations that should not be blurred in a single profile.

**Not the gatekeeper.** Verifier is the system's quality bar. Librarian proposes optimistically; Verifier checks conservatively. The asymmetry between them is the design — two profiles with opposing postures produce better outcomes than one profile trying to be both.

**Not Mapper.** Librarian and Mapper share retrieval tooling but face opposite directions: Librarian reaches outward to new sources; Mapper maps what already exists in the corpus. Giving them the same tooling without the same mission keeps the distinction sharp.

**Not autonomous about classification.** The `_proposed_classification` block Librarian writes lives in its own agent-owned frontmatter namespace, never in the main human-owned fields — a proposal the human or Verifier promotes on review. This is not a limitation; it's what makes optimistic proposals safe to ship without human attention on every one.

---

## Related

**Explanation**

- The Librarian's opposing counterpart on posture: [Verifier](verifier.md)
- Directional counterpart on retrieval: [Mapper](mapper.md)
- Why intake is separated from synthesis: [why specialist profiles](../rationale/why-specialist-profiles.md)

**How-to**

- Workflows the Librarian drives: [capture and ingest](../../how-to-guides/sources/capture-and-ingest.md), [find new sources](../../how-to-guides/sources/find-new-sources.md)

**Reference**

- External APIs the Librarian calls: [External integrations](../../reference/integrations.md)
- The ingest routing and enrichment table: [Ingest routing](../../reference/ingest.md)
- The `[!brief]` callout the Librarian composes at ingest: [Obsidian callouts](../../reference/obsidian-callouts.md), [Callouts](../obsidian/callouts.md)
