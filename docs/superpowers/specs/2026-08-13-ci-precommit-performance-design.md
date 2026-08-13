# Verification performance design

**Status:** draft for owner review
**Related:** #1823, #1827, #1828

## Problem

Memoria's verification remains intentionally comprehensive, but its current
workflow repeats setup that only one shard consumes. A post-merge run spends
roughly three minutes wall time, with the runtime job on the critical path. All
four matrix jobs currently install Node dependencies, Bubblewrap,
PSScriptAnalyzer, and restore pre-commit environments even when their selected
gate cannot use them. Docs-only pull requests also provision contract and
runtime jobs that select no work, while the lint shard still runs non-prose
manual hooks across the whole tree.

The local `python scripts/verify` command is similarly conservative: its
shards are correct and balanced, but users must invoke them serially.

## Goals

- Reduce CI wall time and runner time without narrowing the normal verification
  contract.
- Keep docs-only pull requests conservative, fail closed, and visibly covered
  by prose checks plus static tests.
- Preserve one authoritative formatter/linter scope for CSpell and every
  existing required GitHub check.
- Offer an opt-in faster local full verification path without concurrent
  worktree writes or uncontrolled CPU oversubscription.
- Measure before making lower-value pre-commit changes.

## Non-goals

- Do not remove tests, merge test shards, weaken the post-merge run, or replace
  the required `verify` fan-in check.
- Do not merge the Verify and Gitleaks caches. They remain deliberately
  separate after a prior shared-cache race caused costly reinstallations.
- Do not make `pre-commit` commit-stage hooks less protective. Ruff formatting
  and Oxfmt formatting serve different staged-index and whole-tree boundaries.
- Do not duplicate `cspell.json` exclusions in `.pre-commit-config.yaml` merely
  to avoid handing CSpell already-ignored Markdown files.

## Decisions

### Make CI setup shard-aware

Retain the four existing verification shards and their tested marker roster.
Every shard still receives Python and the project dependencies it needs, but
workflow setup becomes conditional on the selected work:

| Resource | Shard(s) that install or restore it | Reason |
| --- | --- | --- |
| Pre-commit cache and `pre-commit gc` | `lint` | Only the lint shard invokes manual hooks. |
| PSScriptAnalyzer cache/install | `lint` when the scope says PowerShell changed; every `main` push | Preserve the existing fast path without weakening post-merge validation. |
| Node runtime | `lint`, `contract` | Lint runs Node-backed hooks; contract builds/checks the Obsidian package. |
| npm download cache | `contract` | Only the package install consumes the adapter lockfile cache. |
| `npm ci --prefix packages/memoria-obsidian` | `contract` | Only package-contract tests require adapter dependencies. |
| Bubblewrap and its host probe | `runtime` | Only runtime/e2e tests exercise the code sandbox. |

The Python dependency cache key must include both `requirements-dev.txt` and
`pyproject.toml`, because editable installation derives runtime and MCP
dependencies from project metadata. Node's download cache must key from
`packages/memoria-obsidian/package-lock.json`.

Setup conditions derive from the declared matrix shard, except for the existing
PowerShell fast path. The scope job emits `ps1=true` by default, changes it to
`false` only after a complete pull-request diff proves no current or former path
ends in `.ps1`, and the lint job alone consumes it. Thus every `main` push still
installs and runs PSScriptAnalyzer. A skipped step must never be relied upon by
another shard; the roster tests remain the source of truth for which shard owns
each gate.

### Select a smaller docs-only matrix before jobs start

Replace each matrix job's duplicate pull-request scope inspection with a small
`scope` job. Before it queries GitHub, it emits syntactically valid defaults:
the complete four-shard JSON matrix, `ps1=true`, and `docs_only=false`. It
replaces those defaults only after complete, validated pull-request data. The
verification job consumes the matrix:

- A verified docs-only pull request runs `lint` and `sweep`.
- Every other pull request and every push to `main` runs `lint`, `contract`,
  `runtime`, and `sweep`.

The classifier remains fail closed. It must consider both names of a renamed
file, require a complete API result whose record count agrees with the pull
request's declared changed-file count, and choose the full matrix on API
failure, incomplete pagination, a 3,000-file boundary, malformed output, or an
empty result. It must continue to classify PowerShell changes separately from
docs-only changes.

The `verify` fan-in depends on both `scope` and the selected matrix shards, uses
`if: always()`, and fails unless both jobs succeeded. If the scope job or its
matrix output is unavailable, shard jobs may be skipped, but the required
fan-in must become decisively red rather than silently skipped or green.

### Run only prose-relevant manual hooks for verified docs-only scope

When CI sets the existing `VERIFY_DOCS_ONLY=1` mode and `scripts/verify` reaches
its lint gate, run these existing manual hooks individually over all files:

