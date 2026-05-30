# `contradictions.md` — claim-tension surfacer

**Location.** `00-meta/01-dashboards/contradictions.md`

**Decision.** Surface claim notes that disagree with each other as a synthesis starting point (ADR-16). Reads the **human-set** `relations.contradicts` link (ADR-9) from claim notes and lists each conflicting pair **once** — `contradicts` is symmetric, so a pair typed on either side (or both) collapses to a single row. Pure consumer: no model judges which claims conflict (the deterministic-rollup discipline every dashboard follows; the NLI candidate-proposer is deferred future work). Diagnostic, never gating — a cluster of contradictions is usually where the interesting writing is. Sparse by design until you file `contradicts` links; the emptiness is itself the signal.

## Conflicting claims

```dataviewjs
const claims = dv.pages('"30-synthesis/01-claims"')
  .where(p => p.type === "claim-note" && p.relations && p.relations.contradicts);

const seen = new Set();
const rows = [];
for (const p of claims) {
  const raw = p.relations.contradicts;
  const targets = Array.isArray(raw) ? raw : [raw];
  for (const t of targets) {
    if (!t) continue;
    const tKey = t.path ?? String(t);
    const key = [p.file.path, tKey].sort().join(" ⇔ ");   // symmetric → canonical pair key
    if (seen.has(key)) continue;
    seen.add(key);
    rows.push([p.file.link, t]);
  }
}

if (rows.length === 0) {
  dv.paragraph("**No `relations.contradicts` links yet.** This is expected early — and the emptiness is the signal that tells you whether the deferred NLI proposer is worth building. File a `contradicts` link in a claim note's `relations:` block (ADR-9) and conflicting pairs appear here. This view reads only human-set links; it never infers tensions, and a `contradicts` edge marks a disagreement to resolve, not an error to clear.");
} else {
  rows.sort((a, b) => (a[0].path ?? "").localeCompare(b[0].path ?? ""));
  dv.table(["Claim", "Conflicts with"], rows);
}
```
