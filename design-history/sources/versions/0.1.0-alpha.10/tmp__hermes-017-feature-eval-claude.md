# Hermes 0.17 feature evaluation — reconciled

Reconciled report (2026-06-22) merging the Codex evaluation
(`hermes-017-feature-eval-codex.md`) and the Claude source-verified variant.
Codex contributes operational/deployment breadth and production-provider
grounding; Claude contributes source-level verification that de-risks the two
highest-value items. Verified against the local install at
`~/.hermes/hermes-agent` (v0.17.0).

## Local verification

CLI surface (Codex):

- `hermes --version` reports v0.17.0, up to date.
- `hermes profile list` shows the five Memoria profiles installed.
- `hermes -p memoria-copi config show` renders the local test profile as
  `provider: custom` against local `qwen2.5:7b`. **Production Memoria uses Kilo**;
  treat local model output as test-vault evidence, not the production target.
- `hermes prompt-size --profile memoria-copi` reports 28 tools, ~49 KB of tool
  schemas; `AGENTS.md` is truncated at the context-file limit.
- `hermes_contract_doctor.py --json` → `ok: true` (warning: dead denylist names).
- `board_export.py --cost-doctor` → `ok: true`.
- `hermes doctor` flags the default profile's stale config: unknown provider
  `ollama`, config version `v23 -> v30`.

Source level (Claude) — these turn two conditional recommendations into confirmed:

- `platform_toolsets` (positive allowlist) **and** `disabled_toolsets` (subtractive)
  are both first-class — `model_tools.py:277-397`, `toolsets.py`. The allowlist
  switch is feasible today, not pending a test.
- Plugin lifecycle hooks are real and in-process: `register_hook("pre_tool_call" |
  "post_tool_call" | "pre_llm_call" | "post_llm_call" | "post_api_request" |
  "on_session_end")` — `plugins/observability/langfuse/__init__.py:1132`,
  `plugins/disk-cleanup/__init__.py:310`.
- The post-LLM hook payload carries input/output/cache/reasoning tokens **and**
  runs `get_pricing_entry` / `estimate_usage_cost` → `cost_details.total` (USD).
  The cost-capture migration is confirmed feasible, not conditional.
- Native kanban has an auxiliary-judge completion gate and a native `review`
  status — `hermes_cli/kanban_db.py:822-826,1060`, `VALID_STATUSES`.
- `reasoning_effort` (`parse_reasoning_effort`) and the `auxiliary:` config block
  exist and are per-profile.

## Feature evaluation

| Hermes 0.17 feature | Used by Memoria? | Assessment |
| --- | --- | --- |
| Kilo/provider routing | Yes, production | Keep Kilo as the production main provider. OpenRouter `provider_routing` is irrelevant unless a profile actually moves to OpenRouter. |
| Auxiliary model slots | Partly | Route title generation, compression, MCP routing, approval, and curator work to cheap models. Config-only. |
| `reasoning_effort` | Not effectively | Set per lane: low/none for deterministic work, high only for Writer/Peer-reviewer. Config-only. |
| `platform_toolsets` allowlist | No (subtractive instead) | Confirmed first-class (`model_tools.py:277-397`). Replace computed `disabled_toolsets`; closes new upstream toolsets by default. |
| `post_llm_call` cost hook | No (state.db join) | Confirmed to carry `cost_details.total`. Move ADR-106 cost capture into the gate plugin's hook; retire the brittle session-store join. |
| Managed scope | No | Skip. Useful only to pin admin-owned non-secret config on a shared host. |
| Bitwarden Secrets Manager | No | Adopt for shared profile secrets (Kilo, Obsidian, scholarly APIs, central gateway tokens). |
| Multi-profile gateway multiplexing | No | Pilot in `Memoria-test`. Reduces service sprawl; not a policy boundary. |
| Dashboard/profile switcher | Not core | Inspection/admin only, not source of truth. |
| MCP catalog/OAuth/tool filters | Partly | Add explicit include filters for upstream MCPs with mutating/irrelevant tools. |
| Late MCP refresh / HTTP keepalive | Implicit | Good for Obsidian MCP reliability; stop assuming startup is the only discovery point. |
| Tool Search | Auto/implicit | Leave `auto`; forcing on adds round trips. |
| Cron lifecycle / no-agent jobs | Partly | Move deterministic sweeps/heartbeats to no-agent cron; agent cron only for narrative work. |
| Kanban workers, judge, review status | Yes | Keep kanban as the queue. Use native judge/`review` status as an automated pre-filter, never a replacement for human approval. |
| Built-in memory + write approval | Partly | Co-PI preferences and durable runtime lessons only, write approval on. Canonical knowledge stays in the vault. |
| External memory providers/Honcho | No | Not for core Memoria. Optional later for personalization. |
| Skills opt-out / curator | Partly | Lane profiles opt out of bundled skill seeding; keep lane skills only. |
| Nous Tool Gateway | No | Keep off. Scholarly discovery stays through curated MCPs. |
| Billing/insights/cost columns | Yes | Cost doctor passes; keep cost telemetry as a release gate when cloud models are active. |
| Web/X search | No | Disabled for core literature work; use paper-search, Zotero, deterministic ingest. |
| Deliverable mode/artifacts | Not core | Useful for messaging delivery; kanban artifacts suffice for Obsidian-first. |
| Image/TTS/voice/computer-use/media | No | Skip; no core-requirement gain today. |
| ADR-105 diagnostic plane (hand-rolled) | Yes, bespoke | Fold into the gate plugin's `post_tool_call`/`post_llm_call`/`on_session_end` hooks; keep the redaction policy. |
| `hermes security audit` | No | Add to release/runbook checks for third-party MCP + Python dependency drift. |

