---
topic: decisions
id: 69
title: Operations — name the deterministic layer and its four categories
nav_exclude: true
status: superseded
date_proposed: 2026-06-14
date_resolved: 2026-06-14
assumes: [46]
supersedes: []
superseded_by: [125]
---

# ADR-69: Operations — name the deterministic layer and its four categories

> **Status note (0.1.0-alpha.15):** superseded by [ADR-125](125-standalone-cli-engine-architecture.md). Kept for decision history; current architecture is carried by the consolidation ADR.

## Context

The deterministic, non-LLM layer ([ADR-46](46-seven-layer-architecture.md)) is named
inconsistently. The docs call it both **"engines"** and **"Memoria's deterministic
apps"** — one concept, two words, the textbook ubiquitous-language anti-pattern (DDD).
"engine" is also not plainly self-descriptive (game/search/rules engines abound). The
five components have no shared structure: `engines/ingest/` exists, but the Cluster
engine logic lives inside `mcp/cluster_mcp.py` with no `engines/cluster/`, Search has
no directory at all, and `engines/sweeps/` mixes three different kinds of work. The
ingest entry point is the shape-named `pipeline.py`, and `engines/lib/` is a generic
catch-all. The original alpha.3 design note asked whether the work splits into
"processing/maintenance vs bookkeeping/housekeeping" — four near-overlapping words
that mis-cut the space (maintenance ≈ housekeeping; bookkeeping is a metaphor for
recording). Deriving names from what each component *does*, rather than from the
existing folder, gives a cleaner, self-descriptive vocabulary.

## Decision

Memoria's deterministic, non-LLM layer is named **Operations** (the term "engine" and
the synonym "app" are retired). The contrast with the agent layer is: **you _run_ an
operation; you _delegate_ to an agent.**

Operations group into **four categories, named by what the PI does with each one's
output**:

- **Processing** — builds and serves the knowledge base; the PI **uses** the result.
  (`ingest`, `search`, `cluster`.) Agent-reachable via an MCP facade.
- **Integrity** — detects and repairs correctness/consistency problems; the PI **acts
  on** the findings (cards/alerts). (`verify`/lint detectors, `retraction`, `golden`.)
  Cron/CI-only.
- **Cleanup** — routine, silent tidying/normalizing/archiving; the PI **never sees**
  it. (`reconcile`, retry/stamp.) Cron-only.
- **Telemetry** — records activity and emits metrics; the PI **consults** it on demand.
  (board/telemetry export, `metrics`, session digests, `eval`.) Cron-only.

Each **leaf operation** has **one bare-verb token** (`ingest`, `search`, `cluster`,
`verify`, `lint`) used identically as its proper name, directory, module stem, and CLI
verb. The code tree is restructured by category:
`vault-template/.memoria/operations/{processing,integrity,cleanup,telemetry}/`. Generic
shape-names are retired in the move — `ingest/pipeline.py` → a responsibility name
(`runner.py` or `catalog.py`), `lib/` dissolved, `golden.py` → `golden_restore.py`.

The rename is **decided now but executed as one atomic refactor** (see *When this
matters*), not piecemeal.

## Consequences

- Each term is self-descriptive and non-overlapping; "maintenance"/"housekeeping"
  synonyms collapse and "bookkeeping" becomes the distinct **Telemetry**.
- The four categories line up with two things already true: the **MCP-facade boundary**
  (Processing is agent-reachable; the other three are cron/CI-only) and the
  **surface model** ([ADR-116](116-obsidian-surface-architecture.md)) —
  Integrity → status bar + Action cards, Telemetry → pull dashboards, Cleanup →
  invisible, Processing → the knowledge itself.
- The restructure fixes the structural inconsistencies: it gives **Cluster** a real
  home (logic out of `mcp/cluster_mcp.py`, a thin façade left behind, mirroring
  `ingest_mcp.py`), gives **Search** a directory, and splits the three-category
  `sweeps/` folder.
- **High blast radius.** `engines/` is hardcoded in `tests/conftest.py`,
  `scripts/test.sh`, `scripts/e2e-smoke.sh`, `scripts/install.sh`,
  `tests/test_precommit_schema.py`, and across docs/ADRs — all must move in the same
  change, with `docs-doctor` and the test suite re-run after.
- **Excluded from any find/replace** (false positives): the `memoria-engineer` agent
  profile (a persona, not the layer), qmd's "search engine" (third-party), and the
  `PolicyEngine` class name (decide separately).
- [ADR-46](46-seven-layer-architecture.md) and every doc using "engine"/"deterministic
  apps" must be amended to the new term; this ADR governs the vocabulary, ADR-46 keeps
  the architecture.

## When this matters

The **vocabulary decision** is accepted for alpha.3 so UI work builds on settled terms
(the navigation, dashboards, and docs all reference these categories). The **code/tree
rename** serves engineering clarity, not the alpha.3 "UI build", and carries real risk
— so it is scheduled as a **dedicated refactor pass, sequenced _after_ the docs→source
link convention lands** (the alpha.3 research notes, `open-issues-research` Issue 3c)
so links aren't pinned to paths about to move. Re-judge priority each release cycle.
Cheap, non-structural parts (delete "app" from prose; define "CI invocation") can land
in alpha.3 ahead of the rename.

## Alternatives considered

- **Keep "engine," delete "app."** Cheapest (the folder and ADR-46 already use it), but
  "engine" is not plainly self-descriptive and keeps a mildly overloaded term. Retained
  only as a fallback if the rename churn proves unacceptable.
- **Two buckets — Processing vs Maintenance.** Matches the MCP-facade boundary exactly,
  but lumps "findings you act on" with "records you consult" and "silent tidying",
  losing the distinctions that drive the dashboards.
- **The note's pairing — {Processing+Maintenance} vs {Bookkeeping+Housekeeping}.** Splits
  the two synonyms (maintenance/housekeeping) into different buckets and pairs the two
  genuinely-different ops concepts (recording vs tidying); "bookkeeping" is a metaphor.
- **"service" or "tool" as the umbrella.** "service" implies an always-on RPC daemon
  (wrong for the on-demand + cron mix); "tool" collides with "MCP tool" — a new dual
  vocabulary.
- **Three categories** (fold Cleanup into Integrity). The merge was tempting only because
  "maintenance"/"housekeeping" overlap; with the self-descriptive names "Integrity" and
  "Cleanup" are obviously different work, so four crisp categories read clearer.

## Related

- **Files affected:** `vault-template/.memoria/engines/` (→ `operations/`), `tests/conftest.py`,
  `scripts/test.sh`, `scripts/e2e-smoke.sh`, `scripts/install.sh`,
  `tests/test_precommit_schema.py`, `docs/explanation/engines/` (→ renamed),
  `docs/reference/system-actions.md`
- **Related decisions / Depends on:** [ADR-46](46-seven-layer-architecture.md) (defines
  the layer; its "engine" term is amended here), [ADR-116](116-obsidian-surface-architecture.md)
  (the surface model the categories map onto)
- **Source discussion:** the alpha.3 research notes (`open-issues-research` Issue 2, `naming-and-diataxis-audit`)
