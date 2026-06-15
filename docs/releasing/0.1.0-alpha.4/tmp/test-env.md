# Test environment design — WSL2 process-testing env

Status: draft (scratch under `tmp/`)
Author: PI + Claude
Context: stand up a fully separate **test** environment (WSL2) alongside the
**production** environment (Windows). The test env validates **system processes,
not work quality**; quality is validated only on production.

---

## 1. Guiding principle — separate by *what uses the model*

A weaker/cheaper model changes agent *behaviour*: small wording differences
compound across a multi-step lane until tool calls diverge. So a local model can
prove the **plumbing works** (profiles load, MCP servers respond, the write-gate
fires, a lifecycle completes) but **cannot** prove the production agent makes the
same decisions. That is acceptable, because most of Memoria isn't the LLM.

This maps onto the existing **ADR-29** L0–L5 pyramid. Two clarifications about
provenance, since this doc elsewhere insists on not over-claiming ADR-29:
- ADR-29's headline **table has a single L2** ("per release, cheap model,
  disposable vault"). The **L2a / L2b split at the model boundary** (L2a hermetic
  = no model; L2b runtime-bound = cheap model) comes from ADR-29's **L2
  implementation note**, not the table — but it *is* ADR-29's own framing.
- What this doc **refines** is the *placement*: ADR-29 says "cheap model,
  disposable vault" without naming an environment; assigning L2b to **the WSL2
  local-Gemma env** is this doc's decision, not ADR-29's.

Net: L0–L2a are model-free, L3 is Windows/GUI, L5 is the real model.

| Layer | What runs | Uses a model? | Where | Cadence |
|---|---|---|---|---|
| L0 Static & schema | 5 CI checks + schema-drift | No | CI | per commit |
| L1 Component | `pytest tests/`: engines (ingest, clustering, linter/detectors, sweeps), board, metrics, MCP units | No | CI | per commit |
| L2a Policy-gate contract | allow/deny/dry_run per lane (`policy_mcp.py`) | No | CI | per commit |
| **L2b Agent wiring** | profile dispatch → live gate → artifact, via Option-B fs shim | **local Gemma 4 12B** | **WSL2 test env** | nightly smoke + per release |
| **L2b-extended** | full-lifecycle Option-B trace (multi-lane, GUI/REST excluded) | **local Gemma 4 12B** | **WSL2 test env** | per release |
| L3 System integration | Obsidian plugins, REST bridge, dashboards render, Zotero→bib, ACP | n/a (GUI runtime) | **Windows, attended** | per release |
| L4 Golden-path E2E | the cross-layer trace with the real REST/GUI path | prod model | **Windows** | per release |
| L5 Quality / eval | agent *output* quality (gold tasks, scored) | Claude via Kilocode | **Windows production** | per release / model swap |

> **Framing (corrected):** the **WSL2 test env runs L2b + an extended L2b
> full-lifecycle trace against local Gemma 4 12B.** L0–L2a run **model-free in
> CI**. **L3 (GUI/plugins/dashboards/Zotero), the true L4 golden-path, and L5
> (quality) stay on Windows** per ADR-29 — WSL2 does not replace them.

The deterministic engines and the policy gate — the riskiest, most
safety-critical code — are tested with **no model at all**, free and
reproducibly, in CI. The local model only carries L2b and its extended trace, the
layers that are expensive to run against Claude repeatedly.

### Why this is "extended L2b," not "headless L4"

ADR-29 defines a **single** L4 — "one full-lifecycle trace across **all** layers"
— whose entire point is the cross-layer integration (real REST bridge, plugins,
dashboards). A WSL2 run that excludes the GUI/REST path is **not** that. Calling
it "headless L4" would repeat exactly the L3 overclaim corrected above, relabeled:
"golden-path passed on WSL2" would read as L4-green when the integration L4 exists
to prove was excluded. So this doc scopes the WSL2 full-lifecycle run as
**extended L2b** — a multi-lane Option-B trace — and reserves the **L4** label for
the Windows run on the real REST/GUI path. (If a first-class headless sub-layer is
ever wanted, the `MEMORIA_ENV` ADR is where it must be *defined* as an extension
of ADR-29 — this doc does not assert ADR-29 already sanctions it.)

### Why L3 is *not* moved onto WSL2

