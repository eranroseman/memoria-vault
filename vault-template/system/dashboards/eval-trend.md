---
type: dashboard
title: Eval trend
---

# Eval trend

vault-eval capability scores over time, from `system/metrics/eval/runs.jsonl` — written by the deterministic scorer (`memoria_vault.runtime.subsystems.telemetry.eval.eval_score`, ADR-11). Open after the quarterly run scores (or an on-demand scoring pass) to see whether the deployed system still finds, extracts, links, and verifies correctly on this vault. The verdict is **diagnostic, never gating** — a dip informs you; it does not pause scheduled work. Reference: [vault eval](https://eranroseman.github.io/memoria-vault/reference/vault-eval) · rationale: [dashboard rationale](https://eranroseman.github.io/memoria-vault/explanation/dashboards/operational-health/#eval-trend).

Metrics (each 0–1, higher is better; a task is **unscored** when its card reported no machine-readable result — never faked):

- **recall@k** — the gold citekeys found in the top-k retrieved results.
- **support-rate** — cited evidence resolving to real catalog records.
- **FAMA-clean** — no superseded/archived claim was reused (the FAMA failure mode, ADR-129).

## Trend (newest score per quarter)

```dataviewjs
if (!dv.container.dataset.poll) {
  dv.container.dataset.poll = '1';
  const id = setInterval(() => dv.component.load(), 30000);
  dv.component.register(() => clearInterval(id));
}
const text = await dv.io.load("system/metrics/eval/runs.jsonl");
if (!text || !text.trim()) { dv.paragraph("_No data yet — no eval run has been scored._"); return; }
const runs = text.trim().split("\n").filter(Boolean).map(l => JSON.parse(l));
const byQuarter = {};
for (const r of runs) byQuarter[r.quarter] = r;   // later lines supersede (append-only log)
const fmt = (m) => m ? `${m.mean.toFixed(2)} (n=${m.n})` : "—";
const rows = Object.values(byQuarter)
  .sort((a, b) => b.quarter.localeCompare(a.quarter))
  .map(r => [r.quarter, r.timestamp, fmt(r.aggregate.recall_at_k),
             fmt(r.aggregate.support_rate), fmt(r.aggregate.fama_clean),
             `${r.aggregate.tasks_scored}/${r.aggregate.tasks_total}`,
             r.aggregate.tasks_unscored]);
dv.table(["Quarter", "Scored at", "Recall@k", "Support-rate", "FAMA-clean", "Scored/total", "Unscored"], rows);
```

## Latest run — per task

```dataviewjs
if (!dv.container.dataset.poll) {
  dv.container.dataset.poll = '1';
  const id = setInterval(() => dv.component.load(), 30000);
  dv.component.register(() => clearInterval(id));
}
const text = await dv.io.load("system/metrics/eval/runs.jsonl");
if (!text || !text.trim()) { dv.paragraph("_No data yet._"); return; }
const runs = text.trim().split("\n").filter(Boolean).map(l => JSON.parse(l));
const latest = runs[runs.length - 1];
const num = (v) => (v === undefined || v === null) ? "—" : (typeof v === "number" ? v.toFixed(2) : String(v));
dv.paragraph(`**${latest.quarter}** · scored ${latest.timestamp} · k=${latest.k}`);
dv.table(
  ["Task", "Workflow", "Eval role", "Status", "Recall@k", "Support-rate", "FAMA-clean", "Self-score"],
  latest.tasks.map(t => [t.task, t.workflow, t.eval_role, t.status,
                         num(t.metrics?.recall_at_k), num(t.metrics?.support_rate),
                         num(t.metrics?.fama_clean), num(t.self_score)])
);
const exposed = latest.tasks.filter(t => t.metrics?.fama_exposed?.length);
if (exposed.length) {
  dv.paragraph("**FAMA exposure** — superseded claims reused:");
  dv.list(exposed.map(t => `${t.task}: ${t.metrics.fama_exposed.join(", ")}`));
}
```

## Unscored tasks (latest run)

A task lands here when its eval report carried no machine-readable result block for the quarter — the run is honest about what it could not score. Re-run the task (or fix the report) and score again: `python -m memoria_vault.runtime.subsystems.telemetry.eval.eval_score --vault <vault> --quarter <quarter> --from-json results.json`.

```dataviewjs
if (!dv.container.dataset.poll) {
  dv.container.dataset.poll = '1';
  const id = setInterval(() => dv.component.load(), 30000);
  dv.component.register(() => clearInterval(id));
}
const text = await dv.io.load("system/metrics/eval/runs.jsonl");
if (!text || !text.trim()) { dv.paragraph("_No data yet._"); return; }
const runs = text.trim().split("\n").filter(Boolean).map(l => JSON.parse(l));
const latest = runs[runs.length - 1];
const missing = latest.tasks.filter(t => t.status === "unscored");
if (!missing.length) { dv.paragraph("_None — every gold task reported a result._"); return; }
dv.table(["Task", "Workflow", "Eval role"], missing.map(t => [t.task, t.workflow, t.eval_role]));
```

## Related

- `system/metrics/` — structural health and gold-set rot evidence live with exported metrics.
