---
topic: decisions
id: NN
title: <short imperative phrase, e.g. "Shared candidate frontmatter format">
status: proposed
date_proposed: YYYY-MM-DD
date_resolved:
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
> - `accepted` — decided; the codebase follows this rule.
> - `superseded` — replaced by a later ADR (set `superseded_by`).
> - `retired` — withdrawn without replacement (e.g. the problem dissolved).
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
