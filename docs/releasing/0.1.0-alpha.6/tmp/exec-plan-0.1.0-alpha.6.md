# Exec plan — v0.1.0-alpha.6

_Living build doc (alpha.6 `tmp/`). Tracks the **how**; the prose plan
([../release-plan-0.1.0-alpha.6.md](../release-plan-0.1.0-alpha.6.md)) holds the
**what**, and gate/stage **state** lives in the `Release v0.1.0-alpha.6` issue and its
sub-issues. Delete `tmp/` at cut — promote durable decisions to ADRs first._
Date opened: 2026-06-16.

## Scope (locked recommendation)

**Track A — conformance (re-implement approved goals):** #620, #621, #624 (G1), #622
(G2), #627, #626, #585 (G3); #625 documented, not a gate.
**Track B — net-new:** #586, the ADR-80 Phase 1 harness (G4).
**Deferred to alpha.7:** #370, #611, #416, #371 (shadow/instrument harvest) — their
telemetry has no corpus to chew on until the Phase-1 harness can seed one. #521
(packaging) stays cadence-gated.

## Critical path & sequencing

- **WS-4 (harness, #586) is the long pole — start day 1, in parallel.** It is ~⅔ of the
  release's effort and gates S3/S5.
- **WS-1 #620 (security) starts first within Track A** — it is the only High-priority
  blocker and the only item that touches the live runtime.
- WS-1/2/3 are otherwise independent subsystems and parallelize freely.
- Each WS lands as its own PR off its own branch/worktree (shared-checkout rule); never
  commit to `main` directly; never touch `~/Memoria` (production) — runtime work is on
  the memoria-test sandbox only.

## Workstreams

Workstream _n_ maps 1:1 to gate G_n_.

| WS | Gate | Issues | One-line deliverable | Stage proof |
|---|---|---|---|---|
| WS-1 | G1 | #620, #621, #624 | the 3 `bug` accepted-ADR invariants hold | S1 + S4 |
| WS-2 | G2 | #622 | Project = 4th switchable workspace | S3 + S5 |
| WS-3 | G3 | #627, #626, #585 | docs/template/supply-chain conformance | S0 |
| WS-4 | G4 | #586 | model-free L0–L4 harness (ADR-80 Ph1) | S3 + S5 |

### WS-1 — Correctness & security (#620, #621, #624)

**#620 · ADR-31 — runtime serves Obsidian MCP over verified HTTPS.** The repo source is
already compliant (`src/.memoria/profiles/*/config.yaml` use `https://` + `ssl_verify:
${OBSIDIAN_MCP_SSL_VERIFY}`); the **runtime contradicts it** — all five
`~/.hermes/profiles/*/config.yaml` serve `http://127.0.0.1:${OBSIDIAN_MCP_PORT}/mcp`,
`OBSIDIAN_MCP_SSL_VERIFY` unset in `~/.hermes/.env`.
- Get Hermes to trust the plugin's exported PEM via `OBSIDIAN_MCP_SSL_VERIFY`, then flip
  the live profiles back to `https://`. Sandbox `~/.hermes` only.
- **Risk / open question:** the profiles' own comments claim "Hermes can't skip TLS
  verify for the self-signed HTTPS port." Confirm whether Hermes can be pointed at a
  trusted PEM (then this is config) or genuinely cannot (then it's an upstream-Hermes
  capability gap and #620 narrows to "track + document" — escalate early).
- **Proof:** S4 — observe the bearer token no longer on plain loopback (HTTPS handshake
  on `${OBSIDIAN_MCP_PORT}`; `ssl_verify` on).

**#621 · ADR-78 — reject a born-`current` thesis + gate promotion.** Today
`validate_frontmatter` only checks enum membership and `current` is a legal value, so a
thesis authored at `lifecycle: current` validates clean; `projects/` is absent from
`gated_prefixes` ([folders.yaml:31-33](../../../../src/.memoria/schemas/folders.yaml)),
so the policy MCP doesn't gate the promotion either.
- Enforce `initial_lifecycle: proposed` for `thesis` at schema-validation time (reject
  born-`current`).
- Review-gate the promotion to `current`.
- **Design sub-question:** gating is **type-specific, not a blanket `projects/`
  prefix** — adding `projects/` to `gated_prefixes` would also deny the deterministic
  Project-gate's own materialization writes. Gate the thesis lifecycle transition, not
  the whole folder. Settle this in the PR.
- **Proof:** S1 (rejection unit) + S4 (deny-assertion through the ADR-28 plugin).

**#624 · ADR-10 — exclude superseded claims by default.** The FAMA detector is done
(`detectors.py fama_exposure()`); the missing half is "`query`/`write` exclude
superseded claims **by default**" (nothing filters on `superseded_by`) and the promised
claim-template `schema_version` bump.
- Add the default `superseded_by` filter to the `query`/`write` paths (default-on,
  overridable).
- Bump the claim template `schema_version`.
- **Proof:** S1 — filter unit (superseded claim excluded by default, surfaced on
  opt-in).

### WS-2 — Project-gate navigation surface (#622)

`src/.obsidian/workspaces.json` registers only `Desk` / `Library` / `Studio` (verified).
The deterministic gate logic + `project-gate.{md,base}` already exist (alpha.5); only the
**surface** is missing.
- Register `Project` as the fourth switchable top-level workspace in `workspaces.json`.
- Keep the `registerBasesView` pilot deferred (ADR-77) — render through the standard
  surface.
- **Proof:** S3 (workspace switches, Bases render) + S5 (driven from Obsidian).

### WS-3 — Docs / template / supply-chain (#627, #626, #585)

**#627 · ADR-07 — `system/templates/code-note.md`.** Confirmed absent. Either create the
starter template or drop the stale "Files affected" reference in ADR-07. (Recommend
create — it's the cheaper-to-defend choice and the profile/lane wiring already exists.)
**#626 · ADR-73 — bare `(ADR-NN)` codes.** Add the Rule-2 check to `scripts/docs-doctor.py`
**or** fix the offending pages (`docs/reference/{failure-modes,system-actions,
obsidian-command-palette,obsidian-plugins}.md`). Recommend enforce-in-doctor so it can't
regress. Pre-check: `python scripts/docs-doctor.py docs`.
**#585 · ADR-74 — static provenance lock manifest.** Compute pinned version/commit +
SHA-256 + license for the 12 vendored plugins under `src/.obsidian/plugins/` and land a
static lock manifest. Updater + CI provenance-doctor stay deferred (ADR-74 multi-signal
trigger). Mechanical, zero external dep.
- **Proof:** S0 — template parses, manifest validates, `docs-doctor` green.

### WS-4 — Test-env harness Phase 1 (#586, ADR-80)

Model-free L0–L4 golden path: built on `scripts/e2e-smoke.sh` + record/replay cassettes
+ the g9 zero-LLM spine + a seeded L4 golden path. The model is needed at **record**
time, not run time; ADR-80's gates 2 (Gemma-class GGUF served by `llama-server --jinja`)
and 3 (~5-min smoke) are resolved per the cadence review.
- Build the cassette record/replay harness and the seed→cassette L4 path.
- Wire L0–L4 into `e2e-smoke.sh`; make the ADR-80 model-availability smoke check pass.
- **Phase 2 stays out** (live-model L5, visual golden-diffs, chaos/perf).
- **Proof:** S3 (cassette replay green) + S5 (golden path from a fresh clone).

## Verification mapping (WS → stage)

| Stage | WS-1 | WS-2 | WS-3 | WS-4 |
|---|---|---|---|---|
| S0 static | — | — | template/manifest/docs-doctor | — |
| S1 pytest | thesis reject, superseded filter | — | — | cassette/g9 units |
| S2 dry-run | — | workspace in installer | template in installer | cassette replay |
| S3 integration | — | workspace switch + Bases | — | L0–L4 replay |
| S4 live | HTTPS+ssl_verify; thesis deny | — | — | — |
| S5 E2E | — | Project gate from Obsidian | — | golden path fresh clone |

## GitHub setup (done)

- Milestone `0.1.0-alpha.6` (#7) assigned to #620, #621, #622, #624, #626, #627, #585,
  #586. #625 left out (upstream-Hermes-blocked known-limitation, plan §6).
- Parent [#635](https://github.com/eranroseman/memoria-vault/issues/635)
  (`Release v0.1.0-alpha.6`, label `release`) opened with gate sub-issues #636 (G1),
  #637 (G2), #638 (G3), #639 (G4) and stage sub-issues #640–#645 (S0–S5), all linked.
- **Pending:** mark #620 High priority — it is a Project field (Memoria Issue Tracker),
  not a label; set it in the board (the `gh` token lacks the `project` scope).

## Open questions

- **#620:** is the Hermes self-signed-PEM trust achievable as config, or an upstream gap?
  (Decides whether #620 is a fix or a tracked limitation — resolve before committing G1.)
- **#621:** confirm the type-specific thesis-lifecycle gate (not a blanket `projects/`
  prefix) does not regress the deterministic gate's materialization writes.
- **#626 / #627:** enforce-vs-fix and create-vs-drop — both lean to the durable option
  (enforce; create), confirm in PR.
