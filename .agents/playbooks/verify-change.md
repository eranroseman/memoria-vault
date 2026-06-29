# Verify a change

Verification demonstrates the requested behavior rather than merely showing
that code compiles.

## 1. State the claim

Write one observable claim for each requested outcome:

```text
Given <starting state>, when <action occurs>, then <observable result> follows.
```

Include failure behavior and important unchanged behavior where relevant.

## 2. Choose evidence

Use the lowest-cost evidence that proves the claim:

1. Focused unit or component test.
2. Direct command or CLI reproduction.
3. Source Gate: `scripts/verify pr`.
4. Package Gate: `scripts/verify package`.
5. Runtime Gate: `scripts/verify runtime`.
6. Release-candidate prefix: `scripts/verify rc`.
7. Product, manual GUI, or failure/recovery evidence in the release issue.

Do not test installers against the real `~/Memoria`. Do not claim live-runtime
verification when only static or synthetic tests ran.

## 3. Gate meanings

| Gate | Proves | Use when |
|---|---|---|
| Source | Repo contracts, docs, schemas, Python tests, and static checks are coherent. | Any PR broader than a tiny prose edit. |
| Package | A disposable vault assembles and the model-free workflow replay works. | Shipped vault, installer skeleton, hooks, plugins, or workflow replay changed. |
| Runtime | Hermes, MCP, Obsidian bridge, model endpoint, cron, and policy boundaries work live. | Runtime wiring or release-candidate confidence depends on live services. |
| Product | Research workflows produce reviewable value, telemetry, GUI/Bases/dashboard evidence, and quality evidence when claimed. | Release candidates or product-surface changes. |
| Failure/recovery | Denied writes leave no file, MCP-down fails closed, retries recover, dry-run is clean, and installer re-run is idempotent. | Policy, ingest, MCP, installer, cron, or replay changed. |

Manual GUI checks cover bundled plugins, Local REST API, dashboards, spaces,
Bases, Zotero/BBT, Agent Client, deny visibility, and board visibility. Record
manual evidence in the relevant release parent issue or sub-issue, not in docs.

## 4. Execute

- Start with the narrow regression test.
- Run related tests for the affected component.
- Use `scripts/verify pr` for shared behavior or before PR handoff.
- Compare actual output and side effects with the stated claim.
- Inspect logs, generated files, audit entries, or diffs when those are part of
  the contract.
- Clean up only artifacts created by this verification run.

## 5. Record

Report:

- Claims verified
- Commands or interactions performed
- Relevant results
- Tests not run and the concrete reason
- Residual risk that needs a live runtime, Windows, Obsidian, network access, or
  another unavailable dependency

“Tests pass” is supporting evidence, not the entire verification report.
