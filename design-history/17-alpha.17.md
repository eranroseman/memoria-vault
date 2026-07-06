## alpha.17 - WRITE half: host-neutral text output loop

**Theme:** alpha.17 is the checkpoint that turns alpha.16's READ substrate into
the first host-neutral WRITE loop: project slice -> outline -> draft ->
verification/export -> draft passage back into the knowledge graph. It lands
text output only, through files, CLI operations, and the read API; the
Obsidian-plugin/workspace-topology track and code execution remain outside the
checkpoint.

What drove it (2-3 sentences): beta.1 planning had already resolved several
writing mechanisms, but only the text-output subset was design-resolved and
host-neutral. The owner directive was to ship what could be built now, while
separating two unrelated future gates: client/workspace rendering and code
execution sandboxing. Implementation landed in PR #1278 (`0031586b`, "Implement
alpha17 write half") and was simplified in PR #1281 (`756fbea2`); the checkpoint
was not cut as a formal release-please package/tag.

---

### 1. Role and acceptance boundary

- **What:** alpha.17 ships the text WRITE path: propose a project slice, write
  `outline.md`, compose `draft.md`, attach evidence-set markers, verify the
  draft, export with `project export --draft`, promote a selected draft passage
  into an unchecked note, surface exploration candidates, and run seeded gate
  calibration. **Why:** alpha.16 had the READ loop and two-graph substrate, but
  no user-visible path from checked notes to a draft and back into the graph.

- **What:** Acceptance stays host-neutral. The new surfaces are CLI verbs,
  prompt operations, plain files, and additive read-API functions; no UI host is
  required for the checkpoint. **Why:** the client/adapter decision must not
  block text output, and the engine boundary stays testable without trusting a
  rendered pane.

- **What:** This is a checkpoint close, not a formal packaged release. Local
  release metadata still has `pyproject.toml` at `0.1.0a16`, no local
  `0.1.0-alpha.17` tag exists, and release-please remains manual/pre-alpha.
  **Why:** the release playbook treats version bump, changelog, tag, and GitHub
  release notes as release-please-owned; alpha.17 closed as a design-history
  checkpoint over already-merged code.

### 2. Project slice, outline, and canvas projection

- **What:** The canonical project slice is `projects/<name>/outline.md`: an
  ordered markdown list of checked member notes, with BM25-based proposal
  reasoning and line order as the human-editable sequence. **Why:** one plain
  file is enough for membership and order; a separate slice database or
  canvas-to-outline derivation would add sync machinery without adding
  authority.

- **What:** Typed connections are computed, not stored in the outline. A link
  appears when it already exists in a member note's argument-graph `links:` and
  both endpoints are in the current outline. **Why:** alpha.17 consumes the
  argument graph; it does not create project-local duplicate edges that can
  drift from the knowledge graph.

- **What:** Existing canvas rendering now reads the outline when present and
  emits `argument.canvas` as a projection of the same slice. **Why:** the spatial
  view stays a projection, while interactive canvas/workspace editing remains a
  future host-adapter task.

### 3. Draft composition and evidence sets

- **What:** `compose-project-draft` creates `draft.md` from checked outline
  members, using bounded excerpts and one evidence marker per drafted block.
  **Why:** alpha.17's shipped draft path is deliberately small and
  deterministic; it proves the file/evidence/export loop before adding richer
  prose generation.

- **What:** Evidence sets use mint-once opaque IDs (`ev-<8hex>`) and canonical
  inline markers of the form `%%ev: ... items=...%%`. The marker carries the
  ordered item list; the SQLite `evidence_sets` rows are rebuildable derived
  state. **Why:** content-derived IDs would break when items change, and a DB row
  cannot be the recovery source for a plain-file draft.

- **What:** The evidence-set table lands at SQLite `user_version = 6` through
  additive `CREATE TABLE IF NOT EXISTS` DDL, not a new migration function.
  **Why:** alpha.17 adds a new derived table with no old data to preserve; the
  project is still pre-1.0 and does not owe an in-place vault upgrade path.

