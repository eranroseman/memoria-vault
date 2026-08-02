## alpha.23 - The usable loop: a live argument graph, one read surface, and instrumented judgment

**Theme:** alpha.22 made the substrate *keyed*; alpha.23 makes it *usable*. The
argument graph stops being a schema and starts propagating — a retraction now
reaches every claim that stood on it, typed by how it was reached. Retrieval,
attention, evidence review and the cockpit converge on one read API and one
seven-panel dashboard, so the researcher has a single place to see what the
vault knows and what it is asking of them. A second telemetry plane, deliberately
separate from the hash-chained journal, records what the machine observed without
letting analytics contaminate the trust record. It is the first checkpoint where
the phrase "co-PI" describes behavior rather than intent: the system now
proposes, routes, throttles and reports, while every consequential write still
waits for the one human.

**Schema:** rungs 17-19 (relation roster, `telemetry_events`,
`concept_verdicts.consequence`). Fresh-install only, as since alpha.22: a bump
declares incompatibility, it does not authorize an upgrade path.

### 1. The graph propagates (ERP-A through ERP-D)

- **What:** `propagation.compute_consequences(vault, target_id, *, trigger)` walks
  the closure reachable from a retracted or superseded target and returns, per
  concept **path**, `{consequence, via, depth}` — a pure read, no writes, no
  journal. `propagate_consequences` is its writing sibling: it labels every claim
  it reaches, commits them through the trusted writer, and routes an alert card
  into each active project whose slice the closure touched. `hop_consequence`
  types each hop, so a claim that lost its grounds and a claim whose warrant was
  merely weakened are not the same finding.
  **Why:** a retraction that does not travel is a retraction only its author knows
  about. The vault's whole claim is that trust rests on inspectable structure, and
  structure that cannot carry bad news is decoration.

- **What (namespaces, made explicit):** the graph now names three key spaces and
  refuses to confuse them. `links:` frontmatter and the substrate projection answer
  in **path space**; the resolver is an **alias table** whose key domain is a strict
  superset; `concept_edges` rows are **identity space**, where an unresolved target
  is SQL `NULL`. `edges.concept_edge_path_pairs` is the one projection production
  reads. **Why:** the same conflation produced four separate defects during this
  checkpoint, one of which fused two unrelated projects' slices through a single
  blank hub keyed `"None"`. Naming the boundary is what makes the next one visible.

- **What (ERP-D):** `structural_impact` reads the substrate projection instead of
  parsing authored `links:` text; the finding family follows Graph-R11's roles; and
  `edge-write.v1` counts every edge write by relation type at the seam a researcher
  actually used. **Why:** the structural graph was over-resolving past its own
  validator — three `links:` shapes that `schema._check_links` rejects were
  producing edges anyway.

### 2. Identity settles (NID-A through NID-C)

- **What:** concepts are keyed by path, `concept_edges` carries `target_path`, the
  mirror is upsert-and-prune, and `compile_source_digest` writes hub candidates
  through the Candidates block writer rather than staging a suggestion copy.
  **Why:** two identities for one note is two answers to every question asked of
  it. The v16 numbered-migration mechanism the plan drafted was never built, by
  design — under the fresh-install ruling the contract is delivered directly.

### 3. One read surface (U1, U2, R2)

- **What (U1):** every read the product performs goes through a registry row in
  `engine/surface_contract.py` and a named function in `engine/api.py`. The CLI,
  HTTP and MCP doors bind to rows, not to internals. **Why:** three surfaces
  reimplementing one read is three chances to disagree about what the vault says.

- **What (U2):** `memoria dashboard` and the cockpit read
  `assemble_dashboard(vault)` through `dashboard.read`, never past it. Seven
  panels — attention flow, dispositions, evidence review, reads staleness, edge
  writes, exploration, decision rules — with `DASHBOARD_PANELS` as both roster and
  order. **Why:** the cockpit is where the researcher decides what to do next; a
  panel that quietly diverges from the engine is worse than a missing one.

- **What (R2):** retrieval modes are frozen. `tests/fixtures/retrieval/cases.yaml`
  carries `frozen: true, frozen_on: 2026-08-02` on all three registered rows,
  evaluated green *before* the freeze so the preregistered bets stand as
  registered. An empty answer is *honest* — the payload says so, and says at which
  stage the count reached zero. **Why:** a retrieval system that cannot say "I
  don't know" will always find something, and something is what a researcher will
  then cite.

### 4. Two planes, kept apart (I1)

