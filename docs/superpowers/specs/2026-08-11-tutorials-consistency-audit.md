# Consistency audit — `docs/tutorials/`

A `consistency-audit` run scoped to the nine files under `docs/tutorials/`.
28 candidates, 9 confirmed, 19 refuted. One finding is `ready-for-human`; the
other eight are `ready-for-agent`. Nothing has been changed — the audit's
findings wait on the owner's ruling.

**A run samples; it does not survey.** What follows is what two readers, twenty-eight
skeptics and two throwaway probes found. It is not a claim that the tutorials
are otherwise clean.

---

## Findings

Nine cards, ranked by severity.

### F1 — `high` — Following the arc in order breaks `memoria workspace scan`

- **Where:** `docs/tutorials/06-close-loop.md:32` and `docs/tutorials/07-customize.md:121`
- **Quote:** `memoria workspace scan --workspace .`
- **Contradiction:** `docs/tutorials/04-draft-section.md:59` has the reader run
  `memoria project compose`, which writes `projects/<project>/draft.md` carrying
  `type: draft` under a bundle root. From that point on the scan fails:
  `FAILED: unknown Concept type: draft`, exit 1. `06-close-loop.md:37-38` then
  narrates the opposite — "Notice that `status` reports the refreshed workspace
  after the scan and rebuild". The raise site is `_validate_concept`
  (`src/memoria_vault/runtime/trusted_writer.py:1313`), whose accepted set comes
  from `concept-types.yaml`, which has no `draft`. The decisive evidence that
  this is a code defect rather than a doc one is
  `src/memoria_vault/runtime/sweeps/linter/detectors.py:54-71`, which carries
  `PROJECT_WORKING_FILES = {"outline.md", "draft.md"}` and the comment that no
  per-type schema claims them and "the Concept detectors must not read them as
  Concepts" — the scan path is missing the exemption the linter documents.
- **Verdict:** `confirmed`. Reproduced three times: with the Tutorial 05 hand
  edit, with a freshly recomposed machine-written draft, and in a clean second
  vault built from scratch.
- **State:** `ready-for-agent` — deliverable *record*. **The tutorial text is
  correct as written and needs no edit.** The deliverable is an issue capturing
  the reproduction, the arc position (04 composes; `06:32` and `07:121` break),
  the two code sites, and the linter exemption as the reference behaviour. The
  `src/` half routes to a normal code review, which this audit does not site.
- **Severity:** `high` — both triggers fire: a reader following the arc in order
  takes a failing step, and the finding reveals a bug in shipped code.

### F2 — `medium` — "Notice the admitted rows" points at output the command does not print

- **Where:** `docs/tutorials/02-first-source.md:29`
- **Quote:** `Notice the admitted rows in the output.`
- **Contradiction:** the command it refers to, at `:20`, is
  `memoria seed install --workspace .`, written without `--json`.
  `_cmd_seed_install` (`src/memoria_vault/cli.py:1564-1572`) prints only
  `notice:` and `failed row` lines, both to stderr, then hands the payload to
  `_emit` (`:4203-4229`), which falls through `_success_detail` to a request id.
  `admitted` is never printed outside `--json`.
- **Verdict:** `confirmed`.
- **State:** `ready-for-agent` — deliverable *repair*. Replace `:29` with
  `Add --json to see the admitted rows; the plain run prints only notices and
  failed rows.` Carry the knock-on in the same edit: `:77` tells the reader to
  pick a `work_id` "from the seed install output or the JSON below", and the
  plain run shows no work IDs either.
- **Severity:** `medium` — the reader is misinformed about output; no wrong
  action follows.
