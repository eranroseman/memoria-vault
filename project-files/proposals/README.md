---
topic: proposals
---

# Proposals

Capabilities thought through but not yet adopted. Each has a clear shape, known
trade-offs, and an explicit adoption trigger — a specific condition that would
warrant scheduling it. A proposal is not a to-do item; it won't be scheduled until
its trigger fires.

Two kinds, both browsable in this directory:

- **Single-capability proposals** — `PROP-NN-*.md`, one capability each, following the full [_template.md](_template.md).
- **Capability explorations** — thematic bundles of several related capabilities, in [explorations/](explorations/); unnumbered, each capability carrying its own lighter What / Trade-offs / Adoption trigger / Guard block.

---

## How to use this folder

**Adding an idea:** copy [_template.md](_template.md), name it `slug-describing-capability.md` (or `PROP-NN-…` to number it). New ideas are proposals, not decisions — see [AGENTS.md §10](../../AGENTS.md).

**When a proposal is adopted:** move the file to [decisions/](../decisions/), assign the next ADR number, set `status: accepted`. The proposal becomes the ADR's starting point.

**When a proposal is rejected:** add a `status: rejected` field and a "Why rejected" section, and keep the file — cheaper than rediscovering the same idea later.

Tools and approaches evaluated and **not** adopted are recorded as *Alternatives considered* in the relevant [decision](../decisions/) and the plugin reference docs (`docs/reference/`), not enumerated here.
