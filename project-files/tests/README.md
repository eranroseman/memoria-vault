---
topic: tests
---

# Tests

Reusable, version-agnostic test **protocols** (procedures) — not test code, and not
filled-in run results. A *protocol* is the steps to validate something; a *run* is a
protocol executed with results recorded. **Protocols live here; runs live with their
release** in `releases/vX.Y/` (e.g. `gui-test-protocol_v0.1.md`).

## Layout

| Path | What it is |
|---|---|
| [coverage-matrix.md](coverage-matrix.md) | Keystone index: every component → coverage layer → which protocol validates it → automated? → status |
| [test-protocol-template.md](test-protocol-template.md) | Copy this to author a new protocol |
| [protocols/](protocols/) | The reusable protocols (browse the directory) |

## Why `tests/` and `releases/` stay separate

Protocols are **version-agnostic** and shared across every release; runs are
**version-specific** records of one cut. Merging them would tie reusable procedures
to a single version. So: reusable procedure → `tests/protocols/`; completed run +
sign-off → `releases/vX.Y/`.

## Coverage layers and gates

- **Layers (L0–L5)** — what *kind* of coverage: L0 static, L1 self-tests, L2 agent
  wiring, L3 GUI/dashboards, L4 end-to-end lifecycle, L5 output quality.
- **Tiers (T0–T5)** and **Gates (G1–G11)** — release-readiness checkpoints; their
  state lives in the [release plan](../releases/v0.1/release-plan-v0.1.md) §2/§3, not here.

## Run order

```
headless ─▶ installer ─▶ cli ─┐
                        gui ─┴─▶ e2e ─▶ g9-spine ─▶ g10-ingest
```

`headless` (static + Python self-tests, CI-enforced) must be green first; `installer`
stands up a throwaway vault; `cli` and `gui` validate the wired system; `e2e` runs one
source through the full lifecycle; `g9`/`g10` prove the deterministic spine and ingest
value-loop. Per-release orchestration + sign-off: [candidate-run-checklist](../releases/v0.1/candidate-run-checklist.md).

## Adding or changing a protocol

Copy `test-protocol-template.md`, keep the shared shape (preconditions → numbered
Parts/steps → results table → explicit green criteria), and add a row to
`coverage-matrix.md` so the component → protocol mapping stays complete.
