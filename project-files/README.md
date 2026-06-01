# Project files

Four folders. One job each.

| Folder | What it holds | When to look here |
|---|---|---|
| [decisions/](decisions/) | Accepted architectural decisions | You want to know *why* something is the way it is |
| [proposals/](proposals/) | Deferred capabilities and ideas under consideration | You want to add a feature or understand what's been considered |
| [rejected/](rejected/) | Tools and approaches evaluated and not adopted | You want to avoid re-evaluating something already considered |
| [plans/](plans/) | Timeline, implementation status, release plan | You want to know what's built and what to do next |

---

## How decisions and proposals differ

A **decision** is closed. Something was considered, a choice was made, and the design reflects it. Decisions don't change — they get superseded by a new decision if the design shifts. The number is permanent.

A **proposal** is open. It's a capability that's been thought through enough to have a clear shape, an adoption trigger, and known trade-offs — but it hasn't been scheduled yet. Proposals graduate to decisions when they're adopted, or stay in proposals until conditions warrant.

**If you're adding a new idea:** write a proposal file, not a decision. Use [proposals/_template.md](proposals/_template.md).

**If you're recording a choice that was just made:** write a decision file. Use [decisions/_template.md](decisions/_template.md) and give it the next available number.
