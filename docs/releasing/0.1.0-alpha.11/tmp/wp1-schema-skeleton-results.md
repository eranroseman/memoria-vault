# WP1 schema skeleton results

Date: 2026-06-29

Verdict: **pass for the local WP1 schema/skeleton contract**.

## What landed

- Canonical alpha.11 Concept schemas now live in
  `vault-template/.memoria/schemas/types/` for `source`, `person`,
  `organization`, `venue`, `digest`, `note`, `hub`, `project`, `operation`,
  `skill`, `mcp`, and `workflow`.
- `folders.yaml` now owns the three bundle roots (`catalog/`, `knowledge/`,
  `capabilities/`), type homes, staging roots, quarantine root, and installer
  skeleton; it no longer declares alpha.10 review-gated prefixes as a live
  schema boundary.
- Shared schema validation now exposes:
  - `validate_okf_core_workspace(...)`
  - `validate_memoria_profile_workspace(...)`
- The minimal `catalog/`, `knowledge/`, and `capabilities/` fixture validates
  before copy export, after copy export, and after copy import, with markdown
  content preserved byte-for-byte.
- The PI-created templates are reduced to alpha.11 `note`, `hub`, and `project`.
- Bases are reduced to minimal alpha.11 bundle views for catalog, knowledge, and
  capabilities.
- Capability import now has the local unsigned-denial path: unsigned imported
  capability files are copied to `.memoria/quarantine/`, recorded as failed
  `capability-import-trust` checks, omitted from `ai-catalog.json`, and not
  loadable as executable operation policy.
- The prompt-pattern runner now reads checked `operation` Concepts from
  `capabilities/operations/`; the old `system/patterns/` files were moved into
  the capability bundle.
- Schema-backed reference docs now generate from the alpha.11 Concept schemas,
  and the QuickAdd pattern pickers list checked operations from
  `capabilities/operations/`.
- The fresh template no longer tracks alpha.10 placeholder roots such as
  `notes/`, `projects/`, `inbox/`, split `catalog/papers`/`people`/`venues`
  folders, `system/board`, or `system/worklists`.
- `refresh-test-vault.sh` now syncs the alpha.11 skeleton surfaces, including
  the checked `capabilities/` bundle, instead of deleted alpha.10 Bases.
- `test_alpha11_fresh_package_contract_is_shipped` pins the G2 package surface
  directly to `folders.yaml`, `scripts/install/manifest.sh`, and
  `vault-template/`: `catalog/`, `knowledge/`, `capabilities/`, `steering.md`,
  journal, queue, tracked projections, and the disposable qmd index skeleton.
- `scripts/e2e-smoke.sh` now replays the package gate with alpha.11 artifacts:
  checked source capture plus `references.bib`, checked project notes, an
  argument canvas projection, an attention prompt, and the denied forbidden
  `knowledge/notes` write.
- The legacy `archive_inbox.py` direct-write sweep and its
  `inbox.archive_after_days` calibration knob are removed from the shipped
  skeleton; alpha.11 attention disposition is worker-owned.

## Evidence

| Check | Result |
| --- | --- |
| `python scripts/gen_reference_refs.py --check` | pass |
| `python -m pytest tests/test_schemas.py tests/test_templates.py tests/test_bases.py tests/test_precommit_schema.py tests/test_detectors.py tests/test_patterns.py tests/test_policy_mcp.py tests/test_installer_skeleton.py::test_skeleton_covers_the_schema_skeleton tests/test_installer_skeleton.py::test_skeleton_covers_every_type_home tests/test_quickadd.py::test_assist_surface_commands_are_staged_and_skill_backed tests/test_quickadd.py::test_run_pattern_uses_checked_operations` | pass, 54 tests |
| `python -m ruff check scripts/gen_reference_refs.py scripts/docs_doctor.py tests/test_quickadd.py vault-template/.memoria/operations/lib/schema.py vault-template/.memoria/operations/integrity/linter/detectors.py vault-template/.memoria/mcp/patterns_mcp.py` | pass |
| `python -m ruff format --check scripts/gen_reference_refs.py scripts/docs_doctor.py tests/test_quickadd.py vault-template/.memoria/operations/lib/schema.py vault-template/.memoria/operations/integrity/linter/detectors.py vault-template/.memoria/mcp/patterns_mcp.py` | pass |
| `python scripts/docs_doctor.py docs` | pass |
| `python scripts/agents_doctor.py` | pass |
| `python scripts/status_doctor.py` | pass |
| `bash -n scripts/install.sh scripts/install/manifest.sh` | pass |
| `git diff --check` | pass |
| `python -m pytest tests/test_installer_skeleton.py tests/test_refresh_test_vault.py` | pass, 31 tests |
| `python -m pytest tests/test_schemas.py tests/test_patterns.py tests/test_profiles.py tests/test_installer_skeleton.py tests/test_refresh_test_vault.py` | pass, 76 tests |
| `python -m pytest tests/test_capabilities.py` | pass, 4 tests |
| `python -m pytest tests/test_installer_skeleton.py::test_alpha11_fresh_package_contract_is_shipped tests/test_projections.py::test_shipped_workspace_indexes_are_current -q` | pass, 2 tests |
| `python -m ruff check tests/test_installer_skeleton.py tests/test_projections.py` | pass |
| `python -m ruff format --check tests/test_installer_skeleton.py tests/test_projections.py` | pass |
| `bash scripts/e2e-smoke.sh` | pass: fresh vault assembly, skeleton check, golden system-file staging, plugin bundle check, fresh-vault integrity, commit gate, offline ingest with `references.bib`, argument canvas projection, package-gate cassette replay, denied forbidden write, and final integrity review all green |
| `python -m pytest tests/test_test_env_harness.py tests/test_e2e_smoke_helpers.py -q` | pass, 5 tests |
| `python -m ruff check scripts/test_env_harness.py scripts/e2e_smoke.py tests/test_test_env_harness.py tests/test_e2e_smoke_helpers.py` | pass |
| `python -m ruff format --check scripts/test_env_harness.py scripts/e2e_smoke.py tests/test_test_env_harness.py tests/test_e2e_smoke_helpers.py` | pass |
| `scripts/verify package --evidence-dir /tmp/memoria-alpha11-package-verify-2` | pass, 603 tests plus alpha.11 e2e smoke; evidence bundle: `/tmp/memoria-alpha11-package-verify-2/summary.json` |
| `scripts/verify package --evidence-dir /tmp/memoria-alpha11-package-verify-archive-retire` | pass, 593 tests plus alpha.11 e2e smoke after retiring the legacy inbox archival sweep; evidence bundle: `/tmp/memoria-alpha11-package-verify-archive-retire/summary.json` |
| `scripts/test.sh all` | pass, 594 tests plus L0 static/schema/docs/provenance/shell checks |
| `npx --yes cspell@8.19.4 lint --no-progress --no-must-find-files --gitignore "**/*.md"` | pass, 485 markdown files checked |

## Limits

This proves local schema/template/package shape, not attended runtime install
behavior. The fresh-install assertion is package-level evidence from the shipped
template and installer manifest; it is not a live `Memoria-test` product run.
Traced writes, promotion, PI-edit observation, and foreign-write quarantine are
covered by the WP2 evidence file. The pre-alpha.11 profile policy modules still
keep their dependency-free fallback constants for their own legacy tests; they
are not the alpha.11 write boundary.
