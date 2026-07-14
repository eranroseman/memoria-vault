## alpha.21 - Foundation trust repairs, content-security, and instrumentation skeleton

**Theme:** alpha.21 makes the machinery alpha.20 delivered *true and visible*
before beta.1 builds on it. The engine already claimed attributable, reversible,
detected integrity; alpha.21 pays that claim in enforceable code — a
provenance-honest actor model, a verifiable journal, durable grounds, honest
surfaces — then hardens the content layer against untrusted markdown and plants
the non-backfillable feedback-instrumentation seam. It is a repair-and-harden
checkpoint, not a feature release: no propagation-semantics or edge-parsing
changes, and the four-type knowledge model and control surfaces are untouched.

### 1. Foundation — make the delivered machinery true (F1-F4)

- **What (F1 · provenance & actor integrity, #1361):** every mediated write
  consumes one validated `OperationContext` whose actor is exactly one of
  `pi | agent | operation | integrity`; engine and worker interfaces never
  default a missing actor. A fixed `PROTECTED_OPERATION_ACTORS` map in
  `runtime/worker.py` reserves sensitive operations to a required actor —
  `cascade-rollback`, `record-copi-interview`, `mark-checked`,
  `promote-draft-passage` and peers to `pi`; `trace-integrity-scan` and
  `observe-pi-edits` to `integrity` — enforced by `_require_operation_actor`
  as the first check inside `_run_operation_job`, before any payload
  processing. A wrong-actor job fails with `"{op} requires {label} actor
  authority"` and appends zero `event_log` rows. **Why:** integrity that
  "rests on a trace" is only real if the trace cannot be forged; an agent
  request must not be able to invoke a PI-only destructive operation.

- **What (F2 · journal trust, #1362):** the `event_log` is a hash chain, and
  `memoria journal verify` (`state.verify_journal_chain`) is the one
  authoritative trust-read path — it checks the chain, the live-tip anchor, the
  committed-anchor prefix, and the JSONL export subset. Trust reads consume the
  authoritative event log first. **Why:** a tamper-evident derivation graph is
  worth nothing without a single, callable way to verify it end to end.

- **What (F3 · durability of grounds, #1363):** `memoria workspace backup
  <dir>` verifies and reconciles the journal, then publishes one complete
  manifest-bound snapshot (SQLite, blobs, journal head) outside the live vault;
  `memoria workspace restore <dir>` validates and replays it, requiring
  `--force` while a live database exists; `memoria workspace recover` completes
  an interrupted publish/restore. `memoria doctor` fails when a blob has no
  corresponding backup coverage. All three are PI-only. **Why:** WAL and
  synchronous commits survive a mid-write crash but not a lost disk; the
  keep-set's grounds must be recoverable, and an unbacked blob is a durability
  gap, not a passing state.

- **What (F4 · surface honesty, #1364, folds #1351):** `_emit` never reports a
  success it did not perform; `list --type work` genuinely enumerates catalog
  Works (a distinct code path from frontmatter Concepts); `new-note --mode
  work` is creatable; dead CLI knobs were deleted; and `argument.canvas`
  projection-drift is actually covered by the tracked-projection check (closing
  #1351, where the canvas declared a drift check that `TRACKED_PROJECTION_PATHS`
  did not cover). **Why:** a control surface that claims more than the engine
  does trains the researcher to distrust it; honesty is the surface's only
  load-bearing property.

### 2. Content-security hardening (schema v12)

- **What (CS1 · untrusted-markdown neutralization):**
  `runtime/content_security.py`'s `neutralize_untrusted_markdown` (and its
  `_fragment` variant) mask machine- or third-party-derived markdown before it
  can pose as trusted content — image embeds and raw HTML become inert, links
  and external URLs become non-clickable code spans — applied at the
  operation/knowledge field boundaries (enrichment findings, note-candidate
  bodies, discovered Work titles) and the export choke. **Why:** poisoned input
  can attack through a legitimate read-and-reason path; least-privilege
  allowlists are necessary but not sufficient.

- **What (PR-MC · evidence-to-text hash binding):** an immutable
  `evidence_bindings(id, block_text_sha256)` ledger — insert-only, with
  `UPDATE`/`DELETE` triggers that `RAISE` — binds an evidence marker to the
  exact cited text, so a citation cannot be silently re-pointed at different
  text after the fact. **Why:** provenance-everywhere is only enforceable if a
  marker's binding to its source span is itself tamper-evident.

- **What (PR-CS3 · out-of-band change witness):** a `file_baseline` table
  (`subject_id`, `human_sha256`, `restriction_keys_json`, `observed_at`)
  witnesses foreign edits to human files and restriction-key removal via the
  observe-edit sweep. **Why:** the read barrier must detect changes that arrive
  outside the operation envelope, not just those it mediates.

- **What (#1399 · code-span mask robustness):** the inline-code mask token no
  longer embeds literal `<`/`>`, so the HTML-tag pass can no longer swallow it,
  drop the code-span content, and leave a raw NUL byte in the output. **Why:**
  a content-integrity defense must not itself corrupt legitimate content.

- These advance the runtime schema to `user_version = 12`. The complete
  implementation was reconciled onto `origin/main` after F4's PR had bundled a
  partial CS1-only version at schema v11.

### 3. I1 · feedback-instrumentation skeleton (#1365)

- **What:** `empirical_event.v1` gains `loudness` (`quiet|notice|alert|block`)
  and a boolean `staleness_hit`. A server-side `disposition.v1` journal event
  is emitted from `resolve-attention` with the F1-true actor (via journal
  provenance) and a `request_id` join key — no fabricated client
  `session_id`/`surface`. A `read-observed.v1` validator plus the
  `staleness_hit` field ship as schema plumbing. A shadow-first
  `.memoria/config/feedback.yaml` `production_enabled` flag (defaults false;
  gates *acting* on the signal, never recording) is surfaced read-only in
  `doctor bundle`. **Why:** disposition telemetry is non-backfillable — every
  day without the seam is permanently lost calibration baseline — but the
  skeleton establishes the honest seam, not a dashboard.

- **What (deferred to beta.1):** the full I1 package — dashboard,
  payoff-attribution, calibration, client-side empirical events with real
  session/surface, wiring the other decision operations, and a real read-path
  `staleness_hit` sink. The skeleton deliberately does *not* emit from
  `answer-query`: a read that appends a journal event rewrites the git-tracked
  `.memoria/journal-head` anchor, and a read must not mutate tracked state.

### 4. Docs migration and seed repair

- **What (#1366):** the pre-`main` corpus doctrine was folded into the published
  Diátaxis `docs/` tree (tutorials / how-to / reference / explanation), and the
  `docs/superpowers/` working records (specs, plans) became the tracked-but-
  unpublished design workspace. **Why:** the current system is described in
  `docs/`; `design-history/` is the frozen record of how it got there.

- **What (#1350):** the seeded Obsidian plugin shipped `main.js` without
  `schema.js` and failed at load; the seed now ships the plugin's runtime
  files as an exact set. **Why:** the default adapter is useful only if a fresh
  workspace's plugin actually loads.

### 5. Verification gate

- **What:** `scripts/verify` was widened from a contract-only pytest roster to
  also run the `runtime`, `package`, and `floor` levels (only the
  network-dependent `live` level stays out). CI defers the `runtime` level
  (`VERIFY_CI` in `verify.yml`): it holds environment-sensitive tests
  (fsync/filesystem) that pass locally but can fail on CI runners — to be
  hardened before CI gates them (tracked in #1480). The floor golden-digest
  determinism bug — date-only fields were not redacted, so the golden digests
  re-drifted every calendar day — was fixed with a `<DATE>` redaction. **Why:** the widened
  gate immediately surfaced drifted or stale tests that the contract-only gate
  had hidden (a schema-version assertion, a stale seed-set assertion), which is
  exactly the blind spot the widening exists to close.

### 6. Deferred scope

- **Beta.1 blockers** stay deferred behind their empirical or design blockers:
  retrieval-default promotion, canvas/workspace topology, SRD/code-module
  planning, PI evidence review, onboarding seed corpus, the feedback dashboard
  and full I1 package, deep-work/gate topology, multi-device topology, and raw
  empirical-dataset packaging.
- **Runtime-level CI gating** waits on hardening the environment-sensitive
  runtime tests (#1480).
- **Remote API** — remote bind, CORS, OAuth, cookies, SSE, WebSockets, and
  multi-user service behavior — remains out of scope.

### Release management

- The Python package version is `0.1.0a21`.
- No formal tag or GitHub Release is cut; release-please remains
  `workflow_dispatch`-only.
- The alpha.21 working plans under `docs/superpowers/` are retired as active
  scratch at checkpoint close after their accepted decisions are folded into
  this chapter and `arcs.md`; they remain tracked design evidence, not a frozen
  history chapter.
