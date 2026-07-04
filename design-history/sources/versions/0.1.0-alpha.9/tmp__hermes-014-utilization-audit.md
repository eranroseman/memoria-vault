# Hermes v0.14.0 utilization audit

**Scope.** Audits the single assumption that Memoria uses the **installed Hermes
v0.14.0** optimally. Source of truth = `~/.hermes/hermes-agent` (version confirmed
`pyproject.toml` → `0.14.0`). 0.15–0.17 features are explicitly out of scope.
Memoria surface examined: `src/.memoria/profiles/memoria-*/config.yaml`,
`src/.memoria/mcp/`, `src/.memoria/plugins/memoria-policy-gate/`, `scripts/install*.sh`,
`docs/adr/`. All claims below were verified against the actual 0.14.0 source, not
Memoria's own docs.

Two lists:

- **A.** 0.14 capabilities Memoria does NOT use but plausibly should.
- **B.** Places Memoria relies on a 0.14 behavior that is NOT the boundary it assumes.

Each finding ranked by impact within its list.

---

## List B — assumed boundaries that the 0.14 runtime does not enforce

> These are the higher-stakes findings: they are silent gaps in the sandbox model,
> not missed conveniences. Listed first.

### B1 — `agent.disabled_toolsets` is schema-hiding, not an execution boundary (CRITICAL)

- **Severity:** Critical — it is the security premise of the whole MCP-only sandbox
  (ADR-27 calls it the "capability layer / first wall"; ADR-46/D40 "agents reach
  the vault only through MCP, no exceptions").
- **What Memoria assumes:** Every profile sets
  `agent.disabled_toolsets: [browser, code_execution, computer_use, file, image_gen,
  messaging, terminal, web, x_search, …]` and treats that list as *the* capability
  wall, with the policy gate as a second in-process wall.
- **What 0.14.0 actually does:** `disabled_toolsets` is applied only in
  `model_tools.get_tool_definitions` as a set-subtraction over the **schemas sent to
  the model** (`model_tools.py:366-381` — `tools_to_include.difference_update(resolved)`).
  The dispatcher `registry.dispatch(name, args)` looks the entry up by name and runs
  its handler with **no enablement/allowlist check whatsoever**
  (`tools/registry.py:393-405`). So `disabled_toolsets` only hides tools from the
  model's tool list; it does not stop a tool from executing if its name reaches
  dispatch by any other path (a leaked/hallucinated name re-surfaced via
  `execute_code`, a plugin, `delegate_task` child context, MCP-to-tool routing, or a
  future Hermes path that bypasses the schema list). It is a label, not a mechanism —
  exactly as the task framing states.
- **Evidence:** `model_tools.py:366-381` (subtraction at schema build);
  `tools/registry.py:393-405` (`dispatch` — no check); `tools/registry.py` grep for
  `disabl/enabl/allow` returns only cache-key and CLI-enable comments, no dispatch
  guard.
- **The real wall is the gate, and it is narrow** (see B2/B3): the gate only
  hard-blocks obsidian-writes + a short denylist; everything else returns allow.
- **Fix (one line of intent):** Treat the gate — not `disabled_toolsets` — as the
  enforcement boundary, and make the gate's denylist *complete* (B2). Long-term, the
  only true fix is fronting writes/capabilities with a custom bridge that calls policy
  internally (the policy_hook.py docstring already says this), since 0.14 has no
  dispatch-level toolset enforcement to lean on.

### B2 — the gate allows every capability tool except obsidian-writes + a stale denylist (CRITICAL)

- **Severity:** Critical — this is what makes B1 exploitable rather than theoretical.
- **What Memoria assumes:** "every direct-capability tool (file, terminal, code-exec
  families — `DENY_DIRECT_TOOLS`) is HARD-DENIED for every lane" (policy_hook.py:14-18).
- **What actually happens:** `policy_hook.evaluate_pre` returns `{}` (allow) for any
  tool that is neither an obsidian-write keyword nor an exact member of
  `DENY_DIRECT_TOOLS` / `DENY_OBSIDIAN` (`policy_hook.py:216-218` → `classify` returns
  `None` → allow). So `web_*`, `browser_*`, `image_generate`, `computer_use`,
  `x_search`, `send_message`, `delegate_task`, `process`, and every MCP read tool are
  **allowed by the gate**. For all of those the sandbox relies *entirely* on B1's
  schema-hiding, which is not a boundary. The plugin hook *does* fire for every tool
  (`tool_executor.py:125-133` → `get_pre_tool_call_block_message`, keyed on
  `function_name` before dispatch, MCP and native alike — so the gate sees them; it
  just waves them through).
