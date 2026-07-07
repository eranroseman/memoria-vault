---
title: "Tutorial 05: Verify it holds"
parent: Tutorials
nav_order: 5
---

# Tutorial 05: Verify it holds

This tutorial turns a verification result into explicit review decisions.

## Steps

**1. Re-run verification after editing the draft.**

```bash
memoria project verify --workspace . <project-path> --json
```

Read the JSON for evidence IDs, review-required markers, and incomplete
evidence. The command is deterministic: a clean draft should stay clean until
the draft, evidence, or checked corpus changes.

**2. Resolve an evidence review item.**

When you have checked the source span and agree with the marker:

```bash
memoria project resolve-evidence --workspace . <project-path> \
  --evidence-id <evidence-id> \
  --decision accept \
  --reason "Reviewed source span"
```

Use `--decision reject` when the draft passage is not supported. Then edit the
draft or notes and verify again.

**3. Promote reusable prose deliberately.**

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
- Accepted evidence decisions are recorded.
- Draft passages become notes only through an intentional promotion path.

Next: [Close the loop](06-close-the-loop.md).
