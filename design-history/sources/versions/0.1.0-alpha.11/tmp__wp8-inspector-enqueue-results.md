# WP8 Inspector Enqueue Slice Results

Timestamp: 2026-06-29T06:28:10Z

Scope: first WP8 implementation slice for the Obsidian control panel:

- the Memoria Inspector plugin gained a Control panel action that enqueues
  `integrity-evidence-check` operation jobs under `.memoria/queue/pending/`;
- the Control panel can also enqueue `integrity-claim-quote-check` jobs for the
  high-precision unwarranted-claim check;
- the Control panel can enqueue `integrity-link-target-check` jobs for the
  structural link-target check;
- the Control panel can enqueue `integrity-quote-anchor-check` and
  `check-source-metadata` jobs for quote-span and source metadata checks;
- the Control panel can enqueue `integrity-provenance-checkpoint` jobs for the
  deterministic fresh/uncorroborated source attention checkpoint;
- the Control panel can enqueue the unified projection refresh job
  `regenerate-tracked-projections`; the plugin still writes only queue jobs,
  while the worker owns projection writes;
- the Control panel can enqueue the checked-only qmd source rebuild job
  `rebuild-checked-qmd-source`;
- the Control panel can enqueue deterministic `answer-query` jobs from a
  PI-entered query; this is still a queued Ask/Query job, not a chat surface;
- the Control panel can enqueue `capture-url-source` jobs from a PI-entered URL;
- the Control panel can enqueue `record-copi-interview` jobs that journal a
  PI-entered source takeaway for later digest synthesis; attended Co-PI use
  still needs live runtime evidence;
- the Control panel can enqueue `compile-source-digest` jobs for a PI-entered
  source id and comma-separated hub topics;
- the Control panel can enqueue `propose-note-candidates` jobs for a PI-entered
  digest path and supplied candidate JSON array;
- the Control panel can enqueue `curate-note-candidate` jobs that record a
  PI-entered accept/reject disposition for one checked candidate note;
- the Control panel can enqueue `curate-note-link` jobs that record PI-entered
  `supports`, `contradicts`, or `extends` links between checked Concepts;
- the Control panel can enqueue the deterministic `analyze-gaps` job for
  re-running gap analysis from the checked graph;
- the Control panel can enqueue `analyze-project-argument` jobs for a PI-entered
  project path;
- the Control panel can enqueue `render-project-argument-canvas` jobs for a
  PI-entered project path; the worker renders the checked-note argument graph as
  `knowledge/projects/<project>/argument.canvas` and commits it with a journal
  row;
- the Inspector now includes a read-only Worker queue panel with
  pending/running/failed counts and recent failed-job detail from
  `.memoria/queue/`;
- the Memoria Inspector plugin also gained a trace rollback control that enqueues
  `cascade-rollback` operation jobs for PI-entered trace targets;
- the Inspector now reads recent failed `check-fired` rows from `journal/*.jsonl`
  into an integrity flags panel;
- the Inspector now includes a read-only Knowledge graph panel over checked
  `catalog/` and `knowledge/` Concepts, with counts, declared-edge count, recent
  node links, and an Open button for `knowledge/views/knowledge.base`;
- the Knowledge graph panel now also previews declared graph edges from checked
  Concepts and opens normalized edge targets, including source bundle references
  that omit `/source.md`;
- the plugin gained Acknowledge and Resolve controls that enqueue
  `acknowledge-attention` and `resolve-attention` jobs; the worker records those
  decisions as committed journal `resolved` rows;
- the runtime worker gained `enqueue_operation()` and executes the
  `integrity-evidence-check` job by calling `check_evidence_integrity()` and the
  `integrity-claim-quote-check` job by calling `check_claim_quote_support()`,
  the `integrity-link-target-check` job by calling `check_link_targets()`, plus
  the `cascade-rollback` job by calling `cascade_rollback()`;
- ADR-121 supersedes ADR-84's read-only-only Inspector boundary with an
  enqueue-only mutation boundary;
- plugin provenance hashes were updated for the changed Inspector files and
  previously changed QuickAdd/Commander/Modal Forms config.
