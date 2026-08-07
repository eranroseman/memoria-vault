---
title: Glossary
parent: Reference data model
nav_order: 5
grand_parent: Reference
---

# Glossary

Term definitions for Memoria, organized by domain. One definition per term; disambiguation noted where a term has multiple senses.

Memoria is a phase-gated personal knowledge-production tool for one
researcher; these are its canonical terms and usage rulings.

For the short version of the core terms, see [Home](../../README.md).

---

## System

### Agent

A model-backed process doing work. Memoria exposes agents through
the standalone CLI/engine and optional adapters; it does not ship installed
profile packages or lane assignments.

### autoresearch

The self-improvement loop (fixed harness, one metric, keep-or-discard) applied to Memoria's own instruments — detectors, prompts, gates — never to the knowledge they assess. Planned — see [Roadmap](../../roadmap.md).

### Catalog

The SQLite record of every source the vault knows: Works, their
identifiers and provenance, and the work-graph edges discovered for
them. Sources enter the catalog before any knowledge work. See
[Ingest routing](../pipelines-and-io/ingest.md) for how sources arrive.

### Co-PI

The research-partner role exposed through the standalone
`memoria ask` / `memoria project ask` commands.

### generated

OKF v0.2 provenance frontmatter (`{ by, at }`) stamped by the
trusted writer at staging; `by` uses the OKF actor grammar. Records
authorship, not judgment.

### Grounding

The inspectable structure connecting a claim to the sources and
reasoning that support it. All trust in Memoria lives in grounding
structure, never in any author — human or machine
(`src/memoria_vault/runtime/grounding/`). See
[Intellectual foundations](../../explanation/rationale/foundations/intellectual-foundations.md).

### Knowledge Bundle

An OKF unit of distribution: the plain-file tree holding the researcher's knowledge, separable from the `.memoria/` engine state. The format ships; the export and import path is planned — see
[Roadmap](../../roadmap.md).

### Memoria

The whole system: the OKF knowledge bundles, capability manifests,
standalone CLI/engine, policy/audit layer, workspace DB, and `.memoria/`
runtime state.

### memoria doctor

The diagnostic command family (`memoria doctor`,
`memoria doctor bundle`, `memoria doctor self-test`): read-only checks
of installation, configuration, runner reachability, and bundle health.
Its one writing member is `memoria doctor --repair`, which restores
runtime scaffold files and missing view preferences. See
[Installer](../system/installer.md) and
[Failure modes](../system/failure-modes.md).

### Open Knowledge Format (OKF) {#open-knowledge-format-okf}

The plain-files bundle format Memoria targets, at **v0.2**: a self-contained, tool-agnostic Knowledge Bundle readable without Memoria present. The vault (excluding `.memoria/`) is one OKF bundle; each project is a nested one.

### Operation

A checked capability manifest plus runner behavior invoked by
the CLI/engine. Operations compute and propose; the PI decides. The shipped
operations are listed in [Operations](../commands-and-transports/operations.md).

