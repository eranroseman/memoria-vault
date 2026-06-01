# Contributing to Memoria

Thanks for your interest in contributing. Memoria is a research operating system built on [Hermes Agent](https://hermes-agent.nousresearch.com) and [Obsidian](https://obsidian.md) — contributions to the installer, agent profiles, vault templates, and docs are all welcome.

## Before you start

- Check [open issues](https://github.com/eranroseman/memoria-vault/issues) to avoid duplicating work.
- For significant changes (new agents, installer overhauls, new profile capabilities), open an issue to discuss first.
- For small fixes (docs, typos, script bugs), a PR is fine without prior discussion.

## Development setup

**Requirements:** Git, WSL2 (Windows) or Linux, a `KILOCODE_API_KEY`.

```bash
git clone https://github.com/eranroseman/memoria-vault.git
cd memoria-vault

# Validate the installer without running it
bash -n install.sh

# Dry-run (shows every command, changes nothing)
bash install.sh --dry-run
```

See [docs/tutorials/01-set-up-from-zero.md](docs/tutorials/01-set-up-from-zero.md) for a full walkthrough.

## What to work on

| Area | Where |
|---|---|
| Installer (`install.sh` / `install.ps1`) | repo root |
| Agent profiles | `vault/.hermes/profiles/memoria-*/` |
| Vault templates & structure | `vault/` |
| Documentation (Diátaxis) | `docs/` — tutorials, how-to-guides, reference, explanation |
| Scripts | `scripts/` |

## Coding conventions

- **Shell:** `install.sh` targets Bash on Ubuntu/WSL2. Use `shellcheck` before submitting. Avoid bashisms if POSIX portability matters.
- **PowerShell:** `install.ps1` targets Windows PowerShell 5.1. Test on a real Windows machine or WSL2 bridge.
- **Profiles:** Agent profiles live under `vault/.memoria/profiles/`. Follow the existing `SOUL.md` / `AGENTS.md` / `skills/` structure used by the other seven profiles.
- **Docs:** Follow the [Diátaxis](https://diataxis.fr/) framework — tutorials teach, how-to guides direct, reference informs, explanation discusses. Keep docs in the right quadrant.
- **Markdown:** Enforced by `.markdownlint.jsonc` at the repo root. Run `markdownlint '**/*.md'` before pushing.

## Submitting a pull request

1. Fork the repo and create a branch off `main`.
2. Make your changes and test them (`--dry-run` at minimum; a live run if you can).
3. Run `bash -n install.sh` (syntax check) and `markdownlint '**/*.md'` if you touched docs.
4. Open a PR against `main`. Fill out the PR template.

## Commit style

Use short, lowercase imperative subject lines:

```
fix: installer fails when KILOCODE_API_KEY is unset
docs: add WSL2 troubleshooting section
profiles: extend Librarian skill for Zotero groups
```

## Questions?

Open a [GitHub Discussion](https://github.com/eranroseman/memoria-vault/discussions) or file an issue with the `question` label.
