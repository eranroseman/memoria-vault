---
title: v0.1.0-alpha.9
parent: Releasing
has_children: true
---

# v0.1.0-alpha.9

The **UI/workflow and runtime-gate** checkpoint. alpha.9 is the current draft
internal checkpoint: it carries the Obsidian workflow review, runtime capability
boundary hardening, Hermes-version decision, and ADR/code/docs truth-alignment
work surfaced during the alpha.9 audits.

Live readiness state belongs to the
[Release v0.1.0-alpha.9](https://github.com/eranroseman/memoria-vault/issues/835)
parent issue and its gate/stage sub-issues. Scope belongs to the
`0.1.0-alpha.9` milestone plus the Memoria Issue Tracker.

| File | Holds |
|---|---|
| `release-plan-0.1.0-alpha.9.md` | The release plan: scope, gates, stages, limitations, docs/runtime bars, and cut procedure. |
| `tmp/execplan-alpha9-ui-workflow-runtime-gates.md` | The living implementation plan for this checkpoint. |
| `tmp/*.md` / `tmp/*.py` | Temporary alpha.9 research, audits, probes, and spike scripts to disposition before closeout. |

## Tmp disposition check

At alpha.9 closeout, every tracked file under `tmp/` must either be folded into
durable docs/ADRs/issues, moved forward to the next release `tmp/`, or deleted
after its findings have been routed. Do not delete the folder as cleanup until
each file has a named disposition in the release plan, ExecPlan, or issue trail.

