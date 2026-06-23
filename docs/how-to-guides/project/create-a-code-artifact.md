---
title: Create a code artifact
parent: Project
nav_order: 8
---

# Create a code artifact

This guide produces a code artifact: a small note plus its implementation (for example, the script that draws a figure), saved under `projects/<slug>/code/`.

You delegate the work to the **Engineer**, a background worker (a **lane**) that prepares the code task and controls when changes are saved. The Engineer doesn't write the substantive code itself; it sets up a scaffold and hands the actual implementation to an external coding agent. You stay responsible for the *why*: what claim or figure the code serves.

For the reasoning behind this split, see [Why implementation is delegated outward](../../explanation/rationale/why-not-autonomous.md).

## Prerequisites

- A `projects/<slug>/` scratch folder with a `code/` subfolder. The Engineer can only write inside `projects/*/code/`.
- An external coding agent available (Claude Code, Aider, Codex, or similar). Memoria delegates the actual implementation outward by design ([ADR-07](../../adr/07-delegate-coding-to-external-agents.md)).

## Steps

**1. Delegate the code task.**

Open the command palette with `Cmd/Ctrl-P` and run **Memoria: delegate task**, then choose `code`. State the artifact and the claim it serves:

> "Code task: produce the figure-3 receptivity curve for `projects/<slug>/`, from the data behind `[[receptivity-decreases-under-high-cognitive-load]]`."

This creates a **`code`** task for the Engineer. If the purpose or scope still needs discussion, ask instead in the Agent Client pane (the **Co-PI**, your one conversational assistant) to shape the handoff first. Either route ends in the same `code` task (see [Command palette](../../reference/obsidian-command-palette.md)).

**2. Let the Engineer scaffold.**

The Engineer prepares the handoff in `projects/<slug>/code/`, using `system/templates/code-note.md`. The result is a provenance note (purpose, motivating claim, expected outputs) and a working structure for the implementation.

The Engineer has no direct access to your terminal or filesystem. It writes only through Memoria's controlled vault interface, and only inside `projects/*/code/` — the narrowest write scope of any lane.

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

Review it as you would any research output. Run the code and check two things: does it do what the purpose says, and does its output match what the claim asserts?

**6. Record the runbook and commit.**

In the note, fill in the dependencies, the exact command to reproduce the output, and where outputs land. Then commit the note and implementation together in one changeset. This is the per-task commit the Engineer's approval gate expects over `projects/*/code/`:

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
