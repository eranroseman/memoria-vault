---
topic: tests
title: Installer test plan
status: draft
parent: Test plans
grand_parent: Testing
nav_order: 18
---

# Installer test plan — v0.1 (S0–S3)

The clean-install end-to-end the other plans *assume has already happened*: `scripts/install.ps1` for native Windows production and `scripts/install.sh` for Linux/WSL testing, deploying the five profiles, substituting `{{VAULT_PATH}}`, seeding `.env`, copying plugins, registering profiles with Hermes, and surviving a re-run. Backs **S0-S3**. Installer *lint* is covered headless ([Headless test plan](headless-test-plan.md) §C); agent behaviour after install is the [Hermes CLI plan](hermes-cli-test-plan.md); this plan is *the install itself*.

**Where to run.** A **throwaway target** — never the real production vault. Windows production uses `install.ps1` against a disposable Windows folder such as `$env:USERPROFILE\Memoria-test`. Linux/WSL testing uses `install.sh --vault ~/Memoria-test`. Discard the target after Part G.

**How to read each step.** **Action** → **✓ Pass** → **✗ If it fails**. Confirm exact flag names / output strings against `scripts/install.sh` source if one drifts — this plan names behaviour, the script is canonical.

---

## 0. Preconditions

- [ ] Clean clone of the repo at a known commit, on the branch under test.
- [ ] Hermes ≥ 0.12 on `PATH`; Python 3.11+; `uv`/`uvx` present (for `mcp-obsidian`).
- [ ] No `~/Memoria-test` yet (start from nothing); no `memoria-*` profiles registered (`hermes profile list` empty or pre-recorded), so "newly created" is observable.
- [ ] Headless gate green first (don't debug an install on top of a red repo).

---

## Part A — `install.sh` clean run (S0–S1)

**A0. Missing Python fails with a fix path.** On a disposable Ubuntu/WSL2 image without Python 3, run:
```
bash scripts/install.sh --yes --no-apps --vault ~/Memoria-test
```
- ✓ Pass: the prereq gate stops before profile/runtime work, says Python 3 is required for Memoria's deterministic tools and MCP servers, and prints `sudo apt-get update && sudo apt-get install -y python3 python3-venv`.
- ✗ Fails: a generic "not found" message or a later MCP/profile failure leaves the user without an actionable fix.

**A1. Run the profiles install into a throwaway vault.**
```
bash scripts/install.sh --yes --no-apps --vault ~/Memoria-test
```
- ✓ Pass: exit 0; the run stages each of the 5 profiles and calls `hermes profile install … --force`; closing summary lists 5 deployed.
- ✗ Fails: read the first error; a missing prereq aborts early with the exact package or app to install.

**A2. Vault deployed.** `ls ~/Memoria-test`
- ✓ Pass: the vault skeleton present — `catalog/ notes/ projects/ inbox/ system/ home.md research-focus.md troubleshooting.md .obsidian/ .memoria/`.
- ✗ Fails: wrong `--vault` target, or the copy step (rsync/cp) failed.

**A3. Profiles registered.** `hermes profile list`
- ✓ Pass: all 5 `memoria-{copi,librarian,writer,peer-reviewer,engineer}` listed with an installed path under the Hermes profiles directory (`%LOCALAPPDATA%\hermes\profiles` on Windows, `~/.hermes/profiles` on Linux/WSL2).

---

## Part B — Substitution + secrets (S1–S2)

**B1. `{{VAULT_PATH}}` substituted.** `grep -rn '{{VAULT_PATH}}' ~/.hermes/profiles/memoria-*/` 
- ✓ Pass: **no matches** — every placeholder was replaced with the absolute vault path (the policy MCP launch line in `config.yaml`, hooks). A leftover `{{VAULT_PATH}}` means the deployed gate can't find `policy_mcp.py`.

**B2. `.env` bootstrapped + shared keys seeded.** `cat ~/.hermes/profiles/memoria-librarian/.env`
- ✓ Pass: a `.env` exists (from `.env.EXAMPLE`), and shared keys present in each profile (`seed_profile_env`): `OBSIDIAN_API_KEY`, `KILOCODE_API_KEY`, plus `OPENALEX_API_KEY` for the Librarian.
- ✗ Fails: the shared Hermes env file held the keys but they weren't seeded per-profile — the documented `${OBSIDIAN_API_KEY}`→empty failure ([ADR-27](../../adr/27-hermes-native-config-and-gate-enforcement.md), #39).

**B3. Profile config is valid.** `hermes profile show memoria-librarian`
- ✓ Pass: shows `SOUL.md`, the model block, `mcp_servers` (`policy`, `obsidian`) from `config.yaml`, allowed skills, and `.env` key **names** (values redacted). No parse error.

---

## Part C — Plugins + MCP venv (S2)

**C1. Bundled plugins copied.** `ls ~/Memoria-test/.obsidian/plugins/`
- ✓ Pass: the 12 plugin folders present; secret configs shipped as `data.json.example` (not real `data.json`) for `obsidian-local-rest-api` and `agent-client`.

**C2. MCP venv wired.** `ls ~/Memoria-test/.memoria/.venv` and `grep -n '\.venv' ~/.hermes/profiles/memoria-librarian/config.yaml`
- ✓ Pass: a vault-local venv exists; the profile's `mcp_servers` points its interpreter at it.

---

## Part D — Idempotency (S3)

**D1. Re-run is safe.** `bash scripts/install.sh --yes --no-apps --vault ~/Memoria-test` (second time)
- ✓ Pass: exit 0; **`.env` secrets preserved** (re-read B2 — not clobbered); author-owned files re-staged without error; no duplicate profiles in `hermes profile list`.
- ✗ Fails: a re-run that wipes `.env` or errors on existing files breaks the "safe after `git pull`" guarantee.

---

## Part E — Flags

| # | Run | ✓ Pass |
| --- | --- | --- |
| E1 | `bash scripts/install.sh --profiles-only --vault ~/Memoria-test` | only redeploys profiles (no app/vault bootstrap); `profile show` reflects source changes |
| E2 | `bash scripts/install.sh --only memoria-engineer --vault ~/Memoria-test` | only `memoria-engineer` re-staged; others untouched |
| E3 | `bash scripts/install.sh --dry-run --yes --no-apps --vault ~/Memoria-test` | prints the plan and every command it would run without changing the target |

---

## Part F — Native Windows production bootstrap (S2-S3, Windows)

**F1. `install.ps1` deploys profiles natively.** From PowerShell:
```
.\scripts\install.ps1 -ProfilesOnly -Vault "$env:USERPROFILE\Memoria-test"
```
- ✓ Pass: no WSL invocation; profiles deploy under `$env:LOCALAPPDATA\hermes\profiles`, `config.yaml` contains Windows vault paths, and the policy-gate plugin is present under each deployed profile.

**F2. Full bootstrap (optional, heavy).** The one-line bootstrap installs Obsidian, Hermes, Zotero.
- ✓ Pass: the three apps install; then A–C hold. (Run only on a genuinely disposable Windows box.)

---

## Part G — Teardown

**G1.** `hermes profile remove memoria-*` (the test registrations) and `rm -rf ~/Memoria-test`.
- ✓ Pass: registrations gone; throwaway vault deleted; the real `~/Memoria` never touched.

---

## Results

| Part | Test | Pass / Fail | Notes |
| --- | --- | --- | --- |
| A | clean install: vault deployed, 5 profiles registered | | |
| B | `{{VAULT_PATH}}` substituted; `.env` seeded; config valid | | |
| C | 12 plugins copied; MCP venv wired | | |
| D | re-run idempotent; `.env` preserved | | |
| E | flags (`--profiles-only` / `--only` / `--skip-*`) | | |
| F | native Windows `install.ps1` (+ bootstrap) | | |

**S0-S3 green** when A-E pass on Linux/WSL testing and F1 passes on native Windows production. Record the result in the relevant gate/stage sub-issue under the current release parent issue; preserve run details in that release folder's `validation-log.md` only when a curated summary is worth keeping.