- `vale`
- `markdownlint-structural`
- `mermaid-parse`
- `cspell`

Do not invoke the whole manual hook stage in this mode. Normal lint and every
non-docs-only run retain the current whole-stage command, including Ruff, MyPy,
YAML, shell, Oxfmt, and Oxc checks. This is safe only because the workflow's
conservative classifier already upgrades a mixed or uncertain change to the
full matrix.

Tests must pin the exact docs-only hook roster and prove that no code-oriented
manual hook is silently retained or removed.

### Add CI-only duration telemetry before further test splitting

Expose slow-test information only in CI, using pytest's duration reporting with
a modest threshold (for example, 25 entries at 0.25 seconds). Feed it through
an explicit verifier environment variable so local output and contract stay
unchanged. Publish the output in the job log or step summary.

The existing contract, runtime, and sweep test work is already balanced enough
that adding a fifth shard before collecting this evidence would repeat setup
cost more readily than it improves wall time.

### Add a separate, opt-in local parallel verifier

After the CI changes are established, add `python scripts/verify --parallel`.
It is intentionally a two-phase coordinator:

1. Run the lint shard alone, because formatters may write the worktree.
2. If lint succeeds, run `contract`, `runtime`, and `sweep` concurrently.

The coordinator must set explicit worker limits for each child so their combined
pytest workers do not exceed the detected CPU budget. It captures each child
output in a temporary log, waits for all children rather than failing fast,
then replays labeled output and fails if any shard failed. It leaves the
existing e2e/vault serialization boundary intact.

The coordinator is not itself a shard: it must parse `--parallel` before the
ordinary vault-lock selection and must not acquire that lock. It launches
children with `--shard`, leaving the existing runtime child as the sole owner of
the lock around the vault-mutating gate. `--parallel` and `--shard` are mutually
exclusive, and unsupported argument combinations fail explicitly.
`VERIFY_DOCS_ONLY` remains CI-only; the local parallel mode does not introduce a
`--docs-only` flag. The existing sequential command is unchanged and remains
the simplest debugging path. This is a separate implementation slice because it
changes local process orchestration, not CI topology.

### Treat CSpell as a measured experiment, not an immediate configuration edit

Benchmark CSpell with its current single-source scope before proposing a change.
The experiment may land only if it avoids a second hand-maintained exclusion
list, demonstrably improves warm manual-hook time, and retains a regression
test for the scope authority. Otherwise record the result and keep the current
configuration.

## Verification design

Before each implementation slice, capture the current CI and local baseline.
The implementation plan must add or update tests that prove:

1. The scope job emits a valid full matrix before inspection, produces the
   two-shard matrix only for complete docs-only data, and falls back to the full
   matrix for rename, pagination, hostile filename, count-mismatch, API-failure,
   missing output, and 3,000-file cases. The fan-in fails if either scope or
   shards is not successful.
2. Each setup step's condition matches the matrix ownership table; Python cache
   dependencies include both project metadata sources; and the npm cache uses
   the adapter lockfile.
3. `VERIFY_DOCS_ONLY=1` runs precisely the prose-hook roster, while the normal
   lint shard still runs the full manual-hook stage.
4. The shard union remains exactly the complete test roster and every selected
   matrix shard reaches the `verify` fan-in.
5. `--parallel` first completes lint, honors its aggregate worker budget,
   propagates every child failure, gives the runtime child (not the coordinator)
   the vault lock, and leaves sequential verification unchanged.

Run focused workflow/verifier tests, then `python scripts/verify`. Exercise
the changed workflow on a pull request and compare at least three green runs
with the recorded baseline. Treat cache misses separately from warm runs.

## Acceptance criteria

- A normal pull request and a `main` push execute the same full verification
  coverage as today.
- A clearly docs-only pull request executes lint and sweep only, while uncertain
  scope always executes all four shards.
- Runtime no longer pays for PSScriptAnalyzer or pre-commit setup, and no shard
  installs unrelated Node or Bubblewrap dependencies.
- Docs-only lint retains all four prose checks and skips only code-oriented
  manual hooks.
- CI logs provide actionable slow-test evidence before any additional shard is
  proposed.
- The opt-in local parallel mode has no concurrent formatter writes and never
  oversubscribes its configured CPU budget.
- CSpell's authoritative scope remains singular unless measurement supports a
  non-duplicating alternative.

## Rollout order

1. Implement and verify the CI topology, shard-aware setup, and docs-only hook
   roster as one workflow/verifier slice.
2. Collect duration telemetry from several green runs and decide whether a
   test-level optimization is warranted.
3. Implement the local parallel coordinator as an independent slice with its
   own failure-propagation tests and benchmark.
4. Complete or close the CSpell experiment based on measured benefit.
