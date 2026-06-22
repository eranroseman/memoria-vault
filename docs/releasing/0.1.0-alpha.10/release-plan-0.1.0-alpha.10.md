---
release: v0.1.0-alpha.10
status: draft        # draft | candidate | complete | released
released: false      # machine cut-flag; true ONLY for a formal tagged release
title: Release plan -- v0.1.0-alpha.10
parent: Releasing
nav_order: 2
---

# Release plan -- v0.1.0-alpha.10

**Current status: draft internal checkpoint.** alpha.10 began as a carryover
checkpoint for
[#859](https://github.com/eranroseman/memoria-vault/issues/859) and is now shaping
around the in-place Hermes 0.17 upgrade. The upgrade landed on 2026-06-22 (0.14
-> 0.17; contract doctor and cost doctor pass) and a reconciled 0.17 feature
evaluation confirmed which cleanup items are feasible on this install. #859
remains the evidence gate: observed usage decides which memory/cleanup work, if
any, is worth doing now. Temporary carryover and the ExecPlan live in
[`tmp/`](tmp/). It is not a formal release: no release-please PR, no tag, and no
GitHub Release.

## 1. Scope -- what this release is

alpha.10 is the Hermes 0.17 upgrade checkpoint plus the #859 measurement gate.
Known scope:

- Finish the Hermes 0.17 upgrade acceptance (profile redeploy, one live
  direct-tool deny, one Obsidian/MCP smoke pass — the doctors already pass).
- Fill the #859 baseline and record a scope/defer/kill decision per candidate.
- Land only Hermes hygiene the reconciled eval confirmed feasible on-box and that
  #859 keeps: config migration to the v0.17 schema (remove stale `ollama`),
  positive `enabled_toolsets`, cheap auxiliary slots, and per-lane
  `reasoning_effort`.

Pilots, not committed scope: `post_llm_call` cost-capture relocation (ADR-106),
Bitwarden shared secrets, `gateway.multiplex_profiles` in `Memoria-test`, and
`hermes security audit` in release validation. Do not add the NLI/MaxSAT
contradiction engine, the warrant checker, or any new memory machinery until
#859 shows it pays.

## 2. Definition of done -- gates

v0.1.0-alpha.10 ships when every gate sub-issue under the release parent issue is
closed. Create the parent and gates when scope is shaped.

| Gate | Proves | Verified by | Issue |
| --- | --- | --- | --- |
| G1 | #859 baseline filled; scope/defer/kill recorded per candidate. | S0 + issue evidence | — |
| G2 | Hermes 0.17 upgrade acceptance complete (redeploy + live deny + MCP smoke). | S1 runtime evidence | — |
| G3 | Confirmed Hermes hygiene landed for items G1 keeps (config migration, `enabled_toolsets`, auxiliary slots, `reasoning_effort`). | S1 + deny-path tests | — |
| G4 | Cost-capture decision recorded; Bitwarden/multiplex/security-audit pilots resolved for items G1 keeps. | S1 test-vault evidence | — |

## 3. Validation -- stages

| Stage | Proves |
| --- | --- |
| S0 | `static-contract`: release docs, links, spelling, status, and test-ref checks are clean. |
| S1 | `runtime`: profiles redeploy to `~/Memoria-test`, contract/cost doctors pass, one direct-tool deny and one Obsidian/MCP smoke pass succeed; deny-path tests confirm `enabled_toolsets` closure. |

## 4. Blockers

Not enumerated here. By definition the blockers are any open gate/stage
sub-issue, plus any open High-priority blocker in the
[Memoria Issue Tracker](https://github.com/users/eranroseman/projects/1).

## 5. Out of scope (later)

- Full NLI/decomposed-gate/MaxSAT contradiction automation and the model-free
  warrant checker remain out of scope unless #859 proves missed contradictions or
  bad warrants are a real bottleneck.
- Hermes cleanup beyond the confirmed-feasible hygiene above stays out of scope
  unless #859 selects the item and assigns it to alpha.10. The Bitwarden,
  gateway-multiplex, and cost-hook items are test-vault pilots; promoting them to
  production is a separate decision, not part of this checkpoint.
- OpenRouter `provider_routing` and external memory providers stay excluded; Kilo
  remains the production provider.

## 6. Known limitations

- Limitation: alpha.10 is a draft internal checkpoint. Impact: there is no release
  artifact or frozen scope yet. Workaround: use #859 and future release issues as
  the live state. Tracking:
  [#859](https://github.com/eranroseman/memoria-vault/issues/859).

## 7. Documentation integrity

Before the checkpoint is approved, run the standard docs sweep: `docs_doctor`,
`status_doctor`, `check_test_refs`, cspell, and a manual scan for changed behavior.

## 8. Runtime readiness

Runtime evidence is required for the Hermes 0.17 upgrade acceptance (G2) and any
hygiene/pilot work that changes installed behavior (G3/G4): profile redeploy,
contract/cost doctors, `enabled_toolsets` deny-path tests, one live direct-tool
deny, and one Obsidian/MCP smoke pass. All runtime work uses `~/Memoria-test`;
never test against the production vault `~/Memoria`. Local `provider: custom` /
`qwen2.5:7b` output is test-vault evidence — production runs Kilo.

## 9. Release close-out sweep

Before closeout, move unfinished scratch forward, fold durable findings into
ADRs/docs/issues, and delete completed `tmp/` files only after disposition.

## 10. Cut procedure

1. Close every gate and stage issue under the release parent.
2. Complete documentation and runtime readiness checks for scoped work.
3. Do not cut a tag or GitHub Release for this internal checkpoint.
4. Set this plan to `status: complete`, `released: false`.

## 11. Roadmap after this release

| Phase | When | Goal |
| --- | --- | --- |
| Measurement-led memory work | After #859 baseline | Decide whether contradiction, retrieval, ingest, or supervision attribution is the next bottleneck. |
| Hermes cleanup | After #859 triage | Pick only the cleanup item that pays for itself. |

## 12. Appendix

Temporary carryover notes, the reconciled Hermes 0.17 evaluation, the ExecPlan
(`tmp/execplan-alpha10.md`), and smoke probes live in [`tmp/`](tmp/) until
alpha.10 closeout.
