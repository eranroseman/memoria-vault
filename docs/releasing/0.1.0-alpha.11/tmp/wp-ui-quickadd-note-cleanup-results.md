# WP-UI QuickAdd Note Cleanup Results

Timestamp: 2026-06-29T02:20:07Z

Scope: alpha.11 cleanup for the visible Obsidian/QuickAdd surface after the
schema reset:

- retired the shipped `Memoria: capture fleeting` command and replaced it with
  `Memoria: capture note`;
- removed the `archive fleeting` QuickAdd command instead of restoring the
  deleted `fleeting` type/template;
- `capture-note.js` writes unchecked `note` Concepts to `knowledge/notes/`
  from `system/templates/note.md`;
- Modal Forms now exposes `memoria-note-capture`; `scripts/gen-forms.py`
  generates the committed Modal Forms data without depending on deleted
  `creation.form` schema blocks;
- Commander, app defaults, navigation rail, home, Inbox, Maintenance, and
  space dashboards point at alpha.11 homes/Bases;
- exploration traces and hub-threshold handoffs now use `knowledge/notes/maps/`
  with `type: note` / `check_status: unchecked`.

This is not the full WP8 plugin. It removes stale alpha.10 QuickAdd/fleeting
surface area and keeps the shipped Obsidian shell from referencing deleted
templates, Bases, or type homes.

Verification:

```bash
python -m pytest tests/test_quickadd.py tests/test_workspaces.py tests/test_modalforms.py tests/test_exploration_trace.py tests/test_hub_handoff.py
python -m pytest tests/test_operations.py tests/test_capture.py tests/test_trusted_writer.py tests/test_worker_queue.py tests/test_search_index.py tests/test_qmd_filter_mcp.py tests/test_patterns.py tests/test_schemas.py tests/test_package_spine.py tests/test_installer_skeleton.py tests/test_detectors.py tests/test_quickadd.py tests/test_workspaces.py tests/test_modalforms.py tests/test_exploration_trace.py tests/test_hub_handoff.py tests/test_templates.py tests/test_bases.py tests/test_precommit_schema.py
python -m ruff check scripts/gen-forms.py scripts/gen_reference_refs.py vault-template/.memoria/operations/integrity/linter/hub_handoff.py src/memoria_vault/runtime/operations.py src/memoria_vault/runtime/capture.py src/memoria_vault/runtime/search_index.py src/memoria_vault/runtime/trusted_writer.py src/memoria_vault/runtime/worker.py src/memoria_vault/runtime/__init__.py tests/test_modalforms.py tests/test_quickadd.py tests/test_workspaces.py tests/test_exploration_trace.py tests/test_hub_handoff.py tests/test_operations.py tests/test_capture.py tests/test_trusted_writer.py tests/test_worker_queue.py tests/test_search_index.py tests/test_qmd_filter_mcp.py tests/test_patterns.py tests/test_schemas.py
python -m ruff format --check scripts/gen-forms.py scripts/gen_reference_refs.py vault-template/.memoria/operations/integrity/linter/hub_handoff.py src/memoria_vault/runtime/operations.py src/memoria_vault/runtime/capture.py src/memoria_vault/runtime/search_index.py src/memoria_vault/runtime/trusted_writer.py src/memoria_vault/runtime/worker.py src/memoria_vault/runtime/__init__.py tests/test_modalforms.py tests/test_quickadd.py tests/test_workspaces.py tests/test_exploration_trace.py tests/test_hub_handoff.py tests/test_operations.py tests/test_capture.py tests/test_trusted_writer.py tests/test_worker_queue.py tests/test_search_index.py tests/test_qmd_filter_mcp.py tests/test_patterns.py tests/test_schemas.py
python scripts/gen-forms.py --check
python scripts/gen_reference_refs.py --check
python scripts/docs_doctor.py docs
python scripts/agents_doctor.py --write
python scripts/agents_doctor.py
python scripts/status_doctor.py
bash -n scripts/install.sh scripts/install/manifest.sh
git diff --check
```

Result: all passed.
