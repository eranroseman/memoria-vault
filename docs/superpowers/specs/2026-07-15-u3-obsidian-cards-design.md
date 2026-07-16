# U3 · Obsidian plugin as thin renderer — Design

Date: 2026-07-15. Status: **design (PI-approved in session), pre-plan**.
Plan 23 LOOP.11 output. Consumes `2026-07-15-surfaces-bootstrap-design.md`
(server rendezvous, token, failure states, bundle seeding) and the I1
loudness taxonomy. The plugin renders and enqueues; it never writes files
and never owns judgment.

## 1. Attention substrate prerequisites

From the attention-cards rethink-audit (representation sound — files stay;
the lifecycle was convicted). Implemented ahead of plugin work:

1. **Compaction of the cold tail.** Resolved cards leave `inbox/`: packed
   into a monthly, append-only `inbox/archive/YYYY-MM.md` digest (cat-able,
   in-bundle, bounded file count). Keeps the hot `open_blockers` scan and
   the editor's cold-parse budget flat (the measured ~76 s at 10k files).
2. **Sweep-before-gate hand-edit adoption.** Before the policy gate
   evaluates, hand-edited `attention_status` flips in `inbox/` are swept
   into journaled disposition events (`via: manual-edit`). Vim disposition
   keeps working; it stops being invisible. Closes the gate-clearing hole
   (inbox is not a bundle root, so `observe-pi-edits` never saw it).
3. **Open-status fingerprint dedupe.** `write_finding` (and the retraction
   sweep) dedupe on a fingerprint against **open** cards: re-observing an
   open finding touches it; recurrence after resolution legitimately
   re-raises. Fixes both the duplicate-alert-per-sweep bug and the
   existence-dedupe permanently suppressing re-raises.

## 2. The pane: engine-authored cards, closed block catalog

