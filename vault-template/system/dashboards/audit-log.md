# Audit log

Policy-gate write decisions, from `system/logs/audit.jsonl`. Open when a write didn't happen as expected, a worker looks off, or after an overnight run. Contract: [Policy gate](https://eranroseman.github.io/memoria-vault/reference/policy-mcp) · rationale: [dashboard rationale](https://eranroseman.github.io/memoria-vault/explanation/dashboards/operational-health/#audit-log).

## Recent denies and dry-runs

Writes the policy gate refused or downgraded. Anything here > 1 day without attention is an unhandled escalation.

```dataviewjs
if (!dv.container.dataset.poll) {
  dv.container.dataset.poll = '1';
  const id = setInterval(() => dv.component.load(), 30000);
  dv.component.register(() => clearInterval(id));
}
const text = await dv.io.load("system/logs/audit.jsonl");
if (!text || !text.trim()) { dv.paragraph("_No data yet._"); return; }
const events = text.trim().split("\n").filter(Boolean).map(l => JSON.parse(l));
const filtered = events
  .filter(e => e.decision === "deny" || e.decision === "dry_run")
  .sort((a, b) => b.timestamp.localeCompare(a.timestamp))
  .slice(0, 30);
dv.table(
  ["When", "Actor", "Action", "Path", "Decision", "Rule", "Request"],
  filtered.map(e => [e.timestamp, e.actor, e.action, e.path, e.decision, e.policy_rule, e.request_id ?? ""])
);
```

## Writes to review-gated zones

Should be near zero. Each row is a request-envelope promotion
(`allow_with_log` + `request_id`) or an attempted bypass (`deny` / `dry_run`).
A raw `allow` here is a smell — these zones degrade to `dry_run` by default.

```dataviewjs
if (!dv.container.dataset.poll) {
  dv.container.dataset.poll = '1';
  const id = setInterval(() => dv.component.load(), 30000);
  dv.component.register(() => clearInterval(id));
}
const text = await dv.io.load("system/logs/audit.jsonl");
if (!text || !text.trim()) { dv.paragraph("_No data yet._"); return; }
const events = text.trim().split("\n").filter(Boolean).map(l => JSON.parse(l));
const canonical = events
  .filter(e => e.path && (
    e.path.startsWith("knowledge/notes/") ||
    e.path.startsWith("knowledge/hubs/")
  ))
  .sort((a, b) => b.timestamp.localeCompare(a.timestamp))
  .slice(0, 20);
dv.table(
  ["When", "Actor", "Decision", "Path", "Request"],
  canonical.map(e => [e.timestamp, e.actor, e.decision, e.path, e.request_id ?? ""])
);
```

## Adapter activity (last 24h)

If optional adapters write through the policy shim, their `actor` field appears
here.

```dataviewjs
if (!dv.container.dataset.poll) {
  dv.container.dataset.poll = '1';
  const id = setInterval(() => dv.component.load(), 30000);
  dv.component.register(() => clearInterval(id));
}
const text = await dv.io.load("system/logs/audit.jsonl");
if (!text || !text.trim()) { dv.paragraph("_No data yet._"); return; }
const events = text.trim().split("\n").filter(Boolean).map(l => JSON.parse(l));
const cutoff = new Date(Date.now() - 24 * 60 * 60 * 1000).toISOString();
const recent = events.filter(e => e.timestamp >= cutoff);
const counts = {};
for (const e of recent) {
  const key = `${e.actor}|${e.action}|${e.decision}`;
  counts[key] = (counts[key] ?? 0) + 1;
}
const rows = Object.entries(counts)
  .map(([k, n]) => { const [actor, action, decision] = k.split("|"); return [actor, action, decision, n]; })
  .sort((a, b) => b[3] - a[3]);
dv.table(["Actor", "Action", "Decision", "Count (24h)"], rows);
```

## Hash drift (tamper detection)

A path's last recorded `after_hash` should match the file's current SHA-256. A mismatch means a write outside the audit trail (non-MCP tool or direct human edit) — investigate; it breaks reversibility. Cross-reference the Linter's drift report.

```dataviewjs
if (!dv.container.dataset.poll) {
  dv.container.dataset.poll = '1';
  const id = setInterval(() => dv.component.load(), 30000);
  dv.component.register(() => clearInterval(id));
}
const text = await dv.io.load("system/logs/audit.jsonl");
if (!text || !text.trim()) { dv.paragraph("_No data yet._"); return; }
const events = text.trim().split("\n").filter(Boolean).map(l => JSON.parse(l));
const lastWriteFor = {};
for (const e of events) {
  if (e.after_hash && e.decision === "write_complete") {
    lastWriteFor[e.path] = { ts: e.timestamp, hash: e.after_hash, actor: e.actor };
  }
}
// Drift detection requires a current-hash sidecar produced by the Linter's scheduled scan.
// This query surfaces the recorded last-write per path so the Linter's drift report can be cross-referenced.
const rows = Object.entries(lastWriteFor)
  .sort((a, b) => b[1].ts.localeCompare(a[1].ts))
  .slice(0, 30)
  .map(([path, info]) => [info.ts, info.actor, path, info.hash.slice(0, 16) + "…"]);
dv.table(["Last write", "Actor", "Path", "Recorded after_hash"], rows);
```

## Anomalies

Patterns the query flags — each is a configuration bug; see [Policy gate](https://eranroseman.github.io/memoria-vault/reference/policy-mcp) for why:

- Any allowed adapter write missing `before_hash`, or completion row missing `after_hash`.
- Any adapter write allowed under `.memoria/`.
- Any adapter write allowed under `system/`.

```dataviewjs
if (!dv.container.dataset.poll) {
  dv.container.dataset.poll = '1';
  const id = setInterval(() => dv.component.load(), 30000);
  dv.component.register(() => clearInterval(id));
}
const text = await dv.io.load("system/logs/audit.jsonl");
if (!text || !text.trim()) { dv.paragraph("_No data yet._"); return; }
const events = text.trim().split("\n").filter(Boolean).map(l => JSON.parse(l));
const isAllowed = (d) => d === "allow" || d === "allow_with_log";
const writeAction = (a) => a === "write" || a === "append";
const hiddenRuntime = (p) => /^\.memoria\//.test(p ?? "");
const systemPath = (p) => /^system\//.test(p ?? "");
const anomalies = events.filter(e =>
  (isAllowed(e.decision) && writeAction(e.action) && !e.before_hash) ||
  (e.decision === "write_complete" && !e.after_hash) ||
  (isAllowed(e.decision) && writeAction(e.action) && hiddenRuntime(e.path)) ||
  (isAllowed(e.decision) && writeAction(e.action) && systemPath(e.path))
);
dv.table(
  ["When", "Actor", "Action", "Path", "Decision", "Rule"],
  anomalies.map(e => [e.timestamp, e.actor, e.action, e.path, e.decision, e.policy_rule])
);
```

## Log size

`audit.jsonl` is append-only and unbounded; each view above caps its own row count, so the dashboard stays bounded as the log grows. Rotation (archiving older weeks to `system/logs/archive/`) is a deferred convention, not yet implemented.
