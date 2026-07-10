# OKF and Memoria — 2026-07-09

How the Open Knowledge Format (v0.1 draft) relates to Memoria, read
against the day's record. Bottom line: **the vault is one OKF Knowledge
Bundle; Memoria is an opinionated OKF producer profile.** OKF standardizes
the minimal interoperable shell (markdown + frontmatter `type`, path
concept IDs, index/log conventions, permissive consumption) and explicitly
declines taxonomies, link semantics, and verdicts — Memoria's product is
exactly what OKF leaves out (typed links, phase gates, verdicts,
provenance, the argument graph). Complementary by construction: OKF's
non-goals are Memoria's value.

## The vault as a conformant bundle

- The workspace already matches §2/§3: concept documents with typed
  frontmatter (Memoria's schemas enforce far more than OKF's one required
  field), generated `index.md`, path concept IDs, markdown links. Inbox
  cards are conformant concepts (typed frontmatter) — even the proposals
  layer conforms.
- Near-conformance gap: files like `steering.md` lack `type` frontmatter
  (§9 requires it of every non-reserved `.md`). Cheap sweep to full
  conformance.
- Grounded ontology for the product statement: the workspace is one
  bundle; projects nest within it; the three spaces are regions of one
  bundle, not separate containers.

## The alpha.15 "export-only retreat" was the right architecture

OKF calls the bundle "the unit of distribution." Internal representation
is Memoria's business (SQLite verdicts, blob store, typed edges); the
**boundary** is OKF:

- **Export** = a bundle with Memoria extensions as producer-defined
  frontmatter keys (§4.1 blesses unknown keys). Verdicts may be frozen
  into exported frontmatter without violating the retired-fields rule —
  an export is a dated snapshot: a record, not a mirror; it cannot drift.
- **Import** = permissive consumption (§9) of anyone's bundle into the
  catalog as unchecked material awaiting the gates.
- The journal → `log.md` projection (§7) is a free export feature.

## Connections to open work

1. **Warrant ontology — exportability weight for nodes.** OKF links are
   untyped (§5.3); edge-borne semantics survive export only as prose. A
   warrant-as-concept exports as a first-class document any OKF consumer
   reads; a warrant-as-edge-property evaporates at the boundary. Added to
   the open question in `product-statement.md`.
2. **The catalog bridge gets a sanctioned address.** §8's `references/`
   subdirectory ("external material as first-class OKF concepts") is the
   `catalog/sources/<work_id>` namespace's published convention: on
   export, catalog works materialize as `references/` concepts.
3. **Broken links are gaps.** §5.3 tolerates broken links as
   "not-yet-written knowledge"; `analyze_gaps` is the consumer that
   mechanizes what OKF permits.
4. **Identity tension, reconciled.** OKF concept ID *is* the path (§2);
   the architecture review flagged path-as-identity as the years-scale
   provenance risk. Reconciliation: **ULID is the internal identity; the
   path is the OKF-facing address**; rename tracking maps between them.
   OKF conformance is not an argument for path-keyed internal provenance.
   Noted in roadmap item 6.

## The durability pitch

Your vault is a standard, portable, tool-independent knowledge bundle —
Memoria is the engine that makes it trustworthy. If Memoria dies, the
bundle remains readable by anything (`cat` works, the spec's own bar);
everything Memoria adds is extension keys plus a sidecar DB. The
strongest possible story for "compounds over months and years": the
knowledge outlives the tool.
