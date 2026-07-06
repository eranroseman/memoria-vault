# Design History

Use this playbook when work changes product architecture, workflow policy, or a
released design claim.

## Decision-time Capture

1. Write the decision in the active release workspace, normally
   `releases/<version>/decisions.md` on the `scratch` branch.
2. Use a dated Y-statement:
   `Y: Memoria will <choice>. Because: <evidence and tradeoff>.`
3. Add typed pointers to the evidence, implementation files, tests, issues, and
   reversals that make the decision checkable.
4. Link the decision from the ExecPlan or issue that needs it. Do not record a
   product or architecture decision only in an ExecPlan execution log.

## Release-close Capture

1. Fold accepted/rejected decisions into the release's frozen chapter under
   `design-history/`.
2. Update `design-history/arcs.md` when the release changes the current line,
   and keep unreleased questions under `Pending (unreleased)`.
3. Keep `docs/` focused on current behavior. Use `design-history/` for why the
   current behavior exists or how it replaced older designs.
4. Leave historical notes and retired ADRs as evidence only. Do not treat them
   as current authority when implementation or release decisions disagree.

## Verification

- Check workflow prose with `rg -n 'ADR' .agents/ AGENTS.md` and confirm every
  match is historical, a retirement note, or an explicit verification example.
- Run the relevant focused tests for any changed doctor, policy, or docs link
  behavior.
- Run `python3 scripts/verify l0` before merge unless the task explicitly scopes
  to docs-only evidence and the maintainer accepts a narrower check.
