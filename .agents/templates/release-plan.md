# Release {{ version }}

Use this as the body for the release parent issue. State lives in GitHub fields,
milestones, parent/sub-issue state, Actions artifacts, and release-please.

## Status

{{ One short paragraph: what this release/checkpoint is, whether it is draft,
candidate, complete, or formally released, and the main remaining blocker. }}

## Scope

{{ What this version delivers, in one paragraph. Name the boundary: what is in,
what is deliberately later. }}

## Definition of done

This release is done when every gate/stage sub-issue below is closed.

| Gate | Proves | Evidence home |
|---|---|---|
| Source | Repo contracts, docs, schemas, Python tests, and static checks are coherent. | CI and `scripts/verify pr` summary |
| Package | Disposable vault assembly and model-free workflow replay work. | `scripts/verify package` summary |
| Runtime | Hermes, MCP, Obsidian bridge, model endpoint, cron, and policy boundaries work live. | `scripts/verify runtime` or explicit skip reason |
| Product | The product workflow produces reviewable value, telemetry, GUI evidence, and output-quality evidence when claimed. | Product/manual sub-issue |
| Release | Blockers, docs, versioning, notes, and close-out are ready. | Release parent/sub-issues |

## Known limitations

- Limitation: {{ user-visible limitation }}. Impact: {{ practical impact }}.
  Workaround: {{ workaround or "none" }}. Tracking: {{ issue/ADR }}.

## Candidate checks

1. Required CI is green on `main`.
2. `scripts/verify rc` passes, or Runtime is skipped with a concrete reason.
3. Fresh install or profile redeploy succeeds against a disposable vault, never
   the production `~/Memoria`.
4. Product, manual GUI, failure/recovery, and runtime checks required by the
   release scope are recorded in sub-issues.
5. Documentation integrity is complete: shipped behavior is covered, stale
   claims are fixed, and durable decisions are captured in ADRs.
6. `scratch/releases/{{ version }}/` scratch is deleted from the `scratch`
   branch after durable content is moved to ADRs, docs, release notes, or issues.

## Cut or checkpoint close

1. No open release-milestone issue has `Readiness: Blocked`.
2. All release sub-issues are closed or explicitly rolled forward.
3. Formal release: merge the release-please PR. It owns version bump, changelog,
   tag, and GitHub Release notes.
4. Internal checkpoint: close the parent issue and milestone without tagging.
