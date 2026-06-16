# ADR implementation gap analysis — accepted ADRs vs. built state

_Generated 2026-06-16 during alpha.6. Working artifact (tmp/) — route durable
actions to issues/ADRs before this release closes._

**Scope:** all 56 ADRs with status `accepted` (the "approved" set). Deferred (12),
rejected (34, 40), and superseded (12) ADRs were out of scope. Each ADR was read in
full and verified against the actual artifacts in `src/`, `scripts/`, `tests/`,
`docs/`, and the live `~/.hermes` runtime — not against the ADR's own claims.

## Headline

| Verdict | Count | ADRs |
|---|---|---|
| **Implemented** | 48 | 03, 05, 06, 09, 11, 12, 13, 14, 15, 16, 19, 21, 22, 23, 24, 25, 26, 27, 28, 29, 30, 32, 33, 43, 44, 45, 46, 47, 48, 49, 50, 51, 52, 53, 54, 55, 56, 57, 62, 64, 67, 68, 69, 71, 72, 75, 79 |
| **Partial (gap)** | 8 | 07, 10, 20, 31, 70, 73, 77, 78 |
| **Gap (unbuilt)** | 0 | — |

Every accepted decision has real, test-pinned implementation behind it. No accepted
ADR is wholly unbuilt. The 8 partials below are the actionable list, ranked by
materiality.

## Gaps, by priority

### 1. ADR-31 — Native Obsidian MCP over verified HTTPS · runtime security drift 🔴
The decision's point is that the bearer token "no longer travels over unencrypted
loopback." The **repo source is compliant** (`src/.memoria/profiles/*/config.yaml`
use `https://127.0.0.1:${OBSIDIAN_MCP_PORT}/mcp` + `ssl_verify:
${OBSIDIAN_MCP_SSL_VERIFY}`), but the **deployed runtime contradicts it** (verified
2026-06-16): all five `~/.hermes/profiles/*/config.yaml` serve
`http://127.0.0.1:${OBSIDIAN_MCP_PORT}/mcp` with no `ssl_verify`, and
`OBSIDIAN_MCP_SSL_VERIFY` is unset in `~/.hermes/.env`. The profiles' own comments
admit "Hermes can't skip TLS verify for the self-signed HTTPS port, hence plain HTTP
on loopback." So `OBSIDIAN_API_KEY` rides unencrypted loopback in production.
**Close it:** get Hermes to trust the plugin's exported PEM via
`OBSIDIAN_MCP_SSL_VERIFY`, then flip the live profiles back to `https://`.

### 2. ADR-78 — Thesis note type · invariant unenforced 🟠
ADR-78 requires "the schema must **reject a born-`current` thesis**" and a
review-gated promotion to `current`. Neither holds: `validate_frontmatter` only
checks enum membership, and `current` is a legal enum value, so a thesis authored
directly at `lifecycle: current` validates clean. `initial_lifecycle: proposed` /
`promotion_gate: current` are declarative metadata no code reads, and `projects/` is
**not** in `gated_prefixes`, so the policy MCP doesn't gate the promotion either. The
type exists (`thesis.yaml`, `thesis.md`); its guardrails don't.

### 3. ADR-70 + ADR-77 — Project gate not a navigation surface 🟠
The deterministic Project-gate logic is fully built and tested
(`src/.memoria/operations/processing/project/structural_impact.py`, 764 lines;
`tests/test_project_structural_impact.py`), and `project-gate.{md,base}` exist. But
ADR-70 counts Project as the **fourth navigation gate** and ADR-77 declares it
adopted, while `src/.obsidian/workspaces.json` registers only Desk/Library/Studio.
The gate is reachable by link but is not a switchable top-level workspace — both ADRs
are PARTIAL on the same missing surface. (The custom `registerBasesView` pilot is
explicitly deferred in ADR-77, so its absence is *not* a gap.)

### 4. ADR-10 — Claim supersession · query-filter half missing 🟠
The correctness-critical FAMA detector is done (`detectors.py:529 fama_exposure()`,
surfaced on `eval-trend.md`). But the ADR's other guarantee — "`query` and `write`
exclude superseded claims **by default**" — has no implementation; nothing filters on
`superseded_by` (dashboards filter `lifecycle`, a separate axis per the ADR). The
promised `schema_version` bump on the claim template is also absent.

### 5. ADR-20 — Publication path · 2 of 6 capture signals blocked upstream 🟡
Capture instrumentation is largely built (`board-transitions.jsonl`, `audit.jsonl`
deny-reasons, FAMA/supersession). `disposition.jsonl` and `cost.jsonl` stay empty
because Hermes doesn't yet surface the card `metadata` overlay — documented at
`docs/reference/telemetry.md:39` as an upstream limitation; the exporter is already
wired to emit the moment it appears. The benchmark paper itself is forward-looking
strategy, which the ADR concedes.

### 6. ADR-73 — Docs reference conventions · one rule unenforced & violated 🟡
`docs-doctor` enforces site-local-link and link-text rules. But Rule 2 ("never bare
`(ADR-NN)` codes outside explanation pages") is doc-only and violated — bare
`(ADR-12)`, `(ADR-15)`, `(ADR-25)`, `(ADR-47)`, `(ADR-53)` appear in
`docs/reference/{failure-modes,system-actions,obsidian-command-palette,obsidian-plugins}.md`.
Either add the check to `docs_doctor.py` or fix the pages.

### 7. ADR-07 — Code agent attachment · named template missing 🟡
Fully wired (memoria-engineer profile, `claude-code`/`codex` external agents,
`code`-lane override), but the ADR's "Files affected" promises a
`system/templates/code-note.md` starter template that does not exist. Either create
it or drop the stale reference.

## Minor / non-blocking notes (verdict stayed Implemented)

- **ADR-11** — gold eval tasks ship as `type: eval-task` markdown notes, ahead of the
  ADR's literal "YAML files" default (consistent with its own escape hatch).
- **ADR-13 / ADR-18** — stale plugin counts and a residual back-compat `agent_verdict`
  reader (explicitly sanctioned by the 2026-06-16 note).
- **ADR-29** — the opt-in nightly `scripts/test-l2.sh` smoke harness is the one
  self-declared deferred sub-phase.
- **ADR-64** — `install.ps1` is a real native Windows installer; only a live attended
  Windows install remains unverifiable from this Linux host.
- **ADR-69** — `search/`/`cluster/` leaf dirs and `lib/` dissolution are scheduled for
  a later refactor pass per the ADR's own staging; an empty untracked
  `src/.memoria/engines/` dir (pycache only) is worth deleting.
- **ADR-06** — one stale citekey formula in an alpha.1 release appendix (canonical
  setup doc is correct).

## Suggested next actions

The two worth fixing now: **ADR-31** (live runtime serves the API key over plain HTTP
— a real security regression vs. an accepted decision) and **ADR-78** (a stated schema
invariant that silently doesn't hold). The Project-gate workspace (ADR-70/77) is the
largest *product* gap. The rest are small cleanups.