ADR-29's L2 implementation note is explicit: its **Option A** (headless Obsidian,
`xvfb-run`) is "heavy/flaky and overlaps L3 #15, so it doesn't gate L2b," and L3
itself is a **Windows, per-release** layer. So this design deliberately **does
not** push L3 onto WSL2. WSL2 automation scope = **L2b (Option-B shim, no
Obsidian) + the extended-L2b full-lifecycle trace**. The
real REST bridge, plugin and dashboard rendering, and Zotero→bib remain an
**attended Windows step** — runnable against the *test* vault (a Windows Obsidian
instance pointed at the WSL2 vault path) when you want to exercise the test env's
data, but still GUI-bound and not part of the cheap WSL2 loop.

---

## 2. Model — local Gemma 4 12B

> **Decision note:** this **supersedes** the prior test-env model decision
> (Haiku-via-Kilocode as default, Qwen3-MoE as the offline upgrade). The
> `MEMORIA_ENV` ADR must record the override explicitly.

- **Why Gemma 4 12B:** `google/gemma-4-12B-it` (a `gemma4_unified` any-to-any
  multimodal model, ~12B params — not a plain dense text model, though the sizing
  math is unchanged). Runs natively on the test box's **RTX 4060 Ti 16 GB**
  (~7–8 GB at Q4_K_M, no MoE / no CPU-offload tuning), leaving headroom for KV
  cache on the longer Librarian lanes.
- **⚠️ To verify before this becomes load-bearing:** the claim that Gemma 4 has
  **native function calling via dedicated special tokens** mapping onto MCP — and
  that it fixed the old Gemma tool-calling weakness — is from secondary blog
  sources, **not** the model card. Confirm against the official Gemma 4 model card
  before committing the L2b harness to it; the entire L2b path depends on Gemma
  reliably emitting well-formed tool calls.
- **Serving:** run under **vLLM** with the OpenAI-compatible endpoint at
  `http://127.0.0.1:8000/v1`.
  - **Caveat — tool calling isn't zero-config.** vLLM needs
    `--enable-auto-tool-choice`, a Gemma-compatible `--tool-call-parser`, and the
    matching chat template so Gemma's special tokens surface as OpenAI-style tool
    calls. *Once that's configured*, Hermes' MCP wiring is unchanged — only the
    model endpoint differs.
- **Cost:** zero tokens, fully offline.
- **Accepted tradeoff:** Gemma diverges from the prod Opus/Sonnet traces, but
  divergence only matters for quality (L5), which stays on Windows.

### WSL2 GPU notes
- GPU passthrough is automatic via the Windows NVIDIA driver. **Do not install a
  Linux NVIDIA driver inside WSL2** — it breaks the `/usr/lib/wsl/lib/`
  passthrough. CUDA libraries are exposed automatically.
- Set memory limit + `sparseVhd=true` in `.wslconfig`.
- Inference runs within ~5% of native Windows.

### GPU contention — how unattended smoke still gets a model
The GPU serves only the test env, so "busy" almost always means *a test run is
already in progress*. Resolution: **serialize model jobs** — the nightly
Option-B smoke (§5) takes the GPU when free; record/replay (§5.3) covers
PR-time regression but is **not** a substitute for the live smoke (it can only
replay already-recorded traces, never carry a new unattended run). If GPU
contention ever proves real, the parked alternative is a cheap **cloud fallback**
for unattended smoke only — deliberately out of scope here per the Gemma-only
decision, but this is where it would plug in.

---

## 3. One-knob environment switch

All five profiles today **hardcode the same literal** `base_url:
https://api.kilo.ai/api/gateway` (verified across
`memoria-{copi,librarian,writer,peer-reviewer,engineer}/config.yaml`). It's a
**duplicated config field, not a variable** — so switching the test env to the
local endpoint is **five hand-edits** today.

**Proposed:** collapse those five duplicated literals into **one
environment-level overlay**. A single switch — `MEMORIA_ENV=test|prod` (or a
`model-overrides.<env>.yaml`) — rewrites `provider` / `base_url` / `default`
across all five profiles at deploy time in `scripts/install.sh`. Test vs prod
then differ by exactly one variable instead of five edits.

```yaml
# test overlay
model:
  provider: openai-compatible
  base_url: http://127.0.0.1:8000/v1   # local Gemma 4 via vLLM
  default: gemma-4-12b
```

