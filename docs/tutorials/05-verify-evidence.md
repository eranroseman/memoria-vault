---
title: "05: Verify evidence"
parent: Tutorials
nav_order: 5
---

# 05: Verify evidence

This tutorial turns one deterministic verification result into an explicit
review decision.

## Steps

**1. Add one deliberately incomplete evidence marker to the draft.**

Open `projects/<project>/draft.md` and add this sentence near the end:

```text
Participant burden always predicts receptivity. %%ev: ev-00000001 items=missing-work#^p0001%%
```

This derives a `single-span` evidence set. Because `missing-work#^p0001` does
not resolve, its state is `evidence-incomplete` and `review_required=false`.
The claim is deliberately too strong, giving verification incomplete evidence
to report.

**2. Re-run verification.**

```bash
memoria project verify --workspace . <project-path> --json
```

Read the JSON for evidence IDs and incomplete evidence. The command is
deterministic: a clean draft should stay clean until the draft, evidence, or
checked corpus changes.
Notice `ev-00000001` in the output.

**3. Record a disposition for the incomplete evidence.**

Because the evidence is incomplete, reject the marker:

```bash
memoria project resolve-evidence --workspace . <project-path> \
  --evidence-id ev-00000001 \
  --decision reject \
  --reason "Tutorial marker is deliberately unsupported"
```

Then remove or rewrite the unsupported sentence and verify again.
Reject records the PI disposition and keeps the export hold blocking; it does
not silently rewrite the draft or remove its durable evidence marker.

**4. Promote one draft passage into a note.**

Promotion is the intentional path from draft prose back into durable
knowledge. Promote the burden sentence the draft carries from Tutorial 03:

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

For more detail: [Project slice, outline, draft composition, verification, and
write-back](../how-to-guides/project/compose-a-draft.md).

Next: [06: Close loop](06-close-loop.md).
