# alpha.9 current-state baseline (instrument)

Per §0 of the recommendations: §1 is **not committed** until this is filled from *observed* alpha.9 behaviour, not the literature. This is the instrument — the PI fills the numbers from real runs; I can't observe the running vault. Keep it to one sitting; rough counts beat none.

Method: pull the last N gate decisions / contradiction flags / retrievals from the session logs (ADR-25) or a one-off dump, hand-label a small sample (~30–50 each), record the rate. The point is **rank the §1 build items against real failure**, not precision.

| Area | The question | Metric to record | How |
|---|---|---|---|
| **Review gate** | Does PI review actually catch engine errors, or rubber-stamp? | of PI-*approved* writes, % later found wrong (the Jacobs test) | sample approved claims, re-check against source |
| | | of PI-*rejected*, % actually wrong (false-reject rate) | sample rejected, re-judge |
| **Contradictions / supersession** | Is auto-detection usable or noise? | proposer precision: % of flagged contradictions that are real | hand-label last ~40 flags |
| | | miss rate: known contradictions it didn't flag | seed a few known pairs, check |
| **Retrieval / discovery** | What's actually failing — recall, ranking, or relevance? | recall@k on ~20 queries with a known target note | run queries, check target in top-k |
| | | cosine "false same" rate (the spike, on real claims) | run `spike-nli-vs-cosine.py --models` over vault pairs |
| **Ingest extraction** | Does the frozen model produce schema-valid + correct claims? | % schema-valid; % spot-checked-correct of those | dump last ~30 extractions |

## Decision rule

After filling: re-rank §1 against the **largest observed failure**, not corpus leverage. Examples:
- Gate false-approve rate high → §3.2 warrant checker + the Jacobs calibration check first.
- Extraction schema-invalid often → §3.6 / QLoRA spike first.
- Contradiction precision low → keep auto-detection as *propose-only*, don't build the filter (§3.1/§3.4) yet.
- Retrieval recall fine, relevance bad → §4.1 reranker; if recall fine and relevance fine → **NLI comparator is not the top priority**, regardless of §1's ordering.

Empty rows are a finding too: "we don't log enough to answer this" → first fix is observability (ADR-25/104), not any §3 item.
