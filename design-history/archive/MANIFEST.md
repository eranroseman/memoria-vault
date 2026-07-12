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

## What's here (116 files)

### `releases/0.1.0-beta.1/` (53) — the beta.1 research + adjudication layer
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

### `sources/prealpha-docs-design/` (27) — early explorations / roads not taken
21 PARAPHRASED into `01-alpha.1-baseline.md` + 6 UNIQUE. Notable: `publication-strategy.md`
(four-path publication map behind ADR-20) and `graph-visualization.md` (typed-projection
view layer) — both now summarized in [`arcs.md` → "Roads worked out and set aside"](../arcs.md).

### `sources/notes/` + build + misc (~28) — raw data, exports, fact-check trail
- `notes/paper-review-verdicts.json` (401-entry raw verdicts) + `notes/bibliography.bib`
- `notes/docs-exports/*.md` (~38.8k lines — the only surviving copy of the retired
  `docs/adr/` subsystem and the pre-reorg docs site)
- `notes/ai-research-systems-survey.md`, `notes/publication-path-report.md`, `notes/REVIEW-*.md`
- `verification-findings.md` + `corrections-to-apply.md` (fact-check evidence behind the
  curated history's accuracy); `build/assemble*.py` (the scripts that compiled the records)

### Scattered alpha UNIQUE design docs (9)
`sources/versions/0.1.0-alpha.7/tmp__ui-architecture-{design,future}.md` (deferred
projector/Canvas engine); `.../alpha.8/tmp__{alpha7-docs-audit-report,deferred-adr-implementability-alpha6,refactor-no-compat-exec-plan}.md`;
`.../alpha.10/tmp__{current-state-baseline,hermes-017-feature-eval-codex,hermes-017-feature-eval}.md` + `validation-log.md`.

---

## What's NOT here (recoverable from `scratch-final`, and where noted, git history)

| removed | why |
|---|---|
| **workflow-audit dossier** (8) | byte-identical to main commit `1705c79e`; folded into `docs/superpowers/specs/2026-07-12-beta.1-consolidation.md` |
| **alpha.1–20 per-version working docs** (design/exec/requirements) | curated `01`–`20` records were authored from them; decisions preserved there |
| **alpha.15 ADRs 125–130** | **redundant** — full text is in git history at `docs/adr/125-*.md … 130-*.md` (`git log --all -- 'docs/adr/12*'`); the record's §11 summarizes the consolidation |
| **release-plans + exec-plans** (alpha.12/13/16 …) | release-engineering process; no lasting design-history value |
| **alpha.12 spike scripts + fixtures, alpha.15 dogfood** | ephemeral test data + disposable spike code; conclusions are in `12`/`15-alpha.*.md` |

The complete 290-file snapshot (everything above) is in the `scratch-final` tag.