**The overlay deliberately erases prod model tiering.** The five profiles today
carry **different** `default`s (Opus / Sonnet / Haiku per ADR-48 cost-tiering).
The test overlay collapses all five to one `gemma-4-12b` — correct for a
single-GPU local env, but it means the overlay must override **each profile's
`default`, not just `base_url`**, and that **L2b cannot exercise anything that
depends on tier differences** (e.g. a lane assuming Opus-depth reasoning). That's
acceptable — L2b tests wiring, not reasoning depth — but the ADR should state it
as an explicit non-goal so nobody reads green L2b as "the Opus lanes work."

Given the ADR-only decision model, this warrants a short ADR (it also ties to the
deferred ADR-76 wheel work).

---

## 4. Isolation matrix — "completely separate" everything

The coexistence primitives already exist (per-vault `OBSIDIAN_MCP_PORT`, per-vault
Hermes home; ADR-31, ADR-63).

| Resource | Test (WSL2) | Production (Windows) |
|---|---|---|
| Vault | `Memoria-test` (ext4) | `memoria-private` |
| Hermes home | `~/.hermes-test` | native `~/.hermes` |
| Obsidian REST/MCP port | `27125` (skips `27124`) | `27123` |
| Obsidian instance | for attended L3 only: a Windows instance pointed at the WSL2 test vault | normal install |
| Model | local Gemma 4 12B (vLLM) | Claude Opus/Sonnet mix |
| Zotero | separate data dir (`zotero -datadir`) or a tiny fixture library | real library |
| Keys | test `.env` (dummy/cheap) | production `.env` |

