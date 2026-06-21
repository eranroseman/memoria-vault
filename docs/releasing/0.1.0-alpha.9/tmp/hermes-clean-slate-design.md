# How Memoria uses Hermes — usage audit & findings

_Working artifact for the 0.1.0-alpha.9 checkpoint; deleted before the release closes (AGENTS.md). Durable findings → ADRs/issues (filed — see §9)._

> **What this is, honestly (read first).** This started as a "clean-slate design" and isn't one. After on-box verification almost every proposed deletion was **refuted**, and most sections below conclude *keep this*. So it is a **verification audit of a rejected redesign + a findings/cleanup list**, not a forward design. The one genuinely new design claim — one-disposition-with-structured-attribution (§3 Supervision) — is small and, as written, only half-true (see its caveat). The first draft trusted Hermes **0.17** release-notes; the box runs **v0.14.0** (checkout 2026-05-23, *before* 0.15.0), so every platform claim now carries a status tag.
>
> **Self-assessment of this audit's own bias:** rigor was **mis-allocated**. The cheap-and-checkable (tool names, deletions, on-box probes) got hard verification; the expensive-and-load-bearing (the attribution claim §3, the threat-model severity §6b, and the upgrade decision §10 that was never asked) got anecdote or omission. Where a finding is verified-and-easy it is strong; where it is hard-and-load-bearing, treat it as a sketch.

**Status legend.** `on-box ✓` verified against installed v0.14.0 source/docs · `available today` shipped in v0.14.0 · `refuted on-box` checked and false on this version · `verified-0.17 (isolated source)` **read in an isolated 0.17 venv — source-verified, NOT runtime-verified in the real profile/plugin/config stack**; a rung *below* `on-box ✓` (behaviour can still diverge live), above `claim-only` · `claim-only` release-note, unverified · `untested` no probe run.

## 1. The requirements (the invariants — true in any implementation)

These define Memoria; everything else is mechanism and is negotiable.

1. **The vault is the only source of truth** — plain markdown + git, human-readable and diffable, survives Hermes being deleted. Hermes is a *driver*, never the store.
2. **No durable epistemic write without _appropriate_ approval** — the approval level scales with the write. Mechanical bookkeeping (a DOI, an author list, a Catalog field) is `allow_with_log`; a durable epistemic write (a claim, a contradiction, a supersession) requires PI review; some classes may warrant an automated-judge sign-off below the PI bar. A *graduated* gate, not a single human bottleneck — conflating mechanical and epistemic writes is what burns the supervision budget (req. 8).
3. **Provenance** — every durable fact traces to a source; every write traces to an actor + a decision.
4. **Bounded autonomy** — no unaudited bulk egress, no irreversible local action. (Honest version: vault text *already* leaves the box per LLM call, so the requirement is *no unaudited* egress, not "no egress.")
5. **The human surface is Obsidian, not a terminal** — PI-direct-access rule. The Hermes desktop app is a non-goal; the ACP pane stays the interface.
6. **Config-as-code** — rebuildable from source. GUI-authored profile state is rejected on principle.
7. **Cost is observable per action** — research has a budget.
8. **The binding constraint is the supervision budget** — human approve/reject labels are scarce. Minimise the number of distinct human-judgment surfaces, not multiply them (the alpha.9 "÷9 mechanisms" finding).

## 2. The thesis (hedged)

The *intent* is right: Memoria should be a thin domain layer and let Hermes own the platform. But "thin" is a target, not a license to delete fail-closed controls or working capture on unverified claims.

> **Memoria = a vault schema + a gate policy + three domain operations (ingest, contradiction-check, retrieval-index), exposed through a minimal MCP surface and a declarative profile manifest.**

What that does *not* license, per §6 verification: deleting the cost join, demoting the policy gate, or collapsing the memory substrates on access-control grounds. All three are load-bearing on the version we run.

> **Governing lens — AGENTS.md "Enforcement is a mechanism, not a label."** This doc's biggest errors were one mistake: treating a *description* (the `disabled_toolsets` denylist; the substrate taxonomy) as the *enforcement*. Every component below names the mechanism that actually holds the boundary and, where it exists, the test that proves it. A doc that asserts a guarantee is never the thing that holds it.

## 3. The clean-slate components

### Store — unchanged
Vault markdown + git. This is the point; nothing improves it.

