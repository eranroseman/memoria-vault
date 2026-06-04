---
topic: tests
title: "{{Subject}} test protocol"
status: draft
---

<!--
TEMPLATE — derived from gui-test-protocol.md. Copy this file, rename it
<subject>-test-protocol.md, and fill the {{placeholders}}. Delete these comments.

Use a protocol like this for validation that a script/CI can't fully cover —
GUI flows, external services, human-in-the-loop steps, anything needing a real
device or eyeball. Each step is written so a different person could run it and
get the same verdict.

Conventions (keep them):
  • Every step: **Action** → **✓ Pass** (the exact observable that means it worked)
    → **✗ If it fails** (the first thing to check). Add **Expected** when the
    result needs describing before the pass check.
  • Number steps within a Part (A1, A2, …) so the results table and cross-refs
    can point at them.
  • Ground every step in real paths / commands / names — no generic hand-waving.
  • End with a results table the runner fills, then explicit green criteria.
-->

# {{Subject}} test protocol{{ — scope, e.g. "v0.1 (component X)"}}

{{One paragraph: what this protocol validates, and what is validated *elsewhere*
(so the reader knows the boundary). Name the gate(s)/tier(s) it backs, e.g. **T5**,
**G4**.}}

**Where to run.** {{The environment — machine, OS, which shells/apps you bounce
between. Be specific; this is why the protocol can't be headless/automated.}}

**How to read each step.** **Action** → **✓ Pass** (the exact thing that means it
worked) → **✗ If it fails** (first thing to check). Tick the boxes; fill the
results table at the end.

> {{Optional rule-of-thumb callout — a recurring judgment the runner needs, e.g.
> "empty is success" for dashboards. Delete if not needed.}}

---

## 0. Preconditions

<!-- Everything that must already be true before step 1. Each a checkable line. -->
- [ ] {{precondition — e.g. installer has run; `hermes profile list` shows 7 profiles}}
- [ ] {{precondition — apps installed / keys set / network mode / data seeded}}
- [ ] {{…}}

---

## Part A — {{Group title, e.g. "App opens and plugins load"}} ({{gate/tier}})

**A1. {{Step title}}.** {{Action — the exact thing to do.}}
- {{**Expected:** describe the result if it needs context.}}
- ✓ Pass: {{the precise observable}}.
- ✗ Fails: {{first thing to check / how to fix}}.

**A2. {{Step title}}.** {{Action}}
- ✓ Pass: {{…}}.
- ✗ Fails: {{…}}.

<!-- For a set of similar checks (plugins, dashboards, endpoints…), use a table
     whose last column is the per-row validation: -->

| {{Item}} | {{Purpose / source}} | ✓ Validate |
| --- | --- | --- |
| `{{item}}` | {{what it is}} | {{the concrete check}} |
| `{{item}}` | {{…}} | {{…}} |

- ✓ Pass: {{the aggregate criterion, e.g. "8/8 enabled, no errors"}}.
- ✗ Fails: {{triage}}.

---

## Part B — {{Group title}} ({{gate/tier}})

**B1. {{Step title}}.** {{Action.}}
```
{{exact command, if any}}
```
- ✓ Pass: {{observable}}.
- ✗ Fails: {{triage}}.

<!-- Add Parts C, D, … as needed. Keep each Part to one capability/decision. -->

---

## Results

<!-- One row per meaningful check (or per Part). The runner fills Pass/Fail + Notes. -->

| Section | Test | Pass / Fail | Notes |
| --- | --- | --- | --- |
| A | {{what A proves}} | | |
| B | {{what B proves}} | | |
| {{…}} | {{…}} | | |

**{{Gate/tier}} green** when {{the explicit condition across the Parts}}. Record the
outcome in the {{relevant rows}} of [release-plan-v0.1.md](../releases/v0.1/release-plan-v0.1.md).