- **What:** `telemetry_events` (rung 18) is a second, non-chained plane for what
  the machine observed — view opens, dwell, onboarding steps, edge writes, import
  runs. The hash-chained `event_log` remains the authoritative journal and records
  what was *decided*. The separation is asserted at the writer, both ways: one
  telemetry row **and** a before/after identity snapshot of the entire journal
  plane across the call. **Why:** analytics wants volume and tolerates loss;
  provenance tolerates neither. Mixing them makes the trust record a function of
  how much the researcher happened to browse.

- **What (attention):** `rank_factors` rides every card payload —
  `{loudness, priority, impact, staleness, age_days}` — with a configurable
  ordering contract, per-producer throttles, and `attention-admitted` /
  `producer-run-skipped` telemetry at admission. `age_days` is signed; `priority`
  is reported verbatim and never normalized, so a typo ranks as nothing rather
  than silently as something.
  **Why:** the inbox is the system's only claim on the researcher's time. It has to
  be orderable, pausable, and honest about why a card is on top.

- **What (dispositions and rules):** six operation families emit `disposition.v1`,
  and a sixteen-entry decision-rule registry ships as a code constant — one source
  of truth, readable on vaults that already exist — assessed against the live
  panels into `would_fire` entries carrying the numbers that crossed.
  **Why:** a stop rule the vault cannot see is a stop rule kept in a notebook.

### 5. The loop a researcher can actually run (O1, O2, V2)

- **What (O1):** `memoria init` seeds, `memoria seed install` admits a starter
  corpus, `memoria onboard` walks the first project, and five telemetry emit
  points — `init-done`, `project-framed`, `seed-installed`, `onboard-done`,
  `first-answer` — observe whether that path is actually walked. The tutorials
  follow the seeded path rather than describing an older one.
  **Why:** an empty vault is the hardest state to be in, and the one every user
  starts from.

- **What (O2):** staged import routes each entry by what is known about it,
  collects duplicate, unmapped and failed entries into one import worklist, and
  writes a single `import-run.v1` row per run. **Why:** bulk import is where a
  vault stops being a demo, and where a silent failure is most expensive.

- **What (V2):** all seven `memoria review` verbs, plus an Obsidian evidence-review
  pane with the machine's analysis behind a disclosure the researcher opens.
  **Why:** grounds that are never reviewed are asserted, not checked — and the
  analysis has to be *offered*, not applied.

### 6. Surfaces (BOOT, U3-PLUG, U3-CANVAS, U4)

- **What:** the installer seeds a workspace whose bundles are write-if-absent; the
  Obsidian plugin carries attention and evidence panes, a relate modal that proves
  its warrant end to end over the wire, canvas forks with staleness reporting and
  edge graduation, and a hardcoded-color detector that holds the theme boundary.
  The co-PI method ships to `AGENTS.md` for agent consumers, and
  `generate-questions` turns a scope into inspectable prompts.
  **Why:** Memoria is used through an editor, not a terminal. A surface that
  bypasses the engine is a second implementation of the vault's rules.

### 7. What this checkpoint chose not to build

- **No upgrade path.** Every schema change from 17 to 19 edits the current DDL and
  fails closed on any other rung.
- **No `read-observed.v1` from the ask path.** Deliberate, and now recorded as a
  decision rather than a deferral: the conversational-ask read is neither a
  telemetry emitter nor a journal writer, and that silence is tested with positive
  controls on both planes.
- **No automatic rule application.** `apply-decision-rule-notices` mints a notice;
  it does not act. The panel reports, the researcher decides.
- **No project-slice fallback.** `propagation.active_project_slices` is the sole
  provider; the `links:`-frontmatter closures that preceded it were deleted rather
  than left as dead producer state with live tests over them.

### Status

**This chapter is not yet frozen.** Every plan feeding alpha.23 is at zero open
tasks except three items, and all three require a human at a keyboard:

- **LOOP.13** — the instrumented 10→100 staged-import run, against a fresh real
  vault with licensed Zotero exports, live model dispatch and human wall-clock
  triage timing (#1702). Every code precondition is closed.
- **U3-PLUG.11** — the manual Obsidian click-through (#1690).
- **U3-CANVAS.5's manual check** — the same interactive-Obsidian class.

No functional gap remains open. The last one — `copi_bundle_files()` having no
production consumer, so the co-PI method reached agent consumers through
`AGENTS.md` while the vault-embedded skill files were seeded nowhere — closed with
#1699: `seed_bytes` now resolves a rendered provider before falling back to
packaged bytes, and the `SessionStart` registration ships with the hook, since
`.claude/hooks/` is not auto-discovered and an unregistered hook would have been
one dead artifact traded for another.
