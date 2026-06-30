<!-- cspell:words SSOT SQLite Crossref OpenAlex Unpaywall DOI ISBN PubMed arXiv CSL BibTeX -->
<!-- cspell:words PydanticAI allowlist frontmatter idempotency Obsidian Hermes Memoria -->

# ExecPlan - alpha.11-13 SSOT and CLI-first implementation

This is a living plan. It must remain self-contained enough for a fresh agent to
continue the work without relying on chat history. Keep tactical progress here;
move durable decisions into ADRs and durable product state into issues.

## 0. Metadata

- Task: Make the alpha.11, alpha.12, and alpha.13 designs the implementation
  source of truth, with CLI-first behavior winning over Hermes-first behavior.
- Plan branch and worktree: `scratch` at `~/mv/scratch`.
- Implementation branch and worktree: `feat/cli-first-ssot` at
  `~/mv/cli-first-ssot`.
- Release/checkpoint: `0.1.0-alpha.13`.
- Started: 2026-06-30 17:10 CDT.
- Owner: agent-assisted implementation for `eranroseman/memoria-vault`.
- Existing related plan:
  `scratch/releases/0.1.0-alpha.13/0.1.0-alpha.13-exec-plan.md`.
  That plan is enrichment-specific; this plan owns the broader CLI-first and
  source-of-truth reset.

## 1. Purpose

The alpha.11-13 designs define the product direction. The implementation and
documentation currently still describe a Hermes-first vault architecture in many
places. This plan lands the smallest coherent pivot:

- `memoria` CLI is the primary operator surface.
- SQLite plus worker queues own catalog and operation state.
- Files remain durable notes, references, projections, templates, and shipped
  vault material, but not the source catalog database.
- Hermes becomes an optional adapter, not the product runtime contract.
- Current docs describe only implemented behavior; forward-looking decisions
  live in ADRs or scratch plans.

The observable outcome is a fresh checkout where a contributor can run
`memoria --help`, capture a DOI into SQLite without creating
`catalog/sources/*/source.md`, enrich it through declared providers, and read
docs that no longer claim Hermes is the primary runtime.

## 2. Context

Terms used in this plan:

- SSOT: the file or store that owns a contract. The repo's
  `.agents/system/source-of-truth-map.md` still governs general contracts, but
  the alpha.11-13 design files govern this pivot until a superseding ADR is
  accepted.
- CLI-first: product flows start from `memoria ...` commands and queue/worker
  state. Obsidian and Hermes can call into those flows, but do not own them.
- Catalog: source identity, source metadata, provider evidence, provenance,
  checked/unchecked state, and enrichment state stored in SQLite.
- Keep-set: user-authored durable notes and references. Keep-set files may link
  to `source_id`, but do not define catalog truth.
- Projection: generated consumer files such as indexes, references, capability
  JSON, or docs mirrors. Projections must be regeneratable from their owner.
- Hermes adapter: optional compatibility integration for environments that
  still run Hermes. It must not be required by the CLI, tests, or installer
  defaults.

Known implementation gaps from current code:

- `src/memoria_vault/runtime/state.py` has SQLite tables for operation and
  catalog work, but still maps sources to `catalog/sources/{source_id}`.
- `src/memoria_vault/runtime/capture.py` still writes
  `catalog/sources/<id>/source.md`, entity Markdown, raw files, and references
  during capture. Alpha.13 requires DOI capture to stage an unchecked database
  record only; enrichment promotes after evidence.
- `src/memoria_vault/runtime/operations.py` still loads source state from
  `catalog/sources/<id>/source.md` and includes Hermes/direct API runner
  assumptions.
- `src/memoria_vault/runtime/worker.py` has an internal argparse entrypoint, but
  the package has no product CLI or console script.
- `pyproject.toml` has no `memoria` console script and no runner dependency
  aligned to alpha.12's CLI-first runner design.
- `vault-template/.memoria/schemas/folders.yaml`,
  `vault-template/.memoria/schemas/types/source.yaml`,
  `person.yaml`, `organization.yaml`, `venue.yaml`, and `mcp.yaml` still model
  source/entity/runtime adapter records as document Concepts.
