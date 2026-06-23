---
title: Configure a profile
parent: Hermes Agent
nav_order: 1
---


# Configure a profile

A **profile** is the per-worker configuration for one Hermes worker. Editing a profile changes how that worker behaves: which model it routes to, what it is allowed to write, and which API credentials it uses. Each background worker on the kanban board is a **lane**; the conversational agent you talk to is the **Co-PI**.

This page collects the common configuration tasks. Each section is a self-contained procedure: change the model overlay, change auxiliary models, change write permissions, add or remove a skill, update API credentials, and verify your change.

Memoria ships five profiles: `memoria-copi`, `memoria-librarian`, `memoria-writer`, `memoria-peer-reviewer`, and `memoria-engineer`. For what each one can do, see [Profile capabilities](../../reference/profiles.md).

> **Don't hand-edit tool allowlists.** To change which tools a profile can use, edit `src/.memoria/tool-registry.yaml` and run `scripts/render_profile_configs.py --write`. Do not hand-edit the generated `platform_toolsets` block (the rendered list of built-in tool groups) or the MCP `tools.include` blocks — they are regenerated from the registry.

## Where profile files live

Each profile exists in two places. Edit the first; the installer copies it to the second.

| Location | Purpose |
| --- | --- |
| `<vault>/.memoria/profiles/memoria-<name>/` | **Vault source** — version-controlled, authoritative |
| `~/.hermes/profiles/memoria-<name>/` | **Deployed copy** — what Hermes actually runs |

Always edit the vault source, then re-deploy to push your changes to the deployed copy:

```bash
bash scripts/install.sh --profiles-only --vault <vault>
```

Never edit the deployed copy directly. The next install overwrites it.

## File roles

These are the files inside a profile directory and what each one controls.

| File | Controls | Who edits |
| --- | --- | --- |
| `SOUL.md` | Profile identity, posture, behavioral constraints | Author (you) |
| `config.yaml` | Model routing, `mcp_servers`, generated capability blocks, and the `plugins` block enabling the `memoria-policy-gate` write gate | Author plus `scripts/render_profile_configs.py` (installer substitutes Python, vault, qmd, and model tokens) |
| `distribution.yaml` | Packages the profile for `hermes profile install` | Author |
| `skills/` | Skill packages the profile can load | Author |
| `.env` (deployed copy only) | API keys and secrets | **Human only** — never committed to git |

