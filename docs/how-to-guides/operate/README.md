---
title: Operate
parent: How-to guides
nav_order: 8
has_children: true
permalink: /how-to-guides/operate/
---

# Operate

Terminal-side system upkeep — operational checks and maintenance tasks run from the command line or scheduler.

| Guide | What it covers |
| --- | --- |
| [Run the Linter](run-the-linter.md) | On-demand or scheduled structural health check |
| [Run a retraction sweep](run-a-retraction-sweep.md) | Check ingested papers against retraction registries; update affected claims |
| [Run a schema migration](run-a-schema-migration.md) | Rewrite a frontmatter field across many notes, dry-run first |
| [Redeploy profiles](redeploy-profiles.md) | Push vault source edits out to `~/.hermes/profiles/` |
| [Rebuild the search index](rebuild-the-search-index.md) | Re-run `qmd embed` when Writer search returns stale results |
| [Upgrade the vault to a new release](upgrade-to-a-new-release.md) | Pull a new release and three-way reconcile system files into the live vault |
| [Run the vault eval](run-the-vault-eval.md) | Dispatch and score the gold-set evaluation on demand |
| [Inspect session logs](inspect-session-logs.md) | Read the audit and per-session logs ad-hoc — filter by lane, date, or decision |