- `src/memoria_vault/runtime/projections.py` still treats `catalog`,
  `knowledge`, and `capabilities` as bundle roots and emits catalog indexes.
- `docs/README.md`, `docs/reference/hermes-cli.md`, and Hermes-oriented design
  pages still present Hermes as the user-facing runtime.
- Tests still assert source Markdown and Hermes-default behavior.

## 3. Plan Of Work

Work in small PRs. Do not put every change into one branch unless the user
explicitly asks for a single PR.

1. Decision authority PR.
   Create or update ADR coverage so alpha.11-13 are the explicit current
   decision source. Supersede or qualify conflicting Hermes-first ADRs and
   schema ADRs before relying on new behavior. Do not rewrite user docs to
   describe unimplemented behavior in this PR.

2. CLI spine PR.
   Add the `memoria` CLI and console script using the existing standard-library
   `argparse` style. Provide commands for help, capture, enrich, scan,
   run-pending, recover, and basic ask/answer/resume stubs where alpha.12 needs
   a stable command contract. The CLI must run without Hermes, Obsidian, or
   profile environment variables.

3. SQLite catalog PR.
   Move source capture, lookup, digest, references, attention, rollback, and
   worker recovery to SQLite by `source_id`. DOI capture creates an unchecked
   catalog row and provider/work queue state only. It must not create
   `catalog/sources/*/source.md`, source Concept Markdown, entity Concept
   Markdown, or `references.bib`.

4. Enrichment MVP PR.
   Implement the alpha.13 DOI enrichment path with faked provider tests first:
   Crossref, OpenAlex, and Unpaywall; provider allowlist enforcement from
   `vault-template/.memoria/enrichment/providers.yaml`; payload blob caching;
   deterministic merge; field provenance; conflict and retraction handling;
   attention on required provider failure; and idempotent recovery after
   promotion crashes.

5. Projection and schema cleanup PR.
   Remove or demote stale document Concept schemas and folder homes for
   source/person/organization/venue/mcp. Keep generated projections that are
   still required, including `capabilities/ai-catalog.json`. Do not add deferred
   migrations from the alpha.13 design.

6. Documentation and installer PR.
   Update public docs, reference docs, README text, installer references, and
   test guidance to reflect the implemented CLI-first behavior. Keep Hermes docs
   only as optional adapter or historical material. Ensure generated references
   and drift doctors agree with the implementation.

Non-goals for this checkpoint:

- Directory-per-capability manifests.
- `knowledge/_views` migration.
- Universal frontmatter migration.
- ISBN, Semantic Scholar, PubMed, arXiv, full citation graph, embeddings,
  topics, or full-text enrichment.
- Obsidian PI catalog UI beyond queued follow-up wording.
- Any migration of an installed production vault.

## 4. Concrete Steps

Start the implementation branch from a clean worktree:

```bash
cd ~/memoria-vault
git fetch origin
git worktree add ~/mv/cli-first-ssot -b feat/cli-first-ssot origin/main
cd ~/mv/cli-first-ssot
git status --short --branch
```

Expected result: branch `feat/cli-first-ssot` exists, status is clean, and no
edits happen in `~/memoria-vault` or another active worktree.

Recover and pin the design inputs:

```bash
git fetch origin scratch
git show origin/scratch:scratch/releases/0.1.0-alpha.12/0.1.0-alpha.12-design.md > /tmp/alpha12-design.md
git show origin/scratch:scratch/releases/0.1.0-alpha.13/0.1.0-alpha.13-design.md > /tmp/alpha13-design.md
git log --all --name-only -- '*alpha.11-design.md'
```

Expected result: alpha.12 and alpha.13 design files are available locally. Use
the `git log` output to locate the alpha.11 design, then save it as
`/tmp/alpha11-design.md` with `git show <commit>:<path>`.

Run the baseline before editing:

```bash
git diff --check
python -m pytest tests/test_capture.py tests/test_capabilities.py tests/test_projections.py tests/test_schemas.py
bash scripts/test.sh check
```