One piece of configuration lives *outside* the profile directory: the **lane ceiling**, the maximum write scope a lane is allowed. It sits at `<vault>/.memoria/lane-overrides/<name>.yaml`. See [Change write permissions](#change-write-permissions-lane-overrides) below.

## Change the model overlay

The **model overlay** is the `model:` block in a profile's `config.yaml` — it sets which model the profile's main work routes to. The shipped `config.yaml` files use placeholders that the installer fills in, so a production vault and a disposable test vault can use different model providers without hand-editing all five profiles.

**Production (the default).** Profiles render to the kilocode gateway:

```yaml
model:
  provider: kilocode
  base_url: https://api.kilo.ai/api/gateway
  default: ~anthropic/claude-<tier>-latest
```

**Test (Linux/WSL).** Render every profile to a local Ollama endpoint by setting `MEMORIA_ENV=test` when you install:

```bash
MEMORIA_ENV=test bash scripts/install.sh --profiles-only --vault ~/Memoria-test
```

That renders:

```yaml
model:
  provider: custom
  base_url: http://127.0.0.1:11434/v1
  default: qwen2.5:7b
  context_length: 65536
  ollama_num_ctx: 65536
```

To point the test install at a different local endpoint or model, set `MEMORIA_MODEL_BASE_URL`, `MEMORIA_MODEL_NAME`, and `MEMORIA_MODEL_CONTEXT_LENGTH`.

To change the production tier permanently, update the installer's profile model overlay and the profile tests together, then re-deploy:

```bash
bash scripts/install.sh --profiles-only --vault <vault>
```

> **The main-model key is `default`, not `name`.** That is the key the installer renders for the profile's main model.

> **Profiles override whole sections, they don't merge into them.** Each shipped profile sets only the `model`, `mcp_servers`, and `plugins` blocks. Everything else is inherited from the global `~/.hermes/config.yaml`. Hermes replaces a config section wholesale rather than deep-merging, so whatever block you put in a profile fully replaces the global one of the same name — it does not add to it.

## Change auxiliary models (set globally, not per-profile)

**Auxiliary slots** are the small, high-frequency bookkeeping calls Hermes makes around the main work: title generation, context compression, command approval, MCP routing, and skills-hub search. Each slot defaults to `provider: auto`, which reuses the profile's main model. That is wasteful, because it routes these frequent calls through an expensive main model such as Opus. Route them to cheap models instead.

**Set auxiliary models once, in the global config — not in a profile.** A profile replaces a whole config section rather than merging into it, so a per-profile `auxiliary:` block would replace (and so lose) the rest of the global one. Edit `~/.hermes/config.yaml`:

```yaml
auxiliary:
  title_generation: { provider: kilocode, model: z-ai/glm-4.7-flash }            # cheapest input
  approval:         { provider: kilocode, model: z-ai/glm-4.7-flash }
  mcp:              { provider: kilocode, model: z-ai/glm-4.7-flash }
  skills_hub:       { provider: kilocode, model: z-ai/glm-4.7-flash }
  compression:      { provider: kilocode, model: deepseek/deepseek-v4-flash }     # 1M ctx — must hold the main model's window
  # vision / web_extract: a cheap multimodal (e.g. google/gemini-2.5-flash) only if you use image/page analysis
```

Then restart Hermes to pick up the global config change.

> **`compression` needs a large context window.** It must hold at least the main model's full window. That is why the example uses DeepSeek's 1M-token context; GLM's 202K is too tight.

To find valid kilocode model ids, request `GET https://api.kilo.ai/api/gateway/models` (no auth required).

## Change write permissions (lane overrides)

A **lane override** is the write ceiling for one profile — the widest set of paths that profile is ever allowed to write. The **policy MCP** (an MCP server is a process that exposes tools and rules to Hermes; this one enforces write policy) reads and enforces these ceilings. Lane overrides live at `<vault>/.memoria/lane-overrides/<name>.yaml`, where `<name>` is one of `copi`, `librarian`, `writer`, `peer-reviewer`, or `engineer`. They sit outside the profile directory.

**To change a profile's write scope:**

1. Edit the profile's lane-override file: `<vault>/.memoria/lane-overrides/<name>.yaml`. The full file shape (`policy.allow`/`deny`, `require`, `routing`) and the decision protocol are in [Policy MCP](../../reference/policy-mcp.md).
2. Re-deploy. The installer picks up lane-override changes on every run:

   ```bash
   bash scripts/install.sh --profiles-only --vault <vault>
   ```

> **The lane is a ceiling, not the exact scope.** A board card's `allowed_paths` may *narrow* a lane's scope for that one task but never widen it. Think of the lane as the ceiling and the card's payload as the floor.

> **You do not declare review-gating per lane.** Writes to the gated path prefixes — `notes/claims/` and `notes/hubs/`, declared in `.memoria/schemas/folders.yaml` — automatically degrade to `dry_run` at the human approval gate. There is nothing to add to the lane file for this.

## Add or remove a skill

A **skill** is a packaged capability a profile can load, stored as one directory per skill under `<vault>/.memoria/profiles/memoria-<name>/skills/`. Examples: the Librarian's `catalog-enrich-record` and `map-cluster-corpus`, and the Peer-reviewer's `verify-check-citation`.

**To add a skill:**

1. Copy the skill package into the profile's `skills/` directory.
2. Re-deploy: `bash scripts/install.sh --profiles-only --vault <vault>`.

**To remove a skill:**

1. Delete the skill's directory.
2. Re-deploy: `bash scripts/install.sh --profiles-only --vault <vault>`.

> **A skill does not grant its own tools.** `<vault>/.memoria/tool-registry.yaml` is the authoritative per-profile tool allowlist, and it is default-deny (tools are denied unless explicitly listed). If a skill needs a tool the registry withholds from that profile, copying the skill in will not give it that tool — change the registry. See the note at the top of this page.

## Update API credentials

At runtime, each profile reads only its own deployed `.env` file. But you should never edit those per-profile files by hand — the installer manages them, and hand-edits drift from the shared source. Instead, edit the one shared Hermes env file and let `--profiles-only` copy the keys into each profile.

**To update credentials (macOS/Linux):**

1. Edit `~/.hermes/.env`.
2. Re-deploy:

   ```bash
   bash scripts/install.sh --profiles-only --vault <vault>
   ```

**To update credentials (Windows):**

1. Edit `%LOCALAPPDATA%\hermes\.env`.
2. Re-deploy:

   ```powershell
   .\scripts\install.ps1 -ProfilesOnly -Vault <vault>
   ```

For how `--profiles-only` seeds each profile's `.env` from the shared file, see [Redeploy profiles](../operate/redeploy-profiles.md).

## Verify a configuration change

After re-deploying, confirm the deployed profile reflects your vault source changes.

**For any profile change**, show the deployed profile:

```bash
hermes profile show memoria-<name>
```

This reports the deployed `SOUL.md`, MCP servers, skills, and `.env` key names (with values redacted).

**For a lane-override change**, you have two ways to confirm the new policy is enforced:

- Run a write operation, then check the audit log `system/logs/audit.jsonl` to see how the policy was applied.
- Or test a single decision without running a real write:

  ```bash
  python3 .memoria/mcp/policy_mcp.py --vault <vault> \
    --decide '{"profile":"memoria-librarian","action":"write","path":"notes/claims/x.md","task_id":"T1"}'
  ```

## Related

- Deploy vault source to profiles: [Redeploy profiles](../operate/redeploy-profiles.md)
- Fix profile drift (deployed ≠ source): [Fix profile drift](../troubleshooting/fix-profile-drift.md)
- Lane-override reference: [Policy MCP](../../reference/policy-mcp.md)
- The five profiles and their ceilings: [Profile capabilities](../../reference/profiles.md)
