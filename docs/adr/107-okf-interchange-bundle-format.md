---
topic: decisions
id: 107
title: OKF as Memoria's import/export bundle format
status: proposed
date_proposed: 2026-06-19
date_resolved:
assumes: [26, 30, 47, 50, 52, 101, 102]
supersedes: []
superseded_by: []
parent: Decisions
grand_parent: Explanation
nav_order: 107
nav_exclude: true
---

# ADR-107: OKF as Memoria's import/export bundle format

## Context

Memoria's substrate — a directory of markdown files with YAML frontmatter,
`type`-routed presentation, path-derived ids, links between notes, agent- and
version-control-friendly — was independently arrived at by Google Cloud's **Open
Knowledge Format** (OKF, `okf/SPEC.md`, v0.1 draft). The convergence is near
total: OKF's *Concept* is a typed markdown document (a tangible asset or an
abstract idea), its *Concept ID* is the file path minus `.md`, relationships are
markdown links, and it reserves `index.md` (progressive disclosure) and `log.md`
(history). That an external, vendor-backed spec landed on the same shape is
validation of [ADR-47](47-type-first-category-folders.md) /
[ADR-26](26-repo-as-install-unit.md), but it also names a contract Memoria lacks.

Memoria's **outbound** layer is its least-defined. The Path-4 open-artifact
release is deferred ([ADR-20](20-publication-path.md)); navigation spaces
([ADR-101](101-navigation-spaces-gate-reserved-for-approval.md)) and the
disposable projection engine ([ADR-102](102-disposable-projection-engine.md))
produce views with no *named, runtime-independent* serialization. OKF supplies
exactly that missing unit: the **Knowledge Bundle**, "the primary unit of
distribution," consumable without Memoria's gates, MCPs, or Hermes runtime.

OKF's defining trait, however, is the inverse of Memoria's thesis. OKF mandates
permissive consumption — "Consumers MUST NOT reject a bundle because of missing
optional fields, unknown `type` values, or broken cross-links" — and holds that "the
specific kind of relationship is conveyed by the surrounding prose, not by the link
itself." Memoria deliberately rejected prose-typed relationships in favor of typed
edges ([ADR-08](08-typed-relations-frontmatter.md) →
[ADR-52](52-links-vs-relationships.md)) because graph queries need the type *on*
the edge, and it enforces strict schemas, controlled vocabularies, and category-error
rejection in the Linter. OKF is therefore a fit for the **boundary**, not the core.

## Proposal

Memoria may treat OKF as its import/export lingua franca, adopted strictly at the
vault boundary and never as a relaxation of the internal model.

**Export.** A projection or navigation space may be serialized as an
OKF-conformant Knowledge Bundle: one Memoria note or catalog entity → one OKF
concept; the projection's folder tree → the bundle tree; the bundle's root
`index.md` declares `okf_version`. The export is **lossy by contract**, and the
loss is documented, not hidden:

- typed `links:` / `relationships:` ([ADR-52](52-links-vs-relationships.md))
  collapse to untyped markdown links, with the relation type emitted as prose per
  OKF convention — graph-queryable typing does not survive the round trip;
- `lifecycle` / `maturity` / gate state ([ADR-50](50-universal-lifecycle-and-maturity.md))
  survive only as custom frontmatter that conformant consumers may ignore;
- the bundle carries no gate, no Linter, and no MCP surface — it is inert data.

The serialization runs through the projection engine's reconciliation and failure
model ([ADR-102](102-disposable-projection-engine.md)) rather than as a bespoke
emitter; bundles are disposable consumer-only artifacts, not a second source of
truth.

**Import.** An external OKF bundle may be ingested as a new source type through the
deterministic pipeline ([ADR-30](30-deterministic-ingest-pipeline.md)). OKF
concepts enter as candidate material subject to the normal write/link gates
([ADR-28](28-write-gate-as-plugin.md)) — Memoria's tolerance of OKF's permissiveness
stops at ingest; nothing from a foreign bundle reaches a canonical surface ungated.

**Conventions borrowed outright.** Independently of the bundle contract, Memoria
may align two cheap conventions: a standardized `index.md` progressive-disclosure
manifest at folder roots, and OKF's reserved body headings `# Schema` /
`# Examples` / `# Citations` as a presentation convention for notes that already
carry that content.

## Consequences

- Memoria gains a runtime-independent publication artifact, de-risking the deferred
  Path-4 release ([ADR-20](20-publication-path.md)) and making "exports as OKF
  bundles" an interoperability claim in an emerging agent-knowledge ecosystem.
- Export is lossy; the typed-relation and gate-state loss must be stated in the
  bundle and in user-facing docs so a shared bundle is never mistaken for the live
  vault.
- Import widens the inbound surface to foreign bundles; the gate, not OKF's
  permissive consumer rule, governs what lands.
- A new serialization format to track against OKF's version line; `okf_version`
  pins the target and bounds breakage.
- No change to the internal model: typed links, strict schemas, and category-error
  rejection stay as-is. OKF's permissiveness is honored only when *reading* foreign
  bundles, never when authoring Memoria's own.

## When this matters

This becomes worth deciding when there is a concrete consumer for an exported
bundle (a publication artifact, a shared subset, another tool that reads OKF), or a
concrete foreign OKF corpus worth ingesting. Below that, the projection and ingest
layers already cover internal needs and the format adds surface without a reader.
OKF is a v0.1 draft; its stability and adoption are themselves a gating signal.

## Alternatives considered

**Invent a Memoria-specific export schema.** Rejected: it repeats OKF's design with
none of its interoperability, and forfeits alignment with a vendor-backed format
that already matches the substrate.

**Adopt OKF's permissiveness internally** (untyped prose relationships, tolerate
unknown types, never reject). Rejected outright: it is the inverse of the typed-edge
and structural-gate thesis ([ADR-52](52-links-vs-relationships.md),
[ADR-28](28-write-gate-as-plugin.md)) — Memoria is deliberately *ahead* of OKF here.

**Export only, no import.** Viable as a first slice, but the inbound direction is
near-free given the format symmetry and positions Memoria to consume the broader OKF
corpus; deferring it is a sequencing choice, not a different decision.

## Related

- **Workflows affected:** publication / open-artifact release, navigation-space
  export, OKF-bundle ingest.
- **Files affected:** future OKF (de)serializer under `src/.memoria/operations/`,
  the projection registry ([ADR-102](102-disposable-projection-engine.md)), the
  ingest pipeline source-type registry ([ADR-30](30-deterministic-ingest-pipeline.md)),
  schema/Linter conformance for emitted bundles.
- **Related decisions / Depends on:**
  [ADR-26](26-repo-as-install-unit.md),
  [ADR-30](30-deterministic-ingest-pipeline.md),
  [ADR-47](47-type-first-category-folders.md),
  [ADR-50](50-universal-lifecycle-and-maturity.md),
  [ADR-52](52-links-vs-relationships.md),
  [ADR-101](101-navigation-spaces-gate-reserved-for-approval.md),
  [ADR-102](102-disposable-projection-engine.md);
  serves the deferred Path-4 release of [ADR-20](20-publication-path.md).
- **Reference:** Open Knowledge Format (OKF) v0.1 draft —
  `GoogleCloudPlatform/knowledge-catalog`, `okf/SPEC.md`.
