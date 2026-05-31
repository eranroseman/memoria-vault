---
topic: reference
---

# Glossary

Term definitions for Memoria, organized by domain. One definition per term; disambiguation noted where a term has multiple senses. For conceptual depth see [explanation/](../../docs/explanation/).

---

## System

**ACP** (Agent Client Protocol) — the editor-level protocol that exposes Hermes profiles to IDE and editor chat panes (Obsidian, VS Code). Gives the human a conversational interface to a profile from inside the editor. Distinct from the Obsidian Local REST API (which gives Hermes vault-level read/write access).

**Canonical** — approved as the authoritative, immutable form of a piece of knowledge until explicitly archived. Human approval is always the final gate. *Also used informally as "the authoritative version" — these are separate senses.*

**Hermes** — the Nous Research agent runtime Memoria runs on. Provides Kanban, profile management, MCP server connections, skill installation, and the gateway process.

**Human** — the person who owns and runs the vault. Makes all approval, triage, and promotion decisions. Single-user by design.

**Memoria** — the whole system: the vault, the seven profiles, the policy MCP, the Kanban board, and the tooling layer (`.memoria/`).

**Memoria v0.1** — the complete initial configuration on a single device (`local-only`): all seven profiles, all 15 templates, all 10 dashboards, the Kanban board, ACP plugins, and K-Dense skills. No component is optional. See [roadmap/README.md](../../docs/project/roadmap/README.md#memoria-v01).

**Profile** — a Hermes role with bounded permissions, commands, skills, and tools. Memoria defines seven: Librarian, Mapper, Socratic, Writer, Verifier, Coder, Linter. No Orchestrator (routing is static, in lane-overrides) and no Reviewer (review is a human action).

**Vault** — the Obsidian folder tree where durable knowledge lives, organized by lifecycle stage: `00-meta`, `10-inbox`, `20-sources`, `30-synthesis`, `40-workbench`, `50-deliverables`, `90-assets`, `95-archive`.

---

## Board and cards

**Archive reason** — why a card was archived: `superseded` (a new card replaces it) or `discarded` (work abandoned). Stored in `metadata.archive_reason`. Distinct from `outcome` (what happened during execution).

**Card** — a task on the Hermes Kanban board. Carries `status`, `assignee`, `reason` (if blocked), retry count, and a handoff summary. Lives in `kanban.db`.

**Dispatcher** — the Hermes component that polls the board every 60 seconds, claims `ready` cards for matching-lane profiles, and advances them to `running`. Does not make quality or approval decisions.

**Escalation threshold** — `max_retries` (default `3`): after this many recoverable failures, a card auto-moves to `blocked`. Per-lane configurable.

**Handoff payload** — the structured `summary` a worker writes on `kanban_complete`, containing: `task`, `result`, `allowed_paths`, `promote_target`, `context_notes`. Self-contained so the next worker needs nothing else.

**Lane** — a profile's execution path on the board. A lane *is* an `assignee` value (`memoria-<name>`); there is no separate `lane` field. Socratic is a profile but not a lane — it runs synchronously, off the board.

**Lane exit contract** — what a lane guarantees when its card reaches `status: done`: which review signal is attached and what "done" means for that specific lane.

**Outcome** — the Hermes execution result on a *run* (not a card): `completed`, `blocked`, `crashed`, `gave_up`, `reclaimed`, `timed_out`, `spawn_failed`, `protocol_violation`.

**Promote** (three senses) — (1) *lifecycle promotion*: a note advances to a more durable type; (2) *field promotion*: a reviewed value moves from `_proposed_classification` or `_enrichment` to main YAML; (3) *canonical promotion*: work moves into a review-gated zone.

**Review gate** — the `metadata.review_status` overlay that blocks promotion until a human approves. Hermes has no native review state; Memoria layers one on top of `status: done`.

**Review-gated zone** — a vault folder where the policy MCP degrades all agent writes to `dry_run` regardless of lane policy: `30-synthesis/01-claims/`, `30-synthesis/02-reference/`, `30-synthesis/03-moc/`, `50-deliverables/`. Promotion into one is always synchronous with human attention.

**Verdict** (four senses — deliberately distinct):

| Name | Values | Set by | Scope |
| --- | --- | --- | --- |
| `verdict` | `approve` / `reject` / `escalate` | Human | per-card review decision |
| `agent_verdict` | `clean` / `issues-found` / `inconclusive` | Verifier / Linter | advisory recommendation only |
| **verdict band** | `PASS` / `REVIEW` / `FAIL` | Linter | structural rollup gating scheduled work |
| Verifier trace result | `verify-clean` / `verify-needs-revision` / `verify-needs-attention` | Verifier | per-draft claim-trace outcome |

**WIP limit** — a work-in-progress cap: *active-per-profile* (1 `running` card, Hermes-enforced); *review-queue depth* (bounded; dispatcher delays new done cards once queue is full).

---

## Notes and lifecycle

**Claim** (three senses) — (1) *to claim a card*: the dispatcher atomically claims a `ready` card and spawns the assigned profile; (2) *a substantive claim*: an assertion in a draft that Verifier traces; (3) **claim-note**: a `claim-note` in `30-synthesis/01-claims/`.

**Lifecycle** (three senses) — (1) the board's two lifecycle tracks (`status` + `review_status`); (2) a note's `lifecycle` field (`proposed` / `current` / `dormant` / `archived`); (3) the vault's lifecycle stages (the numbered folders `10-` through `95-`).

**Note type** — one of the 15 defined types a vault note can be. Set by the `type` frontmatter field at creation; never changed. See [note-types.md](note-types.md).

---

## Policy and audit

**Audit log** — append-only JSONL trail of every policy MCP decision at `00-meta/02-logs/audit.jsonl`. Feeds the `audit-log` dashboard.

**Automation tier** — the system-wide autonomy setting: `strict` (propose-only), `standard` (safe auto-fixes + low-stakes triage), or `minimal` (+ scheduled answer drafting). Configured per profile. Distinct from the per-profile *invocation level* (cadence: background / Kanban-pulled / interactive).

**Lane-override file** — per-lane YAML at `.memoria/lane-overrides/<name>.yaml` declaring `policy.allow`, `policy.deny`, `policy.require`, and `routing`. Read by the policy MCP at startup.

**Policy MCP** — the runtime write-gate. Intercepts every vault write, checks the lane-override rules, returns `allow` / `allow_with_log` / `deny` / `dry_run`, and appends decisions to the audit log.

**Skill-conditional policy** — a skill's `SKILL.md` frontmatter can declare additive `policy.deny` rules that tighten the host lane's policy for that session. Cannot be loosened from inside the session.

**Structural detector** — one of the Linter's eight deterministic, zero-LLM drift checks. Named by descriptive slug: `profile-install-drift`, `vault-hash-drift`, `skeleton-drift`, `dashboard-field-drift`, `command-vocab-drift`, `plugin-config-drift`, `orphan-working-files`, `extract-path-broken`. See `.memoria/profiles/memoria-linter/M-detectors.md`.

---

## Architecture

**Computational method class** — how a task is solved: **deterministic** (regex / graph / similarity — single right answer), **hybrid** (deterministic narrowing + LLM on the residual), or **generative** (open-ended LLM composition). Memoria prefers deterministic and hybrid over generative wherever correctness and testability matter.

**Deployment option** — how the vault and execution layer sync across machines. Four patterns: `local-only` (single device, v0.1 default), `local-mesh` (Syncthing, peer-to-peer), `obsidian-sync` (cloud-managed), `always-on` (Syncthing + VPS). See [roadmap/deployment-options.md](../../docs/project/roadmap/deployment-options.md).

**Thin control over thick state** — the design principle: the control plane carries as little persistent context as possible; durable knowledge (plans, notes, drafts, audit traces) lives in vault files that workers re-read between steps. See [explanation/architecture/](../../docs/explanation/architecture/).

---

## Obsidian UI

**Callout** — agent output rendered in-place inside a note: `[!brief]` (Mapper's comparative read), `[!suggestions]` (Librarian's link candidates), `[!verification]` (Verifier's claim trace). Defined by the Callout Manager plugin.

**Channel** — how the human reaches Memoria from outside Obsidian: CLI (terminal), Telegram (async), or API (programs only). Obsidian itself is the primary UI, not a channel.

**Status line** — a glanceable Dataview widget in a pinned note showing lane health. Not the OS status bar (Dataview cannot write there).

**Workspace layout** — a saved Obsidian workspace preset: Human (`Cmd-1`), Reading (`Cmd-2`), Drafting (`Cmd-3`).

---

## Pipeline stages

**Discuss stage** — upstream pipeline stage between classify and distill. Paper note is read through the Socratic profile (write-denied vault-wide) before any claim note is written.

**Assess stage** — first downstream stage. Mapper runs `scope-project` and produces `corpus-map.md`. Human decides whether corpus is ready to write or needs more reading.

**Frame stage** — second downstream stage. Writer generates competing outlines via `counter-outline`; Socratic optionally produces lens-based framings. Human commits to one via `framing/CHOSEN.md`.

**Verify stage** — downstream stage after draft. Verifier traces every claim to a claim note; failed traces spawn `gap:` cards.

**Revise stage** — downstream stage between verify and export. Human addresses verification findings until the verify→revise loop closes.
