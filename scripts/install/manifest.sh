#!/usr/bin/env bash
# Static runtime-vault manifest consumed by install.sh.
# shellcheck disable=SC2034  # sourced declaration is consumed by install.sh

# Canonical empty-folder skeleton. Keep this list aligned with
# vault-template/.memoria/schemas/folders.yaml; tests/test_installer_skeleton.py enforces it.
SKELETON_DIRS=(
  .memoria/index
  .memoria/index/search
  .memoria/audit
  .memoria/config
  .memoria/quarantine
  .memoria/blobs
  .memoria/blobs/provider-payloads
  .memoria/blobs/source-content
  .memoria/staging/works
  .memoria/staging/sources
  .memoria/staging/notes
  .memoria/staging/hubs
  .memoria/staging/projects
  inbox
  works
  sources
  notes
  hubs
  projects
  system
  system/incidents
  system/metrics
  system/eval
)
