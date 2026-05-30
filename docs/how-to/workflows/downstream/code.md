---
topic: workflows
---

# Code

**Group.** Downstream
**Goal.** Treat code as a first-class research output with provenance.

## Steps

1. Human identifies a research code need.
2. The Coder creates or scaffolds a code-note in `40-workbench/<project>/06-code/`.
3. The **external coding agent** (delegated per [ADR-6](../../../project/decisions/06-code-agent-attachment.md)) implements the code; the Coder only scaffolds and links.
4. Output is linked back to the motivating literature.
5. The artifact page records purpose, architecture, and usage.

## Owners

Human owns intent and review. The **Coder** scaffolds the code-note and links provenance; an **external coding agent** (Claude Code, Aider, Codex, Kilocode — [ADR-6](../../../project/decisions/06-code-agent-attachment.md)) writes the implementation. Hermes bookkeeps.

## Example

A chapter needs a reproducible figure → the Coder scaffolds `40-workbench/<project>/06-code/figure-3-receptivity-curve.md` (a `code-note`) linking the motivating claim note → the external coding agent implements the script in the same folder → the human reviews via the standard review gate → the `code-note` records purpose, dependencies, and how to regenerate the figure.

## Related

- **Profile:** [profiles/coder.md](../../../explanation/profiles/coder.md)
- **External coding agent pattern:** [profiles/why-coder-external-agent.md](../../coder/external-agent-workspace.md)
- **Code agent attachment:** [ADR-6 code agent attachment](../../../project/decisions/06-code-agent-attachment.md) — delegate to external agent (Claude Code, Aider, Codex, Kilocode).
- **Autopilot policy:** [ADR-10 code-artifact autopilot](../../../project/decisions/10-code-artifact-autopilot.md) — deferred.
