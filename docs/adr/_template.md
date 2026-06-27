---
topic: decisions
id: NN
title: <short imperative phrase, e.g. "Shared candidate frontmatter format">
nav_exclude: true
status: proposed  # proposed | accepted | rejected | superseded
date_proposed: YYYY-MM-DD
date_resolved:
assumes: []        # ADR-NN refs / mechanisms this rests on — so a change that invalidates it is detectable
supersedes: []
superseded_by: []
---

# ADR-NN: \<title>

> **How to use this template.** Copy to `NN-kebab-case-title.md` (replacing `NN`
> with the next available integer). Fill in each section; keep them tight —
> the structure is the discipline, not the length. Leave the leading `_` off
> the filename so the file isn't filtered out by tools that ignore template
> files. Update `status` as the decision moves through its lifecycle.
>
> **Status values:**
>
> - `proposed` — under discussion; no action taken yet.
> - `accepted` — decided; the codebase follows this rule. Implementation can still
>   be unscheduled; readiness and scheduling live on the linked GitHub issue.
> - `superseded` — replaced by a later ADR (set `superseded_by`).
> - `rejected` — decided against; kept with the reasoning so it isn't re-litigated.
>
> **All ADR files** carry `nav_exclude: true` so the public sidebar links to the
> Decision records index instead of listing every decision as a top-level page.
> Proposed ADRs add a *When this matters* section in place of the retired "Adoption
> trigger"/"Guard" — describe the conditions that would raise priority as context
> for the cadence review, never as an automatic gate.
>
> Delete this how-to-use block when copying the template.

## Context

What problem motivates this decision? What constraints, prior choices, or
incidents make it live now rather than later? One paragraph is usually enough;
two if the constraints are non-obvious.

## Decision

What did we decide? State it as a present-tense rule the codebase will follow,
not as an aspiration. Write "Memoria uses X" rather than "Memoria should use
X." One paragraph.

## Consequences

What follows from this — both positive and negative? What new constraints does
it impose on future work? What does it close off? Use a bulleted list if the
consequences split into independent threads.

## When this matters

*(Proposed ADRs only — delete when accepted.)* The conditions under which this
proposal becomes worth deciding — written as context for the per-release cadence
review, not a gate. Pair with `assumes:` so that a change invalidating those
conditions is detectable rather than silently leaving the proposal parked.

## Alternatives considered

What did we reject and why? Each rejected option gets one short paragraph
explaining the trade-off that ruled it out. If the answer is "we didn't
consider alternatives," delete this section — don't fabricate a list.

## Related

Include only the bullets that apply — omit any that would read "none."

- **Workflows affected:** \<specific workflow files, linked>
- **Files affected:** \<list with links>
- **Related decisions / Depends on:** \<ADR-NN refs>
- **Resolves / supersedes:** \<ADR-NN refs>
- **Source discussion:** \<link to issue, conversation, or commit>
