## alpha.10 — The post-alpha.9 consolidation checkpoint: Hermes 0.17 acceptance, measurement-gated cleanup, and a clean-slate rebuild of the Obsidian surface + type schema (ADR-114–119)

**Theme.** alpha.10 is not a feature release — it is an internal validation checkpoint that gathers every design change landed after alpha.9 into one coherence boundary (`docs/releasing/0.1.0-alpha.10/release-plan-0.1.0-alpha.10.md`, §1). Two forces drove it. First, an **in-place Hermes 0.14→0.17 runtime upgrade** that had to be *accepted against on-box evidence* before any dependent work could land, paired with a deliberately austere, **measurement-first** stance: the `#859` current-state baseline was the gate that decided which memory/runtime cleanup was worth building versus deferring or killing (`tmp/execplan-alpha10.md` §3, `tmp/current-state-baseline.md`). Second, a run of **clean-slate design reviews** that produced ADR-111 through ADR-119 — rethinking onboarding, the left-pane/dashboards/spaces surface, the type-naming scheme, and the type schema itself — from first principles rather than from the accreted implementation. The net across the schema/surface work is *consolidation and deletion*, not new machinery.

> **Note on the range.** `830ecd31..383034b0` (70 commits) spans from just before the alpha.9 close commit (`3ba5081f`/#858) through `main` at `e56aba40`/#928 plus the release-execution fixes. The release plan explicitly scopes alpha.10 as "the full post-alpha.9 change set" (release-plan §1), so the alpha.9-tagged finalization commits (`35b53426`–`3ba5081f`) are treated here as in-scope design-bearing work.

---

### Vault / concepts, type schema, and document naming

**What:** The umbrella term for a typed object changed **"note type" → "document type"**; `docs/reference/note-types.md` → `docs/reference/document-types.md` and `docs/explanation/knowledge/note-types.md` → `document-types.md` (renames R069/R086 in the diff), with schema/code comments and prose following (`1319b93e`, ADR-117). A *note* is now one **kind** of document (`source`/`claim`/`hub`/`fleeting`), so the `notes/` folder is a legitimate subset rather than a circular "notes are notes."
**Why:** A clean-slate walk of all 26 types found there was *no stated naming rule*, so apparent overloads read as bugs (a reviewer "fixing" the kanban `worker-card`→`worker-row`) and new types could drift with nothing to check them against; and `notes/` doubled the medium word (every object is a note, yet one category is "notes"). The tempting fix — rename `notes/`→`knowledge/` — was rejected because a `knowledge/` folder would collide *with a different meaning* with the Knowledge space (the folder feeds both Library's `source` docs and Knowledge's `claim` docs). Changing the umbrella term is strictly cheaper: "No folder moves, no `type:` values change, no paths change" (ADR-117 Context + Consequences).

**What:** A formal **naming rule** was recorded: singular common noun in the field's ubiquitous language, scoped to one of four *kinds* carried by the category folder — **Record** (`catalog/`,`notes/`,`projects/`), **Signal** (`inbox/`), **Surface** (`spaces/`), **Control** (`system/`) — plus a **no-collision corollary** (a folder may not also name a navigation surface with a different meaning) (ADR-117 Decision).
**Why:** To end the recurring "card"/"note" debates by naming the bounded-context and no-collision principles, and to validate already-correct names (`worker-card`, `worklist-item`, the catalog six) rather than churn them. `fleeting` is kept as the one explicit adjective exception because it is the entrenched capture term and renaming it would force runtime migration for no ambiguity gain. Kind-prefixed names (`entity:paper`) were rejected as over-engineered — the folder already encodes the kind (ADR-117 Alternatives).

**What:** ADR-119 promoted the type schema from a **fields+enums fragment to (the design for) the complete declarative contract** covering all eight concerns — identity/placement, fields-as-specs, controlled vocab, lifecycle state machine, typed edges, invariants, generation metadata, evolution — with the Linter becoming a generic engine that *executes* declared rules and forms/templates/`folders.yaml`/reference docs *generated* from the schema via one `create(type, inputs)` engine serving both the human form and the agent writers (ADR-119 Decision, `76b2a148`).
**Why:** The contract was scattered across four hand-synced places — invariants hard-coded in `detectors.py` (`thesis`→`promoted_at`, `claim`→`sources`), defaults in templates, labels "nowhere," placement split between `folders.yaml` and the schema — so adding a type meant editing four files and the field list was re-encoded three times (schema, template frontmatter, Modal Form), which had *already drifted* (the source form added `summary`, dropped `links`) (ADR-119 Context). This is Memoria's own single-source-of-truth philosophy applied to creation, not just validation. Full JSON Schema was rejected as the format because it models a document's internal shape, not the vault's placement/graph/referential layer, so a custom layer survives regardless; an enriched native DSL projectable to JSON Schema later was chosen (ADR-119 Decision §5, Alternatives).

**What (implemented this release):** Type schemas gained **`initial_lifecycle`** declared uniformly (e.g. `claim: current`, `source/fleeting: proposed`), **`source_type` became an enum** (`[paper, dataset, repository, web-page, report]`, was free `str`), a **`sample: bool`** optional field was added across content/space types, and each user-facing type gained an in-schema **`creation.form`** block (field, label, description, input widget, vocabulary/enum bindings) — landed for `claim`, `source`, `project`, `fleeting` (`src/.memoria/schemas/types/*.yaml`, `5a7209ed`/`cb81a255`).
**Why:** These are the confirmed-feasible ADR-119 phases (invariants/state uniformity + schema-owned forms). The `source_type` case is the worked example: the *form* already rendered it as a required five-value select while the *schema* said optional `str`, so generating the form from the schema would have *lost* the controlled vocabulary — the enum had to move into the schema (ADR-119 §6, `b92941ed`). The `sample` flag exists so sample-vault documents can be excluded from "New this week" digests and found by the remove command (see UI/sample-vault below).

**What:** The **`index` document type was removed** — the type, its `index.yaml` schema, template, and the `notes/indexes/` skeleton folder are gone (`folders.yaml` drops `index: notes/indexes` and the skeleton entry; `index.yaml` deleted, `cb81a255` (#924)/ADR-119).
**Why:** Its schema was title-only and expressed none of its "register" purpose, it had no creation path, and its register function (a list of hubs) is already the `hubs.base#Hubs index` view — "the one type whose schema simply does not match its purpose" (ADR-119 §6).

**What:** Two new **`spaces`-category types were added** — `queue` and `maintenance` (`queue.yaml`, `maintenance.yaml`, both `category: spaces`, `initial_lifecycle: current`) — and the `space` type's `space` enum **dropped `inbox`** → `[library, knowledge, project]`; `folders.yaml` maps `queue → spaces/` and `maintenance → spaces/` (`16c6844e`, `616bdc1b`, ADR-115/116).
**Why:** The Inbox is a *state that converges to empty*, not a durable room, so modeling it as a co-equal fourth space was wrong (see Discovery/UI). Maintenance is a separate weekly-cadence collection split off from the daily queue. Templates deliberately exclude `queue`/`maintenance` (authored, not template-created), keeping the template count stable at 20 (ADR-115 Consequences).

**What:** The retracted sample source's supersession pointer moved from a top-level `superseded_by:` into the source's `links:` map (`0f9da419`).
**Why:** ADR-119 made the type schema the complete field contract; `source.yaml` has no `superseded_by` (that field belongs to claim/thesis schemas), so the PREDIMED-original fixture violated no-unknown-field validation. Moving it into `links: map` (which `source.yaml` allows) preserves the supersession relationship while conforming to schema (commit body `0f9da419`).

---

### Profiles / runtime (Hermes 0.17)

**What:** Hermes was upgraded **v0.14.0 → v0.17.0** in place (upstream `b1b20270`; RC validated on `74265c8e`) and the config schema migrated **v23 → v30** — profile `config.yaml` files now carry `_config_version: 30` and `context_file_max_chars: 30000` (`tmp/hermes-upgrade.md`; `src/.memoria/profiles/*/config.yaml`; validation-log).
**Why:** `hermes doctor` flagged the pre-upgrade default profile as stale (unknown provider `ollama`, config `v23→v30`); the upgrade + migration is pure hygiene that unblocks everything else, and the plan made it the G2 gate that "gates everything else: no cleanup lands on an unaccepted runtime" (`tmp/execplan-alpha10.md` §3).

**What:** Profile capability blocks are now **materialized from `tool-registry.yaml`** by a new `scripts/render_profile_configs.py`; each `config.yaml` is stamped "Generated by scripts/render_profile_configs.py; edit tool-registry.yaml" (new ADR-115 *profile-config-materialization*, the second ADR numbered 115).
**Why:** ADR-27 already made `tool-registry.yaml` the source for each profile's positive toolsets/MCP filters, but the checked-in configs *repeated those derived blocks by hand* across five profiles — the highest-risk capability surface copied five ways. Rendering lets CI fail on stale generated configs instead of relying on humans to copy allowlist edits, while keeping runtime "boring" (Hermes still receives plain `config.yaml`, no install-time template language). A full profile compiler was rejected as too broad (ADR-48 already retired it); Hermes-native inheritance isn't available on the installed v0.17 model (ADR-115 profile-config Context/Alternatives).

**What:** Gating shifted to a **positive `platform_toolsets` allowlist** — every profile now declares the exact toolset list per Hermes runtime platform (cli/cron/api_server/telegram/…/google_chat), plus per-MCP-server `tools.include` filters (e.g. `policy: [check_permission, complete_write]`, `qmd: [search, vsearch, deep_search, get, status]`); the subtractive `disabled_toolsets` list is retained as belt-and-suspenders (now also naming `session_search`) (`be6ebbb0`, `src/.memoria/profiles/memoria-copi/config.yaml`; `tool-registry.yaml` header rewritten to "the policy-gate plugin reads this on pre_tool_call and blocks calls outside the profile allowlist").
**Why:** The 0.17 eval found subtractive denylists "brittle when Hermes adds new tools" — a new upstream toolset would be *granted by default*. A positive allowlist closes new tools by default; the eval demanded a live deny-path test to *prove* it closes rather than merely hides them before switching (`tmp/hermes-017-feature-eval.md` "Used sub-optimally"; execplan §3 fourth). This is the reconciled, on-box-verified item (no longer speculative), so it landed.

**What:** The **`memory` toolset became profile-scoped to `memoria-copi` only** (enforced in `policy_hook.py` via `PROFILE_SCOPED_DIRECT_TOOLS = {"memory": {"memoria-copi"}}`), with memory config set to `write_approval: true`, `user_profile_enabled: true`; and Co-PI's memory `provider: ''` keeps canonical knowledge in the vault (`450f659d`, `test_policy_gate_completeness.py`; copi `config.yaml`).
**Why:** The eval's clean-slate architecture says only the Co-PI carries the self-improving loop and "Hermes memory stores only preferences and runtime lessons, with write approval on. Canonical knowledge stays in Obsidian/vault schemas" (`tmp/hermes-017-feature-eval.md` §"Built-in memory", Clean-slate §3). Scoping it to one lane and enabling write-approval enforces that boundary.

**What:** New ACP-exposed local-history tool **`session_search` added to the hard-deny set** for every lane (`DENY_DIRECT_TOOLS`, `policy_hook.py`); contract doctor and completeness test updated (`450f659d`, "harden direct history tools").
**Why:** Hermes 0.17 surfaces session/history search tools; leaving them reachable would let an agent read cross-session history directly, bypassing the MCP-only vault access discipline (D40/ADR-46). The regression test asserts it is blocked bare and MCP-prefixed.

**What:** Every profile gained a **`.no-bundled-skills`** marker ("Memoria owns this profile's skill surface; do not seed Hermes bundled skills"), plus `skills: {write_approval: true, guard_agent_created: true}`, `curator: {enabled: false}`, `tool_search: {enabled: auto}`, and `agent.tool_use_enforcement: true` (`be6ebbb0`/`79e6ea43`, all `config.yaml`).
**Why:** The eval found bundled skills "seeded broadly; lane profiles should stay narrower" and recommended opting out; Tool Search should stay `auto` ("forcing it on adds round trips") (`tmp/hermes-017-feature-eval.md` §Skills, §Tool Search, ranked rec #5/#6).

**What:** The `qmd` MCP server was re-pointed from the raw `qmd mcp` binary to a **Memoria `qmd_filter_mcp.py` wrapper** that "hides superseded claim notes by default" (`tool-registry.yaml` `qmd_read` comment; copi `config.yaml`; the underlying filter landed in `baa92e61`/#851 "filter superseded claims from qmd").
**Why:** Retrieval should not surface retracted/superseded claims as live evidence; wrapping qmd rather than trusting the raw index enforces this at the read boundary without qmd writing the vault.

**What (deferred/killed, notable):** Auxiliary model slots, per-lane `reasoning_effort`, Bitwarden shared secrets, and `gateway.multiplex_profiles` did **not** land — `grep` confirms no `reasoning_effort`/aux/`auxiliary` keys and **no `checkpoints:` block** remains in any shipped profile config.
**Why:** These were G3/G4 items explicitly conditioned on the `#859` baseline ("scope alpha.10 / defer / kill") and on test-vault pilots that "promote nothing without the post-change re-run" (execplan §3 fifth). The measurement-led stance is deliberate: "If stale facts / missed contradictions / retrieval misses / extraction errors are not top issues, the NLI/MaxSAT and warrant-checker work stays deferred" (execplan §3 third; release-plan §5 Out of scope). Bitwarden/multiplexing are also explicitly *not* security boundaries — kanban lane isolation and the policy gate remain the real boundaries (`tmp/hermes-017-recommendations.md`). *(The `checkpoints` removal reason is not stated verbatim in the docs I found — inferred: it is part of "Simplify profile and runtime surfaces" (#904) trimming a runtime surface the baseline didn't justify; marked as inference.)*

**What:** Profile redeploy drift resolved and profile/runtime surfaces simplified (`6f439e77`, `79e6ea43`); `distribution.yaml` version bumped to `0.1.0-alpha.10` on all five profiles.
**Why:** The checkpoint's Runtime Gate requires clean profile redeploy to `~/Memoria-test` with contract/cost doctors green (release-plan §2, validation-log confirms all 42 covered direct/egress tools hard-denied and cost doctor green for copi/librarian/writer).

---

### Gate / provenance / policy engine

**What:** `tool-registry.yaml`'s enforcement note changed from aspirational ("TODO — today writes are gated by path") to **active** ("the policy-gate plugin reads this on `pre_tool_call` and blocks calls outside the profile allowlist. Path writes still narrow through the lane-overrides"), and the `vault_read`/`vault_write` capability groups gained Hermes-0.17 tool names (`obsidian.get_content`, `obsidian.vault_read`, `obsidian.vault_write`) (`tool-registry.yaml` diff).
**Why:** The 0.17 upgrade renamed/added Obsidian MCP tool surfaces; the registry must enumerate them or the positive allowlist would leave the new names ungoverned. This makes the registry the enforced single source rather than a drift-check reference (ADR-27, ADR-28).

**What:** The homepage plugin's **provenance-lock entry removed** — `homepage` deleted from `plugin-provenance-lock.json` and `community-plugins.json`, and its vendored bundle deleted (`16c6844e`, ADR-115 Consequences).
**Why:** Retiring the startup plugin (see UI) means "one fewer vendored dependency and one fewer provenance lock to maintain" (ADR-115 Consequences).

---

### Pipeline / ingest / enrichment

**What:** No new extraction/enrichment machinery; the ingest MCP facade is unchanged, now with an explicit `tools.include: [ingest_pipeline]` filter (copi `config.yaml`).
**Why:** The baseline instrument asks whether extraction errors are a top issue and, if not, "keep API path / defer" — no evidence forced ingest changes this cycle (`tmp/current-state-baseline.md` §Ingest extraction). One creation-track note: ADR-119's `create()` engine is designed to route *both* the human form and the agent writers (`inbox.py`, ingest) through one path, but that unification is a later phase, not landed here (ADR-119 §4, Phasing).

---

### Retrieval / derived store

**What:** Retrieval reads now flow through the superseded-claim-filtering qmd wrapper (see Profiles/runtime), and the `#859` baseline defined an explicit **qmd rerank-on-vs-off** evaluation over ~20 known-target queries as the gate for any retrieval tuning.
**Why:** "If stale/retrieval/contradiction/extraction are not top issues, do not build more memory machinery yet" — the decision line is "keep qmd as-is / tune qmd / defer" and tuning was not selected (`tmp/current-state-baseline.md` §Retrieval; execplan §3 third).

---

### Discovery, UI, navigation, dashboards, panes

**What:** A **left-pane navigation rail** was added — a single pinned plain note `_nav.md` at vault root (`cssclasses: memoria-nav`, no `type`), with a **Now** zone (live Inbox needs-me count as Dataview inline-JS) over a **Places/Go** zone (Library · Knowledge · Project, each with one context badge); the saved **Memoria** workspace pins it as the first left tab at width 280, ahead of the file explorer; `memoria-nav.css` snippet added (`7dd390d9`, ADR-114).
**Why:** Space-switching previously happened only via nav rows on space dashboards opened in the main pane, leaving two gaps: no *ambient awareness* ("is anything waiting on me?" required entering the Inbox, contradicting ADR-70's ambient-health principle) and no *persistent orientation*. Counts use Dataview inline-JS because a Bases formula computes per-row and cannot emit a standalone count (ADR-114 Context/Decision). Bookmarks-core was rejected (can't carry live counts); rendering full dashboards in the rail was rejected as duplicating the main pane — "the left pane navigates and alerts; analytics live in the main pane."

**What:** **Inbox reclassified from a space to the queue** (`type: space`→`type: queue`, `dashboard: queue`), its in-note nav row removed, and its weekly views (Drift watch, Loose ends, Board) moved out; the **homepage front-door plugin retired** in favour of Obsidian native session-restore; `home.md` rewritten from a homepage fallback into a thin **first-run welcome seed** ("Welcome to Memoria… everyday navigation lives in the left-pane rail") pointed at by the Memoria workspace's main leaf (`16c6844e`, ADR-115, supersedes ADR-13).
**Why:** ADR-114 committed to "Inbox is a *state*, not a *place*" but three things still assumed the pre-rail world: Inbox-as-fourth-space, per-space nav rows, and forced-launch into the Inbox. Forcing the full queue as the launch workspace "casts a knowledge/writing tool as inbox-management, and — since empty is the goal — often lands the human on nothing" (ADR-115 Context #3). Session-restore returns the human to real work; the rail carries the ambient signal. Deleting `home.md` entirely was rejected because a new user benefits from a curated welcome and onboarding (ADR-113) needs a landing to attach to (ADR-115 Alternatives).

**What:** ADR-116 established the **View / Collection / Rail** surface vocabulary — a *View* is one Bases query defined once and surfaced by embedding (Dataview only for non-note JSONL sources and inline counts); a *space is a named collection of views*; the durable spaces are three (Library, Knowledge, Project) with **Queue** (daily, converges to empty) and **Maintenance** (weekly structural debt) split by cadence; operational-health stays a pull-only Dataview-over-JSONL collection (ADR-116 Decision).
**Why:** A clean-slate review found three overlaps in the accreted surface: two navigation taxonomies (rail-by-intent vs Portals-by-folder), two dashboard engines defining the same view twice (five drifted Dataview/Bases twins), and one queue mixing two cadences (decide-now beside review-Friday, violating "one decision per dashboard") (ADR-116 Context). The cadence split lets the Queue actually converge to empty (ADR-116 Alternatives).

**What:** **Five duplicate Dataview dashboard pages collapsed to single-definition Bases embeds** (Phase 1) — `contradictions`, `open-questions`, `discuss-queue`, `drift-watch`, `loose-ends` now embed `![[claims.base#Contradictions]]` etc. (`9677e42f`); this also **fixed the drift-watch ordering defect for free** (the Dataview page string-sorted `loudness` alphabetically; the base view sorts by `loudness_rank`: block→alert→notice).
**Why:** Each page re-queried in Dataview what a `.base` view already defined and a space already embedded; the twins had already drifted in columns and sort order — "proof that two definitions of one view is a defect surface, not a feature" (ADR-116 Alternatives; `9677e42f` body). A stale "push to Home" clause was also dropped (ADR-115 retired Home as a surface).

**What:** **`system/dashboards/` reduced from 13 `.md` to 5** (ADR-118 dashboard consolidation, `fd5c9f00`): six pages deleted (contradictions, open-questions, discuss-queue, drift-watch, loose-ends, and `reading-pipeline`), their deep-links repointed at space-section anchors; `project-gate.base`/`project-gate.md` merged into `projects.base` + the Project space; `weekly-review.md` retired with its unique "New this week" 7-day digest folded into the new **Maintenance** space note. The five read-only system dashboards (`board-state`, `audit-log`, `eval-trend`, `fleet-health`, `skill-state`) stay in `system/`.
**Why:** ADR-116's View primitive means a standalone page whose view already lives in a space is redundant. `reading-pipeline.md` also carried a *broken embed* (`![[sources.base#To read & distill]]` referenced a non-existent view; the real one is `Reading pipeline`) that rendered empty — deleting the page removed the bug. The system dashboards are *read-only internals hidden by Portals*, not user work-contexts, so a "System space" was rejected as repeating the Inbox-as-a-space error (ADR-118 Decision, Alternatives). `tests/test_bases.py` was hardened to assert the `#View` name exists — the gap that let the broken embed stay green.

**What:** The **read-only Inspector pane became the system index** (ADR-118 §5, `main.js`): added a **fleet/trust band** reading per-lane trust from `system/metrics/lane-*` notes, and **deep-links each panel to its full dashboard** (board→`board-state`, audit→`audit-log`, verdict→`spaces/maintenance#Drift watch`, fleet→`fleet-health`), carrying only *continuous* signals (episodic `eval-trend`/`skill-state` stay pure pull dashboards).
**Why:** ADR-84's Inspector is the natural always-on read-only window but predated the operational dashboards it should summarize and overlapped the new rail health-band; the fleet band is "the one continuous system-health signal the Inspector currently lacks." It is deliberately reconciled with the rail: "the rail's Now band is the one-glance ambient signal; the Inspector is the read-only detail panel it points to. Ship one signal + one panel — not two competing health surfaces" (ADR-118 §5).

**What:** ADR-116 Phase 3 (**fold Portals into the rail as a stacked Now/Go/Find spine**) was **retired**; the left pane stays two sibling tabs — the rail (Now + Go) and Portals (the object browser) (`5c09aa99`, `d7c5aada`, `328e5146`; ADR-116 Amendment).
**Why:** PR #908 settled the two-tab arrangement; the spine "regresses file-tree height and is only visual — the intent-vs-storage taxonomy overlap survives whether the two are tabs or stacked, so the spine doesn't deliver the consolidation that motivated it." Intent-navigation (rail) and object-browsing (Portals) are accepted as complementary axes (ADR-116 Alternatives, commit body).

---

### Onboarding / tutorials / distribution / sample vault

**What:** A **bundled sample vault** ("mediterranean-diet", ~8 sources / ~15 claims, deliberately half-built) ships in the installer scaffold under `.memoria/samples/mediterranean-diet/` (added to `folders.yaml` skeleton), with `Memoria: load sample vault` / `remove sample vault` QuickAdd commands (`load-sample-vault.js`, `remove-sample-vault.js`) that copy into / clean `catalog/`+`notes/` without overwriting user work (`f96b31ab`, `28540227`, ADR-111 retained by ADR-112).
**Why:** Done for real the knowledge loop takes months, so a one-sitting tutorial can't reproduce the payoff (writing from a *dense* claim graph) without pre-existing state; a seeded half-built corpus the learner *finishes* is the resolution, doubling as an end-to-end test fixture and demo. Crucially the seed is **authored from real sources, never LLM-generated** — "provenance *is* the product; because learners imitate the form they are shown, a faked seed teaches fabrication of the exact thing the system prevents" (ADR-111 Decision/Consequences/Alternatives, backed by the deep-research pass over PKM/sample-DB-pedagogy/onboarding/learning-science). The `sample: bool` frontmatter flag lets Maintenance's "New this week" digest exclude sample docs and the remove command find them.

**What:** The **tutorial arc was rebuilt as one destination-first project arc** — the seven old pipeline-ordered tutorials (`01-set-up-from-zero`…`07-find-new-sources`) were deleted and replaced by seven (`01-orient` … `06-close-the-loop` … `07-make-it-your-own`): orient by *reading* the Co-PI's coverage map → capture → distill&connect (faded) → draft (payoff) → verify → close the loop → graduate; **setup was excluded** and delegated to the Quickstart (ADR-112, `00978952`/`b361acad`, supersedes ADR-111's spine).
**Why:** The old spine "is the ontology sequenced — it starts on the wrong object (the fleeting note, the system's cheapest object, not how a researcher enters) and draws a loop as a line." Re-derived from Diátaxis + learning-science: setup "has one right way and teaches no Memoria idea by doing — it is how-to," and embedding it duplicated the Quickstart and the two copies drifted (restart-Obsidian/git-init present in one, absent in the other). Opening with the map "sells Accumulate via the visible gap — something a from-scratch vault cannot do but the seed can" (ADR-112 Context/Decision/Alternatives). Beat 3 must include one rep of distilling the learner's *own* source because transfer requires the fade-to-own-data to happen inside the lesson.

**What:** A new **"Your first month" practice guide** was added (`docs/explanation/knowledge/your-first-month.md`, `cd544392`).
**Why:** The months-long real-time rhythm is a *habit*, not teachable by-doing in a sitting — "cramming the real timeline into a by-doing tutorial is a genre mismatch," so it belongs in a practice guide separate from the tutorials (ADR-111/112).

**What:** ADR-113 (**Co-PI-guided conversational onboarding**) was recorded as `proposed`/deferred.
**Why:** The AI-native end state is the Co-PI walking the first loop in conversation, but "the ADR-112 doc arc is the script the agent layer would dramatize, so it must exist and stabilize first; building the agent layer against a moving doc flow would mean syncing two moving targets." Kept on record with preconditions rather than built (ADR-113).

**What:** Setup/reference docs reorganized — sample-vault reclassified as reference (`docs/reference/sample-vault.md`, `docs/how-to-guides/setup/sample-vault.md`), a new `docs/reference/configuration.md` documenting Memoria configuration surfaces, `set-up-messaging.md` **deleted**, `use-the-vault-homepage.md` → `use-the-vault-launch-screen.md`, `use-the-acp-pane.md` → `use-the-agent-client-pane.md` (`eff1f908`, `3949332a`, ADR-115).
**Why:** Homepage retirement (ADR-115) renamed the launch surface; messaging setup was dropped consistent with the eval keeping messaging/deliverable tools out of core lanes ("Skip; they do not improve core Memoria requirements today").

---

### Distribution / evaluation / release process

**What:** `scripts/verify` now defines the **Source / Package / Runtime / Product / Release gate** vocabulary and a `scripts/verify rc` prefix; the release-candidate runbook and testing plans were updated to it (release-plan §2–3; `c9114349` "promotion-gated verification process").
**Why:** alpha.10 changed profiles, policy shape, navigation, embeds, forms, and sample-vault behavior, so the checkpoint needed a named gate structure where "This file defines the gates; issue state is the source of truth" and Runtime/Product remain attended (CI can prove Source+Package but GUI/live-MCP need a local host) (release-plan §2, Known limitations).

**What:** A **weekly Hermes version-check CI issue** was added (`deb8b69f`, #862).
**Why:** The whole release began from an out-of-date runtime discovered manually; automating a weekly upstream check surfaces the next upgrade before it becomes a blocker (inferred from commit + the 0.14→0.17 drift that opened alpha.10).

**What:** alpha.10 closes as an **internal checkpoint** — `status: complete`, `released: false`, no tag/release-please PR/GitHub Release (release-plan front-matter §10; validation-log Release close-out).
**Why:** The scope is "validation and documentation, not new feature work" — proving the post-alpha.9 repo/vault-tree/test-runtime are coherent — so a formal public release is explicitly out of scope (release-plan §1, §5).

**What:** All alpha.10 release **scratch (`tmp/`) was disposed** — the execplan, both Hermes eval reports (Claude + Codex), the recommendations memo, the upgrade record, the baseline instrument, and the two smoke probes (`probe-qwen-compliance.py`, `spike-nli-vs-cosine.py`) were deleted at closeout (`450f659d`).
**Why:** Per the closeout protocol: selected findings route to ADRs/issues, superseded copies are deleted, and scripts are deleted after their result is recorded (execplan §Finally, release-plan §9). A recurring correction preserved from the eval: the local `provider: custom`/`qwen2.5:7b` render is *test-vault evidence, not the production target* — production Memoria runs Kilo — so production strategy must not be inferred from it (`tmp/hermes-017-recommendations.md` Provider baseline; execplan §3).

---

### Security

**What:** `hermes security audit` was recommended for release/runbook validation (third-party MCP + Python dependency drift), and the reconciled architecture reaffirms the **ADR-22 lane/MCP-only bet**: agents get no direct file/terminal/code-execution/web/messaging tools for vault work; canonical knowledge stays in the vault, not external memory providers; the Nous Tool Gateway stays off (`tmp/hermes-017-feature-eval.md` Clean-slate architecture, "correctly excluded").
**Why:** The 0.17 eval re-tested each new upstream capability against Memoria's requirements and confirmed the exclusions still hold — Bitwarden/multiplexing "reduce service sprawl but are not a policy boundary," so "kanban lane isolation and the Memoria policy plugin stay unchanged" (execplan §3 fifth). The concrete security hardening that *landed* is the `session_search` deny + profile-scoped `memory` + positive `platform_toolsets` (see Gate/Runtime).

---

### ADRs governing this release

| ADR | Status | Decision | Note |
|---|---|---|---|
| **111** | superseded (by 112) | Two-mode (Accumulate/Produce) tutorial spine + seeded half-built corpus | Spine superseded; **seeded sample vault + load/remove commands retained** by ADR-112 |
| **112** | accepted | Onboarding = one destination-first project arc; setup excluded | Supersedes ADR-111's spine |
| **113** | proposed/deferred | Co-PI-guided conversational onboarding | Assumes 112; preconditioned on a stable doc arc + a Co-PI onboarding skill |
| **114** | accepted | Left pane is a navigation rail (Now over Places), never a second dashboard | Per-space object browsing in the rail deferred |
| **115** (inbox-queue) | accepted | Inbox is the queue not a space; retire homepage front door for session-restore + welcome seed | **Supersedes ADR-13** |
| **115** (profile-config) | accepted | Profile capability blocks materialized from `tool-registry.yaml` | **Duplicate ADR number** — two distinct ADRs share id 115 in the repo |
| **116** | accepted | Obsidian surface = View/Collection/Rail + two edges (Home, Co-PI) | Phase 1 shipped; **Phase 3 (spine) retired** |
| **117** | accepted | Document-type naming scheme (kind-scoped singular nouns; no folder/space collision); "note type"→"document type" | `notes/` kept, no path migration |
| **118** | accepted | Dashboard consolidation: fold redundant pages into spaces; keep 5 system dashboards read-only; Inspector = read-only system index | Refines 116/84/70 |
| **119** | accepted | The type schema is the complete declarative contract that validates, generates, and is the single source | Phased; invariants+schema-owned-forms landed, index type dropped |

**Retired / removed this release, and why:**
- **`index` document type + `notes/indexes/` folder** — schema didn't match purpose; register function already covered by `hubs.base#Hubs index` (ADR-119 §6).
- **Homepage community plugin (bundle + config + provenance-lock entry)** — forced landing duplicates the rail's ambient signal and discards working context; native session-restore replaces it (ADR-115, `16c6844e`).
- **Six `system/dashboards/` pages + `project-gate` + `weekly-review`** — redundant with space-embedded views; one broken embed removed with them (ADR-118, `fd5c9f00`).
- **Per-space nav rows on the four space notes** — the rail owns switching (ADR-114/115).
- **ADR-116 Phase 3 (Portals-into-rail spine)** — only visual, regressed file-tree height, didn't fix the taxonomy overlap (ADR-116 Amendment).
- **`set-up-messaging.md` how-to; `checkpoints:` profile block; hand-authored profile capability blocks** — messaging is out of core lanes; profile configs now generated from the registry; checkpoint removal is part of runtime-surface simplification (*inferred*, #904).
- **Deferred (not killed):** auxiliary model slots, per-lane `reasoning_effort`, Bitwarden, gateway multiplexing, NLI/MaxSAT contradiction automation, model-free warrant checking — all gated behind the `#859` baseline / test-vault pilots and not selected for alpha.10 (execplan §3, release-plan §5).
