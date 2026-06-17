---
topic: decisions
id: 80
title: Ephemeral containerized Linux test-env harness
status: accepted
date_proposed: 2026-06-16
date_resolved: 2026-06-17
assumes: [28, 29, 64, 76]
supersedes: []
superseded_by: []
parent: Decisions
grand_parent: Explanation
---

# ADR-80: Ephemeral containerized Linux test-env harness

## Context

[ADR-64](64-native-windows-support.md) already splits provisioning into two
single-OS installers — native Windows is the production runtime (`install.ps1`),
Linux/WSL is the testing runtime (`install.sh`). That split is settled and shipped;
this ADR does **not** revisit it. What ADR-64 left open is *how thoroughly the
Linux test path is exercised*: [ADR-29](29-testing-framework.md) still places L3
integration as manual/Windows and leaves the cross-cutting suites
(installer / recovery / chaos / security / performance) and absolute L5 quality as
uncovered or per-release-manual gaps. Because the production bridge is gone, the
full stack can now run headless on one OS — making most of that automatable for
the first time. alpha.5 shipped only the thin slice this design needs as a proof:
a negative deny-assertion driven through the [ADR-28](28-write-gate-as-plugin.md)
policy-gate plugin ([#582](https://github.com/eranroseman/memoria-vault/issues/582)).
The full harness is the roadmap's next effort, captured here so the decision has an
ADR trail rather than living only in a release scratch note.

## Decision

The all-Linux test environment is a **version-controlled golden image** (a
peer-reviewed `Dockerfile`) holding the full real stack — headless Obsidian
(`xvfb-run --no-sandbox`) with all plugins, Zotero (headless) or a fixture
`memoria.bib`, Hermes, the five `memoria-*` profiles + MCP, the Local REST API +
native MCP, and `qmd` — with the local model as a `--gpus all` sibling container.
`docker compose` brings it up clean per run; a fresh vault volume is seeded from
checksummed, idempotent fixtures; nothing persists across runs except the cached
model weights. A **pytest orchestrator** drives the Obsidian CLI over the
command-palette surface (one trigger per palette command), asserting artifact
shape / frontmatter, gate decision + audit row, board transition, dashboard
re-render (injected JS), and a screenshot golden-image diff.

The local model is **served by `llama.cpp`** (already vended via `qmd`'s
`node-llama-cpp`, GPU path solved on the test box). The target is **Gemma 4 12B**,
confirmed GA (Google, 2026-06-03, Apache 2.0): it is **multimodal-input /
text-output**, so it serves cleanly through a standard OpenAI text+tool endpoint —
dissolving the earlier "any-to-any won't serve" worry — with an official GGUF
(`unsloth/gemma-4-12b-it-GGUF`, `UD-Q4_K_XL` ≈ 7–8 GB, fitting the 16 GB card) run
via `llama-server … --jinja`, exposing `/v1`. **Qwen3-MoE remains an optional
fallback, no longer load-bearing.** The model is selected per environment through a
`MEMORIA_ENV=test|prod` overlay that extends the installer's existing
`{{PYTHON}}`/`{{VAULT_PATH}}`/`{{QMD}}` substitution with `{{MODEL_PROVIDER}}` /
`{{MODEL_BASE_URL}}` / `{{MODEL_DEFAULT}}` — flipping the Hermes provider
(`kilocode` → `openai-compatible`), not just an endpoint URL. This flattens
production's per-profile model tiering ([ADR-48](48-copi-and-agent-consolidation.md)),
so absolute L5 quality and the per-profile config-shape surface stay on the
Windows production-acceptance pass; the harness validates wiring, integration,
golden path, recovery, security, and scale, plus eval *mechanics* and regression.

**Three gates must be resolved before the harness ships** (it is `deferred` until
then):

1. **Prove the gate fires (safety).** The harness MUST include a negative
   deny-assertion: a known-deny write, routed through the live ADR-28 plugin, is
   **blocked** with a deny audit row — never inferred from positive assertions. The
   superseded `re.fullmatch("obsidian.*")` shell-hook never matched the real
   `mcp_obsidian_*` tool names; the plugin's substring match does, so the shim must
   route through the plugin. (Shipped as the alpha.5 thin slice.)
2. **Model exists and is text+tool-servable — RESOLVED (2026-06-16).** Gemma 4 12B
   is GA with an official GGUF and `llama.cpp` / Ollama / vLLM support; it is
   multimodal-input / text-output, so a standard OpenAI text+tool endpoint fits. No
   longer a blocker; Qwen3-MoE is a kept-in-reserve fallback.
3. **Tool-call emission — narrowed to a smoke test.** Model, GGUF, `--jinja`, the
   `/v1` endpoint, and headline tool-use are all confirmed; the one unverified
   detail is whether `llama.cpp --jinja` parses Gemma 4's chat template into
   OpenAI-format `tool_calls` Hermes can consume (Gemma 3 lacked native tool tokens,
   so it is worth a local check). A ~5-minute `llama-server` smoke test settles it;
   only if it fails is a parser/shim needed, not a `base_url` swap.

## Phased adoption — the minimal viable harness (80/20)

The full harness is a large build, but most of its release-blocking value does
**not** need the costly parts. Memoria's load-bearing logic is deterministic
(Operations, the policy gate, ingest, schemas), so the **model layer** and the
**visual layer** — the two most expensive pieces — buy the *last* increment of
confidence, not the first.

**Phase 1 — deterministic integration + golden-path harness (~20% of the cost,
~80% of the value), covering L0–L4 + cross-cutting.** No GPU, no live model, no
screenshots. The framework's own cheap/expensive line is the **L4/L5 boundary**
([ADR-29](29-testing-framework.md)): L0–L4 are *wiring* (does the lifecycle produce
the right artifacts and transitions), L5 is *quality* (judgement). So **L4 belongs
in this tier** — the agent steps need a model only to emit a structurally-valid
output, which a recording or a seed supplies, so **the model is needed at record
time, not run time.** Containerize the *existing* offline stack —
`scripts/e2e-smoke.sh` already builds a vault installer-equivalently and walks
scaffold → golden → commit gate → offline ingest → honesty card → lint with no
network — and add:

- (a) **headless Obsidian over the command palette with data-layer asserts**
  (artifact / frontmatter, gate decision + audit row, board transition, dashboard
  re-render) — *not* pixel diffs;
- (b) **record/replay cassettes** for the agent-wiring loops, matched on tool-call
  structure, so L2b runs with **no live model**;
- (c) the **deny-assertion** (already shipped) plus the **installer / recovery**
  smoke;
- (d) the **L4 golden-path** (source → ingest → classify → discuss → claim → draft →
  verify → export), model-free, by two means that compose. **Seed** fixture
  artifacts at the generative steps and drive the deterministic stages live —
  reusing `e2e-smoke.sh` for ingest, the **g9 zero-LLM spine**
  (dispatch → claim → run → gated write → audit → `done`), and the alpha.5 **seeded
  structural-impact path** — for partial L4 immediately from existing parts; then
  **upgrade each seeded step to a cassette** as cassettes are recorded, ratcheting
  to full L4 *inside* Phase 1 with no jump to Phase 2.

Deterministic, runs per-PR, and closes the L3-integration, **L4 golden-path**,
recovery, and safety gaps that actually block releases. The only L4 piece held back
is the path driven by a *live* model — the L4/L5 seam — which stays on the Windows
production-acceptance pass and Phase 2.

**Phase 2 — the live-model + visual + chaos/perf tail (~80% of the cost).** The
`--gpus all` sibling container + Gemma 4 + nightly real-quality L5 eval (and the
live-model golden-path run — the L4/L5 seam), the screenshot golden-image diffs,
and the chaos / security / performance suites. Its
*model* risk is now low (gate 2 resolved), but its *cost* — GPU infra,
nondeterminism, and flaky visual baselines — is what makes it the expensive tail.
Build it only once Phase 1's coverage proves insufficient.

This phasing is already latent in the design's cadence (per-PR fs-shim + cassettes
with no live model; nightly full stack on Gemma); Phase 1 simply makes the
no-model tier the shippable unit and defers the rest.

## Consequences

- Closes the ADR-29 L3 manual/Windows gap and the recovery / security /
  performance cross-cutting gaps; same-host localhost on the Linux side also makes
  HTTPS REST trivial and closes the cross-OS trust gap
  ([#527](https://github.com/eranroseman/memoria-vault/issues/527),
  [ADR-31](31-native-obsidian-mcp.md)).
- Introduces new maintained artifacts: the golden image, the fixture corpus, and
  the Obsidian-CLI harness — each version-pinned and hash-recorded per run so
  "green today = green tomorrow."
- A binary "did it call a tool?" check misclassifies a weak local model. Assertions
  use a three-bucket classification (no tool call / wrong (tool,path) / expected
  shape); only the expected bucket asserts artifact, gate, audit, board, and
  dashboard state.
- Record/replay cassettes match on **tool-call structure** (tool name + arg shape),
  not raw prompt bytes, or they no-op on exactly the wiring refactors they exist to
  catch. The nightly trigger is a Windows Task Scheduler → `wsl.exe` job, not WSL2
  `crond` (WSL2 has no persistent init).
- Residuals are bounded: OS portability (test = Linux, prod = Windows) replaces the
  deleted bridge, checked by each installer on its own OS plus the
  production-acceptance pass; absolute output quality stays a production-model
  judgment.

## When this matters

**Phase 1 shipped in v0.1.0-alpha.6** (model-free L0–L4 record/replay harness, #586;
the G3 tool-call smoke runs against a local OpenAI-compatible endpoint, #662) — this
ADR is `accepted` for Phase 1. **Phase 2 stays deferred**: raise it when any holds —
the manual L3 surface or an uncovered cross-cutting suite (recovery / security /
performance) becomes a recurring release-blocking gap; a real project's PI-touch
budget needs L5 regression automated rather than hand-run. **Phase 1 needed no model
work at all** — its trigger was simply that recurring L3 / recovery gap; gate 2 is
already resolved and Phase 2 carries the remaining model / visual cost. The `assumes:` list pins the
mechanisms it rests on — if the two-installer split (ADR-64), the write gate
(ADR-28), or the reconciling installer (ADR-76) change shape, re-judge this.

## Alternatives considered

**Keep the split-OS WSL2 bridge for testing.** Rejected: it needs `.wslconfig`
tuning, blocks HTTPS, and forces manual Windows-only L3 — the fragility class
ADR-64 already deleted on the production side.

**Ship the fs-shim smoke suite (ADR-29 Option B) as the whole test env.** Rejected
as the *whole* env, kept as the per-PR cheap tier: a filesystem shim cannot
exercise real plugins, REST, dashboards, Zotero, or the visual surface.

**Serve the model with vLLM.** vLLM *is* in fact supported for Gemma 4 (Google
lists it), so this is a preference, not a constraint: `llama.cpp` is still chosen
because it is already vended via `qmd`, its GGUF (`UD-Q4_K_XL` ≈ 7–8 GB) fits the
16 GB card with headroom, and the GPU path is already solved on the test box. Ollama
is acceptable only as a thin wrapper over the same `llama.cpp` engine, not a
separate stack.

## Related

- **Related decisions / Depends on:** [ADR-64](64-native-windows-support.md) (the
  two-installer split this builds the Linux side of),
  [ADR-29](29-testing-framework.md) (the testing framework this automates),
  [ADR-28](28-write-gate-as-plugin.md) (the deny-assertion path),
  [ADR-76](76-versioned-vault-release-reconciling-installer.md) (the installer the
  `MEMORIA_ENV` overlay extends), [ADR-31](31-native-obsidian-mcp.md) (HTTPS REST
  on same-host localhost).
- **Files affected:** `scripts/install.sh`, `scripts/install.ps1`, profile
  `config.yaml` templates and cron wrappers (the `{{MODEL_*}}` overlay), a new
  `Dockerfile` + `docker compose` stack, and the fixture corpus.
- **Source discussion:** alpha.5 closeout (WS-0 spike
  [#576](https://github.com/eranroseman/memoria-vault/issues/576), thin deny-slice
  [#582](https://github.com/eranroseman/memoria-vault/issues/582)) and issue
  [#527](https://github.com/eranroseman/memoria-vault/issues/527) (HTTPS REST).
