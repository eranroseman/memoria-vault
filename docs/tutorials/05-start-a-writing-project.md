---
title: "Tutorial 05: Start a writing project"
parent: Tutorials
---


# Tutorial 05: Start a writing project

**You will end with:** a project folder at `40-workbench/first-synthesis/`, a corpus map produced by Mapper, and a committed framing — one outline you've chosen as the direction for your first piece of writing.

**Time:** 45–60 minutes.

**You will use:** Obsidian command palette, the board-state dashboard, and your project's workbench folder.

**Prerequisite:** [Tutorial 04](04-build-a-reading-batch.md) complete — at least 5 classified papers and 3 linked claim notes on one topic.

---

## Step 1 — Create the project

Scaffold the project in one step with **Memoria: new project** (`Cmd+P` → type `new project`) — it prompts for the title, research question, and output type, then creates `40-workbench/<slug>/` with its subfolders, the project note (`README.md`), and the Mapper scope card that produces the corpus map in Step 2. Name it `first-synthesis`. *(The narrower **Memoria: write project note** just creates the folder and note without the scope card.)*

**What happens:**

- A project folder is created at `40-workbench/first-synthesis/`
- A `README.md` project-note opens inside it, from the template
- A scope card is created on the Mapper lane queue

---

## Step 2 — Fill in the brief

The `README.md` file is open. Fill in two things:

**What you're trying to write:** One sentence. For example: "A 500-word synthesis of what we know about notification timing and user receptivity."

**For whom:** One sentence. For example: "For my dissertation chapter on adaptive intervention design."

That's enough. Save `README.md`.

---

## Step 3 — Watch Mapper work

Open `00-meta/01-dashboards/board-state.md`.

You'll see a card on the Mapper lane with `status: ready`. Within 60 seconds, it advances to `status: running` as Mapper picks it up.

Mapper is:

- Reading your `README.md`
- Searching the vault for notes relevant to the project's topic
- Counting how many notes exist per sub-topic
- Identifying which adjacent topics have thin coverage
- Writing the corpus map

When the card reaches `status: done`, the corpus map is ready.

---

## Step 4 — Read the corpus map

Open `40-workbench/first-synthesis/01-map/corpus-map.md`.

The map shows you:

- A breakdown of your corpus by sub-topic and how many notes you have on each
- Which sub-topics have good coverage (ready to write from) and which are thin (might need more reading)
- Adjacent topics that appear in your notes but weren't the focus of your reading

Read it carefully. **Make a decision:** Is the corpus ready to write from?

Look for the sub-topic with the most claim notes. If you have at least 3 claim notes on one sub-topic, proceed. If everything is thin, go back to Tutorial 04 and add more papers before continuing.

---

## Step 5 — Request counter-outlines

With `corpus-map.md` open:

Run **Memoria: frame this section** (with a note in the project open) — it creates the Writer card that produces the outlines under `02-framing/`. The terminal is the equivalent fallback:

```bash
hermes -p memoria-writer chat -s counter-outline
# then, in the session:
/counter-outline --project first-synthesis
```

**What happens:** A card goes to the Writer lane with the `counter-outline` skill loaded. Writer reads your brief and corpus map, then generates 2–3 competing outlines — each one organizes the same material in a fundamentally different way.

Wait until the board-state dashboard shows this card reaching `status: done`.

---

## Step 6 — Read the competing outlines

Open `40-workbench/first-synthesis/02-framing/`.

You'll find 2–3 outline documents. Each takes a different approach to structuring your argument. For example:

- **Outline A** might be chronological: how the field's understanding of receptivity evolved
- **Outline B** might be problem-first: start with the design problem, work backward to the evidence
- **Outline C** might be contrast-driven: frame the whole piece as a tension between two camps

Read all three. Notice what each one forces you to emphasize and what it forces you to hide.

---

## Step 7 — Commit to one framing

Choose the outline that best serves your brief.

Create a new file in `40-workbench/first-synthesis/02-framing/` named `CHOSEN.md`. Copy your chosen outline into it.

At the top of `CHOSEN.md`, add one sentence explaining why you chose this framing over the others.

Save `CHOSEN.md`.

---

## What you have

- `40-workbench/first-synthesis/` — your project folder
- `40-workbench/first-synthesis/README.md` — project note (`type: project-note`)
- `40-workbench/first-synthesis/01-map/corpus-map.md` — Mapper's view of your corpus
- `40-workbench/first-synthesis/02-framing/CHOSEN.md` — your committed outline
- Board-state dashboard: scope and framing cards archived as complete

**Your corpus is scoped. Your framing is committed. The next step is prose.**

**See also:** [The Mapper](../explanation/profiles/mapper.md) — how scope-project builds a corpus map and what the clustering and gap signals mean.

---

## What's next

[Tutorial 06 — Verify and address a gap](06-verify-and-address-gaps.md): write one section of prose from your outline, run verification to check your citation trail, and address a gap when verification finds a claim without backing.

---

← [Tutorial 04: Build a reading batch](04-build-a-reading-batch.md) · [Tutorial 06: Verify and address a gap](06-verify-and-address-gaps.md) →
