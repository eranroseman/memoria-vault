---
topic: tests
title: Test coverage matrix
status: draft
parent: Testing
nav_order: 10
---

# Test coverage matrix

Every design component → the behavior/layer/plan that covers it → whether it's automated → status. This is the keystone of the [testing framework](../adr/29-testing-framework.md): if a surface isn't a row here, it isn't tracked. Update it whenever a component or plan changes.

Memoria's process promotes evidence through five gates:

| Gate | Behaviors in this matrix |
| --- | --- |
| Source | `static-contract`, `component` |
| Package | `vault-assembly`, `workflow-replay` |
| Runtime | live Hermes/MCP/service boundary checks |
| Product | golden workflows, evals, GUI/Bases/dashboard rendering, telemetry |
| Release | S0-S5 plus G-gate cut evidence |

**Behavior names** are the reader-facing contract; historical layers remain aliases:
`static-contract` = L0, `component` = L1, `vault-assembly` = installer-equivalent
smoke, `workflow-replay` = ADR-80 Phase 1 model-free L2-L4 replay,
`runtime-integration` = L3 live runtime/GUI, and `release-acceptance` = S0-S5 +
G-gate evidence. `scripts/verify` is the front door over the automated gates:
`pr` runs Source, `package` runs Source+Package, `runtime` and `rc` run the
automated Runtime prefix, and `live` runs only the live runtime smoke.
`scripts/test-l2.sh` is the opt-in live Hermes L2 smoke: it is
manual/nightly, not a required PR gate, and defaults to a deterministic local
OpenAI-compatible smoke endpoint while allowing a real local model override. L5
output quality remains the eval layer, and X marks cross-cutting surfaces that
still need a named plan.

**Status:** ✅ covered · 🟡 partial · ⛔ gap (no coverage yet).

