---
title: "Tutorial 04: Draft a section from your claims"
parent: Tutorials
---

# Tutorial 04: Draft a section from your claims

**You will end with:** the goal you named in Tutorial 01, realized as a short, cited section — drafted from your own claim and the sample's worked claims, with every citation bound to a source you actually hold.

**Time:** 30–45 minutes.

**You will use:** Obsidian, the Co-PI pane, the project you opened in Tutorial 01, and the claim cluster you completed in Tutorial 03.

**Prerequisite:** [Tutorial 03: Build claims and connect them](03-build-claims-and-connect-them.md) complete — the sample cluster finished (the `meddiet-and-stroke-risk` stub grounded, the unmade `supports` link made) and your own source distilled into at least one claim wired into the cluster.

You already opened a project and read its coverage map in [Tutorial 01](01-orient.md); since then your cluster has grown — your own claim joined it in Tutorial 03. Now you stop accumulating and **produce**: decide what the section can stand behind, then draft it. The gap you saw on the map stays in view — a defensible section is honest about where its evidence stops.

---

## Step 1 — Decide what the section claims

The map in Tutorial 01 told you what you can stand behind. Now scope the section to it. Open the hub (`mediterranean-diet-and-cvd`) and your own claim, and decide the spine of 200 words:

- The headline finding — `meddiet-reduces-major-cv-events` — carried by two randomized trials (`[@estruch2018]`, `[@delorgeril1999]`).
- Its likely mechanism — `evoo-and-nuts-active-components`, now linked under the headline by the `supports` link you made in Tutorial 03.
- The honest qualifier — `observational-associations-confounded`, sharpened by `predimed-randomization-caveat` — so the section does not overstate its case.
- The claim you grounded — `meddiet-and-stroke-risk`, from `[@sofi2010]` — and your own claim from your own source, wired into the cluster.

Write the gap into your scope deliberately: a defensible 200 words is one that says *who* the evidence is about and *where it stops*, not one that pretends to cover everyone. Record the framing where the draft lane can read it — write a short `projects/<slug>/chosen-framing.md` yourself (the claims this section stands on, plus a line on what it deliberately leaves out). The framing procedure: [Frame a project](../how-to-guides/project/frame-a-project.md).

---

## Step 2 — Draft the section

Now delegate the prose. Run `Cmd/Ctrl-P` → **Memoria: draft section**, or ask the Co-PI to shape the handoff. Name the section, the framing, and the claims it stands on:

> "Draft a ~200-word section on whether a Mediterranean diet protects the heart, from `projects/<slug>/chosen-framing.md`, using my claims on Mediterranean diet and cardiovascular health. Lead with the trial evidence, name the mechanism, qualify it with the confounding caution and the PREDIMED randomization caveat, and scope it to high-risk adults in Mediterranean populations. Cite citekeys in-text."

This creates a **`draft`** task for the **Writer** — a background lane you never chat with directly ([The Writer](../explanation/profiles/writer.md)). Two properties make its output trustworthy:

- **It writes only under `projects/`** — your claims, hub, Catalog, and Inbox are off-limits to it.
- **Its external-API policy is blocked** — it composes from your vault and *cannot* cite a source you do not hold. That is what binds the citations: every `[@citekey]` in the draft traces to a Catalog entity behind a claim you wrote.

The done card surfaces in the Inbox with the draft's location under `projects/<slug>/`. Keep citations in Pandoc form (`[@estruch2018]`) so the export route can later render the bibliography ([Draft with the Writer](../how-to-guides/project/draft-with-writer.md)).

---

## Step 3 — Make the draft yours

The Writer's output is a starting point, never the deliverable. Open the draft and read it as an editor:

- **Every citation should be a citekey you recognize** — one that sits on a claim in your cluster. The draft cannot invent one (blocked API), but it can lean on the wrong claim. If a sentence cites `[@estruch2018]` for something PREDIMED did not show, fix the sentence.
- **Don't draft past an unsupported claim.** If a line asserts something with no claim note behind it, stop: write the claim from a source you hold, or cut the line. The verify lane in Tutorial 05 will flag this anyway — cheaper to fix now.
- **The gap belongs in the prose, named.** A defensible section says where its evidence stops. One clause does it: *"…in high-risk adults; the trials say nothing about primary prevention in low-risk people or populations outside the Mediterranean."* That sentence is the seed of Tutorial 06.

Iterate by re-delegating a corrected spec, not by nagging the same card; small fixes you just make in the file yourself.

---

## What you have

- Your Tutorial 01 goal realized: a ~200-word section, drafted from your own claim and the sample's worked claims, every citation bound to a source you hold and traceable through its claim to a real paper
- The gap card still in your Inbox, now named in the prose — kept for Tutorial 06

This is the *Produce* payoff the dense cluster bought you: cited prose, in one sitting, from a corpus that normally takes weeks of reading to build.

---

## What's next

[Tutorial 05: Verify it holds](05-verify-it-holds.md) — put the draft in front of the independent verify lane, read the finding-first cards, and turn it into a section you would defend.

---

← [Tutorial 03: Build claims and connect them](03-build-claims-and-connect-them.md) · [Tutorial 05: Verify it holds](05-verify-it-holds.md) →
