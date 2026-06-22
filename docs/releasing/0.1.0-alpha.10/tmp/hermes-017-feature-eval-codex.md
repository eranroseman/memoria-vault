# Hermes 0.17 feature evaluation — Codex

Fresh Codex analysis on 2026-06-22, verified against the local Hermes install:

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

## Detailed recommendations

### Kilo provider baseline

Production Memoria uses Kilo as the LLM provider. Local test profiles can render
as `provider: custom` against local `qwen2.5:7b`; do not infer production
provider strategy from that test-vault state.

Recommendation:

- Keep Kilo as the production main provider.
- Do not use OpenRouter `provider_routing` unless a profile is deliberately
  moved to OpenRouter.
- Configure cheap auxiliary model slots for title generation, compression, MCP
  routing, approval, and curator work.
- Configure lane-specific `agent.reasoning_effort`: low/none for deterministic
  lanes, high only for Writer or Peer-reviewer work that needs it.

### Bitwarden

Bitwarden Secrets Manager fits Memoria's multi-profile secret management problem.

Use it for shared provider/API secrets:

- Kilo provider key.
- Obsidian Local REST API key.
- Scholarly API keys such as Semantic Scholar, NCBI, and related lookup keys.
- Messaging or gateway tokens only when the same deployment owns them centrally.

Keep per-profile `.env` files only for the bootstrap token and values that are
truly profile-specific.

Pros:

- One rotation point for all Memoria profiles.
- Less duplicated plaintext in profile `.env` files.
- Each Hermes process picks up rotated values on next start.

Risks:

- `BWS_ACCESS_TOKEN` becomes the high-value bootstrap secret.
- Startup now depends on Bitwarden/network unless local fallbacks remain.
- Bitwarden centralizes secrets; it does not enforce lane policy.

Recommendation: adopt Bitwarden for shared secrets, while keeping profile
config, MCP allowlists, and policy gates as the actual boundaries.

### Multi-profile gateway multiplexing

Memoria aligns with Hermes' multiplexing use case when the goal is to run
several low-traffic profiles online from one host without one gateway service
per profile.

Use multiplexing for gateway/platform operation only:

- The default profile owns the gateway process.
- Secondary profiles are served through the multiplexer.
- Per-profile config, SOUL, skills, memory, and provider keys still resolve per
  routed profile.

Pros:

- Less service/process sprawl.
- One gateway to start, monitor, and restart.
- Fits a single-machine Memoria deployment.

Risks:

- One gateway crash affects every served profile.
- Secondary profiles lose process-level gateway isolation.
- Port-binding platforms must be configured only on the default profile.

Recommendation: pilot `gateway.multiplex_profiles: true` in `Memoria-test`.
Do not treat multiplexing as a security boundary; keep kanban lane isolation and
the Memoria policy plugin unchanged.

### Immediate clean next step

1. Migrate Hermes config to the current 0.17 schema.
2. Configure Bitwarden in the test vault and verify profile startup.
3. Pilot gateway multiplexing in the test vault.
4. Re-run `hermes_contract_doctor.py` and `board_export.py --cost-doctor`.
5. Promote only after one direct-tool deny and one Obsidian/MCP smoke pass.
