# Domain Docs

How the engineering skills should consume this repo's domain documentation when exploring the codebase.

## Before exploring, read these

- **`CONTEXT.md`** at the repo root. It is a **pointer stub**, not the vocabulary
  itself — follow it to the canonical glossary.
- **`docs/reference/data-model/glossary.md`** — the canonical vocabulary. One
  definition per term, usage rulings included. This is the document to read
  before naming anything.
- **`docs/adr/`** — read ADRs that touch the area you're about to work in.

If any of these files don't exist, **proceed silently**. Don't flag their absence; don't suggest creating them upfront. The `/domain-modeling` skill (reached via `/grill-with-docs` and `/improve-codebase-architecture`) creates them lazily when terms or decisions actually get resolved.

## File structure

This repo is single-context. The root `CONTEXT.md` exists only so tools that look
for that filename by convention find their way to the real glossary:

```
/
├── CONTEXT.md                              ← stub; routes to the glossary and AGENTS.md
├── AGENTS.md                               ← agent operating facts
├── docs/
│   ├── adr/                                ← architecture decision records
│   └── reference/data-model/glossary.md    ← THE canonical vocabulary
└── src/
```

## Use the glossary's vocabulary

When your output names a domain concept (in an issue title, a refactor proposal, a hypothesis, a test name), use the term as defined in **`docs/reference/data-model/glossary.md`**. Don't drift to synonyms the glossary explicitly avoids.

If the concept you need isn't in the glossary yet, that's a signal — either you're inventing language the project doesn't use (reconsider) or there's a real gap (note it for `/domain-modeling`).

**New rulings land in the glossary**, never in the `CONTEXT.md` stub and never in
a new file. AGENTS.md states the rule directly: never start a second glossary.

## Flag ADR conflicts

If your output contradicts an existing ADR, surface it explicitly rather than silently overriding:

> _Contradicts ADR-0007 (event-sourced orders) — but worth reopening because…_

Historical ADRs predating `docs/adr/` survive only as a frozen export at
`design-history/archive/notes/docs-exports/adr-full.md`. Cite one from there by
number if it is still load-bearing, and note that it has no live file yet.
