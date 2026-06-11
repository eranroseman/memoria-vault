---
title: Set up Hermes
parent: Setup
nav_order: 5
---


# Set up Hermes

Fill the API secrets, propagate them into the five profiles, and verify that Hermes can reach the vault. Without secrets the profiles install but can't call any model or external API.

## Prerequisites

- Hermes installed and on your `PATH` (`hermes --version` returns a version) — the bootstrap does this for you
- Memoria installed — the bootstrap (`scripts/install.sh`, or `scripts/install.ps1` on Windows) run ([Set up the vault](set-up-the-vault.md))
- Obsidian running with the Local REST API plugin active ([Set up Obsidian](set-up-obsidian.md)) — you need the `apiKey` from that step

## Steps

**1. Put the shared keys in the global `~/.hermes/.env`.**

```env
KILOCODE_API_KEY=...                  # model access — the shipped provider is kilocode (kilo.ai)
OBSIDIAN_API_KEY=<64-char hex apiKey from the Local REST API plugin>
OBSIDIAN_MCP_PORT=27123               # the plugin's insecure HTTP port serving the native MCP; change only if you moved it or run a 2nd vault
OPENALEX_API_KEY=...                  # openalex.org/settings/api — required since 2026-02 (sent as ?api_key=)
S2_API_KEY=...                        # Semantic Scholar, optional (the var is S2_API_KEY, not SEMANTIC_SCHOLAR_API_KEY)
NCBI_API_KEY=...                      # PubMed/PMC, optional (the var is NCBI_API_KEY, not PUBMED_API_KEY)
NCBI_EMAIL=you@example.com            # Entrez contact email; also reused as the Crossref mailto / Unpaywall email param
# Zotero needs no key — pyzotero reads the local desktop API (http://localhost:23119, read-only)
# ANTHROPIC_API_KEY=sk-ant-...        # only if you switch config.yaml to provider: anthropic
```

**2. Propagate the keys into every profile.**

Hermes profile runs read **only the profile's own `.env`** — there is no global fallback. The installer seeds each key a profile declares in its `.env.EXAMPLE` from the global file, without overwriting anything already set:

```bash
bash scripts/install.sh --profiles-only --vault <vault>
```

Re-run this any time you add or rotate a key in `~/.hermes/.env`. To check a single profile, open `~/.hermes/profiles/memoria-librarian/.env` — the Librarian carries the most keys (it does all enrichment and discovery).

**3. Confirm the placeholders were substituted.**

```bash
grep -A2 "policy" ~/.hermes/profiles/memoria-librarian/config.yaml | head
```

The `policy` server's entry should point at the vault venv's Python and an absolute path ending in `.memoria/mcp/policy_mcp.py`. If you see `{{PYTHON}}` or `{{VAULT_PATH}}`, re-run `bash scripts/install.sh --profiles-only --vault <vault>`.

**4. Install the upstream MCP servers (Librarian + Peer-reviewer).**

The research lanes reach external services over MCP, not direct HTTP (their `web` toolset is disabled — see [ADR-32](../../adr/32-external-access-over-mcp.md)). Two of those servers are upstream `pip` installs; the rest ship in the vault. Install them where Hermes can launch them:

```bash
pip install paper-search-mcp          # Librarian: scholarly discovery across 20+ databases
pip install "pyzotero[mcp]"           # Librarian + Peer-reviewer: read-only Zotero (local desktop API)
```

**5. Seed the retraction dataset.**

The Peer-reviewer's retraction check indexes a local Retraction Watch CSV; a monthly cron wrapper (`memoria-refresh-rw.sh`) keeps it fresh thereafter. Seed it now:

```bash
.memoria/.venv/bin/python .memoria/engines/sweeps/retraction.py --refresh
```

Until the CSV is present, retraction checks degrade to the live CrossRef + Open Retractions sources.

**6. Smoke-test the co-PI.**

```bash
hermes -p memoria-copi chat
```

Ask it "explain how this vault is organized". It should answer from the vault. For the in-Obsidian pane, the same profile runs as an ACP server (`hermes -p memoria-copi acp`) — the bundled `agent-client` config launches it for you; the picker offers exactly one agent, the co-PI ([Agent-client pane](../using-obsidian/use-the-acp-pane.md)).

**7. Test the ingest path end-to-end.**

In Obsidian, `Cmd/Ctrl-P` → **Memoria: capture source from URL** with a DOI-resolvable URL (or tell the co-PI "bring in this paper: `<DOI>`"). Within a couple of minutes the Catalog entity should exist at `catalog/papers/<citekey>.md` and a candidate card should sit in `inbox/`.

**8. Route the auxiliary models to cheap flash tiers (cost efficiency).**

Hermes runs cheap, high-frequency bookkeeping tasks (title generation, context compression, command approval, MCP routing, skills-hub search) through *auxiliary* model slots that default to the profile's main model — so a co-PI compression call would otherwise burn **Opus**. These are set **globally** (not per-profile — Hermes replaces a config section wholesale). Use a split: GLM 4.7 Flash for the light slots (cheapest input), DeepSeek V4 Flash for compression (its 1M context safely holds the conversation being summarized). Add this block to your **global** `~/.hermes/config.yaml`:

```yaml
auxiliary:
  title_generation: { provider: kilocode, model: z-ai/glm-4.7-flash }
  approval:         { provider: kilocode, model: z-ai/glm-4.7-flash }
  mcp:              { provider: kilocode, model: z-ai/glm-4.7-flash }
  skills_hub:       { provider: kilocode, model: z-ai/glm-4.7-flash }
  compression:      { provider: kilocode, model: deepseek/deepseek-v4-flash }
  # vision / web_extract: a cheap multimodal (e.g. google/gemini-2.5-flash) only if you use image/page analysis
```

Restart Hermes after editing the global config. Full rationale (split reasoning, the GLM-context caveat, the GLM-5-turbo cost trap): [Configure a profile § Auxiliary models](../hermes-agent/configuration.md#auxiliary-models-set-globally-not-per-profile).

## Verify

```bash
hermes profile list
```

Exactly the five `memoria-*` profiles (`copi`, `librarian`, `writer`, `peer-reviewer`, `engineer`) show as registered.

Check the audit log after the first real ingest:

```bash
tail -5 <vault>/system/logs/audit.jsonl
```

Each line should carry a `"decision"` (`allow_with_log` for the Librarian's Catalog writes) and the acting `"profile"`.

## Related

- API key sources: [Set up Zotero § API keys for enrichment](../zotero/set-up-zotero.md#api-keys-for-enrichment-optional-but-recommended)
- Re-deploying after profile edits: [Redeploy profiles](../operate/redeploy-profiles.md)
- What the installer wires for you: [Installer (bootstrap)](../../reference/installer.md)
- Profile design: [explanation/profiles/](../../explanation/profiles) (the co-PI and the four lanes)
