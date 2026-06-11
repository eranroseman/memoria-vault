---
title: Configure a profile
parent: Hermes Agent
nav_order: 1
---


# Configure a profile

Edit a profile's `config.yaml`, `SOUL.md`, skills, or lane-override to change its behavior — model routing, write permissions, or API credentials. Memoria ships five profiles: `memoria-copi`, `memoria-librarian`, `memoria-writer`, `memoria-peer-reviewer`, and `memoria-engineer` ([Profile capabilities](../../reference/profiles.md)).

## Where profile files live

Each profile has two locations:

| Location | Purpose |
| --- | --- |
| `<vault>/.memoria/profiles/memoria-<name>/` | **Vault source** — version-controlled, authoritative |
| `~/.hermes/profiles/memoria-<name>/` | **Deployed copy** — what Hermes actually runs |

Always edit the vault source. Re-deploy with `bash scripts/install.sh --profiles-only --vault <vault>` to push changes to the deployed copy. Never edit the deployed copy directly — it will be overwritten on the next install.

## File roles

| File | Controls | Who edits |
| --- | --- | --- |
| `SOUL.md` | Profile identity, posture, behavioral constraints | Author (you) |
| `config.yaml` | Model routing, `mcp_servers`, and the `plugins` block enabling the `memoria-policy-gate` write gate | Author (installer substitutes `{{PYTHON}}` and `{{VAULT_PATH}}`) |
| `distribution.yaml` | Packages the profile for `hermes profile install` | Author |
| `skills/` | Skill packages the profile can load | Author |
| `.env` (deployed copy only) | API keys and secrets | **Human only** — never committed to git |

The lane ceiling is the one piece that lives *outside* the profile directory: `<vault>/.memoria/lane-overrides/<name>.yaml` (see below).

## Change the model for a profile

Open `<vault>/.memoria/profiles/memoria-<name>/config.yaml` and edit the `model` field:

```yaml
model:
  provider: kilocode                       # your gateway/provider
  base_url: https://api.kilo.ai/api/gateway
  default: ~anthropic/claude-opus-latest   # the model string (provider/model)
```

The key is `default` (not `name`). For direct Anthropic instead, use `provider: anthropic`, `default: claude-opus-4-8`, and omit `base_url`. The shipped profiles set **only** the `model` block (plus `mcp_servers` and `plugins` blocks) — everything else inherits from the global `~/.hermes/config.yaml`, because Hermes replaces a config section wholesale rather than deep-merging.

Save and re-deploy: `bash scripts/install.sh --profiles-only --vault <vault>`.

## Auxiliary models (set globally, not per-profile)

Hermes runs several cheap, high-frequency tasks through *auxiliary* model slots — title generation, context compression, command approval, MCP tool routing, skills-hub search. Each defaults to `provider: auto`, meaning it **reuses the profile's main model**. For Memoria that's wasteful: a co-PI or Peer-reviewer compression/title call would burn **Opus**.

