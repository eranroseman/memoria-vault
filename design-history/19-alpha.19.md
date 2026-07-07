## alpha.19 - query substrate and code-output lane

**Theme:** alpha.19 turns the beta.1 query/code gaps into a source-install
checkpoint. It adds derived passage tables, optional vector packaging, a
fail-closed code runner gate, and computed evidence without changing BM25 as the
default answer path.

### 1. Bundle root rename

- **What:** The generated full-text folder is now `fulltexts/`; the document
  schema label remains `type: fulltext`. **Why:** generated full text is a
  collection root like `digests/`, while the singular type names the artifact
  kind.

### 2. Query substrate

- **What:** The SQLite schema is `user_version = 8` and fresh vaults create
  `passages`, `passage_fts`, `passage_vec`, `file_index_state`, and
  `concept_edges`. **Why:** lexical, vector, and graph retrieval candidates need
  one local derived store with rebuildable state.
- **What:** v7 databases fail fast instead of migrating. **Why:** the project is
  still pre-1.0 alpha; derived query state is cheaper and safer to rebuild from
  markdown/catalog state than to migrate.
- **What:** query-time refresh updates changed passage rows, and verdict/status
  changes cascade to `passages.check_status` in the same transaction. **Why:**
  checked-only retrieval must not depend on a daemon or stale copied status.

### 3. Retrieval activation

- **What:** BM25 remains the selected answer substrate. FTS5, deterministic
  hash-vector, and hybrid/RRF candidates exist for fixture comparison, while the
  dense production capability fails closed unless the optional `sqlite-vec`
  extra is installed and loadable. **Why:** alpha.19 builds the substrate but
  does not claim dense/vector retrieval is better than the active baseline.

### 4. Code-output lane

- **What:** Project code outputs have `code-artifact` markdown records under the
  project, companion `src/` and `outputs/` folders, and DB rows in
  `code_artifacts`. Code runs are recorded in `code_runs` with argv, cwd,
  sanitized env names, input/output hashes, stdout/stderr hashes, sandbox
  backend/profile, state, and timestamps. **Why:** code outputs need durable
  provenance, not transcript-only claims.
- **What:** the single execution gate is
  `runtime/code/runner.py::execution_availability(vault)`. It returns
  `unsupported` until a Linux/WSL `bwrap` proof passes. **Why:** partial code
  execution without network/secret isolation is worse than no execution.

### 5. Computed evidence

- **What:** evidence markers accept `code-warrant:<run_id>:<artifact_id>:<sha>`
  items and derive `type: computed`. Computed evidence is complete only while
  the referenced run succeeded and the current output hash still matches. **Why:**
  code execution warrants the structural fact that an output came from a
  recorded command and inputs; it does not make the research claim true.

### Release management

- The Python package version is `0.1.0a19`.
- No formal tag or GitHub Release is cut; release-please remains
  `workflow_dispatch`-only.
- The alpha.19 scratch ExecPlan is retired at checkpoint close.
