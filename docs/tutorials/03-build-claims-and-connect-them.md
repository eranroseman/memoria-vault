---
title: "Tutorial 03: Build claims and connect them"
parent: Tutorials
---

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
