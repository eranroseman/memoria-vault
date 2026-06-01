# AGENTS.md — working guidelines for AI agents in this repo

Conventions for any AI agent (Claude Code, Hermes, etc.) making changes to
`eranroseman/memoria-vault`. Human contributors: see [CONTRIBUTING.md](CONTRIBUTING.md).

This file encodes hazards learned the hard way. Following it avoids the two
failure modes that bite agents here: the **auto-commit hook** entangling your
work, and the **branch protection** rejecting direct pushes.

---

## 1. Branch before you edit — always

**Create your own branch as the first action of any edit task**, off the latest
`origin/main`:

```bash
git fetch origin && git switch -c fix/<thing> origin/main
```

**Why this is non-negotiable here:** an editor auto-backup (obsidian-git style)
periodically commits the working tree on a timer — you'll see commits titled
`vault: <timestamp> N files`. If you edit while on `main` or on a branch the user
is also touching, that hook bundles your in-progress edits together with the
user's unrelated work into one commit, and can spawn phantom branches that orphan
work. A dedicated branch keeps your change isolated and reviewable.

## 2. Stage by explicit path — never `git add -A`

The working tree may hold the user's parallel work-in-progress or hook-generated
churn. Stage only the files you changed:

```bash
git add install.sh                      # yes — explicit
git add project-files/decisions/24-*.md # yes
git add -A                              # NO — sweeps in others' work
```

If you find unmerged work you didn't author tangled into a branch (new ADRs,
renames, a stash), **preserve it** (back it up / leave the stash) and surface it
to the user. Never delete a branch or stash that holds work you didn't create
without confirming its content is already on `main`.

## 3. `main` is protected — use the PR flow

Direct `git push origin main` is **rejected** (`GH013` — repository ruleset). The
flow is:

```bash
git push -u origin <branch>
gh pr create --base main --fill          # or --title/--body
gh pr checks <n> --watch                  # wait for green (see §4)
gh pr merge <n> --squash --delete-branch
```

Then resync local main:

```bash
git checkout main && git fetch origin && git reset --hard origin/main
```

**Known quirk:** `gh pr merge` may print `fatal: Not possible to fast-forward,
aborting` — this is `gh` failing to update your *local* main; the merge still
**succeeds server-side**. Verify with `gh pr view <n> --json state -q .state`
(expect `MERGED`), then resync as above. Don't re-attempt the merge.

If a PR shows `BEHIND` (strict checks require an up-to-date branch), run
`gh pr update-branch <n>` and wait for checks to re-run.

## 4. Required status checks

Three checks are **required** by the branch ruleset and must all pass:

| Check | Runs |
| --- | --- |
| `docs-doctor` | structural lint of `docs/` (broken links, misfiled files) |
| `shellcheck (install.sh)` | shell lint |
| `PSScriptAnalyzer (install.ps1)` | PowerShell lint |

**CI invariant — do not break this:** a workflow that backs a *required* status
check must **not** have a `paths:` filter. A path-filtered required check never
reports on PRs that don't touch those paths, leaving them permanently `BLOCKED`.
Both `docs-doctor.yml` and `lint-installers.yml` therefore run on every push/PR
unconditionally. If you add a new required check, follow the same rule.

**Linter notes:** `install.ps1` is an interactive installer, so `Write-Host` is
intentional and excluded via `PSScriptAnalyzerSettings.psd1`; PowerShell
functions must use approved verbs (`Install-`, not `Ensure-`).

## 5. Test before you commit

Every installer bug in this repo's history was caught by *running* the code, not
reading it. Before opening a PR:

- **Shell** (`install.sh`): `bash -n install.sh` (parse) + a `--dry-run` pass.
- **PowerShell** (`install.ps1`): `Invoke-ScriptAnalyzer -Settings ./PSScriptAnalyzerSettings.psd1`.
- **Python** (`.memoria/mcp/*.py`, `detectors.py`): run `--self-test`
  (`policy_mcp.py`, `policy_hook.py`, `board_export.py`, `metrics_aggregate.py`,
  `detectors.py` all support it).
- **Installer end-to-end:** deploy into a *throwaway* vault
  (`bash install.sh --yes --no-apps --vault ~/Memoria-test`), verify, then clean
  up — never test against the real `~/Memoria`.

## 6. Runtime / platform facts

- The Hermes runtime runs on **Linux/WSL2**; Windows is only the editing surface.
  `install.ps1` is a thin launcher that hands off to `install.sh` inside WSL2.
- Line endings: `.gitattributes` pins `*.sh`/`*.py`/`*.yaml`/`*.json` to **LF**
  (a CRLF in `install.sh` breaks the WSL2 shebang). Don't override it.
- MCP deps install into a vault-local venv (`<vault>/.memoria/.venv`); the
  installer wires that interpreter into each profile's `mcp.json`/`config.yaml`.
- Secrets live only in `~/.hermes/profiles/<profile>/.env` and gitignored vault
  files (shipped as `.example`). **Never** commit a real key; if one leaks,
  rotate it.

## 7. Profiles and the vault

- Agent profiles live under `vault/.memoria/profiles/memoria-*/` and follow the
  `SOUL.md` / `AGENTS.md` / `config.yaml` / `mcp.json` / `distribution.yaml`
  structure. Keep the seven in sync.
- Authoritative design is in `docs/` (Diátaxis) and `project-files/decisions/`
  (ADRs). `notes/` and working reports are scratch — don't treat them as canon.