Expected result: whitespace check passes; focused tests show the current known
baseline. If a baseline test fails before edits, record it in this plan before
changing code.

Decision authority PR:

```bash
python scripts/gen_adr_index.py --help
NEXT_ADR=<next-adr-number>
ADR_FILE="docs/adr/${NEXT_ADR}-cli-first-runtime-and-catalog-ssot.md"
cp docs/adr/_template.md "$ADR_FILE"
python scripts/agents_doctor.py
```

Expected result: a new ADR or explicit ADR updates identify alpha.11-13 as the
current decision source, list the older Hermes-first ADRs that are superseded or
qualified, and name the enforcing mechanisms that will make the boundary real.
Replace `<next-adr-number>` with the next ADR number following the repo's ADR
index rules.

CLI spine PR:

```bash
python -m pytest tests/test_package_spine.py tests/test_worker_queue.py
python -m memoria_vault.cli --help
python -m memoria_vault.cli capture-source --help
python -m memoria_vault.cli enrich-source --help
```

Expected result after implementation: help output lists the stable alpha.12/13
commands, and the commands import without Hermes or Obsidian configuration.
Add a `memoria` console script in `pyproject.toml` and verify it in an isolated
editable install only if the package-spine tests do not already cover it.

SQLite catalog PR:

```bash
python -m pytest tests/test_capture.py tests/test_alpha12_state.py tests/test_worker_queue.py -k "capture or sqlite or source"
python -m memoria_vault.cli capture-source --vault /tmp/memoria-cli-vault --doi 10.0000/example
```

Expected result after implementation: DOI capture creates an unchecked SQLite
catalog row and queue state, does not write `catalog/sources/*/source.md`, does
not write entity Concept Markdown, and does not materialize references.

Enrichment MVP PR:

```bash
python -m pytest tests/test_enrichment.py tests/test_capabilities.py
python -m memoria_vault.cli enrich-source --vault /tmp/memoria-cli-vault --source-id <source_id>
python -m memoria_vault.cli recover --vault /tmp/memoria-cli-vault
```

Expected result after implementation: provider calls are constrained by the
manifest and provider config, payloads are cached under
`.memoria/blobs/provider-payloads/`, checked state is promoted only after
required evidence, failures create attention, and recovery is idempotent.

Projection, schema, docs, and installer PR:

```bash
python scripts/docs_doctor.py docs
python scripts/docs_doctor.py --vault-links
python scripts/status_doctor.py
python scripts/agents_doctor.py
python scripts/ruleset_doctor.py
npx --yes cspell@8.19.4 lint --no-progress --no-must-find-files --gitignore "**/*.md"
npx --yes markdownlint-cli@0.42.0 --config .markdownlint.json 'docs/**/*.md'
python -m pytest tests/test_cspell_scope.py tests/test_ruleset_doctor.py tests/test_schemas.py tests/test_installer_skeleton.py
```

Expected result: docs describe the implemented CLI-first system, generated
references match source contracts, `cspell`, `markdownlint`, and `lint-config`
contract tests pass, and installer tests no longer assume Hermes is mandatory
unless an optional Hermes adapter path is being tested.

Full gate before PR merge:

```bash
git diff --check
bash scripts/test.sh all
bash -n scripts/install.sh scripts/install/*.sh
scripts/verify pr
```

Expected result: all source checks pass and `scripts/verify pr` writes its JSON
evidence bundle.

## 5. Validation And Acceptance

The implementation is complete only when all of these are true:

- `memoria --help` exposes the CLI-first command surface and imports without
  Hermes, Obsidian, or profile environment variables.
- DOI capture creates an unchecked SQLite source record and no source Markdown,
  entity Markdown, or reference projection.
- Enrichment uses declared provider config and allowed network surfaces only.
- Required provider failure leaves the source unchecked and creates an attention
  item.
- Conflict, partial evidence, unverified evidence, and retraction cases do not
  promote a source to checked.
- Provider payloads are cached as blobs and deterministic repeated payloads
  produce deterministic CSL/provenance output.
- Lookup, digest, references, attention, rollback, and recovery work by
  `source_id` without reading `catalog/sources/*/source.md`.
