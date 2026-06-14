"""Shared, dependency-free policy semantics."""

from .paths import (
    ACTIONS,
    MUTATING_ACTIONS,
    REVIEW_GATED_PREFIXES,
    glob_to_regex,
    normalize_path,
    path_matches,
    within_scope,
)

__all__ = [
    "ACTIONS",
    "MUTATING_ACTIONS",
    "REVIEW_GATED_PREFIXES",
    "glob_to_regex",
    "normalize_path",
    "path_matches",
    "within_scope",
]
