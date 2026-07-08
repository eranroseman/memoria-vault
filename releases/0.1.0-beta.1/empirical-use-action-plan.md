# Memoria 0.1.0-beta.1 - Empirical Use Data Action Plan

Date: 2026-07-07
Status: scratch action plan

## 1. Requirements

The beta.1 blockers need empirical data for product decisions, not a large
analytics system. The plan must:

- answer only the blocker and validation questions in the beta.1 requirements
  and design docs;
- collect enough repeated real-use evidence to make a decision;
- avoid raw content logging unless a user explicitly saves an artifact;
- preserve the single-user local-first posture;
- produce decisions that can update `decisions.md` or the beta.1 design.

Best-practice basis: use repeated single-case measurement, because beta.1 is a
single-user/self-use product; keep a null-workflow comparison so "helped" means
better than the user's existing Zotero/Obsidian/ChatGPT path; capture
dispositions as events, not ratings. This follows the beta.1 requirements'
single-case/autobiographical design evidence and the design's
human-AI-complementarity guardrail.

## 2. Instrumentation First

Add the smallest shared event shape before dogfooding:

| Field | Purpose |
| --- | --- |
| `timestamp` | ordering and session reconstruction |
| `session_id` | one reading/writing/SRD work session |
| `project_id` | compare repeated loops inside one project |
| `surface` | CLI, HTTP, MCP, editor, manual |
| `workflow` | ask, gap, evidence-review, canvas, draft, SRD, export |
| `item_type` / `item_id` | reviewed object without storing body text |
| `variant` | table/canvas, BM25/FTS/vector/hybrid, human/null/assisted |
| `decision` | accept, reject, edit, defer, override, abandon |
| `duration_s` | PI load and return-to-work cost |
| `outcome` | kept artifact, fallback, exported, blocked |
| `reason_code` | short controlled reason; free text optional and local |

Use existing journal/telemetry paths where possible. Add new event types only
when current logs cannot answer a blocker. Do not build a dashboard before the
events exist.

## 3. Data Collection Phases

### Phase 0 - Baseline And Fixtures

Duration: 1-2 sessions.

- Record the user's current null workflow for one small project: source, notes,
  ask, outline/draft/SRD, export.
- Preregister retrieval fixture cases before any default-promotion claim.
- Select candidate seed-corpus sources and record license/fetch rule.
- Define the diary template: goal, workflow used, artifact kept, blocker hit,
  fallback used.

Exit: baseline path and fixture definitions exist. No product decision yet.

### Phase 1 - Guided Beta Slice Dogfood

Duration: two full project loops or ten sessions, whichever comes first.

Run the same real project through:

1. source/capture/digest,
2. note/claim extraction,
3. gap analysis,
4. project slice,
5. canvas/table comparison,
6. outline/draft,
7. SRD,
8. evidence review,
9. export attempt.

After each session, fill the five-line diary. After each gate item, log the
disposition event. If the user falls back to the null workflow, log why.

Exit: every blocker has at least one real event trail, or is explicitly still
unobservable because its mechanism does not exist.

### Phase 2 - Decision Review

Duration: one review session.

For each blocker, decide one of:

- **keep**: observed data supports the mechanism as beta.1 scope;
- **simplify**: a smaller mechanism answers the observed need;
- **defer**: no real beta.1 use required it;
- **instrument more**: the mechanism exists but data is insufficient.

Update `decisions.md` or beta.1 design only for decisions, not raw notes.

### Phase 3 - Validation Runs

Duration: after the relevant mechanism exists.

Run validation protocols from design §8.2:

- PI review load;
- complementarity and payoff;
- canvas threshold;
- draft write-back residual;
- exploration value;
- retrieval default activation;
- LLM call-site regression;
- provider conflicts and topic ownership.

Exit: each protocol has a pass/defer/simplify decision and the evidence path.

## 4. Blocker Data Plan

| Blocker | Data to collect | Minimum observation | Decision rule |
| --- | --- | --- | --- |
| SRD contract | SRD sections added/edited/deleted, unresolved requirement count, missing trace links, acceptance criteria edits | two SRDs from real projects or one SRD revised twice | Keep only sections that survive real editing; move rare sections to optional appendix |
| Evidence-review UI | item count/session, time/item, accept/reject/edit/defer, reopen rate, reason codes | ten reviewed items across at least two sessions | Batch and filter until review load fits a session; if review is skipped, simplify the gate |
| Seed corpus | source list, license, fetch method, first grounded answer time, first write/SRD gesture time | one clean install rehearsal | Ship only sources with clear license/fetch rule and a path to first answer under 30 minutes |
| Workspace/gate topology | path between ask, review, writing, SRD, export; context switches; abandon/fallback events | two full loops | Choose the shortest path that avoids repeated lost-return or hidden-gate failures |
| Export target | actual recipient/tool, format tried, refusal reasons, manual cleanup time | two export attempts or one externally shared draft | Pick the first target that appears in real use; defer live citation fields unless required |
| Multi-device topology | attempted second-device read/write events, conflicts, sync workarounds | all dogfood sessions | Default to single-writer unless repeated real handoffs require more |
| Raw dataset bundling | dataset size/type, mutation, sharing need, export need | every project with dataset material | Default to catalog-by-reference unless a real export requires packaged raw data |
| `mode: work` creation | creation attempts, command confusion, alias requests | all new Work-note creation events | Add an alias only if the user reaches for it or repeats a workaround |
| Non-API schema drift | drift incidents, stale doc fields, failed lint/generation checks | every release-doc/schema edit | Use the cheapest lint that catches observed drift |

## 5. Validation Metric Plan

| Protocol | Primary measure | Guardrail |
| --- | --- | --- |
| PI review load | reviewed items/session and time/item | no hidden auto-approval |
| Complementarity | assisted outcome vs null workflow outcome | review cost included |
| Payoff | kept artifacts and fallback rate | no synthetic health score |
| Canvas threshold | canvas edits/use vs table use | table remains available |
| Draft write-back | promoted notes kept/rejected/reworked | no auto-write to graph |
| Exploration | acted-on exploration candidates | no relevance stream pollution |
| Retrieval default | preregistered recall/grounding/latency/cost | BM25 remains default until beaten |
| LLM call-site | eval pass/fail against baseline | shadow-first promotion only |
| Provider/topic quality | conflict rate and PI corrections | conflicts stay visible |

## 6. Operating Cadence

- Log events during the session.
- Write the diary immediately after the session.
- Review blocker evidence weekly or after five sessions.
- Promote only decisions, not raw telemetry, into durable release docs.
- Delete or archive local raw notes after the decision is recorded.

## 7. What Not To Build Yet

- No analytics dashboard before the event stream proves useful.
- No custom survey system.
- No broad user study before the self-use loop works.
- No retrieval default switch before the preregistered fixture beats BM25.
- No code execution data collection for beta.1; SRD is the code-side output.
