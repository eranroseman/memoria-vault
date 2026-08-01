---
title: Roadmap & status
nav_order: 6
permalink: /roadmap/
---

# Roadmap & status

The canonical record of scope and readiness is GitHub: the
[milestones](https://github.com/eranroseman/memoria-vault/milestones) (a
milestone is a release) and the
[open issues](https://github.com/eranroseman/memoria-vault/issues). This page
is the published decoder for the release vocabulary and workstream codes the
docs use, plus a dated status snapshot. When this page and the milestone
disagree, the milestone wins.

*Snapshot date: 2026-08-01.*

---

## Where the project stands

Memoria is in the **v0.1 alpha source-install** phase: the installer and CLI
engine are being validated as a standalone local product, installed from
current `main` rather than a release artifact. alpha.22 is the latest closed
checkpoint; the formal package/tag release gate remains open. What is not
working today:

- **Release-candidate validation is still pending** — the offline runtime gate
  replays capture, enrich, digest, ask, project writing/export, recovery, and
  seeded-error evidence (`scripts/verify`), but the RC still needs a live
  provider/package run before release.
- **Mobile capture is not available** — no push channel ships; inbound capture
  from a phone is out of scope for beta.1. See
  [Architecture](explanation/architecture/README.md#interaction-channels).
- **No autonomous code-experiment loop** — provenance-tracked code experiments
  are future work.
- **Broad writability scoring is not implemented** — the current alpha baseline
  has structural draft verification and project export readiness, but it does
  not decide whether developed claims are ready to become prose.
- **Single-user only** — team and multi-user review are out of scope by design.
- **macOS is not supported** — only Linux (including WSL2) and Windows are
  tested.

Throughout the docs, unshipped capabilities are marked *planned* or *deferred*;
nothing implies they work before they ship.

## Release vocabulary

| Marker | Meaning |
| --- | --- |
| `alpha.N` (e.g. alpha.15, alpha.22) | Closed internal checkpoints on the way to beta.1. A page saying "shipped in alpha.17" means the capability is on `main` today. |
| `beta.1` | The current milestone: the first coherent end-to-end release. |
| `beta.2` | The deferral register — work deliberately parked until after beta.1 (see below). |
| `B1` / `B2` | Scope-tier tags inside workstream notes: B1 lands in beta.1, B2 is deferred. |

## Workstream decoder

Docs pages cite work packages by code ("Planned beta.1 — K1"). The codes group
into lettered workstreams; per-package readiness lives in the
[milestone](https://github.com/eranroseman/memoria-vault/milestones), not here.

| Code | Workstream | What it covers |
| --- | --- | --- |
| F1 | Provenance & actor integrity | One actor vocabulary; every mediated mutation carries a validated operation context through the trusted-writer seam. |
| F2 | Journal trust | Journal chain verification and the `event_log` substrate behind trust paths. |
| F3 | Durability of grounds | Backups for blobs and operational ledgers; durable (fsync, atomic-replace) writes. |
| F4 | Surface honesty | Honest failure output, real catalog enumeration, doc–code contradiction fixes. |
| G1 | Migration machinery | Numbered schema migrations so upgrades stop hard-failing. |
| G2 | Edge module + live concept edges | One owner for the relation roster and edge parsing; persistent `concept_edges`. |
| G3 | Stable identity | ULID internal keys, path-facing OKF identity, the work-id rename sweep. |
| G4 | Six-role argument graph | Toulmin roles (warrant, backing, qualifier, rebuttal) carried by typed relations. |
| G5 | Typed propagation (blast radius) | When a source or claim changes, typed consequences mark everything it was holding up. |
| S1 | Type roster + mode collapse | Fewer, real note modes and concept types; schema pruning. |
| S2 | Real grounding detection | NLI-based grounding detection — never truth scoring. |
| S3 | Hub | The editorial concept plus the wiki-digest candidates block: the wiki–Zettelkasten bridge. |
| R1 | Passages + freshness | The passages table, span anchors, and incremental reindexing. |
| R2 | Retrieval modes + fusion + shapes | Filter-before-rank staging, graph-SQL primitives, result shapes, grounded synthesis. |
| R3 | Dense substrate | Real embeddings and semantic mode, built shadow-gated; default activation is beta.2. |
| W1 | Canvas → outline → draft | The writing path from project canvas to composed draft. |
| W2 | Draft write-back | Extract-to-note, transclusion backlinks, closing the drafting loop into the vault. |
| C1 | SRD generation + contract | The software-requirements document derived from a project's checked slice. |
| V1 | Checks + export refusal | The verification-check surface (abstain routing, structural integrity, sparse triage); the core refusal — export refuses when a citation does not resolve — is already shipped. |
| V2 | Evidence-set contract + review surface | Evidence-set rows, marker syntax, and the PI review surface for them. |
| V3 | Provenance labels | Human/machine/contradicted/stale labels with monotone taint. |
| O1 | Onboarding + seed corpus | The onboarding wizard, the licensed seed corpus, and the ≤30-minute first-answer bar. |
| O2 | Import pipeline | Staged BibTeX/CSL bulk import: admit to the catalog, flag duplicates, one quiet worklist per run. |
| I1 | Event plumbing + dispositions | Telemetry planes, disposition capture, the loudness policy, and the raw-counts dashboard. |
| E1 | Call-site ledger + gates | The LLM call-site ledger, runtime-mode boundary, and frozen-eval promotion gates. |
| K1 | OKF conformance + export/import | Frontmatter conformance; export is a bundle-folder copy; import re-enters as unchecked. |
| K2 | Fulltext v2 | Retiring `fulltexts/` as a bundle root in favor of blob + catalog storage. |
| K3 | Crash consistency + backup/restore | Crash-boundary tests, recovery reconciliation, the restore matrix. |
| K4 | Config / secrets / drift | Parameter ownership, fail-closed secrets, schema–doc drift checks. |
| U1 | Read API + surface contract | The surface-contract registry generating HTTP routes, MCP read tools, and CLI parity. |
| U2 | Deep-work + review cockpit | The composed cockpit screens; runs in a bare terminal by design. |
| U3 | Obsidian plugin | A thin renderer that enqueues over loopback HTTP; poll-based status in beta.1. |
| U4 | Co-PI skill / MCP | The engine authors the method; the user's agent voices it. |
| X1 | Records & safety | Snapshot/revert, derivation lineage, manifest-driven dispatch, prompt-injection defense. |

## Deliberately deferred (beta.2)

The headline items parked until after beta.1, each with a recorded reason in
the working specs:

- The reactive daemon and live on-save badges (no daemon before staleness data
  exists).
- Dense/hybrid retrieval as the *default* (BM25 stays until a pre-registered
  spike beats it on the real corpus).
- The code-execution lane and executable warrants.
- Warrant-node reification (evidence-gated on observed warrant usage).
- The autoresearch overnight loop (needs a scheduler and real gold tasks).
- 1000-scale seed-corpus load (disposition telemetry must exist first).
- Multi-device write topology (single-writer local-first stands).
- Merging two Memoria bundles (an exception path, not the common case).

## Related

- [Home](README.md) — what Memoria is and what it guarantees.
- [Failure modes](reference/system/failure-modes.md) — when something breaks
  today.
- [Design rationale](explanation/rationale/README.md) — why the system is
  shaped this way.
