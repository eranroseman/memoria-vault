# 0.1.0-alpha.11 design assumption verification results

Date: 2026-06-28

Scope: `docs/releasing/0.1.0-alpha.11/tmp/0.1.0-alpha.11-design.md`.

This is a local verification pass over the design assumptions previously flagged
from the alpha.11 reset design. The pass tested only what is testable from this
worktree and the installed local tools. Live Obsidian/Zotero/Local REST API checks,
external OKF tooling, model calls, and Hermes workflow runs were not fabricated;
they are marked blocked where they are required.

## Evidence status update

Later same-day disposable spikes supersede the `not-implemented-local` /
`failed-local` rows below only as feasibility evidence. They do not mean
production alpha.11 code exists; the rows remain implementation gaps until a
production check says otherwise. The later scope correction also removes
migration, upgrade, and backwards-compatibility work from alpha.11 because no
non-sandbox install exists.

## Commands run

| Command | Result |
| --- | --- |
| `scripts/test.sh all` | Failed: 545 pytest tests passed, 1 failed. L0 also failed at `scripts/agents_doctor.py`. Failure: `.agents/system/docs-manifest.yaml` is stale and needs `scripts/agents_doctor.py --write`. This is unrelated to the alpha.11 design assumptions and was not changed. |
| `env PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 python3 -m pytest tests/test_cluster_mcp.py tests/test_policy_gate_completeness.py tests/test_eval_score.py tests/test_qmd_filter_mcp.py tests/test_memoria_inspector.py tests/test_ingest_mcp.py tests/test_ingest_paper.py tests/test_project_structural_impact.py -q` | Passed: 63 tests. Covers current policy hard-deny, read-only inspector contract, ingest pieces, graph/canvas staging allowlist, supersession filtering, eval scoring, and current project structural impact. |
| `find . -path './.git' -prune -o -iname '*okf*' -print` | Only `docs/adr/107-okf-interchange-bundle-format.md` found. No OKF serializer/importer implementation in this worktree. |
| `find . -path './.git' -prune -o -path '*ai-catalog*' -print` | No `ai-catalog` files found. |
| `find src -path '*staging*' -o -path '*quarantine*' -o -path '*capabilities*' -o -path '*journal*'` | No alpha.11 staging/quarantine/capabilities/journal paths found in shipped `src/`. |
| `find /home/eranr/Memoria-test -maxdepth 3 -path '*staging*' -o -path '*quarantine*' -o -path '*capabilities*' -o -path '*journal*'` | No matching runtime paths found in the test vault. |
| `hermes --version` | Hermes Agent v0.17.0 is installed. |
| `qmd --version` | qmd 2.5.3 is installed. |
| `qmd search "rollback"` | Failed: local project qmd store/index is not usable here (`SQLITE_CANTOPEN` / sqlite-vec probe failure). |
| `pgrep -a obsidian` | No Obsidian process running, so live Local REST API/native MCP behavior was not tested. |

## Status legend

- `verified-local`: tested and passed for the current implementation.
- `partial-local`: existing tests/mechanisms cover a narrower older form, not the
  alpha.11 reset claim.
- `not-implemented-local`: no local implementation found to test.
- `failed-local`: the local implementation contradicts the alpha.11 assumption.
- `blocked-live`: requires live runtime, external tool, model, or source corpus.
- `open-design`: design/acceptance ambiguity, not a runtime behavior.
- `superseded-scope`: the assumption was removed from alpha.11 scope.

## Findings

