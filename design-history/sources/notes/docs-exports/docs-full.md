<!-- source: docs/README.md -->

# Memoria

A research operating system for a single researcher (the PI) — a Co-PI you converse with and four background agents that read, enrich, map, verify, and write inside your Obsidian vault, under a human-approval gate that audits every proposed change before it lands.

**[Read about what Memoria is](explanation/overview/what-memoria-is.md)**, what it's not, and why it exists. Everything else builds on this.
If you want a guided first experience, see [Tutorials](tutorials).
If you need to _do_ something, see [how-to guides](how-to-guides).
If you need exact values, field names, or configuration formats, see [Reference](reference).

**v0.1** — installer validated; not yet run end-to-end on a live Hermes. · [GitHub](https://github.com/eranroseman/memoria-vault) · [Install](https://github.com/eranroseman/memoria-vault#install) · [Issues](https://github.com/eranroseman/memoria-vault/issues)

<!-- SCREENSHOT: Replace this comment with ![Memoria vault](assets/screenshot.png) once the system is running. -->

---

## Where do you want to go?

| I want to…                                  | Go here                                                                                           |
| ------------------------------------------- | ------------------------------------------------------------------------------------------------- |
| **Get set up for the first time**           | [Quickstart — set up your vault](how-to-guides/setup/quickstart.md)                                |
| **Do something specific**                   | [How-to guides](how-to-guides/README.md)                                                          |
| **Look up a field, command, or schema**     | [Reference](reference/README.md)                                                                  |
| **Understand why something works this way** | [Explanation](explanation/README.md)                                                              |
| **Fix something broken**                    | [Failure modes](reference/failure-modes.md) · [Troubleshooting](how-to-guides/troubleshooting/README.md) |

---

## New here? Follow the tutorial sequence

Seven tutorials, each building on the last. Start at 01 and follow the sequence — or jump in at whichever step matches where you are. The full sequence, with what you do and end with at each step, is in [Tutorials](tutorials/README.md).

---

## Common tasks

**First session**
[Quickstart](how-to-guides/setup/quickstart.md) · [Set up Hermes](how-to-guides/setup/set-up-hermes.md) · [Vault launch screen](how-to-guides/using-obsidian/use-the-vault-launch-screen.md) · [Use workspaces](how-to-guides/using-obsidian/use-workspaces.md)

**Daily work — sources**
[Find new sources](how-to-guides/library/find-new-sources.md) · [Capture and ingest](how-to-guides/library/capture-and-ingest.md) · [Classify a source](how-to-guides/library/classify-a-source.md) · [Write a claim note](how-to-guides/knowledge/write-a-claim-note.md)

**Daily work — writing**
[Query the vault](how-to-guides/knowledge/query-the-vault.md) · [Assess your corpus](how-to-guides/project/assess-your-corpus.md) · [Draft with Writer](how-to-guides/project/draft-with-writer.md) · [Verify and revise](how-to-guides/project/verify-and-revise.md)

**Weekly**
[Return to work](how-to-guides/inbox/return-to-work.md) · [Weekly review](how-to-guides/inbox/run-the-weekly-review.md) · [Run the Linter](how-to-guides/operate/run-the-linter.md)

**Troubleshooting**
[Safe mode](how-to-guides/troubleshooting/safe-mode.md) · [Failure modes reference](reference/failure-modes.md)

---

## The agents

| Agent             | What it does                                                                  |
| ----------------- | ----------------------------------------------------------------------------- |
| **Co-PI**         | The one agent you converse with — questions, explains, and delegates; read-only |
| **Librarian**     | The four processing lanes (catalog · extract · link · map) — intake to corpus maps |
| **Writer**        | Turns evidence into draft prose — lands in review, never direct to canonical  |
| **Peer-reviewer** | The independent verify gate — traces claims, red-teams arguments; flags, never fixes |
| **Engineer**      | Scaffolds handoffs to external coding agents and owns the commit/revert gate  |

Five deterministic **operations** (ingest · search · clustering · sweeps · Linter) do the mechanical work, behind the policy MCP.

→ [Per-agent design rationale](explanation/profiles/README.md) · [Capability and permission table](reference/profiles.md)

---

## Browse the docs

[**Tutorials**](tutorials/README.md) — Guided first experiences, work through in order.

[**How-to guides**](how-to-guides/README.md) — Task-oriented recipes. Setup · Using Obsidian · Using Hermes Agent · Sources · Writing · Maintenance · Recovery.

[**Explanation**](explanation/README.md) — Why Memoria is built the way it is. Architecture · Knowledge model · Profiles · Workflows · Obsidian surfaces.

[**Reference**](reference/README.md) — Exact values, schemas, commands. Frontmatter · Document types · Profiles · Hermes CLI · Policy MCP · Failure modes · Glossary.

---

<!-- source: tutorials/README.md -->

# Tutorials

These tutorials teach Memoria by building one small thing end to end: a short, well-sourced paragraph you could defend. You work in Obsidian, one concrete step at a time, and finish with real notes in your own vault.

You don't need any prior Memoria experience — each new idea is explained the first time it comes up. Plan for **three short sessions**, about a focused day of work in total.

**Before you start:** these tutorials assume Memoria is installed and the Co-PI is answering. If it isn't, run the [Quickstart](../how-to-guides/setup/quickstart.md) first — installing Memoria is a one-time setup, separate from learning to use it.

Throughout, you talk to **one** assistant: the **Co-PI**, in Obsidian's Agent Client pane. It explains how things work and questions your thinking. The actual work — capturing sources, building claims, drafting, verifying — you start yourself with a command from Obsidian's command palette, and you can always ask the Co-PI to help with any of it.

## Why you start at the end

Memoria earns its keep once you've read enough to write something — and that much reading takes weeks. Waiting that long to see the point is no way to learn. So these tutorials give you a running start: a small **sample vault**, already half-built, on a single topic. You open it, see the finished shape, then build toward it — completing the parts left unfinished and adding one source of your own. By the end you've gone around the full cycle once and are ready to switch to your own work. (For the thinking behind the cycle, see [The knowledge cycle](../explanation/knowledge/knowledge-cycle.md).)

## The path

Seven short tutorials, grouped into three sessions. Do one session, take a break, come back — each ends at a natural stopping point.

### Session 1 — Build a starter corpus *(~1.5–2 hours)*

| # | Tutorial | What you'll do | What you'll have |
| --- | --- | --- | --- |
| 01 | [See what you're building](01-orient.md) | Load the sample, open a project, and read its narrated map — a dense cluster of claims, and the one gap it leaves open. | A project that names your goal, and a clear destination |
| 02 | [Bring in your first source](02-bring-in-your-first-source.md) | Capture a real source of your own, judge the card Memoria raises, and write its source note in your own words. | Your own catalog entity and source note |
| 03 | [Build claims and connect them](03-build-claims-and-connect-them.md) | Study one worked claim, finish the sample's half-built claim and link, then distill claims from your own source and connect them. | A connected cluster of claims, dense enough to write from |

### Session 2 — Produce a cited section *(~1–1.5 hours)*

| # | Tutorial | What you'll do | What you'll have |
| --- | --- | --- | --- |
| 04 | [Draft a section from your claims](04-draft-a-section-from-your-claims.md) | Decide what your section can stand behind, then draft it with every citation tied to a source you hold. | Your goal from 01, written as cited prose |
| 05 | [Verify it holds](05-verify-it-holds.md) | Run a verification pass, read the findings, and fix or keep each one. | A draft you would defend |

### Session 3 — Close the loop and graduate *(~45 minutes)*

| # | Tutorial | What you'll do | What you'll have |
| --- | --- | --- | --- |
| 06 | [Close the loop](06-close-the-loop.md) | Hand the gap your draft exposed back to discovery — one full turn of the cycle. | A cycle you can keep turning |
| 07 | [Make it your own](07-make-it-your-own.md) | Set a weekly-review rhythm, then graduate: archive the sample, import your library, open your real project. | The scaffold gone, your own vault running |

## The sample vault

The sample vault is a small, clearly **labeled** corpus on one neutral topic — whether sticking to a Mediterranean diet protects the heart. It's deliberately **half-built**: some sources are fully worked into claims and links, others are left for you to finish in Tutorial 03. Every note in it traces to a real, citable paper — nothing is invented, because faking a source is the one habit Memoria exists to prevent.

You can remove it when you're done: **Memoria: remove sample vault** archives the labeled notes without breaking any links (Tutorial 07). It isn't something to skip, though — these tutorials are built around it, starting with the map you read in Tutorial 01. If you'd rather work straight from your own material, follow the [how-to guides](../how-to-guides/README.md) instead. For a full inventory, see [the sample vault](../reference/sample-vault.md).

---

## See also

- [What Memoria is](../explanation/overview/what-memoria-is.md) — what the system is, and what it isn't
- [The knowledge cycle](../explanation/knowledge/knowledge-cycle.md) — the cycle these tutorials turn, and the six tasks you can hand off
- [The Co-PI](../explanation/profiles/co-pi.md) — the one assistant you talk to, and why it hands every change to a background helper
- [Your first month](../explanation/knowledge/your-first-month.md) — the real rhythm to settle into once the tutorials are done


---

<!-- source: tutorials/01-orient.md -->

# Tutorial 01: See what you're building

*Session 1 of 3 · Build a starter corpus.*

**You'll finish with:** a project that names your goal, opened over a ready-made sample corpus whose map you've read — a tight cluster of connected claims, and the one gap it leaves open. You'll have seen where you're headed before you start building toward it.

**Time:** 20–30 minutes.

**You'll use:** Obsidian's command palette and the Agent Client pane.

**Before you start:** a working vault with the Co-PI answering. If you don't have one yet, run the [Quickstart](../how-to-guides/setup/quickstart.md) first — installing Memoria is a one-time setup, not part of learning it.

---

Most of Memoria's payoff comes at the end, once you've read enough to write from. Building that much from scratch takes weeks — too long to wait to see what you're aiming at. So this first tutorial starts you at the destination: you open a project over a corpus that is **already built** and read its map, so you know the shape of what you're working toward before you build any of it. (For why the work is shaped this way, see [The knowledge cycle](../explanation/knowledge/knowledge-cycle.md).)

You talk to **one** assistant, the **Co-PI**, in the Agent Client pane (`Cmd/Ctrl-P` → **Agent Client: Open chat view**). It explains how things work and questions your thinking. The real tasks — mapping, capturing, drafting, verifying — each have their **own command** in the palette, and running the command directly is the quickest, most precise way to do them. Start with the command, and turn to the Co-PI when you want help shaping the request or making sense of the result.

## Step 1 — Load the sample vault

Press `Cmd/Ctrl-P` and run **Memoria: load sample vault**. It copies a small, labeled starter corpus on one neutral topic — **whether a Mediterranean diet protects the heart** — into your vault. Every note it adds is tagged `sample: true`, so it stays clearly separate from your own work, and you can remove it with one command when you're done (Tutorial 07).

> One honest note: a cluster this dense is weeks of reading, compressed. It's a teaching scaffold — you'll finish a few of its deliberately-unfinished pieces to learn the moves, then repeat them on your own sources.

---

## Step 2 — Open a project and name your goal

A **project** is where writing happens, and opening one is how you name what you're writing toward. Run `Cmd/Ctrl-P` → **Memoria: start project** and fill in the form: a **title**, the **scope topics** it covers (Mediterranean diet, cardiovascular health), and an **output mode**. Choose **thesis**, and a **provisional thesis** field appears in the form — write it as one sentence, the claim you want to be able to stand behind:

> *A Mediterranean diet reduces major cardiovascular events in high-risk adults.*

Write a claim you could actually defend — not a vague area like "learn about X." By the end of Session 2 you'll have turned it into a verified, cited section.

The command creates the project, which now appears in the **Project space**. Open it there and run **Memoria: refresh project gate** — this checks how ready the corpus is to write from and records the result. (Full procedure: [Start a writing project](../how-to-guides/project/start-a-writing-project.md).) The thesis you just wrote is the line you'll come back to in Tutorial 04, when you draft.

---

## Step 3 — Read the map

Now look at what the corpus can support. Run `Cmd/Ctrl-P` → **Memoria: map corpus**, or ask the Co-PI to map it if you'd like help framing the scope first.

This builds a map of the corpus — how its pieces connect, and where they cluster — and delivers a short read of that map to your **Inbox** (the queue of things waiting on your attention). Open the **Inbox queue** → **Needs me** view and read it with the Co-PI narrating. You don't yet know how each piece was made — that's the next four tutorials — so let it walk you through:

- **Each dot is a claim** — one defensible sentence that traces back to a real paper. Open one (say `meddiet-reduces-major-cv-events`) and you'll see its shape: a single assertion, evidence lines that each cite a paper, and typed links to neighboring claims. That shape is what you'll learn to make.
- **They cluster** — most of these claims pull the same way: a Mediterranean diet lowers cardiovascular events, carried by two randomized trials and supporting cohort evidence. A dense, mutually linked cluster is the sign that you can *write* from it.
- **The cluster holds a tension on purpose** — one claim (`observational-associations-confounded`) cuts against the others, and a hub note marks where the evidence is strong versus only suggestive. Disagreement is information, not a defect.
- **And it has a gap.** The map flags what the corpus does *not* cover:

> "Corpus has no evidence on **primary prevention in low-risk people**, and nothing on whether the benefit **carries beyond Mediterranean populations and diets**."

**Keep that gap in view.** It isn't a flaw — it's the corpus telling you the truth about its own edges, and in Tutorial 06 it becomes the thing that sends you back out to read. Read coverage by its *pattern*, not by counting notes (full procedure: [Assess your corpus](../how-to-guides/project/assess-your-corpus.md)).

---

## What you have

- A project in the Project space, its provisional thesis naming your goal
- A map of a dense, writable corpus — and the **gap** it surfaced, which you'll pick up again in Tutorial 06
- The words you'll build with — *claim, cluster, gap* — met in context on a finished example, before you make your own

You've seen where you're headed. Everything from here builds toward it: you'll bring in a source of your own, distill and connect claims the way the sample shows, draft your section, verify it, and close the loop.

---

## What's next

[Tutorial 02: Bring in your first source](02-bring-in-your-first-source.md) — capture a real source of your own, check the entry Memoria drafts from it, and write its source note in your own words.

---

[Tutorial 02: Bring in your first source](02-bring-in-your-first-source.md) →


---

<!-- source: tutorials/02-bring-in-your-first-source.md -->

# Tutorial 02: Bring in your first source

*Session 1 of 3 · Build a starter corpus.*

**You'll finish with:** one source of your own in the catalog, the card it raises in your Inbox judged, and a source note written in your own words. Your first source brought in start to finish, sitting next to the sample's worked examples.

**Time:** 30–45 minutes (includes reading the paper or its abstract).

**You'll use:** the Obsidian command palette, the Inbox, and the Agent Client pane.

**Prerequisite:** [Tutorial 01: See what you're building](01-orient.md) complete — the sample vault loaded and a project opened over it.

---

Turning what you read into durable, traceable notes is the habit at the center of Memoria, and you learn a habit by doing it. The sample vault gives you finished source notes to study, but the move only sticks once you do it on your own material — so in this tutorial you bring in a source of your own.

The sample came with finished source notes — the PREDIMED note, the Lyon Diet Heart note, and others. Open the **Library** space and you'll see them in the Reading pipeline, already filled in. Keep one open in a split pane as you work: it shows the shape you're aiming for, not text to copy.

## Step 1 — Capture your source

Pick a paper you actually want to read for your own goal, and copy its URL — the publisher page, or any link that resolves to a DOI. In Obsidian, press `Cmd/Ctrl-P` → **Memoria: capture source from URL** and paste it. A URL with a clear DOI comes in right away; a plain URL asks you for the DOI or citekey first. Either way, your request goes to the **Librarian** — the background worker that looks after your catalog.

> **See also:** if you keep a [Zotero](https://www.zotero.org/) library, **Memoria: capture from Zotero selection** brings in the selected item the same way — [Set up Zotero](../how-to-guides/zotero/set-up-zotero.md) is a one-time setup that gives you stable citekeys. Not sure what to capture? Ask the Co-PI to help shape the request, then run the matching command. Both commands feed the same place.

---

## Step 2 — What capturing creates

Within a couple of minutes, the Librarian has finished bringing the paper in. It has:

- Created the **catalog entity** — Memoria's record of the paper itself, at `catalog/papers/<citekey>.md`. It holds `type: paper`, the merged metadata (title, DOI, authors, year, venue — each field tracing back to where it came from: Semantic Scholar, OpenAlex, Crossref, or PubMed/NCBI), and a **`relationships`** block linking the paper to its authors, its venue, and the papers it cites — each of those a record Memoria finds or creates alongside.
- Created a **source note** for it (still just a stub) in `notes/sources/`, so it shows up in your reading queue.

Open the **Library** space, find your new paper in its **Catalog** view (`catalog.base`), and look at the `relationships` block. These links came for free, from the paper's own metadata — the links *you* make come later, on the notes you write. Compare it to one of the sample's papers: same shape, real metadata. Full reference: [Ingest routing](../reference/ingest.md).

---

## Step 3 — Judge the candidate card

Bringing a paper in doesn't happen silently: a **candidate card** lands in your Inbox, with Memoria proposing that you keep this source and asking you to decide. Open the **Inbox queue** → **Needs me** view.

The card makes an argument, not a ruling: a proposed `action`, the case for and against, what tipped the balance, and how certain it is. Read the `argument_against` field first — it's the one that actually tells you something. Then decide, and resolve the card from the palette: `Cmd/Ctrl-P` → **Memoria: resolve inbox card**. For this tutorial, keep the source (`current`). If you skip one instead, its card goes to `archived` and the catalog record stays as a trace. Why a card argues instead of ruling: [The honesty card](../explanation/kanban-board/card-schema.md).

---

## Step 4 — Read it, then write the source note in your own words

Read the paper — or at least its abstract and conclusions — with its catalog entity open in a split pane (from the **Library** space's **Catalog** view) for the metadata and links. Watch for one or two things worth keeping, not a summary of everything.

Then open the source note from the **Library** space's Reading pipeline. This note is *your* reading record — written in your words, never the agent's. Behind the scenes it carries frontmatter like:

```yaml
type: source
lifecycle: proposed
entity: "[[<citekey>]]"
source_type: paper
```

- **`entity`** — a link back to the catalog entity from Step 2. Every source note is *about* exactly one paper.
- **`lifecycle: proposed`** — a source note starts out `proposed` and moves forward as you work it into claims (the full progression: [Frontmatter fields](../reference/frontmatter.md)).

Fill in the three sections the template gives you. This is where the sample notes earn their keep: open the **PREDIMED** source note (`estruch2018-predimed`) beside yours, notice *how* it's written, and write yours the same way about your own paper:

1. **In my words** — what the paper claims, and on what evidence. Write it fresh; don't paste the abstract. (See how the PREDIMED note lays out the trial, its arms, and the result in plain sentences.)
2. **Worth distilling** — one or two claims you might pull out later. Each bullet is a future claim note; use the **Create linked claim** button when a sentence is ready.
3. **Tensions** — where this paper disagrees with anything already in your vault. Does it touch the same cause-versus-confounding tension the sample's cluster holds? Note it.

Save, then set the source note to `lifecycle: provisional` — read and recorded in your words, but not yet turned into claims. Once you distill the claims you need (next tutorial), you'll move it to `current`.

---

## A note on stray thoughts: fleeting notes

Not every thought comes attached to a source. When something occurs to you mid-read with no citation behind it — a hunch, a question, a connection — capture it as a **fleeting note** (`Cmd/Ctrl-P` → **Memoria: capture fleeting**). It's the lightest note there is: one thought, no quality bar. It shows up in the Inbox later, to be turned into a real note or archived. That's all a fleeting note is — a holding pen for un-sourced sparks, not where your knowledge lives. Sourced reading is the backbone; keep your attention there.

---

## What you have

- `catalog/papers/<citekey>.md` — your own paper, with `relationships` links into the catalog
- A candidate card judged — you read an honest argument and decided
- One source note of your own (now `provisional`), written in your words and linked to its paper
- The sample's worked source notes still beside it as models

The paper is now part of your vault; the source note is your own reading of it. You've done this once — the months of real work are just this, repeated.

---

## What's next

[Tutorial 03: Build claims and connect them](03-build-claims-and-connect-them.md) — study a worked claim in the sample, finish its half-built claims and links, then distill a claim from your own source and connect it to the cluster.

---

← [Tutorial 01: See what you're building](01-orient.md) · [Tutorial 03: Build claims and connect them](03-build-claims-and-connect-them.md) →


---

<!-- source: tutorials/03-build-claims-and-connect-them.md -->

# Tutorial 03: Build claims and connect them

*Session 1 of 3 · Build a starter corpus.*

**You'll finish with:** the sample's half-built cluster finished — one stub claim backed by its source, and one missing link made — plus a claim of your own, distilled from your source and connected into the graph. A connected cluster dense enough to write from.

**Time:** 30–45 minutes.

**You'll use:** the Obsidian command palette, the Agent Client pane, and the sample vault's claims.

**Prerequisite:** [Tutorial 02: Bring in your first source](02-bring-in-your-first-source.md) complete.

---

A source note records what you read. A **claim** is a single, durable sentence you can write *from*. Pulling claims out of your reading and linking them is what turns a pile of notes into a structure you can use — and it's the move people get wrong most often, because it's tempting to write a claim that doesn't quite trace back to a source.

So you learn it in three passes, each with less help. First you **study** a finished claim. Then you **finish** the pieces the sample left half-built — easier, because the shape is already there. Only then do you do it **from scratch**, on your own source. By the third pass, the move is yours.

## Step 1 — Study a worked claim

Open the **Knowledge** space and find the sample claim **"A Mediterranean diet reduces major cardiovascular events…"** (`meddiet-reduces-major-cv-events`) in its **Claims by maturity** view (`claims.base`). Read its three sections and notice what makes it a claim, not a summary:

- **Claim** — one sentence. Not a paragraph, not a topic. One assertion you could defend, or be wrong about.
- **Evidence** — every line ends in a citekey (`[estruch2018]`, `[delorgeril1999]`) that also appears in the note's `sources` field. This is the rule that keeps claims honest: an evidence line that traces to no source is the exact failure Memoria exists to prevent. If you can't cite it, it isn't a claim yet — it's a hunch (a fleeting note).
- **Connections** — the prose around its links. Look at the frontmatter `links` block: this claim `contradicts` `observational-associations-confounded`. Your claims are meant to hold disagreement; a tension like this is information, not a bug to fix.

That shape — one sentence, traced evidence, typed links — is what you're about to reproduce twice.

---

## Step 2 — Finish the sample's half-built work

The sample left two things undone on purpose. Finishing them is the middle pass — lower stakes, because the structure is already there.

**2a — Back the stub claim with its source.** Open the claim **"Higher Mediterranean-diet adherence is associated with lower stroke risk"** (`meddiet-and-stroke-risk`). Its `sources` field is empty and its **Evidence** section is just a prompt: the assertion is there, but nothing backs it yet — right now it's a hunch dressed as a claim.

Open the half-built source note **`sofi2010-meta-analysis`** beside it — its **In my words** is also just a prompt, because the paper was captured but never read. Read the abstract, write two or three plain sentences in **In my words**, then go back to the claim and finish it: add `sofi2010` to the claim's `sources`, and write one **Evidence** line that cites it. The moment the citekey and the evidence line match, the claim is real.

**2b — Make the missing link.** Open the claim **"Extra-virgin olive oil and nuts are the components most linked to the benefit"** (`evoo-and-nuts-active-components`). It's written but unconnected — it names a likely *reason* for the headline effect, but nothing in your notes says so yet. With the claim open, run `Cmd/Ctrl-P` → **Memoria: link claim** and propose a `supports` link to `meddiet-reduces-major-cv-events`. The link is only a proposal until you confirm it (the next aside explains why); confirm it now.

---

## Step 3 — Distill a claim from your own source, from scratch

Now the pass that matters. Open your own source note from Tutorial 02 and look at its **Worth distilling** bullets. Pick the one that's closest to a single, defensible sentence.

With the source note open, run `Cmd/Ctrl-P` → **Memoria: create linked claim note**. It creates a claim that already carries your source in `sources`. Fill it in the way the worked claim showed you:

1. **Claim** — one sentence. If it needs an "and," it's probably two claims.
2. **Evidence** — one or two lines, each citing your citekey. If a line won't trace to a source, cut it or capture the source that would back it.
3. **Connections** — run `Cmd/Ctrl-P` → **Memoria: link claim** and propose a link to a nearby claim: one of yours, or one of the sample's if your topic touches it. Use `supports` if it points the same way, `contradicts` if it cuts against — disagreement is welcome.

You've now distilled a claim with no scaffolding under you — the hardest move in the whole habit, done once on your own material.

---

## A note on the link gate

Links are never added silently. `Memoria: link claim` *proposes* a `supports` or `contradicts` connection; it becomes real only when you confirm it — that confirmation step is the **link gate**. The agent can suggest connections all day, but which ones are real is your call — the same split between agent and you that runs through the whole system. Confirming takes one keystroke; the point is that nothing enters your notes behind your back.

---

## What you have

- The sample's stub claim now **backed** by `sofi2010`, its evidence tracing to a citekey
- The missing `supports` link **made** and confirmed — the mechanism claim now sits under the headline claim
- One claim of your own, distilled from scratch and connected into the cluster
- A claim layer dense enough to write from — which is exactly what the next tutorial does

A vault with 50 sources and 5 claims is just a reading list. What makes the difference is the density you just added: connected claims you can navigate, instead of papers you have to re-read.

---

## What's next

[Tutorial 04: Draft a section from your claims](04-draft-a-section-from-your-claims.md) — decide what your section can stand behind, then draft it, with every citation bound to the claims you just built.

---

← [Tutorial 02: Bring in your first source](02-bring-in-your-first-source.md) · [Tutorial 04: Draft a section from your claims](04-draft-a-section-from-your-claims.md) →


---

<!-- source: tutorials/04-draft-a-section-from-your-claims.md -->

# Tutorial 04: Draft a section from your claims

*Session 2 of 3 · Produce a cited section.*

**You'll finish with:** the goal you named in Tutorial 01, turned into a short, cited section — drafted from your own claim and the sample's worked claims, with every citation bound to a source you actually hold.

**Time:** 30–45 minutes.

**You'll use:** Obsidian, the Agent Client pane, the project you opened in Tutorial 01, and the claim cluster you completed in Tutorial 03.

**Prerequisite:** [Tutorial 03: Build claims and connect them](03-build-claims-and-connect-them.md) complete — the sample cluster finished (the `meddiet-and-stroke-risk` stub backed, the missing `supports` link made) and your own source distilled into at least one claim connected to the cluster.

You opened a project and read its map back in [Tutorial 01](01-orient.md), and since then your cluster has grown — your own claim joined it in Tutorial 03. Now you switch from gathering to writing: decide what the section can stand behind, then draft it. Keep the gap from the map in view — a section you can defend is honest about where its evidence runs out.

---

## Step 1 — Decide what the section claims

The map in Tutorial 01 showed you what you can stand behind; now scope the section to it. Open the hub note (`mediterranean-diet-and-cvd`) and your own claim, and decide the backbone of your 200 words:

- The headline finding — `meddiet-reduces-major-cv-events` — carried by two randomized trials (`[@estruch2018]`, `[@delorgeril1999]`).
- Its likely reason — `evoo-and-nuts-active-components`, now sitting under the headline thanks to the `supports` link you made in Tutorial 03.
- The honest qualifier — `observational-associations-confounded`, sharpened by `predimed-randomization-caveat` — so the section doesn't overstate its case.
- The claim you backed — `meddiet-and-stroke-risk`, from `[@sofi2010]` — and your own claim, connected into the cluster.

Build the gap into your scope on purpose: a defensible 200 words says *who* the evidence is about and *where it stops*, instead of pretending to cover everyone. Write this framing down where the draft step can read it — create a short `projects/<slug>/chosen-framing.md` yourself, listing the claims the section stands on plus one line on what it deliberately leaves out. Full procedure: [Frame a project](../how-to-guides/project/frame-a-project.md).

---

## Step 2 — Draft the section

Now hand off the writing. Run `Cmd/Ctrl-P` → **Memoria: draft section**, or ask the Co-PI to help shape the request. Name the section, point to your framing, and list the claims it stands on:

> "Draft a ~200-word section on whether a Mediterranean diet protects the heart, from `projects/<slug>/chosen-framing.md`, using my claims on Mediterranean diet and cardiovascular health. Lead with the trial evidence, name the mechanism, qualify it with the confounding caution and the PREDIMED randomization caveat, and scope it to high-risk adults in Mediterranean populations. Cite citekeys in-text."

This hands a **draft** task to the **Writer** — another background worker you don't chat with directly ([The Writer](../explanation/profiles/writer.md)). Two things make its output trustworthy:

- **It writes only under `projects/`** — your claims, hub, catalog, and Inbox are off-limits to it.
- **It can't reach the internet** — it writes only from what's in your vault, so it *cannot* cite a source you don't already hold. That's what ties the citations down: every `[@citekey]` in the draft traces to a catalog entity behind a claim you wrote.

When it's done, a card appears in your Inbox with the draft's location under `projects/<slug>/`. Keep citations in Pandoc form (`[@estruch2018]`) so the bibliography can be rendered on export later ([Draft with the Writer](../how-to-guides/project/draft-with-writer.md)).

---

## Step 3 — Make the draft yours

The Writer's output is a starting point, never the deliverable. Open the draft and read it as an editor:

- **Every citation should be a citekey you recognize** — one that sits on a claim in your cluster. The draft can't invent a citation, but it can lean on the wrong claim. If a sentence cites `[@estruch2018]` for something PREDIMED didn't show, fix the sentence.
- **Don't let an unsupported sentence stand.** If a line asserts something with no claim behind it, stop: write the claim from a source you hold, or cut the line. Verification in Tutorial 05 will catch it anyway — cheaper to fix now.
- **The gap belongs in the prose, named.** A defensible section says where its evidence stops. One clause does it: *"…in high-risk adults; the trials say nothing about primary prevention in low-risk people or populations outside the Mediterranean."* That sentence is the seed of Tutorial 06.

To revise, send a corrected request rather than nudging the same card; small fixes you just make in the file yourself.

---

## What you have

- Your Tutorial 01 goal realized: a ~200-word section, drafted from your own claim and the sample's worked claims, every citation bound to a source you hold and traceable through its claim to a real paper
- The gap card still in your Inbox, now named in the prose — kept for Tutorial 06

This is the payoff the dense cluster bought you: cited prose, in a single sitting, from a corpus that would normally take weeks of reading to build.

---

## What's next

[Tutorial 05: Verify it holds](05-verify-it-holds.md) — hand the draft to the independent verifier, read the findings it raises, and turn it into a section you'd defend.

---

← [Tutorial 03: Build claims and connect them](03-build-claims-and-connect-them.md) · [Tutorial 05: Verify it holds](05-verify-it-holds.md) →


---

<!-- source: tutorials/05-verify-it-holds.md -->

# Tutorial 05: Verify it holds

*Session 2 of 3 · Produce a cited section.*

**You'll finish with:** an independent verification pass over your draft, the findings it raises read and acted on, and a short section you would defend in front of someone who disagrees with you.

**Time:** 30–45 minutes.

**You'll use:** the Agent Client pane and the Inbox.

**Prerequisite:** [Tutorial 04: Draft a section from your claims](04-draft-a-section-from-your-claims.md) complete — a ~200-word draft under `projects/<slug>/` with in-text citekeys, and the gap card from the map kept in your Inbox.

Drafting got the words down; verifying asks whether they hold up. The point isn't to bless the draft — it's to put a deliberate skeptic between you and publishing, so the weak spots surface here instead of in front of a reviewer.

---

## Step 1 — Ask for a verification pass

Run `Cmd/Ctrl-P` → **Memoria: verify draft** with the draft as the active note, or ask in the Agent Client pane if you want help shaping the scope:

> "Verify `projects/<slug>/<section>.md` — check that every claim it makes is actually supported by its cited sources."

Either way, this hands a **verify** task to the **Peer-reviewer** — the background worker whose whole job is to challenge your draft ([The Peer-reviewer](../explanation/profiles/peer-reviewer.md)). Three things define it:

- **It flags, it doesn't fix.** The only thing it can write is Inbox cards. It never edits your draft — every change stays yours.
- **It's independent by design.** It is deliberately *not* the worker that gathered the evidence or wrote the prose. Whoever proposes and whoever checks are kept separate on purpose.
- **It traces, checks, and attacks.** It follows each claim back to its cited source, checks that the citations resolve, and hunts the argument for gaps and overreach.

For project drafts, saving and committing the draft also queues a verify pass automatically, so verification keeps up with your actual edits ([Verify and revise a draft](../how-to-guides/project/verify-and-revise.md)).

---

## Step 2 — Read the findings

Open the **Inbox queue** → **Needs me** view. Findings arrive as **flag cards**. A flag card leads with the finding itself: the `finding` comes first, the recommendation rides along in a separate `agent_recommendation` field, and the card names its `target`. Why a verification card is built this way: [The honesty card](../explanation/kanban-board/card-schema.md); the exact fields: [Inbox card fields](../reference/inbox-card-fields.md).

A `clean` flag closes nothing on its own, and an `issues-found` flag changes nothing on its own — **you act, the agent only flags.** Read each finding as a question about your draft, not a verdict on it.

---

## Step 3 — This is where the built-in tension shows up

The cluster you finished was never all agreement, and verification is what brings that out. Expect the Peer-reviewer to put its finger on the tension you wrote across:

- **The causal claim leans harder than the evidence.** Your section says a Mediterranean diet *reduces* cardiovascular events. The standing counter-claim — `observational-associations-confounded` — warns that cohort signals may be confounded by an overall healthy lifestyle. A good flag asks: does your prose make clear that the *trials* are what let the causal reading survive that caution, or does it quietly borrow confidence from the cohort data the caution is about?
- **The trial evidence has a catch too.** If the draft treats PREDIMED (`[@estruch2018]`) as clean, a flag may surface `predimed-randomization-caveat`: the 2013 report was retracted over randomization problems, and it's the 2018 re-analysis that left the result standing. A section you'd defend says so, rather than hoping no reviewer knows.
- **A claim resting on thin evidence.** If your `meddiet-and-stroke-risk` claim or your own claim rests on a single source, the flag says so — verification finding the same thin spot the map did.

This is the system working as intended: the tension was planted so verification has something real to catch. A draft that survives it is stronger than one that was never challenged.

---

## Step 4 — Fix or trust

Work each flag and resolve it. Typical actions:

- **A cited source doesn't say what the draft says:** revise the sentence, or soften it and acknowledge the weakness in the text.
- **An unsupported assertion:** add the citation, write the missing claim from a source you hold, or rewrite the line as explicitly your own view.
- **A real open question (the gap):** that's a *limitation, not a failure*. Name it in the draft's own words — "the evidence here is about high-risk Mediterranean populations" — archive the flag, and move on. The honest card exists precisely so you can disagree with the agent.

Resolve each handled flag from the palette: `Cmd/Ctrl-P` → **Memoria: resolve inbox card**. After revising, commit the draft again or send another pass over the same file — verify and fix is a loop, not a one-shot gate. The Inbox settles back to empty.

One check you never have to run yourself: a retraction sweep runs on a schedule in the background and raises an `alert` card if any of your DOIs has been retracted ([Run a retraction sweep](../how-to-guides/operate/run-a-retraction-sweep.md)) — fitting, since the PREDIMED retraction is part of this very corpus.

---

## What you have

- An independent verify pass over your draft, with each flag read and acted on
- A section that names its own seams — the confounding caution, the PREDIMED caveat, and the limit of who the evidence is about — instead of hiding them
- A draft you would defend: not because nothing could be said against it, but because the strongest things that *could* be said are already in the text

> **The gap is still open.** Verification confirmed the section holds for high-risk Mediterranean populations — and, with the map, that it says nothing beyond them. That open edge isn't a loose end; it's the start of the next turn. Keep the gap card.

---

## What's next

[Tutorial 06: Close the loop](06-close-the-loop.md) — let the gap your draft exposed become a discovery that sends you back to read again: one full turn of the loop.

---

← [Tutorial 04: Draft a section from your claims](04-draft-a-section-from-your-claims.md) · [Tutorial 06: Close the loop](06-close-the-loop.md) →


---

<!-- source: tutorials/06-close-the-loop.md -->

# Tutorial 06: Close the loop

*Session 3 of 3 · Close the loop and graduate.*

**You'll finish with:** the gap your draft exposed turned into a discovery task that sends you back to read — one full turn of the loop, the move that makes the vault compound.

**Time:** 15–20 minutes.

**You'll use:** the Inbox and the command palette.

**Prerequisite:** [Tutorial 05: Verify it holds](05-verify-it-holds.md) complete — a defended draft under `projects/<slug>/`, and the gap card from the map still in your Inbox.

You've oriented, captured, distilled, drafted, and verified — one full pass through the work. But this is a loop, not a line: the gap your draft ran into is the reason to go read again. Closing that loop is this short tutorial; making the vault your own is the next.

---

## Step 1 — Find the gap card again

Open the **Inbox queue** → **Needs me** view and find the **gap card** the map surfaced in Tutorial 01 and verification confirmed in Tutorial 05:

> "Corpus has no evidence on **primary prevention in low-risk people**, and nothing on whether the benefit **carries beyond Mediterranean populations and diets**." — `certainty: likely`, with the same honest body as the other cards.

A gap card is a *proposal*, not a verdict — "your corpus is missing X" — carrying the same honest body as the candidate cards you've already judged. You drafted *around* this gap (your section is honest about who its evidence covers), and that honesty is exactly what tells you where to read next. The gap isn't a flaw in the draft; it's the draft pointing at the next source to find.

---

## Step 2 — Hand the gap back to discovery

For a gap you agree with, hand it straight back as a discovery task. Run `Cmd/Ctrl-P` → **Memoria: delegate task** → `catalog`, or ask the Co-PI to route it. Phrase it as a research question, not a list of keywords:

> "My corpus on Mediterranean diet and heart health only covers high-risk adults in Mediterranean populations. Find sources on **primary prevention in low-risk people**, and on whether the benefit **carries to non-Mediterranean populations and diets** — what am I missing?"

The Librarian searches, compares what it finds against your catalog so it doesn't resurface anything you already hold, and drops **candidate cards** into your Inbox — keep-or-skip, exactly as you judged your own source in Tutorial 02. Full mechanics: [Find new sources](../how-to-guides/library/find-new-sources.md).

**Notice what just happened.** Something you wrote (the draft) raised a gap; the gap became something to go read about (discovery); the sources you keep become claims, and the next map or verify pass finds the next gap. That's one full turn of the loop — and it compounds, because each turn leaves the corpus denser than the last ([The knowledge cycle](../explanation/knowledge/knowledge-cycle.md)).

You can re-enter this loop wherever your work actually is — a paper in hand, a deadline, a draft, a thin spot. There's no "first" step, because it's a loop, not a line. The next tutorial steps you off the scaffold to run it on your own material.

---

## What you have

- The gap turned back into a discovery task — your first full, self-sustaining turn of the loop
- The shape of the cycle in view: writing exposes a gap, the gap pulls new reading, new reading feeds the next draft — and the corpus compounds

---

## What's next

[Tutorial 07: Make it your own](07-make-it-your-own.md) — name the rhythm that keeps the loop alive, then leave the scaffold: archive the sample, import your own library, open your real project.

---

← [Tutorial 05: Verify it holds](05-verify-it-holds.md) · [Tutorial 07: Make it your own](07-make-it-your-own.md) →


---

<!-- source: tutorials/07-make-it-your-own.md -->

# Tutorial 07: Make it your own

*Session 3 of 3 · Close the loop and graduate.*

**You'll finish with:** the weekly review named as the rhythm that keeps the loop alive, and the real handoff — the sample archived, your own library imported, and your own project open. The scaffold is gone; you're standing in your own work.

**Time:** 20–30 minutes.

**You'll use:** the command palette, the Inbox, and your reference manager.

**Prerequisite:** [Tutorial 06: Close the loop](06-close-the-loop.md) complete — you have turned the loop once on the sample.

You've run a full turn with training wheels on. This tutorial takes them off: it names the rhythm that keeps the loop alive, then hands you off the scaffold and into your own vault.

---

## Step 1 — Name the rhythm: the weekly review

You don't babysit this loop, but you can't leave it alone either — queues age and gaps go stale. One standing habit keeps it honest: the **weekly review**, a Friday pass through the Inbox, Maintenance, and Knowledge views. Once the vault is established it takes about 20–30 minutes. You update `research-focus.md` so discovery aims at what you mean to read next, clear the Inbox to empty (candidates kept or skipped, gaps turned into discovery tasks, flags acted on — **empty is the goal**), and advance the claims that have genuinely settled. Full ritual: [Run the weekly review](../how-to-guides/inbox/run-the-weekly-review.md). It's what keeps every background worker's output from piling up unread — the difference between a vault that compounds and one that quietly rots.

---

## Step 2 — Leave the scaffold, bring your own work

Now the handoff, in three moves.

**Archive the sample.** It did its job — a dense cluster to learn the moves on, fast. You don't delete it, you **archive** it: run **Memoria: remove sample vault**. Archiving is a change of state, not a deletion — the command finds the live notes labeled `sample: true`, sets them to `lifecycle: archived`, and stamps the date. That label is exactly its reach: the sample pieces you finished while distilling (the stub you backed, the link you made) carry the label too, so they archive with the rest — while the claim you distilled from your *own* source was never labeled, so it stays live. Archived notes drop out of your active views but stay on disk, and **no link breaks** — so the handoff isn't a cliff. Details: [the sample vault](../reference/sample-vault.md).

**Bring in your own library.** In these tutorials you brought sources in one at a time. For real work, point Memoria at your reference manager so reading flows in as fast as you read. Set up Zotero once ([Set up Zotero](../how-to-guides/zotero/set-up-zotero.md)), then capture from a selection or run **Memoria: capture source from URL** with a DOI — or, if you're still deciding what to bring in, talk it through with the Co-PI first. Discovery now runs against *your* catalog, surfacing what *your* corpus is missing.

**Open your own project.** The project from Tutorial 01 was about the sample's topic. Open one for the question you actually care about — `Cmd/Ctrl-P` → **Memoria: start project**, with your own scope and thesis — and run the same loop on it: capture as you read, distill claims, map for coverage, draft, verify, and let the gaps pull your next reading. The moves are the same; only the material is now yours.

---

## Step 3 — The four jobs, in any order

You've now done every recurring job Memoria exists to support. They aren't steps in a line — they're a loop you re-enter from wherever you are:

- **Capture** — turn what you read into a durable, traceable note.
- **Synthesize** — distill claims, connect them, draft from them.
- **Verify** — put the work in front of the adversarial worker before it ships.
- **Discover** — let the gaps pull the next reading.

A paper in hand → capture; a deadline → synthesize and draft; a draft → verify; a thin spot → discover. None is the "first" step, because it's a loop, not a line ([The knowledge cycle](../explanation/knowledge/knowledge-cycle.md)).

The one thing these tutorials *can't* teach by doing is the real-time rhythm — capturing as you read over weeks, distilling once ~10 sources have piled up, mapping and drafting when a deadline appears, letting gaps pull the next batch. That months-long pace is a habit, not a few sessions, and it lives in the **[Your first month](../explanation/knowledge/your-first-month.md)** practice guide. The tutorials taught you the moves; that guide is where you learn the tempo.

---

## What you have

- The weekly review named as the ritual that keeps the loop alive without babysitting
- The sample archived on a clean handoff — your own library wired in, your own project open
- The four recurring jobs — capture, synthesize, verify, discover — as a loop you re-enter in any order, on your own material

You've completed the tutorials. The scaffold is gone, and the vault is yours.

---

## What's next

- [How-to guides](../how-to-guides/README.md) — each recurring task in depth, for when you hit it for real on your own vault.
- [The knowledge cycle](../explanation/knowledge/knowledge-cycle.md) — the loop you just turned, and the delegable jobs that serve it, explained as a system rather than a walkthrough.
- [Your first month](../explanation/knowledge/your-first-month.md) — the real-time rhythm these tutorials compressed: what to do when, over your first weeks of real use.

---

← [Tutorial 06: Close the loop](06-close-the-loop.md)


---

<!-- source: how-to-guides/README.md -->

# How-to guides

Task-oriented recipes for getting specific things done with Memoria. Each guide assumes you already know the system — if you're new, start with the [Tutorials](../tutorials).

For the *why* behind any design choice, see [Explanation](../explanation). For exact field names, schemas, and command flags, see [Reference](../reference).

---

## Two operating modes

Memoria has two distinct modes of use, each with its own tooling:

**Day-to-day use — Obsidian is the UI.**
Reading, classifying, discussing, distilling, drafting, and reviewing all happen inside Obsidian — the command palette, the Agent Client pane, and the Inbox are your primary controls. The guides in the [Inbox](inbox), [Library](library), [Knowledge](knowledge), and [Project](project) spaces are written for this mode.

**Setup and maintenance — terminal (Linux/Ubuntu, WSL2, or PowerShell).**
Installing profiles, configuring environments, rebuilding indexes, and recovering from failures happen in the terminal. The guides in [Setup](setup), [Operate](operate), and [Troubleshooting](troubleshooting) are written for this mode.

---

## Guide map

| Section | Use it for |
| --- | --- |
| [Setup](setup/) | One-time machine, vault, Obsidian, Hermes, optional sample, and second-vault setup |
| [Using Obsidian](using-obsidian/) | Day-to-day Obsidian controls: home, dashboards, workspaces, ACP, and the command palette |
| [Using Hermes Agent](hermes-agent/) | Profile configuration and terminal chat sessions |
| [Inbox](inbox/) | Triage, review queues, weekly review, and returning to work |
| [Library](library/) | Finding, capturing, ingesting, reading, classifying, and archiving sources |
| [Knowledge](knowledge/) | Writing, linking, promoting, refactoring, querying, and pattern-running over knowledge notes |
| [Project](project/) | Scoping, framing, drafting, verifying, exporting, and code-artifact handoff |
| [Operate](operate/) | Terminal-side upkeep: linter, sweeps, migrations, profile redeploy, search, eval, and logs |
| [Troubleshooting](troubleshooting/) | Detect-fix-verify recipes for operational failures |
| [Zotero](zotero/) | Zotero setup and bibliography recovery |

Each section README owns its guide table. This index stays intentionally shallow so guide titles and descriptions have one home.


---

<!-- source: how-to-guides/setup/README.md -->

# Setup

One-time configuration tasks. Start with the quickstart; use the focused guides
only when you need the extra detail.

## Core path

| Guide | What it covers |
| --- | --- |
| [Quickstart](quickstart.md) | Four-step fast path for a new machine |
| [Set up the vault](set-up-the-vault.md) | Clone the repo and run the install script |
| [Set up Obsidian](set-up-obsidian.md) | Open the vault and install required plugins |
| [Set up Hermes](set-up-hermes.md) | Install profiles and fill `.env` secrets |

## Optional setup

| Guide | What it covers |
| --- | --- |
| [Load and remove the sample vault](sample-vault.md) | Add or archive the optional tutorial corpus |
| [Set up Zotero](../zotero/set-up-zotero.md) | Better BibTeX, citekey format, autosync to `.bib` |
| [Configure project hints](configure-project-hints.md) | Optional per-project topic hints for Librarian classification |

## Advanced setup

| Guide | What it covers |
| --- | --- |
| [Add a second vault](add-a-second-vault.md) | Fork the starter for a separate project |


---

<!-- source: how-to-guides/setup/quickstart.md -->

# Quickstart

Four steps from zero to an installed vault. For the full walkthrough with explanations, see [Set up the vault](set-up-the-vault.md) through [Set up Hermes](set-up-hermes.md). Once you're installed, learn Memoria itself with [Tutorial 01: See what you're building](../../tutorials/01-orient.md).

## Prerequisites

- Git on your `PATH`; on **Windows**, PowerShell 5.1+ for the native production installer. Sandbox images must include Git too.
- A `KILOCODE_API_KEY` (the shipped model provider is `kilocode` — kilo.ai) and an `OPENALEX_API_KEY` ([openalex.org/settings/api](https://openalex.org/settings/api) — required since 2026-02)
- The installer provisions Hermes, verifies ACP, and guides the Obsidian install — you don't need them beforehand. Zotero is optional and comes later ([Tutorial 02](../../tutorials/02-bring-in-your-first-source.md)).

## Steps

**1. Install.** One line (inspect the script first if you like — see the raw URL):

```bash
# Linux / WSL2:
curl -fsSL https://raw.githubusercontent.com/eranroseman/memoria-vault/main/scripts/install.sh | bash
```

```powershell
# Windows production (PowerShell): native Hermes + native vault
irm https://raw.githubusercontent.com/eranroseman/memoria-vault/main/scripts/install.ps1 | iex
```

The installer provisions Hermes, scaffolds your runtime vault (default `~/Memoria`), deploys the **five profiles** (`memoria-copi`, `-librarian`, `-writer`, `-peer-reviewer`, `-engineer`), and wires the maintenance crons — full walkthrough in [Set up the vault](set-up-the-vault.md).

**2. Open the vault in Obsidian.** Open the folder the installer reported (default `~/Memoria`) → Open folder as vault. The required plugins ship pre-installed in `.obsidian/plugins/` — turn off **Restricted mode** (Settings → Community plugins) to activate them, then restart Obsidian. You do not browse or install plugins.

**3. Fill the secrets.** Copy the `apiKey` from Settings → Local REST API, then put your keys in the shared Hermes env file (`%LOCALAPPDATA%\hermes\.env` on Windows, `~/.hermes/.env` on Linux/WSL2). At minimum you need `KILOCODE_API_KEY` (model access), the `OBSIDIAN_*` keys (the REST API key, port, and cert path), and `OPENALEX_API_KEY` — the full annotated list is in [Set up Hermes](set-up-hermes.md).

Propagate them into every profile (profile runs read only their own `.env`):

```powershell
.\scripts\install.ps1 -ProfilesOnly -Vault "$env:USERPROFILE\Memoria"
```

```bash
bash scripts/install.sh --profiles-only --vault ~/Memoria
```

**4. Make the vault a git repo.** The installer deliberately doesn't `git init` for you; obsidian-git, rollback/history, the pre-commit schema check, and verify-on-commit need a repo:

```bash
cd ~/Memoria && git init && git add -A && git commit -m "Initial Memoria vault"
```

The remote-and-backup details are in [Set up the vault](set-up-the-vault.md).

On a fresh vault, empty tables are normal. The Inbox, Library, Knowledge, and
Project spaces each show a **First actions** callout above their Bases views; use
those commands as the day-1 path for the space you are in.

## Verify

- `hermes profile list` shows the five `memoria-*` profiles
- `Cmd/Ctrl-P` → `Mem` lists the `Memoria:` commands
- The runtime vault has a `.git/` directory after the initial commit

## Related

- Full install walkthrough: [Set up the vault](set-up-the-vault.md)
- Plugin activation details: [Set up Obsidian](set-up-obsidian.md)
- API keys and profile secrets: [Set up Hermes](set-up-hermes.md)
- First source walkthrough: [Tutorial 02](../../tutorials/02-bring-in-your-first-source.md)
- Optional bibliographic backbone: [Set up Zotero](../zotero/set-up-zotero.md)


---

<!-- source: how-to-guides/setup/set-up-the-vault.md -->

# Set up the vault

Run the bootstrap installer to provision the runtime, lay the vault down, and register the profiles. This is the foundation step — all other setup guides build on it.

## Prerequisites

- Git on your `PATH` (required for the installer and for runtime history; sandbox images must include it too)
- Windows PowerShell 5.1+ for production, or Ubuntu/Debian/WSL for the Linux test path — macOS is not supported
- The installer provisions Hermes and verifies ACP; you don't need it beforehand

## Steps

**1. Run the bootstrap.** The one-liner does everything; inspect the script first if you like.

```bash
# Linux / WSL2:
curl -fsSL https://raw.githubusercontent.com/eranroseman/memoria-vault/main/scripts/install.sh | bash
```

```powershell
# Windows production (PowerShell): native Hermes, native profiles, native vault
irm https://raw.githubusercontent.com/eranroseman/memoria-vault/main/scripts/install.ps1 | iex
```

Prefer to see it first? Clone and run from the **repo root** (the installers live there, not inside `src/`):

```bash
git clone https://github.com/eranroseman/memoria-vault.git
cd memoria-vault
bash scripts/install.sh            # or .\scripts/install.ps1 on Windows
```

**2. What it does.** With your confirmation at each external step, the installer scaffolds and populates your runtime vault from `src/` (default `%USERPROFILE%\Memoria` on Windows, `~/Memoria` on Linux/WSL2; keep it off OneDrive), installs Hermes, verifies ACP, provisions skills, and for each of the five profiles (`memoria-copi`, `-librarian`, `-writer`, `-peer-reviewer`, `-engineer`):

- Stages the profile files from `<vault>/.memoria/profiles/memoria-<name>/`
- Substitutes `{{VAULT_PATH}}` in `config.yaml` with the runtime vault's absolute path
- Calls `hermes profile install` to register the profile
- Copies `.env.EXAMPLE` to `.env` for each profile (only on first install — existing `.env` files are never overwritten)

It is idempotent. To re-deploy only the profiles after editing the vault source, run `bash scripts/install.sh --profiles-only` on Linux/WSL2 (`.\scripts\install.ps1 -ProfilesOnly` on Windows) — what that flag re-deploys is in [Redeploy profiles](../operate/redeploy-profiles.md).

**3. Set up your own git in the vault** (recommended).

The installer copies the vault but does **not** initialize git — the runtime vault is your repo, under your identity. From the runtime folder:

```bash
git init && git add -A && git commit -m "Initial Memoria vault"
git remote add origin git@github.com:<your-handle>/<your-vault-repo>.git   # optional — your own repo
git push -u origin main                                                    # if you added a remote
```

obsidian-git needs a repo to commit into; the remote (your own, not the starter repo) enables backup, multi-machine sync, and the version history the Librarian and Linter depend on. A sandbox without a real `git` binary is an unsupported degraded runtime, because the commit hooks and rollback/history assumptions cannot run.

## Verify

```bash
hermes profile list
```

All five `memoria-*` profiles appear in the output. If a profile is missing, the script reported that its required files weren't present — re-run and read its output.

Check that `{{VAULT_PATH}}` was substituted:

```powershell
Get-Content "$env:LOCALAPPDATA\hermes\profiles\memoria-librarian\config.yaml"
```

The `policy` server path should show an absolute vault path, not the `{{VAULT_PATH}}` placeholder. If the placeholder is still there, re-run `.\scripts\install.ps1 -ProfilesOnly` on Windows or `bash scripts/install.sh --profiles-only` on Linux/WSL2.

## Related

- Next step: [Set up Obsidian](set-up-obsidian.md)
- Profile secrets: [Set up Hermes](set-up-hermes.md)
- Redeploying profile configuration: [Redeploy profiles](../operate/redeploy-profiles.md)


---

<!-- source: how-to-guides/setup/set-up-obsidian.md -->

# Set up Obsidian

Open the vault in Obsidian, activate the bundled plugins, and copy the REST API key.

## Prerequisites

- Obsidian installed ([obsidian.md](https://obsidian.md)) — or let the bootstrap guide you through it
- Memoria installed — the bootstrap (`scripts/install.sh`, or `scripts/install.ps1` on Windows) run ([Set up the vault](set-up-the-vault.md))

## Steps

**1. Open the vault.**

In Obsidian: Open vault → Open folder as vault → navigate to the runtime vault the installer created (default `~/Memoria`, off OneDrive). The vault name shown is whatever that folder is called on disk. On startup the saved **Memoria** shell opens: `home.md` in the main pane, the pinned rail on the left, and the Co-PI pane on the right.

**2. Enable community plugins.**

The vault **ships its plugins pre-installed and configured** in `.obsidian/plugins/` — you do not browse or install them. The only action is to allow Obsidian to load them:

Settings → Community plugins → turn off **Restricted mode**. The bundled plugins activate on the next restart.

The required plugins:

| Plugin | Purpose |
| --- | --- |
| `obsidian-local-rest-api` | Hermes reaches the vault over this plugin's native MCP |
| `agent-client` | The Co-PI chat pane (ACP) inside Obsidian |
| `obsidian-citation-plugin` | Reads `.memoria/memoria.bib`; inserts citations |
| `callout-manager` | Renders `[!brief]`, `[!suggestions]`, `[!verification]` callout types |
| `dataview` | Powers the dashboards and queue views |
| `templater-obsidian` | Provides the template folder integration for manual template insertion |
| `quickadd` | Registers the `Memoria:` command-palette entries |
| `cmdr` | Places frequent `Memoria:` commands in the ribbon and page header |
| `modalforms` | Provides structured capture forms with controlled vocabulary fields |
| `obsidian-git` | Scheduled, version-controlled vault commits |
| `buttons` | Renders command buttons in note templates |
| `portals` | Provides curated shortcuts to the space/Bases surfaces |
| `memoria-inspector` | Shows the read-only Memoria Inspector sidebar |

All settings ship pre-configured except the per-machine ones below (REST API secrets, agent-client command paths). See [Obsidian plugin settings](../../reference/obsidian-plugin-settings.md) for the load-bearing settings of each.

**3. Configure the REST API plugin.**

The REST API plugin stores its config in a gitignored `data.json`. Copy the example file to bootstrap it:

```bash
cp .obsidian/plugins/obsidian-local-rest-api/data.json.example \
   .obsidian/plugins/obsidian-local-rest-api/data.json
```

**4. Restart Obsidian.**

On restart the plugin regenerates a real `apiKey` (64-char hex token) and its TLS material. You should see "Local REST API: started" in the bottom-right status bar.

**5. Copy the API key and HTTPS certificate path.**

Settings → Local REST API → copy the `apiKey` value. It goes into `OBSIDIAN_API_KEY` in the shared Hermes env file (`%LOCALAPPDATA%\hermes\.env` on Windows, `~/.hermes/.env` on Linux/WSL2) in [Set up Hermes](set-up-hermes.md).

Export or copy the plugin's HTTPS certificate/CA bundle as a PEM file and keep
that path for `OBSIDIAN_MCP_SSL_VERIFY`. The path is machine-local; do not commit
the certificate or a real plugin `data.json`.

**6. Confirm plugin settings match the shipped defaults.**

- Local REST API: **HTTPS server ON, port 27124** (loopback-only) — Hermes reaches the vault over the plugin's native MCP at `https://127.0.0.1:27124/mcp` and verifies the plugin cert through `OBSIDIAN_MCP_SSL_VERIFY` ([ADR-31](../../adr/31-native-obsidian-mcp.md)). Keep `OBSIDIAN_MCP_PORT` in the shared Hermes env file equal to this port.
- Obsidian Citation Plugin: bibliography path set to `.memoria/memoria.bib`

**7. Do not install the frontend Obsidian Linter.**

Memoria is **incompatible** with the frontend `obsidian-linter` plugin — do not install it. It is a second frontmatter authority that collides with the agent-owned namespaces and bypasses the policy-MCP audit trail; the full rationale is in [ADR-12](../../adr/12-obsidian-linter-reference-only.md).

Memoria's linting is the Linter **operation** — deterministic Python with a daily cron and a pre-commit hook ([Linter: detectors and auto-fix](../../reference/linter.md)); `markdownlint` covers Markdown hygiene. Neither needs this plugin.

## Verify

- Status bar shows "Local REST API: started"
- Settings → Local REST API shows a 64-char hex `apiKey`
- `Cmd/Ctrl-P` → `Mem` lists the `Memoria:` commands ([Obsidian command palette](../../reference/obsidian-command-palette.md))
- The left ribbon includes Memoria capture, delegate, and resolve buttons
- Modal Forms lists the four Memoria capture/project forms
- Startup restores the **Memoria** shell with `home.md`, the pinned rail, and the Co-PI pane

Once Hermes is set up, the working loop is: use the left-pane rail to open **Library** for the reading pipeline, use `Memoria:` commands for actions, and open the Agent Client pane when you want conversational help.

## Related

- Next step: [Set up Hermes](set-up-hermes.md)
- Plugin inventory: [Obsidian plugins](../../reference/obsidian-plugins.md)
- Load-bearing settings: [Obsidian plugin settings](../../reference/obsidian-plugin-settings.md)
- Callout types: [Obsidian callouts](../../reference/obsidian-callouts.md)
- Workspaces reference: [Obsidian workspaces](../../reference/obsidian-workspaces.md)


---

<!-- source: how-to-guides/setup/set-up-hermes.md -->

# Set up Hermes

Fill the API secrets, propagate them into the five profiles, and verify that Hermes can reach the vault. Without secrets the profiles install but can't call any model or external API.

## Prerequisites

- Hermes installed and on your `PATH` (`hermes --version` returns a version) — the bootstrap does this for you
- Memoria installed — the bootstrap (`scripts/install.sh`, or `scripts/install.ps1` on Windows) run ([Set up the vault](set-up-the-vault.md))
- Obsidian running with the Local REST API plugin active ([Set up Obsidian](set-up-obsidian.md)) — you need the `apiKey` from that step

## Steps

**1. Put the shared keys in the shared Hermes env file.**

Use `%LOCALAPPDATA%\hermes\.env` on Windows and `~/.hermes/.env` on Linux/WSL2.

```env
KILOCODE_API_KEY=...                  # model access — the shipped provider is kilocode (kilo.ai)
OBSIDIAN_API_KEY=<64-char hex apiKey from the Local REST API plugin>
OBSIDIAN_MCP_PORT=27124               # must equal the Local REST API HTTPS port ([Set up Obsidian](set-up-obsidian.md))
OBSIDIAN_MCP_SSL_VERIFY=/absolute/path/to/obsidian-local-rest-api.pem
OPENALEX_API_KEY=...                  # openalex.org/settings/api — required since 2026-02 (sent as ?api_key=)
S2_API_KEY=...                        # Semantic Scholar, optional (the var is S2_API_KEY, not SEMANTIC_SCHOLAR_API_KEY)
NCBI_API_KEY=...                      # PubMed/PMC, optional (the var is NCBI_API_KEY, not PUBMED_API_KEY)
NCBI_EMAIL=you@example.com            # Entrez contact email; also reused as the Crossref mailto / Unpaywall email param
MEMORIA_TELEGRAM_BOT_TOKEN=...        # optional urgent alert/block pushes
MEMORIA_TELEGRAM_CHAT_ID=...          # optional urgent alert/block pushes
# Zotero needs no key — pyzotero reads the local desktop API (http://localhost:23119, read-only)
# ANTHROPIC_API_KEY=sk-ant-...        # only if you switch config.yaml to provider: anthropic
```

For a Linux/WSL disposable test vault that should use a local Ollama model instead of Kilo Code, leave `KILOCODE_API_KEY` alone and run the profile deploy with `MEMORIA_ENV=test`. The installer renders every profile to `http://127.0.0.1:11434/v1`, `qwen2.5:7b`, and a 64K context by default:

```bash
MEMORIA_ENV=test bash scripts/install.sh --profiles-only --vault ~/Memoria-test
```

Override the local endpoint with `MEMORIA_MODEL_BASE_URL`, `MEMORIA_MODEL_NAME`, or `MEMORIA_MODEL_CONTEXT_LENGTH` when your Ollama setup uses a different model.

**2. Propagate the keys into every profile.**

Hermes profile runs read **only the profile's own `.env`** — there is no global fallback, so the keys must be seeded into each profile:

```bash
bash scripts/install.sh --profiles-only --vault <vault>
```

```powershell
.\scripts\install.ps1 -ProfilesOnly -Vault <vault>
```

What `--profiles-only` re-deploys, and how it seeds each profile's `.env` from the shared file without overwriting existing values, is in [Redeploy profiles](../operate/redeploy-profiles.md). Re-run this any time you add or rotate a key in the shared Hermes env file. To check a single profile, open the deployed `memoria-librarian/.env` under the Hermes profiles directory — the Librarian carries the most keys (it does all enrichment and discovery).

**3. Confirm the placeholders were substituted.**

```bash
grep -A2 "policy" ~/.hermes/profiles/memoria-librarian/config.yaml | head
```

The `policy` server's entry should point at the vault venv's Python and an absolute path ending in `.memoria/mcp/policy_mcp.py`. If you see `{{PYTHON}}`, `{{VAULT_PATH}}`, or `{{MODEL_*}}`, re-run `bash scripts/install.sh --profiles-only --vault <vault>` on Linux/WSL2 or `.\scripts\install.ps1 -ProfilesOnly -Vault <vault>` on Windows.

**4. Install the upstream MCP servers (Librarian + Peer-reviewer).**

The research lanes reach external services over MCP, not direct HTTP (their `web` toolset is disabled — see [ADR-32](../../adr/32-external-access-over-mcp.md)). Two of those servers are upstream `pip` installs; the rest ship in the vault. Install them where Hermes can launch them:

```bash
<vault>/.memoria/.venv/bin/python -m pip install paper-search-mcp
python -m pip install --user zotero-mcp
```

```powershell
& "<vault>\.memoria\.venv\Scripts\python.exe" -m pip install paper-search-mcp
py -m pip install --user zotero-mcp
```

`paper_search` runs under the vault venv's Python. `pyzotero` is launched as the
`pyzotero-mcp` executable, so install `zotero-mcp` somewhere on the PATH Hermes
uses.

**5. Seed the retraction dataset.**

The Peer-reviewer's retraction check indexes a local Retraction Watch CSV; a monthly cron wrapper (`retraction-refresh-cron.sh`) keeps it fresh thereafter. Seed it now:

```bash
python3 .memoria/operations/integrity/retraction/retraction.py --refresh
```

Until the CSV is present, retraction checks degrade to the live CrossRef + Open Retractions sources.

**6. Smoke-test the Co-PI.**

```bash
hermes -p memoria-copi chat
```

Ask it "explain how this vault is organized". It should answer from the vault. For the in-Obsidian pane, the same profile runs as an ACP server (`hermes -p memoria-copi acp`) — the bundled `agent-client` config launches it for you; the pane runs one agent, the Co-PI ([Agent Client pane](../using-obsidian/use-the-agent-client-pane.md)).

**7. Test the ingest path end-to-end.**

In Obsidian, `Cmd/Ctrl-P` → **Memoria: capture source from URL** with a DOI-resolvable URL. If you are still shaping the request, use the Co-PI for conversation, then run the matching capture command. Within a couple of minutes the Catalog entity should exist at `catalog/papers/<citekey>.md` and a candidate card should sit in `inbox/`.

## Verify

```bash
hermes profile list
```

Exactly the five `memoria-*` profiles (`copi`, `librarian`, `writer`, `peer-reviewer`, `engineer`) show as registered.

Check the audit log after the first real ingest:

```bash
tail -5 <vault>/system/logs/audit.jsonl
```

Each line should carry a `"decision"` (`allow_with_log` for the Librarian's Catalog writes) and the acting `"profile"`.

## Related

- API key sources: [Set up Zotero § API keys for enrichment](../zotero/set-up-zotero.md#api-keys-for-enrichment-optional-but-recommended)
- Cost tuning: [Configure a profile § Auxiliary models](../hermes-agent/configuration.md#change-auxiliary-models-set-globally-not-per-profile)
- Re-deploying after profile edits: [Redeploy profiles](../operate/redeploy-profiles.md)
- What the installer wires for you: [Installer (bootstrap)](../../reference/installer.md)
- Profile design: [explanation/profiles/](../../explanation/profiles) (the Co-PI and the four lanes)


---

<!-- source: how-to-guides/setup/sample-vault.md -->

# Load and remove the sample vault

Load the sample vault to follow the [tutorials](../../tutorials/README.md), which are built around a small worked corpus instead of an empty vault. It is removable — archive it when you're done (below). To work straight from your own material instead, skip the tutorial arc and use the other how-to guides.

## Prerequisites

- Memoria is installed and open in Obsidian.
- QuickAdd is enabled, so `Memoria:` commands appear in `Cmd/Ctrl-P`.

## Load it

1. Open Obsidian in your Memoria vault.
2. Press `Cmd/Ctrl-P`.
3. Run **Memoria: load sample vault**.
4. Open the Library or Knowledge space.

The command copies the bundled `.memoria/samples/mediterranean-diet/` notes into live `catalog/` and `notes/` folders. It skips existing files, so it will not overwrite your notes.

## Remove it from active views

1. Press `Cmd/Ctrl-P`.
2. Run **Memoria: remove sample vault**.

The command archives live sample notes labeled `sample: true`. They stay on disk so wikilinks keep resolving, but active dashboards stop showing them.

## Related

- Sample vault contents: [The sample vault](../../reference/sample-vault.md)
- Command details: [Obsidian command palette](../../reference/obsidian-command-palette.md)


---

<!-- source: how-to-guides/setup/configure-project-hints.md -->

# Configure project hints

`project-hints.yaml` gives the Librarian a lightweight per-project topic list so it can **propose** which project a newly ingested paper belongs to — you confirm or correct that at triage, exactly like every other proposed field. It is **optional**: with no file, project membership is tagged fully by hand. This guide creates it from the shipped example and tunes it.

A hint is just a topic list — no weights, no expected-method/design fields. Don't turn it into a scoring matrix ([ADR-15](../../adr/15-project-membership-from-topic-hint.md)).

## Prerequisites

- The starter vault (ships `.memoria/project-hints.yaml.example`)
- The auto-proposal takes effect once the Librarian's `classify` step runs; the file is editable any time before that

## Steps

**1. Copy the example into place.**

```bash
cp .memoria/project-hints.yaml.example .memoria/project-hints.yaml
```

Copy-on-first-use. (Memoria-authored examples use lowercase `.example`; Hermes-generated ones like `.env.EXAMPLE` stay uppercase.) An absent `project-hints.yaml` simply means manual project tagging — nothing breaks without it.

**2. Declare one entry per active project.**

```yaml
projects:
  - id: phd-dissertation
    description: HCI + digital health — JITAI, receptivity, health coaching, equity, LLM mHealth.
    primary_topics: [jitai, receptivity-detection, health-coaching, mhealth, sensemaking, health-equity]
  - id: scoping-review
    description: Scoping review of just-in-time adaptive interventions in mHealth.
    primary_topics: [jitai, mhealth]
```

- `id` — a stable slug; this is the value that lands in a note's `projects` field.
- `description` — a one-line scope, free text. For your reference; not scored.
- `primary_topics` — the topic terms papers in this project tend to carry.

**3. Draw `primary_topics` from the topic signals papers actually carry.**

Prefer terms that appear verbatim in the OpenAlex topics your papers resolve to (use `mhealth`, not `just-in-time-adaptive-interventions`) — at classify time hints are matched against those signals by simple overlap, so a term that never shows up in them contributes nothing ([ADR-15](../../adr/15-project-membership-from-topic-hint.md)). Keep to the ~30-term vocabulary discipline ([Wikilink and link conventions](../../reference/linking.md#vocabulary-discipline)).

**4. Keep it a hint, not a matrix.**

Do **not** add `expected_study_designs` or `expected_methods` blocks ([ADR-15](../../adr/15-project-membership-from-topic-hint.md)) — study design and method are proposed independently. There are no weights to tune; overlap is the whole mechanism.

**5. Re-tune when classification mis-routes.**

This is the file to edit when the symptom appears: if the Librarian keeps proposing the wrong project (or none) for papers that clearly belong somewhere, broaden or narrow that project's `primary_topics` so the overlap reflects how you actually tag. It's a hint you edit freely — no migration, no schema bump.

## Verify

- `.memoria/project-hints.yaml` exists (not just the `.example`).
- Each project entry has an `id` and a non-empty `primary_topics` list.
- After the next ingest + classify, the note's `_proposed_classification` proposes a `projects` value you can confirm at triage.

## Related

- Where the proposed project is confirmed: [Classify a source](../library/classify-a-source.md)
- Topic vocabulary discipline: [linking.md — Vocabulary discipline](../../reference/linking.md#vocabulary-discipline)
- The profile that reads it: [The Librarian](../../explanation/profiles/librarian.md)
- The ~30-term topic vocabulary discipline: [Vocabulary discipline](../../explanation/knowledge/vocabulary-discipline.md)
- The decision and its rationale: [ADR-15](../../adr/15-project-membership-from-topic-hint.md)


---

<!-- source: how-to-guides/setup/add-a-second-vault.md -->

# Add a second vault

Fork the starter vault for a separate project or research area, keeping it independent from your primary vault while sharing the same Hermes profiles.

## Prerequisites

- Your primary vault is working ([Quickstart](quickstart.md))
- Hermes is installed and on your `PATH`
- A separate GitHub repo for the second vault (or plan to create one)

## Steps

**1. Choose a folder for the second vault.**

You already have the repo from your primary setup — no need to re-clone. Pick a distinct folder, e.g. `~/my-second-vault`; step 2 lays the vault down there.

**2. Register the second vault's profiles under unique aliases.**

The default aliases (`memoria-librarian`, etc.) belong to your primary vault, and the installer does not yet support an alias prefix. Lay down the second vault (this temporarily re-points the shared `memoria-*` profiles at it), then duplicate the deployed profiles under a `project2-*` alias:

```bash
# from your repo clone — copy the vault out + deploy (memoria-* now point at it):
bash scripts/install.sh --vault ~/my-second-vault

# duplicate each deployed profile under a project2-* alias (its config.yaml already
# has the substituted second-vault path):
for role in copi librarian writer peer-reviewer engineer; do
  hermes profile install ~/.hermes/profiles/memoria-$role --alias project2-$role --force --yes
done

# restore the memoria-* profiles to your primary vault:
bash scripts/install.sh --profiles-only --vault ~/your-primary-vault
```

This leaves `project2-copi`, `project2-librarian`, etc. pointing at the second vault while `memoria-*` keep pointing at your primary.

> **Note.** A built-in `--alias-prefix` flag is a future enhancement; until then this manual duplication is the supported route.

**3. Open the second vault in Obsidian.**

Obsidian supports multiple vaults. File → Open Another Vault → Open folder as vault → select `~/my-second-vault` (the folder the installer copied the vault to).

**4. Install the same set of required plugins** in this vault (same as step 2 of [Set up Obsidian](set-up-obsidian.md)). Each vault has its own `.obsidian/` config.

**5. Give the second vault its own MCP port and copy its key.**

Each vault's Obsidian instance runs its own Local REST API plugin, and two instances can't share the same HTTPS port ([Set up Obsidian](set-up-obsidian.md) covers the port itself). In the second vault's Local REST API settings, set a distinct HTTPS port (for example, `27125`), export that instance's PEM certificate/CA bundle, and restart Obsidian. Then, in each second-vault profile's `.env`:

- `OBSIDIAN_MCP_PORT` = that port (e.g. `27125`), so the native MCP targets the right instance.
- `OBSIDIAN_API_KEY` = the second instance's `apiKey` (Settings → Local REST API).
- `OBSIDIAN_MCP_SSL_VERIFY` = the second instance's exported PEM certificate/CA bundle path.

> **Tip — full isolation.** To keep the two vaults' profiles, skills, and `.env`s completely separate, install the second vault under its own Hermes home: `HERMES_HOME=~/.hermes-project2 bash scripts/install.sh --vault ~/my-second-vault`. Each `HERMES_HOME` then owns an independent set of `memoria-*` profiles, sidestepping the alias dance above.

**6. Set up Zotero for the second vault.**

Add a second auto-export in Better BibTeX pointing at `my-second-vault/.memoria/memoria.bib`. You can share the same Zotero library or create a separate collection.

## Verify

```bash
hermes profile list
```

Both the primary (`memoria-*`) and second vault (`project2-*`) profiles appear.

Test ingest on the second vault:

```bash
hermes -p project2-librarian chat
# in session: ask it to dry-run an ingest of a known citekey
```

The dry-run output should show paths inside `my-second-vault/`, not your primary vault.

## What collides when two vaults run at once

The steps above isolate the three resources two vaults would otherwise contend for — the Obsidian REST API port (step 5), the Hermes profiles (step 2 aliases or a separate `HERMES_HOME`), and the Kanban queue (a separate `HERMES_HOME`). For what each fix protects against and why coexistence works this way, see [Distribution model → Running more than one vault](../../explanation/deployment/distribution-model.md#running-more-than-one-vault).

## Related

- First vault setup: [Set up the vault](set-up-the-vault.md)
- Redeploying after profile edits: [Redeploy profiles](../operate/redeploy-profiles.md)
- Distribution model explanation: [Distribution model](../../explanation/deployment/distribution-model.md)


---

<!-- source: how-to-guides/inbox/README.md -->

# Inbox

Act on what needs you — the queue of agent proposals, integrity flags, and recurring rituals that await a decision. The job of this space is to reach a clear queue. Performed inside Obsidian.

| Guide | What it covers |
| --- | --- |
| [Triage fleeting notes](triage-fleeting-notes.md) | Clear `notes/fleeting/`: promote, attach, or discard |
| [Review link suggestions](review-link-suggestions.md) | Triage the link lane's Inbox proposals — approve or reject |
| [Work the review queue](work-the-review-queue.md) | Sweep the Inbox: proposals, flags, and held gated writes |
| [Run the weekly review](run-the-weekly-review.md) | Friday ritual: classify debt, synthesis agenda, structural health |
| [Return to work](return-to-work.md) | Three pre-session checks after any break — takes under two minutes |


---

<!-- source: how-to-guides/inbox/triage-fleeting-notes.md -->

# Triage fleeting notes

Clear `notes/fleeting/`: promote each note to something durable, attach it to an existing note, or archive it. Fleeting notes are raw captures — they have a short shelf life by design, and the Linter's `stale-fleeting` detector flags anything older than 7 days.

## Prerequisites

- At least one note in `notes/fleeting/`
- Obsidian open (all steps are in the vault UI)

## Steps

**1. Open the fleeting queue.**

Open the Inbox queue (`spaces/inbox.md`) and use the **Fleeting notes** section. It embeds the **To process** view of `system/dashboards/fleeting.base`, which is the single queue for every fleeting note still at `lifecycle: proposed`.

**2. Open each fleeting note and decide its fate.**

**Promote — it's a real idea worth keeping.**

- If it connects cleanly to an existing claim: open the claim note and work the idea into its Evidence or Connections section. Archive the fleeting note.
- If it could stand alone as a claim: use it as the seed for [Write a claim note](../knowledge/write-a-claim-note.md), then archive the fleeting note.
- If it's a paper or source to chase: capture it (`Cmd/Ctrl-P` → **Memoria: capture source from URL**), delegate discovery (**Memoria: delegate task** → `catalog`), or ask the Co-PI to shape the search, then archive the fleeting note.

**Attach — it's context for something else.**

Open the relevant source note or hub, add the content where it belongs, archive the fleeting note.

**Discard — the capture served its purpose.**

Set `lifecycle: archived` (or delete outright — a fleeting note has no provenance value once judged).

**3. Confirm the queue is empty** (or contains only notes from the current session).

## Verify

- `notes/fleeting/` has no `proposed` notes older than 7 days
- The **Fleeting notes** queue in the Inbox is empty

## Notes

**Chat exports are adjacent, not automatic fleeting notes.** Closed pane sessions are auto-exported to `system/exports/` for PI review. They do not enter the fleeting queue automatically; when a transcript contains a durable thought, create the fleeting note yourself and link back to the export if the context matters. See [Agent Client pane](../using-obsidian/use-the-agent-client-pane.md).

The Linter flags stale fleeting notes but never promotes or deletes them — that decision is always yours. A rising fleeting backlog in the Inbox is a signal to run this triage before the next session.

## Related

**How-to**

- Write a claim note: [Write a claim note](../knowledge/write-a-claim-note.md)
- Weekly review rhythm: [Run the weekly review](../inbox/run-the-weekly-review.md)
- Command-palette capture: [Obsidian command palette](../../reference/obsidian-command-palette.md)

**Reference**

- The fleeting type and its lifecycle subset: [Document types](../../reference/document-types.md)

**Explanation**

- The fleeting note's role: [Document types and epistemic roles](../../explanation/knowledge/document-types.md)
- Triage as the first promotion decision: [Why promotion is gated](../../explanation/knowledge/promotion-model.md)


---

<!-- source: how-to-guides/inbox/review-link-suggestions.md -->

# Review link suggestions

**Goal:** decide which of Memoria's proposed links between your claims to accept, and add the accepted ones to the graph yourself.

A **link suggestion** proposes a connection between two claim notes. It is raised by the **Librarian**, a background worker (a **lane**) that scans your claims and proposes links. The Librarian never edits your notes directly. Instead its proposals arrive for you to approve or reject. This is the **link gate**: nothing enters the graph behind your back.

Suggestions reach you in two places. First, as a `[!suggestions]` callout written into a claim note. Second, as cards in the **Inbox**, your review queue. Each card is a **`gap` card** carrying an honest argument for and against the link, not a verdict — you make the call. There are two card kinds: a candidate connection (`link-suggest-claim`) and a surfaced tension (`link-surface-tension`).

This guide is for *triaging Memoria's proposals*. To type a `supports`/`contradicts` link you've already decided on yourself, see [Link related claims](../knowledge/link-related-claims.md) instead.

## Prerequisites

- A claim note with a `[!suggestions]` callout, or Librarian cards in the Inbox. To generate them, run **Memoria: link claim** from a claim note: open the command palette with `Cmd/Ctrl-P` and run it.

## Steps

**1. Open the suggestions in context.**

Run **Memoria: link claim** from the claim note. It writes a collapsed `[!suggestions]` callout listing the top candidate links, then hands off the richer review to the Librarian. Open the callout first, in the note where the link would matter.

If the Librarian also raised cards, open the **Needs me** view of `inbox/inbox.base` on the Inbox queue. Triage the whole batch in one pass. Reviewing them together keeps your judgment sharp ([ADR-54](../../adr/54-two-decision-kinds-batch-worklists.md)).

**2. Read each suggestion before deciding.**

For each callout row or `gap` card, ask: *would I want this link to exist when I come back to either note?* A good link is one a future reading or writing session would actually follow. Read the `argument_against` field first. It carries the most information. Two notes can be very similar and still not be worth linking.

**3. Approve by writing the link yourself.**

To accept a suggestion, *you* open the claim and add the entry to its `links:` map, exactly as you would type one by hand ([Link related claims](../knowledge/link-related-claims.md)). Then resolve the card from `current` to `archived` ([Work the review queue](../inbox/work-the-review-queue.md)). Memoria proposed; your edit to the file is the approval.

**4. Reject the rest. Don't leave them pending.**

Resolve unconvincing cards straight to `archived`. Leaving cards undecided defeats the queue: the Inbox is meant to empty out, and a stale half-reviewed queue is just noise.

**5. Resist approve-all.**

The fleet-health dashboard tracks your accept/reject ratio. A too-high rate means rubber-stamping; a too-low one means the scoring needs tuning. Both are worth acting on ([Dashboards](../../reference/dashboards.md)).

## Verify

- No Librarian card remains at `lifecycle: proposed`
- The latest `[!suggestions]` callout has been read, not mass-approved
- Every approved suggestion exists as a `links:` entry on the claim, written by your hand
- A `contradicts` approval now shows in Knowledge's **Contradictions** view

## Related

**How-to**

- The deliberate, non-proposed path: [Link related claims](../knowledge/link-related-claims.md)
- The callout shape: [Obsidian callouts](../../reference/obsidian-callouts.md)
- Resolving cards from the palette: [Command palette](../using-obsidian/obsidian-command-palette.md)

**Reference**

- The card shapes: [Document types](../../reference/document-types.md)
- The accept-ratio signal: [Dashboards](../../reference/dashboards.md)

**Explanation**

- Why proposals carry arguments, not verdicts: [The honesty card](../../explanation/kanban-board/card-schema.md)


---

<!-- source: how-to-guides/inbox/work-the-review-queue.md -->

# Work the review queue

Clear the decisions waiting on you. The review surface is the **Inbox**: agents finish board cards, and what needs your judgment lands as typed cards (`candidate` / `gap` / `flag` / `alert`) at `lifecycle: proposed`. Anything an agent wanted to write into a **review-gated zone** (`notes/claims/`, `notes/hubs/`) was degraded to `dry_run` by the policy MCP — the proposal reaches you as a card; the write only happens by your hand.

## Prerequisites

- Cards in the Inbox at `lifecycle: proposed` (the **Needs me** view of `inbox/inbox.base` on the Inbox queue)

## Steps

**1. Open the queue and work it as one batch.**

Sit down once and sweep the queue — high-cardinality decisions belong in one worklist worked in one sitting, never N cards trickling at you ([ADR-54](../../adr/54-two-decision-kinds-batch-worklists.md)).

**2. Read each card the right way round.**

- **Proposals** (`candidate`, `gap`) carry the honesty body — read `argument_against` and `certainty` first; the card existing *is* the recommendation, so there is no verdict field.
- **Verification cards** (`flag`, `alert`) lead with the `finding` and carry an `agent_recommendation` — a recommendation, never the decision ([Inbox card fields](../../reference/inbox-card-fields.md)). You can reject a `clean` and accept an `issues-found`.

**3. Act, then resolve.**

Acting on a card is whatever the card proposes — write the link, fix the claim, queue the discovery task, apply the gated write yourself. Then flip the card in place: `Cmd/Ctrl-P` → **Memoria: resolve inbox card** sets your outcome (`current` = accepted, `archived` = rejected / done) and stamps `resolved:`. You don't archive accepted cards by hand: the archival sweep flips resolved `current` cards to `lifecycle: archived` once the stamp is older than `inbox.archive_after_days` (default 30, set in calibration.yaml), so accepted verdicts stay visible while fresh and the Inbox converges to empty; empty is success.

**4. Reject cleanly.**

Rejecting costs one decision and leaves nothing behind — the proposed write never landed. If the *task* behind a card was mis-specified and should be redone, delegate a corrected card via the Co-PI; on the board, rejection spawns a new card (`supersedes:` the original) rather than re-running the old one, so the audit trail can't lie.

**5. Mind the back-pressure.**

The board caps `done` cards awaiting you at 5 — when the queue fills, the dispatcher slows new work on that lane. That's the system protecting your review capacity, not a malfunction. If a lane stalls, clear your queue rather than wishing the cap away.

**6. Watch your own accept rate.**

The fleet-health dashboard tracks accept/reject ratios per proposing lane — very high acceptance reads as rubber-stamping, very low means candidate scoring needs tuning ([Dashboards](../../reference/dashboards.md)). Both are signals to act on.

## Verify

- No card sits at `lifecycle: proposed` longer than your review cadence (the weekly review is the backstop)
- Every accepted proposal resulted in a change made by your hand; rejected cards left nothing behind
- the Inbox's **Needs me** view is empty at the end of the pass

## Related

- Resolving cards from the palette: [Command palette](../using-obsidian/obsidian-command-palette.md)
- The card shapes and their fields: [Document types](../../reference/document-types.md)
- The gate that holds agent writes: [Policy MCP](../../reference/policy-mcp.md)
- Why review is structural, not a convention: [Why a human gate](../../explanation/rationale/why-human-gate.md)


---

<!-- source: how-to-guides/inbox/run-the-weekly-review.md -->

# Run the weekly review

Walk the Friday ritual: refresh your research focus, sweep the Inbox, use Maintenance's weekly sections, and check structural health. Allow up to ~60 minutes; closer to 20–30 once the vault is established and the queues run near-empty — **empty is success**.

## Prerequisites

- Obsidian open with the vault
- `spaces/maintenance.md` open — the Friday collection: loose ends, drift watch, board state, and the week's new catalog entries and notes

## Steps

**Step 1 — Refresh research priorities (2 min).**

Open `research-focus.md`. Confirm or update the active questions and reading focus — the Librarian reads this to aim discovery, and it sets the lens for every decision below.

**Step 2 — Sweep the Inbox (10–15 min).**

Open the Inbox queue's **Needs me** view of `inbox/inbox.base` (every card at `lifecycle: proposed`) and work it as one batch: candidates kept or skipped, gaps turned into discovery tasks or archived, flags and alerts acted on and resolved ([Work the review queue](../inbox/work-the-review-queue.md)). The weekly review is the backstop that keeps the queue from aging past a week.

**Step 3 — Notice-level findings (5 min).**

Maintenance's **Loose ends** view lists cards at `loudness: notice` — things that didn't demand attention mid-week. Resolve each or consciously defer.

**Step 4 — Review the week's movement (5–10 min).**

The **New this week** sections list catalog entries and notes created in the last 7 days. Scan for anything that landed and stalled: a kept paper with no source note, a source stuck at `proposed`, or a claim with no connections (cross-check Knowledge's **Open questions** view).

**Step 5 — Clear the fleeting backlog (10–15 min).**

Return to the Inbox queue's fleeting **To process** view. Promote, attach, or archive each note ([Triage fleeting notes](../inbox/triage-fleeting-notes.md)). Target: zero notes older than a week.

**Step 6 — Advance settled claims (5 min).**

Scan the Knowledge space's Claims view for long-stable `budding` claims with several inlinks; advance the genuinely settled ones to `evergreen` and slot them into hubs ([Advance a claim to evergreen](../knowledge/promote-a-claim.md)). Don't advance to clear a queue.

**Step 7 — Check structural health (5 min).**

Use Maintenance's **Drift watch** and **Loose ends** views — the Linter operation's daily 06:00 cron feeds them. Address HIGH findings this session; MEDIUM can wait for a maintenance pass; LOW is aggregated noise until it isn't. To re-check after fixes, run the detectors directly ([Run the Linter](../operate/run-the-linter.md)).

**Step 8 — Glance at fleet health (1 min).**

Use the fleet-health dashboard from the rail health band — per-lane trust scores, refreshed by the Monday metrics cron. Anything under 90 is worth a minute's curiosity; under 70 is a real signal.

## Verify

- The Inbox shows nothing at `lifecycle: proposed`
- The fleeting queue is empty in the Inbox
- No HIGH or CRITICAL finding is outstanding in Maintenance's Drift watch
- `research-focus.md` reflects what you actually intend to read next week

## Related

- The Inbox discipline: [Work the review queue](../inbox/work-the-review-queue.md)
- Fleeting triage in depth: [Triage fleeting notes](../inbox/triage-fleeting-notes.md)
- The detectors behind Maintenance drift watch: [Run the Linter](../operate/run-the-linter.md)
- The dashboard inventory: [Dashboards](../../reference/dashboards.md)


---

<!-- source: how-to-guides/inbox/return-to-work.md -->

# Return to work

Three checks before starting any research session after being away — a day, a week, or longer. Takes under two minutes. Catches the most common resumption failures before they cost time mid-session.

## Steps

**1. Confirm Hermes and the profiles are healthy.**

```bash
hermes --version
hermes profile list
```

`hermes profile list` shows the five `memoria-*` profiles (`copi`, `librarian`, `writer`, `peer-reviewer`, `engineer`). If any is missing, re-deploy with the `--profiles-only` redeploy from the repo clone ([Set up Hermes](../setup/set-up-hermes.md)).

**2. Confirm the secrets are in place.**

```bash
grep -c '=' ~/.hermes/.env
cat ~/.hermes/profiles/memoria-librarian/.env | grep -E 'KILOCODE|OPENALEX|OBSIDIAN' | sed 's/=.*/=set/'
```

```powershell
(Get-Content "$env:LOCALAPPDATA\hermes\.env" | Where-Object { $_ -match '=' }).Count
Get-Content "$env:LOCALAPPDATA\hermes\profiles\memoria-librarian\.env" |
  Where-Object { $_ -match '^(KILOCODE|OPENALEX|OBSIDIAN)' } |
  ForEach-Object { $_ -replace '=.*', '=set' }
```

The five keys checked here should all show as set — see [Set up Hermes](../setup/set-up-hermes.md) for what each one is and where it comes from. A blank key or placeholder certificate path fails mid-task. If you rotated keys in the shared Hermes env file, propagate them with the `--profiles-only` redeploy above.

**3. Confirm the vault is synced.**

```bash
cd <vault-path>
git pull --ff-only
git status
```

Expected: "Already up to date" or a clean fast-forward. A diverged branch means another machine pushed while this one was offline — resolve before starting work.

Then open the Inbox queue for **Needs me**. If the rail health band is non-zero, open Maintenance for **Drift watch**, **Loose ends**, and **Board** (the crons kept running — sweeps every 15 minutes, lint daily).

## What's fragile

**Agent Client pane not responding** — the Co-PI also runs in a terminal: `hermes -p memoria-copi acp` to test the server, and every delegation has a CLI equivalent (`hermes kanban create`). The pane is a convenience layer; see [Safe mode](../troubleshooting/safe-mode.md).

**qmd search index stale** — if notes changed outside a session, vault search may lag. Rebuild: [Rebuild the search index](../operate/rebuild-the-search-index.md).

**Sync (Syncthing/multi-device) incomplete** — notes created on another device won't be queryable until sync completes; check before blaming retrieval.

## If something is broken

See [Safe mode](../troubleshooting/safe-mode.md) — the minimal working paths when optional tooling is down.

## Related

- Safe mode (when tools are broken): [Safe mode](../troubleshooting/safe-mode.md)
- Rebuild search index: [Rebuild the search index](../operate/rebuild-the-search-index.md)
- Fix a stale .bib: [Fix a stale .bib](../zotero/fix-stale-bib.md)
- Reinstall missing profiles: [Set up Hermes](../setup/set-up-hermes.md)
- The comprehensive failure catalog: [Failure modes](../../reference/failure-modes.md)


---

<!-- source: how-to-guides/library/README.md -->

# Library

Work sources in — find, capture, read, and classify the literature the vault is built from. Performed inside Obsidian via the Library space, Inbox, and `Memoria:` commands; the Agent Client pane helps with read-only discussion and unclear handoffs.

| Guide | What it covers |
| --- | --- |
| [Find new sources](find-new-sources.md) | Forward/backward citation search, concept queries, candidate cards |
| [Capture and ingest a source](capture-and-ingest.md) | Palette/Zotero capture → Catalog entity + candidate card: the complete intake path |
| [Use structured capture forms](use-structured-capture-forms.md) | Stage a hand-entered source (report, web page, dataset) via the Modal Forms form |
| [Classify a source](classify-a-source.md) | Handle classify flags, review what the automation applied, promote proposals |
| [Discuss a paper](discuss-a-paper.md) | A questioning pass with the Co-PI in the Agent Client pane |
| [Read a paper through a lens](read-through-a-lens.md) | Question a paper through a named theoretical frame |
| [Run a systematic review](run-a-systematic-review.md) | PRISMA-compliant protocol → screening → ingest for defensible literature searches |
| [Archive a source](archive-a-source.md) | Retire a source with `lifecycle: archived` — a state, not a folder |


---

<!-- source: how-to-guides/library/find-new-sources.md -->

# Find new sources

Run a discovery pass — papers that build on what you hold, papers you're missing, or papers matching a research question — and judge the resulting candidate cards in the Inbox. Discovery is a delegated task: use the palette directly or ask the Co-PI to route it; either way, the Librarian searches and candidates come back as honest arguments.

## Prerequisites

- At least a few Catalog entries and source notes, so discovery has something to compare against
- `research-focus.md` reasonably current — the Librarian reads it to aim discovery

## Steps

**1. Delegate discovery.**

Use the direct command when you know this is a catalog/discovery job: `Cmd/Ctrl-P` → **Memoria: delegate task** → `catalog`. Or open the Agent Client pane and name the need as a research question, not keywords:

> "Find sources on just-in-time interventions for physical activity — what am I missing?"

Seed it however helps: "papers that build on `<citekey>`" (forward citations), "the foundational papers `<citekey>` builds on" (backward), "recent work that disagrees with my receptivity claims."

Both routes create a **`catalog`** task for the Librarian. The Co-PI route uses `delegate_route_task`; the palette route is the direct action path and should be the default when the lane is already clear.

**2. Let the Librarian search.**

It searches over the `paper_search` MCP (20+ scholarly databases) and compares hits against your Catalog so papers you already hold aren't resurfaced. Its posture is faithful and generous — include liberally, represent accurately, let your review gate filter — with a diversity reserve so the corpus doesn't become an echo chamber ([The Librarian](../../explanation/profiles/librarian.md)).

**3. Judge the candidates as one batch.**

**`candidate` cards** land in the Inbox (the **Needs me** view of `inbox/inbox.base`, shown on the Inbox queue), one per proposed source, each carrying the honesty body and never a verdict ([Frontmatter fields](../../reference/frontmatter.md)). Judge each one the same way as any captured candidate — read `argument_against` first, then keep (`current`) or skip (`archived`) ([Capture and ingest a source](capture-and-ingest.md)). Work them in one sitting:

- **Keep:** the paper enters the Tutorial 04 flow (Catalog entity, reading queue, proposed source note).
- **Skip:** skipping generously offered candidates is the system working, not failing.

Resolving a card flips it in place ([Work the review queue](../inbox/work-the-review-queue.md)). Don't leave candidates undecided — a drip-feed of stale cards trains you to wave things through ([ADR-54](../../adr/54-two-decision-kinds-batch-worklists.md)).

**4. Feed it from gaps.**

Every `gap` card you agree with — from a `map` or `verify` pass — is a pre-written discovery prompt: use **Memoria: delegate task** → `catalog` with the gap as context, or ask the Co-PI ("that gap is real — find sources to fill it") if you want help shaping the request. This is the compounding loop: mapping finds holes, discovery fills them, verification keeps the filling honest.

## Verify

- Candidate cards from the run are all resolved — none left at `lifecycle: proposed`
- Kept papers have Catalog entities in `catalog/papers/` and appear in the reading queue (`system/dashboards/sources.base`) through their proposed source-note stubs

## Related

- After keeping a candidate: [Capture and ingest a source](capture-and-ingest.md)
- The full guided loop: [Tutorial 06: Close the loop](../../tutorials/06-close-the-loop.md)
- The profile behind the search: [The Librarian](../../explanation/profiles/librarian.md)
- A defensible, protocol-driven search instead: [Run a systematic review](run-a-systematic-review.md)


---

<!-- source: how-to-guides/library/capture-and-ingest.md -->

# Capture and ingest a source

Goal: bring a paper into the vault. You capture it once; Memoria then builds the records and proposes that you keep it.

This is the full intake path. You capture the paper from the command palette (or from Zotero). After that, a background worker called the **Librarian** does the setup. The Librarian is the lane (a background worker) that owns the **catalog** — Memoria's set of records about papers.

By the end you have three things: a **catalog entity** (Memoria's record of the paper, at `catalog/papers/<citekey>.md`), a draft **source note** (your reading record, in `notes/sources/`), and a **candidate card** in your Inbox proposing that you keep the paper.

## Prerequisites

- The vault installed with the five profiles, and the Hermes gateway running ([Set up Hermes](../setup/set-up-hermes.md))
- Optional but recommended: Zotero with Better BibTeX, auto-exporting to `.memoria/memoria.bib` ([Set up Zotero](../zotero/set-up-zotero.md))

## Steps

**1. Capture the source.** Pick one of three routes. Each hands the same capture card to the Librarian.

- **From Zotero:** Add the source to Zotero. Better BibTeX pins the citekey for you. Select the item. Then, in Obsidian, press `Cmd/Ctrl-P` and run **Memoria: capture from Zotero selection**.
- **From a URL:** Press `Cmd/Ctrl-P` and run **Memoria: capture source from URL**, then paste the paper's URL. A URL with a resolvable DOI ingests on its own. A bare or proxied URL prompts you for the DOI or citekey.
- **With Co-PI help:** The Co-PI is the one agent you talk to, in the Agent Client pane. If you are unsure how to frame the capture, open that pane and ask. Once the request is clear, use the matching palette route, or let the Co-PI hand off the same card for you.

**2. Clean the metadata in Zotero (Zotero route only).**

Check the title, authors, and year in Zotero's item panel before you capture. Memoria seeds its first record from these values, so fix any OCR or auto-import errors here, at the source.

**3. Let the ingest run — nothing to invoke.**

The Librarian claims the card and runs the ingest for you ([Ingest routing](../../reference/ingest.md)). Within a couple of minutes it produces the following.

- **The catalog entity**, at `catalog/papers/<citekey>.md`. This is Memoria's record of the paper. The Librarian fills it by merging metadata from four sources: Semantic Scholar, OpenAlex, Crossref, and PubMed/NCBI. Each field notes which source it came from (its provenance). If full text is available, the Librarian also extracts from it, and that shows up in the entity's metadata.
- **Links to related entities.** The catalog entity gets a `relationships` block — the edges to other records. Three kinds: `authored_by`, `published_in`, and `cites`. These point to person, venue, and paper entities, which the Librarian finds or creates alongside this one.
- **A classification, when it's clear.** The Librarian sets `research_area` (and `methodology` where it can tell). When the call is genuinely ambiguous, it leaves these unset and raises one `flag` in your Inbox instead.
- **A `candidate` card** in your Inbox. This proposes that you keep the paper. Its body is an honest argument for and against, not a verdict — you decide. The card also carries the Librarian's `_proposed_classification`.
- **A draft source note**, at `notes/sources/<citekey>.md`. This is the start of your reading record.

**4. Judge the candidate card.**

Your Inbox is a queue. Open its **Needs me** view, in `inbox.base`. Read `argument_against` first — it carries the most information ([Frontmatter fields](../../reference/frontmatter.md)).

Then decide. To keep the paper, resolve the card to `current`, act on it, then mark it `archived`. To skip it, resolve straight to `archived`; the catalog entity stays as a record either way. Resolving a card is one palette command ([Work the review queue](../inbox/work-the-review-queue.md)).

**5. Write your source note.**

For a kept paper, open the draft reading record from the Library space's source views. Its `entity:` field wikilinks back to the catalog entity. Its `lifecycle` is `proposed` until you read the paper. Fill the note in your own words.

The note's `lifecycle` then advances as you work. It moves to `provisional` once you've read the paper but not yet distilled it (the discuss queue picks it up at that point). It moves to `current` once you've distilled its claims. The full chain is defined in [Frontmatter fields](../../reference/frontmatter.md). For the end-to-end walkthrough, see [Tutorial 02: Bring in your first source](../../tutorials/02-bring-in-your-first-source.md).

## Verify

- `catalog/papers/<citekey>.md` exists, with `type: paper`, a `relationships` block, the merged metadata, and any metadata the full-text extract produced
- `system/logs/capture-intake.jsonl` has a new line for the capture, and `system/logs/audit.jsonl` shows the writes the gate let through
- A `candidate` card landed in `inbox/` (or you've already resolved it)
- `notes/sources/<citekey>.md` exists at `lifecycle: proposed`, ready for your reading notes

## Batch capture

Capture papers one at a time. Run one palette command (or make one Zotero selection) per paper. Each enqueues its own card, and the Librarian works through them one at a time (one `running` card per lane).

For a topic-sized batch, skip manual capture. Run discovery instead, with **Memoria: delegate task** targeting `catalog`. If you are still clarifying what you want, ask the Co-PI to shape the batch first. See [Find new sources](find-new-sources.md).

## If a capture stalls

A scheduled sweep, `memoria-sweeps`, runs every 15 minutes. It looks for captures that logged an intake line but never produced a note, and re-enqueues an ingest card for them. The re-ingest is safe to repeat, so a first stall needs no action from you. For a card stuck beyond that, see [Fix a stuck card](../troubleshooting/fix-stuck-card.md).

## Related

- Next step: [Classify a source](classify-a-source.md)
- If the citekey isn't found: [Fix a stale .bib](../zotero/fix-stale-bib.md)
- The pipeline behind the card: [Ingest routing](../../reference/ingest.md)
- The entity and card schemas: [Document types](../../reference/document-types.md)


---

<!-- source: how-to-guides/library/use-structured-capture-forms.md -->

# Use structured capture forms

Stage a source from a guided form when you're entering its metadata by hand — a report, a web page, a dataset, or a paper you want to log without running the enrichment pipeline. The **structured source capture** form (a Modal Forms form, [ADR-71](../../adr/71-structured-capture-forms.md)) collects schema-valid fields and writes a proper `source` note plus an Inbox candidate, so a hand-entered source still arrives shaped like every other one.

This guide covers the **source-capture** form specifically. The project on-ramp form is a different surface — see [Start a writing project](../project/start-a-writing-project.md). The generated `memoria-fleeting-capture` and `memoria-claim-capture` forms back their dedicated palette commands.

## When to use the form

Pick the capture route by what you have:

| You have… | Use | Why |
| --- | --- | --- |
| A paper with a resolvable DOI or a Zotero/BibTeX citekey | **Capture from URL / Zotero** | Runs the full deterministic ingest — enrichment, classification, links ([Capture and ingest a source](capture-and-ingest.md)). |
| A source you'll describe by hand — report, web page, dataset, or a paper to log without enrichment | **Structured source capture** (this guide) | A guided form with schema-valid fields; no DOI required, no enrichment pipeline. |

## Prerequisites

- The `modalforms` plugin enabled (it ships with the vault — [Obsidian plugins](../../reference/obsidian-plugins.md)); the command no-ops with a notice if the Modal Forms API isn't available

## Steps

**1. Open the form.**

`Cmd/Ctrl-P` → **Memoria: structured source capture**.

**2. Fill the fields.**

| Field | Required | Notes |
| --- | --- | --- |
| Source title | yes | Becomes the note title and the candidate-card title. |
| Catalog entity | yes | A note picker over `catalog/` — link the source to its Catalog entity. |
| Source type | yes | `paper` · `dataset` · `repository` · `web-page` · `report`. |
| Evidence level | no | CEBM 1–5 or `ungraded`. |
| Research area | no | From the controlled vocabulary ([Vocabulary](../../reference/vocabulary.md)). |
| Methodology | no | From the controlled vocabulary. |
| Summary | no | Your-words summary — what it claims, on what evidence. |

Title and catalog entity are enforced; submit without them and the form re-prompts.

**3. Submit.**

The form stages two files: a `source` note at `lifecycle: proposed` under `notes/sources/` (with `# In my words`, `# Worth distilling`, and `# Tensions` sections, and a button to create a linked claim), and an Inbox `candidate` card pointing at it (`raised_by: modalforms`, `loudness: notice`). A success notice names both paths. The note is staging — it is not a canonical claim or hub write.

**4. Judge the candidate.**

Open the Inbox queue's **Needs me** view and resolve the card: keep the source (resolve to `current`) or archive it. Resolving is one palette command — [Work the review queue](../inbox/work-the-review-queue.md).

## Verify

- `notes/sources/<title-slug>.md` exists at `lifecycle: proposed` with `type: source` and the `entity:` wikilink you chose
- An `inbox/candidate-structured-source-<slug>.md` card landed, pointing at the staged note
- The note's `research_area` / `methodology` values match the controlled vocabulary exactly (off-vocabulary values silently drop from filtered views — [Fix missing query results](../troubleshooting/fix-missing-query-results.md))

## Related

- The enriched capture path for papers with a DOI/citekey: [Capture and ingest a source](capture-and-ingest.md)
- The palette command behind the form: [Obsidian command palette](../../reference/obsidian-command-palette.md)
- The `source` note schema: [Frontmatter fields](../../reference/frontmatter.md), [Document types](../../reference/document-types.md)
- Resolving the candidate it raises: [Work the review queue](../inbox/work-the-review-queue.md)
- The decision: [ADR-71: Structured capture forms](../../adr/71-structured-capture-forms.md)


---

<!-- source: how-to-guides/library/classify-a-source.md -->

# Classify a source

Settle a paper's `research_area` (and `methodology`) when ingest couldn't decide on its own.

Classifying tags a paper with its field of study. When a source comes in, ingest fills these tags in automatically wherever the answer is clear. Most of the time you do nothing. This guide covers the cases where the work lands on you.

Three situations bring you in:

- **Genuine ambiguity.** Ingest couldn't pick a value, so it left the field blank and raised a card in your queue. (A `flag` card is one type of Inbox card; it reports a finding and lists the top candidates with scores, but never decides for you.)
- **A draft to review.** The Librarian (the background worker that does library setup) often drafts a suggested classification. It parks the draft in a `_proposed_classification` block — a holding area in the paper's frontmatter, kept separate from the real fields until you accept it.
- **A correction.** Ingest applied a value you disagree with. You edit the frontmatter directly; no card is involved.

For what ingest decides and how, see [Ingest routing](../../reference/ingest.md).

## Prerequisites

- A paper ingested to `catalog/papers/<citekey>.md` ([Capture and ingest a source](capture-and-ingest.md))

## Steps

**1. Handle any `flag` card first.**

Open your queue from the navigator rail on the left: **Now** → **Needs you** opens the **Inbox** queue; its **Needs me** view lists what's waiting. If ingest hit genuine ambiguity, you'll see a card titled something like "Ambiguous research area for `<citekey>`". It reports the `finding` and the scored candidates, but states no verdict — you choose. Pick the right value, write it into the paper's frontmatter at `catalog/papers/<citekey>.md`, then resolve the card ([Work the review queue](../inbox/work-the-review-queue.md)).

**2. Open the paper and check what ingest applied.**

In `catalog/papers/<citekey>.md`, compare `research_area` and `methodology` against the paper itself. If a value is wrong, **edit the frontmatter directly** — there is nothing to approve.

Every decision, applied or flagged, is logged as one line in `system/logs/classify.jsonl`. That audit line is what makes a value safe to correct by hand. The thresholds ingest uses (`classify.confidence_floor`, `classify.near_tie_margin`) live in `.memoria/schemas/calibration.yaml`.

**3. Accept the Librarian's draft, if there is one.**

Look for a `_proposed_classification` block in the frontmatter. This is the Librarian's draft, parked in a holding area apart from the real fields. Read each proposed value. Copy the ones you accept — edited for accuracy — into the main frontmatter, then delete the whole `_proposed_classification:` block. The block is temporary and should not be left behind.

The `projects` sub-key inside the draft isn't a guess: it's derived from your optional [project hints](../setup/configure-project-hints.md).

**4. Confirm the paper reads `lifecycle: current`.**

A paper is created at `lifecycle: current` straight away — Catalog facts don't wait in a queue. (What sits at `proposed` is the candidate *card* in your queue, not the paper.) Classifying doesn't change the paper's lifecycle. Confirm it still reads `current`, then resolve the candidate card:

```yaml
lifecycle: current
```

**5. Reuse the same terms in your source note.**

When you fill the source note in `notes/sources/`, use the same `research_area` / `methodology` values you settled here. Mismatched vocabulary between the catalog and your notes is what makes later queries miss results ([Vocabulary discipline](../../explanation/knowledge/vocabulary-discipline.md)).

## Verify

- The paper reads `lifecycle: current`, has a settled `research_area`, and no longer has a `_proposed_classification` block
- No `flag` card for this citekey is still at `proposed` in your queue
- `system/logs/classify.jsonl` records the decision (applied or flagged) for this citekey

## Related

- Previous step: [Capture and ingest a source](capture-and-ingest.md)
- Next step: [Discuss a paper](discuss-a-paper.md)
- The automation's thresholds and audit trail: [Ingest routing](../../reference/ingest.md)
- Field semantics: [Frontmatter fields](../../reference/frontmatter.md)
- Optional per-project hints the proposal draws on: [Configure project hints](../setup/configure-project-hints.md)


---

<!-- source: how-to-guides/library/discuss-a-paper.md -->

# Discuss a paper

Think a source through with the Co-PI before writing a claim. The Co-PI is the one conversational agent — a reflective thinking-partner that questions and pushes back; it is read-only ([The Co-PI](../../explanation/profiles/co-pi.md)), so the thinking and the eventual claim note are yours.

## Prerequisites

- A source you've read, with a source note in `notes/sources/` ([Capture and ingest a source](capture-and-ingest.md))
- The `agent-client` Obsidian plugin connected ([Agent Client pane](../using-obsidian/use-the-agent-client-pane.md))

## Steps

**1. Pick a source from the discuss queue.**

Open the Library space and use the **Discuss queue** view — source notes at
`lifecycle: provisional`, the read-not-yet-distilled stage where the queue picks
a note up ([Frontmatter fields](../../reference/frontmatter.md)). Or open a
source note from the Library space if you already know which one you want to
think through.

**2. Orient yourself first.**

Re-read your **In my words** and **Worth distilling** sections, and keep `catalog/papers/<citekey>.md` open for the source metadata while you consult the paper/PDF if you need the full text. Bring a position, not a blank page.

**3. Open the Agent Client pane.**

Open the [Agent Client pane](../using-obsidian/use-the-agent-client-pane.md) with the source note active, then ask it to discuss the source. The Co-PI reads the active note when the question is about it.

**4. Work the standard questions.**

Good opening moves, whoever asks them first:

- What is the strongest single claim this paper makes?
- What does it connect to in your existing notes?
- What would falsify it?
- What is the smallest version of this idea that stands alone?

Answer in your own words, not the paper's.

**5. Follow where the dialogue leads.**

Don't treat the questions as a checklist. When a question feels too abstract, ask the Co-PI to ground it in a specific passage. When you disagree with the paper's framing, say so directly — the dialogue exists to surface *your* position, not to defend the author's. The conversation is done when you can state the paper's core claim in your own words and name where you stand on it.

**6. Decide the outcome.**

- **The paper yields one or more claims** → proceed to [write a claim note](../knowledge/write-a-claim-note.md), then advance the source note to `lifecycle: current`.
- **No standalone claim right now** → add one line to the source note's **Worth distilling** section saying why ("confirms existing claims, adds no new argument"), and advance the lifecycle anyway — the discuss queue reads `provisional`, and the decision is the work.

Closing the pane exports the transcript for later review ([Agent Client pane](../using-obsidian/use-the-agent-client-pane.md)). If the dialogue surfaced a durable insight, promote that insight yourself as a fleeting note, claim note, or source-note update.

## Verify

- The source note has moved off `lifecycle: provisional` and out of the discuss queue
- Nothing in the vault was edited by the agent — the Co-PI's write scope is empty; if you see an unexpected edit, treat it as a configuration error and check `system/logs/audit.jsonl`

## Related

**How-to**

- Previous step: [Classify a source](classify-a-source.md)
- Next step: [Write a claim note](../knowledge/write-a-claim-note.md)
- A named theoretical frame for the session: [Read a paper through a lens](read-through-a-lens.md)

**Reference**

- The full permission matrix: [Profile capabilities](../../reference/profiles.md)

**Explanation**

- The agent in the Agent Client pane: [The Co-PI](../../explanation/profiles/co-pi.md)
- The queue this works down: [Discuss queue](../../explanation/dashboards/synthesis-agenda/discuss-queue.md)


---

<!-- source: how-to-guides/library/read-through-a-lens.md -->

# Read a paper through a lens

Read a paper through a named theoretical frame so the Co-PI questions it from an angle you choose. This is one of the deliberate Co-PI-only cases: the synchronous, read-only dialogue is the product, so the `ask-read-lens` skill ([Hermes CLI](../../reference/hermes-cli.md#skill-names)) is never queue-dispatched. If the lens session should create a durable artifact, capture that artifact separately with the palette or a normal delegated card.

## Prerequisites

- A source note (or a cluster of notes) open to read against
- The [Agent Client pane](../using-obsidian/use-the-agent-client-pane.md) connected; this guide is intentionally conversational rather than a queued action

## Steps

**1. Pick a lens that fits the question you're bringing.**

Choose by the question in your head, not by the paper on screen — the point of a lens is to read a familiar text through an unfamiliar frame. Examples of frames worth naming:

| Lens | Frame it brings |
| --- | --- |
| sensemaking | How people interpret and act on information |
| informational justice | Who is served and who is left out |
| design justice | Power, participation, and harm in design |
| receptivity and timing | When an intervention can land |

**2. Open the session in that lens.**

Open the [Agent Client pane](../using-obsidian/use-the-agent-client-pane.md) with the source note active, and ask the Co-PI to read through the frame by name:

> "Read this through a sensemaking lens."

The lens provides the framing; you provide the answers through that frame.

**3. Stay in one frame per session.**

Switching lenses mid-session muddies whose questions are being asked. For a different lens, clear the pane and start a new session — one frame at a time.

**4. Read actively — the lens shapes questions, not answers.**

The Co-PI questions the text through the frame; it will not summarize your thinking back to you or write anything to the vault ([The Co-PI](../../explanation/profiles/co-pi.md)). The entire product is the conversation, which exports on close for review ([Agent Client pane](../using-obsidian/use-the-agent-client-pane.md)).

**5. Capture what the lens surfaced — yourself.**

When the frame surfaces something worth keeping, author it in your own words: a fleeting note (`Cmd/Ctrl-P` → **Memoria: capture fleeting**) or a claim note ([Write a claim note](../knowledge/write-a-claim-note.md)). The lens did its job if you leave with a question or claim you wouldn't have reached unframed.

## Add a standing lens of your own

Curate a lens you reach for repeatedly as a **pattern** in `system/patterns/` ([ADR-53](../../adr/53-pattern-library.md)). Author the framing as a pattern note (the stance and the *kinds of questions* the frame privileges — not a summary of any one paper), then set `lifecycle: current` when ready. The Co-PI can then run it through the patterns MCP — typed, audited, and provenance-logged.

## Verify

- The session stays in the named frame and questions through it
- Nothing in the vault was edited by the agent (the Co-PI is write-denied)
- Anything durable from the session exists as *your* note — fleeting or claim

## Related

- The workflow it anchors: [Discuss a paper](discuss-a-paper.md)
- Capturing the output: [Write a claim note](../knowledge/write-a-claim-note.md)
- Curated frames as data: [Document types](../../reference/document-types.md)
- The profile behind it: [The Co-PI](../../explanation/profiles/co-pi.md)


---

<!-- source: how-to-guides/library/run-a-systematic-review.md -->

# Run a systematic review

Set up a PRISMA-compliant screening protocol and process the results into Memoria. Use this when you need a defensible, reproducible literature search — not for exploratory discovery, which the normal [find → capture](find-new-sources.md) path handles.

> **Status: a manual procedure.** There is no "run systematic review" command and no screening template. The workflow composes existing pieces — a protocol note you author, your own database searches, optional [ASReview](https://asreview.nl/) for large pools, and the standard capture pipeline. Every step below works today; the protocol discipline is yours to keep.

## Prerequisites

- Memoria installed and the Librarian lane running
- A defined, written research question
- Access to at least two literature databases (PubMed, ACM DL, Scopus, arXiv, …)
- Zotero + Better BibTeX — batch ingest without a `.bib` backbone is not worth the friction
- [ASReview](https://asreview.nl/) installed if the title/abstract pool exceeds ~200 records

## Steps

**1. Create a protocol note.**

Author it as a project or source note attached to the review work. Record: review title, protocol date, reviewer, review type (Scoping / Systematic / Rapid).

**2. Write your research question and criteria.**

In the protocol note, complete:

- **Research question** — one sentence, specific enough to determine inclusion at the abstract stage
- **Inclusion criteria** — 3–5 explicit conditions a source must meet
- **Exclusion criteria** — 3–5 explicit grounds for rejection

Commit the protocol before running any searches. A protocol written after seeing the results is not a protocol.

**3. Run database searches.**

Run your search string in each database. Record in a protocol table: database, search date, records retrieved. Export each result set to RIS or BibTeX, combine, and deduplicate.

**4. Screen titles and abstracts.**

**Under ~200 records — screen manually:** apply your criteria per record; log decisions in the protocol note's decision table (`Citekey / DOI | Decision | Exclusion reason`).

**200+ records — use ASReview:**

```bash
asreview oracle combined_export.ris
```

Label records in the ASReview interface; when the active-learning curve flattens, export the labeled dataset and map decisions back to the protocol log. Either way, tag each record's screening outcome in Zotero before ingest so the provenance survives.

**5. Full-text assess included records.**

For each record marked relevant at the abstract stage: retrieve the full text, re-apply the criteria, record the final decision and any exclusion reason.

**6. Update the PRISMA counts.**

Complete the protocol's flow table: identified → duplicates removed → screened → excluded (title/abstract) → full-text assessed → excluded (full text) → **included**.

**7. Capture the included sources.**

Add each included paper to Zotero, then capture it one per paper through the standard intake path ([Capture and ingest a source](capture-and-ingest.md)). The ingest operation builds the Catalog entity and raises the candidate card — for a protocol-screened paper, the keep decision is already made, so resolve each card to `current` and move on.

## Verify

- The protocol note has all PRISMA counts filled in and `lifecycle: current`
- Every included source has a Catalog entity in `catalog/papers/`
- Every excluded source has a decision and reason recorded in the protocol

## Related

- Exploratory discovery (no protocol needed): [Find new sources](find-new-sources.md)
- The intake path per paper: [Capture and ingest a source](capture-and-ingest.md)
- The adopt-on-demand decision: [ADR-16](../../adr/16-systematic-review-adopt-on-demand.md)


---

<!-- source: how-to-guides/library/archive-a-source.md -->

# Archive a source

Retire a source note that is no longer active — superseded, irrelevant to current projects, or fully processed with nothing new to extract. Archiving is a **lifecycle change, not a folder move**: the note stays where it is and `lifecycle: archived` takes it out of every active view.

## Prerequisites

- The source note is at `lifecycle: current` (fully distilled), or you've decided it won't be processed further

## Steps

**1. Confirm there are no open board cards for this source.**

Check for open cards referencing this citekey ([Hermes CLI](../../reference/hermes-cli.md#board-management)):

```bash
hermes kanban list
```

If an open card references the citekey, archive it with a reason first:

```bash
hermes kanban archive <card-id> --reason "source archived: superseded"
```

**2. Open the source note in Obsidian.**

Use the Library space's source views or Obsidian search to open the reading record
for the source. The on-disk path is `notes/sources/<note>.md`, but navigation should
start from the space/Bases surface.

**3. Set `lifecycle: archived` in frontmatter.**

```yaml
lifecycle: archived
```

Add one line at the top of the body saying why ("superseded by newer work", "out of scope", "fully processed"). This is the only record of why this source left the active pool.

**4. Decide whether the Catalog entity archives too.**

The paper entity at `catalog/papers/<citekey>.md` is the bibliographic record, not your reading of it — it usually stays `current` so its `relationships` edges keep serving the graph. Set the entity to `lifecycle: archived` only when the record itself should leave the Catalog views (for a *retracted* paper, use `lifecycle: retracted` instead — usually prompted by a retraction `alert` card).

**5. Confirm any claims that cite this source still stand.**

Open the backlinks panel before walking away. Claims citing the source remain valid — the source is archived, not deleted, and every `sources:` citekey still resolves. If the archive was prompted by a retraction, revisit those claims deliberately (soften, supersede, or caveat).

## Verify

- The source note carries `lifecycle: archived` and no longer appears in the active views of `system/dashboards/sources.base`
- No open board cards reference this citekey
- Claims citing this source still resolve their `sources:` citekeys

## When not to archive

Do not archive a source just to clear it from a queue. If a source has sat unread for weeks but you still plan to read it, leave it at `lifecycle: proposed` — the backpressure is intentional. Archive only when you've made a deliberate decision that this source is done.

## Related

- Weekly review (surfaces stale sources): [Run the weekly review](../inbox/run-the-weekly-review.md)
- Lifecycle field values: [Frontmatter fields](../../reference/frontmatter.md)
- Why archived notes aren't deleted: [The knowledge cycle](../../explanation/knowledge/knowledge-cycle.md)
- What happens on a retraction hit: [Run a retraction sweep](../operate/run-a-retraction-sweep.md)


---

<!-- source: how-to-guides/knowledge/README.md -->

# Knowledge

Build durable synthesis — distill claims, connect them into the graph, and curate the structure. Performed inside Obsidian; claims and hubs are review-gated, so you author and the agents propose.

| Guide | What it covers |
| --- | --- |
| [Write a claim note](write-a-claim-note.md) | Distill a source into a durable claim in `notes/claims/` |
| [Link related claims](link-related-claims.md) | Add typed `supports` / `contradicts` relations between claims |
| [Advance a claim to evergreen](promote-a-claim.md) | Mark a settled claim by advancing its `maturity` — no move, no folder |
| [Build a hub](build-a-moc.md) | Create a navigational hub when a claim cluster crosses 15–20 notes |
| [Refactor claim notes](refactor-a-note.md) | Merge near-duplicates or split compound claims |
| [Manage your topic vocabulary](manage-vocabulary.md) | Add terms, rename safely, prune the active list |
| [Query the vault](query-the-vault.md) | Use the Co-PI for read-only synthesis grounded in your notes |
| [Run a pattern](run-a-pattern.md) | Run a shipped prompt-transformation over the active note or a selection |


---

<!-- source: how-to-guides/knowledge/write-a-claim-note.md -->

# Write a claim note

Distill a source into a single, durable claim in `notes/claims/`. One claim per note; no more than 2–3 claims per source. Claims live in a **review-gated zone** — agents can only propose writes there; you author claims directly, because they're yours.

## Prerequisites

- A read source whose **Worth distilling** section names the candidate ([Discuss a paper](../library/discuss-a-paper.md) sharpens it first)

## Steps

**1. Check for a near-duplicate first.**

For a quick read-only duplicate check, ask the Co-PI: "Do I already hold a claim like *\<one-sentence statement\>*?" — it searches the vault and answers in the pane because the product is conversational judgment, not a card. For a systematic pass over a claim set or topic, use **Memoria: delegate task** → `verify` instead; the Peer-reviewer's duplicate hunt returns flag cards. If a close match exists, extend that note rather than creating a twin.

**2. Create the note.**

From a source note, click **Create linked claim** under **Worth distilling**. It creates a new note in `notes/claims/`, adds the source citekey to `sources`, links the claim back into the source note, and opens the claim for editing.

If you prefer the palette, open the source note and run `Memoria: create linked claim note` ([Obsidian command palette](../../reference/obsidian-command-palette.md)). The command asks for the claim sentence, then performs the same linked-source write. Before filing, it runs the qmd pre-file similarity shadow check and writes neighbours to a `[!similarity]` callout/log when available; that report is advisory and never blocks note creation.

For a standalone claim, use `Cmd/Ctrl-P` → **Memoria: write claim note**. The guided form asks for the title, maturity, supporting sources, topics, and claim statement, then writes a new note in `notes/claims/` from `system/templates/claim.md` with the frontmatter pre-populated:

```yaml
type: claim
lifecycle: current
maturity: seedling
sources:
  - mamykina2010sense
topics: []
links:
  supports: []
  contradicts: []
```

**3. Name the file with the claim as the title.**

The filename *is* the claim: `receptivity-decreases-under-high-cognitive-load.md`, not `receptivity.md` or `mamykina-claim.md`. One falsifiable sentence, in your words. A topic stub is not a claim note.

**4. Write the body.**

- **Claim** — the assertion, standing alone; a reader with no access to the source should understand it.
- **Evidence** — why this seems true; **every line traces to a citekey in `sources`** (the provenance guardrail).
- **Connections** — the conceptual neighbors, in prose.

Do not quote the paper directly — distillation, not transcription.

**5. Check `sources`.**

The linked-claim button fills the active source's citekey for you. For standalone claim notes, list the citekey(s) of the supporting paper(s):

```yaml
sources: ["mamykina2010sense"]
```

**6. Leave maturity at `seedling`.**

Maturity (`seedling → budding → evergreen`) tracks development, never trust — a seedling isn't a doubted claim, it's a young one. It advances as connections accumulate: [Advance a claim to evergreen](promote-a-claim.md).

**7. Add typed links if applicable.**

If the claim supports or contradicts an existing claim, say so in `links:` — the contradictions are the valuable ones ([Link related claims](link-related-claims.md)). If it *replaces* an existing claim, that is supersession, not a link: set `superseded_by` on the **old** note instead ([Advance a claim to evergreen](promote-a-claim.md)).

**8. Close the loop on the source.**

Advance the source note past `provisional` and, if a candidate card is still open for this paper, resolve it — its job is done.

## Verify

- The file exists at `notes/claims/<claim-as-a-sentence>.md` with `maturity: seedling`, `lifecycle: current`
- At least one citekey in `sources`, and every Evidence line traces to one
- The claim appears in `system/dashboards/claims.base` under seedling

## Related

**How-to**

- Previous step: [Discuss a paper](../library/discuss-a-paper.md)
- When the claim settles: [Advance a claim to evergreen](promote-a-claim.md)
- Relating it to its neighbors: [Link related claims](link-related-claims.md)

**Reference**

- The claim schema: [Document types](../../reference/document-types.md)
- Field semantics: [Frontmatter fields](../../reference/frontmatter.md)

**Explanation**

- Why each section functions as knowledge: [Note body structure](../../explanation/knowledge/note-body-structure.md)
- The summary-without-synthesis pitfall: [Common pitfalls](../../explanation/knowledge/common-pitfalls.md)


---

<!-- source: how-to-guides/knowledge/link-related-claims.md -->

# Link related claims

Add a typed `supports` / `contradicts` link between two claims that **already exist**; to set one while writing a claim, see [Write a claim note](write-a-claim-note.md).

> **`links:` vs `relationships`.** `links:` are authored edges on notes (your thinking); `relationships` are given edges on Catalog entities (facts from the record, written by the ingest operation) ([ADR-52](../../adr/52-links-vs-relationships.md)).

## Prerequisites

- At least two claim notes in `notes/claims/`
- These links are yours to set — `notes/claims/` is review-gated; agents only *propose*, never write

## Steps

**1. Decide whether the relationship is worth typing.**

Link for usefulness, not completeness. Add a typed link only when "*what contradicts X?*" or "*what supports X?*" would matter in a later reading or writing session. Untyped concept links (a plain `[[wikilink]]` in the body) remain first-class — don't promote every connection.

**2. Pick the link type.**

| Link | Meaning | Direction |
| --- | --- | --- |
| `supports` | This claim supports the linked claim | Directional — set it on the supporting claim |
| `contradicts` | The two claims disagree | Symmetric — set it on either; the dashboard reads both ways |

If the relationship is *temporal replacement* — this claim makes an older one obsolete — that is **not** a `links:` entry; it's supersession (`superseded_by` on the old claim), covered in [Advance a claim to evergreen](promote-a-claim.md).

**3. Add the entry to the claim's `links:` map.**

Open the claim note and extend the frontmatter block the claim template ships:

```yaml
links:
  supports: []
  contradicts:
    - "[[receptivity-decreases-under-high-cognitive-load]]"
```

Both keys can carry lists — a claim may support one claim and contradict another.

**4. Point with the exact note name.**

The target is a wikilink to the other claim note (lowercase kebab-case, the claim as a sentence). Copy it from the target's filename rather than retyping — the Linter's `frontmatter-link` detector flags any frontmatter wikilink that resolves to no note, but only on its next pass.

**5. Let agents propose; confirm yourself.**

The Librarian's `link` lane surfaces candidate connections and tensions as Inbox proposals ([Review link suggestions](../inbox/review-link-suggestions.md)). Never copy a proposed link into `links:` unread — the agent proposes, you dispose.

**6. Confirm it surfaced.**

For a `contradicts` link, open the Knowledge space's **Contradictions** view. The pair should appear — that visibility is the payoff of typing the link.

## Verify

- The `links:` keys stay within `supports` / `contradicts` (the Linter's `schema-check` flags anything else)
- A `contradicts` pair appears in Knowledge's **Contradictions** view
- Every link target resolves to a real claim note

## Related

**How-to**

- Set a link while authoring: [Write a claim note](write-a-claim-note.md)
- Triage agent-proposed links: [Review link suggestions](../inbox/review-link-suggestions.md)
- The temporal complement (replacement, not disagreement): [Advance a claim to evergreen](promote-a-claim.md)

**Reference**

- The two edge kinds: [Frontmatter fields](../../reference/frontmatter.md)

**Explanation**

- The consumer: [Contradictions](../../explanation/dashboards/synthesis-agenda/contradictions.md)
- Why connections are load-bearing: [Note body structure](../../explanation/knowledge/note-body-structure.md)


---

<!-- source: how-to-guides/knowledge/promote-a-claim.md -->

# Advance a claim to evergreen

Mark a claim as settled knowledge by advancing its `maturity` to `evergreen` — no folder move, no rename; the claim stays in `notes/claims/`.

## Prerequisites

- The claim has accumulated real connections — cross-linked from several distinct sources or claims, and stable across recent reading
- The claim does **not** carry `superseded_by` — a superseded claim represents prior belief and never advances

## Steps

**1. Find candidates.**

Knowledge's **Claims by maturity** view groups claims by maturity. Long-stable `budding` claims with several inlinks are the candidates. The weekly review is the natural moment.

**2. Re-read the claim as a stranger.**

An evergreen claim will be read months from now without its original context. Tighten the body: the claim in one falsifiable sentence, the evidence with every line tracing to a `sources` citekey, the connections in prose.

**3. Advance the maturity.**

```yaml
maturity: evergreen
```

No move, no rename, no lifecycle change — `lifecycle: current` was already the claim's state from creation.

**4. Give it a navigational home.**

If a hub for the topic exists in `notes/hubs/`, add the claim to its `members` list. If this is the third or fourth settled claim on a topic with no hub, create one: [Build a hub](../knowledge/build-a-moc.md).

**5. Handle supersession separately.**

If this claim *replaces* an older one, set on the **old** note:

```yaml
superseded_by: "[[this-new-claim]]"
lifecycle: archived
```

The Linter's `fama-exposure` detector then flags any downstream note still wikilinking the superseded claim — reuse of obsolete memory.

## Verify

- The claim shows under **evergreen** in `system/dashboards/claims.base`
- A hub lists it as a member (or you've consciously decided the topic doesn't need one)
- No `superseded_by` claim was advanced

## Notes

**Don't advance to clear a queue.** Evergreen is a judgment that this claim is settled in your corpus. If you're uncertain, leave it at `budding` — that is not a penalty state.

## Related

- Where claims are born: [Write a claim note](write-a-claim-note.md)
- The hub the evergreen claim joins: [Build a hub](../knowledge/build-a-moc.md)
- Maturity vs lifecycle, and why `reference` was dropped: [Frontmatter fields](../../reference/frontmatter.md)
- The promotion rules: [Why promotion is gated](../../explanation/knowledge/promotion-model.md)


---

<!-- source: how-to-guides/knowledge/build-a-moc.md -->

# Build a hub

Create a structure note in `notes/hubs/` that gives a dense claim cluster a stable entry point — a navigational home that says what a topic holds, what's settled, and what's still fighting. Like claims, hubs are review-gated: agents only propose; you author ([ADR-50](../../adr/50-universal-lifecycle-and-maturity.md)).

## When to create a hub

When a topic has accumulated a handful of claims that belong together — typically by the third or fourth settled claim on one topic. Earlier is premature structure; much later and the cluster is already hard to navigate.

## Steps

**1. Create the note from the template.**

In `notes/hubs/`, create a new note from `system/templates/hub.md`:

```yaml
type: hub
lifecycle: current
topic: <your-topic>
members: []
links: {}
```

**2. Name it after the topic.**

Use the topic slug directly, for example `receptivity-timing.md` — the folder already says what it is.

**3. Write the shape of the topic.**

Two to four sentences in the **Shape of the topic** section: what this cluster is about, how the member claims relate, what's settled, what's still contested.

**4. List the members.**

Add the claim notes (and key source notes) to the `members` list and wikilink them in the **Members** section. Curate — omit tangentially related notes; one strong hub beats a complete-but-noisy one.

**5. Name the gaps.**

Note what the cluster is missing — thin sub-topics, open questions, papers not yet captured. Each named gap is a ready-made discovery prompt for the Co-PI ([Find new sources](../library/find-new-sources.md)).

## Splitting a hub

When one branch of a hub grows past ~15–20 member claims, split it: create a new hub for the branch, move those members over, and in the parent replace the individual links with one link to the child hub.

## Owners

You author and curate hubs. The Librarian's `map` lane can propose that a cluster deserves one (a `gap` card in the Inbox), and the Linter's `graph-analyze` detector flags orphan hubs with zero inlinks — but every structural decision is yours.

## Verify

- The hub validates: `type: hub`, `topic` set, every `members` entry resolving to a real note
- The member claims link back (open the backlinks panel on the hub)
- The hub shows up where you'd look for the topic — link it from `research-focus.md` or a parent hub if not

## Related

- The claims that fill it: [Advance a claim to evergreen](../knowledge/promote-a-claim.md)
- The hub type and schema: [Document types](../../reference/document-types.md)
- Why hubs matter to the cycle: [The knowledge cycle](../../explanation/knowledge/knowledge-cycle.md)


---

<!-- source: how-to-guides/knowledge/refactor-a-note.md -->

# Refactor claim notes

Keep claim notes atomic and remove duplication without losing provenance. Agents surface the candidates; every structural decision — merge, split, or leave — is yours, because `notes/claims/` is review-gated.

## When to refactor

- A claim's body contains an "and" doing real work — two distinct ideas in one note
- A duplicate hunt flags two notes saying the same thing in different words
- A note has grown to where you hesitate to link it because only part of it applies

## Find duplicate candidates

Use `Cmd/Ctrl-P` -> **Memoria: delegate task** -> `verify`:

> "Verify my claims on `<topic>` for near-duplicates."

The Peer-reviewer's `verify` lane (and the sweeps operation's similarity checks) return findings as **flag cards** in the Inbox, each naming the suspect pair. Nothing is auto-merged — the lane can only write cards.

## Merge two notes into one

1. **Review the pair side by side.** Decide which is the stronger formulation.
2. **Combine the content.** Copy any non-redundant Evidence from the weaker note into the stronger.
3. **Merge the sources.** Union the citekeys into the stronger note's `sources:`.
4. **Merge the links.** Carry any `supports` / `contradicts` entries (and `topics`) the weaker note held.
5. **Redirect backlinks.** Search for wikilinks to the weaker note and point them at the stronger one; update any hub `members` lists.
6. **Archive the weaker note.** Set `lifecycle: archived` and `superseded_by: "[[stronger-note]]"`. Do not delete — the note has provenance value, and the Linter's `fama-exposure` detector will flag anything still leaning on it.

## Split one note into two

1. **Create the second note** via `Cmd/Ctrl-P` → **Memoria: write claim note**.
2. **Move the second claim** out of the original's body — each note one falsifiable sentence.
3. **Divide the sources.** Assign citekeys to whichever claim each source actually supports.
4. **Link the pair** if they relate: a `supports` or `contradicts` entry in `links:`.
5. **Update backlinks and hub members** to point at the right half.

## Verify

- Each resulting note states exactly one claim, with every Evidence line tracing to its own `sources`
- The archived note carries `superseded_by`, and no active note wikilinks it (the `fama-exposure` detector confirms on its next pass)
- The flag card that started this is resolved

## Related

- Validation after structural edits: [Run the Linter](../operate/run-the-linter.md)
- The compound-note failure this fixes: [Common pitfalls](../../explanation/knowledge/common-pitfalls.md)
- The note shape you're refactoring toward: [Note body structure](../../explanation/knowledge/note-body-structure.md)
- The lane that surfaces candidates: [The Peer-reviewer](../../explanation/profiles/peer-reviewer.md)


---

<!-- source: how-to-guides/knowledge/manage-vocabulary.md -->

# Manage your topic vocabulary

Keep the `research_area`, `methodology`, and `topics` values consistent across your corpus — so Dataview and Bases views stay reliable and classification stays navigable as the vault grows. The controlled lists live in **`system/vocabulary.md`**, which ships with the vault (and is golden-copied, so the Linter can detect drift from the shipped scaffold once you've made it yours).

These vocabularies are deliberately **open** — yours to define. The fixed Memoria vocabularies (lifecycle, maturity, certainty, card types) are schema-enforced and not yours to extend.

## When to do each task

| Trigger | Task |
| --- | --- |
| Starting a new corpus | Define your initial lists |
| The active list exceeds ~30 terms | Prune and consolidate |
| A term's meaning has drifted or split | Rename it safely |
| Annually, or after a major reading batch | Full vocabulary review |

## Step 1 — Make `system/vocabulary.md` yours

Open it and structure one section per field:

```markdown
## research_area
- receptivity-detection
- ema-experience-sampling
- health-equity

## methodology
- field-study
- qualitative-interview
- meta-analysis

## topics (claims)
- receptivity-timing
- sensemaking
```

Keep each list to **~30 terms**. A tighter vocabulary produces more consistent classification and more reliable queries ([Vocabulary discipline](../../explanation/knowledge/vocabulary-discipline.md)).

Note the consumers: the ingest operation's automated classify stage rolls OpenAlex topics into `research_area` on paper entities ([Ingest routing](../../reference/ingest.md)); you carry the same terms onto source notes and use `topics` on claims. Your list is what keeps the human side consistent with the automated side.

## Step 2 — Add a new term

1. Check the relevant section first — the term may already exist under another name. That check is the whole discipline.
2. Add it to `system/vocabulary.md`, then use it in the note you're classifying.
3. If the list is already at ~30, ask whether an existing term covers the ground before adding.

## Step 3 — Rename a term safely

Renaming a vocabulary value across the corpus is the same git-disciplined manual pass as any field migration (commit → enumerate → edit → lint → commit): [Run a schema migration](../operate/run-a-schema-migration.md) is the full procedure. The two vocabulary-specific points:

- **Also update `system/vocabulary.md`** in the same pass — the controlled list and the notes must move together.
- **Your selector is a frontmatter value**, so enumerate with Obsidian global search for the old term (or `grep -rl "old-term" notes/ catalog/`) before editing.

## Step 4 — Annual vocabulary review

Once a year (or after a major reading batch), walk each list:

1. **Prune** terms appearing on fewer than ~3 notes — they're not load-bearing.
2. **Consolidate** terms that drifted to mean the same thing (rename the smaller into the larger, per Step 3).
3. **Split** a term that now covers two distinct concepts.

## Verify

- `system/vocabulary.md` reflects the current active lists, each ≤ ~30 terms
- A grep for each removed term returns no frontmatter hits
- The Linter's `schema-check` and `dashboard-field-drift` detectors report nothing new

## Related

- Where the automated side applies terms: [Classify a source](../library/classify-a-source.md)
- The validation pass: [Run the Linter](../operate/run-the-linter.md)
- Why three open fields and a small list: [Vocabulary discipline](../../explanation/knowledge/vocabulary-discipline.md)


---

<!-- source: how-to-guides/knowledge/query-the-vault.md -->

# Query the vault

Ask the vault a research question and get a grounded answer in the Agent Client pane. Query is a deliberate Co-PI-only case because the product is synchronous, read-only dialogue: nothing is written, and anything worth keeping you author yourself. When you want a durable artifact instead of a conversation, use a direct command or delegated lane task.

## Which retrieval path?

Several surfaces overlap; pick by what you want *out*:

| You want… | Use | Output |
| --- | --- | --- |
| A synthesized answer grounded in your notes | **Ask the Co-PI** (this guide) | conversation in the pane |
| To sharpen your *own* thinking by being questioned | The Co-PI's questioning posture — say "push back on this" | conversation in the pane |
| A written, citable synthesis to keep | Delegate a **`draft`** task | a draft in `projects/`, via the Inbox |
| A fast lookup of a known term or field | Obsidian search, or a Dataview/Bases view | results in the UI |

Rule of thumb: converse when *you* should do the synthesizing; use a command or delegated lane task when you want a card, report, draft, or other durable output you'll verify and keep.

## Prerequisites

- At least a handful of classified sources and a few claims — retrieval needs something to retrieve
- The `qmd` search index current (the Co-PI's vault search runs on it — [Rebuild the search index](../operate/rebuild-the-search-index.md) if results look stale)

## Steps

**1. Ask in natural language.**

Open the [Agent Client pane](../using-obsidian/use-the-agent-client-pane.md) and ask the question, not keywords:

> "What predicts JITAI receptivity?"
> "Which of my claims would the 2024 papers contradict?"
> "What methods have my sources used to measure EMA compliance?"

The active note is passed as a readable reference; attach others when the question is about a specific cluster ([Agent Client pane](../using-obsidian/use-the-agent-client-pane.md)).

**2. Interrogate the answer.**

The Co-PI reads the vault directly and never writes (hybrid keyword + vector
search over Memoria's filtered `qmd` MCP, plus the typed graph — [The
Co-PI](../../explanation/profiles/co-pi.md)). Current retrieval excludes claim
notes that carry `superseded_by`; ask explicitly for historical/superseded claims
when you are reconstructing what changed. Push on it: "which note says that?",
"what disagrees with this?". An assertion it can't ground in a note of yours is
its synthesis, not your knowledge — treat it accordingly.

**3. Keep what's worth keeping — yourself.**

- A genuine new synthesis → distill it properly: [Write a claim note](../knowledge/write-a-claim-note.md).
- Context for a writing project → copy into your `projects/<slug>/` scratch.
- A one-off answer → close the pane. The transcript auto-exports for review ([Agent Client pane](../using-obsidian/use-the-agent-client-pane.md)); promote anything durable yourself instead of letting the raw transcript become a canonical note.

## Verify

- Every assertion you kept traces to a note or citekey you checked
- Anything durable from the session exists as *your* note, not just a transcript

## Related

- Distilling a kept answer: [Write a claim note](../knowledge/write-a-claim-note.md)
- The transcript's afterlife: [Triage fleeting notes](../inbox/triage-fleeting-notes.md)
- The search engine underneath: [Rebuild the search index](../operate/rebuild-the-search-index.md)
- The agent in the Agent Client pane: [The Co-PI](../../explanation/profiles/co-pi.md)


---

<!-- source: how-to-guides/knowledge/run-a-pattern.md -->

# Run a pattern

Run a shipped prompt-transformation — analyze the claims in a note, red-team an argument, summarize for recall — over the active note or a selection, and read the result. A pattern proposes; it never writes a canonical note. For the full library and the runner contract, see [Pattern library](../../reference/patterns.md).

## When to use a pattern

- You want a quick, repeatable analytical pass (claims, falsifiability, tensions) over something you're reading or drafting
- You want the same framing applied consistently every time, with a provenance line recording that it ran
- The output is *raw material you'll reshape* — not a finished note. If you want durable prose, delegate a `draft` task instead ([Draft with the Writer](../project/draft-with-writer.md)).

## Prerequisites

- The patterns MCP wired into the lane (it ships on the Librarian and Co-PI profiles)
- The note or selection you want to run over, open in Obsidian

## Steps

**1. Pick the surface.**

Open the note you want to analyze, or select the span in the editor. The active note rides along as the pattern's `input_ref` when you don't select text.

**2. Run the pattern.**

`Cmd/Ctrl-P` → **Memoria: run pattern**, then choose from the suggester. The list is the runnable (`lifecycle: current`) patterns, filtered by mode — library patterns for ongoing reading, project patterns for a writing project. The command stages a Librarian card that calls `patterns_run`; the composed prompt is the shared voice preamble plus the pattern, with your note or selection substituted in.

Equivalent: **Memoria: assist patterns**, or ask the Co-PI in the Agent Client pane ("run analyze-claims over this note").

**3. Read the result where it lands.**

The product lands in the pattern's staging target — a `projects/` scratch note or `notes/fleeting/`, never a gated zone. Treat it as a proposal: the patterns are written to *propose, never assert*, to flag uncertainty, and to mark a missing source as `[no source]` rather than invent one.

**4. Keep what's worth keeping — yourself.**

A pattern result is staging. Distil anything durable into your own note ([Write a claim note](../knowledge/write-a-claim-note.md)); a `contradicts` candidate from `surface-tensions` goes through the link gate ([Review link suggestions](../inbox/review-link-suggestions.md)), never written directly.

## Verify

- The result appears in the pattern's staging target (`projects/` or `notes/fleeting/`), not in `notes/claims/` or `catalog/`
- `system/logs/patterns.jsonl` has a new line for the run (pattern id, `run_id`, target)
- Anything you keep exists as *your* note, distilled in your words — not the raw pattern output promoted as-is

## If the result is a dry-run

If the run reports `dry_run: true`, the pattern's `output_target` is empty or points into a review-gated zone — it produced a prompt but no sanctioned write target, and the Linter flags the pattern file. This is a pattern-authoring fix, not a run-time one: see the gated-target rule in [Pattern library](../../reference/patterns.md).

## Related

- The library, schema, and runner contract: [Pattern library](../../reference/patterns.md)
- When to delegate durable prose instead: [Draft with the Writer](../project/draft-with-writer.md)
- Distilling a kept result: [Write a claim note](../knowledge/write-a-claim-note.md)
- The palette command behind this guide: [Obsidian command palette](../../reference/obsidian-command-palette.md)


---

<!-- source: how-to-guides/project/README.md -->

# Project

Steer an inquiry to output — scope, frame, draft, verify, and export a deliverable. Performed inside Obsidian via the Project space, Inbox, and `Memoria:` task commands; the Agent Client pane helps shape unclear handoffs. Export runs in the terminal.

| Guide | What it covers |
| --- | --- |
| [Start a writing project](start-a-writing-project.md) | Scaffold a Project space and active thesis |
| [Assess your corpus](assess-your-corpus.md) | Delegate a `map` task: dense clusters, thin coverage, gap cards |
| [Frame a project](frame-a-project.md) | Competing outlines from the `draft` lane; choose one framing |
| [Supersede a thesis](supersede-a-thesis.md) | Pivot the active thesis while preserving the old argument trail |
| [Use canvas for argument mapping](use-canvas-for-argument-mapping.md) | Arrange claims spatially to find structure before prose |
| [Draft with the Writer](draft-with-writer.md) | Delegate sections to the `draft` lane; edit the result |
| [Verify and revise a draft](verify-and-revise.md) | Delegate `verify` passes; act on flag cards; loop |
| [Export a draft](export-a-draft.md) | Pandoc export to Word, PDF, or plain Markdown |
| [Create a code artifact](create-a-code-artifact.md) | Delegate the `code` lane; hand off to an external coding agent |


---

<!-- source: how-to-guides/project/start-a-writing-project.md -->

# Start a writing project

Stand up the bounded Project space a writing project draws from.

Use this when a cluster has become more than a topic: you have a question, an initial thesis or survey intent, and enough claims/sources that it needs a Project space record instead of loose scratch.

## Steps

**1. Build the synthesis surface.** Distill claims into `notes/claims/` and gather the cluster under a hub in `notes/hubs/` — [Tutorial 04: Draft a section from your claims](../../tutorials/04-draft-a-section-from-your-claims.md) walks the whole arc.

**2. Start the project.** In Obsidian, run `Memoria: start project`. Fill the title and output mode; add scope topics if they are clear now. Thesis mode also asks for the provisional thesis. The command derives the slug, creates blank PICO/FINER scaffolding for shaping, and writes the project and thesis records shown in the Project space, plus the project scratch areas used by code, drafts, and exports.

**3. Check readiness.** Delegate a `map` task ([Assess your corpus](assess-your-corpus.md)) and relate the resulting claims to the active thesis with `supports` / `contradicts` links. A hub with several mutually linked claims is the tell that a cluster is dense enough to write from.

**4. Refresh the gate.** Open the project from the Project space and run `Memoria: refresh project gate`. The operation updates `project-gate-index.md` with graph maturity, saturation state, open high-impact gaps, and advisory findings.

**5. Sketch and draft.** Lay the argument out spatially ([Use canvas for argument mapping](use-canvas-for-argument-mapping.md)), delegate outline and section work to the Writer's `draft` lane ([Draft with the Writer](draft-with-writer.md)), and keep scratch attached to the project so it stays visible from the Project space.

## Verify

- `projects/<slug>/project.md` and `projects/<slug>/thesis.md` exist
- `project-gate-index.md` exists after refresh
- The Project dashboard shows the project and active thesis
- Any ungrounded drafting claim becomes a gap to resolve before export

## Related

- The synthesis layer a project stands on: [Write a claim note](../knowledge/write-a-claim-note.md) and [Build a hub](../knowledge/build-a-moc.md)
- Readiness check: [Assess your corpus](assess-your-corpus.md)
- Drafting today: [Draft with the Writer](draft-with-writer.md)


---

<!-- source: how-to-guides/project/assess-your-corpus.md -->

# Assess your corpus

Delegate a **`map`** task to get a corpus map — a structured read of what claims and sources you hold, where coverage is dense, and where the gaps are. The map is the decision point before drafting: write now, or read more first.

## Prerequisites

- At least ~5 claim notes in `notes/claims/` (fewer than that and the map is mostly gaps)
- Obsidian command palette available; the Agent Client pane is optional if you want help shaping the scope

## Steps

**1. Name the question.**

The map lane scopes against what you ask, so bring the deliverable into the question: the topic, the intended output, any framing constraints ("must cover 2020–2025", "needs to foreground equity").

**2. Delegate the map task.**

Use the direct command when the scope is clear: `Cmd/Ctrl-P` → **Memoria: map corpus**. Or, if you want help framing the pass, ask in the Agent Client pane:

> "Map my corpus on `<topic>` — what do I have good coverage on, and where is it thin? I'm aiming at `<deliverable>`."

Both routes create a **`map`** task for the Librarian's map lane, which builds the typed graph and topic clusters over the cluster MCP ([The Librarian](../../explanation/profiles/librarian.md)). The palette command prompts for an optional scope; the Co-PI route delegates the same card after helping shape the request (see [Command palette](../../reference/obsidian-command-palette.md)).

**3. Read the results from the Inbox.**

The coverage read comes back through the Inbox, with **`gap` cards** for the thin areas — each carrying the honesty body, never a verdict. Read by pattern:

- **Dense + recent cluster** — draft from it; the evidence is there and current.
- **Dense + stale cluster** — well-read a while ago; check for newer work before leaning on it.
- **Thin cluster** — mentioned but under-evidenced; read more first.
- **Gap the deliverable requires** — fill it or explicitly scope it out. A gap you neither fill nor acknowledge becomes an unsupported section later.

**4. Decide: write now or read more?**

- **Dense enough** (a hub with several mutually linked claims is the tell): proceed to sketching and drafting.
- **Gaps that matter:** use **Memoria: delegate task** → `catalog` with each accepted gap as context, or ask the Co-PI to shape the discovery request ([Find new sources](../library/find-new-sources.md)). Archive the gaps you don't buy.

**5. Record rejected directions.**

When a map or gap report shows a direction you considered and intentionally rejected, open that report and run `Memoria: record exploration trace` ([Obsidian command palette](../../reference/obsidian-command-palette.md)). Capture the rejected direction, the reason, the evidence you checked, and when it would be worth revisiting.

The trace lands beside the map under `notes/fleeting/maps/`. It is project-local memory for future you, not canonical knowledge: do not turn it into a claim or hub unless you later find positive evidence worth distilling.

Two standing Knowledge views answer the same questions continuously: **Open questions** (unconnected claims — the synthesis backlog) and **Contradictions** (open tensions).

## Verify

- The map results and gap cards arrived in the Inbox, and every gap card is resolved — turned into a discovery task or archived
- You've made an explicit "write now / read more" decision — not just noted the map and moved on
- Rejected directions that shaped the decision are captured as exploration traces next to the map/gap report

## Related

- Filling the gaps: [Find new sources](../library/find-new-sources.md)
- Next step when dense: [Use canvas for argument mapping](use-canvas-for-argument-mapping.md)
- The guided walk: [Tutorial 04: Draft a section from your claims](../../tutorials/04-draft-a-section-from-your-claims.md)
- The lane behind the map: [The Librarian](../../explanation/profiles/librarian.md)


---

<!-- source: how-to-guides/project/frame-a-project.md -->

# Frame a project

Generate competing argument structures and commit to one framing before drafting. This prevents the first outline from winning by default. Framing work runs on the Writer's **`draft`** lane (`draft-outline-argument`, `draft-score-outline` — [Hermes CLI](../../reference/hermes-cli.md#skill-names)); the choice is yours.

> This is the primary path to `projects/<slug>/chosen-framing.md` — framing from scored outlines. [Use canvas for argument mapping](use-canvas-for-argument-mapping.md) is an optional refinement that refines or replaces that file after you map the claims spatially.

> Start the project first ([Start a writing project](start-a-writing-project.md)), then frame against its active thesis and `project-gate-index.md`. Outline scoring remains advisory; the deterministic gate is the structural-impact cache.

## Prerequisites

- A corpus dense enough to write from ([Assess your corpus](assess-your-corpus.md))
- A stated research question and deliverable

## Steps

**1. Delegate competing outlines.**

Use `Cmd/Ctrl-P` → **Memoria: draft section** when you already know the outline request, or use the Agent Client pane if you want to shape the alternatives conversationally:

> "Outline the argument for `<research question>` two or three different ways — chronological, mechanism-of-action, and theory-first. Work from my claims on `<topic>`."

Both routes create a **`draft`** task for the Writer, whose write scope is `projects/` — the outline options land there, and the result resurfaces through the Inbox. The Writer composes from the vault only (its external-API policy is `blocked`); it can't pad an outline with sources you don't hold.

**2. Read each option — then let them sit.**

Don't commit immediately; the framing that still feels right after a break is usually the one. The options are competing *structures*, not drafts — judge which order of argument your claims actually support.

**3. Stress-test the leading framing with the Co-PI.**

In the Agent Client pane: "read this outline through an equity lens", "what's the strongest objection to this structure?" ([Read a paper through a lens](../library/read-through-a-lens.md) — the same move pointed at your own outline). The Co-PI is read-only; copy anything useful into your notes yourself.

**4. Choose and record the framing.**

Write `projects/<slug>/chosen-framing.md` yourself: the selected outline (edited freely) plus 2–3 sentences on why this framing beat the alternatives. An empty or one-line choice is not a framing decision.

## Verify

- 2–3 genuinely different outline options exist — not one outline with cosmetic variations
- `chosen-framing.md` carries both the outline and the rationale
- Every section of the chosen outline names claims you actually hold; anything else is a gap to fill first

## Related

- Previous step: [Assess your corpus](assess-your-corpus.md)
- Sketching the chosen framing spatially: [Use canvas for argument mapping](use-canvas-for-argument-mapping.md)
- Next step: [Draft with the Writer](draft-with-writer.md)
- The lane behind the outlines: [The Writer](../../explanation/profiles/writer.md)


---

<!-- source: how-to-guides/project/use-canvas-for-argument-mapping.md -->

# Use canvas for argument mapping

Arrange claim notes spatially in an Obsidian Canvas to find the argument structure before drafting — the cycle's *sketch* phase, engaged by judgment when the argument is tangled, not run on every section.

> This is an optional refinement of the framing produced by [Frame a project](frame-a-project.md), which is the primary path to `projects/<slug>/chosen-framing.md`. The canvas refines or replaces that file once the spatial arrangement is stable.

## When to use it

Open a canvas when you have 8–15 relevant claim notes on a topic and need to see how they fit together before writing. Below 8 notes the argument isn't ready; above 15, split into sections and do one at a time.

## Steps

**1. Create the canvas file.**

Create a `.canvas` file in your project folder, `projects/<slug>/` ([Start a writing project](start-a-writing-project.md)). Name it after the argument section: `chapter-2-receptivity-argument.canvas`.

**2. Collect the notes.**

Open the Knowledge space's Claims view and use the relevant claim names from the
hub's `members` list as the shopping list. Add those claim notes to the canvas;
include Catalog paper entities for key sources if helpful, but primarily use
claims — they already state the argument in your words.

**3. Arrange spatially.**

Group notes by sub-argument. Place claims that support the same point together; let `contradicts` pairs face each other. Draw arrows for logical flow: premise → implication → conclusion. Use text cards (no wikilink) for transitional claims that aren't in any note yet — these are gaps.

**4. Identify gaps.**

Any text card not grounded in a claim note is an unverified assertion. Before drafting, either write the claim from a source you hold, or queue the missing source (`Cmd/Ctrl-P` → **Memoria: capture source from URL**, **Memoria: delegate task** → `catalog`, or ask the Co-PI to shape the gap — [Find new sources](../library/find-new-sources.md)).

**5. Build the outline.**

Once the arrangement is stable, write the outline from the canvas groupings: each group becomes a section; the notes in a group become its evidence. Save it as (or fold it into) `projects/<slug>/chosen-framing.md` ([Frame a project](frame-a-project.md)).

**6. Draft.**

Open the canvas in a split pane and draft section by section — yourself, or by delegating sections to the `draft` lane ([Draft with the Writer](draft-with-writer.md)). Keep prose claims tied to claim notes on the canvas, never improvised — see [Draft with the Writer](draft-with-writer.md).

## Conventions

- One canvas per argument cluster or chapter section, not one per paper.
- Canvases are sketches, not knowledge — the claims are the durable units; delete or shelve the canvas when the section is done.
- Never embed a canvas in a draft note — the canvas format does not export through Pandoc ([Export a draft](export-a-draft.md)).

## Verify

- Every text card on the canvas is either grounded in a claim note or queued as a discovery task
- The outline you drafted maps one-to-one onto the canvas groupings

## Related

- Producing the framing the canvas maps: [Frame a project](frame-a-project.md)
- Drafting from the stable arrangement: [Draft with the Writer](draft-with-writer.md)
- Filling exposed gaps: [Find new sources](../library/find-new-sources.md)
- Why claim notes (not canvas cards) are the knowledge unit: [Note body structure](../../explanation/knowledge/note-body-structure.md)


---

<!-- source: how-to-guides/project/draft-with-writer.md -->

# Draft with the Writer

Delegate prose and outline work to the Writer's **`draft`** lane. Drafting is human-led — the Writer turns your chosen framing and claims into candidate prose; the argument assembly, and every edit that matters, is yours. The Writer is a background lane: you never chat with it — use the direct palette command when the request is clear, or use the Co-PI to shape an unclear handoff before it becomes a board card.

## Prerequisites

- A chosen framing and the claims it stands on ([Frame a project](frame-a-project.md))
- A `projects/<slug>/` scratch folder — the Writer's write scope is `projects/`

## Steps

**1. Delegate a section.**

Use `Cmd/Ctrl-P` → **Memoria: draft section**, or ask in the Agent Client pane if you want help shaping the handoff. Name the section, the framing, and the working set:

> "Draft the introduction for `<deliverable>` from `projects/<slug>/chosen-framing.md`, using my claims on `<topic>`. Cite citekeys in-text."

The palette command prompts for the goal or outline ref; the Co-PI route delegates via `delegate_route_task` ([Hermes CLI](../../reference/hermes-cli.md)). Both paths validate the handoff against the Writer's lane ceiling and land a card on the board (see [Command palette](../../reference/obsidian-command-palette.md)).

**2. Know what the lane can and can't do.**

The Writer writes **only** under `projects/` — claims, hubs, catalog, and inbox are denied. Its external-API policy is `blocked`: it composes from the vault, never researches, so it can't cite a source you don't hold. One `running` card at a time keeps drafts in flight bounded ([Kanban board reference](../../reference/kanban-board.md)).

**3. Pick up the result.**

The done card surfaces in the Inbox with the draft's location in `projects/<slug>/`. Open the draft and edit freely — the Writer's output is a starting point, never the deliverable.

**4. Don't draft past unsupported claims.**

If the prose asserts something with no current claim note behind it, stop: find
the source, write the claim, or cut the assertion. The Writer's search path hides
superseded claims by default; use them only when the task explicitly asks for
historical contrast. The verify lane will flag unsupported or stale claim reuse
anyway ([Verify and revise a draft](verify-and-revise.md)) — it's faster to
address now.

**5. Cite citekeys in-text.**

Keep citations in Pandoc form (`[@mamykina2010sense]`) so the export route renders the bibliography ([Export a draft](export-a-draft.md)).

**6. Iterate by new delegation, not by nagging.**

A rejected draft is not "redo it better" on the same card — delegate a corrected spec (the board archives the old card as superseded). Small fixes you just make yourself in the file.

## Verify

- The draft exists under `projects/<slug>/` and the done card is resolved
- Every substantive claim in the prose corresponds to a claim note; every citation is a citekey in your `.bib`
- `system/logs/audit.jsonl` shows the Writer's writes confined to `projects/`

## Related

- Previous step: [Frame a project](frame-a-project.md)
- Next step: [Verify and revise a draft](verify-and-revise.md)
- The spatial sketch behind the outline: [Use canvas for argument mapping](use-canvas-for-argument-mapping.md)
- The lane's posture and scope: [The Writer](../../explanation/profiles/writer.md)


---

<!-- source: how-to-guides/project/verify-and-revise.md -->

# Verify and revise a draft

Put a draft in front of the **Peer-reviewer** — the independent, adversarial `verify` lane — read the finding-first flag cards it raises, close the gaps, and loop until clean or the remaining gaps are consciously accepted. The Peer-reviewer's posture is *flag, don't fix*: the only thing it can write is Inbox cards; every edit is yours.

## Prerequisites

- A draft in `projects/<slug>/` ([Draft with the Writer](draft-with-writer.md)), or any text whose claims you want traced

## Steps

**1. Delegate or commit a verify pass.**

For project drafts under `projects/<slug>/`, committing the draft enqueues a verify-lane card automatically through the vault's `post-commit` hook. You can also request a pass with `Cmd/Ctrl-P` → **Memoria: verify draft**, or ask in the Agent Client pane if you want help shaping the check:

> "Verify `projects/<slug>/<section>.md` — check that every claim it makes is actually supported by its cited sources."

Both manual routes create a **`verify`** task. **Memoria: verify draft** defaults to the active note when it's under `projects/` and writes a local `[!verification]` preflight trace before delegating; the Co-PI route delegates the same lane card after conversational framing (see [Command palette](../../reference/obsidian-command-palette.md)). You can point the lane at anything — one claim, a hub, a whole draft. The proposer and the checker are independent by construction: the Peer-reviewer is deliberately not the agent that gathered the evidence or wrote the prose.

**2. Read the flag cards.**

Findings land in the Inbox as **`flag` cards** — finding-first, with the verdict carried as a separate `agent_recommendation` field ([Inbox card fields](../../reference/inbox-card-fields.md)). A `clean` flag closes nothing by itself; an `issues-found` flag changes nothing by itself. You act.

**3. Address each gap.**

- **A cited source doesn't say what the draft says:** revise the sentence, or soften it and acknowledge the weakness.
- **An unsupported assertion:** add the citation, write the missing claim note from a source you hold, or rewrite the line as explicitly your view.
- **A superseded claim cited:** the draft leans on a claim with `superseded_by` set — cite the successor instead (the Linter's `fama-exposure` detector hunts the same failure across the vault).
- **A missing source:** capture it first ([Capture and ingest a source](../library/capture-and-ingest.md)), or cut the placeholder.

Resolve each handled flag (`Cmd/Ctrl-P` → **Memoria: resolve inbox card**); the Inbox converges to empty.

**4. Loop.**

After revising, commit the project draft again or delegate another pass over the same file. Verify ↔ fix is a loop, not a single gate.

**5. Accept a gap without closing it** (when appropriate).

A genuine open question you're flagging *in the paper* is a limitation, not a failure — say so in the draft's text, archive the flag, and move on. The honesty body exists so you can disagree with the agent.

**6. Remember the check you never run.**

The retraction sweep runs on cron behind you and raises Inbox `alert` cards on hits ([Run a retraction sweep](../operate/run-a-retraction-sweep.md)) — but a pre-submission manual sweep is cheap insurance.

## Verify

- The latest verify pass came back `clean`, or every remaining `issues-found` flag is consciously accepted in the draft's own text
- No flag cards for this draft remain `proposed` in the Inbox
- No citation in the draft points at a superseded claim

## Related

- Previous step: [Draft with the Writer](draft-with-writer.md)
- Next step: [Export a draft](export-a-draft.md)
- The guided first pass: [Tutorial 05: Verify it holds](../../tutorials/05-verify-it-holds.md)
- The adversarial lane: [The Peer-reviewer](../../explanation/profiles/peer-reviewer.md)


---

<!-- source: how-to-guides/project/export-a-draft.md -->

# Export a draft

Run Pandoc to convert a verified draft Markdown file into a Word document, PDF, or clean Markdown for submission. Export is a terminal operation you run yourself — there is no export lane or palette command.

## Prerequisites

- Pandoc installed and on your `PATH` (`pandoc --version` returns a version)
- The draft verified — the latest verify pass clean or its gaps consciously accepted ([Verify and revise a draft](verify-and-revise.md))
- `.memoria/memoria.bib` current (your Better BibTeX auto-export target)
- A CSL style file — create `.memoria/csl/` in the vault and drop your `.csl` there (styles from the [Zotero style repository](https://www.zotero.org/styles))

## Steps

**1. Decide the final editor before exporting.**

Citations convert mostly one-way (see [Export routes and formats](../../reference/export.md)). Static Pandoc citations are frozen; live Word/LibreOffice fields stay restylable; Google Docs has no automated route at all.

**2. Export to Word (`.docx`) — the default static route.**

Run from the vault root; the draft lives in your `projects/<slug>/` scratch:

```bash
pandoc projects/<slug>/<draft>.md \
  --from markdown+smart \
  --to docx \
  --citeproc \
  --bibliography .memoria/memoria.bib \
  --csl .memoria/csl/apa.csl \
  --output projects/<slug>/exports/<output>.docx
```

**3. Export to PDF.**

Requires a LaTeX operation (`pdflatex` or `lualatex` on your `PATH`):

```bash
pandoc projects/<slug>/<draft>.md \
  --from markdown+smart \
  --to pdf \
  --pdf-operation=lualatex \
  --citeproc \
  --bibliography .memoria/memoria.bib \
  --csl .memoria/csl/apa.csl \
  --output projects/<slug>/exports/<output>.pdf
```

**4. Export to clean Markdown** (conference systems, CMS upload):

```bash
pandoc projects/<slug>/<draft>.md \
  --from markdown+smart --to gfm --citeproc \
  --bibliography .memoria/memoria.bib \
  --output projects/<slug>/exports/<output>.md
```

**5. Convert wikilinks first.**

Pandoc does not understand `[[wikilink]]` syntax. Convert any body wikilinks to plain text (or standard Markdown links) before export, or use a Pandoc Lua filter.

## Live Word citations via `zotero.lua` (optional)

The routes above produce static citations. For live, restylable Zotero fields in Word:

**Prerequisites:** Pandoc ≥ 2.16.2; Zotero running; the `zotero.lua` filter from the [Better BibTeX documentation](https://retorque.re/zotero-better-bibtex/exporting/zotero.lua).

**Do not add `--citeproc`** — `zotero.lua` handles citation conversion:

```bash
pandoc projects/<slug>/<draft>.md \
  --from markdown+smart --to docx \
  --lua-filter=/path/to/zotero.lua \
  --output projects/<slug>/exports/<output>.docx
```

Open the `.docx` in Word → Zotero tab → Refresh: citations convert to live fields and a bibliography is inserted.

**Known failures:** the `lpeg` Lua dependency often needs build tools on Windows — test on a one-citation document first; a corrupt `.docx` on first open is known behavior — rerun Pandoc; the filter does not work for LibreOffice — use the ODT route below.

## Live LibreOffice citations via ODF scan (optional)

1. Export to `.odt` without `--citeproc`.
2. Zotero: Tools → RTF/ODF Scan (add-on) → select the `.odt` → scan. Zotero rewrites it with live Reference Mark citations.
3. Open in LibreOffice — citations are live via the Zotero plugin.

## Verify

- The output file opens cleanly and the bibliography renders at the end
- All `[@citekey]` citations resolved — none appear as bare `[@...]` in the output
- The export landed where you pointed it; the draft `.md` in `projects/` remains the source of truth

## Related

- Previous step: [Verify and revise a draft](verify-and-revise.md)
- Routes, states, and failure modes: [Export routes and formats](../../reference/export.md)
- The `.bib` behind the bibliography: [Set up Zotero](../zotero/set-up-zotero.md)
- The works-cited backbone: [Bibliography](../../reference/bibliography.md)


---

<!-- source: how-to-guides/project/create-a-code-artifact.md -->

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


---

<!-- source: how-to-guides/project/supersede-a-thesis.md -->

# Supersede a thesis

Pivot a project thesis without erasing the old argument trail. Supersession marks the old thesis as replaced, creates a proposed successor, and asks you to re-check the project gate instead of pretending the graph stayed valid.

## Prerequisites

- A project already exists under `projects/<slug>/`
- The current thesis note is open in Obsidian
- You have the replacement thesis as one sentence

## Steps

**1. Open the active thesis.**

Open the project from the Project space, then open the thesis named by
`active_thesis`. The command only runs from a thesis note in the project.

**2. Run the command.**

Use `Cmd/Ctrl-P` -> `Memoria: supersede thesis` ([Obsidian command palette](../../reference/obsidian-command-palette.md)). Enter the replacement thesis as one sentence.

The command creates a new `projects/<slug>/thesis-<replacement>.md` note at `lifecycle: proposed`, sets `supersedes:` to the old thesis, sets `superseded_by:` on the old thesis, updates `project.md` so `active_thesis` points at the replacement, and raises an Inbox alert to re-confirm the argument graph.

**3. Refresh the project gate.**

Open the project from the Project space and run `Memoria: refresh project gate`. The refreshed `project-gate-index.md` recalculates impact, saturation, open risks, and on-path relations from the new active thesis.

**4. Triage the alert.**

Open the Inbox alert named for the thesis pivot. Treat it as a reminder to re-check high-impact links lazily as you keep working. Archive it only after the gate has been refreshed and any obviously stale on-path relations are corrected or captured as gaps.

## Verify

- The old thesis has `superseded_by:` pointing at the replacement
- The new thesis has `lifecycle: proposed` and `supersedes:` pointing at the old thesis
- `projects/<slug>/project.md` names the replacement in `active_thesis`
- `project-gate-index.md` was refreshed after the pivot
- The Inbox alert is resolved only after you have checked the gate

## Related

- Start point: [Start a writing project](start-a-writing-project.md)
- Gate refresh context: [Assess your corpus](assess-your-corpus.md)
- Draft verification after a pivot: [Verify and revise a draft](verify-and-revise.md)
- Thesis schema: [Document types](../../reference/document-types.md)


---

<!-- source: how-to-guides/using-obsidian/README.md -->

# Using Obsidian

Driving Memoria from inside Obsidian — the command palette, the Agent Client pane, and the dashboards. These are the day-to-day controls for the Obsidian-centred workflow; for terminal-side tasks see [Setup](../setup) and [Operate](../operate).

| Guide | What it covers |
| --- | --- |
| [Vault launch screen](use-the-vault-launch-screen.md) | Land on the welcome note, switch spaces from the rail, update research focus |
| [Navigate the dashboards](navigate-the-dashboards.md) | Which gate or supporting dashboard to open for each situation |
| [Workspaces](use-workspaces.md) | Use the saved Memoria workspace as a reset layout |
| [Agent Client pane](use-the-agent-client-pane.md) | Attach context, read responses, clear sessions |
| [Command palette](obsidian-command-palette.md) | The shipped `Memoria:` capture and per-task commands, invoking by type, assigning hotkeys |


---

<!-- source: how-to-guides/using-obsidian/use-the-vault-launch-screen.md -->

# Vault launch screen

On startup — and after a layout reset — you land on the vault-root `home.md` welcome note: a short "start here" screen that points you at capturing your first source, the three places (Library · Knowledge · Project), and asking the Co-PI. Navigation between surfaces is the left-pane rail ([ADR-81](../../adr/81-persistent-gate-dashboards.md)).

## Prerequisites

- The vault open in Obsidian

## Steps

**1. Land on the welcome note.**

On startup or a layout reset, the saved **Memoria** workspace seeds `home.md` — a welcome note. It is a "start here" screen, not a dashboard: capture your first source, meet the three places, and ask the Co-PI. To return to this clean layout at any time, use the saved Memoria workspace ([Use the reset workspace](use-workspaces.md)).

**2. Switch spaces from the rail.**

The left-pane rail (`_nav.md`) owns navigation. Under **Now** it shows the Inbox action count plus the Maintenance/Fleet health band; under **Places** it links **Library** · **Knowledge** · **Project**. Click a place to open that space in the active tab; reach the queue and Maintenance from **Now**.

**3. Act from the action row.**

Use the ribbon or command palette for capture/delegation actions: **Capture fleeting**, **Capture from Zotero**, **Capture URL**, **Delegate a task**, **Resolve card**, and **Agent Client: Open chat view**. Each dispatches the matching palette command — the visible controls are shortcuts, not a second mechanism.

**4. Drill down from the index.**

The three spaces group the day-to-day views by job: Library, Knowledge, and Project, with the Inbox queue as the triage surface. For the full dashboard roster see [Dashboards](../../reference/dashboards.md); to pick the right one for a situation, see [Navigate the dashboards](navigate-the-dashboards.md).

Keep `research-focus.md` current — the Librarian reads it at the start of every session to set discovery targets. Update it at least weekly during the Friday ritual.

## Verify

- Startup or layout reset lands on the `home.md` welcome note with the rail pinned
- The left-pane rail shows the Inbox action count and health band under **Now**, and **Library** · **Knowledge** · **Project** under **Places**
- Clicking **Capture fleeting** opens the QuickAdd capture prompt

## Related

- Why the launch screen is a plain note, not a custom app: [Home welcome note](../../explanation/obsidian/home.md)
- The persistent gate decision: [ADR-81](../../adr/81-persistent-gate-dashboards.md)
- What each dashboard shows: [explanation/dashboards/](../../explanation/dashboards)
- The reset workspace: [Obsidian workspaces](../../reference/obsidian-workspaces.md)
- Updating research focus on schedule: [Run the weekly review](../inbox/run-the-weekly-review.md)


---

<!-- source: how-to-guides/using-obsidian/use-workspaces.md -->

# Use the reset workspace

Memoria's daily navigation is the left-pane rail, not saved workspace switching.
Use the saved **Memoria** workspace manually only when you want to reset a rearranged window.
Startup loads the same workspace automatically.

## Prerequisites

- The vault open in Obsidian
- The Workspaces core plugin enabled (it ships enabled)

## Steps

**1. Switch surfaces from the left-pane rail.**

The pinned **Navigator** (`_nav.md`) owns switching. Its *Now* opens the Inbox queue and Maintenance collection; its *Places* open the three spaces:

- `spaces/inbox.md` — the queue: triage what needs the PI now
- `spaces/maintenance.md` — weekly structural debt and board state
- `spaces/library.md` — collect and organize sources
- `spaces/knowledge.md` — build and test claims
- `spaces/project.md` — steer bounded inquiry to output

**2. Reset the shell only when needed.**

If panes are disarranged, use Obsidian's command palette:
`Cmd/Ctrl-P` → **Workspaces: Manage workspaces** → load **Memoria**.

The reset layout opens `home.md` in the main pane, keeps file navigation on the left, and
keeps the Agent Client pane on the right.

## Verify

- On launch, Obsidian restores the saved **Memoria** shell with `home.md` and the pinned rail.
- The left-pane rail switches among the three spaces, the Inbox queue, and Maintenance.
- Loading the **Memoria** workspace restores the shared shell without changing the
  gate model.

## Related

- Workspace reference: [Obsidian workspaces](../../reference/obsidian-workspaces.md)
- Conversation surface: [Agent Client pane](use-the-agent-client-pane.md)
- Opening dashboards: [Navigate the dashboards](navigate-the-dashboards.md)
- The gate decision: [ADR-81](../../adr/81-persistent-gate-dashboards.md)


---

<!-- source: how-to-guides/using-obsidian/use-the-agent-client-pane.md -->

# Agent Client pane

Talk to the Co-PI from inside Obsidian without switching to a terminal. This guide covers opening the pane, attaching context, reading responses, and ending a session cleanly.

## Prerequisites

- Obsidian open with the vault
- `agent-client` plugin installed and Hermes available; the bundled config launches `hermes -p memoria-copi acp` ([Set up Hermes](../setup/set-up-hermes.md))

## One agent in the pane — by design

The pane runs exactly one agent: the **Co-PI** (`memoria-copi`) — the only profile you converse with. Use `Memoria:` commands first for known tasks; use the Co-PI when you want conversational help or an unclear handoff shaped into a board card. Why it's the sole agent is explained in [The Agent Client pane](../../explanation/obsidian/agent-client-pane.md). The Co-PI's lane can write nothing, so a pane conversation can never damage the vault — ask freely.

## Opening the pane

The saved **Memoria** reset workspace keeps the pane in the right sidebar, so restoring
the shell brings the Co-PI back beside the active space ([Workspaces](use-workspaces.md)).
Space switching does not reset the chat session because spaces are notes, not workspace
layout swaps. To open it manually: `Cmd/Ctrl+P` -> **Agent Client: Open chat view** or
the Hermes icon in the left ribbon.

## Attaching a note as context

**Auto-mention (default).** With `autoMentionActiveNote` on, the note open in your editor is sent as a reference when you open the pane or send a message. Open the note you want to discuss first, then open the pane (or just type, if the pane is already open). When the question is about that note, the Co-PI reads it with its vault read tools before answering.

**Via the pane directly:**
Click the paperclip icon at the top of the Agent Client pane → select a file from the picker. Use this when the note you want to discuss isn't the one currently open in the editor.

Explicitly attached notes and selected text are sent as bounded context, capped by the plugin's note/selection length limits. The Co-PI does not follow wikilinks to other notes — attach additional files explicitly if you need them in context.

## Reading responses

Two kinds of turn come back:

- **Conversation** — questions, observations, gentle pushback on the attached note. You are expected to reply. The Co-PI will not produce a finished note: when you've arrived at a durable claim, write the claim note yourself (`Memoria: write claim note`).
- **Delegation receipts** — when a conversation becomes lane work, the Co-PI raises a card on the right lane and tells you so. Known tasks should start from the matching `Memoria:` command; this route is for shaping unclear requests. Track delegated work on the board (`hermes kanban list`, or the Board State dashboard); the result lands in your Inbox, not in the pane.

## Ending a session

Leave the pane open during a reading session — sustained questioning across the notes of one topic is its purpose. Press **Clear** at the top of the pane when you finish a paper or topic cluster, before switching to unrelated work. Long histories degrade response quality.

## Exporting a session

Sessions are captured automatically: with the shipped config, opening and closing a chat exports the conversation as a markdown file to `system/exports/` (filenames start with `chat_`). You can also export mid-session via `Cmd/Ctrl+P` → **Agent Client: Export chat**.

Exports are visible raw material for PI review. They are not canonical notes and they do not enter Inbox or fleeting triage automatically. When a conversation contains something durable, promote the insight yourself from the appropriate space: create a fleeting note, claim note, source note annotation, or project scratch entry with the matching command or visible Base view.

Three folders to **never** point `exportSettings.defaultFolder` at:

- `.memoria/` — hidden runtime internals, not a PI-facing review surface.
- `inbox/` — reserved for agent-raised honesty cards (candidates, gaps, flags, alerts), not chat transcripts.
- `projects/` — active project work belongs here, not chat transcripts.

Auto-export is enabled for both new-chat and close-chat events (`autoExportOnNewChat: true`, `autoExportOnCloseChat: true`) so a pane session has a visible transcript even if Obsidian closes unexpectedly.

## If the pane won't connect

On production Windows, Obsidian and Hermes both run natively. The shipped Agent
Client config should use:

- **WSL mode off.** `windowsWslMode: false`.
- **Command = `hermes`** when the native Hermes installer has placed Hermes on
  your User PATH. If Obsidian was already open during install, fully restart it
  so it sees the updated PATH.

For the Linux/WSL test path where Obsidian runs on Windows and Hermes runs
inside WSL, turn `windowsWslMode` on and point the command at the WSL absolute
Hermes path, for example `/home/<you>/.local/bin/hermes`. That is a test-path
exception, not the production Windows default.

## Verify

- The pane runs one agent — **Co-PI** — and connects
- Opening the pane with a note active passes that note as a readable reference
- Asking for lane work ("verify this draft") produces a card on the board, not prose-only
- Pressing **Clear** empties the pane and resets the session

## Related

- Discussing a paper end-to-end: [Discuss a paper](../library/discuss-a-paper.md)
- Gate/reset layout: [Obsidian workspaces](../../reference/obsidian-workspaces.md)
- Plugin settings and `customAgents` keys: [Obsidian plugins](../../reference/obsidian-plugins.md)
- Why one conversational agent: [The Agent Client pane](../../explanation/obsidian/agent-client-pane.md)


---

<!-- source: how-to-guides/using-obsidian/obsidian-command-palette.md -->

# Command palette

The command palette is Obsidian's keyboard launcher for actions. In Memoria it's how you capture notes and hand work to agents without leaving the editor — no buttons to hunt for, no terminal.

Open it with `Cmd-P` (`Ctrl-P` on Windows), then type `Memoria:` to filter to Memoria's commands. Every Memoria action reads `Memoria: <action>`.

The palette is for **actions**, not navigation. To switch between spaces — the rooms you work in, like Library or Knowledge — use the navigator rail (the **Now** / **Places** strip in the left pane), not the palette.

This guide covers the commands that ship pre-wired and how to make them fast.

## Prerequisites

- Obsidian open with the vault
- QuickAdd and Commander ship bundled and enabled with the starter vault — no install needed (see [Set up Obsidian](../setup/set-up-obsidian.md))
- The Memoria command catalog open for reference: [Obsidian command palette](../../reference/obsidian-command-palette.md)

## Steps

**1. Open the palette and confirm the pre-wired commands are present.**

`Cmd-P` (or `Ctrl-P`) → type `Memoria:`. The commands ship pre-wired in the starter vault, in four groups. The full catalog is in [Obsidian command palette](../../reference/obsidian-command-palette.md).

First, a few terms used below:

- **Lane** — a kind of background work an agent does (catalog, extract, draft, verify). Lanes run on the **kanban board**, a column-per-lane task tracker.
- **Card** — a tracked work item: a board card is a task on a lane; an **Inbox** card is something waiting for your attention. The Inbox is a **queue** — a list you work down to empty.
- **Citekey** — a paper's short citation id, e.g. `smith2024`.

**Capture and note creation** — entry points that must fire from inside the editor:

- `Memoria: capture fleeting` — a quick-note form; writes one raw item to `notes/fleeting/`
- `Memoria: write claim note` — a guided form; writes a claim note in `notes/claims/` (only you create these)
- `Memoria: capture source from URL` — turns a pasted URL into a capture card on the Librarian lane
- `Memoria: structured source capture` — a guided form; writes a proposed source note plus an Inbox candidate card
- `Memoria: capture from Zotero selection` — the same capture card, citekey pre-filled from the current Zotero selection
- `Memoria: resolve inbox card` — marks the active Inbox card resolved, in place

**Per-task lane commands** ([#203](https://github.com/eranroseman/memoria-vault/issues/203)) — one command per lane task. Each prompts only for what that task needs, then raises a board card on the right lane:

- `Memoria: catalog source` · `Memoria: extract claims` · `Memoria: link claim` · `Memoria: map corpus` — the Librarian's four tasks
- `Memoria: draft section` — the Writer's `draft` lane
- `Memoria: verify draft` — the Peer-reviewer's `verify` lane
- `Memoria: run pattern` — pick a runnable pattern from `system/patterns/`; the active note rides along
- `Memoria: delegate task` — the generic fallback: pick any lane (including `code`) and type a free-form goal

**Assist commands** — verb-shaped starts, from the palette, a pane conversation, or selected text:

- `Memoria: assist find` · `Memoria: assist search` · `Memoria: assist patterns`
- `Memoria: assist ask` · `Memoria: assist draft` · `Memoria: assist explore`

From the palette or a selection, assist commands stage a card or draft for review. They never write directly to your canonical notes.

**Project commands** — maintenance for a writing project:

- `Memoria: start project` — scaffold `projects/<slug>/` with the project note, first thesis, and gate surface (a **gate** is the human approval step before work advances)
- `Memoria: refresh project gate` — recalculate `project-gate-index.md` from the active project's state
- `Memoria: supersede thesis` — create a replacement thesis, mark the old one superseded, and raise a re-confirmation alert

Task commands default to the **active note** — the file open in your editor. `extract claims` runs on an open paper or source note, `link claim` on an open claim, `verify draft` on an open project file. Assist commands also carry the active note and any selected text as context.

**2. Use the visible buttons for the main loop.**

You don't have to type every command. The most frequent ones also appear as buttons.

The left ribbon holds: capture fleeting, capture from Zotero selection, capture source from URL, delegate task, and resolve inbox card.

The note page header holds: capture fleeting, create linked claim note, write claim note, extract claims, and link claim — so capture stays close while the active-note defaults stay visible.

Navigation lives elsewhere: switch spaces and open the Inbox queue from the navigator rail (**Now** / **Places**) in the left pane, not from the palette.

**3. Reach for the Co-PI when the command isn't obvious.**

The **Co-PI** is the one agent you can chat with, in the Agent Client pane ([Agent Client pane](use-the-agent-client-pane.md)). It complements the palette; it doesn't replace it.

- **Know the lane, task, or assist verb?** Use the palette — it's faster.
- **Not sure which command, or the work spans several tasks?** Ask the Co-PI.
- **Want Ask or Explore to stay a conversation?** Stay in the pane.

When a conversation should produce real work, the Co-PI raises a card on the right lane for you. (It checks the request against that lane's write limits first, so it can't overstep.)

Two things to know:

- **Linting has no command.** The Linter runs on a daily schedule and on each commit, not from the palette ([Run the Linter](../operate/run-the-linter.md)).
- **Starting a project does** — use `Memoria: start project`.

**4. Filter by typing, don't scroll.**

`Cmd-P` → type `Memoria:` → the palette shows Memoria's commands only. Type a few more letters to narrow (e.g. `Memoria: ext` for `extract claims`). Filtering is fast enough that most commands never need a hotkey.

**5. Assign a physical hotkey to any command you invoke more than ten times a day** (optional).

Settings → Hotkeys → search for the command name → assign a key combination. Reserve physical hotkeys for the genuinely highest-frequency commands only — `Memoria: capture fleeting` is the usual candidate.

## Verify

- `Cmd-P` → type `Memoria:` returns the commands in the capture, task, assist, and project groups
- The left ribbon exposes capture, delegate, and resolve controls; the navigator rail (**Now** / **Places**) handles space switching
- `Memoria: capture fleeting` creates a new note in `notes/fleeting/` with `lifecycle: proposed` and `origin: human`, then surfaces it in the Inbox **Fleeting notes** queue
- `Memoria: structured source capture` creates a proposed `notes/sources/` note and an Inbox `candidate` card
- `Memoria: write claim note` opens the guided claim form and creates a titled claim note in `notes/claims/` — Properties populated, clean body, no template scaffolding
- A task command (e.g. `Memoria: map corpus`) lands a card on the board: `hermes kanban list` shows it addressed to the right lane

## Related

- Full command catalog: [Obsidian command palette](../../reference/obsidian-command-palette.md)
- The conversational route: [Agent Client pane](use-the-agent-client-pane.md)
- QuickAdd and the rest of the plugin set: [Obsidian plugins](../../reference/obsidian-plugins.md)


---

<!-- source: how-to-guides/using-obsidian/navigate-the-dashboards.md -->

# Navigate the dashboards

Memoria has a few different surfaces, and it is easy to lose track of which one answers which question. This guide maps everyday situations to the exact place to look.

You move around Memoria from the **navigator rail** on the left. It has two parts:

- **Now** — what is waiting for you right now. Three entries: **Needs you** (your action queue), **Drift** (integrity flags), and **Fleet** (the health of the background workers).
- **Places** — the three working **spaces** you switch between: **Library** (sources you are reading), **Knowledge** (claims you are synthesizing), and **Project** (drafts you are steering toward output).

Two more surfaces hang off *Now*. The **Inbox** is your action queue — open it from *Now → Needs you*; its main view is **Needs me**. **Maintenance** is a separate weekly surface for structural cleanup; it holds Drift watch, Loose ends, the Board, and a "new this week" digest.

Behind those surfaces sit **5 read-only system dashboards** under `system/dashboards/`. They are Dataview-backed views that report state and never change anything. The space surfaces themselves are built from Obsidian Bases (database-style views over your notes). For the full roster and what each one shows, see [Dashboards](../../reference/dashboards.md).

A few orientation notes: startup restores the saved **Memoria** shell, but you still navigate through the left rail, not by switching saved workspaces; see [Use the reset workspace](use-workspaces.md). `home.md` is a launch screen, not a navigation hub, so do not treat it as your home base.

To open anything that is not on the rail, follow a link from a space, or press `Cmd/Ctrl-P` → Omnisearch → the dashboard name.

---

## Situation → where to look

### "What needs attention right now?"

Open the **Inbox** (`spaces/inbox.md`) from *Now → Needs you*.

The Inbox is your action queue: items that Memoria has parked for a decision from you. Glance at it at the start of every session. Empty means nothing is waiting; a full read takes under 30 seconds.

### "What work is in flight? What's stuck?"

Open **Maintenance** from *Now*, then read its **Board** section.

The Board shows the background workers — Memoria calls them **lanes** — and the work moving through them as **cards** (one card per unit of work). A card that has sat in the same lane for days is probably stuck: [Fix a stuck card](../troubleshooting/fix-stuck-card.md).

### "What should I read and distill next?"

Open the **Library** space (`spaces/library.md`) from *Places*.

Library is where sources you are reading live. It lists items oldest-first, so clear the oldest ones first. See [Classify a source](../library/classify-a-source.md).

### "Which papers are worth a discussion pass?"

Open the **Library** space, then its **Discuss queue** view.

This queue lists papers ready for a back-and-forth with the conversational agent (the **Co-PI**). Open a paper from the queue, then open the Agent Client pane — the active note attaches itself automatically. See [Discuss a paper](../library/discuss-a-paper.md).

### "What open questions has my synthesis raised?"

Open the **Knowledge** space, then its **Open questions** view.

Knowledge is where your **claims** live — the individual statements you are building an argument from. A **hub** is a topic note that gathers related claims in one place. Review Open questions during the weekly review, or when starting a new topic cluster, and connect each loose claim either to a hub or to related claims.

### "Are any of my claims contradicted by other claims?"

Open the **Knowledge** space, then its **Contradictions** view.

This view lists pairs of claims that disagree with each other. Check it before you promote a claim to `evergreen` (the most settled maturity level) or submit a draft. An unresolved contradiction means the argument is not settled yet.

### "Is this project ready to draft?"

Open the **Project** space (`spaces/project.md`) from *Places*.

Project steers a piece of work toward output. Refresh it from a project file, then read the project's readiness signals: the active thesis, the **refutation stamp** (a record of whether the thesis survived being argued against), how mature the claim graph is, the **saturation** state (whether new sources are still adding anything, or you have read enough), and any remaining gap findings.

### "Something seems wrong but I can't see why"

Open **Maintenance** from *Now*, then read its **Drift watch** view. You can also reach drift flags directly from *Now → Drift*.

Drift watch flags integrity problems — the kind of thing that makes agents behave oddly or queries return wrong results. It shows a `PASS` / `REVIEW` / `FAIL` band. A `FAIL` pauses scheduled work until you resolve it ([Run the Linter](../operate/run-the-linter.md)).

### "Are my workers performing well? Is API cost increasing?"

Open **Fleet health** (`system/dashboards/fleet-health.md`), reachable from *Now → Fleet*.

This dashboard scores each lane (background worker) on trust and cost. Check it monthly, or when a lane seems slow or degraded. It is not a daily surface — the numbers only mean something after a week or more of accumulated data.

### "What did the policy MCP allow or deny?"

Open the **Audit log** (`system/dashboards/audit-log.md`) manually.

This dashboard lists recent writes and whether the policy layer allowed or denied each one. Open it when a write did not happen as you expected ([Diagnose a denied or blocked write](../troubleshooting/diagnose-a-denied-write.md)), or after changing a lane's policy override to confirm the new rule behaves as intended.

### "What do I need to do this week?"

Open **Maintenance** from *Now* on Fridays for the weekly review.

Maintenance gathers the week's structural cleanup in one place. The [Run the weekly review](../inbox/run-the-weekly-review.md) guide walks through it step by step.

### "What low-stakes structural debt has piled up?"

Open **Maintenance** from *Now*, then read its **Loose ends** view.

Loose ends collects small structural tidy-ups that are safe to defer. More than five items waiting is a signal to do a cleanup pass.

## Related

- Weekly review procedure: [Run the weekly review](../inbox/run-the-weekly-review.md)
- Workspace layouts: [Obsidian workspaces](../../reference/obsidian-workspaces.md)
- The dashboard inventory and the Bases views behind it: [Dashboards](../../reference/dashboards.md)


---

<!-- source: how-to-guides/hermes-agent/README.md -->

# Hermes Agent

Operational guides for the Hermes CLI — profile configuration and interactive chat sessions.

| Guide                                       | What it covers                                        |
| ------------------------------------------- | ----------------------------------------------------- |
| [Configure a profile](configuration.md)     | Model routing, write permissions, skills, API keys    |
| [Run a CLI chat session](chat-with-hermes.md) | Start a session, run skill commands, use dry-run mode |

First-time install configures the profiles for you — see [Set up Hermes](../setup/set-up-hermes.md). **Configure a profile** is for *editing* a profile afterward (changing model routing, skills, or keys).

Administrative CLI commands (profile list/install, kanban management, skills, cron) are reference material: [Hermes CLI](../../reference/hermes-cli.md).


---

<!-- source: how-to-guides/hermes-agent/configuration.md -->

# Configure a profile

A **profile** is the per-worker configuration for one Hermes worker. Editing a profile changes how that worker behaves: which model it routes to, what it is allowed to write, and which API credentials it uses. Each background worker on the kanban board is a **lane**; the conversational agent you talk to is the **Co-PI**.

This page collects the common configuration tasks. Each section is a self-contained procedure: change the model overlay, change auxiliary models, change write permissions, add or remove a skill, update API credentials, and verify your change.

Memoria ships five profiles: `memoria-copi`, `memoria-librarian`, `memoria-writer`, `memoria-peer-reviewer`, and `memoria-engineer`. For what each one can do, see [Profile capabilities](../../reference/profiles.md).

> **Don't hand-edit tool allowlists.** To change which tools a profile can use, edit `src/.memoria/tool-registry.yaml` and run `scripts/render_profile_configs.py --write`. Do not hand-edit the generated `platform_toolsets` block (the rendered list of built-in tool groups) or the MCP `tools.include` blocks — they are regenerated from the registry.

## Where profile files live

Each profile exists in two places. Edit the first; the installer copies it to the second.

| Location | Purpose |
| --- | --- |
| `<vault>/.memoria/profiles/memoria-<name>/` | **Vault source** — version-controlled, authoritative |
| `~/.hermes/profiles/memoria-<name>/` | **Deployed copy** — what Hermes actually runs |

Always edit the vault source, then re-deploy to push your changes to the deployed copy:

```bash
bash scripts/install.sh --profiles-only --vault <vault>
```

Never edit the deployed copy directly. The next install overwrites it.

## File roles

These are the files inside a profile directory and what each one controls.

| File | Controls | Who edits |
| --- | --- | --- |
| `SOUL.md` | Profile identity, posture, behavioral constraints | Author (you) |
| `config.yaml` | Model routing, `mcp_servers`, generated capability blocks, and the `plugins` block enabling the `memoria-policy-gate` write gate | Author plus `scripts/render_profile_configs.py` (installer substitutes Python, vault, qmd, and model tokens) |
| `distribution.yaml` | Packages the profile for `hermes profile install` | Author |
| `skills/` | Skill packages the profile can load | Author |
| `.env` (deployed copy only) | API keys and secrets | **Human only** — never committed to git |

One piece of configuration lives *outside* the profile directory: the **lane ceiling**, the maximum write scope a lane is allowed. It sits at `<vault>/.memoria/lane-overrides/<name>.yaml`. See [Change write permissions](#change-write-permissions-lane-overrides) below.

## Change the model overlay

The **model overlay** is the `model:` block in a profile's `config.yaml` — it sets which model the profile's main work routes to. The shipped `config.yaml` files use placeholders that the installer fills in, so a production vault and a disposable test vault can use different model providers without hand-editing all five profiles.

**Production (the default).** Profiles render to the kilocode gateway:

```yaml
model:
  provider: kilocode
  base_url: https://api.kilo.ai/api/gateway
  default: ~anthropic/claude-<tier>-latest
```

**Test (Linux/WSL).** Render every profile to a local Ollama endpoint by setting `MEMORIA_ENV=test` when you install:

```bash
MEMORIA_ENV=test bash scripts/install.sh --profiles-only --vault ~/Memoria-test
```

That renders:

```yaml
model:
  provider: custom
  base_url: http://127.0.0.1:11434/v1
  default: qwen2.5:7b
  context_length: 65536
  ollama_num_ctx: 65536
```

To point the test install at a different local endpoint or model, set `MEMORIA_MODEL_BASE_URL`, `MEMORIA_MODEL_NAME`, and `MEMORIA_MODEL_CONTEXT_LENGTH`.

To change the production tier permanently, update the installer's profile model overlay and the profile tests together, then re-deploy:

```bash
bash scripts/install.sh --profiles-only --vault <vault>
```

> **The main-model key is `default`, not `name`.** That is the key the installer renders for the profile's main model.

> **Profiles override whole sections, they don't merge into them.** Each shipped profile sets only the `model`, `mcp_servers`, and `plugins` blocks. Everything else is inherited from the global `~/.hermes/config.yaml`. Hermes replaces a config section wholesale rather than deep-merging, so whatever block you put in a profile fully replaces the global one of the same name — it does not add to it.

## Change auxiliary models (set globally, not per-profile)

**Auxiliary slots** are the small, high-frequency bookkeeping calls Hermes makes around the main work: title generation, context compression, command approval, MCP routing, and skills-hub search. Each slot defaults to `provider: auto`, which reuses the profile's main model. That is wasteful, because it routes these frequent calls through an expensive main model such as Opus. Route them to cheap models instead.

**Set auxiliary models once, in the global config — not in a profile.** A profile replaces a whole config section rather than merging into it, so a per-profile `auxiliary:` block would replace (and so lose) the rest of the global one. Edit `~/.hermes/config.yaml`:

```yaml
auxiliary:
  title_generation: { provider: kilocode, model: z-ai/glm-4.7-flash }            # cheapest input
  approval:         { provider: kilocode, model: z-ai/glm-4.7-flash }
  mcp:              { provider: kilocode, model: z-ai/glm-4.7-flash }
  skills_hub:       { provider: kilocode, model: z-ai/glm-4.7-flash }
  compression:      { provider: kilocode, model: deepseek/deepseek-v4-flash }     # 1M ctx — must hold the main model's window
  # vision / web_extract: a cheap multimodal (e.g. google/gemini-2.5-flash) only if you use image/page analysis
```

Then restart Hermes to pick up the global config change.

> **`compression` needs a large context window.** It must hold at least the main model's full window. That is why the example uses DeepSeek's 1M-token context; GLM's 202K is too tight.

To find valid kilocode model ids, request `GET https://api.kilo.ai/api/gateway/models` (no auth required).

## Change write permissions (lane overrides)

A **lane override** is the write ceiling for one profile — the widest set of paths that profile is ever allowed to write. The **policy MCP** (an MCP server is a process that exposes tools and rules to Hermes; this one enforces write policy) reads and enforces these ceilings. Lane overrides live at `<vault>/.memoria/lane-overrides/<name>.yaml`, where `<name>` is one of `copi`, `librarian`, `writer`, `peer-reviewer`, or `engineer`. They sit outside the profile directory.

**To change a profile's write scope:**

1. Edit the profile's lane-override file: `<vault>/.memoria/lane-overrides/<name>.yaml`. The full file shape (`policy.allow`/`deny`, `require`, `routing`) and the decision protocol are in [Policy MCP](../../reference/policy-mcp.md).
2. Re-deploy. The installer picks up lane-override changes on every run:

   ```bash
   bash scripts/install.sh --profiles-only --vault <vault>
   ```

> **The lane is a ceiling, not the exact scope.** A board card's `allowed_paths` may *narrow* a lane's scope for that one task but never widen it. Think of the lane as the ceiling and the card's payload as the floor.

> **You do not declare review-gating per lane.** Writes to the gated path prefixes — `notes/claims/` and `notes/hubs/`, declared in `.memoria/schemas/folders.yaml` — automatically degrade to `dry_run` at the human approval gate. There is nothing to add to the lane file for this.

## Add or remove a skill

A **skill** is a packaged capability a profile can load, stored as one directory per skill under `<vault>/.memoria/profiles/memoria-<name>/skills/`. Examples: the Librarian's `catalog-enrich-record` and `map-cluster-corpus`, and the Peer-reviewer's `verify-check-citation`.

**To add a skill:**

1. Copy the skill package into the profile's `skills/` directory.
2. Re-deploy: `bash scripts/install.sh --profiles-only --vault <vault>`.

**To remove a skill:**

1. Delete the skill's directory.
2. Re-deploy: `bash scripts/install.sh --profiles-only --vault <vault>`.

> **A skill does not grant its own tools.** `<vault>/.memoria/tool-registry.yaml` is the authoritative per-profile tool allowlist, and it is default-deny (tools are denied unless explicitly listed). If a skill needs a tool the registry withholds from that profile, copying the skill in will not give it that tool — change the registry. See the note at the top of this page.

## Update API credentials

At runtime, each profile reads only its own deployed `.env` file. But you should never edit those per-profile files by hand — the installer manages them, and hand-edits drift from the shared source. Instead, edit the one shared Hermes env file and let `--profiles-only` copy the keys into each profile.

**To update credentials (macOS/Linux):**

1. Edit `~/.hermes/.env`.
2. Re-deploy:

   ```bash
   bash scripts/install.sh --profiles-only --vault <vault>
   ```

**To update credentials (Windows):**

1. Edit `%LOCALAPPDATA%\hermes\.env`.
2. Re-deploy:

   ```powershell
   .\scripts\install.ps1 -ProfilesOnly -Vault <vault>
   ```

For how `--profiles-only` seeds each profile's `.env` from the shared file, see [Redeploy profiles](../operate/redeploy-profiles.md).

## Verify a configuration change

After re-deploying, confirm the deployed profile reflects your vault source changes.

**For any profile change**, show the deployed profile:

```bash
hermes profile show memoria-<name>
```

This reports the deployed `SOUL.md`, MCP servers, skills, and `.env` key names (with values redacted).

**For a lane-override change**, you have two ways to confirm the new policy is enforced:

- Run a write operation, then check the audit log `system/logs/audit.jsonl` to see how the policy was applied.
- Or test a single decision without running a real write:

  ```bash
  python3 .memoria/mcp/policy_mcp.py --vault <vault> \
    --decide '{"profile":"memoria-librarian","action":"write","path":"notes/claims/x.md","task_id":"T1"}'
  ```

## Related

- Deploy vault source to profiles: [Redeploy profiles](../operate/redeploy-profiles.md)
- Fix profile drift (deployed ≠ source): [Fix profile drift](../troubleshooting/fix-profile-drift.md)
- Lane-override reference: [Policy MCP](../../reference/policy-mcp.md)
- The five profiles and their ceilings: [Profile capabilities](../../reference/profiles.md)


---

<!-- source: how-to-guides/hermes-agent/chat-with-hermes.md -->

# Run a CLI chat session

Start a terminal session with a Memoria profile — the Co-PI without Obsidian, or a background lane for debugging. (This is the `hermes … chat` CLI — not the in-Obsidian Agent Client pane, which speaks ACP to the same profiles.)

Reach for a CLI chat session when Obsidian isn't running, when debugging a lane profile directly outside board dispatch, or to verify a redeployed profile loads its MCP servers and skills. For normal task dispatch, use the Obsidian command palette first; the [Agent Client pane](../using-obsidian/use-the-agent-client-pane.md) is for conversation and handoff shaping. Note that lint and the retraction sweep are now **operations**, not chat sessions ([Run the Linter](../operate/run-the-linter.md), [Run a retraction sweep](../operate/run-a-retraction-sweep.md)).

```bash
hermes -p <profile-alias> chat
```

- `-p <profile-alias>` — which profile to invoke (a **global** Hermes flag, so it also works with other subcommands, e.g. `hermes -p memoria-copi acp` for the pane's stdio server)

The five aliases: `memoria-copi`, `memoria-librarian`, `memoria-writer`, `memoria-peer-reviewer`, `memoria-engineer`.

## Common session starters

| Goal | Command |
| --- | --- |
| Talk to the Co-PI from the terminal | `hermes -p memoria-copi chat` |
| Shape a task when Obsidian is unavailable | `hermes -p memoria-copi chat`, then e.g. "help me frame a verify request for projects/jitai/draft.md" |
| Debug the ingest path | `hermes -p memoria-librarian chat`, then ask it to dry-run `catalog-find-source` on a citekey |
| Debug the verify checks | `hermes -p memoria-peer-reviewer chat`, then ask for a `verify-trace-claim` pass on a claim note |

The Co-PI is the only profile designed for conversation — it reads the vault, answers, and delegates writes as board cards via `delegate_route_task`. The dispatched lanes normally run from the Kanban board, so a direct chat with them is a debugging posture, not a workflow.

Type `exit` or Ctrl-C to end a session cleanly.

## Chatting safely

No special flag is needed — the policy gate enforces it ([Policy MCP](../../reference/policy-mcp.md)): the Co-PI's lane denies every path, and any lane write to a review-gated prefix degrades to `dry_run` and lands in the review queue ([Work the review queue](../inbox/work-the-review-queue.md)). To test a single permission decision without any agent, use the policy MCP's `--decide` one-shot mode ([Configure a profile § Verify a configuration change](configuration.md#verify-a-configuration-change)).

## Watching what a session did

- `system/logs/audit.jsonl` — every gated action the session attempted
- `system/logs/sessions/` — per-session digests the Linter writes from the audit log
- `hermes kanban list` — cards a Co-PI session delegated to the board

## Related

- Profile configuration: [Configure a profile](configuration.md)
- The pane that replaces most CLI chats: [Agent Client pane](../using-obsidian/use-the-agent-client-pane.md)
- Ingest: [Capture and ingest a source](../library/capture-and-ingest.md)
- Administrative CLI commands (profile, kanban, skills, cron): [Hermes CLI](../../reference/hermes-cli.md)


---

<!-- source: how-to-guides/operate/README.md -->

# Operate

Terminal-side system upkeep — operational checks and maintenance tasks run from the command line or scheduler.

| Guide | What it covers |
| --- | --- |
| [Run the Linter](run-the-linter.md) | On-demand or scheduled structural health check |
| [Run a retraction sweep](run-a-retraction-sweep.md) | Check ingested papers against retraction registries; update affected claims |
| [Run a schema migration](run-a-schema-migration.md) | Rewrite a frontmatter field across many notes, dry-run first |
| [Redeploy profiles](redeploy-profiles.md) | Push vault source edits out to `~/.hermes/profiles/` |
| [Rebuild the search index](rebuild-the-search-index.md) | Re-run `qmd embed` when Writer search returns stale results |
| [Run the vault eval](run-the-vault-eval.md) | Dispatch and score the gold-set evaluation on demand |
| [Inspect session logs](inspect-session-logs.md) | Read the audit and per-session logs ad-hoc — filter by lane, date, or decision |


---

<!-- source: how-to-guides/operate/run-the-linter.md -->

# Run the Linter

Run a structural health check on the vault, or review the scheduled report. The Linter is an **operation, not an agent** — deterministic, zero-LLM Python under `.memoria/operations/integrity/linter/`, report-only by design: findings surface for you to act on; nothing is auto-moved or auto-archived ([Linter: detectors and auto-fix](../../reference/linter.md)).

## When it runs without you

- **Daily cron** — the installer wires `memoria-lint` at 06:00: the detectors plus a golden-copy drift check. Findings feed Maintenance's Drift watch and Loose ends views.
- **Pre-commit hook** — every staged `.md` is schema-validated; an invalid typed document blocks the commit.

Run it by hand after a large batch ingest, after structural edits, or when a Dataview query returns something unexpected.

## Steps

**1. Run the detectors.**

From the vault root:

```bash
python3 .memoria/operations/integrity/linter/detectors.py --vault .
```

Add `--json` for machine-readable output. The detectors cover schema validity, broken frontmatter and body wikilinks, misplaced typed documents, dashboard field drift, superseded-claim reuse (`fama-exposure`), broken extract paths, orphan synthesis notes, leftover working files, and stale fleeting notes.

**2. Read the report by severity.**

| Severity | Meaning | Action |
| --- | --- | --- |
| CRITICAL | Vault integrity at risk | Fix immediately — the verdict rolls to FAIL and scheduled work pauses |
| HIGH | Silent or active breakage | Fix this session |
| MEDIUM | Real drift, will compound | Address in the weekly review |
| LOW | Cosmetic or easily recovered | Defer or accept |

The verdict band rolls up as **PASS** (LOW only or clean) / **REVIEW** (any MEDIUM or HIGH) / **FAIL** (any CRITICAL) — the same band Maintenance's Drift watch shows.

**3. Check golden-copy drift.**

```bash
python3 .memoria/operations/integrity/linter/golden_restore.py --vault . check
```

Reports any system file (templates, dashboards, patterns, eval tasks, scripts, `home.md`, `system/vocabulary.md`, `AGENTS.md`) that drifted from the installer-staged golden copy. To repair:

```bash
python3 .memoria/operations/integrity/linter/golden_restore.py --vault . restore          # propose-only: lists what it would restore
python3 .memoria/operations/integrity/linter/golden_restore.py --vault . restore --apply  # write the golden bytes back, deliberately
```

**4. Fix findings by hand.**

Every detector is report-only — fixes are yours, in Obsidian or the editor. The most common ones have dedicated recovery guides (see Related). Commit when done; the pre-commit hook re-validates what you staged.

**5. Confirm the cron is alive** (occasionally):

```bash
hermes cron list        # memoria-lint should show with a next-run time
hermes cron run memoria-lint   # force a pass now
```

## Verify

- A re-run reports no CRITICAL or HIGH findings
- `golden_restore.py check` exits clean
- Maintenance's Drift watch and Loose ends views show the improvement after the next cron pass

## Related

- Weekly review (the structural-health step): [Run the weekly review](../inbox/run-the-weekly-review.md)
- Fix broken frontmatter: [Fix broken frontmatter](../troubleshooting/fix-broken-frontmatter.md)
- The detector inventory and gate flags: [Linter: detectors and auto-fix](../../reference/linter.md)
- Where findings surface: [Dashboards](../../reference/dashboards.md)


---

<!-- source: how-to-guides/operate/run-a-retraction-sweep.md -->

# Run a retraction sweep

Check the papers in your Catalog against retraction registries and act on the hits. The sweep is part of the **sweeps operation** — deterministic, read-only Python at `.memoria/operations/integrity/retraction/retraction.py`; flag-don't-fix: it raises Inbox **`alert`** cards and never flips a note.

## When it runs without you

The installer ships a monthly cron wrapper (`retraction-refresh-cron.sh`) that refreshes the local Retraction Watch dataset and sweeps. Run it by hand before citing a cluster of older papers in a draft, or right after hearing of a retraction in your field.

## Steps

**1. Refresh the local dataset** (skippable if the monthly cron just ran):

```bash
python3 .memoria/operations/integrity/retraction/retraction.py --refresh
```

Downloads the Retraction Watch CSV to `.memoria/data/retraction_watch.csv`.

**2. Run the sweep.**

```bash
python3 .memoria/operations/integrity/retraction/retraction.py --sweep --vault .
```

The sweep scans the Catalog's DOIs against three sources, most authoritative first: the local Retraction Watch index, the live Crossref `update-to` delta, and Open Retractions as a cross-check. Each hit raises one finding-first **`alert`** card in `inbox/`.

**3. Read the alert cards.**

Each card leads with the `finding` — what was retracted (or corrected, or flagged with an expression of concern) and which citekey. Open the paper entity and the claims that cite it (backlinks panel, or search the citekey across `notes/claims/`).

**4. Decide per affected claim.** Three honest options:

- **Soften** — rewrite to hedge: "X was suggested by [author], though the paper was subsequently retracted."
- **Supersede** — find a cleaner source, write a new claim on it, set `superseded_by` on the old one and archive it.
- **Accept with a caveat** — if the specific finding wasn't part of the retraction, note the retraction in the claim body and keep it.

No claim is rewritten automatically. The judgment is always yours.

**5. Update the paper entity.**

Set the entity's lifecycle to match the record:

```yaml
lifecycle: retracted
```

Then resolve the alert card (`Cmd/Ctrl-P` → **Memoria: resolve inbox card**).

**6. Check for new tensions.**

A retraction sometimes resolves — or creates — a contradiction. Glance at Knowledge's **Contradictions** view after updating claims.

## Verify

- Every alert card from the sweep is resolved
- Affected paper entities carry `lifecycle: retracted`
- Each citing claim was softened, superseded, or caveated — and a re-run raises no new alerts

## Related

- The pipeline context: [Ingest routing](../../reference/ingest.md)
- Archiving the fallout: [Archive a source](../library/archive-a-source.md)
- The per-draft complement: [Verify and revise a draft](../project/verify-and-revise.md)
- Why the operation never flips a note: [The Peer-reviewer](../../explanation/profiles/peer-reviewer.md)


---

<!-- source: how-to-guides/operate/run-a-schema-migration.md -->

# Run a schema migration

Rewrite a frontmatter field across many notes at once — a field rename, a value-set change, or a deprecated-field removal. There is **no automated migration command**: a migration is a deliberate, git-disciplined manual pass, validated by the schemas. That's by design — schema changes fall in the `schema-content` class, which the policy gate never lets run unattended ([Linter: detectors and auto-fix](../../reference/linter.md)).

Use this for **structural** changes that touch many notes. For renaming a single vocabulary term, [Manage your topic vocabulary](../knowledge/manage-vocabulary.md) covers the lighter path.

## Prerequisites

- A clean working tree — `git status` shows nothing uncommitted, so the migration is one reviewable diff
- A clear before/after for the field you're changing
- If the schema itself changes: the matching edit ready for `.memoria/schemas/types/<type>.yaml` (the single schema source the Linter, the pre-commit hook, and the policy MCP all read)

## Steps

**1. Commit the current vault state.**

```bash
cd ~/Memoria
git status                                   # confirm the tree is clean first
git add notes/ catalog/ .memoria/schemas/    # stage only the migration scope, never -A
git commit -m "pre-migration snapshot"
```

Stage the paths the migration touches explicitly — never `git add -A`, which would sweep unrelated working-tree changes into the snapshot. A clean commit beforehand makes the migration one diff you can review — and revert in one command.

**2. Enumerate the affected notes — your dry run.**

```bash
grep -rl "^methodology: rct" notes/ catalog/ | tee /tmp/migration-files.txt
wc -l /tmp/migration-files.txt
```

If the count is surprisingly high or low, your selector is wrong — fix it before touching anything. Do not proceed on a surprising count.

**3. Update the schema first (if the field definition changes).**

Edit `.memoria/schemas/types/<type>.yaml` so the new field name or value set is legal *before* the notes change — otherwise every migrated note fails validation.

**4. Apply the change.**

For a mechanical rename over the reviewed file list:

```bash
xargs -a /tmp/migration-files.txt sed -i 's/^methodology: rct$/methodology: randomized-controlled-trial/'
```

For anything non-mechanical (restructuring a map, splitting a field), edit by hand or with a one-off script — but always over the step-2 list.

**5. Validate.**

```bash
python3 .memoria/operations/integrity/linter/detectors.py --vault .
```

`schema-check` must report nothing for the migrated field. The pre-commit hook will re-validate every staged note at commit, so a missed file blocks rather than lands.

**6. Review and commit.**

```bash
git diff --stat       # only the expected files, only the expected change
xargs -a /tmp/migration-files.txt git add            # stage exactly the reviewed file list
git add .memoria/schemas/types/<type>.yaml           # plus the schema, if step 3 changed it
git commit -m "schema: rename methodology rct → randomized-controlled-trial"
```

Staging from the step-2 file list keeps the commit scoped to the reviewed notes — no stray working-tree edits ride along.

If the diff is wrong, `git reset --hard HEAD~1` returns you to the step-1 snapshot.

## Verify

- `git diff --stat` showed only the intended change across the expected note count before commit
- The detectors report no `schema-check` findings for the migrated field
- Dataview/Bases views that filter on the field still return the expected notes

## Related

**How-to**

- The lighter, single-term path: [Manage your topic vocabulary](../knowledge/manage-vocabulary.md)
- The validation pass: [Run the Linter](run-the-linter.md)
- Recovering from a bad edit: [Fix broken frontmatter](../troubleshooting/fix-broken-frontmatter.md)

**Reference**

- The schema source and what reads it: [Document types](../../reference/document-types.md)
- Why `schema-content` never runs unattended: [Linter: detectors and auto-fix](../../reference/linter.md)


---

<!-- source: how-to-guides/operate/redeploy-profiles.md -->

# Redeploy profiles

Push vault source edits — to `SOUL.md`, `config.yaml`, skills, or lane-overrides — out to the installed copies in `~/.hermes/profiles/`.

## When to redeploy

- After editing any author-owned file in `<vault>/.memoria/profiles/memoria-<name>/`
- After editing `<vault>/.memoria/lane-overrides/<name>.yaml`
- After a `git pull` that changed profile files
- After adding or rotating a key in `~/.hermes/.env` (the redeploy propagates it into each profile's `.env`)

## Steps

**1. Redeploy all profiles.** Run from the repo clone (it holds the installer); `--profiles-only` skips the full bootstrap and just re-deploys MCP dependencies, the five profiles, and the crons.

```bash
bash scripts/install.sh --profiles-only --vault <vault>      # Linux / WSL2 (where Hermes runs)
```

```powershell
.\scripts/install.ps1 -ProfilesOnly -Vault <vault>           # Windows native production
```

`--vault <dir>` / `-Vault <dir>` names your runtime vault if it isn't the platform default (`~/Memoria` on Linux/WSL2, `%USERPROFILE%\Memoria` on Windows). The script is idempotent — safe to run at any time. It:

- Stages each profile's files to a temp directory
- Substitutes `{{PYTHON}}` (the vault venv interpreter) and `{{VAULT_PATH}}` in `config.yaml`
- Calls `hermes profile install --force` for each of the five profiles ([Installer (bootstrap)](../../reference/installer.md))
- Seeds each profile's `.env` from `~/.hermes/.env` — never overwrites a value already set

**2. Redeploy a single profile** (faster when only one changed):

```bash
bash scripts/install.sh --profiles-only --only memoria-librarian
```

```powershell
.\scripts/install.ps1 -ProfilesOnly -Only memoria-librarian
```

**3. Confirm the change landed.**

```bash
hermes profile show memoria-<name>
```

The output should reflect the edit you made (e.g., updated model name, new MCP server entry).

For lane-override changes, verify with a test write operation — check `system/logs/audit.jsonl` to confirm the new policy is enforced.

## Verify

```bash
hermes profile list
```

The five `memoria-*` profiles (`copi`, `librarian`, `writer`, `peer-reviewer`, `engineer`) show as registered.

If you suspect the deployed copies still don't match the vault source, compare them directly and reconcile per the full procedure in [Fix profile drift](../troubleshooting/fix-profile-drift.md).

## Related

- Profile configuration guide: [Configure a profile](../hermes-agent/configuration.md)
- Fix profile drift: [Fix profile drift](../troubleshooting/fix-profile-drift.md)
- Set up profiles (first install): [Set up Hermes](../setup/set-up-hermes.md)
- The flags and the idempotency mechanism: [Installer (bootstrap)](../../reference/installer.md)


---

<!-- source: how-to-guides/operate/rebuild-the-search-index.md -->

# Rebuild the search index

Re-run the `qmd` embedding to restore semantic search. `qmd` (hybrid BM25 + vector search) is the shared similarity index behind the Co-PI's vault search, the Librarian's comparative pulls, and the Peer-reviewer's verify checks ([External integrations](../../reference/integrations.md)).

## When to rebuild

- The Co-PI's vault answers miss notes you know exist ([Query the vault](../knowledge/query-the-vault.md))
- New papers stop showing up in `[!brief]` comparisons or similarity checks
- A batch of 20+ notes was ingested and you haven't rebuilt since
- `qmd search "known term"` returns empty or omits notes you know exist

## When a re-embed is (and isn't) the fix

A full `qmd embed` re-embeds *every* note. Before spending the time, rule out cheaper causes:

| Symptom | Likely cause | What to do |
| --- | --- | --- |
| One new note isn't found | Not yet indexed | Confirm it's saved to disk; a few notes rarely justify a full rebuild — let the scheduled rebuild (step 4) catch it |
| Search misses many notes or returns empty | Stale or missing index | Full `qmd embed` (this guide) |
| Found by keyword but not by meaning | Vectors stale / embedding model changed | Full `qmd embed` — re-embedding is the only fix when the vectors are stale |
| Found by `qmd search` but the Co-PI doesn't cite it | Not an index problem — a retrieval/prompt issue | Push the Co-PI ("which note says that?"), not the index |

## Steps

**1. Confirm the symptom.**

```bash
cd <vault>
qmd search "<term you know exists in a note>"
```

If this returns empty or fewer results than expected, the index is stale.

**2. Run a full rebuild.**

```bash
cd <vault>
qmd embed
```

This re-embeds every note in the vault. Estimated time:

| Vault size | Time |
| --- | --- |
| Under 500 notes | 1–5 minutes |
| 500–2000 notes | 5–15 minutes |
| 2000+ notes | 15–30 minutes |

The index lives inside the vault and is gitignored — never commit it.

**3. Verify the rebuild.**

```bash
qmd search "<term>"
```

Confirm the expected notes now appear. Then test the consumer you actually noticed the staleness in — ask the Co-PI a question whose answer lives in a recently added note and check it cites that note.

**4. Set up automatic rebuilds** (optional).

The installer wires no qmd cron — embedding is incremental in normal operation. If your ingest volume makes weekly full rebuilds worthwhile, drop a one-line wrapper in `~/.hermes/scripts/` and register it the same way the installer registers its deterministic crons:

```bash
printf '#!/usr/bin/env bash\ncd <vault> && qmd embed\n' > ~/.hermes/scripts/memoria-qmd-embed.sh
chmod +x ~/.hermes/scripts/memoria-qmd-embed.sh
hermes cron create '0 3 * * 0' --script memoria-qmd-embed.sh --no-agent \
  --name memoria-qmd-embed --deliver local
```

`hermes cron list` should then show `memoria-qmd-embed` with a next-run time.

## Verify

```bash
qmd search "claim note you recently wrote"
```

Returns the note, and the Co-PI's vault answers cite recently added notes again.

## Related

- Stale-index failure mode: [Failure modes](../../reference/failure-modes.md) — "qmd search index stale"
- The search consumer you'll notice first: [Query the vault](../knowledge/query-the-vault.md)
- Where qmd sits in the toolchain: [External integrations](../../reference/integrations.md)


---

<!-- source: how-to-guides/operate/run-the-vault-eval.md -->

# Run the vault eval

Run Memoria's system-level evaluation on demand — dispatch the gold-set tasks, let the lanes work them, and score the results — instead of waiting for the quarterly cron. The eval measures whether the *deployed system* finds, extracts, links, and verifies correctly on your vault; its verdict is diagnostic, never gating. For the gold set, the metrics, and the result contract, see [Vault eval](../../reference/vault-eval.md).

## When to run it by hand

- After installing a fresh release vault or changing profiles, to confirm capability didn't regress
- When the eval-trend dashboard shows a dip you want to reproduce immediately
- To smoke-test a fresh vault once the gold-set papers (Transformer, BERT, ResNet, Adam, Dropout) are ingested

## Prerequisites

- The gold-set papers ingested — the shipped tasks reference well-known papers so they work on any vault once those are present
- The board and the five profiles running (the eval reuses board dispatch and the lane → profile map)

## Steps

**1. Preview the dispatch.** See which `lifecycle: current` gold tasks would enqueue, creating nothing:

```bash
cd <vault>
python .memoria/operations/telemetry/eval/eval_dispatch.py --vault . --dry-run
```

**2. Dispatch the cards.** One idempotent card per gold task, on its owning lane. The idempotency key is per `(task, quarter)`, so re-running inside the same quarter converges to one card per task rather than duplicating:

```bash
python .memoria/operations/telemetry/eval/eval_dispatch.py --vault .
```

**3. Let the lanes run the cards.** Each lane works its eval card under the non-committing contract — scratch-only writes, results reported on the card; a run never mutates the vault. Give the board time to drain (`hermes kanban list` to watch).

**4. Score the run.** The deterministic, zero-LLM scorer reads the cards' reported result blocks and computes only what each result makes computable — no faked scores:

```bash
python .memoria/operations/telemetry/eval/eval_score.py --vault .                    # current quarter
python .memoria/operations/telemetry/eval/eval_score.py --vault . --quarter previous # what the cron scores
```

Add `--k <n>` to change the recall window (default 3) and `--dry-run` to compute without appending to the log.

**5. Read the trend.** Open the **eval-trend** dashboard (`system/dashboards/eval-trend.md`) — it renders the newest run per quarter plus the latest run's per-task breakdown ([Dashboards](../../reference/dashboards.md)).

## Verify

- `system/metrics/eval/runs.jsonl` has a new line (timestamp, quarter, k, per-task records, per-metric aggregates) — written only when at least one card reported a result block
- The eval-trend dashboard shows the run, with `recall@k` / `support-rate` / `FAMA-clean` per task
- A task whose card reported no machine-readable result shows as **unscored** — never a faked score
- `system/eval/last-run.md` reflects the dispatch you just ran

## The cron equivalent

The quarterly `memoria-eval` cron does exactly these steps in one pass: it **scores the previous quarter** first (its cards have reported by then), then **dispatches** the new quarter's cards. Running on demand is the same two commands by hand. The schedule and wrapper are owned by [Installer (bootstrap)](../../reference/installer.md).

## Related

- The gold set, metrics, and result contract: [Vault eval](../../reference/vault-eval.md)
- The trend dashboard and metric bands: [Dashboards](../../reference/dashboards.md)
- The sibling deterministic maintenance job: [Run the Linter](run-the-linter.md)
- The cron wiring: [Installer (bootstrap)](../../reference/installer.md)


---

<!-- source: how-to-guides/operate/inspect-session-logs.md -->

# Inspect session logs

Read the audit trail and the per-session summaries from the terminal — filter by lane, date, decision, or card — when you need to answer "what did the system actually do?" without waiting for a dashboard. This is the ad-hoc path beneath the audit-log and fleet-health dashboards ([Dashboards](../../reference/dashboards.md)); they render the same data — this is for one-off questions and scripting.

Both logs are append-only JSONL and **read-only** — never edit them; an out-of-band edit is exactly what the Linter's tamper detectors exist to catch.

## The two logs

| Log | Path | One row / file |
| --- | --- | --- |
| Policy audit log | `system/logs/audit.jsonl` | One gated decision (`allow` / `allow_with_log` / `deny` / `dry_run`), plus a paired `write_complete` record per write. |
| Per-session summaries | `system/logs/sessions/YYYY-MM-DD-HHMM.jsonl` | One deterministic digest per session — a header plus one record per touched path. |

The audit log is forensic and grows forever; the per-session summaries are digests the Linter writes once a session has been quiet for 24 h. The design is in [Session logging](../../explanation/architecture/session-logging.md); the audit field schema is owned by [Policy MCP](../../reference/policy-mcp.md).

## Prerequisites

- `jq` installed (`sudo apt install jq`) — every recipe below uses it
- Run from the vault root so the relative paths resolve

## Recipes

The audit fields you'll filter on: `timestamp` (UTC, `…Z`), `profile` (`memoria-<name>`), `action` (`read` / `write` / `append` / `move` / `delete` / `mkdir` / `auto_fix` / `report`), `path`, `task_id`, `decision`, and `policy_rule`.

**Recent denials across all lanes** — the first thing to check when a write didn't land:

```bash
jq -c 'select(.decision == "deny")' system/logs/audit.jsonl | tail -20
```

**One lane's activity on a given day:**

```bash
jq -c 'select(.profile == "memoria-writer" and (.timestamp >= "2026-06-18"))' system/logs/audit.jsonl
```

**Everything a single card touched** — the full footprint of one task, in order:

```bash
jq -c 'select(.task_id == "TASK-2026-06-18-003") | {timestamp, action, path, decision}' system/logs/audit.jsonl
```

**Pending schema migrations** — `dry_run` decisions are writes the gate refused to apply automatically (a field rename or enum change awaiting `lint:migrate-schema`):

```bash
jq -c 'select(.decision == "dry_run") | {path, policy_rule}' system/logs/audit.jsonl
```

**Decision tally for a lane** — a quick health read without the dashboard:

```bash
jq -r 'select(.profile == "memoria-librarian") | .decision' system/logs/audit.jsonl | sort | uniq -c
```

**Trace a write's reversibility pair** — the decision entry carries `before_hash`; the separate `write_complete` record carries the paired `after_hash`, matched by `task_id` + `path`:

```bash
jq -c 'select(.path == "catalog/papers/smith-2024.md")' system/logs/audit.jsonl
```

**Read the latest session summary** — what a session accomplished, digested:

```bash
ls -t system/logs/sessions/ | head -1
jq . "system/logs/sessions/$(ls -t system/logs/sessions/ | head -1)"
```

The digest's header carries the task, profiles, start/end, and counts by action and decision; each subsequent record is one touched path with its actions, final decision, and final `after_hash`.

## Verify

- Your filter returns rows (an empty result usually means the field value or date didn't match — check `profile` is the full `memoria-<name>` and the date is `YYYY-MM-DD`)
- Counts you compute by hand match what the audit-log / fleet-health dashboards show for the same window

## Notes and limits

- **No note content** ever enters either log — only paths, IDs, actions, decisions, and hashes. You can't reconstruct *what* was written, only *that* it was and whether it was authorized.
- **`write_complete` is a record kind, not a decision** — don't filter for it under `.decision`; match the before/after pair by `task_id` + `path`.
- **Audit growth is expected** — the log is never rotated; the Linter raises an advisory only past 50 MB.
- Only sessions quiet for 24 h are summarized, so a digest for today's in-flight work won't exist yet.

## Related

- The two-log design and why they stay separate: [Session logging](../../explanation/architecture/session-logging.md)
- The audit field schema and hash pairing: [Policy MCP](../../reference/policy-mcp.md)
- The full log inventory and JSONL conventions: [Telemetry & logs](../../reference/telemetry.md)
- The dashboards over this data: [Dashboards](../../reference/dashboards.md)
- Diagnosing a write that was denied: [Diagnose a denied or blocked write](../troubleshooting/diagnose-a-denied-write.md)


---

<!-- source: how-to-guides/troubleshooting/README.md -->

# Troubleshooting

Start from the symptom you're seeing. Each guide takes one failure mode from symptom → diagnosis → fix — find the row that matches what's wrong and follow it through.

| Symptom                                                           | Guide                                                            |
| ----------------------------------------------------------------- | ---------------------------------------------------------------- |
| Hermes or ACP is down and you still need to work                  | [Safe mode](safe-mode.md)                                        |
| A card won't advance on the Kanban board                          | [Fix a stuck card](fix-stuck-card.md)                            |
| YAML parse error; a note is missing from Dataview queries         | [Fix broken frontmatter](fix-broken-frontmatter.md)              |
| An agent's write didn't land — denied, or never reached the gate  | [Diagnose a denied or blocked write](diagnose-a-denied-write.md) |
| "Citekey not found" at ingest                                     | [Fix a stale `.bib`](../zotero/fix-stale-bib.md)                           |
| Deployed profile doesn't match the vault source                   | [Fix profile drift](fix-profile-drift.md)                        |
| Enrichment is empty after ingest; classification never applied    | [Fix empty enrichment](fix-empty-enrichment.md)                  |
| A filtered query returns nothing though the notes are valid       | [Fix missing query results](fix-missing-query-results.md)        |

## When several failures appear at once

Work highest-impact failures first:

1. Address `CRITICAL` issues before anything else: tamper detection and security failures can invalidate later diagnosis.
2. Address silent `HIGH` issues next: failures that look like "nothing to do" waste time and compound quietly.
3. Address visible `HIGH` breakage after silent failures.
4. Batch `MEDIUM` issues into the weekly review ritual.
5. Batch `LOW` issues monthly unless they block current work.

The severity definitions and full failure table live in [Failure modes](../../reference/failure-modes.md).


---

<!-- source: how-to-guides/troubleshooting/safe-mode.md -->

# Safe mode

**Symptom:** Hermes, ACP, or some optional tool is down, and you still need to ingest, triage, or export.

**Diagnosis:** the integration layer is unreachable, but the underlying operations don't depend on it — every core workflow has a terminal-level fallback.

**Fix:** for each of the three workflows below — the command that must work, the named fallbacks, and the one thing never to run automatically.

## Ingest a source

**Must work:** enqueue the capture card from the terminal — the same card the palette commands create:

```bash
hermes kanban create "Ingest <citekey>" --assignee memoria-librarian
```

**If the Agent Client pane is unresponsive** — the terminal is always the fallback: the pane and the palette macros shell out to the same `hermes kanban create`. A direct lane chat (`hermes -p memoria-librarian chat`) also works as a debugging posture.

**If enrichment APIs are unreachable** — ingest still creates the Catalog entity from the `.bib` metadata; the per-field provenance records what's missing. The enrichment fills in on a later re-ingest once connectivity is restored — a thin entity is better than a deferred ingest.

**If `.bib` is not synced** — push it manually first, then ingest: [Fix a stale .bib](../zotero/fix-stale-bib.md).

**Never run automatically:** a schema migration. Schema changes require human review of every proposed field change ([Run a schema migration](../operate/run-a-schema-migration.md)).

---

## Review and triage

**Must work:** open the Inbox queue for **Needs me** and Maintenance for weekly
structural checks. The embedded Bases/Dataview queries surface the triage queue
without any Hermes involvement.

**If Hermes is unreachable** — triage is a human-only action anyway. Classify by hand:

1. Open the paper entity from the Library space's Catalog papers view.
2. Copy the fields you accept from the `_proposed_classification` block into the main frontmatter
3. Delete the `_proposed_classification:` block
4. Set `lifecycle: current` ([Classify a source](../library/classify-a-source.md))

**If Dataview is not rendering** — search manually in Obsidian for `lifecycle: proposed` to find unclassified notes.

**Never run automatically:** accept Inbox cards in bulk. Every `proposed` card requires human review — agent output is unverified until you confirm the citekeys and claims.

---

## Export a draft

**Must work:**

```bash
pandoc projects/<slug>/<draft>.md \
  --citeproc \
  --bibliography .memoria/memoria.bib \
  --csl .memoria/csl/<style>.csl \
  -o /tmp/<output>.docx
```

**If an Obsidian export plugin fails** — run Pandoc directly from the terminal; it is the authoritative export route (any plugin is just a UI wrapper over the same command). See [Export routes and formats](../../reference/export.md).

**If `zotero.lua` live citations are broken** — fall back to static `--citeproc`. Do not debug `zotero.lua` mid-draft. Finish the draft with static citations, then investigate using the failure-modes guide.

**Never run automatically:** auto-export on file save. Drafts change constantly; automatic export creates Git noise and can overwrite a clean export with a mid-sentence state.

---

## Quick system check

Run before assuming something is broken:

```bash
echo $KILOCODE_API_KEY $OPENALEX_API_KEY   # env vars loaded?
hermes --version                           # Hermes reachable?
hermes profile list                        # profiles registered?
cd <vault-path> && git status              # vault synced?
```

All four must return expected values before blaming a tool.

## Related

- Return-to-work checklist: [Return to work](../inbox/return-to-work.md)
- Fix stale .bib: [Fix a stale .bib](../zotero/fix-stale-bib.md)
- Fix stuck card: [Fix a stuck card](fix-stuck-card.md)
- Rebuild search index: [Rebuild the search index](../operate/rebuild-the-search-index.md)


---

<!-- source: how-to-guides/troubleshooting/fix-stuck-card.md -->

# Fix a stuck card

**Symptom:** a Kanban card won't advance — it sits in `running`, `ready`, or `blocked` without progressing, and a queue may be backing up behind it.

**Diagnosis:** the state the card is stuck in names the cause — a crashed worker, an unresolvable `assignee`, or an exhausted retry budget awaiting a human decision.

**Fix:** identify the state below, then apply the matching remedy.

## Detect

```bash
hermes kanban show <card-id>     # full state: status, retry count, blocker reason
hermes kanban list               # see if a queue is backing up behind one card
```

A stuck card shows one of three states:

| State | What it means |
| --- | --- |
| `running` long past expected completion | Worker crashed or hung mid-claim |
| `ready` never dispatched | Unresolvable `assignee` field |
| `blocked` | Hit `max_retries` — needs human decision before it can continue |

## Fix

**Card stuck in `running` (worker crashed).**

The dispatcher reclaims stale `running` claims automatically on its next tick and returns the card to `ready`. No manual intervention is needed for a first occurrence. Wait for the next tick (usually within 60 seconds).

If the card re-enters `running` and immediately stalls again, the problem is the prompt or tool, not the crash. Treat it as the `blocked` case.

**Card stuck in `ready` and never dispatched.**

Check the `assignee` field:

```bash
hermes kanban show <card-id> | grep assignee
```

The assignee must match a real lane name. If it doesn't, edit the card:

```bash
hermes kanban edit <card-id> --assignee memoria-librarian
```

If the card was created with an invalid lane, it will never be picked up — the dispatcher logs `skipped_nonspawnable` and leaves it in `ready`. Fix the assignee and the dispatcher will claim it on the next tick.

**Card stuck in `blocked` (hit max_retries).**

A blocked card needs a fix before re-queuing, not just a retry. Diagnose first:

```bash
hermes kanban show <card-id>
```

Read the `blocker_reason` and the `handoff_summary`. Then:

1. Fix the underlying problem (broken tool, malformed input, missing file)
2. Update the card's metadata if the payload was wrong:
   ```bash
   hermes kanban edit <card-id> --metadata '{"source": "corrected-citekey"}'
   ```
3. Unblock the card:
   ```bash
   hermes kanban unblock <card-id>
   ```

The unblock resets the retry count and returns the card to `ready`. If the same failure recurs, the prompt or tool is broken — archive rather than retry indefinitely.

**Archive an infeasible card.**

If the card represents work that genuinely can't be done (source no longer available, citekey doesn't exist, task was superseded):

```bash
hermes kanban archive <card-id> --reason "infeasible: source PDF no longer accessible"
```

## Verify

```bash
hermes kanban show <card-id>
```

Status has changed from the stuck state, or the card is archived with an explicit reason. No card should be silently sitting.

## Related

- Kanban board states reference: [Kanban board reference](../../reference/kanban-board.md)
- Full failure-modes catalog: [Failure modes](../../reference/failure-modes.md)
- Retry pattern explanation: [Kanban board](../../explanation/kanban-board/README.md)
- The state machine explained: [Board states and the review gate](../../explanation/kanban-board/states.md)


---

<!-- source: how-to-guides/troubleshooting/fix-broken-frontmatter.md -->

# Fix broken frontmatter

**Symptom:** a note disappears from Dataview queries, or Obsidian's Properties panel shows a YAML parse error.

- The Obsidian Properties panel shows a YAML parse error on a note
- The note does not appear in Dataview queries that should include it
- The Linter operation reports a schema or YAML finding on this note

**Diagnosis:** the note's frontmatter contains malformed YAML, so the parser skips the whole block. Run the Linter operation to confirm and pinpoint the bad line.

**Fix:** edit the raw file outside Obsidian, correct the malformed line, and re-check.

## Detect

Run the Linter operation — report-only, zero-LLM — to confirm and identify the specific error ([Run the Linter](../operate/run-the-linter.md)):

```bash
python3 .memoria/operations/integrity/linter/detectors.py --vault .
```

Common YAML errors:

| Error | Example |
| --- | --- |
| Unclosed string | `title: "Unterminated title` |
| List indentation error | `methods:` followed by `- field-study` at wrong indent |
| Missing closing `---` delimiter | Frontmatter block never ends |
| Colon in value without quoting | `title: A Study of AI: Methods` (colon in title) |
| Tab character instead of spaces | YAML requires spaces, not tabs |

## Fix

**1. Open the raw file in an editor outside Obsidian.**

Obsidian masks the raw YAML in Properties view. Open the file in VS Code or Notepad++ to see exactly what's in the frontmatter block:

```powershell
code "catalog\papers\<citekey>.md"
```

**2. Locate and fix the malformed line.**

The Linter's output names the specific line or field. Common fixes:

- Wrap strings containing colons, brackets, or special characters in double quotes: `title: "A Study of AI: Methods"`
- Fix list indentation — each item should be two spaces in, with a hyphen: `- field-study`
- Ensure the frontmatter ends with a closing `---` on its own line
- Replace any tab characters with two spaces

**3. Save and verify in Obsidian.**

After saving the fix, Obsidian should show no error in the Properties panel. The note should appear in Dataview queries within a few seconds (Dataview re-indexes on file change).

## Verify

In Obsidian, run this Dataview query in a new note to confirm the repaired note is visible:

```dataview
FROM "catalog/papers"
WHERE file.name = "<citekey>"
```

The note should appear. Then confirm with the Linter operation:

```bash
python3 .memoria/operations/integrity/linter/detectors.py --vault .
```

No YAML or schema findings reported for this note.

## If the fix doesn't hold

If Obsidian re-introduces the error after saving, a plugin or Obsidian's Properties panel is auto-formatting the YAML. Check which plugins have "format on save" behavior and disable it for this file type. The frontend `obsidian-linter` plugin is the likely cause — it must be uninstalled, not merely excluded from folders; see [Set up Obsidian](../setup/set-up-obsidian.md).

## Related

- Why the frontend Obsidian Linter is incompatible: [Set up Obsidian](../setup/set-up-obsidian.md)
- Frontmatter schema reference: [Frontmatter fields](../../reference/frontmatter.md)
- Full failure-modes catalog: [Failure modes](../../reference/failure-modes.md)
- Related YAML-corruption pitfalls: [Common pitfalls](../../explanation/knowledge/common-pitfalls.md)


---

<!-- source: how-to-guides/troubleshooting/diagnose-a-denied-write.md -->

# Diagnose a denied or blocked write

**Symptom:** an agent reports a write, but it never shows up in the vault.

**Diagnosis:** there are two very different causes, and they need opposite fixes:

1. The policy MCP **denied** it — a deliberate decision, recorded in the audit log.
2. The write **never reached the gate** — a wiring or plugin failure. Because Hermes fails *open* on hook errors, these can be silent.

**Fix:** use the audit log to tell the two apart, then act on the cause — read the policy `reason`, or repair the wiring.

## Prerequisites

- The policy MCP wired and running — it writes `system/logs/audit.jsonl`. Until the gate runs live, that log does not exist; a missing *file* is a wiring problem, not a denial.
- The [audit-log dashboard](../../explanation/dashboards/operational-health/audit-log.md) available in Obsidian

## Steps

**1. Open the audit-log dashboard.**

From `home.md` → the audit-log dashboard. Its primary view is recent **denies and dry-runs**, newest first. Find an entry whose `path` and `profile` match the missing write, around the time it happened.

**2. Found a matching `deny` or `dry_run`? It was a policy decision.**

Read the `decision`, `policy_rule`, and `reason` fields on the entry (full field schema: [Policy audit log](../../reference/policy-audit-log.md); lane-override decision protocol: [Policy MCP](../../reference/policy-mcp.md)):

- **`deny`** — the lane forbids that action on that path (e.g., Librarian writing to `notes/claims/`). The fix is either the wrong lane for the task, or an intended permission you must change in the lane-override.
- **`dry_run`** — the path is a review-gated zone; the write is *held*, not refused. Approve it through the queue: [Work the review queue](../inbox/work-the-review-queue.md).

**3. No matching entry at all? The write never reached the gate.**

Hermes fails open on hook errors, so a broken hook or unregistered MCP can let an attempt pass without ever logging a decision. Check, in order:

- Is the policy server registered in the profile's `config.yaml` (`mcp_servers`)?
- Smoke-test the gate live: `python3 .memoria/mcp/policy_mcp.py --vault . --decide '{"profile":"memoria-librarian","action":"write","path":"notes/claims/x.md","task_id":"T1"}'`. It must return `"decision": "deny"` — `notes/claims/` is review-gated. If it errors or allows, the gate logic is broken. (The full component test suite is `scripts/test.sh l1` from the repo clone.)
- Did the Obsidian Local REST API native MCP or a plugin error? The agent may report success while the write silently failed upstream of the gate. Check the plugin's HTTPS server is on, its port matches `OBSIDIAN_MCP_PORT`, and `OBSIDIAN_MCP_SSL_VERIFY` points at the exported PEM certificate/CA bundle ([Set up Obsidian](../setup/set-up-obsidian.md)).

A missing log entry for a write that *should* have been attempted points at wiring, not policy.

**4. Distinguish a policy denial from a plugin failure.**

If the agent reported success, nothing changed on disk, and there's **no** audit entry, suspect the vault-access path (obsidian-local-rest-api) rather than policy. The audit log only records what reached the gate — silence there means the write didn't get that far.

**5. Watch for a spike — it can be a security signal.**

A sudden rise in denies, especially right after ingesting a PDF, can indicate an indirect prompt-injection attempt nudging an agent toward unauthorized writes — not just operator error. The audit log is where this surfaces first; escalate and inspect the source rather than reflexively widening permissions.

## Verify

- You can name the cause: a logged `deny`/`dry_run` (policy) vs no entry (wiring/plugin).
- For a policy denial, you've read `policy_rule` and `reason`.
- Each write's `before_hash` / `after_hash` pairing is intact (the Linter's `audit-unpaired-writes` isn't firing) — confirming the write completed and wasn't tampered with.

## Related

- Approving a held (`dry_run`) write: [Work the review queue](../inbox/work-the-review-queue.md)
- Other troubleshooting procedures: [Troubleshooting](README.md)
- The audit event schema: [Policy audit log](../../reference/policy-audit-log.md)
- The decision protocol and action vocabulary: [Policy MCP](../../reference/policy-mcp.md)
- The dashboard: [audit-log dashboard](../../explanation/dashboards/operational-health/audit-log.md)


---

<!-- source: how-to-guides/troubleshooting/fix-profile-drift.md -->

# Fix profile drift

**Symptom:** a deployed Hermes profile runs stale behavior — an edit you made to a `SOUL.md`, skill, or lane-override doesn't show up. The deployed copy in `~/.hermes/profiles/` no longer matches the vault source in `<vault>/.memoria/profiles/`.

**Diagnosis:** either the vault source changed and the install script hasn't been re-run, or someone edited the deployed copy directly. Compare the two to confirm, then decide which case you're in before fixing.

**Fix:** resolve the cause, then re-run the profile install to bring the deployed copy back in sync.

## Detect

Compare the vault source against the deployed copy, per profile:

```bash
diff -r <vault>/.memoria/profiles/memoria-librarian ~/.hermes/profiles/memoria-librarian \
  --exclude .env   # config.yaml will differ by the substituted {{PYTHON}}/{{VAULT_PATH}} placeholders
```

Any difference beyond the `.env` and the placeholder substitutions is drift. Repeat for each of the five profiles (`copi`, `librarian`, `writer`, `peer-reviewer`, `engineer`).

Also confirm the registration list is clean:

```bash
hermes profile list
```

The five `memoria-*` profiles should be present.

## Diagnose before fixing

There are two causes with different implications:

**Cause A: The vault source changed and the install script hasn't been re-run.**
This is the normal case after a `git pull` or after editing a `SOUL.md`. Fix: re-run the profile install (below).

**Cause B: Someone edited the deployed copy directly.**

If the diff shows meaningful changes in the deployed copy (not in the vault source), decide:

- **Promote the edit to vault source:** copy the change into `<vault>/.memoria/profiles/memoria-<name>/`, commit, then re-deploy (below)
- **Discard the edit:** just re-deploy (it overwrites the deployed copy with the vault source)

## Fix

Once you've resolved Cause A or B, run the redeploy procedure — `install.sh --profiles-only` (whole fleet or `--only <profile>`) from the repo clone — per [Redeploy profiles](../operate/redeploy-profiles.md). That guide owns the install flags, the Windows variants, and the idempotency details.

## Verify

- The `diff -r` above is clean for every profile (modulo `.env` and placeholders)
- The redeploy verification passes — `hermes profile list` shows exactly the five `memoria-*` profiles and `hermes profile show memoria-<name>` reflects the edit you expected ([Redeploy profiles](../operate/redeploy-profiles.md))

## Related

- Redeploy profiles (normal workflow): [Redeploy profiles](../operate/redeploy-profiles.md)
- Profile configuration: [Configure a profile](../hermes-agent/configuration.md)
- Full failure-modes catalog: [Failure modes](../../reference/failure-modes.md)
- The idempotency mechanism behind the fix: [Distribution model](../../explanation/deployment/distribution-model.md)


---

<!-- source: how-to-guides/troubleshooting/fix-empty-enrichment.md -->

# Fix empty enrichment

**Symptom:** a paper ingested "successfully" — the Catalog entity and Inbox candidate appeared — but the note carries no enrichment: the `_enrichment` block is empty, `research_area` and `methodology` were never applied, and there's no `[!brief]` comparative read.

- A captured paper's `_enrichment.*` namespace is empty or absent
- `research_area` / `methodology` stayed unset even though the paper is clearly classifiable
- No Inbox `flag` was raised explaining the ambiguity — it simply looks like nothing happened

**Diagnosis:** the Librarian's `OPENALEX_API_KEY` is missing. OpenAlex has required a key since 2026-02; without it the enrichment call degrades silently. Tier-0 capture still succeeds (it works from the local `.bib` alone — the offline floor), so the note lands and ingest *looks* done — but the OpenAlex topics that drive classification never arrive, so `classify` is a no-op and the enrichment block stays thin. This is the trap: degraded data, no error.

**Fix:** seed the key, then re-ingest the affected paper(s) — the fix is not retroactive, the enrichment has to be re-run.

## Detect

**1. Confirm the key is missing.**

```bash
grep OPENALEX_API_KEY ~/.hermes/profiles/memoria-librarian/.env || echo "not set"
```

**2. Confirm the symptom on the note.** Open the paper at `catalog/papers/<citekey>.md` and check that the `_enrichment` namespace is empty and `research_area` is unset.

**3. Confirm classify saw no data.** The classify audit names the cause — a no-data run logs a no-op rather than an applied or flagged decision:

```bash
grep '"citekey": "<citekey>"' system/logs/classify.jsonl
```

## Fix

**1. Add the OpenAlex key and propagate it.**

Register a free key at `openalex.org/settings/api`, add it to the global secrets file, then redeploy so each profile's `.env` is seeded (the redeploy never overwrites a value already set):

```bash
echo 'OPENALEX_API_KEY=your-key-here' >> ~/.hermes/.env
bash scripts/install.sh --profiles-only --vault <vault>
grep OPENALEX_API_KEY ~/.hermes/profiles/memoria-librarian/.env   # confirm seeded
```

See [Set up Hermes](../setup/set-up-hermes.md) and [External integrations](../../reference/integrations.md) for the full key roster.

**2. Re-ingest the affected paper.**

Enrichment ran once and degraded; re-running it on the single citekey backfills it. From Obsidian, re-run the catalog step on the one paper:

`Cmd/Ctrl-P` → **Memoria: catalog source**, enter the `<citekey>`. This stages a Librarian `catalog-enrich-record` card that re-runs enrichment with the key now present. (Equivalently, ask the Co-PI: "re-enrich `<citekey>`".)

For a paper that never completed past Tier-0 (`ingest_status: tier0`), the `memoria-sweeps` cron's `--retry` backstop re-enqueues it automatically every 15 minutes — once the key is set, the next sweep recovers it with no action needed ([Sweeps](../../reference/sweeps.md)).

**3. For a whole batch captured key-less,** re-catalog each citekey the same way. Each enqueues its own card and the Librarian processes them one at a time.

## Verify

- `catalog/papers/<citekey>.md` now has a populated `_enrichment` block and a `[!brief]` read
- `research_area` (and `methodology` where derivable) is applied, or one Inbox `flag` explains a genuine ambiguity — not silence
- `system/logs/classify.jsonl` shows an `applied` or `flagged` decision for the citekey, not a no-op

## If enrichment is still empty after re-ingest

- **The key didn't propagate.** Re-check `grep OPENALEX_API_KEY ~/.hermes/profiles/memoria-librarian/.env`; if absent, the redeploy didn't run against the right vault — re-run `--profiles-only --vault <vault>`.
- **The paper genuinely resolves no OpenAlex topics.** Some preprints and non-indexed works have no topics; classification staying unset is then correct, not a bug — tag `research_area` by hand.
- **Other enrichment sources also empty.** If Semantic Scholar / Crossref / PubMed fields are blank too, this is a broader network or `.bib` problem, not the OpenAlex key — see [Failure modes](../../reference/failure-modes.md).

## Related

- The enrichment and classify stages: [Ingest routing](../../reference/ingest.md)
- The re-ingest backstops: [Sweeps](../../reference/sweeps.md)
- Where the keys live: [Set up Hermes](../setup/set-up-hermes.md), [External integrations](../../reference/integrations.md)
- Full failure-modes catalog: [Failure modes](../../reference/failure-modes.md)


---

<!-- source: how-to-guides/troubleshooting/fix-missing-query-results.md -->

# Fix missing query results

**Symptom:** a Dataview or Bases view that filters on `methodology`, `research_area`, or claim `topics` returns nothing — or quietly omits notes you *know* should match. The notes are fine in every other way: they open cleanly, show no YAML error, and appear in unfiltered queries.

- A `WHERE methodology = "..."` (or a Base filter on the field) returns fewer notes than exist
- A dashboard or hub view is emptier than the vault warrants
- The "missing" notes are valid and visible everywhere except the filtered view

**Diagnosis:** the field value doesn't match the controlled vocabulary *exactly*. Dataview and Bases compare strings literally, so a near-miss term (`RCT` for `randomized-controlled-trial`, `field study` for `field-study`, a stray capital, a plural) silently drops the note from the filtered result. Nothing errors — the value is well-formed YAML, just off-vocabulary. This is term drift, and it fails silently by design ([Vocabulary discipline](../../explanation/knowledge/vocabulary-discipline.md)).

**Fix:** find the off-vocabulary values, then either correct the note to the exact controlled term or add the term to the vocabulary if it's genuinely new.

## First, rule out the two look-alike cases

This recipe is specifically for *structured* queries (Dataview / Bases filtering on a vocabulary field). Two different problems look similar:

| If… | It's not this — see |
| --- | --- |
| The note shows a YAML parse error, or is missing from **un**filtered queries too | [Fix broken frontmatter](fix-broken-frontmatter.md) |
| The **Co-PI** or semantic search misses notes (not a Dataview/Bases filter) | [Rebuild the search index](../operate/rebuild-the-search-index.md) |

If the note appears in an unfiltered query but vanishes the moment you filter on a vocabulary field, you're in the right place.

## Detect

**1. List every value actually in use for the field.** Drop this into a scratch note — it surfaces the drift at a glance by grouping notes under each distinct value:

```dataview
TABLE rows.file.link AS Notes
FROM "notes" OR "catalog"
FLATTEN methodology AS value
GROUP BY value
```

Swap `methodology` for `research_area` or `topics` as needed.

**2. Compare the list against the controlled vocabulary.** Every value in the output should appear verbatim in [Vocabulary](../../reference/vocabulary.md) (the live list is `system/vocabulary.md`). Any value that *doesn't* — a variant spelling, wrong case, a space where there should be a hyphen, a term not in the list at all — is an offender, and the notes grouped under it are your missing notes.

## Fix

**1. Correct the note to the exact term.** Open each offending note and set the field to the controlled value exactly — kebab-case, exact spelling, scalar vs list as the schema requires ([Frontmatter fields](../../reference/frontmatter.md)). The note re-appears in the view within a few seconds (Dataview re-indexes on save).

**2. Or add the term to the vocabulary** — if the value is a legitimate concept the vocabulary simply lacks. Don't scatter one-off variants; promote it once, properly: [Manage vocabulary](../knowledge/manage-vocabulary.md). Then bring any existing variants into line with the new canonical term.

## Verify

- The original query now returns the previously-missing notes
- Re-running the distinct-values query shows **only** controlled-vocabulary terms — no stragglers
- The dashboard or hub view that prompted this is no longer suspiciously empty

## If the fix doesn't hold

- **Case or whitespace.** `Field-Study` ≠ `field-study`; a trailing space defeats an exact match. Retype the value rather than edit in place.
- **Scalar vs list.** A field the schema expects as a list (`methodology: [field-study]`) won't match a scalar query and vice-versa — match the shape the query uses.
- **Wrong field.** Claim subject tags live in `topics`, not `research_area`; querying the wrong field returns nothing even when every value is valid.
- **Stale Dataview cache.** If a corrected note still won't show, force a re-index (toggle the file, or reload Obsidian) — Dataview occasionally lags a rename.

## Related

- The controlled values: [Vocabulary](../../reference/vocabulary.md)
- Why the vocabulary is kept tight and how drift fails silently: [Vocabulary discipline](../../explanation/knowledge/vocabulary-discipline.md)
- Adding or consolidating a term: [Manage vocabulary](../knowledge/manage-vocabulary.md)
- The YAML-error look-alike: [Fix broken frontmatter](fix-broken-frontmatter.md)
- Full failure-modes catalog: [Failure modes](../../reference/failure-modes.md)


---

<!-- source: how-to-guides/zotero/README.md -->

# Zotero

Everything Zotero in one place — the optional reference-manager backbone
([ADR-05](../../adr/05-zotero-as-bibliographic-backbone.md)).

| Guide | When |
| --- | --- |
| [Set up Zotero](set-up-zotero.md) | Install Zotero + Better BibTeX and wire the auto-export. |
| [Fix a stale .bib](fix-stale-bib.md) | Captures resolve to the wrong/missing citekey. |


---

<!-- source: how-to-guides/zotero/set-up-zotero.md -->

# Set up Zotero

Configure Zotero with Better BibTeX and wire up the automatic export so Memoria's Librarian always has an up-to-date `.bib` file to read from.

## Prerequisites

- Zotero 9 installed ([zotero.org](https://www.zotero.org/download/))
- Better BibTeX plugin installed in Zotero ([retorque.re/zotero-better-bibtex/](https://retorque.re/zotero-better-bibtex/))
- The vault cloned ([Set up the vault](../setup/set-up-the-vault.md))

## Steps

**1. Open Better BibTeX preferences.**

In Zotero 9: Tools → Better BibTeX Preferences.

**2. Set the citation key formula.**

Citation Keys tab → Citation key formula:

```text
[auth.lower][year][shorttitle1_0]
```

This produces keys in the `mamykina2010sense` shape — lowercase author, year, and the first significant title word (`shorttitle(1,0)`) — which is the format Memoria's vault file names, frontmatter, and Dataview queries all expect. This matches the canonical formula in [ADR-6](../../adr/06-citekey-naming-convention.md) (`auth.lower + year + shorttitle(1,0)`); do not substitute `condense:N`, which takes a fixed character count rather than the first whole word and yields a different key.

**3. Enable automatic export.**

Automatic Export tab → Add Automatic Export:

- **Format:** Better BibLaTeX
- **Path:** the absolute path to `.memoria/memoria.bib` inside your vault, e.g.:
  `C:\Users\{USERNAME}\memoria-vault\vault\.memoria\memoria.bib`
- **Export notes:** off
- **Use Journal Abbreviations:** off
- **On change:** Automatic (exports whenever Zotero's library changes)

**4. Pin citekeys for existing items.**

For any item already in Zotero whose citekey might change if the formula is applied retroactively: right-click the item → Better BibTeX → Pin BibTeX key. Pinned keys are stable even if author names, year, or title are corrected later.

**5. Pin the key for every new item immediately after adding it.**

Better BibTeX keys are **dynamic by default** — a generated key can change when you later correct an item's author, year, or title, silently breaking any note or `.bib` reference already using the old key. Pin each new item right after adding it: right-click → Better BibTeX → Pin BibTeX key. The lock icon in Zotero's item list confirms it. (This is the recurring discipline behind [Fix a stale `.bib`](fix-stale-bib.md).)

**6. Verify the export ran.**

After adding one item and pinning its key, check that the `.bib` file was written:

```powershell
Get-Item vault\.memoria\memoria.bib | Select-Object LastWriteTime
```

The timestamp should be recent. Open the file and confirm the new citekey appears in an `@article{mamykina2010sense,` block (substituting your actual citekey).

## Verify

- `vault/.memoria/memoria.bib` exists and contains your item's entry.
- The citekey in `.bib` matches the `mamykina2010sense` shape.
- The key is pinned (shown with a lock icon in Zotero's item list, and `extra: bibtex: mamykina2010sense` in the item's Extra field).

## Enable the local API (for the `pyzotero` MCP)

The Librarian and Peer-reviewer resolve citekeys and item metadata through the read-only **`pyzotero` MCP**, which talks to Zotero's **local desktop API** — no Web API key, no cloud, no write access. Zotero exposes this at `http://localhost:23119` while it's running (Zotero 9; if it isn't already on, enable local API access under **Settings → Advanced**).

- Zotero must be **running** for the MCP to reach it.
- The MCP itself is installed during [Set up Hermes](../setup/set-up-hermes.md) (`python -m pip install --user zotero-mcp`).
- It is **read-only** — Memoria reads from Zotero but never writes back to it.

## Close the loop: install MarkDB-Connect (recommended)

MarkDB-Connect is a Zotero plugin (not an Obsidian plugin). It scans your vault, finds notes that contain a citekey, and tags the corresponding Zotero item — so you can see at a glance which items have notes and jump from Zotero directly to the vault note.

**a. Install MarkDB-Connect in Zotero.**

Download from the [MarkDB-Connect releases page](https://github.com/daeh/zotero-markdb-connect/releases) (`.xpi` file) → Zotero → Tools → Add-ons → gear icon → Install Add-on From File.

**b. Configure the note folder.**

After install: Tools → MarkDB-Connect Settings → set the **note folder path** to your vault's `catalog/papers/` absolute path (e.g., `C:\Users\{USERNAME}\Memoria\catalog\papers`).

MarkDB-Connect detects citekeys from the note filename by default, which matches Memoria's naming convention (`mamykina2010sense.md` → citekey `mamykina2010sense`).

**c. Run the initial sync.**

Tools → MarkDB-Connect Sync Tags. Zotero items with matching vault notes get an `ObsCite` tag (shown as a colored dot in the library). Right-click any tagged item → Open in Obsidian to jump to the note.

Re-run the sync periodically (or after ingesting a batch) to keep the tags current. It is not automatic.

## API keys for enrichment (optional but recommended)

Enrichment during ingest calls OpenAlex, Semantic Scholar, and PubMed. Without keys these calls either fail or are rate-limited. Register a free key for each service now; you'll add them to the Librarian's `.env` in [Set up Hermes](../setup/set-up-hermes.md).

For each service's registration URL and the with-/without-key rate limits, see [External integrations → API keys and rate limits](../../reference/integrations.md#api-keys-and-rate-limits).

## Related

- Next step: [Set up Hermes](../setup/set-up-hermes.md)
- What ingest does with the `.bib`: [Capture and ingest a source](../library/capture-and-ingest.md)
- Fixing a stale `.bib`: [Fix a stale .bib](fix-stale-bib.md)
- Citekey naming convention: [ADR-6](../../adr/06-citekey-naming-convention.md)


---

<!-- source: how-to-guides/zotero/fix-stale-bib.md -->

# Fix a stale .bib

**Symptom:** a capture card fails at ingest with `"citekey not found"` or `"not in memoria.bib"` — the candidate never lands, and the failure surfaces on the card or in the Librarian's session log.

**Diagnosis:** the citekey is missing from `memoria.bib` — either Zotero's auto-export hasn't run, or the Hermes node hasn't pulled the latest `.bib`. Confirm with a `grep` before reaching for a fix.

**Fix:** re-export from Zotero, pull on the agent node, or commit and push the file — whichever step is missing.

## Detect

Confirm the citekey is missing from the file:

```bash
grep <citekey> vault/.memoria/memoria.bib
```

If this returns nothing, the `.bib` is stale. If it returns the entry, the issue is something else — check the session logs.

## Fix

**Option A — Trigger auto-export from Zotero** (preferred).

In Zotero: File → Export Library → Better BibLaTeX → overwrite `vault/.memoria/memoria.bib`. Or make any change to the Zotero library (add/remove a tag) to trigger the auto-export.

**Option B — Force a git pull on the agent node** (if using a remote/VPS setup).

```bash
git pull --ff-only   # run on the node where Hermes runs
grep <citekey> vault/.memoria/memoria.bib   # confirm entry is now present
```

**Option C — Commit and push manually from Windows** (if auto-export ran but the file wasn't committed).

```bash
git add vault/.memoria/memoria.bib
git commit -m "manual: bib update"
git push
```

Then pull on the agent node (Option B).

## Verify

```bash
grep <citekey> vault/.memoria/memoria.bib        # entry present
git log --oneline vault/.memoria/memoria.bib | head -3   # recent commit timestamp
```

Then retry the ingest — re-run the capture (`Cmd/Ctrl-P` → **Memoria: capture from Zotero selection** with the item selected), or enqueue the card from the terminal:

```bash
hermes kanban create "Ingest <citekey>" --assignee memoria-librarian
```

The Librarian's run should now complete without a "not found" error and raise the candidate card in `inbox/`.

## Prevent recurrence

- Confirm Zotero's auto-export is set to "Automatic (on change)" in Better BibTeX preferences
- Confirm the export path is the absolute path to `vault/.memoria/memoria.bib`
- Pin every citekey immediately after adding to Zotero — unpinned keys can change and create false "not found" errors

## Related

- Zotero setup: [Set up Zotero](set-up-zotero.md)
- Full failure-modes catalog: [Failure modes](../../reference/failure-modes.md)


---

<!-- source: reference/README.md -->

# Reference

Lookup material for Memoria — fields, values, commands, schemas, folder paths. For design rationale and conceptual explanations, see [Explanation](../explanation).

The files are grouped below by domain for scanning; the folder itself is flat.

## Vault data model

| File | What it covers |
| --- | --- |
| [Frontmatter fields](frontmatter.md) | Every YAML frontmatter field: type, allowed values, owner, namespace |
| [Inbox card fields](inbox-card-fields.md) | Field-level contract for candidate, gap, flag, alert, and work-prompt cards |
| [Document types](document-types.md) | The 25 document types: folder, template, lifecycle, promotion map |
| [Vocabulary](vocabulary.md) | Controlled values for `research_area`, `methodology`, and claim `topics` |
| [Wikilink and link conventions](linking.md) | Wikilink conventions, authored-link vocabulary, hub thresholds |
| [Kanban board reference](kanban-board.md) | Kanban state machine, card schema, review overlay, WIP limits |
| [Glossary](glossary.md) | Term definitions, alphabetical |

## Agents and control

| File | What it covers |
| --- | --- |
| [System actions](system-actions.md) | Every action the system performs — operations, MCP servers, crons, the 27 skills, PI palette — with performer and purpose |
| [Operations](operations.md) | Deterministic operation entry points, facades, direct callers, and responsibilities |
| [Project structural impact](project-structural-impact.md) | Project-gate structural-impact command, generated index payload, and write behavior |
| [Worklists](worklists.md) | Batch worklist report JSON, emitted item notes, and aggregate review prompt contract |
| [Profile capabilities](profiles.md) | Lane identifiers, capability table, invocation levels, folder permissions |
| [Linter: detectors and auto-fix](linter.md) | Linter structural detectors, auto-fix classes, and severity scale |
| [Vault eval](vault-eval.md) | The vault-eval gold set, the quarterly dispatch, idempotency keys, and the eval-task schema |
| [Obsidian command palette](obsidian-command-palette.md) | Obsidian `Memoria:` command-palette entries (the in-Obsidian UI surface) |
| [Hermes CLI](hermes-cli.md) | All `hermes …` CLI commands: per-profile research, board management, profile/skills/cron admin |
| [Policy MCP](policy-mcp.md) | Policy MCP: decision values, request/response contract, tools, lane overrides, and enforcement |
| [Policy audit log](policy-audit-log.md) | Audit-log fields, JSON example, decision enum, and per-write hash pairing |
| [Policy auto-fix](policy-auto-fix.md) | Auto-fix classes and dispositions enforced by the policy gate |
| [Retrieval and analysis methods](computational-toolbox.md) | Deterministic and hybrid methods: embeddings, classifiers, clustering, NLI, graph algorithms |
| [Calibration](calibration.md) | Drift-bound threshold contracts and shadow-first score calibration |
| [Dashboards](dashboards.md) | The three space dashboards plus the Inbox queue, Maintenance collection, support dashboards, and Bases views: source file, sort order, verdict band, trust score, eval metrics, rail badges |
| [Pattern library](patterns.md) | The shipped patterns, the pattern-note schema, the `patterns_list`/`patterns_run` contract, gated-target dry-run, and provenance |
| [Clustering](clustering.md) | The cluster MCP: graph build, claim-debate Canvas, BERTopic topics — parameters, outputs, and the opt-in stack |

## Pipelines and I/O

| File | What it covers |
| --- | --- |
| [Ingest routing](ingest.md) | Type detection dispatch, per-type enrichment, frontmatter written at ingest |
| [Sweeps](sweeps.md) | Re-ingest and retraction maintenance passes |
| [Search](search.md) | The qmd retrieval surface: hybrid BM25 + vector + rerank, the MCP, consumers, the index, and limits |
| [Export routes and formats](export.md) | Citation states, export routes, editor comparison, deliverable targets |
| [Memory substrates](memory.md) | Memory substrate table, audit log schema, retention (append-only forever) |
| [Telemetry & logs](telemetry.md) | Operational log inventory, JSONL conventions, cadence, and join keys |
| [Telemetry log schemas](telemetry-logs.md) | Exact JSONL schemas and derived metric-note contracts |
| [Board export](board-export.md) | Hermes Kanban projection command, generated board files, event logs, and cost-join failure modes |
| [Fleet metrics](fleet-metrics.md) | Weekly lane metrics, trust-score formula, inputs, bands, and low-confidence behavior |
| [Diagnostics](diagnostics.md) | Local diagnostics location, redaction, raw-capture, and support-bundle contract |

## System and infrastructure

| File | What it covers |
| --- | --- |
| [External integrations](integrations.md) | External APIs and tools: enrichment, entity resolution, vault access, execution layer |
| [Memoria configuration](configuration.md) | Configuration surfaces, source/installed ownership, redeploy triggers, and secret boundaries |
| [On-disk layout](on-disk-layout.md) | Vault folder tree, `.memoria/` layout, skeleton notes, naming conventions |
| [System artifacts](system-artifacts.md) | Visible `system/` files, eval fixtures, and shipped Bases views |
| [Installer (bootstrap)](installer.md) | Bootstrap installer: platform matrix, install flow, component checklist, secrets and skills tables |
| [Failure modes](failure-modes.md) | All failure modes by severity: symptom, cause, fix |
| [Bibliography](bibliography.md) | Works cited across the docs, in ACM author-date style; in-text citations link here |

## Obsidian

| File | What it covers |
| --- | --- |
| [Obsidian plugins](obsidian-plugins.md) | Obsidian plugin inventory, install status, and evaluated alternatives |
| [Obsidian plugin settings](obsidian-plugin-settings.md) | Load-bearing per-plugin settings |
| [Obsidian plugin data files](obsidian-plugin-data-files.md) | `data.json`, `.example`, generated, and secret-bearing config conventions |
| [Zotero plugins](zotero-plugins.md) | Zotero add-ons and the Zotero↔Obsidian connector comparison |
| [Obsidian callouts](obsidian-callouts.md) | Callout type identifiers, trigger conditions, and field schema |
| [Obsidian workspaces](obsidian-workspaces.md) | The Memoria reset layout and the navigation-rail space-switching model |


---

<!-- source: reference/bibliography.md -->

# Bibliography

Works cited across the Memoria documentation. Formatted in ACM author-date style. In-text citations elsewhere in the docs (e.g. "Chen et al. 2026") link here.

Entries are alphabetical by first author. Classic sources (Bush, Luhmann, Matuschak, Karpathy) appear first under *Foundational sources*; the contemporary AI-research systems follow under *AI-research systems*; pivotal works from the wider ~400-paper literature review follow under *Broader literature foundations*.

---

## Foundational sources

<a id="bush1945"></a>
Vannevar Bush. 1945. As We May Think. *The Atlantic Monthly* 176, 1 (July 1945), 101–108. Retrieved from https://www.theatlantic.com/magazine/archive/1945/07/as-we-may-think/303881/

<a id="karpathy-llm-wiki"></a>
Andrej Karpathy. 2025. On the LLM-as-compiler / persistent-wiki pattern. Public remarks and posts. Retrieved from https://x.com/karpathy

<a id="luhmann-zettelkasten"></a>
Niklas Luhmann. 1992. Communicating with Slip Boxes: An Empirical Account. In *Universität als Milieu: Kleine Schriften* (André Kieserling, Ed.). Haux, Bielefeld, 53–61. (Original work on the Zettelkasten method.)

<a id="matuschak-evergreen"></a>
Andy Matuschak. 2019. Evergreen notes. Retrieved from https://notes.andymatuschak.org/Evergreen_notes

---

## AI-research systems

<a id="ajith2024litsearch"></a>
Anirudh Ajith, Mengzhou Xia, Alexis Chevalier, Tanya Goyal, Danqi Chen, and Tianyu Gao. 2024. LitSearch: A Retrieval Benchmark for Scientific Literature Search. arXiv:2407.18940. Retrieved from https://arxiv.org/abs/2407.18940

<a id="bisht2026agentic"></a>
Harshit Bisht, Vinay Kumar, Kevin Maik Jablonka, Mausam, and N. M. Anoop Krishnan. 2026. Agentic AI Scientists Are Not Built for Autonomous Scientific Discovery. arXiv:2605.08956. Retrieved from https://arxiv.org/abs/2605.08956

<a id="chen2026copilots"></a>
Deli Chen. 2026. From Copilots to Colleagues: A Survey of Autonomous Research Agents. Self-published. Retrieved from https://victorchen96.github.io/auto_research_survey.pdf. A survey of ~95 papers across machine learning, software engineering, and scientific discovery; proposes the L1–L5 autonomy taxonomy (L1 code-autocomplete → L5 fully self-directed) and identifies persistent knowledge accumulation as a primary barrier to L5 autonomy.

<a id="chen2026autonomous"></a>
Guoxin Chen, Jie Chen, Lei Chen, Jiale Zhao, Fanzhe Meng, Wayne Xin Zhao, Ruihua Song, Cheng Chen, Ji-Rong Wen, and Kai Jia. 2026. Toward Autonomous Long-Horizon Engineering for ML Research. arXiv:2604.13018. Retrieved from https://arxiv.org/abs/2604.13018

<a id="aideml"></a>
Weco AI. 2026. AIDE: AI-Driven Exploration in the Space of Code (aideml). Software. Retrieved from https://github.com/WecoAI/aideml

<a id="idea2paper"></a>
AgentAlphaAGI. 2026. Idea2Paper. Software. Retrieved from https://github.com/AgentAlphaAGI/Idea2Paper

<a id="feng2026visionary"></a>
Yebo Feng and Yang Liu. 2026. A Visionary Look at Vibe Researching. arXiv:2604.00945. Retrieved from https://arxiv.org/abs/2604.00945

<a id="gottweis2025aicoscientist"></a>
Juraj Gottweis, Wei-Hung Weng, Alexander Daryin, Tao Tu, Anil Palepu, Petar Sirkovic, Artiom Myaskovsky, et al. 2025. Towards an AI Co-Scientist. arXiv:2502.18864. Retrieved from https://arxiv.org/abs/2502.18864

<a id="gridach2025agentic"></a>
Mourad Gridach, Jay Nanavati, Khaldoun Zine El Abidine, Lenon Mendes, and Christina Mack. 2025. Agentic AI for Scientific Discovery: A Survey of Progress, Challenges, and Future Directions. arXiv:2503.08979. Retrieved from https://arxiv.org/abs/2503.08979

<a id="huang2025deepresearch"></a>
Yuxuan Huang, Yihang Chen, Haozheng Zhang, Kang Li, Huichi Zhou, Meng Fang, Linyi Yang, et al. 2025. Deep Research Agents: A Systematic Examination and Roadmap. arXiv:2506.18096. Retrieved from https://arxiv.org/abs/2506.18096

<a id="hong2024metagpt"></a>
Sirui Hong, Mingchen Zhuge, Jiaqi Chen, Xiawu Zheng, Yuheng Cheng, Ceyao Zhang, Jinlin Wang, et al. 2024. MetaGPT: Meta Programming for a Multi-Agent Collaborative Framework. arXiv:2308.00352. Retrieved from https://arxiv.org/abs/2308.00352

<a id="kang2024researcharena"></a>
Hao Kang and Chenyan Xiong. 2024. ResearchArena: Benchmarking Large Language Models' Ability to Collect and Organize Information as Research Agents. arXiv:2406.10291. Retrieved from https://arxiv.org/abs/2406.10291

<a id="li2025mlrcopilot"></a>
Ruochen Li, Teerth Patel, Qingyun Wang, and Xinya Du. 2025. MLR-Copilot: Autonomous Machine Learning Research Based on Large Language Models Agents. arXiv:2408.14033. Retrieved from https://arxiv.org/abs/2408.14033

<a id="liu2026autoresearchclaw"></a>
Jiaqi Liu, Shi Qiu, Mairui Li, Bingzhou Li, Haonian Ji, Siwei Han, Xinyu Ye, et al. 2026. AutoResearchClaw: Self-Reinforcing Autonomous Research with Human-AI Collaboration. arXiv:2605.20025. Retrieved from https://arxiv.org/abs/2605.20025

<a id="lu2024aiscientist"></a>
Chris Lu, Cong Lu, Robert Tjarko Lange, Jakob Foerster, Jeff Clune, and David Ha. 2024. The AI Scientist: Towards Fully Automated Open-Ended Scientific Discovery. arXiv:2408.06292. Retrieved from https://arxiv.org/abs/2408.06292

<a id="long2026aisupervisor"></a>
Yunbo Long. 2026. AI-Supervisor: Autonomous AI Research Supervision via a Persistent Research World Model. arXiv:2603.24402. Retrieved from https://arxiv.org/abs/2603.24402

<a id="meng2026scientistone"></a>
Rui Meng, Bhavana Dalvi Mishra, Jiefeng Chen, Chun-Liang Li, Palash Goyal, Mihir Parmar, Yiwen Song, et al. 2026. ScientistOne: Towards Human-Level Autonomous Research via Chain-of-Evidence. arXiv:2605.26340. Retrieved from https://arxiv.org/abs/2605.26340

<a id="qi2023hypothesis"></a>
Biqing Qi, Kaiyan Zhang, Haoxiang Li, Kai Tian, Sihang Zeng, Zhang-Ren Chen, and Bowen Zhou. 2023. Large Language Models Are Zero Shot Hypothesis Proposers. arXiv:2311.05965. Retrieved from https://arxiv.org/abs/2311.05965

<a id="qian2026omegawiki"></a>
Weitong Qian. 2026. OmegaWiki. Software. Retrieved from https://github.com/skyllwt/OmegaWiki

<a id="qu2026coral"></a>
Ao Qu, Han Zheng, Zijian Zhou, Yihao Yan, Yihong Tang, Shao Yong Ong, Fenglu Hong, et al. 2026. CORAL: Towards Autonomous Multi-Agent Evolution for Open-Ended Discovery. arXiv:2604.01658. Retrieved from https://arxiv.org/abs/2604.01658

<a id="press2024citeme"></a>
Ori Press, Andreas Hochlehnert, Ameya Prabhu, Vishaal Udandarao, Ofir Press, and Matthias Bethge. 2024. CiteME: Can Language Models Accurately Cite Scientific Claims? arXiv:2407.12861. Retrieved from https://arxiv.org/abs/2407.12861

<a id="li2025scilitllm"></a>
Sihang Li, Jin Huang, Jiaxi Zhuang, Yaorui Shi, Xiaochen Cai, Mingjun Xu, Xiang Wang, Linfeng Zhang, Guolin Ke, and Hengxing Cai. 2025. SciLitLLM: How to Adapt LLMs for Scientific Literature Understanding. arXiv:2408.15545. Retrieved from https://arxiv.org/abs/2408.15545

<a id="schmidgall2025agentlaboratory"></a>
Samuel Schmidgall, Yusheng Su, Ze Wang, Ximeng Sun, Jialian Wu, Xiaodong Yu, Jiang Liu, Michael Moor, Zicheng Liu, and Emad Barsoum. 2025. Agent Laboratory: Using LLM Agents as Research Assistants. arXiv:2501.04227. Retrieved from https://arxiv.org/abs/2501.04227

<a id="ren2025scientific"></a>
Shuo Ren, Can Xie, Pu Jian, Zhenjiang Ren, Chunlin Leng, and Jiajun Zhang. 2025. Towards Scientific Intelligence: A Survey of LLM-based Scientific Agents. arXiv:2503.24047. Retrieved from https://arxiv.org/abs/2503.24047

<a id="rouzrokh2026lattereview"></a>
Pouria Rouzrokh. 2026. LatteReview. Software. Retrieved from https://github.com/PouriaRouzrokh/LatteReview

<a id="schmidgall2025agentrxiv"></a>
Samuel Schmidgall and Michael Moor. 2025. AgentRxiv: Towards Collaborative Autonomous Research. arXiv:2503.18102. Retrieved from https://arxiv.org/abs/2503.18102

<a id="wang2024scimon"></a>
Qingyun Wang, Doug Downey, Heng Ji, and Tom Hope. 2024. SciMON: Scientific Inspiration Machines Optimized for Novelty. In *Proceedings of the 62nd Annual Meeting of the Association for Computational Linguistics (Volume 1: Long Papers)*. 279–299. https://doi.org/10.18653/v1/2024.acl-long.18

<a id="wang2025openhands"></a>
Xingyao Wang, Boxuan Li, Yufan Song, Frank F. Xu, Xiangru Tang, Mingchen Zhuge, Jiayi Pan, et al. 2025. OpenHands: An Open Platform for AI Software Developers as Generalist Agents. arXiv:2407.16741. Retrieved from https://arxiv.org/abs/2407.16741

<a id="wang2026parness"></a>
Yuchen Wang and Zhongzhi Luan. 2026. PARNESS: A Paper Harness for End-to-End Automated Scientific Research with Dynamic Workflows, Full-Text Indexing, and Cross-Run Knowledge Accumulation. arXiv:2605.05258. Retrieved from https://arxiv.org/abs/2605.05258

<a id="wang2026sibyl"></a>
Chengcheng Wang, Qinhua Xie, Wei He, Jianyuan Guo, Shiqi Wang, and Chang Xu. 2026. Sibyl-AutoResearch: Autonomous Research Needs Self-Evolving Trial-and-Error Harnesses, Not Paper Generators. arXiv:2605.22343. Retrieved from https://arxiv.org/abs/2605.22343

<a id="weng2025cycleresearcher"></a>
Yixuan Weng, Minjun Zhu, Guangsheng Bao, Hongbo Zhang, Jindong Wang, Yue Zhang, and Linyi Yang. 2025. CycleResearcher: Improving Automated Research via Automated Review. arXiv:2411.00816. Retrieved from https://arxiv.org/abs/2411.00816

<a id="wu2023autogen"></a>
Qingyun Wu, Gagan Bansal, Jieyu Zhang, Yiran Wu, Beibin Li, Erkang Zhu, Li Jiang, et al. 2023. AutoGen: Enabling Next-Gen LLM Applications via Multi-Agent Conversation. arXiv:2308.08155. Retrieved from https://arxiv.org/abs/2308.08155

<a id="xiong2026autoresearchbench"></a>
Lei Xiong, Kun Luo, Ziyi Xia, Wenbo Zhang, Jin-Ge Yao, Zheng Liu, Jingying Shao, et al. 2026. AutoResearchBench: Benchmarking AI Agents on Complex Scientific Literature Discovery. arXiv:2604.25256. Retrieved from https://arxiv.org/abs/2604.25256

<a id="xu2025deepresearch"></a>
Renjun Xu and Jingwen Peng. 2025. A Comprehensive Survey of Deep Research: Systems, Methodologies, and Applications. arXiv:2506.12594. Retrieved from https://arxiv.org/abs/2506.12594

<a id="xu2026nanoresearch"></a>
Jinhang Xu, Qiyuan Zhu, Yujun Wu, Zirui Wang, Dongxu Zhang, Marcia Tian, Yiling Duan, et al. 2026. NanoResearch: Co-evolving Skills, Memory, and Policy for Personalized Research Automation. arXiv:2605.10813. Retrieved from https://arxiv.org/abs/2605.10813

<a id="yamada2025aiscientistv2"></a>
Yutaro Yamada, Robert Tjarko Lange, Cong Lu, Shengran Hu, Chris Lu, Jakob Foerster, Jeff Clune, and David Ha. 2025. The AI Scientist-v2: Workshop-Level Automated Scientific Discovery via Agentic Tree Search. arXiv:2504.08066. Retrieved from https://arxiv.org/abs/2504.08066

<a id="yang2026moose"></a>
Zonglin Yang et al. 2024. Large Language Models for Automated Open-Domain Scientific Hypotheses Discovery (MOOSE). In *Findings of the Association for Computational Linguistics: ACL 2024*. Software retrieved from https://github.com/ZonglinY/MOOSE

<a id="yu2026knows"></a>
Guangsheng Yu and Xu Wang. 2026. Knows: Agent-Native Structured Research Representations. arXiv:2604.17309. Retrieved from https://arxiv.org/abs/2604.17309

<a id="yue2026mcpnative"></a>
Ling Yue, Ching-Yun Ko, Pin-Yu Chen, Shimin Di, and Shaowu Pan. 2026. Building MCP-native Hierarchical AI Scientist Ecosystems: A Perspective on Scaling Multi-Agent Scientific Discovery. Preprints 202507.1951. https://doi.org/10.20944/preprints202507.1951.v2

<a id="zhang2024massw"></a>
Xingjian Zhang, Yutong Xie, Jin Huang, Jinge Ma, Zhaoying Pan, Qijia Liu, Ziyang Xiong, Tolga Ergen, Dongsub Shim, Honglak Lee, and Qiaozhu Mei. 2024. MASSW: A New Dataset and Benchmark Tasks for AI-assisted Scientific Workflows. arXiv:2406.06357. Retrieved from https://arxiv.org/abs/2406.06357

<a id="zhang2026howfar"></a>
Zhengxin Zhang, Ning Wang, Sainyam Galhotra, and Claire Cardie. 2026. How Far Are We from True Auto-Research? arXiv:2605.19156. Retrieved from https://arxiv.org/abs/2605.19156

---

## Broader literature foundations

Pivotal works from the wider literature review — ~400 papers read end-to-end and judged adopt/borrow/reject for the design (`_papers/`, reviewed 2026-06; the working corpus is the Zotero export `_papers/Exported Items.bib`). These ground the cross-cutting choices cited in [Pattern provenance: borrow, adapt, ignore](../explanation/rationale/why-pattern-provenance.md) and [Intellectual foundations](../explanation/overview/intellectual-foundations.md): the HCI human-augmentation tradition behind the review gate, generator–verifier and evidence-grounded verification, temporal retrieval, and the indirect-prompt-injection case for the MCP sandbox.

<a id="abdallah2026tempo"></a>
Abdelrahman Abdallah, Mohammed Ali, Muhammad Abdul-Mageed, and Adam Jatowt. 2026. TEMPO: A Realistic Multi-Domain Benchmark for Temporal Reasoning-Intensive Retrieval. arXiv:2601.09523. Retrieved from https://arxiv.org/abs/2601.09523

<a id="ackerman2000cscw"></a>
Mark S. Ackerman. 2000. The Intellectual Challenge of CSCW: The Gap Between Social Requirements and Technical Feasibility. *Human–Computer Interaction* 15, 2–3 (Sept. 2000), 179–203. https://doi.org/10.1207/S15327051HCI1523_5

<a id="amershi2019guidelines"></a>
Saleema Amershi, Dan Weld, Mihaela Vorvoreanu, Adam Fourney, Besmira Nushi, Penny Collisson, Jina Suh, Shamsi Iqbal, Paul N. Bennett, Kori Inkpen, Jaime Teevan, Ruth Kikin-Gil, and Eric Horvitz. 2019. Guidelines for Human-AI Interaction. In *Proceedings of the 2019 CHI Conference on Human Factors in Computing Systems*. ACM, 1–13. https://doi.org/10.1145/3290605.3300233

<a id="bender2021parrots"></a>
Emily M. Bender, Timnit Gebru, Angelina McMillan-Major, and Shmargaret Shmitchell. 2021. On the Dangers of Stochastic Parrots: Can Language Models Be Too Big? In *Proceedings of the 2021 ACM Conference on Fairness, Accountability, and Transparency (FAccT '21)*. ACM, 610–623. https://doi.org/10.1145/3442188.3445922

<a id="bernstein2010soylent"></a>
Michael S. Bernstein, Greg Little, Robert C. Miller, Björn Hartmann, Mark S. Ackerman, David R. Karger, David Crowell, and Katrina Panovich. 2010. Soylent: A Word Processor with a Crowd Inside. In *Proceedings of the 23rd Annual ACM Symposium on User Interface Software and Technology (UIST '10)*. ACM, 313–322. https://doi.org/10.1145/1866029.1866078

<a id="cobbe2021verifiers"></a>
Karl Cobbe, Vineet Kosaraju, Mohammad Bavarian, Mark Chen, Heewoo Jun, Lukasz Kaiser, Matthias Plappert, Jerry Tworek, Jacob Hilton, Reiichiro Nakano, Christopher Hesse, and John Schulman. 2021. Training Verifiers to Solve Math Word Problems. arXiv:2110.14168. Retrieved from https://arxiv.org/abs/2110.14168

<a id="debenedetti2024agentdojo"></a>
Edoardo Debenedetti, Jie Zhang, Mislav Balunović, Luca Beurer-Kellner, Marc Fischer, and Florian Tramèr. 2024. AgentDojo: A Dynamic Environment to Evaluate Prompt Injection Attacks and Defenses for LLM Agents. arXiv:2406.13352. Retrieved from https://arxiv.org/abs/2406.13352

<a id="greshake2023injection"></a>
Kai Greshake, Sahar Abdelnabi, Shailesh Mishra, Christoph Endres, Thorsten Holz, and Mario Fritz. 2023. Not What You've Signed Up For: Compromising Real-World LLM-Integrated Applications with Indirect Prompt Injection. In *Proceedings of the 16th ACM Workshop on Artificial Intelligence and Security (AISec '23)*. ACM, 79–90. https://doi.org/10.1145/3605764.3623985

<a id="horvitz1999mixedinitiative"></a>
Eric Horvitz. 1999. Principles of Mixed-Initiative User Interfaces. In *Proceedings of the SIGCHI Conference on Human Factors in Computing Systems (CHI '99)*. ACM Press, 159–166. https://doi.org/10.1145/302979.303030

<a id="perez2022modelwritten"></a>
Ethan Perez, Sam Ringer, Kamilė Lukošiūtė, Karina Nguyen, Edwin Chen, Scott Heiner, Craig Pettit, Catherine Olsson, Sandipan Kundu, Saurav Kadavath, et al. 2022. Discovering Language Model Behaviors with Model-Written Evaluations. arXiv:2212.09251. Retrieved from https://arxiv.org/abs/2212.09251

<a id="thorne2018fever"></a>
James Thorne, Andreas Vlachos, Christos Christodoulopoulos, and Arpit Mittal. 2018. FEVER: A Large-Scale Dataset for Fact Extraction and VERification. arXiv:1803.05355. Retrieved from https://arxiv.org/abs/1803.05355

---

## Notes on this list

- **Coverage.** This list holds works *cited in the documentation*, not Memoria's full reading corpus (the working bibliography lives in Zotero / `notes/papers.md`). The wider literature reviewed for the design — ~400 papers — sits in `_papers/` (Zotero export `_papers/Exported Items.bib`), with synthesized adopt/borrow/reject verdicts in `_papers/REVIEW-SUMMARY.md`.
- **Preprints.** Most contemporary entries are arXiv preprints (`pubstate: prepublished`); the `arXiv:ID` is the stable identifier.

---

## Related

- Foundations that cite these works: [Intellectual foundations](../explanation/overview/intellectual-foundations.md)
- The pattern-provenance survey citing this list: [Pattern provenance: borrow, adapt, ignore](../explanation/rationale/why-pattern-provenance.md)


---

<!-- source: reference/board-export.md -->

# Board export

`src/.memoria/mcp/board_export.py` is the one-way projection from the Hermes Kanban database into vault files and telemetry logs. The Hermes board at `~/.hermes/kanban.db` remains authoritative; the exported files are consumer views for Obsidian dashboards, Dataview, metrics aggregation, and review prompts.

## Command

```bash
python src/.memoria/mcp/board_export.py --vault <vault>
python src/.memoria/mcp/board_export.py --vault <vault> --from-json cards.json
python src/.memoria/mcp/board_export.py --cost-doctor
```

| Option | Contract |
| --- | --- |
| `--vault <vault>` | Required unless `--cost-doctor` is used. Resolves the installed runtime vault root. |
| `--from-json <file>` | Test/offline mode. Reads a saved `hermes kanban list --json` payload instead of invoking Hermes. Cost lookup is skipped in this mode. |
| `--hermes-home <path>` | Overrides `$HERMES_HOME` / `~/.hermes` when joining completed cards to Hermes session rows. |
| `--cost-doctor` | Validates Hermes session-store cost capture and exits without exporting board files. |

Without `--from-json`, the exporter shells out to `hermes kanban list --json`. Completed-card cost rows also join through `hermes kanban show <id> --json` using `runs[].metadata.worker_session_id` and the per-profile Hermes `state.db` session table.

## Outputs

| Path | Shape |
| --- | --- |
| `system/board/<task_id>.md` | One markdown projection per live card for board-state dashboards. |
| `system/logs/board-state.jsonl` | Queue-depth snapshot, one row per export run. |
| `system/logs/board-transitions.jsonl` | Per-card status and review-state transitions derived from the previous export cache. |
| `system/logs/disposition.jsonl` | Review decisions: `accept`, `edit`, or `reject`. |
| `system/logs/cost.jsonl` | API spend and token counts per completed card when the Hermes session join succeeds. |
| `system/logs/cost-misses.jsonl` | Completed cards whose Hermes session/cost join could not be completed. |
| `system/logs/blind-review-samples.jsonl` | Deterministic sample requests for blind re-review. |
| `inbox/work-prompt-review-*.md` | One PI review prompt for a card that newly reaches `done`. |

`system/logs/.board-state-cache.json` stores the previous card snapshot. The exporter diffs the current board against that cache before saving the new cache, so transition logs are append-only while projected card markdown is refreshed.

## Failure modes

| Failure | Result |
| --- | --- |
| `hermes` is missing from `PATH` and no `--from-json` is provided | The command exits with an explanatory error. |
| `hermes kanban list --json` exits non-zero | The command exits and includes the Hermes stderr text. |
| Cost-capture schema validation fails | The command exits with `[board_export] cost doctor failed`. |
| A completed card cannot be joined to a Hermes session row | Export continues; the miss is written to `system/logs/cost-misses.jsonl`. |

## Related

- Board state machine and review overlay: [Kanban board reference](kanban-board.md)
- Log schemas consumed by the exporter and metrics: [Telemetry log schemas](telemetry-logs.md)
- Derived lane metrics: [Fleet metrics](fleet-metrics.md)


---

<!-- source: reference/calibration.md -->

# Calibration

`src/.memoria/schemas/calibration.yaml` is the source of truth for shared
thresholds. Every calibrated value follows the same discipline: grounded in real
Memoria data, bounded by an explicit error budget, recalibrated on drift, and
shadow-first before it affects routing or automation.

## Production Rule

A score may affect production behavior only when all of these are true:

- `production_enabled: true`
- the relevant threshold fields are non-null
- `grounding_dataset` names the reviewed dataset or log slice used to fit the
  thresholds
- `model_version` pins the model, scorer, or upstream source version whose scores
  were calibrated
- the sample-count and error-budget fields in that block are satisfied

If any threshold is `null`, the score is report-only. It may log shadow telemetry
or appear in a review surface, but it must not auto-accept, auto-defer, hide,
merge, block, or reorder canonical work.

## Existing Thresholds

| Block | Purpose | Production use |
| --- | --- | --- |
| `entity_resolution` | cross-source identity agreement floor | below the floor, ingest raises an Inbox near-tie flag instead of merging |
| `classify` | OpenAlex topic classification floor and near-tie margin | clear winners apply; near ties raise a review flag |
| `inbox` | resolved-card archival age | archival sweep moves old resolved cards out of active Inbox views |
| `clustering` | display defaults for graph/topic maps | layout/topic defaults only; not a canonical-write decision |

## Hybrid-Score Thresholds

#379 adds explicit threshold slots for the score families that are not yet
calibrated. They intentionally ship disabled and unfilled.

### `hybrid_scores.candidate_rank`

Future use: reorder or batch candidate review attention.

Grounding requirement: at least `min_labeled_decisions` real PI keep/archive/edit
decisions with the score recorded in shadow mode.

Error budget:

- `max_false_promote_rate`: promoted candidates that the PI later rejects or
  heavily edits
- `max_top_decile_miss_rate`: PI-kept candidates that the score failed to surface
  in the top decile

Production thresholds:

- `promote_threshold`
- `defer_threshold`

Both remain `null` until the grounding dataset meets the sample and error-budget
requirements.

### `hybrid_scores.outline_score`

Future use: prioritize or flag draft outlines for revision.

Grounding requirement: at least `min_labeled_outlines` real outlines with human
accepted/revised outcomes, collected in shadow mode.

Error budget:

- `max_false_accept_rate`: outlines scored as acceptable that the PI revises
  materially
- `max_false_revise_rate`: outlines flagged for revision that the PI accepts
  without material change

Production thresholds:

- `accept_threshold`
- `revise_threshold`

Both remain `null` until calibrated against the grounding dataset.

### `clustering.quality_thresholds`

Future use: decide whether a generated map or topic model is good enough to rank
or route downstream work.

Grounding requirement: at least `min_reviewed_maps` human-reviewed map/topic runs.

Error budget:

- `max_cluster_churn_rate`: maximum acceptable cluster membership churn across
  stable reruns or adjacent calibration windows

Production thresholds:

- `silhouette_floor`
- `topic_coherence_floor`

Both remain `null` until reviewed map runs establish useful values.

## Drift

Recalibrate any enabled block when the scoring model, embedding model, upstream
classification source, prompt, or feature extraction changes. Until recalibration
passes the same sample and error-budget checks, set `production_enabled: false`
and return the score to shadow mode.


---

<!-- source: reference/clustering.md -->

# Clustering

The cluster MCP (`src/.memoria/mcp/cluster_mcp.py`): three tools over the vault's **typed graph** and note text that drive the `map:*` lanes and the claim-debate canvas ([ADR-33](../adr/33-cluster-mcp-bertopic.md)). The operation decides *how to display*, never *what is canonical* — every result echoes its parameters, defaults come from `.memoria/schemas/calibration.yaml` (drift-bound — recalibrate on a model-version change), and runs are deterministic for identical input (fixed seed). The text-similarity counterpart is [Search](search.md); the Canvas artifact it emits is what you arrange in [Use canvas for argument mapping](../how-to-guides/project/use-canvas-for-argument-mapping.md).

The graph is built from authored `links:` edges on notes (`notes/claims`, `notes/hubs`, `notes/sources`) and the given `relationships` on Catalog entities (`catalog/papers`, `catalog/people`, `catalog/organizations`, `catalog/venues`, `catalog/datasets`, `catalog/repositories`) — see [Links vs relationships](../adr/52-links-vs-relationships.md).

---

## `cluster_build_graph(seed=-1)`

The typed link/relationship graph as JSON — read-only, no write. `seed < 0` uses the calibration default. Built with NetworkX (`greedy_modularity_communities` + `spring_layout`).

| Output | Shape |
| --- | --- |
| `nodes` | `{id, type, folder}` per note/entity. |
| `edges` | `{source, target, type, kind}` — `type` is the link/relationship label (`supports`, `contradicts`, `cited_by`, …); `kind` is `links` or `relationships`. |
| `communities` | `{node_id: community_index}` from greedy modularity. |
| `centrality` | `{node_id: degree_centrality}`, rounded. |
| `layout` | `{node_id: [x, y]}` spring-layout coordinates. |
| `params_echo` | `{seed, algorithm}` — the run's reproducibility record. |

The map lane turns this JSON into Canvas proposals; nothing is written by this tool.

---

## `cluster_emit_canvas(scope="notes/claims", out="", seed=-1)`

The claim-debate map, written as a JSON Canvas artifact. **Propose-class, staging-only**: it writes only under `notes/fleeting/maps/` and refuses every other target — the human edits and promotes the artifact.

| Parameter | Meaning |
| --- | --- |
| `scope` | A hub/topic note path (`…/x.md` → that note plus everything one hop away) or a folder prefix (notes under it). Default `notes/claims`. |
| `out` | Optional output path; must resolve inside `notes/fleeting/maps/` and end in `.canvas`. |
| `seed` | Layout seed; `< 0` uses the calibration default. |

Rendering: file nodes for in-scope notes; **node color = maturity** (`seedling` → `budding` → `evergreen`), **node size = in-degree**, **edge color = relation** (`supports` green, `contradicts` red, `extends`/other neutral), and communities of two-plus members drawn as group nodes. The return value is `{canvas_path, nodes, edges, groups, scope, params_echo}`; an out-of-`maps/` or non-`.canvas` target returns `{"error": "invalid-target"}`, and an empty scope returns `{"error": "empty-scope"}`.

---

## `cluster_model_topics(folder="notes/sources", min_cluster_size=0, seed=-1)`

BERTopic over note bodies — the **opt-in heavy path**. Its dependencies (`bertopic` → `torch`) live in `.memoria/mcp/requirements-cluster.txt`, never the policy-core requirements, so a default install does not carry them ([ADR-33](../adr/33-cluster-mcp-bertopic.md)).

| Parameter | Meaning |
| --- | --- |
| `folder` | Corpus folder to model; default `notes/sources`. |
| `min_cluster_size` | Minimum topic size; `0` uses the calibration default. |
| `seed` | UMAP `random_state`; `< 0` uses the calibration default. |

Returns `{topics, doc_topic_map, outliers, params_echo}` — `topics` is `{topic, size, label}` per cluster, `doc_topic_map` maps each note stem to its topic, and `outliers` are notes assigned topic `-1`. It errors cleanly rather than crashing: `{"error": "bertopic-not-installed", "note": "pip install -r .memoria/mcp/requirements-cluster.txt"}` when the deps are absent, and `{"error": "too-few-documents"}` when fewer than `max(min_cluster_size × 2, 10)` non-empty notes exist under `folder`.

---

## Calibration defaults

Read from the `clustering` block of `.memoria/schemas/calibration.yaml` (drift-bound — recalibrate when the embedding model changes):

| Knob | Default | Used by |
| --- | --- | --- |
| `seed` | `42` | all three tools (graph layout, canvas layout, UMAP) |
| `hdbscan_min_cluster_size` | `5` | `cluster_model_topics` minimum topic size |
| `umap_n_neighbors` | `15` | `cluster_model_topics` UMAP neighbourhood |
| `embedding_model` | `null` | reserved pin for the configured topic-model embedding |

The `clustering.quality_thresholds` block is separate from these display
defaults. Its `silhouette_floor` and `topic_coherence_floor` remain `null` and
`production_enabled: false` until real reviewed map/topic runs calibrate them;
see [Calibration](calibration.md).

---

## Determinism

The discipline across all three tools: a **fixed seed** (so identical input yields an identical layout), **parameters echoed** in every result (`params_echo`), and **no canonical writes** — `build_graph` and `model_topics` return JSON only, and `emit_canvas` writes a single Canvas under the staging allowlist. The operation never sets a note's lifecycle, maturity, or links; it only renders what the notes already declare.

---

## Related

- The decision and the opt-in dependency split: [ADR-33: Cluster MCP and BERTopic](../adr/33-cluster-mcp-bertopic.md)
- The graph's edge vocabulary: [Wikilink and link conventions](linking.md)
- Where the map lane's output lands: [System actions](system-actions.md)
- The text-similarity surface: [Search](search.md)
- The methods catalog this sits in: [Retrieval and analysis methods](computational-toolbox.md)


---

<!-- source: reference/computational-toolbox.md -->

# Retrieval and analysis methods

Deterministic and hybrid methods Memoria uses, organized by purpose. This page is the current lookup surface; deferred method ideas live in ADRs and explanation pages, not in the active reference contract.

For the rationale — why deterministic over LLM, the hybrid pattern, cost and audit implications — see [Why Memoria uses deterministic methods alongside LLMs](../explanation/rationale/why-computational-methods.md).

---

## Methods in use

### Regex and rule-based scripts

**For:** parsing structured text (citations, frontmatter, wikilinks), pattern detection in filenames, deterministic transformations (normalize whitespace, sort YAML keys).

**Used by:** Linter structural detectors, Peer-reviewer `verify-check-citation`, schema validation, Librarian ingest type-detection dispatch table.

**Cost:** free. Latency: microseconds. Determinism: total.

---

### Vector embeddings + cosine similarity

**For:** finding similar notes, ranking candidate links, detecting near-duplicates, narrowing comparative-read candidates.

**Used by:** qmd-backed Co-PI and lane retrieval, Librarian comparative reads, QuickAdd pre-file similarity shadow reports, and Peer-reviewer duplicate/citation sub-checks. No standalone `similarity-check` or `find-duplicates` command ships today.

**Implementation:** a sentence-transformer model embeds note bodies into an HNSW index. The shipped backend is `qmd` (hybrid BM25 + vector retrieval) — the local tool and stdio MCP actually granted to the lanes that call these methods; FAISS and hnswlib are underlying index libraries `qmd` can sit on. Re-indexed incrementally as new notes arrive. Default models:

| Model | Params | Best for |
| --- | --- | --- |
| `bge-small-en` | 33M | General-purpose English research vaults |
| `all-MiniLM-L6-v2` | 22M | Resource-constrained setups |
| `SPECTER2` | — | Citation-similarity tasks specifically |

Re-embedding the vault on a model change takes minutes (≈10ms per note). The vault stores embeddings keyed by `(model_id, model_version)` so multiple models can coexist during evaluation.

**Cost:** one-time embedding compute per note (~10ms). Per-query: <100ms across thousands of notes. Determinism: total — same model + same text → same vector.

---

### Classical clustering (HDBSCAN, k-means)

**For:** corpus density analysis, identifying conceptual clusters in a project scope, gap detection.

**Used by:** the Librarian's map lane — `map-cluster-corpus`, `map-scope-project`, `map-report-coverage`.

**Implementation:** HDBSCAN over note embeddings (no need to pre-specify cluster count). UMAP for 2D projection if visualization is needed. HDBSCAN is deterministic for fixed parameters; fix UMAP's random seed for reproducibility.

**Cost:** seconds to minutes for thousands of notes. Determinism: total for fixed parameters.

---

### Topic modeling (LDA, NMF, BERTopic)

**For:** identifying underrepresented topics, comparing topic distributions across projects, surfacing methodological themes.

**Used by:** `map-report-coverage` thin-coverage detection and map-lane gap reports.

**Implementation:** BERTopic is the modern default (combines embeddings + clustering + class-based TF-IDF for topic labels). Classical LDA over TF-IDF works for smaller corpora.

**Cost:** minutes for thousands of documents (one-time per analysis). Determinism: same data + same parameters → same topics.

---

### Small classifiers (logistic regression, gradient boosting, fine-tuned BERT)

**For:** proposing `_proposed_classification` labels, scoring whether a note belongs to a project, predicting reading priority.

**Used by:** `_proposed_classification` proposal (with LLM fallback for low-confidence cases), reading-priority ranking when sufficient training data exists.

**Implementation:** `scikit-learn` for tabular and TF-IDF features; fine-tuned DistilBERT for deeper text. Trained on the human's past classification decisions — the human-confirmed `lifecycle: current` notes are the training set.

Training characteristics:

- Multi-label (one-vs-rest) for `research_area`, `methodology`, and `topics` — all list-valued.
- Retrain cadence: monthly, or when the human-override rate on proposed labels exceeds 25%.
- Training set: `lifecycle: current` notes only — `proposed` notes are not yet ground truth.
- Useful at ~200–500 classified notes; well-calibrated at ~1,000.

**Cost:** training is occasional and offline; inference is sub-millisecond. Determinism: total once trained.

---

### Graph algorithms (BFS, PageRank, shortest path)

**For:** orphan detection, hub identification, dependency walks, link density measurement.

**Used by:** Linter `graph-analyze`, future propagation-debt enumeration.

**Implementation:** build the wikilink graph from frontmatter and body links; run standard algorithms (NetworkX in Python, or `dataviewjs` queries against Obsidian's link-graph cache). The current `graph-analyze` command is the `graph_analyze` function in the Linter's `detectors.py` — **pure stdlib** (in-degree arithmetic over the wikilink graph for orphan detection); NetworkX is only needed if/when richer metrics (community detection, centrality) are added, which is why the Linter grants no `networkx` skill today.

**Cost:** linear in graph size. Determinism: total.

---

### API calls (Zotero, OpenAlex, PubMed, CrossRef, GitHub)

**For:** metadata enrichment, retraction monitoring, citation graph traversal.

**Used by:** Librarian catalog enrichment and discovery skills, ingest enrichment, retraction sweep operations, and external metadata lookups.

**Cost:** per-call API budget. Determinism: most APIs are stable; some return ranked results that drift across calls.

---


## Skill frontmatter declarations

Each Hermes skill declares its method class in `SKILL.md` frontmatter:

```yaml
method_class: deterministic | hybrid | generative
deterministic_engine: regex | embedding | classifier | clustering | graph | api
llm_fallback_threshold: 0.85     # hybrid skills only
llm_backend: generic | open-notebook
llm_backend_fallback: generic | none
```

`generic` routes to the host profile's default LLM. `open-notebook` routes to a self-hosted Open Notebook instance for source-grounded RAG (currently pilot-scoped to the `[!brief]` comparative-read step in the Librarian's `catalog-enrich-record`).

---

## Related

- Profiles that call these methods: [Librarian](../explanation/profiles/librarian.md) (catalog · extract · link · map lanes), [Peer-reviewer](../explanation/profiles/peer-reviewer.md), and the [operations](../explanation/operations/README.md) (Linter, Clustering, Sweeps)
- Why deterministic methods: [Why Memoria uses deterministic methods alongside LLMs](../explanation/rationale/why-computational-methods.md)


---

<!-- source: reference/configuration.md -->

# Memoria configuration

Memoria configuration is split across repo-authored source, rendered Hermes
profiles, runtime vault files, Obsidian plugin files, and per-machine secrets.
This page is the ownership ledger: field-level contracts stay in the linked
reference pages and schema files.

## Configuration surfaces

| Surface | Source | Installed location | Owner | Edit policy | Validator |
| --- | --- | --- | --- | --- | --- |
| Hermes profile config | `src/.memoria/profiles/memoria-*/config.yaml` | `~/.hermes/profiles/memoria-*/config.yaml` | Memoria | Edit source; regenerate capability blocks from `tool-registry.yaml`; then redeploy profiles | `tests/test_profiles.py` |
| Profile metadata | `src/.memoria/profiles/memoria-*/distribution.yaml` | Hermes profile manifest | Memoria | Edit source | `tests/test_profiles.py` |
| Profile identity | `src/.memoria/profiles/memoria-*/SOUL.md` | Hermes profile directory | Memoria, with PI customization inside release limits | Edit source; reconcile runtime drift intentionally | profile docs and tests |
| Bundled profile skills | `src/.memoria/profiles/*/skills/` | Hermes profile directory | Memoria | Edit source | profile tests |
| Tool capability registry | `src/.memoria/tool-registry.yaml` | vault source and runtime vault | Memoria | Edit source | `tests/test_profiles.py` |
| Lane policy overlays | `src/.memoria/lane-overrides/*.yaml` | vault source and runtime vault | Memoria | Edit source | policy tests |
| Policy gate plugin | `src/.memoria/plugins/memoria-policy-gate/plugin.yaml` | Hermes profile plugins | Memoria | Edit source | policy tests |
| MCP server config | embedded in each profile `config.yaml` | Hermes profile config | Memoria | Edit source, then redeploy profiles | profile and MCP tests |
| MCP Python dependencies | `src/.memoria/mcp/requirements*.txt` | `<vault>/.memoria/.venv` | Memoria | Edit source; reinstall deps | installer tests |
| Project hints | `src/.memoria/project-hints.yaml.example` | `<vault>/.memoria/project-hints.yaml` | PI | Copy-on-first-use; absent means manual tagging | project-hints guide and linter checks |
| Schema config | `src/.memoria/schemas/**` | vault source and runtime vault | Memoria | Edit source | linter and schema tests |
| Calibration | `src/.memoria/schemas/calibration.yaml` | vault source and runtime vault | Memoria | Edit source | calibration and linter tests |
| Obsidian plugin settings | `src/.obsidian/plugins/**` | runtime vault `.obsidian/plugins/**` | Memoria except local secrets | Shipped config; reconcile intentionally | plugin docs and status checks |
| Local REST API secrets | example files only | runtime plugin `data.json` plus profile `.env` | PI machine | Never commit live secrets | setup docs |
| Profile environment variables | `env_requires` in each profile's `distribution.yaml` (rendered by Hermes as `.env.EXAMPLE`) | `~/.hermes/profiles/<profile>/.env` or `%LOCALAPPDATA%\hermes\profiles\<profile>\.env` | PI machine | Never commit; seed from shared Hermes env | installer smoke |
| Shared Hermes environment seed | not in repo | `~/.hermes/.env` or `%LOCALAPPDATA%\hermes\.env` | PI machine | Never commit; rerun profiles-only after changes | installer propagation |
| qmd index config and state | scripts plus runtime collection | `.qmd/` and runtime qmd store | generated | Rebuild; do not hand-edit | qmd scripts |
| Cron wrappers | `src/.memoria/scripts/*.sh` | vault source and Hermes cron commands | Memoria | Edit source | shellcheck |

## Rendered versus authored

`src/.memoria/profiles/**/config.yaml` is checked-in source. Its mechanical
capability blocks are generated from `src/.memoria/tool-registry.yaml` by
`scripts/render_profile_configs.py`; profile-specific server wiring and model
placeholders remain in the profile config.
`~/.hermes/profiles/**/config.yaml` is rendered installed output. If the two
drift, fix the source and redeploy unless the drift is an intentional local
experiment.

Profile `.env` files are user-owned secret stores. They are not source, and
Hermes profile runs read the profile-local `.env` rather than inheriting a
global fallback.

Memoria profiles do not use standalone `mcp.json`. MCP servers live in profile
`config.yaml`; profile redeploy removes any legacy
`~/.hermes/profiles/memoria-*/mcp.json` stale state.

## Required redeploys

| Change | Command |
| --- | --- |
| Profile config, tools, MCP servers, or model overlay | `bash scripts/install.sh --profiles-only --vault ~/Memoria-test` or `.\scripts\install.ps1 -ProfilesOnly -Vault "$env:USERPROFILE\Memoria-test"` |
| Secrets added or rotated in the shared Hermes `.env` | `bash scripts/install.sh --profiles-only --vault ~/Memoria-test` or `.\scripts\install.ps1 -ProfilesOnly -Vault "$env:USERPROFILE\Memoria-test"` |
| Schema or vault source config | reinstall or refresh the vault, then run the linter |
| qmd index inputs | `bash scripts/qmd-codebase-index.sh --embed` |

Use the production vault path instead of `~/Memoria-test` only when you are
deploying a real runtime vault. Development verification uses the test vault.

## Never commit

- `OBSIDIAN_API_KEY`, model provider keys, or API tokens.
- Profile `.env` files.
- Local REST API live `data.json`.
- Generated qmd indexes.
- Runtime vault state, logs, and local diagnostics.

## Related references

- Profile surfaces and capability gates: [Profile capabilities](profiles.md)
- Installer rendering and environment overlays: [Installer (bootstrap)](installer.md)
- Write-gate contract: [Policy MCP](policy-mcp.md)
- Obsidian plugin files: [Obsidian plugin data files](obsidian-plugin-data-files.md)
- Obsidian plugin settings: [Obsidian plugin settings](obsidian-plugin-settings.md)
- External integrations: [External integrations](integrations.md)
- Frontmatter fields: [Frontmatter fields](frontmatter.md)
- Calibration thresholds: [Calibration](calibration.md)
- Search and qmd: [Search](search.md)


---

<!-- source: reference/dashboards.md -->

# Dashboards

The primary dashboards are the three durable space notes under `spaces/`
(`src/spaces`): Library, Knowledge, and Project. The Inbox queue (`spaces/inbox.md`,
`type: queue`) and Maintenance collection (`spaces/maintenance.md`, `type: maintenance`)
sit alongside them by cadence: daily action vs weekly structural debt. Both are reached
from the navigation rail's **Now**. Five read-only system dashboards and the
claim/source/fleeting Bases live under `system/dashboards/` (`src/system/dashboards`);
other Bases live beside their data folders. Space
switching is owned by the navigation rail (`_nav.md`), not an Obsidian workspace swap.
All dashboards are Dataview / Bases consumers: they render existing vault state and
logs, never write, and a healthy vault shows action queues near-empty.

The daily glance starts in the rail's **Now**: action count opens the Inbox queue,
while the health band opens Maintenance and Fleet health. **Board-state is the Inbox
board** — a thin page embedding `inbox.base`.

No standalone status-line widget ships in the current Obsidian surface. The rail health
band is the ambient glance for structural and fleet health; the Inbox queue stays the
action surface.

---

## Dashboard inventory

| Surface | Dashboard | File | Shows |
| --- | --- | --- | --- |
| Queue | Inbox | `spaces/inbox.md` | Action-first triage queue (`type: queue`), reached from the rail's *Now*: the Inbox `Needs me` and fleeting processing views. |
| Maintenance | Maintenance | `spaces/maintenance.md` | Weekly structural-debt collection (`type: maintenance`): drift watch, loose ends, board, and new-this-week digest. |
| Space | Library | `spaces/library.md` | Source intake space: reading pipeline, discuss queue, and Catalog papers. |
| Space | Knowledge | `spaces/knowledge.md` | Synthesis space: claims by maturity, open questions, contradictions, hubs, and patterns. |
| Space | Project | `spaces/project.md` | Project steering space: active projects, refutation-stamp gate, saturation, and project gaps. |
| Maintenance support | Board state | `system/dashboards/board-state.md` | The full Inbox board (embeds `inbox.base` — "Needs me" = cards in `proposed`, with the card's `action`/`finding` visible) plus live worker cards from `system/board/`. |
| Agent-ops | Audit log | `system/dashboards/audit-log.md` | `system/logs/audit.jsonl` — recent writes (each view row-capped, not time-windowed); unhandled denies -> flag. |
| Agent-ops | Fleet health | `system/dashboards/fleet-health.md` | Per-lane trust score / operational rollup from `system/metrics/`. |
| Agent-ops | Eval trend | `system/dashboards/eval-trend.md` | Quarterly vault-eval capability scores (recall@k, support-rate, FAMA-clean) from `system/metrics/eval/runs.jsonl` — diagnostic, never gating. |
| Agent-ops | Skill state | `system/dashboards/skill-state.md` | Which skills are active in which lane, read live from `.memoria/lane-overrides/` + `.memoria/profiles/*/skills/`; mismatches surface as consistency-check rows ([ADR-43](../adr/43-skill-governance.md)). |

The **Surface** column names the space, queue, maintenance collection, or support context where a dashboard is reached.
The explanation site groups the support dashboards by the *kind of attention* they
demand — **Daily glance**, **Synthesis agenda**, **Structural health**, **Operational
health** ([Dashboards](../explanation/dashboards/README.md)).

---

## The Bases views

Obsidian Bases (`.base` files) are the database views the dashboards and space notes lean on ([ADR-49](../adr/49-catalog-in-bases-linter-monitor.md)). Bases are views; the notes are the source of truth.

| Base | Lives at | View over |
| --- | --- | --- |
| `catalog.base` | `catalog/` | The Catalog — entity records by type (papers, people, organizations, venues, datasets, repositories), `lifecycle != archived`. |
| `inbox.base` | `inbox/` | The Inbox board — cards grouped by type; "Needs me" = `proposed`; `action`/`finding` columns expose the next thing to decide; converges to empty. |
| `board.base` | `system/board/` | Live worker cards by lane/state, mirrored from Hermes board state. |
| `claims.base` | `system/dashboards/` | Claims by maturity. |
| `sources.base` | `system/dashboards/` | Source notes by lifecycle. |
| `fleeting.base` | `system/dashboards/` | Fleeting notes awaiting promote-or-discard. |
| `hubs.base` | `notes/hubs/` | Hub notes by topic cluster and lifecycle. |
| `projects.base` | `projects/` | Project notes by output mode, refutation stamp, thesis state, saturation, and open gaps. |
| `patterns.base` | `system/patterns/` | The pattern library by mode and lifecycle. |
| `worklists.base` | `system/worklists/` | Batch screening rows grouped by worklist, decision, or group; rows are `worklist-item` notes and one aggregate Inbox prompt points here. |

### Verified Bases behavior

The supported dashboard UI relies on these Obsidian 1.12.7 Bases behaviors:

- Wikilinks inside nested `links:` maps register as backlinks, so typed edges such
  as `links.contradicts` are visible both to contradiction views and to orphan
  checks that use `file.backlinks`.
- Native Bases filters handle nested relation presence checks such as
  `!links.contradicts.isEmpty()`; no materialized `has_contradiction` field is
  needed for the shipped contradiction view.
- Warm-cache Bases rendering is not the current scale limit: a 7,004-row grouped
  view with multi-key sort and formulas rendered in about 1.4 seconds in the
  sandbox.
- Cold metadata parsing is the scale risk: a 10,000-file bulk write took about
  76 seconds before the metadata cache fully settled. Future projection work must
  wait for cache settlement before signalling readiness; see
  [ADR-102](../adr/102-disposable-projection-engine.md).

---

## Verdict band (Maintenance drift watch)

Maintenance's Drift watch view rolls the Linter operation's detector findings up into
a `PASS` / `REVIEW` / `FAIL` band; the rollup rule and the severity scale it reads
are owned by [Linter: detectors and auto-fix](linter.md#the-detectors).

## Trust score (fleet-health)

A 0–100 composite per lane, computed by `src/.memoria/mcp/metrics_aggregate.py` into `system/metrics/`. Inputs: audit deny rate, structural-drift incidents, secret-field access attempts, retry rate, success rate, and accept/reject ratios on lanes producing proposals. The shipped `fleet-health.md` dashboard embeds a Dataview table over those `lane-metric` notes and shows PI attention fields (`time_on_gate_min`, `expand_then_accept_min`, `card_open_resolve_min`) plus blind re-review sample counts. Bands: **90+ healthy · 70–89 watch · < 70 act**. Suggestion-ratio extremes both down-weight: accept > ~90% = rubber-stamping; < ~20% = candidate scoring needs tuning.

## Eval metrics (eval-trend)

Per-quarter capability scores, computed by the deterministic scorer `src/.memoria/operations/telemetry/eval/eval_score.py` into `system/metrics/eval/runs.jsonl` ([ADR-11](../adr/11-vault-eval-maintenance.md)). Each metric is 0–1, higher is better: **recall@k** (gold citekeys in the top-k retrieved), **support-rate** (cited evidence resolving to real catalog records), **FAMA-clean** (no superseded/archived claim reused). A gold task whose card reported no machine-readable result shows as **unscored** — never a faked score. Diagnostic, not gating: a dip informs the PI; it does not pause scheduled work. Full contract: [Vault eval](vault-eval.md).

---

## Design conventions (apply to all dashboards)

- **One decision per dashboard** — each surfaces a single decision type.
- **Empty is success** — a healthy vault shows near-empty tables.
- **Sort by decision type** — queues oldest-first; logs newest-first.
- **Graceful degradation** — a missing log or plugin shows an explanatory placeholder, never an error.

The reasoning behind these conventions (and the synthesis-vs-structural actor split) is in [Dashboards](../explanation/dashboards/README.md).

---

For the exact `lane-metric` fields and trust-score calculation, see [Fleet metrics](fleet-metrics.md) and [Telemetry log schemas](telemetry-logs.md).

## Related

- The detectors behind Maintenance drift watch: [Linter: detectors and auto-fix](linter.md)
- The audit-log schema fleet-health and audit-log read: [Memory substrates](memory.md)
- The card types the Inbox board groups: [Document types](document-types.md)
- Where the dashboards open by default: [Obsidian workspaces](obsidian-workspaces.md)


---

<!-- source: reference/diagnostics.md -->

# Diagnostics

Local troubleshooting records for Memoria-owned Python MCP servers and Operations. These records are not audit memory and never live under the vault or `system/logs/`.

## Contract

| Item | Contract |
| --- | --- |
| Default location | `$XDG_STATE_HOME/memoria/diagnostics/`, or `~/.local/state/memoria/diagnostics/` when `XDG_STATE_HOME` is unset |
| Override | `MEMORIA_DIAGNOSTICS_DIR`, still rejected when a caller supplies a vault path and the target is inside that vault |
| File pattern | `diagnostics-YYYY-MM-DD.jsonl`, rotated to bounded `.gz` backups |
| Default level | `warn` and `error`; raise with `MEMORIA_DIAGNOSTIC_LEVEL` or `MEMORIA_DIAGNOSTIC_LEVEL_<COMPONENT>` |
| Default content | typed `code`, `component`, `level`, timestamp, payload SHA-256, payload byte length, and content-light details |
| Raw capture | one process only with `MEMORIA_DIAGNOSTIC_RAW_ONCE=1`; the flag is consumed after one event and stored only as redacted text |
| Bundle command | `python -m memoria.runtime.diagnostics --bundle ~/memoria-diagnostics.tgz` |
| Redaction self-test | `python -m memoria.runtime.diagnostics --self-test` |

Diagnostic detail fields hash strings and paths instead of writing them verbatim.
The user-triggered bundle is a compressed archive with a README and redacted JSONL
files; review it before sharing. Use `--include-raw` only when a one-shot raw
capture was deliberately enabled and the redacted payload is needed for support.

## Related

- Operational telemetry inventory: [Telemetry & logs](telemetry.md)
- Log schemas: [Telemetry log schemas](telemetry-logs.md)


---

<!-- source: reference/document-types.md -->

# Document types

The 25 document types by category, with their folder homes, lifecycle subsets, and required fields. **The schemas are authoritative:** every type is defined by one YAML file under `src/.memoria/schemas/types`, and the type → folder map lives in `src/.memoria/schemas/folders.yaml` ([ADR-47](../adr/47-type-first-category-folders.md)). The Linter, the pre-commit hook, the policy MCP, and the installer all read those files — this page is the human-readable view, and the schemas win on any disagreement. Human capture form metadata also lives in the relevant type schemas under `creation.form` ([ADR-119](../adr/119-schema-driven-document-creation.md)). For field semantics see [Frontmatter fields](frontmatter.md).

The 25 types group into: **6 entities** (catalog), **3 project types**, **4 notes**, **5 cards** (inbox), **4 system types** (pattern, eval task, worklist item, and worker card), and **3 navigation surfaces** (`space`, `queue`, and `maintenance`).

---

## Catalog entities (6)

Bibliographic / world records, keyed on stable IDs and carrying **given** `relationships` edges (the field contract is in [Frontmatter fields](frontmatter.md)). None is review-gated.

| Type | Folder | Lifecycle subset | Required fields | Key optional fields |
| --- | --- | --- | --- | --- |
| `paper` | `catalog/papers/` | `current → retracted → archived` | `citekey`, `title` | `doi`, `authors`, `year`, `venue`, `url`, `relationships`, `research_area`, `methodology` |
| `person` | `catalog/people/` | `current → archived` | `name` | `orcid`, `affiliations`, `relationships` |
| `organization` | `catalog/organizations/` | `current → archived` | `name` | `subtype` (lab · university · company · funder …), `location`, `relationships` |
| `venue` | `catalog/venues/` | `current → archived` | `name` | `subtype` (journal · conference · publisher …), `issn`, `relationships` |
| `dataset` | `catalog/datasets/` | `current → retracted → archived` | `name` | `doi`, `url`, `license`, `relationships` |
| `repository` | `catalog/repositories/` | `current → archived` | `name` | `url`, `language`, `license`, `relationships` |

---

## Projects (3)

Project records live under `projects/` and anchor the Project space ([ADR-77](../adr/77-project-gate.md)). They are not review-gated folders; the gated transition is the thesis promotion to `current`.

| Type | Folder | Lifecycle subset | Required fields | Key optional fields |
| --- | --- | --- | --- | --- |
| `project` | `projects/` | `current → archived` | `title`, `slug`, `scope_topics`, `inquiry`, `finer`, `output_mode`, `question_version`, `question_log` | `active_thesis`, `refutation_sufficiency`, `impact`, `on_path`, `evidence_saturation`, `argument_stage`, `computed_at` |
| `thesis` | `projects/` | full chain | `title`, `project`, `sources` | `links`, `superseded_by`, `refutation_sufficiency`, `promoted_at`, `promoted_by`, `impact`, `on_path`, `evidence_saturation`, `argument_stage`, `computed_at` |
| `code-note` | `projects/` | `proposed → current → archived` | `title`, `project`, `agent`, `task`, `acceptance` | `motivating_claims`, `inputs`, `outputs`, `run_command`, `dependencies`, `repository`, `created` |

`project.inquiry` carries the PICO block (`population`, `intervention`, `comparison`, `outcome`) and `project.finer` carries the answerability lens. A `thesis` starts at `proposed`; promotion to `current` is the project's review transition, not a template default. Current theses must carry `promoted_at` so the promotion is visible to the Linter and pre-commit hook. A `code-note` is the Engineer's handoff/provenance note for external coding agents under a project's `code/` scratch.

---

## Notes (4)

The PI's knowledge, carrying **authored** `links:` edges (the field contract is in [Frontmatter fields](frontmatter.md)). Two of the four live in review-gated zones — the policy MCP degrades every agent write there to `dry_run`.

| Type | Folder | Gated | Lifecycle subset | Required fields | Key optional fields |
| --- | --- | --- | --- | --- | --- |
| `fleeting` | `notes/fleeting/` | no | `proposed → archived` | `origin` (`human` / `agent` / `chat`) | `title` |
| `source` | `notes/sources/` | no | `proposed → provisional → current → retracted → archived` (the full chain) | `title`, `entity` (wikilink to the Catalog entity it is about) | `source_type` (`paper` / `dataset` / `repository` / `web-page` / `report`), `research_area`, `methodology`, `links` |
| `claim` | `notes/claims/` | **yes** | `current → retracted → archived` | `title`, `maturity`, `sources` (every claim → a citekey) | `schema_version`, `links` (supports / contradicts / …), `topics`, `superseded_by` |
| `hub` | `notes/hubs/` | **yes** | `current → archived` | `title`, `topic` | `members`, `links` |

A `hub` is a curated synthesis surface: it explains an area, selects members,
and lives behind the review gate. Pure registers are Bases views such as
`hubs.base#Hubs index`, not a separate document type.

`maturity` is a claim **property, never a gate** — its values and the universal lifecycle chain are specified in [Frontmatter fields](frontmatter.md). Claim template version 2 includes `schema_version: 2`; query and write-assist surfaces exclude claims with non-empty `superseded_by` unless the task is explicitly about supersession history.

---

## Inbox cards (5)

The agent → human action queue ([ADR-51](../adr/51-inbox-category-and-honesty-card.md)). All five live flat in `inbox/`, start at `lifecycle: proposed` (awaiting the PI), and converge to `archived`. Three shapes:

| Shape | Types | What it carries |
| --- | --- | --- |
| **Proposals** | `candidate`, `gap` | The honesty body — arguments, never a verdict. A `candidate` proposes an acceptance (e.g. a discovered paper); a `gap` proposes a missing piece (coverage gap, missing link). |
| **Verification cards** | `flag`, `alert` | Lead with the finding and carry the verdict. A `flag` is a pointed finding (e.g. a retraction); an `alert` is a standing system warning. |
| **Work prompts** | `work-prompt` | An action and a pointer, never a verdict — e.g. the review prompt the board export raises when a card reaches `done` ([Kanban board reference](kanban-board.md)). |

Use `flag` for a bounded verification finding that needs a decision about one object or assertion: retraction, extraction conflict, link contradiction, or failed invariant. Use `alert` for a standing warning about a condition the PI may need to monitor over time: structural drift, backlog health, or repeated runtime failure. Both are Signal documents and lead with the finding; neither is a proposal.

See [Inbox card fields](inbox-card-fields.md) for the complete per-document-type field contract (required, `required_any`, optional, and the shared `raised_by` / `loudness` fields). Operations and lanes never invent card formats — every card goes through the shared writer `src/.memoria/operations/lib/inbox.py`.

---

## System types (4)

| Type | Folder | Lifecycle subset | Required fields | Key optional fields |
| --- | --- | --- | --- | --- |
| `pattern` | `system/patterns/` | `proposed → current → archived` | `title`, `posture`, `mode` (`library` / `project` / `both`), `action`, `input`, `output_target` | `model_hint`, `version`, `adapted_from` |
| `eval-task` | `system/eval/` | `proposed → current → archived` | `title`, `workflow`, `lane` (`catalog` / `extract` / `link` / `map` / `draft` / `verify` / `code`) | `references`, `created` |
| `worklist-item` | `system/worklists/` | `proposed → current → archived` | `title`, `decision`, `worklist`, `item_ref` | `source_report`, `group`, `rank`, `reason`, `created` |
| `worker-card` | `system/board/` | `current → archived` | `title`, `task_id`, `lane`, `status` | `as_of`, `review_status`, `retry_count`, `reason`, `expected_outputs` |

Patterns are curated prompt-transformations stored as data ([ADR-53](../adr/53-pattern-library.md)); only `lifecycle: current` patterns are runnable, and the runner refuses an `output_target` inside a gated zone. Eval tasks are the [Vault eval](vault-eval.md) gold set ([ADR-11](../adr/11-vault-eval-maintenance.md)); only `lifecycle: current` tasks dispatch. Worklist items are file-backed rows for ADR-54 batch screening: the PI toggles each row's `decision` in `system/worklists/worklists.base`, while the Inbox receives one aggregate `work-prompt` for the batch. Worker cards are the file-backed board rows under `system/board/`, separate from Inbox cards because they are execution state rather than PI-facing prompts. `system/` is otherwise untyped infrastructure.

---

## Navigation surfaces (3)

The top-level surfaces under `spaces/`. The three durable **spaces** are the rooms you work in; the **queue** (the Inbox) is a transient triage surface that converges to empty; **maintenance** is the weekly structural-debt collection. Space-switching is owned by the left-pane rail, so these notes carry no nav row.

| Type | Folder | Lifecycle subset | Required fields | Key optional fields |
| --- | --- | --- | --- | --- |
| `space` | `spaces/` | `current → archived` | `title`, `space` (`library` / `knowledge` / `project`) | `created` |
| `queue` | `spaces/` | `current → archived` | `title` | `created` |
| `maintenance` | `spaces/` | `current → archived` | `title` | `created` |

---

## Gating and transience

From `folders.yaml`, the single source the policy MCP and the Linter share:

| Setting | Value |
| --- | --- |
| `gated_prefixes` (agent writes degrade to `dry_run`) | `notes/claims/` · `notes/hubs/` |
| `transient_prefixes` (items converge to `archived` and leave active views) | `inbox/` |
| `categories` (legal vault-root folders) | `catalog` · `notes` · `projects` · `inbox` · `spaces` · `system` |
| `skeleton` sample bundle | `.memoria/samples/mediterranean-diet/` holds optional tutorial notes until **Memoria: load sample vault** copies them into live homes |

---

## Templates

Human-facing starter notes for 19 of the 25 types ship in `src/system/templates` (patterns, eval tasks, spaces, the inbox queue, maintenance collection, and worker cards are authored by their owning surfaces). Templates are scaffolding — the schemas, not the templates, are what validation runs against; the Linter's golden-copy check keeps the deployed templates byte-identical to the shipped ones.

The four Modal Forms-backed human entry points (`fleeting`, `source`, `claim`,
and `project`) are generated from those types' `creation.form` blocks, with
vocabulary-backed inputs filled from `system/vocabulary.md`.

---

## Related

- Field kinds, the universal lifecycle, and the two edge kinds: [Frontmatter fields](frontmatter.md)
- The folder tree the homes map into: [On-disk layout](on-disk-layout.md)
- What enforces the schemas: [Linter: detectors and auto-fix](linter.md) and [Policy MCP](policy-mcp.md)


---

<!-- source: reference/export.md -->

# Export routes and formats

Citation states, export routes, editor feature comparison, and deliverable folder targets. For choosing between routes and failure modes see [Export a draft](../how-to-guides/project/export-a-draft.md).

---

## Citation states

A citation passes through up to four states. Conversions are mostly one-way.

| State | Form | Lives in | Editable / restylable downstream? |
| --- | --- | --- | --- |
| Citekey | `[@smith2020]` | Obsidian Markdown draft | — (source form; always editable here) |
| Pandoc-static | Rendered text string | `.docx` / `.odt` | ❌ Frozen — no restyling |
| Word field | Binary field code | Word (live) | ✅ Live; restyle via Zotero Word plugin |
| Google Docs NamedRange | Hidden citation ID | Google Docs (live) | ✅ Live; restyle via Zotero Connector |

---

## Export routes

| Option | Output format | Use case | Tool chain |
| --- | --- | --- | --- |
| **A — Pandoc static** *(default)* | `.docx` / `.odt` | Final submission; frozen citations | `pandoc … --citeproc --bibliography .memoria/memoria.bib --csl .memoria/csl/<style>.csl` |
| **B — Live Word fields** | `.docx` with Zotero fields | Advisor feedback rounds on Word | Pandoc + `zotero.lua` filter → Word + Zotero plugin |
| **C — Live LibreOffice** | `.odt` with Reference Marks | Advisor feedback rounds on LibreOffice | Pandoc → `.odt` → Zotero RTF/ODF Scan |
| **D — Google Docs** | (manual) | Real-time co-authoring only | No Pandoc route; insert citations manually via Zotero Connector |

The final editor is effectively fixed at drafting time: switching from Obsidian → Google Docs late means re-inserting every citation by hand.

---

## Editor feature comparison

| Feature | Word + Zotero | LibreOffice + Zotero | Google Docs + Zotero |
| --- | --- | --- | --- |
| Live citation fields | ✅ | ✅ | ✅ |
| Citation restyling | ✅ | ✅ | ✅ |
| Pandoc automation route | ✅ (via `zotero.lua`) | ✅ (via ODF Scan) | ❌ (manual only) |
| Real-time co-editing | ❌ | ❌ | ✅ |
| Track changes | ✅ | ✅ | ✅ |
| 100+ citation performance | ✅ | ✅ | ⚠️ Slow |
| Journal template availability | ✅ (wide) | ⚠️ Limited | ❌ |

---

## Known failure modes per route

| Route | Failure mode | Mitigation |
| --- | --- | --- |
| Option B (Word + `zotero.lua`) | `lpeg` dependency on Windows requires Visual Studio to build — can take days to debug | Test on a single-citation document first |
| Option B | `.docx` may be corrupt on first open | Rerun Pandoc |
| Option A (Pandoc static) | Pandoc + BBT `.docx` corrupt with some citation styles | Rerun Pandoc; test on single-citation document first |
| Option D (Google Docs) | No automated route — each citekey re-inserted by hand | Only viable for short documents or when real-time collaboration is essential |

---

## Export target folder

Drafts live in their project's scratch, and every export lands beside them under `exports/` — the project is self-contained ([ADR-47](../adr/47-type-first-category-folders.md)). There is no separate top-level deliverables tree.

| Artifact | Folder |
| --- | --- |
| Manuscripts (papers, articles, preprints) | `projects/<slug>/exports/` |
| Presentations (slides, talks, posters) | `projects/<slug>/exports/` |
| Media (figures, infographics, web assets) | `projects/<slug>/exports/` |
| Releases (datasets, models, code, supplementary) | `projects/<slug>/exports/` |

---

## Default Pandoc command

```bash
pandoc projects/<project>/composition/<chapter>.md \
  --citeproc \
  --bibliography .memoria/memoria.bib \
  --csl .memoria/csl/apa.csl \
  -o projects/<project>/exports/<chapter>.docx
```

CSL files live in `.memoria/csl/`. The folder ships as an empty `.keep` placeholder; place your `.csl` files there before export.

---

## Export gate

An exported artifact is terminal — rendered once from its source composition and not edited in place; an update is a re-export from the composition. Agents propose; the export itself is a human-run step ([ADR-47](../adr/47-type-first-category-folders.md)).

---

## Related

- The bibliography rendering depends on: [Bibliography](bibliography.md)
- The export how-to: [Export a draft](../how-to-guides/project/export-a-draft.md)


---

<!-- source: reference/failure-modes.md -->

# Failure modes

All known failure modes, sorted by severity. Each entry: symptom, severity, cause, and fix. For full symptom → diagnosis → fix recipes on the most common failures see [Troubleshooting](../how-to-guides/troubleshooting).

**Severity scale.** These rows use the same `LOW`/`MEDIUM`/`HIGH`/`CRITICAL` scale defined by [Linter: detectors and auto-fix](linter.md#the-detectors); what this page adds is where each level escalates:

| Severity | Escalates to |
| --- | --- |
| `CRITICAL` | Raises `loudness: block`: blocks new delegation and review-gated promotion until acknowledged, surfaces in the rail's **Now**, and records a Telegram push attempt when the bot environment is configured ([Inbox card fields](inbox-card-fields.md)). |
| `HIGH` | Surfaced in the rail's **Now** and in Maintenance's Drift watch. |
| `MEDIUM` | Surfaced in Maintenance during the weekly review. |
| `LOW` | Aggregated weekly. |

---

## All failure modes

Sorted by severity, then topic.

| Symptom | Severity | Cause | Fix |
| --- | --- | --- | --- |
| **Obsidian Linter corrupts frontmatter** | CRITICAL | The frontend Obsidian Linter plugin is installed — it is incompatible with Memoria ([ADR-12](../adr/12-obsidian-linter-reference-only.md)) | Uninstall it. It reorders/rewrites the agent-owned `_proposed_classification` / `_enrichment` frontmatter; folder exclusion does not make it safe. `markdownlint` + the Memoria Linter cover its role. |
| **`_proposed_classification` or `_enrichment` overwritten** | CRITICAL | A frontend formatter reordered or stripped agent-owned frontmatter namespaces on save | Exclude agent-maintained folders from any frontend formatter; let the Memoria Linter own frontmatter. |
| Enrichment block empty after ingest | HIGH | `OPENALEX_API_KEY` missing in per-profile `.env` (silent — ingest "succeeded" with degraded data; OpenAlex requires a key since 2026-02) | Check `echo $OPENALEX_API_KEY`; populate the per-profile `.env`, then re-ingest — full recipe: [Fix empty enrichment](../how-to-guides/troubleshooting/fix-empty-enrichment.md). |
| Dataview queries returning nothing | HIGH | `methodology` or `topics` field value doesn't match the controlled vocabulary exactly — looks like "nothing to do" | Check values in notes match [Vocabulary](vocabulary.md) exactly — full recipe: [Fix missing query results](../how-to-guides/troubleshooting/fix-missing-query-results.md). |
| `qmd` search index stale — `draft` finds no notes | HIGH | Index not rebuilt after notes changed (silent) | `cd {vault-path} && qmd embed` — full rebuild (1–5 min for 500+ notes, 10–15 min for 2000+). |
| `audit.jsonl` growing without bound | LOW | Expected: the log is append-only forever, never rotated ([ADR-25](../adr/25-session-logging-two-logs.md)) | The Linter's `audit-log-size` detector raises an advisory past 50 MB; archive a vault backup if disk pressure ever matters. |
| Broken frontmatter YAML | MEDIUM | YAML parse error: unclosed string, list indentation error, missing closing `---` | Open in an editor outside Obsidian (Obsidian masks raw YAML). Fix manually. Verify with `python3 .memoria/operations/integrity/linter/detectors.py --vault .` (the Linter is an operation, not an agent — there is no `memoria-linter` profile). |
| Obsidian agent-client can't connect | MEDIUM | `hermes -p memoria-copi acp` cannot start or the plugin command path is stale | Run `hermes -p memoria-copi acp` in a terminal, then check the bundled agent-client settings and profile `.env`. |
| `_proposed_classification` not appearing | MEDIUM | The Librarian's `catalog-classify-source` skill did not run or the capture never reached the catalog lane | Check the source card and `memoria-librarian` bundled skills, then rerun the catalog/classify task. |
| Syncthing + `.bib` race condition | MEDIUM | VPS reads `.bib` while Syncthing is mid-transfer | Use Git pull for `.bib` distribution on `always-on` deployment — not Syncthing. |
| Deferred always-on bridge unreachable | MEDIUM | Unsupported `always-on` topology drifted or the single dispatcher is offline | Return to the supported local install, or follow the deferred topology notes in [Always-on VPS design](../explanation/deployment/always-on-vps-design.md). |
| Schema mismatch in Dataview | MEDIUM | Notes do not match the current schema | Run a manual, git-disciplined migration — there is no automated migrate command. Follow [Run a schema migration](../how-to-guides/operate/run-a-schema-migration.md) and validate with `python3 .memoria/operations/integrity/linter/detectors.py --vault .`. |
| Cron job didn't fire overnight | MEDIUM | Sleep-prone host, stale `.env`, or missing Hermes cron registration | Check `hermes cron list`, the latest board/metrics outputs under `system/`, and rerun the installer profiles-only path if wrappers are missing. |
| Retry count climbing on same card | MEDIUM | Brittle prompt or broken tool | After `max_retries` (default 3) the card auto-moves to `blocked`. Revise the handoff `metadata` or archive as infeasible. |
| Card not progressing (`running` / `ready` / `blocked`) | MEDIUM | Worker crashed mid-claim, unresolved `assignee`, or human decision owed on `blocked` card | See full recipe in [Fix a stuck card](../how-to-guides/troubleshooting/fix-stuck-card.md). |
| Citekey not found at ingest | LOW | `.bib` not updated or not pulled | Export from Zotero (File → Export Library → Keep Updated); `git add .memoria/memoria.bib && git commit && git push`. |
| `_enrichment` fields not queryable | LOW | `_enrichment` is a nested frontmatter namespace; Dataview can't query nested keys directly | Promote specific fields (e.g., `enriched_date`) to main frontmatter, or query the parent key. |
| Pandoc + BBT DOCX corrupt | LOW | Known Pandoc/Better BibTeX issue with some citation styles | Rerun Pandoc; test on a single-citation document first. |
| Profile install drift after edit | LOW | Vault source changed but profiles not re-deployed | Re-run `bash scripts/install.sh --profiles-only` (`.\scripts/install.ps1 -ProfilesOnly` on Windows). |
| Bitwarden bootstrap token rejected | LOW | Wrong region or revoked token | Re-run `hermes secrets bitwarden setup` and pick the correct region. |

---

## Related

- The troubleshooting how-to guides: [Troubleshooting](../how-to-guides/troubleshooting/README.md)
- Why the CRITICAL self-review failure can't happen: [Why the review gate is structural](../explanation/rationale/why-human-gate.md)


---

<!-- source: reference/fleet-metrics.md -->

# Fleet metrics

`src/.memoria/mcp/metrics_aggregate.py` rolls board history, policy audit rows, lint findings, review dispositions, cost rows, and attention timing into weekly lane-metric notes. These notes are the source queried by the Fleet health dashboard.

## Command

```bash
python src/.memoria/mcp/metrics_aggregate.py --vault <vault>
python src/.memoria/mcp/metrics_aggregate.py --vault <vault> --from-json cards.json
```

`--from-json` supplies a saved board JSON payload for tests/offline runs. All other inputs are read from the vault logs listed below and degrade gracefully when absent.

## Inputs

| Input | Used for |
| --- | --- |
| `system/logs/audit.jsonl` | Mutating policy decisions: write count, deny count, dry-run count, and deny rate. |
| Hermes board / `--from-json` cards | Done/blocked counts, retry totals, time on gate, and expand-to-accept timing when card timestamps are present. |
| `system/logs/lint-findings.jsonl` | Drift incident counts and the weekly lint verdict note. |
| `system/logs/disposition.jsonl` | Accepted, edited, rejected review counts and accept ratio. |
| `system/logs/cost.jsonl` | API spend and token totals. |
| `system/logs/board-transitions.jsonl` | Median operator decision time from `review: requested` to a terminal review state. |
| `system/logs/attention.jsonl` | Obsidian-side PI card-open-to-resolve timing. |
| `system/logs/blind-review-samples.jsonl` | Blind re-review sample counts. |

The aggregator covers the four background lanes only: `memoria-librarian`, `memoria-writer`, `memoria-peer-reviewer`, and `memoria-engineer`. Co-PI and deterministic operations are not lane-metric subjects.

## Trust score

The score starts at `100` and subtracts bounded penalties:

| Signal | Penalty |
| --- | --- |
| Deny rate | `40 * deny_rate` |
| Failure rate | `40 * (1 - success_rate)` |
| Retry rate | `20 * retry_rate`, capped at `30` |
| Drift incidents | `2 * drift_incidents`, capped at `20` |
| Secret hits | `10 * secret_hits`, capped at `30` |
| Review ratio anomaly | `10` when accept ratio is above `0.9` or below `0.2` |

The final score is rounded and clamped to `0..100`. Bands are fixed: `90+` is `healthy`, `70..89` is `watch`, and `<70` is `act`. When the combined sample count is below `5`, the score is still written but the band becomes `insufficient-data`.

`consistency_passk` is currently `null`; repeated-run pass-at-k needs a future harness.

## Outputs

| Path | Shape |
| --- | --- |
| `system/metrics/lane-<lane>-<YYYY-Www>.md` | Weekly lane metric note with frontmatter fields used by dashboards. |
| `system/metrics/lint-verdict-<YYYY-Www>.md` | Weekly lint verdict note when `lint-findings.jsonl` exists. |

Re-running in the same ISO week overwrites the metric notes for that week; source logs remain append-only.

## Related

- Dashboard consumers: [Dashboards](dashboards.md)
- Source log schemas: [Telemetry log schemas](telemetry-logs.md)
- Board projection that creates several inputs: [Board export](board-export.md)


---

<!-- source: reference/frontmatter.md -->

# Frontmatter fields

The frontmatter contract for every typed document. **The single source is `.memoria/schemas/`** — per-document-type field schemas in `src/.memoria/schemas/types`, the type → folder map in `src/.memoria/schemas/folders.yaml`, and the calibrated thresholds in `src/.memoria/schemas/calibration.yaml`. The shared loader/validator is `src/.memoria/operations/lib/schema.py`; the Linter, the pre-commit hook, and the installer-skeleton tests all read it, so a schema change is a one-file edit, never a hunt across hardcoded lists. This page explains the grammar and the universal fields; the per-type tables live in [Document types](document-types.md).

---

## The field-kind grammar

Each type schema declares `required:` and `optional:` maps of `field: kind`, plus an `enums:` block and (optionally) `required_any:` — a list of field names of which at least one must be present (e.g. a `flag` needs `target` or `citekey`). The kinds:

| Kind | Accepts |
| --- | --- |
| `str` | a string |
| `int` | an integer (not a bool) |
| `bool` | a boolean |
| `date` | a YAML date or an ISO-8601 date string |
| `list` | a YAML sequence |
| `map` | a YAML mapping |
| `literal:<value>` | exactly that value — e.g. `type: literal:claim` pins the `type` field |
| `enum:<name>` | one of the values the schema's `enums.<name>` lists |

Unknown extra fields are **allowed** — the schema constrains, it does not enumerate. A schema example (`types/claim.yaml`):

```yaml
type: claim
category: notes
gated: true
enums:
  lifecycle: [current, retracted, archived]
  maturity: [seedling, budding, evergreen]
required:
  type: literal:claim
  lifecycle: enum:lifecycle
  title: str
  maturity: enum:maturity
  sources: list
optional:
  schema_version: int
  links: map
  topics: list
  superseded_by: str
  created: date
```

---

## Creation metadata

Human capture forms are declared beside the validating fields when a type has an
Obsidian Modal Forms entry. The `creation.form` block owns the form name, title,
field order, labels, descriptions, required-at-entry flags, and input source
(`enum`, fixed values, note picker, or vocabulary). `scripts/gen-forms.py`
projects that metadata into the committed Modal Forms `data.json`; it does not
change the validator grammar above.

Fields such as `summary` or `claim` are creation inputs, not necessarily
frontmatter fields. The QuickAdd writer maps them into the note body or into
structured frontmatter.

---


## Display order and grouping

The schema validates field presence and kind; display order is a shipped-vault convention so the Properties pane is scannable. Templates and deterministic emitters put fields in this order:

1. Human identity: `title` or `name`.
2. Schema identity and PI-facing state: `type`, then `lifecycle`.
3. Type-specific state: `maturity`, `certainty`, `agent_recommendation`, `loudness`, `origin`, or `ingest_status`.
4. Primary references: `citekey`, `entity`, `target`, `task_id`, `url`, `doi`.
5. Classification and relations: `research_area`, `methodology`, `topics`, `sources`, `links`, `relationships`.
6. Provenance and housekeeping: owned namespaces such as `_enrichment` / `_proposed_classification`, then labels such as `sample`, timestamps such as `created`, `updated`, `enriched_date`, and version fields.

Obsidian does not have a global property-order schema file, so the shipped templates, emitters, and Bases carry this convention directly. The `memoria-property-badges.css` snippet colors the scan-critical state fields (`lifecycle`, `ingest_status`, `loudness`, and verification status) when Obsidian exposes editable property values; the field order still carries the meaning when snippets are disabled.

---

## `lifecycle` — the one chain

Every typed document carries `lifecycle`, drawn from the **universal chain** ([ADR-50](../adr/50-universal-lifecycle-and-maturity.md)):

```text
proposed → provisional → current → retracted → archived
```

Each type's schema declares the **subset** it uses (validated as `enum:lifecycle`; the subset must be ⊆ the chain — test-enforced):

| Subset | Types |
| --- | --- |
| full chain | `source`, `thesis` |
| `proposed → current → archived` | `candidate`, `gap`, `flag`, `alert`, `work-prompt`, `code-note`, `pattern`, `eval-task`, `worklist-item` |
| `proposed → archived` | `fleeting` |
| `current → retracted → archived` | `claim`, `paper`, `dataset` |
| `current → archived` | `project`, `person`, `organization`, `venue`, `repository`, `hub`, `space`, `queue`, `maintenance`, `worker-card` |

`proposed` always means _awaiting the PI_. `retracted` is a state, not a deletion — supersession keeps the lineage (`superseded_by`). Claim queries and write-assist surfaces exclude claims with a non-empty `superseded_by` by default; include them only for lineage, audit, or supersession-history work. This lifecycle is the **PI-facing state**; the board's `status` enum is a separate, hidden execution mechanic (see [Kanban board reference](kanban-board.md)).

## `maturity` — a claim property, never a gate

Claims only: `seedling → budding → evergreen`. It describes how settled a claim is; nothing in the system blocks on it ([ADR-50](../adr/50-universal-lifecycle-and-maturity.md)).

---

## `links:` vs `relationships` — field presence

Notes (`source`, `claim`, `hub`) carry the authored `links:` map; catalog entities carry the given `relationships` map. Why the split exists and who asserts each — the authored-vs-given distinction — is owned by [Wikilink and link conventions](linking.md).

Two related fields: a `source` note's required `entity` field is a wikilink to the Catalog entity the note is about, and a `claim`'s required `sources` list holds citekeys (bibliographic provenance, not note links). The Linter's `frontmatter-link` detector checks that every wikilink in `links:` and `entity` resolves to a real note; citekeys are checked by the sweeps instead.

Project-gate argument edges may carry an optional `warrant` attribute on a
`supports` relation when the author wants to state the grounds-to-claim inference
explicitly ([ADR-79](../adr/79-argument-graph-and-warrant.md)). The schema keeps
`links:` as a map so relation values can carry either plain wikilinks or structured
edge objects.

---

## Project-gate fields

`project` and `thesis` notes add the Project gate's authored state and operation
cache ([ADR-77](../adr/77-project-gate.md), [ADR-78](../adr/78-thesis-note-type.md)):

| Field | Kind | Notes |
| --- | --- | --- |
| `scope_topics` | `list` | Topic boundary for the project map. |
| `inquiry` | `map` | PICO block: `population`, `intervention`, `comparison`, `outcome`. |
| `finer` | `map` | Answerability lens: `feasible`, `novel`, `relevant`. |
| `output_mode` | `enum` | `thesis` or `survey`. |
| `question_version` / `question_log` | `int` / `list` | Version and rationale log for question changes. |
| `gap_type` | `enum` | Project gap kind: `additive`, `conflict`, `fragility`, `structural`, `unstated-warrant`, or `refutation`. |
| `impact` / `on_path` | `int` / `bool` | Materialized structural-impact cache for Project dashboards. |
| `evidence_saturation` | `enum` | `unknown`, `unsaturated`, `saturated`, or `stale`. |
| `argument_stage` | `enum` | `cold-start`, `developing`, or `mature`. |
| `computed_at` | `date` | Timestamp for the derived cache; stale values are shown as stale, not silently current. |
| `refutation_sufficiency` / `refutation_sufficiency_at` | `bool` / `date` | PI stamp that the active thesis has faced its strongest available rebuttal; the Project operation treats this as saturation condition 3, not as a deterministic judgment. |
| `promoted_at` / `promoted_by` | `date` / `str` | Promotion provenance for a thesis. A `thesis` at `lifecycle: current` must carry `promoted_at`; proposed and provisional theses do not. |

Source notes also carry optional `evidence_level`, a CEBM-style enum
(`cebm-1` … `cebm-5`, `ungraded`) used when source appraisal becomes relevant to
Project work.

---

## The honesty-card fields

Inbox cards split into proposals (`candidate`, `gap`), verification cards (`flag`, `alert`), and work prompts (`work-prompt`) ([ADR-51](../adr/51-inbox-category-and-honesty-card.md)). Their field-level contract lives in [Inbox card fields](inbox-card-fields.md).

---

## Batch worklist fields

Worklist rows are `worklist-item` notes under `system/worklists/`. Their `lifecycle` says whether the row is still active in the vault; their separate `decision` field is the PI's batch-screening choice: `proposed`, `include`, `exclude`, `maybe`, or `archived`. `worklist` groups rows into one batch, `group` supports grouped sweeps, `rank` preserves report order, and `item_ref` points at the source/path/citekey being screened. The emitter raises one aggregate `work-prompt` for the batch, never one card per row.

---

## Other universal fields

| Field | Kind | Notes |
| --- | --- | --- |
| `type` | `literal:` | Pins the note to its schema. Set at creation; never changed. |
| `title` / `name` | `str` | Notes and cards use `title`; catalog entities use `name` (papers carry both `citekey` and `title`). |
| `created` | `date` | Optional everywhere. |
| `sample` | `bool` | Optional label for bundled tutorial notes loaded from `.memoria/samples/`; dashboards exclude `sample: true` from active-corpus views, and **Memoria: remove sample vault** archives those notes. |
| `research_area`, `methodology`, `topics` | `list` | Controlled-vocabulary classification (papers, sources, claims); values live in [Vocabulary](vocabulary.md). |
| `ingest_status` | `enum` | Paper ingest floor/progress: `tier0`, `enriched`, `complete`, or `needs-human`. |

---

## Enforcement

| Where | What |
| --- | --- |
| Pre-commit hook | Every staged `.md` note must pass its type schema; exit 1 blocks the commit (`src/.memoria/operations/integrity/linter/precommit_check.py`). |
| Daily Linter cron | The `schema-check` and `frontmatter-link` detectors monitor between commits. |
| Exemptions | Most `system/` infrastructure and vault-root navigation pages (`home.md`, `research-focus.md`, `troubleshooting.md`) are untyped and exempt. Typed system homes (`system/patterns/`, `system/eval/`, `system/worklists/`, `system/board/`) follow [Document types](document-types.md#system-types-4). |

---

## Related

- The per-document-type field tables: [Document types](document-types.md)
- The controlled classification values: [Vocabulary](vocabulary.md)
- What validates this contract: [Linter: detectors and auto-fix](linter.md)
- Where the schema files live: [On-disk layout](on-disk-layout.md)


---

<!-- source: reference/glossary.md -->

# Glossary

Term definitions for Memoria, organized by domain. One definition per term; disambiguation noted where a term has multiple senses.

---

## System

**ACP** (Agent Client Protocol) — the editor-level protocol that exposes Hermes profiles to editor chat panes. Obsidian's Agent Client pane uses ACP to talk to Hermes. Distinct from the Obsidian Local REST API (which gives Hermes vault-level read/write access).

**Co-PI** — the one conversational agent (`memoria-copi`, [ADR-48](../adr/48-copi-and-agent-consolidation.md)): a reflective thinking-partner, system explainer, and delegation front. Hard read-only across the vault (empty write scope); every write it wants goes out as a board card; the sole carrier of the Hermes memory loop.

**Operation** — deterministic, no-LLM (or LLM-free-by-default) code that runs on cron/CI or behind an MCP facade, never as a board lane. Operations compute and propose; agents judge; the PI decides. The shipped operations are listed in [Operations — the deterministic layer](../explanation/operations/README.md).

**Hermes** — the Nous Research agent runtime Memoria runs on: Kanban, profile management, MCP server connections, skills, cron, and the gateway process.

**Memoria** — the whole system: the vault, the Co-PI + four background agents, the Operations layer, the policy gate, the board, and the tooling layer (`.memoria/`).

**PI** — the human principal investigator who owns and runs the vault. Makes every approval, triage, and promotion decision. Single-user by design. (Older pages say "the human".)

**Profile** — a Hermes role with bounded permissions, skills, and tools. Memoria defines five: Co-PI, Librarian, Writer, Peer-reviewer, Engineer. See [Profile capabilities](profiles.md).

**Seven-layer architecture** — PI · Interface · Co-PI · Tasks · MCP · Operations · Vault ([ADR-46](../adr/46-seven-layer-architecture.md)): conversation at the top, deterministic code at the bottom, the board and the gate in between.

**Vault** — the Obsidian folder tree where durable knowledge lives, organized into six legal root categories: `catalog`, `notes`, `projects`, `inbox`, `spaces`, `system` ([ADR-47](../adr/47-type-first-category-folders.md)).

---

## Surfaces and navigation

**Navigator rail** — the left-pane surface for everyday navigation (`_nav.md`, [ADR-116](../adr/116-obsidian-surface-architecture.md)): **Now** over **Places**. Replaces the older per-dashboard nav rows.

**Now** — the rail's top band: what is waiting on you right now — **Needs you** (your Inbox queue), **Drift** (open integrity flags), and **Fleet** (background-worker health).

**Places** — the rail's lower band: the three durable **spaces** — Library, Knowledge, Project.

**Space** — a navigation surface that is also a dashboard-as-note (`type: space`): Library, Knowledge, Project, each embedding Bases views over the vault. "Gate" is reserved for the approval gate, never a space ([ADR-101](../adr/101-navigation-spaces-gate-reserved-for-approval.md)).

**Queue** — the **Inbox** (`type: queue`, [ADR-115](../adr/115-inbox-queue-and-retired-homepage.md)): the daily surface of agent proposals and integrity flags, reached from **Now → Needs you**; main view **Needs me**. Clearing it to empty is the goal.

**Maintenance** — the weekly structural-debt surface (`type: maintenance`): Drift watch, Loose ends, the worker board, and "new this week".

**Rail health band** — the count the rail's **Now** shows for open `flag` / `alert` cards; non-zero means structural debt is waiting in Maintenance.

**System dashboard** — one of the read-only, Dataview-backed notes in `system/dashboards/` (consolidated to five in [ADR-118](../adr/118-dashboard-consolidation.md)); the spaces and Maintenance carry the action surfaces.

**Home** — `home.md`, the fresh-vault launch screen — not a navigation front door (the homepage front door was retired in [ADR-115](../adr/115-inbox-queue-and-retired-homepage.md)).

---

## Board and delegation

**Card** — a task on the Hermes Kanban board. Carries `status`, `assignee`, retry count, and a handoff summary. Lives in `kanban.db`, projected into `system/board/`.

**Ceiling** — a lane's `routing.write_scope` in its lane-override: the outer bound on where its writes may land. A card's `allowed_paths` may _narrow_ but never _widen_ it (lane = ceiling, payload = floor); the tasks MCP refuses widening delegations and the policy MCP re-checks per write.

**Dispatcher** — the Hermes component that polls the board every 60 seconds and claims `ready` cards for matching-lane profiles. Makes no quality or approval decisions.

**Handoff payload** — the self-contained block that provisions the next worker; its fields are specified in the [Kanban board reference](kanban-board.md).

**Lane** — a background agent's execution path on the board; a lane _is_ an `assignee` value. Four lanes: Librarian, Writer, Peer-reviewer, Engineer. The Co-PI has no lane; operations run off the board.

**Card vs task** — a *task* is a unit of delegated work; the *card* (`worker-card`) is its representation on the board. One task becomes one card — the same split as a Jira *work item* rendered as a Kanban *card*.

**Worklist** — the batch surface for high-cardinality decisions ([ADR-54](../adr/54-two-decision-kinds-batch-worklists.md)): instead of one card per item, like decisions queue into one `system/worklists/` batch where each `worklist-item` row has a `decision` field the PI can sweep in Bases.

---

## Notes and lifecycle

**Golden copy** — the canonical, hash-manifested copy of every system file at `.memoria/golden/`, staged by the installer ([ADR-55](../adr/55-src-scaffold-populate-golden-copy.md)). The Linter checks drift against it and can restore from it (propose-only by default).

**Honesty card** — an Inbox proposal (`candidate` / `gap`) carrying the honesty body and **never a verdict** ([ADR-51](../adr/51-inbox-category-and-honesty-card.md)); verification cards (`flag` / `alert`) are the complement, leading with the `finding`. The honesty-card and verification-card field contracts are specified in [Frontmatter fields](frontmatter.md).

**Hub** — a review-gated structure note in `notes/hubs/` aggregating a topic's members and links ([ADR-50](../adr/50-universal-lifecycle-and-maturity.md)).

**Lifecycle vs maturity** — two different axes, never interchangeable ([ADR-50](../adr/50-universal-lifecycle-and-maturity.md)). `lifecycle` is the one universal chain (the PI-facing state of any item); `maturity` is a claim **property** describing how settled it is — never a gate. Both chains and their values are specified in [Frontmatter fields](frontmatter.md).

**Links vs relationships** — the two kinds of connection: authored `links:` edges on notes versus given `relationships` edges on catalog entities. The distinction and its rationale are explained in [Wikilink and link conventions](linking.md); the field contract is specified in [Frontmatter fields](frontmatter.md).

**Document type** — one of the 25 types defined in `.memoria/schemas/types/`; the full roster, categories, and folder homes are in [Document types](document-types.md).

**Pattern** — a curated prompt-transformation stored as data in `system/patterns/` ([ADR-53](../adr/53-pattern-library.md)), typed and lifecycle-gated, executed only through the patterns MCP runner (one audited chokepoint; gated output targets degrade to dry-run).

**State** — not a field name on its own; use the specific field. A note's state is its **`lifecycle`** (`proposed → … → archived`, [ADR-50](../adr/50-universal-lifecycle-and-maturity.md)); a board card's execution state is its **`status`** (`triage → … → done`); review carries **`review_status`**, ingest **`ingest_status`**, and the operational-health dashboard tracks **skill state**. Prefer the precise field name over a bare "state" wherever one of these is meant. Field contracts are specified in [Frontmatter fields](frontmatter.md).

---

## Policy and audit

**Audit log** — the append-only JSONL trail of every policy decision at `system/logs/audit.jsonl`. Feeds the audit-log dashboard.

**Extraction-uncertainty flag** — the near-tie rule ([ADR-56](../adr/56-extraction-uncertainty-flag.md)): when cross-source identity agreement falls below the calibration floor (0.85), ingest raises an Inbox `flag` instead of merging silently.

**Lane-override file** — per-lane YAML at `.memoria/lane-overrides/<lane>.yaml` declaring `policy.allow`/`deny`/`require` and `routing` (invocation, external-API policy, write scope). Read by the policy MCP.

**Policy MCP** — the runtime write-gate: intercepts every vault action, returns `allow` / `allow_with_log` / `deny` / `dry_run`, and appends to the audit log. Enforced in-process by the fail-closed `memoria-policy-gate` plugin. See [Policy MCP](policy-mcp.md).

**Review-gated zone** — a folder where the policy MCP degrades all agent writes to `dry_run` regardless of lane policy: `notes/claims/` and `notes/hubs/`, loaded from `folders.yaml`.

---

## Verdicts

| Name | Values | Set by | Scope |
| --- | --- | --- | --- |
| `agent_recommendation` | `inconclusive` / `issues-found` / `clean` | Peer-reviewer / operations | the soft verdict on a verification card — advisory only |
| verdict band | `PASS` / `REVIEW` / `FAIL` | Linter operation | structural rollup over the detectors — the rollup rule is owned by [Linter: detectors and auto-fix](linter.md) |
| `certainty` | `confident` / `likely` / `unsure` | proposing agent | the calibrated confidence on an honesty card |

**Trust score** — a 0–100 per-lane operational-health aggregate on the fleet-health dashboard; its inputs and bands are specified in [Dashboards](dashboards.md).

---

## Related

- Frontmatter fields these terms name: [Frontmatter fields](frontmatter.md)
- The document types referenced throughout: [Document types](document-types.md)
- Lane and profile terms: [Profile capabilities](profiles.md)
- Board and delegation terms: [Kanban board reference](kanban-board.md)


---

<!-- source: reference/hermes-cli.md -->

# Hermes CLI

Every `hermes …` command-line operation: the per-profile research skills, the administrative commands (profiles, skills, cron), and the Kanban board commands. These are the **terminal** surface; the primary day-to-day surface is Obsidian's spaces, Bases views, and `Memoria:` command palette. The Agent Client pane is the conversational route for shaping unclear work, not the first or only way to trigger tasks. For the in-Obsidian palette see [Obsidian command palette](obsidian-command-palette.md).

Command structure: `hermes <command> [subcommand] [args]` — runs from any directory; Hermes resolves the vault path from the profile's `config.yaml`. Per-profile sessions run as `hermes -p memoria-<name> chat` (or `hermes -p memoria-copi acp` for the Co-PI Agent Client pane).

---

## The profile set

Five profiles: `memoria-copi`, `memoria-librarian`, `memoria-writer`, `memoria-peer-reviewer`, `memoria-engineer` (see [Profile capabilities](profiles.md)).

---

## Skill names

Lane skills use the **`<task>-<verb>-<object>`** kebab-case convention — the task/lane is the first token, the verb comes from a closed set, and the object is the artifact, so a skill's name says which task delegates it (e.g. `catalog-enrich-record`, `link-suggest-claim`). Co-PI conversational skills that are not lane work use bare `<verb>-<object>` names (`explore-framings`, `route-task`, `explain-system`). One spelling is used everywhere — in prose, on disk, and at the `-s` load flag.

So `catalog-enrich-record` lives in `skills/catalog-enrich-record/` and loads as `hermes -p memoria-librarian chat -s catalog-enrich-record`. When serialized as an MCP tool the separators collapse to underscores: `catalog_enrich_record`.

The on-disk registry under `src/.memoria/profiles/<profile>/skills/` matches the table below exactly (enforced by `tests/test_profiles.py`):

| Actor | Skills (all shipped in `src/.memoria/profiles/<profile>/skills/`) |
| --- | --- |
| **Co-PI** (pane) | `ask-question-source` · `ask-read-lens` · `explore-framings` · `route-task` · `explain-system` |
| **Librarian** (catalog · extract · link · map) | `catalog-find-source` · `catalog-enrich-record` · `catalog-classify-source` · `catalog-rank-candidate` · `extract-stub-claim` · `extract-flag-distill` · `link-suggest-claim` · `link-surface-tension` · `map-scope-project` · `map-report-coverage` · `map-cluster-corpus` · `map-seed-canvas` · `map-graph-claims` · `map-canvas-hub` |
| **Writer** (draft) | `draft-write-section` · `draft-outline-argument` · `draft-score-outline` · `draft-bind-citation` |
| **Peer-reviewer** (verify) | `verify-check-citation` · `verify-trace-claim` · `verify-card-gap` · `verify-propose-fix` |

Deterministic operation entrypoints are MCP tools, cron wrappers, or repo scripts, not Hermes chat skills. Use [Operations](operations.md), [Ingest routing](ingest.md), [Search](search.md), [Clustering](clustering.md), [Linter](linter.md), and [Sweeps](sweeps.md) for their current commands. Two map-lane entries from the design's full registry remain **deferred, not shipped**: `map:score-writability` / `map:score-readiness` are later Project-gate expansion work (calibration-gated). The graph-visualization pair `map-graph-claims` / `map-canvas-hub` now ship (#381) — both emit propose-class JSON Canvas over the cluster operation's typed graph, with no score or calibration.

Every shipped `SKILL.md` carries a machine-checkable `metadata.memoria` block (`skill_id`, `profile`, `lane`, `mcp_tools`, `write_scope`, `outputs`): the MCP tools must resolve against the tool registry (`src/.memoria/tool-registry.yaml`) and the write scope must sit inside the lane-override ceiling — `tests/test_profiles.py` enforces both.

---

## The MCP tool surface

Tools the profiles call (and you can exercise directly when debugging — each server also runs one-shot from the CLI):

| Server | Tool | Does |
| --- | --- | --- |
| tasks | `delegate_route_task(lane, goal, context, allowed_paths, expected_outputs, review_checks, idempotency_key)` | The Co-PI's delegation path: validates the handoff against the lane ceiling, then creates the board card. See [Kanban board reference](kanban-board.md). |
| cluster | `cluster_build_graph(seed)` | NetworkX over authored `links:` + given `relationships` → nodes, typed edges, communities, centrality, layout. Read-only; params echoed. |
| cluster | `cluster_model_topics(folder, min_cluster_size)` | BERTopic over note text → topics, doc-topic map, outliers (needs the opt-in cluster stack). |
| cluster | `cluster_emit_canvas(scope, out, seed)` | Writes the claim-debate JSON Canvas artifact (staging-only) — the Librarian's map lane (`map-seed-canvas`). |
| patterns | `patterns_list(mode)` | Runnable (`lifecycle: current`) patterns, optionally filtered by `library` / `project`. |
| patterns | `patterns_run(pattern_id, input_text, input_ref)` | Compose preamble + pattern + input → the prompt + staging target; gated targets degrade to dry-run; every run provenance-logged to `system/logs/patterns.jsonl`. |
| ingest | `ingest_pipeline(citekey, enrich, pdf_path)` | The deterministic draft bundle with the two LLM holes. See [Ingest routing](ingest.md). |
| policy | `check_permission` / `complete_write` | The write gate. See [Policy MCP](policy-mcp.md). |

---

## Board management

| Command | What it does |
| --- | --- |
| `hermes kanban list` | List all cards on the board. |
| `hermes kanban show <card-id>` | Full card state: status, retry count, blocker reason, handoff summary. |
| `hermes kanban create "<title>" --assignee memoria-<name>` | Create a card (the tasks MCP shells out to this same command; `--idempotency-key` dedupes). |
| `hermes kanban specify <id>` | Flesh out a `triage` card into a concrete spec → `todo`. |
| `hermes kanban release <id>` | Release a `todo` card to `ready` for dispatch. |
| `hermes kanban dispatch` | Run one dispatcher pass. |
| `hermes kanban unblock <id>` | Clear a `blocked` card → `ready`. |
| `hermes kanban edit <id> --assignee <lane>` | Correct an unresolvable assignee. |
| `hermes kanban archive <id> --reason "<text>"` | Archive a terminal card with an explicit reason. |
| `hermes kanban decompose <id>` | Fan out a `triage` card into child task cards. |

---

## Profile management

| Command | What it does |
| --- | --- |
| `hermes profile list` | List registered profiles: alias, status, installed path. |
| `hermes profile install <dir> --name <name> --alias --force --yes` | Install a profile from a staged directory. In practice use `scripts/install.sh --profiles-only` or `scripts/install.ps1 -ProfilesOnly` — the installer renders Python, vault, qmd, and model tokens, writes deployed `config.yaml`, and seeds `.env` first. |
| `hermes profile show <alias>` | A profile's `SOUL.md`, MCP servers, skills, and `.env` key names (values redacted). |
| `hermes profile remove <alias>` | Remove a profile registration. Does not delete the vault source under `.memoria/profiles/`. |

---

## Skills

| Command | What it does |
| --- | --- |
| `hermes skills list` | List installed skills. |
| `hermes skills install <id> --yes` | Install a hub skill (the installer fetches `obsidian-markdown` and `qmd` this way). |

---

## Scheduled tasks (cron)

| Command | What it does |
| --- | --- |
| `hermes cron list` | List scheduled tasks with next-run times (you should see the five crons the installer wires — see [Installer (bootstrap)](installer.md)). |
| `hermes cron create '<spec>' --script <name>.sh --no-agent --name <name> --deliver local` | The shape the installer uses for the deterministic crons. |
| `hermes cron run <task-name>` | Run a scheduled task immediately. |
| `hermes cron enable <task-name>` / `disable <task-name>` | Toggle a task without removing it. |

---

## Related

- In-Obsidian command palette (`Memoria:` entries): [Obsidian command palette](obsidian-command-palette.md)
- The lane identifiers the commands map to: [Profile capabilities](profiles.md)
- The delegation path behind the board: [Kanban board reference](kanban-board.md)
- What the installer wires for you: [Installer (bootstrap)](installer.md)


---

<!-- source: reference/inbox-card-fields.md -->

# Inbox card fields

Schema fields for Inbox cards under `inbox/`. The source of truth is `src/.memoria/schemas/types/`; this page is the lookup view for the PI-facing card shapes.

## Shared card fields

| Field | Kind | Applies to | Meaning |
| --- | --- | --- | --- |
| `type` | `literal` | All cards | Pins the note to its schema. |
| `lifecycle` | `enum` | All cards | `proposed`, `current`, or `archived`. |
| `title` | `str` | All cards | Human-readable card title. |
| `raised_by` | `str` | Optional on all cards | Profile, operation, or process that raised the item. |
| `loudness` | `enum` | Optional on all cards | `quiet`, `notice`, `alert`, or `block`. `quiet`/`notice` stay pull-only; `alert`/`block` create a Telegram push record when written through the shared card writer; open `block` cards pause delegation and review-gated promotion until resolved. |
| `created` | `date` | Optional on all cards | Creation date. |

## Proposal cards

`candidate` and `gap` cards carry an argument, not a verdict.

| Field | Kind | Required | Meaning |
| --- | --- | --- | --- |
| `action` | `str` | Yes | What the PI would be accepting. |
| `argument_for` | `str` | Yes | The agent's case for the action. |
| `argument_against` | `str` | Yes | The agent's strongest honest self-rebuttal. |
| `what_tipped_it` | `str` | Yes | Why the item was raised anyway. |
| `certainty` | `enum` | Yes | `confident`, `likely`, or `unsure`. |
| `citekey` | `str` | Optional on `candidate` | Bibliographic item the card points at. |
| `url` | `str` | Optional on `candidate` | External source URL. |

## Verification cards

`flag` and `alert` cards lead with the finding because the verdict is not implied by the card existing.

| Field | Kind | Required | Meaning |
| --- | --- | --- | --- |
| `finding` | `str` | Yes | What the check found. |
| `agent_recommendation` | `enum` | Required on `flag`; optional on `alert` | `inconclusive`, `issues-found`, or `clean`. |
| `target` | `str` | Required-any on `flag`; optional on `alert` | Vault path or artifact the card points at. |
| `citekey` | `str` | Required-any on `flag` | Bibliographic item the card points at. |

## Work prompts

`work-prompt` cards tell the PI what completed or needs attention. They carry no recommendation field.

| Field | Kind | Required | Meaning |
| --- | --- | --- | --- |
| `action` | `str` | Yes | What the PI should do. |
| `what_happened` | `str` | Yes | What finished or triggered the prompt. |
| `target` | `str` | Required-any | Output path or artifact to review. |
| `task_id` | `str` | Required-any | Board card the prompt is about. |
| `lane` | `str` | Optional | Lane that completed the work. |

## Related

- The universal field grammar: [Frontmatter fields](frontmatter.md)
- The board state machine: [Kanban board reference](kanban-board.md)
- Why these shapes exist: [The honesty card](../explanation/kanban-board/card-schema.md)


---

<!-- source: reference/ingest.md -->

# Ingest routing

The ingest operation (`src/.memoria/operations/processing/ingest`): the deterministic spine that turns a citekey into a draft `paper` catalog bundle, the Catalog outputs it plans, the uncertainty floor, and the recovery sweeps. The Librarian reaches it over the ingest MCP (`src/.memoria/mcp/ingest_mcp.py`) — its lane has no terminal — fills the two LLM holes, and performs the gated writes; the operation itself writes no vault notes.

---

## The pipeline

`src/.memoria/operations/processing/ingest/runner.py` chains four deterministic stages into a single **draft bundle**:

| Stage | Module | Does |
| --- | --- | --- |
| Tier-0 capture | `ingest_paper.py` | Identity + route + captured frontmatter from the local `.bib` alone — the offline, nothing-lost floor. |
| Tier-1 resolve/merge | `resolve_merge.py` | Semantic Scholar + OpenAlex (co-primary) + Crossref + PubMed/NCBI, merged per-field best-source-wins **with provenance**; PubMed contributes PMID/PMCID, publication types, and MeSH terms when available; references = the union across sources, deduped by DOI. |
| Tier-1 classify | `classify.py` | `research_area` (and a `methodology` facet when derivable) from the OpenAlex topics already in the merged payload — automated, audited, flag-on-ambiguity ([ADR-54](../adr/54-two-decision-kinds-batch-worklists.md)). Also proposes project membership from the optional `.memoria/project-hints.yaml` ([ADR-15](../adr/15-project-membership-from-topic-hint.md)). No extra network call; without enrichment it is a no-op. |
| Tier-1 extract | `extract.py` | Full text, open-access-first: Unpaywall OA PDF → PMC JATS → local Zotero PDF via pymupdf4llm. OA and local PDFs pass through the same deterministic coherence check (chars/page, replacement-char ratio, word ratio) so only good text reaches the model; non-English text is flagged, never auto-failed. |
| Tier-1 link | `link.py` | The knowledge-graph plan: entity find-or-create keyed on stable IDs (ISSN / ORCID / ROR — never name-merged) + cites edges by local DOI/arXiv match. |

The bundle arrives **with two holes** the Librarian fills: `_proposed_classification` (LLM #1 — its `projects` sub-key is pre-filled deterministically from the optional project hints, [ADR-15](../adr/15-project-membership-from-topic-hint.md)) and the `[!brief]` comparative read (LLM #2). `ingest_pipeline(citekey, enrich=True, pdf_path="")` is the MCP tool; without `enrich` only Tier-0 runs.

### Catalog outputs

The link plan is what populates the Catalog ([ADR-52](../adr/52-links-vs-relationships.md)):

- **Entities** — find-or-create records in `catalog/` (`paper`, `person`, `organization`, `venue`, `dataset`, `repository`), keyed on the stable ID so same-named entities never merge. Entities without a stable ID are recorded by name only, never node-created.
- **Relationships** — the operation writes only the **given** `relationships` edges on those entities (`cited_by`, `authored_by`, `published_in`, …), applied bidirectionally by the worker; it never writes the PI's authored `links:`. The field contract behind the given-vs-authored split is in [Frontmatter fields](frontmatter.md).

---

## The uncertainty floor

The operation never merges identities silently ([ADR-56](../adr/56-extraction-uncertainty-flag.md)). `resolve_merge.py` scores **cross-source identity agreement** (title + year across Semantic Scholar, OpenAlex, Crossref, and PubMed when they resolve) in `[0,1]`; the floor comes from `src/.memoria/schemas/calibration.yaml` (`entity_resolution.confidence_floor: 0.85`, drift-bound — recalibrate on model/source-version change).

Below the floor, the bundle carries a `flag_needed` block instead of a silent best-source-wins merge: the Librarian raises a **near-tie `flag` card** in the Inbox ("Identity disagreement on `<citekey>`", with the agreement score and the disagreements), and the PI decides. One source found = trusted (1.0) — the floor measures _disagreement_, not coverage.

---

## Automated classification

classify is **not a gate** ([ADR-54](../adr/54-two-decision-kinds-batch-worklists.md)): low-stakes metadata a human would rubber-stamp is automated, audited, and correctable. `classify.py` reads the **scored OpenAlex topics already in the enrichment payload** (no new network call), rolls them up to their subfield (the research-area granularity, best score per area), and decides:

- **Clear winner** — the top score clears the floor _and_ beats the runner-up by the near-tie margin → `research_area` is applied silently. A `methodology` facet is applied whenever it is derivable from the S2 publication types (Review, MetaAnalysis, ClinicalTrial, CaseReport, Dataset — deterministic, independent of topic ambiguity).
- **Genuine ambiguity** — below the floor or within the margin → the field **stays unset** and ingest raises **one** Inbox `flag` card: what was ambiguous and the top candidates with scores, never a verdict (the [ADR-51](../adr/51-inbox-category-and-honesty-card.md) honesty rules).
- **No data** (enrichment off, or no topics resolved) → a no-op.

The thresholds live beside the entity-resolution floor in `src/.memoria/schemas/calibration.yaml`, under the same drift-bound discipline:

| Knob | Default | Means |
| --- | --- | --- |
| `classify.confidence_floor` | `0.6` | Below this top-candidate score, nothing is applied. |
| `classify.near_tie_margin` | `0.15` | The top candidate must beat the runner-up by at least this much. |

Every applied or flagged decision appends **one JSONL audit line** to `system/logs/classify.jsonl` (timestamp, run id, citekey, decision, the candidates with scores, the reason, and the thresholds in force) — the audit trail that makes the automation correctable: the PI edits the frontmatter, never approves a card.

### Project membership proposal ([ADR-15](../adr/15-project-membership-from-topic-hint.md))

When an optional `.memoria/project-hints.yaml` exists ([Configure project hints](../how-to-guides/setup/configure-project-hints.md)), the classify stage also **proposes** project membership by simple overlap: each project's `primary_topics` is scored against the paper's OpenAlex topic names and subfields (both kebab-case normalized; a hint matches a signal when equal to it or when all the hint's tokens appear in it). Every project with at least one overlapping hint topic is proposed, ranked by overlap count, into `_proposed_classification.projects` — confirmed or corrected by the PI at triage, **never** applied to the `projects` field. Each decision (proposed or no-match) appends one `stage: project_hints` line to the same `system/logs/classify.jsonl`, carrying the candidates with their matched topics and overlap counts ([ADR-51](../adr/51-inbox-category-and-honesty-card.md) honesty — counts, not confidence). An absent hints file means fully manual project tagging (a silent no-op); a malformed one warns once on stderr and degrades to manual.

---

## Derived artifacts

The ingest MCP persists the un-gated derived artifacts the agent can't:

| Artifact | Path | Notes |
| --- | --- | --- |
| Full-text extract | `.memoria/data/extracts/<citekey>.md` | Outside the Librarian's write lane; the paper note's `extract_path` points here (the `extract-path-broken` detector checks it). |
| Capture-intake anchor | `system/logs/capture-intake.jsonl` | One append-only line per capture, written **before** enrichment — the durability anchor. Zotero QuickAdd capture also writes a schema-valid Tier-0 `catalog/papers/<citekey>.md` stub immediately, so the Catalog reflects the capture even before the Librarian enriches it. |
| Classify audit | `system/logs/classify.jsonl` | One append-only line per classify decision (applied or flagged) and per project-membership proposal (`stage: project_hints`, [ADR-15](../adr/15-project-membership-from-topic-hint.md)) — see Automated classification above. |

---

## Recovery sweeps

Re-ingest and retraction maintenance are deterministic sweep operations rather than ingest stages. Their command-level contract lives in [Sweeps](sweeps.md).

---

## Frontmatter written at ingest

| Field | Value |
| --- | --- |
| `type` / `lifecycle` | `paper` / `current` from creation — Catalog facts don't queue; the pending classification lives in `_proposed_classification` + an Inbox card, not in the lifecycle. |
| `citekey`, `title`, `doi`, `authors`, `year`, `venue`, `url` | From the merged record, with per-field provenance. |
| `relationships` | The given edges from the link plan. |
| `research_area`, `methodology` | Applied by the automated classify stage when the decision is clear; left unset (plus one Inbox flag) on genuine ambiguity. |
| `extract_path`, `pdf_uri` | The extract store path and the Zotero PDF URI. |
| `_proposed_classification` | The Librarian's proposal (LLM hole #1), promoted by the PI at classify; its `projects` sub-key is the deterministic [ADR-15](../adr/15-project-membership-from-topic-hint.md) hint-overlap proposal. |

---

## Related

- The schemas and field kinds these notes must satisfy: [Frontmatter fields](frontmatter.md)
- The lane that runs the pipeline: [Profile capabilities](profiles.md)
- The crons that wire the sweeps: [Installer (bootstrap)](installer.md)
- The cards the sweeps and flags land in: [Kanban board reference](kanban-board.md)


---

<!-- source: reference/installer.md -->

# Installer (bootstrap)

The bootstrap installers (`scripts/install.ps1` for native Windows production; `scripts/install.sh` for Linux/WSL testing): what each step does, the flags, and the crons they wire. The install model is **scaffold → populate → golden copy** ([ADR-55](../adr/55-src-scaffold-populate-golden-copy.md)): the repo ships the vault under `src/`, the installer creates the schema-checked folder skeleton in your runtime vault, fills it from `src/`, and stages a restorable golden copy of every system file.

Safety posture: no silent privilege escalation (every `sudo` is printed and confirmed), `--dry-run` echoes everything and touches nothing, and the recommended invocation is inspect-first (`curl -o install.sh`, read it, then run it).

---

## Flags

| Flag | Effect |
| --- | --- |
| `--vault DIR` | Install the runtime vault here (default `~/Memoria`; prompted otherwise). Pick a folder outside any cloud-synced tree. |
| `--profiles-only` | Skip fresh vault creation; just deploy MCP deps, the five profiles, and crons from an existing vault after editing profile source or adding keys to `~/.hermes/.env`. |
| `--only NAMES` | Restrict the profile step to a comma-separated subset (e.g. `--only memoria-librarian`); pairs with `--profiles-only`. |
| `--no-apps` / `-NoApps` | Skip the Obsidian guidance (headless / server installs). |
| `--dry-run` | Print every command that would run; change nothing. |
| `--yes` / `-y` | Non-interactive: accept all defaults, no prompts (CI). |

## Environment overlays

| Variable | Effect |
| --- | --- |
| `MEMORIA_ENV=prod` | Default. Renders the shipped Kilo Code gateway model tiers: Co-PI and Peer-reviewer on Opus, Writer on Sonnet, Librarian and Engineer on Haiku. |
| `MEMORIA_ENV=test` | Linux/WSL test overlay. Renders every profile to an OpenAI-compatible local endpoint, defaulting to `custom` + `http://127.0.0.1:11434/v1` + `qwen2.5:7b` with `context_length` and `ollama_num_ctx` set to `65536`. |
| `MEMORIA_MODEL_BASE_URL` | Overrides the local endpoint when `MEMORIA_ENV=test`. |
| `MEMORIA_MODEL_NAME` | Overrides the local model name when `MEMORIA_ENV=test`. |
| `MEMORIA_MODEL_CONTEXT_LENGTH` | Overrides the rendered local context length when `MEMORIA_ENV=test`. |

The local model overlay changes only the Hermes model block. The Obsidian MCP remains verified loopback HTTPS and still requires `OBSIDIAN_MCP_PORT`, `OBSIDIAN_MCP_SSL_VERIFY`, and `OBSIDIAN_API_KEY` in each profile's `.env`.

---

## The install flow

| Step | What happens |
| --- | --- |
| 1. Prerequisites | Ensures `git` and `pandoc` (Hermes provisions uv-Python, Node, ripgrep, ffmpeg itself). |
| 2. Fetch the repo | Clones `memoria-vault` to a temp staging dir (or uses a local checkout). |
| 3. Hermes | Runs the official Hermes installer for the host OS. On Windows this is Hermes's native PowerShell installer; on Linux/WSL this is the shell installer. |
| 4. Scaffold + populate | Copies `src/` into a new vault, then recreates the empty-folder **skeleton** (the `SKELETON_DIRS` list mirrors `folders.yaml`'s `skeleton:` block). A full install refuses an existing Memoria vault; use a fresh target for a new release. |
| 4a. Golden copy | Stages the shipped system files and SHA-256 manifest at `.memoria/golden/` — the Linter's restore source (`golden_restore.py stage`). |
| 4b. Git hooks | If the vault is a git repo, wires `.memoria/operations/integrity/linter/pre-commit` into `.git/hooks/pre-commit` so staged notes pass schema validation, and `.githooks/post-commit` into `.git/hooks/post-commit` so committed project drafts enqueue Peer-reviewer verification. (The vault is _your_ repo; the installer never `git init`s for you.) |
| 4c. Obsidian CSS snippets | Preserves `.obsidian/appearance.json` but reconciles `enabledCssSnippets` so the Memoria link-color and property-badge snippets are on by default. Missing shipped snippet files are copied back; other appearance settings are left alone. |
| 5. MCP dependencies + package | Creates the vault-local venv at `.memoria/.venv`, pip-installs `mcp/requirements.txt`, and installs the Memoria package from the release root (`pip install <release_root>`). The **clustering stack is opt-in**: a confirm prompt offers `requirements-cluster.txt` (bertopic → torch, ~2 GB); skipping it leaves graph tools working and `cluster_model_topics` erroring cleanly. |
| 5b. qmd search engine | Installs `@tobilu/qmd` (npm, Node ≥22) if missing, registers the vault as a qmd collection (BM25 works immediately), and offers the ~2GB vector-model embed as an opt-in. Resolves the absolute binary path into each profile's `{{QMD}}` slot — a conda package also ships a `qmd`, so PATH lookup is unsafe. |
| 6. Profiles | Deploys the **five** profiles (`memoria-copi`, `-librarian`, `-writer`, `-peer-reviewer`, `-engineer`): substitutes `{{PYTHON}}` (the venv interpreter), `{{VAULT_PATH}}`, `{{QMD}}`, and the `{{MODEL_*}}` slots into each `config.yaml`, verifies the generated Obsidian MCP config still uses `https://127.0.0.1:${OBSIDIAN_MCP_PORT}/mcp` with `ssl_verify: ${OBSIDIAN_MCP_SSL_VERIFY}`, runs `hermes profile install`, refreshes the rendered deployed `config.yaml`, reconciles the source-owned `skills/` directory (including clearing stale bundled skills from profiles that opt out), bootstraps `.env` from `.env.EXAMPLE`, propagates shared secrets from `~/.hermes/.env` (profile runs read only their own `.env`), and deploys the `memoria-policy-gate` write-gate plugin per lane. |
| 7. Skills | Clones the K-Dense bundle, verifies bundled official Hermes skills, installs the official optional `research/qmd` skill, and installs the `obsidian-markdown` hub skill. |
| 8. Obsidian | Guided, not silent: Windows offers `winget`; Linux offers the Flatpak/AppImage path. **Zotero is no longer provisioned by the Linux test installer** — Windows production still offers winget guidance because Zotero is the expected production bibliography surface. |
| 9. Secrets + next steps | Prints where keys go (`~/.hermes/.env` -> re-run `--profiles-only` to propagate) and the first-session checklist (use the left-pane rail to open Library, then open the Agent Client pane when you want conversational help). |

---

## The crons it wires

All five are deterministic, no-LLM `hermes cron … --no-agent` jobs; the wrappers are substituted into `~/.hermes/scripts/` and the job creation is idempotent.

| Cron | Schedule | Runs | Effect |
| --- | --- | --- | --- |
| `memoria-board-export` | `* * * * *` | `board_export.py` | Projects the live kanban board into `system/board/` and appends its telemetry logs (metrics aggregation is the separate weekly `memoria-metrics` job). |
| `memoria-sweeps` | `*/15 * * * *` | `operations/cleanup/reconcile.py` | Recovers stalled captures: enqueues idempotent re-ingest cards (see [Ingest routing](ingest.md)). |
| `memoria-lint` | `0 6 * * *` | `operations/integrity/linter/detectors.py` + `golden_restore.py check` | The daily monitor: structural detectors + golden-copy drift (see [Linter: detectors and auto-fix](linter.md)). |
| `memoria-metrics` | `30 6 * * 1` | `mcp/metrics_aggregate.py` | Weekly fleet health: rolls the audit log, the Hermes board, and lint findings into per-lane trust-score notes under `system/metrics/` (read by the fleet-health dashboard). |
| `memoria-eval` | `0 7 1 */3 *` | `operations/telemetry/eval/eval_score.py` + `eval_dispatch.py` | Quarterly vault-eval: scores the previous quarter's run into `system/metrics/eval/runs.jsonl`, then fans the `system/eval/` gold set out as one idempotent eval card per task — diagnostic, never gating (see [Vault eval](vault-eval.md)). |

A further wrapper ships for the monthly Retraction Watch refresh (`src/.memoria/scripts/retraction-refresh-cron.sh` — `retraction.py --refresh` + `--sweep`).

---

## What the user still supplies

| Item | Where |
| --- | --- |
| `KILOCODE_API_KEY` (production model access; not used by the `MEMORIA_ENV=test` local model block), `OBSIDIAN_API_KEY` + `OBSIDIAN_MCP_PORT` + `OBSIDIAN_MCP_SSL_VERIFY` (Local REST API HTTPS/native MCP), `OPENALEX_API_KEY` (required since 2026-02) | `$env:LOCALAPPDATA\hermes\.env` on Windows or `~/.hermes/.env` on Linux/WSL, then rerun the matching installer with `-ProfilesOnly` / `--profiles-only` to propagate |
| Obsidian first launch | Open the vault folder; disable Restricted mode so the bundled plugins load |
| git binary + git in the vault | The host or sandbox must have `git` on `PATH`; then initialize the runtime vault with `git init && git add -A && git commit`. obsidian-git, the pre-commit hook, verify-on-commit, rollback, and history need a real repo. |
| Zotero (optional) | The bring-in-a-paper tutorial on the docs site |

---

## Related

- What the populated tree looks like: [On-disk layout](on-disk-layout.md)
- The five profiles the install deploys: [Profile capabilities](profiles.md)
- The gate and plugin the installer wires per lane: [Policy MCP](policy-mcp.md)


---

<!-- source: reference/integrations.md -->

# External integrations

APIs and tools the Librarian profile reaches during ingest and enrichment. All external calls are gated by `external_api_policy: explicit_only` in the Librarian lane-override — a skill must declare its API usage explicitly before it can invoke it.

---

## Bibliographic backbone

| Integration | Role | Notes |
|---|---|---|
| **Zotero + Better BibTeX** | Source of truth for citekeys, PDFs, and bibliographic metadata | Every citable source must have a Zotero entry with a pinned BBT citekey before ingest. See [Citekey naming convention](../adr/06-citekey-naming-convention.md). |
| **`.memoria/memoria.bib`** | Auto-exported BibTeX from Zotero | Librarian reads this; never writes to it. Excluded from git (user-specific). |

---

## Metadata enrichment APIs

Used during `enrich` to populate or refresh `paper` catalog-entity fields.

| API | What it provides | Key fields populated |
|---|---|---|
| **OpenAlex** | Citation graph, concept tags, institutional affiliations, open-access links | `cited_by_count`, `concepts`, `oa_url`, `institutions` |
| **Semantic Scholar** | Semantic citation context, paper recommendations | `tldr`, `citation_contexts`, `recommendations` |
| **Crossref** | DOI resolution, reference metadata, publication venue | `doi`, `journal`, `volume`, `issue`, `pages` |
| **PubMed** | Biomedical coverage, MeSH terms, abstract | `mesh_terms`, `pmid`, `abstract` |
| **Unpaywall** | Open-access PDF discovery | `pdf_uri` (OA version) |
| **Scite** | Supporting / contrasting / mentioning citation signals | `scite_supporting`, `scite_contrasting`, `scite_mentioning` |
| **DataCite** | Dataset DOIs and metadata | `doi`, `data_url` for dataset items |

### API keys and rate limits

Enrichment and search calls are rate-limited (or fail outright) without a free API key. Register a key per service and add it to the Librarian's `.env` during [Set up Hermes](../how-to-guides/setup/set-up-hermes.md).

| Service | Where to register | Rate without key | Rate with free key |
| --- | --- | --- | --- |
| OpenAlex | openalex.org/settings/api | Fails (required since Feb 2026) | 10 req/sec |
| Semantic Scholar | semanticscholar.org/product/api | 1 req/sec | 10 req/sec |
| PubMed | ncbi.nlm.nih.gov/account/ | 3 req/sec | 10 req/sec |
| GitHub | github.com/settings/tokens (`public_repo` scope) | 60 req/hr | 5,000 req/hr |

---

## Entity resolution

Used during enrichment to link paper notes to person, organization, and venue entities.

| API | Role |
|---|---|
| **ORCID** | Unique author identifiers; links `paper` → `person` |
| **ROR (Research Organization Registry)** | Institution identifiers; links to `organization` |
| **GitHub API** | Repository metadata for `repository` (tools, packages, code) |

---

## Vault access and agent interface

| Integration | Role |
|---|---|
| **Obsidian Local REST API** (native MCP, verified loopback HTTPS port 27124 by default) | Lets Hermes profiles read and write vault files through the plugin's native MCP rather than direct filesystem calls. Required for the Librarian and other write-active profiles. |
| **Agent Client pane (ACP)** | Interactive Obsidian sidebar pane for synchronous human-driven sessions (the Co-PI, ad-hoc queries). Separate from queue-dispatched card work. |
| **qmd** | Hybrid BM25 + vector search over the vault. Used by the Co-PI, Librarian map lane, Writer, Peer-reviewer, and QuickAdd pre-file similarity shadow reports. It is read-only; no standalone duplicate-sweep command ships today. |
| **MarkDB-Connect** (Zotero add-on) | Recommended, optional. Tags Zotero items that have a vault note and adds a right-click jump-to-note. Convenience layer over the Librarian's BBT-citekey linking, not a dependency. Setup: [Set up Zotero](../how-to-guides/zotero/set-up-zotero.md). |
| **Telegram Bot API** | Optional urgent push channel for `loudness: alert` / `block` Inbox cards. Configure `MEMORIA_TELEGRAM_BOT_TOKEN` and `MEMORIA_TELEGRAM_CHAT_ID` during [Set up Hermes](../how-to-guides/setup/set-up-hermes.md). |

---

## Search and retrieval (used at ingest)

These are called during `find` to surface candidate sources.

| API | Coverage |
|---|---|
| **OpenAlex** | General academic literature, all fields |
| **Semantic Scholar** | General academic, strong on CS / ML |
| **PubMed** | Biomedical and life sciences |

---

## Execution layer

| Integration | Role |
|---|---|
| **Kilo Code gateway** | Production model provider for the five shipped Hermes profiles. Profile defaults route Co-PI and Peer-reviewer to Opus, Writer to Sonnet, and Librarian/Engineer to Haiku. |
| **Kilocode / Aider / Claude Code** | External coding agent the Engineer hands substantive code work off to. The Engineer is MCP-only — it has no terminal or file toolset ([ADR-21](../adr/21-l3-autonomy-ceiling.md)); it writes scaffolds through the gated obsidian MCP into `projects/*/code/`, and the third-party agent runs under execution isolation. Not invoked by other profiles. |

---

## Not adopted

Tools evaluated and not in the current design:

| Tool | Why not |
|---|---|
| **ZotLit** | Obsidian-native Zotero integration — not the shipped connector. Its evaluation, status, and how it compares to the bundled `obsidian-citation-plugin` are in [Zotero plugins](zotero-plugins.md). |

---

## Related

- Ingest workflow (what runs when a source is ingested): [Ingest routing](ingest.md)
- Profile permissions (which profiles can call which integrations): [Profile capabilities](profiles.md)
- Where the API keys are configured: [Set up Hermes](../how-to-guides/setup/set-up-hermes.md)
- Librarian design (the profile that calls most of these): [The Librarian](../explanation/profiles/librarian.md)


---

<!-- source: reference/kanban-board.md -->

# Kanban board reference

Lookup tables for the Hermes Kanban board — the control plane for every unit of **agent** work. A human action (usually a `Memoria:` palette command, sometimes a Co-PI-shaped delegation) or a cron creates a card; the dispatcher assigns it to a lane; the worker runs it; the result resurfaces as an Inbox signal. Engines run _off_ the board (cron/CI), and the Co-PI has no lane — it converses in the pane.

---

## Lanes = the four background agents

A lane _is_ an `assignee` value. Four lanes only ([ADR-48](../adr/48-copi-and-agent-consolidation.md)): `memoria-librarian`, `memoria-writer`, `memoria-peer-reviewer`, and `memoria-engineer`. The lane → profile map (which task lanes each assignee serves) is owned by [Profile capabilities](profiles.md).

---

## Delegation: the tasks MCP

Co-PI-shaped task handoffs use `delegate_route_task` on the tasks MCP (`src/.memoria/mcp/tasks_mcp.py`):

1. The task lane resolves to its owning profile (table above; an unknown lane is refused).
2. **Ceiling validation:** every `allowed_paths` prefix must sit inside the lane-override's `routing.write_scope`. Paths may _narrow_ but never _widen_ the lane (lane = ceiling, payload = floor); a violation returns `ceiling-violation` and no card is created. An empty write scope (the Co-PI's own) can never receive a delegation.
3. The card body is assembled from the handoff payload and created via `hermes kanban create --assignee <profile> --created-by memoria-copi` (optionally with `--idempotency-key`), so board semantics — WIP, dedup, dispatch — stay Hermes-native.

### Handoff payload

Forward-looking and self-contained — the receiver needs nothing beyond it:

| Field | Notes |
| --- | --- |
| `goal` | One sentence: what the receiving worker must achieve. |
| `context` | The working set of notes, prior decisions. |
| `allowed_paths` | The write-scope **floor** for this card; ceiling-validated as above and re-checked per write by the [Policy MCP](policy-mcp.md). |
| `expected_outputs` | What the receiver should produce, and where. |
| `review_checks` | What the PI (or the verify lane) should check before accepting. |

---

## Execution lifecycle — the hidden mechanic

Cards carry the Hermes-native `status` enum. This chain is the **hidden execution mechanic**: the PI-facing state of any piece of work is the note's `lifecycle` (the universal chain, owned by [Frontmatter fields](frontmatter.md)), surfaced through the Inbox — not the board column. Never use one in place of the other.

```text
triage ──► todo ──► ready ──► running ──► done ──► archived
                      ▲          │
          (retry) ────┘          └──► blocked ──(unblock)──► ready
```

| `status` | Meaning | Who moves the card |
| --- | --- | --- |
| `triage` | Created; spec incomplete. Dispatcher ignores it. | Human (`hermes kanban specify` / `decompose`) |
| `todo` | Specified; on backlog. | Human |
| `ready` | Dispatchable. | Human (`hermes kanban release`) — delegation-created cards arrive ready to specify |
| `running` | A lane owns the card and is executing. | Dispatcher (atomic claim + spawn); workers do not self-claim |
| `blocked` | Worker cannot proceed; carries a `reason`. | Worker blocks; human clears (`hermes kanban unblock`) |
| `done` | Worker finished; the result surfaces as an Inbox card or a proposed note. The board export raises **one `work-prompt` review card** in `inbox/` on this transition (see below). | Worker |
| `archived` | Terminal. | `hermes kanban archive` |

Three orthogonal dimensions keep an agent verdict from rubber-stamping a human decision: `status` (execution, hidden) · the note's lifecycle (the PI's state) · `agent_recommendation` (the soft verdict on verification cards — its values are in the [Glossary](glossary.md) Verdicts table, [ADR-51](../adr/51-inbox-category-and-honesty-card.md)).

**Rejection spawns a new card** (`supersedes: <original-id>`; the original archives as `superseded`), mirroring claim supersession — each card is one attempt, so the audit trail can't lie. Abandoned work archives as `discarded`.

### Done → review prompt

The Inbox is the PI's single slice of the board ([ADR-51](../adr/51-inbox-category-and-honesty-card.md)) — a finished card must surface there, not wait silently in a board column. When the board-export cron (`src/.memoria/mcp/board_export.py`) observes a card transition into `done`, it writes **one `work-prompt` card** to `inbox/` through the shared card writer: which lane finished, the card's goal, the `expected_outputs` path(s) as the card's `target`, and the action — review the work product, then accept it or archive the board card. Honesty rules apply: action + what happened + where to look, never a verdict.

The emit is idempotent: transitions are diffed against the export's state cache (`system/logs/.board-state-cache.json`), and the prompt's filename derives from the card id (`inbox/work-prompt-review-<task_id>.md`), so the same done card never produces two prompts across cron runs. On a fresh cache (first run), only cards done within the last 24 hours raise a prompt — the board's history never floods the Inbox.

---

## WIP limits

Back-pressure protects the human bottleneck:

| Lane | WIP cap | Notes |
| --- | --- | --- |
| Review queue | 5 cards in `done` awaiting the PI | Dispatcher delays new done cards once the queue is full. |
| Per worker lane | 1 `running` card | A lane holds one card at a time — the invariant that makes idempotent re-ingest safe. |
| Writer lane (drafts in flight) | Bounded (no fixed number) | Protects synthesis quality, not throughput. |

---

## Dispatch settings

| Setting | Value |
| --- | --- |
| `dispatch_in_gateway` | `true` — the dispatcher runs in the Hermes gateway process. |
| `dispatch_interval_seconds` | `60` |
| Retry threshold | `max_retries: 3` (default; per-lane configurable) — then auto-`blocked`. |

---

## Related

- The lane ceilings the delegation is validated against: [Profile capabilities](profiles.md)
- The per-write enforcement of `allowed_paths`: [Policy MCP](policy-mcp.md)
- The board CLI: [Hermes CLI](hermes-cli.md)
- The Inbox the results surface in: [Dashboards](dashboards.md)


---

<!-- source: reference/linking.md -->

# Wikilink and link conventions

Wikilink conventions, typed-relation vocabulary, cross-link topology, and hub creation thresholds — the *how*. The *why* linking is load-bearing isn't a single page; it's explained across the knowledge model: why connections are a required section ([Note body structure](../explanation/knowledge/note-body-structure.md)), why topics live in links rather than folders ([Lifecycle, not topic — and state, not folders](../explanation/knowledge/lifecycle-over-topic.md)), and why a densely linked vault compounds ([The knowledge cycle](../explanation/knowledge/knowledge-cycle.md)). For the overall conceptual model see [explanation/vault](../explanation/architecture/vault.md).

---

## Link types

| Type | Syntax | Direction | Use |
| --- | --- | --- | --- |
| `citekey-link` | `[[mamykina2010sense]]` | `claim` → `paper` | Link a claim to its supporting paper. |
| `concept-link` | `[[receptivity-decreases-under-high-cognitive-load]]` | `claim` ↔ `claim` | Connect related claims; builds the knowledge graph. |
| `hub-link` | `[[jitai-design-hub]]` | Note → `hub` | Place a note within a navigational hub. |
| `entity-link` | `[[mamykina-lena]]` | Any → catalog entity | Connect people, organizations, venues, datasets, repositories. |
| `agent-cross-link` | Inline in note body | Proposed | Agent-generated candidates; human confirms before treating as canonical. |

---

## Linking conventions

- A link records a useful relationship, not exhaustive coverage.
- A `claim` traces to at least one `paper` citekey.
- A `paper` eventually connects to at least one relevant `hub`.
- A concept link carries a relationship that would matter in a later reading or writing session.
- A note's hub placement is a single strong link, not many weak generic ones.
- Provenance runs one way: claims point to evidence, not the reverse.
- An agent-proposed cross-link is not canonical until reviewed.
- A complete note is one that has received a hub link or relevant concept links — an orphan is incomplete.
- A `paper` and a `claim` are not peers: the claim stands on its own and the paper is its support.

---

## Required patterns by type

| Note type | Required link structure |
| --- | --- |
| `paper` | `relationships:` frontmatter on the Catalog entity (`cited_by`, `authored_by`, `published_in`) — given facts from the bibliographic record. |
| `claim` | `sources:` frontmatter listing the citekey(s) the claim draws on. `Connections` section for conceptual neighbors via authored `links:`. |
| `hub` | `links:` frontmatter. Body: overview, curated entries, gaps. |

---

## Authored links (`links:` map)

Notes carry **authored** `links:` — the PI's thinking ([ADR-52](../adr/52-links-vs-relationships.md)). The `links:` vs `relationships` field contract (which document types carry each, and the authored-vs-given split) is specified in [Frontmatter fields](frontmatter.md). Available on `source`, `claim`, and `hub` notes; agent-proposed candidates are reviewed before they become canonical.

```yaml
links:
  supports:
    - "[[another-claim]]"
  contradicts:
    - "[[a-conflicting-claim]]"
  extends:
    - "[[a-foundational-claim]]"
```

Allowed link types:

| Link | Direction |
| --- | --- |
| `supports` | This note supports the linked note. |
| `contradicts` | This note contradicts the linked note. |
| `extends` | This note builds on the linked note. |

Catalog entities carry **given** `relationships:` instead, written by the ingest operation (see [Frontmatter fields](frontmatter.md)). Adding a new authored link type requires updating this reference and the Linter's `frontmatter-link` detector.

---

## Cross-link topology

Expected link graph by document type:

```text
paper ({citekey})
  ↔ person               (authored_by)
  ↔ venue                (published_in)
  ↔ organization         (author affiliation)
  ↔ paper (other)        (cited_by)

claim
  → paper                (citekey in sources:)
  ↔ claim (other)        (authored links — supports / contradicts / extends)
  → hub                  (links: frontmatter)

person
  ↔ paper                (authored)
  ↔ organization         (affiliated with)

organization
  ↔ person               (members, affiliates)
  ↔ venue                (hosts or sponsors)

venue
  ↔ paper                (published)

hub
  ← claim                (links: frontmatter on claims)
  ← paper                (links: frontmatter on sources)
  ↔ hub (other)          (parent/child hub hierarchy)

project
  ← project artifacts    (projects/<project>/* all reference the project note)
```

---

## Hub thresholds

| Threshold | Action |
| --- | --- |
| ≥ 15–20 notes (papers + claims combined) on a topic | Create a top-level hub for the topic. |
| > 20 claims + > 10 papers on a branch | Build a child hub for that branch. |

Below these thresholds a topic carries no hub — the friction of the missing hub is lower than the cost of maintaining a premature one.

---

## Vocabulary discipline

The `research_area`, `methodology`, and `topics` fields use the controlled lists in [Vocabulary](vocabulary.md), whose runtime home is `system/vocabulary.md`.

- The active `research_area` list stays near **~30 terms** per corpus; a smaller vocabulary produces more consistent classification.
- Claim `topics` draw from the same `research_area` list so claims and sources stay queryable together.
- Richer taxonomy (MeSH, ACM CCS, OpenAlex concepts) lives in `_enrichment` (auto-populated from APIs), not in the hand-curated classification fields.
- A topic-term rename goes through [Manage your topic vocabulary](../how-to-guides/knowledge/manage-vocabulary.md), not a manual search-replace across notes.

---

## Slug conventions for wikilinks

| Note type | Slug format | Example |
| --- | --- | --- |
| `paper` | Citekey (Better BibTeX format) | `mamykina2010sense` |
| `claim` | Lowercase kebab-case, subject-verb-object | `receptivity-decreases-under-high-cognitive-load` |
| `hub` | `<topic>-hub` | `jitai-design-hub` |
| `person` | `<lastname>-<firstname>` | `mamykina-lena` |
| `organization` | Slug of the official name | `columbia-dbmi` |
| `venue` | Slug of the venue name | `chi-conference` |
| All others | Descriptive kebab-case | `ema-best-practices` |

Slugs are permanent — renaming a note breaks all wikilinks pointing to the old slug, so renames are rare and the Linter's `graph-analyze` check catches the breakage afterward.

---

## Related

- How-to for setting authored links: [Link related claims](../how-to-guides/knowledge/link-related-claims.md)
- Why the Connections section is load-bearing: [Note body structure](../explanation/knowledge/note-body-structure.md)
- Why notes are filed by lifecycle, not topic: [Lifecycle, not topic — and state, not folders](../explanation/knowledge/lifecycle-over-topic.md)
- How links keep the vault compounding: [The knowledge cycle](../explanation/knowledge/knowledge-cycle.md)


---

<!-- source: reference/linter.md -->

# Linter: detectors and auto-fix

The Linter is an **operation, not an agent** ([ADR-49](../adr/49-catalog-in-bases-linter-monitor.md)): deterministic, zero-LLM Python under `src/.memoria/operations/integrity/linter`. Its contract is **gates at commit, monitors between** — the pre-commit hook blocks schema-invalid notes from being committed, and the daily cron reports everything else. Scope: detection only. Live in-app edits are caught by the next sweep, and every detector is report-only — findings surface for the PI to act on; nothing is auto-moved or auto-archived.

---

## The detectors

`src/.memoria/operations/integrity/linter/detectors.py` — self-contained (vault tree only), report-only. Constants are **schema-driven**: when `.memoria/schemas/` + PyYAML are available, the type → home map and the legal root folders are derived from `folders.yaml`/`types/*.yaml`; the hardcoded fallbacks keep the operation running without dependencies.

| Detector | Severity | Catches |
| --- | --- | --- |
| `schema-check` | MEDIUM | A typed document failing its schema in `.memoria/schemas/types/` (missing `type`, unknown type, bad field kind/enum). |
| `frontmatter-link` | MEDIUM | A frontmatter wikilink that resolves to no note — every link in the `links:` map and the `entity` field must resolve ([ADR-52](../adr/52-links-vs-relationships.md)). Citekeys in `sources` are bibliographic, checked by the sweeps instead. |
| `broken-wikilink` | MEDIUM | A body wikilink resolving to no note (scaffolding under `system/templates/`, `system/dashboards/`, and `system/patterns/` is skipped). |
| `misplaced-note` | MEDIUM / LOW | A typed document outside its `folders.yaml` home, or a stray vault-root folder outside `catalog · notes · projects · inbox · spaces · system`. Skips work-in-flight zones (`inbox/`, `system/logs/`, `system/board/`). |
| `audit-unpaired-writes` | MEDIUM | A mutating allow in `system/logs/audit.jsonl` with no paired `write_complete` record after an hour — the per-write hash pair is incomplete and the write's after-state can no longer be pinned. |
| `vault-hash-drift` | CRITICAL | A path whose latest `write_complete` `after_hash` in `system/logs/audit.jsonl` no longer matches the on-disk SHA-256 — an out-of-band change ([ADR-25](../adr/25-session-logging-two-logs.md)). A legitimate human edit in Obsidian surfaces here too, by design: the finding means the audit trail no longer pins that file's state. A completed delete records the empty-bytes hash, so a deleted-and-still-absent file matches and stays silent. |
| `skeleton-drift` | MEDIUM | A directory from the installer skeleton (the `skeleton` list in `.memoria/schemas/folders.yaml`) missing from the vault — re-run the idempotent installer or create it ([ADR-67](../adr/67-drift-procedures-keep-or-retire.md)). Checked only in installed vaults (golden manifest present); the repo's `src/` ships no empty dirs. |
| `hub-threshold` | LOW | A topic with ≥ 15 notes (papers' `research_area` + claims' `topics`, case-insensitive) and no covering `hub` note — consider creating one ([ADR-19](../adr/19-moc-threshold-alert.md) Tier 1; report-only, never auto-created). Tier 2 is the separate `hub_handoff.py` operation, which delegates a staged proposal to the `map` lane without widening into `notes/hubs/`. |
| `audit-log-size` | LOW | `system/logs/audit.jsonl` over the 50 MB advisory threshold. The log is append-only forever — never rotated ([ADR-25](../adr/25-session-logging-two-logs.md)) — so growth is surfaced here instead of staying silent. |
| `dashboard-field-drift` | HIGH | A dashboard Dataview query referencing a frontmatter field no template declares. |
| `design-system-drift` | MEDIUM / LOW | Visual-discipline drift from `.memoria/design-system.md`: off-palette colors, font sizes outside the scale, emoji in note titles, ad-hoc/rainbow callout variants, and terminology/capitalization drift. |
| `fama-exposure` | HIGH | A downstream note wikilinking a **superseded** claim (`lifecycle: archived` or `superseded_by` set) — reuse of obsolete memory. |
| `extract-path-broken` | HIGH | A paper note whose `extract_path` does not resolve. |
| `graph-analyze` | LOW | Orphan synthesis notes (claims/hubs with zero inlinks). |
| `orphan-working-files` | LOW | Leftover working files (`*.tmp.*`, `*.bak`, `*.orig`, …) outside transient zones. |
| `stale-fleeting` | LOW | Fleeting notes older than 7 days — promote or discard. |

CLI entry point:

```bash
python3 .memoria/operations/integrity/linter/detectors.py --vault <vault> [--json] [--space dashboard-field-drift,design-system-drift]
python3 .memoria/operations/integrity/linter/hub_handoff.py --vault <vault> [--threshold 15] [--json]
```

`--gate DETECTORS` makes only the named detectors blocking (exit 1); everything else stays advisory. `hub_handoff.py` is opt-in: it reads current `hub-threshold` findings and creates idempotent Librarian `map` cards whose allowed paths are only `notes/fleeting/maps/` and `inbox/`. The verdict rolls up as **PASS** (LOW only or clean) / **REVIEW** (any MEDIUM/HIGH) / **FAIL** (any CRITICAL).

---

## The pre-commit hook

The commit gate ([ADR-50](../adr/50-universal-lifecycle-and-maturity.md)): the installer wires `src/.memoria/operations/integrity/linter/pre-commit` into the deployed vault's `.git/hooks/pre-commit`. On every commit it passes the staged `.md` paths to `src/.memoria/operations/integrity/linter/precommit_check.py`, which validates each typed document against its schema via the shared loader (`src/.memoria/operations/lib/schema.py`). Any error blocks the commit (exit 1). Exempt: untyped `system/` infrastructure, vault-root nav pages, and paths outside the vault.

---

## The golden copy

`src/.memoria/operations/integrity/linter/golden_restore.py` turns the Linter into a _repairer_ ([ADR-55](../adr/55-src-scaffold-populate-golden-copy.md)). The installer stages a canonical copy of every system file — `system/templates|dashboards|patterns|eval|scripts/` plus `home.md`, `system/vocabulary.md`, `AGENTS.md` — at `.memoria/golden/` with a SHA-256 `manifest.json`.

This is the human-facing half of template protection (#179): agents are already blocked by the lane ceilings — every shipped lane-override denies writes under `system/**` (see [Policy MCP](policy-mcp.md)) — so the golden copy exists to catch and repair an *accidental human* edit or deletion of a system file.

| Command | Effect |
| --- | --- |
| `golden_restore.py --vault V stage` | Stage or refresh the golden copy from the live system files. |
| `golden_restore.py --vault V check` | Report drifted/missing system files vs the manifest (exit 1 if any). |
| `golden_restore.py --vault V restore [PATH …]` | **Propose-only by default** — lists what it would restore. |
| `golden_restore.py --vault V restore --apply` | Write the golden bytes back (the PI or cron runs it deliberately). |

The manifest also covers the **Memoria-shipped Obsidian config** ([ADR-67](../adr/67-drift-procedures-keep-or-retire.md)): each shipped plugin's `data.json` plus `.obsidian/community-plugins.json`, `core-plugins.json`, and the `memoria-link-colors.css` and `memoria-property-badges.css` snippets. Per-machine and runtime-generated state never enters the manifest — `agent-client/data.json` (seeded per machine), `obsidian-local-rest-api/data.json` (regenerated on first launch), and workspace/appearance state stay the user's.

---

## Per-session digests

`src/.memoria/operations/integrity/linter/session_summary.py` writes the second of [ADR-25](../adr/25-session-logging-two-logs.md)'s two logs: a **deterministic digest** of each session's audit activity (the Linter is zero-LLM — no narrative). It groups `audit.jsonl` entries by `task_id` and writes one `system/logs/sessions/YYYY-MM-DD-HHMM.jsonl` per finished session (named from the session's first timestamp; a deterministic `-2` suffix disambiguates a shared start minute): a header record (task, profiles, start/end, counts by action and decision) plus one record per touched path (actions, final decision, final `after_hash`). Idempotent — an already-digested `task_id` is never rewritten — and sessions active within the last **24 h** (`--quiet-hours`) are left for a later run so in-flight work isn't summarized early.

```bash
python3 .memoria/operations/integrity/linter/session_summary.py --vault <vault> [--quiet-hours H]
```

---

## The daily cron

The installer wires `memoria-lint` (`hermes cron create '0 6 * * *' --script memoria-lint.sh --no-agent`), whose wrapper runs the detectors, `golden_restore.py check`, and the per-session digests over the vault. Findings surface in Maintenance's Drift watch and Loose ends views — see [Dashboards](dashboards.md).

---

## Auto-fix classes

Auto-fix is class-gated at the policy layer — the four classes and their dispositions are owned by [Policy auto-fix](policy-auto-fix.md). The Linter operation is report-only; the gate exists for any future fixer, including `golden_restore.py restore --apply`, which is the shipped repair path.

---

## Related

- The schemas the detectors validate against: [Frontmatter fields](frontmatter.md)
- The class gate enforcing auto-fix policy: [Policy auto-fix](policy-auto-fix.md)
- Where the findings surface: [Dashboards](dashboards.md)
- The crons the installer wires: [Installer (bootstrap)](installer.md)


---

<!-- source: reference/memory.md -->

# Memory substrates

Where each type of state lives across the Memoria + Hermes stack: substrate, provider, scope, lifespan, backing store, and what it holds. Listed by how much the PI touches them.

**The Co-PI is the sole carrier of the Hermes memory loop**: only `memoria-copi` keeps the `memory` toolset (plus `/goals`, skills, `/personality`) — it alone accumulates working preferences and environment facts across sessions. The four specialist lanes omit `memory` from their positive `platform_toolsets` and keep it in the disabled-toolset backstop: a dispatched worker gets everything it needs from the handoff payload and the vault, so per-lane memory would only drift. See the per-profile allowlists in `src/.memoria/tool-registry.yaml`.

---

## Substrate table

| Substrate | Provider | Scope | Lifespan | Backing store | What it holds |
| --- | --- | --- | --- | --- | --- |
| **Program memory** | Memoria — vault files | Whole research program | Persistent | Vault root (`research-focus.md`) | Standing steering: discovery priorities, review mode. The PI's main lever over what the system pursues. |
| **Project memory** | Memoria — vault files | One project, across lanes | Project-bound; archives with the project | `projects/<project>/` | Open questions, decisions, framing for one project. |
| **Audit memory** | Memoria — vault files | Whole vault | Indefinite; append-only | `system/logs/` + `system/metrics/` | Audit trail, capture-intake anchors, pattern provenance, board projections, fleet metrics. |
| **Handoff memory** (payload) | Memoria — Kanban | One card; travels across lanes | Card-bound | Card `metadata` | The handoff payload — schema owned by the [Kanban board reference](kanban-board.md). |
| **Agent memory** (`MEMORY.md` + `USER.md`) | Hermes native | **The Co-PI only** | Durable; frozen snapshot at session start | `~/.hermes/profiles/memoria-copi/memories/` | `MEMORY.md` (~800 tokens): environment facts, conventions, learned preferences. `USER.md` (~500 tokens): the PI's working style. Disabled on the four specialist lanes. |
| **Session history** | Hermes native | One profile, all past sessions | Indefinite | SQLite at `~/.hermes/state.db` (full-text) | Searchable history of prior conversations; costs no tokens until queried. |
| **Working memory** | Hermes native | One session | Session-bound; cleared on `/clear` | In-context | Current goal, recent tool results, in-flight reasoning. |

Token caps on `MEMORY.md` / `USER.md` are approximate — verify in the upstream [Hermes docs](https://hermes-agent.nousresearch.com/docs/user-guide/features/memory).

---

## Ownership rules

| Rule | Details |
| --- | --- |
| Program memory is the PI's steering | The PI authors `research-focus.md`; every profile reads it; it never archives. |
| Project memory is the per-project cross-lane channel | Anything that must survive across lanes within one project. Archives with the project. |
| Audit memory is append-only | The policy gate writes an entry at every decision; operations append their own logs (`capture-intake.jsonl`, `patterns.jsonl`). |
| Handoff memory is per-card, not per-profile | When work moves Librarian → Writer, the payload travels with the card; the Writer does not inherit the Librarian's working memory. |
| Agent memory is the Co-PI's alone | Frozen at session start; mid-session writes show up next session. Keep it small and stable — not in-flight task state. Specialists have it disabled. |
| Session history is read-only history | Never gates anything; never authoritative over the vault. |
| Working memory is not shared | One lane's in-session reasoning never bleeds into another's. |

---

## What lives where — decision table

| State type | Correct substrate | Wrong substrate (common mistake) |
| --- | --- | --- |
| What you want the system to pursue | Program memory (`research-focus.md`) | `project-hints.yaml` (that's config, not recall) |
| One project's open questions / decisions | Project memory (`projects/<project>/`) | Handoff memory (card-scoped, dies with the card) |
| Current task goal and context | Handoff memory (payload) | Agent memory (capped, frozen at start — and disabled on lanes) |
| Stable facts about the environment | Co-PI `MEMORY.md` | Working memory (not persistent) |
| The PI's preferences and style | Co-PI `USER.md` | `MEMORY.md` (keep identity vs preference separate) |
| Cross-session retrieval | Session history | Agent memory (too small for bulk recall) |
| Audit trail of all decisions | Audit memory (`system/logs/audit.jsonl`) | Agent memory (wrong granularity) |
| Durable synthesized knowledge | Vault notes (`notes/claims/`, `notes/hubs/`) | Any of the above |

`SOUL.md` is **not** memory — it is the profile's identity prompt, stable across sessions by design.

---

## Audit memory

The audit trail (`system/logs/audit.jsonl`) records every policy decision with its before/after hash pair. Its field schema, the eight guarded actions, the `decision` enum, and the per-write hash-pairing mechanism are owned by [Policy audit log](policy-audit-log.md).

---

## Related

- The writer of the audit log: [Policy MCP](policy-mcp.md)
- The capability allowlist that disables specialist memory: [Profile capabilities](profiles.md)
- The handoff payload schema: [Kanban board reference](kanban-board.md)


---

<!-- source: reference/obsidian-callouts.md -->

# Obsidian callouts

Three inline callout types defined via the [Callout Manager](obsidian-plugins.md) plugin. All three now have shipped producers: `[!brief]` during ingest, `[!suggestions]` from the link-claim palette action, and `[!verification]` from the verify-draft palette action.

The fixed palette also applies to shipped navigation surfaces: the space dashboards use
`[!brief]` for their empty-state and orientation copy instead of generic Obsidian
callout types. The `design-system-drift` Linter detector reports any ad-hoc/rainbow
callout variants in shipped vault notes.

---

## The three callout types

| Callout | Location | Producer | Purpose |
| --- | --- | --- | --- |
| `[!brief]` | Top of every source note in `notes/sources/` | Librarian (composed during ingest by `catalog-enrich-record`) | Comparative read — what this source overlaps with, what it may contradict, what new constructs it introduces |
| `[!suggestions]` | Claim notes in `notes/claims/` | QuickAdd `Memoria: link claim` preflight, followed by Librarian `link-suggest-claim` | Bounded deterministic candidate links (5 forward + 5 backward, hard cap) |
| `[!verification]` | Drafts in `projects/` | QuickAdd `Memoria: verify draft` preflight, followed by Peer-reviewer `verify-check-citation` | Deterministic claim-link/citekey trace scaffold plus visible `gap` cards for ungrounded assertions; the lane performs support judgment |

---

## Example shape

```markdown
> [!brief] Comparative read
> Overlaps with: [[mamykina2010sense]], [[veinot2018good]]
> May contradict: [[chen2021pipeline]]
> New construct: "prosodic mimicry safety"
> 5 candidate links queued for review.
```

---

## Behavior

| Property | Value |
| --- | --- |
| Default collapse state | `[!brief]` expanded; `[!suggestions]` collapsed; `[!verification]` expanded |
| Re-run on edited callout | Producers append a dated callout instead of overwriting existing human-edited callouts |
| Write path | Policy-MCP gated — logged with SHA-256 hashes, reversible from the audit log |

For why each behaves this way, see [Callouts](../explanation/obsidian/callouts.md).

---

## How content is produced (hybrid pattern)

The shipped `[!brief]` producer uses a deterministic candidate-selection step followed by an LLM composition step. The `[!suggestions]` and `[!verification]` producers ship the deterministic preflight now; their delegated lane cards are where optional one-line explanations and support judgments happen.

| Callout | Deterministic step | LLM step |
| --- | --- | --- |
| `[!brief]` | Top-5 candidates ranked by: shared-citation overlap + embedding similarity + topic-tag intersection | Composes the "overlaps with / may contradict / new construct" narrative over the 5 candidates |
| `[!suggestions]` | Top-10 local candidates ranked deterministically by claim/source token overlap, truncated to 5 forward + 5 backward | Optional Librarian one-line explanation per candidate on the delegated card |
| `[!verification]` | Regex extraction of claim links and citekeys from the draft; writes the trace scaffold inline | Peer-reviewer judges whether the cited material supports the draft claims |

For `[!brief]`, the audit-relevant part is the deterministic candidate set that the Librarian composes over. For the link and verify callouts, the deterministic preflight is visible immediately and the delegated lane card carries any judgment/prose that should not be done by the UI script.

---

## Drift signals

No shipped dashboard tracks `[!suggestions]` accept/reject ratios yet. The producer now exists, and the intended drift signal remains: ratio extremes should flag rubber-stamping versus over-strict scoring in fleet health. How to read and respond to these signals is covered in [Callouts](../explanation/obsidian/callouts.md).

---

## Related

- Callout Manager plugin: [Obsidian plugins](obsidian-plugins.md)
- Computational toolbox (scoring functions): [Retrieval and analysis methods](computational-toolbox.md)
- Fleet-health dashboard: [explanation/dashboards/](../explanation/dashboards)
- The callout explanation page: [Callouts](../explanation/obsidian/callouts.md)


---

<!-- source: reference/obsidian-command-palette.md -->

# Obsidian command palette

The `Memoria:` command-palette surface — the in-Obsidian commands, registered by QuickAdd (`Cmd-P → Memoria: …`). Commander mirrors the highest-frequency entries into the ribbon and page header: capture, delegate, resolve, and note-local claim/source actions. Space switching is handled by the left-pane navigator rail (**Now** / **Places**); the command palette is for actions, not navigation.

**Action parity rule:** if an action creates a card, note, draft, report, capture, resolved Inbox item, or any other durable artifact, it must be reachable without asking the Co-PI ([ADR-72](../adr/72-command-surfacing.md)). The Co-PI conversation is a convenient route for agent tasks — you tell the Co-PI what you want and it delegates a ceiling-validated card to the right lane via the tasks MCP (see [Kanban board reference](kanban-board.md)) — but durable actions are also reachable from the palette ([#203](https://github.com/eranroseman/memoria-vault/issues/203)): direct commands for the six non-code lane tasks, the generic delegate fallback for code or unusual work, a pattern runner, the capture entry points that must fire from inside the editor, the inbox resolve action, and verb-shaped assist commands for Find/Search/Patterns/Ask/Draft/Explore.

The allowed Co-PI-only surface is conversation-bound, not action-bound: synchronous read-only sparring, source questioning, lens reading, memory-backed coaching, and `/personality` tuning. When that conversation should produce something durable, leave the pane and use the matching command or delegated card path.

---

## Capture and note-creation commands

| Command | Output | Implementation |
| --- | --- | --- |
| `Memoria: capture fleeting` | Opens the `memoria-fleeting-capture` Modal Forms form, writes one raw item to `notes/fleeting/` (`lifecycle: proposed`, `origin: human`), and leaves processing to the Inbox queue. | QuickAdd Macro → `system/scripts/capture-fleeting.js` |
| `Memoria: archive fleeting note` | The **active** fleeting note (must be under `notes/fleeting/`) flipped in place to `lifecycle: archived` and stamped with `archived:`. | QuickAdd Macro → `system/scripts/archive-active-note.js` (`Type: fleeting`) |
| `Memoria: write claim note` | Opens the `memoria-claim-capture` Modal Forms form, writes a standalone claim in the **review-gated home** (`notes/claims/`), runs the pre-file similarity shadow check, and opens the note. | QuickAdd Macro → `system/scripts/write-claim.js` |
| `Memoria: archive claim note` | The **active** claim note (must be under `notes/claims/`) flipped in place to `lifecycle: archived` and stamped with `archived:`. | QuickAdd Macro → `system/scripts/archive-active-note.js` (`Type: claim`) |
| `Memoria: load sample vault` | Copies the bundled `.memoria/samples/mediterranean-diet/` `catalog/` and `notes/` files into the live vault, skipping existing files so user work is not overwritten. | QuickAdd Macro → `src/system/scripts/load-sample-vault.js` |
| `Memoria: remove sample vault` | Archives live `catalog/` and `notes/` files labeled `sample: true`, leaving the hidden bundle in place. | QuickAdd Macro → `src/system/scripts/remove-sample-vault.js` |
| `Memoria: capture source from URL` | A capture card on the Librarian lane with the pasted URL. A URL with a resolvable DOI ingests; a bare/proxied URL blocks asking for the DOI or citekey. | QuickAdd Macro → `src/system/scripts/capture-from-url.js` → `hermes kanban create` |
| `Memoria: structured source capture` | Opens the `memoria-source-capture` Modal Forms form, writes a schema-valid `source` note at `lifecycle: proposed` under `notes/sources/`, and raises an Inbox `candidate` pointing at it. | QuickAdd Macro → `src/system/scripts/structured-source-capture.js` (Modal Forms API + Obsidian adapter) |
| `Memoria: start project` | Opens the Project start form, scaffolds `projects/<slug>/` with `project.md`, `thesis.md`, and empty `code/`, `drafts/`, and `exports/` folders. | QuickAdd Macro → `src/system/scripts/start-project.js` (Modal Forms API + Obsidian adapter) |
| `Memoria: capture from Zotero selection` | A Tier-0 Catalog stub plus a capture card on the Librarian lane, citekey pre-populated from the current Zotero selection. | QuickAdd Macro → `src/system/scripts/capture-from-zotero.js` (Better BibTeX JSON-RPC) → `hermes kanban create` |
| `Memoria: resolve inbox card` | The **active** note (must be under `inbox/`) flipped in place: `lifecycle:` set to your outcome (`current` = accept, `archived` = reject / done) and `resolved:` stamped with today's date. | QuickAdd Macro → `src/system/scripts/resolve-inbox-card.js` (pure Obsidian API — no shelling) |

Template-based document creation starts from the templates in `system/templates/` — see [Document types](document-types.md). Claim and fleeting capture use Modal Forms wrappers that render their templates, so the form prompts, note body, and note-local command buttons stay aligned.

---

## Per-task lane commands

One command per non-code lane task, each prompting only for what that task needs and creating a card addressed to the lane's agent and skill (`hermes kanban create --assignee … --skill …`). Code and unusual work use the generic delegate command.

| Command | Lane → agent (skill) | Prompts for | Implementation |
| --- | --- | --- | --- |
| `Memoria: catalog source` | catalog → Librarian (`catalog-enrich-record`) | Citekey or URL, optional goal. | QuickAdd Macro → `src/system/scripts/catalog-source.js` |
| `Memoria: extract claims` | extract → Librarian (`extract-stub-claim`) | The source note — defaults to the active note when it's under `catalog/papers/` or `notes/sources/`, otherwise prompts for a path or citekey. | QuickAdd Macro → `src/system/scripts/extract-claims.js` |
| `Memoria: link claim` | link → Librarian (`link-suggest-claim`) | The claim note — defaults to the active note when it's under `notes/claims/`. | QuickAdd Macro → `src/system/scripts/link-claim.js` |
| `Memoria: map corpus` | map → Librarian (`map-cluster-corpus`) | Scope (folder or hub note) — optional; Enter maps the whole corpus. | QuickAdd Macro → `src/system/scripts/map-corpus.js` |
| `Memoria: draft section` | draft → Writer (`draft-write-section`) | The goal or outline ref. | QuickAdd Macro → `src/system/scripts/draft-section.js` |
| `Memoria: verify draft` | verify → Peer-reviewer (`verify-check-citation`) | The draft — defaults to the active note when it's under `projects/`. | QuickAdd Macro → `src/system/scripts/verify-draft.js` |
| `Memoria: delegate task` | Any lane (you pick from a suggester; no skill pinned) | Lane + free-form goal — the generic fallback for work that doesn't fit a single-task command. | QuickAdd Macro → `src/system/scripts/delegate-task.js` |
| `Memoria: run pattern` | Librarian card invoking `patterns_run` ([ADR-53](../adr/53-pattern-library.md)) | A pattern, from a suggester over the runnable (`lifecycle: current`) patterns in `system/patterns/`; the active note rides along as `input_ref`. | QuickAdd Macro → `src/system/scripts/run-pattern.js` |

The lane → agent mapping mirrors `LANE_PROFILE` in `.memoria/mcp/tasks_mcp.py` (the `code` lane has no single-task command — use `Memoria: delegate task`).

---


## Assist commands

Assist commands are verb-shaped entry points for work that starts in the current surface. Invoke them from the palette, from a selected span in the editor, or by asking the Co-PI in the Agent Client pane. Palette/selection invocations create staged cards or proposal artifacts; pane invocations stay conversational until you ask the Co-PI to delegate. None of these commands writes directly to canonical notes.

| Command | Existing skill / operation | Palette and selection behavior | Pane behavior |
| --- | --- | --- | --- |
| `Memoria: assist find` | Librarian `catalog-find-source` | Prompts for a source, topic, DOI, URL, or clue; selected text and the active note ride on the card. | Ask the Co-PI to find a source; it delegates if the result should persist. |
| `Memoria: assist search` | Librarian `map-report-coverage` | Prompts for a search lens or coverage question and stages a coverage/gap report request. | Ask the Co-PI what the corpus already holds for the lens. |
| `Memoria: assist patterns` | Librarian card invoking `patterns_run` | Picks a runnable pattern from `system/patterns/`; selected text/active note become input context, and output goes only to the returned target. | Ask the Co-PI which pattern to run, then delegate or use this command. |
| `Memoria: assist ask` | Co-PI `ask-question-source` / `ask-read-lens` | Stages a Co-PI question card when the answer should be reviewable or persistent. | Ask directly in the Agent Client pane; the active note is passed as a readable reference. |
| `Memoria: assist draft` | Writer `draft-write-section` | Prompts for a section/outline goal and stages a draft request with selected text as source context. | Ask the Co-PI to shape the draft, then delegate the durable drafting step. |
| `Memoria: assist explore` | Co-PI `explore-framings` | Stages an exploration card with the active note/selection attached. | Explore directly in the pane while the output is still human understanding. |

## Note utility commands

These commands write notes directly from local templates or the active note; they do
not create board cards.

| Command | Use | Implementation |
| --- | --- | --- |
| `Memoria: write claim note` | Create a standalone claim note through the guided claim form. | QuickAdd Macro → `src/system/scripts/write-claim.js` |
| `Memoria: create linked claim note` | From an active source note, create a claim in `notes/claims/`, add the source citekey to `sources`, link it under **Worth distilling**, and open the claim. | QuickAdd Macro → `src/system/scripts/create-linked-claim.js` |
| `Memoria: refresh project gate` | From an active project file, runs the deterministic Project structural-impact operation and refreshes `project-gate-index.md`. | QuickAdd Macro → `src/system/scripts/refresh-project-gate.js` |
| `Memoria: supersede thesis` | From an active thesis note, creates a proposed replacement, marks `superseded_by` on the old thesis, updates the project `active_thesis`, and raises a re-confirmation alert. | QuickAdd Macro → `src/system/scripts/supersede-thesis.js` |
| `Memoria: record exploration trace` | Capture a rejected direction/dead end beside an active or selected map/gap report under `notes/fleeting/maps/`. | QuickAdd Macro → `src/system/scripts/record-exploration-trace.js` |

---
## The Co-PI delegation path

For work where the lane is unknown or spans several tasks, the conversational path runs through the Agent Client pane (the Co-PI, with the active note available as a readable reference): a free-form request triggers a `delegate_route_task` call, the handoff is validated against the lane's write-scope ceiling, the card lands on the board, and the result resurfaces in the Inbox. The mechanics are in [Kanban board reference](kanban-board.md).

---

## Related

- The delegation mechanics: [Kanban board reference](kanban-board.md)
- The terminal surface: [Hermes CLI](hermes-cli.md)
- The capture pipeline behind both macros: [Ingest routing](ingest.md)


---

<!-- source: reference/obsidian-plugin-data-files.md -->

# Obsidian plugin data files

Rules for committed, generated, example, and secret-bearing plugin `data.json` files. For plugin inventory and load-bearing settings, see [Obsidian plugins](obsidian-plugins.md) and [Obsidian plugin settings](obsidian-plugin-settings.md).

## `data.json` conventions

| Suffix | Meaning |
| --- | --- |
| `data.json` | Committed, ready to use. |
| `data.json.example` | Committed stub; rename to `data.json` and fill in per-human values (e.g., API keys). |
| `data.json.TODO` | Committed; manual configuration required before the plugin is functional. |
| (gitignored) | Contains secrets; generated on first launch with defaults. |

**Example-file casing.** Memoria-authored example files use lowercase `.example` (the industry-standard convention; `.env.example`, `.sample`, etc.). The only uppercase exception is Hermes's `.env.EXAMPLE`, which is **generated by `hermes profile install`** ([upstream schema](https://hermes-agent.nousresearch.com/docs/user-guide/profile-distributions)) and reused verbatim — its casing is not Memoria's to change. Rule of thumb: *Memoria-authored = `.example`; Hermes-generated = `.EXAMPLE`*.

| Constraint | Rule |
| --- | --- |
| `data.json` edits | Only edit while Obsidian is not running; Obsidian overwrites it on every settings change. |
| `main.js` / `styles.css` / `manifest.json` | **Committed.** The starter vault ships every required plugin pre-installed, so the plugin build files are part of the distribution and are tracked in git. Do not add them to `.gitignore`. |
| Private `data.json` | Any plugin `data.json` that holds secrets or per-machine data is **gitignored and ships as `data.json.example`**. Two qualify: `obsidian-local-rest-api/data.json` (apiKey + TLS cert + RSA private key, regenerated on first launch) and `agent-client/data.json` (per-machine agent command paths + any provider apiKeys). Every other plugin's `data.json` carries no private data and is committed, configured to spec. Rule: a new secret-bearing config gets **both** a `.gitignore` line and a `.example` sibling. |

---

## Related

- Plugin inventory: [Obsidian plugins](obsidian-plugins.md)
- Plugin settings: [Obsidian plugin settings](obsidian-plugin-settings.md)


---

<!-- source: reference/obsidian-plugin-settings.md -->

# Obsidian plugin settings

Load-bearing settings for the Obsidian plugins Memoria ships or relies on. For the plugin inventory and install status, see [Obsidian plugins](obsidian-plugins.md).

## Settings per plugin

Settings with a fixed required value. All others are personal preference. See [explanation/obsidian/](../explanation/obsidian) for rationale.

### obsidian-local-rest-api

| Setting | Required value | Constraint |
| --- | --- | --- |
| HTTPS server | **on**, port `27124` | Serves the plugin's native MCP at `https://127.0.0.1:27124/mcp` — Hermes's vault path ([ADR-31](../adr/31-native-obsidian-mcp.md)). Loopback-only. Each profile's `OBSIDIAN_MCP_PORT` must match; use distinct ports per vault to run a sandbox + production at once. |
| HTTPS certificate | Exported PEM path in `OBSIDIAN_MCP_SSL_VERIFY` | Hermes passes this path to `mcp_servers.obsidian.ssl_verify`, keeping certificate verification enabled for the plugin's self-signed/local cert. |
| HTTP (insecure) server | off unless debugging | Plain HTTP is no longer the shipped Hermes path. Do not use it for normal profile runs. |
| `data.json` | **gitignored** | Contains API key secrets. Ships as `.example`; never commit the real file. |

### templater-obsidian

| Setting | Required value | Constraint |
| --- | --- | --- |
| `templates_folder` | `system/templates` | Must match vault schema convention. |
| `trigger_on_file_creation` | `false` | Auto-trigger races with agent writes. |
| `enable_system_commands` | `false` | Not required by Memoria; increases attack surface. |

### obsidian-citation-plugin

| Setting | Required value | Constraint |
| --- | --- | --- |
| BibTeX file (`citationExportPath`) | `.memoria/memoria.bib` | Single source of bib data; Better BibTeX auto-exports here. |
| Export format (`citationExportFormat`) | `biblatex` | Matches the Better BibTeX export. |
| Literature note folder (`literatureNoteFolder`) | `catalog/papers` | Notes must land in the canonical papers home ([ADR-47](../adr/47-type-first-category-folders.md)). |
| Note title (`literatureNoteTitleTemplate`) | `@{{citekey}}` | Filename keys off the stable citekey. |
| Template (`literatureNoteContentTemplate`) | **Inline, in `data.json`** | This plugin has no external-template-file setting — the full paper-note body is stored inline in `literatureNoteContentTemplate`. Kept **structurally aligned** with `system/templates/paper.md` (the human-facing copy): both follow the `paper` schema in `.memoria/schemas/types/paper.yaml`. They are not identical field-for-field (the citation copy carries Zotero `{{vars}}`); edit both together when the shared structure changes. |

### CSS snippets

| Snippet | Required value | Constraint |
| --- | --- | --- |
| `memoria-link-colors.css` | Enabled by default through the installer-maintained `enabledCssSnippets` entry in `appearance.json`; user can toggle after install | Colors wikilinks by folder/type and adds lifecycle accents when Supercharged Links exposes `data-link-*` attributes. |
| `memoria-property-badges.css` | Enabled by default through the installer-maintained `enabledCssSnippets` entry in `appearance.json`; user can toggle after install | Accents scan-critical Properties rows: `lifecycle`, `ingest_status`, `loudness`, and verification status. This is the visual layer for the property display order in [Frontmatter fields](frontmatter.md). |

### obsidian-git

| Setting | Required value | Constraint |
| --- | --- | --- |
| `commitMessage` / `autoCommitMessage` | `"vault: {{date}} {{numFiles}} files"` | `{{numFiles}}` makes abnormally large auto-commits visible. Set both keys so timed and manual commits match. |
| `autoBackupAfterFileChange` | `false` | Produces hundreds of commits per session when Hermes is writing; use scheduled commits instead. |
| `autoSaveInterval` | `30` | Scheduled commit every 30 min (the replacement for per-change backup). `0` disables it. |
| `pullBeforePush` | `true` | Required; prevents conflicts once a remote is configured. |
| `autoPullOnBoot` | `false` | Required default; fresh sandboxes and local-only vaults have no upstream branch, so startup must not emit a git pull error. Users with a remote can enable boot pulls after setting an upstream. |
| `post-commit` hook | enabled | Load-bearing — enqueues Peer-reviewer verification for committed `projects/**/*.md` drafts. Source lives in `.githooks/`, installer copies it into `.git/hooks/`; it is not a `data.json` setting. Do not disable. |

The host running Obsidian or the sandboxed test runtime must have a real `git`
binary on `PATH`. Without it, obsidian-git, pre-commit schema validation,
verify-on-commit, rollback, and history are degraded; the installer now fails
clearly instead of silently skipping those paths.

> **Note:** obsidian-git has no `pullBeforeCommit` setting (earlier docs listed one in error). Divergence is caught by manual pulls plus `pullBeforePush`; enable `autoPullOnBoot` only after the vault branch has an upstream. Push is governed by `disablePush` and `autoPushInterval` (`0` = no auto-push), not an `autoPush` boolean — the table below maps each deployment onto those two real keys.

**Push behavior by deployment** (the two keys that actually exist):

| Deployment | `disablePush` | `autoPushInterval` | Notes |
| --- | --- | --- | --- |
| `local-only` | `false` | `0` | Push manually for offsite-backup checkpoints. |
| `local-mesh` | `false` | `0` | Syncthing handles sync; Git is history only. |
| `obsidian-sync` | `false` | `0` | Obsidian Sync handles sync; Git is history only. |
| `always-on` (desktop) | `false` | `> 0` (e.g. `10`) | Desktop auto-pushes as backup; Syncthing handles sync. |
| `always-on` (VPS) | `true` | `0` | VPS must only pull, never push. |

### dataview

| Setting | Required value | Constraint |
| --- | --- | --- |
| Enable JavaScript queries | `true` | Required; several dashboards use `dataviewjs` blocks. |
| Inline queries | `true` | Required; used in some reference notes for live field display. |
| `refreshEnabled` | `true` | Required; queries must update as notes change. |
| `refreshInterval` | `2500` (ms) | Default; lower values degrade performance on large vaults. |

### agent-client

| Setting | Required value | Constraint |
| --- | --- | --- |
| `defaultAgentId` | `memoria-copi` | The Co-PI is the only Agent Client chat partner (`test_agent_client_pane_is_copi_only`). |
| `customAgents[0].displayName` | `Memoria Co-PI` | The pane label uses the product-facing agent name, not the internal profile id. |
| `autoMentionActiveNote` | `true` | Active note is passed as a readable reference; selected text and explicit attachments carry bounded body context. |
| `exportSettings.defaultFolder` | `system/exports` | Session exports are visible PI review material; never point them at hidden `.memoria/` internals. |
| `exportSettings.autoExportOnNewChat` / `autoExportOnCloseChat` | `true` / `true` | Pane sessions export automatically at session start and close. |
| `exportSettings.openFileAfterExport` | `false` | Exporting a session must not steal focus from the Co-PI conversation. |
| `exportSettings.imageCustomFolder` | `system/exports/assets` | Exported images stay beside the visible transcript surface, never in hidden runtime internals. |

### cmdr

| Setting | Required value | Constraint |
| --- | --- | --- |
| `leftRibbon` | Capture fleeting, capture from Zotero selection, capture source from URL, delegate task, resolve inbox card. | The always-visible ribbon carries the commands needed for the capture → triage loop; space switching lives in dashboard nav rows. |
| `pageHeader` | Capture fleeting, create linked claim note, write claim note, extract claims, link claim. | Fast capture and note-local actions sit beside the active note, where their active-note defaults are visible. |
| `showAddCommand` | `false` | The shipped toolbar is curated; ad hoc personal buttons can still be added from Commander settings. |

### modalforms

| Setting | Required value | Constraint |
| --- | --- | --- |
| `formDefinitions[].name` | `memoria-fleeting-capture`, `memoria-source-capture`, `memoria-claim-capture`, `memoria-project-start` | Generated by `scripts/gen-forms.py` from each form type's `creation.form` block in `src/.memoria/schemas/types/`; `tests/test_modalforms.py` fails if the committed plugin data drifts. |
| `research_area` / `methodology` / `topics` / `scope_topics` fields | Fixed options projected from `system/vocabulary.md` where a schema creation input names a vocabulary. | The type schema owns which field appears on the form; `system/vocabulary.md` owns the option values. |
| `globalNamespace` | `MF` | Keeps the plugin API available at the default namespace used by Modal Forms examples. |

### portals

Portals persists its shortcuts, hidden items, custom icons, and explorer
replacement settings to a vendored `data.json`. It is adopted as supplemental reach
chrome only; primary navigation stays in spaces and Bases views.

| Setting | Required value | Constraint |
| --- | --- | --- |
| `spaces[]` | Shortcuts for the vault homes behind Inbox, Library, Knowledge, and Project work. | Portals is supplemental reach-only navigation; no tag portals and no space switching. |
| `replaceFileExplorer` | `true` | Portals replaces the visible explorer surface through its own setting while the core `file-explorer` plugin remains enabled as fallback. |
| `hiddenItems` | `{ "system": true, ".memoria": true }` | Runtime and generated infrastructure stay out of the PI-facing navigation pane. |
| `tagNotesFolderPath` | `system/_tag-notes` | Keeps the plugin's tag-note folder out of the user namespace. |
| `splitViewTabs` | `recent`, `bookmarks`, `context-notes`, `trash` | Drops journal/properties modules because Memoria does not use tag/daily-note navigation as primary structure. |

### memoria-inspector

| Setting | Required value | Constraint |
| --- | --- | --- |
| View type | `memoria-inspector-view` | Opens as a right-sidebar pane through the plugin command or ribbon icon. |
| Data sources | `system/logs/board-state.jsonl`, `system/logs/audit.jsonl`, latest `system/metrics/lint-verdict-*.md`, latest `system/metrics/lane-*.md` | Read-only operational snapshot only; the plugin has no vault write path, network request path, or shell path. |
| Deep links | Board state, audit log, Maintenance drift watch, and fleet health. | Uses native Obsidian note links only; the Inspector remains an observability pane, not an action surface. |
| Refresh cadence | Manual refresh plus 60 s refresh while open | Keeps the inspector current without becoming an action surface. |

### callout-manager

| Setting | Required value | Constraint |
| --- | --- | --- |
| `callouts.custom` | `["brief", "suggestions", "verification"]` | The three Memoria callout types must be registered as custom callouts. |
| `callouts.settings` | per-callout `color` (RGB triplet) + `icon` (Lucide id) | `brief` = `74, 144, 226` / `lucide-info`; `suggestions` = `123, 74, 226` / `lucide-list-plus`; `verification` = `226, 164, 74` / `lucide-shield-check`. Colors are stored as comma-separated RGB strings (not hex) — that is the format Callout Manager writes to `--callout-color`. |

---

## Related

- Plugin inventory: [Obsidian plugins](obsidian-plugins.md)
- Plugin data-file conventions: [Obsidian plugin data files](obsidian-plugin-data-files.md)


---

<!-- source: reference/obsidian-plugins.md -->

# Obsidian plugins

Obsidian plugin inventory, install status, and load-bearing configuration for Memoria. For Zotero-side add-ons and the Zotero↔Obsidian connector comparison see [Zotero plugins](zotero-plugins.md). For the plugin model and reasoning see [explanation/obsidian/](../explanation/obsidian).

---

## Required Obsidian plugins (13)

Memoria breaks without these. The starter vault **ships all thirteen bundled and configured** in `.obsidian/plugins/` — twelve third-party plugins plus the Memoria-authored Inspector, with no manual install. Enable community plugins (turn off Restricted mode) on first launch; see [Set up Obsidian](../how-to-guides/setup/set-up-obsidian.md).

The provenance lock for the bundled artifacts is
`src/.obsidian/plugin-provenance-lock.json`: it records each required plugin's
upstream repository, pinned local version, artifact SHA-256 digests, license assertion,
and local patch status. `python scripts/plugin_provenance_doctor.py` validates the
lock in the required gate: every enabled plugin is represented once, declared
artifacts exist and match their digests, and no undeclared executable artifact is
bundled. Updater automation remains deferred by
[ADR-74](../adr/74-pinned-obsidian-plugin-supply-chain.md).

| Plugin | ID (`.obsidian/plugins/<id>/`) | Purpose |
| --- | --- | --- |
| obsidian-local-rest-api | `obsidian-local-rest-api` | Exposes the vault to Hermes via its native MCP over verified loopback HTTPS (default port 27124). Required for the control plane. |
| agent-client | `agent-client` | ACP inside Obsidian — routes human conversations with Hermes through a chat pane. |
| dataview | `dataview` | Powers every dashboard. Without it the dashboard layer is non-functional. |
| templater-obsidian | `templater-obsidian` | Provides the template folder integration for manual template insertion. |
| quickadd | `quickadd` | Registers all `Memoria:` command palette entries. |
| cmdr | `cmdr` | Places the high-frequency `Memoria:` commands in the ribbon and page header so capture, delegation, and resolution do not require a palette round trip. |
| modalforms | `modalforms` | Provides structured in-Obsidian forms for capture and Project flows, generated from type-schema `creation.form` metadata with controlled options sourced from `system/vocabulary.md`. |
| portals | `portals` | The curated file browser for the left sidebar — replaces the core file explorer with folder roots (inbox, catalog, sources, claims, hubs, projects) and hides `system/`/`.memoria/`. The navigation rail and Bases are the primary navigation surface; Portals is for browsing the underlying notes. |
| obsidian-citation-plugin | `obsidian-citation-plugin` | Inserts citations from `.memoria/memoria.bib`; creates paper notes from the configured template. (Zotero-side: see [Zotero plugins](zotero-plugins.md).) |
| memoria-inspector | `memoria-inspector` | Memoria-authored read-only sidebar pane for board counts, WIP depth, recent audit entries, and the Linter verdict band ([ADR-84](../adr/84-read-only-obsidian-inspector.md)). |
| callout-manager | `callout-manager` | Defines `[!brief]`, `[!suggestions]`, `[!verification]` callout types. |
| obsidian-git | `obsidian-git` | Git commits from inside Obsidian; the `post-commit` hook enqueues project-draft verification. |
| buttons | `buttons` | Supports command-button snippets in note bodies. **Command-type buttons only** — the plugin's `template`/`text`/`calculate` button types write to notes outside the policy gate and are banned. Needs no `data.json` (defaults). |

---

## Recommended Obsidian plugin rows (9)

Install when the friction is felt. Not required for core function.

### Core seven

| Plugin | Purpose |
| --- | --- |
| smart-connections | Vector search across notes. |
| smart-lookup | Question-first semantic search (shares index with smart-connections). |
| omnisearch | Fast fuzzy full-text search (keyword counterpart to smart-*). |
| supercharged-links + style-settings | Tune the shipped CSS snippets for link colors and property state badges. |
| hover-editor | Preview wikilinked notes in a popup. |
| tag-wrangler | Bulk-rename, merge, and inspect tags. |
| pdf-plus | Deep-link from notes to specific PDF passages. |

### Narrower two (install for specific use cases)

| Plugin | When to install |
| --- | --- |
| obsidian-outliner | When nested-list editing becomes friction. |
| obsidian-excalidraw | When hand-drawn diagrams are needed (stored as `.excalidraw`). |

---

## Reference plugins (evaluated, not in the install set)

Documented but not in the install set. Obsidian-side evaluated alternatives. (Zotero-connector alternatives — zotlit, zotero-integration — are in [Zotero plugins](zotero-plugins.md).)

| Plugin | Status | Notes |
| --- | --- | --- |
| obsidian-kanban | Evaluated, not wired in | Cannot render `kanban.db` without an unadopted bridge. |
| Workspaces Plus | Evaluated, not shipped | Registers workspace-switching commands, but [ADR-81](../adr/81-persistent-gate-dashboards.md) keeps space switching in dashboard notes rather than saved workspace layouts. The core Workspaces plugin remains only as a reset layout. |
| obsidian-linter | **Incompatible — do not install** ([ADR-12](../adr/12-obsidian-linter-reference-only.md)) | Frontend formatter; second frontmatter authority that collides with the agent-owned `_proposed_classification` / `_enrichment` namespaces and writes outside the policy MCP audit trail. No config makes it safe. |

---

## Load-bearing settings

The required per-plugin settings live in [Obsidian plugin settings](obsidian-plugin-settings.md).

## `data.json` conventions

Committed, generated, example, and secret-bearing plugin data-file rules live in [Obsidian plugin data files](obsidian-plugin-data-files.md).

## Related

- How a new user enables these plugins: [Quickstart](../how-to-guides/setup/quickstart.md)


---

<!-- source: reference/obsidian-workspaces.md -->

# Obsidian workspaces

Memoria ships one saved Obsidian workspace named **Memoria** in
`src/.obsidian/workspaces.json`. It is a reset layout, not the space switcher
([ADR-81](../adr/81-persistent-gate-dashboards.md)).

Space switching happens through the navigation rail — the pinned `_nav.md` note in
the left pane. Its **Now** section surfaces the Inbox queue action count and the
Maintenance/Fleet health band, and its **Places** section links the three durable spaces:

| Space | Job | Dashboard |
| --- | --- | --- |
| Library | Collect and organize sources | `spaces/library.md` |
| Knowledge | Build and test claims | `spaces/knowledge.md` |
| Project | Steer bounded inquiry to output | `spaces/project.md` |

The Inbox queue (`spaces/inbox.md`, `type: queue`) and Maintenance collection
(`spaces/maintenance.md`, `type: maintenance`) are reached from the rail's **Now**,
not from **Places**. Each space dashboard embeds the relevant Bases views; the rail
owns switching, so the dashboards no longer carry a nav row. Clicking a rail link opens
that dashboard in the active tab; it does not load a new workspace layout.

On launch QuickAdd runs the `Memoria: restore shell on startup` macro, which asks
Obsidian's core Workspaces plugin to load the saved **Memoria** workspace. That makes
normal startup, a fresh vault, and a layout reset land on the same shell: `home.md` in
the main pane, the pinned rail on the left, and the Co-PI pane on the right. There is
no Homepage plugin and no Inbox forced landing.

## Reset layout

The **Memoria** workspace has one shared shell:

- **Main pane** — `home.md`, the launch/reset welcome note, opened in reading view.
- **Left sidebar** — two tabs: the `_nav.md` navigation rail (surface switching) and the
  Portals curated file browser, which replaces the core file explorer and hides `system/`
  and `.memoria/`. Primary movement happens through the rail and the Bases views on each
  space dashboard; Portals is for browsing the underlying notes.
- **Right sidebar** — the Co-PI Agent Client chat view.

The core Workspaces plugin stays enabled so startup can restore this shell and so you
can restore it manually with Obsidian's own **Manage workspaces** command if panes get
rearranged. Space switching is not exposed through QuickAdd commands or loader scripts.

Workspaces Plus was evaluated and rejected for the shipped path. It can register
native workspace-switching commands, but Memoria models spaces as dashboard notes
reached from the navigation rail, not saved workspace layouts; the rail and the
dashboard notes in `spaces/` are the source of truth.

## Layout storage

The reset layout is saved in `.obsidian/workspaces.json`. Runtime state such as
`.obsidian/workspace.json` remains per-machine and is not part of the golden copy.

---

## Related

- Gate decision: [ADR-81](../adr/81-persistent-gate-dashboards.md)
- The superseded workspace model: [ADR-68](../adr/68-workspaces-desk-library-studio.md)
- The dashboard roster: [Dashboards](dashboards.md)
- The plugin set behind the panes: [Obsidian plugins](obsidian-plugins.md)
- Conversation surface: [Agent Client pane](../how-to-guides/using-obsidian/use-the-agent-client-pane.md)


---

<!-- source: reference/on-disk-layout.md -->

# On-disk layout

Where every file lives. The repo ships the vault under **`src/`**; the installer scaffolds the folder skeleton in your chosen runtime vault (default `~/Memoria`) and populates it from `src/` ([ADR-55](../adr/55-src-scaffold-populate-golden-copy.md)). Repo and deployed vault have the same internal shape; the deployed vault additionally grows the runtime-only artifacts listed at the end. The tree itself is fixed by [ADR-47](../adr/47-type-first-category-folders.md): six legal vault-root categories, with the type → folder map living in `src/.memoria/schemas/folders.yaml`. `.memoria/` is never opened by the PI; if a workflow tells the PI to open a `.memoria/...` path, that workflow is wrong.

---

## The vault tree

```text
<vault>/
├── home.md                  launch/reset welcome note
├── _nav.md                  the navigation rail — pinned in the left pane, owns space-switching
├── research-focus.md        program memory — the PI's standing steering
├── AGENTS.md                ground rules for any agent in the vault
├── troubleshooting.md       vault-root nav page
├── catalog/                 entity records (given relationships)
│   ├── catalog.base           the Catalog Bases view
│   ├── papers/  people/  organizations/  venues/  datasets/  repositories/
├── notes/                   the PI's knowledge (authored links:)
│   ├── fleeting/  sources/
│   ├── claims/                review-gated
│   └── hubs/                  review-gated
├── projects/                project records, theses, drafts, code, exports
│   └── _template/             starter project scaffold copied by the Project on-ramp
├── inbox/                   the action queue — candidate/gap/flag/alert/work-prompt cards
│   └── inbox.base             the Inbox board view
├── spaces/                  space dashboards + Inbox queue + Maintenance collection
└── system/                  infrastructure plus typed system homes
    ├── vocabulary.md          controlled vocabularies
    ├── templates/             starter notes per type
    ├── dashboards/            5 read-only system dashboards + claims/sources/fleeting .base files
    ├── patterns/              the pattern library (+ patterns.base, _preamble.md)
    ├── scripts/               QuickAdd capture scripts (capture-from-url/-zotero)
    ├── board/                 board-export card projections
    ├── eval/                  the vault-eval gold set (eval-task notes + last-run.md)
    ├── worklists/             Bases-backed batch screening rows (worklist-item notes)
    ├── metrics/               derived metric notes (lane-*, lint-verdict-*) + eval/runs.jsonl
    └── logs/                  audit.jsonl, capture-intake.jsonl, patterns.jsonl, sessions/
```

The six vault-root categories (`catalog`, `notes`, `projects`, `inbox`, `spaces`, `system`) are the legal top-level set — the Linter flags any stray root folder. The gated and transient prefixes those subfolders carry are declared in `folders.yaml`, not hardcoded; what they mean is in [Document types](document-types.md).

---

## `.memoria/` — the runtime tooling layer

Hidden from Obsidian; everything agents and operations need, shipped in `src/.memoria`:

```text
.memoria/
├── schemas/                 THE single schema source (ADR-49/50)
│   ├── types/<type>.yaml      25 per-type schemas; capture forms read creation.form
│   ├── folders.yaml           type→folder homes, gated/transient prefixes, skeleton
│   └── calibration.yaml       drift-bound thresholds (entity-resolution, classify, hybrid scores, cluster params)
├── operations/              the deterministic operation cores
│   ├── lib/                   schema.py (loader/validator) + inbox.py (card writer) + loudness.py (alert/block routing)
│   ├── processing/ingest/     runner.py, ingest_paper.py, resolve_merge.py, extract.py, link.py
│   ├── integrity/linter/      detectors.py, hub_handoff.py, precommit_check.py, pre-commit, golden_restore.py
│   ├── integrity/retraction/  retraction.py
│   ├── cleanup/               reconcile.py, archive_inbox.py
│   └── telemetry/eval/        eval_dispatch.py, eval_score.py
├── mcp/                     the MCP servers (Layer 5)
│   ├── policy_mcp.py + policy_server.py + policy_hook.py     the write gate
│   ├── ingest_mcp.py · cluster_mcp.py · tasks_mcp.py · patterns_mcp.py
│   ├── board_export.py · metrics_aggregate.py    telemetry (cron, not MCP)
│   └── requirements.txt · requirements-cluster.txt
├── profiles/                the five Hermes profile packages
│   └── memoria-{copi,librarian,writer,peer-reviewer,engineer}/
│       ├── SOUL.md · config.yaml · distribution.yaml · skills/
├── lane-overrides/          the five lane ceilings: copi/librarian/writer/peer-reviewer/engineer.yaml
├── samples/                 optional bundled tutorial corpora, loaded by QuickAdd commands
│   └── mediterranean-diet/    hidden source for Memoria: load sample vault
├── plugins/memoria-policy-gate/   the fail-closed write-gate Hermes plugin
├── scripts/                 cron wrappers (sweeps, lint, board-export, retraction refresh)
├── tool-registry.yaml       authoritative per-profile tool allowlist
├── memoria.bib              the bibliographic backbone export
├── design-system.md · project-hints.yaml.example
```

The policy gate's stable deployed entrypoint stays in `.memoria/mcp/`, while its
behavior-preserving decision/audit/engine modules live in the installed
`memoria.runtime.policy` package.

## `.githooks/` — source hooks

Shipped in `src/.githooks`: canonical git hooks that the installer copies into the runtime vault's `.git/hooks/` after the user initializes the vault repository. `post-commit` enqueues Peer-reviewer verify cards for committed Markdown drafts under `projects/`.

Runtime-only (created in the deployed vault, never shipped):

| Path | Created by | Holds |
| --- | --- | --- |
| `.memoria/golden/` | installer (`golden_restore.py stage`) | The restorable golden copy of every system file + `manifest.json` (SHA-256). |
| `.memoria/data/extracts/` | ingest MCP | Full-text extracts per citekey — outside the Librarian's write lane. |
| `.memoria/data/retraction_watch.csv` | retraction refresh cron | The local Retraction Watch index. |
| `.memoria/.venv/` | installer | The vault-local Python the MCP servers run on. |
| `.git/hooks/pre-commit` | installer | The pre-commit hook (once the vault is a git repo). |
| `.git/hooks/post-commit` | installer | The verify-on-commit trigger copied from `.githooks/post-commit`. |

---

## `.obsidian/` — app configuration

Shipped in `src/.obsidian`: `app.json`, `appearance.json` (starter snippet toggles), `core-plugins.json`, `community-plugins.json`, `graph.json` (link color-groups), `snippets/` (`memoria-link-colors.css`, `memoria-property-badges.css`), and per-plugin config under `plugins/` (QuickAdd, Commander, Modal Forms, agent-client, Local REST API, Buttons, Dataview, Templater, Citation, Callout Manager, Obsidian Git, Portals). `src/.obsidian/workspaces.json` ships one reset layout named **Memoria**; QuickAdd restores it on startup, with `src/home.md` in the main pane and the pinned `src/_nav.md` rail on the left. Space switching is handled by the rail over the space dashboards `src/spaces/library.md`, `src/spaces/knowledge.md`, and `src/spaces/project.md`, with the Inbox queue at `src/spaces/inbox.md` and Maintenance collection at `src/spaces/maintenance.md` (see [Obsidian workspaces](obsidian-workspaces.md)).

### The Bases views

The `.base` files sit alongside their data: `catalog/catalog.base`, `inbox/inbox.base`, `notes/hubs/hubs.base`, `projects/projects.base`, `system/board/board.base`, the `claims`/`sources`/`fleeting` bases in `system/dashboards/`, `system/patterns/patterns.base`, and `system/worklists/worklists.base` ([ADR-49](../adr/49-catalog-in-bases-linter-monitor.md)). What each view shows is in [Dashboards](dashboards.md#the-bases-views).

---

## Outside the vault

| Path | Holds |
| --- | --- |
| `<repo>/scripts/` | `install.sh` / `install.ps1`, `docs_doctor.py`, test drivers — install tooling never deploys into the vault. |
| `%LOCALAPPDATA%\hermes\profiles\memoria-*` (Windows) / `~/.hermes/profiles/memoria-*` (Linux/WSL2) | The deployed profile copies (config substituted, `.env` seeded). |
| `%LOCALAPPDATA%\hermes\scripts\` (Windows) / `~/.hermes/scripts/` (Linux/WSL2) | The substituted cron wrappers (`memoria-sweeps.sh`, `memoria-lint.sh`, `memoria-board-export.sh`, …), copied and renamed from the repo's `.memoria/scripts/<job>-cron.sh`. |
| `%LOCALAPPDATA%\hermes\.env` (Windows) / `~/.hermes/.env` (Linux/WSL2) | The shared secrets file the installer propagates per profile. |

---

## Related

- How `src/` becomes a runtime vault: [Installer (bootstrap)](installer.md)
- The type → folder homes in table form: [Document types](document-types.md)
- What keeps the deployed tree honest: [Linter: detectors and auto-fix](linter.md)


---

<!-- source: reference/operations.md -->

# Operations

Deterministic mechanisms that agents, cron, CI, and the PI can invoke. Agents reach processing operations through MCP facades; trusted local callers may use direct entries. Integrity, cleanup, and telemetry operations run directly because they are not agent-facing.

Shared dependency-light helpers for operation code live under `memoria.runtime`
(`vaultio`, `jsonl`, `time`, and `paths`). MCP modules import those helpers
directly; package code owns the behavior.

| Operation | Primary entry point | MCP facade | Direct callers | What it does |
| --- | --- | --- | --- | --- |
| Ingest | `src/.memoria/operations/processing/ingest/runner.py` | `src/.memoria/mcp/ingest_mcp.py` | PI, tests, debug sessions | Fetches metadata, extracts text, builds entity `relationships`, and prepares Catalog records. |
| Project structural impact | `src/.memoria/operations/processing/project/structural_impact.py` | None | PI, tests, future Project dashboard | Traverses the thesis-rooted `supports`/`contradicts` argument graph and writes one generated Project gate index note with `impact`, `on_path`, gap findings/advisories, `evidence_saturation`, `argument_stage`, and `computed_at`. |
| Search | qmd plus Obsidian MCP | Profile MCP tools | PI, debug sessions | Performs deterministic retrieval over the vault. |
| Clustering | `src/.memoria/mcp/cluster_mcp.py` | `src/.memoria/mcp/cluster_mcp.py` | PI, tests, debug sessions | Builds typed link-structure graphs, topic models, and claim-debate Canvas artifacts. |
| Integrity retraction | `src/.memoria/operations/integrity/retraction/retraction.py` | None | Cron, CI, PI | Runs retraction lookups, surfacing findings as Inbox cards. |
| Cleanup sweeps | `src/.memoria/operations/cleanup/*.py` | None | Cron, CI, PI | Reconciles capture gaps and archives resolved Inbox cards. |
| Eval telemetry | `src/.memoria/operations/telemetry/eval/*.py` | None | Cron, CI, PI | Dispatches and scores vault-eval runs. |
| Linter | `src/.memoria/operations/integrity/linter/detectors.py`; `hub_handoff.py` | None | Cron, CI, pre-commit, PI | Validates schemas, links, graph health, audit-chain integrity, golden-copy drift, session digests, and opt-in hub-threshold handoffs. |
| Batch worklists | `src/.memoria/operations/lib/worklists.py` | None | Reports, tests, PI | Emits ADR-54 `worklist-item` rows from a report and raises one aggregate Inbox `work-prompt` for the batch. |

## Related

- Why operations are separate from agents: [Operations — the deterministic layer](../explanation/operations/)
- Ingest command details: [Ingest routing](ingest.md)
- Project-gate cache details: [Project structural impact](project-structural-impact.md)
- Sweep command details: [Sweeps](sweeps.md)
- Batch worklist command details: [Worklists](worklists.md)
- Linter command details: [Linter: detectors and auto-fix](linter.md)


---

<!-- source: reference/patterns.md -->

# Pattern library

The shipped runnable patterns, the pattern-note schema, and the `patterns_list` / `patterns_run` contract. Patterns are *data* — markdown prompt-transformations in `system/patterns/` — and the patterns MCP (`src/.memoria/mcp/patterns_mcp.py`) is the single audited chokepoint that runs them ([ADR-53](../adr/53-pattern-library.md)). The runner never writes content: it composes a prompt and hands it back through the gated path the calling agent already uses. To invoke one from Obsidian, see [Run a pattern](../how-to-guides/knowledge/run-a-pattern.md); for why provenance is recorded, see [Pattern provenance: borrow, adapt, ignore](../explanation/rationale/why-pattern-provenance.md).

---

## The shipped patterns

Seven patterns ship at `lifecycle: current` (runnable). Each is one file under `system/patterns/`; the file `stem` is its `pattern_id`.

| Pattern (`id`) | Title | `posture` | `action` | `mode` | `input` | `output_target` |
| --- | --- | --- | --- | --- | --- | --- |
| `analyze-claims` | Analyze claims | peer-reviewer | analyze | both | selection-or-note | `projects/` |
| `check-falsifiability` | Check falsifiability | peer-reviewer | check | both | selection-or-note | `projects/` |
| `compare-and-contrast` | Compare and contrast | librarian | compare | both | two-or-more-notes | `projects/` |
| `extract-claim-stubs` | Extract claim stubs | librarian | extract | library | source-note | `notes/fleeting/` |
| `red-team-argument` | Red-team an argument | peer-reviewer | check | project | draft-or-claim | `projects/` |
| `summarize-for-recall` | Summarize for recall | librarian | summarize | both | selection-or-note | `notes/fleeting/` |
| `surface-tensions` | Surface tensions | librarian | link | library | note-set | `projects/` |

`mode` filters the picker: `library` patterns are for ongoing reading, `project` patterns for a writing project, `both` for either. The set is authored directly — the files *are* the instances, there is no template — and staged into the golden copy like the other system files ([Installer (bootstrap)](installer.md)).

---

## The pattern-note schema

Every pattern file is YAML frontmatter followed by a single `# Pattern` body. The body is the prompt; `{{input}}` is the one substitution token.

| Field | Kind | Meaning |
| --- | --- | --- |
| `title` | str | Display name in the picker. |
| `type` | `literal:pattern` | Identifies the note as a pattern; non-patterns are skipped. |
| `lifecycle` | `proposed → current → archived` | Only `current` patterns are runnable; `run` on a non-current pattern errors `pattern-not-current`. |
| `posture` | enum | The voice the run adopts (`librarian` / `peer-reviewer`) — echoed back to the caller as `posture`. |
| `mode` | `library` \| `project` \| `both` | Which picker view the pattern appears in. |
| `action` | str | The verb (`analyze` / `check` / `compare` / `extract` / `summarize` / `link`). |
| `input` | str | The expected input shape (`selection-or-note`, `source-note`, `note-set`, …) — documentation for the caller, not enforced. |
| `output_target` | path | Where the run's product is meant to land. An empty or review-gated target forces dry-run (below). |
| `model_hint` | str (optional) | A suggested model tier, passed through as `model_hint`; empty means caller's default. |
| `version` | str | Logged with every run for provenance. |
| `adapted_from` | str (optional) | Upstream provenance of the prompt (e.g. `fabric/analyze_claims`). |
| `created` | date | — |

The schema is enforced by the Linter and the pre-commit hook, the same machinery that guards every other system note.

---

## The runner

The MCP exposes two tools. Both are read-only; neither writes a vault note.

### `patterns_list(mode="")`

Returns the runnable (`lifecycle: current`) patterns, optionally filtered by `mode` (`library` / `project`; `both`-mode patterns always match). Each row is `{id, title, mode, action, posture, output_target}`. Files whose name starts with `_` (the preamble) are skipped.

### `patterns_run(pattern_id, input_text="", input_ref="")`

Loads the pattern by id, composes the prompt, enforces the gated-zone rule, logs provenance, and returns the prompt for the calling agent to execute and write through its normal gated path.

| Return field | Meaning |
| --- | --- |
| `run_id` | 8-char id correlating the return value with its provenance line. |
| `pattern` | The `pattern_id` that ran. |
| `prompt` | The composed prompt: `preamble` + `---` + pattern body with `{{input}}` substituted. |
| `output_target` | The pattern's staging target (empty when dry-run). |
| `dry_run` | `true` when the target is missing or review-gated — the run produces a prompt but no sanctioned write target. |
| `posture` | The pattern's posture, for the caller's voice. |
| `model_hint` | The pattern's `model_hint`, or `null`. |
| `note` | Present only on dry-run: explains the target was missing or gated. |
| `provenance_logged` | Present (and `false`) only when the provenance append failed — the prompt still returns, but the run left no audit line (also warned on stderr). |

An unknown id returns `{"error": "unknown-pattern", "available": [...]}`; a non-current pattern returns `{"error": "pattern-not-current"}`.

---

## Composition: preamble + pattern + input

Every run is prefixed with the shared voice preamble at `system/patterns/_preamble.md` ([ADR-53](../adr/53-pattern-library.md)). It is non-negotiable regardless of the pattern, and encodes four rules: output is raw material for the PI to rewrite; propose, never assert; cite, don't fabricate (a missing source is a visible `[no source]`, never invented); and stay inside the provided input. `{{input}}` in the pattern body is replaced with `input_text`; when only an `input_ref` is supplied (e.g. the active note path), the token becomes `[see <input_ref>]` and the executing agent reads that reference itself.

---

## Gated-target dry-run

A pattern is a *proposal* tool — propose-not-dispose holds. `patterns_run` refuses to hand back a sanctioned write target inside a review-gated zone: when `output_target` is empty, or starts with a gated prefix (read from `.memoria/schemas/folders.yaml` `gated_prefixes`, falling back to the policy core's `REVIEW_GATED_PREFIXES`), the run degrades to `dry_run: true` and the Linter flags the pattern file. The shipped patterns target only staging homes (`projects/` scratch and `notes/fleeting/`), so they run live; a pattern pointed at `notes/claims/` or `catalog/` would dry-run by design. The product still reaches canonical notes only through the normal human gate.

---

## Provenance

Every run appends one JSONL line to `system/logs/patterns.jsonl` before the prompt is returned — the audit trail that makes pattern output traceable.

```json
{"timestamp": "2026-06-01T14:23:01Z", "run_id": "a1b2c3d4", "pattern": "analyze-claims", "version": "1.0", "input_ref": "notes/sources/vaswani2017.md", "input_chars": 0, "output_target": "projects/", "dry_run": false}
```

| Field | Meaning |
| --- | --- |
| `timestamp` | ISO-8601 UTC, `Z`-suffixed (the [Telemetry & logs](telemetry.md) convention). |
| `run_id` | Correlates with the `run_id` in the tool return value. |
| `pattern` / `version` | Which pattern and pattern version ran. |
| `input_ref` | The reference passed in (a note path), or empty when raw text was supplied. |
| `input_chars` | Length of the supplied `input_text` (0 when only a reference was passed). |
| `output_target` | The staging target the run resolved to. |
| `dry_run` | Whether the run was a dry-run (missing/gated target). |

A failed provenance write does not abort the run — the prompt is the product — but the return value carries `provenance_logged: false` and a stderr warning so the operator knows the run left no line.

---

## Related

- Running a pattern from Obsidian: [Run a pattern](../how-to-guides/knowledge/run-a-pattern.md)
- Why runs are provenance-logged: [Pattern provenance: borrow, adapt, ignore](../explanation/rationale/why-pattern-provenance.md)
- The palette commands that invoke the runner: [Obsidian command palette](obsidian-command-palette.md)
- Every action the system performs: [System actions](system-actions.md)
- The picker view over the library: [Dashboards](dashboards.md)


---

<!-- source: reference/policy-audit-log.md -->

# Policy audit log

The audit trail written by the Policy MCP. For the request/response protocol and lane enforcement rules, see [Policy MCP](policy-mcp.md).

## Format

Every decision is appended to **`system/logs/audit.jsonl`** (append-only JSONL — crash-safe, grep-friendly).

### Fields

| Field | Type | Notes |
| --- | --- | --- |
| `schema_version` | integer | Audit-log schema version. Current value: `2`. |
| `review_mode` | enum | Current review-gate arm. Production value: `blocking`; advisory behavior remains deferred. |
| `timestamp` | ISO datetime | UTC, `…Z`. |
| `profile` | string | `memoria-<name>` — which lane triggered the action. |
| `action` | string | One of the eight actions above (`read` / `write` / `append` / `move` / `delete` / `mkdir` / `auto_fix` / `report`). |
| `path` | string | The vault-relative path targeted. |
| `task_id` | string | The board card that triggered the action (required on every request). |
| `decision` | enum | Exactly one of `allow` · `allow_with_log` · `deny` · `dry_run`. |
| `policy_rule` | string | Which lane-override rule matched. |
| `reason` | string | Optional prose from the request. |
| `before_hash` / `after_hash` | SHA-256 | The reversibility pair (see below). |

A representative decision entry:

```json
{
  "schema_version": 2,
  "review_mode": "blocking",
  "timestamp": "2026-06-10T14:23:01Z",
  "profile": "memoria-librarian",
  "action": "write",
  "path": "catalog/papers/smith-2024.md",
  "task_id": "TASK-2026-06-10-003",
  "decision": "allow",
  "policy_rule": "Librarian.write.catalog",
  "before_hash": "sha256:e3b0c44298fc1c149afbf4c8996fb924...",
  "after_hash": null
}
```

### Per-write hash pairing

Auditing uses **per-write SHA-256 hash pairing, not a cross-entry chain**: each mutating write produces a `before_hash` on the decision entry, and a *separate* `write_complete` record carries the paired `after_hash` once the write lands. `write_complete` is a **record kind, not a value of the `decision` enum** — the four `decision` values are exactly `allow`, `allow_with_log`, `deny`, and `dry_run`. The two records are matched by `task_id` + `path`; the pairing pins one write's before/after state and nothing more — it does not hash-link successive entries.

**SHA-256 rules:** the MCP computes hashes — workers never supply them; format `"sha256:<64-hex>"`; a freshly-created file's `before_hash` is the empty-string SHA-256, never null; a hash read-error denies the request (no hash, no allow).

---

## Related

- Runtime gate: [Policy MCP](policy-mcp.md)
- Audit-memory substrate: [Memory substrates](memory.md)


---

<!-- source: reference/policy-auto-fix.md -->

# Policy auto-fix

The class gate for automated repairs that pass through the Policy MCP. For the request/response protocol and lane enforcement rules, see [Policy MCP](policy-mcp.md).

## Classes

| Class | Disposition | Examples |
| --- | --- | --- |
| `safe-and-unambiguous` | `allow_with_log` within the lane's write scope | Trailing whitespace, missing `created` with one obvious value |
| `authorized-targeted` | `allow_with_log`, `task_id`-bound | Findings-file truncation, golden-copy restore |
| `schema-content` | `dry_run` always | Field rename, enum change — needs `lint:migrate-schema` |
| `review-gated-edit` | `deny` always | Any write to a gated zone |

---

## Related

- Runtime gate: [Policy MCP](policy-mcp.md)
- Linter repair surfaces: [Linter: detectors and auto-fix](linter.md)


---

<!-- source: reference/policy-mcp.md -->

# Policy MCP

The runtime write-gate (`src/.memoria/mcp/policy_mcp.py`): it intercepts every vault action, checks the lane-override rules, and returns a decision before any content reaches disk. The stable deployed entrypoint is `policy_mcp.py`; the behavior-preserving core is split under `memoria.runtime.policy` (`model`, `paths`, `lanes`, `decision`, `audit`, and `engine`), with the MCP tools wrapped by `src/.memoria/mcp/policy_server.py`. Every rule lives in a versioned lane-override file — the gate is not a substitute for the review gate, not a content checker, and not a hidden controller.

---

## Request flow

```text
Hermes profile
  → tool call (write / move / delete / auto_fix)
    → Policy MCP
      → profile lookup in lane-override file
      → path + action evaluation
      → allow | allow_with_log | deny | dry_run
      → filesystem execution or diff report
```

Every request carries complete identity and task metadata. `task_id` is required — the MCP cannot ask the worker mid-decision which task it is running. A missing `task_id` or a path-traversal attempt (`..` escaping the vault root) is denied and audited.

---

## Action vocabulary

Eight guarded actions; `read` and `report` are non-mutating, the rest are subject to the review-gated `dry_run` rule.

| Action | Default disposition |
| --- | --- |
| `read` | Default-allow; `allow_with_log` in review-gated zones; an explicit `deny.read` wins. |
| `write` / `append` | `deny.write` wins; else `allow.write` → allow; else **default-deny**. `dry_run` in review-gated zones. |
| `move` | As write, and always `allow_with_log` when allowed. |
| `delete` | `deny` unless `flags.explicit_authorization` (then `allow_with_log`, within the lane's write globs); review-gated → `dry_run`. |
| `mkdir` | `allow` within `routing.write_scope`, else `deny`. |
| `auto_fix` | Class-gated via `flags.class` (see [Auto-fix policy](#auto-fix-policy)). |
| `report` | Always `allow` within the worker's lane. |

A skill loaded for the session can only **narrow**: its `policy.deny.write` patterns are composed additively onto the lane (one-way for the session; checked before everything but action validity).

---

## Decision values

| Decision | Meaning | Logged? |
| --- | --- | --- |
| `allow` | Action proceeds. | Only if the lane's `policy.require` includes `audit_log` (every shipped lane does). |
| `allow_with_log` | Action proceeds; audit entry mandatory. | Always. |
| `deny` | Action blocked; worker must escalate or choose a different path. | Always. |
| `dry_run` | Action logged and reported but not performed; the worker surfaces it as a board comment. | Always. |

**Two rules override lane configuration entirely:**

1. **Review-gated zones are never auto-written.** The gated prefixes are loaded from `src/.memoria/schemas/folders.yaml` (`gated_prefixes`) — currently `notes/claims/` and `notes/hubs/`. The dependency-free fallback tuple in `memoria.runtime.policy.paths` mirrors them (test-enforced to stay in sync). An otherwise-allowed mutating action there degrades to `dry_run` regardless of the lane's `policy.allow`. No profile can bypass this.
2. **Auto-fix is class-gated.** Only `flags.class ∈ {safe-and-unambiguous, authorized-targeted}` may proceed; `schema-content` is pinned to `dry_run` and `review-gated-edit` to `deny`, regardless of who asks.

---

## Request contract

```json
{
  "profile": "memoria-writer",
  "action": "write",
  "path": "projects/project-x/drafts/chapter-1.md",
  "reason": "draft synthesis from claim notes",
  "task_id": "TASK-2026-05-31-007",
  "flags": {
    "explicit_authorization": false,
    "class": null
  }
}
```

| Field | Required | Notes |
| --- | --- | --- |
| `profile` | yes | Must match a lane-override file (`memoria-writer` → `writer.yaml`). |
| `action` | yes | One of the eight actions above. |
| `path` | yes | Vault-root-relative, forward slashes; normalized (no `./`, no `..`) before evaluation. |
| `reason` | no | Short prose for the audit log. |
| `task_id` | yes | The board card that triggered the action. Required on every request. |
| `flags.explicit_authorization` | no | Required for `delete`; forces `allow_with_log` on writes. |
| `flags.class` | no | Required for `auto_fix`. |

Debugging an unexpected deny is a one-shot CLI away (the lane-override says what the rule is; the audit log says what was decided):

```bash
python3 .memoria/mcp/policy_mcp.py --vault <vault> \
  --decide '{"profile":"memoria-librarian","action":"write","path":"catalog/papers/x.md","task_id":"T1"}'
```

---

## Response contract

Allow:

```json
{ "decision": "allow", "policy_rule": "Librarian.write.catalog", "log_required": true }
```

Deny:

```json
{ "decision": "deny", "policy_rule": "Librarian.deny.write", "message": "memoria-librarian is denied write to 'notes/claims/x.md'" }
```

Dry-run:

```json
{ "decision": "dry_run", "policy_rule": "review_gated.dry_run", "message": "review-gated zone write requires approval — surface as board comment" }
```

On an allowed mutating action the response also carries `before_hash`; the worker calls `complete_write` after the write so the paired `after_hash` lands in the audit trail as a separate `write_complete` record (see [Audit log format](#audit-log-format)).

### Tools

| Tool | Does |
| --- | --- |
| `check_permission(profile, action, path, task_id, reason, flags)` | The decision entry point. |
| `complete_write(profile, action, path, task_id, before_hash)` | Records the post-write `after_hash` (reversibility / tamper trail). |
| `set_session_skill(task_id, skill_policy)` / `clear_session_skill(task_id)` | Register / drop a loaded skill's one-way deny narrowing. |

---

## Audit log format

The full audit-log schema, JSON example, decision enum, and per-write SHA-256 hash-pairing rules live in [Policy audit log](policy-audit-log.md).

## Auto-fix policy

The auto-fix classes and their dispositions live in [Policy auto-fix](policy-auto-fix.md).

## The five lane-overrides

The policy manifest for each profile lives in `src/.memoria/lane-overrides` — `copi.yaml`, `librarian.yaml`, `writer.yaml`, `peer-reviewer.yaml`, `engineer.yaml`. Shape:

```yaml
profile: memoria-librarian

policy:
  allow:
    skills: [obsidian, qmd]
    write:
      - "inbox/**"
      - "catalog/**"
      - "notes/fleeting/**"
      - "notes/sources/**"
  deny:
    skills: [review_gated_publish, destructive_shell]
    write:
      - "notes/claims/**"
      - "notes/hubs/**"
  require:
    - audit_log
    - timeout_required
    - source_tracking

routing:
  invocation: dispatched
  external_api_policy: explicit_only
  write_scope:
    - "inbox/"
    - "catalog/"
    - "notes/fleeting/"
    - "notes/sources/"
```

`policy.deny` wins over `policy.allow`; an unmatched path is default-denied. The Co-PI's override is the limiting case: `allow.write: []` plus `deny.write: "**"` — the structural guarantee behind "read directly, delegate writes". The full scope table is in [Profile capabilities](profiles.md).

One consequence worth naming: every shipped lane denies writes under `system/**` (the Co-PI under `**`), and no lane's `allow.write`, `routing.write_scope`, or auto-fix scope reaches into `system/` — so no profile can mutate `system/templates/` (or any other system file) through the gate, for any action: write, append, move, delete (even with `explicit_authorization`, the scope check denies), mkdir, auto_fix. Accidental *human* overwrites of system files are the golden copy's job — drift detection plus `lint:restore`, see [Linter: detectors and auto-fix](linter.md#the-golden-copy).

Globs use doublestar semantics: `**` crosses path segments, `*` stays within one, `?` matches one non-`/` character.

---

## Enforcement: the policy-gate plugin

`check_permission` only decides — the bridge that actually stops a write is the **`memoria-policy-gate` Hermes plugin** (deployed per profile by the installer; it reuses `src/.memoria/mcp/policy_hook.py`'s decision core):

- **`pre_tool_call`** maps the obsidian tool to a policy action, calls the decision core, and blocks on `deny`/`dry_run`; on an allowed write it stashes the `before_hash`. **Fail-closed:** any error inside the gate blocks.
- **`post_tool_call`** computes `after_hash` and appends the paired `write_complete` audit record.

It is a Python plugin, not a shell hook ([ADR-28](../adr/28-write-gate-as-plugin.md)): Hermes registers MCP tools as `mcp_<server>_<tool>`, shell hooks are consent-gated and fail-open — the plugin runs in-process in every mode, matches in Python, receives the `task_id`, and is fail-closed. The hook hard-denies the native `vault_delete`/`vault_move` and `command_execute` (no path to gate), hard-denies direct-world/history tools, allows Hermes `memory` only where the registry grants it, and denies `session_search` everywhere. It also enforces the per-profile tool capability registry before lane path checks; writes then narrow through lane policy.

---

## Related

- The lane ceilings in table form: [Profile capabilities](profiles.md)
- Audit-log substrate and retention: [Memory substrates](memory.md)
- The ceiling check on delegation payloads: [Kanban board reference](kanban-board.md)
- The gated folder map's single source: [Document types](document-types.md)


---

<!-- source: reference/profiles.md -->

# Profile capabilities

The five Memoria profiles ([ADR-48](../adr/48-copi-and-agent-consolidation.md)): posture, board lanes, write scopes, MCP servers, and bundled skills. Every value on this page is read from the shipped sources — the profile packages under `src/.memoria/profiles`, the lane ceilings under `src/.memoria/lane-overrides`, and the per-profile tool allowlist in `src/.memoria/tool-registry.yaml`.

---

## The five profiles

One conversational agent (the Co-PI) plus four background agents, each defined by a posture rather than a tool list:

| Profile | Posture | Role | Invocation | Production default model |
| --- | --- | --- | --- | --- |
| `memoria-copi` | Reflective thinking-partner | The one agent the PI converses with (the Agent Client pane). Reads directly, delegates every write as a board card. Sole carrier of the memory loop. | `interactive_only` — never dispatched to the board | `claude-opus-latest` |
| `memoria-librarian` | Faithful | Finds, ingests, enriches, and draft-classifies evidence. Four processing lanes: catalog · extract · link · map. | `dispatched` | `claude-haiku-latest` |
| `memoria-writer` | Generative | Drafts and synthesizes into project scratch; review-gated. | `dispatched` | `claude-sonnet-latest` |
| `memoria-peer-reviewer` | Adversarial (flag, don't fix) | The independent verify gate: claim, citation, duplicate, and retraction checks. Writes only Inbox cards. | `dispatched` | `claude-opus-latest` |
| `memoria-engineer` | Coordinating | The code lane: writes scoped handoff/provenance notes for an external coding agent under `projects/*/code/`; substantive coding and git stay outside Memoria. | `dispatched` | `claude-haiku-latest` |

These are the `MEMORIA_ENV=prod` defaults rendered by the installer. Linux/WSL test installs may render all five profiles to a local OpenAI-compatible Ollama endpoint with `MEMORIA_ENV=test`; see [Installer environment overlays](installer.md#environment-overlays).

---

## Board lanes

A lane _is_ an `assignee` value on the Hermes board. The task-lane → profile map is enforced by the tasks MCP (`src/.memoria/mcp/tasks_mcp.py`):

| Task lane | Profile |
| --- | --- |
| `catalog` · `extract` · `link` · `map` | `memoria-librarian` |
| `draft` | `memoria-writer` |
| `verify` | `memoria-peer-reviewer` |
| `code` | `memoria-engineer` |

The Co-PI has **no lane** — it converses in the pane and delegates via `delegate_route_task`, which validates every handoff against the receiving lane's ceiling. See [Kanban board reference](kanban-board.md).

---

## Write scopes (lane ceilings)

From `routing.write_scope` and the `policy` block in each lane-override. The policy MCP enforces these per path; a card's `allowed_paths` may narrow but never widen them (lane = ceiling, payload = floor).

| Profile | Write scope | Explicitly denied |
| --- | --- | --- |
| `memoria-copi` | `[]` — **no write paths at all** (`deny.write: "**"`) | everything |
| `memoria-librarian` | `inbox/` · `catalog/` · `notes/fleeting/` · `notes/sources/` | `notes/claims/**` · `notes/hubs/**` · `projects/**` · `system/**` |
| `memoria-writer` | `projects/` | `notes/claims/**` · `notes/hubs/**` · `catalog/**` · `inbox/**` · `system/**` |
| `memoria-peer-reviewer` | `inbox/` (flag / gap cards only) | `notes/**` · `catalog/**` · `projects/**` · `system/**` |
| `memoria-engineer` | `projects/*/code/` | `notes/**` · `catalog/**` · `inbox/**` · `system/**` |

All five profile policy overrides require `audit_log`; the dispatched four also require `timeout_required`, and the Librarian and Peer-reviewer additionally require `source_tracking`. `routing.external_api_policy` is `explicit_only` everywhere except the Writer (`blocked` — it composes from the vault, never researches).

---

## MCP servers per profile

From each profile's `config.yaml` (`mcp_servers` — the only place Hermes loads servers from, per [ADR-27](../adr/27-hermes-native-config-and-gate-enforcement.md)). The `policy` and `obsidian` servers are universal; the rest follow the lane's job:

| Server | copi | librarian | writer | peer-reviewer | engineer |
| --- | --- | --- | --- | --- | --- |
| `policy` (the write gate) | ✓ | ✓ | ✓ | ✓ | ✓ |
| `obsidian` (Local REST API native MCP, verified loopback HTTPS) | ✓ (reads only, by lane) | ✓ | ✓ | ✓ | ✓ |
| `ingest` (the deterministic pipeline) | ✓ (read/compute) | ✓ | — | — | — |
| `cluster` (typed graph + topics, read-only) | ✓ | ✓ | — | — | — |
| `tasks` (`delegate_route_task`) | ✓ | — | — | — | — |
| `patterns` (the pattern runner) | ✓ | ✓ | — | — | — |
| `paper_search` (scholarly discovery, 20+ databases) | — | ✓ | — | — | — |
| `pyzotero` (read-only Zotero 7 local API) | — | ✓ | — | ✓ | — |
| `qmd` (filtered local hybrid search over the vault corpus, read-only) | ✓ | ✓ | ✓ | ✓ | — |

The `web` toolset is disabled on every lane — all external lookups go through MCP servers (gated, audited, deterministic). The write gate itself is the `memoria-policy-gate` Hermes plugin, enabled per profile and fail-closed; see [Policy MCP](policy-mcp.md).

---

## Bundled skills

**27 skills** ship inside the vault profiles, under `src/.memoria/profiles/<profile>/skills/`. Lane skills use a single kebab-case name, `<task>-<verb>-<object>` (e.g. `catalog-enrich-record`, in `skills/catalog-enrich-record/`) — the same spelling in prose, on disk, and at load. Co-PI conversational skills that are not lane work use bare names such as `route-task` and `explain-system`.

| Profile | Bundled-skill count |
| --- | --- |
| `memoria-copi` | 5 |
| `memoria-librarian` | 14 |
| `memoria-writer` | 4 |
| `memoria-peer-reviewer` | 4 |
| `memoria-engineer` | 0 — the code lane scaffolds an external-agent handoff |

For the full per-skill map (names and lanes) see the [Hermes CLI](hermes-cli.md) reference.

---

## Capability allowlist

`src/.memoria/tool-registry.yaml` is the authoritative per-profile **tool** allowlist (default-deny). Two layers, deliberately separate: the registry governs _which tools_ a profile may invoke; the lane-override governs _which paths_ those tools may write. Notably:

- `memoria-copi` is the only profile granted `memory` (the self-improving loop — see [Memory substrates](memory.md)) and `tasks`; it is the only one **withheld** `vault_write`.
- No profile is granted `session_search`; session history is not a lane recall substrate for alpha.10.
- **No** profile is granted a direct-world toolset (`terminal`, `file`, `code_execution`, `browser`, `web`, `computer_use`) — every agent reaches the vault, operations, and APIs only through MCP ([ADR-21](../adr/21-l3-autonomy-ceiling.md), [ADR-48](../adr/48-copi-and-agent-consolidation.md)); enforced by `test_no_profile_has_direct_world_access`.

Enforcement is split deliberately:

| Contract | Runtime status | Drift check |
| --- | --- | --- |
| Direct-world toolsets are absent from shipped profile config | Enforced by rendered Hermes `platform_toolsets`, with disabled toolsets as a backstop | `tests/test_profiles.py` |
| Direct ACP fallback tools cannot bypass profile shaping | Enforced by the `memoria-policy-gate`; `memory` is granted only to Co-PI by the registry and `session_search` is denied everywhere | `tests/test_policy_gate_completeness.py` |
| Obsidian write tools obey lane path scopes | Enforced at runtime by the fail-closed `memoria-policy-gate` plugin | Policy and lane-scope tests |
| Registry allowlist matches profile skill metadata and profile config | Checked as a source-of-truth contract | `tests/test_profiles.py` |
| General tool-call gating from `tool-registry.yaml` inside the policy hook | Enforced by the fail-closed `memoria-policy-gate` plugin before lane path checks | Policy gate and profile tests |

---

## Related

- The write-gate decisions and lane-override shape: [Policy MCP](policy-mcp.md)
- The board the lanes pull from: [Kanban board reference](kanban-board.md)
- The CLI surface per profile: [Hermes CLI](hermes-cli.md)
- Where profiles live on disk: [On-disk layout](on-disk-layout.md)


---

<!-- source: reference/project-structural-impact.md -->

# Project structural impact

`src/.memoria/operations/processing/project/structural_impact.py` computes the thesis-rooted argument graph for one Project and writes a generated Project gate index note. It is deterministic operation code, not a Hermes chat skill.

## Command

```bash
python src/.memoria/operations/processing/project/structural_impact.py --vault <vault> --project <project-slug>
python src/.memoria/operations/processing/project/structural_impact.py --vault <vault> --project <project-slug> --dry-run --json
```

| Option | Contract |
| --- | --- |
| `--vault <vault>` | Runtime vault root. Defaults to the current directory when omitted. |
| `--project <project-slug>` | Project selector. When empty, the operation resolves the active project from the vault scan. |
| `--dry-run` | Computes the payload without writing the generated note. |
| `--json` | Prints the full result payload instead of only `updated:` / `unchanged:` and the output path. |

## Inputs

The operation scans markdown notes, resolves the selected Project and active Thesis, then follows authored `links.supports` and `links.contradicts` relationships. Scope terms and relation values come from the same note frontmatter fields documented in [Frontmatter fields](frontmatter.md).

## Output note

The generated note is written next to the Project note as `project-gate-index.md`. Its frontmatter includes:

| Field | Meaning |
| --- | --- |
| `generated_by` | Always `memoria-structural-impact`. |
| `project` | Resolved Project path/identifier. |
| `active_thesis` | Thesis at the root of the argument graph. |
| `computed_at` | UTC timestamp for the last material payload change. |
| `stale` | Whether the generated analysis is stale relative to available project evidence. |
| `argument_stage` | Derived project argument maturity stage. |
| `evidence_saturation` | Derived saturation value for the scoped argument graph. |
| `displayed_confidence` | Confidence value shown to the PI. |
| `relation_count` | Count of graph relations considered. |
| `open_high_impact_gaps` | Count of open high-impact gaps. |
| `gap_findings` | Count of confident gap findings. |
| `advisories` | Count of advisory findings. |

The body contains three tables: graph nodes, gap findings, and advisories. It also embeds the full machine payload between `<!-- memoria-structural-impact:json -->` and `<!-- /memoria-structural-impact:json -->` markers.

## Write behavior

The renderer compares the new payload to the previous embedded JSON after removing `computed_at`. If the stable payload is unchanged, the note is not rewritten and the prior `computed_at` is preserved. If the stable payload changes and `--dry-run` is not set, the operation rewrites the generated note.

## Gap taxonomy

The payload separates confident gap kinds from advisory gap kinds. Confident gaps are counted in `gap_findings`; advisory gaps are shown separately so dashboards can surface them without treating them as blocking structural defects.

## Related

- Project workflow guide: [Start a writing project](../how-to-guides/project/start-a-writing-project.md)
- Project fields: [Frontmatter fields](frontmatter.md)
- Operation inventory: [Operations](operations.md)


---

<!-- source: reference/sample-vault.md -->

# The sample vault

A small, labeled starter corpus the tutorials load so you can reach the *Produce* payoff in one sitting instead of after weeks of reading. Its topic is neutral and broadly legible: **adherence to a Mediterranean diet and cardiovascular health**.

It ships inside the installed vault as a hidden bundle at `.memoria/samples/mediterranean-diet/` and becomes live `catalog/` and `notes/` only when you load it. To **load or remove** it, see [Load and remove the sample vault](../how-to-guides/setup/sample-vault.md); **why** it is shaped this way — seeded, half-built, provenance-bound — is recorded in [ADR-112](../adr/112-tutorial-destination-first-arc.md).

## What is in it

| Layer | Worked (study these) | Half-built (left for you to finish) |
| --- | --- | --- |
| Sources | 6 source notes, written "in my words" with claims distilled | 2 sources captured but not yet distilled |
| Claims | 11 connected claims with typed `supports` / `contradicts` links | 2 claim stubs (evidence blank) and 1 deliberately unmade link |
| Catalog | 8 catalog entities, one per cited paper | — |
| Hub | 1 hub organizing the cluster and naming an open gap | — |

Every note is labeled `sample: true`, which keeps it visibly separate from your own work and lets a single command archive the whole sample later.

Everything traces to a **real, citable paper** (PREDIMED, the Lyon Diet Heart Study, the Seven Countries Study, a Greek cohort, and two reviews). Nothing is fabricated or model-generated: the whole point of Memoria is that every claim traces to a source, so a sample that faked its provenance would teach the exact habit the system exists to prevent.

## The shape to notice

The cluster is not all agreement. It deliberately holds a **tension** — the strong causal reading of the trial evidence sits against the observational caution that diet effects may be confounded by overall healthy lifestyle — and the hub names a **gap** the corpus does not yet cover: primary prevention in low-risk people, and whether the benefit transports beyond Mediterranean populations. The tutorials have you read that tension and gap on the coverage map, and later turn the gap back into discovery — one full turn of the loop.

The **half-built pieces** — the un-distilled sources, the claim stubs, the unmade link — are deliberate. Finishing them is how the tutorials teach the distill-and-connect move on a worked example before you do it on your own material; the completions stay `sample: true`, so they archive with the sample when you remove it, while the claims you distill from your own sources do not.


---

<!-- source: reference/search.md -->

# Search

The vault's retrieval surface: `qmd`, a local hybrid search index, and the read-only MCP the agents query through it. Every other I/O surface has a reference home — this is search's. For *why* hybrid retrieval pairs with the typed graph, see the consumer profiles ([The Co-PI](../explanation/profiles/co-pi.md)); to rebuild a stale index, see [Rebuild the search index](../how-to-guides/operate/rebuild-the-search-index.md); to query conversationally, see [Query the vault](../how-to-guides/knowledge/query-the-vault.md).

`qmd` is an external tool (the `qmd` package), not a vault database. The profiles
reach it through Memoria's `qmd_filter_mcp.py` wrapper, which preserves the qmd
tool surface and adds one vault rule from [ADR-10](../adr/10-claim-supersession.md):
claim notes with a non-empty `superseded_by` relation are excluded from ordinary
retrieval unless the caller explicitly asks for historical results. The qmd CLI
still exists for operator debugging and raw index checks. The clustering surface
that consumes the *typed graph* (not text similarity) is documented separately in
[Clustering](clustering.md).

---

## The retrieval surface

Memoria runs a stdio MCP named `qmd` beside the obsidian native MCP, exposing
read-only hybrid search over the vault corpus through the filtered wrapper. It is
wired into the four reading-active profiles — **Librarian, Writer, Co-PI,
Peer-reviewer** — and the `ask-*` / `explore-*` skills use it for semantic reads.

| Property | Value |
| --- | --- |
| Backend | `qmd`, local; no network call leaves the machine |
| Mode | Stdio MCP wrapper (`qmd_filter_mcp.py` over `qmd`); raw CLI (`qmd …`) for operators |
| Access | **Read-only** — `qmd` never writes the vault |
| Cold start | Models load on the first search (~19s cold) and stay warm for the session |
| Profiles | Librarian, Writer, Co-PI, Peer-reviewer |

The qmd executable is resolved to an absolute path at deploy (`{{QMD}}`) because
a conda package also ships a `qmd` binary and bare `PATH` is ambiguous.

For explicit historical lookup, the MCP tools accept `include_superseded: true`.
The default remains current-claim retrieval: superseded claim notes are hidden,
but source notes, project notes, and non-superseded claims remain visible.

---

## Hybrid ranking

A query is scored by three combined signals, which is why results survive both vocabulary mismatch and exact-term queries:

| Signal | Catches |
| --- | --- |
| **BM25** (lexical) | Exact terms, citekeys, rare tokens a vector model blurs. |
| **Vector** (embedding) | Semantic matches — paraphrases and near-synonyms with no shared words. |
| **Rerank** | A cross-encoder pass that re-orders the merged candidates for final precision. |

Found-by-keyword-but-not-by-meaning (or the reverse) is the diagnostic that distinguishes a stale vector index from a genuine miss — the breakdown is in [Rebuild the search index](../how-to-guides/operate/rebuild-the-search-index.md).

---

## Consumers

`qmd` is shared infrastructure; several surfaces query the same index rather than maintaining their own.

| Consumer | Uses search for |
| --- | --- |
| Co-PI vault answers | The grounded retrieval behind a conversational question ([Query the vault](../how-to-guides/knowledge/query-the-vault.md)). |
| Librarian map lane | `map-cluster-corpus`, `map-report-coverage`, `map-scope-project`, `map-graph-claims`, and `map-canvas-hub` use qmd to narrow the corpus before graph, topic, and canvas work. Scope/gap reports may carry a companion exploration trace under `notes/fleeting/maps/` for rejected directions and dead ends. |
| Librarian comparative pulls | The `[!brief]` comparative read at ingest and catalog enrichment. |
| Writer and Peer-reviewer | Draft binding, claim tracing, citation checks, and duplicate/citation sub-checks pull candidate evidence without writing through qmd. |
| QuickAdd pre-file shadow | `create-linked-claim` and `structured-source-capture` run a report-only top-3 neighbour check before filing claim/source notes. |

---

## The index

The index lives **inside the vault** and is gitignored — never commit it. It is built once and maintained incrementally in normal operation:

```bash
cd <vault>
qmd collection add <vault> --name vault   # one-time: register the collection
qmd embed                                  # build / fully rebuild the index
```

A full `qmd embed` re-embeds every note (roughly 1–5 min under 500 notes, up to 15–30 min past 2000). The installer wires **no** qmd cron — embedding is incremental during normal use, and a full rebuild is the manual fix when results go stale. The when-and-how of rebuilding is owned by [Rebuild the search index](../how-to-guides/operate/rebuild-the-search-index.md).

---

## CLI

| Command | Does |
| --- | --- |
| `qmd search "<term>"` | One-shot query — the fastest way to confirm whether the index, not the agent, is the problem. |
| `qmd embed` | Full re-embed of every note. |
| `qmd collection add <vault> --name vault` | One-time collection registration. |
| `qmd mcp` | Raw serve mode. Memoria profiles use `qmd_filter_mcp.py` instead so ADR-10 filtering applies. |

---

## Limits

- **Read-only and local.** Search never mutates the vault and never calls out to a network service; it cannot be the cause of a denied write or a leaked note.
- **Current by default.** Superseded claim notes are hidden from agent retrieval
  unless a caller explicitly requests historical results. Raw CLI checks may show
  them because the CLI bypasses the Memoria wrapper.
- **Index can lag.** A new note isn't searchable until it's embedded; staleness is silent and surfaces as "the Co-PI misses notes I know exist" — the dominant search failure mode ([Failure modes](failure-modes.md)).
- **Pre-file similarity is shadow-only.** QuickAdd surfaces neighbours in a `[!similarity]` callout and logs `pre-file-similarity.jsonl`, but it never blocks filing, auto-merges notes, or uses a calibrated threshold. qmd failures become warnings, not write failures.
- **No standalone duplicate sweep ships today.** Retrospective duplicate detection is still skill/sub-check work, not a `sweep:find-duplicates` command. The shipped creation-time surface is the QuickAdd shadow report above.
- **Text, not graph.** `qmd` ranks by text similarity. Relationship-aware retrieval (`supports` / `contradicts` edges, communities, centrality) is the typed-graph surface in [Clustering](clustering.md), not here.

---

## Related

- Rebuilding a stale index: [Rebuild the search index](../how-to-guides/operate/rebuild-the-search-index.md)
- Querying conversationally: [Query the vault](../how-to-guides/knowledge/query-the-vault.md)
- Where qmd sits among external tools: [External integrations](integrations.md)
- The typed-graph counterpart: [Clustering](clustering.md)
- The deterministic and hybrid methods catalog: [Retrieval and analysis methods](computational-toolbox.md)


---

<!-- source: reference/sweeps.md -->

# Sweeps

Deterministic maintenance passes under `src/.memoria/operations`. Re-ingest and retraction sweeps surface review work through the board or Inbox; the inbox archival sweep is a deterministic direct write that only flips eligible resolved cards to `lifecycle: archived`.

## Re-ingest backstops

`reconcile.py` finds ingest work that started but did not land cleanly. Re-ingest must be board-serialized, so each backstop enqueues an idempotent re-ingest card with `hermes kanban create --idempotency-key reingest:<citekey>`; the board provides deduplication, backoff, and the failure circuit-breaker.

| Pass | Detects |
| --- | --- |
| `--reconcile` | A capture logged in `capture-intake.jsonl` with no note on disk. |
| `--retry` | A captured note stuck at `ingest_status: tier0`. |

`--dry-run` reports without touching the board. The installer wires these re-ingest passes into the `memoria-sweeps` cron every 15 minutes.

## Inbox archival sweep

`archive_inbox.py` is the direct-write cleanup pass in the same cron wrapper. It archives handled Inbox cards after the freshness window expires:

```bash
python src/.memoria/operations/cleanup/archive_inbox.py --vault <vault>
python src/.memoria/operations/cleanup/archive_inbox.py --vault <vault> --dry-run
```

The retention window comes from `.memoria/schemas/calibration.yaml` at `inbox.archive_after_days`; when the value cannot be read, the operation warns once and uses the default of `30` days. `--days <n>` overrides calibration for a single run.

The sweep scans `inbox/**/*.md` and rewrites only the top-level `lifecycle:` line when all conditions are true: the card is in a resolved-but-visible lifecycle (`current`), it has a parseable `resolved:` date, and that date is older than the cutoff. It never touches `proposed` cards, cards without `resolved:`, already archived cards, or malformed frontmatter. The file stays in place; no body text or other frontmatter fields are rewritten.

Because the operation is idempotent and single-line, it is exempt from board serialization. `--dry-run` returns the same JSON report shape without writing.

## Retraction sweep

`retraction.py` performs deterministic, read-only retraction-by-DOI checks from three sources, most authoritative first:

| Source | Role |
| --- | --- |
| Local Retraction Watch CSV | Primary source; `--refresh` downloads it to `.memoria/data/retraction_watch.csv`, refreshed monthly by cron. |
| Crossref `update-to` delta | Live DOI status check. |
| Open Retractions | Cross-check source. |

`retraction.py --sweep --vault V` scans the Catalog DOIs and raises Inbox `alert` cards on hits. It never flips a note lifecycle.

## Related

- The ingest stage that creates the source records these sweeps monitor: [Ingest routing](ingest.md)
- The cron wiring for installed vaults: [Installer (bootstrap)](installer.md)
- The alert-card fields: [Inbox card fields](inbox-card-fields.md)


---

<!-- source: reference/system-actions.md -->

# System actions

Every action the system can perform, with its performer. Three performer kinds: **deterministic operations** (zero-LLM Python, report-only or idempotent), **agents** (LLM lanes acting through gated MCP tools and skills), and the **PI** (palette actions and review decisions). Where a topic has its own reference page, that page is authoritative for the details — this catalog is the map.

## Deterministic operations

### Ingest pipeline (`operations/processing/ingest/`)

| Action | Performer | What it does |
| --- | --- | --- |
| Tier-0 capture | ingest operation (`ingest_paper.py`) | Extracts citekey identity and frontmatter from local BibTeX — no network. |
| Tier-0 routing | ingest operation (`ingest_paper.py`) | Routes the entry type (article / book / software / dataset) to its catalog home and document type ([Ingest routing](ingest.md)). |
| Resolve | ingest operation (`resolve_merge.py`) | Queries Semantic Scholar, OpenAlex, Crossref, and PubMed/NCBI to resolve identity, authors, citations, biomedical identifiers, and enrichment metadata. |
| Merge | ingest operation (`resolve_merge.py`) | Merges per-field best-source-wins across the four sources with provenance, and scores identity disagreement. |
| Classify | ingest operation (`classify.py`) | Proposes `research_area` / `methodology` from OpenAlex topics, with a confidence floor and near-tie flagging; audited to `system/logs/classify.jsonl`. |
| Project-hints proposal | ingest operation (`classify.py`) | Scores topic overlap against `.memoria/project-hints.yaml` and proposes `projects` membership for human confirmation ([ADR-15](../adr/15-project-membership-from-topic-hint.md)). |
| Extract | ingest operation (`extract.py`) | Pulls full text — Unpaywall OA PDF first, then PMC JATS, then the local PDF via sandboxed pymupdf4llm — behind a deterministic coherence gate; marks `degraded` otherwise. |
| Link entities | ingest operation (`link.py`) | Plans idempotent find-or-create venue / person / organization entities from merged metadata. |
| Link citations | ingest operation (`link.py`) | Plans cited-by / cites edges by matching the reference union against the vault by DOI / arXiv id. |

### Linter (`operations/integrity/linter/`)

The seventeen registered detectors (slugs, severities, and what each catches) live in [Linter: detectors and auto-fix](linter.md#the-detectors); every detector is report-only.

| Action | Performer | What it does |
| --- | --- | --- |
| Run detectors | Linter (`detectors.py`, daily cron) | Runs all seventeen structural detectors over the vault; findings surface on the drift dashboards. |
| Pre-commit hook | Linter (`precommit_check.py`, git hook) | Schema-validates staged notes and blocks the commit on a violation — the one check that prevents rather than reports. |
| Golden stage | Linter (`golden_restore.py stage`) | Snapshots every system file (templates, dashboards, patterns, eval set, scripts, shipped Obsidian config) into a SHA-256 manifest. |
| Golden check | Linter (`golden_restore.py check`, daily cron) | Reports system files that drifted from or went missing against the golden manifest. |
| Golden restore | Linter (`golden_restore.py restore`) | Lists what restoring would change; writes the golden bytes back only with `--apply` (a PI decision). |
| Session digests | Linter (`session_summary.py`, daily cron) | Writes one deterministic per-session digest file under `system/logs/sessions/` from the audit log ([ADR-25](../adr/25-session-logging-two-logs.md)). |
| Hub proposal handoff | Linter (`hub_handoff.py`, PI-run) | Converts current `hub-threshold` findings into idempotent Librarian `map` cards that stage proposals under `notes/fleeting/maps/` and `inbox/`; `notes/hubs/` stays PI-approved. |

### Sweeps (`operations/`)

| Action | Performer | What it does |
| --- | --- | --- |
| Reconcile | sweeps operation (`reconcile.py`) | Finds capture-intake anchors with no note on disk and enqueues idempotent re-ingest cards. |
| Retry tier-0 | sweeps operation (`reconcile.py`) | Finds notes stuck at `ingest_status: tier0` and enqueues idempotent re-ingest cards. |
| Archive inbox | sweeps operation (`archive_inbox.py`) | Flips accepted inbox cards (`lifecycle: current` with a `resolved:` stamp older than `inbox.archive_after_days`, default 30) to `lifecycle: archived` so the inbox converges to empty. |
| Eval dispatch | sweeps operation (`eval_dispatch.py`, quarterly cron) | Fans the gold set out as one idempotent kanban card per task, routed to the owning lane ([Vault eval](vault-eval.md)). |
| Eval score | sweeps operation (`eval_score.py`, quarterly cron) | Computes recall@k / support-rate / FAMA-clean from the result blocks reported on eval cards; appends to `system/metrics/eval/runs.jsonl`. |
| Retraction check | sweeps operation (`retraction.py`) | Checks a DOI against the Retraction Watch dataset, Crossref, and Open Retractions (read-only). |
| Retraction sweep | sweeps operation (`retraction.py`) | Scans the catalog's DOIs for retractions and hands findings to the agent to flag. |
| Emit worklist | shared operation helper (`worklists.py`) | Converts a scan/search report into file-backed `worklist-item` rows and one aggregate Inbox `work-prompt`. |

## Vault-side MCP servers and hooks (`.memoria/mcp/`)

| Action | Performer | What it does |
| --- | --- | --- |
| Policy decision | [Policy MCP](policy-mcp.md) (`policy_mcp.py`) | Decides allow / allow_with_log / deny / dry_run for every vault action against the lane's ceiling; fail-closed. |
| Pre-tool gate | policy hook (`policy_hook.py`) | Blocks denied or gated writes before the tool runs and stashes the file's `before_hash`. |
| Post-tool pairing | policy hook (`policy_hook.py`) | Computes the `after_hash` and appends the paired reversibility record to `system/logs/audit.jsonl`. |
| Run ingest pipeline | ingest MCP (`ingest_mcp.py`), Librarian-facing | Runs the full deterministic Tier-0/1 ingest for a citekey and returns the draft bundle with its two LLM holes (classification + brief). |
| Persist extract | ingest MCP (`ingest_mcp.py`) | Stores the full-text extract under `.memoria/data/extracts/`, outside the agent write lane. |
| Append intake anchor | ingest MCP (`ingest_mcp.py`) | Appends the durability anchor to `system/logs/capture-intake.jsonl` that the reconcile sweep recovers from. |
| Build cluster graph | cluster MCP (`cluster_mcp.py`), Librarian-facing | Builds the typed knowledge graph from authored links and computes communities and centrality. |
| Emit canvas | cluster MCP (`cluster_mcp.py`) | Renders the claim-debate map as a JSON Canvas with maturity-colored nodes and typed edges. |
| Model topics | cluster MCP (`cluster_mcp.py`) | Runs BERTopic over the corpus to extract topics, the doc-topic map, and outliers. |
| List / run patterns | patterns MCP (`patterns_mcp.py`) | Lists runnable patterns from `system/patterns/` and composes a pattern run (refusing gated-zone output targets), logging provenance. |
| Route task | tasks MCP (`tasks_mcp.py`), Co-PI-facing | Validates a delegation against the target lane's ceiling, refuses dispatch while an open `loudness: block` card exists, and creates the kanban card. |
| Loudness routing | shared operation helper (`operations/lib/loudness.py`) | Sends/logs alert/block push attempts, keeps quiet/notice pull-only, and exposes open block cards to delegation and policy gates. |
| Board export | board export (`board_export.py`, 60 s cron) | Projects kanban cards into `system/board/` and appends board-state, transition, cost, and blind-review telemetry; review disposition is emitted by QuickAdd when the human resolves a work prompt. |
| Metrics aggregate | metrics aggregator (`metrics_aggregate.py`, weekly cron) | Rolls audit + board + lint signals into per-lane trust-score notes under `system/metrics/`. |

## External MCP servers (declared per profile)

| Action | Performer | What it does |
| --- | --- | --- |
| Vault read / gated write | obsidian native MCP (all lanes) | File reads, search, and writes into the vault over the Local REST API plugin's MCP — every write passing the policy gate. |
| Vault search | filtered qmd MCP (Librarian, Writer, Co-PI, Peer-reviewer) | Hybrid BM25 + vector + rerank search over the vault corpus, local and read-only; superseded claim notes are hidden unless historical lookup is explicit. |
| Literature discovery | paper_search MCP (Librarian) | Searches arXiv, PubMed, Semantic Scholar, Google Scholar, and bioRxiv (Unpaywall email for OA lookups). |
| Zotero reads | pyzotero MCP (Librarian, Peer-reviewer) | Read-only citekey resolution, metadata, and citation context from the local Zotero library — no write-back. |

## Scheduled crons (`.memoria/scripts/`)

The deterministic cron jobs (board export, sweeps, lint, metrics, retraction refresh, eval) and their schedules are owned by [Installer (bootstrap)](installer.md#the-crons-it-wires). They run from the repo source wrappers under `.memoria/scripts/`: the installer copies each `<job>-cron.sh` to `~/.hermes/scripts/` renamed **`memoria-<job>.sh`** — that `memoria-*` form is the cron-job name `hermes cron list` shows.

## Agent skills (per lane)

### Librarian (14)

| Skill | What it does |
| --- | --- |
| catalog-find-source | Searches the literature via paper_search, screens against the vault, raises honesty-bodied candidate cards. |
| catalog-rank-candidate | Ranks candidate sources by relevance / novelty / venue into a batch worklist. |
| catalog-classify-source | Proposes `research_area` / `methodology` from the vocabulary for human promotion at triage. |
| catalog-enrich-record | Runs the ingest pipeline MCP, fills the classification and `[!brief]` holes, applies the gated writes. |
| extract-flag-distill | Flags kept sources worth reading and raises a distill work-prompt. |
| extract-stub-claim | Proposes one-sentence, citekey-bound claim stubs in a source's "Worth distilling" section. |
| link-suggest-claim | Proposes typed links (supports / contradicts / extends) as one candidate card with quoted evidence. |
| link-surface-tension | Surfaces claim-pair contradictions with both sides quoted and reconciliation options. |
| map-cluster-corpus | Clusters topics via the cluster MCP and emits a map note plus a report card. |
| map-report-coverage | Topic-models the corpus and composes a gap report of thin topics; records rejected directions/dead ends as a companion exploration-trace note when present. |
| map-scope-project | Corpus-maps a project into a narrative map with thin spots named; records rejected directions/dead ends as a companion exploration-trace note when present. |
| map-seed-canvas | Seeds a JSON Canvas from the cluster graph (communities, edges, layout). |
| map-graph-claims | Emits a propose-class claim-debate JSON Canvas from authored `supports` / `contradicts` / `extends` links, with pruning disclosed in a companion note. |
| map-canvas-hub | Assembles existing maps, claim graphs, project gates, and dashboards into a propose-class JSON Canvas hub for navigation. |

### Writer (4)

| Skill | What it does |
| --- | --- |
| draft-outline-argument | Produces 2–3 outline options for an argument, each with a counter-outline. |
| draft-score-outline | Scores an outline against coverage / maturity / contradictions / holes (advisory). |
| draft-write-section | Drafts a prose section with every fact bound to a citekey, marking holes. |
| draft-bind-citation | Binds every factual sentence to a citekey and normalizes citations against the bibliography. |

### Peer-reviewer (4)

| Skill | What it does |
| --- | --- |
| verify-trace-claim | Traces a draft's factual claims to supporting notes (link → citekey → similarity) and flags failures. |
| verify-check-citation | Checks every `[@citekey]` resolves and that the source supports the claim. |
| verify-card-gap | Converts missing-evidence findings into gap cards in `inbox/`. |
| verify-propose-fix | Proposes the obvious remedy for a finding as a candidate card — flag, don't fix. |

### Co-PI (5)

| Skill | What it does |
| --- | --- |
| ask-question-source | Answers questions about a source from vault holdings, read-only. |
| ask-read-lens | Re-reads a source through a named lens (frame / checklist / hypothesis), read-only. |
| explore-framings | Branches a question into rival framings — the sparring partner. |
| route-task | Routes work to the right lane via the tasks MCP with a composed handoff payload. |
| explain-system | Teaches how Memoria works, pointing at concrete affordances. |

## PI actions

### Palette (QuickAdd scripts, `system/scripts/`)

| Action | What it does |
| --- | --- |
| Capture fleeting | Creates a proposed fleeting note in `notes/fleeting/` from the bundled template. |
| Capture from Zotero | Reads the current Zotero selection (Better BibTeX JSON-RPC), writes the intake anchor, materializes a Tier-0 `catalog/papers/<citekey>.md` stub, and creates an `intake:source` card. |
| Capture source from URL | Prompts for a URL and creates an `intake:source` card on the Librarian lane. |
| Structured source capture | Opens the guided Modal Forms capture; writes a proposed `notes/sources/` note plus an Inbox candidate, with pre-file similarity reported but never blocking. |
| Write claim note | Creates a human-authored claim note in `notes/claims/` from the bundled claim template. |
| Create linked claim note | Starts from the active source note, creates a claim note with the source citekey prefilled, links it back under **Worth distilling**, and opens it for editing. |
| Catalog a source | Prompts for a citekey / URL and creates a catalog-lane card. |
| Extract claims | Sends the active (or chosen) source to the extract lane. |
| Link a claim | Sends the active (or chosen) claim to the link lane. |
| Map the corpus | Prompts for an optional scope and creates a map-lane card. |
| Record exploration trace | Captures a rejected direction/dead end beside a map or gap report under `notes/fleeting/maps/`; it stays project-local and is never canonical knowledge. |
| Draft a section | Prompts for a goal and creates a draft-lane card. |
| Verify a draft | Sends the active (or chosen) draft to the verify lane. |
| Delegate a task | Prompts for a lane and goal — the palette twin of the Co-PI's routing skill. |
| Assist commands | `assist find/search/patterns/ask/draft/explore` start the same task or conversation shape with active-note and selection context attached. |
| Run a pattern | Suggester over runnable patterns; creates the card that invokes the patterns MCP. |
| Resolve inbox card | Flips the active inbox card's `lifecycle` to a schema-valid outcome (`current` or `archived`) and stamps `resolved:`. |
| Start project | Scaffolds `projects/<slug>/`, creates the initial active thesis, and opens the project gate index for triage. |
| Refresh project gate | Rebuilds the project gate index from current thesis, links, saturation signals, and open risks. |
| Supersede thesis | Creates a replacement thesis, marks the old one superseded, updates the project `active_thesis`, and raises an Inbox alert for re-confirmation. |
| Open a space | Opens `spaces/inbox.md`, `spaces/library.md`, `spaces/knowledge.md`, or `spaces/project.md` from the left-pane navigator rail (**Now** / **Places**). |

### Review decisions

| Action | What it does |
| --- | --- |
| Review-gated approval | Every write to `notes/claims/` and `notes/hubs/` is a proposal until the PI approves it — the agents cannot land it alone. |
| Inbox triage | Accept / edit / reject candidate and flag cards; dispositions are logged for the trust metrics. |
| Golden restore `--apply` | The PI (not the cron) decides to write golden bytes back over drifted system files. |


---

<!-- source: reference/system-artifacts.md -->

# System artifacts

Visible system artifacts live under `system/` in the runtime vault. They are not hidden `.memoria/` internals; the PI can inspect them from Obsidian.

| Runtime path | What it is | Reference |
| --- | --- | --- |
| `system/vocabulary.md` | Controlled vocabulary for `research_area`, `methodology`, and claim `topics`. | [Vocabulary](vocabulary.md) |
| `system/eval/` | Gold-task fixtures for vault-eval dispatch and scoring. | [Vault eval](vault-eval.md) |
| `system/dashboards/*.base` | Bases views for sources, claims, and fleeting notes. | [Dashboards](dashboards.md) |
| `system/board/board.base` | Bases view over exported Hermes worker cards. | [Kanban board reference](kanban-board.md) |
| `system/patterns/patterns.base` | Bases view over runnable patterns. | [System actions](system-actions.md) |
| `system/worklists/worklists.base` | Bases view over batch screening rows; the Inbox points here with one aggregate work-prompt per batch. | [Dashboards](dashboards.md) |
| `catalog/catalog.base` | Catalog-wide Bases view for papers, people, organizations, venues, datasets, and repositories. | [Document types](document-types.md) |
| `inbox/inbox.base` | Inbox card Bases view, including the `Needs me` surface embedded on the Inbox queue. | [Kanban board reference](kanban-board.md) |
| `notes/hubs/hubs.base` | Bases view over hub notes. | [Dashboards](dashboards.md) |
| `projects/projects.base` | Bases view over project notes, including the refutation-stamp gate. | [Dashboards](dashboards.md) |

The source copies are tracked in [`src/system/`](https://github.com/eranroseman/memoria-vault/tree/main/src/system), [`src/catalog/catalog.base`](https://github.com/eranroseman/memoria-vault/blob/main/src/catalog/catalog.base), and [`src/inbox/inbox.base`](https://github.com/eranroseman/memoria-vault/blob/main/src/inbox/inbox.base). The installer copies them into the runtime vault and stages a golden copy for drift detection.


---

<!-- source: reference/telemetry-logs.md -->

# Telemetry log schemas

Exact JSONL schemas for Memoria operational logs. For the inventory, conventions, and capture posture, see [Telemetry & logs](telemetry.md).

## audit.jsonl

The write-gate's decision trail. Its full schema — the field table, the JSON example, the `decision` enum, and the per-write SHA-256 hash-pairing rules — is owned by [Policy audit log](policy-audit-log.md).

Every gated decision is logged when the lane requires `audit_log` (all shipped Memoria lanes do), and `allow_with_log` / `deny` / `dry_run` are logged unconditionally. So for the shipped lanes every decision — `allow`, `allow_with_log`, `deny`, and `dry_run` — appends a row. Only a plain `allow` on a lane that does *not* require `audit_log` would write nothing.

Every row is stamped with `schema_version: 2` and `review_mode: "blocking"`. The latter is deliberately non-backfillable: it records the live review-gate arm for future blocking-vs-advisory studies while keeping production behavior blocking-only.

## board-state.jsonl

A queue-depth snapshot appended once per `board_export.py` run. Counts only — no card identity — so it is safe to keep forever and cheap to plot as a time series.

```json
{
  "timestamp": "2026-06-01T09:00:00Z",
  "lanes": {
    "memoria-writer":    {"running": 1, "ready": 0, "blocked": 1, "review_queue": 2, "retrying": 0},
    "memoria-librarian": {"running": 0, "ready": 3, "blocked": 0, "review_queue": 0, "retrying": 1}
  },
  "totals": {"running": 1, "ready": 3, "blocked": 1, "review_queue": 2, "retrying": 1}
}
```

`review_queue` counts cards that are `status: done` **and** sitting in a non-terminal `review_status` (awaiting a human). `retrying` counts cards in `ready` with `retry_count > 0`. A card is counted in exactly one of `running` / `ready` / `blocked`; `review_queue` and `retrying` are overlays for board diagnostics, not separate card states.

## board-transitions.jsonl

The card-level state-change stream — the spine the other event logs hang off. Emitted by diffing the previous per-card state (held in `system/logs/.board-state-cache.json`, an internal dotfile, not a telemetry log) against the current board. **A card seen for the first time emits no transition** — it is seeded into the cache silently, so the log records only genuine movements, never the initial population.

```json
{"timestamp": "2026-06-01T09:00:00Z", "task_id": "TASK-2026-05-31-003", "lane": "memoria-writer", "kind": "status", "from": "running", "to": "done"}
{"timestamp": "2026-06-01T11:30:00Z", "task_id": "TASK-2026-05-31-003", "lane": "memoria-writer", "kind": "review", "from": "requested", "to": "approved"}
```

| Field | Values |
| --- | --- |
| `kind` | `status` or `review` — which axis moved |
| `from` / `to` | the prior and new value of that axis (either may be `null` on the first observed change) |

**Decision time** is computed downstream by pairing a card's `kind: review, to: requested` transition with its later terminal-review transition — the wall-clock minutes a card waited for a human.

## disposition.jsonl

The **un-backfillable** signal: what the human actually did with a finished work
prompt. Emitted by the `Memoria: resolve inbox card` QuickAdd command at the same
moment it writes `attention.jsonl` and `triage.jsonl`; it is not inferred from
board metadata or terminal `review_status`.

```json
{"timestamp": "2026-06-01T11:30:00Z", "event": "work_prompt_reviewed", "path": "inbox/work-prompt-review-x.md", "task_id": "TASK-2026-05-31-003", "lane": "memoria-writer", "disposition": "edited", "outcome": "current (edited)", "agent_recommendation": "clean", "source": "quickadd.resolve-inbox-card"}
```

| Field | Values |
| --- | --- |
| `event` | currently `work_prompt_reviewed` |
| `path` | vault-relative Inbox card path |
| `disposition` | `accepted` \| `edited` \| `rejected` — the three-way human verdict |
| `outcome` | visible resolve choice: `current (accept)`, `current (edited)`, or `archived (reject)` |
| `agent_recommendation` | what the agent proposed (values in the [Glossary](glossary.md) Verdicts table); pairs the agent's self-assessment against the human's call |
| `source` | currently `quickadd.resolve-inbox-card` |

Only `work-prompt` cards with a `task_id` write a disposition row. `archived (done
/ no action)` remains a generic Inbox cleanup outcome and does not count as a
finished-work review. The explicit `current (edited)` outcome is how the human
records accepted-after-changes; without it the system cannot distinguish "accepted
as written" from "accepted after I fixed it."

## cost.jsonl

API spend and token counts, captured once, at the transition into `status: done`
(cost is only final when the work is). The row is not copied from card metadata:
`board_export.py` looks up `runs[].metadata.worker_session_id` with
`hermes kanban show <id> --json`, then joins that ID to the lane profile's
Hermes `state.db` `sessions` row.

```json
{"timestamp": "2026-06-01T09:00:00Z", "task_id": "TASK-2026-05-31-003", "lane": "memoria-writer", "session_id": "20260601_190628_c5e9fb", "cost": 0.0142, "input_tokens": 8200, "output_tokens": 1450, "cache_read_tokens": 0, "cache_write_tokens": 0, "reasoning_tokens": 0, "estimated_cost_usd": 0.0142, "actual_cost_usd": 0.0142, "cost_status": "actual", "cost_source": "provider-usage", "billing_provider": "openai", "pricing_version": "2026-06", "model": "gpt-test", "source": "hermes-session-store"}
```

`cost` is USD and prefers `actual_cost_usd`, falling back to `estimated_cost_usd`
when the actual value is absent. Token counts use the explicit Hermes field names:
`input_tokens`, `output_tokens`, `cache_read_tokens`, `cache_write_tokens`, and
`reasoning_tokens`. The provenance fields (`session_id`, `cost_status`, `cost_source`,
`billing_provider`, `pricing_version`, `model`, `source`) preserve where the number
came from.

Run `python src/.memoria/mcp/board_export.py --cost-doctor` to validate the
current Hermes session-store contract. Schema drift or a `hermes kanban show`
contract change fails closed; missing data is reported separately and never
materialized as zero spend.

## cost-misses.jsonl

Completion transitions whose cost join could not produce a trustworthy row.

```json
{"timestamp": "2026-06-01T09:00:00Z", "task_id": "TASK-2026-05-31-003", "lane": "memoria-writer", "reason": "missing-session-row", "session_id": "20260601_190628_c5e9fb", "source": "hermes-session-store"}
```

`reason` is currently `missing-state-db` or `missing-session-row`. These rows are
quality counters, not cost facts, and downstream spend totals must ignore them.

## attention.jsonl

The Obsidian-side PI attention signal. The `Memoria: resolve inbox card` QuickAdd command appends one row when the active Inbox card is resolved. This is the only signal emitted from the actual human action surface rather than from the board exporter.

```json
{"timestamp": "2026-06-01T11:30:00Z", "event": "inbox_card_resolved", "path": "inbox/work-prompt-review-x.md", "lane": "memoria-writer", "task_id": "TASK-2026-05-31-003", "outcome": "current (accept)", "lifecycle_from": "proposed", "lifecycle_to": "current", "opened_at": "2026-06-01T11:00:00Z", "resolved_at": "2026-06-01T11:30:00Z", "duration_minutes": 30.0}
```

| Field | Meaning |
| --- | --- |
| `event` | currently `inbox_card_resolved` |
| `path` | vault-relative Inbox card path |
| `lane` / `task_id` | copied from card frontmatter when present; otherwise `lane` is `unknown` and `task_id` is blank |
| `outcome` | the visible resolve choice the PI selected |
| `lifecycle_from` / `lifecycle_to` | card lifecycle before and after the resolve command |
| `opened_at` / `resolved_at` | the open marker and resolve timestamp; `opened_at` uses `attention_opened_at`, `opened_at`, then `created` if present |
| `duration_minutes` | rounded wall-clock minutes from `opened_at` to `resolved_at`; `null` when no usable open marker exists |

## triage.jsonl

The PI's Inbox decision stream. The same `Memoria: resolve inbox card` action that writes `attention.jsonl` also appends one triage row with the selected outcome and lifecycle transition.

```json
{"timestamp": "2026-06-01T11:30:00Z", "event": "inbox_card_resolved", "path": "inbox/work-prompt-review-x.md", "card_type": "work-prompt", "lane": "memoria-writer", "task_id": "TASK-2026-05-31-003", "outcome": "current (accept)", "lifecycle_from": "proposed", "lifecycle_to": "current", "source": "quickadd.resolve-inbox-card"}
```

## pre-file-similarity.jsonl

The ADR-38 shadow ratchet stream. When QuickAdd creates a linked claim note or a
structured source note, it runs a report-only `qmd search --format json --full-path`
check before writing the note, appends a `[!similarity]` callout to the note, and
writes one content-light telemetry row here. It never blocks filing, merges notes,
or claims a calibrated threshold.

```json
{"timestamp": "2026-06-01T11:30:00Z", "event": "pre_file_similarity_shadow", "source": "quickadd.create-linked-claim", "note_type": "claim", "path": "notes/claims/example.md", "source_path": "notes/sources/smith2026.md", "query_sha256": "64hex...", "query_chars": 118, "status": "ok", "warning": "", "neighbours": [{"path": "notes/claims/nearby.md", "score": 0.42}]}
```

| Field | Meaning |
| --- | --- |
| `source` | QuickAdd surface that filed the note: `quickadd.create-linked-claim` or `quickadd.structured-source-capture` |
| `note_type` | `claim` or `source` |
| `path` / `source_path` | vault-relative new note path and, for linked claims, the source note it was distilled from |
| `query_sha256` / `query_chars` | content-light fingerprint and length of the proposed claim/source text; the raw query is not logged |
| `status` | `ok` when qmd ran, `unavailable` when the vault path was unavailable or the qmd command failed |
| `warning` | empty, `no-scoped-neighbours`, `vault-base-path-unavailable`, or `qmd-search-failed` |
| `neighbours` | up to three scoped neighbours under `notes/claims/` or `notes/sources/`, with qmd scores when reported |

`warning` rows are expected in fresh or unindexed vaults and are shadow telemetry
for the later #562 enforcement/tuning work, not release blockers. The human-facing
callout points to the qmd rebuild guide when the check looks stale.

## blind-review-samples.jsonl

The deterministic blind re-review sampler. When `board_export.py` observes a card's `review_status` reach a terminal outcome, it hashes the card id and samples a stable small fraction for a second pass. `metadata.blind_rereview: true` on a card forces a sample for an intentional spot-check or a test fixture.

```json
{"timestamp": "2026-06-01T11:30:00Z", "task_id": "TASK-2026-05-31-003", "lane": "memoria-writer", "disposition": "accepted", "review_status": "approved", "sample_reason": "blind-rereview", "agent_recommendation": "clean"}
```

## linkage.jsonl

The deterministic linker refuses to create or merge entity notes by name alone. When an ingest run encounters authors, venues, or organizations without stable IDs, it records the count and names here.

```json
{"timestamp": "2026-06-01T09:15:00Z", "stage": "link", "citekey": "smith2026test", "event": "recorded_by_name", "counts": {"authors": 1, "venues": 0, "orgs": 1}, "total": 2, "recorded_by_name": {"authors": ["Bob B"], "venues": [], "orgs": ["Acme Lab"]}, "source": "link.py"}
```

This log feeds the ADR-59 record-linkage trigger. It is a counter, not a merge proposal: ID-keyed linking remains the only automatic entity creation path.

## cron-heartbeat.jsonl

Successful scheduled operations append a heartbeat row after their operation chain exits cleanly.

```json
{"timestamp": "2026-06-01T06:30:00Z", "job": "memoria-metrics", "status": "success", "source": "cron-wrapper"}
```

The wrappers do not write a success heartbeat after a failed command. Missing or stale heartbeats are therefore the evidence used by always-on / sleep / scheduler-trigger checks.

## lint-findings.jsonl

One row per detector finding from a `memoria-lint` run. The in-memory shape is the `Finding` dataclass in `src/.memoria/operations/integrity/linter/detectors.py`; serialized as:

```json
{"timestamp": "2026-06-01T02:00:00Z", "detector": "fama-exposure", "severity": "HIGH", "path": "projects/draft-x/notes/n.md", "message": "cites superseded claim [[oldclaim]]"}
```

| Field | Values |
| --- | --- |
| `timestamp` | ISO-8601 UTC; one clock per lint pass (`run_all` stamps every finding in a pass with the same time) — enables periodized rollups and 4-week trends |
| `detector` | the detector slug (`orphan-working-files`, `broken-wikilink`, `fama-exposure`, …) |
| `severity` | `LOW` \| `MEDIUM` \| `HIGH` \| `CRITICAL` |
| `path` | vault-relative path of the offending note |
| `message` | short human-readable cause |

The per-pass `PASS` / `REVIEW` / `FAIL` verdict is computed from severities (per [Linter: detectors and auto-fix](linter.md)) and persisted **per period** as a `lint-verdict` note (below), not as a field on each finding.

## Derived: lane-metric notes

`metrics_aggregate.py` reads the logs above weekly and writes one Markdown note per lane per period to `system/metrics/lane-<lane>-<period>.md`. These are *output*, but their frontmatter is a stable contract:

| Field | Source | Meaning |
| --- | --- | --- |
| `trust_score` | composite | the lane's headline score |
| `accepted` / `edited` / `rejected` | `disposition.jsonl` | three-way disposition counts |
| `accept_ratio` | derived | `accepted / (accepted + edited + rejected)` |
| `decision_time_min` | `board-transitions.jsonl` | median human review latency, minutes |
| `time_on_gate_min` | board card timestamps | median time from card creation to terminal `done` / `blocked`, minutes |
| `expand_then_accept_min` | `attention.jsonl` / board metadata | median PI expansion-to-accepted resolution latency, minutes |
| `card_open_resolve_min` | `attention.jsonl` | median open-marker-to-resolve latency, minutes |
| `blind_rereview_samples` | `blind-review-samples.jsonl` | count of terminal reviews sampled for blind re-review |
| `cost` / `input_tokens` / `output_tokens` | `cost.jsonl` | period totals |
| `consistency_passk` | reserved | placeholder (`null`) for a future pass^k harness |

### The trust-score composite

`trust_score` is the lane's headline 0–100 number, computed by `src/.memoria/mcp/metrics_aggregate.py` from the signals above. It starts at 100 and subtracts weighted penalties, each capped so no single signal can sink the score alone:

| Penalty | Weight | Cap | Driven by |
| --- | --- | --- | --- |
| `deny_rate` | 40 × rate | — | denials ÷ writes (`audit.jsonl`) — the strongest negative signal (injection / misconfiguration) |
| `1 − success_rate` | 40 × rate | — | failed runs — `done ÷ (done + blocked)` from the board |
| `retry_rate` | 20 × rate | 30 | retries ÷ runs |
| drift incidents | 2 each | 20 | structural-drift incidents in the period |
| secret-field hits | 10 each | 30 | secret-field access attempts |
| suggestion-ratio extreme | 10 flat | — | `accept_ratio` > 0.9 (rubber-stamping) **or** < 0.2 (candidate scoring needs tuning) |

The result is clamped to `[0, 100]` and rounded. Bands: **≥ 90 healthy · 70–89 watch · < 70 act**. A lane with fewer than 5 samples in the period is reported `insufficient-data` rather than a band — the score is indicative, not actionable. The inputs in prose and the dashboard that renders the bands are in [Dashboards](dashboards.md).

## Derived: lint-verdict notes

`metrics_aggregate.py` also rolls the period's `lint-findings.jsonl` into one `system/metrics/lint-verdict-<period>.md` note (written only once the Linter has produced a findings log). It gives the drift dashboards a periodized verdict history that the timeless findings feed can't:

| Field | Meaning |
| --- | --- |
| `type` | `lint-verdict` |
| `period` | ISO week (`2026-W22`), matching the lane-metric notes |
| `verdict` | `PASS` / `REVIEW` / `FAIL` (any `CRITICAL` → FAIL; any `HIGH`/`MEDIUM` → REVIEW; else PASS) |
| `finding_count` | total findings in the period |
| `critical_count` / `high_count` / `medium_count` / `low_count` | per-severity counts |
| `computed_at` | ISO-8601 UTC when the aggregator wrote the note |

A field with no data for the period renders as `null` (never omitted) so downstream parsers see a stable key set.

The read-only Memoria Inspector pane ([ADR-84](../adr/84-read-only-obsidian-inspector.md))
reads the latest board-state snapshot, recent audit rows, latest `lint-verdict` note,
and latest lane-metric notes to show the same operational health signals inside
Obsidian. It does not emit telemetry or mutate any source log.

## What is *not* captured

By design, to keep capture minimal and the consent story simple:

- **No note content** ever enters a log — only paths, IDs, counts, severities, and the human verdict.
- **No keystroke- or token-level provenance** inside a draft; cost is per-card, not per-edit.
- **No `pass^k` consistency runs** — the `consistency_passk` field exists but the harness that would populate it is deferred.

## Related

- Telemetry inventory and conventions: [Telemetry & logs](telemetry.md)
- Diagnostic plane: [Diagnostics](diagnostics.md)


---

<!-- source: reference/telemetry.md -->

# Telemetry & logs

Every signal Memoria records about its own operation, with the log inventory,
capture posture, and shared conventions. Audit and analytics logs live under
`system/logs/`; the diagnostic plane is the deliberate exception and lives
outside the vault under the OS state directory. For the design rationale — why these particular signals and how they
map to a publication — see [ADR-20 (publication path)](../adr/20-publication-path.md),
the deferred [ADR-62 (measurement and verification harnesses)](../adr/62-measurement-and-verification-harnesses.md),
and [ADR-105 (diagnostic plane)](../adr/105-diagnostic-plane.md).

## Conventions (apply to every log)

- **Format.** One JSON object per line (JSONL). No top-level array, no trailing comma; a partial last line is the only acceptable corruption and is dropped on read.
- **Append-only.** Writers only ever `open(..., "a")`. Rows are immutable events; nothing is rewritten in place. Rotation (truncate-after-archive) is the *only* sanctioned mutation, and only the owning profile may do it (see the `authorized-targeted` auto-fix class in [Policy MCP](policy-mcp.md)).
- **Time.** Every row carries a timestamp in ISO-8601 **UTC** with a trailing `Z` (`2026-06-01T14:23:01Z`). The key is `timestamp` in every log. Never local time — cross-log joins depend on a single clock.
- **Identity.** Card-scoped rows carry `task_id` (board card ID) and `lane` (the assignee profile, e.g. `memoria-writer`). `task_id` is the join key across `board-transitions`, `disposition`, and `cost`.
- **Encoding.** UTF-8, `ensure_ascii=false` — em-dashes and accented author names survive verbatim.

## Log inventory

| File | Writer | Cadence | One row = |
| --- | --- | --- | --- |
| `audit.jsonl` | policy MCP | per gated decision | one policy decision (`allow` / `allow_with_log` / `deny` / `dry_run`) |
| `board-state.jsonl` | `board_export.py` | per export run | a snapshot of per-lane queue counts |
| `board-transitions.jsonl` | `board_export.py` | per export run | one card changing `status` or `review_status` |
| `disposition.jsonl` | Obsidian QuickAdd | per Inbox resolve action | one human review disposition over a work prompt |
| `cost.jsonl` | `board_export.py` | per export run | one completed card joined to a Hermes session cost row |
| `cost-misses.jsonl` | `board_export.py` | per export run | one completed card whose Hermes session join could not be completed |
| `attention.jsonl` | Obsidian QuickAdd | per Inbox resolve action | one PI-side card-open-to-resolve timing sample |
| `triage.jsonl` | Obsidian QuickAdd | per Inbox resolve action | one PI triage decision over an Inbox card |
| `pre-file-similarity.jsonl` | Obsidian QuickAdd | per claim/source note creation | qmd top-neighbour shadow check before filing |
| `blind-review-samples.jsonl` | `board_export.py` | per export run | one terminal review selected for blind re-review |
| `linkage.jsonl` | ingest `link.py` | per ingest with ID-missing names | by-name entity collision counters the linker refused to merge |
| `cron-heartbeat.jsonl` | cron wrappers | per successful cron job | last-successful-run heartbeat for always-on trigger detection |
| `lint-findings.jsonl` | `memoria-lint` cron | per Linter run | one detector finding |

> **Per-session summaries (`sessions/YYYY-MM-DD-HHMM.jsonl`).** The Linter's `session_summary.py` writes one deterministic digest file per session into `system/logs/sessions/` on the daily lint cron — a header (task, profiles, start/end, action/decision counts) plus one record per touched path. The decision is [ADR-25 (two session logs)](../adr/25-session-logging-two-logs.md); the raw record of session activity remains `audit.jsonl` (below).

Derived, not raw: `system/metrics/lane-<lane>-<period>.md` notes are *computed* by `metrics_aggregate.py` from the logs above; they are reference output, not a capture point. See [their schema](telemetry-logs.md#derived-lane-metric-notes). Likewise derived: `system/metrics/eval/runs.jsonl`, one line per scored vault-eval run, written by `eval_score.py` from the board's eval-card results — schema in [Vault eval](vault-eval.md).

> **Hermes-dependent cost capture.** `board_export.py --cost-doctor` validates the
> pinned Hermes session-store shape before live exports trust cost joins. On a
> completion transition, the exporter reads `hermes kanban show <id> --json` for
> `runs[].metadata.worker_session_id`, joins that ID to
> `~/.hermes/profiles/<lane>/state.db` (`sessions` table), and writes `cost.jsonl`.
> CLI or schema drift fails closed with a clear doctor error. Normal data misses
> such as a missing profile database or missing session row are counted in
> `cost-misses.jsonl` and do not create a bogus zero-cost row.

## Diagnostic plane

Local troubleshooting records for Memoria-owned MCP servers and operations live outside the vault. Exact location, redaction, bundle, and raw-capture rules are in [Diagnostics](diagnostics.md).

## Log schemas

The per-log JSONL schemas and derived metric-note contracts live in [Telemetry log schemas](telemetry-logs.md).

## Related

- Diagnostic plane: [Diagnostics](diagnostics.md)
- Per-log schemas: [Telemetry log schemas](telemetry-logs.md)
- Audit-log writer: [Policy MCP](policy-mcp.md)


---

<!-- source: reference/vault-eval.md -->

# Vault eval

`vault-eval` ([ADR-11](../adr/11-vault-eval-maintenance.md)) is Memoria's system-level evaluation: a small, hand-curated **gold set** per workflow that measures whether the *deployed system* finds, extracts, links, and verifies correctly *on this vault*. It reuses existing machinery (board dispatch, the lane → profile map, the Linter's schema and broken-link checks, the golden copy), and its verdict is diagnostic, not gating — a dip informs the PI but does not pause scheduled work. The rationale for both choices is in [ADR-11](../adr/11-vault-eval-maintenance.md).

---

## The gold set

Gold tasks live in `system/eval/` as typed documents — `type: eval-task`, schema `src/.memoria/schemas/types/eval-task.yaml`. Each is self-contained: an `## Input`, an `## Expected behavior`, and a `## Scoring rubric` section, so a lane can run and score it with nothing but the card.

| Field | Kind | Meaning |
| --- | --- | --- |
| `type` | `literal:eval-task` | — |
| `title` | str | The card title fragment. |
| `lifecycle` | `proposed → current → archived` | Only `current` tasks dispatch. |
| `workflow` | str | The capability under test (`find` · `extract` · `link` · `verify` · …). |
| `lane` | enum | The board lane the eval card routes to: `catalog` · `extract` · `link` · `map` · `draft` · `verify` · `code` ([ADR-48](../adr/48-copi-and-agent-consolidation.md)). |
| `references` | list (optional) | Citekeys the task presupposes in the catalog. |
| `created` | date (optional) | — |

The shipped set (nine tasks) references well-known papers — the Transformer, BERT, ResNet, Adam, Dropout — so it works on any vault once those papers are ingested:

| Workflow | Lane | Gold tasks |
| --- | --- | --- |
| `find` | `catalog` (Librarian) | locate the Transformer paper; resolve a paraphrase to the ResNet paper |
| `extract` | `extract` (Librarian) | claim stubs from the Transformer paper; Adam's exact default hyperparameters |
| `link` | `link` (Librarian) | propose BERT builds-on Transformer; *decline* a strong dropout↔ResNet edge (negative control) |
| `verify` | `verify` (Peer-reviewer) | a supported BLEU figure (positive control); a contradicted positional-encoding claim; a BERT-Base/Large parameter swap |

Like patterns, eval tasks are authored directly — the files *are* the instances, no template. They are golden-copied ([ADR-55](../adr/55-src-scaffold-populate-golden-copy.md)), schema-checked by the Linter and the pre-commit hook, and a gold task whose wikilinked target no longer resolves surfaces as a broken-reference finding — gold-set rot is caught by machinery already running.

---

## Dispatch

`src/.memoria/operations/telemetry/eval/eval_dispatch.py` — a sweeps-shaped operation: deterministic, no-LLM, enqueues idempotent cards and lets the board provide serialization and dedup ([ADR-30](../adr/30-deterministic-ingest-pipeline.md) discipline).

- One `hermes kanban create` per `lifecycle: current` gold task, assigned to the lane's owning profile (the same lane → profile map as the Co-PI's `tasks_mcp.py`; a test guards the parity).
- **Idempotency key per (task, quarter):** `eval:<task-id>:<quarter>` — the quarterly cron and any on-demand re-runs inside a quarter converge to one card per task; a new quarter re-opens the window.
- The card body wraps the task in the **non-committing eval contract**: scratch-only writes, results reported on the card — a run never mutates the vault.
- The dispatch record is written to `system/eval/last-run.md` (plain markdown, overwritten each run).

```sh
python .memoria/operations/telemetry/eval/eval_dispatch.py --vault <vault>            # dispatch
python .memoria/operations/telemetry/eval/eval_dispatch.py --vault <vault> --dry-run  # print, create nothing
```

## Scoring

`src/.memoria/operations/telemetry/eval/eval_score.py` — the deterministic scorer (zero-LLM, report-only). It closes the loop the dispatcher opens, turning each quarter's run into machine scores.

**The result contract.** A lane never writes the vault; it ends its card report with one fenced `json` block (the card body shows the exact template, pre-filled with the task id and quarter):

```json
{
  "vault_eval": "result",
  "task": "<gold-task id>",
  "quarter": "<e.g. 2026-Q2>",
  "retrieved": ["<citekey>", "..."],
  "cited": ["<citekey>", "..."],
  "claims": ["<claim-note-stem>", "..."],
  "self_score": 1.0
}
```

`retrieved` (ranked results, best first), `cited` (citekeys offered as evidence), and `claims` (claim notes used or produced; `[]` = none) are each optional — a lane reports the fields its workflow produces. The scorer reads the cards via `hermes kanban list --json` (`--from-json <file>` offline, the `board_export.py` pattern) and computes per task only what the result makes computable — **no fake scores**; a task with no result block is reported `unscored`, and a result with no computable field is `reported`.

| Metric | 0–1, higher is better | Computed when |
| --- | --- | --- |
| `recall_at_k` | Fraction of the task's gold citekeys (frontmatter `references`) in the top-*k* of `retrieved` (default k=3, the rubrics' "top 3" window; `--k`). | `retrieved` reported and the task has `references`. |
| `support_rate` | Fraction of `cited` citekeys resolving to a real catalog record (note stem or `citekey:` frontmatter under `catalog/`). | `cited` reported, non-empty. |
| `fama_clean` | 1.0 if no note in `claims` is a superseded/archived claim, else 0.0 — the same superseded-reuse check the Linter's detector enforces (a test guards the parity, see [Linter: detectors and auto-fix](linter.md#the-detectors)); offenders are named in `fama_exposed`. | `claims` reported (`[]` counts: no claims used → clean). |

The lane's rubric `self_score` is recorded per task for comparison but never aggregated — only the machine metrics trend.

**The log.** Each scoring run appends one JSONL line to `system/metrics/eval/runs.jsonl` — timestamp, quarter, k, per-task records, and per-metric aggregates (`mean` + `n`, plus scored/reported/unscored counts). When a quarter produced no result blocks at all, nothing is appended. The **eval-trend dashboard** (`system/dashboards/eval-trend.md`) renders the newest line per quarter as the trend, plus the latest run's per-task breakdown — see [Dashboards](dashboards.md).

```sh
python .memoria/operations/telemetry/eval/eval_score.py --vault <vault>                       # score the current quarter
python .memoria/operations/telemetry/eval/eval_score.py --vault <vault> --quarter previous    # what the cron runs
python .memoria/operations/telemetry/eval/eval_score.py --vault <vault> --quarter 2026-Q2 --dry-run
```

## Cadence

The installer wires the quarterly `memoria-eval` cron (schedule and wrapper owned by [Installer (bootstrap)](installer.md#the-crons-it-wires)), following the same pattern as the lint and metrics crons. The wrapper first **scores the previous quarter** (its cards have reported by then), then **dispatches** the new quarter's cards. On-demand runs are the same commands by hand.

---

## Related

- The decision: [ADR-11](../adr/11-vault-eval-maintenance.md)
- The lanes the cards route to: [Profile capabilities](profiles.md)
- The machinery that guards the gold set: [Linter: detectors and auto-fix](linter.md)
- The trend dashboard and metric bands: [Dashboards](dashboards.md)
- The other scheduled jobs: [Installer (bootstrap)](installer.md)


---

<!-- source: reference/vocabulary.md -->

# Vocabulary

`system/vocabulary.md` is the visible, PI-editable home for the controlled values used by `research_area`, `methodology`, and claim `topics`.

The shipped file lives at [`src/system/vocabulary.md`](https://github.com/eranroseman/memoria-vault/blob/main/src/system/vocabulary.md). In a runtime vault, edit `system/vocabulary.md` directly and keep note frontmatter values in lockstep with it.

## Fields

| Field | Applies to | Source list |
| --- | --- | --- |
| `research_area` | `paper`, `source` | `system/vocabulary.md` → `## research_area` |
| `methodology` | `paper`, `source` | `system/vocabulary.md` → `## methodology` |
| `topics` | `claim` | Draw from `## research_area` so claims and sources stay queryable together |

## Allowed values

The tables below mirror the shipped [`src/system/vocabulary.md`](https://github.com/eranroseman/memoria-vault/blob/main/src/system/vocabulary.md). That note is the single source of truth — if these tables and the shipped note ever disagree, the shipped note wins. Each field takes **many values per note**.

### `research_area`

*What the work is about.* Claim `topics` draw from this same list. Kept to ~30 terms; consolidate drift at roughly fifty papers.

| Term | Definition |
| --- | --- |
| `personal-informatics` | Self-tracking systems and how people collect, reflect on, and act on data about their own behavior and health. |
| `mobile-health` | Health interventions and tools delivered through smartphones and mobile devices (mHealth). |
| `digital-mental-health` | Technology-delivered mental-health screening, support, and therapy. |
| `health-equity` | Fair access to and outcomes from health technology across populations; reducing disparities. |
| `patient-clinician-communication` | How technology mediates interaction between patients and their care providers. |
| `engagement-sustained-use` | Drivers of initial adoption and long-term continued use of health technology. |
| `chronic-disease-management` | Technology supporting the ongoing management of long-term conditions (diabetes, hypertension, and the like). |
| `behavior-change` | Designing systems to initiate and maintain changes in health behavior. |
| `llm-generative-ai-for-health` | Large language models and generative AI applied to health information, support, and care. |
| `patient-generated-data` | Health data created by patients outside clinical settings and its use in care. |
| `family-caregiver-health` | Technology supporting informal caregivers and family involvement in health. |
| `mobile-sensing` | Passive collection of behavioral and physiological signals from mobile-phone sensors. |
| `sociotechnical-systems` | The interplay of social context and technical systems in health settings. |
| `social-computing-for-health` | Social-media and collective-platform dynamics applied to health. |
| `conversational-agents` | Chatbots and voice agents for health support and interaction. |
| `community-health` | Technology serving population- and community-level health needs. |
| `digital-therapeutics` | Evidence-based software interventions that treat or manage a condition (DTx). |
| `wearable-sensing` | Body-worn devices that capture physiological and activity signals. |
| `aging` | Technology for older adults and age-related health needs. |
| `human-ai-interaction` | How people understand, trust, and collaborate with AI systems. |
| `online-health-communities` | Peer-support forums and groups where people discuss health. |
| `implementation-science` | How interventions are adopted, scaled, and sustained in real-world care settings. |
| `sensemaking` | How people interpret and construct understanding from health data and information. |
| `race-intersectionality` | How race and intersecting identities shape health-technology experiences and outcomes. |
| `cscw-collaborative-work` | Computer-supported cooperative work applied to health and care coordination. |
| `jitai` | Just-in-time adaptive interventions that deliver support tailored to a person's changing state and context. |
| `ema-self-report` | Ecological momentary assessment and self-report capture of in-the-moment experience. |

### `methodology`

*How the study was structured, and the techniques it used.* The schema carries study architecture and specific technique in this one field; both groups below are valid `methodology` values.

**Research architecture — how the study was structured**

| Term | Definition |
| --- | --- |
| `rct` | Randomized controlled trial. |
| `quasi-experiment` | Controlled comparison without randomization. |
| `observational` | Non-interventional study of naturally occurring data. |
| `field-study` | In-situ deployment study in a real-world setting. |
| `lab-experiment` | Controlled experiment conducted in a lab. |
| `survey-study` | Cross-sectional questionnaire-based study. |
| `qualitative` | Interview, ethnographic, or grounded inquiry as the primary architecture. |
| `design-science` | Build-and-evaluate of a novel artifact or system. |
| `formative-study` | Early needs-finding or exploratory design study. |
| `case-study` | In-depth study of one or a few instances. |
| `systematic-review` | Structured synthesis of prior studies. |
| `meta-analysis` | Statistical pooling of results across studies. |
| `secondary-analysis` | New analysis of an existing dataset. |

**Specific methods — the techniques used**

| Term | Definition |
| --- | --- |
| `semi-structured-interview` | Open-ended interviews around a guiding protocol. |
| `thematic-analysis` | Coding qualitative data into recurring themes. |
| `grounded-theory` | Building theory inductively from data. |
| `contextual-inquiry` | Observing and interviewing participants in their own setting. |
| `experience-sampling` | Repeated in-situ prompts capturing momentary experience. |
| `ecological-momentary-assessment` | Time- or event-sampled self-report in daily life. |
| `diary-study` | Participant-logged entries over a study period. |
| `co-design` | Designing artifacts together with stakeholders. |
| `usability-testing` | Observed task performance to surface interaction problems. |
| `think-aloud` | Participants verbalize thought while performing tasks. |
| `survey` | Structured questionnaire administered to a sample. |
| `regression` | Modeling outcomes as functions of predictors. |
| `mixed-effects-model` | Regression with fixed and random effects for nested data. |
| `log-analysis` | Analysis of system interaction logs. |
| `machine-learning` | Supervised or unsupervised modeling for prediction or clustering. |
| `nlp` | Computational analysis of text. |
| `content-analysis` | Systematic categorization of communication content. |
| `participant-observation` | Researcher embeds in the setting being studied. |
| `ab-test` | Randomized comparison of two variants in deployment. |

### `topics`

Claim notes only. Drawn from the `research_area` terms above so a claim and the sources it rests on share the same controlled values (and surface together in queries). Propose a new provisional term only when no `research_area` value fits.

## Related

- How to edit the lists: [Manage your topic vocabulary](../how-to-guides/knowledge/manage-vocabulary.md)
- Why this exists: [Vocabulary discipline](../explanation/knowledge/vocabulary-discipline.md)
- Frontmatter field grammar: [Frontmatter fields](frontmatter.md)


---

<!-- source: reference/worklists.md -->

# Worklists

`src/.memoria/operations/lib/worklists.py` turns a high-cardinality report into one file-backed batch review surface. The operation writes many `worklist-item` notes and raises exactly one aggregate Inbox `work-prompt` for the PI.

## Command

```bash
python src/.memoria/operations/lib/worklists.py emit --vault <vault> --report report.json --title "Batch title"
```

| Option | Contract |
| --- | --- |
| `emit` | The only CLI subcommand. |
| `--vault <vault>` | Runtime vault root. Required. |
| `--report <file>` | JSON report containing `items` or `rows`. Required. |
| `--title <text>` | Overrides the report title. Optional. |
| `--workflow <name>` | Default group/category for rows without `group` or `category`; defaults to `screen`. |

## Report JSON

The report must contain either `items` or `rows` as a list. Each row may be an object or a scalar. Scalar rows are converted to `{"title": <value>, "item_ref": <value>}`.

| Report field | Use |
| --- | --- |
| `title` | Batch title when `--title` is omitted. |
| `source_report` | Source path recorded on emitted item notes and in the Inbox prompt. |
| `worklist` / `worklist_id` | Stable worklist slug input. If absent, the title is slugged. |
| `items` / `rows` | Row list. |

Row objects may include `title` or `name`, `item_ref` or `target` or `path` or `citekey` or `url` or `id`, `group` or `category`, `decision`, `rank`, `reason`, `evidence`, and `source_report`.

`decision` defaults to `proposed` and must be one of `proposed`, `include`, `exclude`, `maybe`, or `archived`.

## Outputs

| Path | Shape |
| --- | --- |
| `system/worklists/<worklist>/<rank-title>.md` | One `type: worklist-item` note per row. |
| `inbox/work-prompt-*.md` | One aggregate review prompt with `raised_by: worklists` and `lane: copi`. |

The aggregate prompt uses a `worklist-<slug>` dedupe key. Re-running the same report rewrites the item notes and does not create a second prompt when the deduped prompt already exists.

## Related

- Worklist fields: [Frontmatter fields](frontmatter.md)
- Worklist document type: [Document types](document-types.md)
- Operation inventory: [Operations](operations.md)


---

<!-- source: reference/zotero-plugins.md -->

# Zotero plugins

Plugins that install in **Zotero** (not Obsidian), plus the Zotero↔Obsidian connector comparison. For the Obsidian plugin set (including `obsidian-citation-plugin`, the connector Memoria ships with) see [Obsidian plugins](obsidian-plugins.md). For setup steps see [Set up Zotero](../how-to-guides/zotero/set-up-zotero.md).

---

## Zotero add-ons

Required or recommended alongside the Obsidian plugin set.

| Add-on | Install in | Status | Purpose |
| --- | --- | --- | --- |
| Better BibTeX | Zotero | **Required** | Stable citekeys; auto-export `.bib` to vault; `zotero.lua` Lua filter for live Word export. |
| MarkDB-Connect | Zotero | Recommended | Tags Zotero items that have a vault note; right-click → jump to note. Setup: [Set up Zotero](../how-to-guides/zotero/set-up-zotero.md). |
| RTF/ODF Scan | Zotero | Optional | Converts Scannable Cite markers in `.odt` exports to live LibreOffice citations. Needed only for the LibreOffice live-citation export route. |

---

## Zotero ↔ Obsidian connector comparison

Four Obsidian plugins connect Zotero to Obsidian. Memoria ships with `obsidian-citation-plugin` (documented in [Obsidian plugins](obsidian-plugins.md)); the others are documented here for evaluation.

| Plugin | Connects via | Zotero must run | Annotation import | Bulk import | Stability |
| --- | --- | --- | --- | --- | --- |
| **obsidian-citation-plugin** (hans) | `.bib` / CSL-JSON file | No | No | No | High — Memoria default |
| **zotero-integration** (mgmeyers) | BBT HTTP API | Yes | Yes | No | High — breaks on major updates |
| **zotlit** (PKM-er) | Zotero SQLite DB | No (reads DB) | Yes | Yes | Medium — Zotero 9 issues reported |
| **zotero-bridge + zotero-link** (vanakat) | Zotero Local API | Yes | No | No | Low — ~20 installs/day |

For guidance on choosing between these connectors see [Set up Zotero](../how-to-guides/zotero/set-up-zotero.md).

### Evaluated, not in the install set

| Plugin | Status | Notes |
| --- | --- | --- |
| zotlit | Future migration target | Reads Zotero SQLite directly — faster for bulk imports. See comparison table above. |
| zotero-integration | Not in use | Imports Zotero items via HTTP API; useful if a PDF-annotation workflow is adopted. |
| Inciteful | Not in use | Citation-network discovery (Zotero plugin + public Inciteful API). Surfaces central related papers not yet in the library — a complement to OpenAlex forward/backward snowballing in the discover stage. Additive to an already-covered capability. |

---

## Related

- Obsidian plugin set: [Obsidian plugins](obsidian-plugins.md)
- Obsidian plugin settings: [Obsidian plugin settings](obsidian-plugin-settings.md)
- Zotero setup how-to: [Set up Zotero](../how-to-guides/zotero/set-up-zotero.md)


---

<!-- source: explanation/README.md -->

# Explanation

This section is for **understanding** Memoria — what it is, how it thinks, and why it was built the way it was. These documents answer "why" and "what is" questions. They are for reading and reflection, not for following step-by-step.

If you need to *do* something, see [how-to guides](../how-to-guides). If you need exact values, field names, or configuration formats, see [Reference](../reference). If you want a guided first experience, see [Tutorials](../tutorials).

---

## What explanation documents do (and don't do)

Explanation documents build a mental model. They:

- Answer "why is it this way?" and "what does this mean?"
- Compare alternatives and explain trade-offs
- Provide context and intellectual background
- Make connections between concepts

They don't include step-by-step instructions, lookup tables, or precise configuration values. When an explanation references exact schemas or commands, it points to the reference section.

---

## Conceptual map

Read from the inside out: start with what the system is, then why it's shaped that way, then how each design area works.

### Start here — [Overview](overview/README.md)

1. **[What Memoria is](overview/what-memoria-is.md)** — the system's identity: what it is, what it's not, and why it exists. Everything else builds on this.
2. **[Intellectual foundations](overview/intellectual-foundations.md)** — the three ideas Memoria is built on (Karpathy, Zettelkasten, Memex) and how the AI-research systems survey shaped the design.
3. **[Design principles](overview/design-principles.md)** — the cross-cutting principles the design returns to.

### Why the design is shaped this way

1. **[Why the architecture is layered](rationale/why-three-layers.md)** — why board, workers, and vault are kept separate.
2. **[Why specialist profiles, not a generalist agent](rationale/why-specialist-profiles.md)** — why five profiles (one conversational Co-PI plus four background lanes) instead of one generalist agent.
3. **[Why the review gate is structural](rationale/why-human-gate.md)** — why the review gate is structural, not advisory.
4. **[Why Memoria doesn't pursue full autonomy](rationale/why-not-autonomous.md)** — the autonomy ceiling and why Memoria doesn't cross it.

### How it's structured

1. **[Architecture](architecture/README.md)** — the seven-layer model and the structural pages (control plane, memory tiers, channels, vault, logging).
2. **[Knowledge](knowledge/README.md)** — how the vault organizes durable knowledge (lifecycle folders, document types, gated promotion).
3. **[Workflows](workflows/README.md)** — how work moves through the system (the board as a state machine, review as a state).

---

## Entry points by background

**New to Memoria:** The two identity documents, then [Why the architecture is layered](rationale/why-three-layers.md), the [knowledge model overview](knowledge/README.md), and the [workflow overview](workflows/README.md) together give a working mental model. The architecture, knowledge, and workflow sections fill in the detail.

**Coming from another agent system (LangChain, CrewAI, autogen, etc.):** The key differences — specialist lanes, structural human gate, no reasoning orchestrator — are concentrated in [Why specialist profiles, not a generalist agent](rationale/why-specialist-profiles.md), [Why the review gate is structural](rationale/why-human-gate.md), and [The board as a state machine (the control plane)](workflows/board-as-state-machine.md).

---

## All sections

The curated path above is a reading order, not a full index. The sidebar lists every page; the sections are:

- [Overview](overview/README.md) — start here: what-memoria-is, intellectual-foundations, design-principles
- [Design rationale](rationale/README.md) — the `why-*` arguments: three-layers, specialist-profiles, human-gate, not-autonomous, hermes, computational-methods, pattern-provenance
- [Architecture](architecture/README.md) — what each layer and surface *is*: vault, the memory model, control-plane, interaction channels, session-logging
- [Knowledge](knowledge/README.md) — how durable knowledge is organized: document-types, knowledge-cycle, note-body-structure, lifecycle-over-topic, promotion-model, vocabulary-discipline, common-pitfalls
- [Profiles](profiles/README.md) — the five profiles: Co-PI (conversational front) plus four background lanes — librarian, writer, peer-reviewer, engineer — plus delegation-posture
- [Kanban board](kanban-board/README.md) — the board as coordination layer: states, card-schema, obsidian-projection
- [Workflows](workflows/README.md) — how work moves: board-as-state-machine, review-as-state, plus verify-on-commit
- [Obsidian](obsidian/README.md) — how the human interacts through Obsidian: home, callouts, agent-client-pane, visual-discipline, design-system
- [Dashboards](dashboards/README.md) — the space and support dashboards, grouped: daily-glance, synthesis-agenda, Project space, structural-health, operational-health
- [Deployment](deployment/README.md) — how the system is packaged and installed: distribution-model, bootstrap-installer, deployment-options

---

## For decisions and direction

The *why* behind a specific choice lives in an ADR — see [Decisions](../adr); forward-looking decisions are ADRs too (`status: proposed`) until accepted or rejected. Scheduling and readiness live on GitHub issues. The release plan lives in the repo's [Releasing](https://github.com/eranroseman/memoria-vault/tree/main/docs/releasing) docs.


---

<!-- source: explanation/overview/README.md -->

# Overview

Start here. These three pages give the working mental model the rest of the Explanation section builds on — what Memoria is, the ideas it's built on, and the principles its design returns to.

| Page | What it covers |
|---|---|
| [What Memoria is](what-memoria-is.md) | The system's identity: what it is, what it's not, and why it exists |
| [Intellectual foundations](intellectual-foundations.md) | The four converging ideas Memoria builds on — Karpathy's LLM-wiki, Luhmann's Zettelkasten, Bush's Memex, and the AI-research-systems survey |
| [Design principles](design-principles.md) | The cross-cutting principles the design returns to |

---

## Where to go next

- **Why the design is shaped this way:** [Design rationale](../rationale/README.md)
- **How it's structured:** [Architecture](../architecture/README.md)
- **How knowledge is organized:** [Knowledge](../knowledge/README.md)
- **How work moves:** [Workflows](../workflows/README.md)


---

<!-- source: explanation/overview/what-memoria-is.md -->

# What Memoria is

## The central insight

**Maintaining a knowledge base is a bookkeeping problem, not an intelligence problem.**

Humans are excellent at recognizing what matters and forming original arguments. They are poor at consistently updating summaries, patching broken links, filing useful answers, and running structural health checks. Those tasks are mechanical, repetitive, and easy to defer — and because they're deferred, knowledge bases stagnate. Notes pile up without synthesis; citations go unverified; gaps go unnoticed.

The AI agent is suited for exactly those bookkeeping tasks. Memoria's design follows from this: make the agent narrower and more reliable, and let the human do the irreducibly judgment-laden work. This is not a claim about agent capability — it's a claim about which tasks should be delegated. **Memoria gives the bookkeeping to the agent and keeps judgment human.**

---

## What Memoria is

Memoria is an **opinionated, phase-gated, bounded, personal tool for thinking and writing** — a durable research vault that compounds across months and years.

**Personal** — thinking is private and separate from communication; notes stay unfiltered, preserving raw reasoning before audience-aware editing sanitizes it. The design assumes one human who owns judgment: review decisions, synthesis choices, and scope priorities all belong to that researcher. This is not a team tool.

**Opinionated** — it enforces specific workflows and eliminates setup paralysis. The vault structure, the document types, and the review gates are not configurable surfaces to tune; they are the design.

**Phase-gated** — work passes through defined phases with explicit outputs, and nothing becomes a claim or deliverable without human review. A source doesn't become a claim until it's been classified, discussed, and synthesized; a draft doesn't become a deliverable until it's been verified and approved. Each phase has a clear entry and exit condition.

**Bounded** — agent autonomy is structurally constrained. The agent does not decide what is worth keeping or promote claims to canonical knowledge; the PI does. These limits are structural — enforced by the system's architecture, not by prompt instructions.

It is **knowledge production**, not just storage: the vault grows more useful over time as new sources connect to existing claims, synthesis sharpens as evidence accumulates, and structural maintenance keeps the graph coherent. That is the difference between a research vault and a notes pile.

Day to day, that work happens at three spaces: you bring sources into the **Library**, build them into connected claims in **Knowledge**, and drive an inquiry to output in a **Project**. You act on what the agents surface for you in the **Inbox** queue.

---

## What Memoria is not

**Not an autonomous research scientist.** Contemporary AI research systems (AI Scientist, AI co-scientist, CORAL) run experiments end-to-end, generate papers without review, and promote outputs to canonical based on scalar metrics. Memoria declines this posture for knowledge work — synthesis quality is not scalar, and synthesis errors compound across everything that later cites them.

**Not a general-purpose chat assistant.** Chat history is ephemeral. Conversations are inputs to filing, not the substrate of memory. If a useful answer lives only in a chat transcript, it hasn't been captured.

**Not a Deep Research agent.** Deep Research tools (OpenAI DR, Gemini DR, Perplexity DR) are query-driven and ephemeral: they produce a comprehensive report per query and end. Memoria is corpus-curating and durable: the human builds a vault over months, and each session compounds with prior sessions. The two categories serve different needs.

**Not a single-agent system.** "One model does everything" produces an agent with unclear responsibility, ambiguous permission boundaries, and no separation between discovery and synthesis. Memoria explicitly avoids this. Five profiles — one conversational Co-PI plus four background lanes, each with narrow permissions and a clear exit condition — replace one generalist.

**Not a team tool in its current form.** The design assumes one human reviewer who owns judgment about what enters the canonical vault. Multi-user review semantics are not in scope.

---

## The problem it solves

A research vault typically fails in one of two ways:

1. **Capture without synthesis.** Sources accumulate in the inbox and never move forward. Notes pile up but don't connect. The vault grows but doesn't compound.

2. **Synthesis without rigor.** Bullets replace citations. Summaries replace claims. Sources get summarized in a way that no longer traces back to what the paper actually says.

Both failures are bookkeeping failures. The first is a maintenance problem (who keeps the structure healthy?). The second is a provenance problem (where did this claim come from?).

Memoria addresses both: the agent handles the maintenance discipline that humans consistently avoid; the vault structure enforces provenance.

---

## Where it sits on the autonomy spectrum

On [Chen 2026](../../reference/bibliography.md#chen2026copilots)'s (*From Copilots to Colleagues*) L1–L5 autonomy taxonomy, **Memoria targets L3 with a structurally enforced ceiling** — multi-step work runs unattended within a card, but the human sets the strategy and the review gate blocks every promotion. Why L4 and L5 are out of reach for knowledge work, and where the taxonomy sits in full, is in [Why Memoria doesn't pursue full autonomy](../rationale/why-not-autonomous.md).

Two 2026 perspectives anchor this positioning. [Feng and Liu 2026](../../reference/bibliography.md#feng2026visionary) describe "vibe researching" — the human keeps the intellectual steering wheel while agents handle labor — as the appropriate posture for research. [Bisht et al. 2026](../../reference/bibliography.md#bisht2026agentic) argue current systems are co-scientists, not autonomous scientists, for structural reasons that sit upstream of capability. Memoria is vibe researching made durable (the vault) and gated (blocking review).

---

## Naming

**Memoria** — because the heart of the design is memory: not just collecting information, but building a memory architecture that compounds. The name signals continuity, durability, and the act of remembering as deliberate practice.

**Hermes** — the agent runtime. [Hermes Agent](https://hermes-agent.nousresearch.com/) is the messenger: it carries work between states, between profiles, and between the human and the vault. Memoria is what you keep; Hermes is who moves things.

---

## Related

**Explanation**

- The intellectual roots of the design: [Intellectual foundations](intellectual-foundations.md)
- The seven-layer architecture: [Architecture](../architecture/README.md)
- Why the human gate is structural: [Why the review gate is structural](../rationale/why-human-gate.md)
- Why L3 is the ceiling: [Why Memoria doesn't pursue full autonomy](../rationale/why-not-autonomous.md)
- The principles this framing produces: [Design principles](design-principles.md)

**Reference**

- Term lookup for the jargon used here: [Glossary](../../reference/glossary.md)


---

<!-- source: explanation/overview/intellectual-foundations.md -->

# Intellectual foundations

Memoria is built on four converging ideas and informed by a full review of ~400 papers spanning contemporary AI-research systems and the HCI, extraction, evaluation, and retrieval traditions they build on. Understanding where the design comes from makes it easier to understand why specific choices were made.

---

## Karpathy's LLM-Wiki pattern

[Andrej Karpathy](../../reference/bibliography.md#karpathy-llm-wiki) proposed an AI agent that compiles raw sources into a persistent, interlinked Markdown wiki. The key move is replacing _retrieval from scratch at query time_ with a _persistent wiki that grows with use_.

In standard retrieval-augmented generation, every question triggers a fresh search over raw documents. Useful synthesis is never stored; nothing compounds. The LLM-wiki pattern inverts this: the agent builds durable pages, and each new source improves those pages rather than sitting in isolation. The agent is a **compiler**, not just a retriever.

Memoria takes this insight seriously. The vault is the compiled artifact. Ingest doesn't just add documents — it integrates sources into an existing graph of notes. A new source note connects to existing claims through typed wikilinks. The Librarian profile's job is essentially compilation.

What Memoria doesn't take from this pattern: Karpathy's framing implies an agent that autonomously decides what to synthesize and what to keep. Memoria refuses that — the human decides what enters the canonical graph. The compiler role belongs to the agent; the editorial role belongs to the human.

---

## Luhmann's Zettelkasten

[Niklas Luhmann](../../reference/bibliography.md#luhmann-zettelkasten)'s slip-box method enforces three disciplines that prevent a wiki from becoming an undifferentiated pile:

**Atomicity** — each note captures one idea, not a topic dump. An atomic note can be moved, cited, and linked without carrying irrelevant context.

**Explicit linking** — notes earn their place by connecting to existing notes. A note that connects to nothing has not been integrated into the system; it is still just a document.

**Type distinction** — Luhmann distinguished _fleeting notes_ (raw capture), _literature notes_ (what a source says), and _permanent notes_ (the human's own durable claim). Each type has a different epistemic status and a different lifespan. Memoria preserves this three-way distinction under different names: `fleeting`, `source` (what the source says), and `claim` (what the human thinks). The rename reflects a software context; the distinction is unchanged.

Zettelkasten's weakness in modern workflows is that it is entirely human-maintained — the linking discipline breaks down under load. Memoria delegates the maintenance work to the agent. Classifying notes, detecting orphans, suggesting cross-links, enforcing schema — these are the tasks the Librarian and Linter handle. The _intellectual_ work of the Zettelkasten (writing claim notes, forming arguments, building hubs) remains human.

---

## Bush's Memex

[Vannevar Bush](../../reference/bibliography.md#bush1945)'s 1945 vision: a personal interconnected knowledge machine where _associations_ are first-class objects. The device would let a researcher leave "trails" through a document collection — associative links that persist and can be revisited.

What Bush identified is that memory is associative, not taxonomic. A subject-area folder structure doesn't model how thinking actually works. What makes a knowledge base useful is not whether items are correctly classified, but whether the associations between them are preserved.

Memoria's vault is the Memex made operational: the graph of wikilinks, typed relations, entity links, and hubs is the associative layer. The folders are a secondary organizational scheme; the graph is the primary one. A claim note that has no incoming links hasn't made it into the knowledge graph — it may as well not exist.

---

## The literature review

A full review of ~400 papers (`_papers/`, each read end-to-end and judged for what Memoria should adopt, borrow, or reject) grounds the design in what the field has actually tried. It subsumes an earlier ~47-system survey of agent-driven research platforms and extends across the bodies of work those systems sit on: the HCI/CSCW human-augmentation tradition (mixed-initiative interfaces, Find-Fix-Verify, the social-technical gap), faithful information-extraction and claim-verification methods, evaluation and benchmark discipline, and retrieval with temporal reasoning.

The headline finding is that this wider literature does not merely *permit* Memoria's design — it independently *re-derives* it. The structural review gate ("engines write, agents judge, PI approves"), the durable vault-as-memory, the MCP-only agent sandbox, and deterministic ingest are each re-arrived-at by separate research lines. The patterns Memoria borrows — stage-gated pipelines, thin control over thick state, explicit agent roles, structured outputs at handoffs, persistent knowledge graphs — recur across nearly every end-to-end system, and Memoria's layered split is the structural form of them. The review also fixes what Memoria *declines* (advisory-only LLM review, scalar-metric keep/revert, tree-search-over-synthesis) and contributes two sharpenings to the knowledge model: build contradiction and supersession on entailment rather than embedding similarity, and treat temporal coverage as a first-class retrieval dimension.

The pattern-by-pattern judgment — what was borrowed as-is, taken with the autonomy stripped, referenced for framing, or refused, plus the [cross-cutting findings](../rationale/why-pattern-provenance.md#cross-cutting-findings-from-the-full-literature-review) from the wider corpus — is in [Pattern provenance: borrow, adapt, ignore](../rationale/why-pattern-provenance.md); the confident-wrong argument behind the structural human gate is in [Why the review gate is structural](../rationale/why-human-gate.md).

---

## The synthesis

Memoria takes Karpathy's compiler insight, Luhmann's typed-note discipline, Bush's associative memory, and the operational patterns of contemporary AI-research systems as a single design stack:

- The wiki is the compiled artifact (Karpathy).
- The document types preserve atomicity and lifespan distinction (Zettelkasten).
- The associative graph (wikilinks, hubs, entity links) preserves trails (Memex).
- The stage-gated pipeline and explicit agent roles come from the field survey.
- The AI agent provides the maintenance discipline that all three earlier traditions required from the human.

The design is not a novel invention — it is an integration of patterns that already existed, applied to a specific problem (single-researcher knowledge production) that none of the surveyed systems addressed directly.

---

## Related

- What the foundations produced: [Design principles](design-principles.md)
- Full borrow/adapt/ignore breakdown: [Pattern provenance: borrow, adapt, ignore](../rationale/why-pattern-provenance.md)
- What Memoria is: [What Memoria is](what-memoria-is.md)
- The layered architecture (structural form of thin-control-thick-state): [Architecture](../architecture/README.md)
- Why the autonomy boundary is where it is: [Why Memoria doesn't pursue full autonomy](../rationale/why-not-autonomous.md)


---

<!-- source: explanation/overview/design-principles.md -->

# Design principles

Ten principles that settle ambiguous decisions. When a tool choice, workflow step, or architectural question is unclear, these are the tiebreakers.

---

**1. The vault is the artifact.**

Not the chat log, not the PDF folder, not the Zotero library. The Obsidian vault is what you are building. Everything else — Zotero, Hermes, the Kanban board — serves the vault. A useful output that lives only in a chat transcript hasn't been captured.

**2. Compound, don't just collect.**

Every source ingested should make the whole corpus more useful. A new source note that connects to existing claim notes, adds to a hub, and updates a comparative-brief is compounding. An isolated file that sits unlinked is just collection. The design distinguishes them: synthesis structures (claim notes and hubs) exist precisely to force compounding.

**3. Separate capture from synthesis.**

Raw annotations are not synthesis. A source note is not a claim note. A fleeting thought is not a finished claim. The architecture preserves this distinction with folder structure, lifecycle fields, and separate templates. Blurring it produces a vault where everything is "sort of processed" and nothing is reliably citable.

**4. The agent writes narrowly.**

Agents read broadly but write to controlled areas. Humans review every promotion to canonical zones. This is not a limitation — it is what keeps the vault trustworthy. A vault where agents write freely is a vault where the human doesn't know what they actually believe.

**5. Provenance everywhere.**

Every claim traces back to a citekey. Every agent action traces back to an audit log entry. Untraceable content is not knowledge — it is a liability that will fail when cited. The [Policy MCP](../../reference/policy-mcp.md), its per-write SHA-256 hash pairing, and the `sources:` field on claim notes all enforce this.

**6. Prefer incremental over full rewrites.**

The agent updates notes, not replaces them. History matters. Dry-run before auto-fix. A note that exists and is imperfect is almost always better than a note that was deleted and recreated. The `superseded_by` field exists precisely so claims can be updated without destroying provenance.

**7. Lint or decay.**

A knowledge base that is never linted slowly becomes unusable. The Linter is not optional maintenance — it is the mechanism that keeps the vault structurally trustworthy. Schema drift, broken links, stale enrichment, and orphaned notes compound silently; the Linter makes them visible.

**8. Code is a research output.**

Code artifacts belong in the vault and are traceable to the literature that motivated them. The false boundary between "notes" and "code" is an organizational failure mode. A figure-generation script with no provenance link to the claim it illustrates is as untrustworthy as an uncited claim.

**9. Simplest stack that solves the real bottleneck.**

Every tool in the stack addresses a specific friction point. Tools that don't address real friction are liabilities — they add maintenance overhead, failure modes, and cognitive load. The design is deliberately narrow: Zotero for references, Obsidian for the vault, Hermes for the agent layer. Extensions earn their place by removing friction, not adding features.

**10. The agent lives in the editor.**

Research, writing, and coding all access the same agent from within their respective editors via ACP. Context-switching to a separate chat window is a UX failure mode — the agent should be present where the work is happening, with the active note as implicit context. This is why the agent-client plugin, the command palette, and the VS Code workspace pattern exist.

---

## Related

- Why these principles led to a human-gated system: [Why the review gate is structural](../rationale/why-human-gate.md)
- Why specialist profiles rather than one generalist: [Why specialist profiles, not a generalist agent](../rationale/why-specialist-profiles.md)
- Why not autonomous: [Why Memoria doesn't pursue full autonomy](../rationale/why-not-autonomous.md)
- What the principles describe: [What Memoria is](what-memoria-is.md)
- Where the principles come from: [Intellectual foundations](intellectual-foundations.md)


---

<!-- source: explanation/architecture/README.md -->

# Architecture

Memoria is **seven layers** ([ADR-46](../../adr/46-seven-layer-architecture.md)): the **PI** (the human — Principal Investigator), the **Interface** (the Obsidian UI), the **Co-PI** (the one conversational agent), **Tasks** (the kanban board and its background lanes), **MCP** (the policy boundary), the **Operations** (deterministic mechanisms), and the **Vault** (the files — the knowledge itself). One flow rule governs the stack: **decisions flow down, information flows up.**

```text
L1  PI          the human — the only actor who promotes to canonical
L2  Interface   the Obsidian UI: Home, dashboards, Inbox, Library/Project Workspaces
L3  Co-PI       the permanent conversational agent (Agent Client pane); read-only, delegates writes
L4  Tasks       ephemeral agent lanes + the kanban board + cards
L5  MCP         the policy boundary — agents reach operations and the Vault only through it
L6  Operations     deterministic mechanisms: ingest · search · clustering · sweeps · Linter
L7  Vault       the files & folders — durable knowledge
```

## Three actor-kinds

Three kinds of actor work across the structural layers:

| Actor-kind | Who | Trait |
| --- | --- | --- |
| **PI** | the human (L1) | judgment; the only actor who promotes to canonical |
| **Agents** | the Co-PI (L3) + the Task lanes (L4) | posture + LLM judgment; propose, never dispose |
| **Operations** | ingest · search · clustering · sweeps · Linter (L6) | deterministic, no posture; never on the board |

The "is it an agent or an operation?" question is decided by posture and LLM judgment, not invocation style — deterministic work never occupies a board lane. Agents propose and only the PI disposes; why that gate is structural rather than a convention is [Why the review gate is structural](../rationale/why-human-gate.md).

## The layering binds the agent write-path only

The strict each-layer-depends-only-on-the-one-below contract holds along the **agent write-path** (Co-PI → Tasks → MCP → Operations/Vault). The PI and trusted automation are **direct edges, not rungs**: the PI edits the Vault directly in Obsidian, and cron, CI, and the PI invoke operations directly. Read the stack as a dependency *order*, not a claim that every actor traverses all seven layers.

**MCP is a policy gate, not an execution sandbox.** The MCP layer validates every agent request — allow-listing tools, scoping writes, rate-limiting, logging — before it touches the Vault or an external API. It does not confine processes; the honest phrase is *policy-sandboxed via MCP*. Under the solo, local premise the threat is *wrong writes*, not tenant escape, and the policy gate plus propose-not-dispose, the gated zones, the audit log, and git history cover it. Execution isolation is deferred until untrusted third-party code is actually run.

## Documents in this section

| Page | What it covers |
| --- | --- |
| [The vault](vault.md) | The vault's category folders, type homes, gated zones, archived-as-state, and how Bases and the Linter keep it sound. |
| [The memory model](memory-model.md) | The memory substrates — their scope, owner, and lifespan — and why the Co-PI is the sole memory carrier. |
| [The control plane](control-plane.md) | The board, the lanes, the hidden execution mechanic vs the PI-facing lifecycle, and the handoff payload. |
| [Interaction channels](human-channels.md) | The interaction surfaces — Obsidian, CLI, Telegram — and how the Inbox's graded loudness routes signals. |
| [Session logging](session-logging.md) | What each agent session records, and why the audit log and session summaries stay separate. |
| [Telemetry architecture](telemetry-architecture.md) | Why audit, analytics, and diagnostics are separate planes with different retention and content rules. |

## Where to go next

- **Why the architecture is layered**, and the research behind it → [Why the architecture is layered](../rationale/why-three-layers.md)
- **The agents that occupy L3 and L4** → [Profiles](../profiles/README.md)
- **The deterministic L6 operations** → [Operations](../operations/README.md)
- **The board state machine** under the Tasks layer → [Kanban board](../kanban-board/README.md)


---

<!-- source: explanation/architecture/vault.md -->

# The vault

The vault is where durable knowledge lives. Everything else in Memoria — the board, the agents, the operations, the dashboards — exists to serve it. This page explains its structure: the category folders, the type homes, the gated zones, and the conventions that keep it sound.

---

## Category folders, not lifecycle numbers

The top level is organized by **category** — one content kind per folder, no lifecycle numbers ([ADR-47](../../adr/47-type-first-category-folders.md)). The knowledge is a *network*, not a pipeline: direction lives in the state property, not in folder ordering.

```text
<vault-root>/
├── home.md         ← launch/reset welcome note
├── catalog/        ← CATALOG: structured entity records (Obsidian Bases)
│   papers · people · organizations · venues · datasets · repositories
├── notes/          ← NOTES: prose (Zettelkasten)
│   fleeting/ · sources/ · claims/ 🔒 · hubs/ 🔒 · indexes/
├── projects/       ← PROJECTS: work artifacts, project-scoped
├── inbox/          ← INBOX: agent→human messages — candidate · gap · flag · alert · work-prompt cards
├── spaces/         ← SPACES: persistent Obsidian dashboard notes for the four working modes
├── system/         ← SYSTEM: visible infrastructure — logs · templates · patterns · dashboards · board
├── .obsidian/      ← hidden Obsidian app config (Bases definitions, layouts)
└── .memoria/       ← hidden runtime (MCP, profiles, schemas, golden copy)
```

**One folder never mixes two categories**, and folders are named for their *content*, not for a doer — both the ingest operation and the Librarian agent operate *on* `catalog/`. The type → folder-home map is machine-read (`.memoria/schemas/folders.yaml`) and is the single source for the Linter, the policy gate, the installer skeleton, and the tests.

## Types and their homes

Each category houses a fixed set of types — Catalog entity records, the prose Notes (fleeting, source, claim 🔒, hub 🔒), project work artifacts, Inbox cards, Space notes, and System infrastructure. The architectural distinction is the trust posture each carries: Catalog frontmatter is **given facts** built by ingest and **not gated** (one escape valve — low-confidence extraction routes to a `flag`, [ADR-56](../../adr/56-extraction-uncertainty-flag.md)), while the claim and hub are the PI's **judgment**. The full type roster and its folder homes are in [Document types](../../reference/document-types.md).

## Gated zones

The review-gated zones 🔒 are structurally protected: no agent writes there without the PI's approval, enforced by the policy MCP. Agents *propose* (cards, staging artifacts); the PI *disposes*. The Catalog is deliberately ungated: its content is given facts, not judgment. Which prefixes are gated is owned by [Document types](../../reference/document-types.md).

## Archived is a state, not a folder

Everything the PI sees uses one lifecycle chain ([ADR-50](../../adr/50-universal-lifecycle-and-maturity.md), enumerated in [Frontmatter fields](../../reference/frontmatter.md)), each type using a subset. The architectural point is that a state change is a frontmatter edit, never a file move: an archived note stays in its type-home and drops from active views, preserving links and provenance. There is no archive folder. Likewise `links:` on notes are authored connections the PI confirms, while `relationships` on entities are given facts built by ingest ([ADR-52](../../adr/52-links-vs-relationships.md)) — two kinds of connection, two trust models; their field contract is in [Frontmatter fields](../../reference/frontmatter.md).

## Bases is the view layer; the Linter keeps it sound

Catalog entities (and the Inbox board, and the per-type note queues) surface through **Obsidian Bases** — saved database views over frontmatter. Every row is a file; the records are the source of truth; nothing reads a Base as data ([ADR-49](../../adr/49-catalog-in-bases-linter-monitor.md)).

Bases has no integrity guarantees — no schema, no constraints. That gap is the **Linter operation's** job: it validates every record against its type schema in `.memoria/schemas/` (required fields, value types, enum vocabularies, `links:`/`relationships` resolving to real targets) and flags drift as Inbox `flag`s. It is a **monitor and a commit gate**: a pre-commit `schema-check` gates git-tracked writes at commit, and the cron/CI sweep monitors between commits. It does not block a live in-app edit — between a bad edit and the next sweep a Base can briefly serve a malformed record; that window is accepted under the solo premise and bounded by the commit gate. On detected drift in system files, the Linter can restore from the golden copy ([ADR-55](../../adr/55-src-scaffold-populate-golden-copy.md)).

---

## Related

- The full stack the vault sits under: [Architecture](README.md)
- The agent→human signal folder in depth: [ADR-51](../../adr/51-inbox-category-and-honesty-card.md)
- The operations that maintain the vault: [Operations](../operations/README.md)
- Why the review gate is structural: [Why the review gate is structural](../rationale/why-human-gate.md)


---

<!-- source: explanation/architecture/memory-model.md -->

# The memory model

"Memory" in Memoria is not one thing: it's seven distinct stores — **substrates** — each with its own scope, owner, and lifespan. Knowing which substrate a fact lives in is what keeps one lane's reasoning out of another's, and durable knowledge out of size-capped session stores. Confusing the scopes is the source of most "the agent forgot" and "the agent remembered something it shouldn't" problems.

They're grouped below by how much **you** touch them — the ones you steer and read first, the ones the runtime manages on its own last.

---

## The ones you steer and read

**Program memory** (your standing steering — `research-focus` discovery priorities + `screening-protocol` review mode), **project memory** (one sub-project's cross-lane working state — open questions, decisions, framing), and **audit memory** (the tamper-evident record of every gated write, append-only forever per [ADR-25](../../adr/25-session-logging-two-logs.md)).

## The ones the runtime manages

**Handoff memory** (what travels with a card between lanes), **agent memory** (the Co-PI's `MEMORY.md` + `USER.md`, the **sole memory carrier** — the background lanes are stateless), **session history**, and **working memory** (the live session's reasoning).

What each substrate holds, its scope and lifespan, and where it is stored is tabulated in [Memory substrates](../../reference/memory.md); the rest of this page explains *why* each has the scope it does.

`SOUL.md` is adjacent but is *not* memory — it's an agent's identity prompt (its posture), stable across sessions by design.

**Why the Co-PI alone carries memory.** Concentrating every conversation in one agent is what lets Hermes' self-improving loop — **memory · /goals · skills** — compound into a genuine Co-PI rather than fragmenting across lanes that never converse ([ADR-48](../../adr/48-copi-and-agent-consolidation.md)). The background lanes (Librarian, Writer, Peer-reviewer, Engineer) are stateless propose-then-dispose executors: each run grounds on the card's handoff payload and the vault, never on remembered context.

---

## Why each substrate has its scope

The scoping isn't arbitrary — it follows from what each substrate holds, and the cost of getting it wrong.

**Program memory** is program-wide and persistent because it's the standing strategy you set for the whole research effort — what to pursue (`research-focus`) and how to screen (`screening-protocol`). Every agent that touches the program reads it; you refresh it on your own cadence. It never archives, because the program outlives any one sub-project.

**Project memory** is scoped to a single sub-project and archives with it. A project in `projects/<project>/` is a bounded, transient effort; its open questions and decisions are working state that matters while the project is live and becomes provenance once it ships. Keeping it separate from program memory holds "what I want pursued overall" apart from "where this one project's thinking is" — different scope, different lifespan.

**Audit memory** is append-only because its value is the complete, unmodified record. Agents read it; the Policy MCP writes an entry at every gated write. The constraint is enforced, not advisory — every gated write is hash-paired so it can be reversed and tamper is detectable; that mechanism is owned by [Policy MCP](../../reference/policy-mcp.md), and audit memory is the immutable substrate it writes to. Capture must start from day one, because the cost and human-loop trends it tracks can't be reconstructed retroactively.

**Handoff memory** is per-card rather than per-agent because the handoff is the unit of cross-lane communication. When a card moves from the Librarian lane to the Writer lane, the payload travels with it; the Writer inherits the structured handoff, never the Librarian's session context. That's what makes cross-lane handoffs reliable without agents sharing session state.

**Agent memory** belongs to the Co-PI and is frozen at session start because it's injected as a snapshot into the system prompt. The token caps on `MEMORY.md` (~800) and `USER.md` (~500) are load-bearing: anything larger gets truncated. So it holds stable facts only — in-flight task state belongs in handoff memory, cross-project state in program or project memory.

**Session history** is the cross-session recall channel but carries no authority. It's searchable history — useful for "did we discuss X before?" — but it never gates promotion and is never authoritative over the vault. A session-history result that contradicts a vault note loses; the vault is ground truth.

**Working memory** is correctly session-scoped because it's the agent's active reasoning state. Sharing it across agents would bleed one lane's in-flight reasoning into another's. Discarding it on `/clear` costs nothing — anything worth keeping must be written to a durable substrate.

---

## Why the split matters

This is thin-control-over-thick-state applied to memory. The Hermes-native substrates are deliberately thin — bounded working memory, capped agent notes, on-demand session history — so an agent carries minimal persistent state. The durable, compounding knowledge lives in thick files: the board's handoff payloads while work is in flight, and the vault while it's settled.

The vault side then splits by *purpose and lifespan*: **program memory** is your standing steering (persistent, program-wide); **project memory** is one effort's working state (bounded, archives with the project); **audit memory** is the immutable record of what happened. Collapsing program and project into one bucket — as the model originally did — hid that a program-wide steering file and per-project scratch are different kinds of memory, on different scopes and lifespans ([ADR-23](../../adr/23-scoped-memory-substrates.md)).

Without the split, every cross-session question collapses into "store it and hope," and agents either share too much (leaking context between lanes) or too little (re-deriving the goal every session). The substrates make "where does X live?" answerable by scope and lifespan.

---

## Configuration is not memory

A frequent miscategorization is storing a *fact* in a *config* file, or a *rule* in a memory substrate. The seven substrates hold state the system produces and reads back as **recall**; configuration is input you author that the agent reads as **rules**. Keep them distinct:

| If the thing is… | It belongs in… | Not in… |
| --- | --- | --- |
| A durable fact or convention the agent should recall | Agent `MEMORY.md` | `project-hints.yaml` (that's config, not recall) |
| Your working style or preferences | Agent `USER.md` | `MEMORY.md` (keep identity vs. preference separate) |
| What you want the system to pursue | Program memory (`research-focus`) | `project-hints.yaml` |
| Which topics map to which project | `.memoria/project-hints.yaml` (config) | a memory substrate |
| A synthesized claim or finding | Vault notes (`notes/claims/`) | any memory substrate |

The test: **memory is read back as recall; configuration is read as rules.** "Topics `jitai`, `mhealth` belong to the scoping-review project" is a rule (config → [Configure project hints](../../how-to-guides/setup/configure-project-hints.md)); "the user prefers British spelling" is recall (agent memory).

---

## Related

**Explanation**

- Board handoff payload (handoff memory travels here): [The honesty card](../kanban-board/card-schema.md)
- Architecture overview: [Architecture](README.md)

**How-to**

- Configuring project hints (the config example above): [Configure project hints](../../how-to-guides/setup/configure-project-hints.md)

**Reference**

- Audit log format: [Policy MCP](../../reference/policy-mcp.md)
- The substrate table as reference: [Memory substrates](../../reference/memory.md)

**Background**

- Hermes native memory: [hermes-agent.nousresearch.com/docs/user-guide/features/memory](https://hermes-agent.nousresearch.com/docs/user-guide/features/memory)


---

<!-- source: explanation/architecture/control-plane.md -->

# The control plane

Every unit of **agent** work is a card on the kanban board — the Tasks layer of the [seven-layer stack](README.md). A trigger (the PI, the Co-PI — Memoria's single conversational agent — or cron) creates a card; the dispatcher assigns it to a **lane** (a background worker on the board — see [Glossary](../../reference/glossary.md)); the lane's agent runs it under propose-not-dispose — agents propose, only the PI disposes, a wall the policy MCP enforces ([Why the review gate is structural](../rationale/why-human-gate.md)); the result resurfaces as an Inbox signal (a proposal card in your queue). Engines run *off* the board — on cron/CI or behind an MCP facade, never as cards.

---

## Lanes are the four background agents

The board's lanes are exactly the four background agents, keyed by `assignee = memoria-<name>` — the roster and postures (each agent's fixed stance, e.g. faithful or skeptical) are owned by [Profiles](../profiles/README.md). Two lanes that might seem missing are absent by design:

- **No Co-PI lane.** The Co-PI converses in the Agent Client pane and never appears on the board. It is read-only — when the conversation produces work that writes, the Co-PI **delegates** it: the tasks MCP's `delegate_route_task` creates a card on the board, assigned to the right lane. Delegation through the board is the Co-PI's *only* write path.
- **No operation lanes.** Operations are deterministic and have no posture; they run on cron/CI or are invoked directly, never claimed as cards — the roster is in [Operations — the deterministic layer](../operations/README.md).

## Hidden mechanic vs PI-facing state

The board carries two distinct state axes, and the split is the point: the board's native execution `status` is the **hidden mechanic** the PI never sees, while the PI-facing state of any card is the universal lifecycle chain ([ADR-50](../../adr/50-universal-lifecycle-and-maturity.md)) — a card awaiting you is `proposed`, you act and it moves on, and closed cards are `archived`. The status enum is owned by the [Kanban board reference](../../reference/kanban-board.md); the lifecycle chain by [Frontmatter fields](../../reference/frontmatter.md).

Three orthogonal dimensions keep an agent verdict from rubber-stamping a human decision: execution `status`, the lifecycle state (the PI's decision), and `agent_recommendation` (a soft verdict, never a gate). Rejection spawns a new card rather than reopening the old one, mirroring claim supersession — each card is one attempt, so the audit trail cannot lie ([Kanban board reference](../../reference/kanban-board.md)).

## The handoff payload and ceiling-narrowing

A card's handoff payload is self-contained: the receiving lane inherits the structured payload (its field contract is in the [Kanban board reference](../../reference/kanban-board.md)), never the sender's session context — that is what makes handoffs reliable without agents sharing state.

`allowed_paths` may **narrow** but never **widen** the lane's write scope: the lane is the ceiling, the payload is the floor, and the policy MCP enforces both. A delegated task can be more constrained than its lane, never less.

**WIP limits** apply back-pressure on the human bottleneck, capping the review queue and running cards per lane ([Kanban board reference](../../reference/kanban-board.md)).

---

## Related

- The lanes' postures and boundaries: [Profiles](../profiles/README.md)
- The board state machine in detail: [Kanban board](../kanban-board/README.md)
- The signal end of the loop: [ADR-51](../../adr/51-inbox-category-and-honesty-card.md)
- What the policy boundary enforces: [Policy MCP](../../reference/policy-mcp.md)


---

<!-- source: explanation/architecture/human-channels.md -->

# Interaction channels

Memoria's primary UI is Obsidian — and within it, the **Inbox** is the one place agents speak to the PI: candidate, gap, flag, alert, and work-prompt cards ([ADR-51](../../adr/51-inbox-category-and-honesty-card.md)) feeding the Inbox queue's "Needs me" view ([ADR-81](../../adr/81-persistent-gate-dashboards.md)). Beyond Obsidian are two secondary channels for reaching the system when it isn't the right place — the CLI (precise, occasional, forensic) and Telegram (mobile, async) — plus one non-human integration path, the API server, which programs use and humans never touch directly.

The organizing principle: **each channel owns one mode.** Using one for another's job produces slow erosion — daily operations done via CLI compound into friction that eventually stops the behavior; push notifications wired for the wrong events train the human to ignore them all.

| Channel | Mode | Purpose |
| --- | --- | --- |
| **Obsidian** | Desktop, focused, deliberate | Daily triage (the Inbox), reading, authoring, the Co-PI conversation in the Agent Client pane |
| **CLI** (`hermes …`) | Desktop, occasional, precise | Forensic queries, profile administration, manual dispatch, backup |
| **Telegram** | Mobile, async, lightweight | Urgent push notifications today; mobile capture is planned work |

The three rows above are the human channels. The API server (port 8642) is listed separately below because it is *not* a human-operated channel — it is a programmatic integration surface that programs use and humans never operate directly:

| Integration surface | Mode | Purpose |
| --- | --- | --- |
| **API server** (port 8642) | Programmatic, integration (not human-operated) | File-system watchers, Zotero hooks, git post-commit hooks, cross-machine dispatch |

---

## Why the CLI is for rare, precise operations

A UI exists for frequent operations. A CLI is invisible until needed, and then exactly the right shape — it surfaces complete state (retry count, blocker reason, audit slices) without the constraints of a dashboard layout.

The CLI's role is forensic and administrative: card inspection, lane health checks, audit trail queries, manual dispatch outside the normal trigger flow, profile administration, and backup operations. These are all low-frequency and high-precision — exactly the profile where a CLI excels over a UI.

The diagnostic the CLI is uniquely suited for is "why did this happen" rather than "what should I do next." The dashboards answer the second question; the CLI is for the first.

The signal that a CLI operation is being used too often is that the operation belongs somewhere else. Daily approvals done at the terminal mean the dashboard approval path is missing or broken. Frequent manual dispatch means a trigger should be automated. CLI frequency is a smell, not a workflow.

For command syntax and available operations, see [Hermes CLI](../../reference/hermes-cli.md).

---

## Graded loudness — how a signal picks its surface

Every agent and operation finding carries one of four loudness levels, and the level decides where it surfaces:

| Level | Outcome |
| --- | --- |
| **Quiet** | logged only; no push |
| **Notice** | appears in the relevant dashboard + weekly review; no push |
| **Alert** | appears in Home / the Inbox's "Needs me" queue and sends Telegram push when configured |
| **Block** | appears in Home, sends Telegram push when configured, and pauses new delegation plus review-gated promotion until acknowledged |

The test for push vs dashboard routing: *does it change what the PI does in the next 30 minutes?* Only Alert and Block should ever reach a push channel; everything else waits in the Inbox and dashboards. This is what keeps the push channel trustworthy — when Telegram buzzes, it matters.

---

## Why Telegram stays narrow

Telegram has two tempting jobs that are easy to conflate: push notification for
urgent signals, and lightweight mobile capture. Only urgent push is shipped
today; inbound mobile capture remains planned work ([#382](https://github.com/eranroseman/memoria-vault/issues/382)).

The push notification mode carries the **Alert** and **Block** levels only — hard blockers, time-sensitive completions, high-severity drift alarms, cron failures. Wiring Telegram for per-card events or routine approvals teaches the human to ignore Telegram notifications — including the ones that actually matter.

The planned mobile capture mode takes advantage of the phone's always-accessible nature: capture fleeting thoughts, queue URLs for ingest, or quick corpus lookups while in motion. The key constraint is that the Telegram toolset stays narrower than the CLI or desktop — mobile is for thinking and capture, not for code execution, web search, or programmatic operations that have desktop footguns.

Confining Telegram to one messaging channel is also intentional. Each additional channel — Discord, Slack, WhatsApp — competes for attention and demands its own notification discipline. Until there is a concrete need that Telegram cannot serve, additional channels add noise without value.

---

## Why the API server is for programs only

The API server (port 8642) is the one-row integration surface in the table above: programs connect through it (file-system watchers, Zotero hooks, git post-commit hooks, cross-machine dispatch) while humans use the command palette and CLI instead. It is a different door, not a different key — every API write still passes through the policy MCP at the calling profile's permissions. The full rationale is in [Why Hermes](../rationale/why-hermes.md).

---

## Related

- Obsidian UI components: [Obsidian workspaces](../../reference/obsidian-workspaces.md)
- CLI commands: [Hermes CLI](../../reference/hermes-cli.md)
- Policy MCP (what API calls go through): [Policy MCP](../../reference/policy-mcp.md)


---

<!-- source: explanation/architecture/session-logging.md -->

# Session logging

Session logging is a system mechanism, not a workflow. The policy MCP records every gated write to an audit log that Git preserves — there is no card, nothing to claim, and no state transition. It runs underneath the card-driven workflows rather than being one of them.

A second, per-session log — a deterministic digest the Linter writes from the audit trail — accumulates alongside it under `system/logs/sessions/`. This page explains the two-log design and why they stay separate.

---

## Two logs in `system/logs/`

These are different artifacts written by different components with different lifecycles. Don't conflate them.

| Log | Path | Writer | Lifecycle |
| --- | --- | --- | --- |
| **Policy MCP audit log** | `system/logs/audit.jsonl` | Policy MCP | Append-only **forever** — never rotated ([ADR-25](../../adr/25-session-logging-two-logs.md)); growth is surfaced by the Linter's `audit-log-size` advisory (50 MB) |
| **Per-session summaries** | `system/logs/sessions/YYYY-MM-DD-HHMM.jsonl` | Linter (`operations/integrity/linter/session_summary.py`, daily cron) | One file per session; never rotated; accumulate indefinitely |

The audit log is what the audit-log and fleet-health [dashboards](../dashboards/README.md) read. The per-session summaries are **deterministic digests** of what happened in a session — the Linter is zero-LLM, so the digest is derived from the audit trail, not narrated: a header (task, profiles, start/end, counts by action and decision) plus one record per touched path (actions, final decision, final `after_hash`). The writer is idempotent (a digested session is never rewritten) and only digests sessions quiet for 24 h, so in-flight work is never summarized early.

---

## Why the two-log separation

The audit log answers "did this write happen and was it authorized?" — it is forensic and append-only. Because each write is hash-paired (the mechanism is owned by [Policy MCP](../../reference/policy-mcp.md)), a write can be reversed and an edit made outside the trail is detectable; the Linter closes the loop over this log with its `audit-unpaired-writes` and `vault-hash-drift` detectors (a legitimate human edit in Obsidian surfaces on the latter too, by design — see [Operations](../operations/README.md)). Per-session summaries answer "what did the session accomplish?" — they are per-session digests.

Combining them would make the audit log verbose (session detail) and would make session summaries harder to query (mixed with per-write events). Each log has a different reader: the audit log feeds dashboards and tamper detection; session summaries are for the PI reviewing what happened. The decision is [ADR-25](../../adr/25-session-logging-two-logs.md).

---

## Multi-machine safety

Per-session files are named by `YYYY-MM-DD-HHMM`, so files from different machines don't collide during sync. Each machine writes its own session files; the vault accumulates them from all machines without conflict.

---

## Related

- The Linter operation (reads `system/logs/`; runs the integrity checks; writes the session digests): [Operations](../operations/README.md)
- Session-log granularity (per-session files, not per-action): [Memory substrates](../../reference/memory.md)
- Audit log (the other log): [Policy MCP](../../reference/policy-mcp.md)


---

<!-- source: explanation/architecture/telemetry-architecture.md -->

# Telemetry architecture

This page explains *why* Memoria records what it records, and how the pieces divide
into three planes with different rules. It is the design rationale behind
[ADR-104 (telemetry three planes)](../../adr/104-telemetry-three-planes.md),
[ADR-105 (diagnostic plane)](../../adr/105-diagnostic-plane.md), and
[ADR-106 (cost and disposition capture)](../../adr/106-cost-and-disposition-capture.md).
For the exact on-disk schemas, see [Telemetry log schemas](../../reference/telemetry-logs.md);
for the audit log specifically, [Session logging](session-logging.md).

---

## Start from the questions

Telemetry exists to answer questions, and Memoria's questions fall into three groups
that pull in opposite directions:

| Plane | The question it answers | Reader | Defining requirement |
| --- | --- | --- | --- |
| **Audit** | Did this write happen, and was it authorized? | Tamper detection, dashboards, the PI | Forensic permanence, integrity |
| **Analytics** | How is the system performing — cost, throughput, my attention, decision quality? | Dashboards, the publication benchmark | Content-free, reproducible from events |
| **Diagnostic** | Why did Memoria's own code break? | The developer (the PI, debugging) | Detail now, disposable later, private |

These are not three flavors of one log. Forensic permanence wants append-only-forever;
diagnostics want rotate-and-discard. Analytics must stay content-free so it is safe to
keep and to publish; diagnostics need content to be useful. Forcing them onto one
substrate applies the strictest rule to everything and still leaves debugging unserved —
which is exactly the state Memoria was in, with a strong audit trail, a content-free
analytics family, and **no diagnostic plane at all** (failures left only a stderr print).

---

## The three planes

### Audit — forensic, integrity via Git

The audit plane is `audit.jsonl` plus its deterministic per-session digest projection
([ADR-25](../../adr/25-session-logging-two-logs.md)). It is content-free, append-only,
and records a SHA-256 before/after hash for every gated write, so a write can be reversed
and an out-of-band edit is detectable.

Its integrity substrate is **Git, not in-file cryptography.** The vault is already a Git
repository: commit history is a Merkle chain, a remote the researcher does not solely
control is a real second trust domain, and signed commits add authorship. So Memoria does
**not** add a per-entry hash chain. A linear `prev_hash` chain would *fork* the moment a
second machine appends across a sync, and anyone who owns the file can recompute it — it
adds complexity without a guarantee Git does not already provide, better. Per-write hash
pairing stays (it pins content state at finer grain than a commit). External cryptographic
anchoring (OpenTimestamps, RFC-3161) is deferred: under
[single-researcher scope](../../adr/24-single-researcher-scope.md) there is no distinct
adversary to anchor against, so it would be theater until a second party or a compliance
driver makes it real.

The honest framing: tamper-evidence here is **detective, not preventive**, and only as
strong as "a remote you do not solely control, plus you do not force-push history." Where
that remote lives (self-hosted vs. hosted) is the lever for how much activity-cadence
metadata — content-free, but it reveals *when* you work — leaves the machine.

### Analytics — content-free events, metrics as projections

The analytics plane is the operational and publication signals: board state and
transitions, disposition, cost, attention, triage, linkage, lint findings. Two principles
govern it:

- **Content-free.** Hashes, IDs, counts, enums, and durations only — never note content.
  This is what makes the plane safe to keep forever and to publish as the
  [ADR-20](../../adr/20-publication-path.md) benchmark.
- **Events are the source of truth; metrics are projections.** The lane-metric notes, the
  trust-score, and the eval trends are pure, reproducible functions over the event stream —
  never a second store. A formula change re-runs over history instead of going dark until
  new data accumulates.

It is a small set of streams grouped by writer and cadence — not one merged firehose (which
would make every reader filter and let one corrupt line poison everything) and not a file
per metric.

Two of these signals — **cost/tokens** and **disposition** — are captured at different
control points. Cost and token counts come from the per-profile Hermes session store,
joined to board cards by worker session id. Disposition is a human decision captured
at the review action, not an inference event. [ADR-106](../../adr/106-cost-and-disposition-capture.md)
records the design.

### Diagnostic — the operability plane, scoped honestly

The diagnostic plane closes the real gap: when a Memoria MCP server, ingest run, or cron
fails, there must be a persisted, queryable record. It is new, and it is the one plane that
introduces risk, so its contract ([ADR-105](../../adr/105-diagnostic-plane.md)) is strict:

- **Memoria's own Python MCP and Operations only.** Agent reasoning, prompts, and retries
  live inside the external unmodified Hermes runtime
  ([ADR-22](../../adr/22-build-on-hermes-runtime.md)) and the MCP-only sandbox
  ([ADR-46](../../adr/46-seven-layer-architecture.md)) — unreachable. The plane diagnoses
  Memoria-side failures, not whole-system behavior, and does not pretend otherwise.
- **Outside the vault, outside Git.** It lives under an OS state directory, never in the
  Git-tracked, sync-tracked vault — so a forgotten flag plus a `git push` cannot exfiltrate
  it.
- **Content-light by default.** Typed error codes plus a hash + length of any payload, never
  the payload itself; paths and titles are treated as content in anything shareable. Raw
  payloads need a deliberate, ephemeral, self-disarming capture — there is no standing
  "log content" toggle.
- **Rotated and disposable**, errors-and-warnings by default with per-component levels,
  bounded footprint.
- **No remote telemetry.** Sharing is a user-triggered, human-reviewable, redaction-tested
  bundle — never automatic.

---

## One spine, lightly

All three planes share a single event envelope (timestamp in UTC, schema version, plane,
event name, `machine`, `task_id` where a card exists) and a small emit helper per language —
not a heavyweight observability framework. There is deliberately **no** correlation-ID
propagated across processes: it cannot be threaded through the external Hermes runtime, and
at single-user local scale there is no service mesh to reconstruct. `task_id` is the join
key wherever a card exists.

---

## Multi-machine: partition, don't chain

Memoria is multi-machine single-user ([ADR-63](../../adr/63-multi-machine-deployment.md)):
the vault syncs by Git, exactly one dispatcher runs per vault, but the dispatching machine
changes over time. That sets a global invariant: **every Git-synced plane writes per-machine
files** — a `machine` stamp in the envelope and the filename — so two machines appending
across a sync never collide and Git merges stay conflict-free. This generalizes the
per-session-file naming already used for digests. The diagnostic plane is out of Git, so it
is per-machine by construction. This same property is *why* in-file hash-chaining is the
wrong integrity mechanism — a single linear chain has no conflict-free multi-writer form,
whereas Git merges do.

---

## Related

- Decisions: [ADR-104 (telemetry three planes)](../../adr/104-telemetry-three-planes.md),
  [ADR-105 (diagnostic plane)](../../adr/105-diagnostic-plane.md),
  [ADR-106 (cost and disposition capture)](../../adr/106-cost-and-disposition-capture.md)
- The audit plane in detail: [Session logging](session-logging.md)
- Exact schemas: [Telemetry log schemas](../../reference/telemetry-logs.md)
- The integrity threat model: [ADR-24 (single-researcher scope)](../../adr/24-single-researcher-scope.md)
- The sync substrate: [ADR-63 (multi-machine deployment)](../../adr/63-multi-machine-deployment.md)


---

<!-- source: explanation/knowledge/README.md -->

# The knowledge model

The vault stores durable knowledge organized type-first into category folders, with lifecycle carried as a frontmatter state. Understanding the knowledge model means understanding what makes knowledge _durable_, how the vault's organization serves that goal, and why certain moves are allowed and others aren't. Knowledge is the durable counterpart to transient _work_: work lives on the board as cards and dies at `archived`, while knowledge lives in the vault and persists — a distinction the board section develops in [Cards and notes are different things](../workflows/board-as-state-machine.md#cards-and-notes-are-different-things).

> **Lineage.** This section's core ideas — atomic notes, links over folders, maturing notes, and Maps of Content — descend directly from Luhmann's **Zettelkasten** method and its modern "evergreen notes" successors. Memoria's contribution is not the method but its _delegation_: agents do the Zettelkasten bookkeeping (linking, classifying, drift detection) the method demands while the human keeps the intellectual work. The full intellectual debt is traced in [Intellectual foundations](../overview/intellectual-foundations.md#luhmanns-zettelkasten); the pages below note where each specific idea is borrowed.

## Documents in this section

| Page                                                               | What it covers                                                                                                                           |
| ------------------------------------------------------------------ | ---------------------------------------------------------------------------------------------------------------------------------------- |
| [Document types and epistemic roles](document-types.md)                    | The three epistemic roles (source / synthesis / working) behind the document types, and why agent permissions follow from them.              |
| [The knowledge cycle](knowledge-cycle.md)                          | The progression from ingested source to written output, and why the vault compounds rather than merely accumulates.                      |
| [Your first month](your-first-month.md)                            | The tempo of that cycle over your first weeks of real use — when to capture, distill, produce, and review so the vault compounds, not rots. |
| [Note body structure](note-body-structure.md)                      | Why source notes, claim notes, and hubs have the body sections they do, and what each section makes the note able to do.                  |
| [Lifecycle, not topic — and state, not folders](lifecycle-over-topic.md) | Why folders encode a note's type rather than subject, why lifecycle is a frontmatter state rather than a folder, and how topics live in frontmatter and links instead. |
| [Why promotion is gated](promotion-model.md)                       | What promotion means, the one-way promotion map and its disallowed moves, and why the human gate sits at the synthesis boundary.         |
| [Vocabulary discipline](vocabulary-discipline.md)                  | Why the classification fields are kept separate, why vocabulary consolidation is deferred, and how term drift fails silently.            |
| [Common pitfalls](common-pitfalls.md)                              | The recurring failure modes of a vault built this way, and the automation-boundary principle underneath them.                            |
| [Why hubs](hubs-and-navigation.md)                                 | Why the link-first vault needs a human-curated navigation layer, and why hubs are authored, threshold-prompted, and review-gated.        |

For the complete document-type reference (fields, templates, lifecycle tables), see [Document types](../../reference/document-types.md).


---

<!-- source: explanation/knowledge/document-types.md -->

# Document types and epistemic roles

The vault's types are not arbitrary — each one answers a different question about who created the content, from whose perspective, and what status it has in the knowledge system. The deepest split is between the **Catalog** (structured entity records, built mechanically) and **Notes** (prose, written by someone). Understanding that split matters more than memorizing the type list.

---

## Entities vs notes: Luhmann's two boxes

The Catalog/Notes split revives Luhmann's two-box system: he kept a **bibliographic index** (who wrote what, where) physically separate from the **main slip-box** (his own thinking). Memoria does the same (see [Intellectual foundations](../overview/intellectual-foundations.md#luhmanns-zettelkasten)):

- **`catalog/` — entity records.** Structured facts about things in the world: a paper's DOI and authors, a person's ORCID, a venue's ISSN. Built by the **ingest operation** from metadata APIs, surfaced through Obsidian Bases, not review-gated — they are extractions of given facts, not judgments. Entities carry `relationships` (cited-by, authored-by, published-in): **given** connections the operation derives mechanically ([ADR-52](../../adr/52-links-vs-relationships.md)).
- **`notes/` — prose.** What a source says, what you think, how it all hangs together. Written by the PI or proposed by an agent. Notes carry `links:` — **authored** connections (supports, contradicts, hub membership) that an agent may propose but only the PI confirms.

"Relationships are given; links are authored." A connection between two entities is always a relationship; `links:` endpoints are always notes. Keeping the two boxes separate is what lets the mechanical half run ungated while the judgment half stays human.

---

## The six entity types

All in `catalog/`, all operation-built, all Base-backed: the bibliographic records — `paper`, `person`, `organization`, `venue`, `dataset`, `repository` — each keyed on stable IDs (a DOI, an ORCID, an ISSN) and carrying `relationships`. The exhaustive field lists live in [Document types](../../reference/document-types.md#catalog-entities-6).

An entity record never contains anyone's reading of the source — that is what a source *note* is for. The same paper is therefore two files: the `paper` entity (the bibliographic fact) and, if the PI reads it, a `source` note in `notes/sources/` that points back at the entity.

---

## The four note-document types

### Source notes: describing the world

A **`source`** note records what a source says — the brief, the key concepts, the limitations, the critique. It is written from an outside perspective: a source note never says what the PI thinks; it says what the source argues. That constraint is the mechanism that makes citation tracing work. If source notes expressed opinions, the boundary between "what the source says" and "what I think" would collapse, and provenance would become unverifiable.

A source note is one prose type regardless of whether the entity behind it is a paper, repository, dataset, report, or other source. Identification lives on the Catalog entity; the prose record stays focused on what the source says.

### Claim notes: the synthesis atom

A **`claim`** is one durable assertion in the PI's own words, linked to the sources that support it. It is the most important document type and the one that distinguishes a research vault from a document store. A vault full of source notes is a bibliography with annotations; a vault with interlinked claims is a knowledge graph the PI can write from.

Claims live in `notes/claims/` — a **review-gated zone** (🔒): agents draft claim *stubs* into staging, but the canonical claim is human-made. The discipline is atomicity — one claim per note, Luhmann's one-idea-per-slip rule — because wikilinks citing a multi-claim note are ambiguous, and a multi-claim note cannot be cleanly superseded when evidence changes. The test: if the title contains an "and" doing real conceptual work, it is two notes.

Claims carry `maturity` — a soft, PI-set signal of how *developed* the claim is, never a gate: a `seedling` claim is fully `current` ([ADR-50](../../adr/50-universal-lifecycle-and-maturity.md)). The values and the "signal, not a gate" rule are owned by [Why promotion is gated](promotion-model.md); the field is defined in [Frontmatter fields](../../reference/frontmatter.md).

### Hubs: authored navigation

A **`hub`** is a curated, annotated view of an area: what it is about, what matters most in it, and where it needs work. Hubs live in `notes/hubs/` — also gated 🔒, because a hub is an act of judgment about what belongs together, not a query result. Agents can propose additions; the PI curates.

### Fleeting notes

A **fleeting note** (`type: fleeting`) is raw capture — a thought, a URL, a quote — recorded before deciding what to do with it (`origin:` records whether a human or an agent wrote it). Fleeting notes are either distilled or archived; they don't persist as knowledge. Registers are Bases views, not a note type.

---

## The five card types

The **Inbox** (`inbox/`) is the agent→human message category — the signal end of every background loop ([ADR-51](../../adr/51-inbox-category-and-honesty-card.md)). Its five types are *transient cards*, not knowledge, and they sort into three shapes by epistemic role: **proposals** to judge (`candidate`, `gap`), **verification cards** to adjudicate (`flag`, `alert`), and a **work prompt** for work waiting on the PI (`work-prompt`). The exhaustive list — required fields, who raises each — lives in [Document types](../../reference/document-types.md#inbox-cards-5).

A card awaiting you is simply in the `proposed` state — there is no separate `review-request` type. Cards carry the honesty-card fields rather than verdicts; see [The honesty card](../kanban-board/card-schema.md).

---

## Why the distinctions matter

**Provenance.** If a source note could contain the PI's claims, "what does this paper say?" gets mixed with "what do I think about it?", and the Peer-reviewer cannot trace citations in a draft back to what sources actually said.

**Agent permissions.** The boundary follows the epistemic roles: agents (and the ingest operation) build entity records and propose source-note material, but `notes/claims/` and `notes/hubs/` are gated — recording what a source says is bookkeeping; asserting the PI's synthesis is not delegable.

**Lifecycle subsets.** Every type uses a subset of the one universal lifecycle chain, declared in its schema file under `.memoria/schemas/types/`; the chain and its values are defined in [Frontmatter fields](../../reference/frontmatter.md). The subset encodes the epistemic shape: entities are born `current` (facts don't await approval); source notes start `proposed` (awaiting reading); claims exist only once the PI makes them `current`.

---

## Related

- Why folders carry the type and frontmatter carries the state: [Lifecycle, not topic — and state, not folders](lifecycle-over-topic.md)
- How material crosses the review gate: [Why promotion is gated](promotion-model.md)
- The *how* of note bodies: [Note body structure](note-body-structure.md)
- The card format in depth: [The honesty card](../kanban-board/card-schema.md)
- Complete type reference (fields, templates): [Document types](../../reference/document-types.md)


---

<!-- source: explanation/knowledge/knowledge-cycle.md -->

# The knowledge cycle

Every note in the vault is somewhere in a long-term progression from catalogued source to written output. Understanding the cycle as a whole — what it is for, where it gets stuck, and what makes it compound — is the conceptual foundation for understanding why the vault is structured the way it is.

## The six delegable tasks

The PI works at the three spaces — **Library**, **Knowledge**, and **Project** — not along a pipeline, plus the **Inbox** queue. Library, Knowledge, and Project are where knowledge is taken in, built into claims, and turned into output; the Inbox queue is where the agents' proposals surface for a decision. Beneath the spaces, six tasks can be delegated to a background agent lane; each task's name is at once the action, the lane, and the Inbox signal it raises:

| Task        | What it does                                            | Inbox signal    |
| ----------- | ------------------------------------------------------- | --------------- |
| **catalog** | find and record a source (entity record + candidate)    | `candidate`     |
| **extract** | distill a kept source toward claim stubs                | (work prompt)   |
| **link**    | propose connections between claims                      | (link proposal) |
| **map**     | scope a corpus — coverage, clusters, writability        | `gap`           |
| **draft**   | generate proposed prose with bound citations            | —               |
| **verify**  | check citations, trace claims, red-team the argument    | `flag`          |

The tasks are **individually triggered, not a set**. A human gate — often a long gap — sits between each: a source is catalogued; much later, if ever, extracted; only after a claim exists does linking fire. The four Librarian tasks (catalog, extract, link, map) belong to the Librarian posture, draft to the Writer, and verify to the Peer-reviewer; the authoritative task-lane → profile map lives in [Profile capabilities](../../reference/profiles.md). All six are reachable from the spaces via the command palette.

A new source typically arrives as a `candidate` card, is kept at triage, and becomes a Catalog entity plus a `proposed` source note. The PI reads it, distills claims in their own words, and confirms the links that connect them into the graph. Those claims mature and cross-link; once enough accumulate, a project maps the corpus, drafts, verifies, and ships.

**The loop that compounds:** gaps found in _map_ and _verify_ raise Inbox `gap` cards that re-trigger _catalog_. The output end of the cycle feeds the intake end — what you write exposes what you're missing, and what you catalog next is shaped by what you tried to write.

## Why the cycle is not a linear path

The cycle describes the intended direction of flow, not a timeline or a required sequence. A claim can remain at `maturity: seedling` for months — that is normal, not broken. A source note can sit `current` for a year before there is enough surrounding context to extract claims from it. A new paper may arrive and retroactively change what an older claim was arguing.

What the cycle prevents is the two failure modes at opposite ends: notes that are captured but never synthesized (the vault grows but never compounds), and claims that are synthesized but never written from (the knowledge accumulates but never produces output). The cycle's shape names these as distinct failure modes because they look identical from the outside — both appear as an active vault — but indicate different structural problems.

## Why the vault compounds rather than accumulates

The distinction between a vault that compounds and one that merely accumulates is in the density of the claim layer. A vault with 500 catalog entities and 10 claims is a sophisticated reading list — useful for finding sources but not for writing from. A vault with 50 source notes and 40 claims that link to each other and to hubs is a structure the PI can write from directly, navigating the graph of connected ideas rather than remembering what they read.

A new source's value is not the text it contains but what it contributes to existing claims — the connections it makes explicit, the contradictions it names, the open questions it opens or closes. Compounding-through-connection is the **Zettelkasten** wager — that a densely linked note collection becomes a thinking partner rather than a filing cabinet. The claim density that separates a compounding vault from an accumulating one is the same density Luhmann's slip-box depended on (see [Intellectual foundations](../overview/intellectual-foundations.md#luhmanns-zettelkasten)).

## Where the cycle gets stuck

The Inbox and space dashboards surface exactly where work has stopped. Sources awaiting reading and distillation surface in the Library reading pipeline. Unconnected claims surface in Knowledge's Open questions view; low-stakes structural debt surfaces in Maintenance's Loose ends view. Open verification findings surface as `flag`/`alert` cards on the board. The correspondence between stuck points and views is not accidental — they were designed to make the cycle's failure modes visible before they compound.

The one transition the dashboards cannot surface is when developed claims are never assembled into a draft — that gap is a judgment call, not a structural signal. It is also the hardest gap to notice, because a vault full of well-developed claims looks healthy even when nothing is being written. (The _map_ task's writability and readiness reports exist to prompt exactly this.)

## Why archiving preserves the cycle's integrity

Notes that are no longer useful do not become invisible by deletion — they become gaps in the provenance graph. A deleted source note breaks every claim that cited it; a deleted claim leaves later notes without their grounding.

Archiving preserves the chain, and since `archived` became a **state rather than a folder** ([ADR-50](../../adr/50-universal-lifecycle-and-maturity.md)), it costs nothing structurally: the note stays in its type-home, remains readable and in Git history, drops out of active views and the agents' working scope, and can still be traced from any note that linked to it. No file moves, so no links break. The cycle's integrity depends on every step being traceable backward, not just forward. Archiving itself is propose-only for every actor but the PI.

## Related

**Explanation**

- The ritual that keeps the cycle from stalling: [Run the weekly review](../../how-to-guides/inbox/run-the-weekly-review.md)
- The cycle's tempo over your first weeks of real use: [Your first month](your-first-month.md)
- The epistemic roles of document types: [Document types and epistemic roles](document-types.md)
- Why promotion is gated: [Why promotion is gated](promotion-model.md)
- The folder structure the cycle flows through: [The vault](../architecture/vault.md)

**How-to**

- The weekly maintenance pass: [Run the weekly review](../../how-to-guides/inbox/run-the-weekly-review.md)
- The cycle's key transition: [Write a claim note](../../how-to-guides/knowledge/write-a-claim-note.md)


---

<!-- source: explanation/knowledge/note-body-structure.md -->

# Note body structure

The three most important prose types — source notes, claim notes, and hubs — have distinct body structures because they answer different questions and serve different epistemic purposes. Understanding why each section exists helps explain what makes a note function as knowledge rather than as accumulated text.

For the frontmatter fields, templates, and field-by-field reference, see [Document types](../../reference/document-types.md).

---

## Why source notes are split between machine and human

A source's record has two authorship layers, and the split between them is intentional, not a convenience.

The mechanical layer is the **paper entity** in `catalog/`: the ingest operation populates the bibliographic facts and the `relationships` (cites, cited-by, authored-by, published-in) at intake. These are derivable from the source's metadata and the existing corpus without reading comprehension — structural facts about the source's place in the graph, produced deterministically and cheaply. The Librarian adds the two LLM pieces — a comparative brief and a draft classification — as proposals.

The human layer is the **source note** in `notes/sources/`: the Summary, the Critique, and the Open questions. These require reading comprehension and judgment. The Summary in particular is load-bearing — it is what the PI reads six months later to cite the paper without re-reading it. A Summary that merely paraphrases the abstract has failed this purpose; it needs to capture the thesis, the key findings that will actually be cited, and the paper's relevance to the specific research direction.

The Critique section is where a source note earns its place in a knowledge system rather than a bibliography. A source note without critical engagement — what is missing, what is methodologically weak, what you would push back on — is storage, not synthesis. The Open questions section completes the loop by recording what the source raises but doesn't answer, feeding the synthesis agenda.

---

## Why claim notes have a required Links section

The three required sections of a claim note correspond to three epistemic commitments.

The `## Claim` section states the single durable idea. Atomicity is the constraint here — one claim per note, not one topic. The discipline matters because wikilinks citing a multi-claim note become ambiguous: does the link support claim A or claim B? And when evidence changes, which part of the note gets superseded?

The `## Evidence and argument` section is what distinguishes a claim from an assertion. A claim with no evidence is an opinion. A claim with citekeys pointing to supporting sources is an argument that can be verified, updated, and superseded as evidence accumulates.

The `## Links` section is the most structurally significant. A claim with no `links:` to other claims has not made it into the knowledge graph — it exists in isolation, where it cannot compound. The `links:` here are *authored* connections (as distinct from the *given* `relationships` on entities — that distinction is explained in [Document types and epistemic roles](document-types.md)), and they are what make the vault a graph rather than a collection. A note that supports, contradicts, or extends another note has been integrated; one without links has not.

This is the **Zettelkasten** principle at the center of the method: a note's value comes from its links, not its contents — an unlinked note is, in Luhmann's terms, lost to the box. The required Links section makes that discipline structural rather than aspirational (see [Intellectual foundations](../overview/intellectual-foundations.md#luhmanns-zettelkasten)).

---

## Why hubs answer three distinct questions

A hub is not an index. The failure mode of a hub-as-index is that it becomes a flat list no one opens because a Base or Dataview query already does it faster. What a hub adds over a query is perspective: a framing of what a cluster is about, a curation of what matters most in it, and a diagnosis of where the cluster needs work.

The three questions a hub body should answer — what is this area about, what belongs here right now, and what needs review or synthesis — correspond to three distinct cognitive operations: framing, curating, and planning. A hub that only does the first two (framing and curating) is a static artifact. One that also does the third (diagnosing open questions and thin branches) is a living planning tool.

---

## How the body sections honor the epistemic separation

The body structures above only work if the underlying separation holds: a source note records what a source says from an external perspective, a claim records what the PI thinks in their own words, and a hub is a navigational surface rather than a synthesis destination. Why that separation exists, why mixing it breaks citation tracing, and why it lets agent permissions be cleanly scoped are developed in [Document types and epistemic roles](document-types.md).

Taking the separation as given, the body sections are what enforce it concretely. The source note's external-perspective Summary and Critique keep the PI's conclusions out of the record of what the paper argues; the claim note's Claim-plus-Evidence shape forces an asserted position rather than a paraphrase; the hub's three questions keep it a framing-and-planning surface rather than a place synthesis accidentally lands.

---

## Related

- The three epistemic roles explained: [Document types and epistemic roles](document-types.md)
- Why the Links section compounds: [The knowledge cycle](knowledge-cycle.md)
- What goes wrong without this structure: [Common pitfalls](common-pitfalls.md)
- How to use the reading workflow: [Discuss a paper](../../how-to-guides/library/discuss-a-paper.md)
- Document-type reference (templates, fields, lifecycle tables): [Document types](../../reference/document-types.md)


---

<!-- source: explanation/knowledge/your-first-month.md -->

# Your first month

The [tutorials](../../tutorials/README.md) compress the loop into a focused day on a pre-built sample: you orient, capture, distill, draft, verify, and close the loop in a few hours because the corpus is already there. Real use is the same loop at a different tempo — spread across weeks, on your own reading. This guide is that tempo: what to do *when*, so the vault **compounds** instead of either rotting (sources pile up, never synthesized) or stalling (claims accumulate, never written from). The tutorials taught you the moves; this is the rhythm.

## The rhythm, in one line

The four jobs do not run at the same cadence. **Capture** is continuous — you do it whenever you read. **Distill** is periodic — you do it once enough has accumulated to be worth connecting. **Produce** is event-driven — pulled by a real deadline, not a daily habit. **Discover** is gap-driven — triggered by what your producing exposes. And one standing ritual, the **weekly review**, keeps all of it honest. None of these is "step N"; they interleave.

## Week 1 — capture, and resist synthesizing

As you read, capture sources ([Capture and ingest](../../how-to-guides/library/capture-and-ingest.md)) and write each one's source note in your own words. That is the whole job this week. The temptation is to start distilling claims immediately — resist it. A thin corpus distills into thin, isolated claims; the value of a claim is the connections it makes to *other* claims, and there is nothing to connect to yet. Let sources accumulate first.

## Weeks 2–3 — distill once it's worth connecting

When a cluster of related sources has built up — roughly ten on a topic — start distilling claims and linking them ([Write a claim note](../../how-to-guides/knowledge/write-a-claim-note.md)). This is where the vault begins to compound, and the asset is **claim density, not source count**: fifty sources with five claims is a sophisticated reading list; fifty sources with forty connected claims is something you can write from. Distill in batches as clusters mature, not source-by-source.

## When a deadline appears — produce

Producing is an *event*, not a daily habit — it is pulled by a real deliverable (a section, a grant background, a review). When one arrives, switch modes: open a project, map the corpus for coverage, draft from your claims, and verify ([Assess your corpus](../../how-to-guides/project/assess-your-corpus.md) → [Draft with the Writer](../../how-to-guides/project/draft-with-writer.md) → [Verify and revise](../../how-to-guides/project/verify-and-revise.md)). The map will tell you honestly where the corpus is thin — and that thinness becomes your next reading.

## Continuously — let the gaps pull the next reading

The gaps that map and verify surface are not failures; they are the draft pointing at the next source. Hand them back to discovery ([Find new sources](../../how-to-guides/library/find-new-sources.md)) and the loop closes: producing exposes a gap, the gap pulls new reading, new reading feeds the next produce. Each turn leaves the corpus denser than the last — that is what *compounding* means, concretely.

## Every week — the review keeps it from rotting

Left alone, queues age and gaps go stale. The [weekly review](../../how-to-guides/inbox/run-the-weekly-review.md) — a ~20–30 minute Friday pass — is the heartbeat: refresh your research focus, sweep the Inbox toward empty (kept/skipped/triaged), advance settled claims. **An empty Inbox is success.** It is the single discipline that separates a vault that compounds from one that quietly accumulates.

## The two failure modes the rhythm prevents

A research vault fails in one of two ways ([What Memoria is](../overview/what-memoria-is.md)), and the tempo above exists to keep both halves coupled:

- **Capture without synthesis** — you read and file constantly but never distill. The vault grows; it does not compound. (The fix is Weeks 2–3: distill once clusters mature.)
- **Synthesis without rigor** — you write claims that no longer trace to a source. (The fix is the provenance discipline the tutorials drilled: every evidence line cites a citekey, and verification before anything ships.)

## What a month looks like

By the end of your first month you should have a **connected claim layer on a real topic of your own** — dense enough to draft from directly, the way the sample let you draft on day one, but built from your own reading and defensible because you built it. From there the loop just keeps turning, at whatever tempo your work demands.

## Related

- [The knowledge cycle](knowledge-cycle.md) — the loop this is the tempo of, and why it is not a linear path
- [Tutorials](../../tutorials/README.md) — the moves, learned in a day on the sample
- [Run the weekly review](../../how-to-guides/inbox/run-the-weekly-review.md) — the ritual at the center of the rhythm


---

<!-- source: explanation/knowledge/lifecycle-over-topic.md -->

# Lifecycle, not topic — and state, not folders

Two organizational decisions shape the vault: **a note's position in the system is its lifecycle, never its topic**, and **lifecycle is a state property in frontmatter, not a folder**. Folders encode one thing only — the *type-first category* a note belongs to (`catalog/`, `notes/sources/`, `notes/claims/`, …). Where a note stands — `proposed`, `provisional`, `current`, `retracted`, `archived` — is a frontmatter field on the universal chain.

---

## Why topic folders fail

Topic folders seem natural. "Put all my cognitive science notes in `cognitive-science/`." The problem is that topics are **many-to-many**:

A paper on attention and working memory belongs in `cognitive-science/`, and in `neuroscience/`, and in `HCI/`, and possibly in a project's orbit if it's relevant to current work. A topic folder forces a choice: pick one folder and lose the connections to the others, or create duplicates that immediately diverge.

Most knowledge systems respond by letting notes exist in multiple places (aliases, copies) or by moving topics to tags. But that creates a different problem: the folder is now redundant. If topics live in frontmatter and links, the folder adds no information. If the folder adds information, it must mean something other than topic.

**What a folder can uniquely encode is what a note *is*.** A note is exactly one kind of thing: a catalog entity, a source note, a claim, a hub, an Inbox card. That one-to-one fact is the folder's job. Topics live in frontmatter facets (`research_area`, `methodology`) and in links, where many-to-many can be expressed properly. This is a **Zettelkasten** inheritance: Luhmann's slip-box had no subject folders, only a web of cross-references, precisely because a fixed hierarchy can't express a note's many relationships (see [Intellectual foundations](../overview/intellectual-foundations.md#luhmanns-zettelkasten)).

---

## Lifecycle lives in frontmatter
The vault's top level is organized by **category** ([ADR-47](../../adr/47-type-first-category-folders.md)): one folder per category (`catalog/`, `notes/` with its prose subfolders, `projects/`, `inbox/`, `spaces/`, `system/`), never mixing two categories, with no lifecycle numbers and no archive folder. The full tree is catalogued in [On-disk layout](../../reference/on-disk-layout.md). A claim doesn't travel anywhere when the PI retracts it; a source note doesn't become a different kind of thing when it's read. What changes is its *standing* — and standing is a property, not a location.

Direction lives instead in the `lifecycle` frontmatter property — one chain for everything, each type using a subset of it ([ADR-50](../../adr/50-universal-lifecycle-and-maturity.md)); the chain and its per-type subsets are defined in [Frontmatter fields](../../reference/frontmatter.md). A source note awaiting reading is `proposed`; a claim the PI stands behind is `current`; a claim invalidated by new evidence is `retracted`, with lineage links to its successor.

---

## Why state-not-folders is strictly better

**Promotion is a frontmatter edit, not a file move.** A state change does not move a file, so it cannot break wikilinks, lose Git history continuity, or invalidate saved queries. A note is born in its type-home and dies in its type-home.

**Links survive every transition.** A claim cited by twelve other notes can be retracted, superseded, and archived without a single inbound link breaking. Provenance — the property the whole system is built to protect — does not depend on link-rewriting tooling getting every move right.

**`archived` is a state, not a folder.** An archived note stays exactly where it always lived and simply drops out of active views (Bases and Dataview filter on `lifecycle`). It remains readable, linkable, and traceable from every note that ever cited it — *archive, never delete* with zero file churn.

**Queries get honest.** "What's awaiting me?" is a lifecycle query (`lifecycle: proposed`), "what is this thing?" is a folder fact, and "what's it about?" is a facet query — three different questions, three different mechanisms, none overloaded onto the others.

**The agent's permissions stay tractable.** The gated zones (`notes/claims/`, `notes/hubs/`) are stable paths that never gain or lose members through state changes. The policy gate reasons about *where an agent may write*, and the answer never shifts under it mid-task.

One consequence to know: because Inbox cards use the same lifecycle vocabulary as notes (a card awaiting you is `proposed`), queries that filter on `lifecycle` scope by category folder — which the type-first tree makes trivial.

---

## Topics in frontmatter, not folders

With folders carrying the type and frontmatter carrying the state, topics are encoded as **facets** on source and claim notes:

- `research_area` — seeded from OpenAlex topics by the ingest operation
- `methodology` — a controlled vocabulary covering method and study design
- `topics` on claim notes

Topical *navigation* is built on top by **hubs** (`notes/hubs/`): curated notes that link the relevant sources and claims for an area, regardless of state or project. A hub is authored perspective over the graph, not a folder in disguise.

---

## Related

- The type system the folders encode: [Document types and epistemic roles](document-types.md)
- How state changes are gated: [Why promotion is gated](promotion-model.md)
- The decisions: [ADR-47](../../adr/47-type-first-category-folders.md), [ADR-50](../../adr/50-universal-lifecycle-and-maturity.md)
- The folder tree itself: [The vault](../architecture/vault.md)
- The facet fields: [Frontmatter fields](../../reference/frontmatter.md)


---

<!-- source: explanation/knowledge/promotion-model.md -->

# Why promotion is gated

Promotion is the act of making content canonical — confirming a claim into `notes/claims/`, curating a hub, accepting a proposed link. In Memoria it is always a human act. The rule for every actor that is not the PI is **propose, not dispose**: agents and operations stage proposals; the PI decides what becomes part of the record. This is not a safeguard bolted onto the system — it is the mechanism that keeps the vault trustworthy.

---

## What "canonical" means now

The gated zones are `notes/claims/` 🔒 and `notes/hubs/` 🔒. Project notes add a gated thesis promotion path, and a composition's `deliverable` state remains later work. Content there is trusted: when the Peer-reviewer (the background agent that checks drafts and citations — see [Glossary](../../reference/glossary.md)) traces a draft's citations, it assumes the claims represent positions the PI actually holds; when the PI builds on a claim, they assume they once made it theirs. If those zones could be written without review, every downstream use of canonical content would become suspect.

Promotion is not a file move ([ADR-50](../../adr/50-universal-lifecycle-and-maturity.md)). A note is born in its type-home and stays there; what the gate controls is the **state transition** (a fleeting thought becoming a `current` claim, a proposed link becoming part of the graph) and the **write into a gated zone**. The policy gate enforces the boundary mechanically: agents write staging and ungated zones; gated-zone writes, promotions, the `retracted` decision, and the archive move are PI-only.

What is deliberately *not* gated: the Catalog. Entity records are clean mechanical extractions of given facts — gating them would be a rubber stamp. Where the ingest operation's confidence drops (entity resolution, dedup, license calls), it raises a `flag` instead of merging silently.

---

## The honesty card: what an approval gate hands you

The review gate hands the PI a proposal, not a verdict. A proposal card carries an honest argument (with the agent's strongest self-rebuttal) and no verdict line; a verification card leads with the finding instead. Why that shape defeats automation bias — and the per-card field breakdown — is developed in [The honesty card](../kanban-board/card-schema.md) (fields in [Frontmatter fields](../../reference/frontmatter.md#the-honesty-card-fields)), where the design-smell rule it serves is stated in full.

---

## Two kinds of decision point

Not every place the PI acts is an approval ([ADR-54](../../adr/54-two-decision-kinds-batch-worklists.md)):

- **Approval gates** review agent-produced output: candidate triage (keep this source?), link confirmation (with evidence and stance reasoning per edge), certification before shipping, re-adjudication after a retraction, near-tie dedup calls, the archive proposal. Each ships its reasoning as an honesty card.
- **Work prompts** signal that it is time for the PI's *own* thinking: "this kept source is worth distilling into claims," "this corpus is ready to write from." They are rich nudges with the material to start — not approvals, and never blocking.

**Classify is neither — it is automated.** Assigning facet metadata to a kept source is low-stakes, high-volume, and verifiable: a human gate on it is a guaranteed rubber stamp. So classification ships as audited, correctable metadata, with a `flag` only on genuine ambiguity. Prefer full automation over a fake decision.

**High-cardinality decisions become a batch worklist, never N cards.** When a coverage report finds forty sources each needing a keep/reject call, the Inbox gets *one* aggregate work-prompt ("40 sources to screen"), pointing at a Bases-backed worklist where each file-backed row carries a `decision` field the PI toggles at group or item granularity — the systematic-review screening model. Forty cards would flood a queue meant to converge to zero and train select-all-accept.

And nowhere is there confidence-tiered auto-accept: confident-wrong is exactly the failure the review gate exists to catch.

---

## Maturity is a signal, not a gate

Claims carry `maturity` (`seedling → budding → evergreen`) — a soft, PI-set signal of how developed the claim is. It gates nothing and nothing auto-promotes at `evergreen`. Likewise `agent_recommendation` is a soft, agent-set verdict on a check; a `clean` recommendation never substitutes for human approval. The two axes — "how trusted?" (lifecycle) and "how developed?" (maturity) — are visibly different, with distinct value sets, so neither can impersonate the other.

A common pitfall is deferring promotion until a claim "feels evergreen." That misreads the model: make a claim `current` when you have decided it represents your position; maturity tracks how developed it is afterward.

---

## Why this feels slow

The human gate is the system's bottleneck by design, and that is the point — the full argument for why the review gate is structural rather than advisory is in [Why the review gate is structural](../rationale/why-human-gate.md). Here the consequence: agents can catalog, extract, and draft faster than the PI can review, so the proposal queue grows unless the PI keeps pace.

The right response to a full queue is not to automate review but to let the WIP limits and back-pressure bite — the board mechanism that makes the bottleneck visible instead of letting "reviewed" silently degrade into "rubber-stamped." That mechanism, and the rule that a rejected proposal spawns a fresh card rather than reopening the old one, are explained in [Board states and the review gate](../kanban-board/states.md). The gate is also instrumented — time-on-gate and accept-rate feed the fleet-health dashboard — so a gate that has stopped being a real decision shows up in the data.

---

## Related

**Explanation**

- The types and zones involved: [Document types and epistemic roles](document-types.md)
- Why state replaced folders: [Lifecycle, not topic — and state, not folders](lifecycle-over-topic.md)
- The card fields in detail: [The honesty card](../kanban-board/card-schema.md)
- The board mechanics behind the review gate: [Board states and the review gate](../kanban-board/states.md)

**Decisions**

- [ADR-51](../../adr/51-inbox-category-and-honesty-card.md) — the Inbox category and the honesty card
- [ADR-54](../../adr/54-two-decision-kinds-batch-worklists.md) — approval gates vs work prompts; classify automated; batch worklists


---

<!-- source: explanation/knowledge/vocabulary-discipline.md -->

# Vocabulary discipline

A vault that grows without vocabulary discipline accumulates a silent failure: the same concept gets different names in different notes, and queries return half the corpus on a topic while the PI believes coverage is thin. This document explains why the classification facets are separate, how vocabulary drift happens, and why the stabilization happens in stages.

For the exact field definitions and allowed values, see [Frontmatter fields](../../reference/frontmatter.md).

## Why separate facets, not one tag field

Memoria classifies sources with two distinct facets — `research_area` and `methodology` — plus `topics` on claim notes, rather than one general-purpose tag field. The separation is not bureaucratic; the facets answer categorically different questions.

`methodology` captures research architecture: _how_ a study was structured (RCT, observational, qualitative, systematic review, simulation, …). `research_area` captures conceptual content: _what_ the work is about. A query asking "show me all RCTs" is a `methodology` question. A query asking "everything on sensemaking" is a `research_area` question. Routing both to the same field makes both queries unreliable — one field can't simultaneously be the answer to orthogonal questions.

The Linter's `lint:check-schema` pass validates that facet values match the defined vocabulary, but only after the vocabulary has been defined. Drift from a vocabulary that doesn't yet exist is invisible to the Linter.

## Why vocabulary stabilization is deferred

Early in a vault's life, forcing term consistency is counterproductive. The right terms emerge from reading — you don't know yet whether "opportune-moment" and "receptivity-detection" are the same concept until you've read enough papers to recognize the pattern. Premature consolidation locks in the wrong vocabulary.

The deliberate design is to accept provisional terms early and consolidate once enough corpus has accumulated to make the vocabulary decisions durable. At roughly fifty papers, reviewing and merging inconsistent terms is tractable. Before that, the cost of false consolidation — deciding two concepts are the same when they're not — is higher than the cost of deferring.

This is also why `research_area` is seeded from **OpenAlex topics** by the ingest operation: the vocabulary is free, consistent across sources, and applied mechanically, which removes one whole class of drift at intake. `methodology` and claim `topics` are human-extended, and that is where the discipline below applies.

## Why drift fails silently

Vocabulary drift — the same concept appearing as `topics: receptivity-detection` in some claims and `topics: opportune-moments` in others — produces no error. Queries return incomplete results; the PI infers thin coverage when coverage is adequate; research directions are shaped by a false gap signal. The failure is invisible until the vocabulary is audited.

This is the class of failure the Linter's `lint:check-schema` pass is designed to catch, but only after the canonical vocabulary is defined. Before the canonical list exists, drift is entirely silent. See [Common pitfalls](common-pitfalls.md) for the concrete failure scenario and how it compounds over time.

## Related

- The operation that validates the vocabulary: [Operations](../operations/README.md)
- The common-pitfalls scenario this addresses: [Common pitfalls](common-pitfalls.md)
- The how-to for the vocabulary: [Manage your topic vocabulary](../../how-to-guides/knowledge/manage-vocabulary.md)
- Field definitions: [Frontmatter fields](../../reference/frontmatter.md)


---

<!-- source: explanation/knowledge/common-pitfalls.md -->

# Common pitfalls

Failure modes that recur in research vaults built this way. Most of them look like nothing is wrong — which is what makes them worth naming. They are ordered by **severity of outcome**: the ones that silently corrupt trusted content come first; the localized, recoverable ones come last. The closing section names the general principle underneath the worst of them.

## Treating agent output as verified content

The Writer (the background agent that drafts prose — see [Glossary](../../reference/glossary.md)) produces a draft in response to a query. It looks good. A paragraph gets copied into a composition. Later it emerges that the agent cited paper X for a claim that paper X does not actually make — the semantic similarity was there, but the specific claim wasn't.

This is the failure the Peer-reviewer (the background agent that checks drafts and citations — see [Glossary](../../reference/glossary.md)) exists to catch, but its `verify-check-citation` pass only verifies that citekeys resolve — it doesn't verify that the source actually supports the specific claim in the prose. That final check is irreducibly human. The system's design treats agent output as a proposal that requires verification, not a draft that requires only polish.

## Unpinned citekeys

You add a paper to Zotero, the ingest operation catalogs it, wikilinks form across the vault pointing to `mamykina2010sense`. Then you correct a metadata field in Zotero — the author's name, the year, a typo in the title — and Better BibTeX regenerates the citekey. Every wikilink in the vault is now broken, silently.

The reason this is silent: Obsidian doesn't warn about broken wikilinks; it just shows them as unresolved. Without the Linter's `lint:analyze-graph` check, the breakage is invisible until you're actively looking for a specific note. The failure compounds over time because new notes continue linking to the broken citekey, not knowing it has changed.

The root cause is that Better BibTeX treats citekeys as derived from metadata, not as stable identifiers. Pinning a key tells it to treat the key as the identifier, not the derivation. See [Capture and ingest a source](../../how-to-guides/library/capture-and-ingest.md) for the pinning procedure.

## Vocabulary drift

The same concept gets two names across notes — `topics: receptivity-detection` on one claim, `topics: opportune-moments` on another — so a query returns half the corpus and the PI infers thin coverage that isn't real. The failure is invisible because it produces no errors, only incomplete results, and the Linter cannot catch it until a canonical vocabulary exists. The full scenario, why consolidation is deliberately deferred, and how the failure compounds are in [Vocabulary discipline](vocabulary-discipline.md).

## Summary without synthesis

A source note's Summary section records findings and methods but contains no wikilinks to related notes, no tension with alternative views, and no statement of why the finding matters to current work. In six months it is useless because it doesn't connect to anything.

The failure is that summary and synthesis look identical in the moment of writing but diverge drastically in usefulness over time. A summary records what the source says. Synthesis connects what the source says to what you already believe — it is what makes the note compounding rather than merely stored.

## Distilling before triaging

The **Librarian** (the background agent that catalogs and classifies sources — see [Glossary](../../reference/glossary.md)) proposes a classification that often surfaces project connections that weren't obvious at intake — connections that should appear in the claim's `sources:` frontmatter and `links:`. Writing the claim before reviewing that proposal means missing those connections, because the classification pass is also when the system discovers what the source has to do with your existing work.

The deeper reason: classification (automated, audited, correctable) is how the system integrates a source into the existing graph. Bypassing it produces a claim that cites a paper but isn't connected to the web of context that would have been visible from the review.

## Queue accumulation

The Inbox grows week over week. Source notes sit at `lifecycle: proposed` for months. Candidate cards accumulate without triage. The dashboards show activity — sources are being catalogued — but the claim layer isn't growing.

This is a systemic failure because the Inbox and the reading queue are processing surfaces, not storage. The vault is compounding only when sources move through reading into claims. A queue that grows without shrinking is capture without synthesis — a sophisticated reading list, not a knowledge system. The weekly review exists precisely to catch this before it hardens into months of backlog.

## Hub-as-folder-dump

A hub grows to hundreds of lines with no structure, annotations, or curation. It becomes unusable because it takes too long to parse.

The structural issue is a confusion between indexing and curating. A hub's value is in what it leaves out and how it annotates what it keeps — it is a perspective on a topic, not an enumeration. When a hub becomes an index, it duplicates what a Base already does automatically. The embedded query handles volume; the static curated list handles meaning. When the curated list grows past 20–30 entries without structure, the hub needs child hubs or heavy pruning.

## The automation boundary

The failures above share a root, and naming it directly is the best defense. A recurring class of mistake is asking agents to make judgment calls. The distinction between what the agent can do reliably and what requires human judgment is not a question of capability — it is a question of what kind of decision is being made.

Tasks like API enrichment, link-candidate proposals, structural lint checks, and citation trace checks are deterministic or can be checked deterministically. Promotion, merge and archive decisions, synthesis quality assessment, and decisions about which papers to read are not — they require epistemic judgment that the agent cannot claim on behalf of the PI. Asking the agent to do the latter produces outputs that look authoritative but aren't, which is the failure mode the system's review gate (the human approval step before content is trusted — see [Glossary](../../reference/glossary.md)) exists to prevent.

For the explicit mapping of tasks to their appropriate owner, see [Profile capabilities](../../reference/profiles.md).

---

## Related

- Why promotion is gated: [Why promotion is gated](promotion-model.md)
- The fix for compound notes: [Refactor claim notes](../../how-to-guides/knowledge/refactor-a-note.md)
- Catching unverified agent output: [Run a retraction sweep](../../how-to-guides/operate/run-a-retraction-sweep.md)
- Lane (a background agent's execution path on the board — see [Glossary](../../reference/glossary.md)) permissions referenced here: [Profile capabilities](../../reference/profiles.md)


---

<!-- source: explanation/knowledge/hubs-and-navigation.md -->

# Why hubs

The vault organizes notes type-first into category folders and carries topic in links and frontmatter, not in folders ([Lifecycle, not topic — and state, not folders](lifecycle-over-topic.md)). That choice buys a lot — a claim can belong to many topics at once, and reorganizing a topic never means moving files — but it removes the thing a folder quietly provided: a place to *go* when you want to see everything about a subject. A **hub** is that place, rebuilt as a first-class note. This page explains why the vault needs a human-curated navigation layer at all, and why hubs are authored rather than generated.

> **Lineage.** The hub is Memoria's name for the **Map of Content** from the evergreen-notes tradition, itself descended from Luhmann's structure notes ([Intellectual foundations](../overview/intellectual-foundations.md#luhmanns-zettelkasten)). As elsewhere in the knowledge model, the method is borrowed; what Memoria adds is the *delegation boundary* — which parts of maintaining a Map of Content an agent may help with, and which it may not.

---

## A hub is navigation, not retrieval

The vault already has machine ways to gather notes on a topic: [Search](../../reference/search.md) ranks notes by text similarity, [Clustering](../../reference/clustering.md) computes communities over the typed graph, and a Dataview or Bases view lists every note matching a field. All three are fast, and all three are *re-derived on demand* — you run the query, read the result, and the result evaporates.

A hub is the opposite kind of object. It is a durable note you return to, and what it adds over any query is **perspective a query cannot produce**: a framing of what the cluster is about, a curation of what matters most in it right now, and a diagnosis of where it is thin or contested ([Note body structure](note-body-structure.md#why-hubs-answer-three-distinct-questions)). A hub that is merely a flat list of links is a failed hub — no one opens it, because a Base does the same listing faster. The value is in the judgment: *these* notes belong, in *this* framing, with *these* gaps still open.

So the division of labor is clean. Retrieval (search, clustering, queries) answers "what notes touch this topic?" — a question machines answer well. Navigation (hubs) answers "what does this topic *hold*, and where should I look first?" — a question that is an act of synthesis. Keeping them separate is what lets the machine surfaces stay ephemeral and the hub stay a stable, curated home.

---

## Why curation can't be delegated

Hubs live under `notes/hubs/`, which is a review-gated prefix: an agent's write there degrades to a dry-run ([Document types and epistemic roles](document-types.md), [Wikilink and link conventions](../../reference/linking.md)). That is deliberate, and it follows directly from what a hub is for. The curation *is* the hub — the framing and the "why these belong together" annotations are the entire value-add over a query. An agent can list the notes that mention a topic, but a list that *looks* curated without being curated is worse than no hub: it invites the reader to trust an organization no one actually performed, which is precisely the "hub-as-folder-dump" failure the design warns against ([Common pitfalls](common-pitfalls.md)).

This is why the agent's role around hubs stops at the threshold of judgment. The Librarian's `map` lane can notice that a cluster has grown dense and propose that a hub is due — but the proposal it is allowed to make is a **bare member list plus the threshold evidence**, written to staging, never the annotations and never into `notes/hubs/` itself ([Agent-proposed hubs](../../adr/19-moc-threshold-alert.md)). The human writes the framing, curates the membership, and names the gaps. The agent absorbs the bookkeeping (counting notes per topic) that the system is built to absorb; it does not absorb the synthesis, which is the part that defines the type.

---

## Why a threshold, not on-demand or always-on

A hub is worth creating only when there is something to navigate. Below roughly **15–20 notes** on a topic, the friction of a missing hub is lower than the cost of maintaining a premature one — an early hub is structure imposed before the shape of the topic is known, and it has to be rebuilt as the cluster actually forms ([Wikilink and link conventions](../../reference/linking.md#hub-thresholds)). Much past that, the cluster is already hard to move through, and the hub arrives late.

Rather than make the human watch note counts by hand, the Linter's `hub-threshold` detector makes the crossing visible — "topic *X* has 18 notes and no hub; consider one" — as a low-priority advisory, never an auto-creation ([Agent-proposed hubs](../../adr/19-moc-threshold-alert.md)). The threshold is a prompt to the human's judgment, not a trigger for the machine's. The same logic governs splitting: when one branch of a hub outgrows it, the hub spawns a child hub and the parent links to it, so navigation scales as a shallow hierarchy of curated maps rather than one ever-growing list.

---

## Where hubs sit in the knowledge model

Hubs are the navigational layer over the durable knowledge the vault accumulates. Claims are the atomic units — what the PI has come to think, in their own words ([Why promotion is gated](promotion-model.md)); hubs are how those units stay findable and legible as they multiply, the difference between a vault that compounds and one that merely accumulates ([The knowledge cycle](knowledge-cycle.md)). They are the one structural document type the human owns end to end, because navigation of one's own knowledge is not a task that survives being handed off. To build one in practice, see [Build a hub](../../how-to-guides/knowledge/build-a-moc.md).

---

## Related

- The folder-light, link-first organization that makes hubs necessary: [Lifecycle, not topic — and state, not folders](lifecycle-over-topic.md)
- What the three hub body sections each make the note able to do: [Note body structure](note-body-structure.md#why-hubs-answer-three-distinct-questions)
- The hub-as-folder-dump failure mode: [Common pitfalls](common-pitfalls.md)
- The machine surfaces a hub is *not*: [Search](../../reference/search.md), [Clustering](../../reference/clustering.md)
- Building one: [Build a hub](../../how-to-guides/knowledge/build-a-moc.md)


---

<!-- source: explanation/profiles/README.md -->

# Profiles

Memoria runs **one conversational agent — the Co-PI — and four background agents** it delegates to ([ADR-48](../../adr/48-copi-and-agent-consolidation.md)). The PI talks to exactly one agent; everything else runs as a lane (a background worker on the board — see [Glossary](../../reference/glossary.md)) on the board (the kanban board), invisible until it has something for you. A profile's stable trait is its **posture** — a stance like *faithful* or *skeptical* — while the skills it runs attach per lane.

## The one you talk to

| Agent | Posture | Where | What it does |
| --- | --- | --- | --- |
| **[The Co-PI](co-pi.md)** | reflective thinking-partner | the Agent Client pane | Holds the conversation, asks the sharpening questions, and delegates every write as a task card (a unit of work on the board — see [Glossary](../../reference/glossary.md)). Read-only by design. |

## The four background lanes

| Agent | Posture | Lane(s) | What it does |
| --- | --- | --- | --- |
| **[The Librarian](librarian.md)** | faithful | catalog · extract · link · map | The four processing tasks — intake, distillation, connection, and corpus mapping. Proposes generously; the review gate (the human approval step — see [Glossary](../../reference/glossary.md)) filters. |
| **[The Writer](writer.md)** | generative, draft-only | draft | Composes prose and outlines into project scratch. Never canonizes, never self-verifies. |
| **[The Peer-reviewer](peer-reviewer.md)** | skeptical, independent | verify | The formal review gate: judgment checks and the conceptual red-team. Flags, never fixes. |
| **[The Engineer](engineer.md)** | delegating | code | Scaffolds the handoff to an external coding agent and owns the commit gate. Writes no code itself. |

All five profiles ship; the Writer, Peer-reviewer, and Engineer run as background lanes, and the Project space (a navigation surface and dashboard-as-note — see [Glossary](../../reference/glossary.md)) those lanes write around — project folders, active theses, and structural-impact cache — ships alongside them. Deterministic work — ingest, search, clustering, the project structural-impact operation, verification sweeps, and the Linter — is [Operations](../operations/README.md), not agents: no posture, no board lane.

The tables above orient by posture; the canonical lane→profile map, write-scope ceilings, and bundled-skills counts live in [Profile capabilities](../../reference/profiles.md).

## Shared layer, unique layer

Each agent is a **shared** layer (the vault's `AGENTS.md` house rules, one copy for all) plus a **unique** layer (its own posture, skills, model, and connections). How those layers are packaged and shipped is owned by [Distribution model](../deployment/distribution-model.md); what matters here is the consequence — the agents share the house rules but each brings its own stance and toolset.

The Co-PI is the sole memory carrier while the background lanes stay stateless propose-then-dispose executors (they suggest; only the PI decides) — the substrate split behind that is [The memory model](../architecture/memory-model.md). Two affordances are Co-PI-only — the Hermes self-improving loop and `/personality` tuning ([The Co-PI](co-pi.md)) — and the specialists' postures are fixed by design, stable traits rather than per-run knobs.

## The bounded rule

All five agents **propose**; the **PI disposes** — promotions, the `retracted` decision, and gated-zone writes are PI-only, enforced by the policy MCP. Why that gate is structural rather than a convention is [Why the review gate is structural](../rationale/why-human-gate.md); how far each agent may hand support work onward is its [Delegation posture](delegation-posture.md).

## Where to go next

- Why one Co-PI + four background lanes: [Why specialist profiles, not a generalist agent](../rationale/why-specialist-profiles.md)
- The deterministic actors that left the profile set: [Operations](../operations/README.md)
- How cards reach the lanes and come back: [The control plane](../architecture/control-plane.md)


---

<!-- source: explanation/profiles/co-pi.md -->

# The Co-PI

The Co-PI is the one agent the PI converses with — the permanent presence in the Agent Client pane. Its mission has three verbs: **question** (sharpen the PI's thinking), **explain** (it knows the system and can account for what any part of Memoria is doing), and **delegate** (route work to the right background lane). Its product is the PI's sharpened thinking and well-routed work — never a file ([ADR-48](../../adr/48-copi-and-agent-consolidation.md)).

---

## The hard write-wall

The Co-PI is **read-only**. It runs the PI's read-only skills directly — searching, reading, questioning, explaining — but **every write leaves as a delegated task**: the `route-task` skill creates a card on the board via the tasks MCP, assigned to the lane whose posture fits. The policy MCP enforces the wall; it is structural, not prompt discipline.

The wall is what makes a permanent, memory-carrying conversational agent safe. A conversation drifts, accumulates context, and gets persuaded; a card does not. By the time delegated work touches the vault it has passed through a lane's scoped permissions, the propose-not-dispose process, and the PI's gate — none of which a chat message can shortcut.

## Memory — the loop only the Co-PI carries

Concentrating every conversation in one agent lets it run Hermes' self-improving loop — **memory · /goals · skills** — and compound into a genuine Co-PI rather than a stateless assistant. It is the **sole memory carrier** among the agents (see [The memory model](../architecture/memory-model.md)); the background lanes are stateless executors that ground on their handoff payloads. **`/personality`** — interactive persona tuning — is likewise Co-PI-only: the specialists' postures are fixed by design.

## What the Co-PI is not

**Not a lane.** It never appears on the board; it converses in the pane and creates cards for others.

**Not a router-only shell.** Delegation is one verb of three. The informal, continuous sparring — questioning a source, branching framings, explaining a decision — is the Co-PI's own work, distinct from the formal artifact-level pass run by [The Peer-reviewer](peer-reviewer.md).

**Not an author.** It never writes canonical content, drafts, or even staging artifacts. When the conversation produces something worth keeping, the keeping is delegated or done by the PI.

---

## Related

- The lanes it delegates to: [Profiles](README.md)
- How a delegated card travels: [The control plane](../architecture/control-plane.md)
- Why one conversational front: [Why specialist profiles, not a generalist agent](../rationale/why-specialist-profiles.md)


---

<!-- source: explanation/profiles/librarian.md -->

# The Librarian

The Librarian runs Memoria's four processing lanes (background worker paths on the board — see [Glossary](../../reference/glossary.md)) — **catalog · extract · link · map** — covering everything between "a source exists somewhere" and "the corpus is mapped for a project." Its defining posture is **faithful**: include generously, report state accurately, and let the review gate (the human approval step — see [Glossary](../../reference/glossary.md)) filter. The cost of a missing source is invisible; the cost of an over-inclusive candidate is one human decision. Given that asymmetry, generosity is the right policy for an intake agent — and fidelity to the source material is what keeps the generosity honest.

A research librarian does both intake and literature search, so corpus work (scope reports, gap analysis, cluster maps) belongs in this agent ([ADR-48](../../adr/48-copi-and-agent-consolidation.md)): the **map** lane is the same faithful posture pointed at what the vault already holds.

---

## The four lanes

The table below is an orienting illustration of what each lane does and the Inbox signal (a proposal card in your queue — see [Glossary](../../reference/glossary.md)) it raises; [Profile capabilities](../../reference/profiles.md) owns the canonical lane definitions (task-lane ids, write scopes, MCP servers).

| Lane | Work | Inbox signal |
| --- | --- | --- |
| **catalog** | find sources, propose intake, the comparative `[!brief]`, draft classifications | `candidate` |
| **extract** | claim-stubs and distill nudges from kept sources | work prompt |
| **link** | note-link candidates with evidence and stance reasoning | link proposal |
| **map** | corpus-maps, coverage-reports, cluster maps, writability reads, seeded canvases | `gap` |

The lanes are individually triggered, not a pipeline — a human gate (often a long gap) sits between each. Gaps found in *map* raise Inbox `gap`s (one of the card types — `candidate` / `flag` / `gap` — see [Glossary](../../reference/glossary.md)) that re-trigger *catalog*: the loop that compounds.

## Why it's designed this way

**The operation/agent split.** The mechanical half of cataloging — fetch metadata, extract text, build entity `relationships`, create Catalog records — is the **ingest operation**, not the Librarian. The agent fills the two LLM holes: composing the comparative `[!brief]` and proposing the classification. Keeping the mechanics deterministic keeps the high-volume path reproducible, auditable, and cheap; the agent spends LLM judgment only where judgment is needed — the [hybrid select-then-compose pattern](../rationale/why-computational-methods.md) applied to cataloging. Below a confidence floor the operation's fuzzy calls (entity resolution, dedup) emit a `flag` rather than merging silently ([ADR-56](../../adr/56-extraction-uncertainty-flag.md)).

**Faithful, not optimistic-and-loose.** The posture is generous about *inclusion* and strict about *representation*: a brief reports what the paper says, a coverage-report reports what the corpus holds, and neither editorializes. The review gate can only filter well if the proposals beneath it are faithful.

**One external surface, fully gated.** The Librarian touches the most external data in the system (OpenAlex, Crossref, Semantic Scholar, …), and every lookup goes through MCP — discovery tools and the ingest facade — never raw web access. Concentrating the external surface in one agent and routing it through the policy boundary makes it auditable by construction.

## What the Librarian is not

**Not a synthesizer.** It curates and maps evidence; the Writer composes arguments and the PI writes claims. It never writes `notes/claims/` or `notes/hubs/`.

**Not its own reviewer.** The agent that gathers and proposes must not also grade the result — that is the [Peer-reviewer](peer-reviewer.md)'s independence, the anti-rubber-stamp principle.

**Not the ingest operation.** You *run* ingest; you *delegate* to the Librarian. The folder is named `catalog/` for its content because both operate on it.

---

## Related

- The mechanical counterpart: [Operations](../operations/README.md)
- The independent checker downstream: [The Peer-reviewer](peer-reviewer.md)
- Why intake is separated from verification: [Why specialist profiles, not a generalist agent](../rationale/why-specialist-profiles.md)


---

<!-- source: explanation/profiles/writer.md -->

# The Writer

The Writer turns evidence into structured prose — section drafts with bound citations, and competing outlines. It runs the **draft** lane, and its posture is **generative, draft-only**: every output is a proposal in project scratch (`projects/<project>/`), and nothing it writes lands in `notes/claims/` or a deliverable without the PI's review. The PI owns canonical synthesis; the Writer is the composer whose work the PI reviews, edits, and either promotes or discards. In the Project space, Writer drafts can expose gaps, but promotion remains the PI's move.

---

## Why it's designed this way

**Draft-only is policy, not etiquette.** The Writer's lane ceiling excludes every gated zone; the policy MCP intercepts any attempt. Even an aggressive Writer cannot corrupt the canonical layer.

**No self-verification.** The Writer's job is to make tracing *possible* — cite sources explicitly, link claims — not to do the tracing. Citation checks, claim traces, and the red-team belong to the [Peer-reviewer](peer-reviewer.md); an author grading its own work is the rubber-stamp the split exists to prevent.

**No external reach.** The Writer's inputs are entirely what the vault already holds — sources, claims, hubs, the project's canvas and outline. This keeps the writing grounded in the PI's own corpus rather than freshly retrieved material, and keeps the prompt-injection surface at zero.

## What the Writer is not

**Not the Co-PI.** The Co-PI sharpens thinking *before* writing, in conversation; the Writer composes prose after the thinking is delegated as a card. Blurring them produces writing that sounds like the PI's thinking but never was.

**Not a promoter.** A draft becoming part of a claim or a deliverable is the PI's move, at the review gate. The Writer can mark a draft ready — an FYI, not an approval request.

---

## Related

- The agent that checks its output: [The Peer-reviewer](peer-reviewer.md)
- Where its drafts live: [The vault](../architecture/vault.md)
- Why canonical synthesis belongs to the human: [Why Memoria doesn't pursue full autonomy](../rationale/why-not-autonomous.md)


---

<!-- source: explanation/profiles/peer-reviewer.md -->

# The Peer-reviewer

The Peer-reviewer runs the **verify** lane — the formal, independent review gate before anything ships, the academic peer-review pass. Its posture is **skeptical, and deliberately independent**: flag, don't fix. It runs the *judgment* checks — citekey resolution, claim→source tracing, near-duplicate adjudication — and the conceptual red-team, reading a draft *for soundness, not just facts*. Its findings land as Inbox `gap` and `flag` cards; it writes nowhere else. It receives work from deliberate verify requests and from the project-draft post-commit trigger.

The Peer-reviewer owns judgment checks; deterministic verification work — retraction lookups, duplicate and broken-citation sweeps — lives in verification-sweep operations, scheduled on cron, no posture, no lane ([Operations](../operations/README.md)). ADR-48 records the consolidation decision.

---

## Why it's designed this way

**Independence is the design, not a staffing detail.** The agent that synthesizes must not also grade its own work — which is why the Peer-reviewer was never merged into the Librarian, however much tooling they share. The separation-of-duties / anti-rubber-stamp argument behind that is [Why specialist profiles, not a generalist agent](../rationale/why-specialist-profiles.md).

**Judgment checks vs operation sweeps.** A retraction lookup gives the same answer on every run — that's an operation. "Does this prose claim actually follow from this source?" requires reading — that's this agent. Splitting by determinism keeps the reproducible checks cheap and auditable while spending LLM judgment only where a verdict requires it.

**Flag, don't fix.** The entity that checks the work must not correct it. A failed trace becomes a `gap` card the Librarian picks up; a soundness problem becomes a `flag` for the PI. The draft is untouched — closing the loop without blurring the duty.

**Verification cards lead with the finding.** Unlike proposal cards (where the verdict is a given and is therefore omitted), a verification item carries its `agent_recommendation` — `clean` / `issues-found` / `inconclusive` — up front, with the evidence ([ADR-51](../../adr/51-inbox-category-and-honesty-card.md)). A recommendation is a soft signal, never a gate: `clean` does not substitute for the PI's approval.

## What the Peer-reviewer is not

**Not a truth oracle.** It judges whether a claim *traces* and whether an argument *holds*, and says so with calibrated certainty. Truth stays the PI's domain.

**Not the Co-PI's sparring.** The Peer-reviewer is the formal, independent pass over a finished artifact — it certifies work, where [The Co-PI](co-pi.md)'s continuous in-conversation questioning sharpens thinking.

**Not the sweeps.** If a check is reproducible without judgment, it belongs to an operation, and findings reach the PI the same way — as Inbox cards.

---

## Related

- The deterministic half of verification: [Operations](../operations/README.md)
- The proposer it stays independent of: [The Librarian](librarian.md)
- Why review is human-driven: [Why the review gate is structural](../rationale/why-human-gate.md)


---

<!-- source: explanation/profiles/engineer.md -->

# The Engineer

The Engineer runs the **code** lane as a documentary front for an external coding agent. Its posture is **delegating** — the defining trait is the **two-agent boundary**: Memoria treats the external coding agent as an opaque peer it hands off to, never executes itself. Like every Memoria agent, the Engineer is **MCP-only** — no terminal, no file access, no code execution ([ADR-46](../../adr/46-seven-layer-architecture.md)); it scaffolds the `code` handoff into `projects/<project>/code/` through the gated obsidian MCP, records provenance, and owns the commit/revert gate. The substantive coding — generating, debugging, restructuring — happens in the external agent, which executes nothing inside Memoria's runtime ([ADR-07](../../adr/07-delegate-coding-to-external-agents.md)). Project folders now exist through the Project gate; the autonomous code-experiment loop remains deferred.

---

## Why it's designed this way

**Memoria doesn't compete with coding agents — it connects to them.** Capable coding agents already exist; reimplementing them inside Memoria would produce a worse copy. The Engineer owns the connective tissue between Memoria's audit and review discipline and the external agent's capability: the handoff package (goal, specs, constraints, acceptance checks) is the contract, and what comes back re-enters through the gated `code/` zone.

**Execution stays outside Memoria.** No Memoria agent — the Engineer included — gets terminal, file, or code-execution capability ([ADR-21](../../adr/21-l3-autonomy-ceiling.md)). The external coding agent is third-party code that runs in its own runtime, never inside Memoria's; its work re-enters only as artifacts under `projects/<project>/code/`, through the Engineer's per-task commits and the PI's review.

**Per-task commits, not mega-commits.** One logical change per call keeps the audit trail granular — one card, one commit, one diff to review — and keeps revert scope small.

## What the Engineer is not

**Not the agent that writes code.** The external agent does. The Engineer scaffolds, records, commits.

**Not orchestration infrastructure.** It does not spawn the external agent as a subprocess, parse its output, or drive it through an API. The two agents coordinate through a markdown handoff and the artifacts that land in `projects/<project>/code/` — an explicit design choice, not a limitation.

**Not a documenter of research.** A `code` handoff records what was built and why. Writing *about* the methodology or results is the Writer's domain.

---

## Related

- Where the handoff lives: [The vault](../architecture/vault.md)
- How far each agent may delegate: [Delegation posture](delegation-posture.md)
- The autonomy boundary it tests: [Why Memoria doesn't pursue full autonomy](../rationale/why-not-autonomous.md)


---

<!-- source: explanation/profiles/delegation-posture.md -->

# Delegation posture

Agents differ in how much they may hand a narrow, temporary subtask to a child or external agent — never the role's *defining* judgment, only support work around it. Strongest delegators at the top:

```text
  more ┌────────────────────────────────────────────────────────────────────┐
   ▲   │ Engineer       Widest      substantive coding goes to the external  │
   │   │                            agent by design; commits stay per-task   │
   │   │ Writer         Supportive  facts / cleanup; synthesis stays local   │
   │   │ Librarian      Targeted    narrow enrichment / source lookups;      │
   │   │                            keeps discovery ownership                │
   │   │ Peer-reviewer  Very low    delegation weakens independence; runs    │
   │   │                            its own traces                           │
   ▼   │ Co-PI          None        read-only; every write leaves as a       │
  less │                            routed card, not a spawned helper        │
       └────────────────────────────────────────────────────────────────────┘
```

**Rule:** delegate narrow, temporary, low-risk subtasks; never the defining judgment. The Engineer's delegation is widest because the substantive coding *is* an external-agent handoff by design ([ADR-07](../../adr/07-delegate-coding-to-external-agents.md)). The Co-PI sits at the bottom despite delegating *everything*: routing a write to a board lane is the system's front door, not a subtask spawn — the card lands under another lane's ceiling and the PI's gate, never under the Co-PI's own authority.

However far an agent delegates, the **propose-not-dispose** rule holds for all five: whatever a helper or external agent produces re-enters as a proposal under the originating lane's write ceiling, and the PI disposes. Delegation can move work around; it can never move a decision past the gate.

---

## Related

- The agents ranked above: [Profiles](README.md)
- Why tasks go to specialists at all: [Why specialist profiles, not a generalist agent](../rationale/why-specialist-profiles.md)
- The widest delegator and its external-agent handoff: [The Engineer](engineer.md)


---

<!-- source: explanation/kanban-board/README.md -->

# The Kanban board

The Kanban board is Memoria's **control plane** — the trigger-and-lanes end of the loop. Every unit of background **agent** work is a card on the Hermes board (`kanban.db`, projected into Obsidian): a human action (or cron) creates a card, the dispatcher assigns it to a **lane**, the lane's agent runs it, and the result resurfaces as an **Inbox** signal. It should feel like a teammate working in the background — invisible until it has something for you.

**Lanes are the four background agents** — Librarian, Writer, Peer-reviewer, Engineer (`assignee = memoria-<name>`). The Co-PI has no lane (it converses in the pane and delegates), and neither do the deterministic operations (ingest, search, clustering, sweeps, the Linter run on cron/CI) — why both stay off the board is in [Board states and the review gate](states.md).

The board's central design move is to keep three dimensions separate — the hidden execution `status`, the PI-facing lifecycle state, and a soft `agent_recommendation` — so "a worker finished" never silently becomes "a human approved." Why they stay separate, and why a rejected card spawns a fresh one rather than reopening, is developed in [Board states and the review gate](states.md); the enums and lane assignments are in the [Kanban board reference](../../reference/kanban-board.md). A card is *work* (transient, archived when done); a vault note is *knowledge* (durable).

## Documents in this section

| Page                                                          | What it covers                                                                                                                                                                          |
| ------------------------------------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| [Board states and the review gate](states.md)                 | Why execution and the PI-facing lifecycle are two separate dimensions, what each transition means, why rejection spawns a new card, where the WIP limits sit, and why the Co-PI and the operations have no lanes. |
| [The honesty card](card-schema.md)                            | The card the PI actually reads: argument for, argument against, what tipped it, certainty — and no verdict on proposals; finding-first verification cards; graded loudness.               |
| [How the board surfaces in Obsidian](obsidian-projection.md)  | The read-only projections — the `inbox.base` board embedded in Home and the `system/board/` worker-card export — that let Obsidian read the authoritative `kanban.db`.                    |

For the state lookup tables (enums, lane assignments, WIP caps, dispatch settings, and the post-rejection paths), see the [Kanban board reference](../../reference/kanban-board.md).

## Related

**Explanation**

- Why review is structural: [Why the review gate is structural](../rationale/why-human-gate.md)
- The decision model behind the cards: [Why promotion is gated](../knowledge/promotion-model.md)
- The Inbox card types: [Document types and epistemic roles](../knowledge/document-types.md)

**Dashboards**

- The Inbox board view: [The board-state dashboard](../dashboards/daily-glance/board-state.md)


---

<!-- source: explanation/kanban-board/states.md -->

# Board states and the review gate

This page explains why the board's state machine is shaped the way it is: why the execution chain is hidden, why the PI sees only the lifecycle chain, why rejection spawns a new card, and why the WIP limits are set where they are. For the state lookup tables — the `status` enum, lane assignments, and the WIP-cap values — see the [Kanban board reference](../../reference/kanban-board.md).

---

## The execution chain is the hidden mechanic

Hermes runs every card through its native execution `status`: `triage → todo → ready → running → done → blocked → archived`. This chain is real and load-bearing — it is what the dispatcher schedules on — but the **PI never sees it**. It is plumbing, and its design serves the workers:

**`triage → todo → ready` exists so work is never dispatched before it's specified.** The dispatcher ignores `triage` cards. A card will never be accidentally claimed by a worker; only a deliberate release moves it to `ready`.

**Retries are not a distinct state.** A recoverable run failure returns the card to `ready` for re-dispatch on the same card. Only unrecoverable failures — those that require human judgment before work can continue — move the card to `blocked`, with a reason, for a human to clear.

## The lifecycle chain is what the PI sees

The human-facing card state is a subset of the same universal lifecycle chain every note uses — defined in [Frontmatter fields](../../reference/frontmatter.md) ([ADR-50](../../adr/50-universal-lifecycle-and-maturity.md)). For a card the path the PI walks is just `proposed → current → archived`.

A card in **`proposed` is awaiting you** — that is the whole convention. You act on it → `current`; closed → `archived`. There is no separate `review-request` card type and no second state vocabulary to learn: "what needs me?" is one query (`lifecycle: proposed`, scoped to `inbox/`), the same query the Inbox queue embeds. Because Inbox cards and vault notes share the vocabulary, queries scope by category folder, so card-state and note-state never collide.

---

## Three orthogonal dimensions

A card carries three independent signals, and keeping them separate is what prevents an agent verdict from rubber-stamping a human decision:

- **`status`** — execution (hidden): did the worker run, finish, or get stuck?
- **lifecycle state** — the PI's decision: has the human acted on this?
- **`agent_recommendation`** — the soft verdict (`inconclusive → issues-found → clean`), agent-set, never a gate.

A worker finishing implies nothing about acceptance; a `clean` recommendation never substitutes for the PI acting. The review gate is enforced, not advisory: state transitions are lifecycle operations the state machine controls, backed by the policy MCP — a worker cannot declare its own output approved.

**Rejection creates a new card, not a revision of the old one.** A rejected card is archived; rework begins on a fresh card that records what it `supersedes` — mirroring claim supersession. Each card is one attempt with one stated outcome, so the history of attempts stays traceable. A system where rejected cards are silently reopened is a system where the audit trail lies.

---

## Why the WIP limits

Three distinct caps, each motivated by a different failure mode (dispatcher polls every 60 seconds):

**One `running` card per lane.** Parallel runs of the same agent would contend for the same write scope and make the audit trail ambiguous about which run touched what file. One running card per lane keeps per-write attribution unambiguous.

**Review queue = 5 `done` cards.** The bottleneck is human attention, not machine capacity. An unbounded review queue grows faster than the PI can clear it, and the excess silently converts "reviewed" into "rubber-stamped." When the queue hits its cap, the dispatcher stops releasing new work — back-pressure that makes the queue depth visible before it becomes invisible.

**Writer lane bounded.** Too many drafts in flight means synthesis quality drops because evidence cannot be fully integrated. The cap protects synthesis quality, not throughput.

---

## The Co-PI and the operations are not lanes

**The Co-PI has no lane.** It is the one agent the PI converses with, interactively, in the Agent Client pane. It is read-only itself: every *write* it wants goes out as a delegated task card to a background lane. It never claims a card and never produces a `done` card — that is the design, not a gap.

**Operations have no lanes either.** Ingest, search, clustering, the verification sweeps, and the Linter are deterministic — no posture, no LLM judgment — so they run on cron and CI, off the board. Their findings still arrive in the Inbox (as `flag`/`alert` cards), but the work itself is never dispatched as a card.

---

## Related

**Explanation**

- Conceptual overview: [Kanban board](README.md)
- The card the PI reads: [The honesty card](card-schema.md)
- Why review is human-only: [Why the review gate is structural](../rationale/why-human-gate.md)
- The decision-kind model the gate implements: [Why promotion is gated](../knowledge/promotion-model.md)

**How-to**

- Troubleshooting for stuck cards: [Fix a stuck card](../../how-to-guides/troubleshooting/fix-stuck-card.md)

**Reference**

- Board-states lookup table: [Kanban board reference](../../reference/kanban-board.md)


---

<!-- source: explanation/kanban-board/card-schema.md -->

# The honesty card

An Inbox card is the one artifact the PI is guaranteed to read, so its format is where automation bias is won or lost. Research is blunt about the failure mode: hand a human a confident verdict and their scrutiny drops. And for a *proposal*, the verdict is a **given** — the agent surfaced the item because it recommends it, so printing "recommend: ACCEPT" adds nothing and subtracts attention. The honesty card ([ADR-51](../../adr/51-inbox-category-and-honesty-card.md)) is the answer: **proposals carry an honest argument, not a verdict; verification cards lead with the finding.**

The card schemas live in `.memoria/schemas/types/` alongside every other type — a card is just an `inbox/` note on the universal lifecycle chain, validated by the same Linter pass. Engines and lanes (a lane is a background agent's execution path on the board — see [Glossary](../../reference/glossary.md)) share one card-writer, so every card of a given type is shaped identically.

---

## Proposal cards: candidate and gap

A `candidate` (a *found* source proposed for intake) and a `gap` (a *missing*-source need) are approval-gate items (the gate is the human approval step — see [Glossary](../../reference/glossary.md)). There is **no verdict field** — the verdict is implied by the card existing. `argument_against` and `certainty` are what make the PI judge the argument rather than wave through a foregone conclusion. A card whose against-case is vacuous is a badly written card, and the design rule applies: *an Inbox item a human can clear without reading is a design smell* — give it real decision material or automate the decision. The full field list is in [Inbox card fields](../../reference/inbox-card-fields.md#proposal-cards).

## Verification cards: flag and alert

A `flag` (a verification or integrity issue) and an `alert` (a drift or retraction notice) are different: here the verdict is *not* a given — the whole point is what the check found. So these cards are **finding-first**: `finding` leads the card, and `agent_recommendation` carries the verdict the proposal cards deliberately omit. The full field list is in [Inbox card fields](../../reference/inbox-card-fields.md#verification-cards). `agent_recommendation` — the soft, agent-set verdict whose 3-tier enum and never-a-gate rule are defined in [Board states and the review gate](states.md) — is meaningful here precisely because it is *not* implied; still, a `clean` flag closes nothing on its own.

## Work prompts: work-prompt

A `work-prompt` is the third shape: not a proposal to judge and not a finding to adjudicate, but **work waiting on the PI** — the board export raises one when a worker card reaches `done`, and a batch worklist surfaces as one aggregate prompt. Like proposals, it carries **no verdict**; see [Inbox card fields](../../reference/inbox-card-fields.md#work-prompts).

---

## Graded loudness

Every card can carry a `loudness` level, and each level has a defined outcome — the difference between an ambient signal and an interruption is a design decision, not a worker's mood. `quiet` and `notice` stay pull-only; `alert` and `block` are push-worthy; an open `block` card also pauses delegation and review-gated promotion (writes that need PI approval — see [Glossary](../../reference/glossary.md)) until the PI resolves it. The four levels and the 30-minute test that picks a card's surface (*does it change what the PI does in the next 30 minutes?*) are owned by [Interaction channels](../architecture/human-channels.md).

---

## What deliberately isn't a card

**Classification** ships as audited, correctable metadata — a gate on it would be a rubber stamp ([ADR-54](../../adr/54-two-decision-kinds-batch-worklists.md)). **High-cardinality screening** (a coverage report with dozens of keep/reject calls) becomes a Bases-backed batch worklist plus *one* aggregate work-prompt card — never N cards, which would flood a queue meant to converge to zero and train select-all-accept. And there is no `review-request` type: any card awaiting the PI is simply in `proposed`, pointing at the artifact under review.

---

## Related

- Conceptual overview: [Kanban board](README.md)
- State machine: [Board states and the review gate](states.md)
- The decision-kind model the card serves: [Why promotion is gated](../knowledge/promotion-model.md)
- The card types in the type system: [Document types and epistemic roles](../knowledge/document-types.md)
- How policy gates writes: [Policy MCP](../../reference/policy-mcp.md)


---

<!-- source: explanation/kanban-board/obsidian-projection.md -->

# How the board surfaces in Obsidian

The authoritative board lives in `kanban.db` — a database Obsidian cannot query directly. The PI never opens it. What they see instead is the **Inbox**: the PI's slice of the board, rendered through Obsidian's own view layer.

---

## The Inbox board: `inbox.base`

The board the PI works is **one Obsidian Base over `inbox/`** — `inbox.base`, grouped by card type, filtered on the lifecycle chain. Its **"Needs me" view** (cards in `proposed`) is shown on the Inbox queue ([ADR-81](../../adr/81-persistent-gate-dashboards.md)); the full board (every card, every state) is the same Base's wider view, surfaced as the [board-state dashboard](../dashboards/daily-glance/board-state.md). No plugin, no custom renderer: cards are markdown notes with frontmatter, and Bases is the vault's standard view layer.

This is why the board needs no bespoke UI — the Inbox category *is* agent→human messaging ([ADR-51](../../adr/51-inbox-category-and-honesty-card.md)), and a Base over it is automatically the kanban view, grouped by type, converging to empty.

## The worker-card export: `system/board/`

Below the Inbox sits the execution layer. A board-export cron projects each live Hermes worker card from `kanban.db` to a markdown file in `system/board/` on a ~60-second cadence (matching the dispatcher's tick, so the projection never lags the board by more than one cycle). Each file carries the queryable fields in frontmatter plus the handoff summary in the body. This is the *mechanic's view* — useful when you want to see what a lane is actually executing — not part of the daily surface.

The same pass appends a compact snapshot line to `system/logs/board-state.jsonl` with per-lane counts and review-queue depth. The snapshot feeds telemetry and diagnostics; the PI-facing surfaces stay on native Inbox and board Bases.

## The two layers meet at `done`

The layers are not parallel feeds the PI has to watch separately — they are unified at the moment a lane finishes. When the export pass observes a worker card transition into `done`, it raises **one `work-prompt` card in the Inbox** — the verdict-free "a lane finished, here's where to look" shape owned by [The honesty card](card-schema.md). So a finished work product never waits silently in the mechanic's view: it surfaces in the same "Needs me" queue as every other agent→human signal, written through the shared card writer. The emit is idempotent — the export diffs against its state cache and names the prompt after the card id, so a done card raises exactly one prompt, once.

---

## The projections are one-way and ephemeral

Editing a projected file in `system/board/` does nothing to the board — the export is regenerated each pass and any manual edit is overwritten. The split of authority is deliberate: **Inbox cards are real notes** (acting on one — `proposed` → `current` — is a real state change the PI makes), while **worker-card exports are read views** of Hermes state, which changes only through Hermes itself.

---

## Related

- Conceptual overview: [Kanban board](README.md)
- The dashboard built on `inbox.base`: [The board-state dashboard](../dashboards/daily-glance/board-state.md)
- Export file schemas (`board-state.jsonl`, frontmatter fields): [Telemetry log schemas](../../reference/telemetry-logs.md)
- The separate fleet-health metrics roll-up: [fleet-health dashboard](../dashboards/operational-health/fleet-health.md)


---

<!-- source: explanation/workflows/README.md -->

# The workflow model

Memoria's workflows are **state-machine paths on the board**, not scripted procedures: work lives as a card whose state is explicit, persistent, and queryable, so it survives across sessions and recovers from failure instead of breaking like a script. This section explains what coordinates work (the board), why the human owns every synthesis boundary (review as a state), and where automation is intended to step in.

## Documents in this section

| Page                                                                          | What it covers                                                                                                                                                       |
| ----------------------------------------------------------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| [The board as a state machine (the control plane)](board-as-state-machine.md) | Why Kanban is the coordination layer (not chat), what a card carries, the card lifecycle, why cards and notes differ, and why there is no Orchestrator.              |
| [Review as a first-class state](review-as-state.md)                           | Why review is a structured field rather than a convention, what "blocking" means technically, and the post-rejection paths.                                          |
| [Verify-on-commit](verify-on-commit.md)                                       | How draft commits enqueue Peer-reviewer verification cards through the post-commit hook. |

For step-by-step workflow recipes, see [how-to guides](../../how-to-guides).


---

<!-- source: explanation/workflows/board-as-state-machine.md -->

# The board as a state machine (the control plane)

The Kanban board is Memoria's **control plane** — the shared state machine that coordinates work across profiles, sessions, and flows. Every long-lived task lives on the board until the PI approves it into the vault or archives it: agents propose, only the PI disposes, and the policy MCP enforces that wall — see [Why the review gate is structural](../rationale/why-human-gate.md).

---

## Procedure vs. state-machine path

A scripted procedure says: "do step 1, then step 2, then step 3." If step 2 fails, the script fails. The state of the work lives implicitly in how far along the script got.

A state-machine path says: "a card in state A, assigned to profile P, moves to state B when condition C is met." The state of the work is **explicit, persistent, and queryable**. If something fails, the card stays in its current state, the failure is recorded, and dispatch retries or escalates.

The difference matters most in long-horizon work. A research task doesn't complete in one session. Sources are found over days, synthesis develops over weeks, verification happens in parallel with drafting. A scripted procedure can't represent "this task is in progress across three sessions" — a state machine can.

---

## Why not chat

The alternative to a board is chat-based coordination: a human messages an agent, the agent does work, the human messages again. Many agent systems work this way. The problems emerge with scale:

**Chat is session-scoped.** When the session ends, the context is gone. The next session starts fresh. "Where was that task we were working on?" doesn't have an answer — it was in the conversation, which is now just a log.

**Chat has no WIP visibility.** In a chat-based system, there's no way to ask "what's in progress right now?" without reading the conversation. The board answers that question with a query.

**Chat doesn't survive handoffs.** When a task passes from the Librarian to the Peer-reviewer, what carries the context? In a chat system, the answer is "we re-explain it in the new session." In a board system, the answer is the card's `summary` and `metadata` — structured, persistent, and readable by any profile that picks it up.

**Chat conflates work with knowledge.** When a useful answer appears in a chat, it's trapped there. The vault and the board create two separate channels: the board is for work, the vault is for knowledge. The discipline separates "this is in progress" from "this has been established."

---

## What a card carries

A card is not just a task title. It carries:

**Execution state** — `status`, the fixed Hermes enum (the full sequence is in the [Kanban board reference](../../reference/kanban-board.md)). This answers "where is the work?" at any moment.

**Review state** — `review_status`, a Memoria overlay (enum in the [Kanban board reference](../../reference/kanban-board.md)). This answers "has the human accepted it as canonical?"

**Agent recommendation** — `agent_recommendation` (optional, from the Peer-reviewer or an operation such as the Linter). This answers "what does the checking pass advise?" — separate from the human's decision.

**Handoff payload** — `summary`, `metadata.allowed_paths`, `metadata.expected_outputs`, `metadata.promote_target`. The context the next worker needs to continue; why the receiver inherits this structured payload and never the sender's session context is [The control plane](../architecture/control-plane.md)'s design point.

**History** — retry count, blocked reason, who worked on it. The card survives retries without losing its identity.

These three dimensions — execution, review, agent recommendation — are intentionally separate because they can disagree; the full rationale for the orthogonality is owned by [The control plane](../architecture/control-plane.md), and what the review dimension means in practice is [Review as a first-class state](review-as-state.md).

---

## The card lifecycle

A card's life from creation to archival:

1. **Created** — either in `triage` (human-created, still needs specification) or directly in `ready` (cron-job-created, already specified). The rule: if a human still needs to shape it, start in `triage`. If it's fire-and-forget, start in `ready`.

2. **Dispatched** — the dispatcher claims a `ready` card whose `assignee` matches an available profile, moves it to `running`, and spawns the profile.

3. **Completed** — the worker finishes, writes its output to the vault's working zones, and marks the card `done` with `review_status: requested`. The worker never marks itself `approved`.

4. **Reviewed** — the human reads the output and sets `review_status` to `approved` (output stays) or `rejected` (output is revised or discarded). The card is then `archived`.

5. **Retried** (if needed) — a recoverable failure returns the card to `ready`. The retry is recorded in the card's history. After `max_retries` failures, the card goes to `blocked` and waits for human intervention.

The key invariant: **a card never closes on a worker's say-so**. The card lives until the human changes the review state.

---

## Cards and notes are different things

A natural confusion: does a card "produce a note"? Sometimes, but they are different kinds of thing and must be kept distinct.

**A card is work** — transient, lives on the board, dies at `archived`. It represents the effort to do something.

**A note is knowledge** — durable, lives in the vault, persists. It represents what was established.

A card may reference a note by path (its `metadata.promote_target` is a note path). A card may produce a note (a Librarian card produces a `paper` entity or `source` note). But a card is never a note — card fields (`status`, `review_status`, `assignee`) and note fields (`lifecycle`, `maturity`, `type`, `citekey`) are deliberately disjoint. Mixing them confuses what has been *done* with what has been *established*.

---

## Why no Orchestrator

Routing — "which profile picks up this card?" — is encoded in the card's `assignee` and the lane-override files, not in a reasoning agent. If the rules can't decide (no eligible profile, or ambiguous assignment), the card sits in `ready` until the human intervenes. Why there is no routing agent — the auditability argument — is owned by [Why specialist profiles, not a generalist agent](../rationale/why-specialist-profiles.md).

---

## Related

- Why the layered architecture requires explicit separation: [Why the architecture is layered](../rationale/why-three-layers.md)
- Why review is a first-class state: [Review as a first-class state](review-as-state.md)
- How the knowledge model complements the board: [Knowledge](../knowledge/README.md)
- The board's conceptual overview: [Kanban board](../kanban-board/README.md)
- Board state machine (full reference): [Kanban board reference](../../reference/kanban-board.md)


---

<!-- source: explanation/workflows/review-as-state.md -->

# Review as a first-class state

In most collaborative systems, "reviewed" is a convention — a comment, a tag, a verbal confirmation. In Memoria, review is a **structured state** in the card schema. The difference is not cosmetic; it is the mechanism that makes review queryable, enforceable, and honest about what has and hasn't been decided.

---

## The problem with review-as-convention

Consider three ways review can be represented:

1. **A comment**: "Looks good" in a card comment.
2. **A tag**: `#reviewed` added to a note.
3. **A field**: `review_status: approved` in structured frontmatter.

Comments and tags share a fatal problem: they are not queryable in a way that can enforce behavior. A Dataview query can find all notes with `review_status: approved` and act on them. A query that depends on "does this note have a `#reviewed` tag?" can be wrong if someone forgot to add the tag, added it before actually reviewing, or removed it. Tags and comments represent *attention*; fields represent *state*.

More critically: comments and tags cannot be used as preconditions by the dispatch system or the policy MCP. The board's dispatcher cannot check "has this card been reviewed?" if review lives in a comment. The policy MCP cannot prevent a write to a review-gated zone if "reviewed" is a convention rather than a field.

---

## The review_status dimension

A card in `done` state carries three orthogonal assessments that are kept separate — execution `status`, `review_status`, and `agent_recommendation` — and they can disagree; why all three are split is argued in [The control plane](../architecture/control-plane.md). This page focuses on the middle one, `review_status` — the field that records the human's accept/reject decision and gates promotion.

**Review state** (`review_status: requested`) says: "The human has not yet decided whether to accept the output" — distinct from `status: done` ("the worker finished") and from `agent_recommendation` (the checker's soft verdict, defined in [The Peer-reviewer](../profiles/peer-reviewer.md)). Collapsing `status` and `review_status` would make "worker finished" and "human approved" the same event — exactly the collapse that makes the system unreliable.

---

## What "blocking" means technically

`review_status: requested` is a blocking state. In practice:

- The dispatcher does not advance a `done` card further until the human changes `review_status`.
- The policy MCP applies `dry_run` to any write targeting review-gated zones regardless of which profile is writing. Even if a worker tried to write directly to `notes/claims/` without the card going through review, the MCP would block it.
- A WIP cap on the `done-awaiting-review` queue limits how many cards can accumulate. When the cap is hit, the dispatcher slows new work on that lane. The cap is back-pressure, not punishment — it keeps the board from racing ahead of the human's review capacity.

The back-pressure mechanism is sometimes misread as a problem (the system slows down). It is the opposite: the cap prevents the worst failure mode (agents producing hundreds of done-awaiting-review cards that the human will never actually review, making the whole queue worthless as a signal).

---

## Post-rejection paths

A rejected card is never reopened — rejection spawns a new card, because each card is one attempt (the principle is [The control plane](../architecture/control-plane.md)'s). The human has judged the work wrong, and what happens next is a fresh human decision:

**Supersede**: The human creates a new card on the same lane with a revised specification. The new card carries a reference back to the rejected one. The old card is archived with `archive_reason: superseded`. This is the standard path: the original task spec was wrong, not just the execution.

**Discard**: The work shouldn't have been created. The card is archived with `archive_reason: discarded`. This is the right path when the human decides the task itself was mistaken.

There is no path "back to the worker" — a worker cannot be told "do the same thing but better" without a new specification. Revision is not iteration; it is a fresh task with clearer constraints.

This is different from a **retry**, which is automatic re-dispatch of the same card after a transient failure (a rate-limited API, a timeout, a lookup that failed). Retries use the same card; rejections create new ones. The difference: retries address execution failures; rejections address quality failures.

---

## What review does not mean

**Review does not mean approval of everything the agent produced.** A human can approve a card while noting that one citation needs to be checked later. Approval means "this is good enough to move forward"; it doesn't mean "every claim in this output is verified."

**Review does not mean the Peer-reviewer checked it.** The Peer-reviewer's `agent_recommendation` is a recommendation that informs human review, not a replacement for it. The human might reject something the Peer-reviewer found clean, or approve something the Peer-reviewer flagged (after reading the flag and deciding it's not significant).

**Review does not happen in the vault.** Review happens on the board card, not on the note itself. A note that has been produced by a reviewed and approved card is not individually marked "reviewed" — the review happened at the card level. This is why it's important to understand cards and notes as distinct things.

---

## Related

- The card lifecycle and state machine: [The board as a state machine (the control plane)](board-as-state-machine.md)
- Why the review gate is structural: [Why the review gate is structural](../rationale/why-human-gate.md)
- Why synthesis promotion is gated: [Why promotion is gated](../knowledge/promotion-model.md)
- The execution-state breakdown: [Board states and the review gate](../kanban-board/states.md)
- The review_status enum and WIP limits: [Kanban board reference](../../reference/kanban-board.md)


---

<!-- source: explanation/workflows/verify-on-commit.md -->

# Verify-on-commit

Committing a draft to `projects/<project>/` automatically creates a verification card in the Peer-reviewer's verify lane. This document explains why the trigger is automatic rather than manual, and what the design is trying to prevent.

## Why automation is the right fit here

The verify step occupies an awkward position in the writing workflow: it is important enough to be non-negotiable in principle, but easily deferred under deadline pressure. A manual trigger depends on the human remembering to invoke it — the exact behavior that erodes under time pressure. An automatic trigger converts the decision from "should I verify this?" to "should I skip this verification?" The latter requires a deliberate act, not just forgetfulness.

The asymmetry is the point. The post-commit hook cannot be invisibly bypassed once the vault hooks are wired: a committed project draft creates a visible verify-lane card. Ignoring it requires leaving an auditable card in the queue. Skipping a manual step requires nothing.

## Why the trigger is a git hook, not a cron job

The trigger fires on `post-commit` to `projects/*/`, not on a schedule. A cron-based verification would verify drafts based on time, not on change — it might re-verify unchanged drafts and miss recently changed ones. The commit is the natural unit of change in the writing workflow; triggering on the commit ensures verification tracks actual edits.

The hook calls `hermes kanban create` to create the verify card — it does not invoke the Peer-reviewer directly. This keeps the trigger thin: it creates a card and returns. The Peer-reviewer claims the card through the normal dispatch mechanism, which means verification is audited, retryable, and visible in the board like any other task. A direct invocation from a hook would bypass all of that.

**Draft commits are deliberate, not timed.** This change-based triggering only holds if commits track edits rather than the clock. obsidian-git's `autoSaveInterval` (a ~30-minute scheduled commit; see [Obsidian plugins](../../reference/obsidian-plugins.md)) is configured as an offsite-backup safety net for the vault at large — it is **not** the verify trigger for drafts. Committing a draft you want verified is a deliberate act (`Cmd-P → Obsidian Git: Commit`), so "I committed this draft" means "verify it," and the verify card appears from that commit rather than on the next timer tick. If you rely on the auto-save timer for draft commits instead, verification still fires — but batched to the timer, up to ~30 minutes after your last edit, which dilutes the immediate feedback the workflow is designed around.

## What the automatic trigger is not

The automatic card creation is not automatic verification completion. The card enters the Peer-reviewer's queue; the Peer-reviewer processes it within its normal dispatch window. The result is an `agent_recommendation` — a soft signal, never an automatic gate (the enum and that constraint are owned by [The Peer-reviewer](../profiles/peer-reviewer.md)). The human still reviews the verification report and decides whether to address gaps or proceed to export.

This is consistent with the rest of the system's posture: agents produce recommendations; humans make decisions. The automation eliminates the "forget to trigger verification" failure mode without removing the "read and decide on the findings" step.

## Related

- [The Peer-reviewer](../profiles/peer-reviewer.md) — what the Peer-reviewer checks and how
- [Verify and revise a draft](../../how-to-guides/project/verify-and-revise.md) — how to read the report and address gaps


---

<!-- source: explanation/obsidian/README.md -->

# Obsidian — the human surface

Obsidian is where the human meets Memoria. The agents run in Hermes and the board lives in `kanban.db`, but everything the human reads, writes, and decides happens here. This section explains _how that surface is designed_ — not how to operate it (that's the [interface how-to guides](../../how-to-guides/using-obsidian)) and not the exact settings (that's [Obsidian plugins](../../reference/obsidian-plugins.md) and the `obsidian-*` reference pages).

One principle runs through every page below: **the architecture is invisible during normal use and legible when something goes wrong.** The vault should feel like a writing environment; the machinery surfaces only when it needs a decision.

## The surfaces

| Page                                            | What it explains                                                                                                                 |
| ----------------------------------------------- | -------------------------------------------------------------------------------------------------------------------------------- |
| [Home welcome note](home.md)          | `home.md` as the launch/reset welcome note; navigation is the left-pane rail.                           |
| [Callouts](callouts.md)                         | The inline callout types (`[!brief]`, `[!suggestions]`, `[!verification]`) and what each means.              |
| [The Agent Client pane](agent-client-pane.md) | The ACP-backed chat pane — why one conversational Co-PI surface exists alongside the board.                                      |

## The discipline behind them

| Page                                            | What it explains                                                                                                                                                                         |
| ----------------------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| [Visual-style discipline](visual-discipline.md) | The restraint that makes the above work — a fixed callout palette, hidden chrome, space dashboards as notes, and why each default is deliberate.                                    |
| [Design system](design-system.md)               | The cross-context visual and voice spec — why a portable design system exists, and why the specific choices (single accent, system fonts, 4pt grid, voice guidelines) are what they are. |

The **dashboards** are also an Obsidian surface, but they have their own section: [explanation/dashboards/](../dashboards/README.md).

---

## Related

- How to _use_ these surfaces (operate the pane, navigate dashboards, drive the palette): [how-to-guides/using-obsidian/](../../how-to-guides/using-obsidian)
- Plugin inventory: [Obsidian plugins](../../reference/obsidian-plugins.md)
- Load-bearing plugin settings: [Obsidian plugin settings](../../reference/obsidian-plugin-settings.md)
- Workspace, callout, and dashboard reference pages: [Reference](../../reference)


---

<!-- source: explanation/obsidian/home.md -->

# Home welcome note

The vault-root `home.md` is a thin welcome note — a "start here" screen for the
Memoria Obsidian shell. On launch QuickAdd asks Obsidian's core Workspaces plugin to
restore that shell: `home.md` in the main pane, the pinned rail on the left, and the
Co-PI pane on the right ([ADR-81](../../adr/81-persistent-gate-dashboards.md)).

---

## What it shows

The welcome note is a "start here" screen: capture your first source, the three places
(Library · Knowledge · Project), and a pointer to ask the Co-PI. It is not a dashboard —
it carries no health views and no counts. Navigation between surfaces is the left-pane
rail, not this note. The welcome note is a plain Markdown note; it owns no custom renderer.

---

## Home is a consumer, never a producer

The welcome note contains no bespoke computation. Where it surfaces anything live, it
embeds Bases views whose data lives in the notes and system projections rather than
computing its own. The reason is single-source-of-truth: if `home.md` ran its own health
queries, those queries would inevitably drift from the authoritative dashboard/Bases and
rail definitions, and the human would have two slightly different answers to "is anything
wrong?"

---

## Why a note, not a plugin start-page

The welcome note is a Markdown note rendered by Obsidian Bases/Dataview — git-tracked, lintable, and embeddable. A plugin-rendered start page would be opaque to git, outside the Linter's reach, and impossible to embed elsewhere. Startup depends on the already-bundled QuickAdd startup macro and Obsidian's core Workspaces plugin to restore the saved **Memoria** shell. `home.md` stays an ordinary, git-tracked note.

This is the same discipline applied to the dashboards themselves: the human-facing surface is always a plain note the system's own tools can see and check.

---

## Graceful degradation

On a freshly cloned vault, before any data exists, the welcome note shows its "start here" guidance and the dashboards behind it show mostly empty states. That is intentional and matches how the dashboards degrade — empty is a valid state, not a broken one. Because the welcome note owns no custom computation, it should never fail just because the vault is new.

---

## Related

- What Home links *to*: [the dashboards](../dashboards/README.md)
- The visual restraint Home participates in: [Visual-style discipline](visual-discipline.md)
- The plugin inventory behind these surfaces: [Obsidian plugins](../../reference/obsidian-plugins.md)
- The welcome-note decision history: [ADR-13](../../adr/13-homepage-front-door.md)


---

<!-- source: explanation/obsidian/callouts.md -->

# Callouts

Not every agent output belongs on a dashboard. Some context is only useful while looking at a specific note — the comparative read on a paper matters when you open it to read the source, not in a daily roll-up. Dashboards surface *decisions across notes*; callouts surface *context inside one note*.

Memoria defines three callout types via the Callout Manager plugin and renders them consistently across the vault. `[!brief]` is produced during ingest; `[!suggestions]` is produced by the link-claim palette action; `[!verification]` is produced by the verify-draft palette action.

For the exact shipped-vs-deferred contract, see the reference: [Obsidian callouts](../../reference/obsidian-callouts.md). This page explains *why* the three callouts exist and why they're shaped the way they are.

## The three callouts and what they represent

**`[!brief]`** is the comparative read the Librarian composes during ingest, before you've read the paper. It tells you: which of your existing notes this paper overlaps with, where it might contradict what you already know, and what new constructs it introduces. The brief primes your attention so you read actively rather than passively.

**`[!suggestions]`** is the Librarian's bounded deterministic set of candidate links, with Approve and Reject affordances. It is designed to start collapsed to prevent rubber-stamping: if you see a wall of suggestions, you tend to approve all of them without reading. The future fleet-health signal should track accept/reject ratios over time, because a too-high acceptance rate means rubber-stamping and a too-low one means the candidate scoring needs tuning.

**`[!verification]`** is the Peer-reviewer's claim-trace scaffold over a draft. It should show the result of tracing every substantive claim in the draft back to a claim note — a check for traced claims, a flag for untraced ones, and a link to the full per-claim report.

The placement, cap values, collapse states, and drift-signal cutoffs are in the [reference](../../reference/obsidian-callouts.md).

## Why callouts rather than dashboards

A dashboard tells you something about the vault as a whole: what's overdue, what's unlinked, what needs review. A callout tells you something about the note you're currently reading. Separating them means you don't have to context-switch to get note-level context, and the dashboard isn't cluttered with per-note detail.

The design rule: if the information is only useful in the context of a specific note, it's a callout. If it requires seeing across multiple notes, it's a dashboard.

## Why content is produced deterministically, then composed

All three callouts follow the same pattern: a deterministic step selects and ranks candidates; an LLM composes the prose over them. This is the [hybrid method pattern](../rationale/why-computational-methods.md) applied to a note-level surface, and it is a deliberate choice rather than a convenience.

The reason is auditability under cost control. The *selection* — which sources are comparable, which links are candidates, which claims trace — is the part that must be reproducible and reviewable, so it stays deterministic: the same vault state produces the same candidates, ranked the same way, every run. The *prose* — the comparative narrative, the one-line link explanations — is the part with no deterministic form, so it's where LLM judgment is spent, and only there. Letting the LLM also do the selection would make the callout non-reproducible and the cost unbounded, for no gain the human can verify.

This is why the audit trail for each callout is the deterministic step's output — which candidates ranked where, by what score — not the LLM's wording. The prose is the visible presentation; the scoring is what the dashboards and the fleet-health accept/reject ratios actually measure. (The exact ranking weights and similarity thresholds are in the [reference](../../reference/obsidian-callouts.md#how-content-is-produced-hybrid-pattern).)

## Why callouts are producer-owned and human-curated

Three properties are shared across all three callout types and reflect common design commitments.

Each produced callout is written by the producing agent and then owned by the human. Producers do not overwrite edits on subsequent runs; they append a new `(updated YYYY-MM-DD)` callout below any existing one. This preserves the human's edits while surfacing new agent output, rather than forcing a choice between freshness and persistence.

The collapsed/expanded default follows the volume of the callout type. `[!brief]` starts expanded because it provides one-shot context that is always relevant when the note is open. `[!suggestions]` starts collapsed because it contains a list of candidate links; `[!verification]` starts expanded because its trace is a finding surface.

Callout writes pass through the policy MCP like any other vault write — logged, hashed, and reversible from the audit log. This means the callout mechanism cannot be used to bypass the review gate, and the audit trail captures when and by whom each callout was written.

---

## Related

- The hybrid pattern behind callouts: [Why Memoria uses deterministic methods alongside LLMs](../rationale/why-computational-methods.md)
- Callout field reference: [Obsidian callouts](../../reference/obsidian-callouts.md)


---

<!-- source: explanation/obsidian/agent-client-pane.md -->

# The Agent Client pane

The agent-client plugin implements ACP (Agent Client Protocol) inside Obsidian: a chat pane where the human talks to a Hermes profile. The pane hosts **one agent — the Co-PI** (Memoria's single conversational agent — see [Glossary](../../reference/glossary.md)) ([ADR-48](../../adr/48-copi-and-agent-consolidation.md)). The specialists (Librarian, Writer, Peer-reviewer, Engineer) are **board lanes** (background workers on the kanban board — see [Glossary](../../reference/glossary.md)), not conversation partners, and the Co-PI delegates cards (units of delegated work) to them. This document explains the pane's *design*: why a conversational surface exists at all alongside the board, and why exactly one agent lives in it.

For *how to operate* the pane — opening it, attaching a note as context, reading responses, ending a session — see the how-to guide [Agent Client pane](../../how-to-guides/using-obsidian/use-the-agent-client-pane.md). For the `data.json` keys, load-bearing settings, hotkeys, and per-device install discipline, see [Obsidian plugin settings](../../reference/obsidian-plugin-settings.md) and [Obsidian plugin data files](../../reference/obsidian-plugin-data-files.md).

---

## Why a conversational pane at all

Most of Memoria's work flows through the board: a card is created, dispatched, completed, reviewed. The pane is the deliberate exception — the one surface for work that is *synchronous and exploratory* rather than queued and auditable. Thinking a paper through, asking what the corpus already holds, sketching a counter-outline: these are conversations, not tasks with a fixed output. Forcing them onto the board would produce cards that never cleanly close, because the "output" lives in the human's understanding, not in a file.

So the pane and the board divide cleanly: **the board is for work that produces a reviewable artifact; the pane is for thinking that produces a clearer human.** Anything from a pane session that *should* become durable (a claim note, a draft) is written through the normal gated path (passing the human approval gate — see [Glossary](../../reference/glossary.md)) afterward — by the PI directly, through the matching command-palette route, or as a card the Co-PI delegates. The pane itself writes nothing canonical: the Co-PI is structurally read-only ([The Co-PI](../profiles/co-pi.md)).

## Why one agent

One agent in the pane means one hard contract to reason about. The Co-PI is read-only — every write leaves as a card under a background lane's ceiling (the outer bound on where its writes may land — see [Glossary](../../reference/glossary.md)) — so no exchange can talk it into a write it isn't allowed, and there is no contract boundary to police mid-conversation. And because the agent never switches, **the conversation persists**, which is exactly what the Co-PI's memory loop needs to compound into a genuine Co-PI rather than a stateless assistant ([The Co-PI](../profiles/co-pi.md)).

The boundary between specialists lives where it belongs — on the board. Each lane runs under its own scoped write ceiling, each delegation is ceiling-validated, and each result comes back through the review gate ([The control plane](../architecture/control-plane.md)). That separation is physical — separate dispatched processes with separate permissions — not a UI affordance the human must operate correctly.

The assist surface keeps that split visible. Find/Search/Patterns/Ask/Draft/Explore exist as direct palette commands and can carry the active editor selection into a staged card or proposal artifact; the same verbs can also start in the pane as conversation. The rule is the same in both places: exploratory Ask/Explore can stay read-only in the pane, while anything durable leaves through a gated card or PI-authored note ([Obsidian command palette](../../reference/obsidian-command-palette.md)).

## Exploratory vs. durable work

The practical discipline the pane asks of the human:

- **Stay in the pane** while the work is exploratory — questioning a source, branching framings, asking what exists. The output is your sharpened thinking; nothing needs to be filed.
- **Leave the pane** the moment the work should produce an artifact. Either write it yourself through the gated path (a claim note, a draft edit), use the matching direct command, or ask the Co-PI to delegate it — "draft this section" becomes a card on the draft lane, with a reviewable output and an audit trail.

A pane session that keeps producing things you wish were files is the signal to switch modes: conversations are for converging on what to make, cards are for making it.

---

## Related

- The one agent in the pane: [The Co-PI](../profiles/co-pi.md)
- Operating the pane: [Agent Client pane](../../how-to-guides/using-obsidian/use-the-agent-client-pane.md)
- Where delegated work goes: [The control plane](../architecture/control-plane.md)
- Plugin settings: [Obsidian plugin settings](../../reference/obsidian-plugin-settings.md)
- Plugin data-file conventions: [Obsidian plugin data files](../../reference/obsidian-plugin-data-files.md)


---

<!-- source: explanation/obsidian/visual-discipline.md -->

# Visual-style discipline

Plugin choice is only half of how the vault feels to use. The other half is **restraint** about how the vault looks and behaves. A vault that becomes a cockpit of indicators is a vault that gets abandoned. The defaults below are deliberate, and the reasoning behind each is the point — any deviation should be equally deliberate.

The defaults below make concrete the principle that governs this whole section — the architecture is invisible during normal use and legible when something goes wrong ([Obsidian — the human surface](README.md)): indicators surface only when something specific demands attention.

---

## Why typography choices are load-bearing

The three callout types (`[!brief]`, `[!suggestions]`, `[!verification]`) use a **fixed three-color palette** — one stable hue per type, each reinforced by a distinct *icon*. The reason is attentional: a fixed, bounded color-per-type becomes a code the eye learns to read at a glance. The discipline is that the set stays small and fixed — three colors, one per callout type; what collapses the signal into visual noise is *arbitrary* or per-note color, not a bounded semantic palette. (What each callout means: [Callouts](callouts.md).)

Heading hierarchy is enforced by the Linter not as an aesthetic preference but because Dataview queries that filter on heading content break when the hierarchy is inconsistent — an H4 with no H3 parent is a structural problem that produces empty or wrong dashboard views, not a cosmetic one.

Emoji in note *titles* break filename portability across operating systems — a filesystem constraint, not a style choice. Emoji in note *bodies* is fine, because body content is never used as a filename.

---

## Why chrome is hidden by default

The vault should feel like writing during normal operation. Chrome — tab bars, sidebars, status indicators — is noise during focused reading and writing, and becomes signal when something needs attention. Hiding it by default preserves the signal-to-noise ratio: when the sidebar opens, it *means* something is happening.

Earlier designs reserved a standalone status line for a one-second ambient answer to "is everything roughly fine?" That widget is not part of the current Obsidian surface. The current answer lives in the rail's **Now**: the Inbox action count and Maintenance/Fleet health band stay visible without adding a separate always-on indicator.

One Obsidian window per vault is a technical constraint as much as a discipline. The agent layer assumes a single active vault; multiple windows updating the same card through the policy MCP produce race conditions in the audit log and board state.

---

## Why spaces are notes, not workspaces

The current design maps work modes to dashboard notes — Inbox, Maintenance, Library,
Knowledge, and Project — rather than to saved Obsidian workspaces
([ADR-81](../../adr/81-persistent-gate-dashboards.md)). A space is content the vault can
diff, lint, link, and restore. A workspace is pane state. Treating every mode as pane
state made navigation heavier than the job required.

The saved **Memoria** workspace remains useful as a reset shell: home in the main pane,
navigation on the left, Co-PI on the right. Daily mode switching happens through the
left-pane rail, not layout swaps. The exact layout and space list are reference material:
[Obsidian workspaces](../../reference/obsidian-workspaces.md).

---

## The success condition

Three months in, the mouse hand barely moves and there is no conscious tracking of which
layout is active. The vault looks like a writing environment, and the only time an
indicator pulls the eye is when something genuinely needs a decision. That is what
visual-style discipline is for — not minimalism for its own sake, but preserving
attention for the moments that deserve it.

---

## Related

- The current ambient glance and dashboard inventory: [Dashboards](../dashboards/README.md)
- The callout types and their fixed three-color palette: [Callouts](callouts.md)
- The welcome note, which participates in the same restraint: [Home welcome note](home.md)
- Gate/reset layout reference: [Obsidian workspaces](../../reference/obsidian-workspaces.md)


---

<!-- source: explanation/obsidian/design-system.md -->

# Design system

Memoria outputs travel through multiple renderers — Obsidian's live preview, Pandoc exports (Word, PDF), and open-design's render pipeline. Without a shared visual spec, each consumer makes independent choices that compound over time: the heading scale used in a delivered PDF becomes different from the callout colors in Obsidian, which become different from the CSS in a web export. The design system is the single source that all consumers read.

The vault file `.memoria/design-system.md` *implements* the spec for this vault (the actual values). This page explains the principles behind the choices.

---

## Why a portable schema

The design system follows the [open-design](https://github.com/nexu-io/open-design) DESIGN.md schema — a structured nine-section format that design tooling can parse directly. The reason is portability: one file, no translation layer. An open-design render run, a Pandoc flag, and a CSS-snippet generator all read the same source of truth without custom adapters. When the design changes, one file update propagates to all consumers.

Without this, each consumer accumulates its own hardcoded values. A heading size changed in Obsidian's CSS doesn't automatically reach the Pandoc template; a brand color updated in one export config doesn't reach the other. The spec file makes the design legible and the propagation intentional.

---

## Why a fixed three-color palette

The three Memoria callout types (`[!brief]`, `[!suggestions]`, `[!verification]`) each carry a fixed, stable hue reinforced by a distinct icon, for the attentional reason owned by [Visual-style discipline](visual-discipline.md) — a bounded color-per-type is a code the eye learns, while *arbitrary* or per-note color is what collapses the signal into noise.

What the design system adds is *scope*: this fixed-palette rule applies to every surface the design system governs, not just Obsidian callouts. In Pandoc exports, in HTML preview, in slides: the same fixed, bounded palette.

---

## Why system fonts, not custom stacks

The typography section specifies system-ui fallback stacks rather than custom font families. The reason is export portability. A custom font that isn't installed on the recipient's machine causes Pandoc or a PDF renderer to fall back silently, producing inconsistent output that's hard to diagnose. System stacks resolve on every machine — the font the author sees is the font the collaborator sees.

The monospace stack (`JetBrains Mono, Consolas, Courier New`) is the one exception: code blocks need a consistent monospace baseline, and JetBrains Mono is widely installed alongside development tooling. If it's absent, the Consolas/Courier New fallback is indistinguishable in a code context.

---

## Why 4pt spacing base

The spacing section is built on multiples of 4px. This isn't aesthetic minimalism — it's precision enforcement. Multiples of 4 produce consistent visual rhythm because the human perceptual system responds to proportional relationships, not to absolute sizes. An arbitrary `7px` gap between elements breaks the rhythm in a way that `8px` (2×base) doesn't. The rule is: if a spacing value isn't on the `4n` grid, it should be changed to the nearest grid point, not kept as a one-off.

---

## Why voice guidelines belong in the design system

The voice section — person, formality, terminology — might seem misplaced in a visual design doc. It's there because Memoria content travels through contexts where visual and verbal choices are equally load-bearing: agent prompts, Pandoc-generated deliverables, and the Obsidian note body are all authored against the same system. A terminology inconsistency (`"permanent note"` vs `"claim-note"`, `"Hermes profile"` vs `"agent"`) is as disruptive to coherence as a color inconsistency. The design system is the place where both kinds of discipline are declared together.

---

## Drift discipline

The vault file is the live implementation; this page explains the philosophy. When the brand evolves, the vault file changes first — the docs follow. The Linter's `design-system-drift` detector now reports consumer drift: off-palette colors, font sizes outside the scale, emoji in note titles, ad-hoc callout variants, and terminology/capitalization drift. Lifecycle link coloring ships in `memoria-link-colors.css`; when Supercharged Links exposes `data-link-lifecycle`, links gain a state accent without replacing the folder/type color.

This asymmetry is intentional: the vault file is the spec; consumers are subordinate to it. When they diverge, the answer is always "update the consumer to match the spec," never "update the spec to match a stray consumer."

---

## Related

- The visual-style discipline this system enables: [Visual-style discipline](visual-discipline.md)
- The callout types and their fixed three-color palette: [Callouts](callouts.md)
- Obsidian plugin inventory: [Obsidian plugins](../../reference/obsidian-plugins.md)
- Vault implementation file: `.memoria/design-system.md`


---

<!-- source: explanation/dashboards/README.md -->

# Dashboards

The **Inbox** is the *action queue* — discrete things that need you now. **Dashboards** are *browsable health views* — where things stand. They live in `spaces/`, `system/dashboards/`, and related Base files, are Bases/Dataview-backed and consumer-only, and a healthy vault shows them near-empty. Each answers one type of question; they are grouped by the kind of attention they demand:

| Group                                              | Dashboards                                                      | When you look                                     |
| -------------------------------------------------- | --------------------------------------------------------------- | ------------------------------------------------- |
| [Daily glance](daily-glance/README.md)             | Rail Now, Inbox queue action view                            | Start of every session — "what needs me?"         |
| [Synthesis agenda](synthesis-agenda/README.md)     | Reading pipeline, Discuss queue, Open questions, Contradictions | When deciding what to read, discuss, or reconcile |
| Project space                                      | Project gate                                                   | When steering a bounded inquiry to output          |
| [Structural health](structural-health/README.md)   | Maintenance collection, Drift watch, Loose ends, Board state  | Weekly maintenance and drift checks               |
| [Operational health](operational-health/README.md) | Fleet health, Audit log, Eval trend, Skill state            | When checking how the agent fleet is performing   |

The daily glance starts in the rail's **Now**: the Inbox is the daily action queue,
and Maintenance is the weekly structural-debt collection behind the health band.
**Board state is the Inbox board itself** — a Base over `inbox/`, not a separate query
page. Project gate is the Project space's steering surface: active thesis, saturation,
and structural-impact cache state. The synthesis-vs-structural split is by *actor*:
open-questions and contradictions are the **PI's** unfinished thinking; loose-ends and
drift-watch are the **Linter operation's** structural debt — kept separate, not collapsed.

## Why the dashboards are designed the way they are

Several principles cut across all of them.

Each dashboard surfaces one type of decision. Mixed queries produce lists the human can't batch-act on — a dashboard that asks "review these cards AND check these orphan notes" forces context-switching within a single glance. The single-decision constraint keeps the cognitive mode coherent.

The default state — nothing to review, everything healthy — should produce an empty or near-empty dashboard, not a list of green checks. Tables that always have rows train the human to ignore them. A dashboard that is always busy is a dashboard that stops being read. Empty is success, not a broken query.

Sort direction follows the decision type. Queues sort oldest-first because the oldest unreviewed item has waited the longest and should be acted on first. Logs sort newest-first because the most recent event is most actionable — investigating a log means starting from what just happened.

When a dependency is missing (a log file not yet created, fleet volume too low for meaningful statistics), dashboards show explanatory text rather than an error or a blank table. The graceful degradation is intentional: a new vault should not look broken just because data is still accumulating.

---

## Related

- Dashboard lookup table (source files, sort orders): [Dashboards](../../reference/dashboards.md)
- How to operate the dashboards: [Navigate the dashboards](../../how-to-guides/using-obsidian/navigate-the-dashboards.md)
- The primary weekly entry point: [Run the weekly review](../../how-to-guides/inbox/run-the-weekly-review.md)


---

<!-- source: explanation/dashboards/daily-glance/README.md -->

# Daily glance

What you check at the start of a session to answer "what needs me today, and is anything red?" The daily glance starts in the rail's **Now**: the Inbox action count opens the daily queue, while the health band opens Maintenance and Fleet health.

| Surface | Question it answers |
|---|---|
| [Daily glance](daily-health.md) | What needs me and what health signal is red? — the rail's Now |
| [Board state](board-state.md) | What's in flight? — the full Inbox board (`inbox.base`) |


---

<!-- source: explanation/dashboards/daily-glance/daily-health.md -->

# The daily glance view

The morning "is anything red?" glance starts at the rail's *Now*, one click from
wherever you are. The Inbox badge counts daily action cards; the health band counts
open drift cards and fleet lanes in `watch` or `act`.

The daily glance is the rail's always-visible action and health line. The budget is
30 seconds — glance, decide whether anything is red, close. If nothing is red, move
on to real work.

---

## What it shows

What populates the glance is intentionally small: non-structural `proposed` Inbox cards,
open `flag`/`alert` cards, and fleet metric notes in `watch` or `act`. The framing:
each is an "is anything red?" check, not a place to do work. Click through to the Inbox,
Maintenance, board-state, or fleet-health surfaces to act.

---

## What this surface is not

**Not a vault audit.** Folder counts, orphan notes, stale literature — those are the weekly review's job. The daily glance is *action and health status*, not *knowledge health*. Mixing them would turn a 30-second glance into a 20-minute triage session.

**Not a task list.** It shows decisions waiting on the human; the human chooses which to address. The Inbox cards, not the glance line, are where state changes happen.

**Not a substitute for the deeper dashboards.** It summarizes red signals; the full views live in Maintenance, `fleet-health`, and `audit-log`. It is a dashboard-of-dashboards: filtered subsets of those deeper views, reached by clicking through.

---

## Why it's designed this way

**Absorption beats a second launch surface.** A standalone daily-health page was one more thing to open every morning. The consumer-only, degrades-to-empty rationale is now carried by the rail: the glance is always exactly as fresh as its feeds.

**Graded loudness decides how urgent it is.** Open `flag` and `alert` cards count in the rail health band; loudness decides how they sort in Maintenance and whether they interrupt through other channels. Alert/block cards also record Telegram push attempts when written through the shared card writer, and open block cards pause new delegation plus review-gated promotion until resolved. The four-level loudness model and the "does it change what the PI does in the next 30 minutes?" test it turns on are owned by [Interaction channels](../../architecture/human-channels.md).

**Graceful degradation.** When a feed has no data yet — a fresh vault with no agent runs — the glance states what would populate it: empty means "nothing to report," not "something is broken" (the cross-cutting [graceful-degradation principle](../README.md#why-the-dashboards-are-designed-the-way-they-are)).

**30 seconds is a constraint, not an aspiration.** A daily ritual that consistently takes more than 30 seconds stops being daily. A healthy vault produces zeroed rail badges and an empty "Needs me" view, and the human closes it immediately. Length is a signal: a long glance means something needs attention, not that the ritual needs more time allocated.

---

## Related

- The board behind "Needs me": [The board-state dashboard](board-state.md)
- The weekly-ritual companion: [Run the weekly review](../../../how-to-guides/inbox/run-the-weekly-review.md)
- What populates the drift signals: [Drift watch](../structural-health/drift-watch.md)
- What populates the trust scores: [fleet-health dashboard](../operational-health/fleet-health.md)


---

<!-- source: explanation/dashboards/daily-glance/board-state.md -->

# The board-state dashboard

The board-state dashboard (`system/dashboards/board-state.md`) is the full Inbox board — the agent→human action queue. Open it from Maintenance when the Inbox's "Needs me" view isn't enough and you want everything: every card, every state, plus what the workers are executing underneath.

---

## What it shows

The page is built on **`inbox.base`** — the one Obsidian Base over `inbox/`, grouped by card type ([ADR-51](../../../adr/51-inbox-category-and-honesty-card.md)). Its **"Needs me"** view (cards in `proposed` — the same view the Inbox queue embeds) comes first; an **"All cards"** view (everything in flight, whatever its state) follows. A third section lists the **live worker cards** — the read-only markdown exports in `system/board/` that mirror what each Hermes lane is currently executing.

Cards in `proposed` are waiting on you; the queue converges to empty. That convergence is the design: batch screening never lands here as N cards (one aggregate work-prompt points at the worklist instead), so a long queue always means real decisions, not noise.

---

## What this dashboard is not

**Not a separate query page.** Board state *is* the Inbox rendered through a Base — the same files, the same state. Acting on a card here (its lifecycle edit) is the real action, not a mirror of one.

**Not the authoritative execution board.** The worker-card section reads the `system/board/` projections of `kanban.db`. Those are one-way and ephemeral — editing a projected file does nothing; the execution `status` chain is the hidden mechanic the PI never manages.

**Not the Inbox's "Needs me" view.** The Inbox shows only the daily `proposed` action slice. Board-state shows the whole board — everything in flight, plus the worker layer.

**Not [Discuss queue](../synthesis-agenda/discuss-queue.md).** Discuss queue is a Library-side cognitive-discipline view — sources read but not yet distilled. Board state is the action-and-execution view — cards, regardless of content.

---

## Why it's designed this way

**One Base, several views — not several dashboards.** "What needs me?", "what's in flight?", and "what are the workers doing?" are slices of one queue. Keeping them as views of `inbox.base` means there is exactly one definition of a card and one place its state lives.

**The lifecycle chain is the card state you see.** No execution vocabulary leaks into the view: `proposed` = awaiting you, `current` = acted on, `archived` = closed — the same chain every note uses, scoped to `inbox/` so card-state and note-state never collide.

**Worker cards are included but last.** They answer "is the machine actually working?" — useful when a lane seems stuck — but they are the mechanic's view, deliberately below the decisions the PI owns.

---

## Related

- The daily glance that links here through Maintenance: [The daily glance view](daily-health.md)
- How the projections work: [How the board surfaces in Obsidian](../../kanban-board/obsidian-projection.md)
- The card format: [The honesty card](../../kanban-board/card-schema.md)
- Troubleshooting board problems: [Fix a stuck card](../../../how-to-guides/troubleshooting/fix-stuck-card.md)


---

<!-- source: explanation/dashboards/synthesis-agenda/README.md -->

# Synthesis agenda

Library and Knowledge views that surface what to read, discuss, and reconcile — the queue of synthesis work. These are the *PI's* unfinished thinking; the structural-health group is the Linter's structural debt, and the actor-split rationale is in [Dashboards](../README.md).

| View | Question it answers |
|---|---|
| [Reading pipeline](reading-pipeline.md) | What's awaiting reading and distillation, and what claims came out of it? |
| [Discuss queue](discuss-queue.md) | Which read sources are worth a pass with the Co-PI before the claims firm up? |
| [Open questions](open-questions.md) | Which claims are still unconnected — the synthesis backlog? |
| [Contradictions](contradictions.md) | Which claims disagree with each other? |


---

<!-- source: explanation/dashboards/synthesis-agenda/reading-pipeline.md -->

# Reading pipeline

Open the Library space's Reading pipeline during a reading session when the queue feels full and you need to decide what to process next.

---

## What it shows

It shows what is in flight on the Library side and what has come out the other side — answering two questions at once: "what should I read next?" (source notes in `notes/sources/` at `lifecycle: proposed`, awaiting reading) and "what came out of my recent reading?" (claims in `notes/claims/` grouped by `maturity`). Sources you've read but not yet distilled into claims sit at `lifecycle: provisional` in between. The two halves together make visible whether reading is converting into synthesis.

---

## What this dashboard is not

**Not [Discuss queue](discuss-queue.md).** Reading pipeline is the broader working surface (sources in active processing plus claim maturity); Discuss queue is the narrow read-but-not-distilled slice, where that split and what it protects are spelled out.

**Not [Weekly review](../structural-health/weekly-review.md).** Weekly review is a scheduled ritual with a fixed top-to-bottom order. Reading pipeline is a working surface consulted between rituals, when deciding what to pick up next in a given session.

**Not a board view.** This view queries note state — source-note `lifecycle` and claim `maturity` — not cards. The [board-state dashboard](../daily-glance/board-state.md) view is the card side.

---

## Why it's designed this way

**Two Bases views, two cadences.** "Sources awaiting reading" answers a near-term question: what should I read this session? "Claims by maturity" answers a longer-term question: what is the durable output of all this reading? Showing both in one dashboard prevents optimizing one measure while ignoring the other — reading without synthesis, or synthesis without new sources.

**Source `lifecycle` is the in-flight signal.** A source note is `proposed` from the moment it's created until the PI reads it, then `provisional` once read but not yet distilled into claims, reaching `current` only when its claims are written. Reading-pipeline shows the `proposed` and `provisional` sources in `notes/sources/` — the pipeline's working middle band. (The Catalog entity behind each source is already `current` — facts don't queue; the *reading* does.)

**Sort by modification time, not creation date.** Recency of touch matters more than recency of intake. A source kept six months ago and annotated yesterday is more likely the PI's current focus than one catalogued yesterday but not yet touched.

---

## Related

- Narrower Library-discipline sibling: [Discuss queue](discuss-queue.md)
- Weekly rhythm that revisits this: [Weekly review](../structural-health/weekly-review.md)
- The state model behind `proposed`/`provisional`: [Lifecycle, not topic — and state, not folders](../../knowledge/lifecycle-over-topic.md)
- Next step after the pipeline surfaces a source: [Discuss a paper](../../../how-to-guides/library/discuss-a-paper.md)


---

<!-- source: explanation/dashboards/synthesis-agenda/discuss-queue.md -->

# Discuss queue

It is the **Library-side cognitive-discipline view**: a long queue means the human's processing is falling behind their intake rate; a short queue means it's keeping up. Making that asymmetry visible early is the point — before it hardens into a synthesis backlog months later.

---

## What it shows

Every source note at `lifecycle: provisional` — read, but not yet distilled into claims — oldest first. These are the sources worth a pass with the **Co-PI** (the Ask assist) before the claims firm up. The queue length *is* the signal: it measures the gap between how fast sources come in and how fast the human actually thinks them through.

---

## What this dashboard is not

**Not [Reading pipeline](reading-pipeline.md).** Reading pipeline is the broader view: all sources in active processing plus claim maturity. Discuss queue is a single focused signal: which read sources still owe a conversation. The implied next action is specific — open the Agent Client pane, work through the sharpening questions, then write the claims. A generic list without that implied action would just be noise.

**Not a generic to-do list.** Discuss-queue is not a general inbox or a catch-all task surface. Its one question is: which sources are read and waiting for the thinking step?

---

## Why it's designed this way

**The Co-PI is the discussion partner.** The queue drains through a conversation in the pane, never through an agent writing the claims itself — the grounded-questioning pass lives there ([The Agent Client pane](../../obsidian/agent-client-pane.md)).

**Five-or-fewer rows is healthy.** Ten or more rows is a signal to schedule a reading session. The goal is to make the queue's depth readable at a glance, without needing to count or calculate.

**A reading-session cadence, not a daily alarm.** Unlike the morning glance, Discuss queue is consulted at reading time. Opening it every morning would be noise; the queue doesn't change unless reading happens. The deliberate cadence is part of the discipline — this view exists to protect time for deep reading, not to add another daily obligation.

**It belongs to the Library space.** The Library space surfaces source intake, reading queues, and Catalog context together — everything literature processing needs in one dashboard note. The discuss-queue is one of those queues; the space exists to support its discipline without requiring a saved-layout switch.

---

## Related

- Broader sibling: [Reading pipeline](reading-pipeline.md)
- The conversation that drains this queue: [Discuss a paper](../../../how-to-guides/library/discuss-a-paper.md)
- What distillation produces: [Write a claim note](../../../how-to-guides/knowledge/write-a-claim-note.md)
- The space/reset layout model: [Obsidian workspaces](../../../reference/obsidian-workspaces.md)


---

<!-- source: explanation/dashboards/synthesis-agenda/open-questions.md -->

# Open questions

Turns the vault into a research agenda by surfacing the **unconnected claims** — `current` claim notes that no hub holds and nothing links to yet. Open it when planning the next reading direction — which claims has past synthesis raised that still haven't been woven into the rest of the corpus?

## What it shows

Every `current` claim note in `notes/claims/` with zero inbound links (`length(file.inlinks) = 0`), sorted oldest-first. These are the synthesis backlog: claims that stand alone, waiting to be connected to a hub or to other claims. The view doesn't propose the connections — it shows which claims are stranded, so you navigate to each and decide where it belongs.

## One source folder

The view reads from `notes/claims/` only. A claim with no inbound links is unconnected by definition; the sources that fed it are tracked separately by Library's Reading pipeline.

## What it is not

**Not a synthesizer.** It surfaces unconnected claims; it doesn't propose the links, cluster the claims, or rank them by importance.

**Not a tracker.** There's no `resolved:` state. When a claim gains an inbound link — a hub picks it up, or another claim references it — it simply drops off the list. The view reflects current link state; it doesn't remember history.

**Not auto-resolving.** Nothing in the system links these claims for you. The Librarian reads `research-focus.md` to guide discovery; the unconnected claims surfaced here can inform what you write there.

## Why inbound-link count, not a prose section

An unconnected claim is one nothing points to — a fact the corpus has captured but not yet integrated. Measuring it by inbound-link count (`file.inlinks`) catches that structurally, without depending on the PI to hand-author a "## Open questions" section. The cost is that it surfaces *which* claims are stranded, not a prose statement of what's unknown.

## Works on day one

Any `current` claim with no inbound links appears immediately. No plugin, no log file, no schema required.

## Related

- [Contradictions](contradictions.md) — closest sibling; both build the synthesis agenda (questions vs. tensions)
- Where the cycle is stuck: [The knowledge cycle](../../knowledge/knowledge-cycle.md)
- [Write a claim note](../../../how-to-guides/knowledge/write-a-claim-note.md) — where to put open questions in claim notes
- Where questions are generated: [Discuss a paper](../../../how-to-guides/library/discuss-a-paper.md)


---

<!-- source: explanation/dashboards/synthesis-agenda/contradictions.md -->

# Contradictions

Surfaces claim notes that disagree with each other as a synthesis starting point. Open it when building an argument or during the weekly synthesis pass — a cluster of contradictions is usually where the interesting writing is.

## What it shows

Every `current` claim carrying a PI-confirmed `contradicts` link (a typed entry in the note's `links:` block, so the query reads `links.contradicts` — [ADR-52](../../../adr/52-links-vs-relationships.md)) appears here, with the claim it contradicts and its `maturity`. Sorted by most-recently-modified first.

## What it is not

**Not an LLM tension-finder.** The view reads only confirmed `contradicts` links. Links are *authored*: the Librarian's link lane may propose a tension (with evidence and stance reasoning per edge), but the link exists only once the PI confirms it — no model ever auto-writes one.

**Not a truth judgment.** A `contradicts` link says two claims disagree, not which one is right. Resolving the tension is the human's call: soften one, supersede one with a newer claim, or keep both as a live productive debate.

**Not a defect list.** A paper that refutes an earlier one is a wanted finding. The view frames pairs as "worth resolving," never as errors to clear.

## How contradictions differ from supersession

A `contradicts` link records that two *current* claims disagree. `superseded_by` records that one claim *replaced* another over time — the older claim is `retracted`, with the lineage link preserved. A contradiction is an open tension; a supersession is a resolved one.

## Sparseness at the start is expected

Until you confirm `contradicts` links, the view is near-empty. That emptiness is meaningful: it tells you either that your corpus has no disagreements yet (unlikely) or that you haven't been filing contradiction links while reading. The first time you find yourself writing "paper X contradicts what I noted from paper Y," file the link and open this view.

## Related

- [Open questions](open-questions.md) — closest sibling; both build the synthesis agenda
- Setting the contradicts links: [Link related claims](../../../how-to-guides/knowledge/link-related-claims.md)
- Sweeps that surface contradictions: [Run a retraction sweep](../../../how-to-guides/operate/run-a-retraction-sweep.md)
- [Wikilink and link conventions](../../../reference/linking.md) — the `links:` block and the typed-link vocabulary


---

<!-- source: explanation/dashboards/structural-health/README.md -->

# Structural health

Views that surface drift, loose ends, board state, and the weekly maintenance agenda — the *Linter operation's* structural debt plus the worker-board view. The Maintenance collection (`spaces/maintenance.md`) is the rail target for this cadence. The synthesis-agenda group is the PI's unfinished thinking; the actor-split rationale is in [Dashboards](../README.md).

| View | Question it answers |
|---|---|
| Maintenance collection | Which weekly structural-debt views should I review together? |
| [Drift watch](drift-watch.md) | What drift have the Linter and the sweeps detected — which `flag`/`alert` cards are open? |
| [Loose ends](loose-ends.md) | Which `notice`-loudness `flag` findings are batched for the weekly pass? |
| [Board state](../daily-glance/board-state.md) | What work is in flight below the action queue? |
| [Weekly review](weekly-review.md) | What Friday sequence keeps Inbox, Maintenance, and Knowledge from aging? |


---

<!-- source: explanation/dashboards/structural-health/drift-watch.md -->

# Drift watch

Surfaces active and imminent drift — the Linter's and the verification sweeps' **open findings** — as one consolidated view. Open it when something feels wrong but the system looks clean: a lint pass came back clear yet things still seem off.

## What it shows

Maintenance's Drift watch view lists the open **`flag` and `alert` cards** — Inbox cards still in `proposed`, sorted loudest-first. Every detector finding becomes a card through the shared card-writer ([ADR-51](../../../adr/51-inbox-category-and-honesty-card.md)), so the view is a filtered slice of the same queue everything else uses: a `flag` is a verification/integrity issue (leading with its `finding` and `agent_recommendation`), an `alert` is a drift or retraction notice. The producing operations are the **Linter** (schema validation, link/relationship resolvability, orphans, golden-copy drift — daily cron + the pre-commit hook) and the **verification sweeps** (retraction lookups, near-duplicate and broken-citation detection).

Loudness is the headline: all open `flag` and `alert` cards count in the rail health band, and this view sorts the actionable list loudest-first. `block` cards pause new delegation and review-gated promotion until the PI resolves the card; quieter cards wait in Maintenance for the weekly review. (The four-level loudness model and the "next 30 minutes" test it follows are owned by [Interaction channels](../../architecture/human-channels.md).)

## What it is not

**Not audit-log or fleet-health.** Drift-watch is the *structural* view — open integrity findings, headlined by the verdict band; audit-log is per-write forensics and fleet-health is the operational aggregate. For the full three-way distinction, see [Operational health](../operational-health/README.md#audit-log-vs-fleet-health-vs-drift-watch).

**Not for content hygiene.** Stale literature and unfinished-looking filenames surface in the weekly review and Loose ends, not here. Drift watch is reserved for what the operations can *detect mechanically* — the "silent" failures the human wouldn't notice by reading content.

## When drift-watch becomes relevant

Drift-watch is most useful after changes that could desynchronize the deployed system from its source: a release refresh, edits to profile files, plugin upgrades, or anything that appears in the audit log as an anomaly. The detectors exist precisely because these desynchronizations are invisible at the content level — the vault looks clean because the content is unchanged, but a system file has drifted from the golden copy or a schema no longer matches its records. (Detected golden-copy drift comes with a restore path: `lint:restore`, propose-only.)

The Friday weekly review includes a drift-watch pass because a week of ordinary operation also accumulates small `notice`-level findings that are not individually urgent but benefit from regular review.

## Before it has real data

Until the daily lint cron and the sweeps have run, this view is empty — which on a fresh vault means "nothing checked yet," not "all clear." After the first pass, empty means clean: the queue of open findings converges to zero as the PI acts on or archives the cards. (Why an empty view is the healthy state at all is the cross-cutting [empty-is-success principle](../README.md#why-the-dashboards-are-designed-the-way-they-are).)

## Related

- [Operations](../../operations/README.md) — the Linter and the sweeps, and what each catches
- [audit-log dashboard](../operational-health/audit-log.md) — per-decision forensics layer below structural drift
- [The honesty card](../../kanban-board/card-schema.md) — the `flag`/`alert` card format and loudness levels
- [Linter: detectors and auto-fix](../../../reference/linter.md) — detector severity reference


---

<!-- source: explanation/dashboards/structural-health/loose-ends.md -->

# Loose ends

Batches the lowest-stakes structural debt — the `flag` cards the Linter raised at **Notice** loudness. Run it from Maintenance during the weekly review or whenever you want to clear cosmetic findings in one pass. The view lists; you decide the action per card.

## What it shows

The `flag` cards in `inbox/` still in `proposed` with `loudness = notice`, sorted oldest-first (`file.ctime ASC`) — each row carrying its `type`, `finding`, and `raised_by`. Older findings have lingered longest and lead the list. These are cosmetic and low-stakes integrity findings the Linter deliberately keeps out of the action queue; they wait here for the weekly batch.

## Why Notice loudness and not louder findings

Loudness, not finding type, is what routes a card here. Louder findings surface higher in Drift watch — they need attention sooner. Loose ends is reserved for the `notice` tail: real findings, but none worth interrupting the PI for. Batching them into the weekly pass keeps the action queue quiet without losing the debt. (The loudness model the routing follows is owned by [Interaction channels](../../architecture/human-channels.md).)

## What it is not

**Not Drift watch.** Drift watch shows the full open `flag`/`alert` set, loudest-first. Loose ends shows only the `notice`-loudness `flag` tail. Same card queue, different loudness slice.

**Not data-quality validation itself.** The Linter detects the issues — empty frontmatter, weak naming, soft integrity smells — and writes the cards. Loose ends is the *view* over the Notice-level subset, not the detector.

## Works once the Linter has run

Loose ends reads the Inbox card queue, so it's empty until the Linter's first pass writes `notice`-level `flag` cards. After that, an empty view means the Notice-level debt is clear — the cards converge to zero as the PI acts on or archives them (the cross-cutting [empty-is-success principle](../README.md#why-the-dashboards-are-designed-the-way-they-are)).

## Related

- [Weekly review](weekly-review.md) — the Friday ritual that includes a loose-ends pass
- [Drift watch](drift-watch.md) — the louder `flag`/`alert` findings; loose ends is the Notice-level tail
- [The honesty card](../../kanban-board/card-schema.md) — the `flag` card format and loudness levels


---

<!-- source: explanation/dashboards/structural-health/weekly-review.md -->

# Weekly review

The weekly review is the Friday ritual that keeps the Inbox, Maintenance, and Knowledge views from aging into noise. It gathers the week's accumulated content decisions — a full Inbox, candidate cards awaiting triage, claim maturity to revisit, new catalog entries and notes, and quiet-level findings — into one ordered pass. The discipline is **one ritual per week** — not "open whenever." A weekly cadence is what prevents the vault from accumulating drift faster than it produces synthesis. (For the actionable top-to-bottom sequence, see [run the weekly review](../../../how-to-guides/inbox/run-the-weekly-review.md); the ordering rationale is below.)

---

## What this dashboard is not

**Not [the daily glance](../daily-glance/daily-health.md).** The daily glance is the morning rail check — 30 seconds, action and health signals, close if green. Weekly review is the knowledge ritual — 90 minutes, deliberate human decisions about content. Different rhythm, different scope, different cognitive mode.

**Not one monolithic page.** The ritual uses the Inbox queue, Maintenance's Drift watch / Loose ends / New this week sections, and Knowledge's claim views. Weekly review is the order of operations, not a separate runtime dashboard.

**Not auto-actioned.** Every section requires a human decision: promote or defer, archive or keep, include or exclude. Nothing in this ritual changes state on its own. The human is the agent of all state changes it surfaces.

---

## Why it's designed this way

**Top-to-bottom ordering follows the workflow logic.** Inbox review unblocks downstream synthesis, so it comes first. Promotion comes before metrics because the metrics reflect promotion behavior — reviewing metrics before doing the promotions would show stale numbers. The sequence is not aesthetic; it is causal.

**Empty sections are the goal, not a bug.** A healthy week leaves most sections empty — recognizing that as success rather than a broken view is the cross-cutting [empty-is-success principle](../README.md#why-the-dashboards-are-designed-the-way-they-are), applied here per section.

**The orphan check has a coverage angle.** Beyond the raw orphan count (notes with zero inbound links), the check surfaces qualifying notes that should connect to current work but don't. This catches missing coverage, not just disconnected notes — the difference between a note that genuinely stands alone and a note that should be connected but hasn't been.

**Schema migration progress lives in Maintenance.** Structural maintenance (schema drift, plugin config changes) belongs in Drift watch. The weekly review includes that check, but does not turn structural drift into a content-decision queue.

---

## Related

**Explanation**

- The morning glance this complements: [Daily glance](../daily-glance/daily-health.md)
- Reading-side companion: [Reading pipeline](../synthesis-agenda/reading-pipeline.md)
- Why the ritual matters: [The knowledge cycle](../../knowledge/knowledge-cycle.md)
- The dashboards overview: [Dashboards](../README.md)

**How-to**

- How to run the ritual: [run the weekly review](../../../how-to-guides/inbox/run-the-weekly-review.md)

**Background**

- Structural drift companion: [Drift watch](drift-watch.md)


---

<!-- source: explanation/dashboards/operational-health/README.md -->

# Operational health

Dashboards that track how the agent fleet is performing and what it decided.

| Dashboard | Question it answers |
|---|---|
| [Fleet health](fleet-health.md) | Are the agents performing well over time? Is cost trending up? |
| [Audit log](audit-log.md) | What did the policy MCP decide, and why? |
| [Eval trend](eval-trend.md) | Is the deployed system still finding, extracting, linking, and verifying correctly on this vault? |
| [Skill state](skill-state.md) | Which skills are active in which lane? Do lane policy and shipped skills agree? |

## Audit log vs fleet health vs Drift watch

Three dashboards sit close together but answer different questions at different layers — keeping them distinct is deliberate:

- **Audit log** is the *raw event stream*: one entry per policy-MCP write decision (per-decision forensics, newest-first).
- **Fleet health** *aggregates* those entries (and other signals) into rolled-up per-lane trend metrics over time — quality and cost of completed work, headlined by the trust score.
- **[Drift watch](../structural-health/drift-watch.md)** is *structural*, not operational: it is the Maintenance view over the Linter operation's open integrity findings, headlined by the verdict band — a different cadence and abstraction layer from the other two.

In short: audit log is per-decision, fleet health is aggregated-operational, Drift watch is aggregated-structural.


---

<!-- source: explanation/dashboards/operational-health/fleet-health.md -->

# `fleet-health` dashboard

Tracks whether the Hermes agent fleet is performing well over time. This dashboard matters once the fleet is doing enough work per week that one stuck card or one runaway loop is hard to spot by eye.

## What it shows

Operational health per lane over time: cost per task, success rate, retry frequency, review latency, PI attention timing, blind re-review sample counts, and the headline **trust score** (0–100). The trust score is the number to read first; the rest are the signals it rolls up or reports alongside it.

The point of a composite is that no single signal dominates: a lane can have a perfect citation-check record yet a low score if its proposal accept rate signals rubber-stamping, and a high accept rate paired with a low success rate still scores low. That is what makes the number a summary of overall lane health rather than a measure of any one metric. The inputs, the band thresholds, and the accept-ratio extremes (both too-high and too-low down-weight the lane) are specified in the [Dashboards](../../../reference/dashboards.md#trust-score-fleet-health) reference.

## What it is not

**Not board-state.** Board-state shows what work is currently in flight. Fleet-health shows the quality and cost of completed work over time.

**Not audit log or Drift watch.** Fleet health aggregates completed work into operational trends (trust score is its headline); audit log is per-decision forensics, and Drift watch is the structural sibling (verdict band is its headline). For the full three-way distinction, see [Operational health](README.md#audit-log-vs-fleet-health-vs-drift-watch).

## When it shows real data

The dashboard and its metrics aggregator ship in `src/` and deploy with the vault. It reads `system/metrics/lane-*-<week>.md`, which the `memoria-metrics` cron computes from `system/logs/`. It shows meaningful data only once weekly fleet volume accumulates — a vault with two runs per week produces statistics that are directional at best. Until volume builds up, board-state and audit-log catch issues directly. Low-volume lane notes are marked `insufficient-data` so the table remains backed by real emitted data without pretending the sample is actionable.

## Related

- [audit-log dashboard](audit-log.md) — per-decision forensics that feed the deny-rate input
- [Drift watch](../structural-health/drift-watch.md) — structural complement; verdict band is the structural sibling of trust score
- [Dashboards](../../../reference/dashboards.md#trust-score-fleet-health) — trust score formula, inputs, and band definitions


---

<!-- source: explanation/dashboards/operational-health/audit-log.md -->

# `audit-log` dashboard

The forensic trail for every vault write the policy MCP touched. Open it when something feels off — a worker behaving unexpectedly, a card stuck with an unclear reason, or after a scheduled overnight run completes.

## What it shows

The dashboard reads directly from `system/logs/audit.jsonl` — the append-only policy MCP event stream. Its primary view is **recent denies and dry-runs**, sorted newest-first and capped at 30. These are the action queue: anything here for more than a day without a corresponding board card is an unhandled escalation.

A second view lists **writes to review-gated zones** (`notes/claims/`, `notes/hubs/`) for periodic audit. Even when these writes were allowed, they warrant occasional review because they represent changes to canonical content.

Further views round out the forensic picture: **per-profile activity over the last 24 hours** (who wrote what, at a glance), **hash drift / tamper detection** (vault-hash mismatches between consecutive entries), **anomalies** (malformed or out-of-order entries in the stream itself), and a **log size** check (when to rotate).

## What it is not

**Not fleet health or Drift watch.** The audit log is the raw event stream — one JSON object per write decision; the other two aggregate. For where each sits, see [Operational health](README.md#audit-log-vs-fleet-health-vs-drift-watch).

**Not editable.** The log is append-only by design: each mutating write is recorded with a hash pair so the action stays reversible, and editing the log would break that. This view flags a path whose recorded after-hash no longer matches the file; the Linter's `audit-unpaired-writes` detector flags a write whose pairing never completed. The hash-pairing mechanism and the full entry schema are owned by [Policy MCP](../../../reference/policy-mcp.md).

## Why a spike in denies is a security signal

Memoria ingests untrusted PDFs — a potential indirect prompt injection surface. A sudden rise in policy MCP denials can indicate an injection attempt coaxing an agent toward unauthorized writes, not just operator error. The audit log is the primary place this signal appears; open it after any unexpected agent behavior.

## Log size

The dashboard reads the whole `audit.jsonl` and caps each *view* (e.g. 30 recent denies), so the surface stays bounded even though the log itself is append-only **forever** — never rotated ([ADR-25](../../../adr/25-session-logging-two-logs.md)); the Linter's `audit-log-size` advisory surfaces growth past 50 MB. The audit log's substrate is reference detail — see [Memory substrates](../../../reference/memory.md); the event-field schema lives in [Policy MCP](../../../reference/policy-mcp.md).

## Related

- [Drift watch](../structural-health/drift-watch.md) — structural drift findings (complementary layer)
- [fleet-health dashboard](fleet-health.md) — trend aggregations that consume this stream
- [Policy MCP](../../../reference/policy-mcp.md) — the decision protocol and action vocabulary the log records


---

<!-- source: explanation/dashboards/operational-health/eval-trend.md -->

# `eval-trend` dashboard

Tracks whether the deployed system still finds, extracts, links, and verifies correctly *on this vault* — the vault-eval capability trend ([ADR-11](../../../adr/11-vault-eval-maintenance.md)). It matters because capability regressions are silent: a profile prompt drift, a model change, or gold-set rot degrades answers without producing an error anywhere else.

## What it shows

One row per scored quarter, from `system/metrics/eval/runs.jsonl` — the append-only log the deterministic scorer (`eval_score.py`) writes after each eval run. Three aggregate metrics, each 0–1 and higher-is-better:

- **recall@k** — did retrieval surface the gold target citekeys in the top *k*?
- **support-rate** — did the cited evidence resolve to real catalog records, or was it fabricated?
- **FAMA-clean** — was any superseded or archived claim reused (the FAMA failure mode the supersession mechanism makes measurable)?

Below the trend, the latest run breaks out per gold task, including each lane's rubric **self-score** for comparison — recorded, not trusted: only the machine metrics aggregate.

## What it is not

Not a gate. The verdict is diagnostic by design — unlike drift-watch's structural FAIL, an eval dip informs the human and pauses nothing. Capability scores are noisy; gating on them invites Goodharting and false halts ([ADR-11](../../../adr/11-vault-eval-maintenance.md), Alternatives).

It is also not a claim of completeness. A gold task whose card reported no machine-readable result shows as **unscored** — the dashboard is honest about what it could not measure rather than backfilling a number.

## Why the scorer is deterministic

The lanes already self-score against the rubric on their cards, but a self-score is the system grading its own homework. The trend you act on must come from zero-LLM checks against vault state — set membership in the catalog, frontmatter lifecycle on claims — so that a score change means the *system* changed, not the grader.

## Related

- The contract and metric definitions: [Vault eval](../../../reference/vault-eval.md)
- The operational sibling: [fleet-health dashboard](fleet-health.md)
- The decision: [ADR-11](../../../adr/11-vault-eval-maintenance.md)


---

<!-- source: explanation/dashboards/operational-health/skill-state.md -->

# `skill-state` dashboard

Which skills are active in which lane. This is the visibility surface [ADR-43](../../../adr/43-skill-governance.md) adopted when the skill inventory no longer fit in the operator's head: "which lane can do what?" needs an answer that doesn't require opening ten YAML files.

## What it shows

The dashboard reads the runtime governance layer directly at view time — the lane ceilings in `.memoria/lane-overrides/*.yaml` (`policy.allow.skills` / `policy.deny.skills`) and the `SKILL.md` folders each profile ships under `.memoria/profiles/*/skills/` — and renders three views:

- **Lane policy at a glance** — per profile: the runtime skill gates the lane allows and denies, and how many skills the profile actually ships.
- **Shipped skills** — every `SKILL.md` with its declared lane, `skill_id`, and the runtime skills it relies on.
- **Consistency checks** — the decision queue: rows appear only where the lane policy and the shipped skills disagree (a skill folder whose frontmatter contradicts where it ships, a duplicate `skill_id`, a skill relying on a runtime gate its lane denies or doesn't list, a profile with no lane override). Empty is success.

Because it reads the live files rather than a generated snapshot, the dashboard cannot drift from the configuration — it *is* the configuration, rendered.

## What it is not

**Not a lifecycle tracker.** ADR-43's alternative shape — an `intake → … → archived` state machine with per-skill governance notes in `system/skills/` and an onboarding checklist — was explicitly not adopted ([ADR-43](../../../adr/43-skill-governance.md) records why). A skill has no recorded state beyond *shipped and allowed*; the lane-override files plus the profile `skills/` folders are the system of record.

**Not an enforcement surface.** The policy gate and the profile configs enforce; the Linter monitors; this dashboard only renders ([ADR-49](../../../adr/49-catalog-in-bases-linter-monitor.md): dashboards are the view layer). An "outside the allow list" row is a question for the operator, not a block — the dependency may be an MCP server governed by `config.yaml` rather than a skill gate.

## Related

- [ADR-43: Skill governance and lifecycle](../../../adr/43-skill-governance.md) — the dashboard-only decision and the rejected state machine
- [fleet-health dashboard](fleet-health.md) — how the lanes are *performing*; this dashboard is what they are *permitted*
- [audit-log dashboard](audit-log.md) — what the policy gate actually decided, write by write
- [Profile capabilities](../../../reference/profiles.md) — the lane model the overrides express


---

<!-- source: explanation/deployment/README.md -->

# Deployment

How Memoria is packaged, installed, and deployed. These pages explain the _rationale_ behind the distribution model and the installer — for the operational steps see the [setup how-to guides](../../how-to-guides/setup), and for exact inventories see [Installer (bootstrap)](../../reference/installer.md).

| Page                                          | What it explains                                                                                                                                                    |
| --------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| [Distribution model](distribution-model.md)   | How profiles and the vault are packaged and installed — the repo as the install unit, idempotent deploy, and generated capability blocks                            |
| [Bootstrap installer](bootstrap-installer.md) | The one-command installer's design and decided rules for native Windows production and Linux/WSL testing                                                           |
| [Deployment options](deployment-options.md)   | The adopted `local-only` default and the conventions common to every sync pattern (Git history, `memoria.bib` in-vault, the append-only audit log, one dispatcher per vault) |
| [Always-on VPS design](always-on-vps-design.md) | Deferred `always-on` topology and validation shape; not a supported setup path. |

---

## Related

- The steps to actually install: [Setup how-to guides](../../how-to-guides/setup)
- Installer inventories (what gets copied where): [Installer (bootstrap)](../../reference/installer.md)
- The repo-as-install-unit decision: [ADR-26](../../adr/26-repo-as-install-unit.md)


---

<!-- source: explanation/deployment/distribution-model.md -->

# Distribution model

Memoria ships as a single repo (`memoria-vault`). **The repo is the install unit** ([ADR-26](../../adr/26-repo-as-install-unit.md), as amended by [ADR-55](../../adr/55-src-scaffold-populate-golden-copy.md)) — you clone it (or run the one-line bootstrap, which clones it for you), and the bootstrap installer at the repo root deploys everything. The repo has three parts:

| Path | Contents | Audience |
| --- | --- | --- |
| `scripts/install.ps1` / `scripts/install.sh` (repo root) | The **bootstrap installers**: native Windows production via PowerShell, Linux/WSL testing via bash. Both derive the vault from `src/` and deploy the same profile/runtime source. | End users (run once). |
| `src/` | **Source files only — never a live vault**: templates, profiles, skills, schemas, dashboards, patterns, and `.obsidian` config. The installer *scaffolds* the vault tree and *populates* it from here. | The installer (and contributors). |
| `docs/` | Architecture, workflow, and decision documents. Not needed at runtime. | Developers and contributors. |

The installer derives the running vault from `src/` at a working location (off OneDrive on Windows); the human opens **that deployed vault** in Obsidian. The deployed vault is self-contained — it does not carry `docs/`, so any reference from a vault-resident file (e.g. `home.md`) to `docs/` is a **GitHub Pages URL, never a relative path**. The installers live at the repo root (not inside `src/`) because the bootstrap is the clone/entry point; installing requires the whole repo. See [Bootstrap installer](bootstrap-installer.md) for the installer's design and [Installer (bootstrap)](../../reference/installer.md) for the component inventories.

Shipping `src/` rather than a live `vault/` template is deliberate ([ADR-55](../../adr/55-src-scaffold-populate-golden-copy.md)): a live-vault template blurs "source of truth" with "a running instance," invites accidental edits to the template, and offers no recovery path. With `src/`, authoring (the repo) and restoring (the runtime golden copy) stay cleanly separate, and user content and system files are structurally distinct from the first minute.

---

## What ships in `src/`

`src/` carries three kinds of source: the **vault skeleton** (the type-first category tree, [ADR-47](../../adr/47-type-first-category-folders.md), with templates, dashboards, Bases, and `home.md` pre-populated), the **`.obsidian/` config**, and the **`.memoria/` scaffold** (profiles, operations, the policy MCP, schemas, lane-overrides, scripts, and `memoria.bib`). The full directory catalog — every folder and what it holds — is owned by [On-disk layout](../../reference/on-disk-layout.md); the design rationale for the category tree is [The vault](../architecture/vault.md). Empty content dirs are recreated by the installer's scaffold step, checked against the machine-read folder map (`.memoria/schemas/folders.yaml`).

## The golden copy: the restore source

At install time, every system file is also staged at `<vault>/.memoria/golden/` with a hash manifest. That golden copy is what makes the deployed vault **self-healing for system files**: the Linter's daily pass compares the live system files against the manifest, flags drift, and can restore a corrupted or hand-mangled file from the known-good baseline (`lint:restore` — propose-only by default) without re-running the installer. Releases refresh the golden copy by fresh install — never by in-place migration, whose half-migrated states [ADR-55](../../adr/55-src-scaffold-populate-golden-copy.md) avoids.

---

## The five profiles: one shared layer, four profile files

The agents ship as five hand-authored profile directories under `src/.memoria/profiles/` — `memoria-copi`, `memoria-librarian`, `memoria-writer`, `memoria-peer-reviewer`, `memoria-engineer`. Each agent is a **shared layer + a unique layer** ([ADR-48](../../adr/48-copi-and-agent-consolidation.md)):

- **Shared:** `AGENTS.md` — the one "how we work in this vault" instruction set every agent reads, living in the vault root so there is exactly one copy of the house rules.
- **Unique per agent:** `SOUL.md` (its posture — the stable stance, like *faithful* or *skeptical*), `config.yaml` (model, tools, and MCP connections), optional `skills/` (assigned per lane), and `distribution.yaml` (packaging metadata).

So the agents share the house rules but each brings its own stance and toolset. Common policy has one home (`AGENTS.md`), and what remains per-profile is genuinely per-profile. At five profiles, a full profile compiler remains unnecessary. The narrow capability blocks in `config.yaml` are materialized from `src/.memoria/tool-registry.yaml` by `scripts/render_profile_configs.py`, so the tool allowlist has one owner while the runtime still receives plain Hermes `config.yaml` files.

## Why the profile install is idempotent

The bootstrap's profile-install step (also runnable on its own via `--profiles-only`) is designed to be re-run after profile source or secret changes without care about current deployed profile state. It writes every author-owned profile file (profile sources, MCP configs, lane-override templates) and leaves human-owned secrets (`.env`, any local overrides) untouched.

The idempotency matters because it is the mechanism that keeps deployed profiles synchronized with their source. Without it, the profile directories under `~/.hermes/profiles/` would drift from the vault source over time — a drift the Linter detects but the re-run fixes; making the re-run safe is what makes the fix actionable.

---

## Running more than one vault

Nothing in the distribution model is single-vault by design — you can fork the starter vault for a second project and run both at once. Coexistence works because three resources two vaults would otherwise contend for can each be isolated:

| Resource | What collides if shared | Isolation |
|---|---|---|
| **Obsidian REST API port** | Both Local REST API plugins bind the same HTTPS port; the second to start can't bind, so its `OBSIDIAN_MCP_PORT` serves nothing (or points Hermes at the wrong vault). | A distinct HTTPS port per vault, with each vault's profiles' `OBSIDIAN_MCP_PORT` and `OBSIDIAN_MCP_SSL_VERIFY` matching that instance. |
| **Hermes profiles** | Profiles substitute one `VAULT_PATH` at install; a shared `HERMES_HOME` points `memoria-*` at whichever vault was installed last, so the other vault's agents read and write the wrong tree. | Unique per-vault aliases (`project2-*`) **or** a separate `HERMES_HOME` per vault. |
| **Kanban queue** | The board/queue (`hermes kanban`) is Hermes runtime state under `HERMES_HOME`, **not** a file in the vault — so a shared `HERMES_HOME` is one shared queue: cards from both vaults intermix and cron fires against the wrong vault. | A separate `HERMES_HOME` per vault gives each its own independent queue. |

For full isolation, use a distinct REST port **and** a separate `HERMES_HOME` per vault. The step-by-step procedure is in [Add a second vault](../../how-to-guides/setup/add-a-second-vault.md).

---

## Related

- The installer's design: [Bootstrap installer](bootstrap-installer.md)
- The decisions: [ADR-55](../../adr/55-src-scaffold-populate-golden-copy.md), [ADR-26](../../adr/26-repo-as-install-unit.md)
- Profile structure: [Profiles](../profiles/README.md)
- Operationalizes idempotent deployment: [Redeploy profiles](../../how-to-guides/operate/redeploy-profiles.md)
- On-disk layout reference: [On-disk layout](../../reference/on-disk-layout.md)


---

<!-- source: explanation/deployment/bootstrap-installer.md -->

# Bootstrap installer

The bootstrap installers — [`scripts/install.ps1`](https://github.com/eranroseman/memoria-vault/blob/main/scripts/install.ps1) for native Windows production and [`scripts/install.sh`](https://github.com/eranroseman/memoria-vault/blob/main/scripts/install.sh) for Linux/WSL testing — take a user from nothing to a runnable Memoria install in one command: they scaffold and populate the vault from `src/`, stage the golden copy, provision the Hermes runtime and the five agent profiles, wire the crons, and guide Obsidian setup.

This page explains *why* the installer is shaped the way it is. The concrete inventories — platform matrix, install-flow steps, the component checklist, the secrets and skills tables — are reference material in [Installer (bootstrap)](../../reference/installer.md).

## Why a bootstrap

Before the bootstrap, the shipped installer did only one of the setup steps — register the Hermes profiles from an already-cloned repo. Everything else was manual and spread across five how-to guides, and a new user had to already have the whole stack installed before any of it worked. The gap was a single, guided first-run path — which is what the bootstrap is.

## The flow: scaffold, populate, golden copy

What the installer ships and stages — the `src/`-not-a-live-vault separation and the hashed `<vault>/.memoria/golden/` restore baseline — is the distribution mechanism, owned by [Distribution model](distribution-model.md). What the installer adds is the *flow* over that mechanism: **scaffold** the folder tree (checked against the machine-read folder map `.memoria/schemas/folders.yaml`), **populate** it from `src/`, **stage the golden copy**, then wire the pre-commit hook, install Hermes and the five profiles, offer the optional cluster stack, install Obsidian if absent, and wire the crons. The ordered install-flow steps, the component checklist, and the cron list are owned by [Installer (bootstrap)](../../reference/installer.md); the five-profile roster is [Profile capabilities](../../reference/profiles.md).

One installer-specific sequencing choice worth calling out: Zotero deliberately *left* the installer — it is the PI's bibliographic-backbone choice, not core provisioning, so its setup moved to the tutorial.

## Goals and non-goals

**Goals**

- One command from zero to a runnable vault on native Windows production and Linux/WSL testing.
- Fresh-install by default, with an idempotent per-profile deployment path (`scripts/install.sh --profiles-only`) for profile source and secret changes.
- Detect-then-install; never clobber existing apps, credentials, or user content.
- Honest about what it cannot do (secrets, GUI steps) — explain, don't fake.

**Non-goals**

- Writing the user's API keys for them.
- Supporting macOS or non-Debian Linux distributions as first-class install targets.
- In-place migration between releases — releases are delivered fresh-install, per [ADR-55](../../adr/55-src-scaffold-populate-golden-copy.md).

## Entry point and safety model

The installer is offered two ways, with **inspect-first as the documented primary** (download, read, then run) and the `curl | bash` / `irm | iex` one-liner shown only as the convenience option. The standard precautions for a piped installer are applied: the entire script body is wrapped in a `main` function invoked on the last line, so a truncated download cannot execute a half-command; it prints a numbered plan and prompts for consent (skippable with `--yes` for CI); `--dry-run` prints every action without executing; and it never silently elevates — if a step needs `sudo`/admin it stops and prints the exact command. These rails are cheap insurance for a script that installs system software, and `--dry-run` doubles as the WSL command transcript (below).

## Production Windows and Linux testing

Per [ADR-64](../../adr/64-native-windows-support.md), Memoria uses a two-script
platform split:

- **Windows production:** `scripts/install.ps1` is the native Windows installer. It runs the official Hermes Windows installer, copies `src/` into the production vault, creates the vault-local MCP venv, deploys profiles and the policy-gate plugin, and wires Hermes crons.
- **Linux/WSL testing:** `scripts/install.sh` remains the Linux/WSL test installer and CI/disposable-vault path.

The production path has no `/mnt/c` vault path, no WSL2 gate in the PowerShell
installer, and no `windowsWslMode` requirement for the Agent Client pane on production
Windows. WSL-specific test docs open the ext4 test vault with Linux Obsidian on
the native path; mirrored networking is only relevant for an explicit split
where WSL Hermes talks to Windows Obsidian serving a Windows-hosted vault.

## Architecture: two installers, one source tree

There are two installers because production and testing deliberately run on
different operating systems:

- **`scripts/install.ps1` (PowerShell)** is the native Windows production installer. It owns Windows app guidance, Hermes native install, vault population, MCP deps, profile deployment, policy plugin deployment, and cron wiring.
- **`scripts/install.sh` (bash)** is the Linux/WSL testing installer. It keeps the same vault/profile contracts so CI and disposable Linux validation exercise the same authored source under `src/`.

Both files live at the repo root because the bootstrap is the clone/entry point,
not a vault-internal artifact. The duplication is intentional at the shell
boundary; shared behavior stays in the deployed vault source and deterministic
Python operations.

## Simplifying decisions

Each trades a little breadth for much less shell to build and maintain:

- **Guide app install, don't fully automate.** Detect Obsidian; if absent, print the exact `winget`/`apt` one-liner and run it on consent — no version parsing, no silent installs.
- **Presence checks, not version gates.** Check a tool is there; let `pip`/Hermes surface a clear error if the installed tool lacks a required capability.
- **Don't install language runtimes.** The Hermes installer provisions uv, Python, Node, ripgrep, and ffmpeg; the bootstrap adds only **Git** (pre-Hermes) and **Pandoc** (not provisioned by Hermes).
- **Assume `local-only` deployment.** No Syncthing/VPS/sync logic — multi-device is a later phase.
- **Default the vault off OneDrive** (`%USERPROFILE%\Memoria` on Windows, `~/Memoria` on Linux; prompt to override) — OneDrive fights Obsidian indexes and file locks, and Git is the backup, so losing OneDrive sync of the vault is fine.
- **The vault's git repo is the user's own.** The installer never `git init`s under a synthetic author; it prints the commands and the user commits with their own identity.

## Trade-offs

- **Surface area** is still nontrivial (native Windows plus Linux/WSL installers, cron wiring), cut hard by the simplifying decisions above; the residue leans on upstream installers and on guidance for the secret steps that genuinely can't be automated.
- **`curl | bash` trust** is inherent to the pattern; mitigated by inspect-first framing, the `main`-guard, consent, and `--dry-run`.
- **Partial automation can imply full automation** — the secrets steps are assisted, not automatic, so the UX must make that explicit.
- **Fresh release installs replace in-place migration.** This keeps the bootstrap small and avoids half-migrated vault states; profile redeploy remains the narrow idempotent path.

## Related

- **Reference:** [Installer (bootstrap)](../../reference/installer.md) — platform matrix, install-flow steps, component checklist, secrets and skills tables.
- **Decisions:** [ADR-55](../../adr/55-src-scaffold-populate-golden-copy.md) (src/ + scaffold-populate + golden copy), [ADR-26](../../adr/26-repo-as-install-unit.md) (the repo is the install unit).
- **Explanation:** [Distribution model](distribution-model.md), [Why Hermes](../rationale/why-hermes.md) (the runtime the installer provisions).
- **How-to:** [Quickstart](../../how-to-guides/setup/quickstart.md), [Set up the vault](../../how-to-guides/setup/set-up-the-vault.md).


---

<!-- source: explanation/deployment/deployment-options.md -->

# Deployment options

The system spans a **vault** (knowledge layer) and an **execution layer** (Hermes profiles, MCPs). Where each lives — and how they sync — is a human decision with real trade-offs. The supported install path is **`local-only`**. The multi-machine topologies (`local-mesh`, `obsidian-sync`, `always-on`) and the secondary-device operating patterns are a forward-looking capability, specified in [multi-machine deployment](../../adr/63-multi-machine-deployment.md).

| Pattern | Sync mechanism | Always-on agent | Zotero API access | Ongoing cost | When to use |
| --- | --- | --- | --- | --- | --- |
| **`local-only`** (default) | Git (manual pull / push) | ❌ Workstation must be on | ✅ Full localhost:23119 | $0 infra | Simplest start; single workstation; no discovery loop |
| `local-mesh` | Syncthing peer-to-peer (no VPS) | ⚠️ Primary device when on | ✅ Full localhost on primary | $0 infra | Desktop + laptop; auto-sync without cloud or VPS — see the [multi-machine proposal](../../adr/63-multi-machine-deployment.md) |
| `obsidian-sync` | Obsidian's cloud sync | ⚠️ Needs VPS for cron | ⚠️ `.bib` only on VPS | ~$10/mo | iOS access; small team — see the [multi-machine proposal](../../adr/63-multi-machine-deployment.md) |
| `always-on` | Syncthing + VPS (P2P, peer = full filesystem) | ✅ VPS runs as a Syncthing peer | ⚠️ `.bib` only on VPS | ~$12–25/mo VPS | Multi-device with always-on agent — see the [multi-machine proposal](../../adr/63-multi-machine-deployment.md) |

**Start with `local-only`.** It is the adopted posture: a single workstation, Git for history, Zotero on localhost. Adding Syncthing or a VPS later is additive — it doesn't require restructuring the vault — so deferring the multi-machine patterns costs nothing. When a second device or unattended automation enters the picture, see the [multi-machine deployment proposal](../../adr/63-multi-machine-deployment.md).

## Common decisions across options

These conventions are adopted design; they hold regardless of which pattern you run, and they are what make the multi-machine patterns safe when you do adopt them. The rationale is the point here; for the exact paths, env-var names, and what the installer writes where, see [Installer (bootstrap)](../../reference/installer.md).

- **Git is the version history layer, not the sync layer.** Every pattern uses Git for reversibility. Sync is a separate concern.
- **`memoria.bib` lives inside the vault** at `.memoria/memoria.bib`, exported by Better BibTeX. This makes the bib a first-class artifact that travels with the vault under whichever sync mechanism you choose.
- **Cheap-task routing is configured in Hermes, not in the deployment.** See the model-routing pattern (synthesis to Claude, embed / classify / quick-summary to cheaper models via OpenRouter or similar).
- **Per-session log files, not a single `log.md`.** The Linter's per-session digests write one file per session to `system/logs/sessions/` ([ADR-25](../../adr/25-session-logging-two-logs.md)). With one append-only file, distributed writes from VPS and desktop produce sync conflicts; one-file-per-session has nothing to conflict on. *(The audit log `audit.jsonl` is a single append-only file, so cross-machine sync of the audit log waits on the multi-machine patterns below.)*
- **Hermes data dir is `~/.hermes/` by default** (or `%USERPROFILE%\.hermes\` on Windows). Override with `HERMES_HOME=/path/to/dir` when you need isolation — most commonly under multi-machine patterns, where a secondary device's Hermes should keep its own profiles, sessions, and audit log isolated from the primary's `~/.hermes/`.
- **One Hermes dispatcher per vault.** Under any multi-machine pattern, multiple machines have the vault but only *one* should run Hermes as a dispatcher (cron + `hermes gateway` + card claiming). The task registry lives in `~/.hermes/` per machine; two active dispatchers against the same synced vault race on card writes and produce conflicting audit logs. The convention: the *[primary device](../../reference/glossary.md#system)* owns dispatch; secondary devices run vault-only or in restricted modes — see the secondary-device patterns in the [multi-machine proposal](../../adr/63-multi-machine-deployment.md).
- **Profile aliases are first-class.** The installer's profile-install step registers each profile under a `memoria-<name>` alias, so `memoria-librarian chat` is a shortcut for `hermes -p memoria-librarian chat` — what the workflows in [Workflows](../workflows/README.md) assume. The exact command and seed semantics are owned by [Installer (bootstrap)](../../reference/installer.md).
- **`.env` is per-machine, never committed.** Each profile ships a `.env.EXAMPLE` listing required and optional env vars with descriptions. The installer copies it to `.env` on first install if `.env` doesn't already exist; the human fills in keys. Hermes hard-excludes `.env` and `auth.json` from `hermes profile install` / `update` so credentials never travel between machines.
- **Agent memory can ride the vault.** Because the Co-PI is the sole memory carrier ([The Co-PI](../profiles/co-pi.md)), its `MEMORY.md` / `USER.md` (`~/.hermes/profiles/memoria-copi/memories/`) are the only agent memory to share. Per-machine by default, but the [`memories/` junction](../../adr/60-cross-vault-knowledge-sharing.md) promotes them into the git-synced vault so the Co-PI's learned notes follow you across machines — the automatic, no-extra-channel way to share agent memory under non-concurrent local-only / local-mesh use. Session history (`state.db`) and secrets (`.env`) deliberately stay per-machine.

## Related

- **Multi-machine deployment** (the deferred topologies and secondary-device patterns): [Multi-machine deployment (topologies and secondary-device patterns)](../../adr/63-multi-machine-deployment.md).
- **Setup steps:** [Setup how-to guides](../../how-to-guides/setup).
- **What gets installed where:** [Installer (bootstrap)](../../reference/installer.md).


---

<!-- source: explanation/deployment/always-on-vps-design.md -->

# Always-on VPS design

> **Status — deferred.** The supported install path is documented around the `local-only` pattern; the `always-on` topology is designed but not validated end-to-end (tracked in [#383](https://github.com/eranroseman/memoria-vault/issues/383); design: [Deployment options](deployment-options.md), [Multi-machine deployment (topologies and secondary-device patterns)](../../adr/63-multi-machine-deployment.md)). This page records the intended topology and validation shape; it is not a supported setup guide.

The always-on design moves Hermes from local WSL2 to a persistent VPS so scheduled crons can run overnight, board cards can process unattended, and the system can stay reachable from more than one device. The VPS becomes the **one dispatcher** for the vault; the desktop keeps Obsidian and Zotero; the vault files sync between them.

## Design intent

The topology exists to solve one specific problem: a laptop or desktop is not always awake when Memoria's maintenance loop should run. A persistent host gives the board dispatcher, sweeps, lint, metrics, eval dispatch, and qmd index a stable place to live.

The design does **not** make Memoria multi-writer. It preserves the solo-researcher premise by keeping exactly one machine responsible for dispatch and cron writes. Obsidian remains the human interface on the desktop, and the VPS is infrastructure: it runs deterministic maintenance and background lane work against the synced runtime vault.

## Required properties

| Property | Reason |
| --- | --- |
| One dispatcher per vault | Two machines dispatching the same board can race on card state and produce conflicting audit rows. |
| Desktop owns Obsidian and Zotero | The human review surface and bibliographic manager stay local to the PI's machine. |
| VPS owns crons and dispatch | Scheduled work needs an always-awake host. |
| Vault files sync between machines | The PI must see the results locally, while the VPS can process background work. |
| `.memoria/memoria.bib` distribution avoids mid-transfer reads | The ingest path depends on stable citekey metadata; partial sync is a real failure mode. |
| Audit rows remain content-free and append-only | Multi-machine topology must not weaken the audit-memory contract. |

## Intended topology

| Component | Intended home |
| --- | --- |
| Obsidian and Zotero | Desktop |
| Hermes dispatch and scheduled crons | VPS |
| qmd index for background work | VPS |
| Co-PI conversation | Either desktop or VPS over an explicit ACP launch path |
| Runtime vault files | Synced between desktop and VPS |

The design assumes an Ubuntu-class VPS and a desktop that can reach it over SSH, but those platform details are validation concerns, not a supported setup contract yet.

## Validation shape

The topology is not ready until a future implementation issue proves all of these behaviors end-to-end:

- The VPS registers the five `memoria-*` profiles and the maintenance crons.
- The desktop crons are disabled while the VPS crons are active.
- A desktop capture can sync to the VPS, process through ingest, and sync the resulting Catalog entity and Inbox card back to the desktop.
- `system/logs/audit.jsonl` records the VPS-side gated writes.
- `system/logs/cron-heartbeat.jsonl` shows fresh rows for scheduled jobs after their expected cadence.
- A stale or missing heartbeat leads to an operator-visible failure path, not silent drift.

## Failure modes to design against

| Failure mode | Design response |
| --- | --- |
| Host sleeps through a timer | Put dispatch on an always-on host rather than a laptop. |
| User services die on logout | The VPS runtime must keep user timers alive across SSH logout. |
| Secrets drift between profiles | Profile redeploy remains the supported way to propagate `.env` changes. |
| Two dispatchers run at once | The topology requires a single active dispatcher per vault. |
| Bibliography sync is partial | `.memoria/memoria.bib` needs a stable distribution path, not a half-written sync read. |

## Related

- Local install prerequisite: [Quickstart](../../how-to-guides/setup/quickstart.md)
- The topology trade-offs and dispatcher rule: [Deployment options](deployment-options.md)
- Profile configuration: [Configure a profile](../../how-to-guides/hermes-agent/configuration.md)
- Failure lookup table: [Failure modes](../../reference/failure-modes.md)


---

<!-- source: explanation/rationale/README.md -->

# Design rationale

The `why-*` pages: the durable conceptual arguments behind Memoria's core design choices. Each answers "why is it shaped this way?" and is written to be read and re-read. These carry no date and no status — they are the canonical reasoning, maintained over time.

> **`why-*` explanations vs. ADRs.** A `why-*` page holds the _argument_; an [ADR](../../adr) holds the _dated decision_. When both cover the same ground, the explanation carries the reasoning and the ADR carries the record — each links to the other rather than restating it. Change the reasoning → update the `why-*` page; reverse the decision → supersede the ADR.

## The arguments

| Page                                                              | The question it answers                                                                                             |
| ----------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------- |
| [Why the architecture is layered](why-three-layers.md)                  | Why board, workers, and vault are kept separate — the thin-control-thick-state principle and what breaks without it |
| [Why specialist profiles](why-specialist-profiles.md)             | Why five profiles (one conversational Co-PI plus four background lanes) instead of one generalist, and why there is no Orchestrator                            |
| [Why the review gate is structural](why-human-gate.md)            | Why the human approval gate is enforced by architecture, not advised by convention                                  |
| [Why Memoria doesn't pursue full autonomy](why-not-autonomous.md) | The autonomy ceiling — why synthesis stays human-owned                                                              |
| [Why Hermes](why-hermes.md)                                       | Why the execution layer is the Hermes runtime, and where the programmatic surface fits                              |
| [Why deterministic methods](why-computational-methods.md)         | Why deterministic methods are preferred over LLM calls wherever correctness matters                                 |

## The evidence base

| Page                                                                   | What it provides                                                                                                                           |
| ---------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------ |
| [Pattern provenance: borrow, adapt, ignore](why-pattern-provenance.md) | The borrow / adapt / reference / ignore judgment table against ~47 surveyed AI-research systems — the evidence the arguments above lean on |

---

## Related

- The structures these arguments shape: [Architecture](../architecture/README.md)
- The dated decisions they pair with: [ADRs](../../adr)
- The cross-cutting principles they share: [Design principles](../overview/design-principles.md)


---

<!-- source: explanation/rationale/why-three-layers.md -->

# Why the architecture is layered

Memoria separates orchestration, execution, and settled knowledge into distinct layers. This is not a layering convention; it is the mechanism that makes retries safe, handoffs lossless, and review enforceable. The argument was first made for three layers ([ADR-01](../../adr/01-three-layer-architecture.md): board, workers, vault) and survives intact in the seven-layer stack that superseded it ([ADR-46](../../adr/46-seven-layer-architecture.md)) — the refinement added layers; it never weakened the separation.

---

## The three concerns

Any knowledge production system that uses AI agents must manage three kinds of state:

1. **Active work state** — what tasks are in flight, what's their status, who owns them, what happened when they failed.
2. **Execution context** — which agent is running, what permissions it has, what tools it can use.
3. **Settled knowledge** — what has been established, synthesized, and approved as canonical.

The failure mode of most single-agent or single-document systems is that these three concerns share the same substrate. They collapse together in chat history, in the agent's working memory, or in a flat document store.

---

## What happens when they collapse

**Orchestration + execution collapsed (no separate board):**
Work state lives in agent memory or chat context. When a session ends, the state is gone. The next session starts fresh: it doesn't know what was already done, what failed and why, or where the previous worker left off. Retries duplicate work. Handoffs lose context. Long-horizon tasks that span multiple sessions become unreliable.

**Execution + knowledge collapsed (agents write canon directly):**
There is no gate between "the agent finished" and "this is now trusted information." A confidently-wrong agent writes claims that downstream work cites — and those errors compound.

**Orchestration + knowledge collapsed (tasks and knowledge share a store):**
Task history pollutes the knowledge graph. In-flight notes get confused with settled notes, and there is no structural way to tell them apart. Queries against the vault return noise.

---

## Thin control over thick state

The layered design follows a principle that several independent research systems identified from different starting points:

**[Chen et al. 2026](../../reference/bibliography.md#chen2026autonomous)** (*Toward Autonomous Long-Horizon Engineering for ML Research*) describes this as "thin control over thick state": the orchestrator and workers carry as little persistent context as possible; durable knowledge lives in files. Their ablation removes the persistent knowledge layer and measures a drop of 6.41 points on PaperBench and 31.82 points on MLE-Bench Lite. The persistent layer isn't overhead — it's the mechanism that enables long-horizon work.

**AgentRxiv** ([Schmidgall and Moor 2025](../../reference/bibliography.md#schmidgall2025agentrxiv)) shows that agents reading prior agent-generated reports gain ~11% over isolated agents on MATH-500. Cross-session knowledge persistence is the mechanism; agents that can't read prior work start from scratch every time.

**PARNESS** ([Wang and Luan 2026](../../reference/bibliography.md#wang2026parness)) names "no existing tool persists cross-run knowledge in a form that can be retrieved into a finite LLM context" as one of five structural problems in the field — and addresses it with a persistent knowledge layer. The defining difference is that PARNESS is fully autonomous where Memoria has a blocking human gate.

Unrelated systems, different architectures, one finding: long-horizon agent work fails when state lives in chat and succeeds when state lives in files. (A further corroboration at the claim grain is catalogued in [Pattern provenance: borrow, adapt, ignore](why-pattern-provenance.md).)

---

## From three layers to seven

ADR-01's three layers framed the original infrastructure, but conflated two distinctions: *where* things live (structure) and *who* acts (actor-kind). [ADR-46](../../adr/46-seven-layer-architecture.md) pulled them apart and superseded ADR-01 with the seven-layer stack: **PI · Interface · Co-PI · Tasks · MCP · Operations · Vault.**

Each refinement carries the same argument further:

- The **board and workers** became the **Tasks** layer, with the **Co-PI** lifted out as its own layer — the one agent that converses and remembers, separated from the stateless lanes that execute.
- The **policy boundary** became an explicit layer (**MCP**) rather than an implementation detail of the worker layer — naming where allow-listing, write-scoping, and audit actually live.
- Deterministic work was pulled out of the worker set into **operations** — reproducible mechanism that needs no posture and no lane.
- The **Interface** and the **PI** were named as layers because the strict layering claim had to be scoped honestly: it binds the *agent write-path* (Co-PI → Tasks → MCP → Operations/Vault); the PI and cron/CI are direct edges.

The file-as-bus, durable-state core — thick files, thin everything else — is unchanged from ADR-01 to ADR-46.

---

## The load-bearing rules

The separation is maintained by rules that cannot be violated without breaking the design:

**The board never holds knowledge.** It tracks work. Cards die at `archived`; knowledge lives in the vault. A card can reference a vault note by path; it never *is* a note.

**The agents never hold permanent state.** Lanes claim cards, act, and release; the Co-PI's memory holds working style and conventions, never canon. Continuity comes from the board (in-flight) or the vault (settled).

**The vault never schedules work.** It is the destination, not the orchestrator. A vault note does not trigger agent action; a board card does.

**The boundary is enforced, not promised.** The policy MCP intercepts every agent write; the gated zones degrade to proposals for every lane. The boundary isn't "an agent should not write here" — it's "an agent cannot write here."

---

## Related

**Explanation**

- The seven layers described: [Architecture](../architecture/README.md)
- How the agent layer is structured: [Why specialist profiles, not a generalist agent](why-specialist-profiles.md)
- Why the vault's review gate is structural: [Why the review gate is structural](why-human-gate.md)

**Reference**

- The guard layer in detail: [Policy MCP](../../reference/policy-mcp.md)
- The thick-state substrate: [Memory substrates](../../reference/memory.md)


---

<!-- source: explanation/rationale/why-specialist-profiles.md -->

# Why specialist profiles, not a generalist agent

Memoria uses **one conversational Co-PI and four posture-defined background agents** instead of one generalist ([ADR-48](../../adr/48-copi-and-agent-consolidation.md)). The dividing line is **posture and write-permission, not capability or tool**: faithful vs skeptical, read-only vs scratch-write vs review-gated. This page makes the argument — why specialists at all, and why posture is the axis that divides them.

---

## The problem with a generalist agent

A generalist agent that does everything — discovers sources, synthesizes claims, verifies citations, writes deliverables — has several structural problems:

**Unclear responsibility.** When quality fails, it's not possible to say "this was a discovery error" vs "this was a verification failure." The same agent made every decision in sequence.

**Ambiguous permissions.** The most permissive access required by any task becomes the baseline for all tasks. The policy MCP can't distinguish "this agent is discovering" from "this agent is synthesizing."

**No separation of stances.** Discovery should be generous; verification should be skeptical. An agent that does both must switch stances internally, with no structural guarantee that it does.

---

## Why posture is the unit, not the role

A profile is a **posture** — a stance bound to a write-permission — not a task list. Skills attach per lane; the agent is defined by *how it acts on the vault*, not *what task it runs*. Organizing by posture rather than by role keeps the set small: tasks that share a stance collapse into one agent.

- Intake and corpus mapping are one *faithful* research-librarian stance pointed in two directions, so they are a single agent — the **Librarian** (catalog · extract · link · map) — not several.
- Judgment-checking is a distinct *skeptical, independent* stance, so it is its own agent — the **Peer-reviewer**.
- Conversational questioning is the read-only front stance — the **Co-PI**.
- Scaffolding a code handoff is a *delegating* stance — the **Engineer**.
- Deterministic, zero-LLM work has no posture at all, so it is not an agent: it is an **operation** (the Linter, the sweeps).

One posture per agent, one agent per posture. The fragmentation cost of going finer is real: more lanes to route between, more permission matrices, and — decisively — a fragmented learning loop.

## Why one Co-PI fronts everything

Splitting conversation across many agents creates a real UX failure: *who do I talk to?* Every profile becomes a possible conversation, so no conversation compounds. Concentrating all dialogue in **one Co-PI** fixes both halves:

- **The learning loop needs one home.** Hermes' self-improving loop — memory · /goals · skills — only compounds in an agent that has every conversation. Split across many fronts, each gets a sliver of context and none grows.
- **Delegation keeps the wall.** The Co-PI is read-only; every write leaves as a routed card under a background lane's ceiling. You get one warm, remembering front *and* stateless, scoped executors — not a generalist with the union of everyone's permissions.

The background lanes stay out of conversation by design: a lane is a propose-then-dispose executor, and keeping it stateless is what keeps its failures scoped and its permissions legible.

## The independence argument

The **Peer-reviewer is kept separate from the Librarian** on principle, however much retrieval tooling they share. The agent that gathers and synthesizes must not also grade the result — separation of duties is the anti-rubber-stamp principle. A checker that inherits the proposer's faithful stance waves through exactly what the review gate exists to catch. The two postures are in deliberate tension: the Librarian includes generously; the Peer-reviewer doubts independently. The asymmetry is the design — you need both, and they must be separate to work.

## No Orchestrator, no Reviewer

Memoria omits two roles that comparable multi-agent systems include:

**No Orchestrator profile.** Routing lives in the Co-PI's `route-task` and the board's dispatch rules — auditable mechanism, not a reasoning agent whose routing mistakes are hard to trace. If the rules can't decide, the card waits for a human.

**No Reviewer profile.** An LLM reviewer that decides whether work is good enough converts a structural gate into a probabilistic one. The Peer-reviewer and the operations produce *recommendations* that inform the PI's judgment; the review gate itself is always human ([Why the review gate is structural](why-human-gate.md)).

---

## The cost: capability duplication

Dividing by posture still has its price: the same *technique* can live in several agents. Embedding similarity drives the Librarian's mapping, the Peer-reviewer's duplicate adjudication, and the intake brief. Memoria takes the duplication on purpose — a shared capability-agent would need the union of every caller's access, dissolving the per-lane write boundaries the split exists to make legible. The reconciliation is layering: capability lives in **operations and shared MCP servers** every lane reaches through the policy gate; the **agents stay posture-pure** — identity, write zone, and stance, not tools.

---

## Related

- The five agents described: [Profiles](../profiles/README.md)
- The deterministic actors that are not agents: [Operations](../operations/README.md)
- Why the layers separate concerns: [Why the architecture is layered](why-three-layers.md)
- Why the review gate is human-owned: [Why the review gate is structural](why-human-gate.md)


---

<!-- source: explanation/rationale/why-human-gate.md -->

# Why the review gate is structural

Memoria's review gate is **structural**: the policy MCP blocks writes to canonical zones regardless of which profile requests them. It is not advisory (a suggestion the agent could override), not configurable (a setting the human could relax), and not prompt-based (an instruction the agent is expected to follow). This document explains why.

---

## The default in the field: advisory review

Most contemporary multi-agent research systems use an LLM-based reviewer. The pattern: after a worker finishes, a reviewer model evaluates the output and either approves, requests revision, or escalates. The reviewer's verdict is factored into downstream processing — a high score moves the output forward; a low score triggers revision.

This is the advisory model. The reviewer advises; the system uses the advice to route the output. The human is in the loop only when they check the system.

Memoria rejects this model for synthesis. The reasoning follows from the specific failure mode that matters for knowledge work.

---

## The specific failure mode

Hallucinated citations and fabricated claims are not produced with visible uncertainty. They are emitted with high fluency and high confidence. A model that "confidently knows" a paper says something that the paper doesn't actually say does not signal that uncertainty — it asserts the claim fluently.

An advisory reviewer evaluating the same output faces the same problem: if the original agent hallucinated confidently, the reviewer may agree confidently. Two models with correlated errors produce a system that routes confidently wrong outputs forward.

This is not a fringe scenario — it is the dominant failure mode in AI-assisted citation work. Studies consistently find that LLMs cite papers for claims those papers don't make, and that LLM-based reviewers miss these errors at meaningful rates.

The structural gate exists because: **the outputs the gate needs to catch are precisely the ones a confident agent reviewer would approve**.

---

## Why structural, not prompt-based

The alternative to a structural gate is a prompt-based rule: "Always wait for human review before writing to canonical zones." This looks equivalent but isn't.

A prompt-based rule is subject to:

- **In-context instruction following**, which degrades at long context lengths.
- **Override by explicit later instruction**, such as "just move it forward this time."
- **Reasoning about exceptions**, where the agent argues to itself that this case is different.
- **Session restart**, where the instruction isn't carried forward.

A structural gate — enforced at the policy MCP — is not subject to any of these. The MCP intercepts every write before it reaches disk and returns `dry_run` for review-gated zones. No reasoning happens; no context is consulted; no exception is possible. The write doesn't succeed. The agent that "decides" to canonize cannot, because the file-system call returns before any content reaches disk.

The practical difference: prompt discipline has a mean time to failure. Structural enforcement doesn't degrade.

---

## The review state as structured data

Because review is structural rather than conversational, the review state is queryable. A Dataview query can ask "which cards are awaiting review?" A dashboard can show review queue depth. A WIP cap can enforce back-pressure when the done-awaiting-review queue grows too long.

None of this is possible if review lives in comments, tags, or conversation. "The human reviewed this" must be a field, not a convention.

The card's `review_status` field carries exactly this: `unreviewed` (initial state), `requested` (worker finished, human's turn), `approved` (human accepted), `rejected` (human declined). These are states in a state machine, not annotations.

---

## The agent verdict is not the review

The Peer-reviewer and the operations (the Linter, the sweeps) can attach a recommendation — `metadata.agent_recommendation` — to a finished card. This recommendation is separate from the review decision:

- **The recommendation can be wrong.** A clean Peer-reviewer report doesn't mean the draft is good; it means the citations trace and the schema is valid. The human judgment about whether the synthesis is correct, useful, and worth keeping is separate.
- **They can disagree.** The Peer-reviewer reports clean; the human reads the draft and rejects it. The separation makes this case coherent — there's no confusion about which verdict counts.
- **The human's decision is the gate.** The agent verdict informs; it never replaces.

---

## The trade-off

The structural gate makes the human a bottleneck. Review doesn't auto-scale; if the human doesn't review, done cards pile up in the `awaiting-review` state and the WIP cap eventually slows new work.

This is the design. The bottleneck is the point: the human must stay in contact with what the agents produce. A system that can autonomously move synthesis to canonical without human attention has removed the epistemic guarantee that makes the vault trustworthy.

The cost reduction that an advisory gate would buy (less time in review) is not worth the structural guarantee it would spend (canonical synthesis is always human-approved).

---

## Related

**Explanation**

- Why specialist profiles support this: [Why specialist profiles, not a generalist agent](why-specialist-profiles.md)
- Why the vault won't autonomize synthesis: [Why Memoria doesn't pursue full autonomy](why-not-autonomous.md)
- How the review state works in the workflow: [Review as a first-class state](../workflows/review-as-state.md)
- What the gate enforces at the synthesis boundary: [Why promotion is gated](../knowledge/promotion-model.md)

**Reference**

- Policy MCP enforcement details: [Profile capabilities](../../reference/profiles.md) (permissions) · [Memory substrates](../../reference/memory.md) (audit log)
- The enforcement mechanism: [Policy MCP](../../reference/policy-mcp.md)


---

<!-- source: explanation/rationale/why-not-autonomous.md -->

# Why Memoria doesn't pursue full autonomy

Memoria targets L3 on the autonomy spectrum — multi-step autonomous execution under human-set strategy with per-batch review — and maintains a structurally enforced ceiling. This document explains why the ceiling exists and where the exception lies.

---

## The three preconditions for autonomous loops

[Karpathy](../../reference/bibliography.md#karpathy-llm-wiki)'s Autoresearch pattern — an agent that runs overnight, modifies code, tests against a fixed evaluator, and keeps or reverts — works because three conditions hold simultaneously:

1. **The metric is monotonic.** Validation loss either improves or it doesn't.
2. **Changes are reversible.** Git reverts the diff; the next experiment starts clean.
3. **Experiments are independent.** Experiment N+1 doesn't depend on the conclusions of N.

An autonomous keep/revert loop is only safe when all three conditions hold. The loop optimizes a scalar; the scalar must be the right signal; errors must be correctable without downstream consequences.

---

## Why knowledge work fails the test

**Synthesis quality is not scalar.** Every autonomous research system (AI Scientist, [AI co-scientist](../../reference/bibliography.md#gottweis2025aicoscientist), CORAL, [SciMON](../../reference/bibliography.md#wang2024scimon), Karpathy Autoresearch, [Chen et al. 2026](../../reference/bibliography.md#chen2026autonomous)) uses one number as the keep/revert signal. That number is plausible for its target task. None of these numbers is plausible for "is this synthesis a faithful, well-cited, non-redundant addition to a research vault." The proxy metrics that exist — citation count, relevance score, Scite support count — can inform triage priority, but they don't measure synthesis correctness.

**Synthesis errors compound.** In ML benchmarking, a wrong experiment is a wasted run. In knowledge work, a wrong claim persists in the vault and gets cited by downstream notes that build on it. The cost model is inverted: errors don't stay local; they accumulate. This asymmetry means the tolerance for autonomous keep/revert is much lower for knowledge work than for code experiments.

**Later sources reinterpret earlier ones.** Experiments in ML are independent. In knowledge work, they are not — a paper published six months later may show that an earlier claim was wrong, or provide the framework needed to understand what an earlier paper was actually arguing. The value of a source is often only knowable in retrospect.

---

## Why confidence-routing doesn't help

One tempting refinement: route to the human only when the agent's self-assessed confidence is low (SmartPause, as in AutoResearchClaw — [Liu et al. 2026](../../reference/bibliography.md#liu2026autoresearchclaw)). Their ablation finds targeted gating beats both full autonomy and dense step-by-step oversight.

Memoria declines this approach for two reasons:

**Confident-wrong is the failure mode.** Hallucinated citations and fabricated numbers are emitted with high fluency and high confidence, not with visible hesitation — the argument is developed in [Why the review gate is structural](why-human-gate.md). Confidence-routing is the specific casualty: it routes on the agent's self-assessed confidence, the one signal that is gameable by exactly the outputs the review gate exists to catch.

**The cost model is inverted.** In a throughput-optimizing autonomous system, the cost of a wrong high-confidence output is a wasted run. In Memoria's vault, the cost is a wrongly-promoted claim that persists and compounds. Confidence-routing is worth the bet when errors are cheap; it isn't when the vault is durable.

The real insight in that ablation — that gating everything is worse than gating well — Memoria keeps, but spends on the other side: **make each review cheaper, not fewer reviews**. A better Peer-reviewer (pre-verified material, structured evidence chains) lets the human review faster without removing the human from the loop.

---

## Why code could be the exception — and why none exists today

Code is the one domain where the three preconditions could hold. Code artifacts have:

- **Monotonic metrics**: tests pass or fail; runtime either improves or doesn't; coverage rises or falls.
- **Reversible changes**: `git reset` recovers the diff; the next run starts from known state.
- **Independent experiments**: one code experiment doesn't depend on the conclusions of another.

All three hold for code work, so in principle an autonomous experiment loop — iterate against a test suite, measure, keep or revert — would be admissible there in a way it never is for synthesis.

**But no autonomy exception exists anywhere in the current system** ([ADR-21](../../adr/21-l3-autonomy-ceiling.md), [ADR-48](../../adr/48-copi-and-agent-consolidation.md)). The Engineer is **MCP-only with no terminal, file, or execution capability**. It cannot run a test suite or a keep/revert loop; it scaffolds the code handoff, records provenance, and owns the per-task commit gate while the substantive coding happens in an external agent the PI reviews. No lane carries an autonomous keep/revert loop.

The synthesis gate remains structurally untouched. The policy MCP's review-gated-zone deny rule still blocks writes to `notes/claims/` and `notes/hubs/`. Whether to admit a bounded code-experiment loop will be revisited only when the code lane / external-coding-agent path is defined beyond the current Project gate handoff — and reopening it requires a superseding decision, not an incremental relaxation.

---

## What this implies in practice

The design produces a bounded, phase-gated, human-in-the-loop operating cadence:

- Agents propose, classify, draft, and verify — but do not canonize.
- Scheduled and overnight operations write to `inbox/` only. Promotion is always synchronous with human attention.
- The discovery loop can run autonomously (finding and ingesting candidates) because the human reviews candidates before they enter the canonical vault.
- The cost discipline ("$1–3/day API budget for the nightly loop") matters because there's no scalar payoff to optimize against. Budget discipline replaces metric discipline.

---

## Where Memoria sits

[Chen 2026](../../reference/bibliography.md#chen2026copilots)'s (*From Copilots to Colleagues*) five-level taxonomy: L1 (autocomplete) → L2 (multi-step, human approval per step) → L3 (multi-step autonomous, human-set strategy, per-batch review) → L4 (self-directed within a domain) → L5 (fully self-directed).

Memoria is L3. The background lanes execute multi-step work unattended within a card. The human sets the strategy (`research-focus.md`, `screening-protocol.md`) and the review gate blocks every promotion. L4 requires autonomous keep/revert on synthesis; L5 requires self-directed agenda-setting. Both fail the preconditions test for knowledge work.

---

## Related

- Why the review gate is structural: [Why the review gate is structural](why-human-gate.md)
- The intellectual foundations of this position: [Intellectual foundations](../overview/intellectual-foundations.md)
- Full borrow/adapt/ignore table: [Pattern provenance: borrow, adapt, ignore](why-pattern-provenance.md)


---

<!-- source: explanation/rationale/why-hermes.md -->

# Why Hermes

Memoria's entire execution layer is [Hermes Agent](https://hermes-agent.nousresearch.com/) (Nous Research). The board is Hermes's Kanban, the workers are Hermes profiles, the dispatcher is Hermes's, and the integration endpoint is Hermes's API server. This page explains why Memoria builds *on* a runtime rather than building its own, what Hermes provides, and where the Memoria/Hermes boundary falls.

If Memoria is *what you keep* — the vault, the knowledge, the schema — Hermes is *who moves things*: it carries work between states, between profiles, and between the human and the vault.

---

## What Hermes provides

Memoria needs an execution substrate with four properties, and Hermes ships all four:

- **A persistent Kanban board** (`kanban.db`) — a durable state machine across sessions and retries. When a session closes, work state survives; the next worker picks the card up from its last known state. This is the [thin-control-over-thick-state](why-three-layers.md) requirement made concrete.
- **Profiles with lanes** — each agent is a named profile (`SOUL.md` identity, `config.yaml` model routing, lane-override permissions) that claims cards on its lane. Memoria's five profiles *are* Hermes profiles.
- **A dispatcher** — claims `ready` cards for matching profiles, runs them, advances state, retries on recoverable failure. Memoria adds routing *rules*, not a routing *agent* (there is no Orchestrator — see [Why specialist profiles, not a generalist agent](why-specialist-profiles.md)).
- **Native memory, MCP, and an API** — agent memory (`MEMORY.md`/`USER.md`), an MCP server interface (which Memoria's policy gate plugs into), and a network endpoint for programmatic triggers.

Memoria supplies the *conventions on top*: the review-gate overlay in card `metadata`, the policy MCP that gates writes, the five profile `SOUL.md`s, and the vault schema. None of those require modifying Hermes — they ride its extension points.

---

## Why not build our own runtime

A bespoke agent runtime would be a large, ongoing engineering commitment whose hardest parts — durable state across crashes, atomic card claiming, retry semantics, memory tiers, an MCP host — are exactly what Hermes already solves. Reimplementing them would produce a worse copy and a maintenance burden, the same reasoning that keeps the [Engineer](../profiles/engineer.md) MCP-only rather than a reimplementation of an external coding runtime.

Building on Hermes also keeps Memoria compatible with stock `hermes` tooling: the board works with any standard Hermes install, and Memoria's overlay lives in `metadata` that Hermes treats as opaque (see [the card schema](../kanban-board/card-schema.md)). The cost of this choice is a dependency on an external runtime's release cadence and conventions; the benefit is that Memoria's design effort goes entirely into the *knowledge* layer, which is where its actual contribution lies.

This is a deliberate **borrow** in the [pattern-provenance](why-pattern-provenance.md) sense: Hermes's persistent-Kanban-plus-worker-lanes pattern is adopted wholesale; what Memoria declines from other runtimes is, e.g., chat-as-substrate (AutoGen) and sandbox-vs-host permission models (OpenHands), because those route durable state or permissions through the wrong layer.

---

## The programmatic surface (the API server)

Hermes exposes an **API server** (port 8642) — the surface where *programs*, not humans, connect to Memoria. File-system watchers, Zotero/Better BibTeX hooks, git `post-commit` hooks, calendar integrations, and cross-machine dispatch all enter here.

**Why a separate surface at all.** Programmatic integration needs a different interface than human operation. A file-system watcher that fires on a PDF drop cannot use the command palette; a Better BibTeX script that fires on Zotero save needs a network endpoint. The API is the integration surface for automation; Obsidian, the CLI, and Telegram (see [Interaction channels](../architecture/human-channels.md)) are the interaction surfaces for humans. The same operations available through the API are exposed to humans through the palette and CLI with better affordances — so humans never need to touch the API directly.

**It grants no extra power.** Every write through the API still passes through the policy MCP. A program calling the API has exactly the permissions of the profile it acts as — no elevation. The API is a different *door*, not a different *key*. See [Policy MCP](../../reference/policy-mcp.md) for enforcement details.

This is why the API server lives here, with Hermes, rather than in [Interaction channels](../architecture/human-channels.md): it is a Hermes integration surface that humans never operate, not a human channel.

---

## The Memoria / Hermes boundary

| Concern | Owned by |
| --- | --- |
| Board state machine, dispatcher, retries | Hermes |
| Profile mechanism (identity, model routing, lanes) | Hermes |
| Native memory tiers, MCP host, API server | Hermes |
| Review-gate overlay (`review_status`, `agent_recommendation`) | Memoria (card `metadata`) |
| Write-gating policy MCP | Memoria (plugs into Hermes's MCP interface) |
| The five profile `SOUL.md`s and lane-overrides | Memoria |
| The vault, schema, and document types | Memoria |

The rule of thumb: **Hermes moves work; Memoria decides what work means and what may become canonical.**

---

## Related

**Explanation**

- What Hermes coordinates — the layered architecture: [Why the architecture is layered](why-three-layers.md)
- The board as a state machine: [The board as a state machine (the control plane)](../workflows/board-as-state-machine.md)
- The card-schema overlay Memoria adds on top of Hermes: [The honesty card](../kanban-board/card-schema.md)
- The human interaction surfaces (Obsidian, CLI, Telegram): [Interaction channels](../architecture/human-channels.md)

**Reference**

- What the API's writes pass through: [Policy MCP](../../reference/policy-mcp.md)
- Hermes admin commands (reference): [Hermes CLI](../../reference/hermes-cli.md)


---

<!-- source: explanation/rationale/why-computational-methods.md -->

# Why Memoria uses deterministic methods alongside LLMs

Every task Memoria performs is classified as deterministic, hybrid, or generative. The class determines which method to use, what the cost looks like, and what can be audited. Without this classification, every task gets routed to an LLM "because it's text" — and the system becomes expensive, slow, and untestable.

## The three classes

**Deterministic** tasks have a single right answer derivable from rules, regex, math, or graph algorithms. Citation token extraction, schema-version checking, link-candidate ranking, duplicate detection, and structural drift detection are all deterministic. The same vault state produces the same result on every run.

**Hybrid** tasks use a deterministic step to narrow the problem, then an LLM to handle the residual judgment on the narrow result. `_proposed_classification`, `cite-check`, and the `[!brief]` callout all follow this pattern: a classifier or similarity search produces a ranked candidate set; an LLM composes over that small set rather than the whole vault.

**Generative** tasks have no fixed output and require open-ended composition. The Co-PI's conversation, the Writer's drafting, counter-outlines, and comparative-brief prose are generative. These are LLM-required and irreducibly so.

## The default test

If a regex, a graph algorithm, or a similarity threshold would produce the right answer most of the time, the task is deterministic or hybrid — not generative. The LLM enters only where the residual judgment genuinely requires it.

## Why the hybrid pattern dominates

The most common pattern in Memoria is deterministic narrowing followed by LLM enrichment on the narrow result:

```text
N candidates → deterministic ranking → K candidates (K ≪ N) → LLM composes over K
```

This matters for two reasons beyond cost. First, the deterministic step is auditable — you can show which candidates were selected, by what score, and why. The LLM's prose is visible but opaque; the selection is what the audit trail and the fleet-health accept/reject ratios actually measure. Second, it makes the system testable: the deterministic layer has a single right answer you can assert in a test; the LLM's composition layer doesn't.

Concrete examples:

- **`[!suggestions]`**: 5,000 vault notes → top-10 candidates by weighted similarity → optional LLM explanation per candidate. The LLM works on 10, not 5,000.
- **`cite-check`**: 80 claims in a draft → citekey resolution + embedding similarity score per pair → LLM judges only the middle band (similarity 0.4–0.75). Above 0.75 auto-clean; below 0.4 auto-fail.
- **`_proposed_classification`**: new paper note → small classifier proposes labels with confidence → if confidence > 0.85, accept; else fall back to LLM proposal.

## Why this classification exists in the design

Without an explicit classification, there is pressure to route every task to an LLM because it's the easiest path. The explicit classification creates a forcing function: before adding a new skill or workflow, the designer must ask whether a deterministic method would suffice. This keeps the LLM's role contracted to where its judgment is actually load-bearing and keeps the rest of the system fast, cheap, and reproducibly testable.

## Related

- [Callouts](../obsidian/callouts.md) — how the hybrid pattern produces callout content
- Which profile handles which task type: [Why specialist profiles, not a generalist agent](why-specialist-profiles.md)
- The zero-LLM operation this rationale produces: [The Linter](../operations/README.md)
- [Retrieval and analysis methods](../../reference/computational-toolbox.md) — the catalog of specific deterministic methods Memoria uses


---

<!-- source: explanation/rationale/why-pattern-provenance.md -->

# Pattern provenance: borrow, adapt, ignore

*Pattern provenance* is Memoria's record of where each design pattern came from and what was done with it: borrowed as-is, taken with the autonomy stripped out, kept only as framing, or evaluated and refused. It is the design's own citation trail.

Memoria records this for the same reason a research vault records claim provenance: a design decision is only trustworthy if you can see what evidence it rests on and what alternatives it rejected. The AI-research field is crowded with end-to-end "autonomous scientist" systems. Many of their mechanics are genuinely useful; almost all of them layer an autonomy posture on top that Memoria refuses. Without an explicit provenance record, those two things blur together — and a reader cannot tell whether Memoria omitted a pattern out of ignorance or out of judgment. The provenance trail makes every omission legible as a decision.

So each pattern Memoria encountered is sorted into one of four verdicts:

- **Borrow** — adopted as-is; the mechanic solved a real problem and needed no change.
- **Adapt** — the mechanic is kept, but the *autonomy posture* is narrowed; Memoria refuses the scalar-metric keep/revert loop most of these systems run on top.
- **Reference** — informs framing or positioning without contributing a borrowable pattern (surveys, position papers, taxonomies).
- **Ignore** — evaluated and explicitly refused; each refusal is a specific judgment, not a default.

The evidence base is a survey of ~47 contemporary AI-research systems, platforms, and benchmarks, now sitting inside a wider review of ~400 papers (`_papers/`, judged adopt/borrow/reject; verdicts in `_papers/REVIEW-SUMMARY.md`) spanning the bodies of work those systems build on — HCI/CSCW, faithful extraction and claim verification, evaluation discipline, and retrieval/temporal reasoning. The wider review mostly *validates and sharpens* rather than adds new agent-system patterns. The rest of this page summarizes the four verdicts with representative exemplars; the full per-system catalog lives in the survey, not inline here.

The headline patterns are summarized in [Intellectual foundations](../overview/intellectual-foundations.md). The autonomy boundary that rejects several patterns wholesale is in [Why Memoria doesn't pursue full autonomy](why-not-autonomous.md).

---

## Borrow: structural patterns adopted as-is

The borrowed patterns are the ones nearly every surveyed system converges on, and Memoria takes them unchanged. The dominant one is the **stage-gated pipeline** (ResearchArena, MLR-Copilot, AutoResearchClaw): distinct stages with validated handoffs at each boundary, rather than one giant prompt. Memoria runs it as Library intake (catalog → extract → link) and Project output (map → draft → verify → export). Supporting it are **explicit roles per agent** ([AI Scientist v2](../../reference/bibliography.md#yamada2025aiscientistv2), [LatteReview](../../reference/bibliography.md#rouzrokh2026lattereview), [Agent Laboratory](../../reference/bibliography.md#schmidgall2025agentlaboratory)), realized as five Hermes profiles — the Memoria term for a permission-scoped agent role; see [Why specialist profiles, not a generalist agent](why-specialist-profiles.md) — and **strong schema with validated handoffs** (AI Scientist, AutoResearchClaw): typed frontmatter at inter-agent boundaries (`_proposed_classification`, `_enrichment.*`, `_aspects.*`; see [Frontmatter fields](../../reference/frontmatter.md)) catches mismatches that free-text handoffs would let compound.

Three patterns make synthesis durable and inspectable. A **persistent knowledge graph** ([OmegaWiki](../../reference/bibliography.md#qian2026omegawiki), Idea2Story) preserves relationships instead of re-searching at every query — wikilinks, typed relations (`supports` / `contradicts`), hubs, entity notes. **Reviewable organization artifacts** (LitLLM, [LatteReview](../../reference/bibliography.md#rouzrokh2026lattereview)) keep synthesis readable by a human rather than hidden in prompts — canvases, hubs, Bases views. A **persistent Kanban + worker lanes** (Hermes Agent, Nous Research) gives a durable state machine across sessions; it is the runtime Memoria builds on (see [Why Hermes](why-hermes.md)) and appears as the board where background lanes claim cards (see [The board as a state machine (the control plane)](../workflows/board-as-state-machine.md)). A **point-of-action discovery loop** (Karpathy Autoresearch) shifts discovery from reactive to proactive — a nightly Librarian run with a bounded batch size, currently deferred.

A second cluster is **independent corroboration of the durable-state thesis** — the bet that a layered architecture with a durable-artifact "bus" is load-bearing, not overhead. Four sources arrive at it separately: the **File-as-Bus / thin-control-over-thick-state** ablation ([Chen et al. 2026](../../reference/bibliography.md#chen2026autonomous), *long-horizon engineering*), **structured outputs at handoff boundaries** ([MetaGPT, Hong et al. 2024](../../reference/bibliography.md#hong2024metagpt)) reducing cascading hallucination, and **cross-run knowledge accumulation** plus **paper ↔ code repository linking** ([PARNESS, Wang and Luan 2026](../../reference/bibliography.md#wang2026parness)) — the latter making the paper↔code correspondence a typed object so the repo, often the only complete spec of a paper's scheme, is linked at ingest (see [Profiles](../profiles/README.md)). The supporting numbers are in [Why the architecture is layered](why-three-layers.md). Finally, **claim-to-evidence chain by construction** ([ScientistOne, Meng et al. 2026](../../reference/bibliography.md#meng2026scientistone); [AutoResearchClaw, Liu et al. 2026](../../reference/bibliography.md#liu2026autoresearchclaw)) requires every claim to trace through a recorded evidence chain to a grounding source — ScientistOne reaches 0/337 hallucinated references where baselines hit up to 21% — and grounds the Peer-reviewer's claim-trace and citation checks.

---

## Adapt: mechanic kept, autonomy stripped

The adapted patterns share one shape: the mechanic is worth borrowing, but the system that originated it bolts on an autonomous quality loop that Memoria removes, leaving the human as the stopping criterion.

Several supply **pipeline and role structure**. ResearchArena's discover/select/organize maps to Memoria's longer human-driven arc (find → capture → enrich → classify → discuss → distill → connect), with the organize step becoming human distillation. AI Scientist's modular roles ([v1](../../reference/bibliography.md#lu2024aiscientist) + [v2](../../reference/bibliography.md#yamada2025aiscientistv2), Sakana AI) keep separate planner/writer/code-executor roles, but tree-search over synthesis is refused (see Ignore). The AI co-scientist's Memory + Meta-review pair ([Gottweis et al. 2025](../../reference/bibliography.md#gottweis2025aicoscientist)) — the same shape as Memoria's vault + hubs, and architectural validation from the survey's most production-mature system — is adapted without its tournament/evolution loop (see Ignore).

A cluster of **retrieval and claim-verification mechanics** feeds the Peer-reviewer as design inputs rather than autonomous gates. Inspiration retrieval before drafting ([SciMON, Wang et al. 2024](../../reference/bibliography.md#wang2024scimon)) lets the writer read related claim notes first, minus SciMON's novelty optimizer. MOOSE's three-channel hypothesis-feedback taxonomy ([Yang et al. 2024](../../reference/bibliography.md#yang2026moose)) is a verification-prompt rubric. ScientistOne's Chain-of-Evidence claim taxonomy ([Meng et al. 2026](../../reference/bibliography.md#meng2026scientistone)) — `citation` / `numerical` / `methodological` / `conclusion`, each with an evidence-chain shape and integrity checks — is the intended next step for the Peer-reviewer once claim-trace is stable; score-verification and method–code alignment are scoped to the Engineer's code lane. PARNESS scenario-typed retrieval (Wang & Luan 2026) is partly active: base `supports` / `contradicts` relations work today; the extended vocabulary (`similar`, `cross-domain`, `counter-intuitive`) is deferred. Knows's per-paper structured representation ([Yu and Wang 2026](../../reference/bibliography.md#yu2026knows)) — a YAML sidecar lifting weak-model comprehension by +29–42 pp — is mirrored by the `_aspects.*` source-note slots, though automatic population at ingest is deferred.

The remaining adapted patterns are **deferred or optional**, each waiting on a felt need or missing harness: a consensus pre-filter before human review ([AI-Supervisor, Long 2026](../../reference/bibliography.md#long2026aisupervisor)), benchmarks that would give the Peer-reviewer and Librarian numeric targets they currently lack ([CiteME, Press et al. 2024](../../reference/bibliography.md#press2024citeme), where frontier LMs hit 4–18%; [AutoResearchBench, Xiong et al. 2026](../../reference/bibliography.md#xiong2026autoresearchbench)), an agent-readable shared synthesis pool ([AgentRxiv, Schmidgall and Moor 2025](../../reference/bibliography.md#schmidgall2025agentrxiv)), exploration-trace capture of rejected directions (ARA / The Last Human-Written Paper, Liu et al. 2026), and an optional `review_mode: systematic-review` layer (LatteReview, LitLLM) for bounded protocol-driven projects. In every case the pre-filter or score only changes *what reaches* the structural gate — it never moves the gate.

---

## Reference: framing, not patterns

These works shape how Memoria positions itself without contributing a borrowable mechanic. The **autonomy-spectrum vocabulary** comes from [Chen 2026](../../reference/bibliography.md#chen2026copilots) (*From Copilots to Colleagues*), whose L1–L5 taxonomy lets Memoria say precisely that it targets L3 with a structurally enforced ceiling (see [What Memoria is](../overview/what-memoria-is.md)); the same ~95-paper survey independently names *persistent knowledge accumulation* as the critical barrier to L5 — validating Memoria's vault-as-load-bearing thesis. [Feng and Liu 2026](../../reference/bibliography.md#feng2026visionary) ("vibe researching") names Memoria's slot — human as creative director and quality gatekeeper — more crisply still: Memoria is vibe researching made durable and gated.

Several works **fix Memoria's position by contrast or corroboration**. Deep Research agents ([Huang et al. 2025](../../reference/bibliography.md#huang2025deepresearch); [Xu and Peng 2025](../../reference/bibliography.md#xu2025deepresearch)) define a query-driven, ephemeral-report category Memoria explicitly is *not*. The autonomous-vs-collaborative axis ([Gridach et al. 2025](../../reference/bibliography.md#gridach2025agentic)) and the co-scientist-not-autonomous thesis ([Bisht et al. 2026](../../reference/bibliography.md#bisht2026agentic)) both place Memoria on the collaborative side — Bisht's recommended "persistent world model carrying epistemic state" is structurally the vault, and its hypothesis-hivemind caution informs the consensus pre-filter. The MCP-native ecosystem argument ([Yue et al. 2026](../../reference/bibliography.md#yue2026mcpnative)) independently calls for durable shared artifacts Memoria already has, while missing Memoria's differentiator (MCP as a permission boundary, not mere interoperability). Artifact-aware review ([Zhang et al. 2026](../../reference/bibliography.md#zhang2026howfar), *How Far Are We From True Auto-Research*, a 117-paper audit) gives empirical support for the evidence-grounded Peer-reviewer and the blocking gate. Two narrower references: an uncertainty-boosts-diversity tuning default ([Qi et al. 2023](../../reference/bibliography.md#qi2023hypothesis)) and a scientific-agents survey ([Ren et al. 2025](../../reference/bibliography.md#ren2025scientific)) relevant only if Memoria explores domain-science applications.

---

## Ignore: patterns evaluated and refused

Almost every refusal traces to one root cause: a scalar-optimization loop with no blocking human gate per iteration. The headline case is **full autonomous scientist mode** ([AI Scientist v2](../../reference/bibliography.md#yamada2025aiscientistv2), Sibyl, AI-Researcher, Auto-Research), which runs end-to-end without a gate — misaligned with a philosophy where the gate is structural and non-negotiable. **Tree search over synthesis** (AIDE ML, AI Scientist v2, Yamada et al. 2025) is refused as a *fit* judgment, not a feasibility doubt: AI Scientist v2's tree search produced a manuscript that cleared an ICLR-workshop acceptance bar, but tree search needs a scalar metric fixed before the loop starts, and synthesis quality is not scalar — later sources reinterpret earlier ones. **Autonomous keep/revert without review** (Karpathy Autoresearch) fails because the three preconditions that make autonomous loops safe for ML benchmarking all break for knowledge work. The full argument for these is in [Why Memoria doesn't pursue full autonomy](why-not-autonomous.md).

The most instructive refusals are the ones where the **metric and the objective collapse into each other**. A co-trained generator + reviewer loop ([CycleResearcher, Weng et al. 2025](../../reference/bibliography.md#weng2025cycleresearcher)) RL-trains the reviewer against human scores, then trains the generator to maximize it — so the reviewer's learned preferences *become* the goal; Memoria's Peer-reviewer must stay prompt-driven against human-defined criteria. The AI co-scientist's tournament/evolution loop ([Gottweis et al. 2025](../../reference/bibliography.md#gottweis2025aicoscientist)) is the same scalar-optimization shape sitting on top of a Memory module Memoria *does* adapt — separating the two shows the architecture is sound and only the autonomy posture is refused. Preference internalization into model weights ([NanoResearch, Xu et al. 2026](../../reference/bibliography.md#xu2026nanoresearch)) is the same failure in a new form: once preferences live in weights they are no longer inspectable, auditable, or revertible, so Memoria keeps personalization external (vault content, lane-override files, configuration). Confidence-routed bypass of the gate (AutoResearchClaw SmartPause, Liu et al. 2026) converts a structural gate into a probabilistic one a confidently-wrong agent sails through; refused, with the argument in [Why Memoria doesn't pursue full autonomy](why-not-autonomous.md).

Three refusals are about **substrate and packaging**. "Harness" framing that still removes the human gate ([Sibyl-AutoResearch, Wang et al. 2026](../../reference/bibliography.md#wang2026sibyl), a 20-agent / 19-stage pipeline on Claude Code) records the lesson that harness rhetoric does not imply a gate — the gate is Memoria's differentiator, not the harness. Conversation as substrate ([AutoGen, Wu et al. 2023](../../reference/bibliography.md#wu2023autogen)) is refused because it inverts the commitment that conversation is ephemeral and the vault is the memory; the conversation *pattern* is fine inside an Agent Client pane, the chat-as-persistent-memory *substrate* is not. A generalist sandboxed dev agent as drop-in worker ([OpenHands, Wang et al. 2025](../../reference/bibliography.md#wang2025openhands)) has a sandbox-vs-host permission model too coarse for Memoria's per-zone-per-profile policy MCP — re-evaluate only if a concrete code-lane limitation surfaces. Underneath all of them is the rejected **one-model-does-everything** anti-pattern, which loses permission separation and the structural split between optimistic discovery and conservative verification.

---

## Cross-cutting findings from the full literature review

The wider ~400-paper review reached past the agent-systems corpus into HCI, extraction/verification, evaluation, and retrieval. Its dominant result is that separate research lines independently re-derive Memoria's existing bets; it adds few *new* end-to-end patterns but contributes a handful of cross-cutting mechanics and one or two genuine sharpenings (contradiction on entailment rather than embedding similarity; temporal coverage as a retrieval dimension).

The verification spine gets the sharpest reinforcement. The **generator–verifier, sample-and-rank** result ([Cobbe et al. 2021](../../reference/bibliography.md#cobbe2021verifiers); [Perez et al. 2022](../../reference/bibliography.md#perez2022modelwritten)) is the formal grounding of "engines write, agents judge" at the claim grain — generate N extractions, score each with a separate cheaper verifier, keep the top-ranked, cap N so candidates can't game the verifier. The **evidence-grounded verification** chain ([Thorne et al. 2018, FEVER](../../reference/bibliography.md#thorne2018fever)) is the first sharpening: build supports/contradicts on explicit NLI/entailment with a tri-class SUPPORTED / REFUTED / NOTENOUGHINFO verdict and a recorded warrant — *not* embedding cosine, which is blind to negation. **Temporal coverage as a retrieval dimension** ([Abdallah et al. 2026, TEMPO](../../reference/bibliography.md#abdallah2026tempo)) is the second: time-mismatched evidence is worse than none and worsens as the store grows, which makes claim supersession load-bearing rather than optional.

Two findings reinforce the gate and the sandbox. The **HCI lineage of the review gate** ([Horvitz 1999](../../reference/bibliography.md#horvitz1999mixedinitiative); [Bernstein et al. 2010, Find-Fix-Verify](../../reference/bibliography.md#bernstein2010soylent); [Amershi et al. 2019](../../reference/bibliography.md#amershi2019guidelines); [Ackerman 2000](../../reference/bibliography.md#ackerman2000cscw)) predates the agent literature — augmentation over delegation, an expected-utility act/ask router, span-level verification separated from generation, and the *social-technical gap* as the structural reason a human stays the adjudicator. **Indirect-prompt-injection hardening** ([Greshake et al. 2023](../../reference/bibliography.md#greshake2023injection); [Debenedetti et al. 2024, AgentDojo](../../reference/bibliography.md#debenedetti2024agentdojo)) shows ingested text is the attack surface and more-capable models are *easier* to hijack — so safety must come from least-privilege tool allowlists, never prompt-level filters, confirming the MCP-only sandbox (ADR-32/46/28/27). Finally, **LM fluency ≠ knowledge** ([Bender et al. 2021](../../reference/bibliography.md#bender2021parrots)) is a discipline, not a feature: a fluent assertion is not evidence, so every atomic claim carries an uncertainty flag and a source-span provenance grade.

These are wired into the existing design rather than standing as separate lanes: generator–verifier and evidence-grounding reinforce the Peer-reviewer's *Claim-to-evidence chain* (Borrow) and *Chain-of-Evidence taxonomy* (Adapt); the augmentation and injection findings reinforce the structural gate and the MCP sandbox.

---

## Net effect

The design shift versus a generic "agent-assisted knowledge base" is from agent-assisted to **bounded, phase-gated knowledge production**:

- The agent becomes better at bookkeeping, retrieval, and drafting.
- The human remains the gatekeeper for meaning, promotion, and final structure.
- Every borrowed pattern is adopted for its mechanic; every scalar-optimization loop that sits on top of that mechanic is stripped.

This makes the architecture more reliable (errors surface at phase gates), easier to debug (each phase has traceable responsibility), and less likely to accumulate polished but untrusted content (nothing reaches canonical without human approval).

---

## The underlying survey

The ~47-system agent-research slice that grounds the four verdicts above is catalogued in full in the survey, not inline on this page. The wider ~400-paper corpus it sits inside — including the HCI, extraction, evaluation, and retrieval works behind the [cross-cutting findings](#cross-cutting-findings-from-the-full-literature-review) — lives in `_papers/` (Zotero export `_papers/Exported Items.bib`) with verdicts in `_papers/REVIEW-SUMMARY.md`. The surveyed agent systems span pipeline / role-based systems (LitSearch, ResearchArena, SciLitLLM, LitLLM, LatteReview, ResearchAgent, Idea2Story, AI Scientist v1/v2, Agent Laboratory, Sibyl, AutoResearchClaw, AI-Researcher, Auto-Research, OmegaWiki, CORAL, AIDE ML, MLR-Copilot, ScientistOne, ARA, Sibyl-AutoResearch), persistent-knowledge / cross-run systems (Karpathy Autoresearch, AI co-scientist, AiScientist long-horizon engineering, AgentRxiv, PARNESS, AI-Supervisor, NanoResearch, Omni-SimpleMem), retrieval / citation / structured-handoff systems (SciMON, MOOSE, CiteME, MetaGPT, Knows), runtime substrates (AutoGen, OpenHands, CycleResearcher), and the surveys and position papers (Gridach et al., [Chen 2026](../../reference/bibliography.md#chen2026copilots), Huang et al. 2025, Ren et al. 2025, Xu & Peng 2025, MASSW, Qi et al. 2023, Bisht et al. 2026, Feng & Liu 2026, Yue et al. 2026, Zhang et al. 2026, AutoResearchBench).

---

## Related

- The principles this survey operationalizes: [Design principles](../overview/design-principles.md)
- What Memoria is, in system terms: [What Memoria is](../overview/what-memoria-is.md)


---

<!-- source: explanation/operations/README.md -->

# Operations — the deterministic layer

Operations are Memoria's deterministic mechanisms — pure mechanism, no posture, no LLM judgment, never on the board ([ADR-46](../../adr/46-seven-layer-architecture.md)). You *run* an operation; you *delegate* to an agent. Five operations keep the substrate sound while the agents do the bookkeeping and the PI does the thinking.

## The invocation rule

*The path follows the caller*: **agents reach operations only through MCP** — that is the policy boundary, no exceptions — while **trusted callers (cron, CI, and the PI) invoke operations directly.** So an agent-reachable *processing* operation carries an MCP-tool facade *and* a direct entry, while integrity, cleanup, and telemetry operations run only by cron/CI need no facade at all — they run directly and post their findings or metrics to the vault.

## The five operations

The entry-point table is reference material; see [Operations](../../reference/operations.md). What matters here is the design split: processing operations expose MCP facades when agents need them, while integrity, cleanup, and telemetry operations stay direct because cron, CI, or the PI are the callers.

**Ingest** (`src/.memoria/operations/processing/ingest/runner.py`) is the mechanical core of cataloging; the Librarian agent fills only the two LLM holes (the comparative brief and the classification proposal). The resolve step merges Semantic Scholar, OpenAlex, Crossref, and PubMed/NCBI; the extract step tries Unpaywall OA PDFs before PMC JATS and local PDFs, with every PDF behind the same deterministic coherence gate. **Classification is automated, not gated** ([ADR-54](../../adr/54-two-decision-kinds-batch-worklists.md)): the classify stage maps the OpenAlex topics already in the enrichment payload to `research_area` (and a `methodology` facet from the publication types), applies a clear winner silently, audits every decision to `system/logs/classify.jsonl`, and raises an Inbox `flag` only on genuine ambiguity — near-tie or below the calibration floor — leaving the field unset for the PI. Its one gate is on **extraction uncertainty** ([ADR-56](../../adr/56-extraction-uncertainty-flag.md)): clean extractions write to the Catalog ungated, but below a confidence floor an entity-resolution, dedup, or license call emits a near-tie Inbox `flag` — the two candidates side by side — instead of merging silently. Both sets of thresholds live in `src/.memoria/schemas/calibration.yaml` with the other calibrated thresholds.

**Clustering** (`src/.memoria/mcp/cluster_mcp.py`) decides *how to display* — which topics and gaps the PI sees — never *what is canonical*; its parameters fall under the same calibration discipline. Beyond the JSON graph (`cluster_build_graph`) and topics (`cluster_model_topics`), it emits the **claim-debate map** (`cluster_emit_canvas`): the typed claim graph as a JSON Canvas artifact — `supports` edges green, `contradicts` red, `extends` neutral; node color = maturity, node size = in-degree, communities as group nodes. The Canvas is propose-class: it lands only in the ungated `notes/fleeting/maps/` staging home (inside the Librarian map lane's write scope), never the review-gated `notes/claims/` or `notes/hubs/`, and the PI edits or promotes it. Output is deterministic for identical input (fixed seed, params echoed).

**Integrity and cleanup sweeps** (`src/.memoria/operations/integrity/retraction/retraction.py` and `src/.memoria/operations/cleanup/`) are the deterministic integrity and cleanup sweeps. The retraction sweep (`--sweep`) writes `alert` cards. The *judgment* checks stayed an agent — [The Peer-reviewer](../profiles/peer-reviewer.md).

**The Linter** (`src/.memoria/operations/integrity/linter/detectors.py`) is schema-driven from `.memoria/schemas/` and plays two roles ([ADR-49](../../adr/49-catalog-in-bases-linter-monitor.md)): integrity **monitor** (the cron/CI sweep detects drift and flags it) and **commit gate** (a pre-commit `schema-check` blocks bad git-tracked writes). It also owns **golden-copy restore** (`src/.memoria/operations/integrity/linter/golden_restore.py`, [ADR-55](../../adr/55-src-scaffold-populate-golden-copy.md)): on detected drift the Linter restores a system file from the golden copy the installer stages at `.memoria/golden/` ([what is staged and why](../deployment/distribution-model.md#the-golden-copy-the-restore-source)) — propose-only by default; the PI or cron applies.

## Why operations are not agents

The split is by **determinism**: an operation produces the same result on every run, so it can serve as an audit trail, a CI gate, and a cron job — roles that depend on reproducibility. Anything requiring a posture or an LLM verdict is an agent. Findings from both reach the PI the same way — as Inbox cards at graded loudness — but an operation's card never carries a recommendation it would take judgment to make.

## Related

- The layer operations occupy: [Architecture](../architecture/README.md)
- The agents that call them through MCP: [Profiles](../profiles/README.md)
- The vault they maintain: [The vault](../architecture/vault.md)