| # | Component | Behavior / layer | Plan / where | Automated | Status |
| --- | --- | --- | --- | --- | --- |
| 1 | Python tooling — policy gate, hook, board export, metrics, detectors | `component` / L1 | [headless](plans/headless-test-plan.md) §A (`pytest tests/`) · `python-selftest` CI | ✅ | ✅ |
| 2 | docs/ integrity — links, anchors, page-title text, frontmatter keys | `static-contract` / L0 | headless §B (`docs-doctor`) · CI | ✅ | ✅ |
| 3 | vault→site links + wikilink resolution | `static-contract` / L0 | headless §B (`check-vault-links`) · CI | ✅ | ✅ |
| 4 | Installer **lint** (shellcheck, PSScriptAnalyzer) | `static-contract` / L0 | headless §C · `lint-installers` CI | ✅ | ✅ |
| 5 | Dashboard/schema + design-system drift | `static-contract` / L0 | headless §D · `detectors --vault --gate dashboard-field-drift,design-system-drift` gated in `python-selftest` CI; §D2 non-note audit manual | ✅ drift / 🟡 D2 | ✅ |
| 6 | 5 profiles — every documented CLI command | L2 | [hermes-cli](plans/hermes-cli-test-plan.md) §4 | manual | ✅ |
| 7 | Policy gate — deny path, per-lane write scope, 8 actions, **direct/egress capability completeness** | L1+L2 | headless §A1 (all lanes' write-walls covered by pytest, [#73](https://github.com/eranroseman/memoria-vault/pull/73)) · `test_policy_gate_completeness.py` (sweep over every `DENY_DIRECT_TOOLS` name) · `hermes_contract_doctor.py` (denylist drift vs *installed* Hermes plus deployed `policy_hook.py` freshness; runbook S4) · hermes-cli §5 (live invariants X4) | semi | ✅ |
| 8 | Review gate (ADR-27) — dry_run degradation, dispatch precondition | L2 | hermes-cli §4 (W4), §5 (X3), §4.8 (B12) | manual | ✅ |
| 9 | Audit pairing — `before_hash`/`after_hash`, `audit-unpaired-writes` | L1+L2 | headless §A · hermes-cli §5 (X4) | semi | ✅ |
| 10 | Board / Kanban — create…archive, dispatch, transitions | L2 | hermes-cli §4.8 | manual | ✅ |
| 11 | Profile mgmt, skills, cron | L2 | hermes-cli §4.9–4.11 | manual | ✅ |
| 12 | 19 templates — frontmatter keys; QuickAdd instantiation | L0+L3 | headless §A5/§D · [GUI](plans/gui-test-plan.md) A3 (QuickAdd) | semi | 🟡 (instantiation only spot-checked) |
| 13 | 5 system dashboards — queries *render* on real data | L3 | GUI Part C | manual | ✅ |
| 14 | 13 Obsidian plugins load + enabled | L3 | GUI Part A | manual | ✅ |
| 15 | Local REST API bridge (write-gate lifeline) | L3 | GUI Part B | manual | ✅ |
| 16 | Zotero + Better BibTeX → `memoria.bib` | L3 | GUI Part D | manual | ✅ |
| 17 | Agent Client pane (model connectivity through GUI) | L3 | GUI Part E1 | manual | ✅ |
| 18 | **Installer end-to-end** — clean install, `{{VAULT_PATH}}`, `.env` seed, plugin copy, profile register, idempotency, bootstrap apps, flags, WSL2↔Windows | `vault-assembly` + `release-acceptance` / X | [installer](plans/installer-test-plan.md); PR-safe subset in `scripts/e2e-smoke.sh` | semi | 🟡 (PR subset automated; full install evidence manual) |
| 19 | **Golden-path E2E** — source → ingest → classify → discuss → claim → draft → verify → export | `workflow-replay` / L4 | [e2e-golden-path](plans/e2e-golden-path-plan.md) for attended runtime; [test-env harness](plans/test-env-harness-plan.md) for ADR-80 Phase 1 cassette replay wired into `scripts/e2e-smoke.sh` | semi | 🟡 (model-free path automated; live model/GUI tail manual) |
| 20 | **Agent output quality** — classification/draft/cite-check correctness | L5 | [ADR-11](../adr/11-vault-eval-maintenance.md) vault-eval | — | ⛔ (harness empty) |
| 21 | **Recovery / failure modes** — safe-mode, MCP-down, chain-break recovery | X | — | — | ⛔ |
| 22 | **Security / adversarial** — lane-escape, prompt-injection, secret leak, fail-open-on-hook-error | `runtime-integration` + release gate / X | alpha.9 G2 [#837](https://github.com/eranroseman/memoria-vault/issues/837) + S4 [#846](https://github.com/eranroseman/memoria-vault/issues/846): interim egress hard-deny, plugin-registration fail-open mitigation, live disabled-tool invocation by name, and structural default-deny decision path | semi | 🟡 |
| 23 | **Performance / scale** — Dataview at 500/2000 notes, `qmd` rebuild | X | — | — | ⛔ |
| 24 | **Deployment modes** — local / mesh / VPS, Syncthing, `memories/` junction | X | — | — | ⛔ |
| 25 | **Plan drift** — plans' own references resolve | L0 | `scripts/check_test_refs.py` (CI + `.githooks/pre-commit`) | ✅ | ✅ |

## L2 — automating the wiring layer

L2 splits at the model boundary (full note: [ADR-29 § L2 implementation](../adr/29-testing-framework.md#l2-implementation-note)). The **policy-gate** half is hermetic Python and now covered for all lanes at L1 (Phase 1, #73) — per-commit, no runtime. The **model-free agent-wiring replay** is covered by ADR-80 Phase 1 `workflow-replay` and runs through `scripts/e2e-smoke.sh`. The **live Hermes agent-wiring smoke** now ships as opt-in `scripts/test-l2.sh`: driver `hermes chat -q` (not ACP), a filesystem-backed `obsidian` MCP shim (Option B), a local OpenAI-compatible endpoint, temporary `HERMES_HOME`, disposable-vault artifact assertion, and a live policy-gate audit-row assertion. The default deterministic endpoint keeps the smoke stable; `MEMORIA_L2_USE_SMOKE_MODEL=0` switches to a real cheap/local model endpoint. It remains nightly/manual and out of required PR CI until stable. The **full §4 matrix + GUI/Zotero/dashboard tail stays attended, per release** — automating the marginal cases costs most and benefits least.

## Open gaps (⛔ / 🟡), prioritized

1. **Product Gate / L5 eval (#20)** — the only layer that tests *quality*; owned by ADR-11, gold tasks unbuilt. Highest long-term value.
2. **Package Gate / Installer E2E (#18)** — plan now exists; needs a real clean-install run recorded.
3. **Runtime/Product Gate live tail (#19)** — the ADR-80 Phase 1 cassette path is automated; `scripts/test-l2.sh` covers the opt-in live Hermes smoke; live GUI proof remains attended or nightly/manual.
4. **Recovery (#21)** — the documented failure-mode/recovery how-tos are never exercised.
5. **Security (#22)** — now tracked by alpha.9 G2/S4 for the live gate boundary; **Performance (#23)** and **Deployment (#24)** still need named plans.

## Related

- Framework + layer definitions: [ADR-29](../adr/29-testing-framework.md)
- Plans: [headless](plans/headless-test-plan.md) · [hermes-cli](plans/hermes-cli-test-plan.md) · [GUI](plans/gui-test-plan.md) · [installer](plans/installer-test-plan.md) · [e2e-golden-path](plans/e2e-golden-path-plan.md) · [test-env harness](plans/test-env-harness-plan.md)
- Shared template: [{{Subject}} test plan](test-plan-template.md)
