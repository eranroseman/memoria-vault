---
title: Create a code artifact
parent: Compose
nav_order: 10
---

# Create a code artifact

Delegate analysis or figure code to the **Engineer** — the `code` lane. Code in Memoria is a research output with provenance: the Engineer coordinates (scaffolds the handoff to an external coding agent and owns the commit/revert gate in `projects/*/code/`); the *why* — what claim or figure the code serves — is yours to state.

## Prerequisites

- A `projects/<slug>/` scratch folder with a `code/` subfolder — the Engineer's write scope is `projects/*/code/`
- An external coding agent available (Claude Code, Aider, Codex, or similar) — substantive implementation is delegated outward by design ([ADR-07](../../adr/07-delegate-coding-to-external-agents.md))

## Steps

**1. Delegate the code task.**

In the co-PI pane, state the artifact and the claim it serves:

> "Code task: produce the figure-3 receptivity curve for `projects/<slug>/`, from the data behind `[[receptivity-decreases-under-high-cognitive-load]]`."

The co-PI delegates a **`code`** task to the Engineer. (Palette twin: **Memoria: delegate a task** → `code`.)

**2. Let the Engineer scaffold.**

The Engineer prepares the handoff in `projects/<slug>/code/` — the provenance note (purpose, motivating claim, expected outputs) and the working structure. It is the only lane with `terminal` + `file` capability, and the narrowest write scope to go with it.

**3. State the purpose yourself.**

Open the scaffolded note and write 2–3 sentences: what this code produces, what research question it addresses, which claim it supports. The scaffold records provenance; the purpose is yours.

**4. Hand off to the external coding agent.**

Point your coding tool at the scaffold:

```text
# In Claude Code (or equivalent):
Read projects/<slug>/code/<artifact>.md, then implement the code it
describes. Place the implementation in the same code/ directory.
```

**5. Review the implementation.**

Apply the same gate as any research output: does the code do what the purpose says? Does the output match what the claim asserts? Run it and check.

**6. Record the runbook and commit.**

Fill in dependencies, the exact command to reproduce the output, and where outputs land. Commit the note and implementation together (the Engineer's commit/revert gate covers `projects/*/code/`):

```bash
git add "projects/<slug>/code/"
git commit -m "code: figure-3 receptivity curve — <slug>"
```

## Verify

- The provenance note in `projects/<slug>/code/` names the motivating claim and the reproduction command
- The implementation runs and produces the expected output
- One changeset links note and implementation

## Related

- The lane's design: [The Engineer](../../explanation/profiles/engineer.md)
- Why implementation is delegated outward: [Why Memoria doesn't pursue full autonomy](../../explanation/rationale/why-not-autonomous.md)
- The decision: [ADR-07](../../adr/07-delegate-coding-to-external-agents.md)
