"""Compatibility import path for the packaged Memoria policy core.

Installed checkouts should import ``memoria.runtime.policy`` directly. Runtime
vaults still carry this module so the policy gate remains self-contained if the
Hermes plugin host has not imported the editable package yet.
"""

try:
    from memoria.runtime.policy import (
        ACTIONS,
        MUTATING_ACTIONS,
        REVIEW_GATED_PREFIXES,
        glob_to_regex,
        normalize_path,
        path_matches,
        within_scope,
    )
except ModuleNotFoundError:  # deployed-vault fallback for the policy plugin host
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
