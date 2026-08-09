---
title: Work the evidence-set review queue
parent: Project
grand_parent: How-to guides
nav_order: 3
---

# Work the evidence-set review queue

Use `memoria review` to work the batch queue after draft verification reports
evidence-review work. This is the PI's local review surface: it is not an
authenticated interface for an untrusted agent. For one finding while composing
a draft, use the separate [Compose a draft](compose-a-draft.md) flow instead.

## Prerequisites

- A working vault and installed Memoria CLI
- A project draft whose verification has reported evidence-review work
- The PI available to inspect and record every disposition

## Steps

**1. List the queue.**

```bash
memoria review list --workspace <vault>
```

The footer distinguishes the rows currently shown from the total queue, so a
batch does not conceal remaining work. The unfiltered queue also includes
read-only SRD gaps after its evidence-set rows.

**2. Narrow a large queue when that helps you focus.**

For example, select a project, a routing reason, rows old enough to revisit, or
a smaller batch:

```bash
memoria review list --workspace <vault> --project <project>
memoria review list --workspace <vault> --type multi-hop
memoria review list --workspace <vault> --min-age-days 7 --batch 5
```

`--type` is the routing-type filter; do not use a nonexistent
`--routing-type` option. Filtering changes the queue shown for this review; it
does not make the other rows resolved. Add `--json` only when a local script
needs the machine-readable form rather than the human review screen.

**3. Inspect one evidence set before deciding.**

Copy an evidence ID from the list and open it:

```bash
memoria review show ev-1234abcd --workspace <vault>
```

Read the claim, its grounds items, and the routing reason first. Machine
analysis is folded by default to preserve that order; expand it only after the
evidence with `--show-analysis`:

```bash
memoria review show ev-1234abcd --workspace <vault> --show-analysis
```

**4. Record exactly one PI disposition.**

Choose the disposition that records your judgment and include a reason:

```bash
memoria review accept ev-1234abcd --workspace <vault> \
  --reason "The cited spans support this claim" \
  --warrant "These sources jointly license the inference"
```

`--warrant` is available only with `accept`; here it records the PI's inference
license for the decision, not a synonym for the evidence set's grounds. The
other dispositions use the same shape without that option:

```bash
memoria review reject ev-1234abcd --workspace <vault> --reason "Grounds do not support the claim"
memoria review edit ev-1234abcd --workspace <vault> --reason "Revise the anchored claim"
memoria review defer ev-1234abcd --workspace <vault> --reason "Review after the next source pass"
```

Only `accept` clears an eligible hold. `reject` remains blocking, `edit`
records the need for an indicated content change, and `defer` suppresses the
row until the next UTC day. All four actions are PI-only; the batch cockpit is
not a way to delegate judgment to an agent.

Do not dispose of read-only cure rows or SRD gaps. A permanent finding such as
`evidence-text-drift` or `evidence-text-unbound` needs a repair to the draft or
its grounds, followed by verification; an SRD gap has no evidence disposition
at all. The queue names the applicable cure. See [Evidence sets](../../reference/control-and-policy/evidence-sets.md)
for the finding classes and the [Evidence-set review](../../reference/analysis-and-surfaces/evidence-review.md)
reference for the queue's exact behavior.

**5. Re-list and verify the project.**

```bash
memoria review list --workspace <vault>
memoria project verify --workspace <vault> projects/<project>/project.md
```

Continue with the next workflow step only after the relevant holds and permanent
findings have been resolved. If you want workflow telemetry, inspect it
separately:

```bash
memoria review stats --workspace <vault>
```

The statistics summarize review activity; they are neither a trust verdict nor
evidence that the queue and project verification are clear.

## Verify

- The rows you reviewed show their current disposition when you list the queue again.
- `memoria project verify` reports no relevant unresolved evidence hold or permanent finding.
- You have repaired, rather than dismissed, every read-only cure row and SRD gap.

## Related

- The single-finding drafting path: [Compose a draft](compose-a-draft.md)
- The queue's data model and dispositions: [Evidence-set review](../../reference/analysis-and-surfaces/evidence-review.md)
- Grounds, finding classes, and export holds: [Evidence sets](../../reference/control-and-policy/evidence-sets.md)
- Command roster and PI-only status: [CLI surfaces](../../reference/commands-and-transports/cli.md)
- The next step after verification: [Export a draft](export-a-draft.md)
