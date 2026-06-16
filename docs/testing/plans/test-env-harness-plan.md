---
topic: tests
title: Test-env harness plan
status: draft
parent: Test plans
grand_parent: Testing
nav_order: 13
---

# Test-env harness plan — ADR-80 Phase 1

The Phase 1 harness is the automated, model-free slice of the L4 golden path. It
replays a version-controlled cassette against a disposable vault, drives deterministic
Memoria operations, and asserts artifact shape, schema validity, the Project gate, and
the policy deny path. It does **not** judge prose quality, run a live local model, drive
the Obsidian GUI, or take screenshot diffs; those remain ADR-80 Phase 2 / attended
production-acceptance work.

## What Runs

The executable entry point is
[`scripts/test_env_harness.py`](https://github.com/eranroseman/memoria-vault/blob/main/scripts/test_env_harness.py).
The default cassette is
[`fixtures/test-env/cassettes/alpha6-l4-golden-path.json`](https://github.com/eranroseman/memoria-vault/blob/main/fixtures/test-env/cassettes/alpha6-l4-golden-path.json).

The cassette is matched on tool name plus argument shape, not raw prompt text. A replay
therefore catches wiring and schema drift while staying stable across prompt wording
changes.

## Preconditions

- A fresh clone or clean worktree on Linux/WSL.
- Python dependencies from the normal dev/test environment.
- No live model, GPU, Obsidian, Hermes gateway, or network.

## Commands

```bash
python3 scripts/test_env_harness.py replay --json
env PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 python3 -m pytest tests/test_test_env_harness.py -q
bash scripts/e2e-smoke.sh
```

`scripts/e2e-smoke.sh` calls the harness replay after the installer-equivalent ingest
and graph steps, then runs final vault lint. This is the release-ready path for the
model-free L4 slice.

When a local OpenAI-compatible `llama.cpp`/Gemma endpoint is running, the optional
ADR-80 G3 smoke is:

```bash
MEMORIA_MODEL_BASE_URL=http://127.0.0.1:8080/v1 MEMORIA_MODEL_NAME=<model> \
  python3 scripts/test_env_harness.py model-smoke
```

Without `MEMORIA_MODEL_BASE_URL`, `model-smoke` reports a skip so ordinary per-PR
model-free checks stay deterministic.

## Green Criteria

- The cassette loads with `match: tool_name+arg_shape`, and every step's recorded
  argument shape matches its fixture arguments.
- Replay writes the expected source, classification audit, project, thesis, claim,
  Project gate index, draft, verification card, done prompt, and export artifacts.
- The policy deny assertion blocks the known forbidden claim write and appends a `deny`
  row to `system/logs/audit.jsonl`.
- The forbidden file does not exist after replay.
- `scripts/e2e-smoke.sh` remains green with the harness wired in.

## Out of Scope

- Requiring live Gemma / `llama.cpp` tool-call emission smoke in the per-PR path.
- Obsidian command-palette automation and dashboard rendering.
- Screenshot golden-image diffs, chaos, scale, and performance.
- L5 quality evaluation.

Record release-specific evidence in the active release gate/stage issues. Keep this
page as the reusable procedure.
