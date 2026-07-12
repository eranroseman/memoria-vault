# design-history/archive — manifest

Primary-source **research and design explorations** from the pre-`main` history
of Memoria, preserved for the record. This is the raw material behind the
curated `design-history/NN-*.md` records — the research corpora, gap
adjudications, and early explorations that the summaries distilled from.

## What this is (and isn't)

The curated `design-history/00-origins.md … 20-alpha.20.md` records are the
**authoritative, compiled history** — authored *from* this material. This archive
is the **appendix**: the detail (research findings, adjudication reasoning,
rejected explorations) that the summaries condense.

It holds **research and explorations only**. Release-engineering process
artifacts (exec-plans, release-plans, validation logs, spike scripts, test
fixtures, dogfood data) and per-version working docs whose decisions already
live in the curated records were **deliberately pruned** — see "What's not here."

**Full backstop:** the complete 290-file pre-`main` snapshot lives in the git
tag **`scratch-final`** (on `origin`) — the recovery point for anything pruned.

## How it was classified

Twelve subagents read every file of the `scratch-final` snapshot and compared it
against all of `origin/main` (curated `design-history/`, `docs/superpowers/**`,
published `docs/`), verdicts DUPLICATE / PARAPHRASED / UNIQUE / UNIQUE-DATA. This
archive keeps the UNIQUE research material; a second pass then pruned the
release-engineering and redundant artifacts below.

---

## What's here (97 files)

### `0.1.0-beta.1/` (53) — the beta.1 research + adjudication layer
The largest pocket of unique content. `main`'s beta.1 work **restarted from the
alpha.20 code baseline**, so this evidentiary/adjudication layer was never carried
forward. Highlights:
- `resources/0.1.0-beta.1-information-flow-research.md` (210 findings),
  `-research-evidence.md` (97 findings, 7 streams),
  `-paper-adversarial-review.md` (401-paper pass) + `-paper-borrow-adapt-reject.md`
- `-design-alternatives.md`, `-evaluation-protocol.md`, `-coherent-slice-research.md`,
  `-information-flow-design.md`, `-docs-history-borrow-adapt-reject.md`,
  `-alpha-regression-review.md`
- `resources/gap-analysis/` — the `S01–S16` adjudications + `owner-rulings-2026-07-05.md`
  + `gap-adjudication.md` (1,680 lines); only terminal conclusions of a few threads
  survive on `main` in `docs/superpowers/specs/2026-07-12-beta.1-consolidation.md`

### `prealpha-docs-design/` (27) — early explorations / roads not taken
21 PARAPHRASED into `01-alpha.1-baseline.md` + 6 UNIQUE. Notable: `publication-strategy.md`
(four-path publication map behind ADR-20) and `graph-visualization.md` (typed-projection
view layer) — both now summarized in [`arcs.md` → "Roads worked out and set aside"](../arcs.md).

### `notes/` + misc (~14) — research, design reasoning, fact-check trail
- `notes/paper-review-verdicts.json` (401-entry raw verdicts) + `notes/bibliography.bib` — the literature-review data
- `notes/docs-exports/adr-full.md` — the consolidated ADR reference the curated `arcs.md` cites for the ADR-consolidation arc
- `notes/REVIEW-SUMMARY.md` + `notes/REVIEW-REFUTATIONS.md`, `notes/ai-research-systems-survey.md`,
  `notes/publication-path-report.md` — the 401-paper review findings that drove the design
- `notes/clean-slate-design.md`, `notes/clean-slate-application-design.md`,
  `notes/0.1.0-alpha.11-design.md` — the reasoning behind the alpha.11 reset;
  `notes/project-starter.md` (deferred Project gate)
- `verification-findings.md` + `corrections-to-apply.md` + `researcher-notes.md`
  (fact-check evidence + the researcher's own round-by-round notes)

### alpha.7 UI design exploration (2)
`0.1.0-alpha.7/tmp__ui-architecture-design.md` (1,123-line clean-slate
UI architecture) and `tmp__ui-architecture-future.md` (the deferred projector/Canvas
engine) — first-principles design not carried into the record.

---

## What's NOT here (recoverable from `scratch-final`, and where noted, git history)

| removed | why |
|---|---|
| **workflow-audit dossier** (8) | byte-identical to main commit `1705c79e`; folded into `docs/superpowers/specs/2026-07-12-beta.1-consolidation.md` |
| **alpha.1–20 per-version working docs** (design/exec/requirements) | curated `01`–`20` records were authored from them; decisions preserved there |
| **alpha.15 ADRs 125–130** | **redundant** — full text is in git history at `docs/adr/125-*.md … 130-*.md` (`git log --all -- 'docs/adr/12*'`); the record's §11 summarizes the consolidation |
| **release-plans + exec-plans** (alpha.12/13/16 …) | release-engineering process; no lasting design-history value |
| **alpha.12 spike scripts + fixtures, alpha.15 dogfood** | ephemeral test data + disposable spike code; conclusions are in `12`/`15-alpha.*.md` |
| **alpha.8/10 version working files** (exec-plan, ADR/docs audits, Hermes eval drafts, validation log, baseline) | process/audit/superseded artifacts; decisions in `08`/`10-alpha.*.md` |
| **build scripts + old compiled-history front-matter** | dead one-off assembly glue (session-specific inputs gone); `part-0-front.md`'s Method note folded into `../README.md` |
| **notes/docs-exports/{docs-full,docs-merged}** (~28k lines) | **redundant** — snapshots of the old `docs/` tree, which is in git history (`git log --all -- 'docs/**'`); uncited (`adr-full.md` kept — `arcs.md` cites it) |
| **notes operational scratch** (TODO, TODO-archive, check-docs, prompts, Communities, repos) | personal task lists, docs-review prompt tooling, and outreach notes — not design history |

The complete 290-file snapshot (everything above) is in the `scratch-final` tag.
