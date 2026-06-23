# Schemas

This directory owns the machine-readable vault contract.

- `types/` defines frontmatter by document type.
- `folders.yaml` owns type homes, gated prefixes, and the empty-folder skeleton.
- `calibration.yaml` owns shared thresholds.

Consumers should use `../operations/lib/schema.py` instead of parsing or duplicating
schema rules. Dependency-free fallback constants are permitted only for
standalone startup and must be equality-tested against these files.
