# Alpha.11 pre-approval test results

Date: 2026-06-29

Verdict: **PARTIAL**.

| Gate | Status | Evidence | Recommendation |
| --- | --- | --- | --- |
| Operation-policy enforcement spike | pass | cases={'valid_read': True, 'valid_staging_write': True, 'direct_knowledge_write_denied': True, 'bad_tool_denied': True, 'network_denied': True, 'invalid_policy_fail_closed': True}; audit_rows=6 | Approve start only if implementation keeps these as enforced worker decisions, not prose. |
| Read-barrier / check_status spike | pass | good_promoted=True; bad_quarantined=True; visible=['knowledge/notes/good']; unknown_missing_unchecked_hidden=True; foreign_quarantined=True | Approve start only if every consumer filters on checked + traced, fail-closed. |
| Plugin boundary spike | partial | control_panel_surface_clean=True; worker_calls=5; platform_hard_sandbox=False | Treat as a design warning: the control-panel API is viable, but Obsidian plugin JavaScript is trusted code. Approval needs either a static/provenance guardrail accepted as the mechanism or a different sandboxed UI boundary. |
| Legacy mapping spike (superseded) | superseded-scope | inputs=14; dispositions=['mapped', 'projection-or-worker-state', 'split']; report=/tmp/memoria-alpha11-preapproval/legacy-mapping/legacy-mapping-report.json | No alpha.11 migrator is needed because no non-sandbox install exists; keep this only as historical spike evidence. |
| Seeded-error harness definition | pass | cases=8; classes=['blind-grounding', 'blind-security', 'read-barrier', 'rollback', 'structural', 'temporal', 'trace']; harness=/tmp/memoria-alpha11-preapproval/seeded-error/seeded-error-harness.json | Approve start; final seeded-error verdict remains the gate before non-sandbox use. |

## Interpretation

- These are disposable pre-implementation spikes, not alpha.11 implementation tests.
- The plugin boundary is partial because ordinary Obsidian plugin JavaScript is trusted code;
  the spike proves a narrow control-panel surface, not a platform sandbox.
- The legacy mapping spike is superseded: alpha.11 initializes a fresh sandbox and
  does not ship migration, upgrade, or backwards-compatibility work.
- The final seeded-error verdict is intentionally deferred until alpha.11 exists; this run
  verifies the harness definition and bar shape only.
