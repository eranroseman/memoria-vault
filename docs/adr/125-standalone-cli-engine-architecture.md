---
topic: decisions
id: 125
title: Memoria is a standalone local CLI + engine
nav_exclude: true
status: accepted
date_proposed: 2026-07-02
date_resolved: 2026-07-02
assumes: [122, 123, 124]
supersedes: [7, 22, 23, 26, 28, 32, 33, 35, 43, 46, 48, 49, 53, 55, 69, 74, 80, 120]
superseded_by: []
---

<!-- cspell:words Typer -->

# ADR-125: Memoria is a standalone local CLI + engine

One of six consolidation ADRs (125–130) that align the corpus with the
alpha.14/15 architecture cut. Each supersedes a batch of earlier decisions and
**carries their surviving invariants forward in its own text**, so a reader
needs the six current ADRs, not the fifty superseded ones. Tombstones on the
superseded files point here.

## Context

ADR-22/26/46/48 built Memoria on the Hermes agent runtime: installed profiles,
board lanes, an MCP policy layer, and Obsidian as the host surface. Alpha.14
cut that runtime out (landed on `main` through #1156: standalone CLI, SQLite
engine ADR-122, DOI enrichment ADR-123, catalog citation authority ADR-124)
but its decision-authority ADR was never written, so the corpus still presents
the Hermes-era architecture as current. Alpha.15 completes the cut with a
clean-slate stack. This ADR is the missing decision authority for both.

## Decision

Memoria is a **standalone local CLI + engine**, single-user, no daemon.

- **Runtime**: Python 3.12+; `uv` distribution (`uv tool install memoria`;
  `pip install -e .` contributor fallback); Typer CLI; stdlib `sqlite3` with
  WAL and FK, **no ORM**; `.sql` DDL gated by `PRAGMA user_version`;
  pydantic-ai as the sole typed LLM runner over OpenAI-compatible endpoints;
  retrieval via SQLite FTS5 + sqlite-vec pending the baseline-gated spike vs qmd (design §10 — the checked-only filter becomes a `WHERE` clause and Node leaves the baseline if the spike clears);
  git CLI for file materialization and journal anchoring.
- **State**: SQLite is the authority for records, operations, queue, journal,
  and verdicts; markdown files are the human corpus; content-addressed blobs
  hold raw payloads and acquired text. This **explicitly overturns ADR-49's
  rejected alternative** ("SQLite as the store: never the source of truth"):
  the split-authority rule — files own meaning, the DB owns verdicts and
  records — keeps the keep-test (die-and-keep-markdown) while giving records,
  queues, and verdicts a transactional home markdown cannot provide.
- **Operations are product code.** Operation manifests/prompts ship in the
  package, are calibrated at build time, and the runner executes only checked
  operations. There is no workspace `capabilities/` tree (supersedes ADR-53's
  patterns-as-vault-data: behavior changes are now PR-reviewed code changes,
  which is a stronger review than a gated content edit). User customization
  goes through `instructions` config, never by authoring operations. ADR-69's
  naming survives: the deterministic layer is "operations," never "agents."
- **Dropped from the product, not deferred**: Hermes (22, 35, 43, 80's
  Hermes-flavored harness), installed profiles and lane/fleet (26, 48, 120),
  the board control plane, MCP-as-required-API (32, 33), the Obsidian-hosted
  policy plugin (28, 31), Zotero-as-authority (05/06, already superseded by
  ADR-124), and the repo-as-install-unit installer with golden-copy restore
  (26, 55, 74) — package reinstall is the restore path for product files.
- **Agent posture carried without the profile system** (the surviving
  invariant of 07/32/46/48): Memoria never grants an agent file, terminal,
  code-execution, or send tools. Any delegated agent — Memoria's worker or a
  bring-your-own agent — is bounded to the read-API and the request envelope
  (ADR-130). Substantive coding stays delegated to external agents (07's
  principle, now the alpha.16 coding-module target).
- **Fail-closed enforcement carried** (the load-bearing lesson of 28: a gate
  that proceeds on its own failure is not a gate): the request envelope,
  checks, and read barrier fail closed on any internal error; a logged denial
  is policy, silence is wiring.
- **Windows-native production and the layered test gates survive unchanged**
  (ADR-64, ADR-29, ADR-44 are not superseded).

## Consequences

- One install command, no external runtime, no always-on process; scheduled
  work is plain CLI invocations under cron/systemd/Task Scheduler.
- The corpus sheds its largest block of dead decisions; readers start here.
- The engineering ADR-22 warned against (durable state, retries, crash
  recovery) is now owned in-house — ADR-127 is where that obligation is paid.

## Alternatives considered

- **Stay on Hermes / any agent framework** — rejected: the framework owned
  state, workflow, and the write boundary; every integrity mechanism had to be
  threaded through it. ADR-22's "never build your own runtime" warning is
  acknowledged and accepted as a cost, bounded by ADR-127's explicit contracts.
- **Rust/Go/TypeScript engine** — rejected: NLI/embeddings/PDF-anchoring/
  scholarly-metadata are Python-native; every other choice embeds Python
  anyway (design §S1).
- **ORM + migration framework** — rejected: the integrity schema is the
  product; single-user scale needs `.sql` + `user_version` only.

## Related

- Design: `scratch/releases/0.1.0-alpha.15/0.1.0-alpha.15-design.md` §0–§S2,
  §S6 (until scratch cleanup; then release notes).
- ADR-126 (knowledge model), ADR-127 (integrity), ADR-128 (epistemics),
  ADR-129 (machine judgment), ADR-130 (surfaces).
