
# How to install Memoria: quickstart

Five steps from zero to a working vault with one source ingested. For the full step-by-step guide with explanations, see [set-up-the-vault.md](set-up-the-vault.md) through [set-up-hermes.md](set-up-hermes.md).

## Prerequisites

- Git on your `PATH`; on **Windows**, WSL2 enabled ([Microsoft guide](https://learn.microsoft.com/windows/wsl/install))
- A `KILOCODE_API_KEY` (the shipped model provider is `kilocode` — kilo.ai)
- The installer provisions Hermes (+ the ACP extra) and guides the Obsidian/Zotero installs — you don't need them beforehand

## Steps

**1. Install.** One line (inspect the script first if you like — see the raw URL):

```bash
# Linux / WSL2:
curl -fsSL https://raw.githubusercontent.com/eranroseman/memoria-vault/main/install.sh | bash
```

```powershell
# Windows (PowerShell): gates WSL2, then runs the Linux installer
irm https://raw.githubusercontent.com/eranroseman/memoria-vault/main/install.ps1 | iex
```

The installer provisions Hermes, deploys the seven profiles, and copies the vault to your chosen folder (default `~/Memoria`, off OneDrive).

**2. Open the vault in Obsidian.** Open the folder the installer reported (default `~/Memoria`) → Open folder as vault. All eight required plugins ship pre-installed in `.obsidian/plugins/` — turn off **Restricted mode** (Settings → Community plugins) to activate them, then restart Obsidian. You do not browse or install plugins.

**3. Wire Zotero.** In Zotero: Tools → Better BibTeX Preferences → Citation key formula: `[auth.lower][year][shorttitle1_0]` (the ADR-6 canonical formula — first significant title word, not a fixed char count). Enable auto-export to `<vault>/.memoria/library.bib` (e.g. `~/Memoria/.memoria/library.bib`).

**4. Fill the Librarian's secrets.** Copy the Obsidian REST API key from Settings → Local REST API, then:

```powershell
notepad "$env:USERPROFILE\.hermes\profiles\memoria-librarian\.env"
```

Set `KILOCODE_API_KEY`, `OPENALEX_EMAIL`, and `OBSIDIAN_API_KEY`.

**5. Ingest your first source.** Drag one PDF into Zotero. Note the citekey Better BibTeX assigned. Then:

```bash
hermes -p memoria-librarian chat -s obsidian-paper-note
# in the session:
/obsidian-paper-note --source <your-citekey>
```

## Verify

- `<vault>/20-sources/01-papers/<citekey>.md` exists and has a `[!brief]` callout.
- `<vault>/00-meta/02-logs/audit.jsonl` shows at least one `allow_with_log` entry.
- `hermes profile list` shows all seven `memoria-*` profiles.

## Related

- Full install walkthrough: [set-up-the-vault.md](set-up-the-vault.md)
- Plugin install details: [set-up-obsidian.md](set-up-obsidian.md)
- Zotero configuration: [set-up-zotero.md](set-up-zotero.md)
- API keys and profile secrets: [set-up-hermes.md](set-up-hermes.md)
