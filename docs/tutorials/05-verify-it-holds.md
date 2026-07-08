---
title: "Tutorial 05: Verify it holds"
parent: Tutorials
nav_order: 5
---

# Tutorial 05: Verify it holds

This tutorial turns one deterministic verification result into an explicit
review decision.

## Steps

**1. Add one review-required marker to the draft.**

Open `projects/<project>/draft.md` and add this sentence near the end:

```text
Participant burden always predicts receptivity. %%ev: ev-00000001 type=implicit state=evidence-incomplete review=true items=missing-work#^p0001%%
```

This is deliberately too strong. It gives verification something concrete to
report.

**2. Re-run verification.**

```bash
memoria project verify --workspace . <project-path> --json
```

Read the JSON for evidence IDs, review-required markers, and incomplete
evidence. The command is deterministic: a clean draft should stay clean until
the draft, evidence, or checked corpus changes.
Notice `ev-00000001` in the output.

**3. Resolve the evidence review item.**

Because the claim is unsupported, reject the marker:

```bash
memoria project resolve-evidence --workspace . <project-path> \
  --evidence-id ev-00000001 \
  --decision reject \
  --reason "Tutorial marker is deliberately unsupported"
```

Then remove or rewrite the unsupported sentence and verify again.

**4. Promote reusable prose deliberately.**

If a draft passage should become durable knowledge:

```bash
memoria project promote --workspace . <project-path> \
  --title "Reusable synthesis title" \
  --passage "Exact draft passage to preserve."
```

The promoted note starts unchecked. Review it before relying on it as checked
knowledge.

## What you should have seen

- Verification findings are explicit work, not hidden warnings.
- Evidence decisions are recorded.
- Draft passages become notes only through an intentional promotion path.

Next: [Close the loop](06-close-the-loop.md).
