# Security Policy

## Supported Versions

Memoria is currently in early development (v0.1). Only the latest commit on `main` is supported.

## Reporting a Vulnerability

**Do not open a public GitHub issue for security vulnerabilities.**

Please report security issues by emailing **eran.roseman@gmail.com** with the subject line
`[Memoria] Security Vulnerability`.

Include:
- A description of the vulnerability and its potential impact
- Steps to reproduce
- Any suggested mitigations

You should receive a response within 7 days. If you do not, follow up to ensure the message
was received.

## Scope

Areas of particular interest:

- **install.sh / install.ps1** — the installer runs with user privileges and copies files; any
  path traversal or injection in installer arguments is in scope.
- **API key handling** — the installer prints guidance for placing API keys; any exposure of
  keys in logs, temp files, or environment variable leakage is in scope.
- **Hermes profile YAML** — profiles in `vault/.hermes/profiles/` define agent tool access;
  privilege escalation via profile configuration is in scope.

## Out of Scope

- Vulnerabilities in upstream dependencies (Hermes, Obsidian, Zotero) — report those to
  their respective projects.
- Issues requiring physical access to the machine.
