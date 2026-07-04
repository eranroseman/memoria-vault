# Source-of-truth map

Use this map to locate the file that owns a contract. Consumer files may mirror
or explain the contract, but they must not silently redefine it.

This map is how you uphold AGENTS.md's **Zero tolerated contradictions** principle:
find the owning file, then fix the stale consumer rather than the source.

| Contract | Authoritative source | Important consumers and checks |
|---|---|---|
| Repository agent policy | `AGENTS.md` | `.agents/`, contributor docs |
| Vault document types and fields | `vault-template/.memoria/schemas/types/*.yaml` | Templates, linter, pre-commit, Bases tests |
| Type homes, staging/quarantine roots, skeleton | `vault-template/.memoria/schemas/folders.yaml` | Installer, linter, templates, dashboards, worker promotion tests |
| Calibrated thresholds | `vault-template/.memoria/schemas/calibration.yaml` | Ingest, classification, clustering, evaluation |
| Installed profile absence | `tests/test_profiles.py` + `scripts/alpha14_negative_gate.py` | Installer tests, profile reference page |
| Runtime path and glob semantics | `src/memoria_vault/runtime/policy/` | Runtime policy tests and optional adapter policy hooks |
| Runtime helper primitives | `src/memoria_vault/runtime/{vaultio,jsonl,time,paths}.py` | Runtime subsystems, operations, test harnesses |
| Runtime write decisions and audit | `src/memoria_vault/runtime/policy/{model,decision,workspace,audit,engine}.py` | `src/memoria_vault/runtime/policy/hook.py`, optional policy gate plugin, audit log |
| Write interception for optional adapters | `src/memoria_vault/runtime/policy/hook.py` and `vault-template/.memoria/plugins/memoria-policy-gate/` | Optional adapter plugin tests |
| Shared schema validation | `src/memoria_vault/runtime/subsystems/lib/schema.py` | Linter, pre-commit, installer and schema tests |
| Inbox card rendering and loudness routing | `src/memoria_vault/runtime/subsystems/lib/inbox.py` + `src/memoria_vault/runtime/subsystems/lib/loudness.py` | Operations that raise attention items; Home/Telegram push; request and policy block checks |
| Runtime vault image | `vault-template/` | `scripts/install.sh`, golden-copy staging |
| Dropped Obsidian baseline payload | `scripts/alpha14_negative_gate.py` + `scripts/plugin_provenance_doctor.py` | `tests/test_plugin_provenance.py`, package smoke, current docs |
| Installer behavior and flags | `scripts/install.sh`, `scripts/install/`, and `scripts/install.ps1` | Installer reference and setup guides |
| Required CI behavior | `.github/workflows/` and `.github/ruleset-contract.yaml` | Live branch ruleset, `scripts/ruleset_doctor.py`, and `AGENTS.md` |
| Offline e2e smoke stages | `scripts/e2e_smoke.py` | `scripts/e2e-smoke.sh`, ADR-80/testing docs, release stage evidence |
| Standalone disposable install harness | `scripts/install-test-vault-local-llm.sh` | `tests/test_install_test_vault_local_llm.py`, testing verification matrix |
| Contributor Python tooling | `requirements-dev.txt` | Dev setup, lint workflows, python-selftest, Dependabot |
| Contributor code search (qmd) | `package.json` + `scripts/qmd-codebase-index.sh` / `scripts/qmd-install-hooks.sh` | AGENTS.md "Searching the codebase (qmd)", dev setup |
| GitHub issue and dependency hygiene | `.github/ISSUE_TEMPLATE/` and `.github/dependabot.yml` | `scripts/github_doctor.py`, issue tracking docs |
| Agent change-impact registry | `.agents/system/change-impact.yaml` | Generated change-impact map and agent doctor |
| PR trust classification | `.github/scripts/pr_policy.py` | `.github/workflows/pr-review-gate.yml`, policy tests |
| ADR decision state | `docs/adr/` frontmatter and `docs/adr/README.md` | Linked GitHub issues for implementation/readiness |
| Work readiness and scheduling | Memoria Issue Tracker fields (`Status`, `Readiness`) and milestones | ADR Related sections and release plans |
| Release scope | GitHub milestone + Memoria Issue Tracker view | Release plan prose and release parent issue |
| Release readiness | `Release <version>` parent issue + gate/stage sub-issues | Release plan and release playbook |
| Release design scratch | `scratch` branch, under `scratch/releases/<version>/` while in progress | Status doctor, release playbook, ExecPlan playbook |
| Release scope/readiness | GitHub milestone, Memoria Issue Tracker, and "Release <version>" parent issue/sub-issues | Release playbook and release template |
| Product decisions | `docs/adr/` | Current docs and implementation |
| Public system model | `docs/README.md` | Tutorials, how-to guides, Reference, Explanation, Design Book |
| Public behavior documentation | Diátaxis pages under `docs/` | README and section indexes |

## Mirrors and Cached Views

Mirrors are permitted only when they are explicitly consumer-facing views of an
owned source. Treat a mirror as a cache, never as a second authority:

- It names or links the owning source in prose, frontmatter, or the surrounding
  reference section.
- It repeats only the contract detail needed by its audience.
- It is generated or covered by a drift check when it repeats machine-readable
  contracts such as counts, rosters, required fields, write scopes, command
  catalogs, lifecycle subsets, plugin inventories, required CI checks, or
  calibration values.
- Frozen release records may preserve historical copies, but they must be
  labeled as frozen and must not be used as current implementation evidence.

## Mirrored constants

The packaged policy layer and schema loader carry a dependency-free fallback for
review-gated prefixes. `folders.yaml` does not declare these prefixes; tests
prove the fallback constants agree with each other and stay separate from the
worker-owned staging/promote/quarantine boundary.

## Decision rule

When two files disagree:

1. Identify the owner in this map.
2. Confirm the owner still represents the intended current decision.
3. Update consumers and tests together.
4. If ownership itself must change, record the decision in an ADR before moving
   the contract.
