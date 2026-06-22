# Hermes 0.17 feature evaluation + clean-slate recommendations

Fresh analysis (2026-06-22) of every relevant Hermes 0.17 capability vs Memoria,
verified against the local install at `~/.hermes/hermes-agent` (v0.17.0).

## Verified against the local install

- `enabled_toolsets` (positive allowlist) **and** `disabled_toolsets` (subtractive)
  are both first-class — `model_tools.py:277-397`, `toolsets.py`.
- Plugin lifecycle hooks are real and in-process: `register_hook("pre_tool_call" |
  "post_tool_call" | "pre_llm_call" | "post_llm_call" | "post_api_request" |
  "on_session_end")` — `plugins/observability/langfuse/__init__.py:1132`,
  `plugins/disk-cleanup/__init__.py:310`.
- The post-LLM hook payload carries input/output/cache/reasoning tokens **and**
  runs `get_pricing_entry` / `estimate_usage_cost` → `cost_details.total` (USD).
- Native kanban has an auxiliary-judge completion gate and a native `review`
  status — `hermes_cli/kanban_db.py:822-826,1060`, `VALID_STATUSES`.
- `reasoning_effort` (`parse_reasoning_effort`) and the `auxiliary:` config block
  exist and are per-profile.
- Contract/cost doctors already report `ok:true` on this version.

## Used today, near-optimal — leave alone

Kanban as the authoritative queue; profiles for agent isolation; MCP hosting from
per-profile `config.yaml`; native Obsidian MCP over HTTP (ADR-31); plugin
`pre/post_tool_call` gate (ADR-28); per-profile main-loop model routing.

## Used sub-optimally — the real wins

1. **Toolset gating is subtractive (`disabled_toolsets`) — flip to `enabled_toolsets`.**
   Computing `disabled = all − allow` means every upstream toolset addition (0.17
   added `computer_use`, more `kanban_*`, `cronjob`) silently widens the schema
   surface until the contract doctor catches it. A positive allowlist closes new
   toolsets by default and shrinks the contract doctor to "is the hard-deny still
   complete." Contradicts the current ADR-27 mechanism.

2. **Cost capture joins the internal `state.db` — move it to a `post_llm_call` hook.**
   ADR-106 reverse-engineers `~/.hermes/profiles/<lane>/state.db`; the upgrade
   notes flag it as brittle (re-run the cost doctor every upgrade, ~1/13 miss from
   session rotation). The post-LLM hook delivers per-call tokens + computed USD
   in-process, fail-closed, upgrade-stable. Capture it in the same plugin that
   already runs the gate. Collapses ADR-106's "brittle join vs deferred proxy
   daemon" dilemma — the hook is neither.

3. **No auxiliary-model routing (#859).** Title/compression/MCP-arg/judge calls run
   on each profile's main model. Route them to a cheap tier via the `auxiliary:`
   block. Config-only cost win.

4. **No per-profile `reasoning_effort` (#859).** Librarian/engineer (mechanical,
   Haiku) don't need extended reasoning; peer-reviewer does. Config-only.

5. **ADR-105 diagnostic plane is hand-rolled.** Emit content-light observability
   from the existing gate plugin's `post_tool_call` / `post_llm_call` /
   `on_session_end` hooks instead of a separate plane. Keep the redaction policy.

## Not used — should evaluate

- **Native kanban auxiliary-judge + `review` status.** Use the judge as an
  automated *pre-filter* feeding the human approval gate (not a replacement — the
  human gate is a hard requirement). The judge catches obvious failures so fewer
  cards reach review.
- **`hermes security audit`** (OSV supply-chain scan of venv + pinned MCP servers).
  Memoria ships third-party MCP servers (paper_search, pyzotero) with no current
  supply-chain check — add to the release runbook.
- **`insights` / session analytics** — overlaps with the bespoke cost pipeline;
  look before extending it.

## Not used — correctly excluded (confirm, don't adopt)

`write_file` / `terminal` / `execute_code` / `read_file` / `patch` (MCP-only
sandbox, ADR-46 — still the exact toolsets the hard-deny must cover; 0.17 didn't
rename them); `browser_*`, `computer_use`, messaging gateways, `delegate_task`,
`cronjob` tool, `homeassistant_*`, `spotify_*`, external memory providers,
desktop/dashboard GUIs, proxy, ACP-as-front, webhooks, Bitwarden (manual `.env`
until multi-machine sharing is real — YAGNI); Hermes checkpoints (snapshot only
native writes, not MCP — irrelevant to our write path).

Watch: 0.17 makes "new plugins/memory backends must be standalone, must not modify
core files" a hard upstream constraint. `memoria-policy-gate` already complies.

## Clean-slate architecture (requirements-first)

Requirements: every feature PI-accessible directly from Obsidian; no agent gets
file/terminal/code execution; human approval gate before canonical; durable
multi-agent queue; auditable fail-closed writes; cost/disposition captured.

The shape barely changes — ADR-22's bet holds — but four wiring decisions flip:

1. **One Memoria plugin owns gate + audit + cost + diagnostics** via four hooks
   (`pre_tool_call` gate, `post_tool_call` audit, `post_llm_call` cost,
   `on_session_end` diagnostics), instead of plugin + `state.db` join + separate
   ADR-105 plane.
2. **`enabled_toolsets`** replaces the computed `disabled_toolsets`.
3. **Native kanban judge** runs as the automated pre-filter into the human review
   gate (native `review` status).
4. **Auxiliary routing + per-profile `reasoning_effort`** set from day one.

Everything else (kanban queue, profiles, native Obsidian MCP, MCP-only sandbox,
deterministic ingest ADR-30, human approval gate) survives unchanged — the
strongest evidence ADR-22 was correct.

## Recommendations, ranked

1. Move cost capture into a `post_llm_call` hook; retire the `state.db` join.
2. Switch profile gating to `enabled_toolsets`.
3. Adopt auxiliary routing + per-profile `reasoning_effort` (the easy #859 items).
4. Use the native kanban judge as a pre-filter before the human gate.
5. Add `hermes security audit` to the release runbook.
6. Fold ADR-105 diagnostics into the gate plugin's hooks.
7. Leave everything in "correctly excluded" denied — 0.17 didn't change why.
