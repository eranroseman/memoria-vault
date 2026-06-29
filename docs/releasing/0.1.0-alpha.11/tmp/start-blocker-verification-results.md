# Alpha.11 start-blocker verification results

Date: 2026-06-29

Verdict: **PASS**.

| Claim | Status | Evidence |
| --- | --- | --- |
| qmd disposable bundle index/search | pass | fixture=/tmp/memoria-alpha11-start-blockers/qmd-bundle; init/update/search rc=0; found_stability=True |
| Zotero Local API item shape | pass | port_open=True; item_status=200; item_shape=True; annotation_import_in_scope=False; errors=none |
| PDF quote/page/span/bbox preservation | pass | fixture=/tmp/memoria-alpha11-start-blockers/pdf-span; fitz=True; content_has_page=True; quote_found=True; page=1; bbox=[72.0, 60.17, 294.55, 75.29] |
| Memoria Inspector control-panel deployment | partial-live-command | enabled=True; version=0.1.0-alpha.11; file_parity=True; control_markers=True; forbidden_absent=True; localhost_27124_open=True; rest_manifest_read=True; rest_command_registered=True; rest_command_executed=True; rest_command_id=memoria-inspector:open-memoria-inspector; workspace_view_present=True; live_visual_render_tested=False; port_note=open |
| worker queue operation dispatch | pass | fixture=/tmp/memoria-alpha11-start-blockers/worker-dispatch; queued_status=pending; done_status=done; engine=bm25; sources=['knowledge/notes/checked.md']; checked_only=True; done_file=True; memoria_test_ready={'queue_root': True, 'knowledge_root': True, 'capability_policies': True, 'answer_query_policy_checked': True, 'policy_error': 'none'}; memoria_test_dispatch={'attempted': True, 'job_id': 'start-blocker-live-answer-query-20260629T142010', 'queued_status': 'pending', 'done_status': 'done', 'done_file': True} |
| source_id stability across citekey changes | pass | fixture=/tmp/memoria-alpha11-start-blockers/source-id; before_path=catalog/sources/src-alpha11-0001/source.md; after_path=catalog/sources/src-alpha11-0001/source.md; path_stable=True; citekey_changed=True; refs_still_resolve=True |

## Interpretation

- `qmd` and `source_id` are verified with disposable local fixtures.
- Zotero item import and Obsidian are live-app checks; if their local services are unreachable,
  the result is blocked rather than simulated.
- PDF span preservation runs a tiny parser-backed capture when `fitz` is
  installed; otherwise it reports a prerequisite failure instead of simulating
  parser fidelity.
- The Memoria Inspector check proves the `Memoria-test` plugin files match the
  alpha.11 template, retain the enqueue-only control-panel markers, avoid direct
  vault/network/shell APIs, and, when Local REST is reachable, execute the live
  Inspector command and check the workspace state for the Inspector view type.
- The worker queue check proves a disposable alpha.11-shaped vault can enqueue
  and drain an `answer-query` operation through the checked operation policy,
  returning only checked Concepts. After refreshing the disposable
  `Memoria-test` sandbox from the alpha.11 template, it also enqueues and drains
  one harmless live `answer-query` job into `.memoria/queue/done/`.

## Evidence status notes

- This report is a point-in-time local probe. `blocked-live` caused by sandboxed
  socket access means this run could not reach the live app, not that prior live
  evidence is invalid.
- Newer disposable smoke results supersede older "not implemented locally" rows
  only as feasibility evidence. They do not prove production implementation or
  close gates that still require visual Obsidian activation or attended Co-PI
  use. Zotero is in scope only as an item/source import path for alpha.11;
  Zotero annotation import is not an alpha.11 capability or release gate.
