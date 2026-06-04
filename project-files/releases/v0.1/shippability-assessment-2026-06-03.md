# Memoria v0.1 — shippability assessment

**Date:** 2026-06-03
**Question it answers:** "Can we ship?" — as a checklist with a critical path, not a gut call.
**Basis:** `implementation-status.md` ledger + live findings from this session (gate enforcement, command-surface status, session-skill plumbing, ACP/pane behavior).

---

## The bar (state it before judging against it)

"Shippable v0.1" here = **a technical early-adopter can install Memoria and run ONE agent workflow end-to-end — through a real trigger, gated and audited, queued for human review — and watch it work.** Not seven polished agents; one *operable, verified loop* + the hand-usable vault scaffold underneath it. Adjust the audience (internal alpha vs. public) and the bar moves, but the critical path below doesn't.

By that bar, **today: not yet.** Gate 0 ~green, Gate 1 partial, Gates 2–4 red (below). The gap is *invocation wiring + one end-to-end run*, not a rebuild.

---

## What's already real (assets you can count on)

| Asset | Status | Evidence |
|---|---|---|
| Vault scaffold (folders, 16 templates, frontmatter schema, 11 dashboards, cockpit) | **real, hand-usable without agents** | ledger rows 50–67 |
| Write gate + policy engine (deny / dry_run / fail-closed) | **self-tested + live-validated** | rows 30–31; writer agent wrote via gate, `hermes -z` |
| obsidian MCP write-bridge | **approved (live write confirmed)** | row 29 |
| Deterministic tooling (`detectors.py`, `board_export.py`, `metrics_aggregate.py`) | **self-tested; some cron-wired** | rows 34–35, 42 |
| 7 profiles configured (SOUL + config + mcp + distribution + lane-overrides) | **shipped (present, not e2e-verified)** | rows 22, 25–27, 36 |
| Installer (bootstrap + Windows launcher) | **shipped, Tier-3 verified** | rows 43–44 |

The **floor and the plumbing are real and partly proven.** What's missing is the agents taking a verified step on them.

---

## Critical path — dependency-ordered gates

Each gate must be green before the next is meaningful. The chosen v0.1 *workflow* threads all five.

### Gate 0 — Install & register (foundation) — **~GREEN**
- [x] Installer runs clean; 7 profiles register at 0.1.0; MCP servers wired; secrets seeded per profile.
- [ ] **Wart:** 2 official skills fail to fetch (`ocr-and-documents`, `github-repo-management`) — installer warns-not-fails, so those capabilities are absent (row 43). Fix the skill paths or drop them from `OFFICIAL_SKILLS`.

### Gate 1 — Live agent spine (does the loop work *at all*?) — **PARTIAL — the #1 thing to prove**
A registered profile, **dispatched a board card**, runs against the live obsidian MCP + policy gate, writes its artifact, the write is gated + audited, and the card **completes**.
- [x] Sub-proof done: a writer agent wrote `10-inbox/02-answers/…` through the bridge + gate (`hermes -z`).
- [ ] **Not done: the full card-dispatch → claim → agent-run → complete → review cycle, observed end-to-end.**
- **De-risk it:** prove this with the *leanest* agent first — a **deterministic** one with no external API and no ingest (Linter `health-report` / drift scan, or Verifier `similarity-check`, or Mapper `corpus-map`). That isolates "does dispatch→run→gate→write→complete work live" from the harder ingest risks. The Linter is the safest: `detectors.py` already runs, zero-LLM, cron-wired.

