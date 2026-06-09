---
topic: explorations
title: Graph visualization — typed projections of the relationships/links graph
status: exploration
created: 2026-06-08
parent: Design notes
grand_parent: Explanation
nav_order: 8
nav_exclude: true
---

# Graph visualization — typed projections of the relationships/links graph

> **Status: exploration** (a capability bundle a design note, not yet adopted). Builds on the
> [four-layer redesign](memoria-redesign.md) — specifically the **relationships vs
> links** distinction — and on issue #197 (the OSS graph/cluster/NLP survey, largely
> resolved by [ADR-33](../adr/33-cluster-mcp-bertopic.md)). #197 answers _what
> computes the graph_; this explores _what the human sees_. Firm decisions graduate to
> an ADR.

## 1. The reframe: not one graph, but two graphs and a bridge

Obsidian's native graph view (and most plugins) draw **one undifferentiated hairball**
of every `[[link]]`. That is precisely the conflation the redesign argues against — it
mixes _given/mechanical_ edges with _authored/interpretive_ ones. The
relationships-vs-links split is not a rendering footnote; it is **what makes good
visualization possible**, because it tells you what each edge _means_.

| Graph | Nodes | Edges | Source | Character |
| ----- | ----- | ----- | ------ | --------- |
| **Relationship graph** (Catalog) | papers · people · orgs · venues · datasets · repos | `cited_by` · `authored` · `affiliated` · `published-in` · `code-of` | OpenAlex / Zotero — mechanical | large, dense, externally fed; _you do not curate it_ |
| **Link graph** (Notes) | fleeting · source · claim · hub · index | `supports` · `contradicts` · `related` · hub-membership | **authored** | smaller, curated, human-meaningful |
| **The bridge** | source-note _is about_ a paper-entity; claim _cites_ a source | projection edges | derived | where **coverage and gaps** live |

Drawn together, the three collapse back into the hairball. Drawn as **typed
projections — each answering one question** — they become the most useful surfaces in
the vault.

## 2. The crown jewel: the typed claim graph

The single highest-value view the redesign unlocks — and one **no off-the-shelf tool
can draw**, because it depends on Memoria's _authored_ typing: claims connected by
**`supports` / `contradicts`**, edges colored green/red, node color = `maturity`
(seedling → evergreen), node size = in-degree (how many other notes lean on it).

This surfaces, at a glance:

- **consensus clusters** — densely mutually-supporting claims;
- **live controversies** — `contradicts` edges not yet resolved;
- **isolated assertions** — claims nothing else supports or builds on.

InfraNodus / SmartConnections / the native graph cannot produce this: they do not know
an edge is a _contradiction_. This is the differentiator and should be built first; it
feeds the existing `contradictions` dashboard directly.

## 3. Renderers — build vs adopt, by purpose

No single renderer fits all three graphs. Match the renderer to the job.

| Purpose | Renderer | Why |
| ------- | -------- | --- |
| **Ambient "what's near this note?"** | **Obsidian native graph** — color groups by category/type, local-graph-on-selection | zero build, local, ungated; undifferentiated edges, but fine for neighborhood orientation |
| **Curated typed maps** (claim-debate, hub structure) | **agent-emitted Obsidian Canvas** | `.canvas` is plain-text JSON, git-tracked, native, supports **colored/labeled edges** and manual rearrange; fits the plain-text discipline + propose-not-dispose (lands in staging, human edits/promotes) |
| **Compute** (layout, communities, centrality, gaps) | **NetworkX inside the gated cluster MCP** | #197 recommendation #2 — keeps compute gated + agent-reachable; emits coordinates/communities the Canvas consumes |
| **Bibliometric "key works" map** (Catalog) | NetworkX → static map artifact | the citation network is large and externally fed; you browse it, you do not curate it |
| **Semantic topic/density map** | **BERTopic** (ADR-33) — the existing `cluster-map` | the semantic layer; complements the structural graphs |
| **Optional power-pane** (topic/gap discovery) | **InfraNodus** — deferred | best-in-class gap surfacing, but managed-service + AI calls → a _human pane_, never the agent engine (per [External integrations](../reference/integrations.md) + #195) |

The **Canvas-as-emitted-artifact** is the Memoria-faithful sweet spot: native,
diffable, reviewable, human-editable — and the only option that renders _typed_ edges.

## 4. The view catalog (the deliverable)

Each view is a typed projection with one question, one owner, one surface — not a mode
of "the graph."

| View | Question | Renderer | Owner | Surfaces as |
| ---- | -------- | -------- | ----- | ----------- |
| **Claim-debate map** ★ | where is consensus / tension / isolation? | Canvas (+ NetworkX) | Analyst | `sketches/`; feeds `contradictions` |
| **Hub structure map** | what is this topic's shape; which claims does no hub hold? | Canvas | Analyst | feeds `open-questions` |
| **Coverage / bridge** | what have I _read_ vs merely catalogued; over/under-cited sources? | Base / matrix (bipartite is not a good graph) | Analyst / verify | feeds `gap-report` |
| **Citation graph** (Catalog) | seminal / bridge papers; author & venue clusters? | static map (NetworkX) | Analyst | browse-only artifact |
| **Topic / cluster map** | what topics exist; where is it thin / stale? | BERTopic (existing `cluster-map`) | Analyst | existing |
| **Structural health** | orphans · broken links · hub overload | **not a graph — a worklist** | Linter engine (`graph-analyze`) | Inbox `flag` / `loose-ends` |

The last row matters: graph _health_ is maintenance, not exploration — a worklist, not
a rendered graph. (Same split-by-layer logic as the Inbox-vs-dashboard distinction:
action queue vs browse view.)

## 5. Where it lives — visual discipline

- **Not on the homepage.** Home is the 30-second "what needs me?" glance; a graph is a
  _deliberate-open_ discovery surface. It belongs in the working surface (the Read/Write
  perspective), opened on intent — or its own "Map" pane.
- **Agents compute gated; the human views ungated.** NetworkX/BERTopic run behind the
  gated MCP (the ADR-33 discipline); the output _artifact_ is propose-class — it lands
  in `reports/` / `sketches/`, and the human disposes. Live human panning (native
  graph, InfraNodus) is read-only viewing and needs no gate.
- **Discovery vs health, split by actor tier.** Interactive exploration is the human's
  (at the working surface); orphan/broken-link debt is the engine tier's (deterministic,
  cron-able). Do not collapse them into one "graph view."

