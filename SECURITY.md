# Security Policy

## Supported Versions

Memoria is currently in early development (v0.1). Only the latest commit on `main` is supported.

## Installing safely

Both installers fetch and run a remote script. The Linux/WSL2 one-liner pipes a
remote script straight into `bash`; the Windows one-liner pipes a remote script
into `iex`. Piping a remote script into a shell is a known risk pattern — you are
trusting `raw.githubusercontent.com` and this repository at the moment you run it.
Before running either:

1. **Inspect first (recommended).** Download and read the script, then run the
   local copy:
   ```bash
   curl -fsSL https://raw.githubusercontent.com/eranroseman/memoria-vault/main/scripts/install.sh -o install.sh
   less install.sh        # read it
   bash install.sh        # then run it
   ```
2. **Or clone and run locally** — the README shows how (`bash scripts/install.sh`).
3. **Preview with `--dry-run`.** `bash install.sh --dry-run` (or
   `.\install.ps1 -DryRun`) prints every command the installer *would* run and
   changes nothing.

What the installer does and does not do, by design:

- **No silent privilege escalation.** Any step needing root prints the exact
  `sudo` command and runs it only on your confirmation.
- **Your notes folder is yours.** The installer copies the starter vault to a
  folder you choose (default `~/Memoria`) and does **not** run `git init` or
  commit on your behalf — you set up your own git, identity, and remote.
- **Dependencies are isolated.** MCP server dependencies install into a
  vault-local virtualenv (`<vault>/.memoria/.venv`), not your system Python.

## API keys and secrets

- API keys are **never** committed. They live only in per-profile `.env` files
  under `~/.hermes/profiles/<profile>/.env`, which you fill in after install.
- The starter vault ships secret-bearing files only as sanitized `.example` /
  `.EXAMPLE` siblings; the real files (`.env`, the Obsidian Local REST API
  `data.json`, the agent-client `data.json`, `project-hints.yaml`) are
  `.gitignore`d. **Never** remove those ignore rules or commit the real files.
- If you ever paste a key into an issue, PR, chat, or log, treat it as
  compromised and **rotate it immediately**.

## Reporting a Vulnerability

**Do not open a public GitHub issue for security vulnerabilities.**

Email **[eran.roseman@gmail.com](mailto:eran.roseman@gmail.com)** with the subject line `[Memoria] Security Vulnerability`. Include:

- A description of the vulnerability and its potential impact
- Steps to reproduce
- Any suggested fix, if you have one

You can expect an acknowledgement within 48 hours and a resolution timeline within 7 days. We will credit you in the fix commit unless you prefer to remain anonymous.

## Scope

Areas of particular interest:

- **scripts/install.sh / scripts/install.ps1** — path traversal, argument injection, unsafe downloads, or privilege escalation in the installer
- **API key handling** — keys exposed in logs, written to unexpected locations, or leaked through environment variables
- **Hermes profile configs** (`vault-template/.memoria/profiles/` in source; `<vault>/.memoria/profiles/` after install) — prompt injection, write-gate bypass, or lane policy circumvention via profile YAML
- **Policy MCP layer** — any path that allows an agent to write to canonical vault zones without human confirmation

## Out of Scope

- Vulnerabilities in upstream dependencies (Hermes, Obsidian, obsidian-local-rest-api, Zotero) — report those to their respective projects
- Issues requiring physical access to the machine
