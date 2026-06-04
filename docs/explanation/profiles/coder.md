---
title: The Coder
parent: Profiles
nav_order: 6
---


# The Coder

The Coder is the documentary front for an external coding agent (Aider, Kilocode, Claude Code, Codex). Its responsibilities within Hermes are narrow by design: scaffold a `code-note` handoff, record provenance, run per-task git commits. The substantive coding — generating code, debugging logic, restructuring modules — happens in the external agent. Coder's defining trait is **the two-agent boundary**: Memoria treats the external coding agent as an opaque peer with shared filesystem access, and the human reviews `code-note` updates as the review gate.

---

## Why it's designed this way

**Memoria doesn't compete with coding agents — it connects to them.** There are already capable coding agents. Reimplementing their capabilities inside Memoria would produce a worse copy. Instead, Coder owns the connective tissue between Memoria's audit and review discipline and the external agent's coding capabilities. The vault is the external agent's read-only context; `40-workbench/*/06-code/` is its write zone; the `code-note` is the handoff.

**Per-task commits, not mega-commits.** Coder's commit command creates one logical change per call. This keeps the audit trail granular (one card, one commit, one diff to review) and keeps revert scope small. A single commit spanning many loosely related code changes is the pattern that makes debugging hard.

**Repo-vs-vault routing.** Small scripts that belong to a project live in `40-workbench/*/06-code/` inside the vault. Larger projects earn their own repo and live outside the vault, with a `code-note` in the vault as the provenance index. The threshold is a judgment call, but the pattern is consistent: the vault records *what was built and why*; the external repo holds *the code itself*.

---

## What the Coder is not

**Not the agent that writes code.** Aider, Claude Code, Codex, and Kilocode do that. Coder scaffolds the handoff (the `code-note`), records provenance, and runs git operations. The actual edits land via the external agent's session.

**Not orchestration infrastructure.** Coder does not spawn the external agent as a subprocess, does not parse its output, and does not feed it instructions through a programmatic API. The two agents coordinate through a markdown handoff and a shared filesystem. This is an explicit design choice — not a limitation to be overcome.

**Not Linter.** Linter validates structure (schema, link health, file shape) deterministically. Coder produces code-note artifacts and git commits; its method class is *delegated* — the external agent does the LLM work outside Memoria's runtime.

**Not a synthesizer of project documentation.** Code-notes describe what was built and what research motivated it. They are handoff artifacts. Writing *about* the code, methodology, or results is Writer's domain.

---

## Related

- Why tasks are delegated to specialists: [why specialist profiles](../rationale/why-specialist-profiles.md)
- Structural validator counterpart: [Linter](linter.md)
- The autonomous-loop exception explained: [Why Memoria doesn't pursue full autonomy](../rationale/why-not-autonomous.md)
- The external agent relationship: [create a code artifact](../../how-to-guides/compose/create-a-code-artifact.md)
