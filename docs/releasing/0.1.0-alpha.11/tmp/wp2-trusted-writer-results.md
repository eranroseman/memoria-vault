# WP2 Trusted Writer And Queue Slice Results

Timestamp: 2026-06-29T06:20:17Z

Scope: WP2 implementation slices for the alpha.11 write boundary:

- machine Concept writes stage under `.memoria/staging/<bundle>/...` and force
  `check_status: unchecked`;
- promotion validates against the Memoria schema/folder contract, writes the
  target bundle file with `check_status: checked`, and records a `check-fired`
  event;
- trace-integrity scans quarantine foreign/untraced bundle files found from git
  status or explicit paths under `.memoria/quarantine/...` through the worker
  `trace-integrity-scan` operation;
- trace state rebuilds from per-machine `journal/<machine>.jsonl` files;
- a two-clone git simulation proves sequential single-writer device commits
  converge by pull/push, keep separate per-machine journals, and rebuild trace
  state from both journals after merge;
- a second two-clone simulation proves simultaneous edits to the same Concept
  fail visibly: the stale device push is rejected, `git merge FETCH_HEAD`
  reports a conflict on the Concept file, and per-machine journals remain
  separate files rather than silently overwriting each other;
- `commit_writer_changes()` couples the selected bundle outputs and the
  per-machine journal into one git commit without sweeping unrelated staged
  files;
- `observe_pi_edit()` backfills direct PI edits as `actor: pi`, includes the
  prior HEAD hash in `inputs`, forces the edited Concept back to
  `check_status: unchecked`, and `mark_checked()` records the later live
  check-status transition through the checked `mark-checked` worker operation;
  `observe_pi_edit_from_head()` derives the prior HEAD hash and prior upstream
  inputs from git + journal; `observe_pi_edits_from_status()` scans bundle-root
  git status, observes tracked or new PI-authored Concept files, and commits
  `{Concept + journal}` without sweeping unrelated files;
- `.memoria/queue/{pending,running,done,failed}` is now part of the fresh
  skeleton and gitignored except for `.gitkeep`;
- `enqueue_trusted_write()` and `run_next_job()` provide the first local worker
  path: a queued machine write is claimed, staged, promoted, committed, and
  moved to `done`; invalid jobs fail closed without a bundle write;
- `enqueue_operation()` routes worker-owned operation jobs for evidence checks,
  quote-anchor checks, claim/quote checks, prompt-injection marker checks,
  provenance checkpoints, contradiction-link checks, structural link-target
  checks, trace-integrity quarantine scans, source and BibTeX capture,
  digest/hub construction, note candidate construction, deterministic gap
  analysis, checked qmd-source rebuild, deterministic answer-query reads,
  cascade rollback, disposable seeded-error verdict runs, PI-edit observation,
  generated index regeneration, and attention acknowledgement/resolution;
- the worker CLI now has a generic `enqueue-operation --operation-id ...`
  entrypoint with a JSON object payload, so manual/live alpha.11 smokes use the
  same queue contract as the plugin instead of bespoke scripts;
- worker-dispatched local network operations enforce the checked operation
  Concept's `allowed_network` before URL/Zotero Local API fetch helpers run; a
  narrowed `capture-url-source` policy fails closed before the HTTP helper is
  called.
- `write_workspace_indexes()` regenerates the root and bundle `index.md`
  projections from checked Concept files; `check_workspace_indexes()` gives the
  drift check, and the worker exposes this as `regenerate-indexes`;
- `write_tracked_projections()` provides the worker-owned generator for the
  tracked projection set (`index.md`, bundle indexes, `references.bib`, and
  `capabilities/ai-catalog.json`); `check_tracked_projections()` regenerates the
  set into a temp tree and reports missing/stale workspace copies; the worker
  exposes this as `regenerate-tracked-projections`;
- the daily `memoria-lint` cron now invokes the worker `integrity-sweep`, which
  enqueues and runs trace-integrity quarantine plus the scheduled
  source-metadata, evidence-resolution, quote-anchor, claim/quote,
  prompt-injection marker, provenance-checkpoint, contradiction-link, and
  structural link-target checks once per UTC day.
- the installer now wires a `memoria-worker` cron every minute; the shared
  cron runner observes PI edits and drains up to 10 pending worker jobs through
  the same CLI/queue path the Inspector uses.
