# Plans

Forward-looking project logistics: the release gate, the build-state ledger, and the roadmap to production use.

**One single-file release plan per version.** Each release's gate/tier *state*,
scope, blockers, and cut procedure live in `release-plan-<version>.md`; anything too
detailed for a crisp plan (full phase steps, investigation notes) goes to its
`-spillover.md` sibling. Per-artifact build state lives only in the build ledger.
Each fact is edited in exactly one place — every other doc points rather than restates.

| File | What it covers |
| --- | --- |
| [release-plan-template.md](release-plan-template.md) | The reusable single-file release-plan skeleton (copy per release; reset every Gate/Tier state to `todo`) |
| [release-plan-v0.1.md](release-plan-v0.1.md) | The v0.1 release plan: scope, gates (G#), validation tiers (T#), blockers, known limitations, cut procedure, roadmap |
| [release-plan-v0.1-spillover.md](release-plan-v0.1-spillover.md) | v0.1 overflow: the full phase roadmap (steps + exit criteria) the plan's §8 summarizes |
| [implementation-status.md](implementation-status.md) | The build-state ledger — per-artifact status (shipped / pending / deferred / approved) |