- Keep-set references can link to `source_id` while compact citations fail
  closed when the source is missing or unchecked.
- `regenerate-tracked-projections` still includes
  `capabilities/ai-catalog.json`.
- Public docs no longer present Hermes as the primary runtime.
- `docs/reference/hermes-cli.md` is either removed from current navigation,
  renamed as optional adapter reference, or rewritten so it cannot be mistaken
  for the primary command reference.
- Installer docs and tests no longer install Hermes/profiles by default unless
  the optional adapter is explicitly requested.

## 6. Idempotence And Recovery

- All testing uses disposable vaults such as `/tmp/memoria-cli-vault` or
  `~/Memoria-test`; never use the real runtime vault.
- Provider tests must fake HTTP responses. Live provider calls are not required
  for the merge gate.
- SQLite schema changes should be additive and idempotent in the checkpoint
  code path. There is no production-vault migration target in this checkpoint.
- If a PR branch becomes tangled, preserve uncommitted work with
  `git stash push -u -m cli-first-ssot-wip`, recreate the worktree from
  `origin/main`, and reapply only the relevant paths.
- If promotion crashes after a DB commit and before file materialization,
  `memoria recover` must be able to resume from the DB journal and blob cache.

## 7. Progress

- [x] 2026-06-30 17:10 CDT - Created this scratch ExecPlan as a separate
  CLI-first source-of-truth plan rather than overwriting the existing alpha.13
  enrichment plan.
- [ ] Decision authority PR created.
- [ ] CLI spine PR implemented and verified.
- [ ] SQLite catalog PR implemented and verified.
- [ ] Enrichment MVP PR implemented and verified.
- [ ] Projection/schema cleanup PR implemented and verified.
- [ ] Documentation and installer PR implemented and verified.
- [ ] Final `scripts/verify pr` evidence recorded.

## 8. Execution Log

- 2026-06-30 - The scratch branch already contained alpha.12 and alpha.13
  design/plan material. The existing alpha.13 ExecPlan is enrichment-specific,
  so this broader plan uses a new file:
  `scratch/releases/0.1.0-alpha.13/cli-first-ssot-exec-plan.md`.
- 2026-06-30 - The PR sequence starts with decision authority because the
  current docs and ADRs still contain Hermes-first claims. That avoids making
  user-facing docs describe behavior before code enforces it.
- 2026-06-30 - The implementation sequence starts with a small CLI spine so
  later catalog and enrichment changes have a stable operator surface and test
  entrypoint.

## 9. Surprises

- The codebase already has partial alpha.12 SQLite state tables, but the source
  catalog still leaks through `catalog/sources/<id>/source.md`.
- The package has an internal worker argparse path, but no installed product
  CLI.
- The repo has required `cspell`, `markdownlint`, and `lint-config` workflows,
  but `package.json` only exposes the qmd script. Use the workflow commands
  directly in validation.

## 10. Interfaces And Dependencies

- Keep the first CLI implementation on standard-library `argparse` unless an
  existing package dependency already supplies a better local convention.
- Do not introduce a new event framework for this checkpoint. Reuse the current
  SQLite queue/journal model in `src/memoria_vault/runtime/state.py`.
- Treat PydanticAI as runner scope only. Do not block capture, catalog, or
  enrichment on adopting it.
- Provider configuration is owned by
  `vault-template/.memoria/enrichment/providers.yaml`.
- Capability operation manifests remain flat for the MVP, including
  `capabilities/operations/enrich-source.md`.
- Generated or mirrored docs must name the owning source and be covered by a
  drift check if they repeat machine-readable contracts.

## 11. Artifacts And Notes

- Plan authored on `scratch` in `~/mv/scratch`.
- No implementation tests were run while creating this plan.
- Existing non-scratch worktree changes in `~/mv/docs-gap-analysis` were left
  untouched.

## 12. Outcomes And Retrospective

Fill this section after the implementation PRs merge:

- PRs merged:
- Checks passed:
- Deferred follow-up issues:
- Any ADRs superseded:
- Any production-vault migration still needed:
