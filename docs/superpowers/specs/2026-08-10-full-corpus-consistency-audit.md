# Full-corpus consistency audit — 2026-08-10

**Status:** findings reported, none applied. No file outside this report was
changed. Every finding below awaits an owner ruling; the question round has not
yet been answered.

**Commit audited:** `e9d74cf51ee2400290850d233c98f676d0760875` (clean tree).

**Method.** Two independent `consistency-audit-inspector` readers each read all
228 in-scope files in full — one slice, no size splitting, so no cross-cutting
comparison was left unmade. Their 83 raw candidates reconciled to 62 distinct
defects. Each of the 62 went to its own skeptic, instructed to refute and to
default to `refuted` where the evidence did not clearly hold; no candidate was
judged by the reader that raised it. Four third-party claims needed upstream
pages the read-only inspectors cannot fetch; those were fetched by the auditor
and handed to the relevant skeptics as evidence.

**Result: 42 confirmed, 20 refuted, 0 unsettled.**

| State | Count |
| --- | --- |
| `ready-for-agent` | 28 |
| `ready-for-human` | 14 |
| `wontfix` | 0 |

| Severity | Count |
| --- | --- |
| `high` | 5 |
| `medium` | 21 |
| `low` | 16 |

---

## HIGH

### H1. The seeded vocabulary note tells the researcher to write frontmatter that validation rejects

- **Where:** `src/memoria_vault/product/workspace_seed/system/vocabulary.md:28`
- **Quote:** "Reference taxonomies (MeSH, ACM CCS, OpenAlex fields-of-study) are **not** here — they live in each note's `_enrichment` namespace for browsing, not querying."
- **Contradiction:** `docs/reference/data-model/frontmatter.md:47` — "Validation is closed: fields a type schema does not declare are rejected. The `x:` map is the escape hatch for extension data". `note.yaml` declares no `_enrichment`; `runtime/vocabulary/schema.py:246-252` rejects undeclared fields and names `x:` in the error. Repo-wide, `_enrichment` occurs exactly once in shipped surfaces: this sentence.
- **Verdict:** `confirmed`. The seed file ships into every vault (`cli.py:59`), so every researcher reads it; a note authored per the instruction fails at the pre-commit hook. The line predates the closed-schema regime and survived the seed retirement. The published counterpart `docs/reference/data-model/vocabulary.md` already dropped the sentence — only the seed drifted.
- **State:** `ready-for-agent` — *repair*
- **Severity:** `high`

### H2. The FAMA detector and the eval scorer key on frontmatter fields the schema can never admit

- **Where:** `docs/reference/analysis-and-surfaces/linter.md:37`
- **Quote:** "| `fama-exposure` | HIGH | A downstream note wikilinking a superseded note (`status: superseded` or `superseded_by` set) — reuse of obsolete memory. |"
- **Contradiction:** `src/memoria_vault/product/workspace_seed/.memoria/schemas/types/note.yaml:36` declares only `superseded: bool`; no type schema declares `status` or `superseded_by`, and validation is closed. `docs/reference/data-model/okf-compliance.md:46` independently calls `status` a "deliberate omission". Shipped code reads the phantom fields anyway: `runtime/sweeps/linter/detectors.py:345-348` and `runtime/eval/eval_score.py:91-94`.
- **Verdict:** `confirmed`, and it reveals a defect in shipped code rather than only in prose. A schema-valid superseded note is invisible to a HIGH-severity detector; any note that does trigger it is simultaneously a `schema-check` "undeclared field" finding, so `linter.md` contradicts itself between line 28 and line 37. The keys are ADR-10 vocabulary that the rest of the system moved off. Four published pages repeat them, including an instruction to the researcher at `docs/how-to-guides/operate/run-a-retraction-sweep.md:51`.
- **State:** `ready-for-human` — the repair is a design choice between three incompatible fixes (declare the fields, retarget the detectors onto `superseded: bool` plus catalog standing, or retire the detector). See Q2.
- **Severity:** `high`

### H3. A setup step instructs an action the shipped plugin makes impossible

- **Where:** `docs/how-to-guides/setup/set-up-obsidian.md:28`
- **Quote:** "4. Open the Memoria plugin settings and enter the local HTTP server URL/token only when you want adapter actions or empirical event recording."
- **Contradiction:** `src/memoria_vault/product/workspace_seed/.obsidian/plugins/memoria-obsidian/main.js:1147-1184` renders exactly four settings — Enable collection, Engine command, Default project ID, Retention days. No URL field, no token field. The plugin obtains its coordinates from `memoria handshake --spawn` and holds them in memory. A committed test forbids the documented fields: `packages/memoria-obsidian/scripts/test.mjs:581-583` asserts `!("serverUrl" in plugin.settings)` and `!("hasToken" in plugin.settings)`.
- **Verdict:** `confirmed`. The fields existed and were removed by `bfbc4312` (2026-08-01); the doc line dates from `cf6fcdae` (2026-07-08). The truthful equivalent action is the Enable collection toggle plus, on WSL2, Engine command.
- **State:** `ready-for-agent` — *repair*
- **Severity:** `high`

### H4. A how-to runs a `src/` script from a vault root that has no `src/`

- **Where:** `docs/how-to-guides/operate/inspect-session-logs.md:63` (and the prose reference at `:59`)
- **Quote:** "python3 src/memoria_vault/runtime/sweeps/linter/session_summary.py --vault ."
- **Contradiction:** the same page's prerequisite at `:16` is "Run from the vault root so the relative paths resolve", and `memoria init` seeds no `src/` (`cli.py:47-66`). `docs/reference/analysis-and-surfaces/linter.md:85` gives the deployed form: `<vault>/.memoria/.venv/bin/python -m memoria_vault.runtime.sweeps.linter.session_summary`. Every sibling guide uses that form; this is the only `python3 src/` in all of `docs/how-to-guides/`.
- **Verdict:** `confirmed`, and neither audience is served: steps 1-6 `jq` files under `system/logs/`, which no repo checkout has, while step 7 needs a `src/` no vault has.
- **State:** `ready-for-agent` — *repair*
- **Severity:** `high`

### H5. The Zotero guide's two verification steps both fail for a reader who followed its own instructions

- **Where:** `docs/how-to-guides/setup/set-up-zotero.md:55` and `:60`
- **Quote (`:55`):** "confirm the lock icon is shown in Zotero and that the item's Extra field contains `bibtex: <citekey>`"
- **Contradiction (`:60`):** "The key is pinned (shown with a lock icon in Zotero's item list, and `extra: bibtex: mamykina2010sense` in the item's Extra field)." Both sentences are anchored to "the item's Extra field" and give different literal contents. Upstream (fetched by the auditor): Better BibTeX's "Pin Citation Key" — the action steps 4-5 instruct — writes `Citation Key: <key>`. The legacy `bibtex: <key>` form is honoured only when typed manually, which this page never instructs. `extra: bibtex: …` is a form upstream documents nowhere.
- **Verdict:** `confirmed`, and wider than an internal inconsistency: a reader who performs steps 4-5 and then either verification step sees a correctly pinned key and a non-matching Extra field. No code reads a citekey out of an Extra field, so `:60` is not a rendering of a parsed record — `runtime/capture.py:545-560` takes the citekey from the BibTeX entry header.
- **State:** `ready-for-agent` — *repair*
- **Severity:** `high`

