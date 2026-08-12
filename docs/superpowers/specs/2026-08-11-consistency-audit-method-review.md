# Consistency-audit method review — 2026-08-11

What three runs of the `consistency-audit` skill established about the method
itself. The runs' findings are filed separately: the
[2026-08-09](2026-08-09-memoria-docs-audit.md) and
[2026-08-10](2026-08-10-full-corpus-consistency-audit.md) full-corpus records
and their [repair plan](../plans/2026-08-09-audit-repairs.md), and the
[2026-08-11 tutorials](2026-08-11-tutorials-consistency-audit.md) run.

## An audit run samples; it does not survey

Two runs, same corpus, 25 hours apart. The commits differ only by a terminology
realignment of `docs/agents/consistency-audit-brief.md`, so misses are recall
losses rather than repairs.

|  | 2026-08-09 | 2026-08-10 |
| --- | --- | --- |
| readers | 12 (6 slices x 2) | 2 (1 slice x 2) |
| candidates | 101 | 83 raw -> 62 |
| confirmed | 41 | 42 |
| refuted | 20 | 20 |
| agents | 113 | 65 |

**They agree on 15 defects.** The re-run missed 23 of the baseline's 41 (21
genuine, 2 outside its scope), contradicted 3, and raised 25 the baseline never
found. Both partitions reconcile: 15 + 3 + 23 = 41; 17 + 25 = 42. **The union is
66 distinct defects**, and nothing suggests that is the ceiling.

Each run landed on ~41 confirmed. *Which* ~41 is close to independent.

Two misses are unarguable, because the re-run held the evidence:

- It **quoted** `run-the-linter.md:16` for an unrelated purpose. The baseline had
  confirmed that exact line as defective.
- It **relied on** `frontmatter.md:209` as sound authority inside a refutation.
  The baseline had confirmed that exact sentence as wrong.

Reading the line is not seeing the defect. The skill's Reading criterion used to
assert that "both halves of every comparison were held together"; no run can
claim that, and it no longer does.

## The runs disagree — and the third run overturned the second

Three defects the 2026-08-09 run confirmed, the 2026-08-10 run refuted. On the
sharpest of them a third pass, on 2026-08-11, reversed the reversal.

`fulltext.yaml:2` declares `category: fulltext`. 2026-08-09 confirmed it as
"orphaned by the alpha.19 rename". 2026-08-10 refuted it (R7) on three grounds:
that `folders.yaml`'s `categories:` is a fallback alias for `bundle_roots:` and
therefore a different namespace, that the shipped invariant is
`home.startswith(category)` rather than membership, and that the prefix
tolerance predates the value.

**All three legs fail, and this file asserted them as fact.**

- Lines 3 and 4 of `folders.yaml` are the *identical list*. `schema.py:149`
  makes `categories` the legacy name for the same concept, which
  `tests/test_search_index.py:509` documents. `fulltext` is absent from both,
  and from `homes:`.
- The `startswith` was authored at `1d299c37` for *path*-prefix semantics, with
  an explicit `if category != "inbox"` exemption, before the `fulltext` type
  existed. `"fulltexts".startswith("fulltext")` passes as a *string* prefix, by
  accident. What one test tolerates is not what the data means.
- Neither earlier run engaged the decisive evidence. `git log -S'fulltexts'
  --follow` over `folders.yaml` returns exactly one commit — `c5af51be`, which
  renamed `fulltext` to `fulltexts` throughout that file and **did not touch**
  `types/fulltext.yaml`. At the schema's authoring commit `14484961`,
  `categories:` still read `fulltext` and `homes:` mapped `fulltext: fulltext`,
  so the value was correct when written. It is rename residue. The five sibling
  schemas each equal their home string exactly; `fulltext` alone does not, and
  names a directory that exists nowhere.

Two of three runs confirm it. The repair was right; the refutation was wrong.

**What that costs this document's earlier claim.** It read: "A repair would have
been made for a defect that does not exist." The opposite holds — the defect is
real, and the refutation would have cancelled a correct repair. The lesson
survives inverted: a later run with better evidence beats an earlier one, and
*better evidence* here meant reading history rather than state.

**The method gap it exposes.** Nothing in the skill adjudicates two skeptics who
disagree, and nothing tells a skeptic that a value which looks wrong while a
test passes may be the residue of an incomplete rename. `git log -S` and
`git blame` settle that class and no rule names them.

## Reading cannot see everything

The tutorials run's highest finding came from *executing* the corpus, not
reading it: following the tutorial arc in order breaks
`memoria workspace scan` — `FAILED: unknown Concept type: draft`, exit 1 — from
Tutorial 04 onward, reproduced three times. **The full-corpus audit at the same
commit missed it a day earlier.**

It exists only because that run allowed itself to raise candidates, which the
skill did not then sanction. Both changes have since landed.

## Cost

~3.2M tokens for 229 files: 62 skeptics averaging 39k (**75% of the total**),
two readers at ~230k each, one orchestrator at 356k. Verification is where an
audit's money goes; reading is cheap.

Scoping down did **not** scale cost down proportionally — the nine-file run
spent ~287k orchestrator tokens against ~356k for 229 files, because two
whole-corpus readers and the probes are near-fixed. "Scope is the lever" remains
unmeasured.

## What the runs changed in the method

Each of these has an observed failure behind it, not an argument:

- The refuted list lost its forward mechanism. A refutation holds only while its
  reason holds, and no second judge ever checks one. Measured value of carrying
  it: 2 of 17 re-raised, both refuted again.
- Skeptics raise candidates too — about one in four, on refuted and confirmed
  alike — and they had nowhere to go but a footnote. They are now candidates,
  with one further round and then a close.
- Verdicts go to a ledger as they arrive. A session death destroyed twenty
  returned verdicts' routing because it lived in the orchestrator's context.
- Skeptics batch by file, not by candidate; a cheap gatherer collects evidence
  and an expensive judge rules on it. **Never** tier a verdict by how mechanical
  a candidate looks — `fulltext.yaml` looked like a string missing from a list.
- `checker spec` is `ready-for-agent` only when a checker is the sole remedy,
  since `AGENTS.md` ranks deletion above checkers.
- Readers and skeptics confirm the checkout they were given. Four skeptics in one
  run caught themselves reading the main tree, because a relative path resolves
  against wherever the shell last reset to.
- `unverified` (could not check) is distinct from `unsettled` (the repository is
  silent), and is never a verdict.
- A run proposes what the next run should be told — scope it found wrong, a
  concern worth making standing, territory a checker now owns — and those go to
  the owner with the findings. The brief is the only thing that carries between
  runs.

## What was rejected, and why

- **Feeding the prior confirmed list forward.** In steady state those defects are
  repaired, so the list manufactures ghosts. The durable trail is the prior scope
  line, which says where the last sample did not look.
- **Auditing the repairs of previous audits.** A repair lands in the corpus and
  the next full pass reads it anyway — this is how `F8` was found, with no such
  rule in existence. Pointing readers at repaired regions would skew a
  recall-limited step and depend on out-of-scope, decaying records. The real
  lesson lives upstream: a repair shipped without re-running its premise step.
- **Cheaper models for readers or skeptics.** Finding contradictions is the
  judgment, not the mechanical half; splitting a corpus so each reader sees 10-15
  files destroys exactly the relations being hunted. Only retrieval and
  bookkeeping are cheap.

## Open

- Whether several scoped runs beat one sweep. Arithmetic on two data points says
  66 defects for 130 agents against 41 for 113; it has not been tested.
- The 2026-08-10 run's 42 findings and the 2026-08-11 run's 9 await an owner
  ruling; neither run could reach its question round without a human.
