#!/usr/bin/env bash
# Static runtime-vault manifest consumed by install.sh.
# shellcheck disable=SC2034  # sourced declaration is consumed by install.sh

# Canonical empty-folder skeleton. Keep this list aligned with
# vault-template/.memoria/schemas/folders.yaml; tests/test_installer_skeleton.py enforces it.
SKELETON_DIRS=(
  .memoria/index
  .memoria/index/qmd
  .memoria/audit
  .memoria/config
  .memoria/quarantine
  .memoria/blobs
  .memoria/blobs/provider-payloads
  .memoria/blobs/source-content
  .memoria/staging/catalog
  .memoria/staging/knowledge
  .memoria/staging/capabilities
  journal
  catalog
  catalog/sources
  catalog/entities
  knowledge
  knowledge/digests
  knowledge/notes
  knowledge/hubs
  knowledge/projects
  knowledge/views
  capabilities
  capabilities/adapters
  capabilities/operations
  capabilities/skills
  capabilities/workflows
  system/exports
  system/exports/assets
  system/logs
  system/logs/sessions
  system/metrics
  system/dashboards
)
