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

The auxiliary slots (title generation, context compression, command approval, MCP routing, skills-hub search) each default to `provider: auto`, which reuses the profile's main model — wasteful, since it would route these high-frequency bookkeeping calls through Opus. Set them once in your **global** `~/.hermes/config.yaml` (not a profile's — Hermes replaces a config section wholesale, so a per-profile `auxiliary:` block would clobber the global one) to route them to cheap models:

```yaml
auxiliary:
  title_generation: { provider: kilocode, model: z-ai/glm-4.7-flash }            # cheapest input
  approval:         { provider: kilocode, model: z-ai/glm-4.7-flash }
  mcp:              { provider: kilocode, model: z-ai/glm-4.7-flash }
  skills_hub:       { provider: kilocode, model: z-ai/glm-4.7-flash }
  compression:      { provider: kilocode, model: deepseek/deepseek-v4-flash }     # 1M ctx — must hold the main model's window
  # vision / web_extract: a cheap multimodal (e.g. google/gemini-2.5-flash) only if you use image/page analysis
```

`compression` needs a model whose context window holds at least the main model's, hence DeepSeek's 1M (GLM's 202K is too tight). Browse valid kilo ids at `GET https://api.kilo.ai/api/gateway/models` (no auth). Restart Hermes after editing the global config.

## Change write permissions (lane overrides)

Lane overrides are the per-profile write ceilings the policy MCP enforces. They live at `<vault>/.memoria/lane-overrides/<name>.yaml` (`copi`, `librarian`, `writer`, `peer-reviewer`, `engineer`), not inside the profile directory. To change a profile's write scope, edit its file and re-deploy — the full file shape (`policy.allow`/`deny`, `require`, `routing`) and the decision protocol are in [Policy MCP](../../reference/policy-mcp.md).

Two things that bite when editing a lane:

- A board card's `allowed_paths` may *narrow* a lane's scope but never widen it (lane = ceiling, payload = floor).
- You do **not** declare review-gating per lane: writes to the gated prefixes (`notes/claims/`, `notes/hubs/` — declared in `.memoria/schemas/folders.yaml`) automatically degrade to `dry_run` at the gate.

After editing, re-deploy (`bash scripts/install.sh --profiles-only --vault <vault>`) — the installer picks up lane-override changes on every run.

## Add or remove a skill

Skills live in `<vault>/.memoria/profiles/memoria-<name>/skills/`, one directory per skill (e.g. the Librarian's `catalog-enrich-record` and `map-cluster-corpus`, the Peer-reviewer's `verify-check-citation`). To add a skill, copy the skill package into the profile's `skills/` directory and re-deploy. To remove one, delete the directory and re-deploy.

Note the tool side of the equation: `<vault>/.memoria/tool-registry.yaml` is the authoritative per-profile **tool** allowlist (default-deny). A new skill that needs a tool the registry withholds from that profile won't get it by being copied in.

## Update API credentials

Put keys in the shared Hermes env file, then propagate — profile runs read only their own `.env`:

```bash
# edit ~/.hermes/.env, then:
bash scripts/install.sh --profiles-only --vault <vault>
```

```powershell
# edit %LOCALAPPDATA%\hermes\.env, then:
.\scripts\install.ps1 -ProfilesOnly -Vault <vault>
```

Always edit the shared Hermes env file and re-run `--profiles-only` — hand-editing the installer-managed per-profile `.env` files drifts from the shared source. How `--profiles-only` seeds each profile's `.env` is in [Redeploy profiles](../operate/redeploy-profiles.md).

## Verify a configuration change

After re-deploying:

```bash
hermes profile show memoria-<name>
```

Confirms the deployed profile reflects your vault source changes (`SOUL.md`, MCP servers, skills, `.env` key names with values redacted).

For lane-override changes, check `system/logs/audit.jsonl` after the next write operation to confirm the new policy is enforced — or test a single decision one-shot:

```bash
python3 .memoria/mcp/policy_mcp.py --vault <vault> \
  --decide '{"profile":"memoria-librarian","action":"write","path":"notes/claims/x.md","task_id":"T1"}'
```

## Related

- Deploy vault source to profiles: [Redeploy profiles](../operate/redeploy-profiles.md)
- Fix profile drift (deployed ≠ source): [Fix profile drift](../troubleshooting/fix-profile-drift.md)
- Lane-override reference: [Policy MCP](../../reference/policy-mcp.md)
- The five profiles and their ceilings: [Profile capabilities](../../reference/profiles.md)
