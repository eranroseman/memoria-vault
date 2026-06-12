# vault-eval — the gold set

This folder holds Memoria's **system-level evaluation fixtures** (ADR-11): a small,
hand-curated gold task per workflow that measures whether the *deployed system* —
the real profiles on the real board — finds, extracts, links, and verifies correctly
*on this vault*. It is a diagnostic maintenance capability built from existing
machinery, not a benchmark and not a gate.

## How it runs

- **Dispatch.** A quarterly cron (`memoria-eval`, wired by the installer) runs
  `.memoria/engines/sweeps/eval_dispatch.py`, which fans each `lifecycle: current`
  gold task out as one Hermes kanban card on the lane its frontmatter names
  (`catalog`/`extract`/`link`/`map` → the Librarian, `draft` → the Writer,
  `verify` → the Peer-reviewer, `code` → the Engineer). Cards carry an
  idempotency key per (task, quarter), so re-runs within a quarter dedup on the
  board. Run it on demand with
  `python .memoria/engines/sweeps/eval_dispatch.py --vault <vault>` (add
  `--dry-run` to print the card set without creating it).
- **Execution.** Eval-context work is **non-committing**: the card body instructs
  the lane to write only to scratch and report results back on the card — a run
  never mutates the vault.
- **Scoring.** Each card ends its report with a machine-readable result block
  (the card body shows the exact JSON template). The deterministic scorer —
  `python .memoria/engines/sweeps/eval_score.py --vault <vault>` — reads those
  blocks off the board (`hermes kanban list --json`) and computes recall@k,
  support-rate, and the FAMA check against vault state, appending one line per
  run to `system/metrics/eval/runs.jsonl`. A task whose card reported no result
  block stays **unscored** — never a faked score. The quarterly cron scores the
  *previous* quarter before dispatching the new one; the `eval-trend` dashboard
  renders the trend.
- **Verdict.** Diagnostic, never gating. A dip informs the PI; it does not pause
  scheduled work. The dispatch record lands in `last-run.md` here.

## Gold task format

Each task is a markdown note with `type: eval-task` frontmatter (schema:
`.memoria/schemas/types/eval-task.yaml`) and three body sections — `## Input`,
`## Expected behavior`, `## Scoring rubric` — so the task is self-contained.
The shipped tasks reference well-known papers (the Transformer, BERT, ResNet,
Adam, Dropout) so they work on any vault after those papers are ingested; the
`references:` field lists the citekeys a task presupposes in the catalog.

When you add vault-specific gold tasks, prefer plain citekeys over wikilinks in
the body unless the target note is permanent — the Linter treats a broken
wikilink here as gold-set rot (a finding, by design).

Full reference: https://eranroseman.github.io/memoria-vault/reference/vault-eval
