# Project files

One job each.

| Path | What it holds | When to look here |
|---|---|---|
| [Decisions](../docs/adr/) | Architecture Decision Records (ADRs) at every status — `proposed` · `accepted` · `deferred` · `superseded` · `rejected` | You want to know *why* something is the way it is, or what's been considered |
| [Design notes](../docs/design/) | Durable design analysis, as-built captures, and research that inform the ADRs | You want the background behind a decision |
| [release/](release) | Per-version release plans + readiness, and the reusable [release-plan template](release/release-plan-template.md) | You want to know what a release covers or how to cut one |
| [Contributing workflow](process.md) | Branch discipline, issue/board flow, landing checklists, divergence recovery | You want to know *how* we work in this repo |
| [test/](test) | Reusable test plans | You want to verify or validate the system |

Decisions and the design notes behind them live under [docs/](../docs/) so they render
on the docs site alongside the explanation pages. Tools and approaches evaluated and
**not** adopted are recorded as *Alternatives considered* in the relevant
[ADR](../docs/adr/) and in the plugin reference docs (`docs/reference/`), not in a
separate folder.

---

## One folder for every decision

There is no separate "proposals" folder. A capability that's been thought through but
not yet scheduled is an ADR with `status: deferred` (or `proposed`) — it lives in
[Decisions](../docs/adr/) with the accepted ones, under one number sequence. A deferred
ADR is **not** gated on a static adoption trigger; it records `assumes:` (what it rests
on) so a change that invalidates it is detectable, and it is re-judged each release
cycle.

**Adding any decision — open or closed:** copy [the ADR template](../docs/adr/_template.md),
take the next number, and set `status` to where it actually is in its lifecycle.