- **Evidence:** `src/.memoria/mcp/policy_hook.py:110-122` (`classify` → None for
  non-obsidian), `:216-218` (None → `return {}`); `agent/tool_executor.py:125-133`
  (hook fires for all tools pre-dispatch); `hermes_cli/plugins.py:1428-1469`
  (`get_pre_tool_call_block_message` — first `action:block` wins, else None=allow).
- **Fix:** Make the gate default-deny: block any tool not on an explicit per-lane
  allowlist (obsidian reads/writes, the policy/ingest/cluster/tasks/patterns/qmd MCP
  tools), instead of allow-by-default + a hand-maintained denylist.

### B3 — `DENY_DIRECT_TOOLS` is incomplete *against 0.14.0 itself* — `process` is missing (HIGH)

- **Severity:** High — the denylist's stated job is to fail-closed on "a Hermes
  update adding a toolset the denylist doesn't know" (policy_hook.py:82-87), yet it
  already misses a tool that exists in the *current* installed version.
- **What Memoria assumes:** `DENY_DIRECT_TOOLS = {write_file, patch, read_file,
  search_files, terminal, run_command, code_execution, execute_code}` covers the
  file/terminal/code-exec families.
- **What 0.14.0 actually has:**
  - `file` toolset = `read_file, write_file, patch, search_files`
    (`tools/file_tools.py:1174-1177`). ✓ all covered.
  - `terminal` toolset = `terminal`, **`process`** (`toolsets.py:142-145`;
    `tools/process_registry.py:1465,1539`). **`process` is NOT in the denylist** —
    a process-management tool (spawn/kill/list/wait on processes) that would dispatch
    if the terminal toolset ever leaked through (the exact config-drift scenario the
    denylist exists to catch).
  - `code_execution` toolset = `execute_code` only (`toolsets.py:223`). The denylist
    entries `"code_execution"` and `"run_command"` are **not real tool names** in
    0.14.0 (dead entries; harmless but misleading). `delegate_task` is grouped with
    code-exec in the leaf-blocked set (`delegate_tool.py:47`) and is also un-denied.
- **Evidence:** `src/.memoria/mcp/policy_hook.py:88-99`; `~/.hermes/hermes-agent/toolsets.py:142-145,187,223`;
  `tools/process_registry.py:1465,1539`; `tools/file_tools.py:1174-1177`.
- **Fix:** Add `process` (and `delegate_task`) to `DENY_DIRECT_TOOLS`; or, better,
  adopt B2's default-deny and retire the denylist.

### B4 — the gate cannot be fail-closed at the Hermes layer; plugin-hook errors fail OPEN (MEDIUM)

- **Severity:** Medium — partially self-acknowledged, but the plugin docstring
  overclaims ("can be made fail-CLOSED").
- **What 0.14.0 does:** `PluginManager.invoke_hook` wraps each callback in its own
  try/except; on exception it logs a warning and **continues** (the write proceeds) —
  `hermes_cli/plugins.py:1316-1329`. The Memoria `_gate` catches *its own* internal
  exceptions and returns block (fail-closed for errors it can observe,
  `plugins/memoria-policy-gate/__init__.py:54-55`), but if the callback never runs
  (registration failure, import error before `register`, an exception Hermes raises
  around the call) Hermes does not abort the tool. So the gate is fail-closed *on its
  own reachable decisions* only, never at the runtime boundary.
- **Evidence:** `hermes_cli/plugins.py:1316-1329`; the policy_hook.py docstring
  already documents this for shell hooks (`:45-51`); the plugin docstring claims it
  "can be made fail-CLOSED" (`__init__.py` header), which is true only for the
  in-callback path.
- **Fix:** Lower the residual risk — add a startup self-test that aborts if the plugin
  fails to register (so a silent non-registration is loud), and keep the
  "front writes with a bridge that calls policy internally" item on the roadmap as the
  only true fix.

### B5 — `checkpoints.enabled: true` snapshots nothing in the MCP-only model (MEDIUM)

- **Severity:** Medium — not a security gap, but a *false reliance*: all 5 profiles
  carry the comment "Shadow-git snapshot before destructive writes — mode-independent
  reversibility," and that reversibility does not exist for any Memoria write.
- **What 0.14.0 does:** the checkpoint manager only fires before the native tools
  `write_file`, `patch`, and destructive `terminal` commands
  (`agent/tool_executor.py:104-123, 564-585`). Every Memoria profile disables `file`
  and `terminal`, and all vault writes go through the **obsidian MCP**
  (`mcp_obsidian_*`), which is not in the checkpoint trigger set. Therefore
  `checkpoints.enabled: true` takes zero snapshots in normal operation. Memoria's
  actual reversibility comes from its own before/after-hash audit records written by
  `policy_hook.evaluate_post`, not from Hermes checkpoints.
