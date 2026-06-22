---
title: "Tutorial 03: Draft a section from your claims"
parent: Tutorials
---

# Tutorial 03: Draft a section from your claims

**You will end with:** the one-line goal you wrote in Tutorial 00, realized as a short, cited section — drafted from your own claim and the sample's worked claims, with every citation bound to a source you actually hold.

**Time:** 40–55 minutes.

**You will use:** Obsidian, the Co-PI pane, and the claim cluster you completed in Tutorial 02.

**Prerequisite:** [Tutorial 02: Build claims and connect them](02-build-claims-and-connect-them.md) complete — the sample cluster finished (the `meddiet-and-stroke-risk` stub grounded, the unmade `supports` link made) and your own source distilled into at least one claim wired into the cluster.

This is the first **Produce** tutorial: you stop accumulating and write something defensible from what you now hold. Two moves carry it — *map* the corpus to see what it can and can't support, then *draft* a section against that map. The map is also where the corpus's planted gap surfaces.

---

## Step 1 — Open a Project

A draft needs somewhere to live. Run `Cmd/Ctrl-P` → **Memoria: start project** and fill the form: a title, a slug, the scope topic (Mediterranean diet and cardiovascular health), and the deliverable. For the inquiry fields, restate your Tutorial 00 goal — *a defensible 200-word section on whether a Mediterranean diet protects the heart*.

The command scaffolds `projects/<slug>/` with `project.md`, `thesis.md`, and empty `code/`, `drafts/`, and `exports/` folders. Then open any file under `projects/<slug>/` and run **Memoria: refresh project gate** — it updates `project-gate-index.md` with your graph maturity, saturation, and open gaps. The full procedure: [Start a writing project](../how-to-guides/project/start-a-writing-project.md).

The claims and the hub you built in Tutorial 02 are this project's inputs — you are not starting from nothing, you are drawing on a cluster.

---

## Step 2 — Map the corpus for coverage

Before you draft, ask the system what the corpus can actually support. Use the direct command (`Cmd/Ctrl-P` → **Memoria: map corpus**) when the scope is clear, or ask in the Co-PI pane if you want help framing it:

> "Map my corpus on Mediterranean diet and cardiovascular health — what do I have good coverage on, and where is it thin? I'm aiming at a 200-word defensible section on whether the diet protects the heart."

Either route creates a **`map`** task for the Librarian's map lane, which builds the typed graph and topic clusters and returns a coverage read through the Inbox, with **`gap` cards** for the thin areas ([The Librarian](../explanation/profiles/librarian.md)). Open the **Inbox space** → **Needs me** view to read them.

**This is where the gap surfaces.** The cluster you finished is dense on one thing — the trial and cohort evidence that a Mediterranean diet helps **high-risk or already-sick adults in Mediterranean and European populations**. The map will show that density, and it will also raise a gap card for what the corpus does *not* cover:

> "Corpus has no evidence on **primary prevention in low-risk people**, and nothing on whether the benefit **transports beyond Mediterranean populations and diets**." — the same honesty body a candidate card carries

That is not a defect in your work — it is the corpus telling you the truth about its own edges. The hub you studied in Tutorial 02 named this gap on purpose. **Keep the gap card.** You will draft *around* it now and let it pull your next reading in Tutorial 05. Read the coverage by pattern — a dense, mutually linked cluster is the tell that you can write from it; the full read-the-map procedure is in [Assess your corpus](../how-to-guides/project/assess-your-corpus.md).

---

## Step 3 — Decide what the section claims

The map told you what you can stand behind. Now scope the section to it. Open the hub (`mediterranean-diet-and-cvd`) and your own claim, and decide the spine of 200 words:

- The headline finding — `meddiet-reduces-major-cv-events` — carried by two randomized trials (`[@estruch2018]`, `[@delorgeril1999]`).
- Its likely mechanism — `evoo-and-nuts-active-components`, now linked under the headline by the `supports` link you made in Tutorial 02.
- The honest qualifier — `observational-associations-confounded`, sharpened by `predimed-randomization-caveat` — so the section does not overstate its case.
- The claim you grounded — `meddiet-and-stroke-risk`, from `[@sofi2010]` — and your own claim from your own source, wired into the cluster.

Write the gap into your scope deliberately: a defensible 200 words is one that says *who* the evidence is about and *where it stops*, not one that pretends to cover everyone. Record the framing where the draft lane can read it — write a short `projects/<slug>/chosen-framing.md` yourself (the claims this section stands on, plus a line on what it deliberately leaves out). The framing procedure: [Frame a project](../how-to-guides/project/frame-a-project.md).

---

## Step 4 — Draft the section

Now delegate the prose. Run `Cmd/Ctrl-P` → **Memoria: draft section**, or ask the Co-PI to shape the handoff. Name the section, the framing, and the claims it stands on:

> "Draft a ~200-word section on whether a Mediterranean diet protects the heart, from `projects/<slug>/chosen-framing.md`, using my claims on Mediterranean diet and cardiovascular health. Lead with the trial evidence, name the mechanism, qualify it with the confounding caution and the PREDIMED randomization caveat, and scope it to high-risk adults in Mediterranean populations. Cite citekeys in-text."

This creates a **`draft`** task for the **Writer** — a background lane you never chat with directly ([The Writer](../explanation/profiles/writer.md)). Two properties make its output trustworthy:

- **It writes only under `projects/`** — your claims, hub, Catalog, and Inbox are off-limits to it.
- **Its external-API policy is blocked** — it composes from your vault and *cannot* cite a source you do not hold. That is what binds the citations: every `[@citekey]` in the draft traces to a Catalog entity behind a claim you wrote.

The done card surfaces in the Inbox with the draft's location under `projects/<slug>/`. Keep citations in Pandoc form (`[@estruch2018]`) so the export route can later render the bibliography ([Draft with the Writer](../how-to-guides/project/draft-with-writer.md)).

---

## Step 5 — Make the draft yours

The Writer's output is a starting point, never the deliverable. Open the draft and read it as an editor:

- **Every citation should be a citekey you recognize** — one that sits on a claim in your cluster. The draft cannot invent one (blocked API), but it can lean on the wrong claim. If a sentence cites `[@estruch2018]` for something PREDIMED did not show, fix the sentence.
- **Don't draft past an unsupported claim.** If a line asserts something with no claim note behind it, stop: write the claim from a source you hold, or cut the line. The verify lane in Tutorial 04 will flag this anyway — cheaper to fix now.
- **The gap belongs in the prose, named.** A defensible section says where its evidence stops. One clause does it: *"…in high-risk adults; the trials say nothing about primary prevention in low-risk people or populations outside the Mediterranean."* That sentence is the seed of Tutorial 05.

Iterate by re-delegating a corrected spec, not by nagging the same card; small fixes you just make in the file yourself.

---

## What you have

- A Project under `projects/<slug>/` with a refreshed gate, holding your draft
- A coverage map of the cluster — and the **gap card** it surfaced, kept for Tutorial 05
- Your Tutorial 00 goal realized: a ~200-word section, drafted from your own claim and the sample's worked claims, every citation bound to a source you hold and traceable through its claim to a real paper

This is the *Produce* payoff the dense cluster bought you: cited prose, in one sitting, from a corpus that normally takes weeks of reading to build.

---

## What's next

[Tutorial 04: Verify it holds](04-verify-it-holds.md) — put the draft in front of the independent verify lane, read the finding-first cards, and turn it into a section you would defend.

---

← [Tutorial 02: Build claims and connect them](02-build-claims-and-connect-them.md) · [Tutorial 04: Verify it holds](04-verify-it-holds.md) →
