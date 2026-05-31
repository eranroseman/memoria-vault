---
topic: workflows
---

# Verify

**Group.** Downstream (stage workflow)
**Goal.** Trace every substantive claim in a draft back to a claim note in `30-synthesis/01-claims/`. Flag unsupported claims for the revise loop.

## Pipeline position

Between draft (inside [Write](write.md)) and [Revise](revise.md). Fires automatically on draft commit.

## Steps

1. The human commits to `40-workbench/<project>/04-drafts/<chapter>.md`. A git post-commit hook creates a `verify` card targeting Verifier.
2. Verifier runs `cite-check`: parses the draft into discrete claims (one per sentence containing a `[@citekey]` or a substantive factual assertion), traces each to claim notes via citekey lookup and similarity search, then runs an **entailment check** on each candidate — a *similar* claim note is not necessarily a *supporting* one, so a match counts only if the claim note entails the draft claim. Superseded claim notes (those with `superseded_by`) are excluded as supports.
3. The output lands as a `[!verification]` callout at the top of the draft (see [obsidian-ui/callouts.md](../../../explanation/obsidian-ui/callouts.md)), summarizing total claims / traced / failed. The detailed per-claim report writes to `40-workbench/<project>/05-verification/<chapter>-<date>.md`.
4. For each failed trace, Verifier spawns a `gap:<claim-text>` card in the upstream queue (`10-inbox/03-candidates/` with `type: gap-candidate`). This is the feedback loop that closes downstream back to upstream — see [Find](../upstream/find.md) for what happens to gap cards.
5. The `verify` card completes to `done` carrying one of three `agent_verdict` values (`verify-clean`, `verify-needs-revision`, `verify-needs-attention`) — these are recommendations attached to the card, not card `status` values. The human decides per claim whether the gap is substantive (needs to be filled) or the claim should be softened.
6. Card moves to [Revise](revise.md) if any claim needs human action, or `accepted` if everything traced cleanly.

## Owners

Verifier executes `cite-check`; human decides per claim; gap cards become Librarian's problem ([Find](../upstream/find.md)).

## Card lifecycle

`ready` (git post-commit hook creates the `verify` card targeting Verifier; hook-created cards skip `triage`) → `running` (Verifier claims; Kanban-dispatched within 60s of commit) → completes to `done` with one of three `agent_verdict` values: `verify-clean` (human advances to export), `verify-needs-revision` (advances to [Revise](revise.md)), or `verify-needs-attention` (human-only judgment; retraction or substantive duplicate finding). Each failed claim-trace also creates a child `gap:<claim-text>` card in the upstream Find queue — those are independent cards, not state changes on the parent.

## Command

Auto-fired by git hook; manual trigger in a `memoria-verifier` session (`hermes -p memoria-verifier chat -s cite-check`): `/cite-check --draft <draft-path>`.

## Why verify is a stage instead of part of export

`cite-check` was always in the design, but as part of the export pipeline it ran (or didn't) right at the end — when the human was already committed to shipping. Promoting it to its own stage between draft and export means gap discovery feeds back into upstream weeks before the deliverable matters, not the day before submission.

## Related

- **Profile:** [profiles/verifier.md](../../../explanation/profiles/verifier.md)
- **Hybrid pattern** (deterministic claim extraction + LLM judgment on ambiguous middle band): [architecture/why-computational-methods.md](../../../explanation/architecture/why-computational-methods.md)
- **Entailment over similarity + superseded-claim exclusion:** [roadmap/evaluation.md](../../../project/roadmap/evaluation.md) (Refinement 2) and [ADR-22](../../../project/decisions/22-claim-supersession.md).
- **Previous step:** draft (inside [Write](write.md))
- **Next workflow:** [Revise](revise.md)
