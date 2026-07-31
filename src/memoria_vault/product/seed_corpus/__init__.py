"""Shipped seed-corpus manifest: pinned identifiers, licenses, fetch methods.

Fetch-on-onboard, manifest-only (O1 spec section 1): the product ships this
manifest, never third-party content. Every row must clear the license floor;
tests/test_seed_manifest.py carries the impl-start check that re-asserts it.
"""

from __future__ import annotations

import re
from importlib.resources import files
from typing import Any

import yaml

SEED_LICENSE_FLOOR = frozenset({"CC BY", "CC BY 4.0", "CC0"})
SEED_FETCH_METHODS = frozenset({"pmc-oa", "pdf-url", "arxiv-pdf"})
_REQUIRED_ROW_FIELDS = (
    "id",
    "title",
    "identifier",
    "license",
    "license_evidence",
    "fetch",
    "role",
)


def load_seed_manifest() -> list[dict[str, Any]]:
    """Load and validate the packaged seed-corpus manifest."""
    text = files(__package__).joinpath("manifest.yaml").read_text(encoding="utf-8")
    return parse_seed_manifest(text)


def parse_seed_manifest(text: str) -> list[dict[str, Any]]:
    """Parse manifest YAML and enforce the row schema plus the license floor."""
    rows = yaml.safe_load(text)
    if not isinstance(rows, list) or not rows:
        raise ValueError("seed manifest must be a non-empty YAML list of rows")
    for row in rows:
        _validate_row(row)
    ids = [str(row["id"]) for row in rows]
    duplicates = sorted({work_id for work_id in ids if ids.count(work_id) > 1})
    if duplicates:
        raise ValueError(f"seed manifest ids must be unique: {', '.join(duplicates)}")
    return rows


def _validate_row(row: Any) -> None:
    if not isinstance(row, dict):
        raise ValueError("seed manifest rows must be maps")
    label = str(row.get("id") or "<missing id>")
    missing = [field for field in _REQUIRED_ROW_FIELDS if not row.get(field)]
    if missing:
        raise ValueError(f"seed manifest row {label} missing fields: {', '.join(missing)}")
    if row["license"] not in SEED_LICENSE_FLOOR:
        raise ValueError(
            f"seed manifest row {label} license {row['license']!r} fails the license floor"
        )
    if not str(row["license_evidence"]).startswith("https://"):
        raise ValueError(f"seed manifest row {label} license_evidence must be an https URL")
    identifier = str(row["identifier"])
    if not identifier.startswith(("doi:", "arxiv:")):
        raise ValueError(f"seed manifest row {label} identifier must be doi:... or arxiv:...")
    if identifier.startswith("arxiv:") and not re.search(r"v\d+$", identifier):
        raise ValueError(f"seed manifest row {label} arXiv identifier must pin a version")
    fetch = row["fetch"]
    if not isinstance(fetch, dict):
        raise ValueError(f"seed manifest row {label} fetch must be a map")
    if fetch.get("method") not in SEED_FETCH_METHODS:
        raise ValueError(
            f"seed manifest row {label} fetch.method must be one of "
            f"{', '.join(sorted(SEED_FETCH_METHODS))}"
        )
    if not str(fetch.get("url") or "").startswith("https://"):
        raise ValueError(f"seed manifest row {label} fetch.url must be an https URL")
