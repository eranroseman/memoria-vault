# Memoria

![Platform](https://img.shields.io/badge/platform-Windows%20%7C%20Linux%20%7C%20WSL2-blue)
![Status](https://img.shields.io/badge/status-v0.1--alpha-orange)
![License](https://img.shields.io/badge/license-MIT-green)

Memoria is a research operating system for a single researcher: a Co-PI you
converse with and four bounded background agents inside your Obsidian vault.

Built on the [Hermes Agent](https://hermes-agent.nousresearch.com) runtime wired to an [Obsidian](https://obsidian.md) vault. A fail-closed policy gate audits lane writes, allows only lane-scoped staging/scratch paths, and keeps canonical synthesis review-gated.

<!-- SCREENSHOT: Add a screenshot or GIF here showing the vault in action — e.g. an agent's audit callout in Obsidian.
     Suggested path: assets/screenshot.png
     To add: drop the image into an assets/ folder at the repo root, then replace this comment with:
     ![Memoria vault](assets/screenshot.png)                                                          -->

> **Status: v0.1 alpha source install.** No formal release has been cut yet; the install commands below run from current `main`. Alpha checkpoints are internal milestones. Check the [milestones](https://github.com/eranroseman/memoria-vault/milestones) and [open issues](https://github.com/eranroseman/memoria-vault/issues) for current checkpoint state before installing.

---

For the system model, start at [Home](docs/README.md). For exact profile names,
postures, and write-scope ceilings, see [Profile capabilities](docs/reference/profile-capabilities.md).

## How it works

The installer copies `vault-template/` to your chosen runtime folder (default `~/Memoria`, deliberately off OneDrive), installs Hermes, deploys the five `memoria-*` profiles, and sets you up to add your API keys — see [Installer (bootstrap)](docs/reference/installer.md) for exactly what it does.

Each agent runs inside Hermes and communicates with Obsidian through the [obsidian-local-rest-api](https://github.com/coddingtonbear/obsidian-local-rest-api) plugin. The policy gate blocks denied paths, logs allowed writes, and turns review-gated synthesis edits into proposals.

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

For the full flag list (`--dry-run`, `--no-apps`, `--profiles-only`, and more), see [Installer (bootstrap)](docs/reference/installer.md).

### Requirements

- **Git** on your `PATH`. **Supported platforms:** native Windows 10/11, Ubuntu/Debian, and WSL2. macOS is not supported.
- A **`KILOCODE_API_KEY`** — get one at [kilo.ai](https://kilo.ai). The shipped model provider is `kilocode`; other providers can be swapped in the profile configs.
- An **`OPENALEX_API_KEY`** — required for source ingest metadata since 2026-02.
- The installer provisions **Hermes** (+ the ACP extra) and guides the Obsidian install — you don't need them beforehand. Zotero is optional and comes later when you need bibliography imports.

---

## After install

The installer prints a **Next steps** checklist: open the runtime folder in Obsidian (turn off **Restricted mode** so the bundled plugins load), make the vault your own git repo (the installer deliberately doesn't `git init` for you), and fill the per-profile API-key secrets. For the exact commands and key names, follow [Set up the vault](docs/how-to-guides/setup/set-up-the-vault.md) and [Set up Hermes](docs/how-to-guides/setup/set-up-hermes.md).

---

## Repo layout

| Path | What |
| --- | --- |
| `scripts/install.sh` / `scripts/install.ps1` | Bootstrap installers: Linux/WSL testing and native Windows production |
| `src/memoria_vault/` | The installable Python package |
| `vault-template/` | The vault source tree — the installer copies it out as your Obsidian vault |
| `docs/` | Product and system documentation: the Diátaxis quadrants (`tutorials/`, `how-to-guides/`, `reference/`, `explanation/`), decision records (`adr/`), and maintained design arguments (`design/`) |

## Documentation

Start in [`docs/`](docs). New here? Begin with the
[Quickstart](docs/how-to-guides/setup/quickstart.md).

Self-route by intent — the docs follow the [Diátaxis](https://diataxis.fr) four-quadrant split:

| Quadrant | For when you want to… |
| --- | --- |
| [Tutorials](docs/tutorials/README.md) | Deferred for alpha.11; use Quickstart and current task guides |
| [How-to guides](docs/how-to-guides/README.md) | Accomplish a specific task you already understand |
| [Reference](docs/reference/README.md) | Look up exact commands, fields, schemas, and config |
| [Explanation](docs/explanation/README.md) | Understand why the system is shaped the way it is |

## Development

For fast UI/system-file iteration on the disposable sandbox, run `bash scripts/refresh-test-vault.sh` to update `~/Memoria-test` from `vault-template/`, preserve runtime state, and restage the golden copy. For release-candidate installer proof, rebuild the disposable vault from scratch with `bash scripts/install-test-vault-local-llm.sh`; it installs into `~/Memoria-test/vault`, wires profiles to a local OpenAI-compatible model endpoint, and runs the package/golden/detector/L2 smoke checks. After editing profile source, re-deploy without reinstalling via `bash scripts/install.sh --profiles-only` (redeploy all profiles, or scope to one with `--only`). Full flags: [Installer (bootstrap)](docs/reference/installer.md).

## Citation

If you use Memoria in your research, please cite it ([CITATION.cff](CITATION.cff)):

> Roseman, E. (2026). *Memoria: a phase-gated research vault with bounded AI agents*. <https://github.com/eranroseman/memoria-vault>

## Contributing

See [Contributing to Memoria](CONTRIBUTING.md) for how to run locally, code conventions, and the PR process.
