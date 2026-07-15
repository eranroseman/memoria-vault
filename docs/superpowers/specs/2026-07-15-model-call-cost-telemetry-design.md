# Model-call usage/cost telemetry — Design

Date: 2026-07-15. Status: design, pre-plan (not yet reviewed or issue-filed).
Governing docs: `docs/explanation/architecture/telemetry-architecture.md`
(analytics plane already names "cost" as a tracked dimension), and
`docs/reference/commands-and-transports/prompt-operations.md` (documents the
current `model_call` journal-event field set this spec extends).

## Goal

Close a gap that already has a named destination but no source.
`telemetry-architecture.md` states the analytics plane is "optimized for
trends: throughput, **cost**, attention, request state, eval results, and
drift," and names `request_id` as the join key "across request state,
**costs**, dispositions, audit rows, and diagnostics." No code path populates
either token usage or cost anywhere in the repo today — confirmed by reading
`_pydantic_ai_chat` (`src/memoria_vault/runtime/operations.py:951-984`): it
calls `agent.run_sync(prompt, model_settings=settings)`, reads only
`result.output`, and returns a bare `str`. The rest of `result` — including
`result.usage()` (a `RunUsage`: `input_tokens`, `output_tokens`,
`cache_read_tokens`, `cache_write_tokens`; `pydantic_ai/usage.py`) and
`result.response.cost()` (a `genai_types.PriceCalculation`, resolved from the
bundled, fully local `genai-prices` package — zero network calls;
`pydantic_ai/messages.py:2348`) — is computed by the SDK on every call and
discarded. `pydantic-ai-slim>=2.0` is already pinned; `genai-prices` is
already a hard, non-optional dependency of it. This closes the gap by reading
what's already there, not by adopting an external observability SDK (see
"Rejected alternative" below).

This spec was written up after reviewing `pydantic/logfire` and
`pydantic/skills` as possible sources of this capability and rejecting both —
see "Rejected alternative."

## Design decisions (made here; confirm at review)

- **Extend the existing `model_call` journal event; do not create a new
  sink.** All three current call sites that build a `model_call` event dict —
  the compile/prompt-operation path (`operations.py:361-375`), the shared
  `run_operation_model_text` helper (`operations.py:438-473`, currently called
  only from `integrity.py:1466`), and the digest-compile path
  (`operations.py:527-542`) — already flow through `append_journal_event` and
  `commit_writer_changes`. Adding fields to this one existing event is a
  smaller, more consistent change than a parallel
  `system/metrics/model-calls.jsonl`, and keeps exactly one durable record per
  model call instead of two.
- **`_pydantic_ai_chat`'s return contract changes from `str` to
  `dict[str, Any]`** with keys `text`, `usage`, `cost_usd`, `elapsed_s` — a
  plain dict, matching the codebase's existing convention for small
  structured values (`policy`, `runner`, `params` are all plain dicts; no
  dataclass is introduced for a 4-key return). `_run_prompt_model` and
  `_run_digest_model` change the same way, since both currently just forward
  or unwrap the string.
- **`usage` is a plain dict of the four `RunUsage` fields actually present on
  every call** (`input_tokens`, `output_tokens`, `cache_read_tokens`,
  `cache_write_tokens`) — logged unconditionally, since `result.usage()` never
  raises.
- **`cost_usd` is best-effort and nullable, never fabricated.**
  `result.response.cost()` raises `LookupError` when the model/provider
  combination isn't in `genai-prices`' static snapshot
  (`pydantic_ai/messages.py:2348` try/except path). Memoria's runner
  `base_url` is operator-configurable to arbitrary OpenAI-compatible
  endpoints — the seeded config already ships a `local` provider pointing at
  Ollama (`http://127.0.0.1:11434/v1`) alongside a `gateway` provider behind a
  `KILOCODE_API_KEY` proxy — so cost resolution will routinely fail for local
  or proxied models. On `LookupError`, `cost_usd` is `null`; this must never
  be papered over with an estimate.
