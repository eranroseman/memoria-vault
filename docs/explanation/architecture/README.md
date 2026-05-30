---
topic: architecture
---

# Architecture

Memoria has three layers — a Kanban board that orchestrates work, seven Hermes profiles that execute it, and an Obsidian vault that stores durable knowledge. The layers are connected through explicit handoffs but never collapsed into one.

## What's in this document

**The three-layer model** — [Three layers](#three-layers) (the diagram), [Why three layers, not one](#why-three-layers-not-one) (the rationale + the *Thin control over thick state* finding), [Layer 1: Board](#layer-1-board-kanban), [Layer 2: Workers](#layer-2-workers-hermes-profiles), [Layer 3: Vault](#layer-3-vault-obsidian-folders).

**Human-facing channels** — [Human channels](#human-channels) (Obsidian UI · CLI · Telegram · API).

**Filesystem and runtime** — [On-disk layout](#on-disk-layout), [Profile management](#profile-management).

**How it operates** — [How the layers interact](#how-the-layers-interact), [Core principles](#core-principles), [Operating model](#operating-model).

**Mechanisms and pointers to depth** — [Memory tiers](#memory-tiers), [Permission enforcement: the policy MCP](#permission-enforcement-the-policy-mcp), [Control plane](#control-plane), [Why Memoria refuses to autonomize synthesis](#why-memoria-refuses-to-autonomize-synthesis), [Pattern provenance](#pattern-provenance), [Capability stack](#capability-stack).

## Three layers

```text
┌─────────────────────────────────────────────────────────────────┐
│  Board layer (Kanban) — orchestration and memory of active work │
│  status: triage → todo → ready → running → done → archived      │
│  review overlay on done: requested → approved                   │
│  (blocked is off-path; rejected → archived)                     │
└────────────────────────────┬────────────────────────────────────┘
                             │ assigns lane / advances state
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│  Worker layer (Hermes) — seven profiles execute work in lanes  │
│  Librarian · Mapper · Socratic · Writer · Verifier ·    │
│  Coder · Linter                                                │
└────────────────────────────┬────────────────────────────────────┘
                             │ every write checked by the policy MCP
                             │ (allow / allow_with_log / deny / dry_run)
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│  Vault layer (Obsidian) — durable knowledge by lifecycle stage  │
│  00-meta · 10-inbox · 20-sources · 30-synthesis · 40-workbench  │
│  50-deliverables · 90-assets · 95-archive                       │
└─────────────────────────────────────────────────────────────────┘
```

## Why three layers, not one

A single-agent or single-document system blurs three different concerns: *what work is in progress*, *who is doing it*, and *what stable knowledge has accumulated*. Memoria treats each as its own layer with its own semantics.

- **The board never holds knowledge.** It tracks work. Cards die at `archived`; knowledge lives in the vault.
- **The workers never hold permanent state.** They claim cards, act, and release. Continuity comes from the board (in-flight) or the vault (settled).
- **The vault never schedules work.** It is the destination, not the orchestrator.

This separation is what makes retries safe, handoffs lossless, and review enforceable.

### Thin control over thick state

A one-line characterization of this design, borrowed from Chen et al. 2026 (*Toward Autonomous Long-Horizon Engineering for ML Research*): **thin control over thick state.** The orchestrator and the workers carry as little persistent context as possible; the durable knowledge — plans, claim notes, drafts, audit traces — lives in files. Workers re-ground on those files between steps rather than relying on conversational handoffs.

This is not just a Memoria-internal preference. Chen et al.'s ablation removes their *File-as-Bus* protocol (the same shape as the Memoria vault layer) and measures the consequence: PaperBench drops by 6.41 points and MLE-Bench Lite by 31.82 points. The same conclusion is reached independently by AgentRxiv (Schmidgall & Moor 2025), which shows that agents reading prior agent-generated reports gain ~11% over isolated agents on MATH-500. A third independent confirmation comes from PARNESS (Wang & Luan 2026), whose entire design rests on naming "no existing tool persists cross-run knowledge in a form that can be retrieved into a finite LLM context" as one of the field's five structural problems and addressing it with a persistent knowledge layer. Three unrelated systems, three architectures, one finding: long-horizon agent work fails when state lives in chat and succeeds when state lives in files.

A fourth, from the coordination angle: Yue et al. 2026 (*Building MCP-Native Hierarchical AI Scientist Ecosystems*) argues that scaling multi-agent discovery requires an MCP-native interoperability substrate plus **durable shared artifacts** — "task boards, lab notebooks, provenance stores" — because unstructured chat-and-memory coordination "becomes brittle as the number of agents grows" and makes it "hard to audit claims back to computations and data." Memoria already instantiates exactly that pairing: the Kanban board is the task board, the vault is the lab notebook + provenance store, and the policy MCP is the interoperability layer. The distinction worth noting is that Yue treats MCP as an *interoperability* layer; Memoria additionally uses it as a **permission / policy boundary** (the review-gated-zone deny rule), which the perspective does not contemplate. See [architecture/why-pattern-provenance.md §Reference](why-pattern-provenance.md#reference) for the verdict.

Memoria's three-layer split is the structural form of that finding. See [architecture/why-pattern-provenance.md](why-pattern-provenance.md) for the borrow/adapt/ignore mapping that places each of these systems against Memoria's design choices.

## Layer 1: Board (Kanban)

The board is the control plane. It persists every task as a card with status, assignee, blocker reason, retry history, and a handoff summary, and it keeps the card alive until the human review gate is passed.

The execution `status` is the fixed Hermes Kanban enum:

- `triage` — card created, specification in progress; dispatcher ignores.
- `todo` — specified, on the backlog, not yet released for dispatch.
- `ready` — dispatchable.
- `running` — owned and being executed by one profile.
- `blocked` — needs a human decision the worker cannot make.
- `done` — worker finished; in Memoria this is where the review overlay applies.
- `archived` — terminal (canonical and shipped, or abandoned).

The review overlay (`metadata.review_status`) rides on `done`: `requested` → `approved` (canonical) or `rejected` (revise-and-supersede or discard). A retry is not a distinct status — a recoverable failure returns the card to `ready`.

The key rule: a `done` card awaiting review is a real state, not a label. A card can be worked on, blocked, reviewed, rejected, and retried without losing history or confusing completion with approval.

See [kanban-board/README.md](../kanban-board/README.md) for the conceptual model and [kanban-board/states.md](../kanban-board/states.md) for the full state machine, the worker-lane exit contracts, and the review gate rules.

## Layer 2: Workers (Hermes profiles)

Hermes is split into seven specialist profiles rather than one generalist agent. Each profile has narrow permissions, a focused command surface, the MCPs it actually needs, and a clear exit condition.

| Profile | Role |
| --- | --- |
| **Librarian** | Discovers, ingests, enriches, and classifies sources. Exits at `done` (`review_status: requested`). |
| **Mapper** | Maps the corpus for a project: scope reports, gap reports, cluster maps. Read-only across vault except project scratch. |
| **Socratic** | Questions the human about a paper note or framing. Write-denied across the entire vault. Invoked synchronously. |
| **Writer** | Synthesizes evidence into drafts, answer notes, and reference-ready prose. Cannot canonize. |
| **Verifier** | Traces draft claims to claim notes; verifies citations; flags duplicates and retractions. Read-only across vault except verification reports. |
| **Coder** | Builds and maintains code artifacts, scripts, project scaffolding. Cannot edit canonical synthesis. |
| **Linter** | Validates structure, metadata, schema, link health; owns session and audit-trail housekeeping. Default is dry-run. |

There is no Orchestrator profile and no Reviewer profile. Routing lives in lane-overrides + Kanban dispatch (not a reasoning agent); review gates live in the policy MCP and the board state machine (not a dedicated profile). See [profiles/README.md](../profiles/README.md#routing-without-an-orchestrator) for the routing rule, and [profiles/README.md](../profiles/README.md) for per-profile detail.

## Layer 3: Vault (Obsidian folders)

The vault stores durable knowledge. Folders encode lifecycle stage, not subject area — see [vault/README.md](../vault/README.md) for the authoritative layout, including the full tree, subfolder roles, and access matrix.

| Folder | Role |
| --- | --- |
| `00-meta/` | Templates, CSL, config, logs, dashboards, schema. |
| `10-inbox/` | Fleeting captures, answer drafts, discovery candidates. |
| `20-sources/` | One zone for everything that describes the world: literature, items, entities. |
| `30-synthesis/` | One zone for everything that expresses the human's thinking: claim notes, reference notes, MOCs. |
| `40-workbench/` | Active work: projects, drafts, code, canvas. |
| `50-deliverables/` | Finished outputs: manuscripts, presentations, media, releases. |
| `90-assets/` | Attachments and binary assets. |
| `95-archive/` | Deprecated, superseded notes. |

The grouping is load-bearing. `20-sources/{01-papers, 02-items, 03-entities}` says "everything that describes something external." `30-synthesis/{01-claims, 02-reference, 03-moc}` says "everything that expresses the human's thinking." `40-workbench/<project>/{01-map, 02-framing, 03-canvas, 04-drafts, 05-verification, 06-code}` says "things being worked on" — one folder per project, all its working artifacts inside. This makes ownership and access policy easier to enforce.

See [vault/README.md](../vault/README.md) for the full layout, note types, templates, and linking patterns.

## Human channels

Memoria's primary UI is Obsidian; CLI and Telegram are secondary channels; port 8642 is the non-human API path. The defining discipline is that each access path owns exactly one mode — misuse produces drift. See [human-channels.md](human-channels.md) for the per-path breakdown: when to use CLI vs dashboards, the two distinct Telegram uses, the deliberately-narrowed Telegram toolset, what the API is and isn't for, and the access-path failure modes.

## On-disk layout

Memoria spans **two filesystem locations**: the starter vault (versioned, holds all install material including the seven hand-authored profile dirs under `.memoria/profiles/`), and the user's Hermes runtime (per-user, holds installed profile copies written by `install.ps1`) at `~/.hermes/profiles/memoria-*/`. Git is the authoritative history layer; sync (Obsidian Sync, Syncthing, or manual git pull/push) is separate from history.

**See [architecture/on-disk-layout.md](on-disk-layout.md)** for the full tree, the vault/runtime relationship, the install flow, version-control rules (in / out of git), and the "sync ≠ history" discipline.

## Profile management

The seven profile directories under `.memoria/profiles/memoria-<name>/` are **hand-authored**. They are checked into the starter vault repo as authored, and `install.ps1` copies them verbatim into `~/.hermes/profiles/memoria-<name>/` (substituting `{{VAULT_PATH}}` placeholders in `mcp.json`). There is no build step; what's in the vault is what the agent reads at runtime.

The trade-off is that shared content (audit-log behavior, common policy invariants, common MCP connections) lives in seven copies that must be kept in lockstep by hand. The Linter's `profile-install-drift` detector (see the [Linter design summary](../profiles/linter.md) and the runtime `M-detectors.md` alongside the Linter SOUL.md in the starter vault) catches one direction of drift (the deployed copy diverging from the vault source); inter-profile drift between the seven SOUL.md files relies on human review during edits. See the [deferred compiler design](../../project/roadmap/profile-compilation.md) for the alternative that may become relevant if drift becomes painful at the seven-profile scale.

## How the layers interact

The recommended interaction pattern is:

1. A trigger (human action, cron job, git hook, file watcher) creates a card on the board with an assignee (its lane) and an initial status. Routing is encoded in the trigger's rules — there is no profile that "decides" lane assignment.
2. **Specialist profile** (Librarian, Mapper, Writer, Verifier, Coder) claims a card from its lane and moves it to `running`. Socratic is invoked synchronously by the human and doesn't appear in queue-based handoffs.
3. The worker executes the task, writes any provisional outputs (e.g., paper notes, answer drafts) into the lane's declared write scope, and completes the card to `done` with `review_status: requested`.
4. The **human** examines the work, then sets `review_status` to `approved` or `rejected`. Some review decisions are partially automated — Verifier produces a `[!verification]` callout the human reads — but the approval is always human-driven.
5. If `approved`, the **dispatcher** archives the card (a state transition, not an approval decision — the human's approval is what licenses it) and the output remains in its current location; if promotion is part of the task, the next workflow trigger moves it to a canonical layer.
6. If `rejected`, the human chooses between two follow-ups: spawn a revision card on the same lane (carrying a `metadata.supersedes` link back to the original; original archived with `metadata.archive_reason: superseded`) or archive the original entirely with `metadata.archive_reason: discarded`. See [kanban-board/README.md Post-rejection paths](../kanban-board/README.md#post-rejection-paths).
7. **Linter** can act on any card structurally — usually before review — to flag schema, link, or orphan issues. It only ever produces reports, never silent fixes.

Cards never close on a worker's say-so. The card lives until the human changes the review state.

## Core principles

- **The board is the shared state machine.** All long-lived work lives there.
- **Lanes are specialist execution paths.** Not separate boards.
- **Review is a state, not a comment.** It is queryable, ownable, and blocks dispatch.
- **Folders encode what a note is, not what it is about.** Topics belong in frontmatter and links.
- **Canonical synthesis is human-owned.** `30-synthesis/01-claims/` is never auto-written.
- **Retries reuse the same card.** No duplicates; history is preserved in comments.
- **Handoff notes carry context.** The next worker should not need to re-read the conversation.
- **Every agent logs what it changed and why.** The policy MCP records every write decision to an audit log; the Linter rotates the log and produces the session summaries that make reversibility auditable.
- **Prefer extending the architecture over adopting peer systems.** A new tool that lives *inside* Memoria's existing channels and surfaces — a plugin, a skill, a dashboard, a lane — composes with the policy MCP, the audit log, and the channel discipline. A new tool that lives *alongside* Memoria as a peer (its own UI, its own state, its own auth) creates boundary disputes, duplicates state, and usually ships a feature that bypasses the policy gate. Extensions compose; peers compete. When evaluating a new capability, look for the extension shape first.

## Memory tiers

Memoria operates across five distinct memory scopes — two Hermes-native (working context, profile memory) and three Memoria-added (session search, board handoff payload, vault files) — each with different lifespans and owners. Confusing them is the source of most "the agent forgot" and "the agent remembered something it shouldn't have" bugs. See [architecture/memory-tiers.md](memory-tiers.md) for the full substrate table, the rules that keep memory from bleeding across lanes, and why the thin-control-over-thick-state split matters.

## Permission enforcement: the policy MCP

Profile permissions and lane scopes are enforced at runtime by a policy MCP that intercepts every vault write, returning one of four decisions (`allow`, `allow_with_log`, `deny`, `dry_run`). Review-gated zones always degrade to `dry_run`; every allowed write is audited with SHA-256 hashes for tamper detection. See [architecture/policy-mcp.md](../../reference/architecture/policy-mcp.md) for the full decision protocol, action vocabulary, request/response contracts, audit log schema, SHA-256 implementation rules, and skill-conditional policy mechanism.

## Control plane

The board defines *what state* a card is in. The policy MCP defines *where* a worker may write. The **control plane** is the daily-use surface that lets the human trigger discrete actions: three thin layers — Obsidian Command Palette → Hermes API → MCP servers — between the human and Hermes. None of them owns business logic except the MCP servers.

The Hermes API is fail-closed: it requires its auth token (`API_SERVER_KEY`) on every bind including the default `127.0.0.1` loopback, and a non-loopback bind must be explicitly configured (`API_SERVER_HOST`).

**See [architecture/control-plane.md](control-plane.md)** for the layer-by-layer responsibility table, fail-closed startup rules, and MCP server registration shape.

## Why Memoria refuses to autonomize synthesis

Karpathy's Autoresearch pattern works for ML experiments because three conditions hold: the metric is monotonic, changes are reversible, and experiments are independent. Knowledge work satisfies none of these. Memoria adopts the parts that *do* fit (overnight discovery loop, point-of-action similarity check) and refuses the parts that don't (autonomous keep/revert; scalar-metric-driven canonization).

**See [architecture/why-no-autonomous-synthesis.md](why-no-autonomous-synthesis.md)** for the three boundaries (cognition-bound vs compute-bound, no autonomous keep/revert, no scalar metric) and what they imply for scheduled operations, agent scope, and cost discipline.

## Pattern provenance

Memoria draws on a broad survey of contemporary AI-research systems (LitSearch, ResearchArena, AI-Scientist, LatteReview, OmegaWiki, Idea2Story, Karpathy Autoresearch, and others). The headline borrowed patterns are summarized in [vision.md](../vision.md#contemporary-ai-research-systems); the autonomy boundary that rejects several wholesale is in [architecture/why-no-autonomous-synthesis.md](why-no-autonomous-synthesis.md).

**Full borrow / adapt / ignore table** — every pattern, every source repo, every rationale — lives in [architecture/why-pattern-provenance.md](why-pattern-provenance.md). The net design shift is from agent-assisted to **bounded, stage-gated knowledge production**: the agent becomes better at bookkeeping, retrieval, and drafting; the human remains the gatekeeper for meaning, promotion, and final structure.

## Capability stack

The minimum capability stack to operate Memoria is eight components: Hermes (seven profiles), the Hermes Kanban, Obsidian, Zotero + Better BibTeX, the external enrichment APIs (OpenAlex, Semantic Scholar, PubMed, Crossref, Unpaywall, ORCID, ROR), git, the Obsidian REST API for vault read/write (with the Agent Client pane (ACP) as the complementary editor-level agent interface), and Pandoc for export.

On top of that base, **pre-built skills** (K-Dense `paper-lookup` / `pyzotero` / `citation-management`; Obsidian `obsidian-paper-note`; Hermes built-in `llm-wiki`) cover most enrichment and ingest work; the agent should use them rather than writing API clients from scratch. **Model routing** — Claude for synthesis, cheap models (via OpenRouter or similar) for bulk/mechanical tasks — keeps the discovery loop's `$1–3/day` budget achievable.

**See [architecture/capability-stack.md](../../reference/architecture/capability-stack.md)** for the full skill catalog (K-Dense, Obsidian, Hermes built-in, the REST passthrough escape hatch), the model-routing table, and the plugins/apps/external-tools list.

## Operating model

The architecture implies a bounded, stage-gated, human-in-the-loop cadence: daily capture and ingest, a weekly dashboard ritual, per-project drafting, and continuous Linter / cron / git-hook activity at the edges — autonomy added at the edges (scheduled discovery, automatic enrichment) without ever weakening the review gate. The full daily / weekly / per-project / continuous breakdown is the [Default operating model in workflows/README.md](../../how-to/workflows/README.md#default-operating-model); it isn't duplicated here.
