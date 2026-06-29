# WP Cluster Alpha.11 Path Repair Results

Timestamp: 2026-06-29T13:24:00Z

Scope: local repair of the cluster MCP after the alpha.11 folder reset:

- `cluster_mcp.py` now scans alpha.11 Concept homes under `knowledge/notes`,
  `knowledge/hubs`, `knowledge/projects`, `catalog/sources`, and
  `catalog/entities`;
- graph node IDs are path-based (`knowledge/notes/example`) instead of bare
  stems, with the source file path included in each node row;
- typed edges come from `links` and `relationships` maps and resolve full
  Concept paths, while unique bare wikilinks still resolve when unambiguous;
- `cluster_emit_canvas()` defaults to `knowledge/notes`, writes only under
  `knowledge/notes/maps/`, and colors note nodes by `status` instead of the
  retired maturity ladder;
- `cluster_model_topics()` defaults to `knowledge/notes` and reports document
  IDs as Concept paths without `.md`;
- current reference docs no longer advertise deleted alpha.10 paths such as
  `notes/claims`, `notes/sources`, or `notes/fleeting/maps` for cluster tools.

Verification:

```bash
python -m pytest tests/test_cluster_mcp.py tests/test_profiles.py tests/test_policy_mcp.py -q
python -m ruff check vault-template/.memoria/mcp/cluster_mcp.py tests/test_cluster_mcp.py
python -m ruff format --check vault-template/.memoria/mcp/cluster_mcp.py tests/test_cluster_mcp.py
python scripts/docs_doctor.py docs
scripts/verify package --evidence-dir /tmp/memoria-alpha11-package-verify-cluster-alpha11
```

Result: all passed. The package verifier reported 593 tests plus the alpha.11
offline e2e smoke; evidence bundle:
`/tmp/memoria-alpha11-package-verify-cluster-alpha11/summary.json`.
