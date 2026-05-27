# `audit-log.md` — forensic trail for vault writes

**Location.** `00-meta/05-dashboards/audit-log.md`

**Decision.** Spot policy-MCP decisions that need attention: writes blocked at the tool layer, dry-run escalations awaiting human action, and writes to canonical zones. Open when something feels off — a worker behaving strangely, a board card stuck on an unclear reason, or after a scheduled overnight run completes.

The audit log lives at `00-meta/04-logs/audit.jsonl`, one JSON object per line. See [reference/policy-mcp.md](../reference/policy-mcp.md) for the format and decision protocol.

## Recent denies and dry-runs

The action queue: writes the policy MCP refused or downgraded. Anything sitting here for more than a day without a corresponding board card is an unhandled escalation.

```dataviewjs
const text = await dv.io.load("00-meta/04-logs/audit.jsonl");
const events = text.trim().split("\n").map(l => JSON.parse(l));
const filtered = events
  .filter(e => e.decision === "deny" || e.decision === "dry_run")
  .sort((a, b) => b.timestamp.localeCompare(a.timestamp))
  .slice(0, 30);
dv.table(
  ["When", "Profile", "Action", "Path", "Decision", "Rule", "Task"],
  filtered.map(e => [e.timestamp, e.profile, e.action, e.path, e.decision, e.policy_rule, e.task_id ?? ""])
);
```

## Writes to canonical zones

Should be near zero. Every entry here is either an approved promotion (`decision: allow_with_log` with a corresponding `task_id` — canonical-zone writes always require `flags.explicit_authorization`, which triggers `allow_with_log`) or an attempted bypass (`decision: deny` or `dry_run`). A raw `allow` to a canonical path is itself a smell, since canonical zones are supposed to degrade to `dry_run` by default.

```dataviewjs
const text = await dv.io.load("00-meta/04-logs/audit.jsonl");
const events = text.trim().split("\n").map(l => JSON.parse(l));
const canonical = events
  .filter(e => e.path && (
    e.path.startsWith("30-synthesis/01-permanent/") ||
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

Sanity check: is each profile writing where you expect? Any `memoria-socratic` write is a smell (Socratic is write-denied across the vault); any `memoria-cartographer` or `memoria-verifier` write outside its declared scratch path is a smell; a researcher with thousands of writes in an hour is a runaway.

```dataviewjs
const text = await dv.io.load("00-meta/04-logs/audit.jsonl");
const events = text.trim().split("\n").map(l => JSON.parse(l));
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

For each path, the last `after_hash` recorded in the audit log should match the file's current SHA-256. A mismatch means the file was modified outside the audit trail — either a non-MCP tool wrote to it or a human edited it directly. Both cases need investigation: undocumented writes break the reversibility guarantee.

```dataviewjs
const text = await dv.io.load("00-meta/04-logs/audit.jsonl");
const events = text.trim().split("\n").map(l => JSON.parse(l));
const lastWriteFor = {};
for (const e of events) {
  if (e.after_hash && (e.decision === "allow" || e.decision === "allow_with_log")) {
    lastWriteFor[e.path] = { ts: e.timestamp, hash: e.after_hash, profile: e.profile };
  }
}
// Drift detection requires a current-hash sidecar produced by the linter's scheduled scan.
// This query surfaces the recorded last-write per path so the linter's drift report can be cross-referenced.
const rows = Object.entries(lastWriteFor)
  .sort((a, b) => b[1].ts.localeCompare(a[1].ts))
  .slice(0, 30)
  .map(([path, info]) => [info.ts, info.profile, path, info.hash.slice(0, 16) + "…"]);
dv.table(["Last write", "Profile", "Path", "Recorded after_hash"], rows);
```

## Anomalies

Specific patterns worth alerting on. Add rows here as you discover new failure modes — the dashboard is the diary of how the system actually misbehaves.

- **Linter `auto_fix` allowed outside the gated classes.** Should be impossible: the policy MCP requires `flags.class ∈ {"safe-and-unambiguous", "authorized-targeted"}`. An entry here means the policy rule drifted from [profiles/linter.md](../profiles/linter.md#auto-fix-policy).
- **Socratic with any allowed write.** Socratic's lane policy is `policy.allow.write: []` — the hard wall. Any `decision: allow` or `allow_with_log` for `profile: memoria-socratic` is a configuration bug (the lane-override file has been tampered with or replaced).
- **Cartographer or Verifier with allowed writes outside their declared scratch paths.** Both are `read_only_mode` for the vault and only write to specific project-scratch paths. Any `allow` outside `40-workbench/01-projects/*/corpus-map.md` (Cartographer) or `40-workbench/01-projects/*/verification/*` (Verifier) is a configuration bug.
- **Researcher writing to `30-synthesis/**` with `decision: allow` or `allow_with_log`.** Researchers do not promote to synthesis. Any allowed write here means the lane override is too permissive.
- **Write recorded with missing hashes.** Every `allow` or `allow_with_log` write must carry both `before_hash` and `after_hash`. Missing hashes break tamper detection.

```dataviewjs
const text = await dv.io.load("00-meta/04-logs/audit.jsonl");
const events = text.trim().split("\n").map(l => JSON.parse(l));
const isAllowed = (d) => d === "allow" || d === "allow_with_log";
const writeAction = (a) => a === "write" || a === "append";
const cartographerScratch = (p) => /^40-workbench\/01-projects\/[^/]+\/(corpus-map\.md|gap-report\.md|comparative-briefs\/|cluster-maps\/)/.test(p ?? "");
const verifierScratch = (p) => /^40-workbench\/01-projects\/[^/]+\/verification\//.test(p ?? "");
const anomalies = events.filter(e =>
  (e.profile === "memoria-linter" && e.action === "auto_fix" && isAllowed(e.decision) &&
    !["safe-and-unambiguous", "authorized-targeted"].some(c => (e.policy_rule ?? "").includes(c))) ||
  (e.profile === "memoria-socratic" && writeAction(e.action) && isAllowed(e.decision)) ||
  (e.profile === "memoria-cartographer" && writeAction(e.action) && isAllowed(e.decision) && !cartographerScratch(e.path)) ||
  (e.profile === "memoria-verifier" && writeAction(e.action) && isAllowed(e.decision) && !verifierScratch(e.path)) ||
  (e.profile === "memoria-researcher" && (e.path ?? "").startsWith("30-synthesis/") && isAllowed(e.decision)) ||
  (isAllowed(e.decision) && writeAction(e.action) && (!e.before_hash || !e.after_hash))
);
dv.table(
  ["When", "Profile", "Action", "Path", "Decision", "Rule"],
  anomalies.map(e => [e.timestamp, e.profile, e.action, e.path, e.decision, e.policy_rule])
);
```

## Rotation

`audit.jsonl` is append-only and grows without bound. Rotate weekly: rename the current file to `00-meta/04-logs/archive/audit-YYYY-WW.jsonl` and start a fresh one. The dashboard reads only the current week's file; archived files remain greppable from the shell. Rotation is the linter's responsibility — see [profiles/linter.md](../profiles/linter.md).