---

## MEDIUM

### M1. The seed ships `system/templates/session-diary.md`; the layout reference documents it nowhere

- **Where:** `docs/reference/system/on-disk-layout.md` — the vault tree (`:41-46`) and the Packaged Seed Inventory (`:140-166`)
- **Quote:** `:10` — "Where every file lives."
- **Contradiction:** the file ships (`cli.py:65` `SEED_FILES`, `pyproject.toml:55` package-data) and is pinned by `tests/test_installer_skeleton.py:75` and `tests/test_cli.py:1583`. No inventory row and no tree line mentions `system/templates/`, and the page carries no non-exhaustiveness disclaimer.
- **Verdict:** `confirmed`, **narrowed**. The reader also charged the page's "**Unshipped:** dashboards, note templates, …" callout (`:132-134`) with denying the file. That half is **refuted**: "note templates" names the retired `.memoria/templates` payload class, and `tests/test_installer_skeleton.py:82-102` asserts exactly that absence. Only the omission survives.
- **State:** `ready-for-agent` — *repair*
- **Severity:** `medium`

### M2. `concept-types.yaml` is required by the frontmatter contract and missing from the seed inventory

- **Where:** `docs/reference/system/on-disk-layout.md:156-157` and the `.memoria/` tree at `:62-66`
- **Quote:** `docs/reference/data-model/frontmatter.md:16` — "the required Concept-type registry in `…/.memoria/schemas/concept-types.yaml`. Each type schema must name a registry member; a schema directory without that registry is invalid."
- **Contradiction:** the inventory lists `folders.yaml` and `types/*.yaml` per-file but never the registry. `runtime/vocabulary/schema.py:77-79` fails closed without it. It ships via `SEED_TREES`.
- **Verdict:** `confirmed`. Same class as M1; `schema_doc_drift` explicitly scopes itself out of the registry, and `doc_cited_paths` only proves the path exists.
- **State:** `ready-for-agent` — *repair*
- **Severity:** `medium`

### M3. The Obsidian adapter Settings roster names two settings that do not exist and omits the one that does

- **Where:** `docs/reference/evidence-and-integrations/integrations.md:103`
- **Quote:** "| Settings | Enable collection, server URL, bearer token in Obsidian SecretStorage, default project ID, retention days. |"
- **Contradiction:** the table's own column heading is "Current behavior"; `main.js:1141-1185` renders four settings, none of them a URL or a token, and adds `Engine command`, which the row omits. `tests/test_memoria_obsidian_package.py:186-189` asserts `"settings.serverUrl" not in source` and `"secretStorage" not in source`. The same page at `:91` says the token is kept "in memory only (never written to plugin settings)".
- **Verdict:** `confirmed`. The row is the verbatim pre-handshake roster; `:91` was rewritten for the 2026-08-02 rework and `:103` was not.
- **State:** `ready-for-agent` — *repair*
- **Severity:** `medium`

### M4. A second page claims SecretStorage token storage the adapter does not implement

- **Where:** `docs/reference/control-and-policy/empirical-events.md:115`
- **Quote:** "The shipped Obsidian proof adapter stores its bearer token with Obsidian SecretStorage, spools only validated event payloads while offline"
- **Contradiction:** `SecretStorage` appears in zero files under the seeded plugin. The token is parsed per boot (`handshake.js:32`) into `this.engine` and used at `main.js:494`. `tests/test_memoria_obsidian_package.py:188-189` forbids the documented behaviour outright.
- **Verdict:** `confirmed`. The contradiction with `integrations.md:91` turns on "in memory only", not on the parenthetical — SecretStorage and plugin settings are genuinely different stores, so anyone rewording this should cite the right clause.
- **State:** `ready-for-agent` — *repair*
- **Severity:** `medium`

### M5. The adapter's documented HTTP reads omit four live routes and misspell one

- **Where:** `docs/reference/evidence-and-integrations/integrations.md:104`
- **Quote:** "| Reads | `GET /status`, `GET /attention`, and `GET /concept?target=<path>` through the local HTTP transport. |"
- **Contradiction:** the plugin reads `/v1/status` (`main.js:41`), `/v1/views/attention`, `/v1/views/evidence-review`, and `/project/canvas/forks`. The transport dispatches `/attention` and `/v1/views/attention` as independent routes (`runtime/http_transport.py:339,351`), so there is no prefix or alias scheme.
- **Verdict:** `confirmed`, **with the reader's rationale corrected**: `/attention` and `/concept?target=` *are* shipped spellings and are command-wired. The defect is four omissions plus one wrong spelling — `GET /status`, which the reader listed as correct.
- **State:** `ready-for-agent` — *repair*
- **Severity:** `medium`

### M6. The adapter's documented command roster is missing five registered commands

- **Where:** `docs/reference/evidence-and-integrations/integrations.md:106`
- **Quote:** "| Commands | Connect to local server, show attention count, show active Concept, queue operation, start/stop data collection session, record disposition, record fallback, flush queued events, delete queued events. |"
- **Contradiction:** `main.js:83-162` registers **fifteen** commands. The nine phrases map to ten of them; `open-attention`, `open-evidence-review`, `relate`, `fork-canvas`, and `graduate-scratch-edges` have no counterpart. None is feature-gated — all fifteen `addCommand` calls sit unconditionally in `onload`.
- **Verdict:** `confirmed`. The row was accurate at `8d5d1435` (2026-07-08); all five omissions landed 2026-08-01/02. Of the five, only `open-evidence-review` is documented anywhere else (`evidence-review.md:12`).
- **State:** `ready-for-agent` — *repair*
- **Severity:** `medium`

### M7. The bibliography cites `_papers/` as a repository path that has never existed

