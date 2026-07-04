# WP5 Operation/Digest Slice Results

Timestamp: 2026-06-29T05:59:18Z

Scope: first WP5 implementation slice for operation policy and source synthesis:

- `load_operation_policy()` loads checked `operation` Concepts and requires the
  WP5 policy contract fields before execution;
- operation policy loading rejects malformed `io_schema` metadata unless both
  `input` and `output` are non-empty strings;
- `compile_source_digest()` reads one checked catalog source and content file;
- `record_copi_interview_turn()` records a PI interview takeaway for a checked
  source as a committed `copi-interview` journal event;
- the operation records a `run` start event and a `model_call` event with
  runner, model, route, prompt version, toolset, and input/output hashes;
- digest compile includes recorded Co-PI interview turns as traceable inputs and
  places their takeaways in the digest body;
- `model: deterministic-fixture` remains the offline default, while non-fixture
  `direct_api` policies call an allowed OpenAI-compatible
  `/chat/completions` endpoint using `MEMORIA_MODEL_BASE_URL` plus
  `MEMORIA_MODEL_API_KEY`/`OPENAI_API_KEY`/`KILOCODE_API_KEY`;
- non-fixture `runner: hermes` policies can route the same digest prompt through
  a fresh embedded Hermes `AIAgent`; the adapter requires an explicit
  `allowed_network` route (`hermes-config` for normal Hermes config or an
  allowed `MEMORIA_HERMES_BASE_URL`/policy `base_url`), runs with
  `quiet_mode=True`, `skip_context_files=True`, `skip_memory=True`, a bounded
  iteration count, and no enabled Hermes toolsets by default;
- an import-only smoke against the installed local Hermes tree resolves the
  adapter target to `run_agent.AIAgent`; this proves library availability, not
  live model quality;
- `hermes_enabled_toolsets` is an explicit policy lever and rejects
  write-capable/external toolsets such as `file`, `terminal`, `browser`, `all`,
  platform bundles, and `mcp-*` before the Hermes agent is constructed;
- direct model output is rejected unless it is a markdown body with
  `## Synthesis` and `## Hub suggestions`, and the trusted writer still owns
  frontmatter;
- digest output also runs a high-precision lexical source-grounding smoke check
  against supplied source text, hub topics, and Co-PI interview turns before any
  digest Concept is written;
- the machine-owned `digest` is born in staging, promoted to
  `check_status: checked`, and committed with the journal;
- 5-15 touched hub updates promote brand-new machine-owned checked hubs, while
  curated live hub changes stay staged as suggestions under
  `.memoria/staging/knowledge/hubs/` and are not overwritten;
- `capabilities/operations/compile-source-digest.md` is the checked seed
  operation for this slice, and the worker exposes it as
  `compile-source-digest`;
- `render_ai_catalog()` / `write_ai_catalog()` generate
  `capabilities/ai-catalog.json` from capability Concepts with local SHA-256
  trust hashes, and `check_ai_catalog()` gives the drift check; the worker
  exposes this as `regenerate-ai-catalog`.
- every worker-dispatched operation is now represented by a checked
  `capabilities/operations/*.md` Concept, and
  `tests/test_capabilities.py::test_worker_operations_are_cataloged_and_policy_shaped`
  fails if a worker operation is missing from the generated capability catalog
  or if a checked operation Concept does not satisfy the WP5 policy contract.
- the worker now loads the checked operation Concept before dispatching any
  operation job, so missing or unchecked operation policies fail closed before
  operation-specific code runs.

This is not the full WP5 runtime proof. The local contract records Co-PI
interview takeaways through `record-copi-interview` and consumes them during
digest compilation; attended Co-PI use, a live Hermes model-quality run, and
richer source-grounded synthesis quality evals remain open runtime evidence.

Verification:

```bash
python -m pytest tests/test_operations.py tests/test_capture.py tests/test_trusted_writer.py tests/test_worker_queue.py tests/test_search_index.py tests/test_qmd_filter_mcp.py tests/test_patterns.py tests/test_schemas.py
python -m ruff check src/memoria_vault/runtime/operations.py src/memoria_vault/runtime/capture.py src/memoria_vault/runtime/search_index.py src/memoria_vault/runtime/trusted_writer.py src/memoria_vault/runtime/worker.py src/memoria_vault/runtime/__init__.py tests/test_operations.py tests/test_capture.py tests/test_trusted_writer.py tests/test_worker_queue.py tests/test_search_index.py tests/test_qmd_filter_mcp.py tests/test_patterns.py tests/test_schemas.py
python -m ruff format --check src/memoria_vault/runtime/operations.py src/memoria_vault/runtime/capture.py src/memoria_vault/runtime/search_index.py src/memoria_vault/runtime/trusted_writer.py src/memoria_vault/runtime/worker.py src/memoria_vault/runtime/__init__.py tests/test_operations.py tests/test_capture.py tests/test_trusted_writer.py tests/test_worker_queue.py tests/test_search_index.py tests/test_qmd_filter_mcp.py tests/test_patterns.py tests/test_schemas.py
python -m pytest tests/test_capabilities.py tests/test_worker_queue.py
python -m ruff check src/memoria_vault/runtime/capabilities.py src/memoria_vault/runtime/worker.py tests/test_capabilities.py tests/test_worker_queue.py
python -m ruff format --check src/memoria_vault/runtime/capabilities.py src/memoria_vault/runtime/worker.py tests/test_capabilities.py tests/test_worker_queue.py
python scripts/gen_reference_refs.py --check
python scripts/docs_doctor.py docs
python scripts/agents_doctor.py --write
python scripts/agents_doctor.py
python scripts/status_doctor.py
bash -n scripts/install.sh scripts/install/manifest.sh
git diff --check
python -m pytest tests/test_capabilities.py tests/test_projections.py tests/test_schemas.py
python -m ruff check tests/test_capabilities.py
python -m ruff format --check tests/test_capabilities.py
python -m pytest tests/test_operations.py -q
python -m ruff check src/memoria_vault/runtime/operations.py tests/test_operations.py
python -m ruff format --check src/memoria_vault/runtime/operations.py tests/test_operations.py
PYTHONPATH=src python -c "from memoria_vault.runtime.operations import _hermes_agent_class; cls = _hermes_agent_class(); print(cls.__module__, cls.__name__)"
```

Result: all passed.

Later cleanup retired the stale alpha.10 QuickAdd/fleeting surface; the current
full pytest suite passes with the alpha.11 `note` command surface.
