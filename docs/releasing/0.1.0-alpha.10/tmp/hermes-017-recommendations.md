# Hermes 0.17 Memoria recommendations

Fresh recommendation after verifying the installed Hermes 0.17 runtime.

## Provider baseline

Production Memoria uses Kilo as the LLM provider. The local test profiles seen
on 2026-06-22 rendered as `provider: custom` against local `qwen2.5:7b`; treat
that as test-vault evidence, not the production design target.

Recommendation:

- Keep Kilo as the production main provider.
- Do not use OpenRouter `provider_routing` unless a profile is actually moved to
  OpenRouter.
- Set cheap auxiliary slots for title generation, compression, MCP routing,
  approval, and curator work so lane models do not pay premium tokens for
  bookkeeping.
- Set lane-specific `agent.reasoning_effort`: low/none for deterministic lanes,
  high only for Writer or Peer-reviewer work that needs it.

## Bitwarden

Bitwarden Secrets Manager fits Memoria's multi-profile secret problem.

Use it for shared provider/API secrets:

- Kilo provider key.
- Obsidian Local REST API key.
- Scholarly API keys such as Semantic Scholar, NCBI, and related lookup keys.
- Messaging or gateway tokens only when the same deployment owns them centrally.

Keep per-profile `.env` files only for the bootstrap token and values that are
truly profile-specific.

Pros:

- One rotation point for five profiles.
- Less duplicated plaintext in profile `.env` files.
- Each Hermes process picks up rotated values on next start.

Risks:

- `BWS_ACCESS_TOKEN` becomes the high-value bootstrap secret.
- Startup now depends on Bitwarden/network unless local fallbacks remain.
- Bitwarden centralizes secrets; it does not enforce lane policy.

Recommendation: adopt Bitwarden for shared secrets, but keep profile config,
MCP allowlists, and policy gates as the real boundaries.

## Multi-profile gateway multiplexing

Memoria aligns with Hermes' multiplexing use case if the goal is to run several
low-traffic profiles online from one host without five gateway services.

Use multiplexing for gateway/platform operation only:

- The default profile owns the gateway process.
- Secondary profiles are served through the multiplexer.
- Per-profile config, SOUL, skills, memory, and provider keys still resolve per
  routed profile.

Do not treat multiplexing as a security boundary.

Pros:

- Less service/process sprawl.
- One gateway to start, monitor, and restart.
- Fits a single-machine Memoria deployment.

Risks:

- One gateway crash affects every served profile.
- Secondary profiles lose process-level gateway isolation.
- Port-binding platforms must be configured only on the default profile.

Recommendation: pilot `gateway.multiplex_profiles: true` in `Memoria-test`.
Keep kanban lane isolation and the Memoria policy plugin unchanged.

## Clean next step

1. Migrate Hermes config to the current 0.17 schema.
2. Configure Bitwarden in the test vault and verify profile startup.
3. Pilot gateway multiplexing in the test vault.
4. Re-run `hermes_contract_doctor.py` and `board_export.py --cost-doctor`.
5. Promote only after one direct-tool deny and one Obsidian/MCP smoke pass.
