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

| WS | Gate | Issues | One-line deliverable | Stage proof | Status |
|---|---|---|---|---|---|
| WS-1 | G1 | #620, #621, #624 | the 3 `bug` accepted-ADR invariants hold | S1 + S4 | pending |
| WS-2 | G2 | #622 | Project = first-class gate surface inside Studio | S3 + S5 | pending |
| WS-3 | G3 | #627, #626, #585 | docs/template/supply-chain conformance | S0 | merged in [#649](https://github.com/eranroseman/memoria-vault/pull/649) |
| WS-4 | G4 | #586 | model-free L0–L4 harness (ADR-80 Ph1) | S3 + S5 | pending |

### WS-1 — Correctness & security (#620, #621, #624)

**#620 · ADR-31 — runtime serves Obsidian MCP over verified HTTPS.** The repo source is
already compliant (`src/.memoria/profiles/*/config.yaml` use `https://` + `ssl_verify:
${OBSIDIAN_MCP_SSL_VERIFY}`); the **runtime contradicts it** — all five
`~/.hermes/profiles/*/config.yaml` serve `http://127.0.0.1:${OBSIDIAN_MCP_PORT}/mcp`,
`OBSIDIAN_MCP_SSL_VERIFY` unset in `~/.hermes/.env`.
- **Resolved — source config is correct, but alpha.6 still needs durable deployment
  verification.** Hermes passes `ssl_verify` straight to httpx's
  `verify` (`~/.hermes/hermes-agent/tools/mcp_tool.py:1355,1443`), and httpx `verify`
  accepts a CA-bundle path — so the exported self-signed PEM verifies cleanly. The old
  "Hermes can't skip TLS verify" comment was wrong: Hermes doesn't skip verification, it
  verifies against the PEM.
- Steps: add installer/profile verification so a fresh deploy proves every generated
  profile uses `https://127.0.0.1:${OBSIDIAN_MCP_PORT}/mcp` and carries
  `ssl_verify: ${OBSIDIAN_MCP_SSL_VERIFY}`; then, in sandbox `~/.hermes` only, export
  the cert from the Local REST API plugin → set `OBSIDIAN_MCP_SSL_VERIFY` to its path
  in `~/.hermes/.env` → redeploy profiles from repo source. One check: the cert's
  `subjectAltName` must include `127.0.0.1` (httpx verifies hostname). Minor: if the
  installed httpx (≥0.28) rejects a string path, wrap it as
  `ssl.create_default_context(cafile=…)`.
- **Proof:** S1/S2 installer/profile tests assert HTTPS + `ssl_verify` in generated
  profiles; S4 live smoke observes the sandbox runtime over verified HTTPS and confirms
  the bearer token no longer rides plain loopback.

**#621 · ADR-78 — reject a born-`current` thesis + gate promotion.** Today
`validate_frontmatter` only checks enum membership and `current` is a legal value, so a
thesis authored at `lifecycle: current` validates clean; `projects/` is absent from
`gated_prefixes` ([folders.yaml:31-33](../../../../src/.memoria/schemas/folders.yaml)),
so the policy MCP doesn't gate the promotion either.
- **Resolved — enforce in the content-aware Linter/schema layer, NOT the policy gate.**
  The policy gate is path-based and **content-blind** (`is_review_gated` is just
  `path.startswith(prefixes)`; `check_permission` never sees the note body —
  `policy_mcp.py:101`), so it can't tell *create-proposed* from *promote-to-current*, and
  it only intercepts agent `mcp_obsidian_*` writes (it misses PI promotions typed
  directly in Obsidian). So `gated_prefixes` is the wrong tool: a `projects/` prefix would
  dry-run all `proposed`/`provisional` agent work too — which ADR-78 says to allow.
- **Born-`current` rejection:** a `thesis` detector + the pre-commit schema check reject
  a thesis at `lifecycle: current` lacking promotion provenance. `validate_frontmatter`
  is stateless, so key on a marker, not history.
- **Promotion-to-`current` gate:** the human review/promotion step writes the provenance
  stamp (e.g. `promoted_at`); `current`-without-stamp fails the Linter/pre-commit. Leaves
  `proposed`/`provisional` free. Leave `gated_prefixes` untouched for theses.
- **No regression to the deterministic gate** (open question retired):
  `structural_impact.py:743` writes `project-gate-index.md` via direct `write_text` (zero
  obsidian-MCP), so it bypasses the policy gate entirely — `gated_prefixes` can't touch
  it. (`initial_lifecycle` / `promotion_gate` / type-level `gated:` are read by nothing
  today — purely declarative.)
