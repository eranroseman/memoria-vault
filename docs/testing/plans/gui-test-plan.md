---
topic: plans
title: GUI test plan — v0.1 (S5 + G4)
status: draft
parent: Test plans
grand_parent: Testing
nav_order: 15
---

# GUI test plan — v0.1 (Obsidian + Zotero)

Covers the parts of the v0.1 validation that **cannot run headless** from a WSL2
shell: the Obsidian/Zotero GUI stage (**S5**) and the eleven Dataview dashboards
rendering on real data (**G4**). Everything else (installer S0–S3, the policy
write-gate in `-z`/gateway/cron) is validated separately.

**Where to run.** On the **Windows** machine, with the vault open in Obsidian and
Hermes installed in WSL2. You'll bounce between Obsidian (GUI) and a WSL2 shell.

**How to read each step.** **Action** → **Expected** → **✓ Pass** (the exact thing
that means it worked) → **✗ If it fails** (first thing to check).

**Marking results.** Tick each test's `- [ ] Pass` box when it passes. If it fails,
**leave it unticked** and record the symptom in the [Results](#results) table at the
end (the boxes are clickable in Obsidian).

> Dashboard rule of thumb: a dashboard with no data yet shows a **placeholder or
> empty table — that is success** ("empty is success"). A **red "Dataview: query
> error" / "Evaluation Error" is a failure.** G4 is about the queries *resolving*,
> not about rows being present.

---

## 0. Preconditions

- [ ] Installer has run; in WSL2 `hermes profile list` shows the **5** `memoria-*` profiles.
- [ ] Obsidian, Zotero, and **Git for Windows** installed (the `install.ps1` path does this; `obsidian-git` needs the Windows git binary).
- [ ] Keys seeded into each profile `.env` (WSL2): `KILOCODE_API_KEY`, `OBSIDIAN_API_KEY`, `OPENALEX_API_KEY` (Librarian; OpenAlex requires a key since 2026-02).
- [ ] **WSL2 mirrored networking** on: `.wslconfig` has `networkingMode=mirrored` (so WSL-Hermes can reach Obsidian's REST API at `127.0.0.1:27124`).
- [ ] Telemetry cron wired (G5) — needed for the board-state dashboard to gain data after activity.
- [ ] The vault folder is **outside OneDrive**.

---

## Part A — Obsidian opens and the 8 bundled plugins load (S5)

**A1. Open the vault.** Obsidian → *Open folder as vault* → select the vault dir.

- ✓ Pass: file tree shows `catalog/ notes/ projects/ inbox/ system/ home.md README`.
- ✗ Fails: wrong folder (open the dir that contains `.obsidian/` and `.memoria/`).
- [ V] **A1 Pass**

**A2. Leave Restricted mode.** Settings → *Community plugins* → turn **off** Restricted mode → **restart Obsidian**.

- ✓ Pass: no "Restricted mode" banner; plugins list populated.
- [V ] **A2 Pass**

**A3. Confirm all 8 required plugins are installed AND enabled** (Settings → Community plugins). Validate each:

| Plugin | Purpose | ✓ Validate it loaded |
| --- | --- | --- |
| `Agent Client` | ACP chat pane to Hermes | an *Agent Client* pane/command exists (Part E1) |
| `Callout Manager` | Defines `[!brief]` `[!suggestions]` `[!verification]` | a note with `> [!brief]` renders as a styled callout |
| `Citations` | Insert citations from `.memoria/memoria.bib` | *Insert Markdown citation* command exists (Part D5) |
| `Dataview` | Powers every dashboard | any dashboard renders a table (Part C) |
| `Git` | Git commits from Obsidian; post-commit workflows | *Source Control* shows the repo. **The vault must be a git repo** — run `git init` (+ first commit) if Source Control is empty; the installer does **not** auto-init (the vault is your repo). An un-init'd vault is not a plugin failure |
| `Local REST API with MCP` | Exposes the vault to Hermes (HTTPS 27124) — control-plane lifeline | status bar shows **"Local REST API: started"** (Part B) |
| `QuickAdd` | Registers the `Memoria:` command-palette entries | Cmd/Ctrl-P → typing `Memoria:` lists commands |
| `Templater` | Frontmatter scripts (Linter safe-fix) | appears enabled; no load error |

- ✓ Pass: **8/8 enabled**, no "Failed to load plugin" notices.
- ✗ Fails: a plugin missing → reinstall via `--profiles-only` or copy `.obsidian/plugins/<name>`; a plugin disabled → enable it; load error → check its `data.json` (the two private ones ship as `data.json.example` and must be copied — see A-note).

Tick each plugin that is enabled and validated:

- [ ] `Agent Client`
- [ ] `Callout Manager`
- [ ] `Citations`
- [ ] `Dataview`
- [ ] `Git`
- [ ] `Local REST API with MCP`
- [ ] `QuickAdd`
- [ ] `Templater`
- [V ] **A3 Pass (8/8)**

> **A-note (private configs).** `obsidian-local-rest-api/data.json` and
> `agent-client/data.json` are gitignored and ship as `data.json.example`. On a
> fresh vault: `obsidian-local-rest-api` **regenerates its own** (apiKey + TLS) on
> first launch, and the installer **seeds `agent-client/data.json`** from its example
> (set the agent command path inside it). Separately, **`obsidian-git` needs Git for
> Windows** — `install.ps1` installs it via winget; if *Source Control* shows "git
> not found", install Git and restart Obsidian.

---

## Part B — Local REST API bridge (the write-gate's lifeline)

**B1. Plugin running.** ✓ Pass: status bar shows **"Local REST API: started"**; Settings → Local REST API shows HTTPS on **27124**, loopback only, insecure HTTP **off**.

- [ V] **B1 Pass**

**B2. Key matches.** Settings → Local REST API → copy `apiKey` (64-char hex). In WSL2: `grep OBSIDIAN_API_KEY ~/.hermes/profiles/memoria-librarian/.env`.

- ✓ Pass: the two match.
- ✗ Fails: paste the Obsidian key into the global `~/.hermes/.env`, then re-run `install.sh --profiles-only` to re-seed each profile `.env`.
- [V ] **B2 Pass**

**B3. Reachable from WSL2.** A fresh WSL2 shell has no `$OBSIDIAN_API_KEY` — **export it first** (from the profile `.env`), then call:

```
export OBSIDIAN_API_KEY="$(grep -m1 '^OBSIDIAN_API_KEY=' ~/.hermes/profiles/memoria-librarian/.env | cut -d= -f2-)"
curl -sk https://127.0.0.1:27124/ -H "Authorization: Bearer $OBSIDIAN_API_KEY"
```

- ✓ Pass: JSON with `"authenticated": true`.
- ✗ Fails: `200` + `"authenticated": false` → the bearer token was empty/wrong; run the `export` above (a fresh shell has no `$OBSIDIAN_API_KEY`). If it persists, the key genuinely mismatches the Obsidian plugin's `apiKey` (B2). `000`/no response → WSL2 mirrored networking is off (fix `.wslconfig`, `wsl --shutdown`, reopen).
- [ V] **B3 Pass**

**B4. Round-trip (write appears live).** In WSL2:

```
hermes -p memoria-librarian -z "Use the obsidian append tool to create notes/fleeting/gui-probe.md with body: gui round-trip. Use only the obsidian tool."
```

- ✓ Pass: within a few seconds, `gui-probe.md` appears in Obsidian's file tree with the body. **Delete it after.**
- ✗ Fails: no file but agent reported success → check the REST bridge (B3) and that Obsidian has the same vault open.
- [ V] **B4 Pass**

---

## Part C — The ten dashboards render (G4)

Open each file under `system/dashboards/` (Reading view). For **every** ```dataview```
block: it must render a table or placeholder, **never a query error**. (The former
*Daily Health* dashboard is now the glance at the top of `home.md`, validated with the
Home page — it is not a standalone dashboard file.)

| # | Dashboard file | Reads from | ✓ Validate (and seed if useful) |
| --- | --- | --- | --- |
| 1 | `board-state.md` | `system/board/` card projections | sections render; **seed:** create a kanban card + run `hermes cron tick`, then the card shows under *Active* (Part E3) |
| 2 | `reading-pipeline.md` | `catalog/papers/` (`lifecycle: proposed`), claims (`maturity`) | resolves; **seed:** a paper note → it appears by lifecycle |
| 3 | `discuss-queue.md` | sources `lifecycle: provisional` | resolves; empty OK |
| 4 | `open-questions.md` | claims with zero inbound links (`notes/claims/`) | resolves; add an unconnected claim → it lists |
| 5 | `contradictions.md` | note `links.contradicts` pairs | resolves; empty OK |
| 6 | `drift-watch.md` | `system/logs/lint-findings.jsonl` | resolves; populates after a Linter engine run |
| 7 | `loose-ends.md` | `notice`-loudness `flag` cards (`lifecycle: proposed`) | resolves; create a notice flag card → it lists |
| 8 | `weekly-review.md` | inbox/candidates/synthesis/orphans/projects/metrics | all sections resolve |
| 9 | `fleet-health.md` | `system/metrics/lane-metric-*` aggregates | resolves; trust-score band shows when metrics exist |
| 10 | `audit-log.md` | `system/logs/audit.jsonl` (current week) | shows the **policy-gate rows** — drive a write in WSL2 (Part E2), the `allow`/`deny` row appears here |

- ✗ Fails: "Dataview: query error" → Dataview not enabled or **JS queries off** (Settings → Dataview → *Enable JavaScript queries* = on, several use `dataviewjs`).

Tick each dashboard whose Dataview blocks all resolve (no query errors):

- [ ] 1 · `board-state.md`
- [ ] 2 · `reading-pipeline.md`
- [ ] 3 · `discuss-queue.md`
- [ ] 4 · `open-questions.md`
- [ ] 5 · `contradictions.md`
- [ ] 6 · `drift-watch.md`
- [ ] 7 · `loose-ends.md`
- [ ] 8 · `weekly-review.md`
- [ ] 9 · `fleet-health.md`
- [ ] 10 · `audit-log.md`
- [ ] **Part C / G4 Pass (all 10 resolve)**

---

## Part D — Zotero + Better BibTeX → `memoria.bib` (S5)

**D1. Add-ons.** Zotero → Tools → Add-ons → install from file: **Better BibTeX** (required); **MarkDB-Connect** (recommended).

- [ V] **D1 Pass**

**D2. Auto-export.** Right-click a collection → *Export Collection* → format **Better BibLaTeX** → check **Keep updated** → save target =
`...\vault\.memoria\memoria.bib` (the absolute Windows path to the vault's bib).

- [ V] **D2 Pass**

**D3. Add an item** with a PDF; confirm Better BibTeX assigns a **citekey**.

- [ ] **D3 Pass**

**D4. Validate the export.** In Windows PowerShell:
`Get-Item vault\.memoria\memoria.bib | Select-Object LastWriteTime` (updates), or WSL2: `grep <citekey> vault/.memoria/memoria.bib`.

- ✓ Pass: `memoria.bib` updated and contains the entry.
- [ ] **D4 Pass**

**D5. Citation in Obsidian.** Command palette → *Citations: Insert Markdown citation* → your item resolves from `memoria.bib`. (If the picker is empty, run *Citations: Refresh citation database* first.)

- ✓ Pass: the citekey/reference is offered and inserts.
- ✗ Fails: citation plugin `citationExportPath` must point at `.memoria/memoria.bib`, format `biblatex`.
- [ ] **D5 Pass**

---

## Part E — End-to-end GUI flows

**E1. ACP pane.** Open the *Agent Client* pane → start a session with `memoria-copi` → ask a question.

- ✓ Pass: a model response renders in the pane (model connectivity through the GUI).
- [ ] **E1 Pass**

**E2. Write gate visible in the GUI.** In WSL2, drive a **denied** write:

```
hermes -p memoria-librarian -z "Use the obsidian append tool to create notes/claims/gui-denied.md. Use only the obsidian tool."
```

Then open `system/dashboards/audit-log.md`.

- ✓ Pass: **no `gui-denied.md` is created**, and a `deny` row for it appears in audit-log.
- [ ] **E2 Pass**

**E3. Board telemetry round-trip.** Create a card (`hermes kanban create …` or via the board), then `hermes cron tick`, then open `board-state.md`.

- ✓ Pass: the card appears under *Active*; `system/board/<task_id>.md` exists.
- [ ] **E3 Pass**

---

## Results

| Section | Test | Pass / Fail | Notes |
| --- | --- | --- | --- |
| A | 8/8 plugins enabled, no load errors |Pass |I didn't verified the settings |
| B | REST authenticated (B3) + round-trip write appears (B4) | | |
| C / G4 | All 10 dashboards' Dataview blocks resolve | | |
| C | Seeded items appear (board-state, audit-log, loose-ends) | | |
| D | `memoria.bib` auto-exports; citation resolves | | |
| E1 | ACP pane returns a model response | | |
| E2 | Denied write blocked; deny row in audit-log | | |
| E3 | Board-state shows a card after cron tick | | |

**S5 green** when A, B, D, E pass. **G4 green** when every dashboard's Dataview
query resolves (Part C) and the seeded checks show data. Record the outcome in the
G4/S5 rows of [Release plan — v0.1.0-alpha.1](../../releasing/0.1.0/release-plan-0.1.0.md).
