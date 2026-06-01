---
topic: proposals
status: implemented  # user-requested 2026-05-31; design approved + scripts written 2026-05-31
created: 2026-05-31
---

# Bootstrap installer (one-line full-stack setup)

> **Implemented 2026-05-31.** The scripts are written against this design and live at
> the repo root: [`install.sh`](../../install.sh) (the bootstrap brain) and
> [`install.ps1`](../../install.ps1) (the thin WSL2 launcher). This doc is now the
> as-built spec. Outstanding items are limited to the confirm-at-build residuals and a
> live smoke-test (see [Still open](#still-open-beforewhile-building)).

## What

A single hosted entry point that takes a user from nothing to a working Memoria
install: it installs the desktop apps (Obsidian, Zotero), provisions the Hermes
runtime and the seven Memoria profiles, lays the vault down in a chosen
directory, and walks the user through the few things that cannot be automated
(secrets, Zotero GUI config, Zotero plugin clicks).

The entry point is offered two ways, **inspect-first as primary**:

```bash
# Linux (Ubuntu/Debian) — recommended: download, read, run
curl -fsSL https://raw.githubusercontent.com/eranroseman/memoria-vault/main/install.sh -o install.sh
less install.sh
bash install.sh

# convenience one-liner
curl -fsSL https://raw.githubusercontent.com/eranroseman/memoria-vault/main/install.sh | bash
```

```powershell
# Windows — recommended: download, read, run
irm https://raw.githubusercontent.com/eranroseman/memoria-vault/main/install.ps1 -OutFile install.ps1
notepad install.ps1
.\install.ps1

# convenience one-liner
irm https://raw.githubusercontent.com/eranroseman/memoria-vault/main/install.ps1 | iex
```

## Why

Today's `install.ps1` / `install.sh` (now at the repo root) only do **step 5**
of the list below — register the seven Hermes profiles from an already-cloned
repo. Everything else is manual and spread across five how-to guides
([set-up-the-vault](../../docs/how-to-guides/setup/set-up-the-vault.md),
[-obsidian](../../docs/how-to-guides/setup/set-up-obsidian.md),
[-zotero](../../docs/how-to-guides/setup/set-up-zotero.md),
[-hermes](../../docs/how-to-guides/setup/set-up-hermes.md), plus the quickstart).
A new user must already have Obsidian, Zotero, Better BibTeX, Hermes, Python,
Git, and Pandoc installed before any of it works. The gap is a single,
guided first-run path.

## Goals / non-goals

**Goals**
- One command from zero to a runnable vault on macOS, Linux, and Windows.
- Idempotent: safe to re-run after a `git pull` (the current installer's contract).
- Detect-then-install; never clobber existing apps or credentials.
- Honest about what it cannot do (GUI clicks, secrets) — explain, don't fake.

**Non-goals**
- macOS support (out of scope for v0.1).
- Linux distros other than Ubuntu/Debian.
- Headless Zotero plugin installation (unsupported by Zotero — GUI only).
- Writing the user's API keys for them.
- Auto-enabling WSL2 (needs a reboot / admin; we link Microsoft's guide instead).
  On Windows, **no WSL2 means the installer does nothing at all** (see below).
- Replacing the per-profile redeploy path (`install.ps1` stays usable standalone).

## Entry point & safety model

Best practice for `curl|bash` / `irm|iex` installers, applied
([dev.to](https://dev.to/operous/how-to-build-a-trustworthy-curl-pipe-bash-workflow-4bb),
[kicksecure](https://www.kicksecure.com/wiki/Dev/curl_bash_pipe),
[buka.sh](https://knowledge.buka.sh/powershell-one-liners-for-installation-what-does-irm-bun-sh-install-ps1-iex-really-do/)):

| Practice | How |
|---|---|
| Inspect-first is the documented primary | One-liner shown as the convenience option, not the headline. |
| No partial-execution hazard | Entire script body wrapped in a `main` function (bash) / single top-level function (PS) invoked on the last line, so a truncated download can't run a half-command. |
| Consent before action | Print a numbered plan of exactly what will be installed/changed, then prompt `[y/N]` (skippable with `--yes` for CI). |
| `--dry-run` | Prints every action without executing. |
| No silent elevation | Never auto-`sudo` / never auto-relaunch as Admin. If a step needs elevation, stop and tell the user the exact command. |
| Idempotent | Detect each component; skip if present; only create `.env` if absent. |
| Pinned & checksummed where possible | Zotero `.xpi` downloads pinned to a release tag + SHA-256 verified. |

## Platform support matrix

Two platforms only. **macOS is out of scope for v0.1.** Linux is **Ubuntu/Debian
only** (apt + `.deb`); other distros are not supported in v0.1.

| Component | Linux (Ubuntu/Debian) | Windows |
|---|---|---|
| Package source | `apt` + official `.deb` files | winget (built in on Win 10/11) |
| Obsidian | official Obsidian `.deb` (`apt install ./obsidian.deb`) | `winget install -e --id Obsidian.Obsidian` |
| Zotero | [zotero-deb](https://github.com/retorquere/zotero-deb) apt repo (`.deb`) | `winget install -e --id DigitalScholar.Zotero` |
| Git | `apt` | in WSL2 (`apt`) — only hard pre-Hermes prereq |
| Pandoc | `apt` | in WSL2 (`apt`) — the one runtime Hermes does *not* provision |
| uv, Python 3.11, Node 22, ripgrep, ffmpeg | **provisioned by the Hermes installer** | same (inside WSL2) |
| Hermes runtime + `.memoria` Python | native (upstream `install.sh`) | **WSL2 (Ubuntu) only — else abort** |

**The Hermes installer provisions the runtimes.** Per the Hermes
[installation docs](https://hermes-agent.nousresearch.com/docs/getting-started/installation),
its `install.sh` auto-installs **uv, Python 3.11, Node.js 22, ripgrep, and ffmpeg** —
*"You do not need to install Python, Node.js, ripgrep, or ffmpeg manually."* The only
prerequisite is **Git**. So our bootstrap installs **only Git (if missing) and Pandoc**
before handing off to Hermes; it does **not** install Python/uv/Node itself. Ordering
matters: ensure Git → run the Hermes installer (brings the runtimes) → then the
`pip install` / `uvx` / profile steps work.

On Linux everything is one environment. On Windows, Obsidian + Zotero + the vault
files are Windows-native (winget + the Windows filesystem); Hermes and everything it
provisions live in **WSL2 Ubuntu** and read the vault across `/mnt/c`.

Hermes installs via its upstream script
(`curl -fsSL https://raw.githubusercontent.com/NousResearch/hermes-agent/main/scripts/install.sh | bash`),
which we invoke rather than reimplement.

## The install flow (maps to the nine requested steps)

1. **Download + explain.** Print the plan and what each step will do; prompt for consent.
2. **Copy the vault to the right directory.** `git clone` the repo to a temp/staging
   location, then copy `vault/` to a **default target off OneDrive**
   (`%USERPROFILE%\Memoria` on Windows, `~/Memoria` on Linux), **prompting the user to
   confirm or override**. The chosen path becomes `$VAULT_PATH` for the rest of the run.
3. **Obsidian.** Detect; if absent, **show the install command and run it on consent**
   (`apt install ./obsidian.deb` on Ubuntu/Debian, `winget install` on Windows) —
   guide, don't silently automate. (Community plugins need no separate step — they ship
   bundled inside `vault/`.)
4. **Hermes.** Detect; install via its upstream installer if absent. On Linux this is
   native; on Windows it runs **inside WSL2** (which is a hard prerequisite — see
   [Windows + WSL2](#windows--wsl2-the-decided-rule)).
5. **Memoria components from `.memoria/`.** `pip install -r .memoria/mcp/requirements.txt`,
   then stage each profile, substitute `{{VAULT_PATH}}`, and `hermes profile install`
   (this is today's `install.ps1`/`install.sh` logic, folded in as a step). On Windows
   this whole step runs in WSL2. Then provision the **skills** the profiles depend on —
   but note that verification (see [Skills: verification of all 28 lane-override IDs](#skills-verification-of-all-28-lane-override-ids))
   found most are Memoria-custom and must be *authored*, not installed.
6. **Zotero.** Detect; if absent, **ask** the user and run the install command on
   agreement (`zotero-deb` apt `.deb` on Ubuntu/Debian; `winget` on Windows) — same
   guide-don't-automate approach as Obsidian.
7. **Explain private information.** Print the secrets checklist (below) and the exact
   file paths to edit — never write keys automatically.
8. **Zotero plugins (only if Zotero is present/just-installed).** Download the
   recommended `.xpi`s (Better BibTeX required; MarkDB-Connect recommended;
   RTF/ODF Scan optional), verify checksums, open Zotero, and print the GUI
   steps to install them plus the Better BibTeX citekey-formula and auto-export config.

## Windows + WSL2 (the decided rule)

Per Memoria's own design, **Hermes runs only on Linux/WSL2; Windows is the editing
surface**. WSL2 is therefore a **hard prerequisite for the entire Windows install**,
checked first:

- **If WSL2 is not present → the installer does nothing.** It prints a short
  explanation that Memoria on Windows requires WSL2, links the official guide
  (`https://learn.microsoft.com/windows/wsl/install`), and **exits without
  installing Obsidian, Zotero, the vault, or anything else** (do not attempt to
  enable WSL2 — that needs admin + a reboot). The user enables WSL2, then re-runs.
- **If WSL2 is present → proceed.** The thin `install.ps1` launcher ensures Obsidian +
  Zotero on the Windows side (guide-on-consent), then **hands the entire rest of the
  flow to bash inside WSL2** (`wsl bash install.sh`) — vault copy, Hermes, `.memoria`,
  profiles — wiring the vault at its `/mnt/c/…` path for Hermes's `mcp.json`. The
  launcher **echoes each WSL command** it runs (and that is what `--dry-run` shows), so
  a failed step degrades to a copy-pasteable manual path — see the
  [decision note](#one-wsl2-path-not-two) below. There is no second copy of the install
  logic in PowerShell.

Note the dual path form: Obsidian uses the Windows path (`C:\Users\…\Memoria`),
Hermes's `mcp.json` uses the WSL view (`/mnt/c/Users/…/Memoria`). The installer
computes both and substitutes the correct one on each side. Watch the OneDrive
`/mnt/c` seam.

### One WSL2 path, not two

*Do we need both an "automatic" and a "manual" WSL2 mode?* **No — one path.** The
installer always attempts the automatic in-WSL invocation and **echoes each WSL
command before running it**. If a step fails (or under `--dry-run`), those same
printed commands are the manual fallback. So "manual" is not a separate mode the
user chooses up front — it is the transparency/​recovery output of the single
automatic path. This keeps the one-line promise while staying debuggable.

## Components installed (completeness checklist)

Cross-checked against every setup doc. ✅ = automated, ⚠️ = assisted (download + guide), ❌ = explained only.

| Layer | Method | Status |
|---|---|---|
| Git | prereq; `apt`/winget if missing | ✅ |
| Pandoc | `apt`/winget (not provisioned by Hermes) | ✅ |
| uv, Python 3.11, Node 22, ripgrep, ffmpeg | **provisioned by the Hermes installer** | ✅ (via Hermes) |
| Obsidian app | detect; show command, run on consent | ⚠️ guided |
| Obsidian community plugins (8) + configs | bundled in `vault/` | ✅ (copied) |
| Obsidian REST API key | regenerated on first launch | ❌ explain (copy into `.env`) |
| Hermes runtime | upstream installer (WSL2 on Win) | ✅ |
| `.memoria` MCP servers (`policy_mcp.py`, `policy_hook.py`) | `pip install -r requirements.txt` | ✅ |
| Seven Hermes profiles | stage + `{{VAULT_PATH}}` + `hermes profile install` | ✅ |
| Skills — 7 installable | `git clone` K-Dense (5) + `hermes skills install official/research/{arxiv,llm-wiki}` (2) | ✅ recipe |
| Skills — 20 Memoria-custom | author `SKILL.md` into profile `skills/` dirs; ship in vault | ❌ pending authorship |
| Per-profile `.env` | bootstrap from `.env.EXAMPLE` if absent | ✅ create / ❌ fill |
| Model provider (v0.1 = **KiloCode**) | `KILOCODE_API_KEY` in `.env` | ❌ explain |
| Zotero app | detect; ask, run command on consent | ⚠️ guided |
| Better BibTeX (required) | download `.xpi` + GUI install | ⚠️ |
| MarkDB-Connect (recommended) | download `.xpi` + GUI install | ⚠️ |
| RTF/ODF Scan (optional) | download `.xpi` + GUI install | ⚠️ |
| Better BibTeX config (citekey formula, auto-export path) | GUI-only | ❌ explain |
| Other API keys (OpenAlex email, S2, PubMed, GitHub) | user-supplied | ❌ explain |

## Secrets / private information (step 7 output)

The installer prints this and the exact paths; it writes nothing.

**v0.1 model provider = KiloCode only.** Every profile's `config.yaml` ships
`provider: kilocode` (`base_url: https://api.kilo.ai/api/gateway`, model
`~anthropic/claude-sonnet-latest`). So a v0.1 user authenticates Hermes **once** to
the KiloCode gateway — they do **not** need a separate Anthropic/OpenRouter key.
Swapping to a direct provider (e.g. `anthropic` + `claude-sonnet-4-6`) is a documented
later option, not a v0.1 requirement.

| Secret | Where to get it | Goes in |
|---|---|---|
| **`KILOCODE_API_KEY`** | [kilo.ai](https://kilo.ai) (the gateway in `config.yaml`) | each profile `.env` (or once in `~/.hermes/.env`); `hermes config set` routes API keys to `.env` |
| `OBSIDIAN_API_KEY` | Obsidian → Local REST API (64-char hex, first launch) | every profile `.env` |
| `OPENALEX_EMAIL` | any working address (polite pool) | Librarian `.env` |
| `SEMANTIC_SCHOLAR_API_KEY`, `PUBMED_API_KEY`, `GITHUB_TOKEN` | per [set-up-zotero § API keys](../../docs/how-to-guides/setup/set-up-zotero.md) | Librarian `.env` (optional) |

Profile `.env` paths: `~/.hermes/profiles/memoria-<name>/.env` (the WSL2 home on Windows).

> **Resolved (2026-05-31).** Confirmed against the Hermes docs: KiloCode authenticates
> via the **`KILOCODE_API_KEY`** env var (`KILOCODE_BASE_URL` optional, defaults to the
> gateway already in `config.yaml`); `ANTHROPIC_API_KEY` is **not** required under
> `provider: kilocode`. All seven `distribution.yaml` `env_requires` were updated to
> require `KILOCODE_API_KEY` and demote `ANTHROPIC_API_KEY` to optional (swap-only), and
> the setup docs were reconciled to match.

## ACP, model, and auxiliary configuration

**ACP (the Obsidian chat pane).** The bundled `agent-client` plugin is an ACP *client* — it
launches a Hermes ACP server per agent. The Hermes side needs the **ACP extra installed**
(`pip install 'hermes-agent[acp]'`, or `pip install -e '.[acp]'` from source), which provides
the `hermes acp` command. The bootstrap must install it before the pane works; config is the
standard `~/.hermes/{.env,config.yaml,skills/}` ([ACP docs](https://hermes-agent.nousresearch.com/docs/user-guide/features/acp)).

> **`-p` in ACP mode — confirmed (2026-05-31).** The [CLI reference](https://hermes-agent.nousresearch.com/docs/reference/cli-commands)
> confirms `-p`/`--profile` is a **global** flag applying to every subcommand, so
> `hermes -p memoria-<profile> acp` (as in `agent-client/data.json.example`) is valid and the
> four-agent picker design holds. Live smoke-test once ACP is installed: `hermes -p memoria-socratic acp`.

**Models — per profile (done, aliases confirmed 2026-05-31).** Each profile `config.yaml` sets
the tier: Linter/Librarian/Coder → `~anthropic/claude-haiku-latest`; Mapper/Writer →
`…sonnet-latest`; Socratic/Verifier → `…opus-latest` (`provider: kilocode`). Alias strings
confirmed against the KiloCode catalog. **Auxiliary models** are set globally (split: GLM 4.7 Flash
for light slots + DeepSeek V4 Flash for compression) — see [hermes/configuration.md](../../docs/how-to-guides/hermes/configuration.md).

**Auxiliary models — set in the *global* `~/.hermes/config.yaml`.** Auxiliary slots default to
`provider: auto` (reuse the profile's main model) — so a Verifier title-gen/compression call
would burn Opus. Split the cheap-task slots: `title_generation`, `approval`, `mcp`, `skills_hub`
→ `z-ai/glm-4.7-flash` ($0.07/$0.40 per 1M, cheapest input); `compression` → `deepseek/deepseek-v4-flash`
(1M ctx — GLM's 202K is too tight to safely summarize a near-full conversation). Cost traps:
`z-ai/glm-5-turbo` is *not* budget ($1.2/$4.0). `vision`/`web_extract` → a cheap multimodal
(e.g. `google/gemini-2.5-flash`) if used. This is global config the human owns —
Memoria's per-profile `config.yaml` only overrides the `model` block (Hermes replaces config
*sections* wholesale, so a per-profile `auxiliary:` block would clobber the global one).

## Architecture: bootstrap vs profile-installer

**Two files, one implementation** — not two installers:

- **`install.sh` (bash)** is the single real script. It holds the whole bootstrap flow
  **and** the profile-install logic. The existing bash profile logic
  (stage → substitute `{{VAULT_PATH}}` → `hermes profile install` → bootstrap `.env`,
  idempotent) is **reused — refactored from a top-to-bottom script into a function** the
  bootstrap calls. A `--profiles-only` flag exposes just that function for the "re-run
  after `git pull`" redeploy path
  ([redeploy-profiles](../../docs/how-to-guides/maintenance/redeploy-profiles.md)). An
  `--only NAME[,NAME]` filter restricts that step to named profiles (forwarded from
  `install.ps1` as `-Only`) — **decision 2026-06-01: kept**, because per-profile redeploy is
  the high-frequency move during profile authoring; it carries over from the old
  profile-installer and pairs with `--profiles-only`. (It is the one flag beyond the
  minimal `--dry-run`/`--yes`/`--profiles-only` surface plus the `--no-apps`/`--vault`
  bootstrap controls.)
- **`install.ps1` (PowerShell)** is a **thin launcher only**: gate on WSL2 → ensure the
  two GUI apps (Obsidian, Zotero) Windows-side → `wsl bash install.sh` (forwarding
  flags). It contains **no install logic**. The existing PowerShell *profile* logic is
  **retired**, not reused.
- Why retire it (correctness, not just simplification): today's `install.ps1` runs
  `hermes profile install` natively on Windows, but Hermes is **WSL2-only on Windows** —
  so that path can't actually work end-to-end. Profiles must be installed *inside* WSL,
  which is exactly what the bash brain + thin launcher do. The installer's real logic has
  to live in bash regardless; PowerShell can only be a doorway into the Linux/WSL side.
- Both files live at the repo root (already moved there) — justified now that the
  bootstrap is the clone/entry point, not a vault-internal artifact.

## Simplifying decisions (v0.1)

Deliberate scope/assumption choices that keep the script small. Each trades a little
breadth for much less shell to build and maintain.

- **One bash implementation; `install.ps1` is a thin WSL2 launcher** (above).
- **Guide app install, don't fully automate.** Detect Obsidian/Zotero; if absent,
  print the exact `winget`/`apt` one-liner and run it **on consent** — no version
  parsing, no `.deb`-URL maintenance, no silent installs.
- **Presence checks, not version gates.** Check a tool is *there*; let `pip`/Hermes
  surface a clear error if it is too old, rather than parsing versions in the installer.
- **Assume `local-only` deployment.** No Syncthing/VPS/obsidian-sync logic — multi-device
  is Phase 3 per [timeline.md](../operations/timeline.md).
- **Default the vault off OneDrive** (`%USERPROFILE%\Memoria` on Windows, `~/Memoria`
  on Linux; prompt to override) — avoids OneDrive fighting Hermes's WSL writes across
  `/mnt/c`. Git is the backup, so losing OneDrive sync of the vault is fine.
- **Don't install language runtimes.** The Hermes installer provisions uv, Python 3.11,
  Node 22, ripgrep, and ffmpeg — verified in the Hermes install docs. Our bootstrap adds
  only **Git** (pre-Hermes) and **Pandoc** (not provisioned). No separate Python/uv/Node step.
- **Bash, not POSIX `sh`;** Ubuntu/Debian + winget package managers assumed present;
  Hermes installed via its own upstream script. No package-manager bootstrapping.
- **Keep the safety rails** (`--dry-run`, up-front consent, `main`-guard) — cheap
  insurance for a script that installs system software, and `--dry-run` doubles as the
  WSL command transcript.

## Documentation changes (Diátaxis)

`docs/` follows [Diátaxis](https://diataxis.fr/); changes slot accordingly:

- **Tutorial** — new "install in one line" happy-path ([tutorials/01](../../docs/tutorials/01-set-up-from-zero.md) rewritten around the bootstrap).
- **How-to/setup** — `set-up-the-vault` becomes "run the bootstrap"; `set-up-obsidian`/`-zotero`/`-hermes` shrink to the manual/assisted residue (secrets, Zotero GUI, WSL2 choice). `quickstart` leads with the one-liner.
- **Reference** — `on-disk-layout` (installers at repo root, vault copied to target), `distribution-model` (the repo is the unit; `vault/` is no longer the standalone deliverable — resolves the open conflict), `plugins` (unchanged; bundling already documented).
- **Explanation** — short "why a bootstrap, and why inspect-first" note.

## Trade-offs

- **Surface area.** Still nontrivial (WSL2 orchestration + Zotero `.xpi` handling), but
  cut hard by the simplifying decisions: one bash implementation (no PowerShell port),
  two platforms not three, guide-don't-automate app installs, presence-only checks, and
  `local-only` only. The residue leans on upstream installers and on guidance for the
  GUI/secret steps that genuinely can't be automated.
- **`curl|bash` trust.** Inherent to the pattern; mitigated by inspect-first framing,
  the `main`-guard, consent, and `--dry-run`.
- **Partial automation can imply full automation.** The Zotero/secrets steps are
  assisted, not automatic — the UX must make that explicit so users don't assume
  the system is wired when it isn't.
- **Distribution-model change.** `vault/` stops being independently distributable.
  Acceptable because the real workflow is cloning the whole repo, but it is a
  documented design reversal that needs the `distribution-model.md` rewrite.

## Dependencies

- A public repo + raw URL for the hosted one-liner (`eranroseman/memoria-vault`).
- Upstream Hermes installer remaining at its current URL.
- `.memoria/mcp/requirements.txt` and the per-profile wiring (part of v0.1) — **both
  exist today** (see explanation below).
- Decision on the open questions below.

### Pinned skill install IDs

Resolved against the live sources (2026-05-31). The official Hermes skills ship with the
Hermes install (bundled / `official/<area>/<name>`); the lane-override allows them by name.
External skills are installed by the bootstrap; the two Memoria skills ship in the vault.

| Skill(s) | Source | How it's provisioned |
|---|---|---|
| `paper-lookup`, `pyzotero`, `citation-management`, `literature-review`, `scientific-writing`, `scikit-learn`, `umap-learn` | K-Dense | `git clone https://github.com/K-Dense-AI/scientific-agent-skills` → `~/.hermes/skills/` (auto-discovered) |
| `arxiv` | official Hermes | `official/research/arxiv` (bundled with Hermes; allow by name) |
| `llm-wiki` | official Hermes | `official/research/llm-wiki` |
| `obsidian` | official Hermes | `official/note-taking/obsidian` |
| `ocr-and-documents` | official Hermes | `official/productivity/ocr-and-documents` |
| `github-repo-management` | official Hermes | `official/github/github-repo-management` |
| `codex`, `claude-code` | official Hermes | `official/autonomous-ai-agents/{codex,claude-code}` |
| `obsidian-markdown` | kepano/obsidian-skills | `hermes skills install kepano/obsidian-skills/skills/obsidian-markdown` (or clone + `external_dirs`) |
| `qmd` | skills.sh / `tobi/qmd` | `hermes skills install skills-sh/moltbot/skills/qmd`; CLI is Node ([tobi/qmd](https://github.com/tobi/qmd)). **Packaging is fragmented — confirm the exact skill at build.** |
| `obsidian-paper-note`, `retraction-check` | **Memoria-authored** | ship as `SKILL.md` in the profile `skills/` dirs (authored 2026-05-31) |
| `rest-passthrough` | policy capability | not a skill — a lane-override capability token |

Two confirm-at-build items remain: whether the official skills are bundled vs. need
`hermes skills install official/…`, and the exact `qmd` skill packaging.

### What `.memoria/mcp/requirements.txt` is

The Python dependency list for Memoria's MCP servers, installed by step 5
(`pip install -r .memoria/mcp/requirements.txt`) before profile registration. It is
deliberately minimal — the policy decision core is dependency-light by design:

- `mcp>=1.2.0` — the Model Context Protocol SDK; provides `mcp.server.fastmcp.FastMCP`,
  the thin server wrapper around the policy decision engine (`policy_mcp.py`).
- `PyYAML>=6.0` — parses the lane-override files (`.memoria/lane-overrides/*.yaml`) the
  live policy server loads at startup. (The decision core's `--self-test` runs without it.)

`.memoria/mcp/` also ships `policy_mcp.py`, `policy_hook.py`, `board_export.py`, and
`metrics_aggregate.py`. `tasks_mcp.py` (the Kanban front) is Phase-4/deferred and not
yet authored — its deps get added here when it lands.

### Skills: verification of all 28 lane-override IDs

The profiles' capabilities are gated by the `lane-overrides/*.yaml` allowlists, which name
**28 distinct skills**. Each was verified (2026-05-31) against the two real sources — the
[K-Dense repo](https://github.com/K-Dense-AI/scientific-agent-skills) and the **official
Hermes skills registry** (`NousResearch/hermes-agent/skills/<area>/`, enumerated via the
GitHub API). The headline result: **only ~7 are installable; ~20 are Memoria-coined and
do not exist in any registry — they must be authored.** Skills live in `~/.hermes/skills/`
and are auto-discovered; per-profile `skills/` dirs currently ship as empty `.keep`.

**A. K-Dense — installable via `git clone …K-Dense-AI/scientific-agent-skills` → `~/.hermes/skills/` (5, verified present):**
`paper-lookup`, `pyzotero`, `citation-management`, `literature-review`, `scientific-writing`.

**B. Official Hermes registry — installable, but the lane-override name differs from the registry ID (rename or wrap):**
- `arxiv-search` → official **`research/arxiv`** (`hermes skills install official/research/arxiv`)
- `llm-wiki-draft` → official **`research/llm-wiki`**
- `obsidian-paper-note` builds on official **`note-taking/obsidian`** (but the paper-note skill itself is custom — bucket C)

**C. Memoria-custom — NO registry ID; must be hand-authored as `SKILL.md` in the profile `skills/` dirs (20):**
`scaffold-code-note`, `workspace-coordinate`, `commit-and-document` (Coder); `obsidian-paper-note` (Librarian);
`schema-check`, `graph-analyze`, `health-report`, `session-log` (Linter); `scope-project`, `gap-report`,
`cluster-mapping`, `comparative-brief` (Mapper); `socratic-processing`, `lens-reading` (Socratic);
`cite-check`, `similarity-check`, `find-duplicates`, `retraction-check` (Verifier); `note-refactor`,
`counter-outline` (Writer). None are in K-Dense or the official registry. (The archived script *tried*
`research/cite-check`, `research/graph-analyze`, etc. — but the official `research/` area only contains
`arxiv`, `blogwatcher`, `llm-wiki`, `polymarket`, `research-paper-writing`, so those installs would have
failed; that explains its many "install failed — do it manually" fallbacks.)

**D. Not a skill (1):** `rest-passthrough` is a policy capability token (it also appears in *deny* lists), not an installable skill.

> **This is an authorship gap, not an install gap.** The installer's skills step can only
> do buckets A + B (clone K-Dense; `hermes skills install official/research/arxiv` and
> `…/llm-wiki`). The 20 bucket-C skills must **ship in the vault** (`vault/.memoria/profiles/<p>/skills/`)
> — they are currently unwritten `.keep` placeholders. `implementation-status.md` should
> reclassify skills from "pending install" to "pending authorship (20 custom) + install (7)".
>
> **Naming drift to reconcile:** lane-overrides use `arxiv-search`/`llm-wiki-draft` (vs the
> official `arxiv`/`llm-wiki`) and `cluster-mapping` (vs `cluster-map` in
> [commands.md](../../docs/reference/commands.md)). Pin these names before authoring.

Hermes **bundles** (`hermes bundles create …`, a YAML alias over already-present skills)
are *optional* for Memoria — the lane-override allowlist is the gate, not a bundle.

### How each custom skill is handled (decision: adapt, **no wrappers**)

Per the adopted decision, none of these become wrapper skills. Each is handled by
*adapting the design* — the lane-override points at a real skill ID and the orchestration
lives in the profile `SOUL.md` — except **two deterministic pipelines** that stay real
(thin) skills. Each was checked against the full official Hermes library, K-Dense, kepano's
obsidian-skills, and GitHub; no skill matches any of the 20 by name+purpose, but only **2
need authoring as skills**.

**Prompt-only → profile `SOUL.md`, no artifact (3):** `socratic-processing`, `lens-reading`,
`counter-outline` — conversational behaviors ("question-only", "read through lens X",
"produce 2–3 outlines"), not tool-using skills.

**Direct-use → lane-override names the real skill ID; procedure in `SOUL.md`; nothing authored (6):**

| Skill | Lane-override points at |
|---|---|
| `note-refactor` | kepano `obsidian-markdown` |
| `workspace-coordinate` | `autonomous-ai-agents/{claude-code,codex,opencode}` |
| `commit-and-document` | `github/github-repo-management` |
| `cluster-mapping` | K-Dense `scikit-learn` (HDBSCAN) + `umap-learn` |
| `similarity-check` | `qmd` (hybrid BM25+vector vault search; skills.sh skill — the documented search backbone) |
| `find-duplicates` | same `qmd` backbone as `similarity-check` |

**Different mechanism, not a Hermes skill (2) — both now done:** `scaffold-code-note` →
a **QuickAdd** Template command (`Memoria: scaffold code note`, like capture-fleeting /
write-claim); `graph-analyze` → a new **`detectors.py`** function (`graph_analyze`,
**pure stdlib** — orphan-synthesis-note detection over the wikilink graph; no `networkx`).

**Already in `detectors.py` (2):** `schema-check` (= `frontmatter_schema_check`) and
`health-report` (= `run_all()` + `verdict()`) — confirmed by the audit below. No authoring.

**Memoria logic → `SOUL.md` procedure composing direct-use skills (5):** `session-log`
(or Hermes's own session logging), `scope-project`, `gap-report`, `comparative-brief`,
`cite-check` (uses the vault + `.bib`; [bibguard](https://github.com/GeoffreyWang1117/bibguard)
/ [hallucinator](https://github.com/gianlucasb/hallucinator) are references for the pattern).
*If one later proves to need determinism it can be promoted to a real skill — but the default stays a procedure.*

**Authored as a real (thin) skill — the only two (2).** Kept as skills because they are
deterministic multi-step pipelines where prompt orchestration is less reliable. Pre-authoring
search (2026-05-31) found no drop-in skill but clear components + prior art to compose:

- **`obsidian-paper-note`** (ingest: Zotero metadata → PDF extraction → literature note).
  Compose **K-Dense `pyzotero`** (metadata) + **K-Dense `pdf`** *or* official
  `productivity/ocr-and-documents` (extraction) + **`note-taking/obsidian`** (write to
  `20-sources/01-papers/` using the paper-note template). Starting point: the archived
  research-wiki **`obsidian-paper-note` SKILL.md** ([setup-hermes-research-wiki.sh](../../../_archived/research-wiki/80-docs/setup-hermes-research-wiki.sh), lines ~324-368). Prior art:
  [zotero-obsidian-claude](https://github.com/AmandaWuMMMqq/zotero-obsidian-claude) (a
  Claude-based Zotero→Obsidian pipeline, close to the Librarian's ingest). Note the bundled
  **obsidian-citation-plugin already creates these notes from `.bib` on the human side** — the
  skill is the *agent* path with PDF extraction + enrichment.
- **`retraction-check`** (DOI → retracted?). The [open-retractions](https://github.com/open-retractions/open-retractions)
  API is the core: `GET https://openretractions.com/api/doi/{doi}/data.json` → `retracted`
  boolean (wraps Retraction Watch); optionally cross-check CrossRef retraction metadata.
  `pyzotero` resolves vault DOIs; compare against each paper note's `pub_status`. Pure
  HTTP + boolean compare — deterministic, matching the Verifier SOUL.md spec.

> **`detectors.py` audit (2026-05-31).** The Linter is **not a set of skills — it's the
> already-shipped `detectors.py`** (7 deterministic, report-only detectors + a
> `verdict()` PASS/REVIEW/FAIL band + `--self-test`). Two of its four lane-override "skills"
> are **already implemented** there (`schema-check`, `health-report`); `graph-analyze` has
> since been **added to `detectors.py`** (`graph_analyze`, pure stdlib — no `networkx`), so
> only `session-log` remains. The Linter's allowlist grants **no Hermes skills**
> (`allow.skills: []`) — `detectors.py` runs via the profile's terminal capability.

Net: **3 + 6 + 2 + 2 + 5 + 2 = 20.** All of it is now in place (2026-05-31): the **2 authored
skills** (`obsidian-paper-note` in the Librarian's `skills/`, `retraction-check` in the
Verifier's), the **`graph_analyze` `detectors.py` function**, the **`Memoria: scaffold code note`
QuickAdd choice**, and the lane-override + `SOUL.md` edits for the rest — no wrapper files.

### What "per-profile wiring" means

v0.1 initially shipped only each profile's `SOUL.md` (system prompt). The **profile
wiring** — also part of v0.1, per the glossary's "complete system" definition, not a
later version — is the three additional files per profile that make
`hermes profile install` actually work. All seven profiles now have them:

- `config.yaml` — model routing (the `provider: kilocode` block) plus the `hooks` block
  that registers the policy gate (`pre_tool_call` / `post_tool_call` → `policy_hook.py`).
- `mcp.json` — the MCP servers the profile connects (the `obsidian` vault-access server
  and the `policy` server), with `{{VAULT_PATH}}` placeholders the installer substitutes.
- `distribution.yaml` — install metadata + the `env_requires` list (the secrets the
  profile expects; now requires `KILOCODE_API_KEY`, with `ANTHROPIC_API_KEY` optional).

The installer treats `SOUL.md + config.yaml + mcp.json + distribution.yaml` as the
required set; a profile missing any of them is skipped (the "graceful skip" behavior
from the walkthrough). Profiles also carry `skills/` and `cron/` directories.

## Decisions (resolved 2026-05-31)

1. **Default vault directory** — off OneDrive: `%USERPROFILE%\Memoria` (Windows),
   `~/Memoria` (Linux); prompt to override. ✅
2. **macOS** — out of scope for v0.1 (dropped). ✅
3. **Linux** — Ubuntu/Debian only; Obsidian and Zotero installed via `.deb`
   (Obsidian official `.deb`; Zotero via the `zotero-deb` apt repo). ✅
4. **Pandoc** — required at install time (not deferred). ✅
5. **WSL2 modes** — one path, not two: automatic in-WSL invocation that echoes its
   commands (manual = the recovery/transparency output, not a separate mode). ✅
6. **Windows without WSL2** — install nothing; link Microsoft's guide and exit. ✅
7. **Model provider** — v0.1 is KiloCode-only; no separate Anthropic key required. ✅
8. **One bash implementation; `install.ps1` is a thin WSL2 launcher** — no duplicated
   flow in PowerShell. ✅
9. **Desktop apps: guide, don't fully automate** — detect, then show/run the install
   command on consent; no version parsing or `.deb`-URL upkeep. ✅
10. **Presence checks, not version gates;** **`local-only` deployment assumed;** bash
    (not POSIX `sh`); package managers assumed present. ✅
11. **Keep the safety rails** — `--dry-run`, up-front consent, `main`-guard. ✅

## Still open (before/while building)

The scripts are **written and validated** (`bash -n` + a full `--dry-run --yes` pass;
`install.ps1` parses clean). Each remaining item is marked in the script as a
`TODO(confirm-at-build)` comment or a warn-not-fail branch, so the installer runs today and
these only refine it:

- **Hermes install mechanism** — `ensure_hermes` currently does `pip install --user
  'hermes-agent[acp]'`. The official installer script (which also provisions
  uv/python/node/ripgrep/ffmpeg) is preferred once its URL is pinned. The ACP extra is
  ensured either way.
- **Official-skills bundled-vs-`install`** — `install_skills` attempts `hermes skills install
  official/…` and warns-not-fails (a Hermes that already bundles them is fine).
- **`qmd` packaging** — attempts `skills-sh/moltbot/skills/qmd`, warns-not-fails; the CLI is
  Node ([tobi/qmd](https://github.com/tobi/qmd)). Confirm the exact skill.
- **Live smoke-test** — `hermes -p memoria-socratic acp` (design says it works; verify on a
  real install — printed as step 4 of the installer's "Next steps").

**Hosting — confirmed:** public repo `eranroseman/memoria-vault`, scripts at the repo root on
`main`. One-liner targets: `https://raw.githubusercontent.com/eranroseman/memoria-vault/main/install.{sh,ps1}`.
These URLs now host the **bootstrap** (the old profile-installer survives as
`install.sh --profiles-only`, the maintenance path).

(Resolved 2026-05-31: bootstrap `install.sh` + thin `install.ps1` written; the 2 skills
authored (`obsidian-paper-note`, `retraction-check`); `graph-analyze` detector +
`scaffold-code-note` QuickAdd done; the 5 `SOUL.md` procedures + 3 prompt-only behaviors in
place; skill IDs pinned; model aliases + ACP `-p` confirmed; KiloCode auth =
`KILOCODE_API_KEY`; `qmd` kept (skills.sh); skill-name drift reconciled.)