- **No content capture, by design.** Only counts, cost, and wall-clock timing
  are logged — never prompt or completion text, matching the existing
  `model_call` fields (`prompt_hash`/`output_hash`, not the prompt/output
  themselves) and `diagnostics.py`'s content-light posture. This is the
  concrete alternative to routing model calls through an external
  observability SDK whose own instrumentation defaults to capturing full
  message content (see "Rejected alternative").
- **The `deterministic-fixture` runner path emits null/zero fields.** No real
  call happens in tests/CI, so `usage: null`, `cost_usd: null`,
  `elapsed_s: 0.0` — no schema surprise, no fixture pretending to measure a
  call that didn't happen.
- **No new dependency, no `SCHEMA_VERSION` bump.** `genai-prices` and
  `result.usage()` ship with the already-pinned `pydantic-ai-slim>=2.0`. This
  is an additive, optional-field change to a journal-event payload schema,
  not the SQLite schema (`SCHEMA_VERSION` stays at its current value).

### Rejected alternative: OpenTelemetry / `pydantic/logfire`

Considered and rejected in a prior review (chat-recorded, not yet filed as a
pattern-provenance entry — see "Out of scope"). Summary of why: Logfire's own
scrubbing rules explicitly exempt `gen_ai.input.messages`/
`gen_ai.output.messages` from redaction, so enabling its instrumentation with
content capture on ships raw prompts/completions to a third-party cloud by
default; free self-hosting doesn't exist (Enterprise-only). Separately,
`pydantic_ai.models.instrumented.InstrumentedModel`'s own
`InstrumentationSettings.include_content` defaults to `True` regardless of
backend, so even a self-hosted OTel collector would capture full message
content unless explicitly overridden. Memoria is a single-process, no-daemon
CLI whose one model-call site registers zero tools today — there is no
multi-span, cross-process trace tree to correlate, so the problem OTel/Logfire
solves doesn't exist here yet. One JSONL row per call, with counts/cost/timing
only, is the right shape for the actual, named need.

## Architecture

Three focused changes, each independently testable.

### 1. `_pydantic_ai_chat` return shape (`operations.py:951-984`)

- Wrap `agent.run_sync(...)` with a wall-clock timer
  (`time.monotonic()` before/after) for `elapsed_s`.
- After `result = agent.run_sync(prompt, model_settings=settings)`:
  - `usage = result.usage()` → `{"input_tokens": ..., "output_tokens": ...,
    "cache_read_tokens": ..., "cache_write_tokens": ...}`.
  - `cost_usd`: `try: result.response.cost().total_price except LookupError:
    None`.
- Return `{"text": text, "usage": usage, "cost_usd": cost_usd, "elapsed_s":
  elapsed_s}` instead of a bare `str`. The existing empty-output check
  (`RuntimeError("pydantic-ai model returned no message content")`) stays,
  applied to `text` before building the return dict.

### 2. Thread the result through `_run_prompt_model` / `_run_digest_model`

- `_run_prompt_model` (`operations.py:801-808`): the `deterministic-fixture`
  branch returns `{"text": _prompt_fixture_body(...), "usage": None,
  "cost_usd": None, "elapsed_s": 0.0}`; the `pydantic-ai` branch returns
  `_pydantic_ai_chat(...)`'s dict unchanged.
- `_run_digest_model` (`operations.py:896-917`): same fixture/real split.
  `_validate_digest_output` still takes plain `text: str` — extract
  `result["text"]` before validating, then return the full dict (validated
  text swapped back in) so the caller keeps `usage`/`cost_usd`/`elapsed_s`.
- Both callers (`operations.py:367`, `:525`) already bind the return value to
  a local (`output` / `digest_text`); update those bindings to unpack the new
  dict shape (e.g. `output = result["text"]`, keeping `result` around for
  step 3).

### 3. Extend the three `model_call` event dicts

