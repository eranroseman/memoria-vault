# Test selection

Choose tests by risk and blast radius. Focused tests provide fast diagnosis; the
full gate proves repository integration.

## Baseline

For every change:

```bash
git diff --check
```

Run the nearest focused tests for the changed contract. Before PR handoff, run:

```bash
scripts/test.sh all
```

If the environment lacks pytest or another required dependency, report that
explicitly; do not describe an unrun check as passing.
Install contributor Python tooling from `requirements-dev.txt`; runtime MCP
dependencies remain in `vault-template/.memoria/mcp/requirements.txt`.

## Focused checks

Use [change-impact-map.md](change-impact-map.md) for path-to-check selection.
It is generated from [change-impact.yaml](change-impact.yaml), which is the only
maintained table for changed paths, related consumers, and primary focused
checks. If a recurring change area is missing, add it to `change-impact.yaml`
instead of creating another table here.

## Full-gate triggers

Always run `scripts/test.sh all` when a change:

- Touches a shared schema, policy, profile, installer, or CI contract
- Affects more than one runtime subsystem
- Changes generated or deployed vault structure
- Fixes a regression not previously covered
- Is ready for PR handoff

## Runtime-dependent verification

The full local gate does not prove Hermes, Obsidian, Windows PowerShell, Zotero,
or network-backed scholarly APIs. Use the relevant disposable or attended test
plan and state the limitation when those environments are unavailable.
