# O1 · Onboarding + seed corpus — Design

Date: 2026-07-16. Status: **design (PI-approved in session), pre-plan**.
Plan 23 LOOP.5 output. Consumes the consolidation §2 O1 unit list
(`2026-07-12-beta.1-consolidation.md:174`), ADR-113 (deferred) + issue #902,
the empirical plan Phase 0 (`0.1.0-beta.1-empirical-use-action-plan.md`
§3/§4), and the bootstrap spec's onboarding runway
(`2026-07-15-surfaces-bootstrap-design.md` §7 — the machine substrate this
spec consumes, per its own boundary note). Two rethink-audits anchor §4:
*steering.md* (mechanism is live, design pre-dates projects) and *steering
vs projects* (authored sections duplicate substrate; verdict: derived
signal + thin override).

## 1. Licensing decision — the freeze blocker, recorded first

**Decision (2026-07-16, PI-ratified).** The canonical decision ledger is
`docs/superpowers/specs/0.1.0-beta.1-decisions.md` (consolidation §
ledger row) — a dated Y-statement copy of this decision lands there **in
the same PR as this spec** (LOOP.5 step 4); this section carries the full
rationale:

- **Fetch-on-onboard, manifest-only.** The product ships a seed *manifest*
  (pinned identifiers + license + fetch method), never third-party
  content. No source text enters the repo or the package.
- **License floor, applied to every seed source regardless of fetch-only
  distribution:** CC BY or CC0 preferred; CC BY-SA admitted only where a
  source is irreplaceable (share-alike obligation recorded on the manifest
  row); PMC Open Access **Commercial-Use subset** for PubMed Central
  items. arXiv items qualify only when the paper page shows an explicit
  CC license — the arXiv default non-exclusive license fails the floor.
- **Fetch rule:** keyless public APIs only — arXiv export API with the
  version pinned (`export.arxiv.org`), PMC OA service
  (`oa.fcgi?id=PMC…`), or a publisher CC-BY PDF URL. No credentials, no
  scraping.
- **Why the floor despite fetch-only:** redistribution-safety (future CI
  fixtures and test vaults may bundle the corpus) and export-safety (the
  PI can publish derivatives with attribution).
- **Offline fallback:** the tutorial accepts any local PDF via
  `memoria work add --pdf`; the seed corpus is the paved path, never a
  gate.
- **Impl-start check:** before O1 implementation begins, each manifest
  row's license is re-verified against its evidence URL; a failed row is
  replaced, never waived.

This decision predates and governs §2's selection (the LOOP.5 hard order).

## 2. The seed corpus (~8 sources, knowledge-work cognition)