- **Proof:** S0/S1 (schema + Linter rejection unit) + S5 (a live PI promotion attempt is
  flagged E2E). Not the path-based ADR-28 policy plugin.

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

`src/.obsidian/workspaces.json` registers `Desk` / `Library` / `Studio` (ADR-68). Studio
and Project are two names for the same workspace: Studio is the saved workspace shell,
and Project is the bounded-inquiry gate surface opened inside it. The deterministic gate
logic + `project-gate.{md,base}` already exist (alpha.5); the missing surface is the
first-class entry point, not a fourth saved workspace.
- Keep `Desk` / `Library` / `Studio` as the saved workspace set.
- Add Home/Studio/palette entry points that open the Project gate surface
  (`system/dashboards/project-gate.md` / `project-gate.base`) inside Studio.
- Keep the `registerBasesView` pilot deferred (ADR-77) — render through the standard
  surface.
- **Proof:** S3 (Studio/Project entry points open and Bases render) + S5 (driven from
  Obsidian).

### WS-3 — Docs / template / supply-chain (#627, #626, #585)

**Status:** merged in [PR #649](https://github.com/eranroseman/memoria-vault/pull/649)
(`c79f659`). Proof: `scripts/test.sh all`, CI green, and the merged artifacts include
`src/system/templates/code-note.md`, the `code-note` schema/folder mapping,
`scripts/docs_doctor.py` bare-ADR enforcement, fixed current-doc ADR links,
`src/.obsidian/plugin-provenance-lock.json`, and
`tests/test_plugin_provenance.py`.

**#627 · ADR-07 — `system/templates/code-note.md`.** Confirmed absent. Either create the
starter template or drop the stale "Files affected" reference in ADR-07. (Recommend
create — it's the cheaper-to-defend choice and the profile/lane wiring already exists.)
**#626 · ADR-73 — bare `(ADR-NN)` codes.** Add the Rule-2 check to `scripts/docs-doctor.py`
**or** fix the offending pages (`docs/reference/{failure-modes,system-actions,
obsidian-command-palette,obsidian-plugins}.md`). Recommend enforce-in-doctor so it can't
regress. Pre-check: `python scripts/docs-doctor.py docs`.
**#585 · ADR-74 — static provenance lock manifest.** Compute pinned version/commit +
SHA-256 + license for the 12 vendored plugins under `src/.obsidian/plugins/` and land a
static lock manifest as an interim artifact. ADR-74 remains deferred; updater + CI
provenance-doctor stay recorded as later work. Mechanical, zero external dep.
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
| S1 pytest | HTTPS+ssl_verify profile assertions; thesis reject + promotion-gate, superseded filter | — | — | cassette/g9 units |
| S2 dry-run | fresh generated profiles prove HTTPS+ssl_verify | Project gate entry points in installer | template in installer | cassette replay |
| S3 integration | — | Studio/Project entry points + Bases | — | L0–L4 replay |
| S4 live | HTTPS+ssl_verify live smoke (#620) | — | — | — |
| S5 E2E | — | Project gate from Obsidian | — | golden path fresh clone |

## GitHub setup (done)

- Milestone `0.1.0-alpha.6` (#7) assigned to #620, #621, #622, #624, #626, #627, #585,
  #586. #625 left out (upstream-Hermes-blocked known-limitation, plan §6).
- Parent [#635](https://github.com/eranroseman/memoria-vault/issues/635)
  (`Release v0.1.0-alpha.6`, label `release`) opened with gate sub-issues #636 (G1),
  #637 (G2), #638 (G3), #639 (G4) and stage sub-issues #640–#645 (S0–S5), all linked.
- **Pending:** mark #620 High priority — it is a Project field (Memoria Issue Tracker),
  not a label; set it in the board (the `gh` token lacks the `project` scope).

## Resolved design decisions

- **#620 — source config is correct; deployment verification is the work.** Hermes feeds
  `ssl_verify` to httpx `verify` (`mcp_tool.py:1355,1443`), which takes a CA-bundle path →
  the exported PEM verifies. Add installer/profile tests for fresh generated profiles and
  keep S4 as the live sandbox smoke.
- **#621 — enforce in the Linter/schema layer, not the policy gate** (content-blind,
  path-based) — born-`current` rejection + a promotion-stamp gate, leaving `gated_prefixes`
  untouched. The deterministic gate bypasses the policy gate (direct `write_text`), so
  there is no materialization regression. See the WS-1 #621 entry.

## Open questions

- **#626 / #627:** enforce-vs-fix and create-vs-drop — both lean to the durable option
  (enforce; create), confirm in PR.