## 6. Relationship to #197

Issue #197 surveyed the libraries and _deferred_ two threads; this proposal is what
they plug into:

- **Recommendation #2** (NetworkX in the cluster MCP, "if link-structure analysis is
  ever wanted") — the claim-debate, citation, and coverage views _are_ that want, so it
  activates.
- **Recommendation #3** (InfraNodus / SmartConnections as deferred human panes) — now
  has a defined slot: an optional working-surface power-pane, never the engine.

So #197's "surveyed, deferred" becomes "here is the visualization layer they serve."

## 7. Impact on agents, engines, and skills

- **Analyst** gains the claim-debate and hub-structure Canvas emitters plus the
  bibliometric map (skills, e.g. `map:claim-graph`, `map:hub-canvas`,
  `map:citation-graph`); `canvas-seed` is the natural home.
- **Engine tier** keeps `graph-analyze` (orphans · broken links · hub overload · link
  density) as a deterministic worklist — _not_ a rendered graph.
- **NetworkX** is added to the gated cluster MCP (alongside BERTopic) as typed
  link-structure tools — not adopted as the Graph-Analysis _plugin_, which would sit
  outside the policy gate.
- **Fact-checker split (raised here, decided in the redesign):** the deterministic
  verification sweeps move to the engine tier; the coverage/bridge view is computed by
  the same link-structure tooling. The _judgment_ verification stays an independent
  agent task. This is the same "engines absorb the deterministic checks" move as
  dissolving Housekeeping into the engine tier.

## 8. Sequencing

1. **Obsidian native graph with category color-groups** — free, today; ambient
   orientation. (Config lives in `.obsidian/`.)
2. **The claim-debate Canvas** — Analyst emits it; NetworkX computes layout/communities
   in the MCP. The first real build and the unique-to-Memoria payoff.
3. **Hub-structure + coverage** views — next, reusing the same compute.
4. **Citation graph** — once the Catalog relationship edges are populated from OpenAlex.
5. **Defer InfraNodus** as an optional pane.

Skip a single, undifferentiated "graph view" entirely — it is the anti-pattern.

## 9. Decisions & alternatives weighed (ADR seed)

- **G1 — Typed projections, not one graph.** Render the relationships graph, the links
  graph, and the bridge as _separate, question-driven_ views. _Rejected:_ a single
  unified graph view (the hairball — it conflates given/authored edges, the redesign's
  core objection).
- **G2 — Canvas is the typed-edge renderer.** Agent-emitted Obsidian Canvas for curated
  typed maps. _Rejected:_ native graph (cannot type/color edges); a plugin/service as
  the primary surface (gating + plain-text discipline).
- **G3 — Compute is gated; viewing is not.** NetworkX/BERTopic behind the policy MCP
  emit propose-class artifacts; live human panes are read-only. _Reinforces_ ADR-33 and
  propose-not-dispose.
- **G4 — Graph health is a worklist, not a graph.** `graph-analyze` stays an
  engine-tier worklist surfaced via Inbox/dashboard. _Rejected:_ a "health graph" view.
- **G5 — The claim-debate map is the priority build.** Highest value, uniquely enabled
  by authored `supports` / `contradicts` typing.

## 10. Open questions

- **Canvas at scale.** Canvas is ideal for curated, bounded maps (one topic, one
  debate); it is not a renderer for thousands of nodes. The citation graph may need a
  static image or a sampled sub-graph — confirm the node-count ceiling per view.
- **Coverage view shape.** Bipartite note↔entity coverage is often clearer as a Base
  matrix/heatmap than as a graph; decide per use.
- **Refresh cadence.** Are agent-emitted maps regenerated on a cron, on demand, or on a
  card trigger? Likely on-demand plus on significant link-graph change.
