# Test environment & procedure — the complete design (clean-sheet)

Status: draft (scratch under `tmp/`)
Author: PI + Claude
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
│  ├─ Hermes (native Linux)          ├─ Ollama + Gemma 4 12B             │
│  ├─ 5 memoria-* profiles + MCP     │  (--gpus all via                  │
│  ├─ Obsidian (headless: xvfb-run   │   nvidia-container-toolkit)       │
│  │   --no-sandbox) + all plugins   │  OpenAI-compatible :11434/v1      │
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
- **Persistent only where intended** — Ollama model cache on a named volume so the
  12B isn't re-pulled each run; everything else disposable.

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

**Two-stage assertion** (keeps the signal honest with a weak model): first assert
a well-formed tool call was emitted (model-capability gate → else classify a
**Gemma flake**, not a wiring regression); only then assert system state.

---

## 4. Local model — Gemma 4 12B via Ollama (containerized, GPU)

- `google/gemma-4-12B-it`, ~7–8 GB at Q4 on the 16 GB 4060 Ti.
- **Ollama** container, `--gpus all`, OpenAI-compatible at `:11434/v1`; day-0 Gemma
  4 + native tool-calling (llama.cpp = perf/MCP alt; vLLM only if concurrent lanes
  saturate). Model cache on a named volume.
- **⚠️ Verify Gemma 4 tool-calling against the model card** — load-bearing for the
  whole CLI driver.
- **Model overlay:** `base_url` is a literal duplicated across all five profiles
  (Hermes has no global config layer — ADR-27). The installer already substitutes
  `{{PYTHON}}`/`{{VAULT_PATH}}`/`{{QMD}}`; add `{{MODEL_BASE_URL}}` +
  `{{MODEL_DEFAULT}}` so `install.sh` points at Ollama and `install.ps1` at
  Kilocode. Non-goal recorded: the overlay flattens prod's Opus/Sonnet/Haiku
  tiering to one Gemma, so tier-dependent reasoning depth is out of scope locally.

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
| **Per-PR** | L2b fs-shim smoke + record/replay cassettes (model id+quant pinned) | base container, no live model | minutes, free, deterministic |
| **Nightly** | full ephemeral stack: L2b real + L3 + L4 + chaos + partial L5, all 16 commands on Gemma, screenshot diffs | compose stack + GPU | tens of min, free |
| **Per-release** | performance/scale + security/adversarial + full L3 matrix | compose stack + GPU | longer |
| **Per-release (prod)** | **production acceptance** on all-Windows: absolute L5 quality (real models), Windows installer + native-OS runtime, HTTPS REST | Windows box | manual/attended |

Disciplines (carry ADR-29's keystones): the **coverage matrix** stays the index of
component → layer → automated? → gate; **drift control** (`check-test-refs`) keeps
plans honest; **determinism** — below L5 assert artifact shape + gate decision,
never prose.

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
- [ ] **Verify Gemma 4 tool-calling against the model card** (gates the driver).
- [ ] Author `install.sh` (all-Linux): Obsidian + Zotero + Xvfb + Hermes + plugins + MCP venv + qmd + `{{MODEL_*}}`.
- [ ] Author `install.ps1` (all-Windows, native): Hermes + Obsidian + Zotero, localhost, HTTPS REST.
- [ ] Build the **golden image** (Dockerfile) + `docker compose` (stack + Ollama/GPU); pin & hash.
- [ ] Wire the **Obsidian CLI** driver over the 16 commands; add JS asserts + screenshot golden diffs.
- [ ] Build **fixture data** (scaled vaults, `.bib`, seeded states, golden screenshots), checksummed + idempotent seed.
- [ ] Author the **chaos**, **security**, and **performance** suites (§6).
- [ ] Keep **fs-shim smoke** + **record/replay** as the per-PR cheap tiers.
- [ ] Define the **production-acceptance** pass (absolute L5 + Windows OS surface).
- [ ] **ADR** capturing the two-installer model + harness + ADR-29/31/64 revisits.
