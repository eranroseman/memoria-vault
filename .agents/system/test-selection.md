# Test selection

Choose tests by risk and blast radius. Focused tests provide fast diagnosis; the
full gate proves repository integration. This file owns which verification
commands to run; [verify-change](../playbooks/verify-change.md) owns
claim/evidence reporting.

## Baseline

For every change:

```bash
git diff --check
```

Run the nearest focused tests for the changed contract. Before PR handoff, run:

```bash
python3 scripts/verify pr
```

If the environment lacks pytest or another required dependency, report that
explicitly; do not describe an unrun check as passing.
Install contributor Python tooling from `requirements-dev.txt`; runtime package
dependencies come from `pyproject.toml` and are installed into the workspace venv.

## Focused checks

Use [change-impact-map.md](change-impact-map.md) for path-to-check selection.
It is generated from [change-impact.yaml](change-impact.yaml), which is the only
maintained table for changed paths, related consumers, and primary focused
checks. If a recurring change area is missing, add it to `change-impact.yaml`
instead of creating another table here.

## Full-gate triggers

Always run `python3 scripts/verify pr` when a change:

- Touches a shared schema, policy, profile, installer, or CI contract
- Affects more than one runtime subsystem
- Changes generated or deployed vault structure
- Fixes a regression not previously covered
- Is ready for PR handoff

Promote beyond the PR gate when the changed contract crosses a release boundary:

- Package seed, installer, hook, optional adapter, or workflow replay changes:
  run `python3 scripts/verify package`.
- Installer behavior changes: also run
  `bash scripts/sandbox/install-test-vault-local-llm.sh --root ~/memoria-vault/sandbox`
  or record why the disposable install check could not run.
- Runtime wiring, worker loops, scheduled wrappers, recovery, live model
  endpoint, or policy-boundary changes: run `python3 scripts/verify runtime` or
  record the missing prerequisite.
- Release-candidate close-out: run
  `python3 scripts/verify rc --evidence-dir <release-evidence-dir>` and link
  the resulting `summary.json` from the release parent issue.

## Runtime-dependent verification

The full local gate does not prove Hermes, Obsidian, Windows PowerShell, Zotero,
or network-backed scholarly APIs. Use the relevant disposable or attended test
plan and state the limitation when those environments are unavailable.