Add three keys to each of the three existing `model_call` dict literals —
`operations.py:369-379` (prompt-operation path), `operations.py:441-456`
(`run_operation_model_text`, called from `integrity.py:1466`), and
`operations.py:527-540` (digest-compile path):

```python
"usage": result["usage"],
"cost_usd": result["cost_usd"],
"elapsed_s": result["elapsed_s"],
```

No other change to those dicts. `context`, `commit_writer_changes`, and the
journal-append plumbing are unchanged — this is three additional keys on an
event that already exists and already commits.

### 4. Docs

- `docs/reference/commands-and-transports/prompt-operations.md`: extend the
  `model_call` row description — currently "`model_call` rows include
  resolved mode/provider/model/params, a prompt hash, and the hash of the raw
  model output" — to also name `usage` (token counts), `cost_usd`
  (best-effort, nullable), and `elapsed_s`.
- `docs/explanation/architecture/telemetry-architecture.md`: no prose change
  needed. "Cost" is already named as a tracked analytics-plane dimension;
  this change makes that claim true rather than aspirational.

## Data flow

```
prompt-operation / digest-compile call
  → _run_prompt_model / _run_digest_model
     → _pydantic_ai_chat: agent.run_sync(...) [timed]
        → result.usage()            → usage dict (unconditional)
        → result.response.cost()    → cost_usd (nullable, LookupError → None)
     → returns {text, usage, cost_usd, elapsed_s}
  → model_call event dict gains usage / cost_usd / elapsed_s
  → append_journal_event(..., context=context)   [unchanged seam]
  → commit_writer_changes(...)                    [unchanged seam]

(deterministic-fixture path: usage=None, cost_usd=None, elapsed_s=0.0 —
no real call happened, nothing to report.)
```

## Testing

- `_pydantic_ai_chat` returns the `{text, usage, cost_usd, elapsed_s}` shape;
  a mocked `result.response.cost()` raising `LookupError` yields
  `cost_usd: None` while `usage` still populates from a mocked
  `result.usage()`.
- `deterministic-fixture` path (both `_run_prompt_model` and
  `_run_digest_model`) returns `usage: None`, `cost_usd: None`,
  `elapsed_s: 0.0` unconditionally, with no dependency on the real
  `pydantic-ai` import path.
- All three `model_call` event call sites (existing tests in
  `tests/test_operations.py` and the `integrity.py:1466` path) assert the
  event dict includes `usage`/`cost_usd`/`elapsed_s` keys, extending rather
  than replacing the current field-set assertions.
- No content-capture regression: assert the new fields are JSON-serializable
  numbers/dicts-of-numbers only — never prompt or completion text.

## Out of scope

Dashboard/worklist surfacing of the new fields (a follow-up over
`docs/reference/analysis-and-surfaces/dashboards.md` or `worklists.md`, not
this spec); joining `model_call.cost_usd` against PI disposition outcomes
(the separate "provenance → disposition" recommendation from the same
review, its own spec if pursued); backfilling historical `model_call` events
already on disk (no backfill — the baseline starts from this change forward,
same non-backfillable posture as `2026-07-14-i1-skeleton-design.md`); filing
the Logfire/`pydantic/skills` rejection as a formal pattern-provenance entry
(reviewed and explicitly rejected as the wrong doc — that table is scoped to
academic AI-research-system citations, not vendor-tooling decisions; an
ADR-style note in `design-history/arcs.md` is the right home, only if the
argument resurfaces, not preemptively).

## Constraints (inherited)

- Correctness gate: `python scripts/verify` passes before merge.
- Test only against disposable vaults (`tmp_path` / `test-vault/`), never a
  personal vault.
- Stage explicit paths only — never `git add -A` (shared-index rule).
- No new dependencies (`genai-prices` ships transitively with the already-
  pinned `pydantic-ai-slim>=2.0`).
- Schema mechanics: this is a `model_call` journal-event payload addition
  (optional fields), not a `SCHEMA_VERSION` change.