- **Evidence:** `agent/tool_executor.py:104,114,564,576` (trigger keyed on
  `write_file`/`patch`/`terminal` only); profiles all list `file` + `terminal` in
  `disabled_toolsets`; `tools/checkpoint_manager.py` snapshots the working tree, not
  MCP effects.
- **Fix:** Either drop `checkpoints` from the profiles (it is inert) and let the
  comment describe the real mechanism (the policy_hook audit-pair), or — if shadow-git
  reversibility is wanted — note that it would only apply if/when the Engineer gains a
  real file/terminal lane.

---

## List A — 0.14 capabilities Memoria does not use but plausibly should

### A1 — Bitwarden Secrets Manager vs per-profile plaintext `.env` fan-out (HIGH value)

- **Hermes feature:** `secrets.bitwarden.*` — at startup (after `.env` load) Hermes
  runs `bws secret list <project_id>` and injects each secret into `os.environ` by
  name; the only credential on disk is `BWS_ACCESS_TOKEN` in `~/.hermes/.env`.
  Config keys: `secrets.bitwarden.{enabled, access_token_env, project_id,
  cache_ttl_seconds, override_existing, auto_install}`. CLI: `hermes secrets bitwarden
  setup|status|sync|sync --apply`.
  - Docs: `website/docs/user-guide/secrets/index`, `.../secrets/bitwarden.md`.
  - Source: `agent/secret_sources/bitwarden.py` (`apply_bitwarden_secrets` :432,
    sets `os.environ[key]` :503; `_run_bws_list` :355); wired at
    `hermes_cli/env_loader.py:213,218-244` (after `.env`, gated on
    `bitwarden.enabled`). Bulk-injection — **no `${SECRET:...}` placeholder syntax**;
    config `${VAR}` interpolation is the generic `os.environ` read at
    `hermes_cli/config.py:4139-4149`.
- **What Memoria does instead:** `scripts/install.sh:504-525` (`seed` helper) copies
  every shared key (`KILOCODE_API_KEY`, `OBSIDIAN_API_KEY`, `OPENALEX_API_KEY`,
  `S2_API_KEY`, `NCBI_EMAIL`, …) from `~/.hermes/.env` into **each of the 5
  per-profile `.env` files** (Hermes profile runs read only their own `.env`, no
  global fallback — Tier-4 confirmed in the installer comment). Result: every provider
  key sits in plaintext in 4–5 places; rotation means re-running `--profiles-only` to
  re-fan-out.
- **Improvement:** one bootstrap token instead of N×5 plaintext keys; rotate/revoke
  centrally in Bitwarden, every install picks it up next start; fewer secrets on disk.
  Caveat (from the docs themselves): for a single personal box it trades one
  credential for another plus a network dependency — so this is a *fleet/sandbox+prod*
  win, which matches Memoria's two-vault setup (memoria-test + memoria-private). Worth
  it as an option; not a slam-dunk for a lone laptop.

### A2 — auxiliary-model routing for cheap side-jobs (HIGH value)

- **Hermes feature:** `auxiliary.<task>.{provider, model, base_url, api_key, timeout}`
  routes ~11 operation classes (compression/summarization, vision, web-extract,
  title-generation, approval scoring, MCP routing, skills search, kanban
  specify/decompose, profile describe, curator) to a cheaper/faster model. Default is
  `provider: auto` = reuse the main model, so cheap routing is **opt-in and unused
  unless configured**.
  - Docs: `website/docs/user-guide/configuring-models` ("Auxiliary models").
  - Source: `agent/auxiliary_client.py` (router; `_resolve_task_provider_model`
    :4284-4340); config schema `hermes_cli/config.py:892-1005`.
- **What Memoria does instead:** Nothing — no profile sets an `auxiliary:` block, so
  every side-job runs on the lane's primary model. With the prod overlay
  (`install.sh:profile_model_default`) the Co-PI and Peer-reviewer run on
  **claude-opus-latest** and the Writer on **claude-sonnet-latest**; trajectory
  compression / title generation / approval scoring for those lanes all bill at the
  expensive model.
- **Improvement:** point `auxiliary.compression`, `auxiliary.title_generation`,
  `auxiliary.approval` (and, if Memoria ever uses native kanban, the decomposer slots)
  at Haiku/Flash. Direct API cost reduction on the highest-volume non-reasoning
  operations with no quality risk (these are mechanical sub-tasks). Cheap to adopt:
  one `auxiliary:` block per heavy-model profile.