- the live Hermes L2 smoke now matches the alpha.11 write boundary: a
  disposable `memoria-writer` profile attempts a direct Obsidian MCP write to
  `knowledge/notes/l2-smoke-direct-write.md`, the policy-gate plugin blocks it
  with `policy_rule: tool-registry.allowlist`, records the deny audit row, and
  leaves no artifact file behind.
- the legacy `archive_inbox.py` cron path is retired rather than grandfathered:
  `memoria-sweeps` no longer runs a deterministic direct write over `inbox/`,
  and the unused `inbox.archive_after_days` calibration block is gone.

This is not the full WP2 worker. Always-on live scheduler evidence and live
Obsidian Git conflict recovery remain open WP2 work; the installer packaging
and git-status dispatch hook are implemented. The 2026-06-29 start-blocker
verifier adds a disposable alpha.11-shaped queue proof: an `answer-query`
operation is enqueued, claimed, dispatched through the checked operation policy,
returns only checked Concepts, and lands in `.memoria/queue/done/`. That same
probe now runs after `scripts/refresh-test-vault.sh --profiles never`, confirms
`Memoria-test` has the alpha.11 queue/knowledge/capability-policy skeleton, and
drains one harmless live `answer-query` job into `.memoria/queue/done/`.
Commit hashes are returned by the worker result and verified by tests; embedding
the final git commit hash inside the same committed journal rows is
intentionally not implemented because the git commit hash covers the journal
content itself.

Verification:

```bash
python -m pytest tests/test_worker_queue.py tests/test_trusted_writer.py
python -m ruff check src/memoria_vault/runtime/worker.py src/memoria_vault/runtime/trusted_writer.py src/memoria_vault/runtime/__init__.py tests/test_worker_queue.py tests/test_trusted_writer.py
python -m ruff format --check src/memoria_vault/runtime/worker.py src/memoria_vault/runtime/trusted_writer.py src/memoria_vault/runtime/__init__.py tests/test_worker_queue.py tests/test_trusted_writer.py
python -m pytest tests/test_trusted_writer.py tests/test_worker_queue.py
python -m ruff check src/memoria_vault/runtime/trusted_writer.py src/memoria_vault/runtime/worker.py tests/test_trusted_writer.py tests/test_worker_queue.py
python -m ruff format --check src/memoria_vault/runtime/trusted_writer.py src/memoria_vault/runtime/worker.py tests/test_trusted_writer.py tests/test_worker_queue.py
python -m pytest tests/test_trusted_writer.py
python -m ruff check tests/test_trusted_writer.py
python -m ruff format --check tests/test_trusted_writer.py
python -m pytest tests/test_projections.py tests/test_worker_queue.py
python -m ruff check src/memoria_vault/runtime/projections.py src/memoria_vault/runtime/worker.py tests/test_projections.py tests/test_worker_queue.py
python -m ruff format --check src/memoria_vault/runtime/projections.py src/memoria_vault/runtime/worker.py tests/test_projections.py tests/test_worker_queue.py
python scripts/gen_reference_refs.py --write
python -m pytest tests/test_worker_queue.py tests/test_trusted_writer.py tests/test_runtime_helpers.py tests/test_package_spine.py tests/test_schemas.py tests/test_installer_skeleton.py tests/test_patterns.py tests/test_detectors.py
python -m pytest tests/test_worker_queue.py::test_worker_runs_capture_url_source_operation_jobs tests/test_worker_queue.py::test_worker_rejects_capture_url_source_outside_allowed_network tests/test_worker_queue.py::test_worker_runs_capture_zotero_source_operation_jobs tests/test_worker_queue.py::test_worker_runs_capture_zotero_source_from_local_api_key tests/test_operations.py -q
python scripts/docs_doctor.py docs
python scripts/agents_doctor.py
python scripts/status_doctor.py
bash -n scripts/install.sh scripts/install/manifest.sh
git diff --check
scripts/verify live --evidence-dir /tmp/memoria-alpha11-live-verify-2
scripts/verify runtime --evidence-dir /tmp/memoria-alpha11-runtime-verify
scripts/verify package --evidence-dir /tmp/memoria-alpha11-package-verify-archive-retire
```

Result: all passed.
