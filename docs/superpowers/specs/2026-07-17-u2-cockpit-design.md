# U2 · Deep-work + review cockpit — Design

Date: 2026-07-17. Status: **design (PI-approved in session), pre-plan**.
Plan 23 LOOP.10 output — the last beta.1 design gate. Consumes the
consolidation §2 U2 unit list (`2026-07-12-beta.1-consolidation.md:197`),
the merged U1 spec (the cockpit is a **read-API client**: every call is a
U1 registry action, checklist letters cited by name), the merged V2 spec
(`memoria review` is the review cockpit proper — hosted by reference,
never re-implemented), the merged I1 spec (ordering contract, flow panel,
dashboard), the merged R2 spec (grounds marks, honest denominators), and
the empirical plan §4 rows this surface generates decision data for
(two-window friction; workspace/gate topology).

## 1. The command and the split (PI ruling: one composer, two screens)

**`memoria cockpit`** — a read-only composer over U1 registry actions;
no private engine calls (the LOOP.10 acceptance line). Two screens embody
`deep-work-workspace` / `deep-vs-task-split`:

- **Deep screen** — `memoria cockpit --project <p>` (bare `memoria
  cockpit` resolves to the single **active** project when exactly one
  exists; otherwise it lists active projects and asks). **The active
  predicate, named once:** a `type: project` concept whose frontmatter
  `archived` is not `True` — the live field (`project.yaml`), the same
  predicate ERP-C.6's `active_project_slices` walks; `lifecycle` is a
  schema-retired frontmatter field (`RETIRED_FRONTMATTER_FIELDS`,
  `vaultio.py:19-34`) and appears nowhere in this spec (recorded note:
  O1's frame-first notice adopts the same predicate at execution).
  Fixed panel order —
  1. project header (title, thesis, archived state);
  2. slice summary (counts by kind over the project slice —
     `project.slice.read`);
  3. draft state — **what the read actions actually expose**:
     outline/draft presence (`project.slice.read`) and per-marker
     evidence states (`evidence-incomplete` / `review-required` counts
     from `project.draft.read`'s `evidence_sets`). No "verification
     status" line: that datum is the transient result of the
     `verify-project-draft` write operation and is persisted nowhere
     readable — persisting it is deliberately not built (§6); the
     review flow owns evidence state;
  4. open gaps + thin claims (R2's grounds marks: `complete`
     evidence-set counts, zero-grounds flagged);
  5. **recent machine changes** touching the slice — journal-derived
     trace, newest first, each line carrying a ref usable by §3's
     revert preview;
  6. the **context-handoff block** — the U1 `context-read` row's
     bundle, rendered as a short fixed-order block (one item per line;
     a one-line *invocation* of the underlying action is printed
     beneath it for pasting). This *is* the `co-pi-loop` unit's beta.1
     form. **Ownership recorded:** U1 lands the row map-or-reserve; if
     it is still reserved at U2 execution, **U2's plan wires it** —
     implements the situated-context bundle computation and registers
     the transport (the row joins §5's registered list); if a live
     transport already exists, the panel wraps it. Until either, the
     panel renders an honest placeholder naming the reserved row. The
     two-window friction the handoff mediates is what the empirical
     plan's §4 rows measure.
- **Triage screen** — `memoria cockpit --triage`: fixed panel order —
  1. the attention worklist rendered **from `read_attention`'s
     I1-ordered payload, order preserved verbatim** —
     `attention-as-projection` is satisfied structurally: the cockpit
     holds no state, re-sorts nothing, and renders `rank_factors` as
     the per-row disclosure;
  2. review-queue counts (V2's queue — linked with the `memoria review`
     invocation line, never re-hosted);
  3. the dashboard flow line (open total · inflow/drain · oldest), from
     the dashboard read. **Registry note:** the I1 plan ships `memoria
     dashboard` engine-direct without a surface-contract row — grep
     first: if no `dashboard.read` row exists at U2 execution, U2
     registers it (the same both-branch discipline as the
     context-read row).

The two screens never mix: deep work sees no queue; triage sees no
draft. That is the split, enforced by layout, honest to
`adaptive-fixed-interface` (adaptive *content* through a fixed frame —
no layout ever encodes a verdict).

## 2. Keep-test degradation (the acceptance criterion, per LOOP.10)

Plain sequential text; fixed panel order; tabular-with-headers only
where columns are honest; **no curses, no TUI dependency, no live
updates, no ANSI requirements** (color, if any, degrades to nothing).
Static per invocation — re-run to refresh (the `static-review-cockpit`
doctrine: the cockpit is a photograph, not a feed). `--json` emits the
composed payload (each panel keyed, carrying its source action id).
**The keep-test, testable:** `memoria cockpit | cat` output is
byte-identical to terminal output; **no identifier is ever truncated or
wrapped mid-identifier** (an identifier longer than the layout renders
whole on its own line) with 80 columns as the layout target for
everything else; the whole screen is a valid nano/vim buffer (it is
just text). `--json` panels each carry **`source_action`** = the
registry row's `id` value.

## 3. Trace → revert preview

The deep screen's recent-changes panel carries refs; the preview is a
**new U1 read row** (`trace.revert_preview`, job `project` — shipped
row-id grammar): given a journal event ref, it reports **exactly what
the shipped records can support**:

- the event's output refs (`output_id`, `output_sha256`, `staging_id`,
  inputs — the derived-event record);
- the **descendant split**, computed read-only from the journal
  derivation graph (the `_downstream_events` walk): which descendants a
  `cascade-rollback` **would quarantine** (machine-derived) vs **would
  flag `needs_human`** (PI-derived) — mirroring the shipped behavior at
  `integrity.py:1080-1108`, never re-deciding it;
- the per-output materialized commit (`outputs.materialized_commit`);
- the **owning explicit operation**, named: `cascade-rollback`
  (`cascade_rollback(vault, target_id, *, context, reason,
  include_target)`).

**Not promised:** DB-row-level impact (no shipped seam computes
quarantine's prospective row touch-set — a row-level preview would
re-implement internals and drift silently). **The backup branch,
honestly:** no per-event snapshot record exists — backup/restore
transaction files are transient crash markers and restore is
whole-workspace; the preview reports only whether a workspace backup
exists (`local_backup_status`) and that restoring it reverts everything
since it. **Preview reads, never acts**: `memoria cockpit` gains no
write power; invoking the revert stays the existing
separately-confirmed operation. A ref with no computable preview says
so honestly (names the record it lacks) rather than guessing.

## 4. Findings in the CLI voice

Cockpit panels render findings as the honesty-card fields verbatim —
finding/action, argument-for/against where present, tipped-by, coarse
certainty, **no verdict line, no pre-selected action** —
`cli-voice-findings` is the honesty-card contract applied to terminal
output, not a new format. (The unit's consolidation lineage is traced
and cited in the plan; the contract is the one U3 renders in panes and
V2 renders in review rows — one card grammar, three surfaces.)

## 5. Boundaries

The cockpit consumes **only U1 registry actions** — it registers its own
row (`cockpit.read`, job `project`, kind `read`, cli-only; `--triage`
documented on the same row), plus `trace.revert_preview`, and — under
their both-branch rules (§1 panel 6, §1 triage note) — `context.read`
and `dashboard.read` where still unregistered. It cites U1 checklist
letters (a)/(e) for its own conformance. It links — never duplicates — `memoria review`
(V2), `memoria dashboard` (I1), and the U3 pane. No SSE, no daemon, no
editing surface (vim/nano beside it is the editor; that is the point of
the keep-test). No model judgment anywhere in assembly or rendering.

## 6. Deliberately not building

A TUI or any live-updating surface (static-cockpit doctrine; keep-test);
a second review surface (V2 owns review; the triage screen counts and
links); a cockpit-owned queue or ordering (I1's projection only); write
affordances (revert stays explicit and separate); session state or
cockpit config files; web/GUI variants (U3/plugin territory); any
panel the U1 registry cannot serve.

## 7. Acceptance criteria

A fixture vault with one active project (`type: project`, `archived`
absent), one thin claim, one derived machine output, and a populated
attention queue: the deep screen renders panels 1–6 in order — slice
counts correct, the thin claim marked with its zero grounds count, the
draft panel showing presence + per-marker evidence-state counts (no
verification-status line), and the machine change carrying a ref whose
`trace.revert_preview` read returns the output refs, the descendant
split (would-quarantine vs would-flag), the materialized commit, and
the owning revert operation — mutating nothing (tree-clean); the
context-handoff block renders the bundle (or, pre-wiring, the honest
reserved-row placeholder) and, once wired, round-trips through the
`context-read` action; `--triage` renders the worklist in exactly
`read_attention`'s payload order with `rank_factors` disclosed, plus
review counts and the flow line; `memoria cockpit | cat` ≡ terminal
output; no identifier is truncated or wrapped mid-identifier; `--json`
carries every panel with its `source_action` registry id; every action
the cockpit calls appears in the U1 registry (checklist (a) extended to
the new rows); with zero or multiple active projects, bare `memoria
cockpit` lists them and exits honestly; `python scripts/verify` green
with the new registry rows (`cockpit.read`, `trace.revert_preview`,
plus `context.read`/`dashboard.read` under their both-branch rules) and
the pinned CLI-surface edit.

## 8. Implementation slices (feeds the plan)

1. Cockpit assembly module (`engine/cockpit.py`): panel builders, each
   wrapping one U1 action; the composed payload shape.
2. Deep screen rendering + project resolution (single-active default,
   list-and-exit otherwise).
3. Triage screen rendering (projection-preserving worklist +
   review/flow lines).
4. `trace.revert_preview` read: the journal-trace panel + the preview
   action over the named shipped seams (§3's exact payload); registry
   rows + parity/pinned-test edits for all new/both-branch rows.
4b. The context-read wiring (both-branch per §1 panel 6): the
   situated-context bundle computation + transport, only if the U1 row
   is still reserved at execution.
5. Keep-test enforcement tests (pipe-identity, 80-column, no-ANSI,
   `--json` round-trip, tree-clean).
6. The cli-voice findings renderer (the shared honesty-card grammar,
   one function all panels use).

## Appendix: session provenance

PI rulings 2026-07-17: cockpit form = one composer command, two screens
(A — TUI and pure-doctrine variants rejected in-session); full design
approved at presentation ("U2 look right"). The trace→revert preview,
attention-as-projection mechanics, cli-voice contract, and boundaries
were presented as proposals and ratified with the design. This closes
the last LOOP design gate; LOOP.13's acceptance run measures the
cockpit against the empirical plan's two-window and topology rows.
