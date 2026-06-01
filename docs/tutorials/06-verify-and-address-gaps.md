---
title: "Tutorial 06: Verify and address a gap"
parent: Tutorials
---


# Tutorial 06: Verify and address a gap

**You will end with:** one verified draft section with a complete citation trail, and your first experience of the downstream feedback loop — where a gap in your draft sends a signal back to the upstream reading queue.

**Time:** 30–45 minutes.

**You will use:** Obsidian for drafting, the command palette for verification, and the board-state dashboard.

**Prerequisite:** [Tutorial 05](05-start-a-writing-project.md) complete — project folder created, `CHOSEN.md` committed.

---

## Step 1 — Create the draft file

Navigate to `40-workbench/first-synthesis/04-drafts/`.

Create a new file named `draft-01.md`. Open it.

---

## Step 2 — Write one section from your outline

Look at `CHOSEN.md`. Find the first section of your outline — the introduction, or the first substantive argument, depending on your framing.

Write 150–250 words of prose from that section. Not a perfect draft — just real sentences that make real claims. Open your claim notes in a split pane and write from what they say, in your own voice.

Write from your notes, not from memory. If you find yourself writing something you believe but haven't noted, add a `[need to check]` marker and keep going.

**Example prose you might write:**

> Notification timing research consistently shows that receptivity varies not by notification content but by the user's current cognitive load and availability state [need to trace]. Mamykina et al. (2010) demonstrated this through a field study of patients managing chronic illness — the moments when users most needed support were reliably the moments when they had the least capacity to act on it. A more recent line of work suggests that predicted availability, rather than measured interruption, is the variable that matters...

Save the file when you have at least 150 words.

---

## Step 3 — Run verification

With `draft-01.md` open:

Press `Cmd+P` → type `verify this draft` → select **Memoria: verify this draft**.

**What happens:** A card goes to the Verifier lane. Verifier reads the draft, parses it into discrete claims, and for each claim traces back to claim notes in `30-synthesis/01-claims/` that support it.

This takes 1–3 minutes. Watch the board-state dashboard for the Verifier card to advance from `running` to `done`.

---

## Step 4 — Read the verification report

Open `40-workbench/first-synthesis/05-verification/`.

You'll find a verification report. It looks like this:

```text
draft-01.md verification report

✓ TRACED: "receptivity varies with cognitive load" → [[receptivity-decreases-under-high-cognitive-load]]
✓ TRACED: "Mamykina et al. (2010) field study" → [[mamykina2010sense]]
✗ UNTRACED: "predicted availability rather than measured interruption is the key variable"
  → No matching claim note found. Closest: [[interruption-costs-scale-with-task-depth]] (0.41 similarity, below threshold)

Verdict: NEEDS REVISION — 1 untraced claim
```

The report also adds a `[!verification]` callout at the top of your draft with a summary verdict. (The human-readable `NEEDS REVISION` / `CLEAN` labels shown here correspond to the formal trace-result slugs `verify-needs-revision` / `verify-clean` in the [glossary](../reference/glossary.md) — same states, display vs. slug.)

---

## Step 5 — Soften the untraced claim

Find the untraced claim in the report. In this example: "predicted availability rather than measured interruption is the key variable."

Go to `draft-01.md`, find that sentence, and rewrite it with appropriate hedging:

> "Some researchers have suggested that predicted availability, rather than measured interruption, may be the key variable — though the evidence base here is thinner."

Save the file.

---

## Step 6 — Re-verify

Press `Cmd+P` → type `verify this draft` → select **Memoria: verify this draft** again.

Wait for the new report. The verification callout at the top of the draft should now show:

```text
[!verification]
Verdict: CLEAN — all claims traced
```

Every substantive claim in the prose now has a backing claim note.

---

## Step 7 — Commit the draft

Open Obsidian's Git panel (bottom status bar → Git icon, or `Cmd+P → Obsidian Git: Open source control`).

Stage `04-drafts/draft-01.md` and `05-verification/<report-file>.md`. Write a commit message: `first draft section with verification pass`. Commit.

When you commit, a git hook fires automatically and creates a Verify card on the Verifier lane as a final automated check. You can watch it on the board-state dashboard — it will quickly confirm the verification you just ran manually.

---

## Step 8 — Meet the review gate

So far every write in this tutorial landed in the workbench (`40-workbench/`), which is yours to edit freely. The moment an agent proposes a write to a **review-gated zone** — promoting a claim into the reference layer (`30-synthesis/02-reference/`) or producing a deliverable (`50-deliverables/`) — it does **not** land automatically. The card stops in the **review queue** (`done` with `review_status: requested`), and the policy MCP holds the write in `dry_run` until you approve it.

To see where these land: open `Home.md` — the front-door note that opens on startup — and go to the **board-state dashboard**. Any card waiting on you appears under the review-queue count. When you start promoting claims, you'll clear them here: **approve** to let the write land, **reject** to send it back as a fresh task.

This is the human gate that makes Memoria safe to run unattended — agents propose, you dispose; nothing reaches synthesis or deliverables without passing through you. Full procedure when you get there: [Work the review queue](../how-to-guides/writing/work-the-review-queue.md).

---

## What you have

- `40-workbench/first-synthesis/04-drafts/draft-01.md` — a verified draft section
- `40-workbench/first-synthesis/05-verification/` — the verification report
- A `[!verification] CLEAN` callout at the top of the draft
- A committed revision in git
- One untraced claim softened with appropriate hedging

**You've experienced the complete research loop.** Upstream: you brought in papers and wrote claim notes. Downstream: you scoped, framed, wrote, and verified. The verification found a gap. You addressed it.

**See also:** [The Verifier](../explanation/profiles/verifier.md) — how the Verifier traces claims, what similarity-check findings mean, and why gap cards close the upstream loop.

---

## Where to go from here

You now know the complete Memoria workflow. The daily rhythm from here is:

- **Capture** fleeting thoughts when they arise (`Cmd+P → Memoria: capture fleeting`)
- **Ingest** papers from Zotero when you add them (`Cmd+P → Memoria: capture from Zotero selection`)
- **Classify** and **discuss** new paper-notes during reading sessions
- **Write claim notes** after Socratic discussions
- **Clear the review queue** (open `Home.md` → board-state dashboard; approve or reject any card waiting at the gate)
- **Run the weekly review** (open `weekly-review.md` every Friday, process link suggestions, address any Linter findings)

The [how-to guides](../how-to-guides/) cover individual workflows in more depth. The [reference section](../reference/) is what you reach for when you need the exact name of a field or command.
