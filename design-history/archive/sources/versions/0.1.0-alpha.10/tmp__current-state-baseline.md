# alpha.10 current-state baseline

Fill this from observed use before choosing memory work. Rough counts are enough.
This is the evidence gate for #859.

## Is memory the bottleneck?

- Last two weeks, what slowed the work most: reading, thinking/writing, finding a
  known note, stale fact, missed contradiction, extraction error, tooling?
- Times Memoria saved time:
- Times Memoria cost time:
- If stale/retrieval/contradiction/extraction are not top issues, do not build
  more memory machinery yet.

## Review gate

- PI-approved writes sampled:
- Later found wrong:
- PI-rejected writes sampled:
- Truly wrong:

## Contradictions and supersession

- Recent contradiction flags sampled:
- Real conflicts:
- Known conflict pairs checked:
- Missed:
- Decision: keep soft-flag / build proposer / defer:

## Retrieval

- Queries with known target note:
- Target in top-k:
- qmd reranker on/off result:
- Decision: keep qmd as-is / tune qmd / defer:

## Ingest extraction

- Recent extractions sampled:
- Schema-valid:
- Spot-check correct:
- Decision: keep API path / test local extraction / defer:

## Supervision budget

- Realistic approve/reject labels per year:
- Competing calibration sinks:
- Decision: enough labels for one threshold? yes/no:

