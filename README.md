# Memoria

![Platform](https://img.shields.io/badge/platform-Linux%20%7C%20WSL2-blue)
![Status](https://img.shields.io/badge/status-v0.1--alpha-orange)
![License](https://img.shields.io/badge/license-MIT-green)

Memoria turns your Obsidian vault into an active research workspace — an AI research team — a co-PI you converse with and four background agents that read your notes, surface connections, pull in papers, and write alongside you, with a human approval gate before any change lands.

Built on the [Hermes Agent](https://hermes-agent.nousresearch.com) runtime wired to an [Obsidian](https://obsidian.md) vault. A policy gate audits every proposed write; nothing reaches your notes without your confirmation.

<!-- SCREENSHOT: Add a screenshot or GIF here showing the vault in action — e.g. an agent's audit callout in Obsidian.
     Suggested path: assets/screenshot.png
     To add: drop the image into an assets/ folder at the repo root, then replace this comment with:
     ![Memoria vault](assets/screenshot.png)                                                          -->

> **Status: v0.1 — not yet validated end-to-end against a live Hermes on Ubuntu.** The installer passes `bash -n` and a full `--dry-run` pass. See the [v0.1 release plan](docs/releasing/v0.1/release-plan-v0.1.md) for current build state before installing.

---

## The agents

| Agent | Role |
|---|---|
| **co-PI** | The one agent you converse with (the ACP pane) — questions your thinking, explains the system, and delegates every write to a background lane; read-only by design |
| **Librarian** | The four processing lanes (catalog · extract · link · map) — fetches and enriches sources, proposes classifications, link candidates, and corpus maps |
| **Writer** | Turns evidence into draft prose (outlines, sections) in project scratch — review-gated, never directly into canonical synthesis |
| **Peer-reviewer** | The independent verify gate — traces claims to sources, validates every `[@citekey]`, and red-teams arguments for soundness; flags, never fixes |
| **Engineer** | Scaffolds handoffs to an external coding agent and owns the commit/revert gate |

Five deterministic **engines** (ingest · search · clustering · verification sweeps · Linter) do the mechanical work — run by cron, CI, or you; agents reach them only through the policy MCP.

Full design rationale for each agent: [`docs/explanation/profiles/`](docs/explanation/profiles)

---

## How it works

The installer copies `src/` to your chosen runtime folder (default `~/Memoria`, deliberately off OneDrive), installs Hermes + the ACP extra, deploys the five `memoria-*` profiles, provisions skills, and prints where to put your API keys.

Each agent runs inside Hermes and communicates with Obsidian through the [obsidian-local-rest-api](https://github.com/coddingtonbear/obsidian-local-rest-api) plugin. A policy MCP layer intercepts every proposed write — you confirm or reject before anything lands in your vault.

---

## Install

One line. Inspect the script first if you like — that's the recommended path.

**Linux (Ubuntu/Debian) or WSL2:**

```bash
curl -fsSL https://raw.githubusercontent.com/eranroseman/memoria-vault/main/scripts/install.sh | bash
```

**Windows (PowerShell)** — gates WSL2, installs the GUI apps via winget, then runs `scripts/install.sh` in WSL2:

```powershell
irm https://raw.githubusercontent.com/eranroseman/memoria-vault/main/scripts/install.ps1 | iex
```

**Prefer to read it first?** Clone and run from the **repo root** (the installers live there, not inside `src/`):

```bash
git clone https://github.com/eranroseman/memoria-vault.git
cd memoria-vault
bash scripts/install.sh            # or  .\scripts/install.ps1  on Windows
#   --dry-run   preview every command, change nothing
#   --no-apps   skip the Obsidian/Zotero guidance (headless / VPS)
```

### Requirements

- **Git** on your `PATH`; on **Windows**, WSL2 enabled ([Microsoft guide](https://learn.microsoft.com/windows/wsl/install)) — the installer installs nothing if WSL2 is absent. **Supported platforms:** Ubuntu/Debian (native Linux), WSL2 on Windows 11. macOS is not supported.
- A **`KILOCODE_API_KEY`** — get one at [kilo.ai](https://kilo.ai). The shipped model provider is `kilocode`; other providers can be swapped in the profile configs.
- The installer provisions **Hermes** (+ the ACP extra) and **guides** the Obsidian/Zotero installs — you don't need them beforehand.

---

## After install

1. Open the runtime folder (default `~/Memoria`) in Obsidian → **Open folder as vault**, then turn off **Restricted mode** to activate the eight enabled bundled plugins (plus `obsidian-homepage`, which ships on disk but is recommended — enable it from Community Plugins if you want `home.md` to auto-open on startup).
2. **Set up your own git** in the vault — the installer copies it but doesn't `git init` (it's your repo, your identity): `cd ~/Memoria && git init && git add -A && git commit -m "Initial Memoria vault"`, then optionally add your own remote. obsidian-git needs a repo to commit into.
3. Fill the per-profile `.env` secrets — see [Set up Hermes](docs/how-to-guides/setup/set-up-hermes.md).

---

## Repo layout

| Path | What |
| --- | --- |
| `scripts/install.sh` / `scripts/install.ps1` | The bootstrap (`scripts/install.sh`) + thin Windows WSL2 launcher |
| `src/` | The vault source tree — the installer copies it out as your Obsidian vault |
| `docs/` | Everything written: the Diátaxis quadrants (`tutorials/`, `how-to-guides/`, `reference/`, `explanation/`), the decision record (`adr/`), design notes (`design/`), and the `contributing/` · `releasing/` · `testing/` process docs |

## Documentation

Start in [`docs/`](docs). New here? Begin with
[tutorials/01-set-up-from-zero.md](docs/tutorials/01-set-up-from-zero.md), or jump to the
[Quickstart](docs/how-to-guides/setup/quickstart.md).

## Development

After editing vault source, re-deploy without reinstalling:

```bash
bash scripts/install.sh --profiles-only                   # redeploy all five profiles
bash scripts/install.sh --profiles-only --only memoria-librarian  # one profile
.\scripts/install.ps1 -ProfilesOnly                       # Windows equivalent
```

## Contributing

See [Contributing to Memoria](CONTRIBUTING.md) for how to run locally, code conventions, and the PR process.
