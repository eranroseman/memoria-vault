---
topic: tests
title: Test coverage matrix
status: draft
parent: Testing
nav_order: 10
---

# Test coverage matrix

Every design component → the layer/plan that covers it → whether it's automated → status. This is the keystone of the [testing framework](../adr/29-testing-framework.md): if a surface isn't a row here, it isn't tracked. Update it whenever a component or plan changes.

**Layers** (see [ADR-29](../adr/29-testing-framework.md)): **L0** static+schema · **L1** component self-tests · **L2** agent wiring + policy gate · **L3** system/GUI · **L4** golden-path E2E · **L5** quality/eval · **X** cross-cutting.

**Status:** ✅ covered · 🟡 partial · ⛔ gap (no coverage yet).

| # | Component | Layer | Plan / where | Automated | Status |
| --- | --- | --- | --- | --- | --- |
| 1 | Python tooling — policy gate, hook, board export, metrics, detectors | L1 | [headless](plans/headless-test-plan.md) §A (`pytest tests/`) · `python-selftest` CI | ✅ | ✅ |
| 2 | docs/ integrity — links, anchors, page-title text, frontmatter keys | L0 | headless §B (`docs-doctor`) · CI | ✅ | ✅ |
| 3 | vault→site links + wikilink resolution | L0 | headless §B (`check-vault-links`) · CI | ✅ | ✅ |
| 4 | Installer **lint** (shellcheck, PSScriptAnalyzer) | L0 | headless §C · `lint-installers` CI | ✅ | ✅ |
| 5 | Dashboard ↔ writer-schema drift | L0 | headless §D · `detectors --vault --gate dashboard-field-drift` gated in `python-selftest` CI; §D2 non-note audit manual | ✅ drift / 🟡 D2 | ✅ |
| 6 | 5 profiles — every documented CLI command | L2 | [hermes-cli](plans/hermes-cli-test-plan.md) §4 | manual | ✅ |
| 7 | Policy gate — deny path, per-lane write scope, 8 actions | L1+L2 | headless §A1 (all lanes' write-walls self-tested, [#73](https://github.com/eranroseman/memoria-vault/pull/73)) · hermes-cli §5 (live invariants X4) | semi | ✅ |
| 8 | Review gate (ADR-27) — dry_run degradation, dispatch precondition | L2 | hermes-cli §4 (W4), §5 (X3), §4.8 (B12) | manual | ✅ |
| 9 | Audit chain — `before_hash`/`after_hash`, `vault-hash-drift` | L1+L2 | headless §A · hermes-cli §5 (X4) | semi | ✅ |
| 10 | Board / Kanban — create…archive, dispatch, transitions | L2 | hermes-cli §4.8 | manual | ✅ |
| 11 | Profile mgmt, skills, cron | L2 | hermes-cli §4.9–4.11 | manual | ✅ |
| 12 | 16 templates — frontmatter keys; QuickAdd instantiation | L0+L3 | headless §A5/§D · [GUI](plans/gui-test-plan.md) A3 (QuickAdd) | semi | 🟡 (instantiation only spot-checked) |
| 13 | 10 dashboards — queries *render* on real data | L3 | GUI Part C | manual | ✅ |
| 14 | 8 Obsidian plugins load + enabled | L3 | GUI Part A | manual | ✅ |
| 15 | Local REST API bridge (write-gate lifeline) | L3 | GUI Part B | manual | ✅ |
| 16 | Zotero + Better BibTeX → `memoria.bib` | L3 | GUI Part D | manual | ✅ |
| 17 | ACP pane (model connectivity through GUI) | L3 | GUI Part E1 | manual | ✅ |
| 18 | **Installer end-to-end** — clean install, `{{VAULT_PATH}}`, `.env` seed, plugin copy, profile register, idempotency, bootstrap apps, flags, WSL2↔Windows | X | [installer](plans/installer-test-plan.md) | manual | 🟡 (plan new; lint-only before) |
| 19 | **Golden-path E2E** — source → ingest → classify → discuss → claim → draft → verify → export | L4 | [e2e-golden-path](plans/e2e-golden-path-plan.md) | manual | 🟡 (plan new) |
| 20 | **Agent output quality** — classification/draft/cite-check correctness | L5 | [ADR-11](../adr/11-vault-eval-maintenance.md) vault-eval | — | ⛔ (harness empty) |
| 21 | **Recovery / failure modes** — safe-mode, MCP-down, chain-break recovery | X | — | — | ⛔ |
| 22 | **Security / adversarial** — lane-escape, prompt-injection, secret leak, fail-open-on-hook-error | X | — | — | ⛔ |
| 23 | **Performance / scale** — Dataview at 500/2000 notes, `qmd` rebuild | X | — | — | ⛔ |
| 24 | **Deployment modes** — local / mesh / VPS, Syncthing, `memories/` junction | X | — | — | ⛔ |
| 25 | **Plan drift** — plans' own references resolve | L0 | `scripts/check-test-refs.py` (CI + `.githooks/pre-commit`) | ✅ | ✅ |

## L2 — automating the wiring layer

L2 splits at the model boundary (full note: [ADR-29 § L2 implementation](../adr/29-testing-framework.md#l2-implementation-note)). The **policy-gate** half is hermetic Python and now self-tested for all lanes at L1 (Phase 1, #73) — per-commit, no runtime. The **agent-wiring** half is settled too: driver `hermes -z` / `hermes chat -q` (not ACP), and it needs **no Obsidian** — the gate is transport-agnostic, so a filesystem-backed `obsidian` MCP shim (Option B) lets it run on any box. It lands as an opt-in `scripts/test-l2.sh` smoke set (§3 S1–S5 + one §4 case per profile) — nightly, not PR-blocking. The **full §4 matrix + GUI/Zotero/dashboard tail stays attended, per release** — automating the marginal cases costs most and benefits least.

## Open gaps (⛔ / 🟡), prioritized

1. **L5 eval (#20)** — the only layer that tests *quality*; owned by ADR-11, gold tasks unbuilt. Highest long-term value.
2. **Installer E2E (#18)** — plan now exists; needs a real clean-install run recorded.
3. **Recovery (#21)** — the documented failure-mode/recovery how-tos are never exercised.
4. **Security (#22)**, **Performance (#23)**, **Deployment (#24)** — stand up as the system hardens.

## Related

- Framework + layer definitions: [ADR-29](../adr/29-testing-framework.md)
- Plans: [headless](plans/headless-test-plan.md) · [hermes-cli](plans/hermes-cli-test-plan.md) · [GUI](plans/gui-test-plan.md) · [installer](plans/installer-test-plan.md) · [e2e-golden-path](plans/e2e-golden-path-plan.md)
- Shared template: [{{Subject}} test plan](test-plan-template.md)
