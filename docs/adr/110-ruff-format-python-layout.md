---
topic: decisions
id: 110
title: Ruff format owns Python layout (line-length 100)
status: accepted
date_proposed: 2026-06-20
date_resolved: 2026-06-20
assumes: []
supersedes: []
superseded_by: []
parent: Decisions
grand_parent: Explanation
nav_order: 110
nav_exclude: true
---

# ADR-110: Ruff format owns Python layout (line-length 100)

## Context

Ruff has been the Python linter for repo tooling and runtime code, but `ruff format`
was deliberately **not** used. The recorded rationale was that the codebase was
hand-formatted — "aligned comment columns, deliberate line breaks" — and that
reformatting would churn ~2k lines for no behavioral gain, with "many lines
intentionally long" cited as the reason E501 stayed disabled.

Two facts undercut that rationale once examined against the actual code:

- **All Python here is generated and maintained by agents**, across many independent
  sessions. There is no human artisan whose deliberate layout would be churned. What
  looked like intentional style is per-session entropy: collections, for example, were
  a ~43/57 split between compact multi-item rows (721) and one-item-per-line (936),
  and ~112 of 148 files lacked the conventional blank line after the module docstring.
  There was no coherent house style to protect.
- **The codebase is not wide.** Of 21,109 lines, ~96% fit within 88 columns; only 50
  exceed 120, and those are long string literals (argparse help, prompt and
  error text) that a formatter cannot break and leaves untouched. "We write wide code on purpose" did
  not describe the real situation — a handful of long *strings* did.

With an all-agent contributor model, any consistent style — even a hand-curated one —
is unmaintainable without a formatter, because every new session re-injects its own
defaults. A formatter is the only mechanism that holds a style steady against that
drift, and it removes a whole class of whitespace-only diffs and merge conflicts
between concurrent agent sessions.

## Decision

Adopt `ruff format` as the single source of truth for Python layout in `memoria/`,
`scripts/`, `src/.memoria/`, `.github/scripts/`, and `tests/`, at **line-length 100**.

Enforcement mirrors the existing `ruff check` wiring: a `ruff-format` pre-commit hook,
a `ruff format --check` step in the CI `lint` job, and the same in `scripts/test.sh`
L0. E501 stays disabled — the formatter owns width, and the only remaining over-100
lines are string literals it cannot break, so E501 would only add noise.

Line-length 100 is chosen from the distribution, not convention: it leaves the
comfortable 88–100 one-liners agents already produce intact, wraps only the longer
expressions that genuinely benefit, and roughly halves the one-time reformat churn
versus the 88 default. The bulk reformat is isolated in a single commit listed in
`.git-blame-ignore-revs` so `git blame` continues to attribute lines to their real
authors.

## Consequences

- Python layout is now deterministic and consistent across all agent sessions;
  formatting leaves every contributor's decision space.
- Whitespace-only diffs and the merge conflicts they cause between concurrent
  worktrees largely disappear.
- One-time churn: 112 files reformatted (+4215/−1865), behavior unchanged (433 tests
  pass, `ruff check` clean). The churn is mostly collection layout, driven by the
  trailing commas the codebase already uses, not by line-length.
- The dense compact-collection style is lost in a few places — `ruff format` explodes
  trailing-comma collections one-item-per-line. This is accepted as the cost of
  consistency; it is also more diff-friendly.
- A first `git blame` pass over reformatted lines requires the ignore-revs file (GitHub
  honors it automatically; locally `git config blame.ignoreRevsFile .git-blame-ignore-revs`).

## When this matters

Revisit the line-length choice only if the over-100 string-literal tail grows enough
that wrapping policy becomes a real readability problem, or if a future contributor
model (human-authored modules) reintroduces a deliberate style worth preserving
differently. Neither is the case today.

## Alternatives considered

**Keep Ruff linter-only (status quo before this ADR).** Rejected: it preserved
inconsistency, not craft — the measured 43/57 layout split is what "trust the agents
to be consistent" produces, and it drifts further every session.

**Line-length 88 (Black/Ruff default).** Rejected: it forces ~768 comfortable
88–100 one-liners to wrap for no readability gain and produces the most churn; its
only benefit is matching the ecosystem default.

**Line-length 120.** Rejected as the steady-state width: so permissive it rarely
engages (only ~1.2% of lines exceed 100), so it fails to enforce a sane width on
future sprawling expressions. It minimizes churn but at the cost of doing little.

## Related

- Implemented in [PR #790](https://github.com/eranroseman/memoria-vault/pull/790).
