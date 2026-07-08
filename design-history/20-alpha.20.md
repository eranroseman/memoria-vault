## alpha.20 - contract spine and surface expansion

**Theme:** alpha.20 turns the standalone engine's three control surfaces into
drift-checked contracts. CLI remains the human/script surface, loopback HTTP
becomes precise enough for editor adapters, and MCP-stdio becomes precise
enough for agents without moving state out of the engine.

### 1. Surface contract spine

- **What:** `engine/surface_contract.py` is the data-only registry for public
  surface actions: status, operations, requests, attention, Concepts, Work,
  journal, project slice/draft, exploration, and `operation_run`. The registry
  feeds or guards OpenAPI, MCP tool descriptions, CLI help, and reference docs.
  **Why:** alpha.19 had the right thin surfaces, but their contract lived in
  hand-written docs and duplicated route/tool/command lists.
- **What:** the registry is not a dispatcher, plugin framework, or new typed
  wrapper layer. Surfaces still call the engine API directly. **Why:** the deep
  interface remains the engine boundary; the registry exists to detect drift,
  not to become a second implementation.

### 2. Local HTTP hardening

- **What:** `memoria serve --http --read-scope <path>` sets a startup maximum
  read scope; per-request scope may narrow it but cannot widen it. The HTTP
  server now returns adapter-grade `400`/`401`/`404`/`405`/`413` responses,
  serves `/openapi.json`, and exposes journal, journal-event, project-slice,
  project-draft, and exploration reads. **Why:** editor plugins need stable
  local semantics, not a best-effort debug endpoint.
- **What:** HTTP remains loopback-only. No CORS, cookies, OAuth, SSE,
  WebSockets, remote bind, or hosted API surface is added. **Why:** alpha.20 is
  an editor/agent integration checkpoint, not a remote-product release.

### 3. MCP and CLI polish

- **What:** MCP gains registry-derived descriptions and the missing scoped
  read tools for project slice, project draft, and exploration. MCP remains an
  optional extra; importing `memoria_vault` does not import FastMCP. **Why:**
  users may bring an agent through MCP, but the agent surface must stay closed
  and scoped.
- **What:** the CLI gains clearer shared-surface help, `memoria surface schema`,
  and `memoria new note|hub|project` writes from code-owned field contracts
  instead of seeded markdown templates. **Why:** CLI is still the broadest local
  maintenance surface, but alpha.20 removes unused template files from the
  runtime seed instead of preserving them for drift tests.

### 4. Empirical events

- **What:** `engine/empirical_events.py` defines `empirical_event.v1` with
  strict allowlist validation, controlled enums, required fields per event type,
  body-text/path rejection, and a client-generated `event_id`. The
  `empirical-event-record` operation stores accepted events through the journal
  path and deduplicates replay with
  `idempotency_key=empirical-event:<event_id>`. **Why:** beta.1 blocker
  decisions need empirical use data, but the first step is private measurement
  plumbing, not analytics.
- **What:** dashboards, payoff attribution, and survey tooling are deferred.
  **Why:** no useful dashboard exists before real interaction events exist.

### 5. Obsidian proof adapter

- **What:** `packages/memoria-obsidian/` is the source package for a minimal
  proof adapter, and `memoria init` installs its built release files into new
  workspaces at `.obsidian/plugins/memoria-obsidian/` with default Obsidian core
  settings. The plugin uses SecretStorage for the bearer token, stores only
  token presence in settings, connects to loopback HTTP, renders
  status/attention/Concept reads, queues operations through `/operation/run`,
  spools offline events, and records empirical events through the same operation
  path. It writes no Memoria-owned Concepts, projections, journal files, or
  SQLite state directly. **Why:** Obsidian is the intended default human editor,
  so a fresh workspace should open with the safe Memoria adapter already present
  while still keeping the engine as the source of truth.
- **What:** `memoria init --no-obsidian` skips the `.obsidian/` seed while
  leaving the default unchanged. **Why:** Obsidian is the intended default
  editor, but server-side tests, non-Obsidian users, and minimal workspace
  fixtures need a first-class opt-out instead of deleting seeded files by hand.
- **What:** the provenance doctor now allows only the seeded Memoria Obsidian
  files plus the source package, while still banning extra plugins, hidden
  `.memoria/plugins`, and legacy adapter code paths. **Why:** the default
  adapter is useful only if it remains narrow and auditable.

### 6. Package seed pruning

- **What:** `vault-template/` is retired. The package now ships the default
  workspace seed under `memoria_vault.product.workspace_seed`: schemas, provider
  config, pre-commit hook, seeded-error bundle, prompt preamble, steering,
  vocabulary, `.gitignore`, Obsidian core settings, and the built Memoria
  Obsidian plugin. `memoria init` creates writable skeleton directories from
  `folders.yaml`, copies the Obsidian defaults, and regenerates projections.
  **Why:** the old template preserved empty directories, historical dashboards,
  markdown eval tasks, note templates, broad adapter payloads, cron wrappers,
  and other files mainly so drift checks could keep finding them. The old
  dashboard/template and design-system drift detectors were removed; remaining
  checks now either validate the actual seed or assert deleted payload classes
  stay absent.
- **What:** the package seed is intentionally exact: `.githooks/pre-commit`,
  `.gitignore`, `.memoria/config/providers.yaml`,
  `.memoria/eval/alpha15-seeded-errors.json`,
  `.memoria/patterns/_preamble.md`, `.memoria/schemas/**`,
  `.obsidian/app.json`, `.obsidian/core-plugins.json`,
  `.obsidian/community-plugins.json`,
  `.obsidian/plugins/memoria-obsidian/{manifest.json,main.js,styles.css}`,
  `steering.md`, and `system/vocabulary.md`. Generated files such as
  `index.md`, `bibliography.bib`, `system/manifest.jsonl`, SQLite state,
  journals, indexes, blobs, and content directories are created by
  `memoria init` or runtime code. **Why:** this keeps the shipped seed tied to
  actual runtime/editor readers instead of carrying empty or historical
  workspace artifacts.

- **What:** the sandbox remains the inspection environment for a non-Python
  runtime vault, but it is produced by installer/CLI initialization instead of
  copying a source template. **Why:** the value is in inspecting a real deployed
  vault, not in maintaining a second source scaffold.

### 7. Deferred scope

- **Dedicated agent app:** deferred until Obsidian+MCP proves unable to provide
  understandable approval flows, multiple editors need one complex shared UI,
  plugin+MCP setup itself blocks adoption, or a client app can stay state-free
  over the same contracts.
- **Beta.1 blockers:** retrieval-default promotion, canvas/workspace topology,
  SRD/code-module planning, PI evidence review, onboarding seed corpus, feedback
  dashboard, deep-work/gate topology, multi-device topology, and raw empirical
  dataset packaging stay deferred behind their empirical or design blockers.
- **Remote API:** remote bind, CORS, OAuth, cookies, SSE, WebSockets, and
  multi-user service behavior remain out of scope.

### Release management

- The Python package version is `0.1.0a20`.
- No formal tag or GitHub Release is cut; release-please remains
  `workflow_dispatch`-only.
- The alpha.20 scratch ExecPlan is retired at checkpoint close after accepted
  decisions are folded into this chapter and `arcs.md`.
