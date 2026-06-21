# How Memoria uses Hermes — a clean-slate design

_Working artifact for the 0.1.0-alpha.9 checkpoint; deleted before the release closes (AGENTS.md). Decisions land in ADRs — this doc proposes them. Derived from requirements, then **corrected against on-box data**._

> **Correction notice (read first).** The first draft of this doc proposed deleting Memoria machinery on the strength of Hermes **0.17** release-note features — written in a measured voice, none of it verified. The box runs **v0.14.0** (checkout dated 2026-05-23, *before* 0.15.0). On-box verification then **refuted two of the draft's load-bearing moves** (delete the ADR-106 cost join; demote the gate plugin) and showed two cited features already shipped. Every platform claim below now carries a status tag, the same discipline the rest of this folder uses. The thesis survives only in its hedged form: the *target* is a thinner layer, but most aggressive deletions are refuted or unverified on the version we run.

**Status legend.** `on-box ✓` verified against installed v0.14.0 source/docs · `available today` shipped in v0.14.0 · `refuted on-box` checked and false on this version · `verified-0.17 (isolated)` confirmed in an isolated 0.17 venv probe, pending a real upgrade · `claim-only` release-note, unverified · `untested` no probe run.

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

### The gate — keep the plugin; it is the enforcement, not a backstop · status: on-box ✓
The first draft proposed "make the architecture enforce it, demote the plugin to a backstop." **Refuted by source.** On v0.14.0:

- `agent.disabled_toolsets` is a **schema subtraction only** — it strips tools from what the *model sees* (`model_tools.py:370`). It is not a runtime capability boundary.
- `registry.dispatch(name, args)` runs any tool found in the **global** registry by name, with **no enablement check** (`tools/registry.py:390`). A "disabled" tool that reaches the executor by any non-model path (plugin, injection) is not stopped by the denylist.
- The only runtime guard is the `pre_tool_call` plugin block (`agent/tool_executor.py:128`). Memoria's `policy_hook` **independently hard-denies** `file`/`terminal`/`code_execution` and **defaults to block** for anything unexpected (`src/.memoria/mcp/policy_hook.py:14-18, 84-96, 204, 264`), explicitly "rather than trusting the capability layer."

