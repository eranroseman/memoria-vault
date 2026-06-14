#!/usr/bin/env bash
# Static runtime-vault manifest consumed by install.sh.
# shellcheck disable=SC2034  # sourced declaration is consumed by install.sh

# Canonical empty-folder skeleton. Keep this list aligned with
# src/.memoria/schemas/folders.yaml; tests/test_installer_skeleton.py enforces it.
SKELETON_DIRS=(
  .memoria/csl
  .memoria/lane-overrides
  .memoria/profiles/memoria-librarian/cron
  .memoria/profiles/memoria-librarian/skills
  catalog/papers
  catalog/people
  catalog/organizations
  catalog/venues
  catalog/datasets
  catalog/repositories
  notes/fleeting
  notes/fleeting/chats
  notes/fleeting/maps
  notes/source
  notes/claims
  notes/hubs
  notes/index
  projects
  inbox
  system/board
  system/exports
  system/exports/assets
  system/logs
  system/logs/sessions
  system/metrics
  system/templates
  system/patterns
  system/eval
  system/dashboards
)