Set these once in your **global** `~/.hermes/config.yaml` — *not* in a profile's `config.yaml`. Hermes replaces a config section wholesale, so a per-profile `auxiliary:` block would clobber the global one. Use a **split**: the trivial, input-heavy slots go to **GLM 4.7 Flash** ($0.07/$0.40 per 1M — cheapest input), and `compression` goes to **DeepSeek V4 Flash** because its summary model must hold at least the main model's context window (DeepSeek's **1M** context gives headroom; GLM's 202K barely clears Claude's ~200K):

```yaml
auxiliary:
  title_generation: { provider: kilocode, model: z-ai/glm-4.7-flash }            # cheapest input
  approval:         { provider: kilocode, model: z-ai/glm-4.7-flash }
  mcp:              { provider: kilocode, model: z-ai/glm-4.7-flash }
  skills_hub:       { provider: kilocode, model: z-ai/glm-4.7-flash }
  compression:      { provider: kilocode, model: deepseek/deepseek-v4-flash }     # 1M ctx — safe summarizer
  # vision / web_extract: a cheap multimodal (e.g. google/gemini-2.5-flash) only if you use image/page analysis
```

> **Model-id format.** `z-ai/glm-4.7-flash` and `deepseek/deepseek-v4-flash` are **pinned** kilo ids (bare `provider/model`). The profiles' main models use the **rolling-alias** form `~anthropic/claude-<tier>-latest` (the `~` prefix denotes a rolling alias). Both are valid kilo gateway ids — browse them at `GET https://api.kilo.ai/api/gateway/models` (no auth). Two cost traps to avoid: `z-ai/glm-5-turbo` is **not** budget ($1.2/$4.0 per 1M), and GLM 4.7 Flash's 202K context is too tight for `compression` — hence DeepSeek there.

This keeps the expensive tiers (Sonnet/Opus) for actual agent work and routes the high-frequency bookkeeping calls to models that cost cents. Restart Hermes after editing the global config.

## Change write permissions (lane overrides)

Lane overrides are the per-profile write ceilings the policy MCP enforces. They live at `<vault>/.memoria/lane-overrides/<name>.yaml` (`copi`, `librarian`, `writer`, `peer-reviewer`, `engineer`), not inside the profile directory. The shipped Librarian lane, for example:

```yaml
profile: memoria-librarian
policy:
  allow:
    write:
      - "inbox/**"
      - "catalog/**"
      - "notes/fleeting/**"
      - "notes/source/**"
  deny:
    write:
      - "notes/claims/**"
      - "notes/hubs/**"
      - "notes/index/**"
      - "projects/**"
      - "system/**"
  require:
    - audit_log
    - timeout_required
    - source_tracking
routing:
  invocation: dispatched
  external_api_policy: explicit_only
  write_scope:
    - "inbox/"
    - "catalog/"
    - "notes/fleeting/"
    - "notes/source/"
```

A board card's `allowed_paths` may *narrow* a lane's scope but never widen it (lane = ceiling, payload = floor). You do **not** declare review-gating per lane: writes to the gated prefixes (`notes/claims/`, `notes/hubs/` — declared in `.memoria/schemas/folders.yaml`) automatically degrade to `dry_run` at the gate. `audit_log` is a token in the `require:` list (the log path is fixed at `system/logs/audit.jsonl`), not a key. Full shape and decision protocol: [Policy MCP](../../reference/policy-mcp.md).

After editing, re-deploy (`bash scripts/install.sh --profiles-only --vault <vault>`) — the installer picks up lane-override changes on every run.

## Add or remove a skill

Skills live in `<vault>/.memoria/profiles/memoria-<name>/skills/`, one directory per skill (e.g. the Librarian's `catalog-enrich-record` and `map-cluster-corpus`, the Peer-reviewer's `verify-check-citation`). To add a skill, copy the skill package into the profile's `skills/` directory and re-deploy. To remove one, delete the directory and re-deploy.

Note the tool side of the equation: `<vault>/.memoria/tool-registry.yaml` is the authoritative per-profile **tool** allowlist (default-deny). A new skill that needs a tool the registry withholds from that profile won't get it by being copied in.

## Update API credentials

Put keys in the **global** `~/.hermes/.env`, then propagate — profile runs read only their own `.env`, and the installer seeds each profile's `.env` from the global file without overwriting existing values:

```bash
# edit ~/.hermes/.env, then:
bash scripts/install.sh --profiles-only --vault <vault>
```

To change a single profile's value directly, edit `~/.hermes/profiles/memoria-<name>/.env` — no installer run needed; `.env` changes take effect on the next session start. `.env` files are never committed and never overwritten by re-installs.

## Verify a configuration change

After re-deploying:

```bash
hermes profile show memoria-<name>
```

Confirms the deployed profile reflects your vault source changes (`SOUL.md`, MCP servers, skills, `.env` key names with values redacted).

For lane-override changes, check `system/logs/audit.jsonl` after the next write operation to confirm the new policy is enforced — or test a single decision one-shot:

```bash
.memoria/.venv/bin/python .memoria/mcp/policy_mcp.py --vault <vault> \
  --decide '{"profile":"memoria-librarian","action":"write","path":"notes/claims/x.md","task_id":"T1"}'
```

## Related

- Deploy vault source to profiles: [Redeploy profiles](../operate/redeploy-profiles.md)
- Fix profile drift (deployed ≠ source): [Fix profile drift](../troubleshooting/fix-profile-drift.md)
- Lane-override reference: [Policy MCP](../../reference/policy-mcp.md)
- The five profiles and their ceilings: [Profile capabilities](../../reference/profiles.md)
