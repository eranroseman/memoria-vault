# Source-of-truth map

Use this map to locate the file that owns a contract. Consumer files may mirror
or explain the contract, but they must not silently redefine it.

This map is how you uphold AGENTS.md's **Zero tolerated contradictions** principle:
find the owning file, then fix the stale consumer rather than the source.

| Contract | Authoritative source | Important consumers and checks |
|---|---|---|
| Repository agent policy | `AGENTS.md` | `.agents/`, contributor docs |
| Vault document types and fields | `src/.memoria/schemas/types/*.yaml` | Templates, linter, pre-commit, Bases tests |
| Type homes, gated zones, skeleton | `src/.memoria/schemas/folders.yaml` | Policy MCP, installer, linter, templates, dashboards |
| Calibrated thresholds | `src/.memoria/schemas/calibration.yaml` | Ingest, classification, clustering, evaluation |
| Profile tool capabilities | `src/.memoria/tool-registry.yaml` | Profile configs, profile tests, skill lifecycle dashboard |
| Profile path permissions | `src/.memoria/lane-overrides/*.yaml` | Policy MCP, policy plugin, tasks MCP, profile tests |
| Hermes profile runtime wiring | `src/.memoria/profiles/*/config.yaml` | Installer deployment, MCP process startup |
| Agent posture | `src/.memoria/profiles/*/SOUL.md` | Profile-owned skills and shared `src/AGENTS.md` |
| Profile package metadata | `src/.memoria/profiles/*/distribution.yaml` | Installer profile deployment |
| Task lane to profile routing | `src/.memoria/mcp/tasks_mcp.py` | QuickAdd delegation, board cards, task tests |
| Runtime path and glob semantics | `memoria/runtime/policy/` | Policy MCP, tasks MCP, patterns MCP |
| Runtime helper primitives | `memoria/runtime/{vaultio,jsonl,time,paths}.py` | MCP modules, operations, test harnesses |
| Runtime write decisions and audit | `memoria/runtime/policy/{model,decision,lanes,audit,engine}.py` | `src/.memoria/mcp/policy_mcp.py`, `src/.memoria/mcp/policy_server.py`, policy hook/plugin, lane overrides, audit log |
| Write interception | `src/.memoria/plugins/memoria-policy-gate/` and `src/.memoria/mcp/policy_hook.py` | Every profile's enabled plugins |
| Shared schema validation | `src/.memoria/operations/lib/schema.py` | Linter, pre-commit, installer and schema tests |
| Inbox card rendering and loudness routing | `src/.memoria/operations/lib/inbox.py` + `src/.memoria/operations/lib/loudness.py` | Operations and lanes that raise cards; Home/Telegram push; tasks and policy block checks |
| Runtime vault image | `src/` | `scripts/install.sh`, golden-copy staging |
| Bundled Obsidian plugin provenance | `src/.obsidian/plugin-provenance-lock.json` | `scripts/plugin_provenance_doctor.py`, CI lint, `tests/test_plugin_provenance.py`, plugin reference |
| Installer behavior and flags | `scripts/install.sh`, `scripts/install/`, and `scripts/install.ps1` | Installer reference and setup guides |
| Required CI behavior | `.github/workflows/` and `.github/ruleset-contract.yaml` | Live branch ruleset, `scripts/ruleset_doctor.py`, and `AGENTS.md` |
| Offline e2e smoke stages | `scripts/e2e_smoke.py` | `scripts/e2e-smoke.sh`, ADR-80/testing docs, release stage evidence |
| Live Hermes L2 smoke contract | `scripts/test-l2.sh` | `scripts/l2_smoke.py`, `scripts/l2_openai_smoke_server.py`, `scripts/l2_obsidian_mcp_shim.py`, ADR-29, testing coverage matrix |
| Contributor Python tooling | `requirements-dev.txt` | Dev setup, lint workflows, python-selftest, Dependabot |
| Contributor code search (qmd) | `package.json` + `scripts/qmd-codebase-index.sh` / `scripts/qmd-install-hooks.sh` | AGENTS.md "Searching the codebase (qmd)", dev setup |
| GitHub issue and dependency hygiene | `.github/ISSUE_TEMPLATE/` and `.github/dependabot.yml` | `scripts/github_doctor.py`, issue tracking docs |
| Agent change-impact registry | `.agents/system/change-impact.yaml` | Generated change-impact map and agent doctor |
| PR trust classification | `.github/scripts/pr_policy.py` | `.github/workflows/pr-review-gate.yml`, policy tests |
| ADR decision state | `docs/adr/` frontmatter and `docs/adr/README.md` | Linked GitHub issues for implementation/readiness |
| Work readiness and scheduling | Memoria Issue Tracker fields (`Status`, `Readiness`) and milestones | ADR Related sections and release plans |
| Release scope | GitHub milestone + Memoria Issue Tracker view | Release plan prose and release parent issue |
| Release readiness | `Release vX.Y` parent issue + gate/stage sub-issues | Release plan and release playbook |
| Release design scratch | `docs/releasing/<version>/tmp/` while in progress | Status doctor and release playbook |
| Release prose | `docs/releasing/<version>/release-plan-*.md` | Release index and status doctor |
| Product decisions | `docs/adr/` | Current docs and implementation |
| Public system model | `docs/the-model.md` | Tutorials, how-to guides, Reference, Explanation, Design Book |
| Docs routing manifest | `.agents/system/docs-manifest.yaml` | Co-PI and agent doc-routing prompts |
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
review-gated prefixes. It is a mirror, not an independent source; tests must
prove it remains equal to canonical `folders.yaml`.

## Decision rule

When two files disagree:

1. Identify the owner in this map.
2. Confirm the owner still represents the intended current decision.
3. Update consumers and tests together.
4. If ownership itself must change, record the decision in an ADR before moving
   the contract.
