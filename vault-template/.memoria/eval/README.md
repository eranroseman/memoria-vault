# vault-eval — the gold set

This folder holds Memoria's **system-level evaluation fixtures** (ADR-11): a small,
hand-curated gold task per workflow that measures whether the local Memoria engine
finds, extracts, links, and verifies correctly *on this vault*. It is a diagnostic
maintenance capability built from existing machinery, not a benchmark and not a
gate.

## How it runs

- **Dispatch.** Run `memoria eval run --workspace <vault>` to fan each
  `lifecycle: current` gold task into one idempotent local eval task for the
  quarter. Add `--dry-run` to print the task set without writing `last-run.md`.
- **Execution.** Eval-context work is **non-committing**: a run reports results as
  JSON and never mutates the vault directly.
- **Scoring.** Each result report ends with a machine-readable result block. The
  deterministic scorer —
  `python -m memoria_vault.runtime.subsystems.telemetry.eval.eval_score --vault <vault> --from-json results.json`
  — computes recall@k, support-rate, and the FAMA check against vault state,
  appending one line per run to `system/metrics/eval/runs.jsonl`. A task whose
  report has no result block stays **unscored** — never a faked score. The
  `eval-trend` dashboard renders the trend.
- **Verdict.** Diagnostic, never gating. A dip informs the PI; it does not pause
  scheduled work. The dispatch record lands in `last-run.md` here.

## Gold task format

Each task is a diagnostic markdown fixture with `type: eval-task` frontmatter
and three body sections — `## Input`, `## Expected behavior`,
`## Scoring rubric` — so the task is self-contained. `eval-task` is not a
checked Concept type and has no schema under `.memoria/schemas/types/`.
The shipped tasks reference well-known papers (the Transformer, BERT, ResNet,
Adam, Dropout) so they work on any vault after those papers are ingested; the
`references:` field lists the citekeys a task presupposes in the catalog.

When you add vault-specific gold tasks, prefer plain citekeys over wikilinks in
the body unless the target note is permanent — the Linter treats a broken
wikilink here as gold-set rot (a finding, by design).

Full reference: https://eranroseman.github.io/memoria-vault/reference/analysis-and-surfaces/vault-eval
