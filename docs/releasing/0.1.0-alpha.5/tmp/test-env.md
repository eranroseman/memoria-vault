# Test environment & procedure — the complete design (clean-sheet)

Status: draft (scratch under `tmp/`)
Author: PI + Claude
> **Process risk:** this scratch note **supersedes a recorded decision** (the prior
> Haiku-via-Kilocode test-model default in the `test-env-hardware-and-model` memory).
> Copy-ready **ADR drafts are now in §10** — but they still live under `tmp/` until
> promoted to `docs/adr/`. Promote them before this file is cleaned up, or the
> decision evaporates with no ADR trail.
Context: design the **best and most complete** testing environment and procedure
for Memoria, with **no inherited constraints**. Two single-OS installers replace
the old split-OS bridge:

- **`install.ps1` — all-Windows = production.** Native Windows Hermes (now
  supported, ADR-64), Obsidian, Zotero — everything on one OS, localhost only.
- **`install.sh` — all-Linux = test.** Native Linux everything, **containerized
  and ephemeral**, GPU-served local model, fully automatable.

> **This supersedes every earlier draft.** Prior versions kept settling for the
> inferior shipped posture (Obsidian-on-Windows ↔ Hermes-in-WSL2, bridged over
> mirrored-networking loopback; manual Windows-only L3). That bridge existed only
> because we lacked native-Windows Hermes and a Linux GUI stack. We now have both,
> so the bridge — and the whole class of fragility and "topology parity" residual
> it created — is **deleted**, not worked around.

---

## 1. Why two single-OS installs is strictly superior

