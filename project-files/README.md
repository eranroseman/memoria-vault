# Project files

One job each.

| Path | What it holds | When to look here |
|---|---|---|
| [decisions/](decisions/) | Accepted architectural decisions (ADRs) | You want to know *why* something is the way it is |
| [proposals/](proposals/) | Deferred capabilities and ideas under consideration (single-capability `PROP-NN` + thematic [surveys/](proposals/surveys/)) | You want to add a feature or understand what's been considered |
| [releases/](releases/) | Per-version release plans + readiness, and the reusable [release-plan template](releases/release-plan-template.md) | You want to know what a release covers or how to cut one |
| [process/](process/) | Contributor process docs (e.g. the [git workflow](process/git-workflow.md) post-mortem) | You want to know *how* we work in this repo |
| [tests/](tests/) | Reusable test protocols | You want to verify or validate the system |

Tools and approaches that were evaluated and **not** adopted are recorded as *Alternatives considered* in the relevant [decision](decisions/) and in the plugin reference docs (`docs/reference/`), not in a separate folder.

---

## How decisions and proposals differ

A **decision** is closed. Something was considered, a choice was made, and the design reflects it. Decisions don't change — they get superseded by a new decision if the design shifts. The number is permanent.

A **proposal** is open. It's a capability that's been thought through enough to have a clear shape, an adoption trigger, and known trade-offs — but it hasn't been scheduled yet. Proposals graduate to decisions when they're adopted, or stay in proposals until conditions warrant.

**If you're adding a new idea:** write a proposal file, not a decision. Use [proposals/_template.md](proposals/_template.md).

**If you're recording a choice that was just made:** write a decision file. Use [decisions/_template.md](decisions/_template.md) and give it the next available number.