One `ItemView` ("Memoria Attention"). The engine serves
`GET /v1/views/attention` returning **`view-spec.v1`** — a closed catalog of
exactly five block types: `card`, `text`, `badge`, `action-row`,
`evidence-list`. The plugin renders blocks from the catalog and composes
nothing; an unknown block type renders as a labeled fallback box (fail
visible, never silent). Cards carry the honesty-card fields — action,
argument-for, argument-against, what-tipped-it, coarse certainty (≤3
levels), **no verdict line** — with evidence pointers as vault links, and
loudness **rendered, never invented** (the payload's value verbatim).

Every action button is an enqueue of a named existing operation via the
loopback server's operation endpoint: `resolve-attention`
(resolved/deferred), `acknowledge-attention`, `curate-note-candidate` for
proposal cards, `curate-note-link` for the relate control (§4). The plugin
is enqueue-only; results surface on the next poll. The operation and views
endpoints are U1-baseline-bound (bootstrap header): they hold until the U1
gate honors or supersedes them.

## 3. UI specification (ratified in the visual session)

**Theme binding.** The plugin styles exclusively through Obsidian theme
variables (`--background-primary/-secondary`, `--text-normal/-muted/
-faint`, `--interactive-accent`, semantic color vars) — no hardcoded
palette; it must sit native in any user theme. The loudness scale maps to
the theme's semantic accents: block → red, alert → orange, notice → faint
hairline, quiet → none.

**Queue anatomy (chosen: queue rows + expand-in-place).**

- Pane header: `ATTENTION` label + `N open · as of HH:MM` — the count and
  the honest data age, always.
- Rows are two-line-height entries: loudness glyph (7px square dot) ·
  title (single line, ellipsis) · age (tabular-nums, right-aligned).
- Sort: `block` pinned as a sticky top group, then loudness rank, then age.
- One row expands in place at a time to the full card: kind line
  (10px uppercase, loudness-colored) → title (13px/600) → **evidence block
  first** (inset, one step darker than the card surface) → compact
  for/against line → `tipped by: <factor>` + certainty chip → action row →
  meta line (`raised by <producer> · timestamp`).
- Keyboard: j/k move, Enter expands/collapses, keyboard-reachable action
  verbs. Actions are **named text verbs** (dispositions are
  provenance-bearing acts), primary verb styled with the accent tint;
  no icon-button toolbars.
- Density: 12–13px type, tabular-nums for all counts/ages, borders in the
  low-opacity range the theme provides; hierarchy through weight and
  surface steps, not lines.

**Plugin settings.** One field: **Engine command** (default `memoria`) —
the WSL2/nonstandard-PATH escape hatch (bootstrap §2, e.g. `wsl memoria`).
No server URL, no token field: both come from handshake.

**Status pill (six states + both skew banners).** Bottom status bar, always
present; one pill; each state has a distinct probe and one remediation
(wordings ratified):

| State | Pill | Panel/behavior |
| --- | --- | --- |
| Connected | `Memoria · N open` (green dot) | click opens the pane |
| Stale | `Memoria · N open · as of 14:02` (amber) | poll failed or idle-backoff; click retries |
| Server down | `Memoria · server down` (red) | after 3 bounded respawns: log path + `memoria serve --vault …` |
| Token invalid | `Memoria · token invalid` (red) | live server 401 after re-handshake: restart instruction |
| Engine missing | `Memoria · engine missing` (gray) | `pipx install memoria` + Retry; vault stays fully usable |
| Key needed | `Memoria · N open · key needed` (accent) | non-blocking; names the credential + `memoria secrets set …` |

Skew banners (non-blocking, top of pane), both directions: plugin older —
*"This vault's plugin (vX) is older than your engine (vY). Run
`memoria upgrade`, then reload Obsidian."*; vault newer — *"This vault was
seeded by a newer engine (vY) than installed (vX). Upgrade the engine:
`pipx upgrade memoria`."*

## 4. The relate control (chosen: single form modal)

Command + pane button "Memoria: Relate…". One modal, everything visible
and editable before submit: **From** (fuzzy note picker, defaults to the
active note) → **Relation** (segmented three-way from the fixed roster —
`supports`/`contradicts`/`extends`; `LINK_RELATIONS` is the single source)
→ **To** (fuzzy note picker) → **Warrant** (optional free text, hung on the
edge — promotion-ready per the G2 reshape) → **Queue edge**. Submission
enqueues `curate-note-link`; the confirmation toast names the queued
request id. This closes the named PI-direct edge-origination gap while the
plugin still never writes a file.

## 5. Poll-based status feed

The pane polls the **authenticated** counts/summary endpoint
(`GET /v1/views/attention?summary=true`) every 30 s while the vault window
is active, backing off to 2 min when idle; the pill shows data age the
moment a poll fails or returns stale. The **unauthenticated**
`GET /v1/status` probe is used only in the failure ladder (distinguishing
server-down from token-invalid) and never resets the server's idle timer
(bootstrap §3). The idle-exit interaction is deliberate: counts polls are
authenticated, so an open pane keeps the server alive; a closed vault lets
it retire. No SSE, no daemon; the payload is shaped so the beta.2 daemon
can later push the same structure.

## 6. Canvas surface

Generated canvases carry a "read-only · regenerated" banner.
**Fork-to-scratch** creates an editable, non-authoritative copy; a scratch
canvas graduates hand-drawn edges into `links:` via the same
`curate-note-link` enqueue (the one place the spatial axis authors); a fork
staleness badge shows the edge-diff count vs the moving source graph —
never auto-reconciled. Project pages **link-open** canvases in their own
pane (embeds render topology without content — thumbnail only). Reconcile
discipline for all regenerated artifacts, ratified: delete-arm reconcile;
collision-safe id→path encoding (raw `id:` in frontmatter is the match key,
filename is a sanitized slug); quarantine-and-log dirty rows, never
fail-the-pass or silent-drop; projector-output conformance test (emitted
enum ⊂ schema enum).

## 7. id-filenames boundary

Machine-created concepts get stable kebab-slug filenames; every seeded view
leads its `order:` with the `title` property; `showInlineTitle: false`.
Adopted outright — no vault data exists to migrate. PI-authored notes keep
whatever names the PI gives them.

## 8. Out of scope

Live on-save badges (beta.2 daemon); any plugin-side write path;
marketplace publication (bootstrap spec §8); the seeded `.base` views
themselves (owned by Plan 23 R1NG tasks — this spec only consumes them);
V2's evidence-set review surface (its own gate, expected to reuse this
pane's `view-spec.v1` infrastructure).

## 9. Acceptance criteria

Every card action names an existing operation id; no SSE/daemon dependency
anywhere; the pane renders entirely from `view-spec.v1` payloads (delete
the pane, the vault loses no data); all six pill states + both skew banners are
reachable in tests via fault injection; substrate prerequisites (§1) land
before the pane ships; keyboard-only triage passes (j/k/Enter/verbs); the
plugin contains zero hardcoded colors.

## Appendix: session artifacts

Card anatomy, relate flow, and pill states ratified in the visual-companion
session of 2026-07-15 (mockups under `.superpowers/brainstorm/`, gitignored
— decisions carried here). Attention-substrate audit (counter-design, code
facts with citations, prior-art sweep) recorded in session; verdict:
files-as-truth kept, lifecycle mechanisms added (§1).
