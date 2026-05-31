
# How to install Memoria: quickstart

Five steps from zero to a working vault with one source ingested. For the full step-by-step guide with explanations, see [set-up-the-vault.md](set-up-the-vault.md) through [set-up-hermes.md](set-up-hermes.md).

## Prerequisites

- Python 3.11+, Git, and Pandoc on your `PATH`
- Obsidian installed
- Zotero 9 + Better BibTeX installed
- Hermes on your `PATH` (`hermes --version` returns a version number)
- `KILOCODE_API_KEY` available (the shipped model provider is `kilocode` — kilo.ai)

## Steps

**1. Clone and install.**

```powershell
git clone https://github.com/<your-handle>/memoria-vault.git
cd memoria-vault\vault
./install.ps1
```

**2. Open the vault in Obsidian.** Open vault → Open folder as vault → select the `vault/` subfolder. Install the four required community plugins when prompted: `obsidian-local-rest-api`, `agent-client`, `obsidian-citation-plugin`, `callout-manager`. Add `dataview` and `templater-obsidian`. Restart Obsidian.

**3. Wire Zotero.** In Zotero: Tools → Better BibTeX Preferences → Citation key formula: `[auth.lower][year][title:lower:condense:6]`. Enable auto-export to `vault/.memoria/library.bib`.

**4. Fill the Librarian's secrets.** Copy the Obsidian REST API key from Settings → Local REST API, then:

```powershell
notepad "$env:USERPROFILE\.hermes\profiles\memoria-librarian\.env"
```

Set `KILOCODE_API_KEY`, `OPENALEX_EMAIL`, and `OBSIDIAN_API_KEY`.

**5. Ingest your first source.** Drag one PDF into Zotero. Note the citekey Better BibTeX assigned. Then:

```bash
hermes -p memoria-librarian chat -s llm-wiki
# in the session:
/llm-wiki ingest --source <your-citekey>
```

## Verify

- `vault/20-sources/01-papers/<citekey>.md` exists and has a `[!brief]` callout.
- `vault/00-meta/02-logs/audit.jsonl` shows at least one `allow_with_log` entry.
- `hermes profile list` shows all seven `memoria-*` profiles.

## Related

- Full install walkthrough: [set-up-the-vault.md](set-up-the-vault.md)
- Plugin install details: [set-up-obsidian.md](set-up-obsidian.md)
- Zotero configuration: [set-up-zotero.md](set-up-zotero.md)
- API keys and profile secrets: [set-up-hermes.md](set-up-hermes.md)
