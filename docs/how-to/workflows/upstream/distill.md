---
topic: workflows
---

# Distill

**Group.** Upstream
**Goal.** Distill discussed literature into durable claims in `30-synthesis/01-claims/`. This workflow covers three pipeline stages: **distill** (initial claim at `maturity: seedling`), **link** (cross-link to budding), **corroborate** (multi-source-supported to evergreen).

## Precondition

The source has been **discussed** ([Discuss](discuss.md)). Distill doesn't fire until the human has thought about the source through Socratic conversation. Before writing a claim from a source that hasn't been discussed yet, run [Discuss](discuss.md) first.

## Steps

1. Open the paper note (which has been discussed).
2. Identify 1–3 durable claims from the discussion.
3. Create or extend claim notes (one claim per note). New claims start at `maturity: seedling`.
4. Link claims to source citekeys and related notes. As cross-links accumulate, `maturity` advances to `budding`, then `evergreen`.
5. Keep each note to a single claim.

## Owners

Human owns authorship and judgment. The Writer can suggest links after the claim is written.

## Why discussion is now a separate workflow

The `socratic-processing` capability used to be documented here as a pattern inside distill (loaded as a skill onto Writer). It's been promoted to its own stage and workflow ([Discuss](discuss.md)) — and the underlying capability is now owned by the dedicated Socratic profile, whose write-denied lane policy makes the protection architectural rather than skill-load-dependent. The queue of "paper notes thought about but not yet written into claims" becomes board-visible. Distill now strictly produces claim notes; discussion strictly produces thinking.

## Card lifecycle

`todo` (claim idea captured after discussion) → `ready` (human decides to write the claim) → `running` (claim note being authored) → `done` (claim note filed at `maturity: seedling`, similarity check passed) → `archived` (card closed; claim note matures independently via cross-links).

## Command

`hermes run draft "..."` (after discussion is done).

## Limit rule

A paper note should generate **at most 2–3 claim notes**. If a single source spawns more, the note is being used as a summary dump rather than distilled into atomic claims. Split the paper note's reading into multiple sessions, or accept that some claims belong to another paper's claim note.

## Title rule

Claim note titles state the **claim**, not the **topic**. `jitai-timing-accuracy-depends-on-context-sensing.md` is a claim note title; `jitai-timing.md` is a topic stub and should not exist as a claim note.

## When to create vs. extend

- New claim that changes how an existing concept is understood → extend the existing claim note.
- New claim with no existing note → create a new claim note.
- Claim that contradicts an existing claim → create a new claim note and type the tension as `relations: { contradicts: [[other-claim]] }` (symmetric, opt-in, human-set) so it surfaces on the [contradictions dashboard](../../../explanation/dashboards/contradictions.md). A claim that *supports* another can likewise carry `relations: { supports: [[other-claim]] }`. See [ADR-9](../../../project/decisions/09-typed-relations-frontmatter.md).
- Claim that *overturns* an existing one (replaces it as the current belief, not merely disagrees) → create the new claim and propose `superseded_by: [[new-claim]]` on the old note for the human to confirm. Supersession is human-set, not agent-written, and is directional replacement over time — distinct from a `contradicts` tension. See [ADR-22](../../../project/decisions/22-claim-supersession.md).

## Pre-filing similarity check

Before a new `claim-note` is filed, `hermes -p memoria-verifier run similarity-check` surfaces the top 3 most-similar existing notes. This is a point-of-action duplicate guard — distinct from the monthly retrospective `find-duplicates` sweep. If similarity exceeds the threshold (~0.8), Verifier flags the card with `near-duplicate-candidate`; the human decides to file, merge, or extend. The check is informational, never blocking — see [profiles/verifier.md](../../../explanation/profiles/verifier.md) for the full protocol.

## Example

Human reads `mamykina2010sense.md` and extracts one durable claim: "JITAI receptivity decreases under high cognitive load." Runs `hermes -p memoria-verifier run similarity-check "receptivity decreases under cognitive load"` → no near-duplicate above 0.8 → creates `30-synthesis/01-claims/receptivity-decreases-under-high-cognitive-load.md` at `maturity: seedling` → cites `[[mamykina2010sense]]` in the body, adds a one-line "Connections" section. Over the next month, two more sources confirm and one contradicts; cross-links accumulate → `maturity` advances to `budding`.

## Related

- **Previous workflow:** [Discuss](discuss.md)
- **Next workflow:** [Promote](promote.md) (when claim reaches `evergreen`)
- **Profile:** [profiles/writer.md](../../../explanation/profiles/writer.md)
- **Linking patterns:** [vault/linking-patterns.md](../../../reference/linking-patterns.md)
