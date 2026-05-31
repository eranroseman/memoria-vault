---
topic: profiles
---

# Hermes profiles

Hermes is the worker layer, split into seven specialist profiles. Each has a focused mission, narrow folder permissions, a small command surface, the skills it actually needs, and an explicit set of MCPs / external tools. **Profiles never share permissions by default — every privilege is granted, not inherited.** This document is the authoritative reference for what each profile can do, what it cannot do, and how the seven relate to each other.

> **Naming.** Prose refers to a profile by its short name (Librarian, Writer, …); its runtime identity is `memoria-<name>` (`memoria-librarian`, `memoria-writer`, …) — the same profile. Use the short name in prose and `memoria-*` in any config, lane-override, or policy reference.

## What's in this document

**What the profiles are** — [The seven profiles](#the-seven-profiles), [Core design rule](#core-design-rule) (the load-bearing principle), [Profile boundaries](#profile-boundaries).

**Permissions and constraints** — the lookup tables (Lane permissions matrix, Invocation levels, Folder permission matrix) live in [profile-matrices.md](../../reference/profile-matrices.md); the YAML encoding is in [Lane-override files](#lane-override-files) below.

**Dispositions and dynamics** — [Delegation ladder](#delegation-ladder), [Routing without an Orchestrator](#routing-without-an-orchestrator), [Inter-profile handoff patterns](#inter-profile-handoff-patterns).

**Extension and per-profile detail** — [Skill governance (deferred)](#skill-governance-deferred), [Per-profile contracts](#per-profile-contracts), [Coder ↔ external coding agent](#coder--external-coding-agent), [Commands](#commands).

**Operational concerns** — [Workflow ownership](#workflow-ownership), [Scaling](#scaling), [Anti-patterns](#anti-patterns).

## The seven profiles

A profile **is** its lane — the `assignee` value the dispatcher routes by; there is no separate lane name.

| Profile | Invocation level | One-line mission |
| --- | --- | --- |
| **Librarian** | Level 1–2 (background + Kanban) | Find, ingest, enrich, and classify evidence. Optimistic. |
| **Mapper** | Level 2 (Kanban-pulled) | Map the corpus for a project: scope reports, gap reports, cluster density. Read-only across vault. |
| **Socratic** | Level 3 (interactive) | Sharpen the human's thinking through questioning and lens-based reading. Architecturally write-denied. |
| **Writer** | Level 2 with review gate | Turn evidence into drafts, answer notes, and reference-ready prose. |
| **Verifier** | Level 2 (Kanban-pulled) | Trace claims to sources; verify citations; flag duplicates and retractions. Read-only across vault except verification reports. |
| **Coder** | Level 2 (external dispatch) | Build and maintain code artifacts, scripts, repos. Transactional. |
| **Linter** | Level 1 (scheduled) | Validate structure, metadata, schema, link health. Default dry-run. Also owns session-log and audit-trail housekeeping. |

**No Orchestrator, no Reviewer.** Routing lives in lane-overrides and Kanban dispatch — see [Routing without an Orchestrator](#routing-without-an-orchestrator). The review gate rides on the card's `review_status` (a `done` card with `review_status: requested`, promoted to `approved`) enforced by the policy MCP; the mechanical parts of review (claim tracing, similarity, retraction) live in Verifier, the judgment parts with the human.

## Core design rule

**Profiles own outcomes; lanes own claimability.**

A profile is a durable identity with a domain — librarians discover, mappers chart, writers synthesize, verifiers verify. The profile is responsible for the quality of its outputs.

A lane is a board-level contract about *who can claim a card*. The lane tells the dispatcher which profile class is allowed to move a card forward; the exit state is part of the lane contract.

The two work together:

- If a card is in the library lane, only Librarian-class workers may claim it.
- If a card is `done` and awaiting review (`review_status: requested`), only the human may clear it (no Reviewer profile to do so).
- When a worker finishes its slice, it completes the card to `done` with `review_status: requested` — it does not mark the work approved.

This is what prevents "everything becomes orchestration." Each profile stays accountable for what it ships.

## Profile boundaries

The profiles are most easily confused in pairs. Each row states the distinction once; the per-profile design summaries carry only the angle unique to that profile.

| Pair | The distinction |
| --- | --- |
| Librarian ↔ Mapper | Librarian fetches *new* sources from outside; Mapper maps what's *already* in the corpus. Shared retrieval tooling, opposite direction. |
| Librarian ↔ Verifier | Librarian proposes optimistically; Verifier checks conservatively. The asymmetry is the design. |
| Librarian ↔ Writer | Librarian curates evidence; Writer composes claims from it. |
| Mapper ↔ Writer | Mapper produces maps; Writer produces arguments from them. |
| Mapper ↔ Verifier | Both read-only. Mapper surveys corpus *structure*; Verifier traces claim *provenance*. |
| Mapper ↔ Socratic | Mapper emits structured artifacts over the whole corpus; Socratic converses about one source at a time. |
| Socratic ↔ Writer | Sequential, not interchangeable: Socratic asks questions in the Discuss stage; Writer drafts prose in the Draft stage. |
| Writer ↔ Verifier | Writer drafts and makes tracing *possible*; Verifier does the tracing. Writer must not pre-empt the checks. |
| Verifier ↔ Linter | Both check mechanically. Verifier checks content *provenance* (citations, traces, duplicates) — content-aware; Linter checks *structure* (schema, links, file shape) — content-agnostic. They compose. |
| Coder ↔ Writer | Coder produces the code artifact; Writer produces the prose *about* it. |
| Coder ↔ Linter | Linter validates structure deterministically; Coder produces code, delegated to an external agent. |
| Coder ↔ external coding agent | Coder scaffolds the handoff (`code-note`) and documents provenance; the external agent writes the code. |

Beyond these pairs, each profile has non-overlap negations in its own design summary (e.g., Librarian is *not autonomous about classification*, Verifier is *not an LLM-as-judge*, Linter is *not a fixer by default*).

## Permission matrices (in the reference)

The three lookup tables that used to live here — the **Lane permissions matrix** (skills, tools, denials, write scope per lane), the **Invocation levels** (cadence per profile), and the **Folder permission matrix** (folder × profile access map) — are pure reference and now live in [profile-matrices.md](../../reference/profile-matrices.md). The YAML form the policy MCP actually reads is in [lane-override files](#lane-override-files) below. Two principles from those tables are load-bearing enough to restate here, because they're design invariants and not just lookups:

- **Socratic is write-denied; Mapper and Verifier are canonically read-only.** Socratic has `policy.allow.write: []` — no writes anywhere. Mapper and Verifier have `canonical_read_only_mode` — any allowed write outside their declared scratch paths is a configuration bug.
- **No lane writes to review-gated zones.** The four review-gated zones are policy-MCP `dry_run` for every lane. Promotion is always synchronous with human attention.

## Lane-override files

The folder permission matrix above is the human-readable summary. The machine-readable encoding lives in **lane-override files** at `.memoria/lane-overrides/{lane}.yaml`. One file per lane. The policy MCP reads these at startup and enforces them at every write (see [architecture/policy-mcp.md](../../reference/architecture/policy-mcp.md)).

### File shape

Each lane-override has the same four blocks. Example for the library lane:

```yaml
lane: library
profile: memoria-librarian

policy:
  allow:
    skills:
      - paper-lookup
      - pyzotero
      - citation-management
    write:
      - "10-inbox/**"
      - "20-sources/**"
  deny:
    skills:
      - review_gated_publish
    write:
      - "30-synthesis/**"
      - "50-deliverables/**"
  require:
    - audit_log
    - timeout_required
    - source_tracking

routing:
  external_api_policy: explicit_only        # blocked | explicit_only | open
  write_scope:                               # the lane's authoritative short-list
    - "10-inbox/"
    - "20-sources/"
```

The four blocks:

- **`policy.allow`** — skills the lane may load and paths it may write. Patterns are glob-style relative to the vault root.
- **`policy.deny`** — explicit blocks. Deny wins over allow.
- **`policy.require`** — invariants the worker must honor. Common values: `audit_log` (every action logged), `timeout_required` (no unbounded calls), `source_tracking` (writes carry a provenance trail), `read_only_mode` (no writes at all — used by Socratic only), `canonical_read_only_mode` (no writes to canonical vault zones; project-scratch writes to declared paths in `40-workbench/` are allowed — used by Mapper and Verifier), `review_gated_write` (writes to review-gated zones always degrade to `dry_run`).
- **`routing.write_scope`** — the authoritative short-list, usually narrower than `policy.allow.write`. Used by the dispatch rules to decide where a worker's output should land by default.
- **`routing.invocation`** — how the lane is invoked. `dispatched` (default; the Kanban dispatcher pulls cards from this lane's queue) or `interactive_only` (the lane is never queue-dispatched; only synchronous human invocation reaches it). Socratic uses `interactive_only` so a misconfigured cron job can't queue work onto a write-denied conversational profile.

### One file per lane

| Profile | Lane-override file | Notes |
| --- | --- | --- |
| Librarian | `.memoria/lane-overrides/librarian.yaml` | May call external APIs through approved skills. |
| Mapper | `.memoria/lane-overrides/mapper.yaml` | `canonical_read_only_mode` — no canonical writes; project-scratch writes only (`40-workbench/*/01-map/`). |
| Socratic | `.memoria/lane-overrides/socratic.yaml` | Hard `policy.allow.write: []` — write-denied across the vault (`read_only_mode`). `routing.invocation: interactive_only` — never queue-dispatched. |
| Writer | `.memoria/lane-overrides/writer.yaml` | May draft and refine; no direct external API; review-gated-zone writes degrade to `dry_run`. |
| Verifier | `.memoria/lane-overrides/verifier.yaml` | `canonical_read_only_mode` — no canonical writes; verification-report and gap-candidate writes only (`40-workbench/*/05-verification/`, `10-inbox/03-candidates/`). |
| Coder | `.memoria/lane-overrides/coder.yaml` | Writes to `40-workbench/*/06-code/` only. |
| Linter | `.memoria/lane-overrides/linter.yaml` | Dry-run by default; `auto_fix` is class-gated by the policy MCP; owns `00-meta/02-logs/` for session and audit-trail housekeeping. |

### Why not encode this in `config.yaml`

The profile-level `config.yaml` says what the profile *is* — model, command surface, skill registry, base MCPs. The lane-override says what the profile *may do in this vault*. The split lets the same profile run against multiple vaults with different policies, and it lets us review permissions independently of model and tooling.

### Composability

Two files compose at session start:

1. `~/.hermes/profiles/memoria-<profile>/config.yaml` — model, command surface, skill registry, base MCPs.
2. `.memoria/lane-overrides/<lane>.yaml` — policy and routing for this vault.

If a worker would claim a card outside its lane override, the policy MCP returns `deny`. If a worker tries to write into a review-gated zone, the MCP returns `dry_run` and the action becomes a board comment for the human to act on. Either way, nothing canonical changes without an explicit approval step.

## Skill governance (deferred)

**Status: deferred — maybe later if needed.** Adding a skill today is purely a runtime operation: edit the relevant lane-override file's `policy.allow.skills` list and drop the `SKILL.md` into the right `.memoria/profiles/memoria-<name>/skills/` folder. The richer lifecycle discipline — state machine, per-skill governance notes in `00-meta/07-skills/`, the `skill-lifecycle` dashboard, the 7-step onboarding checklist, and the passthrough-to-dedicated-skill graduation thresholds — is a future possibility documented in [roadmap/skill-governance.md](../../project/roadmap/skill-governance.md) but not active in the current design.

### Skills with restrictive policy

Most skills inherit their host lane's policy unchanged. A small set of skills *tighten* it further by declaring additive `policy.deny` rules in their SKILL.md frontmatter. The mechanism (composition semantics, enforcement path, frontmatter contract) lives in [architecture/policy-mcp.md](../../reference/architecture/policy-mcp.md#skill-conditional-policy); the **catalog** of Memoria's restrictive skills lives here:

| Skill | Loaded by | What it adds | Why |
| --- | --- | --- | --- |
| `counter-outline` | Writer | `deny: write:30-synthesis/**`, `deny: write:50-deliverables/**`, `deny: write:10-inbox/**` — scratch-only | Generates 2–3 competing project outlines before drafting begins. Outputs land in `40-workbench/*/02-framing/` only; "first outline wins by default" is the failure mode this prevents. Loaded only when Writer is in the Frame stage of a downstream pipeline. |

The shared property: a skill's deny rules are stricter than the host lane's. A `counter-outline` session under Writer is more restricted than Writer's baseline, never more permissive — and the narrowing is enforced at the policy MCP, not by prompt discipline.

**Note on what's NOT here.** Earlier versions of this design had `socratic-processing` and `lens-reading` as restrictive skills. They've been promoted to a profile (Socratic) whose lane policy is `policy.allow.write: []` natively. Profile-level enforcement is stricter than skill-level enforcement because it can't be sidestepped by loading the host profile without the skill. The skill-conditional-policy mechanism is preserved for `counter-outline` and any future scratch-only skills that are too narrow to justify their own profile.

## Per-profile contracts

Each profile's operational contract — exact allowed folders, commands, skills, tooling, rules, and exit conditions — lives in its own SOUL.md file in the starter vault. These are the runtime contracts that Hermes reads at session start; the design documents summarize, the SOUL.md files specify. Each design summary follows the shared [design-summary page template](../../reference/templates/design-summary-template.md).

| Profile | Design summary | Runtime contract (SOUL.md, in starter vault) |
| --- | --- | --- |
| Librarian | [profiles/librarian.md](librarian.md) | `.memoria/profiles/memoria-librarian/SOUL.md` |
| Mapper | [profiles/mapper.md](mapper.md) | `.memoria/profiles/memoria-mapper/SOUL.md` |
| Socratic | [profiles/socratic.md](socratic.md) | `.memoria/profiles/memoria-socratic/SOUL.md` |
| Writer | [profiles/writer.md](writer.md) | `.memoria/profiles/memoria-writer/SOUL.md` |
| Verifier | [profiles/verifier.md](verifier.md) | `.memoria/profiles/memoria-verifier/SOUL.md` |
| Coder | [profiles/coder.md](coder.md) | `.memoria/profiles/memoria-coder/SOUL.md` |
| Linter | [profiles/linter.md](linter.md) | `.memoria/profiles/memoria-linter/SOUL.md` (plus `M-detectors.md`) |

The tables in this document and in [profile-matrices.md](../../reference/profile-matrices.md) — folder permission matrix, command summary, lane mapping, delegation ladder, workflow ownership — are the architectural *summary*. For the specific permission lists, dry-run defaults, and exit conditions per profile, read the SOUL.md.

## Coder ↔ external coding agent

The Coder profile is **narrow by design**: it scaffolds `code-note` handoffs and documents provenance. The actual editing happens in a specialized external coding agent (Kilocode, Aider, Claude Code, Codex) running as a peer with a shared filesystem — the vault is its read-only context, `40-workbench/*/06-code/` is its write zone, and the human reviews `code-note` updates as the review gate. No orchestration infrastructure is needed: the two agents coordinate through the markdown handoff, not through subprocess dispatch.

**Full mechanism** — the two-agent boundary, VS Code workspace JSON for "small scripts in the vault" vs "real projects in their own repo," the `files.readonlyInclude` boundary, agent-instruction-file placement (`CLAUDE.md` / `.kilocode/rules/` / `.cursorrules`), the rule of thumb for when a project earns its own repo, and the `repo:` frontmatter convention on the `code-note` — lives in [external-agent-workspace.md](../../how-to/coder/external-agent-workspace.md). The same pattern generalizes to **external rendering agents** (open-design) for visual deliverables, with `50-deliverables/` as the write zone and the `deliverable` note as the handoff artifact.

## Commands

Each profile's core verbs are listed in the [Lane permissions matrix](../../reference/profile-matrices.md#lane-permissions-matrix). The full operational command catalog — every command, owner profile, and dry-run default — lives in [profile-commands.md](../../reference/profile-commands.md). The rule: any command that writes to a review-gated folder or runs a migration must default to dry-run.

## Routing without an Orchestrator

Routing — "which profile picks up this card?" — is rule-encoded, not reasoned. Three mechanisms together:

1. **The card's `assignee` (its lane)** determines which profile is eligible to claim it. A card assigned to the mapping lane can only be claimed by a worker whose lane-override file declares it on that lane. There is no separate `lane` field — the lane *is* the `assignee`.
2. **The lane-override file's `routing.write_scope`** declares where that worker's output should land by default, so the worker doesn't have to decide.
3. **The Kanban dispatcher** picks the highest-priority eligible card from each lane's queue when a worker becomes available. Priority is set at card creation (cron-triggered work is usually low-priority; human-initiated is high).

There is no reasoning step. If the rules can't decide (two profiles eligible, or none eligible), the card sits in `ready` (unclaimed) until the human intervenes. This is the design — silent reasoning about routing is exactly what the policy MCP exists to prevent.

When a card needs to move between lanes (e.g., from library to verify after ingest), the *worker that just finished* moves it. The Librarian who completes an ingest moves the card to the `verify` lane's queue if a similarity check is needed; the Writer who commits a draft fires the verify-on-commit hook. No central agent makes these decisions; the workflow does.

## Delegation ladder

Delegation is strongest in profiles that produce derivative artifacts (drafts, code-notes), weakest in profiles whose value depends on independence or non-production.

```text
Delegation posture — strongest at top. Delegate narrow, temporary subtasks;
never the role's defining judgment.

  more ┌──────────────────────────────────────────────────────────────────┐
   ▲   │ Coder      Moderate    helper/lookup + substantive coding to the   │
   │   │                        external agent; commits stay per-task       │
   │   │ Writer     Supportive  facts / cleanup; synthesis stays local      │
   │   │ Librarian  Targeted    narrow enrichment / source lookups;         │
   │   │                        keeps discovery ownership                    │
   │   │ Mapper     Low         mechanical retrieval (qmd); keeps the map    │
   │   │ Verifier   Very low    delegation weakens verification independence │
   │   │ Linter     Lowest      does not spawn work; may request context    │
   ▼   │ Socratic   None        can't write; questions are the whole product│
  less └──────────────────────────────────────────────────────────────────┘
```

| Profile | Delegation posture |
| --- | --- |
| Librarian | **Targeted.** Delegates narrow enrichment or source lookups; keeps discovery ownership. |
| Mapper | **Low.** Delegates only mechanical retrieval (e.g., to qmd for vector search). Keeps the map authorship. |
| Socratic | **None.** Socratic has nothing to delegate — questions and conversations are the whole product. Cannot delegate writing because it can't write. |
| Writer | **Supportive.** Delegates facts or cleanup; keeps synthesis ownership. Final draft remains local. |
| Verifier | **Very low.** Delegation weakens verification independence. Inspects, traces, flags. |
| Coder | **Moderate.** Delegates helper work, formatting, lookup; keeps implementation control. Commits stay per task. Also delegates substantive coding work to the external coding agent via handoff payloads — see the Coder section above. |
| Linter | **Lowest.** Does not spawn work. May request context, but its job is to validate, report, and log. |

Rule: delegate narrow, temporary, low-risk subtasks; never delegate away the role's defining judgment.

## Workflow ownership

Each workflow has a primary profile. The authoritative view — workflows × profiles, with primary / support / no-claim distinctions across all 18 workflows — is the [Role × stage matrix in workflows/README.md](../workflows/pipeline-design.md#role--stage-matrix). Don't duplicate it here; keep one source of truth.

## Inter-profile handoff patterns

The recommended handoff chain for a typical upstream card (source → claim):

```text
Librarian  ──► [classify-pending]  ──► (human classifies)  ──► [discuss-pending]
                                                                  │
                                       (human switches to Socratic; conversation; no writes)
                                                                  │
                                       (human writes claim note in Writer profile, with Verifier doing similarity-check at filing time)
                                                                  │
                                                                  └──► [distilled]
```

The recommended handoff chain for a typical downstream card (project → deliverable):

```text
Mapper  ──► [scope-review]  ──► (human decides project is ready)  ──► Writer with counter-outline
                                                                                          │
                                                                                          └──► [framing-review] ──► (human chooses framing)
                                                                                                                          │
                                                                                                                          └──► Writer (draft)
                                                                                                                                  │
                                                                                                                                  └──► Verifier (on commit) ──► [revise or export]
```

Linter can act at any point, on any card, with a dry-run report attached as a comment. Socratic is invoked synchronously by the human and never appears in queue-based handoff chains. The Coder operates in parallel for code artifacts.

## Scaling

The seven-profile design is the full Memoria design, but the system supports graduated starts: a **mode-based** single Hermes for the simplest setup, a **four-profile** minimal configuration (Librarian + Writer + Verifier + Linter) when seven is too much, and the full seven when volume warrants it. The trade-offs and the migration path are documented in [roadmap/README.md](../../project/roadmap/README.md#implementation-paths-graduated-start) — they belong with the implementation timeline, not the profile contracts.

## Anti-patterns

These are the patterns to avoid, drawn from observation of single-agent systems:

- **Profile bleed.** A Librarian writes synthesis. A Writer ingests new sources. Each profile blurs into the next. Symptom: ambiguous responsibility for quality issues.
- **Silent canonization.** A worker says "I'm done"; the system treats that as approval. Symptom: drift between what's marked approved and what was actually reviewed.
- **Re-introducing an orchestrator.** The temptation to add "a profile that decides where work goes" arises when routing rules feel complex. Resist it — encode the rule in the lane-override file or the dispatch policy, not in a reasoning agent. Once a reasoning orchestrator exists, every routing decision becomes hard to audit.
- **Tooling spread.** Every profile gets every MCP. Symptom: profiles can do work outside their lane; debugging becomes unreliable.
- **Linter as auto-fixer.** The Linter silently corrects orphans, retags notes, moves things to archive. Symptom: vault state diverges from human intent without notice.
- **Socratic with write access.** Even a tiny write scope on Socratic ("just to scratch") defeats the architectural protection. Socratic's `policy.allow.write: []` is load-bearing.

The structural guard against all of these is in the permission matrix and the board states. Treat them as non-negotiable.
