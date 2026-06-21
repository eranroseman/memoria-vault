# alpha.9 current-state baseline (instrument)

Per §0 of the recommendations: §1 is **not committed** until this is filled from *observed* alpha.9 behaviour, not the literature. This is the instrument — the PI fills the numbers from real runs; I can't observe the running vault. Keep it to one sitting; rough counts beat none.

Method: pull the last N gate decisions / contradiction flags / retrievals from the session logs (ADR-25) or a one-off dump, hand-label a small sample (~30–50 each), record the rate. The point is **rank the §1 build items against real failure**, not precision.

## Part 0 — Is memory even the bottleneck? (answer before measuring inside it)

The whole agenda assumes gate/contradictions/retrieval are where research time leaks. Confirm that first, or Part 1 measures the wrong subsystem precisely.

- Last ~2 weeks, what actually slowed the work? Rank: reading · thinking/writing · finding a known note · a stale fact misled me · a contradiction missed · tooling. → ______
- Times the memory system *specifically* cost or saved real time (tally): ______
- **Gate:** if finding/stale/contradiction aren't top-2, the binding constraint is elsewhere — note it and stop; §3 is premature. → ______

| Area | The question | Metric to record | How |
|---|---|---|---|
| **Review gate** | Does PI review actually catch engine errors, or rubber-stamp? | of PI-*approved* writes, % later found wrong (the Jacobs test) | sample approved claims, re-check against source |
| | | of PI-*rejected*, % actually wrong (false-reject rate) | sample rejected, re-judge |
| **Contradictions / supersession** | Is auto-detection usable or noise? | proposer precision: % of flagged contradictions that are real | hand-label last ~40 flags |
| | | miss rate: known contradictions it didn't flag | seed a few known pairs, check |
| **Retrieval / discovery** | What's actually failing — recall, ranking, or relevance? | recall@k on ~20 queries with a known target note | run queries, check target in top-k |
| | | cosine "false same" rate (the spike, on real claims) | run `spike-nli-vs-cosine.py --models` over vault pairs |
| **Ingest extraction** | Does the frozen model produce schema-valid + correct claims? | % schema-valid; % spot-checked-correct of those | dump last ~30 extractions |
| **Baseline to beat** | Does the fancy path beat BM25 + long-context dump? | of ~10 real past questions, # the dumb baseline answers acceptably vs # the current system beats it | run both, compare |

## Supervision-budget check (the constraint nothing models)

- Considered approve/reject labels realistically produced per **year**: ______
- Calibration sinks competing for them (NLI threshold · HANS test · judge-vs-PI · FP budget · exemplars · lessons · POTENTIAL-middle · novel-escalation · schema spot-checks ≈ **9**) → labels ÷ 9 = ______ per mechanism.
- If that can't calibrate even one threshold, **drop the calibration-dependent items regardless of literature leverage** — don't reorder them.

## Decision rule

After filling: re-rank §1 against the **largest observed failure**, not corpus leverage. Examples:
- Gate false-approve rate high → §3.2 warrant checker + the Jacobs calibration check first.
- Extraction schema-invalid often → §3.6 / QLoRA spike first.
- Contradiction precision low → keep auto-detection as *propose-only*, don't build the filter (§3.1/§3.4) yet.
- Retrieval recall fine, relevance bad → §4.1 reranker; if recall fine and relevance fine → **NLI comparator is not the top priority**, regardless of §1's ordering.

An item ships only if (a) a Part 1 cell names the pain it fixes, (b) it beats the baseline-to-beat row, and (c) the supervision check can afford it. Two of three → defer. One or zero → **kill** and record why here, so the next review doesn't re-propose it. Re-ranking is not enough; the rule must be able to remove items, not just sort them.

Empty rows are a finding too: "we don't log enough to answer this" → first fix is observability (ADR-25/104), not any §3 item.
