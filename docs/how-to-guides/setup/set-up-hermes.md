---
title: Set up Hermes
parent: Setup
nav_order: 4
---


# Set up Hermes

Fill the API secrets, propagate them into the five profiles, and verify that Hermes can reach the vault. Without secrets the profiles install but can't call any model or external API.

## Prerequisites

- Hermes installed and on your `PATH` (`hermes --version` returns a version) — the bootstrap does this for you
- Memoria installed — the bootstrap (`scripts/install.sh`, or `scripts/install.ps1` on Windows) run ([Set up the vault](set-up-the-vault.md))
- Obsidian running with the Local REST API plugin active ([Set up Obsidian](set-up-obsidian.md)) — you need the `apiKey` from that step

## Steps

**1. Put the shared keys in the shared Hermes env file.**

Use `%LOCALAPPDATA%\hermes\.env` on Windows and `~/.hermes/.env` on Linux/WSL2.

```env
KILOCODE_API_KEY=...                  # model access — the shipped provider is kilocode (kilo.ai)
OBSIDIAN_API_KEY=<64-char hex apiKey from the Local REST API plugin>
OBSIDIAN_MCP_PORT=27124               # must equal the Local REST API HTTPS port ([Set up Obsidian](set-up-obsidian.md))
OBSIDIAN_MCP_SSL_VERIFY=/absolute/path/to/obsidian-local-rest-api.pem
OPENALEX_API_KEY=...                  # openalex.org/settings/api — required since 2026-02 (sent as ?api_key=)
S2_API_KEY=...                        # Semantic Scholar, optional (the var is S2_API_KEY, not SEMANTIC_SCHOLAR_API_KEY)
NCBI_API_KEY=...                      # PubMed/PMC, optional (the var is NCBI_API_KEY, not PUBMED_API_KEY)
NCBI_EMAIL=you@example.com            # Entrez contact email; also reused as the Crossref mailto / Unpaywall email param
MEMORIA_TELEGRAM_BOT_TOKEN=...        # optional urgent alert/block pushes
MEMORIA_TELEGRAM_CHAT_ID=...          # optional urgent alert/block pushes
# Zotero needs no key — pyzotero reads the local desktop API (http://localhost:23119, read-only)
# ANTHROPIC_API_KEY=sk-ant-...        # only if you switch config.yaml to provider: anthropic
```

For a Linux/WSL disposable test vault, run the profile deploy with `MEMORIA_ENV=test`. The installer renders every profile to Kilo DeepSeek V4 Flash by default:

```bash
MEMORIA_ENV=test bash scripts/install.sh --profiles-only --vault ~/Memoria-test
```

Use a local OpenAI-compatible endpoint only when you explicitly want local-model testing:

```bash
MEMORIA_ENV=test \
MEMORIA_MODEL_PROVIDER=custom \
MEMORIA_MODEL_BASE_URL=http://127.0.0.1:11434/v1 \
MEMORIA_MODEL_NAME=<local-model> \
MEMORIA_MODEL_CONTEXT_LENGTH=65536 \
bash scripts/install.sh --profiles-only --vault ~/Memoria-test
```

**2. Propagate the keys into every profile.**

Hermes profile runs read **only the profile's own `.env`** — there is no global fallback, so the keys must be seeded into each profile:

```bash
bash scripts/install.sh --profiles-only --vault <vault>
```

```powershell
.\scripts\install.ps1 -ProfilesOnly -Vault <vault>
```

What `--profiles-only` re-deploys, and how it seeds each profile's `.env` from the shared file without overwriting existing values, is in [Redeploy profiles](../operate/redeploy-profiles.md). Re-run this any time you add or rotate a key in the shared Hermes env file. To check a single profile, open the deployed `memoria-librarian/.env` under the Hermes profiles directory — the Librarian carries the most keys (it does all enrichment and discovery).

**3. Confirm the placeholders were substituted.**

```bash
grep -A2 "policy" ~/.hermes/profiles/memoria-librarian/config.yaml | head
```

The `policy` server's entry should point at the vault venv's Python and an absolute path ending in `.memoria/mcp/policy_mcp.py`. If you see `{{PYTHON}}`, `{{VAULT_PATH}}`, or `{{MODEL_*}}`, re-run `bash scripts/install.sh --profiles-only --vault <vault>` on Linux/WSL2 or `.\scripts\install.ps1 -ProfilesOnly -Vault <vault>` on Windows.

**4. Install the upstream MCP servers (Librarian + Peer-reviewer).**

The research lanes reach external services over MCP, not direct HTTP (their `web` toolset is disabled — see [ADR-32](../../adr/32-external-access-over-mcp.md)). Two of those servers are upstream `pip` installs; the rest ship in the vault. Install them where Hermes can launch them:

```bash
<vault>/.memoria/.venv/bin/python -m pip install paper-search-mcp
python -m pip install --user zotero-mcp
```

```powershell
& "<vault>\.memoria\.venv\Scripts\python.exe" -m pip install paper-search-mcp
py -m pip install --user zotero-mcp
```

`paper_search` runs under the vault venv's Python. `pyzotero` is launched as the
`pyzotero-mcp` executable, so install `zotero-mcp` somewhere on the PATH Hermes
uses.

**5. Seed the retraction dataset.**

The Peer-reviewer's retraction check indexes a local Retraction Watch CSV; a monthly cron wrapper (`retraction-refresh-cron.sh`) keeps it fresh thereafter. Seed it now:

```bash
python3 .memoria/operations/integrity/retraction/retraction.py --refresh
```

Until the CSV is present, retraction checks degrade to the live CrossRef + Open Retractions sources.

**6. Smoke-test the Co-PI.**

```bash
hermes -p memoria-copi chat
```

Ask it "explain how this vault is organized". It should answer from the vault. For the in-Obsidian pane, the same profile runs as an ACP server (`hermes -p memoria-copi acp`) — the bundled `agent-client` config launches it for you; the pane runs one agent, the Co-PI ([Agent Client pane](../using-obsidian/use-the-agent-client-pane.md)).

**7. Test the ingest path end-to-end.**

In Obsidian, `Cmd/Ctrl-P` → **Memoria: capture source from URL** with a DOI-resolvable URL. If you are still shaping the request, use the Co-PI for conversation, then run the matching capture command. Within a couple of minutes the Catalog entity should exist at `catalog/papers/<citekey>.md` and a candidate card should sit in `inbox/`.

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
- Cost tuning: [Configure a profile § Auxiliary models](../hermes-agent/configuration.md#change-auxiliary-models-set-globally-not-per-profile)
- Re-deploying after profile edits: [Redeploy profiles](../operate/redeploy-profiles.md)
- What the installer wires for you: [Installer (bootstrap)](../../reference/installer.md)
- Profile design: [explanation/profiles/](../../explanation/profiles) (the Co-PI and the four lanes)
