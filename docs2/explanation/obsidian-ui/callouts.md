
# Callouts

Not every agent output belongs on a dashboard. Some context is only useful while looking at a specific note — the comparative read on a paper matters when you open it to read the source, not in a daily roll-up. Dashboards surface *decisions across notes*; callouts surface *context inside one note*.

Memoria uses three callout types, defined via the Callout Manager plugin and rendered consistently across the vault.

## The three callouts and what they represent

**`[!brief]`** appears at the top of every paper-note in `20-sources/01-papers/`. The Mapper produces it when a new source enters the queue, before you've read the paper. It tells you: which of your existing notes this paper overlaps with, where it might contradict what you already know, and what new constructs it introduces. The brief primes your attention so you read actively rather than passively.

**`[!suggestions]`** appears at the bottom of any note the Librarian has run link suggestions against. It contains a bounded set of candidate links — five forward (this note → existing notes) and five backward (existing notes that should point here) — with Approve and Reject affordances. It's collapsed by default to prevent rubber-stamping: if you see a wall of suggestions, you tend to approve all of them without reading. The fleet-health dashboard tracks your accept/reject ratios over time; a sustained acceptance rate above ~90% means you're rubber-stamping, and a rate below ~20% means the candidate scoring needs tuning.

**`[!verification]`** appears at the top of any draft in `40-workbench/*/04-drafts/`. The Verifier produces it automatically when you commit a draft. It shows the result of tracing every substantive claim in the draft back to a claim note in `30-synthesis/01-claims/` — a green check for traced claims, a red flag for untraced ones, and a link to the full per-claim report.

## Why callouts rather than dashboards

A dashboard tells you something about the vault as a whole: what's overdue, what's unlinked, what needs review. A callout tells you something about the note you're currently reading. Separating them means you don't have to context-switch to get note-level context, and the dashboard isn't cluttered with per-note detail.

The design rule: if the information is only useful in the context of a specific note, it's a callout. If it requires seeing across multiple notes, it's a dashboard.

## How callout content is produced

All three callouts follow the same pattern: a deterministic step selects candidates; an LLM composes the prose. This keeps cost bounded, makes the candidate selection auditable, and applies LLM judgment only where open-ended composition is genuinely needed.

For `[!brief]`: the top five most-comparable existing sources are selected by a weighted combination of shared-citation overlap, embedding similarity, and topic-tag intersection. The LLM then composes the comparative narrative — "overlaps with," "may contradict," "new construct" — across those five sources.

For `[!suggestions]`: the top ten link candidates are ranked by embedding similarity (weight 0.4), shared citations (0.3), topic-tag overlap (0.2), and a recency boost (0.1), then capped at five forward and five backward. The LLM optionally adds a one-line explanation per candidate.

For `[!verification]`: citekey resolution and embedding similarity produce a score for each (claim, source) pair. Claims scoring above ~0.75 are auto-clean; below ~0.4 are auto-fail; the LLM judges only the middle band where deterministic signals are equivocal.

The audit trail for each callout is the deterministic step's output — which candidates ranked where, by what score. The LLM's prose is visible but the selection is what dashboards and the fleet-health ratios measure.

## Callout design rules

- **Producer-owned, human-curated.** The agent writes the callout once; you accept, reject, or rewrite. The agent does not overwrite your edits on subsequent runs — it appends a new `(updated YYYY-MM-DD)` callout below.
- **Collapsed by default for suggestions, expanded for briefs and verifications.** Volume-prone callouts start collapsed. One-shot context callouts start open.
- **Callout writes are policy-MCP gated.** When the Mapper attaches a `[!brief]`, that write is logged, hashed, and reversible from the audit log like any other vault write.
