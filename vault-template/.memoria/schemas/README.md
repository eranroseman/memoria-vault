# Schemas

This directory owns the machine-readable alpha.11 workspace contract.

- `types/` defines frontmatter by Concept type.
- `folders.yaml` owns bundle roots, type homes, staging/quarantine roots, and
  the empty-folder skeleton.
- `calibration.yaml` owns shared thresholds.

Consumers should use `../operations/lib/schema.py` instead of parsing or duplicating
schema rules. Dependency-free fallback constants are permitted only for standalone
startup and must be equality-tested against these files.
