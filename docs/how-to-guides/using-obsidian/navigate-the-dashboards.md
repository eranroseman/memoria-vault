---
title: Navigate the dashboards
parent: Using Obsidian
nav_order: 5
---

# Navigate the dashboards

Ten dashboards in `00-meta/01-dashboards/`, plus the `daily-health.md` dashboard (Daily Health). Each answers one question about the vault. This guide maps situations to dashboards — open the right one first.

For what each dashboard shows in detail, see [explanation/dashboards/](../../explanation/dashboards/).

## Dashboards pre-loaded by workspace

Switch workspace (`Ctrl+1/2/3`) to get the dashboards most relevant to your current mode:

| Workspace            | Hotkey   | Left pane                                       | Right pane        |
| -------------------- | -------- | ----------------------------------------------- | ----------------- |
| Human                | `Ctrl+1` | Daily Health                                    | Board State       |
| Reading & Processing | `Ctrl+2` | Discuss Queue (top) + Reading Pipeline (bottom) | Socratic ACP pane |
| Drafting             | `Ctrl+3` | Project folder                                  | Backlinks         |

For other dashboards, open manually: `Cmd/Ctrl+P` → Omnisearch → type the dashboard name.

---

## Situation → dashboard

### "What needs attention right now?"

**Daily Health** — opens in the Human workspace left pane (`Ctrl+1`).

Glance at the start of every session. Shows today's HIGH and CRITICAL lint findings, overdue Kanban cards, and anything the system flagged since your last session. Empty means nothing urgent. Under 30 seconds to read.

### "What work is in flight? What's stuck?"

**Board State** — Human workspace right pane (`Ctrl+1`).

Kanban lane counts and oldest card per lane. If a card has sat in one lane more than 3 days, it's likely stuck. See [Fix a stuck card](../recovery/fix-stuck-card.md).

### "What papers are waiting for me to classify?"

**Reading Pipeline** — Reading & Processing workspace, left pane bottom (`Ctrl+2`).

All sources with `lifecycle: proposed`. Sort is oldest-first — clear the oldest items first. See [Classify a source](../compile/classify-a-source.md).

### "Which papers should I be reading and discussing?"

**Discuss Queue** — Reading & Processing workspace, left pane top (`Ctrl+2`).

Paper notes that are `lifecycle: current` but haven't had a Socratic discussion pass. Sort is oldest-first. Open a paper from this queue, then open the ACP pane (**Agent Client: Open chat view**) and switch to Socratic — the active note auto-attaches. See [Discuss a paper](../compile/discuss-a-paper.md).

### "What open questions has my synthesis raised?"

**Open Questions** — open manually.

Collects every claim note and paper note that contains an explicit `## Open questions` section (read from `30-synthesis/01-claims/` and `20-sources/01-papers/`), newest first. It shows _which_ notes carry questions — you open the note to read them in context. Review during the weekly review or when starting a new topic cluster. These are things your existing notes flag but can't answer — discovery prompts.

### "Are any of my claims contradicted by other claims?"

**Contradictions** — open manually.

This dashboard lists every pair of claim notes joined by a **human-set** `relations.contradicts` link. No model judges which claims conflict — the agents may _propose_ a contradiction for confirmation, but the link is always human-set (the NLI-based proposer is deferred). Check before promoting a claim to canonical reference or submitting a draft — unresolved contradictions mean the argument isn't settled.

### "Something seems wrong but I can't see why"

**Drift Watch** — open manually.

Verdict band at the top: PASS / REVIEW / FAIL. FAIL means structural desynchronization between the vault source, deployed Hermes profiles, and working vault state. Open when profiles behave unexpectedly or when commands fire but produce wrong results. See [Fix profile drift](../recovery/fix-profile-drift.md).

### "Are my agents performing well? Is API cost increasing?"

**Fleet Health** — open manually.

Operational metrics per profile: success rate, latency, token cost. Check monthly or when a profile seems slow or returning degraded responses. Not for daily use — meaningful only after a week or more of accumulated data.

### "What did the policy MCP allow or deny?"

**Audit Log** — open manually.

Per-decision forensics. Open when a write operation didn't happen as expected — the audit log shows whether it was denied and why. Also useful after any profile configuration change to confirm the new policy is behaving as intended.

### "What do I need to do this week?"

**Weekly Review** — open on Fridays.

Consolidated weekly agenda: classify backlog, outstanding discovery candidates, drift-watch verdict, retraction candidates. The [Run the weekly review](../maintain/run-the-weekly-review.md) guide walks through it step by step.

### "What orphan or noise files are in the vault?"

**Loose Ends** — open during the weekly review or after a lint pass.

Files named `TODO`, `tmp`, `untitled`, or matching other noise patterns. More than five is a cleanup signal.

---

## Quick reference

| Dashboard        | When to open                     | Workspace shortcut    |
| ---------------- | -------------------------------- | --------------------- |
| Daily Health     | Start of session                 | `Ctrl+1`, left        |
| Board State      | Check for stuck cards            | `Ctrl+1`, right       |
| Reading Pipeline | Classify backlog                 | `Ctrl+2`, left bottom |
| Discuss Queue    | Reading session                  | `Ctrl+2`, left top    |
| Open Questions   | Weekly review / new topic        | Manual                |
| Contradictions   | Before claim promotion or filing | Manual                |
| Drift Watch      | When something seems off         | Manual                |
| Fleet Health     | Monthly check                    | Manual                |
| Audit Log        | After unexpected write failure   | Manual                |
| Weekly Review    | Fridays                          | Manual                |
| Loose Ends       | Weekly review or lint pass       | Manual                |

## Related

- Weekly review procedure: [Run the weekly review](../maintain/run-the-weekly-review.md)
- Workspace layouts and hotkeys: [Obsidian workspaces](../../reference/obsidian-workspaces.md)
- Dashboard design rationale: [Dashboards](../../explanation/dashboards/README.md)
