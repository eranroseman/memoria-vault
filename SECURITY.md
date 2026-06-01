# Security Policy

## Supported Versions

Memoria is currently in early development (v0.1). Only the latest commit on `main` is supported.

## A note on `curl | bash`

The README install command pipes a remote script directly into bash. This is a known risk pattern. Before running it:

1. Inspect the script first: `curl -fsSL https://raw.githubusercontent.com/eranroseman/memoria-vault/main/install.sh | less`
2. Or clone and run locally — the README shows how.
3. Use `--dry-run` to preview every command the installer would execute without making any changes.

The one-liner is provided for convenience but reading the script first is always the recommended path.

## Reporting a Vulnerability

**Do not open a public GitHub issue for security vulnerabilities.**

Email **[eran.roseman@gmail.com](mailto:eran.roseman@gmail.com)** with the subject line `[Memoria] Security Vulnerability`. Include:

- A description of the vulnerability and its potential impact
- Steps to reproduce
- Any suggested fix, if you have one

You can expect an acknowledgement within 48 hours and a resolution timeline within 7 days. We will credit you in the fix commit unless you prefer to remain anonymous.

## Scope

Areas of particular interest:

- **install.sh / install.ps1** — path traversal, argument injection, unsafe downloads, or privilege escalation in the installer
- **API key handling** — keys exposed in logs, written to unexpected locations, or leaked through environment variables
- **Hermes profile configs** (`vault/.memoria/profiles/`) — prompt injection, write-gate bypass, or lane policy circumvention via profile YAML
- **Policy MCP layer** — any path that allows an agent to write to canonical vault zones without human confirmation

## Out of Scope

- Vulnerabilities in upstream dependencies (Hermes, Obsidian, obsidian-local-rest-api, Zotero) — report those to their respective projects
- Issues requiring physical access to the machine
