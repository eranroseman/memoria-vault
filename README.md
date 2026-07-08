# Memoria

![Platform](https://img.shields.io/badge/platform-Windows%20%7C%20Linux%20%7C%20WSL2-blue)
![Status](https://img.shields.io/badge/status-v0.1--alpha-orange)
![License](https://img.shields.io/badge/license-MIT-green)

Memoria is a standalone local CLI and research engine for a single researcher.
It builds a checked Markdown workspace from sources, interviews, digests, notes,
projects, citations, and attention items.

The engine owns requests, records, verdicts, and recovery state in SQLite. The
Markdown workspace stays human-readable, while machine writes go through the
request envelope, checks, quarantine, and read barrier before they are trusted.

> **Status: v0.1 alpha source install.** No formal release has been cut yet; the install commands below run from current `main`. Alpha checkpoints are internal milestones. Check the [milestones](https://github.com/eranroseman/memoria-vault/milestones) and [open issues](https://github.com/eranroseman/memoria-vault/issues) for current checkpoint state before installing.

---

For the system model, start at [Home](docs/README.md). For the command surface,
see [CLI](docs/reference/commands-and-transports/cli.md).

## How it works

The installer creates your chosen runtime folder (default `~/Memoria`,
deliberately off OneDrive), creates a workspace-local venv, installs the
`memoria` package, initializes the workspace from the packaged seed, and wires
Git hooks. The seed includes Memoria's Obsidian adapter files and core Obsidian
settings for users who open the workspace there. It does not install the
Obsidian app, Hermes, profiles, Zotero integration, a host scheduler, or
external search tooling. Direct `memoria init --no-obsidian` is available for
non-Obsidian workspaces. See
[Installer (bootstrap)](docs/reference/system/installer.md) for exactly what it does.

The CLI and thin transports call one engine API. Product reads return checked
verdicts; product writes enqueue requests and land unchecked until the required
checks pass.

---

## Install From Main

This is an alpha source install, not a formal release artifact. Inspect the
script first if you like — that's the recommended path.

**Linux (Ubuntu/Debian) or WSL2:**

```bash
curl -fsSL https://raw.githubusercontent.com/eranroseman/memoria-vault/main/scripts/install.sh | bash
```

**Windows (PowerShell)** — native Windows production path:

```powershell
irm https://raw.githubusercontent.com/eranroseman/memoria-vault/main/scripts/install.ps1 | iex
```

**Prefer to read it first?** Clone and run from the **repo root**:

```bash
git clone https://github.com/eranroseman/memoria-vault.git
cd memoria-vault
bash scripts/install.sh            # or  .\scripts/install.ps1  on Windows
```

For the full flag list, see [Installer (bootstrap)](docs/reference/system/installer.md).

### Requirements

- **Git** on your `PATH`. **Supported platforms:** native Windows 10/11, Ubuntu/Debian, and WSL2. macOS is not supported.
- **Python 3.12+ with venv support** for the workspace-local runtime package.
- Contributor prose hooks provision `cspell` and `markdownlint` through
  pre-commit; no root `node_modules/` install is required.
- **Node 22** only when developing the optional `packages/memoria-obsidian`
  adapter package.
- Provider keys only for the flows you use; replay fixtures and local files cover
  offline development.

---

## After install

The installer prints a **Next steps** checklist with vault-local Python commands
for `memoria doctor bundle`, `memoria workspace rebuild --search`, and
`memoria ask`. For the exact flow, follow
[Quickstart](docs/how-to-guides/setup/quickstart.md).

---

## Repo layout

| Path | What |
| --- | --- |
| `scripts/install.sh` / `scripts/install.ps1` | Bootstrap installers: Linux/WSL testing and native Windows production |
| `src/memoria_vault/` | The installable Python package |
| `src/memoria_vault/product/workspace_seed/` | The minimal runtime workspace seed packaged with `memoria` |
| `docs/` | Product and system documentation: the Diátaxis quadrants (`tutorials/`, `how-to-guides/`, `reference/`, `explanation/`), with maintained design rationale under `explanation/rationale/` |
| `design-history/` | Frozen release-history chapters plus the maintained design arcs and decision-record rules |

## Documentation

Start in [`docs/`](docs). New here? Begin with the
[Quickstart](docs/how-to-guides/setup/quickstart.md).

Self-route by intent — the docs follow the [Diátaxis](https://diataxis.fr) four-quadrant split:

| Quadrant | For when you want to… |
| --- | --- |
| [Tutorials](docs/tutorials/README.md) | Learn the current CLI/runtime workflow by doing one small research loop |
| [How-to guides](docs/how-to-guides/README.md) | Accomplish a specific task you already understand |
| [Reference](docs/reference/README.md) | Look up exact commands, fields, schemas, and config |
| [Explanation](docs/explanation/README.md) | Understand why the system is shaped the way it is |

## Development

For fast system-file iteration on the disposable sandbox, run
`bash scripts/sandbox/refresh-test-vault.sh` to repair the package-seeded files
in `~/memoria-vault/sandbox/vault` while preserving runtime state. For
release-candidate installer proof, rebuild the disposable vault from scratch with
`bash scripts/sandbox/install-test-vault-local-llm.sh`; it installs into
`~/memoria-vault/sandbox/vault` and runs package, detector, and CLI doctor checks. Full
flags: [Installer (bootstrap)](docs/reference/system/installer.md).

## Citation

If you use Memoria in your research, please cite it ([CITATION.cff](CITATION.cff)):

> Roseman, E. (2026). *Memoria: a phase-gated research vault with bounded AI agents*. <https://github.com/eranroseman/memoria-vault>

## Contributing

See [Contributing to Memoria](CONTRIBUTING.md) for how to run locally, code conventions, and the PR process.