### The gate — keep the plugin (it's the *only* boundary), but it's incomplete · status: on-box ✓
The first draft proposed "make the architecture enforce it, demote the plugin to a backstop." **Refuted by source.** On v0.14.0:

- `agent.disabled_toolsets` is a **schema subtraction only** — it strips tools from what the *model sees* (`model_tools.py:370`). It is not a runtime capability boundary.
- `registry.dispatch(name, args)` runs any tool found in the **global** registry by name, with **no enablement check** (`tools/registry.py:390`). A "disabled" tool that reaches the executor by any non-model path (plugin, injection) is not stopped by the denylist.
- The only runtime guard is the `pre_tool_call` plugin block (`agent/tool_executor.py:128`). Memoria's `policy_hook` **independently hard-denies** `file`/`terminal`/`code_execution` and **defaults to block** for anything unexpected (`src/.memoria/mcp/policy_hook.py:14-18, 84-96, 204, 264`), explicitly "rather than trusting the capability layer."

So the gate plugin's hard-deny + default-deny **is** the capability boundary; `disabled_toolsets` is essentially UX (keeps the model from seeing the tool). **But "is the only boundary" ≠ "is complete":** §6b shows this same gate allow-by-defaults `web_*`/`browser_*`/`send_message`/`process`, so as shipped the one thing enforcing the sandbox **leaks exactly the egress req-4 forbids**. The keep decision is still right (demoting the plugin is strictly worse), but it was verified for *necessity*, not *completeness* — the asymmetry this audit is guilty of. The plugin must be **completed** (#822/#825), not just defended. The graduated tiers from req. 2 are a **refinement of the plugin's decision function** (`allow_with_log | require_judge | require_PI | deny`), not a replacement for the plugin. "No card → no write" is enforced *because the plugin denies un-carded epistemic writes* — not by architecture alone.

This also corrects [ADR-28](../../../adr/28-write-gate-as-plugin.md): its prose attributes single-path sufficiency to the `disabled_toolsets` capability layer, but the source shows the plugin's default-deny is what actually holds. See §6.

### Profiles — cut by capability boundary, expressed as concrete MCP toolsets
Five named personas is a persona decomposition; the requirement-driven cut is by least-privilege capability. Express each as the **MCP toolsets it loads**, never as capability prose ("external read" hides whether access is gated MCP or a hole):

- **Co-PI** — toolsets: `obsidian` (read), `qmd`, `cluster`, `ingest` (read facade), `tasks` (propose cards), `memory`, skills, todo. No write toolset; the gate denies its writes. The human's single interface.
- **Ingestor** — adds the **gated external-discovery MCP servers** (`paper_search`, `pyzotero`) — typed, audited MCP, *not* raw `web`/egress — plus mechanical Catalog writes via `obsidian` (gate → `allow_with_log`). Peer-review folds in as a card-verification step, not a standing profile.
- **Claim-writer** — `obsidian` write only, fed only by approved cards; no external MCP at all.
- **Engineer — extract from the research deployment.** Note (correcting the draft): under MCP-only it already has no dev capability, so the win is **one fewer profile to reason about**, not a security delta.

