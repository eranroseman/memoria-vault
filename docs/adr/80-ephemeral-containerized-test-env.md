---
topic: decisions
id: 80
title: Ephemeral containerized Linux test-env harness
status: deferred
date_proposed: 2026-06-16
date_resolved:
assumes: [28, 29, 64, 76]
supersedes: []
superseded_by: []
parent: Decisions
grand_parent: Explanation
nav_exclude: true
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
`node-llama-cpp`, GPU path solved on the test box; GGUF Q4_K_M fits the 16 GB
card). `gemma4_unified` (~12B) is the target **only once its existence and an
OpenAI-style text+tool endpoint are confirmed first-party**; **Qwen3-MoE is the
verified fallback** and the choice of Gemma-over-Qwen3 must be justified on
evidence, not VRAM math. The model is selected per environment through a
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
2. **Verify the local model exists and is text+tool-servable** before any sizing is
   load-bearing — `gemma4_unified` / "any-to-any" is unconfirmed; Qwen3-MoE is the
   verified fallback.
3. **Verify tool-call emission.** Confirm the serving runtime (`llama.cpp --jinja`)
   emits OpenAI-format `tool_calls` Hermes can consume, and that an
   `openai-compatible` Hermes provider exists and carries them; otherwise a
   parser/shim is required, not a `base_url` swap.

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

Raise this from `deferred` when any holds: the manual L3 surface or an uncovered
cross-cutting suite (recovery / security / performance) becomes a recurring
release-blocking gap; a real project's PI-touch budget needs L5 regression
automated rather than hand-run; or a confirmed local tool-calling model (Gemma-4
or Qwen3-MoE) is in hand so gate 2/3 can close. The `assumes:` list pins the
mechanisms it rests on — if the two-installer split (ADR-64), the write gate
(ADR-28), or the reconciling installer (ADR-76) change shape, re-judge this.

## Alternatives considered

**Keep the split-OS WSL2 bridge for testing.** Rejected: it needs `.wslconfig`
tuning, blocks HTTPS, and forces manual Windows-only L3 — the fragility class
ADR-64 already deleted on the production side.

**Ship the fs-shim smoke suite (ADR-29 Option B) as the whole test env.** Rejected
as the *whole* env, kept as the per-PR cheap tier: a filesystem shim cannot
exercise real plugins, REST, dashboards, Zotero, or the visual surface.

**Serve the model with vLLM.** Rejected: no usable GGUF path for the new
`gemma4_unified` arch, and BF16/AWQ won't fit the 16 GB card; `llama.cpp` is
already vended and GPU-solved. Ollama is acceptable only as a thin wrapper over the
same `llama.cpp` engine, not a separate stack.

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
