---
title: "Tutorial 04: Draft a section from your claims"
parent: Tutorials
---

# Tutorial 04: Draft a section from your claims

*Session 2 of 3 · Produce a cited section.*

**You'll finish with:** the goal you named in Tutorial 01, turned into a short, cited section — drafted from your own claim and the sample's worked claims, with every citation bound to a source you actually hold.

**Time:** 30–45 minutes.

**You'll use:** Obsidian, the Co-PI pane, the project you opened in Tutorial 01, and the claim cluster you completed in Tutorial 03.

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
