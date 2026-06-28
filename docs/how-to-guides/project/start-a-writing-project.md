---
title: Start a writing project
parent: Project
grand_parent: How-to guides
nav_order: 1
---

# Start a writing project

Stand up the bounded Project space a writing project draws from.

Use this when a cluster has become more than a topic: you have a question, an initial thesis or survey intent, and enough claims/sources that it needs a Project space record instead of loose scratch.

## Steps

**1. Build the synthesis surface.** Distill claims into `notes/claims/` and gather the cluster under a hub in `notes/hubs/` — [Tutorial 04: Draft a section from your claims](../../tutorials/04-draft-a-section-from-your-claims.md) walks the whole arc.

**2. Start the project.** In Obsidian, run `Memoria: start project`. Fill the title and output mode; add scope topics if they are clear now. Thesis mode also asks for the provisional thesis. The command derives the slug, creates blank PICO/FINER scaffolding for shaping, and writes the project and thesis records shown in the Project space, plus the project scratch areas used by code, drafts, and exports.

**3. Check readiness.** Use the page's **Map corpus** button or delegate a `map` task ([Assess your corpus](assess-your-corpus.md)), then relate the resulting claims to the active thesis with `supports` / `contradicts` links. A hub with several mutually linked claims is the tell that a cluster is dense enough to write from.

**4. Refresh the gate.** Open the project from the Project space and run `Memoria: refresh project gate` with the page's **Refresh gate** button or the command palette. The operation updates `project-gate-index.md` with graph maturity, saturation state, open high-impact gaps, and advisory findings; the project page links to it as **Readiness details**.

**5. Sketch and draft.** Lay the argument out spatially ([Use canvas for argument mapping](use-canvas-for-argument-mapping.md)), delegate outline and section work to the Writer's `draft` lane ([Draft with the Writer](draft-with-writer.md)), and keep scratch attached to the project so it stays visible from the Project space.

## Verify

- `projects/<slug>/project.md` and `projects/<slug>/thesis.md` exist
- `project-gate-index.md` exists after refresh
- The Project dashboard shows the project and active thesis
- Any ungrounded drafting claim becomes a gap to resolve before export

## Related

- The synthesis layer a project stands on: [Write a claim note](../knowledge/write-a-claim-note.md) and [Build a hub](../knowledge/build-a-hub.md)
- Readiness check: [Assess your corpus](assess-your-corpus.md)
- Drafting today: [Draft with the Writer](draft-with-writer.md)
