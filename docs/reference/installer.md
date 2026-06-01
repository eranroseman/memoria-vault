---
title: Installer (bootstrap)
parent: Reference
---

# Installer (bootstrap)

Lookup tables for the bootstrap installer — what it installs, on which platforms, what it touches, and what the user must still supply by hand. For *why* the installer is shaped this way, see [explanation/architecture/bootstrap-installer.md](../explanation/deployment/bootstrap-installer.md).

## Platform support matrix

Two platforms only; **macOS is out of scope for v0.1**, and Linux is **Ubuntu/Debian only**.

| Component | Linux (Ubuntu/Debian) | Windows |
|---|---|---|
| Package source | `apt` + official `.deb` | winget (built in on Win 10/11) |
| Obsidian | official Obsidian `.deb` | `winget install -e --id Obsidian.Obsidian` |
| Zotero | `zotero-deb` apt repo | `winget install -e --id DigitalScholar.Zotero` |
| Git | `apt` | in WSL2 (`apt`) — the one hard pre-Hermes prereq |
| Pandoc | `apt` | in WSL2 (`apt`) — the one runtime Hermes does *not* provision |
| uv, Python 3.11, Node 22, ripgrep, ffmpeg | provisioned by the Hermes installer | same (inside WSL2) |
| Hermes runtime + `.memoria` Python | native (upstream `install.sh`) | **WSL2 (Ubuntu) only — else abort** |

The Hermes installer auto-provisions uv, Python 3.11, Node.js 22, ripgrep, and ffmpeg, so the bootstrap installs only **Git** (if missing) and **Pandoc** before handing off. On Windows, Obsidian + Zotero + the vault files are Windows-native, while Hermes and everything it provisions live in WSL2 Ubuntu and read the vault across `/mnt/c`.

## Install flow

1. **Download and explain** — print the plan and prompt for consent.
2. **Copy the vault** — clone to a staging location, then copy `vault/` to a target off OneDrive (`%USERPROFILE%\Memoria` / `~/Memoria`), prompting to confirm or override. That path becomes `$VAULT_PATH`.
3. **Obsidian** — detect; show the install command and run on consent. (Community plugins ship bundled inside `vault/`.)
4. **Hermes** — detect; install via the upstream installer if absent (inside WSL2 on Windows).
5. **Memoria components** — `pip install -r .memoria/mcp/requirements.txt`, then stage each profile, substitute `{{VAULT_PATH}}`, and `hermes profile install`; then provision the skills the profiles depend on.
6. **Zotero** — detect; ask, and run the install command on agreement.
7. **Explain secrets** — print the secrets checklist and exact file paths; never write keys.
8. **Zotero plugins** (if Zotero is present) — download the recommended `.xpi`s (Better BibTeX required; MarkDB-Connect recommended; RTF/ODF Scan optional), verify checksums, and print the GUI install + Better BibTeX citekey-formula steps.

## Components installed

✅ automated · ⚠️ assisted (download + guide) · ❌ explained only.

| Layer | Method | Status |
|---|---|---|
| Git | prereq; `apt`/winget if missing | ✅ |
| Pandoc | `apt`/winget (not provisioned by Hermes) | ✅ |
| uv, Python 3.11, Node 22, ripgrep, ffmpeg | provisioned by the Hermes installer | ✅ |
| Obsidian app | detect; show command, run on consent | ⚠️ |
| Obsidian community plugins + configs | bundled in `vault/` | ✅ |
| Obsidian REST API key | regenerated on first launch | ❌ (copy into `.env`) |
| Hermes runtime | upstream installer (WSL2 on Win) | ✅ |
| `.memoria` MCP servers (`policy_mcp.py`, `policy_hook.py`) | `pip install -r requirements.txt` | ✅ |
| Seven Hermes profiles | stage + `{{VAULT_PATH}}` + `hermes profile install` | ✅ |
| Skills — installable | clone K-Dense (5) + `hermes skills install` official (2) | ✅ |
| Skills — Memoria-custom | authored as `SKILL.md` in the profile `skills/` dirs | ✅ (ship in vault) |
| Per-profile `.env` | bootstrap from `.env.EXAMPLE` if absent | ✅ create / ❌ fill |
| Zotero app + Better BibTeX (required), MarkDB-Connect, RTF/ODF Scan | detect; download `.xpi` + GUI install | ⚠️ |
| API keys (KiloCode, OpenAlex email, S2, PubMed, GitHub) | user-supplied | ❌ explain |

See [obsidian-plugins.md](obsidian-plugins.md) and [zotero-plugins.md](zotero-plugins.md) for the plugin sets, and [on-disk-layout.md](on-disk-layout.md) for where everything lands.

