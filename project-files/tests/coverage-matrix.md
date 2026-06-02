---
topic: tests
title: Test coverage matrix
status: draft
---

# Test coverage matrix

Every design component → the layer/protocol that covers it → whether it's automated → status. This is the keystone of the [testing framework](../decisions/29-testing-framework.md): if a surface isn't a row here, it isn't tracked. Update it whenever a component or protocol changes.

**Layers** (see [ADR-29](../decisions/29-testing-framework.md)): **L0** static+schema · **L1** component self-tests · **L2** agent wiring + policy gate · **L3** system/GUI · **L4** golden-path E2E · **L5** quality/eval · **X** cross-cutting.

**Status:** ✅ covered · 🟡 partial · ⛔ gap (no coverage yet).

| # | Component | Layer | Protocol / where | Automated | Status |
| --- | --- | --- | --- | --- | --- |
| 1 | Python tooling — policy gate, hook, board export, metrics, detectors | L1 | [headless](headless-test-protocol.md) §A (`--self-test` ×5) · `python-selftest` CI | ✅ | ✅ |
| 2 | docs/ integrity — links, anchors, page-title text, frontmatter keys | L0 | headless §B (`docs-doctor`) · CI | ✅ | ✅ |
| 3 | vault→site links + wikilink resolution | L0 | headless §B (`check-vault-links`) · CI | ✅ | ✅ |
| 4 | Installer **lint** (shellcheck, PSScriptAnalyzer) | L0 | headless §C · `lint-installers` CI | ✅ | ✅ |
| 5 | Dashboard ↔ writer-schema drift | L0 | headless §D (`detectors --vault` + schema audit) | semi | ✅ |
| 6 | 7 profiles — every documented CLI command | L2 | [hermes-cli](hermes-cli-test-protocol.md) §4 | manual | ✅ |
| 7 | Policy gate — deny path, per-lane write scope, 8 actions | L1+L2 | headless §A1/A2 · hermes-cli §5 (X1, X2, X6) | semi | ✅ |
| 8 | Review gate (ADR-27) — dry_run degradation, dispatch precondition | L2 | hermes-cli §4 (W4), §5 (X3), §4.8 (B12) | manual | ✅ |
| 9 | Audit chain — `before_hash`/`after_hash`, `vault-hash-drift` | L1+L2 | headless §A · hermes-cli §5 (X4) | semi | ✅ |
| 10 | Board / Kanban — create…archive, dispatch, transitions | L2 | hermes-cli §4.8 | manual | ✅ |
| 11 | Profile mgmt, skills, cron | L2 | hermes-cli §4.9–4.11 | manual | ✅ |
| 12 | 16 templates — frontmatter keys; QuickAdd instantiation | L0+L3 | headless §A5/§D · [GUI](../plans/gui-test-protocol.md) A3 (QuickAdd) | semi | 🟡 (instantiation only spot-checked) |
| 13 | 11 dashboards — queries *render* on real data | L3 | GUI Part C | manual | ✅ |
| 14 | 8 Obsidian plugins load + enabled | L3 | GUI Part A | manual | ✅ |
| 15 | Local REST API bridge (write-gate lifeline) | L3 | GUI Part B | manual | ✅ |
| 16 | Zotero + Better BibTeX → `memoria.bib` | L3 | GUI Part D | manual | ✅ |
| 17 | ACP pane (model connectivity through GUI) | L3 | GUI Part E1 | manual | ✅ |
| 18 | **Installer end-to-end** — clean install, `{{VAULT_PATH}}`, `.env` seed, plugin copy, profile register, idempotency, bootstrap apps, flags, WSL2↔Windows | X | [installer](installer-test-protocol.md) | manual | 🟡 (protocol new; lint-only before) |
| 19 | **Golden-path E2E** — source → ingest → classify → discuss → claim → draft → verify → export | L4 | [e2e-golden-path](e2e-golden-path-protocol.md) | manual | 🟡 (protocol new) |
| 20 | **Agent output quality** — classification/draft/cite-check correctness | L5 | [ADR-11](../decisions/11-vault-eval-integration.md) vault-eval | — | ⛔ (harness empty) |
| 21 | **Recovery / failure modes** — safe-mode, MCP-down, chain-break recovery | X | — | — | ⛔ |
| 22 | **Security / adversarial** — lane-escape, prompt-injection, secret leak, fail-open-on-hook-error | X | — | — | ⛔ |
| 23 | **Performance / scale** — Dataview at 500/2000 notes, `qmd` rebuild | X | — | — | ⛔ |
| 24 | **Deployment modes** — local / mesh / VPS, Syncthing, `memories/` junction | X | — | — | ⛔ |
| 25 | **Protocol drift** — protocols' own references resolve | L0 | `scripts/check-test-refs.py` | ✅ | ✅ |

## Open gaps (⛔ / 🟡), prioritized

1. **L5 eval (#20)** — the only layer that tests *quality*; owned by ADR-11, gold tasks unbuilt. Highest long-term value.
2. **Installer E2E (#18)** — protocol now exists; needs a real clean-install run recorded.
3. **Recovery (#21)** — the documented failure-mode/recovery how-tos are never exercised.
4. **Security (#22)**, **Performance (#23)**, **Deployment (#24)** — stand up as the system hardens.

## Related

- Framework + layer definitions: [ADR-29](../decisions/29-testing-framework.md)
- Protocols: [headless](headless-test-protocol.md) · [hermes-cli](hermes-cli-test-protocol.md) · [GUI](../plans/gui-test-protocol.md) *(moving to `tests/`)* · [installer](installer-test-protocol.md) · [e2e-golden-path](e2e-golden-path-protocol.md)
- Shared template: [test-protocol-template.md](test-protocol-template.md)