- **Port choice (this doc's proposal, not pre-existing):** `27123`/`27125` are
  **assigned here** — ADR-31 does not define them; it only uses
  `${OBSIDIAN_MCP_PORT}` as a free variable. What ADR-31 *does* record is that
  `27124` was the **old uvx hardwired port**. Separately, `27124` is the Local
  REST API **plugin's** default HTTPS port (a plugin fact, not an ADR-31 fact). So
  test deliberately uses `27125` to skip `27124` and avoid a future collision;
  prod takes `27123`.
- **Obsidian on the test side:** the cheap WSL2 loop (L2b + extended L2b) uses the
  Option-B **filesystem shim** and needs **no Obsidian at all**. A real Obsidian
  instance is only needed for the attended L3 pass, which runs on Windows against
  the test vault path — consistent with ADR-29 keeping L3 on Windows.
- **Caveat — the attended-L3 path crosses the WSL2↔Windows boundary.** A Windows
  Obsidian reading the ext4 test vault over `\\wsl$` (9P) hits known file-watcher
  latency/locking quirks — Obsidian's live watcher can lag or miss external
  writes, which will bite during a release L3 run. Mitigation: for the L3 pass,
  **copy the test vault to a Windows-native path** (or `git clone` it locally) and
  open *that*, rather than live-watching it over 9P.

Two REST servers on different ports is exactly what ADR-31's coexistence model
was designed for — low risk.

---

## 5. How to conduct the tests — aligned to ADR-29's L2 implementation note

This does **not** introduce a parallel plan; it reuses the L2b harness ADR-29's
**L2 implementation note (Option B)** already resolved. (The `§3 S1–S5` / `§4
matrix` references below point to the external **hermes-cli test plan**, not to
sections of ADR-29.)

1. **Deterministic floor in CI (no model).** L0 + L1 + L2a via the existing
   `pytest tests/` suite. This is the real safety net and costs nothing — the
   engines and the policy-gate allow/deny contract live here.

2. **L2b on the WSL2 env (Gemma 4) — ADR-29's Option-B harness.** Driver =
   `hermes chat -q` (tool calls visible in the transcript); backend = the
   **filesystem-backed `obsidian` MCP shim** (same tool names
   `obsidian_append_content`/`patch_content`/`put_content`), so skills call the
   same tools, the **real gate fires**, writes land on disk, no GUI. **Assert
   artifact shape / placement / audit row, never prose** (ADR-29 Discipline 2).
   Follow ADR-29's **split**: build the **unattended** smoke core (§3 S1–S5 + one
   §4 case per profile) as `scripts/test-l2.sh`, run **nightly, not
   PR-blocking**; keep the **full §4 matrix attended, per release**.
   - **"Nightly" trigger (decide, don't leave aspirational):** the WSL2 box is
     not CI. Default = a **cron job on the WSL2 host** that warms vLLM, runs
     `scripts/test-l2.sh`, and tears down the disposable vault; alternative = a
     **self-hosted GitHub runner** on the box if you want the result surfaced as
     a check. Pin this in the `MEMORIA_ENV` ADR / setup.
   - **Two-stage assertion (or nightly red gets ignored):** with a weak model, a
     failure is ambiguous — did the wiring break, or did Gemma just fail to emit a
     well-formed tool call? Assert in order: **(1)** the transcript contains a
     tool call at all (model-capability gate) → if absent, classify as a **model
     flake**, not a wiring regression; **(2)** *only then* assert the artifact
     shape / placement / gate decision / audit row. Without stage 1, capability
     flakes masquerade as wiring failures and the nightly signal goes noisy and
     ignored.
   - **Shim tool-name reconciliation (for the implementer):** the gate keys by
     **substring** — `policy_hook.classify` (in `src/.memoria/mcp/policy_hook.py`)
     fires when `"obsidian"` *and* a `WRITE_KEYWORDS` token
     (`append`/`patch`/`put`/`create`/`write`/`delete`/`rename`/`move`) both
     appear in the lowercased tool name. So prefixing is irrelevant — the
     divergent forms in the ADRs (`obsidian_obsidian_append_content`,
     `obsidian__patch_content`, `obsidian_append_content`) all classify the same.
     The real constraint is the **other** direction: register the shim under the
     **exact names the Memoria skills actually call** so the calls dispatch to it
     — confirm against the skills' emitted tool names, not ADR shorthand. As long
     as those names contain `obsidian` + a write keyword, the gate fires unchanged.

3. **Record/replay for cheap deterministic regression (PR-time).** Record each
   model+tool exchange once (VCR-style cassette), replay in CI with network
   blocked — regression-tests agent *traces* without a live model. Catches "a
   refactor broke the MCP wiring." Complements the nightly live smoke; does not
   replace it (see §2 GPU-contention note).
   - **Cassettes are Gemma-version-bound.** They're recorded against a specific
     Gemma 4 build + quant, so any model/quant bump silently invalidates them and
     CI would replay dead traces. Pin the model id+quant in cassette metadata and
     **re-record on any test-model change** — make the model bump the explicit
     refresh trigger, ideally enforced (fail replay if the recorded model id ≠ the
     configured one).

4. **Extended L2b on WSL2 (Gemma 4).** One multi-lane full-lifecycle trace
   through the Option-B backend, asserting artifact/gate/audit invariants
   end-to-end — **GUI/REST excluded**. This is *not* L4: the true cross-layer
   L4 (real REST/GUI path) runs on Windows (see §1).

5. **Quality + final acceptance on Windows production (real model).** L3
   (attended GUI) + the true L4 golden-path + L5 scored eval (`system/eval/` gold tasks, ADR-11)
   + a production smoke of the golden path. **Do not skip** — a green WSL2 run
   does not prove the production agent makes the same tool-call sequence. The
   local env de-risks the plumbing so production runs are rare and
   quality-focused.

---

## 6. Next steps

- [ ] ADR for the `MEMORIA_ENV` model overlay (five duplicated literals → one switch); also the place to **define "extended L2b"** as a named extension of ADR-29 if we want it first-class, and to pin the nightly trigger.
- [ ] `scripts/install.sh` change to apply the overlay across the five profiles.
- [ ] **Verify Gemma 4 tool-calling against the official model card** (load-bearing for the whole L2b harness — see §2 ⚠️).
- [ ] **Verify the installed vLLM version ships a Gemma-compatible `--tool-call-parser`** (may lag for a brand-new model).
- [ ] vLLM + Gemma 4 12B serving setup on the WSL2 box (incl. tool-call parser + chat template).
- [ ] Decide the **nightly trigger**: WSL2-host cron vs self-hosted GitHub runner.
- [ ] Build the Option-B fs shim — reconcile tool names against the **skills' emitted names** + the gate's substring match (not ADR shorthand).
- [ ] Wire the Gemma endpoint into ADR-29's `scripts/test-l2.sh` Option-B smoke.
- [ ] Record/replay cassette harness for PR-time regression — pin model id+quant, enforce re-record on model bump.
