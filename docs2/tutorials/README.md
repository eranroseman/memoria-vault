---
topic: tutorials
---

# Tutorials

Step-by-step learning paths through Memoria. Each tutorial teaches by doing: you follow concrete steps in Obsidian and end with something real in your vault. Work through them in order — each builds on the last.

## Before you start: two directions of work

Memoria organizes everything around two directions of knowledge flow. You'll encounter these terms throughout the tutorials.

**Upstream — bringing knowledge in.**
You capture a thought, read a paper, or hear something worth remembering. The agents prepare that material so it's ready for your thinking: creating notes, enriching metadata, surfacing related ideas. You do the actual thinking — writing claim notes, classifying sources, linking ideas. The agents handle the tedious mechanical work that would otherwise slow you down.

**Downstream — turning knowledge into output.**
When you have enough in your vault on a topic, you start a project. The agents map what you have, propose framings, check your citations. You write the prose and make every judgment call. The agents make sure you're writing from your actual thinking rather than improvising from memory.

The Zettelkasten method lives entirely in these two directions. Memoria automates the retrieval, enrichment, and linking suggestions — it does not change what a Zettelkasten is: a web of atomic notes in your own words, densely connected, that lets you write from synthesis rather than from scratch.

---

## Tutorial sequence

| # | Tutorial | What you'll do | What you end with |
| --- | --- | --- | --- |
| [01](01-set-up-from-zero.md) | Set up from zero | Clone the vault, install plugins, wire up Zotero, run the installer | A working vault with all eight required plugins and all seven profiles installed |
| [02](02-your-first-note.md) | Your first note | Capture a thought, discuss it with Socratic, write a claim note | One permanent claim note in `30-synthesis/01-claims/`, authored in your own words |
| [03](03-bring-in-a-paper.md) | Bring in a paper | Ingest one paper from Zotero, classify it, write one claim note | One classified `paper-note` and one linked `claim-note` |
| [04](04-build-a-reading-batch.md) | Build a reading batch | Ingest 5 papers, classify them, write 3 linked claim notes | Your first connected knowledge cluster |
| [05](05-start-a-writing-project.md) | Start a writing project | Create a project, read the corpus map, commit a framing | A project folder with corpus map and a chosen outline |
| [06](06-verify-and-address-gaps.md) | Verify and address a gap | Write a draft paragraph, run verification, address one failed trace | A verified draft with a complete citation trail |

---

## A note on what Memoria does — and what it doesn't

The agents handle what the Zettelkasten method calls "the tedious parts": fetching metadata, finding related notes, suggesting links, checking citations. They do not:

- Write your permanent notes (claim notes are always authored by you)
- Make classification decisions (they propose; you promote or reject)
- Choose your framing (they generate options; you commit to one)
- Approve their own output (every agent output goes through human review)

The Socratic profile is the clearest example of this design: it has no write access to the vault whatsoever. It exists to sharpen your thinking through conversation, not to produce artifacts.

---

## Implementation status

Tutorials 02–06 exercise the agent pipeline, which requires the v0.2 profile wiring (`config.yaml`, `mcp.json`, `policy_mcp.py`, lane-overrides). See [implementation-status.md](../../docs/project/implementation-status.md) for what's shipped. Tutorial 02 (claim authoring) is mostly human-driven and works today without the full pipeline.