Worker toolset scoping that makes this safe (`HERMES_KANBAN_BOARD` pinned per worker; dedicated `kanban_*` toolset) is **available today** (`cli-commands.md:407`, `kanban-worker-lanes.md:89`); per-worker toolset *pinning* hardening (#45590) is `claim-only` for 0.15+.

### Orchestration — native kanban · status: available today (core) / claim-only (hardenings)
The board, dispatch, worker board-isolation, and the `kanban_*` worker toolset are in v0.14.0. Per-task model overrides, stale-task detection, and the singleton dispatcher lock (#49068) are `claim-only` for 0.15+ — useful if they land, but not assumed here. `tasks_mcp` stays until the native equivalents are verified on an installed version.

### Sandbox — keep the policy plugin; promptware-defense additions are claim-only
The policy plugin (above) is the enforcement and stays. Native recalled-memory scanning / threat-pattern defense are `claim-only` (0.15) — a *complement* to the gate if verified, never a replacement.

### Domain operations — three, minimal, card-triggered
Ingest, contradiction/NLI check, retrieval index (qmd, off-the-shelf). Contradiction-check is a **verification step on a card**, surfaced in the same PI review — not a standing alert stream. This matches the alpha.9 baseline's defer-by-default and serves req. 8.

### Supervision — one card disposition, attributed via the card's existing structure
One PI accept/reject per card solves the *attention* budget. The idea: close the signal-budget gap (a binary can't say *which* of the ÷9 mechanisms it calibrates) not by adding rejection-reason surfaces but by **instrumenting the structured context the card already carries** — the NLI verdict, the warrant-check pass/fail, the variable-match decomposition (§3.3), the exemplar used.

> **Honest scope — this is the doc's one new design claim, and as written it only works in the easy case.** Self-attribution holds when a card has *exactly one* contested element (reject ⇒ that element was wrong). But the cards that actually burn the supervision budget have *several* weak elements at once, and one reject bit cannot say which drove it — so the proposed solution to the binding constraint (req-8) silently fails in precisely the case that matters. The real shape (untested, needs design + the live label stream): treat a reject as **joint** evidence weakly downweighting *every* contested element (separates only statistically, over volume), or capture an **optional per-element bit** when the PI volunteers one (degrades gracefully to the binary). "Attributes itself post-hoc" is true for the single-contested case, not the multi-contested one — and multi-contested *is* req-8. Residual design item with no durable home yet (§9).

### Memory — substrates are a routing table; access control is topology + gate · status: on-box ✓
The draft's instinct to "collapse the seven substrates" was the gate mistake again. The [ADR-23](../../../adr/23-scoped-memory-substrates.md) scope×lifespan split **describes** where memory lives; it does not **enforce** isolation. On v0.14.0 the enforcement is three concrete mechanisms, none of them the taxonomy:

- **Cross-profile isolation** — per-profile directories (own session store + `MEMORY.md`) + every profile denying `session_search`/`moa`/`delegation` (`src/.memoria/profiles/memoria-*/config.yaml`) + the kanban card as the only shared channel.
- **Durable-write access** — the policy gate's per-lane path globs (`policy_hook.py:13`).
- **Cross-profile handoff** — the card as the structured unit.

So keep the seven as a **reference / routing table** ("where does X live?") — never cite it as access control. Two corrections fold in: substrate **#3 (Session history) is currently disabled** in all five profiles (`session_search` denied), so the live set is smaller than the table; and "keep durable out of capped stores" is **placement correctness** (a write-time lint), not access control. Optional second lens: classify by cognitive function (CoALA — working/episodic/semantic/procedural) for the *retrieval + publication* vocabulary, while scope×lifespan stays the operational routing map. The Co-PI keeps the native `memory` tool (the one self-improving surface); atomic batch ops (#48507) are `claim-only` for 0.17.

### Cost / secrets
- **Cost — keep the ADR-106 join.** `refuted on-box`: cost lives in the session store (`session-storage.md` migration 5: `estimated_cost_usd`, `actual_cost_usd`); the card export drops it, exactly as [ADR-106](../../../adr/106-cost-and-disposition-capture.md) states. Deleting the join = permanent, un-backfillable loss ([ADR-20](../../../adr/20-publication-path.md)). *But* ADR-106's "the join is the only path, pin Hermes forever" is itself unverified — `plugin-llm-access.md:310` documents `cost_usd` exposed to plugins at call time, a capture-at-source path that would drop the version pin. That's a **spike, not a deletion** (§6).
- **Secrets — Bitwarden, available today.** `user-guide/secrets/bitwarden.md` ships in v0.14.0. One bootstrap token replaces the per-profile `.env` seeding and makes rotation propagate. This is a real simplification available now, no upgrade needed.
### Deployment — declarative manifest, unchanged
`install.sh` rendering profiles from templates; test-vault + production coexistence. Dashboard profile-builder stays rejected (req. 6).

## 4. What actually changes for alpha.9 (the honest, small list)

- **Adopt now (`available today`):** Bitwarden secrets → delete per-profile `.env` seeding.
- **Adopt now (design, no Hermes dependency):** graduated gate tiers as the plugin's decision function; contradiction-as-card-step; one-disposition-with-structured-attribution for supervision.
- **`verified-0.17 (isolated source)`, pending a real upgrade (§10):** `memory` batch ops (#48507, `memory_tool.py:450`), kanban singleton dispatcher lock (#49068, `gateway/kanban_watchers.py:26`), glm-5.2 (`hermes_cli/setup.py:96`), promptware/threat-pattern defense (`tools/threat_patterns.py`). Source-verified in an isolated venv — **not** runtime-verified live; adopt only by upgrading Memoria-test → verify live → roll forward (§10), not from release notes.
- **Refuted or absent on 0.17 (do not plan around):** cost-in-card-export (still session-store-only — see §5), MiniMax-M3 (not in the model catalog). `delegate_task(background)` exists but is N/A (delegation disabled in every profile).

## 5. What must NOT happen (refuted — recorded so it isn't re-proposed)

- **Do not delete the ADR-106 cost join** — refuted on-box, and re-checked on 0.17: the card export *still* drops cost (`kanban_db.py` has no cost fields). Irreversible loss ([ADR-20](../../../adr/20-publication-path.md)).
- **Do not demote the policy gate to a backstop** — it is the only runtime capability boundary; `disabled_toolsets` is schema-hiding, not enforcement.
- **Do not assume 0.15–0.17 features** — the box runs 0.14.0; truth is in the on-box docs, not GitHub release notes (AGENTS.md "do not infer").
- **Do not cite the substrate split as the access-control mechanism** (nor "collapse" it on those grounds) — isolation is enforced by per-profile dirs + the `session_search`/`moa`/`delegation` denylist + the card; durable-write by the gate's path globs. The [ADR-23](../../../adr/23-scoped-memory-substrates.md) taxonomy only *describes* this. The draft's "durable × shared = 4" merge is not ADR-23's axis (scope × lifespan) and is `untested`.

## 6. On-box verification findings

### 6a. "Enforcement is a label" — systemic (ADR audit of all 110 ADRs + runtime)
A background audit read every ADR against the AGENTS.md principle; ~38 made a boundary claim, and **six credited a description, not the mechanism** — all corrected in place (PR #820):

| ADR | Credited to | Actually enforced by |
|---|---|---|
| 28 | `disabled_toolsets` | policy plugin hard-deny + default-deny (`policy_hook.py:84-96,264`); `registry.dispatch` has no enablement check (`registry.py:390`) |
| 23 | the substrate split | per-profile dirs + `session_search`/`moa`/`delegation` denylist + card; gate path globs (`policy_hook.py:13`) |
| 60 | "the policy MCP" | **not yet implemented** — no foreign-vault scope on-box (`policy_hook.py:155` is single-vault) |
| 04 | folder structure | lane `allow/deny.write` globs + default-deny |
| 46 | the layer contract | `DENY_DIRECT_TOOLS` + default-deny |
| 41 | "dispatch refuses to advance a card" | the write gate (`decision.py:146`); card-advance is process discipline |

Done-right exemplars (named mechanism **and** a check): ADR-55, 74, 80, 105. On 0.17 (isolated probe) the ADR-28 gap *narrows* — the executor adds a session-toolset-scope block (`tool_executor.py:292-312`) — so a real upgrade would **strengthen** the sandbox (defense-in-depth).

### 6b. The gate is narrow and allow-by-default (runtime-confirmed)
Driving the deployed gate blocks file/terminal/code-exec (incl. `mcp_`-prefixed) + obsidian command/delete/move, allows reads — **but allow-by-defaults everything else**: `web_*`/`browser_*`/`image_generate`/`computer_use`/`x_search`/`send_message`/`delegate_task` all return `{}`. Worse, **`DENY_DIRECT_TOOLS` is wrong against the installed version (B3, runtime-confirmed):** it lists dead names (`code_execution`/`run_command` aren't real 0.14 tools) and **misses `process`** — a real tool in the `terminal` toolset (`toolsets.py:144`) that the gate **allows**. So for egress/messaging/process the sandbox rests entirely on `disabled_toolsets` = schema-hiding on 0.14 (a label, not a mechanism).

**Severity — corrected; it is not "low".** Rate the two paths separately. On the *normal model path* it is low (0.14 providers reject out-of-schema tool calls). On the *injection path* — the sandbox's **stated adversary** — it is **unmitigated and P0**: a poisoned source that induces a `web_fetch`/`send_message`/`process` call hits no wall, violating req-4 (bounded autonomy), the **first invariant**. "Providers only allow in-schema calls" is exactly the assumption injection breaks, so it is no comfort here — an earlier draft of this section rated the whole gap "low," which contradicted the doc's own threat model. The `process` slice is **fixed** (PR #825 + the contract doctor that catches the next such drift); the egress slice is the **default-deny decision, filed #822**.

### 6c. Two more 0.14 reliance gaps (utilization audit, List B)
- **B4 — a *second* fail-open, not a nuance.** Plugin-hook errors are swallowed at the Hermes layer (`plugins.py:1316`); the gate is fail-closed only on decisions it *reaches*. A registration/import failure proceeds silently. So there are now **two independent fail-open paths** — §6b (gate allow-by-defaults egress) and this (gate *absent* on a load error) — and two independent fail-opens in a system whose first invariant is bounded autonomy is a **pattern**, not a footnote. The "fail-closed in every mode" claim (ADR-28) holds only for a *reached, erroring* decision. **Filed #823.**
- **B5 — `checkpoints.enabled: true` snapshots nothing.** It triggers only on native `write_file`/`patch`/`terminal` (`tool_executor.py:104`), none of which Memoria uses (all writes go through the obsidian MCP). The "mode-independent reversibility" comment in all 5 profiles is **false**; real reversibility = Memoria's audit-hash pairs. **Filed #824.**

### 6d. ADR-106 cost (`open` spike)
The cost *gap* is confirmed (card export drops cost on 0.14 **and** 0.17); the *only-the-join* assumption is not. Spike: capture `cost_usd` at source via a plugin hook (`plugin-llm-access.md:310`). This **relocates** the pin, it does not remove it — the plugin LLM-access hook is itself a version-dependent Hermes API on the platform §6/§10 show is unstable. It is a *better* pin (a semi-public API drifts slower and more visibly than an undocumented SQLite schema, and the contract-doctor pattern can guard it), but pin-relocation, not pin-removal — an earlier draft sold it as the latter.

### 6e. ADR-implementation gaps (third audit — all 75 accepted ADRs)
A background audit checked whether each accepted ADR's decision is actually built. **4 UNIMPLEMENTED, 1 DIVERGED, 10 PARTIAL, 60 IMPLEMENTED.** It independently confirmed this session's gate priority: ADRs **03/21/46** are all enforced by the *same* decision-core `dry_run` + ADR-28 plugin, so the ADR-28 residual (the §6b `process`/fail-open gaps) is the highest-leverage real gap. Surprises:
- **ADR-10 (supersession) — live correctness bug (#826):** the "exclude superseded from `query`/`write` by default" half is **unbuilt** — `superseded` is handled only in the FAMA linter + 2 proposer skills, with no query/retrieval-layer filter. So a query surfaces and a draft cites a superseded claim, flagged only *reactively*. The exact FAMA failure ADR-10 exists to prevent, live in the paths it names — in alpha.9's own domain.
- **ADR-83** accepted with nothing built; **ADR-30** Tier-1 tag-suggestion layer absent (`classify` diverged to deterministic OpenAlex-topic); **ADR-55** `upgrade` reconcile deliberately omitted (test-pinned). Dated notes added in-place; batch in #827. (The AGENTS.md ADR-55 exemplar cites the *built + tested* part, so it stands.)
- Report: `adr-implementation-gap-audit.md`.

## 7. 0.14 features under-used (utilization audit, List A)
- **A1 — Bitwarden secrets (`available today`).** One bootstrap token vs fanning plaintext keys into 5 per-profile `.env`. Central rotation; fits the test+private two-vault setup.
- **A2 — auxiliary model routing (`spot-checked`).** Global `~/.hermes/config.yaml` *has* an `auxiliary:` block, but every entry is empty (`provider: auto`, `model: ''`) → aux tasks fall back to the lane's main model. On **this test box** the main model is local `qwen2.5:7b` (free), so it's moot here; in **production** (API lanes) compression/title/approval would bill at the expensive model. Fix is production-only: point `auxiliary.{compression,title_generation,approval}` at Haiku/Flash. (The audit's "unset" → precisely "present but empty," same effect where the main model is paid.)
- **A3 — `reasoning_effort`** recommended in 4 profile comments, set in none: set it (low on mechanical lanes, high on Peer-reviewer) or drop the comment.
- **A4 — `session_search` disabled everywhere** (deliberate isolation for workers); the Co-PI is the one lane where cross-session recall may be wanted — a privacy call, not an auto-win.
- **A5–A7 — confirmed correct as-is:** `memory` Co-PI-only, native kanban bypassed for the gate (per-card `model_override` is plumbed-but-unwired in 0.14 anyway), external cron for the no-LLM sweeps.

## 8. Recommended changes (by leverage; effort sized so "by leverage" has a denominator)
1. **Security — the two fail-opens, treated as one P0 pair** (§6b + B4):
   - (a) **Default-deny the gate per-lane** + an ADR-80 runtime deny-test (#822). This **inverts** the enumeration problem (now enumerate the correct per-lane *allow*-list), it does not remove it — but that's the right trade: a wrong allow-list breaks the lane *noisily* instead of leaking *silently*, and per-lane allow-lists are small and stable. Not "one move" — it's the same combinatorial task that produced the wrong denylist, done on the safe side. **Stopgap landed:** `process` fix + completeness sweep + contract doctor (PR #825). Effort **M**.
   - (b) **Close the registration fail-open** (#823): the lane refuses work / blocks writes when the gate plugin isn't loaded. Effort **S**.
2. **P2 — cost (production only): `auxiliary.*` → Haiku/Flash** in global config; verify against the live API config first (moot on the local-qwen test box). Effort **S**.
3. **P3 — drop the no-op `checkpoints` + the false "reversibility" comment** in the 5 profiles (#824). Effort **S**.
4. **Adopt Bitwarden (A1)** — delete the per-profile `.env` seeding. Effort **S–M**.
5. **Open spike: ADR-106 plugin-cost capture** (§6d) — pin-relocation, not removal. Effort **M**.

## 9. Status & durable homes
**Landed:** AGENTS.md "Enforcement is a mechanism, not a label" + the upgrade rule, dated corrections to ADR-28/23/60/04/46/41 (PR #820); the `process` gate fix + completeness sweep + contract doctor (PR #825); dated implementation-gap notes on ADR-83/30/55 (this PR).
**Filed — everything now has a durable home (this doc can be deleted safely):**
- Gate security: #822 (default-deny / egress fail-open), #823 (registration fail-open), #824 (checkpoints no-op).
- ADR-implementation gaps: #826 (ADR-10 superseded-exclusion correctness bug), #827 (stale-prose / diverged ADR batch).
- The two formerly-homeless design items: **#828** (the §10 upgrade decision), **#829** (the §6/§3 multi-contested attribution claim).
**Open:** the §8 list, the ADR-106 spike, and the §10 fork (#828).

## 10. The decision this audit never asked: should we upgrade?

The entire `verified-0.17` apparatus exists because someone wants 0.17 features — yet every section treats 0.14.0 (a May-2026 checkout) as immovable ground truth and defers everything to "after a real upgrade," without ever putting the upgrade decision on the page. That deferral is a **decision made by omission**, and it may be the highest-leverage one here: hardening a gate (§8) on a version you intend to abandon is possibly wasted effort.

**The fork:**
- **(A) Upgrade the test vault to 0.17 now, verify live, then design against it.** Pros: stops designing against a version you mean to leave; 0.17 *narrows* the gate gap (executor scope-check, §6a) and ships memory-batch / glm-5.2 / promptware (today only `verified-0.17 (isolated source)`); graduates that whole rung to real `on-box ✓`. Cons: real migration cost — the ADR-106 pin + cost-doctor must be re-verified on 0.17 (the schema may move), the one-dispatcher-per-vault invariant, profile re-deploy.
- **(B) Stay on 0.14 and keep hardening.** Pros: zero migration risk; the security fixes (#822/#823) are version-independent and needed anyway. Cons: you keep paying design tax against a version you plan to abandon; the `isolated-source` findings never graduate.

**Recommendation:** #822/#823 are needed on *either* branch — do them now regardless. For the platform features, take **(A)**: upgrade Memoria-test under an isolated `HERMES_HOME`, re-run the ADR-106 cost-doctor + the new contract-doctor, then graduate or refute each `isolated-source` item. The alternative is indefinitely designing against a version no one intends to keep — the exact trap this document is otherwise about. **This decision has no durable home yet — file it (§9).**