| # | Assumption tested | Status | Evidence and reasoning | Next verification |
| --- | --- | --- | --- | --- |
| 1 | Three nested OKF-compatible bundles can round-trip as the storage/export substrate. | not-implemented-local | The only OKF file found is proposed ADR-107. ADR-107 itself says future OKF serializers belong under `vault-template/.memoria/operations/`; none exist. No local OKF fixture or validator is present. | Build a minimal `catalog/`, `knowledge/`, `capabilities/` fixture and run it through real OKF import/export validation. |
| 2 | `.memoria/staging/` plus `.memoria/quarantine/` enforces the read barrier. | failed-local | Neither `vault-template/` nor `/home/eranr/Memoria-test` contains alpha.11 staging/quarantine paths. Current `vault-template/.memoria/schemas/folders.yaml` has review-gated prefixes only for `notes/claims/` and `notes/hubs/`. | Implement staging/promote/quarantine first, then run a negative test proving consumers cannot read unchecked/staged/quarantined content. |
| 3 | Trusted writer commits Concept file plus derivation event atomically. | not-implemented-local | No alpha.11 journal path, derivation-event shape, trusted writer, or coupled commit implementation found. Existing ingest tests cover intake anchors and Tier-0 frontmatter, not derivation commits. | Add a derivation journal fixture and test agent write, PI edit backfill, foreign commit quarantine, and concurrent edit behavior. |
| 4 | Cascade rollback can revert derived outputs per Concept and flag human-directed descendants. | not-implemented-local | No rollback DAG/inverse-commit implementation found. Existing golden-restore tests are system-file restore, not provenance cascade rollback. | Seed a derivation DAG and test machine-only revert, human-directed halt, blast-radius flagging, and traced inverse commit events. |
| 5 | Gateless integrity is safe if trace/check/rollback recall meets a seeded-error bar. | blocked-live | Current tests include eval scoring and linter pieces, but no seeded-error gold set, batch runner, recall threshold, or rollback-completeness measurement exists for this reset design. | Create the seeded-error corpus and run structural, injection, unwarranted-claim, stale-as-current, and rollback-completeness cases against the built alpha.11 loop. |
| 6 | The structural-check suite is feasible. | partial-local | Current source gate and targeted tests prove existing checks for policy, lint pieces, supersession filtering, eval scoring, and project structural impact. They do not cover alpha.11 span entailment, NLI, counterfactual faithfulness, trace integrity, or read-barrier checks. | Prototype each proposed alpha.11 check in shadow mode with thresholds and false-positive accounting. |
| 7 | The wiki compiler can update 5-15 digest/hub nodes per source with acceptable quality. | blocked-live | Hermes v0.17.0 is installed and Hermes docs list `llm-wiki`, but no alpha.11 `digest` type, wiki SCHEMA, wiki compiler integration, or fixture was found in this repo. | Run the Hermes `llm-wiki` / candidate compiler on a small source set and measure traceability, unsupported claims, duplication, and edit burden. |
| 8 | `digest`, `note`, and `hub` replace current note-family types cleanly. | failed-local | Current schema still has separate `claim`, `source`, `fleeting`, and `hub` types under `vault-template/.memoria/schemas/types/`; there is no alpha.11 unified `note` or `digest` schema. | Decide and implement the schema reset, then run schema/docs drift tests against the new type map. |
| 9 | Gap analysis over both catalog and knowledge mismatch is actionable. | partial-local | `tests/test_project_structural_impact.py` passed through the targeted pytest run and covers current project argument graph saturation/gap behavior. It does not inspect catalog-vs-knowledge mismatch, corpus floor, or source-dense/note-thin states from the design. | Add fixtures for source-thin, note-thin, balanced, saturated, and stale states across catalog plus knowledge. |
| 10 | Ask retrieval design beats cheap baselines. | partial-local | qmd is installed, and qmd supersession filtering tests passed. The project qmd index is not usable locally (`qmd search` failed), and no benchmark compared BM25, hybrid union, query expansion, LLM rerank, and long-context whole-read. | Repair/build the qmd index and run retrieval benchmarks with recall@k, support correctness, latency, and cost. |
| 11 | The Obsidian plugin surface can carry Co-PI conversation, trace rollback, flags, and graph browsing. | failed-local | The shipped Memoria plugin is `memoria-inspector`, whose manifest describes a read-only operational inspector. Its tests assert no writes, no fetch, and no command execution. This is narrower than the alpha.11 Co-PI plugin claim. | Build a plugin spike for Co-PI pane, flags, trace-to-rollback, project/gap views, and knowledge graph browsing. |
| 12 | Local REST API/native MCP plus Zotero Local API support the new capture path. | partial-local | ADR-31 documents an accepted Local REST API native MCP path and prior live validation, but no Obsidian process was running for a fresh smoke. Current Zotero backbone is Better BibTeX / `.memoria/memoria.bib`; ADR-05 does not implement alpha.11's Zotero Local API importer assumption. | Start Obsidian on `Memoria-test`, run native MCP read/write smoke, then test Zotero Local API annotation/source import. |
| 13 | `capabilities/` and generated `ai-catalog.json` can be trusted as a supply-chain surface. | not-implemented-local | No `capabilities` path or `ai-catalog` file found in source or runtime test vault. | Add minimal capability Concepts and a generated trust manifest; test signed/unsigned import and no execution of untrusted capabilities. |
| 14 | Clean rebuild migration can preserve the current record while regenerating machine layers. | superseded-scope | The later scope correction states there is no alpha.11 system installed outside the sandbox, so alpha.11 needs fresh initialization only: no migrator, upgrade path, backwards compatibility, or data-preservation checklist. | Remove migration from the ExecPlan and design SSOT; initialize only the sandbox skeleton and seed data through the alpha.11 pipeline. |
| 15 | Git-only, single-user, multi-device operation is safe enough for alpha. | blocked-live | Current repo has git and runtime vault exists, but no two-device/offline divergence simulation was run. No alpha.11 per-machine journal partition exists to test. | Simulate two clones/devices, conflicting edits, foreign commits, pull/merge convergence, and journal partition behavior. |
| 16 | Proposed library/tool choices fit the reset design. | partial-local | Current tests cover existing use of NetworkX graph behavior, eval scoring, ingest parsing, and policy tooling. They do not verify alpha.11 choices such as Pydantic schema emission, PyMuPDF4LLM/PDF++ span preservation, Pandoc/CSL, RapidFuzz dedupe, or SQLite-vec fallback. qmd currently fails without a usable DB/index. | Run one microspike per proposed dependency and record pass/fail ceilings. |
| 17 | Stable `source_id` with citekey as generated alias works. | failed-local | Current ingest and docs still center `citekey`; tests verify citekey frontmatter and path behavior. No `source_id` field/path model was found for alpha.11. | Implement source identity fixtures for retitle, citekey change, source rename, and cross-bundle reference resolution. |
| 18 | Writing/export are deferred, but the functional loop still names draft/verify/export. | open-design | The design status says writing/coding modules are deferred, while the functional loop and mechanism sections still name draft/verify/export behavior. This is an acceptance ambiguity, not a command-testable behavior. | Update the design or release acceptance criteria so alpha.11 either excludes writing/export or ships explicit stubs only. |
| 19 | This file's lifecycle/source-of-truth claim is accurate. | failed-local | The copied file now lives in tracked release `tmp/`, but line 4 still says it is a working architecture note in `_notes/`. | Update the note's status line if this tracked copy is the active release design scratch. |
| 20 | The alpha.11 milestone can ship the full basic knowledge cycle plus plugin as one increment. | open-design | No alpha.11 release plan, task breakdown, dependency DAG, or implementation evidence was found beyond this tmp design note. The current tree is pre-reset and lacks several load-bearing mechanisms above. | Create an alpha.11 implementation plan that sequences schema reset, writer/journal, read barrier, plugin, wiki spike, eval harness, and fresh sandbox initialization. |

## Bottom line

No load-bearing alpha.11 reset assumption is fully verified yet. The current repo
does have useful older mechanisms that pass targeted tests, but the reset design's
central claims--OKF-native bundle tree, trusted writer + derivation journal, read
barrier, cascade rollback, seeded-error verdict, capability bundle, source_id
model, and Co-PI plugin--are either unimplemented locally or require live/runtime
spikes before they can be treated as facts.
