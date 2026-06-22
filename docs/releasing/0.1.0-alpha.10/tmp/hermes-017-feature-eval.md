# Hermes 0.17 feature evaluation

Fresh analysis on 2026-06-22, verified against the local Hermes install:

```text
Hermes Agent v0.17.0 (2026.6.19) · upstream b1b20270
```

## Local verification

- `hermes --version` reports v0.17.0 and up to date.
- `hermes profile list` shows the five Memoria profiles installed; gateways were
  stopped during verification.
- `hermes -p memoria-copi config show` shows the local test profile rendered as
  `provider: custom` against local `qwen2.5:7b`. Production Memoria uses Kilo;
  treat local model output as test-vault evidence, not the production target.
- `hermes prompt-size --profile memoria-copi` reports 28 tools and about 49 KB
  of tool schemas; `AGENTS.md` is truncated at the current context-file limit.
- `python src/.memoria/mcp/hermes_contract_doctor.py --vault /home/eranr/Memoria-test --json`
  passed with `ok: true`, with a warning for dead denylist names.
- `python src/.memoria/mcp/board_export.py --cost-doctor` passed with `ok: true`.
- `hermes doctor` found the default profile still has stale config: unknown
  provider `ollama` and config version `v23 -> v30`.

## Feature evaluation

| Hermes 0.17 feature | Used by Memoria? | Assessment |
| --- | --- | --- |
| Kilo/provider routing | Yes, production | Keep Kilo as the production main provider. OpenRouter `provider_routing` is irrelevant unless a profile actually moves to OpenRouter. |
| Auxiliary model slots | Partly | Use explicitly. Route title generation, compression, MCP routing, approval, and curator work to cheap models. |
| `reasoning_effort` | Not effectively | Set per lane: low/none for deterministic work, high only for Writer/Peer-reviewer work that needs it. |
| Managed scope | No | Skip for normal Memoria. Useful only to pin admin-owned non-secret config on a shared host. |
| Bitwarden Secrets Manager | No | Adopt for shared profile secrets: Kilo, Obsidian, scholarly APIs, and centrally-owned gateway tokens. Keep the bootstrap token protected. |
| Multi-profile gateway multiplexing | No | Pilot in `Memoria-test` for gateway/platform operation. It reduces service sprawl but is not a policy boundary. |
| Machine-level dashboard/profile switcher | Not core | Use for inspection and admin, not as source of truth. |
| MCP catalog/OAuth/tool filters | Partly | Memoria already uses MCP well. Add explicit include filters for upstream MCPs with mutating or irrelevant tools. |
| Late-connecting MCP refresh and HTTP keepalive | Implicit | Good for Obsidian MCP reliability. No design change except stop assuming startup discovery is the only discovery point. |
| Tool Search | Auto/implicit | Leave `auto`; Memoria has enough MCP tools for savings, but forcing it on adds round trips. |
| Cron lifecycle and no-agent jobs | Partly outside Hermes | Move deterministic sweeps/heartbeats to no-agent cron where practical. Use agent cron only for narrative work. |
| Kanban workers, review status, artifacts | Yes | Keep kanban as the work queue. Consider native judge/review status as an automated pre-filter, not a replacement for human approval. |
| Built-in memory and write approval | Partly | Use only for Co-PI preferences and durable runtime lessons. Enable write approval. Canonical knowledge stays in the vault. |
| External memory providers/Honcho | No | Do not adopt for core Memoria. Optional later for personalization only. |
| Skills opt-out / skill diff / curator / simplify-code | Partly | Memoria profiles should opt out of bundled skill seeding and keep lane skills only. |
| Nous Tool Gateway | No | Keep off by default. Memoria scholarly discovery should stay through curated MCPs. |
| Billing, insights, cost columns | Yes | Cost doctor passes. Keep cost telemetry as a release gate when cloud models are active. |
| Web/X search | No | Keep disabled for core literature work; use paper-search, Zotero, and deterministic ingest. |
| Deliverable mode/artifacts | Not core | Useful for messaging delivery. For Obsidian-first workflow, kanban artifacts are enough. |
| Image/TTS/voice/computer-use/Raft/media tools | No | Skip; they do not improve core Memoria requirements today. |
| `hermes security audit` | No | Add to release/runbook checks for third-party MCP and Python dependency drift. |

## Usage quality

Used well:

- Profiles for lane separation.
- Native Obsidian MCP over loopback HTTPS.
- Memoria MCP servers for deterministic operations.
- Policy plugin as the hard write gate.
- Kanban as the durable queue.

Used sub-optimally:

- Subtractive `disabled_toolsets` is brittle when Hermes adds new tools. Prefer
  positive `enabled_toolsets` if current Hermes behavior and policy tests confirm
  it closes new tools by default.
- Cost capture still leans on session/state inspection. Prefer plugin hook capture
  if `post_llm_call` exposes the needed usage and cost details on-box.
- Auxiliary models and reasoning effort are not yet first-class profile policy.
- Bundled skills were seeded broadly; lane profiles should stay narrower.

Not used, should be piloted:

- Bitwarden for shared secrets.
- Gateway multiplexing in `Memoria-test`.
- Native kanban judge/review as a pre-filter.
- Hermes security audit.

Not used, correctly excluded:

- Direct file, terminal, browser, computer-use, broad web/search, media, and
  messaging tools for core lane profiles.
- External memory providers for canonical knowledge.
- Tool Gateway for scholarly discovery.

## Clean-slate architecture

Requirements:

- PI works from Obsidian.
- Durable knowledge is Markdown plus schemas in the vault.
- Every canonical write is gated and auditable.
- Agents do not get direct file/terminal/code execution for vault work.
- Multi-agent work is queued, inspectable, and recoverable.
- Cost and disposition are captured.

Recommended architecture:

1. `memoria-copi` is the only conversational agent. It is read-only and delegates
   durable work to kanban.
2. Librarian, Writer, Peer-reviewer, and Engineer are lane profiles with only
   lane skills, lane MCPs, and lane write ceilings.
3. Canonical knowledge stays in Obsidian/vault schemas; Hermes memory stores only
   preferences and runtime lessons, with write approval on.
4. One Memoria policy plugin owns write gating and should also own audit/cost
   hooks if Hermes hook payloads stay stable.
5. Bitwarden supplies shared secrets across profiles; it does not define policy.
6. Gateway multiplexing is an operational deployment mode, not an isolation
   mechanism.
7. Deterministic jobs run as no-agent cron where possible; LLM work becomes
   kanban cards.
8. Tool Search stays `auto`; positive tool allowlists should replace subtractive
   denylists only after a deny-path test proves the behavior.

## Ranked recommendations

1. Migrate Hermes config to the current 0.17 schema and remove stale `ollama`
   config from the default profile.
2. Adopt Bitwarden for shared profile secrets.
3. Pilot `gateway.multiplex_profiles: true` in `Memoria-test`.
4. Set auxiliary model slots and per-lane `reasoning_effort`.
5. Opt Memoria lane profiles out of bundled skill seeding.
6. Evaluate positive `enabled_toolsets` with a live deny-path test.
7. Move cost capture into plugin hooks if local hook payloads provide stable
   usage/cost data.
8. Add `hermes security audit` to release validation.
9. Keep broad direct tools disabled for core Memoria lanes.