## Secrets

The installer prints this checklist and the exact paths; it writes nothing. **v0.1 model provider is KiloCode only** — a user authenticates Hermes once to the KiloCode gateway and needs no separate Anthropic/OpenRouter key.

| Secret | Where to get it | Goes in |
|---|---|---|
| `KILOCODE_API_KEY` | [kilo.ai](https://kilo.ai) | each profile `.env` (or once in `~/.hermes/.env`) |
| `OBSIDIAN_API_KEY` | Obsidian → Local REST API (first launch) | every profile `.env` |
| `OPENALEX_EMAIL` | any working address (polite pool) | Librarian `.env` |
| `SEMANTIC_SCHOLAR_API_KEY`, `PUBMED_API_KEY`, `GITHUB_TOKEN` | per [set-up-zotero](../how-to-guides/setup/set-up-zotero.md) | Librarian `.env` (optional) |

Profile `.env` paths: `~/.hermes/profiles/memoria-<name>/.env` (the WSL2 home on Windows).

## Skills provisioning

The seven profiles' lane-overrides name **28 distinct skills**. Only a minority are installable from a registry; the rest are Memoria-coined and ship authored in the vault:

- **Installable from K-Dense** (`git clone` → `~/.hermes/skills/`): `paper-lookup`, `pyzotero`, `citation-management`, `literature-review`, `scientific-writing`.
- **Installable from the official Hermes registry** (`hermes skills install official/...`): `arxiv` (lane name `arxiv-search`), `llm-wiki` (lane name `llm-wiki-draft`), plus `obsidian`, `ocr-and-documents`, `github-repo-management`, `codex`, `claude-code`.
- **Memoria-authored, shipped in the vault** (`vault/.memoria/profiles/<p>/skills/`): the two real thin skills `obsidian-paper-note` (Librarian) and `retraction-check` (Verifier); the rest are handled by adapting the design — prompt-only behaviors in `SOUL.md`, lane-overrides pointing at a real skill ID, QuickAdd templates, or `detectors.py` functions (the Linter runs `detectors.py`, not Hermes skills).
- **Not a skill:** `rest-passthrough` is a lane-override capability token.

## `.memoria/mcp/requirements.txt`

The dependency list for Memoria's MCP servers, installed in step 5 before profile registration. Deliberately minimal (the policy decision core is dependency-light):

- `mcp>=1.2.0` — the Model Context Protocol SDK; provides the thin server wrapper around `policy_mcp.py`.
- `PyYAML>=6.0` — parses the lane-override files the live policy server loads at startup.

`.memoria/mcp/` also ships `policy_mcp.py`, `policy_hook.py`, `board_export.py`, and `metrics_aggregate.py`.

## Per-profile wiring

`hermes profile install` requires four files per profile; a profile missing any is skipped (graceful skip):

- `SOUL.md` — the system prompt / identity.
- `config.yaml` — model routing (`provider: kilocode`) plus the `hooks` block registering the policy gate (`pre_tool_call` / `post_tool_call` → `policy_hook.py`).
- `mcp.json` — the MCP servers the profile connects (the `obsidian` vault-access server and the `policy` server), with `{{VAULT_PATH}}` placeholders the installer substitutes.
- `distribution.yaml` — install metadata + `env_requires` (requires `KILOCODE_API_KEY`; `ANTHROPIC_API_KEY` optional).

Profiles also carry `skills/` and `cron/` directories.

## Models and ACP

Per-profile model tiers are set in each `config.yaml` (`provider: kilocode`): Linter/Librarian/Coder → Haiku; Mapper/Writer → Sonnet; Socratic/Verifier → Opus. Auxiliary model slots are set in the global `~/.hermes/config.yaml` (a cheap model for title-gen/approval/compression), not per profile — see [using-hermes-agent/configuration.md](../how-to-guides/using-hermes-agent/configuration.md). The Obsidian chat pane needs the Hermes **ACP extra** (`pip install 'hermes-agent[acp]'`), which the bootstrap installs before the pane works.

## Related

- **Design rationale:** [explanation/architecture/bootstrap-installer.md](../explanation/deployment/bootstrap-installer.md).
- **Redeploy path:** [redeploy-profiles](../how-to-guides/maintenance/redeploy-profiles.md) (`install.sh --profiles-only`).
- **Setup guides:** [set-up-the-vault](../how-to-guides/setup/set-up-the-vault.md), [set-up-hermes](../how-to-guides/setup/set-up-hermes.md), [set-up-zotero](../how-to-guides/setup/set-up-zotero.md).
- **Telemetry shipped by v0.1:** [telemetry.md](telemetry.md).