The cluster is the literature behind Memoria's own design — note-taking,
external memory, spaced retrieval, argumentation, LLM-assisted research —
chosen so support/contradict/extend relations among the eight are real:
gap analysis and tension surfacing find genuine structure, one natural
tension pair carries the verify-evidence chapter, and one paper ships with
its companion open-source repo (§6's affordance pair).

**The eight sources** (every license verified against a live evidence URL
on 2026-07-16; every fetch URL exercised keyless and returned 200 — the
session's research record):

| # | Source | Identifier | License | Fetch (keyless) | Cluster role |
| --- | --- | --- | --- | --- | --- |
| 1 | Chen, Castro-Alonso, Paas & Sweller (2018), *Undesirable Difficulty Effects in the Learning of High-Element Interactivity Materials*, Front. Psychol. 9:1483 | DOI 10.3389/fpsyg.2018.01483; PMC6099118 | CC BY 4.0 | PMC OA service (`oa.fcgi?id=PMC6099118`) | **Tension pair A**: desirable difficulties shrink/reverse for complex material |
| 2 | Moreira, Pinto, Starling & Jaeger (2019), *Retrieval Practice in Classroom Settings: A Review of Applied Research*, Front. Educ. 4:5 | DOI 10.3389/feduc.2019.00005 | CC BY | Publisher CC-BY PDF (`https://www.frontiersin.org/articles/10.3389/feduc.2019.00005/pdf`; not in PMC) | **Tension pair B**: retrieval practice benefits complex authentic material |
| 3 | Settles & Meeder (2016), *A Trainable Spaced Repetition Model for Language Learning*, ACL 2016 | DOI 10.18653/v1/P16-1174 | CC BY 4.0 (ACL 2016+ policy) | ACL Anthology PDF (`aclanthology.org/P16-1174.pdf`) | Extends testing effect to deployed adaptive scheduling; bonus repo `duolingo/halflife-regression` |
| 4 | Morrison & Richmond (2020), *Offloading items from memory*, Cogn. Research 5:1 | DOI 10.1186/s41235-019-0201-4; PMC6942100 | CC BY 4.0 | PMC OA service | External-memory/offloading anchor (registered report); supports #6 |
| 5 | Ose Askvik, van der Weel & van der Meer (2020), *The Importance of Cursive Handwriting Over Typewriting…*, Front. Psychol. 11:1810 | DOI 10.3389/fpsyg.2020.01810; PMC7399101 | CC BY 4.0 | PMC OA service | Note-taking medium (encoding vs storage); in tension with #4's storage framing |
| 6 | Schmidt (2018), *Niklas Luhmann's Card Index: The Fabrication of Serendipity*, Sociologica 12(1) | DOI 10.6092/issn.1971-8853/8350 | CC BY 4.0 | Publisher PDF (`sociologica.unibo.it/article/download/8350/8272`) | PKM/Zettelkasten anchor — the vault's own lineage |
| 7 | Mirzababaei & Pammer-Schindler (2021), *…Structural Wrongness in Arguments Based on Toulmin's Model*, Front. AI 4:645516 | DOI 10.3389/frai.2021.645516; PMC8680349 | CC BY 4.0 | PMC OA service | Toulmin argumentation operationalized in an agent; bridges to #8 |
| 8 | Asai et al. (2024), *OpenScholar: Synthesizing Scientific Literature with Retrieval-augmented LMs* | arXiv:2411.14199**v1** (pinned) | CC BY 4.0 (per-paper; license evidence = the abs page) | arXiv PDF (`export.arxiv.org/pdf/2411.14199v1` — the full text, not the abs page) | **The paper+repo pair**: `github.com/AkariAsai/OpenScholar` (live; Apache-2.0 code) |

- **The tension pair** (#1 vs #2) is the live testing-effect
  boundary-conditions debate — both CC BY, citing the same underlying
  literature from opposing lineages (van Gog/Sweller vs
  Roediger/Karpicke), so the disagreement the verify-evidence chapter
  surfaces is genuine, not an artifact of corpus selection.
- **Vetting record:** PaperQA2 (arXiv 2409.13740) rejected — CC BY-SA and
  replaceable by the CC BY OpenScholar, so §1's SA exception was not
  spent; Agarwal, Nunes & Blunt (2021) rejected — license unverifiable
  behind a Springer auth-wall; the Google-effect and Mueller–Oppenheimer
  originals excluded as paywalled. Topic coverage: note-taking (#5),
  external memory (#4, #6), spaced retrieval/testing effect (#1–#3),
  argumentation (#7), PKM (#6), LLM-assisted research (#8, #7 bridging).

**The manifest** — `src/memoria_vault/product/seed_corpus/manifest.yaml`,
one row per source: `{id, title, identifier (pinned version), license,
license_evidence (URL), fetch (method + URL), role (cluster relation),
repo (optional)}`. The manifest is the shipped artifact; §1's impl-start
check runs against it.

**`memoria seed install`** iterates the manifest with a small
**per-method fetch/resolve layer in front of the shipped capture seams**
(the shipped paths alone do not fit: `--url` capture runs HTML text
extraction on fetched bytes, `--pdf` reads only local files, `--doi` is
metadata-only — `cli.py:877-928`, `capture.py:433-434`):

- **publisher/ACL/arXiv PDF rows** (#2, #3, #6, #8): download the pinned
  PDF keyless, route the raw bytes through the shipped local-PDF seam
  (`stage_pdf_source`) — the same code path as `memoria work add --pdf`,
  fed from a download instead of a file;
- **PMC OA-service rows** (#1, #4, #5, #7): resolve the `oa.fcgi` XML
  record to its package/PDF link, download, and route through the same
  PDF seam;
- catalog metadata rides each row's DOI/identifier as `capture-source`
  does today. Fully keyless; digests are attempted only when live-model
  credentials exist (bootstrap §7.5's notice covers this).

**Idempotency and honesty:** the manifest `id` is the catalog `work_id`;
before fetching, each row checks `state.catalog_source(vault, work_id)`
and **skips on a hit** — a full-skip re-run performs no fetches, no
journal events, no commits, and exits clean. Failures are per-row: a
fetch failure names the row and continues; **zero rows present** (newly
admitted + already admitted) is the failure exit — i.e., a first run
that admits nothing fails; a re-run over a seeded vault succeeds.

## 3. The wizard is the doc arc — no second script

Bootstrap §7 ends the machine runway at `Start here.md`. From there the
existing tutorial arc (`docs/tutorials/01–07`) **is** the wizard — the
ADR-112 doctrine (doc pages the learner reads while doing; the docs are
the one script). O1 adds the rungs the chapters invoke:

- `memoria seed install` (§2) — invoked by chapter 02-first-source, which
  rewires from its current generic capture example onto the seed corpus
  (adding one local-PDF/-file alternative path for offline runs).
- `memoria steering show` — **repointed**, not added (the command ships
  today rendering the raw file body, `cli.py:2001-2006`): §4 makes it the
  effective-steering provenance render; chapters 01/02 use it to show the
  learner what their framed project aims.
- **Tutorial restructure (the ordering fix):** chapter 01 is read-only
  today and the first project is currently created in chapter 04 — after
  capture. Chapter 01 gains a closing "frame your tutorial project" step
  (`memoria new project`), and chapter 04 reconciles to *use* the
  already-framed project. This makes the arc's order real:
  init → onboard → **frame project (ch. 01)** → **seed install (ch. 02)**
  → … → ask.
- The bootstrap-seeded `Start here.md` link to "the co-PI variant"
  repoints at the re-deferral note until ADR-113's preconditions close
  (no dangling link).

**ADR-113 is explicitly re-deferred.** Its preconditions remain open: the
single-script mechanism (one beat definition feeding docs and agent) is
unspecified, and the U4 co-PI plugin is designed but unimplemented. The
doc arc stays the script a future agent layer would dramatize. Recorded
as a comment on issue #902 when this spec merges.

## 4. Steering: derived signal + thin override (rethink-audit verdict)

The shipped mechanism is live — `_steering_tokens` (`knowledge.py:1193`)
feeds `_discovery_relevance` (`:1200-1226`), splitting discovery
candidates into `ranked`/`exploration` — but its design predates projects
and its whole-file tokenization breaks the seeded file's own promises
(inactive topics boost; template placeholders pollute a fresh vault).
Ratified target:

1. **`effective_steering_tokens(vault)`** replaces the whole-file bag at
   the single call-site: the union of
   - **active projects** — title + `thesis` + tags of every non-archived
     `type: project` file (priorities are never retyped);
   - **hubs** — title + tags (the standing-areas level, Luhmann-native);
   - **`mode: question` notes** — title tokens (open questions are vault
     content, not file prose);
   - the authored **Watch for** section (terms that fit no artifact yet);
   **minus** the **Muted** section's tokens. The semantics are
   **token-set subtraction**, stated once: watch/mute entries are section
   bullets run through the same `_relevance_tokens` tokenizer, so
   suppression is per-token (a multi-word entry mutes each of its words —
   the over-suppression consequence is documented in the seeded file); a
   candidate routes to `exploration` iff its overlap with the
   post-subtraction set is empty, so a candidate matching a muted term
   *and* a surviving project token still ranks. Archived projects are
   excluded structurally by never contributing.
2. **`steering.md` reseeds as a two-section override file** — `## Watch
   for` and `## Muted` — with the same frontmatter. All five old sections
   dissolve into the substrate that already expresses them: priorities =
   active projects; open questions = question notes; **synthesis gaps =
   the gap-analysis machinery** (`memoria project gaps` / analyze-gaps
   discovery candidates), with Watch for covering gaps that fit no
   artifact yet; papers-to-prioritize = attention `priority` (I1);
   currently-inactive = archived projects + Muted.
3. **`memoria steering show`** renders the *effective* steering: every
   token with its provenance (which project / hub / question note / watch
   entry contributed it). `memoria steering edit` still opens the
   override file. Legibility is a read surface; authorship stays thin.
4. **No `steering init`, no interview.** The tutorial's "frame your
   project" step is the steering-before-import step. `memoria seed
   install` prints a notice when no active project exists ("frame your
   project first — chapter 01 — or ranking starts empty"); a notice,
   never a gate.
5. **Doc updates ride along:** the weekly-review line "refresh your
   steering" becomes "archive stale projects, prune watch/mute"; the
   seeded file's prose describes the derived model honestly.

## 5. Time-to-first-answer instrumentation (≤30 min, measurable)

A native telemetry event type **`onboarding-step`** `{step}` — one string
field, registered in the shipped native-type table by O1's plan (the same
mechanism as `attention-admitted`; all-string, so I1's validator needs no
change), server-side, `session_id` NULL, zero PI burden. **No duration
field**: each row's own `ts` column is the timestamp, and every delta is
computed at read time — no cross-process t0 state exists or is needed.
Steps: `init-done`, `onboard-done`, `project-framed`, `seed-installed`,
`first-answer`. **The `first-answer` emit rule, exactly:** emit when (a)
the `answer-query` result's `sources` contain at least one path resolving
to a `work_id` present in the seed manifest, and (b) no prior
`first-answer` row exists in `telemetry_events` — so "first" and "over
the seed corpus" are deterministic. **The bar:** `first-answer.ts` −
`init-done.ts` ≤ 30 minutes — consumed by LOOP.13's acceptance run
(**recorded amendment applied in this PR**: LOOP.13's
time-to-first-answer block replaces its `seed-dois.txt` +
`work add --doi` + shell wall-clock protocol with `memoria seed install`
over the manifest and the two event timestamps — the `--doi` path is
metadata-only and would have grounded over titles) and feeding the seeded
`seed-corpus` decision rule (check: manual, already in the I1 registry).

## 6. Implicit feedback + the open-source affordance

- **No surveys anywhere.** Onboarding feedback = the `onboarding-step`
  timestamps plus the empirical plan's five-line **session diary
  template**, seeded once at `system/templates/session-diary.md`
  (goal / workflow used / artifact kept / blocker hit / fallback used —
  Phase 0's exact fields). The diary stays local raw material (empirical
  plan §6: deleted or archived after decisions are recorded).
- **Open-source affordance** (Code-provenance-kit lineage): the corpus
  includes one paper + companion-repo pair; the tutorial's capture
  chapter has the learner `memoria work add` the repo and names the
  practice (a paper's repo is often the method's only complete spec).
  The *typed* paper↔repo edge mechanics belong to their owning beta.1
  package — O1 ships the pair and the habit, not the edge type.

## 7. Deliberately not building

The interactive CLI wizard (second script — ADR-113's drift warning);
the co-PI-guided walk-through (re-deferred, §3); model-assisted steering
authoring (keyless posture; PI-owned file); any steering decay/aging
automation; bundling corpus content in the repo (manifest-only, §1);
digest generation as an onboarding requirement (credentials-optional);
the typed paper↔repo edge (owned elsewhere); onboarding analytics beyond
the five step events.

## 8. Acceptance criteria

The licensing decision (§1) carries a date ≤ §2's source-list date, and
every manifest row names license + evidence URL + fetch method. A fresh
vault runs `init → onboard → frame project → seed install → ask` fully
keyless and records all five `onboarding-step` events, from which the
≤30-min bar is computable. With an active project titled X and Muted
entry Y, discovery candidates matching X route to `ranked` and
candidates matching **only** Y route to `exploration` — including when Y
also appears in a project title (subtraction removes it from the
effective set). A fresh vault with only the framed tutorial project produces
non-empty effective steering, every token carrying project-sourced
provenance in `memoria steering show`; the reseeded `steering.md`
contributes zero tokens beyond watch entries. `memoria seed install`
re-run admits nothing new and exits clean (the failure exit fires only
when zero rows are *present* — first-run emptiness, not re-run
idempotence); with no active project it prints the frame-first notice
and proceeds. Chapter 02 completes offline via its local-file/-PDF
alternative path (arbitrary local content — the seed corpus itself is
fetch-only per §1).

## 9. Implementation slices (feeds the plan)

1. Seed manifest + license impl-start check script + the dated
   Y-statement in `0.1.0-beta.1-decisions.md` (the ledger entry lands
   with this spec's PR).
2. `memoria seed install`: the per-method fetch/resolve layer (remote
   PDF → `stage_pdf_source`; PMC OA-service XML → package/PDF), work_id
   pre-check idempotency, per-row honesty, frame-first notice.
3. `effective_steering_tokens` + call-site switch + token-set-subtraction
   mute.
4. `steering.md` reseed (Watch for / Muted) + repointing the shipped
   `steering show` to the effective-steering provenance render.
5. `onboarding-step` native telemetry type (all-string) + the five emit
   points incl. the `first-answer` rule.
6. Diary template seed.
7. Tutorial + doc sweep: chapter 01 gains project framing, chapter 02
   rewires onto the corpus (+ local-file offline alternative), chapter 04
   reconciles to the existing project, **chapter 07's steering exercise
   rewrites against the derived model**, tutorials/README row; plus the
   stale steering-semantics surface — `memory-substrates.md`,
   `memory-model.md`, `using-obsidian/README.md`, `cli.md` steering rows,
   `on-disk-layout.md`, `build-a-hub.md`, `run-the-weekly-review.md`,
   the seeded `Start here.md` co-PI-variant link.
8. ADR-113 re-deferral comment on #902.
9. LOOP.13 time-to-first-answer block amendment (applied in this PR,
   §5).

## Appendix: session provenance

PI rulings 2026-07-16: licensing = fetch-on-onboard + open floor (A);
corpus topic = knowledge-work cognition (A); wizard form =
doc-arc-as-wizard (A); steering = derived signal + thin override (the
*steering vs projects* rethink-audit verdict, superseding both the
five-section authored file and the interim union design; the earlier
*steering.md* audit's tokenizer findings — inactive-boost, placeholder
pollution — are subsumed: the sections they afflicted no longer exist).
