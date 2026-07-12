# ADR disposition map — the alpha.15 retire-sweep

Executable checklist for the ADR retire-sweep slice. New consolidation ADRs 125–130
(drafted in this folder) absorb the decisions below; each superseded file gets
a tombstone (`status: superseded`, `superseded_by: [NNN]`) with its text kept
(numbers are permanent; rejected-alternatives memory is never pruned). After
this sweep the live accepted corpus is ~19 ADRs instead of ~90.

Consolidation rationale (the decision behind the sweep): a corpus of ~90
fine-grained ADRs has repeatedly caused confusion and contradiction — decisions
were re-litigated, superseded-in-practice ADRs read as current, and reviews
missed collisions. The unit of decision is now the **subsystem**, not the
mechanism: six broad ADRs, each carrying its superseded ancestors' surviving
invariants and rejected alternatives in its own text.

## Superseded (tombstone → new ADR)

| New ADR | Supersedes | One-line carry note per ancestor |
| --- | --- | --- |
| **125 architecture** | 7 (external coding delegation → alpha.16 module target), 22 (Hermes runtime → in-house engine; its warning acknowledged), 23 (memory substrates → journal/config/project state), 26 (repo-as-install-unit → uv package), 28 (write-gate plugin → fail-closed lesson carried), 32/33 (MCP-only tools → agent grant rule carried, ADR-130), 35 (skill insights — dead), 43 (skill governance — dead), 46 (seven layers → CLI+engine; policy-gate honesty carried), 48 (profiles → operations + agent), 49 (Bases/plain-text-only store → **rejection of SQLite explicitly overturned**, split authority), 53 (patterns-as-vault-data → operations as product code), 55 (vault-template/golden copy → package reinstall), 74 (plugin supply chain → wrapper-era note), 80 (Hermes test harness → replay fixtures under ADR-29), 120 (profile config materialization — dead) |
| **126 knowledge model** | 14 (frozen deliverable → export-is-terminal), 15 (project membership hint → project-side candidates via attention), 19 (hub threshold → checked-tag membership + curated salience; its "looks curated but isn't" hazard answered), 47 (type-first folders → four-type template), 50 (universal lifecycle/maturity in frontmatter → meaning-only + DB verdicts + `standing`), 52 (links vs relationships → carried verbatim), 71 (capture forms → schema-driven scaffolds), 77 (project gate → project layer + saturation), 78 (thesis type → thesis role link; born-checked ban + falsified-thesis-preserved carried as checks), 79 (argument graph/warrant/saturation floor → the gap engine saturation block, ADR-129), 83 (relate control → typed wikilinks + extraction), 100 (exploration traces → project working notes), 117 (naming scheme → rule carried, roster superseded), 119 (schema-as-contract → principle carried into pydantic product schemas) |
| **127 integrity** | 25 (two logs → journal + session projections; append-only carried), 104 (three planes → journal/projections/diagnostics; git-as-tamper-root carried; hash-chain rejection narrowed to in-vault log files) |
| **128 epistemics** | 3 (structural human gate), 21 (autonomy ceiling's "never fewer reviews"), 41 (gate modes), 54 (no confidence-tiered auto-accept), 57 (disposal half; "engines write" half carried) — all with inlined evidence and the theatre-check as the new guard |
| **129 machine judgment** | 9 (contradictions v1 → layered proposer; no-LLM-in-rollup carried as proposer-never-authority), 10 (supersession → narrowed visibility contract; human sets the link), 30 (tiered ingest → field-authority merge; spike lessons binding; capture-commits-first carried), 38 (similarity gate → shadow-mode candidate, usage-gated), 39 (acceptance checklists → same), 56 (uncertainty flag → gate-the-uncertainty carried), 66 (calibration.yaml → shadow-first generalized to every score) |
| **130 surfaces** | 31 (native Obsidian MCP → engine MCP transport), 51 (honesty card → attention-surface contract: arguments not verdicts, batch worklists, graded loudness), 70 (gates/dashboards → read-API views), 72 (command surfacing → **PI-direct-access contract carried**: never agent-only, plugin/Inspector implementation deferred to a future adapter ADR), 81 (gate dashboards), 102 (disposable projections → view-spec contract carried), 109 (PM via native views), 112 (tutorial arc → principle carried to the 15 docs pass), 114 (nav rail), 115 (inbox queue), 116 (surface architecture → one-view-one-definition carried), 118 (dashboard consolidation), 121 (enqueue-only panel → **carried verbatim** as the universal UI write rule) |
| **124 (already landed)** | 5 (Zotero backbone); add 6 (citekey convention → citekey-as-alias + pin-before-export carried in 124's consequences) |

## Rejected (stamp `status: rejected`, reasoning kept)

- **95** nightly discovery loop — unattended always-on loop conflicts with the
  no-daemon architecture (design Appendix/§S6).
- **97** Writer-proposed claim notes — the Writer agent is a §13 non-goal.
- **103** projected Canvas spatial axis — spatial-at-scale refuted; tabular/
  faceted is the validated default; small-graph argument view must beat a
  tabular baseline (ADR-130 view-specs).
- **106** cost/disposition capture via Hermes session store — mechanism dead;
  residual lesson (record real per-run cost with provenance, never fabricate
  zeros) carried into ADR-129's runner journaling.

## Stay proposed (deferred; "When this matters" cadence review)

16 (systematic review, adopt-on-demand) ·
88 (literate code-note — alpha.16 candidate with the coding module) ·
89 (LTR triage — needs recorded dispositions, now being captured) ·
90 (claim-sentence classifier) · 91 (prose metrics) · 98 (relation-vocab
expansion) · 107 (OKF boundary export — note: the project layer's internal
OKF sub-bundle is a *new* decision recorded in ADR-126, deliberately beyond
107's boundary-only stance) · 108 (LiteParse).

In-15 proposed ADRs — flip to accepted as their slices land (second wave):
none currently open. **92** (discovery relevance scoring) landed as accepted in
PR #1195 via deterministic `steering.md` candidate relevance with
ranked/exploration channels. **93** (keyphrase tag candidates) landed as
accepted in PR #1191 via deterministic `analyze-gaps` unchecked attention,
without adding KeyBERT/YAKE. **94** (record-linkage dedup) landed as accepted
across PR #1190/#1192/#1193/#1194 via deterministic ID and name-block attention,
without automatic merges. **99** (MASSW aspects) landed as accepted in PR #1196
via the DB `work_aspects` read model populated from source capture/enrichment
and included in checked Work search documents.

## Keep accepted, unchanged

11 (vault-eval diagnostic-never-gates; amended by 129 for build-time model
selection) · 12 (no second frontmatter authority — now user education for the
plugin era) · 20 (publication path; capture-now obligation is satisfied by
128's disposition telemetry + 129's cost journaling; benchmark slices remain
unscheduled) · 24 (single researcher) · 29 (layered testing) · 44 (tests in
pytest tree) · 62 (measurement/verification harnesses — accepted, diagnostic-only,
unscheduled) · 64 (Windows-native production) · 73 (docs reference
conventions) · 75 (GitHub Project fields) · 101 (spaces vs gate vocabulary)
· 105 (diagnostic plane) · 110 (ruff format) · 122/123/124 (alpha.14 cut).

## Housekeeping in the same PR

- Fix dangling `assumes:` refs (74 → [67], 80 → [76]) while tombstoning.
- Regenerate the ADR index (`scripts/gen_adr_index.py`).
- Update the ADR README with the consolidation rationale above and the rule
  that new decisions amend the six subsystem ADRs unless a genuinely new
  subsystem appears.
