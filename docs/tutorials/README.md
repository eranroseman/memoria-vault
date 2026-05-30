---
topic: tutorials
---

# Tutorials

Step-by-step walkthroughs, in order. Each builds on the last. Start at the top if you're new.

| # | Tutorial | What you end with |
| --- | --- | --- |
| 01 | [Set up from zero](01-set-up-from-zero.md) | A working vault, one profile, one ingested source (agent steps gated on the v0.2 wiring). |
| 02 | [Ingest and classify a batch](02-ingest-and-classify-a-batch.md) | 5–10 sources ingested and classified; the first `[!brief]` comparisons. |
| 03 | [Run the Linter and read its findings](03-run-the-linter.md) | A lint report you can act on; the verdict band explained. |
| 04 | [Promote a claim note](04-promote-a-claim-note.md) | One claim note authored and promoted toward `reference-note`. |
| 05 | [Add a second profile](05-add-a-second-profile.md) | A second lane (e.g. Mapper) installed and exercised. |

> **Status.** Tutorials 02, 03, and 05 exercise the agent pipeline, which depends on the **v0.2 profile wiring** (`config.yaml`, `mcp.json`, `policy_mcp.py`, lane-overrides) not yet in the starter vault — see [implementation-status.md](../project/implementation-status.md). They are written as the intended flow; tutorial 04 (claim authoring + promotion) is mostly human-driven and works today.
