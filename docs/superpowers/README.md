# docs/superpowers/

Working records for how Memoria gets built: specs, plans, and audits produced
while running the superpowers workflow. Tracked in git but **not published** to
the docs site (excluded in `docs/_config.yml`), because these are process
artifacts, not product documentation.

- `plans/` — implementation plans for in-flight work.
- `specs/` — dated design records, the in-flight release's decision ledger and
  companions, and derived scope/decision briefs. A ledger folds into
  `design-history/` when its release closes; until then it lives here.

Fully-folded working records retire once their content has a durable home
(a spec here, published docs, or a tracked issue) — the retired files stay
git-recoverable. The beta.1 scope of record is
`specs/2026-07-12-beta.1-consolidation.md`.

Product documentation lives in the published `docs/` sections; the frozen record
of how the current system came to be lives in `design-history/`.
