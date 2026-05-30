---
topic: architecture
---

# Why the on-disk layout is shaped this way

The system spans **two filesystem locations**: the starter vault (versioned, distributable, holds all install material) and the user's Hermes runtime (per-user, holds installed profile directories copied from the vault by the installer). This page explains *why* the layout is the way it is — the source-vs-runtime relationship, the install flow, and the version-control boundary. For the annotated directory tree (every path, its one-line description, and who owns it), see [the on-disk-layout reference](../../reference/on-disk-layout.md).

## Starter vault (versioned, distributable)

The starter vault is the **single distributable artifact**. The human clones one repo and runs one script; that script sets up everything else.

The **vault root folder is human-defined**. The distribution lives at a repo conventionally called `memoria-vault`, but the human clones it into any folder name they want (`git clone <url> my-research-vault`) and can move it anywhere on disk. Memoria's design is agnostic to the root folder's name and location — `install.ps1` detects its own location at runtime via `$PSScriptRoot` and uses that absolute path everywhere a vault path is needed (notably the `{{VAULT_PATH}}` substitution in each profile's `mcp.json`). Only the *contents* of the root — the `00-meta/`, `.obsidian/`, `.memoria/` shape — are fixed by the design.

Numbered-prefix subdirectories (e.g., `01-templates`, `02-csl`, `01-papers`) are the standard naming convention — see [vault/README.md](../vault/README.md#folder-structure) for the full taxonomy and per-folder role table. Numbers encode display order in Obsidian's file explorer (alphabetical sort puts them in semantic-priority order) and give workflows stable paths to reference. The [reference tree](../../reference/on-disk-layout.md#starter-vault-versioned-distributable) lists every path under the vault root.

The **tool registry** (`.memoria/tool-registry.yaml`) is the machine-read tool config: it declares which tools each profile may call, so the policy MCP and the lane overrides resolve against one authoritative list rather than per-profile duplicates.

Engineering documentation (architecture, workflows, decisions (ADRs), profile design summaries, dashboards, roadmap, and topic-distributed reference material — ~125 files under `memoria-docs/`) lives in a **separate repository**. Documentation is not part of the runtime; the human's vault doesn't need it to function.

## Runtime install (per-user, not in repo)

When the human runs `install.ps1` / `install.sh`, the installer copies the seven profile directories from `.memoria/profiles/` to Hermes's standard location at `~/.hermes/profiles/` (or `%USERPROFILE%\.hermes\profiles\` on Windows; both honor `HERMES_HOME` to override). Profiles are prefixed `memoria-` to keep them separable from other agents on the same machine. The [reference tree](../../reference/on-disk-layout.md#runtime-install-per-user-not-in-repo) shows the resulting per-profile layout and which files are author-owned versus user-owned.

Per-profile structure follows the [Hermes profile-distribution shape](https://hermes-agent.nousresearch.com/docs/user-guide/profile-distributions) — `SOUL.md`, `config.yaml`, `mcp.json`, `skills/`, `cron/` — so Memoria profiles are compatible with `hermes profile list` and the standard `hermes -p memoria-librarian chat` invocation surface.

## How the installer works

1. **Detect prerequisites.** Verify Hermes is installed and Python is available for the MCP servers; fail with a clear message if either is missing.
2. **Stage each profile.** Copy `.memoria/profiles/<name>/` to a temporary directory. In each copy's `mcp.json`, substitute `{{VAULT_PATH}}` with the absolute path of this vault (forward-slash form for cross-platform JSON safety).
3. **Install.** For each staged profile, run `hermes profile install <staged-path> --alias memoria-<name> --force --yes`. Hermes copies author-owned files (SOUL.md, config.yaml, mcp.json, skills/, cron/) into `~/.hermes/profiles/memoria-<name>/`, leaves `.env` alone (user-owned).
4. **Bootstrap secrets.** For each installed profile, if `.env` doesn't exist, copy `.env.EXAMPLE` to `.env`. Human fills in real values.
5. **Clean up staging.** Delete the temporary directory.

The script is **idempotent and always-overwrite**: re-running after `git pull` rewrites every author-owned file from the vault source, preserves every human-owned secret. Humans who tuned `config.yaml` through `hermes config set` will see those tweaks reset; the trade is predictability — every install matches the source exactly.

## Why this structure

- **One artifact, one install.** The human's primary interaction is with the Obsidian vault. Bundling install material with the vault gives a single unified UX: clone one repo, run one script, everything is in place.
- **Dot-prefix for tooling.** Both `.obsidian/` (Obsidian's own config) and `.memoria/` (Memoria's install material) use the dot-prefix convention so Obsidian's vault scanner auto-hides them from the file explorer, search, graph view, and Dataview queries. Human sees content; tooling stays out of the way without any per-vault exclusion config.
- **Direct profile management (no compiler).** The seven profile directories under `.memoria/profiles/` are hand-authored, not generated. Shared content (audit-log behavior, common policies, common MCP connections) lives in seven places and is maintained by hand. Drift between sibling profiles is caught by the Linter rather than prevented at build time. See [the deferred compiler vision](../../project/roadmap/profile-compilation.md) for the alternative that may become relevant if drift becomes painful at the seven-profile scale.
- **Source = runtime.** Under direct management, the file in `.memoria/profiles/memoria-librarian/SOUL.md` is exactly what gets installed to `~/.hermes/profiles/memoria-librarian/SOUL.md`. No build step means no "compiled vs source" duality — what's in the repo is what the agent reads at runtime.
- **MCP servers ship with the vault.** The Python sources for `policy_mcp.py` and `tasks_mcp.py` live at `.memoria/mcp/`. Each profile's `mcp.json` points at this location via the `{{VAULT_PATH}}` placeholder, substituted at install time. Humans don't need a separate clone of an MCP-source repo.

## Version control

**Git is Memoria's authoritative version-history layer.** Every reversibility property the system relies on — recoverable mistakes, audited diffs, the ability to roll a worker's write back — assumes a git history exists. This is non-negotiable; it's why the [policy MCP audit log](README.md#permission-enforcement-the-policy-mcp) records `before_hash` and `after_hash` for every write, and why the [Linter's `vault-hash-drift` detector](../profiles/linter.md) treats a non-MCP write as CRITICAL.

- **In Git** (starter vault repo): the vault skeleton (`00-meta/`, `10-inbox/`, …); `.obsidian/` config; all of `.memoria/` (profiles, MCP source, lane overrides); installers; README. Optionally also `.memoria/profile-memory/` — see the profile-memory note below.
- **Out of Git**: `.env` files in `~/.hermes/profiles/`, `auth.json`, secrets, the raw audit log (`00-meta/02-logs/audit.jsonl` — append-only log of human-touchable writes), and sessions / the session database (`~/.hermes/state.db`). These are local runtime state. Profile memory (`MEMORY.md`/`USER.md`) at `~/.hermes/profiles/<name>/memories/` is also local by default — but can be promoted into the vault for non-concurrent multi-machine use via the [`memories/` junction](../../project/roadmap/sync-and-coordination.md#syncing-profile-memory-across-machines-the-memories-junction), which stores the files at `.memoria/profile-memory/memoria-<name>/` and junctions Hermes's path onto them.
- **Generated locally, not committed**: `~/.hermes/profiles/memoria-*/` directories. These are recreated from the vault source on every `install.ps1` run.

**Sync ≠ version history.** Memoria's [deployment options matrix](../../project/roadmap/deployment-options.md) gives three sync choices (manual git pull/push, Obsidian Sync, or Syncthing) — these are about *how the vault propagates between devices*, not about *how history is recorded*. Git is always the history layer regardless of which sync layer the human picks. Running git's pull/push **as the sync layer** (the local-only option) at the same time as Obsidian Sync is a misconfiguration: two sync mechanisms race for the same files (most painfully `.obsidian/workspace.json`) and one will lose. Pick one sync layer; let git be history-only behind it.

## Related

- Vault folder taxonomy: [vault/README.md](../vault/README.md)
- Lane-override YAML format: [profiles/README.md lane-override files](../profiles/README.md#lane-override-files)
- The deferred compiler design (not currently in use): [roadmap/profile-compilation.md](../../project/roadmap/profile-compilation.md)
