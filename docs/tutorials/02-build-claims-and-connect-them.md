---
title: "Tutorial 02: Build claims and connect them"
parent: Tutorials
---

# Tutorial 02: Build claims and connect them

**You will end with:** the sample's half-built cluster finished — one stubbed claim grounded in its source and one missing link made — plus a claim of your own distilled from your source and wired into the graph. A connected cluster dense enough to write from.

**Time:** 30–45 minutes.

**You will use:** the Obsidian command palette, the Co-PI pane, and the sample vault's claims.

**Prerequisite:** [Tutorial 01: Bring in your first source](01-bring-in-your-first-source.md) complete.

---

A source note is a reading record; a **claim** is a single durable assertion you can write *from*. Distilling claims and linking them is the move that turns a pile of reading into a structure — and it is the one move that fails most often when you learn it cold, because it is tempting to write claims that don't quite trace to a source.

So you learn it in three fades. First you **study** a finished claim. Then you **finish** the pieces the sample left half-built — lower stakes, because the shape is already there. Only then do you do it **cold**, on your own source. By the third pass the move is yours.

## Step 1 — Study a worked claim

Open the sample claim **"A Mediterranean diet reduces major cardiovascular events…"** (`meddiet-reduces-major-cv-events`) in `notes/claims/`. Read its three sections and notice what makes it a claim, not a summary:

- **Claim** — one sentence. Not a paragraph, not a topic. One assertion you could defend or be wrong about.
- **Evidence** — every line ends in a citekey (`[estruch2018]`, `[delorgeril1999]`) that appears in the note's `sources` field. This is the **provenance guardrail**: a claim with an evidence line that traces to no source is the exact failure Memoria exists to prevent. If you can't cite it, it isn't a claim yet — it's a hunch (a fleeting note).
- **Connections** — prose context for its typed links. Look at the frontmatter `links` block: this claim `contradicts` `observational-associations-confounded`. A claim graph holds disagreement on purpose; the tension is information, not a bug to resolve.

That shape — one sentence, traced evidence, typed links — is what you're about to reproduce twice.

---

## Step 2 — Finish the sample's half-built work

The sample left two things deliberately undone. Completing them is the lower-stakes middle of the fade.

**2a — Ground the stubbed claim from its source.** Open the claim **"Higher Mediterranean-diet adherence is associated with lower stroke risk"** (`meddiet-and-stroke-risk`). Its `sources` is empty and its **Evidence** section is a prompt: the assertion is there, but nothing grounds it — right now it is a hunch wearing a claim's clothes.

Open the half-built source note **`sofi2010-meta-analysis`** beside it. Its **In my words** is a prompt too — it was captured but never read. Read the paper's abstract, write two or three plain sentences in **In my words**, then go back to the claim and finish it: add `sofi2010` to the claim's `sources`, and write one **Evidence** line that traces to it. The moment the citekey and the evidence line agree, the claim is real.

**2b — Make the missing link.** Open the claim **"Extra-virgin olive oil and nuts are the components most linked to the benefit"** (`evoo-and-nuts-active-components`). It is distilled but unlinked — it names a *mechanism* for the headline effect, yet nothing says so in the graph. With the claim active, `Cmd/Ctrl-P` → **Memoria: link claim**, and propose a `supports` link to `meddiet-reduces-major-cv-events`. The link is a *proposal* until you confirm it at the link gate (next aside); confirm it now.

---

## Step 3 — Distill a claim from your own source, cold

Now the rep that matters. Open your own source note from Tutorial 01 and look at its **Worth distilling** bullets. Pick the one that is closest to a single defensible sentence.

With the source note active, `Cmd/Ctrl-P` → **Memoria: create linked claim note**. That spawns a claim already carrying your source in `sources`. Fill it the way the worked claim taught you:

1. **Claim** — one sentence. If it needs an "and," it is probably two claims.
2. **Evidence** — one or two lines, each tracing to your citekey. If a line won't trace, cut it or capture the source that would ground it.
3. **Connections** — then `Cmd/Ctrl-P` → **Memoria: link claim** and propose a typed link to a neighboring claim: one of yours, or one of the sample's if your topic touches it. `supports` if it points the same way, `contradicts` if it cuts against — disagreement is welcome.

You have now distilled a claim with no scaffolding under you. That is the Accumulate habit's hardest move, done once on your own material.

---

## A note on the link gate

Typed links are never written silently. `Memoria: link claim` *proposes* a `supports`/`contradicts` edge; it becomes part of the graph only when you confirm it at the **link gate**. The agent can find candidate connections all day, but which links are real is your judgment — the same division that runs through the whole system. Confirming is one keystroke; the point is that nothing typed enters the graph behind your back.

---

## What you have

- The sample's stubbed claim now **grounded** in `sofi2010`, evidence tracing to a citekey
- The missing `supports` link **made** and confirmed — the mechanism claim now sits under the headline claim
- One claim of your own, distilled cold and wired into the cluster
- A claim layer dense enough to write from — which is exactly what the next tutorial does

A vault with 50 sources and 5 claims is a reading list. The difference is the density you just added: connected claims you can navigate instead of re-reading.

---

## What's next

[Tutorial 03: Draft a section from your claims](03-draft-a-section-from-your-claims.md) — open a Project, map the corpus for coverage, and draft your goal section with citations bound to these claims.

---

← [Tutorial 01: Bring in your first source](01-bring-in-your-first-source.md) · [Tutorial 03: Draft a section from your claims](03-draft-a-section-from-your-claims.md) →