- **Where:** `docs/reference/evidence-and-integrations/bibliography.md:203` and `:164`
- **Quote:** "The wider literature reviewed for the design — ~400 papers — sits in `_papers/` (Zotero export `_papers/Exported Items.bib`), with synthesized adopt/borrow/reject verdicts in `_papers/REVIEW-SUMMARY.md`."
- **Contradiction:** `_papers/` is untracked, absent from the tree, and **explicitly retired** — commit `31256d3a` (#1367) deleted `/_papers/` from `.gitignore`, `cspell.json`, and `.yamllint` while scrubbing "stale scratch-dir paths", and missed these two lines. The synthesized verdicts survive in-repo at `design-history/archive/notes/REVIEW-SUMMARY.md`, linked from no doc.
- **Verdict:** `confirmed`. `doc_cited_paths` cannot own it: its regex admits only `src|scripts|tests|docs` roots.
- **State:** `ready-for-agent` — *repair* (repoint at the archived record, or say the corpus is author-local)
- **Severity:** `medium`

### M8. The telemetry page's eval-log example is not the record the scorer writes

- **Where:** `docs/reference/pipelines-and-io/telemetry.md:91-101`
- **Quote:** `{ "timestamp": …, "run_id": "eval-2026-06-01", "recall_at_k": 0.8, "support_rate": 0.75, "fama_clean": 1.0 }`
- **Contradiction:** `docs/reference/analysis-and-surfaces/vault-eval.md:102` describes the same file as carrying "timestamp, quarter, k, per-task records, and per-metric aggregates". `runtime/eval/eval_score.py:227-233` returns exactly `{timestamp, quarter, k, tasks, aggregate}` and appends it verbatim. `run_id` appears zero times in the scorer. The three metrics are nested, never top-level.
- **Verdict:** `confirmed`. `tests/test_eval_score.py:277,324` assert the top-level `quarter` and nested `aggregate` the example lacks. The page's two other JSON examples are literal complete rows, so its own convention reads an example as a real record.
- **State:** `ready-for-agent` — *repair*
- **Severity:** `medium`

### M9. `standing` is load-bearing catalog state with no field-level definition anywhere

- **Where:** `docs/reference/control-and-policy/evidence-sets.md:153`
- **Quote:** "An unset standing is `current` by design — standing is PI-curated catalog state, and the PI is the standing authority."
- **Contradiction:** `docs/reference/data-model/glossary.md` contains zero occurrences of `standing`; the `Work` entry omits it, and so does the Catalog Work Record table at `docs/reference/pipelines-and-io/ingest.md:99`. The closed set lives only in `cli.py:365` and `worker.py:1326`. The glossary does carry sibling field enums (`Check status`, `loudness`), so this is an omission against the page's own pattern.
- **Verdict:** `confirmed`, **narrowed**: the values are documented by *effect*, split across `evidence-sets.md` and `archive-a-source.md`. What is missing is any definition of the field and any statement that the set is closed. Compounding it, `archive-a-source.md:69` and `ingest.md:135` both route "lifecycle/Work record fields" to `frontmatter.md`, which documents note-level `archived:`/`superseded:` booleans — different fields sharing two of the same names.
- **State:** `ready-for-agent` — *record*: a `standing` ruling in `docs/reference/data-model/glossary.md`, with its machine form in `.vale/styles/config/vocabularies/Memoria/` in the same change.
- **Severity:** `medium`

### M10. The Home page marks shipped propagation as planned

- **Where:** `docs/README.md:75`
- **Quote:** "- **When a source falls, you will see everything it was holding up** *(planned — typed blast-radius propagation)*."
- **Contradiction:** `docs/explanation/knowledge/consequence-propagation.md:10` — "> **Shipped:** Typed consequence propagation and eager write-time marking run in the current graph substrate." `runtime/propagation.py` ships all four consequence types, the routing table, write-time marking, and the inbox surface, covered by 38 tests. The Home page's own authority claim at `:50-51` is "the docs never claim un-built behavior".
- **Verdict:** `confirmed`. Commit `217fc358` (2026-08-09) flipped the explanation page to Shipped and edited `docs/README.md` heavily without touching the guarantees block. What genuinely remains planned is six-role Toulmin typing (workstream G4), not this promise (G5). **Second location, stated more strongly:** `docs/explanation/rationale/foundations/design-principles.md:91-93` still reads "> **Planned (beta.1):** Origin-blind epistemic consequence and blast-radius propagation are not yet shipped."
- **State:** `ready-for-agent` — *repair* (both locations)
- **Severity:** `medium`

### M11. `.memoria/code-runs/` is documented as gitignored; the seed `.gitignore` has no entry for it

- **Where:** `docs/reference/system/on-disk-layout.md:73`
- **Quote:** "├── code-runs/<run-id>/      gitignored recorded code-execution run artifacts"
- **Contradiction:** the seed `.gitignore` lists six `.memoria/` paths and none is `code-runs`; there is no wildcard and no nested ignore file. `runtime/code/execution.py:137-141` writes there. Every other "gitignored" annotation in the same tree block maps to a real entry — this is the sole outlier.
- **Verdict:** `confirmed`, **with the reader's stated consequence corrected**: the artifacts land *untracked*, not tracked. The ongoing writer stages explicit pathspecs; the only sweeping `git add .` runs once at init, before any run can exist. The exposure is untracked noise and vulnerability to the researcher's own `git add -A`.
- **State:** `ready-for-agent` — *repair*
- **Severity:** `medium`

### M12. The reader is told the pill shows only recording/offline state; it renders workspace health

- **Where:** `docs/explanation/rationale/surfaces/visual-discipline.md:39`
- **Quote:** "The optional proof adapter uses Obsidian's status bar only for recording/offline state, not workspace health."
- **Contradiction:** `pill.js:22-46` renders six states, three of whose strings carry the open-attention count (`Memoria · ${openCount} open`), plus a `key-needed` credential prompt; `main.js:626-634` appends a fork-divergence badge whose own code comment concedes it "says nothing about whether the engine is reachable". The page's *preceding sentence* puts "Inbox attention and linter verdicts" under workspace health, closing the narrow reading.
- **Verdict:** `confirmed`, **wider than stated**: "recording" is not a shipped pill concept at all — zero occurrences across the plugin. The paragraph was written 2026-07-13; `pill.js` was seeded 2026-08-01.
- **State:** `ready-for-agent` — *repair*
- **Severity:** `medium`

### M13. The canonical worked transcript teaches an export path the reference forbids

- **Where:** `docs/tutorials/first-session-transcript.md:310`, with its captured result at `:318`
- **Quote:** "--draft --format markdown --output exports/burden-aware-prompts.md --json" and `"output_path": "exports/burden-aware-prompts.md"`
- **Contradiction:** `docs/reference/pipelines-and-io/export.md:91-93` — "every export lands beside them under `exports/` … There is no separate top-level deliverables tree", with all four artifact rows reading `projects/<project>/exports/`.
- **Verdict:** `confirmed`. `runtime/knowledge.py:3471-3477` resolves a relative `--output` against the vault root, and the transcript's own captured display path (relative to the vault root) proves the file landed there rather than beside the draft. `docs/how-to-guides/project/export-a-draft.md` uses the project-scoped form throughout. The transcript is new (2026-08-09); the convention it breaks is a month older.
- **State:** `ready-for-agent` — *repair*
- **Severity:** `medium`

---

## LOW

### L1. `verify-check-citation` is named as a Peer-reviewer method and exists nowhere

- **Where:** `docs/reference/analysis-and-surfaces/retrieval-and-analysis-methods.md:25`
- **Quote:** "**Used by:** Linter structural detectors, Peer-reviewer `verify-check-citation`, schema validation, and ingest type-detection dispatch."
- **Contradiction:** one hit repo-wide. Not in any of the 57 operation manifests, the CLI parser, or any source file. The page declares itself "the current lookup surface; non-active method ideas belong in release decision ledgers, design history, or explanation pages" and demonstrably knows how to flag unshipped identifiers elsewhere (`:38-39`).
- **Verdict:** `confirmed`. It is a rename artifact: `verify:check-citation` from the abandoned pre-alpha skill-naming scheme, mechanically hyphenated by #694. No successor id exists to substitute.
- **State:** `ready-for-agent` — *repair* (delete the identifier; the sibling `pattern-provenance.md:30` already renders the same idea in prose)
- **Severity:** `low`

### L2. Two rationale pages point at a section that defines neither callout types nor a palette

- **Where:** `docs/explanation/rationale/surfaces/design-system.md:82`, `docs/explanation/rationale/surfaces/visual-discipline.md:67`, and — in body prose — `visual-discipline.md:23`
- **Quote:** "- The callout types and their fixed three-color palette: [Obsidian](../../surfaces/obsidian/README.md#callouts)"
- **Contradiction:** the whole `## Callouts` section (`docs/explanation/surfaces/obsidian/README.md:32-46`) is four paragraphs with no table, no list, no identifier, and no colour. No roster or palette exists anywhere in `docs/`, the glossary, `docs/adr/`, or the seeded `styles.css`.
- **Verdict:** `confirmed`, with the reader's wording corrected — the target is *silent*, not opposite. The pointers were stale on the day they were written: `8d5d1435` folded a deleted page into a section that dropped its roster, and the "fixed three-color palette" has no antecedent in `docs/` at any revision. `doc_link_targets` passes because the anchor resolves.
- **State:** `ready-for-agent` — *repair*
- **Severity:** `low`

### L3. The reference index and `_sources.yml` disagree on which pages are gate-guarded

- **Where:** `docs/reference/README.md:38`, `:44`, `:54`
- **Quote:** "| [CLI](commands-and-transports/cli.md) | `memoria` command surface | Guarded mirror |"
- **Contradiction:** `docs/reference/_sources.yml:17-19`, `:47-49`, `:50-52` mark the same three pages `status: Manual`.
- **Verdict:** `confirmed`, **with the direction of fault inverted from the reader's framing**: `README.md` is the *correct* half. Real gates back all three labels — `doc_claims_gate.roster_drift_errors` for `cli.md` and `system-actions.md`, `control_plane_actor_gate` for `control-plane.md`, both run from `scripts/verify`. `_sources.yml` was corrected *down* to Manual on 2026-08-02 (#1739) and the README raised *up* on 2026-08-03 (PR #1752) ten hours later; nothing reconciled the abandoned file.
- **State:** `ready-for-agent` — *repair* (subsumed if L4 is resolved by deletion)
- **Severity:** `low`

### L4. `_sources.yml` is a second page registry with no consumer, missing three pages

- **Where:** `docs/reference/_sources.yml:1`
- **Quote:** "pages:\n  analysis-and-surfaces/calibration.md:\n    status: Manual\n    owner: …"
- **Contradiction:** it duplicates the Source column defined at `docs/reference/README.md:19-21`. Its only reader, `scripts/checks/docs_doctor.py`, was deleted in `125fc246` (#1349). Nothing in `scripts/`, `tests/`, `.github/`, `pyproject.toml`, `docs/_config.yml`, or `.pre-commit-config.yaml` loads it; there is no `_data/` directory and no `site.data` reference. It carries 44 pages against the README's 47, omitting `okf-compliance.md`, `evidence-review.md`, and `backup-and-recovery.md`.
- **Verdict:** `confirmed`. The repository says so itself: commit `19e056e8`'s message reads "nothing loads `_sources.yml` at all — so the file advertised enforcement that has never run."
- **State:** `ready-for-human` — delete it or wire it up. See Q7.
- **Severity:** `low`

### L5. Two pages call `.claude/` copied from the package seed; two of its files are engine-rendered

- **Where:** `docs/reference/system/configuration.md:22`, and by inheritance the Packaged Seed Inventory row at `docs/reference/system/on-disk-layout.md:164`
- **Quote:** "| First-init agent/MCP bundle | `src/memoria_vault/product/workspace_seed/.claude/`, … | copied once by `memoria init` |"
- **Contradiction:** `workspace_seed/.claude/` holds exactly two files. `runtime/bundles.py:65-76` writes four into a vault, of which `.claude/hooks/session_status.py` and `.claude/skills/memoria-copi/SKILL.md` are *rendered* by the engine — the module's own comment says so. `configuration.md`'s Source column is precisely a provenance claim, and its scope note disclaims only field-level contracts.
- **Verdict:** `confirmed`. `on-disk-layout.md:171-172` carries the analogous carve-out for the generated `AGENTS.md`, proving the page records such exceptions when it knows them.
- **State:** `ready-for-agent` — *repair*
- **Severity:** `low`

### L6. `.memoria/csl/` is instructed by two pages and absent from the page that lists every file

- **Where:** `docs/how-to-guides/project/export-a-draft.md:26` (also `:72`, `:87`) and `docs/reference/pipelines-and-io/export.md:59`
- **Quote:** "- A CSL style file — create `.memoria/csl/` in the vault and drop your `.csl` there"
- **Contradiction:** `docs/reference/system/on-disk-layout.md:10` claims "Where every file lives"; neither the `.memoria/` tree (`:61-82`) nor the five-row runtime-only table (`:180-188`) covers `csl/`, under any glob or prose.
- **Verdict:** `confirmed`. The "engine-created only" defence fails on the table's own first row, `.memoria/config/attention.yaml`, whose Created-by cell reads "the PI, by hand". Narrowing: the product is entirely unaware of the path — every `csl` hit in `src/` is CSL-JSON catalog metadata — so this is docs-vs-docs, not docs-vs-code.
- **State:** `ready-for-agent` — *repair*
- **Severity:** `low`

### L7. `resolve-evidence-review` sits in a column of shipped operation IDs

- **Where:** `docs/reference/control-and-policy/empirical-events.md:92`
- **Quote:** "| `resolve-evidence-review` | `evidence-set` | evidence id (`ev-xxxxxxxx`) | on every decision |"
- **Contradiction:** the column is headed "Operation"; seven of the table's eight cells are exact manifest IDs. There is no `resolve-evidence-review` manifest and never has been (`git log -S` returns nothing). The shipped ID is `resolve-evidence`; `resolve-evidence-review` is a journal payload value written at `runtime/knowledge.py:2850`. Six of the seven other rows never write an `operation` payload field at all, so the "payload field" reading of the column does not hold.
- **Verdict:** `confirmed`. Two more published pages name `resolve-evidence`; this line is the only place in `docs/` where the string appears.
- **State:** `ready-for-agent` — *repair*
- **Severity:** `low`

### L8. The frontmatter grammar says every type schema declares `enums:`; two ship without it

- **Where:** `docs/reference/data-model/frontmatter.md:29`
- **Quote:** "Each type schema declares `required:` and `optional:` maps of `field: kind`, plus an `enums:` block and optionally `required_when:` and `forbidden:`."
- **Contradiction:** `fulltext.yaml` and `code-artifact.yaml` have no `enums:` block. `runtime/vocabulary/schema.py:242` reads `schema.get("enums", {})` — it defaults to empty and the loader never requires the key; `tests/test_schemas.py` uses the same default.
- **Verdict:** `confirmed`. The two schemas' omission is a designed gap — neither declares an enum-kind field — which is what makes the sentence wrong rather than the schemas. It was inaccurate at authoring: neither file has ever contained an `enums:` block. **Second location:** `docs/reference/data-model/document-types.md:16-18` repeats the grouping.
- **State:** `ready-for-agent` — *repair*
- **Severity:** `low`

### L9. The layout tree's `projects/` line omits three generated artifacts

- **Where:** `docs/reference/system/on-disk-layout.md:37`
- **Quote:** "├── projects/<slug>/         project.md, outline.md, draft.md, code/<artifact-id>.md, evidence/gap/export artifacts"
- **Contradiction:** shipped code writes `argument.canvas` (`runtime/projections.py:34`, `knowledge.py:2195`), `scratch-<name>.canvas` (`knowledge.py:2268-2292`), and `project-gate-index.md` (`runtime/project/structural_impact.py:381`) into that folder. `grep -i "canvas\|gate-index"` over the whole page returns zero hits.
- **Verdict:** `confirmed`, **narrowed to three of four**. `exports/` is refuted twice over: the line's own "export artifacts" covers it, and no shipped code writes a fixed `exports/` directory.
- **State:** `ready-for-agent` — *repair*
- **Severity:** `low`

### L10. The seed `.gitignore` ignores `.memoria/queue/`, which nothing creates

- **Where:** `src/memoria_vault/product/workspace_seed/.gitignore:17`
- **Quote:** ".memoria/queue/" — under the header "# Regenerable runtime data."
- **Contradiction:** nothing creates or reads it. `tests/test_worker_queue.py:183` and `tests/test_runtime_state.py:282` positively assert `not (vault / ".memoria/queue").exists()` after a real init and job run. Every sibling under the same header has a real producer; this is the only orphan. It is a leftover of the alpha.12 file-queue mirror retired by #1059, copied forward seven days after it died.
- **Verdict:** `confirmed`. The finding rests on the code and test legs; the reader's cited docs leg is the weak half, since the `.memoria/` tree nowhere claims exhaustiveness.
- **State:** `ready-for-agent` — *repair* (delete the line; AGENTS.md ranks deletion first)
- **Severity:** `low`

### L11. The memory-model page names a substrate the reference table calls something else

- **Where:** `docs/explanation/architecture/memory-model.md:32-34`
- **Quote:** "**Request memory** …, **session history** when an optional adapter exists, and **working memory** …"
- **Contradiction:** `docs/reference/pipelines-and-io/memory-substrates.md:24` — "| **Adapter memory** | Optional external adapter | …". The page enumerates six bolded substrates and points at the table for "what each substrate holds" (`:36`); five names match exactly, the sixth does not.
- **Verdict:** `confirmed`. The same page uses the canonical name at `:117` and `:154`, so it is internally inconsistent too. Mechanism: "Session history" was a distinct substrate in the pre-standalone seven-substrate model and was folded into Adapter memory; the name outlived the merge.
- **State:** `ready-for-agent` — *repair*
- **Severity:** `low`

### L12. A rationale link promises a Linter page and lands on one that never names it

- **Where:** `docs/explanation/rationale/boundaries/why-deterministic-methods.md:60`
- **Quote:** "- The zero-LLM operation this rationale produces: [The Linter](../../execution/operations.md)"
- **Contradiction:** `docs/explanation/execution/operations.md` is 37 lines and contains zero occurrences of "Linter". Both sibling bullets in the same Related list use link text identical to their target's title; this is the only bullet whose link text matches no page title in `docs/`.
- **Verdict:** `confirmed`. The link text was accurate when authored — its original target carried a named Linter section — and reorg commit `8d5d1435` repointed it at a successor page that dropped all named-operation content.
- **State:** `ready-for-agent` — *repair*
- **Severity:** `low`

---

## `ready-for-human` findings not already carded above

### Q-class findings

These are carded here for completeness; their questions appear in the round below.
Each card's Quote and Contradiction are in its prose; the other four fields are
tabulated here so every card carries all six.

| # | Where | Verdict | State | Severity |
| --- | --- | --- | --- | --- |
| F1 | `src/memoria_vault/product/workspace_seed/claims.base:26-39`, `inbox.base:49-53` | `confirmed` (narrowed) | `ready-for-human` | `medium` |
| F2 | `docs/reference/data-model/glossary.md:352` | `confirmed` | `ready-for-human` | `medium` |
| F3 | `docs/adr/README.md:13` | `confirmed` | `ready-for-human` | `low` |
| F4 | `docs/reference/evidence-and-integrations/bibliography.md:203` | `confirmed` | `ready-for-human` | `low` |
| F5 | `docs/how-to-guides/setup/quickstart.md:19-23`, `set-up-obsidian.md:14-17` | `confirmed` (relocated) | `ready-for-human` | `medium` |
| F6 | `src/memoria_vault/product/workspace_seed/.memoria/config/providers.yaml:10-12` | `confirmed` | `ready-for-human` | `medium` |
| F7 | `docs/tutorials/02-first-source.md:39`, `07-customize.md:65` | `confirmed` | `ready-for-human` | `medium` |
| F8 | `docs/reference/pipelines-and-io/telemetry.md:38` | `confirmed` | `ready-for-human` | `medium` |
| F9 | `docs/reference/system/on-disk-layout.md:140` | `confirmed` (checker class) | `ready-for-human` | `medium` |
| F10 | `docs/reference/evidence-and-integrations/integrations.md:94` | `confirmed` (checker class) | `ready-for-human` | `medium` |
| F11 | `docs/reference/evidence-and-integrations/bibliography.md:21-22` | `confirmed` | `ready-for-human` | `low` |
| F12 | `docs/explanation/rationale/surfaces/design-system.md:23-26` | `confirmed` | `ready-for-human` | `low` |

**F1 (medium) — Seeded Base views ship the views four pages call planned.**
`src/memoria_vault/product/workspace_seed/claims.base:26-39` and `inbox.base:49-53`
ship views named "Open questions", "Contradictions", and "Loose ends" with the
filters `docs/explanation/surfaces/dashboards/synthesis-agenda.md:32,40` and
`structural-health.md:28` describe in the subjunctive ("The planned … view
would surface …"), and `docs/reference/analysis-and-surfaces/dashboards.md:25`
marks the row "Planned optional adapter". `tests/test_bases.py:44-59` pins the
names and filters as a contract, `core-plugins.json` enables Bases, and
`docs/how-to-guides/operate/run-a-retraction-sweep.md:67` instructs the
researcher to open the Contradictions view. **Narrowed:** behaviour-level
collision holds only for those three; "Reading pipeline" and "Discuss queue"
(`sources.base`) are self-described unfiltered placeholders, so the reader's
headline quote is its weakest instance, and `on-disk-layout.md:132` and the
glossary `Maintenance` entry are *not* instances — they draw the
dashboard-vs-Base-view distinction correctly. The gap is that no *published*
page states that same-named Base views ship. `ready-for-human`.

**F2 (medium) — `block` loudness: engine-wide pause or adapter-only?**
`docs/reference/data-model/glossary.md:352` states unqualified that "an open
block card pauses delegation and review-gated promotion until the PI resolves
it" (repeated in the `Promotion` entry at `:361`), while
`docs/reference/system/failure-modes.md:26` scopes it to "the optional
policy-hook path" and says "the standalone CLI/worker path is not paused by
loudness". Code sides with failure-modes: `runtime/attention/loudness.py:98`
`open_blockers` has exactly one production consumer, `runtime/policy/engine.py`,
instantiated only from `runtime/policy/hook.py`, while `trusted_writer.py:927`
`promote_checked` consults no blocker. "Delegation" has no
loudness-conditioned enforcement at all. `docs/how-to-guides/inbox/work-the-action-queue.md:68-71`
is a *third* instance of the broad phrasing, not a corroboration of the narrow
one as the reader claimed. `ready-for-human`.

**F3 (low) — `docs/adr/README.md` cites an exclusion `docs/_config.yml` does not contain.**
`:13` reads "Not published to the site — see `docs/_config.yml`", whose exclude
list is `**/tmp/`, `superpowers/`, `agents/`. The repo's own shared reader,
`scripts/checks/doc_link_targets.py:48-61` — written precisely so the list is
"read rather than restated" — classifies `docs/adr/README.md` as **published**.
The page is also the only published page with no Jekyll front matter, which
suggests the author intended it off the site; under the Pages classic builder
that would not achieve it. `CONTRIBUTING.md:74-80` names this exact drift class.
`ready-for-human`, because whether `adr/` should be excluded is an owner call.

**F4 (low) — The bibliography holds three entries its own coverage rule excludes.**
`:203` declares "This list holds works *cited in the documentation*, not
Memoria's full reading corpus", with no exception clause. `ajith2024litsearch`,
`li2025scilitllm`, and `idea2paper` are cited from nowhere — verified by anchor,
title, identifier, and author across all published docs. Exactly 3 of 57
anchors; no others. The rule was added (2026-07-06) over a list that already
contained them. `ready-for-human`.

**F5 (medium) — No page states a minimum Obsidian version, and the seed needs 1.9.0.**
The seed sets `"bases": true` and ships five `.base` files; upstream, Bases is a
core plugin introduced in **Obsidian 1.9.0**. `quickstart.md:19-23` and
`set-up-obsidian.md:14-17` both run Prerequisites sections, name Obsidian, and
state no floor; a sweep of `docs/` finds no Obsidian version token anywhere, and
no code path checks one. **The reader's collides-with is refuted:** the bundled
plugin's `minAppVersion: 1.5.0` is defensible — the plugin uses no Bases API —
and cannot express a requirement of the vault seed. The wrong artifact is not
`manifest.json`; the *missing* claim is in the setup pages. The repo pins other
third-party floors ("Python 3.12+", "macOS is not supported"), so silence is not
a convention. Failure mode is bounded: a user on an older build silently gets no
Base views. `ready-for-human`.

**F6 (medium) — The seeded `gateway` points at OpenAI while naming a Kilo credential.**
`src/memoria_vault/product/workspace_seed/.memoria/config/providers.yaml:10-12`
sets `url: https://api.openai.com/v1` and `key_env: KILOCODE_API_KEY`;
`docs/reference/evidence-and-integrations/integrations.md:115` calls it the
"**Kilo Code gateway**". The block is live YAML — the file has zero comments —
and `configure-the-optional-gateway-runner.md` never instructs replacing the
URL. `runtime/operations.py:404-422` reads `os.environ[key_env]` with no
fallback, so a user following the guide sends a key stored under
`KILOCODE_API_KEY` to OpenAI's endpoint. Upstream (fetched by the auditor): Kilo
documents `https://api.kilo.ai/api/gateway` with `KILO_API_KEY`; the repo's own
frozen record at `design-history/08-alpha.8.md:29` corroborates the `api.kilo.ai`
host. **Residual unsettled sub-question:** whether `KILOCODE_API_KEY` is still a
live Kilo variable name could not be settled. `ready-for-human`.

**F7 (medium) — Seed and tutorials create a vault-root `tmp/` the linter flags.**
`session-diary.md:8` offers `tmp/` and `docs/tutorials/02-first-source.md:39`
and `07-customize.md:65` issue a literal `mkdir -p tmp/tutorial` with the cwd at
the workspace root. `folders.yaml` contains no `tmp` under any key, and
`detectors.py:405-415` reports any root dir outside `known_top_dirs` ∪
`SKIP_DIRS` as "stray top-level folder not in the vault schema". The finding is
LOW and report-only (`verdict()` returns PASS with only LOW findings), and no
tutorial cleans up, so `tmp/` persists. `tests/test_integrity.py:579` only
covers what `init` seeds, so nothing catches it. `ready-for-human`: allow `tmp`
in the schema, change the tutorials, or accept the advisory finding.

**F8 (medium) — `lint-findings.jsonl` is documented with a cadence that never occurs.**
`docs/reference/pipelines-and-io/telemetry.md:38` lists it as written "per manual
or scheduled lint run". `detectors.py:564-585` writes it only when `--jsonl-out`
is passed; the flag has no default, `append_findings_jsonl` has exactly one
non-test call site, and **no shipped or documented path passes it** — the sole
historical producer, a cron-runner, was deleted in `cf6fcdae` (#1322) along with
the test that pinned it. No scheduled lint run exists at all
(`run-the-linter.md:16`: "The installer does not register that schedule").
**Second location:** `on-disk-layout.md:44` lists the file as present.
`ready-for-human`: default the flag, document it, or drop the row.

**F9 (medium, checker class) — No gate compares the seed tree to the Packaged Seed Inventory.**
Generalises M1 and M2. `schema_doc_drift` globs only `types/*.yaml` against two
pages; `doc_cited_paths` admits only `src|scripts|tests|docs` roots, so it skips
all 18 inventory rows, which are vault-relative. `tests/test_installer_skeleton.py`
asserts exact set equality between the seed tree and a literal set *in the test
file* — pinning the code roster while the doc table stays green and wrong.
**Two corrections to the proposed gate:** strict set equality is not
implementable (the inventory column holds one glob, two directory prefixes, and
three multi-path cells); coverage semantics is, and reproduces exactly the two
findings. And the "inventory rows outlive their files" direction has **zero**
current instances. Precedent exists: `control_plane_actor_gate.py` pins a
published table to a Python roster after "the table drifted twice in one release".
`ready-for-human`, because AGENTS.md ranks deletion above a checker and deleting
the table in favour of the already-pinned test roster is a live alternative.

**F10 (medium, checker class) — No gate pins adapter documentation to the plugin source.**
Generalises M3, M4, M5, M6. The only Obsidian-aware gate,
`plugin_provenance_doctor.py`, checks file membership, never content;
`doc_claims_gate` is scoped to the Python argparse tree and the operation
manifests. The node harness under `packages/memoria-obsidian/` makes zero
documentation assertions. **Two corrections:** command ids extract by a stable
regex, but routes do **not** — only 4 of 7 live routes are `*_PATH` constants, so
the proposed extractor would false-flag the doc's two correct routes. And the
`integrations.md` rows are prose inside table cells, so the doc must adopt a
roster shape first (`cli.md`'s `## Complete command roster` is the working
precedent). At the mechanism level this is two classes, not one: an id/route gate
would not touch either SecretStorage claim. `ready-for-human`.

**F11 (low) — `https://x.com/karpathy` cited for a named design pillar.**
`bibliography.md:21-22` cites "Public remarks and posts" with a URL whose path is
an account handle; every other external URL on the page paths to the artifact it
cites (article path, named note, PDF, named repo, DOI, arXiv `abs/ID`). It is the
sole `x.com` URL in published docs. It carries the LLM-Wiki pillar's only
citation (`intellectual-foundations.md:21`) and a second, different claim at
`why-not-autonomous.md:16` that the entry's own title does not name.
Classification under the brief: **internalize** — the substance already lives on
a Memoria page and the URL contributes no retrievable content. Narrowing: the
entry itself is mandated by `CONTRIBUTING.md:111-114`; what fails is the URL's
locating function, not the attribution. `ready-for-human`.

**F12 (low) — `https://github.com/nexu-io/open-design` cited for a shape nothing instantiates.**
`design-system.md:23-26` says the rationale "follows the open-design DESIGN.md
shape"; `:16-17` states "The current workspace does not ship a separate
design-system contract file". Commit `67f56e691` (#1326) authored *both* sentences
in one diff: it deleted the vault artifact that implemented the nine-section
schema and kept the link while replacing every checkable property ("nine-section
format that design tooling can parse directly" → "a structured way"; "one file" →
"one vocabulary"). The page does not instantiate the shape — five content
sections against nine schema slots. Classification: **internalize**, second branch
("a link that has become decoration"). **Two corrections:** the two sentences are
not strictly contradictory (different subjects — workspace vs docs page), and the
denial *precedes* the link rather than following it. `ready-for-human`.

---

## Refuted candidates, and why each failed

Recorded so a later audit does not re-raise them.

| # | Candidate | Why it died |
| --- | --- | --- |
| R1 | 40 anchorless `design-history/arcs.md` citations, plus a gate for them | `CONTRIBUTING.md:104-106` prescribes exactly the blob-URL form used. `arcs.md` is an 11-arc thematic synthesis with no per-decision headings to anchor into; for 9 of the 41 links the cited subject appears nowhere in the file. The 41 links carry only 18 distinct subjects, not "forty differently-titled". `doc_link_targets.py:133-134` skips external URLs by stated design. The proposed gate could not pass today's corpus. |
| R2 | "Open questions" carries two incompatible meanings | The glossary carries **no definition of the term at all** — the candidate's premise. The surface page's phrase is a shipped, test-asserted view name (`claims.base:27`, `tests/test_bases.py:46`) whose extension the same sentence states, and the ordinary-English sense is pervasive across six other live pages. |
| R3 | The co-PI method bundle is documented nowhere in `docs/` | Four published pages document it: `roadmap.md:97` ("Co-PI skill / MCP"), `on-disk-layout.md:164` (the `.claude/` row with its full lifecycle), `:151` (the `Start here.md` "co-PI variant pointer"), and the `operation-postures/co-pi.md` page. Directory-granularity rows are the inventory's own convention. |
| R4 | `linter.md`'s `schema-check` row omits vocabulary enforcement | The parenthetical is a summary, not an inventory: it already omits four other real branches of the same detector (retired fields, `forbidden`, general missing-required, `required_when`). No page contradicts another — `vocabulary.md:44` states the behaviour correctly. Nothing in the repository is wrong. |
| R5 | Hub-split threshold 15-20 vs 20-30 | The passages measure different objects: tag-derived member notes of one branch vs authored entries in the hub body (the remedy there is "pruning and annotation", operations on body lines). The `hub-threshold` detector's 15 is a hub-**creation** number that by construction cannot fire for a topic that already has a hub. |
| R6 | `AGENTS.md` uses "Knowledge Bundle" for an argument graph | The glossary's single sense is "the plain-file tree **holding** the researcher's knowledge" — a container — which is exactly how `AGENTS.md` uses it ("claims **in** Knowledge Bundles"). Plural bundles vs a singular graph shows the parenthetical glosses the graph, not the bundle. `docs/overview.md:23` already uses the same container phrasing. |
| R7 | `fulltext.yaml` declares an unrecognised `category` | `folders.yaml`'s `categories:` is a **fallback alias for `bundle_roots:`** (`schema.py:149`), a different namespace. The shipped invariant on a schema's `category:` is *prefix*, not membership (`tests/test_schemas.py:229`), and `fulltext`/`fulltexts` satisfies it. The prefix tolerance predates the value. |
| R8 | "Zotero 9" is a stale version claim | Upstream: the Zotero download page currently offers **Zotero 9**. The guide names the current major version. (The Better BibTeX *menu path* on the same line remains an unsettled third-party claim — see the scope line.) |
| R9 | `grounds resolve` is a non-existent command | The page disclaims the reading one sentence earlier: `states.md:79-83` — "**This is not a separate CLI command** or a complete Toulmin warrant graph." The quoted line also sits inside a `> **Planned (beta.1):**` callout, and `doc_claims_gate` treats a backticked span as a CLI claim only when it starts with `memoria`. |
| R10 | Residual "per-profile policy" vocabulary | The word is not retired repo-wide — `why-operation-postures.md:93,98` uses it affirmatively in current prose, and "installed profile" appears across six live pages. The glossary carries no retirement ruling. Sequence is also backwards: the row was *re-authored* three weeks after the retirement statement. |
| R11 | `.out-of-scope/` is a dangling reference | The lazy-creation convention **is** declared: `issue-tracker.md:70` names `/triage` as the writer, and the installed skill's `OUT-OF-SCOPE.md:90-95` specifies create-on-first-rejection. The convention landed 2.5 days before HEAD; `docs/adr/` is the repo's own precedent for an effectively-empty lazily-written store. |
| R12 | `claims.base` has a dead `is_orphan` formula and a mis-filtered "Retracted" view | Both halves die. `is_orphan` is pinned on both sides by `tests/test_bases.py:50,58`, mirrored by `loudness_rank` in `inbox.base`, and required by a repo-wide convention (`formula.*` never appears inside a `filters:` block). "Retracted" filtering `superseded` conflates a catalog **Work** standing (`cli.py:365`) with a **note** frontmatter boolean; a notes-scoped view has no `retracted` field to filter. |
| R13 | `archive-a-source.md` routes lifecycle fields to the wrong authority | `frontmatter.md` **owns three of the four** — `archived: bool` (`:75`), `superseded: bool` (`:92`), `stale: bool` (`:93`). "Owns none of them" over-claims. No better target exists, since no page owns catalog standing. (The real residue is carded as M9.) |
| R14 | Session digest called per-session on one page, per-request on three | Only **one** artifact exists, and shipped code calls it both: `session_summary.py` groups by `request_id` while writing `"record": "session"`. "Only this table says per-session" is false — five more doc locations plus `detectors_audit.py:147` say it. The "older meaning" claim is temporally inverted: the per-request line is the newer of the three. |
| R15 | The non-Concept `type` roster omits `eval-task` | The sentence makes no completeness claim; its one universal quantifier ("only the six types above are schema-validated Concepts") is true. The repo mechanises what a closed roster is — `doc_claims_gate` keys on literal `## Complete … roster` headings, which this page lacks. `eval-task` is read but never written by shipped code, and the seed ships no gold tasks. |
| R16 | `safe-mode.md` names a `proposed` state no enum defines | `proposed` **is** a shipped enum member and the default value: `runtime/attention/worklists.py:30` `DECISIONS`, documented at `worklists.md:41`. The candidate was self-refuting. The cited collision is also out of scope — `what-checked-means.md:21` closes the value set for `check_status` only, a field safe-mode never mentions. |
| R17 | Glossary's "sole write action" vs read-api's three writers | Two consistent statements about different registries. The glossary defines its quantifier inline with a pointer to `surface_contract.py`, which has 26 rows and exactly one `"kind": "write"`. The read-API functions are not registered actions at all — and they queue requests, which is precisely what the glossary says the sole write action does. |
| R18 | `fix-stuck-card.md`'s filename contradicts the glossary | The word "card" occurs **zero** times in the page's prose; the page carries the disambiguation the candidate says is missing (`:12-14`). All six live inbound links render the text "Fix a stuck request". A legacy slug after a deliberate rename is a house pattern — `honesty-card.md` and `promotion-and-gated-zones.md` are the same shape. |
| R19 | "the eight actions above" has no list above it | The same cell parenthesises all eight names, which match `runtime/policy/paths.py:7` exactly — nothing is delegated to the missing antecedent, so the reader is never deprived. The second cited location is an explicit markdown link to the owning page, not a deictic. A vestigial word, not a dangling reference. |
| R20 | `worklists.md` / `project-structural-impact.md` route to the wrong authority | Half self-refutes: `project` **has** a per-type schema. And `frontmatter.md:209` explicitly covers untyped documents ("Most `system/` infrastructure … are untyped and exempt"), which is where worklist rows land — the candidate's own stated defence test. The three gate-index fields are documented on the page that owns them. |

---

## Scope line

- **Commit audited:** `e9d74cf51ee2400290850d233c98f676d0760875`, clean tree, in the worktree `.claude/worktrees/audit-rerun` (detached HEAD at scope time).
- **Files read:** 228, listed exhaustively before dispatch. `docs/` minus `docs/superpowers/` and `docs/favicon.ico` (177 files: `reference` 56, `explanation` 63, `how-to-guides` 45, `tutorials` 9, `agents` 5, `adr` 1, plus `README.md`, `overview.md`, `roadmap.md`, `_config.yml`, `_sass/`); `src/memoria_vault/product/workspace_seed/` (42); `AGENTS.md`; `CONTRIBUTING.md`. 871,363 bytes. Both readers reported reading 228 of 228 in full.
- **Files excluded, with reasons:** `design-history/` (123 files) — frozen by design, per the brief. `docs/superpowers/` (43) — point-in-time working records, per the brief. `test-vault/` — gitignored build artifact, per the brief; it is not in `git ls-files` at all. `docs/favicon.ico` — binary, no prose to compare. Everything else tracked (`src/` outside the seed, `tests/`, `scripts/`, `packages/`, `.github/`, `.vale/`, `.vscode/`, `.claude/`, and the 21 remaining root files) — outside the brief's scope defaults. The brief states reasons only for the first three; the remainder are excluded by its scope-defaults list without an individually stated reason there.
- **Cross-cutting comparisons not made: none.** The corpus fit one slice, so both halves of every comparison were held by a single reader, twice over.
- **Evidence read outside the audited scope:** both readers and every skeptic were free to read `src/`, `tests/`, `scripts/`, `packages/`, `design-history/`, and `docs/superpowers/` as evidence. Findings are only ever sited in the audited surfaces.
- **Prior audit findings were reachable from this checkout, which bounds how independent this run was.** A skeptic reached the sibling branch `wip/audit-record` by `git` and found commit `00d990ff` (2026-08-09) — an earlier run of this same skill — already filing M1 and M2 with a repair plan. That branch is not an ancestor of the audited commit, so the defects stand unrepaired, but the corroboration is not independent. The readers were not pointed at it; the discovery was incidental to one skeptic's `git log` sweep. The frozen `2026-08-03` Diátaxis audit's refuted list is also in-tree (`docs/superpowers/specs/`) and was checked against all 62 candidates: no candidate re-raises a previously refuted flag.
- **Third-party claims settled by the auditor, not the inspectors** (the read-only agents have no network): the current Zotero major version, the Obsidian release that introduced Bases, Kilo's documented gateway host and key name, and Better BibTeX's pinned-key Extra-field marker. Two residuals remain **unverified, not unsettled findings**: the Better BibTeX preferences menu path on `set-up-zotero.md:24`, and whether `KILOCODE_API_KEY` is still a live Kilo variable name. Neither changes a verdict.
- **Nothing was applied.** The working tree shows no change other than this report.