- `tests/test_memoria_inspector.py` now executes the real Inspector plugin in a
  Node mock of Obsidian, opens the view, fills all current control-panel inputs,
  clicks every enqueue handler, and proves the plugin writes pending queue jobs
  for integrity checks, projection refresh, checked-qmd rebuild, gap analysis,
  project argument/canvas analysis, Ask, URL capture, Co-PI interview, digest
  compilation, note proposal/accept/reject, typed note linking, cascade
  rollback, and attention acknowledgement/resolution with the expected payload
  shape and `source: memoria-inspector`.

This is not the full WP8 runtime proof. Earlier 2026-06-29 Local REST smoke
evidence proved Obsidian command execution with the temporary smoke pane. The
current start-blocker verifier now checks the shipped `memoria-inspector`
deployment in refreshed `Memoria-test`: the plugin files match the alpha.11
template, expose the enqueue-only control-panel markers, avoid direct
vault/network/shell APIs, the Local REST command executes with HTTP 204, and
`.obsidian/workspace.json` contains `memoria-inspector-view`. The verifier also
proves a disposable alpha.11-shaped vault can enqueue and drain an
`answer-query` operation through the checked operation policy, returning only
checked Concepts, then enqueues and drains one harmless live `answer-query` job
in `Memoria-test` into `.memoria/queue/done/`. Screenshot/human visual rendering
and attended Co-PI use remain open WP8 work. Direct note editing is
intentionally not a plugin feature: PI edits happen in Obsidian and are
observed/backfilled by the worker path tracked in WP2/WP6.

Verification:

```bash
python -m pytest tests/test_worker_queue.py tests/test_memoria_inspector.py
python -m pytest tests/test_memoria_inspector.py -q
python -m ruff check src/memoria_vault/runtime/worker.py tests/test_worker_queue.py tests/test_memoria_inspector.py
python -m ruff check tests/test_memoria_inspector.py
python -m ruff format --check src/memoria_vault/runtime/worker.py tests/test_worker_queue.py tests/test_memoria_inspector.py
python -m ruff format --check tests/test_memoria_inspector.py
python -m pytest tests/test_memoria_inspector.py tests/test_plugin_provenance.py
python scripts/plugin_provenance_doctor.py
python -m pytest tests/test_plugin_provenance.py tests/test_memoria_inspector.py tests/test_worker_queue.py
python -m pytest tests/test_worker_queue.py tests/test_memoria_inspector.py tests/test_plugin_provenance.py tests/test_seeded_errors.py tests/test_integrity.py tests/test_trusted_writer.py tests/test_knowledge.py tests/test_package_spine.py
python -m ruff check src/memoria_vault/runtime/worker.py src/memoria_vault/runtime/seeded_errors.py src/memoria_vault/runtime/integrity.py src/memoria_vault/runtime/trusted_writer.py src/memoria_vault/runtime/__init__.py tests/test_worker_queue.py tests/test_memoria_inspector.py tests/test_seeded_errors.py tests/test_integrity.py
python -m ruff format --check src/memoria_vault/runtime/worker.py src/memoria_vault/runtime/seeded_errors.py src/memoria_vault/runtime/integrity.py src/memoria_vault/runtime/trusted_writer.py src/memoria_vault/runtime/__init__.py tests/test_worker_queue.py tests/test_memoria_inspector.py tests/test_seeded_errors.py tests/test_integrity.py
python scripts/docs_doctor.py docs
python scripts/status_doctor.py
python scripts/agents_doctor.py --write
python scripts/agents_doctor.py
python scripts/gen_adr_index.py
python scripts/gen_adr_index.py --check
git diff --check
/home/eranr/Memoria-test/.memoria/.venv/bin/python docs/releasing/0.1.0-alpha.11/tmp/verify_start_blockers.py
```

Result: listed local/static checks passed. The live verifier remains `PARTIAL`
because screenshot/human visual rendering and attended Co-PI use are still
open; its Inspector row records
`workspace_view_present=True`, and its worker row records both a successful
disposable checked-only `answer-query` queue drain and a successful live
`Memoria-test` `answer-query` queue drain.
