---
title: "05: Verify evidence"
parent: Tutorials
nav_order: 5
---

# 05: Verify evidence

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
Reject records the PI disposition; it does not silently rewrite the draft or
remove its durable evidence marker.

**4. Promote reusable prose deliberately.**

If a draft passage should become durable knowledge:

```bash
memoria project promote --workspace . <project-path> \
  --title "Reusable synthesis title" \
  --passage "Burden changes with context, recent prompts, and task demands."
```

The promoted note starts unchecked. Review it before relying on it as checked
knowledge. The passage must match the draft exactly. If it does not, the CLI
exits 1 and prints `FAILED: draft passage was not found in the project draft`
instead of claiming success.

## What you should have seen

- Verification findings are explicit work, not hidden warnings.
- Evidence decisions are recorded.
- Draft passages become notes only through an intentional promotion path.

Next: [06: Close loop](06-close-loop.md).
