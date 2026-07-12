# design-history/archive — manifest

Primary-source working material from the pre-`main` history of Memoria,
preserved for the record. This is the **raw derivation** behind the curated
`design-history/NN-*.md` records: release working docs, per-version execution
logs, research corpora, and rejected explorations.

## What this is (and isn't)

The curated `design-history/00-origins.md … 20-alpha.20.md` records are the
**authoritative, compiled history** — they were authored *from* the files here.
This archive is the **appendix**: it holds the detail (evidence ledgers,
full ADR text, research findings, spike data) that the summaries distilled.

**It is deliberately incomplete.** It was pruned from a 290-file snapshot to
the ~148 files whose content is *not already fully represented on `main`*. The
full 290-file snapshot lives in the git tag **`archive/scratch-final`**
(commit `91066154`) — the complete backstop if anything dropped is ever needed.

## How it was classified

Twelve subagents read every file and compared it against all of `origin/main`
(the curated `design-history/` records, `docs/superpowers/**`, published
`docs/`). Each file got one verdict:

- **DUPLICATE** — substantially the same text is already on `main`.
- **PARAPHRASED** — the *decisions/concepts* are captured on `main` (summarized
  in a curated record), but the file's *detail* is not.
- **UNIQUE** — the substance appears **nowhere** on `main`, not even summarized.
- **UNIQUE-DATA** — binary/measurement fixture with no prose counterpart.

## Summary of the source snapshot (290 files)

| verdict | ~count | disposition |
|---|---|---|
| DUPLICATE | ~20 | dropped (fully on `main`) |
| PARAPHRASED | ~170 | mostly dropped; kept where the file *is* the research cluster |
| UNIQUE (prose) | ~81 | **kept** |
| UNIQUE-DATA | ~17 | **kept** |

Kept here: **148 files**. The rest are recoverable from `archive/scratch-final`.

---

## KEPT — genuinely irreplaceable content

### `releases/0.1.0-beta.1/` (53 files) — the beta.1 research + adjudication layer
The single largest pocket of unique content. `main`'s beta.1 work **restarted
from the alpha.20 code baseline**, so this entire evidentiary/adjudication layer
was never carried forward. Highlights (all UNIQUE unless noted):
- `resources/0.1.0-beta.1-information-flow-research.md` (210 findings)
- `resources/0.1.0-beta.1-research-evidence.md` (97 findings, 7 streams)
- `resources/0.1.0-beta.1-paper-adversarial-review.md` (401-paper pass) + `-paper-borrow-adapt-reject.md`
- `resources/0.1.0-beta.1-design-alternatives.md`, `-evaluation-protocol.md`,
  `-coherent-slice-research.md`, `-information-flow-design.md`,
  `-docs-history-borrow-adapt-reject.md`, `-alpha-regression-review.md`
- `resources/gap-analysis/` — the `S01–S16` gap adjudications + `owner-rulings-2026-07-05.md`
  + `gap-adjudication.md` (1,680 lines); only terminal conclusions of ~5 threads
  survive on `main` as bullets in `docs/superpowers/specs/2026-07-12-beta.1-consolidation.md`
- A few files here are PARAPHRASED against `docs/superpowers/specs/` (e.g. the
  `resources/0.1.0-beta.1-design.md`/`-requirements.md` predecessors) — kept to
  keep the research body intact and self-contained.

### `sources/prealpha-docs-design/` (27 files) — early explorations / roads not taken
21 PARAPHRASED (condensed into `01-alpha.1-baseline.md`) + 6 UNIQUE kept whole:
- `publication-strategy.md` (four-path comparison behind ADR-20)
- `graph-visualization.md` (full viz architecture, G1–G5)
- `ai-research-systems-survey.md`, `memory-systems-and-benchmarks.md` (evidence
  appendices behind several ADRs' empirical claims)
- `classical-methods-over-llm.md`, `adjacent-tool-integrations.md` (rejected directions)

### `sources/notes/` + `sources/build/` + misc (~26 files) — raw data, exports, fact-check trail
- `notes/paper-review-verdicts.json` (401-entry raw verdicts) + `notes/bibliography.bib`
- `notes/docs-exports/*.md` (~38.8k lines — the **only surviving copy** of the
  retired `docs/adr/` subsystem and the pre-reorg docs site)
- `notes/ai-research-systems-survey.md`, `notes/publication-path-report.md`,
  `notes/project-starter.md`, `notes/REVIEW-*.md`, `notes/clean-slate-*.md`
- `verification-findings.md` + `corrections-to-apply.md` (the fact-check evidence
  behind the curated history's accuracy)
- `build/assemble*.py` (the scripts that compiled the curated records)
- `old-skeleton/OLD-SKELETON-pre-alpha.1.md` (pre-alpha.1 snapshot)

### `releases/0.1.0-alpha.12/` (18 files) — spike scripts + fixtures
`exec-plan.md`, `alpha12_test_harness.py` (615 lines), `preimpl_spikes/run_spikes.py`
(846 lines), and 12 `.db`/`.jsonl`/`.md` UNIQUE-DATA fixtures. `main` narrates the
spike *conclusions* only.

### `releases/0.1.0-alpha.15/adr/` + `dogfood/` (12 files)
- `adr/125`–`130` + `adr-disposition-map.md` — the **sole surviving full text** of
  the ADRs `15-alpha.15.md` compresses into one summary section.
- `dogfood/*.json` + export — raw empirical measurement data.

### Scattered alpha UNIQUE (10 files)
- `sources/versions/0.1.0-alpha.7/tmp__ui-architecture-{design,future}.md` (deferred projector/Canvas engine design)
- `sources/versions/0.1.0-alpha.8/tmp__{alpha7-docs-audit-report,deferred-adr-implementability-alpha6,refactor-no-compat-exec-plan}.md`
- `sources/versions/0.1.0-alpha.10/tmp__{current-state-baseline,hermes-017-feature-eval-codex,hermes-017-feature-eval}.md` + `validation-log.md`
- `releases/0.1.0-alpha.13/0.1.0-alpha.13-release-plan.md`, `releases/0.1.0-alpha.16/0.1.0-alpha.16-exec-plan.md`

---

## DROPPED (recoverable from `archive/scratch-final`)

All fully represented on `main`; the *decisions* live in the curated records.

| area | files | verdict | why safe to drop |
|---|---|---|---|
| `workflow-audit/` dossier | 8 | DUPLICATE | byte-identical to main commit `1705c79e`; folded into `docs/superpowers/specs/2026-07-12-beta.1-consolidation.md` (never entered this archive) |
| `memoria-design-history-alpha.1-to-alpha.15.md` | 1 | DUPLICATE | ~98% verbatim in the numbered `01`–`15` records |
| `sources/versions/alpha.1–6` | 27 | DUP/PARAPHRASED | curated `01`–`06` records authored from them (verbatim quotes, matching SHAs) |
| `sources/versions/alpha.9, alpha.11` | 29 | PARAPHRASED | decisions in `09`/`11-alpha.*.md`; only exec/validation detail here |
| `sources/versions/alpha.7/8/10` (non-unique) | ~18 | DUP/PARAPHRASED | READMEs, dashboards drafts, hermes eval reconciliations — decisions in `07`/`08`/`10` |
| `releases/alpha.13/14/16/17/20` (non-unique) | ~14 | DUP/PARAPHRASED | design/exec/requirements summarized in `13`–`20` records |
| `releases/alpha.15` top-level | 5 | PARAPHRASED | design/exec/release-plan + paper reviews summarized in `15-alpha.15.md` (ADR full text kept) |

Total dropped from the 242-file working copy: **94**.