So the gate plugin's hard-deny + default-deny **is** the capability boundary; `disabled_toolsets` is essentially UX (keeps the model from seeing the tool). The graduated tiers from req. 2 are a **refinement of the plugin's decision function** (`allow_with_log | require_judge | require_PI | deny`), not a replacement for the plugin. "No card → no write" is enforced *because the plugin denies un-carded epistemic writes* — not by architecture alone.

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
One PI accept/reject per card (solves the *attention* budget). The signal-budget gap (a binary can't say *which* of the ÷9 mechanisms it calibrates) is closed not by adding rejection-reason surfaces but by **instrumenting the structured context the card already carries** — the NLI verdict, the warrant-check pass/fail, the variable-match decomposition (§3.3), the exemplar used. A reject on a card whose only contested element was the NLI verdict attributes itself, post-hoc, with no extra PI judgment. One surface, structured attribution.

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
- **`verified-0.17 (isolated)`, pending a real upgrade:** `memory` batch ops (#48507, `memory_tool.py:450`), kanban singleton dispatcher lock (#49068, `gateway/kanban_watchers.py:26`), glm-5.2 (`hermes_cli/setup.py:96`), promptware/threat-pattern defense (`tools/threat_patterns.py`). Adopt by upgrading Memoria-test → verify live → roll forward (AGENTS.md upgrade rule), not from release notes.
- **Refuted or absent on 0.17 (do not plan around):** cost-in-card-export (still session-store-only — see §5), MiniMax-M3 (not in the model catalog). `delegate_task(background)` exists but is N/A (delegation disabled in every profile).

## 5. What must NOT happen (refuted — recorded so it isn't re-proposed)

- **Do not delete the ADR-106 cost join** — refuted on-box, and re-checked on 0.17: the card export *still* drops cost (`kanban_db.py` has no cost fields). Irreversible loss ([ADR-20](../../../adr/20-publication-path.md)).
- **Do not demote the policy gate to a backstop** — it is the only runtime capability boundary; `disabled_toolsets` is schema-hiding, not enforcement.
- **Do not assume 0.15–0.17 features** — the box runs 0.14.0; truth is in the on-box docs, not GitHub release notes (AGENTS.md "do not infer").
- **Do not cite the substrate split as the access-control mechanism** (nor "collapse" it on those grounds) — isolation is enforced by per-profile dirs + the `session_search`/`moa`/`delegation` denylist + the card; durable-write by the gate's path globs. The [ADR-23](../../../adr/23-scoped-memory-substrates.md) taxonomy only *describes* this. The draft's "durable × shared = 4" merge is not ADR-23's axis (scope × lifespan) and is `untested`.

## 6. On-box verification findings (the part worth promoting to ADRs)

1. **ADR-28 mechanism correction `applied`.** `disabled_toolsets` is schema-subtraction only (`model_tools.py:370`); `registry.dispatch` has no enablement check (`registry.py:390`); the policy plugin's hard-deny + default-deny (`policy_hook.py:84-96, 264`) is the real boundary. Recorded as a dated in-place note on ADR-28. On 0.17 (isolated probe) the gap *narrows* — the executor adds a session-toolset-scope block (`tool_executor.py:292-312`) — so the correction is version-specific and a real upgrade would **strengthen** the sandbox (executor scope-check + plugin, defense-in-depth).
2. **ADR-23 rationale correction `applied`.** The scope×lifespan split describes, doesn't enforce; isolation = per-profile dirs + `session_search`/`moa`/`delegation` denylist + card; durable-write = the gate's path globs (`policy_hook.py:13`); substrate #3 is disabled. Recorded as a dated in-place note on ADR-23.
4. **Runtime test (2026-06-21) — the gate hard-denies only the filesystem/shell family `open`.** Driving the deployed gate (`policy_hook.py`) confirms it blocks `code_execution`/`terminal`/`file` (incl. `mcp_`-prefixed) + obsidian command/delete/move, and allows reads. **But** `web_search`/`web_fetch`/`browser_*`/`image_generate`/`computer_use`/`x_search`/`send_message`/`delegate_task` all return `{}` (allow) — `DENY_DIRECT_TOOLS` covers only file/terminal/code-exec. For egress/messaging/browser the sandbox relies entirely on `disabled_toolsets` = schema-hiding on v0.14.0 (a label, not a mechanism — the defect this principle names). Low practical exploitability on the normal model path (providers only allow in-schema tool calls), but a real defense-in-depth gap vs injection and req-4 (no unaudited egress). Fix (version-independent): extend `DENY_DIRECT_TOOLS` to the non-MCP capability families; upgrading to 0.17 also closes it via the executor scope-check.

3. **ADR-106 path re-test `open`.** The cost *gap* is confirmed; the *only-the-join* assumption is not. Spike: can the policy plugin (or a post-LLM-call plugin hook) capture `cost_usd` at source (`plugin-llm-access.md:310`) and attach it to the card, retiring the undocumented-schema join and the version pin?

Findings 1–2 are instances of the AGENTS.md principle *"Enforcement is a mechanism, not a label"* (added this session) — the rule and its two worked examples cross-reference.

## 7. Next step

**Done this session:** the AGENTS.md "Enforcement is a mechanism, not a label" principle + the test-vault upgrade rule, and dated in-place corrections to ADR-28 (gate) and ADR-23 (memory). **Remaining:** the ADR-106 plugin-cost spike (`assumes:` the documented plugin cost API behaves as written), and — if the substrate routing-table reframe is adopted — a write-time lint for the placement-correctness rule. Leave the rest as the requirement-derived target, re-evaluated after a real Hermes upgrade verified in the test vault, not from release notes.
