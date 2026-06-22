---
release: v0.1.0-alpha.10
status: complete     # draft | candidate | complete | released
released: false      # machine cut-flag; true ONLY for a formal tagged release
title: Release plan -- v0.1.0-alpha.10
parent: Releasing
nav_order: 2
---

# Release plan -- v0.1.0-alpha.10

**Current status: complete internal checkpoint.** alpha.10 began as a carryover
checkpoint for
[#859](https://github.com/eranroseman/memoria-vault/issues/859) and the in-place
Hermes 0.17 upgrade. The upgrade landed on 2026-06-22 (0.14 -> 0.17; contract
doctor and cost doctor pass) and a reconciled 0.17 feature evaluation confirmed
which cleanup items are feasible on this install. #859 is closed with the
baseline disposition: observed usage kept only low-risk Hermes hygiene in
alpha.10 and deferred memory machinery/pilots. G2/S1 are closed after launching
Obsidian against `~/Memoria-test`, refreshing the exported Local REST API cert,
syncing the test-vault API key into the installed Memoria profiles, and passing
the CoPI/Writer Obsidian MCP smokes. It is not a formal release: no
release-please PR, no tag, and no GitHub Release.

## 1. Scope -- what this release is

alpha.10 is the Hermes 0.17 upgrade checkpoint plus the completed #859
measurement gate. Known scope:

- Finished the Hermes 0.17 upgrade acceptance: profile redeploy, live direct-tool
  deny, doctors, and CoPI/Writer Obsidian/MCP smokes pass.
- #859 baseline is filled; scope/defer/kill disposition is recorded.
- Landed Hermes hygiene kept by #859: config migration to the v0.17 schema,
  positive `platform_toolsets`, cheap auxiliary slots, and per-lane
  `reasoning_effort`.

Pilots, not committed scope: `post_llm_call` cost-capture relocation (ADR-106),
Bitwarden shared secrets, `gateway.multiplex_profiles` in `Memoria-test`, and
`hermes security audit` in release validation. The #859 baseline did not justify
the NLI/MaxSAT contradiction engine, the warrant checker, or any new memory
machinery for alpha.10.

## 2. Definition of done -- gates

v0.1.0-alpha.10 ships when every gate issue under the release parent
[#875](https://github.com/eranroseman/memoria-vault/issues/875) is closed.

| Gate | Proves | Verified by | Issue |
| --- | --- | --- | --- |
| G1 | #859 baseline filled; scope/defer/kill recorded per candidate. | S0 + issue evidence | [#876](https://github.com/eranroseman/memoria-vault/issues/876) |
| G2 | Hermes 0.17 upgrade acceptance complete (redeploy + live deny + MCP smoke). | S1 runtime evidence | [#877](https://github.com/eranroseman/memoria-vault/issues/877) |
| G3 | Confirmed Hermes hygiene landed for items G1 keeps (config migration, positive `platform_toolsets`, auxiliary slots, `reasoning_effort`). | S1 + deny-path tests | [#878](https://github.com/eranroseman/memoria-vault/issues/878) |
| G4 | Cost-capture decision recorded; Bitwarden/multiplex/security-audit pilots resolved for items G1 keeps. | S1 test-vault evidence | [#879](https://github.com/eranroseman/memoria-vault/issues/879) |

## 3. Validation -- stages

| Stage | Proves |
| --- | --- |
| S0 | `static-contract`: release docs, links, spelling, status, and test-ref checks are clean. |
| S1 | `runtime`: profiles redeploy to `~/Memoria-test`, contract/cost doctors pass, one direct-tool deny and one Obsidian/MCP smoke pass succeed; deny-path tests confirm `platform_toolsets` closure. |

## 4. Blockers

Not enumerated here. By definition the blockers are any open gate/stage
sub-issue, plus any open High-priority blocker in the
[Memoria Issue Tracker](https://github.com/users/eranroseman/projects/1).

## 5. Out of scope (later)

- Full NLI/decomposed-gate/MaxSAT contradiction automation and the model-free
  warrant checker remain out of scope; #859 did not show missed contradictions
  or bad warrants as an alpha.10 bottleneck.
- Hermes cleanup beyond the confirmed-feasible hygiene above stays out of scope
  unless a later issue selects the item. The Bitwarden, gateway-multiplex, and
  cost-hook items remain later pilots; promoting them to production is a separate
  decision, not part of this checkpoint.
- OpenRouter `provider_routing` and external memory providers stay excluded; Kilo
  remains the production provider.

## 6. Known limitations

- Limitation: alpha.10 is an internal checkpoint, not a formal tagged release.
  Impact: there is no release artifact. Workaround: use the closed release parent
  [#875](https://github.com/eranroseman/memoria-vault/issues/875) and gate/stage
  issues as the durable readiness record.

## 7. Documentation integrity

Before the checkpoint is approved, run the standard docs sweep: `docs_doctor`,
`status_doctor`, `check_test_refs`, cspell, and a manual scan for changed behavior.

## 8. Runtime readiness

Runtime evidence is required for the Hermes 0.17 upgrade acceptance (G2) and any
hygiene/pilot work that changes installed behavior (G3/G4): profile redeploy,
contract/cost doctors, `platform_toolsets` deny-path tests, one live direct-tool
deny, and one Obsidian/MCP smoke pass. All runtime work uses `~/Memoria-test`;
never test against the production vault `~/Memoria`. Local `provider: custom` /
`qwen2.5:7b` output is test-vault evidence — production runs Kilo.

## 9. Release close-out sweep

Scratch disposition is complete: durable findings were folded into ADRs/docs and
GitHub issues, and completed `tmp/` files were removed.

## 10. Cut procedure

1. Gate and stage issues under the release parent are closed.
2. Documentation and runtime readiness checks for scoped work are complete.
3. No tag or GitHub Release is cut for this internal checkpoint.
4. This plan remains `status: complete`, `released: false`.

## 11. Roadmap after this release

| Phase | When | Goal |
| --- | --- | --- |
| Measurement-led memory work | Later evidence cycle | Reconsider only when logs show contradiction, retrieval, ingest, or supervision attribution as the bottleneck. |
| Hermes cleanup | Later issue | Pick only the cleanup item that pays for itself. |
