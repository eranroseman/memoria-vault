---
topic: plans
title: GUI test protocol — v0.1 (T5 + G4)
status: draft
---

# GUI test protocol — v0.1 (Obsidian + Zotero)

Covers the parts of the v0.1 validation that **cannot run headless** from a WSL2
shell: the Obsidian/Zotero GUI tier (**T5**) and the ten Dataview dashboards
rendering on real data (**G4**). Everything else (installer T0–T3, the policy
write-gate in `-z`/gateway/cron) is validated separately.

**Where to run.** On the **Windows** machine, with the vault open in Obsidian and
Hermes installed in WSL2. You'll bounce between Obsidian (GUI) and a WSL2 shell.

**How to read each step.** **Action** → **Expected** → **✓ Pass** (the exact thing
that means it worked) → **✗ If it fails** (first thing to check). Tick the boxes;
fill the results table at the end.

> Dashboard rule of thumb: a dashboard with no data yet shows a **placeholder or
> empty table — that is success** ("empty is success"). A **red "Dataview: query
> error" / "Evaluation Error" is a failure.** G4 is about the queries *resolving*,
> not about rows being present.

---

## 0. Preconditions

- [ ] Installer has run; in WSL2 `hermes profile list` shows the **7** `memoria-*` profiles.
- [ ] Obsidian, Zotero, and **Git for Windows** installed (the `install.ps1` path does this; `obsidian-git` needs the Windows git binary).
- [ ] Keys seeded into each profile `.env` (WSL2): `KILOCODE_API_KEY`, `OBSIDIAN_API_KEY`, `OPENALEX_EMAIL`.
- [ ] **WSL2 mirrored networking** on: `.wslconfig` has `networkingMode=mirrored` (so WSL-Hermes can reach Obsidian's REST API at `127.0.0.1:27124`).
- [ ] Telemetry cron wired (G5) — needed for the board-state dashboard to gain data after activity.
- [ ] The vault folder is **outside OneDrive**.

---

## Part A — Obsidian opens and the 8 bundled plugins load (T5)

**A1. Open the vault.** Obsidian → *Open folder as vault* → select the vault dir.

- ✓ Pass: file tree shows `00-meta/ 10-inbox/ 20-sources/ 30-synthesis/ 40-workbench/ 50-deliverables/ 90-assets/ 95-archive Home README`.
- ✗ Fails: wrong folder (open the dir that contains `.obsidian/` and `.memoria/`).

**A2. Leave Restricted mode.** Settings → *Community plugins* → turn **off** Restricted mode → **restart Obsidian**.

- ✓ Pass: no "Restricted mode" banner; plugins list populated.

**A3. Confirm all 8 required plugins are installed AND enabled** (Settings → Community plugins). Validate each:

| Plugin | Purpose | ✓ Validate it loaded |
| --- | --- | --- |
| `Agent Client` | ACP chat pane to Hermes | an *Agent Client* pane/command exists (Part E1) |
| `Callout Manager` | Defines `[!brief]` `[!suggestions]` `[!verification]` | a note with `> [!brief]` renders as a styled callout |
| `Citations` | Insert citations from `.memoria/library.bib` | *Insert citation* command exists (Part D5) |
| `Dataview` | Powers every dashboard | any dashboard renders a table (Part C) |
| `Local Rest API with MCP` | Exposes the vault to Hermes (HTTPS 27124) — control-plane lifeline | status bar shows **"Local REST API: started"** (Part B) |
| `QuickAdd` | Registers the `Memoria:` command-palette entries | Cmd/Ctrl-P → typing `Memoria:` lists commands |
| `Templater` | Frontmatter scripts (Linter safe-fix) | appears enabled; no load error |
| `obsidian-git` | Git commits from Obsidian; post-commit workflows | *Source Control* / Git commands available |

- ✓ Pass: **8/8 enabled**, no "Failed to load plugin" notices.
- ✗ Fails: a plugin missing → reinstall via `--profiles-only` or copy `.obsidian/plugins/<name>`; a plugin disabled → enable it; load error → check its `data.json` (the two private ones ship as `data.json.example` and must be copied — see A-note).

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

**B2. Key matches.** Settings → Local REST API → copy `apiKey` (64-char hex). In WSL2: `grep OBSIDIAN_API_KEY ~/.hermes/profiles/memoria-librarian/.env`.

- ✓ Pass: the two match.
- ✗ Fails: paste the Obsidian key into the global `~/.hermes/.env`, then re-run `install.sh --profiles-only` to re-seed each profile `.env`.

**B3. Reachable from WSL2.** In WSL2:

```
curl -sk https://127.0.0.1:27124/ -H "Authorization: Bearer $OBSIDIAN_API_KEY"
```

- ✓ Pass: JSON with `"authenticated": true`.
- ✗ Fails: `000`/no response → WSL2 mirrored networking is off (fix `.wslconfig`, `wsl --shutdown`, reopen); `401` → key mismatch (B2).

**B4. Round-trip (write appears live).** In WSL2:

```
hermes -p memoria-librarian -z "Use the obsidian append tool to create 10-inbox/01-fleeting/gui-probe.md with body: gui round-trip. Use only the obsidian tool."
```

- ✓ Pass: within a few seconds, `gui-probe.md` appears in Obsidian's file tree with the body. **Delete it after.**
- ✗ Fails: no file but agent reported success → check the REST bridge (B3) and that Obsidian has the same vault open.

---

## Part C — The ten dashboards render (G4)

Open each file under `00-meta/01-dashboards/` (Reading view). For **every** ```dataview```
block: it must render a table or placeholder, **never a query error**. Tick when
all blocks in the file resolve.

| # | Dashboard file | Reads from | ✓ Validate (and seed if useful) |
| --- | --- | --- | --- |
| 1 | `index.md` (Daily Health) | board-state, lint-findings, fleet metrics, cron-history | all sections render; no query error |
| 2 | `board-state.md` | `00-meta/board/` card projections | sections render; **seed:** create a kanban card + run `hermes cron tick`, then the card shows under *Active* (Part E3) |
| 3 | `reading-pipeline.md` | `20-sources/01-papers/` (`lifecycle`), claims (`maturity`) | resolves; **seed:** a paper note → it appears by lifecycle |
| 4 | `discuss-queue.md` | papers `lifecycle: current`, no Socratic pass | resolves; empty OK |
| 5 | `open-questions.md` | `## Open questions` sections in claims/papers | resolves; add a note with that section → it lists |
| 6 | `contradictions.md` | claim `relations.contradicts` pairs | resolves; empty OK |
| 7 | `drift-watch.md` | `00-meta/02-logs/lint-findings.jsonl` | resolves; populates after a Linter run |
| 8 | `loose-ends.md` | whole-vault filename scan (`TODO`/`tmp`/`untitled`) | resolves; create `untitled.md` → it lists; delete after |
| 9 | `weekly-review.md` | inbox/candidates/synthesis/orphans/projects/metrics | all sections resolve |
| 10 | `fleet-health.md` | `00-meta/08-metrics/lane-metric-*` aggregates | resolves; trust-score band shows when metrics exist |
| 11 | `audit-log.md` | `00-meta/02-logs/audit.jsonl` (current week) | shows the **policy-gate rows** — drive a write in WSL2 (Part E2), the `allow`/`deny` row appears here |

- ✓ Pass (G4): **all dashboards' Dataview blocks resolve with no errors**; seeded items appear where seeded.
- ✗ Fails: "Dataview: query error" → Dataview not enabled or **JS queries off** (Settings → Dataview → *Enable JavaScript queries* = on, several use `dataviewjs`).

---

## Part D — Zotero + Better BibTeX → `library.bib` (T5)

**D1. Add-ons.** Zotero → Tools → Add-ons → install from file: **Better BibTeX** (required); **MarkDB-Connect** (recommended).

**D2. Auto-export.** Right-click a collection → *Export Collection* → format **Better BibLaTeX** → check **Keep updated** → save target =
`...\vault\.memoria\library.bib` (the absolute Windows path to the vault's bib).

**D3. Add an item** with a PDF; confirm Better BibTeX assigns a **citekey**.

**D4. Validate the export.** In Windows PowerShell:
`Get-Item vault\.memoria\library.bib | Select-Object LastWriteTime` (updates), or WSL2: `grep <citekey> vault/.memoria/library.bib`.

- ✓ Pass: `library.bib` updated and contains the entry.

**D5. Citation in Obsidian.** Command palette → *Citation: Insert citation* → your item resolves from `library.bib`.

- ✓ Pass: the citekey/reference is offered and inserts.
- ✗ Fails: citation plugin `citationExportPath` must point at `.memoria/library.bib`, format `biblatex`.

---

## Part E — End-to-end GUI flows

**E1. ACP pane.** Open the *Agent Client* pane → start a session with `memoria-socratic` → ask a question.

- ✓ Pass: a model response renders in the pane (model connectivity through the GUI).

**E2. Write gate visible in the GUI.** In WSL2, drive a **denied** write:

```
hermes -p memoria-librarian -z "Use the obsidian append tool to create 30-synthesis/gui-denied.md. Use only the obsidian tool."
```

Then open `00-meta/01-dashboards/audit-log.md`.

- ✓ Pass: **no `gui-denied.md` is created**, and a `deny` row for it appears in audit-log.

**E3. Board telemetry round-trip.** Create a card (`hermes kanban add …` or via the board), then `hermes cron tick`, then open `board-state.md`.

- ✓ Pass: the card appears under *Active*; `00-meta/board/<task_id>.md` exists.

---

## Results

| Section | Test | Pass / Fail | Notes |
| --- | --- | --- | --- |
| A | 8/8 plugins enabled, no load errors | | |
| B | REST authenticated (B3) + round-trip write appears (B4) | | |
| C / G4 | All 10 dashboards' Dataview blocks resolve | | |
| C | Seeded items appear (board-state, audit-log, loose-ends) | | |
| D | `library.bib` auto-exports; citation resolves | | |
| E1 | ACP pane returns a model response | | |
| E2 | Denied write blocked; deny row in audit-log | | |
| E3 | Board-state shows a card after cron tick | | |

**T5 green** when A, B, D, E pass. **G4 green** when every dashboard's Dataview
query resolves (Part C) and the seeded checks show data. Record the outcome in the
G4/T5 rows of [release-plan-v0.1.md](release-plan-v0.1.md).