## Usage quality

Used well: profiles for lane separation; native Obsidian MCP over loopback HTTPS;
Memoria MCP servers for deterministic ops; policy plugin as the hard write gate;
kanban as the durable queue.

Used sub-optimally:

- Subtractive `disabled_toolsets` is brittle when Hermes adds tools. Switch to
  positive `platform_toolsets` (confirmed first-class; no test gate needed).
- Cost capture leans on session/`state.db` inspection. Move to the `post_llm_call`
  hook (confirmed to expose tokens + `cost_details.total`).
- Auxiliary models and `reasoning_effort` are not yet first-class profile policy.
- Bundled skills were seeded broadly; lane profiles should stay narrower.
- Default profile carries stale config (`ollama`, `v23 -> v30`).

Not used, should be piloted: Bitwarden for shared secrets; gateway multiplexing in
`Memoria-test`; native kanban judge/review as a pre-filter; `hermes security audit`.

Not used, correctly excluded: direct file/terminal/browser/computer-use/media,
broad web/X search, and messaging tools for core lane profiles; external memory
providers for canonical knowledge; Tool Gateway for scholarly discovery; Hermes
checkpoints (snapshot only native writes, not MCP — irrelevant to our write path).

Watch: 0.17 makes "new plugins/memory backends must be standalone, must not modify
core files" a hard upstream constraint. `memoria-policy-gate` already complies.

## Clean-slate architecture (requirements-first)

Requirements: PI works from Obsidian; durable knowledge is Markdown + schemas in
the vault; every canonical write is gated and auditable; agents get no direct
file/terminal/code execution for vault work; multi-agent work is queued and
recoverable; cost and disposition are captured.

The shape barely changes — ADR-22's bet holds — with these decisions:

1. `memoria-copi` is the only conversational agent: read-only, delegates durable
   work to kanban.
2. Librarian, Writer, Peer-reviewer, Engineer are lane profiles with only lane
   skills, lane MCPs, and lane write ceilings.
3. Canonical knowledge stays in the vault; Hermes memory stores only preferences
   and runtime lessons, write approval on.
4. **One Memoria plugin owns gate + audit + cost + diagnostics** via four hooks
   (`pre_tool_call` gate, `post_tool_call` audit, `post_llm_call` cost,
   `on_session_end` diagnostics) — replacing plugin + `state.db` join + the
   separate ADR-105 plane.
5. **`platform_toolsets`** replaces the computed `disabled_toolsets`.
6. **Native kanban judge** runs as the automated pre-filter into the human review
   gate (native `review` status).
7. **Auxiliary routing + per-profile `reasoning_effort`** set from day one.
8. Bitwarden supplies shared secrets across profiles; it does not define policy.
9. Gateway multiplexing is an operational deployment mode, not an isolation
   mechanism.
10. Deterministic jobs run as no-agent cron where possible; LLM work becomes
    kanban cards.

Everything else (kanban queue, profiles, native Obsidian MCP, MCP-only sandbox,
deterministic ingest ADR-30, human approval gate) survives unchanged — the
strongest evidence ADR-22 was correct.

## Ranked recommendations

Confirmed-feasible engineering wins (kill upgrade-brittleness; both verified on
this install) come first; operational hygiene and pilots follow:

1. **Move cost capture into a `post_llm_call` hook; retire the `state.db` join.**
   Confirmed: the hook carries tokens + `cost_details.total`.
2. **Switch profile gating to `platform_toolsets`.** Confirmed first-class; no
   deny-path test gate needed (run the existing policy tests to confirm closure).
3. **Migrate Hermes config to the 0.17 schema**; remove stale `ollama` config from
   the default profile.
4. **Set auxiliary model slots + per-lane `reasoning_effort`** (the easy #859 items).
5. **Adopt Bitwarden for shared profile secrets** (Kilo, Obsidian, scholarly API
   keys); keep per-profile `.env` for the bootstrap token and profile-specific
   values. Risk: `BWS_ACCESS_TOKEN` becomes the high-value bootstrap secret and
   startup depends on Bitwarden/network unless a local fallback remains.
6. **Pilot `gateway.multiplex_profiles: true` in `Memoria-test`.** Risk: one
   gateway crash affects every served profile; not a security boundary.
7. **Use the native kanban judge as a pre-filter** before the human gate.
8. **Opt Memoria lane profiles out of bundled skill seeding.**
9. **Fold ADR-105 diagnostics into the gate plugin's hooks.**
10. **Add `hermes security audit` to release validation.**
11. **Keep broad direct tools disabled for core Memoria lanes** — 0.17 didn't
    change why.

After any change: re-run `hermes_contract_doctor.py` and `board_export.py
--cost-doctor`, and promote only after one direct-tool deny and one Obsidian/MCP
smoke pass.