- **Not the same defect:** `:121-122` ("Notice the digest path or request
  result") names both branches `_emit` can take and is correctly hedged.

### F3 — `medium` — A step heading promises a repair branch the step never provides

- **Where:** `docs/tutorials/03-connect-notes.md:43`
- **Quote:** `**3. Check or repair the notes.**`
- **Contradiction:** the commands under it are `memoria workspace scan` and two
  `memoria check` calls; the prose after it (`:51-52`) discusses only checking.
  Neither command repairs: `_cmd_check` enqueues `mark-checked`, `workspace
  scan` runs `observe-pi-edits`. Repair lives on `memoria doctor … --repair`
  (`src/memoria_vault/cli.py:992-1011`).
- **Verdict:** `confirmed`.
- **State:** `ready-for-agent` — deliverable *repair*, in the **heading**, not
  the body: `**3. Check the notes.**` The body is already correct and complete
  for checking, and dropping two words is smaller than adding a `doctor
  --repair` command the arc does not need.
- **Severity:** `medium` — a reader can conclude `memoria check` repairs notes.

### F4 — `medium` — The transcript's stated omissions do not cover what it actually trims

- **Where:** `docs/tutorials/first-session-transcript.md:17-18`
- **Quote:** `For readability, the excerpts omit request envelopes, timestamps,
  commits, hashes, and generated record IDs; those are transient run metadata.`
- **Contradiction:** the `ask` excerpt at `:192-206` shows only `backend`,
  `sources` (path/type) and `unknowns`, while `_answer_from_hits`
  (`src/memoria_vault/runtime/search_index.py:346-357`) also returns `query`,
  `staleness`, `contradictions`, `pipeline_counts`, `excluded_strata`, and
  per-source `title`/`score`. None of those is an envelope, timestamp, commit,
  hash or record ID. The trim is **systematic**, not isolated: `project slice`
  at `:167-179` drops `project_path`, `query`, `edges`, `missing`, `skipped`,
  `edge_count`; `compose` at `:220-229` drops `member_count`,
  `evidence_set_count`, `rebuild`.
- **Verdict:** `confirmed`.
- **State:** `ready-for-agent` — deliverable *repair*, one clause covering all
  three blocks. Replace `:17-18` with wording that adds "and show only a subset
  of each result's remaining keys". `:19-20` needs no change; the enumerated
  values are still literal.
- **Severity:** `medium` — a reader is misinformed about the shipped `--json`
  shape, in the page whose whole value is that it is a faithful capture.

### F5 — `medium` — "The engine … checks direct edits" contradicts who checks

- **Where:** `docs/tutorials/06-close-loop.md:69`
- **Quote:** `- The engine observes and checks direct edits before they become
  trusted read state.`
- **Contradiction:** `workspace scan` runs `observe-pi-edits` and returns
  `needs_check_paths`; it checks nothing. Checking is the PI's own act —
  `docs/tutorials/03-connect-notes.md:47-48` has the reader run `memoria check`
  per note, `docs/reference/data-model/glossary.md:293-297` defines check status
  as the runtime read-state verdict, and
  `docs/reference/commands-and-transports/cli.md` describes `memoria check` as
  marking a Concept checked *as the PI*. The probe shows the split: the scan
  emitted `observe-pi-edits`, then two separate `mark-checked` requests followed
  from the reader's own `memoria check` calls.
- **Verdict:** `confirmed`.
- **State:** `ready-for-agent` — deliverable *repair*, **not** a glossary
  ruling: the term is already ruled at `glossary.md:293` and `03:43-52` uses it
  correctly, so a new ruling would restate what exists. Replace `:69` with
  `- The engine observes direct edits and reports which paths still need a
  check; your own `memoria check` is what makes them trusted read state.`
- **Severity:** `medium` — the reader is misinformed about the actor boundary
  the arc exists to teach. It is a recap bullet, not a step.

### F6 — `medium` — The outline step cannot be followed as written

- **Where:** `docs/tutorials/04-draft-section.md:48-54`
- **Quote:** `Open `projects/<project>/outline.md`. … Keep both note lines and
  order them so the receptivity note ("JITAI receptivity varies by burden") is
  first and the burden note second. … Notice that the outline holds exactly
  those two note lines, receptivity first.`
- **Contradiction:** the outline the slice actually writes:
  ```
  - 01KZPK4W1F3TMYMA92F47AW9MR — BM25 score 2.529 for project query: jitai receptivity Tutorial project A small project for learning the project WRIT
  - 01KZPK4WDVZYH62NHMRWBNDQP2 — BM25 score 1.562 for project query: jitai receptivity Tutorial project A small project for learning the project WRIT
  ```
  Neither line carries a title or a path, and the echoed query text is identical
  on both. The instruction is anchored inside the opened file, so the claim
  about the file is false as written.
- **Verdict:** `confirmed`.
- **State:** **`ready-for-human`** — the fix straddles a product decision.
  - *Docs-only:* rewrite `:48-54` to say the lines are ULIDs with retrieval
    reasoning and have the reader map IDs from the slice output. Cheap and
    truthful — but it enshrines an outline the PI is told to hand-edit (`04:70`,
    "the PI-controlled bridge") and cannot read.
  - *Product:* have `write-project-slice` write the title and/or path into each
    outline line — the data is already in `members`. Fixes the tutorial for free
    and the artifact for everyone; costs a format change to a generated file
    plus any parser or test that reads outline lines.
  - *Both, sequenced:* make the product change, after which the tutorial text
    needs no rewrite at all.
  - *Leave it as it is.*
  - **Recommendation:** the product change. A docs-only patch makes the tutorial
    accurate about an artifact whose stated purpose it defeats.
- **Severity:** `medium` — misinformed rather than misdirected: the ID→title
  mapping is recoverable from the previous step's output, and the requested
  order is already the order the slice writes, so the likeliest outcome is a
  confused no-op rather than a broken draft.

### F7 — `low` — A captured transcript that could not have come from one run

- **Where:** `docs/tutorials/first-session-transcript.md:121` and `:338`
- **Quote (`:121`, the `--body` argument):** `… can reduce a person's immediate
  capacity to respond to an intervention prompt.`
- **Contradiction (`:338`, the exported Markdown reproducing the same
  sentence):** `… can reduce a person’s immediate capacity to respond to an
  intervention prompt. [@local-receptivity-2026]`. Bytes confirm it: `:121` is
  `70 65 72 73 6f 6e 27 73` (U+0027), `:338` is `70 65 72 73 6f 6e e2 80 99 73`
  (U+2019). No smart-quote transform exists anywhere in `src/` or `scripts/`;
  compose passes the note body through verbatim, and `--body` sits inside double
  quotes so the shell delivers ASCII. The two lines cannot both be from one run,
  against `:16-17` "came from one continuous run".
- **Verdict:** `confirmed`.
- **State:** `ready-for-agent` — deliverable *repair* of the **output** line
  `:338`, not the input. Editing `:121` would assert the operator typed U+2019
  into a shell command, which nothing corroborates. `.vale.ini` carries no
  apostrophe rule, so house style does not require the curl.
- **Severity:** `low` — a blemish; no reader acts on it.

### F8 — `low` — "Each folder you listed" is false for `.memoria`

- **Where:** `docs/tutorials/01-system-tour.md:54`, against the command at `:49`
- **Quote:** `Each folder you listed holds one durable file-backed Concept type`
- **Contradiction:** the command at `:49` is
  `ls notes hubs projects digests fulltexts .memoria`. `folders.yaml`'s `homes:`
  names only the five content folders; `.memoria` is a Concept home for nothing,
  and `docs/reference/system/on-disk-layout.md` calls it runtime infrastructure.
  The defence that the next sentence discharges the quantifier fails on reading
  `:56-57` in full — its subject is source catalog state, not `.memoria`.
- **Verdict:** `confirmed`, by two independent skeptics reaching it from
  opposite directions.
- **State:** `ready-for-agent` — deliverable *repair*.
- **Severity:** `low` — a reader notices and moves on.
- **Worth the owner's attention:** `git blame` shows the universal quantifier
  was *introduced* by `3c127a455` ("docs: resolve Diátaxis audit findings"),
  replacing an accurate enumeration. **A previous audit's repair created this
  finding.** See "What the next run should be told".

### F9 — `low` — "Notice the outline path printed by the command"

- **Where:** `docs/tutorials/04-draft-section.md:46`
- **Quote:** `Notice the outline path printed by the command.`
- **Contradiction:** run without `--json` exactly as the page writes it at `:41`,
  the command prints `projects/<project>/project.md` — the project path the
  reader supplied — and nothing else. `_success_detail`
  (`src/memoria_vault/cli.py:4232`) orders its keys `output_path`, `path`,
  `note_path`, `draft_path`, `project_path`, `outline_path`, so `project_path`
  wins and `outline_path` is unreachable for this command. `--json` would emit
  it (`knowledge.py:2502`), but the page's step-3 block has no `--json` — unlike
  its step 1 at `:23`, which does.
- **Verdict:** `confirmed`.
- **State:** `ready-for-agent` — deliverable *repair*: `Notice the project path
  printed by the command; the outline it wrote is at the path above.`
- **Severity:** `low` — `:44` and `:50` both give the correct path, so no reader
  is blocked; but the printed line is a *different real path*, so a literal
  follower is invited to mistake the project file for the outline. The page's
  three other "Notice" lines all point at genuinely observable state; this one is
  the outlier, not a stated convention.

---

## Refuted candidates

Nineteen of twenty-eight candidates died. This section is a record of **this
run**, never an input to the next one: a refutation holds only while its reason
holds, and no second judge ever checked any of them.

### Reasons on record

- **C1** — `01:54` alleged false because `projects/` homes two Concept types.
  `folders.yaml`'s `homes:` is a *document type* → folder map, and both
  `project.yaml` and `code-artifact.yaml` declare `concept_type: project`.
  Schema beats the inference. (The `.memoria` half of the same candidate
  survived separately as **F8**.)
- **C2** — `01:56-57` "Source catalog state lives in SQLite and blobs, not as
  source Markdown files", alleged to collide with `fulltexts/`. The glossary
  defines a Work as "not a markdown Concept type" whose only file-backed
  keep-set presence is its digest and fulltext *reproduction*; a reproduction is
  not catalog state.
- **C7** — `04:65-66` "The next lesson will create one explicit review item".
  "Review item" is a shipped term of art for the disposition unit, not the
  `review-required` finding kind, and `04:63-64` already tells the reader
  Tutorial 04's own run reports review-required items. The candidate
  manufactured a primacy claim the text never makes.
- **C18** — `02:39` / `07:65` `mkdir -p tmp/tutorial` creating a stray
  vault-root folder. Refuted as stated. The surviving substrate is verbatim
  **F7** in `docs/superpowers/specs/2026-08-10-full-corpus-consistency-audit.md:415-424`
  — already on record at this same commit.
- **C22** — `01:58-60`'s three-folder "visible folders" contrast.
  `search_index.py:32-38` keeps `fulltexts` deliberately out of
  `SEARCHABLE_ROOTS` and synthesises the fulltext document from the catalog, so
  `fulltexts/` is not a Work's visible presence at all. `git blame` shows the
  three-folder sentence was authored the day *after* the five-folder `ls` — a
  choice, not drift.
- **C23** — Tutorial 07 overwriting the seeded vault-root `steering.md`. The
  page says "Replace the override" and shows the full replacement body, so
  replacement is stated, not smuggled; `commit_explicit_writer_changes` puts the
  prior content in the vault's own git history and the seed remains in the
  installed package, so "permanent, no way back" over-claims; and the named harm
  is nil — `07:141` links the weekly review directly and `:116` restates the
  muting rule.
- **C24** — `first-session-transcript.md:330` "Slice includes 1 checked notes."
  reproduces shipped output character for character (`knowledge.py:2553`
  hardcodes the plural; a test pins the same literal). Repairing the tutorial
  would make a true page false. The defect is sited in `src/`.
- **C25** — `03:46`'s `workspace scan` called unexplained and inert. The reason
  is in the step heading the candidate did not quote — two verbs, two commands.
  `mark-checked.md` defines the operation as "Promote an observed PI edit back
  to checked", and `system-actions-cli-and-pi.md:26` maps `observe-pi-edits` to
  `memoria workspace scan`: scan-then-check is the shipped pairing the tutorial
  is teaching. "Observes nothing" over-claims — Obsidian is seeded by default,
  and step 3 is the first point the reader holds editable note files on disk.
- **C26** — `first-session-transcript.md:199`'s
  `fulltexts/receptivity-source.md`. `search_index.py:540` synthesises that
  string via `_generated_doc`, an in-memory virtual document; nothing in `src/`
  writes a vault-root `fulltexts/` path, so the CLI genuinely emits it and the
  page's "literal values from that run" is literally true. The real tension —
  a search contract advertising a path with no on-disk counterpart — is sited in
  `src/`, and `docs/roadmap.md:91` (K2, "Fulltext v2") already tracks retiring
  `fulltexts/` as a bundle root.
- **C27** — `:184`'s account of `ask` naming two of four epistemic outputs. The
  page declares itself a set of *excerpts*; `_answer_from_hits` returns eight
  top-level keys, of which the excerpt omits five, so the candidate singled out
  two with no principle separating them from the rest. The four-field contract
  is enumerated where Diátaxis puts it
  (`docs/reference/pipelines-and-io/search.md:64`). Every assertion in the
  quoted sentence is true and none is exclusive.

### Reasons lost — a defect in this run, disclosed

**C3, C4, C5, C6, C8, C10, C12, C13, C16** were each judged `refuted` by their
own skeptic, and each verdict was written to the run log as it landed. The
skeptics' *stated reasons* were held only in the session's context, and that
session died on an API limit before the report was written. They are not
reconstructed here, because reconstruction from memory would be invention
wearing the costume of a record.

For the record, the candidates were: `checked-read` undefined anywhere (C3);
Tutorial 07 duplicating the seed `steering.md` prose (C4); `01:87-88`'s claim
that the vault-root `steering.md` "stays thin" against the 42-line file `init`
installs (C5); `07:113`'s "The token from 'Burden follow-up' is gone" against a
surviving second token (C6); the Tutorial 05 marker's missing `^blk-` anchor and
the resulting `evidence-text-unbound` block (C8); `verified` used for draft
readiness against the glossary's reserved OKF meaning (C10); `06:50-51`'s
`workspace restore` without the `--force` the CLI requires (C12); `fulltexts/`
never explained in the arc (C13); and the README's end-state promise omitting
Tutorials 05 and 06 (C16).

Several of these had strong probe evidence behind them — the restore refusal and
the surviving `follow` token were both reproduced live — so their refutations
are the ones a next run should be least willing to inherit. It cannot inherit
them in any case: the skill is explicit that a refuted list is never an input to
the next run.

---

## Could not verify

Kept apart from the findings, per the skill: `unverified` is not a verdict.

1. **One wave-3 candidate, raised and not routed.**
   `docs/tutorials/01-system-tour.md:49` points a new PI at `.memoria/` under a
   heading calling it a durable root, against
   `docs/reference/system/on-disk-layout.md:23` ("A PI workflow should never ask
   the PI to open it"). Raised by C21's skeptic, which stated its own weakness.
   Under the one-further-round rule this run does not judge it.
2. **`memoria seed install` on its success path.** The environment is offline,
   so only the all-rows-fail branch could be exercised. F2 rests on a code trace
   plus the observed shape of a comparable command, not on a successful run.
3. **Nine refutation reasons**, above.

Two further candidates were raised in wave 2 but are **not** unverified, because
they reconcile by substance to candidates already judged: C23's skeptic
re-raised the `tmp/tutorial` scratch folder (the substance of C18, `refuted`),
and C25's skeptic re-raised "Check or repair" with no repair branch (the
substance of C11, confirmed as **F3**).

---

## Scope line

- **Commit audited:** `f549091da3379564adea682f060f107c88f17a50`, clean tree,
  confirmed by every reader and every skeptic before it read anything.
- **Files read:** 9 of 9 in `docs/tutorials/` — `README.md`, `01-system-tour.md`,
  `02-first-source.md`, `03-connect-notes.md`, `04-draft-section.md`,
  `05-verify-evidence.md`, `06-close-loop.md`, `07-customize.md`,
  `first-session-transcript.md`. 1083 lines. Both readers reported 9 of 9 read
  in full.
- **Files excluded, and why:** everything outside `docs/tutorials/`. The
  invocation scoped this run to that directory; the standing brief's own scope
  is wider (all of `docs/`, the workspace seed, `docs/agents/`, and root
  Markdown). Everything outside the nine files was read freely as *evidence* —
  `src/`, `tests/`, `scripts/`, the reference and how-to pages, `AGENTS.md`,
  `CONTRIBUTING.md`, the packaged workspace seed — but no finding is sited
  there. Several confirmed findings name a `src/` defect as their cause; those
  route to a code review rather than to this report.
- **Passes per slice:** one slice — the whole corpus — read by **two**
  independent `consistency-audit-inspector` readers, neither given this
  session's history. One slice was chosen deliberately: contradictions are
  relational, and 1083 lines fits in one reader's head.
- **Comparisons that could not be made:** none within the corpus, which is the
  point of the single slice. Across the corpus boundary, this run could not
  compare the tutorials against the rest of `docs/` as a whole — a contradiction
  between a tutorial and, say, an explanation page would only surface here if a
  reader happened to open that page as evidence.
- **External URLs:** exactly one in the nine files —
  `https://github.com/AkariAsai/OpenScholar` at `02-first-source.md:106`. Both
  readers independently classified it `essential`; it matches the `repo:` field
  of the `asai-2024-openscholar` row in the shipped seed manifest.
- **Third-party claims:** the seed corpus's "eight openly licensed sources"
  (`02:9`) matches the manifest's eight `- id:` rows exactly. No Obsidian,
  Zotero or MCP-host claim in these nine files required an upstream check.
- **Candidates:** 23 raised by the two readers, reconciled to 18 distinct
  defects; 2 more raised by the probes; 8 more raised by skeptics while judging;
  3 raised in wave 2, of which 2 reconciled to existing candidates. **28
  candidates, 9 confirmed, 19 refuted, 1 left unverified.**
- **Agents:** 2 readers, 28 skeptics and routing judges, all
  `consistency-audit-inspector`. No candidate was judged by the reader that
  raised it; no candidate was judged by the skeptic that raised it.

### Relationship to the prior full-corpus audit

`docs/superpowers/specs/2026-08-10-full-corpus-consistency-audit.md` exists at
this same commit and covered these same nine files (its scope line names
`tutorials` 9) with two readers. **It was found at scope time and deliberately
kept away from both readers and every skeptic**, because the skill is explicit
that a run's record is never an input to the next one, and priming readers with
prior verdicts defeats the two-independent-readers design. Where the two runs
touch:

- **Agreement.** That report's **F7** — the vault-root `tmp/` the seed and
  tutorials create — arrived here independently as C18. This run **refuted** it
  as a tutorials finding; its skeptic then found the prior filing and showed the
  surviving substrate is that F7 verbatim. Same phenomenon, already on record,
  and this run adds nothing to it.
- **Disagreement, and the more interesting result.** Eight of this run's nine
  confirmed findings are **not** in the prior report, despite the same nine
  files, the same commit, and two readers each. The highest-severity one (F1,
  the failing `workspace scan`) is invisible to reading alone: it took running
  the tutorial to find. That is the strongest evidence this run produced about
  the method — a corpus a full-corpus pass declares read is not a corpus
  exhausted, and a probe finds a different class of defect than a reader does.
- **A repair that created a finding.** F8 exists because commit `3c127a455`
  ("docs: resolve Diátaxis audit findings") replaced an accurate enumeration
  with a universal quantifier that is false for one of the six paths. An earlier
  audit's fix is this audit's finding.

---

## What the next run should be told

Proposals about the brief, not findings. They need the owner's ruling like
everything else.

1. **Probe the tutorials, do not only read them.** F1 is `high`, was reproduced
   three times, and is unreachable by reading: nothing in the prose is wrong.
   Two readers over the same nine files at the same commit missed it a day
   earlier. If the brief is to carry one new standing concern, it is that a
   tutorial arc's *commands* get executed in a disposable vault, in order, and
   the output compared to what the page says the reader will see. F2, F6 and F9
   also came from execution rather than reading.
2. **Audit the repairs of previous audits.** F8 was introduced by a commit
   resolving a prior audit's findings. A fix authored to satisfy one finding is
   an unusually good place to look for the next, and no current concern points
   there.
3. **A checker's territory, if the owner wants one.** F2 and F9 are the same
   drift class: a tutorial telling the reader to notice a value the non-`--json`
   command does not print. `_success_detail`'s key-preference order is
   mechanical and the tutorials' "Notice …" lines are greppable, so a gate could
   express this. Two instances is thin evidence for a class — the honest
   alternative is to fix both by hand and see whether a third appears.
4. **Scope note.** This run was narrowed to `docs/tutorials/` by its invocation,
   against a brief whose default scope is much wider. The brief does not say
   what happens when an invocation narrows it; it may be worth one sentence.

---

## Notes on the process itself

Recorded because the skill asks the report to say how the run was conducted, and
because several of these are gaps in the skill rather than in the repository.
The full run log is at `/tmp/audit-small-log.md`; the durable verdict ledger at
`/tmp/audit-small-verdicts.md`.

### Six points where the skill did not say what to do

Verbatim, as recorded at the moment each arose:

> **Ambiguity #1:** the skill says "You MUST create a task for each of these
> items". I have no TodoWrite tool available in this agent configuration. I am
> tracking the nine items in this log instead and completing them in order.
> Recording rather than silently ignoring.

> **Ambiguity #2:** the brief's "Scope defaults" say to audit all of `docs/`,
> the workspace seed, `docs/agents/`, and root Markdown. My invocation scopes the
> run to `docs/tutorials/` only. The skill says the brief carries "this repo's
> standing scope" but does not say what happens when the invocation narrows it. I
> take the invocation as the authority for *this* run (the brief itself says
> "Excluded unless asked", implying scope is negotiable at invocation) and will
> record the narrowing in the scope line. Everything outside `docs/tutorials/` is
> read as evidence only, never sited as a finding.

> **Ambiguity #3:** the skill says nothing about what to do when the same scope
> was audited days earlier and a report is committed in the repo. Its only rule
> points one way (refutations are not carried forward); it is silent on carrying
> forward *confirmed* findings. I treat the whole prior report as out-of-band and
> re-derive.

> **Ambiguity #4:** the skill never says whether the lead may raise candidates of
> its own. Its design has readers raise and skeptics judge, and it explicitly
> handles the case of a *skeptic* raising a new one ("Reconcile it against the set
> and send it to its own skeptic"). By that analogy a lead-raised candidate would
> be legitimate as long as a skeptic judges it. I will default to the readers'
> sets and only add my own if something substantive is missing from both — and if
> I do, it goes to a skeptic like any other, and I will log it.

> **Ambiguity #5:** the HARD-GATE says the probe runs "in a scratch worktree". I
> ran it in a scratch *vault* inside the audited worktree, because the vault is
> the thing under test and `test-vault/` is gitignored, so the tree is provably
> unchanged either way. A separate git worktree would not have made the probe any
> more isolated. Recording the deviation from the literal words.

> **Ambiguity #6:** the skill mandates that skeptic-raised candidates get their
> own skeptic, but sets no termination rule for the recursion — wave 2 will raise
> a wave 3, and so on. I run exactly one more wave, and any candidate raised in
> wave 2 that I cannot route gets recorded under "could not verify"
> (`unverified`, which the skill says is never a verdict), never silently dropped
> and never rounded to a finding.

Two of these produced the run's two most valuable results. **#4** is why F1 and
F6 exist at all: both were raised by the lead from probe output rather than by a
reader, and both were then judged by a skeptic like any other candidate. **#6**
is the sharpest — the rule requiring skeptic-raised candidates to get their own
skeptic is new, and this run appears to be the first to reach the wave where it
recurses. Without a termination rule an audit does not converge.

### The probe

The HARD-GATE permits "a throwaway probe, run in a scratch worktree and reverted
before you report it". Two were run, both offline, both reverted, both leaving
`git status --porcelain` empty.

They ran in a scratch **vault** at `test-vault/audit-probe/` *inside* the
audited worktree, not in a separate git worktree. That deviates from the skill's
words, and it was the right call: the vault is the artifact under test, not the
checkout; `.gitignore:48` excludes `/test-vault/` so the tree is provably
unchanged either way; and `AGENTS.md` requires disposable vaults to live under
`test-vault/` specifically. A second git worktree would have added a checkout
without adding isolation. The code under test was pinned deliberately — main
checkout HEAD equals worktree HEAD equals `f549091d`, main checkout `src/`
clean, and every command run with `PYTHONPATH=<worktree>/src` so the probe
exercised the audited tree rather than whatever the installed console script
resolved to.

Four of the nine confirmed findings (F1, F2 by corroboration, F6, F9) rest on
probe output. Reading alone would have produced five.

### Two session deaths

This run died twice on API session limits, once mid-verification and once
mid-wave-2. The first death destroyed the wave-1 skeptics' stated refutation
reasons and all their routing metadata, because both lived only in context. The
recovery was to re-dispatch routing for the seven confirmed findings — which is
honest work, freshly evidenced — and to disclose the nine lost refutation
reasons rather than reconstruct them.

The lesson generalises past this run: verdicts must be appended to a file as
they land, not held until the report is written. A skill whose method spans
dozens of agent round-trips should not assume one continuous context.