A **Pattern** is a package-owned prompt operation
([standalone engine with operations as product code, no agent tools](https://github.com/eranroseman/memoria-vault/blob/main/design-history/arcs.md))
executed through `memoria operation run`.

### PI

The human principal investigator who owns and runs the vault. Makes
every triage and disposition decision; promotion is the structural gate
those decisions feed, not a per-write approval loop. Single-user by
design.

### Provenance

The umbrella term for recorded origin, in three senses: the OKF
frontmatter fields on Concepts ([generated](#generated),
[sources](#sources), [verified](#verified)), stamped by the trusted
writer and never reconstructed; catalog field provenance — the
per-field record of which provider won a [Work](#work)'s value, kept
in the `field_provenance` table
(`src/memoria_vault/runtime/schema.sql`); and pattern provenance — the
record of which AI-research design patterns Memoria borrowed, adapted,
referenced, or ignored, and why
([Pattern provenance](../evidence-and-integrations/pattern-provenance.md)).

### Read API

The engine's verdict-tagged read surface: the registered read
actions served over CLI, local HTTP, and MCP
(`src/memoria_vault/engine/surface_contract.py`). All but one
registered action are reads; the sole write action, `operation.run`,
queues an operation request rather than writing directly. Surfaces
such as the Cockpit compose over it. See
[Engine read API](../commands-and-transports/read-api.md).

### sources

OKF v0.2 provenance entries derived from derivation inputs at
staging, or authored for external material. The portable face of grounding.

### Standalone runtime

The `memoria` CLI, SQLite state, worker operations,
runtime policy, and file workspace. PI intent enters through the CLI or
observed file edits; optional adapters use the same contracts without owning
runtime state.

### Toulmin roles

The six argument components (Claim, Grounds, Warrant, Backing,
Qualifier, Rebuttal) that type the knowledge graph and its consequence
propagation. Three of them ship today as `links:` relations —
`warrant`, `qualifier`, and `rebuttal`, listed in
[Frontmatter fields](frontmatter.md#links-and-catalog-resources) — and
the typed consequences they carry propagate on a change. Typing the
whole knowledge graph by all six roles is planned — see
[Roadmap](../../roadmap.md).

### Trusted writer

The single runtime component that creates, stages, and promotes
Concepts, and the only one that stamps provenance: `generated` and
`sources` at staging, `verified` at promotion
(`src/memoria_vault/runtime/trusted_writer.py`). Operations never write
Concepts directly. One piece of runtime machinery writes past it: when
a typed consequence propagates, the propagation labeler
(`src/memoria_vault/runtime/propagation.py`) sets exactly `stale` and
`consequence` on an affected Concept's frontmatter.

### verified

OKF v0.2 confirmation events (`{ by, at }`) stamped at
promotion; a projection of engine judgment state, stripped on re-staging.
Not a field name to reuse for other meanings.

### Workspace

The runtime vault root containing `notes/`, `hubs/`,
`projects/`, `digests/`, `fulltexts/`, `inbox/`, `system/`, and `.memoria/`.
Optional editors open this root; the top-level bundle roots are the checked
corpus homes.

---

## Surfaces and navigation

### Cockpit

`memoria cockpit` (registry row `cockpit.read`), a shipped
read-only composer over registered read actions: the deep screen (`--project
<path>`, six fixed panels) or the triage screen (`--triage`: worklist /
review / flow). It prints a static text photograph, or the same payload via
`--json`; it holds no state and never writes.

### Maintenance

A planned optional-adapter weekly structural-debt surface:
Drift watch, loose ends, queue state, and "new this week". Today, its source
state is available separately through request/attention commands, linter
output, logs, and corpus reads; no combined Maintenance view ships.

### Navigator rail

A planned optional-adapter navigation model
([thin read-API surfaces over one engine, PI direct access preserved](https://github.com/eranroseman/memoria-vault/blob/main/design-history/arcs.md)):
a **Now** band — what is waiting on you right now (your Inbox action
queue, open integrity flags, and a health-band count of open `flag` /
`alert` attention projections) — over a **Places** band of durable corpus
homes (Library: `digests/`, `fulltexts/`, `bibliography.bib`; Knowledge:
`notes/`, `hubs/`; Project: `projects/`). It requires no persisted
navigation note. The standalone CLI does not render it. Planned.

### Queue

The **Inbox** (`projection: attention`): the shipped file-backed
daily attention surface, read through CLI/read-API views. A planned rail reaches
it from **Now -> Action queue**. It shows open attention projections such as
`candidate`, `gap`, and `work-prompt`; clearing it to empty is the goal.

### System dashboard

A read-only view over metrics, request state, attention
state, or linter findings. The standalone baseline does not ship `system/dashboards/*.md`;
`inbox/` and CLI request/attention views carry the action surfaces.

---

## Board and delegation

### Ceiling

The maximum write scope a policy grants, in either of two places: an
operation manifest's capability ceiling, or the write scope an optional
adapter policy grants. Request payloads may narrow a ceiling in either
sense, never widen it: a manifest's declared `allowed_paths` and
`allowed_tools` refuse a payload that reaches past them, the same way
an adapter policy's `allow.tools` is a hard ceiling for non-direct
tools.

### Dispatcher

Dispatcher behavior lives in the local worker queue:
CLI commands, scans, and scheduled tasks create request rows, and the worker runs
pending jobs.

### Handoff payload

One idempotent map-proposal block the [Linter](#linter) mints from a
current hub-threshold finding, for the PI to act on; `hubs/` stays
PI-curated. See
[System action operations](../commands-and-transports/system-actions-operations.md).

### Runner

The model-provider execution backend resolved for one prompt
operation invocation (test vs. live mode, provider, model, base URL); see
`resolve_operation_runner` in [Operations](../commands-and-transports/operations.md).
Distinct from the **worker** (the request-dispatch loop that runs both
prompt and deterministic operations) and the **engine** (the whole
verdict-tagged read/write API surface, `src/memoria_vault/engine/`).

### Sweep

A scheduled, deterministic maintenance pass over the catalog or
corpus — the retraction sweep and the [Linter](#linter), under
`memoria_vault.runtime.sweeps` — invoked directly by a manual or
operator-managed schedule rather than through a worker request row;
the retraction sweep writes its findings straight into the Inbox.
Distinct from the worker's `integrity-sweep`: `memoria workspace
check` calls `run_integrity_sweep`
(`src/memoria_vault/runtime/worker.py`), which queues
integrity-check operations as request rows via
`enqueue_integrity_sweep`, then runs them itself. See
[Sweeps](../pipelines-and-io/sweeps.md).

### Task/request {#task-request}

A unit of work represented by a SQLite request row. Attention
projections are PI-facing views over work that needs review.

### Worklist

The batch surface for high-cardinality decisions: instead of one
attention item per row, like decisions queue into one `system/worklists/` batch
where each `projection: worklist-item` row has a `decision` field the PI can
sweep in any editor or adapter view.

---

## Notes and lifecycle

### Attention projection

A file-backed Inbox projection (`candidate`, `gap`,
`flag`, `alert`, `work-prompt`) carrying PI-facing work. Its current state is
in `inbox/*.md`; it is not a durable Concept. SQLite holds associated
request/control history, and per-machine journal JSONL files are derived
synchronization exports.

### Card

The read/render form of an attention projection: `read_attention_card`
(`GET /attention/card`) returns one Inbox item's fields as a single payload for
a surface to display. Not a separate durable type — it reads the same
`inbox/*.md` file the Attention projection entry above describes.

### Check status

The runtime read-state verdict for Concepts and catalog Works:
`unchecked`, `checked`, or `quarantined`. It lives in SQLite/read API
surfaces, not Concept frontmatter.

### Concept

The umbrella name for every typed document Memoria manages
(`note`, `hub`, `project`, `digest`, `fulltext`, `code-artifact`): YAML
frontmatter declaring a schema-backed type, followed by a Markdown body. See
[Document types](document-types.md) for the full roster and folder homes.

### Disposition

The recorded PI verdict on machine-proposed content: a `disposition.v1`
journal event (`decision`: `accept`, `reject`, `edit`, `defer`,
`override`, or `abandon`) appended at PI resolution call-sites such as
`resolve-attention` and `mark-checked`. One of the decision kinds the
PI owns, with [Triage](#triage); [Promotion](#promotion) is the gate
they feed. See
[Empirical events](../control-and-policy/empirical-events.md#disposition-call-sites).

### Document type

One of the Concept types defined in
`.memoria/schemas/types/`; the full roster, categories, and folder homes are in
[Document types](document-types.md).

### Hub

A checked `hub` Concept in `hubs/` aggregating a topic's
members and links. Machine-curated hub changes are suggestions until the PI
adopts them.

### Ingest

The pipeline stage that brings an external source into the
[Catalog](#catalog): capture writes an unchecked catalog row plus raw
and extracted-text blobs, and enrichment checks the row once required
DOI providers and retraction checks pass. See
[Ingest routing](../pipelines-and-io/ingest.md).

### links (frontmatter)

The authored kind of connection: `links:` frontmatter on Concepts,
written by the PI or proposed by operations, with its relation
vocabulary specified in
[Frontmatter fields](frontmatter.md#links-and-catalog-resources).
Distinct from given [Work-graph edges](#work-graph-edge); the
distinction and its rationale are explained in
[Wikilink and link conventions](wikilink-and-link-conventions.md).

### loudness

The urgency band on an attention card's frontmatter: `quiet`,
`notice`, `alert`, or `block`
(`src/memoria_vault/runtime/attention/inbox.py`, and specified in
[Empirical events](../control-and-policy/empirical-events.md#enum-values)).
`block` is pull-only: an open block card pauses delegation and
review-gated promotion until the PI resolves it
(`src/memoria_vault/runtime/attention/loudness.py`).

### Promotion

The review-gated transition where staged content becomes checked
knowledge once trusted-writer checks pass — not a claim the PI approved
the content as true, and not a file move. The
[Trusted writer](#trusted-writer) stamps `verified` at this moment; an
open `block` card pauses review-gated promotion. See
[Promotion and the write boundary](../../explanation/knowledge/promotion-and-gated-zones.md).

### Staging

The trusted-writer step that writes generated content into
`.memoria/staging/` with `generated` and `sources` provenance stamped,
ahead of worker checks; re-staging strips `verified`. Not
git staging, and distinct from the unchecked catalog staging
[Ingest](#ingest) performs before enrichment checks a row. See
[Promotion and the write boundary](../../explanation/knowledge/promotion-and-gated-zones.md).

### State

Not a field name on its own; use the specific field. A Concept's
read verdict is **`check_status`** in runtime state; request state lives in
SQLite. Prefer the precise field name over a bare "state".

### steering.md {#steering-md}

The vault-root watch/mute override: `## Watch for` bullets boost and
`## Muted` bullets suppress discovery-ranking relevance tokens, on top
of steering derived from active projects, hubs, and open question notes.
PI-authored (`memoria steering edit`); operations read the derived
effective steering, never this file directly. See
[Memory substrates](../pipelines-and-io/memory-substrates.md).

### Triage

The PI's review of Inbox attention projections, resolved through
`memoria attention resolve` (`--apply`, `--reject`, or `--defer`); every
resolution logs a disposition for trust and attention metrics. Also the
name of the Cockpit `--triage` screen (worklist / review / flow) that
surfaces the queue. See
[Work the action queue](../../how-to-guides/inbox/work-the-action-queue.md).

### vocabulary (system/vocabulary.md) {#vocabulary}

The PI-editable controlled-vocabulary artifact governing catalog Work
`research_area`/`methodology` metadata and claim-bearing note `topics`,
which draw from the same `research_area` list. Distinct from the
everyday word: when docs say "the vocabulary", they mean this artifact.
See [Vocabulary](vocabulary.md).

### Work

A catalog source's SQLite record (title, identifiers, provenance,
`work_id`); not a markdown Concept type. A Work's only file-backed keep-set
presence is its `digests/<work_id>.md` digest and `fulltexts/<work_id>.md`
reproduction. Human interpretation of a Work lives in a `note` with `mode:
work`.

Memoria ships no cross-Work identity calibration floor or automatic
merge decision; a future near-tie rule may raise an Inbox `flag` for PI
review.

### Work-graph edge

The given kind of connection: a `work_graph_edges` SQLite row
(`src/memoria_vault/runtime/schema.sql`) discovered for catalog Works —
not Concept frontmatter. The `relation_type` roster and the contrast
with authored links are specified in
[Wikilink and link conventions](wikilink-and-link-conventions.md).

---

## Policy and audit

### Actor Authority Guard

The enforcement mechanism that runs first inside every worker
operation dispatch, checking whether the request's actor (`pi`,
`agent`, `operation`, `integrity`) matches that operation's required
actor when one is declared; a mismatch refuses the job outright —
zero `event_log` rows are appended — rather than logging and allowing
it. See
[Control plane reference](../control-and-policy/control-plane.md#actor-authority-guard).

### Audit log

The append-only JSONL trail of every policy decision at
`system/logs/audit.jsonl`. It feeds tamper checks and may feed a planned
audit-log view.

### Detector

One structural check inside the [Linter](#linter): deterministic,
over corpus structure only. The verdict band is a rollup over the
detectors. See
[Linter: detectors and auto-fix](../analysis-and-surfaces/linter.md).

### Empirical event

A typed, allowlisted telemetry payload for self-use measurement:
submitted through the `empirical-event-record` operation and stored
as a `telemetry_events` row in `.memoria/memoria.sqlite`
(`src/memoria_vault/engine/empirical_events.py`), never in the
[event_log](#event_log). The payload roster and enums are specified
in [Empirical events](../control-and-policy/empirical-events.md).
Distinct from the [Audit log](#audit-log) (policy decisions) and the
[Journal](#journal).

### event_log {#event_log}

The SQLite table holding the authoritative, hash-chained journal of
engine state changes, such as operation-request evidence, PI
dispositions, and evidence mints
(`src/memoria_vault/runtime/schema.sql`). One of three observability
trails: `event_log` is the source of truth for what operations did,
the per-machine [journal](#journal) JSONL files are its derived
export, and the [Audit log](#audit-log) is the separate write-gate
policy-decision trail. Distinct from
[Empirical event](#empirical-event) payloads, which land in the
unrelated `telemetry_events` table instead. See
[Telemetry & logs](../pipelines-and-io/telemetry.md).

### Journal

The append-only, hash-chained record of engine state changes: the
journal proper is the chain kept in the [event_log](#event_log)
SQLite table, enforced by its append-only triggers and checked by
`memoria journal verify` (`src/memoria_vault/cli.py`). The
per-machine `.memoria/journal/<machine>.jsonl` files are its derived
export for multi-machine synchronization and recovery —
reconstructible, never the source of truth. See
[Backup and recovery](../system/backup-and-recovery.md).

### Linter

The deterministic structural detector suite over the corpus: it
checks structure (links, frontmatter, thresholds), never knowledge
content, and rolls its detectors up into the PASS / REVIEW / FAIL
verdict band. See
[Linter: detectors and auto-fix](../analysis-and-surfaces/linter.md).

### Peer-reviewer

The independent, skeptical verification posture
(`posture: peer-reviewer`) on the judgment-based prompt operations
`analyze-claims`, `check-falsifiability`, and `red-team-argument`:
flag, don't fix — a candidate is checked for soundness, not just
facts, and findings never become automatic fixes. The Verdicts table
below names it, alongside deterministic operations, as a setter of
the advisory `agent_recommendation` verdict (`inconclusive` /
`issues-found` / `clean`); advisory only — the PI decides. See
[The Peer-reviewer](../../explanation/execution/operation-postures/peer-reviewer.md).

### Policy gate

Optional adapter decision shim: returns `allow` /
`allow_with_log` / `deny` / `dry_run`, appends to the audit log, and fails
closed when adapter policy is missing. See [Policy gate](../control-and-policy/policy-mcp.md).

---

## Verdicts

| Name | Values | Set by | Scope |
| --- | --- | --- | --- |
| `agent_recommendation` | `inconclusive` / `issues-found` / `clean` | Peer-reviewer / operations | advisory only |
| verdict band | `PASS` / `REVIEW` / `FAIL` | Linter operation | structural rollup over the detectors — the rollup rule is owned by [Linter: detectors and auto-fix](../analysis-and-surfaces/linter.md) |
| `certainty` | `confident` / `likely` / `unsure` | proposing agent | calibrated confidence on an attention projection. Distinct from the note-frontmatter `certainty` enum (`reported` / `contested` / `unknown` / `hypothesized`), the PI-set epistemic status of a claim — see [Frontmatter fields](frontmatter.md). |

---

## Related

- Frontmatter fields these terms name: [Frontmatter fields](frontmatter.md)
- The document types referenced throughout: [Document types](document-types.md)
- Request-control terms: [Control plane reference](../control-and-policy/control-plane.md)
