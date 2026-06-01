# Dashboard performance checklist

Discipline for keeping dashboards responsive as the vault grows. Companion to [Dashboards — explanation](https://eranroseman.github.io/memoria-vault/explanation/dashboards/).

## Before writing a new dashboard query

- [ ] **Scope with `FROM "folder"`** (narrow), never `FROM ""` (vault-wide)
- [ ] **Verify the field type is stable** across the queried notes — mixed string/list breaks sort/filter unpredictably
- [ ] **Add a `LIMIT 30`** (or similar) cap; dashboards rarely need more
- [ ] **Sort intentionally** — `oldest first` for maintenance queues, `newest first` for activity views
- [ ] **Prefer `TABLE` or `LIST`** over `dataviewjs` for plain frontmatter views

## When a dashboard feels slow

- [ ] Open the dashboard with the file explorer collapsed (isolates render cost)
- [ ] Time the original query vs a more-folder-scoped version
- [ ] If the scoped version is twice as fast, narrow the `FROM` in the original
- [ ] Look for vault-wide queries (`FROM ""`) you may not have noticed
- [ ] Check whether you're doing string parsing in `WHERE` — push it to a frontmatter field instead

## When dashboards stay slow despite tightening

- [ ] Run the Linter's stale-enrichment / orphan checks — vaults with many half-populated notes are slower
- [ ] Split one dashboard with 10+ queries into two specialized dashboards
- [ ] Disable Dataview features you don't use (Settings → Dataview)
- [ ] Consider whether a `dataviewjs` block is actually doing what a `TABLE` could do simpler

## Graceful degradation

A query that returns zero rows because **the data doesn't exist yet** is correct behavior. A query that returns zero rows because **the field has never existed anywhere** is a broken query masquerading as an empty queue. Every dashboard should distinguish them:

- **Empty result + explanation beats error.** Pair every query with a one-line markdown note explaining what would populate it.
- **`dataviewjs` should guard explicit reads.** Queries that load external files must handle the missing-file case and render a placeholder, not throw a stack trace.
- **Surface dependencies at the top.** Each dashboard's intro should name the decisions, files, or aggregators it depends on.

## Frontmatter discipline that helps performance

- **Keep frontmatter compact.** Long prose belongs in the body, not in fields you query.
- **Use consistent types.** If `lifecycle` is sometimes a string and sometimes a list, every query that touches it slows down.
- **Promote stable fields to top-level.** `enriched_date` lives at top-level (not inside `_enrichment`) precisely because dashboards query it.

---

**For depth:** [Dashboards — explanation](https://eranroseman.github.io/memoria-vault/explanation/dashboards/) — full performance discipline and graceful-degradation guidance.
