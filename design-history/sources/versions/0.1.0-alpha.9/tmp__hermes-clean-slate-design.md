# Hermes-usage audit — findings & change ledger (alpha.9)

_Working artifact for the 0.1.0-alpha.9 checkpoint; deleted at close-out (AGENTS.md). Every durable finding is **landed** (PRs #820 / #825 / #830) or **filed** (issues #822–#829, #832–#833) — see §5. This file is the readable synthesis until the close-out sweep removes it._

> **What this is.** It began as a "clean-slate design" for how Memoria uses Hermes — and isn't one. On-box verification refuted nearly every proposed deletion, so it became a **verification audit + a change ledger**. The single genuinely new design claim (§4) is small and, as written, fails its own motivating case. Honest self-assessment: rigor was **mis-allocated** — the cheap-and-checkable (tool names, deletions, probes) got hard verification; the expensive-and-load-bearing (the §4 attribution claim, the §3 upgrade decision) got anecdote or omission until forced onto the page. The through-line of every finding: **enforcement is a mechanism, not a label** (now an AGENTS.md working principle) — a guarantee kept getting credited to a *description* (a config key, a taxonomy, "the architecture") when a *mechanism* elsewhere was what actually held it.
>
> **Updated after an adversarial critique round.** It found the honesty here was doing double duty as a *shield* — hard problems named precisely, then routed to a backlog as if naming were resolving (the same mis-allocation, one level up). Two things that round forced onto the page: the egress P0 is **live on the running system**, and even the one *landed* fix isn't deployed (**merged ≠ deployed**, §2a / #832); and **"filed" is not "durable"** (§6).

**Evidence tags.** `on-box ✓` verified against installed **v0.14.0** source/docs · `available today` shipped in 0.14.0 · `refuted on-box` checked and false · `verified-0.17 (isolated source)` read in an isolated 0.17 venv — source-verified, **not** runtime-verified in the live stack (a rung *below* `on-box ✓`) · `claim-only` unverified release-note.

## 1. Requirements (the invariants — true in any implementation)

These define Memoria; everything else is mechanism and is negotiable.

1. **The vault is the only source of truth** — plain markdown + git, human-readable and diffable, survives Hermes being deleted. Hermes is a *driver*, never the store.
2. **No durable epistemic write without _appropriate_ approval** — the level scales with the write. Mechanical bookkeeping (a DOI, an author list) is `allow_with_log`; a durable epistemic write (a claim, a contradiction, a supersession) requires PI review; some classes may warrant an automated-judge sign-off below the PI bar. A *graduated* gate, not a single human bottleneck — conflating mechanical and epistemic writes is what burns the supervision budget (req. 8).
3. **Provenance** — every durable fact traces to a source; every write traces to an actor + a decision.
4. **Bounded autonomy** — no *unaudited* egress, no irreversible local action. (Honest version: vault text already leaves the box per LLM call, so the requirement is *no unaudited* egress, not "no egress.")
5. **The human surface is Obsidian, not a terminal** — PI-direct-access rule. The Hermes desktop app is a non-goal; the ACP pane stays the interface.
6. **Config-as-code** — rebuildable from source. GUI-authored profile state is rejected on principle.
7. **Cost is observable per action** — research has a budget.
8. **The binding constraint is the supervision budget** — human approve/reject labels are scarce; minimise the number of distinct human-judgment surfaces, not multiply them (the alpha.9 "÷9 mechanisms" finding).

## 2. What the three audits found

### 2a. The gate is the *only* capability boundary — and it is incomplete · `on-box ✓`
- `agent.disabled_toolsets` is **schema-hiding only** (`model_tools.py:370`); `registry.dispatch` runs any registered tool by name with **no enablement check** (`registry.py:390`). So the policy plugin's hard-deny + default-deny (`policy_hook.py`) is the *only* runtime capability boundary — `disabled_toolsets` is UX, not enforcement.
- That boundary is **incomplete**: it hard-denies file/terminal/code-exec only and **allow-by-defaults** `web_*`/`browser_*`/`send_message`/`process` (returns `{}`). `DENY_DIRECT_TOOLS` had missed the real `process` tool (`toolsets.py:144`) and listed dead names. For egress the sandbox rests entirely on `disabled_toolsets` = schema-hiding.
- **Severity is not "low."** On the normal model path it is low (0.14 providers reject out-of-schema calls); on the **injection path it is unmitigated and P0**, violating req-4. **The adversary, now stated** (it wasn't, and "P0" without a threat model is unanchored): a **poisoned source/paper** whose text reaches the LLM on *every ingest call* (req-1; "data > code", alpha.9 §0b.5) and induces a tool call. Concrete and real for alpha.9 — ingest processes untrusted papers — which is what makes this a genuine P0, not theoretical.
- **A second, independent fail-open:** the gate also fails *open* if the plugin fails to register/import (`plugins.py:1316`) — fail-closed holds only for a *reached* decision. Two independent fail-opens in a bounded-autonomy system is a pattern, not a footnote.
- This corrected **six ADRs** that credited enforcement to a description, not the mechanism (28/23/60/04/46/41, PR #820); the amplifier: ADRs 03/21/46 all ride the *same* gate, so the gate residual was the highest-leverage real gap.
- **Disposition (reconciled — a P0 must not sit behind an M-effort ticket).** The fix was mis-sized by welding it to the structural default-deny (#822, M). Split: the **interim mitigation is S** — hard-deny the egress/messaging families in `DENY_DIRECT_TOOLS` (same low-risk extension as `process`; the contract-doctor already enumerates the 36-tool surface), **filed #832, do now**; #822 stays the proper structural fix. **Live-verified this round:** `web_search`/`browser_navigate`/`send_message`/`delegate_task` still return `{}` on the deployed gate — the P0 is open in the running system. **And merged ≠ deployed:** the deployed gate at `~/Memoria-test` is a *pre-#825 build* (no `process`), so even the landed fix isn't running — #832 includes the redeploy + a deploy-freshness check. **Landed:** `process` fix + sweep + contract doctor (PR #825).

### 2b. ADR-implementation gaps — all 75 accepted ADRs audited
**4 UNIMPLEMENTED · 1 DIVERGED · 10 PARTIAL · 60 IMPLEMENTED** — but the real headline is the *count itself*: **20% of `accepted` is not faithfully built**, and that 20% is a **floor**, not a measurement (the 60 "implemented" came from a shallow 6-agent pass with one-line cites, not deep verification). The deeper failure: **`accepted` is not load-bearing** — nothing detects when code drifts from an accepted ADR's claims, so *silent partials* (ADR-10, ADR-30) present as done and go unnoticed for months. The forward-looking accepted ADRs (83/35/39/66) are a legitimate state; the alarm is the silent partials. Root-cause fix: an **ADR↔code drift doctor** (#833) — the contract-doctor pattern applied to ADR claims. The load-bearing instance:
- **ADR-10 supersession — live correctness bug (#826):** the "exclude superseded from `query`/`write` by default" half is **unbuilt** — `superseded` is honored only by the FAMA linter + 2 proposer skills, with **no retrieval-layer filter**. A query surfaces and a draft cites an already-retired claim, flagged only reactively. The exact FAMA failure ADR-10 exists to prevent, live in alpha.9's own domain. *It also belongs in the alpha.9 recommendations cut* (`design-update-recommendations.md` §3.4): it is **deterministic and cheap** (honor a human-set `superseded_by` pointer), not the contradiction-precision engine that doc rightly defers — a different, higher error tier.
- **ADR-83** accepted with nothing built; **ADR-30** Tier-1 tag-suggestion layer absent (`classify` diverged to deterministic OpenAlex-topic); **ADR-55** `upgrade` reconcile deliberately omitted (test-pinned). Dated in-place notes added (PR #830); text batch in #827.

### 2c. Memory substrates describe, they don't enforce · `on-box ✓`
[ADR-23](../../../adr/23-scoped-memory-substrates.md)'s scope×lifespan split is a **routing table**, not the access-control mechanism. Isolation is enforced by per-profile directories + the `session_search`/`moa`/`delegation` denylist + the kanban card as sole channel; durable-write by the gate's per-lane path globs (`policy_hook.py:13`). Substrate #3 (session history) is disabled in all five profiles. (PR #820.) Optional second lens: CoALA function-typing for the retrieval/publication vocabulary, while scope×lifespan stays the operational routing map.

### 2d. 0.14 is the installed truth; 0.17 was read, not run
The box runs **v0.14.0** (checkout 2026-05-23). 0.17 features were **source-verified in an isolated venv** — memory-batch ops, glm-5.2, promptware defense, and an executor scope-check that *narrows* the gate gap — but **not** runtime-verified in the real profile/plugin/config stack, so they stay a rung below `on-box ✓`. ADR-106 cost-on-card is **refuted on 0.14 and 0.17** (the card export drops cost both ways — keep the session-store join). 0.14 features left on the table: Bitwarden (`available today`), auxiliary-model routing (production), `reasoning_effort`.

## 3. The decision this audit never asked: should we upgrade?

The entire `verified-0.17 (isolated source)` apparatus exists because someone wants 0.17 features — yet every finding above treats 0.14.0 as immovable ground truth and defers to "after a real upgrade" without ever putting the upgrade on the page. That deferral is a **decision made by omission**, and it may be the highest-leverage one here: hardening a gate on a version you intend to abandon is possibly wasted effort.

- **(A) Upgrade the test vault to 0.17 now, verify live.** Pros: stops designing against a version you mean to leave; 0.17 *narrows* the gate gap (executor scope-check) and graduates the isolated-source items to real `on-box ✓`. Cons: migration cost — re-verify the ADR-106 pin + cost-doctor on 0.17, the one-dispatcher-per-vault invariant, profile re-deploy.
- **(B) Stay on 0.14 and keep hardening.** Pros: zero migration risk; the gate fixes (#822/#823) are version-independent anyway. Cons: ongoing design tax against a version you plan to abandon.

**Recommendation:** do #832/#822/#823 regardless (needed on either branch); take **(A)** for the platform features — upgrade Memoria-test under an isolated `HERMES_HOME`, re-run the ADR-106 cost-doctor + the new contract-doctor, then graduate or refute each isolated-source item. Filed as **#828** — a *decision to make this checkpoint*, not a ticket to park.

**Re-grade caveat (this round):** not all `on-box ✓` 0.14 findings are equal on upgrade. The load-bearing one — the gate allow-by-defaults egress (§2a) — is **Memoria-side** (`policy_hook.py` is our plugin), so it **survives the upgrade unchanged** (#832/#822 apply either way). What collapses on 0.17 is narrower: the *"the plugin is the only boundary"* framing (0.17 adds the executor scope-check) and the `registry.dispatch`-has-no-guard claim. So #828 is a real fork, but it does **not** moot the security work — that was a gap in this ledger's grading, now corrected.

## 4. The one new design claim (honest scope)

For the supervision budget (req. 8): one PI accept/reject per card solves the *attention* budget; the idea is to close the *signal* budget too (a binary can't say *which* of the ÷9 mechanisms it calibrates) by **instrumenting the structured context the card already carries** — the NLI verdict, the warrant-check, the variable-match, the exemplar used.

**As written it only works in the easy case.** Self-attribution holds when a card has *exactly one* contested element. The cards that actually burn the budget have *several* weak elements at once, and one reject bit can't say which drove it — so the proposed answer to the binding constraint silently fails in precisely the case that matters. The real shape (untested, needs the live label stream): treat a reject as **joint** evidence weakly downweighting *every* contested element (separates only over volume), or capture an **optional per-element bit** when the PI volunteers one.

**Two honest corrections (this round):** (1) the *premise* — that supervision attention is the binding constraint (req. 8) — is **asserted, never evidenced**; cost (real API \$/document) and retrieval precision are equally plausible. The other doc's **Part 0** ("is memory even the bottleneck? answer before measuring inside it") is exactly this question, so **#829 is gated on Part 0**, not pursued ahead of it. (2) Naming a fatal flaw is not a disposition — an idea that fails its own motivating case is *killed or redesigned*, not "pursued." So **#829 is re-labelled "redesign (current form rejected)"**, not "design to pursue." Filing the rejected form would be the self-criticism-as-armor this doc was caught doing.

## 5. Complete change ledger (the authoritative list — every change this session identified)

Status: ✅ landed · 🔲 filed (issue) · ⬜ **unfiled — lives only here, evaporates on deletion**. Effort: XS/S/M.

| # | Change | Status | Home | Effort |
|---|---|---|---|---|
| L1 | AGENTS.md "Enforcement is a mechanism, not a label" + the installed-version upgrade rule | ✅ | PR #820 | — |
| L2 | Enforcement-attribution corrections to ADR-28/23/60/04/46/41 | ✅ | PR #820 | — |
| L3 | Gate: add `process`; completeness sweep; Hermes **contract doctor** | ✅ | PR #825 | — |
| L4 | Runbook S4 gate-contract gate + coverage-matrix #7 | ✅ | PR #825 | — |
| L5 | ADR-83/30/55 implementation-gap notes; findings folded here | ✅ | PR #830 | — |
| O1 | **Egress P0 — interim: hard-deny the egress/messaging families** + redeploy Memoria-test (merged≠deployed). The act-now fix for the live §2a P0. | 🔲 | #832 | **S — now** |
| O1b | **Gate default-deny per-lane** + ADR-80 deny-test — the *structural* fix (§2a); supersedes O1's interim | 🔲 | #822 | M |
| O2 | Close the **registration fail-open** — lane refuses work if the gate plugin isn't loaded (§2a) | 🔲 | #823 | S |
| O3 | Drop the no-op `checkpoints` + the false "reversibility" comment in the 5 profiles | 🔲 | #824 | S |
| O4 | **ADR-10: exclude superseded from `query`/`write` by default** — live correctness bug (§2b); ships in the alpha.9 recommendations cut | 🔲 | #826 | M |
| O5 | Stale-prose / diverged ADR batch — incl. **ADR-30** tag layer, **ADR-56**, **ADR-78**, ADR-55 prose, 13 stale-text, 84/105 readiness, 35/39/66 unimplemented | 🔲 | #827 | M |
| O6 | **Upgrade decision** — 0.17 vs 0.14 (§3). A *decision to make this checkpoint*, not a ticket to park. | 🔲 | #828 | decision |
| O7 | **Card-attribution — redesign** (current form rejected, §4); **gated on Part 0** (is supervision the binding constraint?) | 🔲 | #829 | redesign |
| O8 | **ADR↔code drift doctor** — detect code drift from accepted-ADR claims (§2b root cause) | 🔲 | #833 | M |
| U1 | Adopt **Bitwarden** secrets → delete the per-profile `.env` seeding | ⬜ | — | S–M |
| U2 | **Auxiliary model routing** → Haiku/Flash in global config — **production only** | ⬜ | — | S |
| U3 | `reasoning_effort`: set per-lane or drop the dead comment | ⬜ | — | XS |
| U4 | **ADR-106 cost spike** — capture `cost_usd` at source via the plugin hook (pin-relocation, not removal) | ⬜ | — | M |

**Sequencing:** **O1 (egress interim, S) + O2 ship now** — they close the live P0 on the running system, regardless of the upgrade fork; O1b (default-deny) is the follow-through. O4 next if alpha.9 touches supersession. **O6 is a decision to make this checkpoint** (it gates whether the isolated-source items are worth chasing). U1–U4 are independent cleanups still needing homes.

## 6. Deletion-safety — and the limit of it

This doc routes to homes (§5): landed (PRs #820/#825/#830) or filed (#822–#829, #832–#833), except **U1–U4** (unfiled — they evaporate on deletion). **But "filed" is not "durable."** #828 (a decision) and #829 (a redesign) are ownerless, dateless tickets that rot as surely as a deleted doc unless triaged: #828 should be **decided** this checkpoint, #829 **gated** on Part 0 — not left as backlog. What this section can honestly promise is that the findings survive *as backlog*, not *as resolved work*. Genuinely safe to delete once U1–U4 are filed **and** #828/#829 are triaged.