### A3 — `reasoning_effort` per lane is recommended in comments but never set (MEDIUM)

- **Hermes feature:** `agent.reasoning_effort` per profile (the profile comments
  themselves say "Recommended: set agent.reasoning_effort per lane via `hermes -p …
  config set`").
- **What Memoria does:** Four profiles carry the *recommendation as a comment*
  (`memoria-{writer,engineer,librarian,peer-reviewer}/config.yaml:5`) but **no profile
  actually sets it**. The recommendation has been deferred indefinitely.
- **Improvement:** low effort on Librarian/Engineer (mechanical lanes) vs high on
  Peer-reviewer (verification) would cut tokens on the cheap lanes and raise rigor on
  the checking lane. Either set it or drop the comment — a recommendation that ships
  unset for 4 lanes is just noise.

### A4 — native `session_search` (deliberately disabled) leaves cross-session recall on the table (MEDIUM, deliberate)

- **Hermes feature:** `session_search` toolset — SQLite FTS5 full-text search over the
  agent's own past conversations (`~/.hermes/state.db`); lets a lane find and re-read
  what was discussed in prior sessions before re-asking.
  - Docs: `website/docs/user-guide/sessions`; `reference/tools-reference.md:153-157`.
  - Source: `tools/session_search_tool.py` (schema :463, registration :586);
    `toolsets.py:209-212`. No dedicated config block; governed by `sessions.*`
    retention (default OFF → recall preserved).
- **What Memoria does:** disables it in **every** profile.
- **Assessment — deliberate and largely correct, with one caveat.** For the Librarian/
  Writer/Engineer/Peer-reviewer worker lanes, isolation is the point (deterministic,
  task-scoped, auditable; ADR-46), so disabling it is right. **But the Co-PI is the
  one conversational, self-improving lane** (it alone keeps `memory`/`skills`), and it
  *also* disables `session_search`. For the Co-PI specifically, cross-session recall of
  prior conversations is the natural complement to `memory` — this is the one place
  where disabling it may be leaving recall on the table rather than buying isolation.
- **Improvement / question to resolve:** consider enabling `session_search` on
  **memoria-copi only**, with `sessions.retention_days` bounded. Note one privacy
  consequence: it would let the conversational lane recall raw prior-session content,
  which may be undesirable for a vault tool — so this is a deliberate trade to decide,
  not an obvious win. Recorded as "verify intent," not "adopt."

### A5 — the `memory` toolset is Co-PI-only — that is optimal; flagged only to confirm (LOW)

- **Hermes feature:** `memory` tool (single action-dispatched tool: add/replace/remove
  over `~/.hermes/memories/{MEMORY,USER}.md`, auto-injected into the system prompt;
  `memory.memory_enabled` etc.). Source: `tools/memory_tool.py:619-677`; config
  `agent/agent_init.py:1068-1077`.
- **What Memoria does:** only `memoria-copi` keeps it (verified: it is the one profile
  whose `disabled_toolsets` omits `memory`); the 4 worker lanes disable it.
- **Assessment:** This is **correct and optimal** as-is. The worker lanes are
  deterministic/auditable and must not carry mutable cross-session state into the gated
  write pipeline; the Co-PI is the self-improving loop (memory · /goals · skills ·
  /personality, D46). No change recommended — listed so the audit explicitly confirms
  the "only Co-PI enables it" choice is the right one rather than an oversight.

### A6 — native kanban / swarm / triage / per-task-model — mostly NOT applicable; one real gap (LOW–MEDIUM)

- **Hermes features (all in 0.14.0):** native kanban kernel (`hermes_cli/kanban_db.py`,
  SQLite state machine + dispatcher + dashboard), `delegate_task` with
  `delegation.{max_concurrent_children, max_spawn_depth, orchestrator_enabled}`
  (`tools/delegate_tool.py`), native swarm topology (`hermes_cli/kanban_swarm.py`,
  `hermes kanban swarm`), LLM auto-triage/decompose
  (`hermes_cli/kanban_decompose.py`, `kanban.auto_decompose`).
  - Docs: `website/docs/user-guide/features/{kanban,delegation}.md`.
- **What Memoria does:** runs its **own** kanban over MCP (`tasks_mcp.py`,
  `board_export*.py`) and routes writes via `delegate_route_task` through the `tasks`
  MCP server — a deliberate choice (ceiling-validated per lane, gated, ADR-48).
- **Assessment:** Replacing Memoria's gated, lane-ceiling kanban with the native kernel
  would *bypass the policy gate*, so it is correctly NOT adopted — this is a
  deliberate, sound divergence, not a missed feature.
- **The one real sub-finding:** native **per-card `model_override`** is
  **plumbed-but-unwired in 0.14.0** — the dispatcher honors it (`kanban_db.py:5613-5614`,
  `-m <model>`) but `create_task` (`:1527`) and every CLI/tool/swarm path never sets
  it, so it is not a usable feature in 0.14. **Therefore Memoria is not missing a
  working capability here** — if Memoria wants per-card model selection it must
  implement it itself regardless. Recorded so this is not mistaken for an available
  feature to "just turn on." Native swarm/triage are similarly moot under the
  gate-everything constraint.

### A7 — native cron vs external crontab wrappers (LOW, with a real caveat)

- **Hermes feature:** first-class scheduler (`cron/jobs.py`, `cron/scheduler.py`,
  `cronjob` tool) — interval/cron/one-shot schedules in `~/.hermes/cron/jobs.json`,
  ticked every 60s by the **gateway daemon**; per-job model/workdir/profile, skill
  loading, `context_from` chaining, lifecycle (pause/resume), recursion guard.
  Docs: `website/docs/user-guide/features/cron`; repo-root
  `hermes-already-has-routines.md`.
- **What Memoria does:** runs sweeps (retraction, `cron_heartbeat.py`) as cron-only
  operations outside Hermes (ADR-46/D41 — they run with no model, server-side).
- **Assessment / caveat:** Native cron **requires the gateway daemon to be running** —
  jobs don't fire otherwise (`hermes_cli/cron.py:122-124`). Memoria's sandbox does not
  assume a long-lived gateway, and its sweeps are deterministic no-LLM operations that
  *should not* go through an agent loop. So external scheduling is the correct fit for
  the integrity sweeps. Native cron would only be attractive for *agentic* recurring
  jobs (e.g. a scheduled Librarian discovery run) — none exist today. Low priority;
  flagged for completeness.

---

## Ranked top findings

**List B (assumed-but-unenforced boundaries) — highest impact first:**

1. **B1** `agent.disabled_toolsets` is schema-hiding only; `registry.dispatch` has no
   enablement check (`model_tools.py:366-381`, `tools/registry.py:393-405`). The
   "first wall" is a curtain.
2. **B2** the gate allows every non-obsidian, non-denylisted tool (`policy_hook.py:216-218`)
   — so for web/browser/messaging/delegate/process the sandbox rests entirely on B1.
3. **B3** `DENY_DIRECT_TOOLS` already misses `process` (a real 0.14 terminal-toolset
   tool) and lists dead names (`code_execution`, `run_command`) — incomplete against
   the installed version it is meant to backstop (`policy_hook.py:88-99` vs
   `toolsets.py:142-145`).
4. **B4** plugin-hook errors fail OPEN at the Hermes layer (`plugins.py:1316-1329`); the
   gate is fail-closed only on decisions it actually reaches.
5. **B5** `checkpoints.enabled: true` snapshots nothing — it triggers only on
   `write_file`/`patch`/`terminal`, none of which Memoria uses (`tool_executor.py:104-123`);
   the "reversibility" comment in all 5 profiles is false for vault writes.

**List A (unused capabilities worth adopting) — highest value first:**

1. **A1** Bitwarden Secrets Manager (`secrets.bitwarden.*`) vs fanning plaintext keys
   into 5 per-profile `.env`s — fleet-grade rotation, one credential on disk. Fits the
   two-vault setup; optional, not mandatory.
2. **A2** `auxiliary.*` model routing — currently unset, so Opus/Sonnet lanes bill
   compression/title/approval at the expensive model. Point them at Haiku/Flash for a
   direct cost cut with no quality risk.
3. **A3** `agent.reasoning_effort` per lane — recommended in 4 profile comments, set in
   none. Either set it (low on mechanical lanes, high on Peer-reviewer) or drop the
   comment.
4. **A4** `session_search` for **memoria-copi only** — disabled everywhere; worker-lane
   isolation is correct, but the conversational/self-improving Co-PI may be the one
   lane where cross-session recall is wanted. A deliberate privacy trade to decide, not
   an automatic win.
5. **A5–A7** confirmed *correct as-is*: `memory` Co-PI-only is optimal (A5); native
   kanban/swarm/triage are correctly bypassed for the gate (A6, and per-card
   `model_override` isn't even a working 0.14 feature); external cron fits the no-LLM
   sweeps (A7). Listed to close the sweep, no action.
