
# The discuss-queue dashboard

It is the **upstream-cognitive-discipline dashboard**: a long queue means the human's processing is falling behind their ingest rate; a short queue means it's keeping up. Making that asymmetry visible early is the point — before it hardens into a synthesis backlog months later.

---

## What it shows

Every fully-classified paper note (`lifecycle: current`) that hasn't yet had a Socratic processing pass, oldest first. The queue length *is* the signal: it measures the gap between how fast sources come in and how fast the human actually thinks them through.

---

## What this dashboard is not

**Not [reading-pipeline](reading-pipeline.md).** Reading-pipeline is the broader view: all papers in active processing plus claim-note maturity. Discuss-queue is a single focused signal: which classified sources still owe a Socratic conversation. The implied next action is specific — invoke the Socratic profile, work through the questions, then write a claim note. A generic list without that implied action would just be noise.

**Not a generic to-do list.** Discuss-queue is not a general inbox or a catch-all task surface. Its one question is: which sources are classified and waiting for the thinking step?

---

## Why it's designed this way

**Five-or-fewer rows is healthy.** Ten or more rows is a signal to schedule a reading session. These thresholds are called out in the dashboard itself. The goal is to make the queue's depth readable at a glance, without needing to count or calculate.

**A reading-session cadence, not a daily alarm.** Unlike Daily Health's morning health check, discuss-queue is consulted only at reading time. Opening it every morning would be noise; the queue doesn't change unless classification happens. The deliberate cadence is part of the discipline — this dashboard exists to protect time for deep reading, not to add another daily obligation.

**The Reading & Processing workspace includes this dashboard.** In the `Cmd-2` workspace, discuss-queue sits in the left pane alongside reading-pipeline, with the source note and Backlinks panel to the right. The workspace exists precisely to support the discuss-queue discipline: everything needed for literature processing in one screen layout.

---

## Related

- Broader sibling: [reading-pipeline](reading-pipeline.md)
- The profile invoked to drain this queue: [Socratic](../profiles/socratic.md)
- Workflow: [discuss a paper](../../how-to-guides/sources/discuss-a-paper.md)
- The workspace this dashboard anchors: [workspaces](../../reference/obsidian-workspaces.md)
