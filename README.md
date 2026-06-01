# Memoria

A research operating system: the [Hermes Agent](https://hermes-agent.nousresearch.com) runtime
wired to an [Obsidian](https://obsidian.md) vault so a fleet of seven specialized agents —
Librarian, Mapper, Socratic, Writer, Verifier, Coder, Linter — read, enrich, map, verify, and
write alongside you inside your notes, under a policy gate that audits every write.

> **Status: v0.1.** The installer is validated (`bash -n` + a full `--dry-run` pass) but has not
> yet been run end-to-end against a live Hermes on Ubuntu. See
> [implementation-status.md](project-files/operations/implementation-status.md) for build state.

## Install

One line. Inspect the script first if you like — that's the recommended path.

**Linux / WSL2:**

```bash
curl -fsSL https://raw.githubusercontent.com/eranroseman/memoria-vault/main/install.sh | bash
```

**Windows (PowerShell)** — gates WSL2, installs the GUI apps via winget, then runs `install.sh` in WSL2:

```powershell
irm https://raw.githubusercontent.com/eranroseman/memoria-vault/main/install.ps1 | iex
```

**Prefer to read it first?** Clone and run from the **repo root** (the installers live there, not inside `vault/`):

```bash
git clone https://github.com/eranroseman/memoria-vault.git
cd memoria-vault
bash install.sh            # or  .\install.ps1  on Windows
#   --dry-run   preview every command, change nothing
#   --no-apps   skip the Obsidian/Zotero guidance (headless / VPS)
```

### Requirements

- **Git** on your `PATH`; on **Windows**, WSL2 enabled ([Microsoft guide](https://learn.microsoft.com/windows/wsl/install)) — the installer installs nothing if WSL2 is absent. macOS is not supported.
- A **`KILOCODE_API_KEY`** (the shipped model provider is `kilocode` — kilo.ai).
- The installer provisions **Hermes** (+ the ACP extra) and **guides** the Obsidian/Zotero installs — you don't need them beforehand.

### What it does

With your confirmation at each external step, the installer copies `vault/` to your chosen runtime
folder (default `~/Memoria`, deliberately off OneDrive), installs Hermes + the ACP extra, deploys
the seven `memoria-*` profiles, provisions skills, and prints where to put your API keys.

## After install

1. Open the runtime folder (default `~/Memoria`) in Obsidian → **Open folder as vault**, then turn off **Restricted mode** to activate the eight bundled plugins.
2. **Set up your own git** in the vault — the installer copies it but doesn't `git init` (it's your repo, your identity): `cd ~/Memoria && git init && git add -A && git commit -m "Initial Memoria vault"`, then optionally add your own remote. obsidian-git needs a repo to commit into.
3. Fill the per-profile `.env` secrets — see [set-up-hermes.md](docs/how-to-guides/setup/set-up-hermes.md).
4. Re-deploy after editing the vault source: `bash install.sh --profiles-only` (`.\install.ps1 -ProfilesOnly` on Windows; add `--only memoria-<name>` for one profile).

## Repo layout

| Path | What |
| --- | --- |
| `install.sh` / `install.ps1` | The bootstrap (`install.sh`) + thin Windows WSL2 launcher. |
| `vault/` | The Obsidian vault — the runtime artifact the installer copies out. |
| `docs/` | Engineering spec, Diátaxis-organized: `tutorials/`, `how-to-guides/`, `reference/`, `explanation/`. |
| `project-files/` | Decisions, proposals, and operations notes. |

## Documentation

Start in [`docs/`](docs/). New here? Begin with
[tutorials/01-set-up-from-zero.md](docs/tutorials/01-set-up-from-zero.md), or jump to the
[quickstart](docs/how-to-guides/setup/quickstart.md).
