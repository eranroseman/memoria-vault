
# How to set up Hermes

Fill the API secrets for each profile and verify that Hermes can reach the vault. Without secrets the profiles install but can't call any external API.

## Prerequisites

- Hermes installed and on your `PATH` (`hermes --version` returns a version)
- The vault cloned and `install.ps1` run ([set-up-the-vault.md](set-up-the-vault.md))
- Obsidian running with the REST API plugin active ([set-up-obsidian.md](set-up-obsidian.md)) — you need the `apiKey` from that step

## Steps

**1. Fill the Librarian's `.env`.**

The Librarian does all source enrichment — it needs the most secrets.

```powershell
notepad "$env:USERPROFILE\.hermes\profiles\memoria-librarian\.env"
```

Set these values:

```env
KILOCODE_API_KEY=...                  # model access — the shipped provider is kilocode (kilo.ai)
OPENALEX_EMAIL=you@example.com        # required polite-pool header — any working address
SEMANTIC_SCHOLAR_API_KEY=...          # optional but recommended
PUBMED_API_KEY=...                    # optional but recommended
GITHUB_TOKEN=ghp_...                  # optional, for repo enrichment
OBSIDIAN_API_KEY=<64-char hex apiKey from Obsidian REST API plugin>
# ANTHROPIC_API_KEY=sk-ant-...        # only if you switch config.yaml to provider: anthropic
```

**2. Fill the remaining profiles' `.env` files.**

The other six profiles share a common minimum set. Open each `.env` and set at minimum:

```env
KILOCODE_API_KEY=<same Kilo Code key>
OBSIDIAN_API_KEY=<same 64-char hex token>
```

The profiles with their `.env` paths:

```powershell
# Run for each profile name:
# memoria-mapper, memoria-socratic, memoria-writer,
# memoria-verifier, memoria-coder, memoria-linter
notepad "$env:USERPROFILE\.hermes\profiles\memoria-mapper\.env"
```

**3. Confirm the policy MCP path was substituted.**

```powershell
Get-Content "$env:USERPROFILE\.hermes\profiles\memoria-librarian\mcp.json"
```

The `policy` server's `args` should point at an absolute path ending in `.memoria/mcp/policy_mcp.py`. If you see `{{VAULT_PATH}}`, re-run `./install.ps1`.

**4. Test the Librarian can reach Obsidian.**

```bash
hermes -p memoria-librarian chat -s obsidian-paper-note
# in the session:
/obsidian-paper-note --check
```

The `--check` query exercises the Obsidian REST API without writing. A successful response shows the vault name and note count. A connection error means the API key is wrong or Obsidian isn't running.

**5. Test ingest on a real source.**

Pick a citekey from `.memoria/library.bib` and run:

```text
/obsidian-paper-note --source <citekey> --dry-run
```

`--dry-run` reports what the Librarian *would* write without actually writing anything. Confirm the output shows the expected note path and metadata fields.

## Verify

```bash
hermes profile list
```

All seven `memoria-*` profiles show `status: registered`.

Check the audit log after the first real ingest (remove `--dry-run` when you're ready):

```powershell
Get-Content vault\00-meta\02-logs\audit.jsonl | Select-Object -Last 5
```

Each line should have `"decision": "allow_with_log"` and `"profile": "memoria-librarian"`.

## Related

- API key sources: [set-up-zotero.md § API keys for enrichment](set-up-zotero.md#api-keys-for-enrichment-optional-but-recommended)
- Re-deploying after profile edits: [redeploy-profiles.md](../maintenance/redeploy-profiles.md)
- Profile design: [explanation/profiles/](../../explanation/profiles/) (Librarian, Mapper, etc.)
- Hermes CLI reference: [reference/integrations.md](../../reference/integrations.md)
