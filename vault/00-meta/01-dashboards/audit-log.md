# Audit log

Policy-MCP write decisions, from `00-meta/02-logs/audit.jsonl`. Open when a write didn't happen as expected, a worker looks off, or after an overnight run. Permissions: [[../04-reference/profile-policies|profile-policies]] · design: [policy MCP](https://eranroseman.github.io/memoria-vault/reference/policy-mcp/), [dashboard rationale](https://eranroseman.github.io/memoria-vault/explanation/dashboards/operational-health/audit-log/).

## Recent denies and dry-runs

Writes the policy MCP refused or downgraded. Anything here > 1 day without a board card is an unhandled escalation.

```dataviewjs
const text = await dv.io.load("00-meta/02-logs/audit.jsonl");
if (!text || !text.trim()) { dv.paragraph("_No data yet._"); return; }
const events = text.trim().split("\n").filter(Boolean).map(l => JSON.parse(l));
const filtered = events
  .filter(e => e.decision === "deny" || e.decision === "dry_run")
  .sort((a, b) => b.timestamp.localeCompare(a.timestamp))
  .slice(0, 30);
dv.table(
  ["When", "Profile", "Action", "Path", "Decision", "Rule", "Task"],
  filtered.map(e => [e.timestamp, e.profile, e.action, e.path, e.decision, e.policy_rule, e.task_id ?? ""])
);
```

## Writes to review-gated zones

Should be near zero. Each row is an approved promotion (`allow_with_log` + `task_id`) or an attempted bypass (`deny` / `dry_run`). A raw `allow` here is a smell — these zones degrade to `dry_run` by default.

```dataviewjs
const text = await dv.io.load("00-meta/02-logs/audit.jsonl");
if (!text || !text.trim()) { dv.paragraph("_No data yet._"); return; }
const events = text.trim().split("\n").filter(Boolean).map(l => JSON.parse(l));
const canonical = events
  .filter(e => e.path && (
    e.path.startsWith("30-synthesis/01-claims/") ||
    e.path.startsWith("30-synthesis/03-moc/") ||
    e.path.startsWith("50-deliverables/")
  ))
  .sort((a, b) => b.timestamp.localeCompare(a.timestamp))
  .slice(0, 20);
dv.table(
  ["When", "Profile", "Decision", "Path", "Task"],
  canonical.map(e => [e.timestamp, e.profile, e.decision, e.path, e.task_id ?? ""])
);
```

## Per-profile activity (last 24h)

Is each profile writing where expected? Smells: any `memoria-socratic` write (write-denied), any `memoria-mapper`/`memoria-verifier` write outside its scratch path, a Librarian writing thousands/hour.

```dataviewjs
const text = await dv.io.load("00-meta/02-logs/audit.jsonl");
if (!text || !text.trim()) { dv.paragraph("_No data yet._"); return; }
const events = text.trim().split("\n").filter(Boolean).map(l => JSON.parse(l));
const cutoff = new Date(Date.now() - 24 * 60 * 60 * 1000).toISOString();
const recent = events.filter(e => e.timestamp >= cutoff);
const counts = {};
for (const e of recent) {
  const key = `${e.profile}|${e.action}|${e.decision}`;
  counts[key] = (counts[key] ?? 0) + 1;
}
const rows = Object.entries(counts)
  .map(([k, n]) => { const [profile, action, decision] = k.split("|"); return [profile, action, decision, n]; })
  .sort((a, b) => b[3] - a[3]);
dv.table(["Profile", "Action", "Decision", "Count (24h)"], rows);
```

## Hash drift (tamper detection)

A path's last recorded `after_hash` should match the file's current SHA-256. A mismatch means a write outside the audit trail (non-MCP tool or direct human edit) — investigate; it breaks reversibility. Cross-reference the Linter's drift report.

```dataviewjs
const text = await dv.io.load("00-meta/02-logs/audit.jsonl");
if (!text || !text.trim()) { dv.paragraph("_No data yet._"); return; }
const events = text.trim().split("\n").filter(Boolean).map(l => JSON.parse(l));
const lastWriteFor = {};
for (const e of events) {
  if (e.after_hash && (e.decision === "allow" || e.decision === "allow_with_log")) {
    lastWriteFor[e.path] = { ts: e.timestamp, hash: e.after_hash, profile: e.profile };
  }
}
// Drift detection requires a current-hash sidecar produced by the Linter's scheduled scan.
// This query surfaces the recorded last-write per path so the Linter's drift report can be cross-referenced.
const rows = Object.entries(lastWriteFor)
  .sort((a, b) => b[1].ts.localeCompare(a[1].ts))
  .slice(0, 30)
  .map(([path, info]) => [info.ts, info.profile, path, info.hash.slice(0, 16) + "…"]);
dv.table(["Last write", "Profile", "Path", "Recorded after_hash"], rows);
```

## Anomalies

Patterns the query flags — each is a configuration bug; see [policy MCP](https://eranroseman.github.io/memoria-vault/reference/policy-mcp/) for why:

- Linter `auto_fix` outside the gated classes (`safe-and-unambiguous` / `authorized-targeted`).
- Socratic with any allowed write (lane is `write: []`).
- Mapper/Verifier allowed write outside its declared scratch path.
- Librarian `allow`/`allow_with_log` to `30-synthesis/**`.
- Any allowed write missing `before_hash` / `after_hash`.

```dataviewjs
const text = await dv.io.load("00-meta/02-logs/audit.jsonl");
if (!text || !text.trim()) { dv.paragraph("_No data yet._"); return; }
const events = text.trim().split("\n").filter(Boolean).map(l => JSON.parse(l));
const isAllowed = (d) => d === "allow" || d === "allow_with_log";
const writeAction = (a) => a === "write" || a === "append";
const mapperScratch = (p) => /^40-workbench\/[^/]+\/01-map\/(corpus-map\.md|gap-report\.md|cluster-maps\/)/.test(p ?? "");
const verifierScratch = (p) => /^40-workbench\/[^/]+\/05-verification\//.test(p ?? "") || /^10-inbox\/03-candidates\//.test(p ?? "");
const anomalies = events.filter(e =>
  (e.profile === "memoria-linter" && e.action === "auto_fix" && isAllowed(e.decision) &&
    !["safe-and-unambiguous", "authorized-targeted"].some(c => (e.policy_rule ?? "").includes(c))) ||
  (e.profile === "memoria-socratic" && writeAction(e.action) && isAllowed(e.decision)) ||
  (e.profile === "memoria-mapper" && writeAction(e.action) && isAllowed(e.decision) && !mapperScratch(e.path)) ||
  (e.profile === "memoria-verifier" && writeAction(e.action) && isAllowed(e.decision) && !verifierScratch(e.path)) ||
  (e.profile === "memoria-librarian" && (e.path ?? "").startsWith("30-synthesis/") && isAllowed(e.decision)) ||
  (isAllowed(e.decision) && writeAction(e.action) && (!e.before_hash || !e.after_hash))
);
dv.table(
  ["When", "Profile", "Action", "Path", "Decision", "Rule"],
  anomalies.map(e => [e.timestamp, e.profile, e.action, e.path, e.decision, e.policy_rule])
);
```

## Rotation

`audit.jsonl` is append-only; the Linter rotates it weekly to `00-meta/02-logs/archive/audit-YYYY-WW.jsonl`. The dashboard reads the current week only; archives stay greppable.