- **What:** Source-span refs use stable `work_id#^pNNNN`, never citekeys, and
  the reserved `anchors:` frontmatter field stays unused for this contract.
  **Why:** citekeys are mutable display/citation attributes, and splitting one
  evidence fact across both frontmatter and an inline marker would create two
  authorities.

### 4. Verification, export, and review routing

- **What:** `verify-project-draft` rebuilds evidence rows from markers, reports
  unresolved `evidence-incomplete` sets, routes `review_required` multi-hop or
  implicit sets, and runs structural reference/number checks. **Why:** the gate
  proves citation and structure hygiene, not semantic truth; labels remain
  narrow and monotone.

- **What:** `project export --draft` strips internal evidence markers only after
  draft verification passes; unclean drafts refuse with explicit reasons.
  **Why:** draft export should share the project export surface without
  stretching the old paper-plan requirements over a different artifact.

- **What:** PI disposition of an evidence review item is recorded as journal
  state through `resolve-evidence-review`, not by changing authored frontmatter.
  **Why:** alpha.15's meaning-only frontmatter rule still governs the WRITE
  path.

### 5. Draft to graph write-back

- **What:** `promote-draft-passage` extracts a selected passage into a new
  unchecked note, stages/materializes it through the existing write path, and
  adds a plain relative markdown link from the draft. **Why:** insights from a
  draft need to re-enter gap analysis, but draft-origin is provenance and
  journal state, not a new frontmatter verdict.

- **What:** The operation reuses the existing optional `source_id` field when a
  source link is supplied and adds no new note schema field. **Why:** the
  release preserves the alpha.15 rule that frontmatter describes meaning, not
  review maturity.

### 6. Exploration and gate calibration

- **What:** The exploration channel is separate from normal relevance ranking:
  it surfaces uncaptured citation-graph candidates and contrary items, reports
  `mode: mmr-baseline`, and honestly returns empty when there is no candidate.
  **Why:** the product needs an anti-suppression lane without turning absence
  into a fabricated recommendation.

- **What:** Seeded-error calibration extends the existing disposable fixture
  runner, keeping probes inside a throwaway vault and behind
  `production_enabled:false`. **Why:** review-gate efficacy must be measured,
  but a calibration probe must never receive a real run id, commit, export, or
  durable graph state.

### 7. Excluded or still open

- **What:** The thin Obsidian plugin and workspace topology were explicitly
  excluded from alpha.17 and moved to a parallel future track. The host research
  recommends a logically thin Obsidian plugin over the existing loopback HTTP
  transport, but that is not an alpha.17 implementation. **Why:** the text loop
  uses files/read-API/CLI and does not need a client decision to ship.

- **What:** Code execution and code-warranted claims remain outside alpha.17.
  **Why:** code runs in a sandboxed execution chain, not in the rendering client;
  it needs its own security and adversarial-validation gate.

- **What:** Formal release-please release work remains open if alpha.17 needs a
  package/tag rather than a checkpoint record. **Why:** the merged code proves
  the implementation path, while version bump, changelog, tag, GitHub Release
  notes, milestone closure, and parent issue closure are separate release-state
  actions.

---

### Notable decisions and deferrals

| Decision / deferral | Disposition |
| --- | --- |
| Project slice stored as `outline.md` | Adopted; canvas is a projection, not a second authority. |
| BM25-only slice proposal | Adopted; dense retrieval stays benchmark-gated. |
| Evidence marker as canonical store | Adopted; `evidence_sets` is derived/rebuildable state. |
| SQLite `user_version = 6` | Adopted with additive DDL; no new migration function. |
| Source-span refs by `work_id`, not citekey | Adopted. |
| `anchors:` frontmatter reuse | Rejected; evidence markers are the only evidence-set store. |
| New frontmatter verdict/maturity field | Rejected; write-back notes use DB/journal state. |
| Draft export CLI surface | Adopted as `project export --draft`. |
| Exploration algorithm | MMR baseline adopted; facility-location and DPP remain fixture-gated/deferred. |
| Obsidian plugin/workspace topology | Excluded from alpha.17; future parallel track. |
| Code execution | Deferred to its own sandbox/security gate. |
| Formal alpha.17 package/tag | Not cut in this checkpoint. |
