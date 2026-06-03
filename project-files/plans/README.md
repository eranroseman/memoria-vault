# Plans

Forward-looking project logistics: the release gate, the build-state ledger, and the roadmap to production use.

**One single-file release plan per version.** Each release's gate/tier *state*,
scope, blockers, and cut procedure live in `release-plan-<version>.md`; anything too
detailed for a crisp plan (full phase steps, investigation notes) goes to its
`-spillover.md` sibling. Per-artifact build state lives only in the build ledger.
Each fact is edited in exactly one place — every other doc points rather than restates.

Per-release artifacts (the dated plan, its spillover, the shippability
assessment, the GUI-run record) live under `../releases/<version>/`. This folder
holds only the release-agnostic logistics: the reusable template and the living
build ledger.

| File | What it covers |
| --- | --- |
| [release-plan-template.md](release-plan-template.md) | The reusable single-file release-plan skeleton (copy per release; reset every Gate/Tier state to `todo`) |
| [implementation-status.md](implementation-status.md) | The build-state ledger — per-artifact status (shipped / pending / deferred / approved) |
| [../releases/v0.1/](../releases/v0.1/) | The v0.1 release set: plan, spillover roadmap, shippability assessment, GUI-test record |