### Gate 2 — One *valuable* workflow end-to-end — **RED — the long pole**
The actual product loop. Most likely **capture → ingest → gated write → review** (the primary intake).
- [ ] A real trigger fires it (manual CLI is operable today; **#85 `feat/quickadd-zotero-capture`** is the first command-surface brick).
- [ ] `ingest_paper.py` (ADR-30) runs the scriptable tiers; LLM classify lands; gated writes create the paper-note at `proposed`.
- **This is where the work and the risk concentrate** — it's the *least*-built path (ADR-30 is *proposed*), and it carries the round-2 red-team risks (multi-source merge correctness, OCR/PDF install fragility, tag-shortlist quality).

### Gate 3 — Human review loop closes — **RED**
- [ ] Card → `done` → `review_status: requested` → human approves → lifecycle `current`. The review gate is a dispatch precondition — policy-tested, **not** e2e-verified.

### Gate 4 — Observability — **AMBER**
- [x] Tooling ships; `board_export` cron wired.
- [ ] `audit.jsonl` populated by a live run; a dashboard shows the live card; `metrics` needs real volume (sparse-data bands are meaningless).

**Ship when Gates 0–4 are green for the chosen workflow.** Today that's `0~ · 1partial · 2red · 3red · 4amber`.

---

## Explicitly OUT of the first slice (to keep it shippable)

Cutting these is what makes "ship one loop" tractable — none blocks a defensible v0.1:

- **The ACP-pane interactive surface** for Mapper/Writer/Verifier — and therefore the **session-skill / pane-readonly hardening** (the ephemeral-engine + unwired-`set_session_skill` fix from this session). The pane simply isn't advertised in v0.1; a dispatched-only slice doesn't need it. *(Re-open once a workflow ships — it's a safety nicety, not a ship-blocker.)*
- **The other six agents' full command sets** — ship one workflow, not seven.
- **ADR-30 Tier 2** (NLI contradiction, KeyBERT, the comparative `[!brief]`) and heavy NLP.
- **Multi-source merge sophistication** (ADR-30 R2-1) — start single-source-with-fallback; validate the merge later.
- **API-POST capture transport** — script/CLI/QuickAdd front-end ships first (ADR-30 §future).
- **L5 eval, recovery/security/perf/deployment suites** — post-v0.1.

---

## Risks that could sink the slice

1. **The end-to-end agent run has never been done.** Unknown unknowns once a real model on the cheap tier drives the skills: tool-use reliability, and whether the **SOUL.md-procedure orchestration** (20 of 28 "skills" are prompt procedures, not packaged skills) actually executes the multi-step work. *Highest-uncertainty item.*
2. **ADR-30 ingest is the least-built path** *and* carries the round-2 merge-correctness + OCR-install + tag-quality risks. If the value loop is ingest, this is the long pole — consider proving Gate 1 with a deterministic agent first so the spine is trusted before betting it on ingest.
3. **Install fragility** — PDF/OCR deps (`ocr-and-documents` already fails to fetch); the very dependency class ADR-30 cites as its motivation. A clean install on a fresh box is itself unproven for the agent path.
4. **Docs claim more than the build delivers.** The design docs describe a complete system; the build is a scaffold. `implementation-status.md` tracks this, but external readers (and a release announcement) will over-read the docs. Keep the status tags honest and the README's claims scoped to what's operable.

---

## Bottom line for the "can we ship?" call

- **Not as an agentic product today** — no agent has completed a verified workflow; the command surface and review loop aren't operable end-to-end.
- **The path is narrow and concrete, not a rebuild:** Gate 1 (prove the spine e2e with a *deterministic* agent — low risk, establishes dispatch→gate→write→complete works live) → Gate 2 (build + verify *one* value workflow, likely ingest) → Gates 3–4 (close review + observe). Cut everything in the OUT list.
- **It's mid-build, not stalled:** #85 is the first capture brick; ADR-30 is the intake redesign; the gate + bridge are proven. The differentiator is in progress.

**Recommended next concrete step:** pick the Gate-1 deterministic loop (Linter `health-report` or Verifier `similarity-check`) and drive it through `hermes -p <profile>` against a live install — card dispatched → run → gated write/audit → complete. That single run converts "we think the spine works" into "the spine works," and tells you whether the much riskier ingest loop (Gate 2) is standing on solid ground.
