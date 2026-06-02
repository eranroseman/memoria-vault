# Contradictions

Claim pairs joined by a **human-set** `relations.contradicts` link (symmetric → each pair listed once). No model judges conflicts — sparse until you file links, and the emptiness is itself the signal. Diagnostic, never gating: a cluster of contradictions is usually where the interesting writing is. [Typed relations (ADR-08)](https://eranroseman.github.io/memoria-vault/reference/frontmatter) · [dashboard rationale](https://eranroseman.github.io/memoria-vault/explanation/dashboards/synthesis-agenda/contradictions).

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