| Property | Old split-OS (Obsidian-Win ↔ Hermes-WSL2) | New: all-Win prod / all-Linux test |
|---|---|---|
| REST/MCP transport | cross-OS loopback over mirrored networking (fragile, needs `.wslconfig`, breaks silently) | **same-host localhost** on each side |
| HTTPS for REST (issue #527) | blocked — Hermes (WSL2) can't trust Windows-Obsidian's self-signed cert | **trivial** — co-located, one trusted local cert |
| Test automation | manual, Windows-bound GUI | **headless, scriptable, containerized** |
| Reproducibility | "disposable vault", hand-reset | **ephemeral golden-image container, clean per run** |
| Parallelism | one box, one vault | **N containers in parallel** |
| Install complexity | two OSes entangled per environment | **one OS per environment**, two clean installers |

The only thing the split bought was "test on the same Windows Obsidian production
uses." We replace that weak parity with **two strong single-OS installs** plus a
focused production-acceptance pass (§7) — better on every axis that matters.

---

## 2. The all-Linux test environment — ephemeral, containerized, complete

A single **version-controlled golden image** (Dockerfile, peer-reviewed like code)
holds the entire real stack; `docker compose` brings it up clean per run.

```
┌─ docker compose (ephemeral, recreated per run) ───────────────────────┐
│  service: memoria-stack            service: model                      │
│  ├─ Hermes (native Linux)          ├─ llama.cpp server + Gemma 4 12B   │
│  ├─ 5 memoria-* profiles + MCP     │  (GGUF Q4_K_M, --jinja, --gpus    │
│  ├─ Obsidian (headless: xvfb-run   │   all via nvidia-container-toolkit)│
│  │   --no-sandbox) + all plugins   │  OpenAI-compatible endpoint       │
│  ├─ Local REST API + native MCP    └───────────────────────────────────│
│  ├─ Zotero (headless) or fixture memoria.bib                          │
│  ├─ qmd (hybrid search)                                                │
│  └─ vault on a fresh volume, seeded from fixtures                      │
│  driver: pytest orchestrator → Obsidian CLI + hermes chat -q + asserts │
└────────────────────────────────────────────────────────────────────────┘
```

Principles (recognized ephemeral-env best practice):
- **Golden image as code** — pinned base, pinned Obsidian/plugin/Hermes versions,
  image hash recorded per run so "green today = green tomorrow."
- **Clean per run** — fresh vault volume + idempotent fixture seed; no drift, no
  state leakage, failures trace to logic not residue.
- **Parallel & isolated** — multiple stacks at once (e.g. scale fixtures vs golden
  path) on separate compose projects.
- **Persistent only where intended** — the GGUF weights cache on a named volume so
  the 12B isn't re-fetched each run; everything else disposable.

Host: the Linux is WSL2-Linux on the RTX 4060 Ti box (GPU passthrough into the
container via `nvidia-ctk runtime configure`); the design is host-agnostic and
runs identically on a bare-metal Linux CI runner.

---

## 3. Headless Obsidian + the Obsidian CLI driver

Obsidian (Electron) runs headless via `xvfb-run --no-sandbox`; the **Obsidian
CLI** drives Memoria's real PI surface — the **16 command-palette commands**
(QuickAdd macros; see `docs/reference/obsidian-command-palette.md`):

- **Capture:** capture fleeting · write claim · capture from URL · capture from Zotero
- **Inbox/workflow:** resolve inbox card · create linked claim
- **Workspaces:** Desk · Library · Studio
- **Lanes:** catalog · extract · link · map · draft · verify
- **Fallback:** delegate task · run pattern

Per command: trigger via CLI → lane runs on Gemma → assert the **artifact shape /
frontmatter**, **gate decision + audit row**, **board transition**, **dashboard
re-render** (via injected JS), and a **screenshot golden-image diff** for visual
correctness. The headless display makes the visual check automatable — the human
sliver shrinks to reviewing diffs, not running the app.

**Prove the gate fires — don't infer it (the false-green trap).** The write gate
is Option B's whole reason to exist, so the harness must include a **negative
assertion**: drive a *known-deny* write and assert it is **blocked** with a deny
audit row — not just that allowed writes land. A silently-disengaged gate passes
every positive assertion while writing freely; only a deny test catches it. This
is not hypothetical: the **live enforcement is the ADR-28 plugin**
(`src/.memoria/plugins/memoria-policy-gate/__init__.py`),
which matches by substring (`"obsidian"` in the name) and therefore *does* catch
the real `mcp_obsidian_*` tool names. Its predecessor — the `hooks:` shell matcher
`re.fullmatch("obsidian.*", …)` — **never matched `mcp_obsidian_*` and never
fired** (that bug is *why* the plugin exists). So the Option-B shim must route
writes through the **plugin** path, and the deny assertion is what proves it did.

**Three-bucket assertion** (a binary pass/fail misclassifies a weak model). Classify
each run into:
1. **No tool call emitted** → model-capability flake (not a wiring regression). But
   note stage 1 alone can't separate *emitted nothing* from *emitted a malformed
   call the runtime parser silently dropped* (the §4 parser risk) — to tell those
   apart, inspect the **raw model output below the parser**, not just the
   OpenAI-format transcript.
2. **A tool call emitted, but the wrong (tool, path) shape** → model *behaviour*,
   not wiring. A binary "did it call a tool?" wrongly buckets this as a wiring
   break. Worse, a wrong call that still contains `obsidian` + a write keyword can
   satisfy a naive gate assertion *for the wrong reason* — which is exactly why the
   gate check must be the **deny assertion above**, keyed on the expected decision,
   not "a gated tool was touched."
3. **The expected (tool, path) shape** → only now assert artifact / gate decision /
   audit / board / dashboard state.

(Practical shim note: the gate over-approximates on substring — `putative`→`put`,
`appendix`→`append` — so don't embed write-keyword substrings in *read*-tool names.)

---

## 4. Local model — Gemma 4 12B served by llama.cpp (containerized, GPU)

- **⚠️ Verify the model exists and is text+tool-servable — before any sizing below
  is load-bearing.** `google/gemma-4-12B-it` is described as a `gemma4_unified`
  *any-to-any* multimodal model; that characterization is **unconfirmed against a
  first-party source**, and "any-to-any" is a yellow flag — such models are often
  *not* served through a standard OpenAI text+tool endpoint at all. The entire
  net-new L2b loop has no engine if the model doesn't exist under this name, isn't
  text-servable, or doesn't tool-call. Confirm existence + a GGUF build + an
  OpenAI-style tool path **first**; the VRAM math is moot until then.
- **Verified fallback — Qwen3-MoE.** If Gemma 4 doesn't pan out, **Qwen3-MoE** is a
  *known* strong tool-caller with real GGUF/AWQ quants that fits the 4060 Ti — the
  prior recorded choice. The ADR must justify Gemma-over-Qwen3 on evidence, not swap
  a verified option for an unverified one on VRAM alone.
- **Model & quant (if Gemma verifies):** `gemma4_unified` ~12B, **GGUF Q4_K_M ≈
  6.9 GB** — fits the 16 GB 4060 Ti with room. (BF16 weights are ~24 GB, so an
  *unquantized* server can't fit this card at all.)
- **Runtime — llama.cpp, not vLLM, not a new daemon.** The stack **already vends
  llama.cpp** via `qmd` (`node-llama-cpp`), and its GPU path is already solved on
  this box (CUDA-13 runtime — see the qmd GPU note). So serve Gemma with a
  **llama.cpp server**: zero new serving dependency, native GGUF Q4_K_M, and
  `--jinja` to render Gemma 4's tool-call chat template. **vLLM is out** — no usable
  GGUF path for a ~2-week-old `gemma4_unified` arch, and BF16/AWQ won't fit 16 GB.
  Ollama is acceptable only as a thin wrapper over the *same* llama.cpp engine, not
  a separate stack.
- **Tool-calling — the ⚠️, re-aimed.** Native function calling is **confirmed by the
  Gemma 4 model card** (structured tool use via special tokens) — that question is
  resolved *yes*. The real, unverified, load-bearing risk is **whether the serving
  runtime emits OpenAI-format `tool_calls`** from those special tokens that Hermes
  can consume. The official path is special-tokens + jinja template + a regex parse;
  **verify llama.cpp's `--jinja` yields OpenAI `tool_calls` for gemma4 — if not, you
  need a parser/shim, not just a `base_url` swap.**
- **Context budget — pin it (don't assume the headroom).** Gemma 4 12B advertises a
  256K window; KV cache at long context is multiple GB, and with ~7 GB of weights
  the ~8 GB headroom on a 16 GB card is eaten fast — exactly on the longer Librarian
  lanes. **Pin `--ctx-size` to a budget-computed length** (size KV against the 16 GB
  budget; do *not* default to 256K) or risk OOM mid-lane.
- **Model overlay — flips the provider adapter, not just the endpoint.** `base_url`
  is a literal duplicated across all five profiles (Hermes has no global config
  layer — ADR-27). The installer already substitutes
  `{{PYTHON}}`/`{{VAULT_PATH}}`/`{{QMD}}`; add `{{MODEL_PROVIDER}}` +
  `{{MODEL_BASE_URL}}` + `{{MODEL_DEFAULT}}`. This **changes the Hermes provider**
  (`kilocode` → `openai-compatible`), which must (a) exist in Hermes and (b) carry
  tool-calls correctly — unverified, and it compounds the tool-call risk above; it
  is *not* a one-variable change. Non-goal: the overlay flattens prod's per-profile
  model tiering (posture-defined, ADR-48) to one Gemma — so **both** the Opus lanes
  (copi *and* peer-reviewer, per their `config.yaml`) go dark under green L2b, not
  one, and per-profile **config-shape** divergence (not just reasoning depth) is
  untestable locally. The Windows production-acceptance pass (§7) is the only place
  the real per-profile model wiring runs.

---

## 5. Coverage — full L0–L5 + cross-cutting, in one environment

| Layer | Coverage in the Linux env | Model |
|---|---|---|
| **L0** static & schema | ✅ full (CI, base image) | none |
| **L1** component (engines, gate, board, metrics) | ✅ full `pytest tests/` | none |
| **L2a** policy-gate contract | ✅ full hermetic | none |
| **L2b** agent wiring | ✅ fs-shim smoke (per-PR) **+** real-stack CLI drive | Gemma |
| **L3** integration (plugins, REST, 12 dashboards, Zotero→bib, ACP) | ✅ **now automated** (headless Obsidian + CLI + JS asserts + screenshot diffs) | Gemma |
| **L4** golden-path E2E | ✅ full lifecycle, capture→…→export | Gemma |
| **L5** quality/eval | 🟡 **mechanics + regression** (gold tasks run, scores compute, regressions caught); **absolute** scores → production | Gemma (local) / Claude (prod) |
| **Cross-cutting: installer** | ✅ the Linux installer tested by building the image; Windows installer tested on Windows (§7) | — |
| **Cross-cutting: recovery/chaos** | ✅ **new** — fault injection (§6) | Gemma |
| **Cross-cutting: security/adversarial** | ✅ **new** — lane-escape, prompt-injection, secret-leak, fail-closed | Gemma |
| **Cross-cutting: performance/scale** | ✅ **new** — 500/2000-note fixtures, qmd rebuild timing | Gemma |

The three cross-cutting gaps that are ⛔ today (recovery, security, performance)
and all manual L3 items become **automated** here — the env's biggest new value.

---

## 6. Chaos & edge-case injection (first-class, not an afterthought)

Each is a scripted scenario: set the bad state → drive the relevant command →
assert detect/block/recover per `docs/reference/failure-modes.md`.

- **Infra:** MCP server down mid-run; REST not up; Ollama/GPU busy; cron miss.
- **Data:** broken/again-nested YAML; `_proposed_classification` overwrite (the
  CRITICAL mode); stale qmd index; missing `OPENALEX_API_KEY`; garbage required
  fields (tier-2 gameability); vocabulary mismatch.
- **Workflow:** stuck Kanban card; review-gate dry-run degradation; duplicate
  source; retraction sweep flips a cited source; cite-check on a missing citekey.
- **Security:** write outside lane scope (write-wall deny); prompt-injection in a
  captured source attempting escalation; secret-leak probe; **hook error must fail
  closed**.
- **Scale:** dashboard + qmd timing at 500 and 2000 notes.

Because the env is ephemeral, destructive scenarios are free — break it, assert,
throw it away.

---

## 7. Procedure — pyramid, cadence, and gates

| Cadence | What runs | Where | Cost |
|---|---|---|---|
| **Per-commit** | L0 + L1 + L2a | base container, no GPU | seconds, free |
| **Per-PR** | L2b fs-shim smoke + record/replay cassettes (pin model id+quant **and** the serving stack — llama.cpp build + jinja template + parser — since they shape the tool-call format) | base container, no live model | minutes, free, deterministic |
| **Nightly** | full ephemeral stack: L2b real + L3 + L4 + chaos + partial L5, all 16 commands on Gemma, screenshot diffs | compose stack + GPU | tens of min, free |
| **Per-release** | performance/scale + security/adversarial + full L3 matrix | compose stack + GPU | longer |
| **Per-release (prod)** | **production acceptance** on all-Windows: absolute L5 quality (real models), Windows installer + native-OS runtime, HTTPS REST | Windows box | manual/attended |

Disciplines (carry ADR-29's keystones): the **coverage matrix** stays the index of
component → layer → automated? → gate; **drift control** (`check-test-refs`) keeps
plans honest; **determinism** — below L5 assert artifact shape + gate decision,
never prose.

**Two operational caveats that decide whether this works at all:**
- **Cassette match granularity (or record/replay is a no-op on real refactors).**
  The value claim is "catches a refactor that broke the MCP wiring" — but most
  wiring refactors change prompt/system text, so a cassette keyed on full request
  bytes just *misses* and you can't tell "broke wiring" from "needs re-record."
  **Match on tool-call structure (tool name + arg shape), not raw prompt bytes**, or
  the harness no-ops on exactly the failure class it's sold to catch.
- **Nightly trigger — not WSL2 cron.** WSL2 has no persistent init, so a distro
  `crond` silently won't run when no shell is open. Pin the trigger as a **Windows
  Task Scheduler job invoking `wsl.exe -d <distro> -e …`** (or, less reliably,
  `systemd=true` + a systemd timer + keepalive). "Nightly" is aspirational otherwise.

**Operating a nightly run:** (1) build/pull the pinned golden image; (2)
`docker compose up` the stack; (3) idempotent fixture seed; (4) pytest orchestrator
drives Obsidian CLI + `hermes chat -q`, collecting assertions; (5) gather artifacts
— logs, audit.jsonl, screenshots, perf timings, coverage; (6) tear down. Clean
every time.

**Test data (version-controlled, checksummed):** fixture vaults at scales
(empty / small / 500 / 2000); fixture Zotero `.bib` + PDFs; seeded board / audit /
inbox states; a golden-path source corpus; golden screenshots. Seed is idempotent
and part of provisioning.

---

## 8. Honest residuals (now genuinely small)

1. **OS portability, not a bridge.** Test = Linux-native, prod = Windows-native.
   Each installer is exercised on its own OS; the *Windows-specific* surface
   (native Windows Hermes/Obsidian/Zotero, path handling, `install.ps1`) gets the
   per-release production-acceptance pass (§7). This is ordinary cross-platform
   hygiene — bounded and well-understood — not the silent cross-OS bridge we
   deleted.
2. **Absolute output quality.** Local Gemma validates eval *mechanics* + catches
   regressions; *absolute* L5 numbers are the production model's. Final quality
   acceptance stays on Windows with real models.

Everything else — wiring, integration, dashboards, golden path, installer,
recovery, security, scale, visual diffs — runs in the Linux env, automated, free.

---

## 9. ADR implications & next steps

Large enough to be ADR-owned (supersedes/amends several):
- **Two-installer model** — `install.ps1` all-Windows prod (native Hermes, revisits
  ADR-64's deferral) + `install.sh` all-Linux test. New decision.
- **Revisit ADR-29** — L3 moves from manual/Windows to automated headless-Linux.
- **Revisit ADR-31** — same-host localhost on each side; **enables HTTPS REST
  (closes issue #527)** since there's no cross-OS trust gap.
- **Ephemeral containerized harness** — golden image, fixtures, compose, the
  Obsidian-CLI driver, local Gemma.
- Record non-goals: flattened model tiering; absolute-L5 + Windows-OS surface stay
  on production.

Next steps:
- [ ] **Verify the model exists and is text+tool-servable** (`gemma4_unified` / any-to-any is unconfirmed; the L2b loop has no engine otherwise — keep **Qwen3-MoE** as the verified fallback). **Gate everything below on this.**
- [ ] **Add the negative gate assertion to the L2b/golden harness** — a known-deny write must be *blocked* (deny audit row), routed through the ADR-28 plugin, so a disengaged gate fails loud instead of green.
- [ ] **Verify the serving runtime emits OpenAI `tool_calls` for gemma4** (model card confirms native FC; the open risk is llama.cpp `--jinja` → OpenAI format, else a parser/shim — gates the whole driver).
- [ ] **Confirm Hermes has an `openai-compatible` provider that carries tool-calls** (the overlay flips the provider, not just the endpoint).
- [ ] **Compute & pin `--ctx-size`** against the 16 GB KV budget (don't default to 256K).
- [ ] Author `install.sh` (all-Linux): Obsidian + Zotero + Xvfb + Hermes + plugins + MCP venv + qmd + `{{MODEL_*}}`.
- [ ] Author `install.ps1` (all-Windows, native): Hermes + Obsidian + Zotero, localhost, HTTPS REST.
- [ ] Build the **golden image** (Dockerfile) + `docker compose` (stack + llama.cpp/GPU); pin & hash.
- [ ] Wire the **Obsidian CLI** driver over the 16 commands; add JS asserts + screenshot golden diffs.
- [ ] Build **fixture data** (scaled vaults, `.bib`, seeded states, golden screenshots), checksummed + idempotent seed.
- [ ] Author the **chaos**, **security**, and **performance** suites (§6).
- [ ] Keep **fs-shim smoke** + **record/replay** as the per-PR cheap tiers.
- [ ] Define the **production-acceptance** pass (absolute L5 + Windows OS surface).
- [ ] **ADR** capturing the two-installer model + harness + ADR-29/31/64 revisits → **drafted in §10**; promote to `docs/adr/`.

---

## 10. ADR drafts (copy-ready for `docs/adr/`)

Two decisions here need ADRs (per the process-risk banner). The drafts below are
copy-ready — promote to `docs/adr/NN-*.md`, confirm the proposed ids, and convert
the yaml block to real frontmatter. Cross-ADR references are plain text to keep the
docs link-checker green.

### 10.1 ADR draft — Two single-OS installers (all-Windows production, all-Linux test)

```yaml
topic: decisions
id: 77            # PROPOSED — next free after ADR-76; confirm at landing
title: Two single-OS installers — all-Windows production, all-Linux test
status: proposed
date_proposed: 2026-06-16
assumes: [29, 31, 64, 76]
supersedes: []
superseded_by: []
parent: Decisions
grand_parent: Explanation
```

**Context.** The shipped posture splits one environment across two OSes — Obsidian/
Zotero on Windows, Hermes in WSL2 — bridged by the Local REST API over
mirrored-networking loopback (ADR-31). That bridge needs `.wslconfig` tuning and
breaks silently; it blocks HTTPS (Hermes can't trust the cross-OS self-signed cert
— issue #527); and it forces L3/GUI testing to be manual and Windows-only (ADR-29).
It existed only because Hermes wasn't native on Windows (ADR-64, deferred) and there
was no Linux GUI stack. Both have changed.

**Decision.** Ship two single-OS installers, each an OS realization of the ADR-76
reconciling installer `install(release_root, vault_path)` — same versioned release,
same manifest, same layer-by-lifecycle reconciliation:
- **`install.ps1` — all-Windows = production.** Native Windows Hermes + Obsidian +
  Zotero, localhost only.
- **`install.sh` — all-Linux = test.** Native everything; containerizable/ephemeral
  (ADR-78).
A single `MEMORIA_ENV=test|prod` overlay extends the installer's existing
`{{PYTHON}}`/`{{VAULT_PATH}}`/`{{QMD}}` substitution with `{{MODEL_PROVIDER}}` /
`{{MODEL_BASE_URL}}` / `{{MODEL_DEFAULT}}`.

**Why.** Deletes the cross-OS bridge and its whole fragility class; co-locates REST
+ Hermes on one OS so HTTPS is trivial (closes #527); makes the test env fully
scriptable; each installer is simpler than the entangled split.

**Consequences / preconditions.**
- **Un-defers ADR-64 for production:** the all-Windows path requires native Windows
  Hermes; ADR-64's load-bearing rationale ("Hermes is WSL2-only on Windows") no
  longer holds. This ADR is in tension with the current ADR-64 deferral and must
  resolve it.
- **Revisits ADR-31:** transport is same-host localhost; HTTPS REST becomes default
  (issue #527).
- **Revisits ADR-29:** L3 moves from manual/Windows to automated headless-Linux
  (ADR-78).
- **`MEMORIA_ENV` non-goal:** the overlay flattens prod's per-profile model tiering
  — **both** Opus lanes (copi *and* peer-reviewer) go dark under test, and
  per-profile config-shape divergence is untestable locally. Absolute quality + the
  Windows-OS surface are validated on the production env.
- **New residual:** OS portability (test=Linux, prod=Windows) replaces the bridge
  residual — bounded cross-platform hygiene, checked by each installer on its own OS
  plus a production-acceptance pass.

**Alternatives.** Keep the split-OS bridge (rejected — fragility, no HTTPS, manual
L3). All-WSL2 for both (rejected — production is the PI's real Windows daily-driver;
testing wants Linux containerization).

### 10.2 ADR draft — A complete, ephemeral, containerized test environment on Linux

```yaml
topic: decisions
id: 78            # PROPOSED
title: A complete, ephemeral, containerized test environment on Linux
status: proposed
date_proposed: 2026-06-16
assumes: [11, 28, 29, 46, 76, 77]
supersedes: []
superseded_by: []
parent: Decisions
grand_parent: Explanation
```

**Context.** ADR-29 placed L3 as manual/Windows, the cross-cutting suites
(installer/recovery/security/performance) as uncovered gaps, and quality (L5)
per-release. With the all-Linux test env (ADR-77) the full stack runs headless and
scriptable, so most of that becomes automatable for the first time.

**Decision.** The all-Linux test env is a version-controlled golden image
(Dockerfile) holding the full real stack — headless Obsidian (`xvfb-run
--no-sandbox`), Zotero/fixture `.bib`, Hermes, plugins, REST/MCP, qmd — with the
local model as a `--gpus all` sibling container, recreated clean per run from
checksummed fixtures. A pytest orchestrator drives the Obsidian CLI over all 16
command-palette commands with JS assertions + screenshot golden-image diffs.
Coverage = **L0–L4 + cross-cutting + partial/mechanical L5**, all on the local
model; production owns absolute L5 + the Windows-OS surface. (Full design: §1–§8.)

**Must-resolve gates — the harness does not ship until each is resolved.**
- **G1 — prove the gate fires (safety).** The harness MUST include a **negative deny
  assertion**: a known-deny write, routed through the live ADR-28 plugin
  (`src/.memoria/plugins/memoria-policy-gate/`), must be **blocked** with a deny
  audit row. The gate-fires property is proven, never inferred. The superseded
  `re.fullmatch("obsidian.*")` shell-hook never matched the real `mcp_obsidian_*`
  names; the live plugin's substring match does — so the Option-B shim must route
  through the plugin, and the deny test is what proves it.
- **G2 — verify the model (foundation).** Confirm the local model exists and is
  text+tool-servable **before** any sizing/serving is load-bearing
  (`gemma4_unified` / any-to-any is unconfirmed). **Qwen3-MoE** is the verified
  fallback.
- **G3 — verify tool-call emission.** Confirm the serving runtime (llama.cpp
  `--jinja`) emits OpenAI-format `tool_calls` Hermes can consume; otherwise a
  parser/shim is needed — not a `base_url` swap — and the `openai-compatible` Hermes
  provider must exist and carry tool-calls.

**Why / how.** Three-bucket assertion (no-call / wrong-call / expected) so a weak
model's misbehaviour isn't misread as a wiring break (§3). Cassettes match on
tool-call structure, not prompt bytes, or they no-op on real refactors (§7). Nightly
is triggered by a Windows Task Scheduler → `wsl.exe` job, not WSL2 cron (§7).
Runtime = llama.cpp (already vended via qmd; GGUF Q4_K_M fits 16 GB; vLLM is out —
§4).

**Consequences.** Closes the L3 manual/Windows gap and the
recovery/security/performance gaps; introduces a golden image + fixtures + the
Obsidian-CLI harness as new maintained artifacts; the absolute-quality and
Windows-OS residuals stay on production (ADR-77).

**Alternatives.** The fs-shim-only smoke (ADR-29 Option B) — kept, but demoted to
the per-PR cheap tier, not the whole env. Manual Windows L3 (status quo) — rejected;
automatable now.
