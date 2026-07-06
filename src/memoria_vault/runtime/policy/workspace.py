"""Workspace policy loading and gated-prefix discovery."""

from __future__ import annotations

from pathlib import Path

import yaml

from .model import ActorPolicy
from .paths import REVIEW_GATED_PREFIXES

POLICY_CONFIG_RELPATH = ".memoria/config/policy.yaml"


def load_gated_prefixes(workspace: Path) -> tuple[str, ...]:
    """Load review-gated prefixes, with a stdlib fallback."""
    try:
        path = Path(workspace) / ".memoria" / "schemas" / "folders.yaml"
        data = yaml.safe_load(path.read_text(encoding="utf-8"))
        prefixes = tuple(data.get("gated_prefixes") or ())
        return prefixes or REVIEW_GATED_PREFIXES
    except Exception:  # noqa: BLE001 -- schema load with import-inside-try; degrade to default prefixes
        return REVIEW_GATED_PREFIXES


def _auto_fix_classes(block: dict, key: str) -> list[str]:
    sub = (block or {}).get(key) or {}
    if isinstance(sub, dict):
        return list(sub.get("classes") or [])
    return []


def parse_actor_policy(actor: str, doc: dict) -> ActorPolicy:
    """Build an ActorPolicy from one actor entry in workspace policy config."""
    allow = (doc or {}).get("allow") or {}
    deny = (doc or {}).get("deny") or {}
    return ActorPolicy(
        actor=actor,
        allow_tools=list(allow.get("tools") or []),
        allow_write=list(allow.get("write") or []),
        allow_read=list(allow.get("read") or []),
        allow_auto_fix_classes=_auto_fix_classes(allow, "auto_fix"),
        deny_tools=list(deny.get("tools") or []),
        deny_write=list(deny.get("write") or []),
        deny_read=list(deny.get("read") or []),
        deny_auto_fix_classes=_auto_fix_classes(deny, "auto_fix"),
        require=list((doc or {}).get("require") or []),
        invocation=str((doc or {}).get("invocation") or "request"),
        external_api_policy=str((doc or {}).get("external_api_policy") or "blocked"),
        write_scope=list((doc or {}).get("write_scope") or []),
    )


def load_policy_map(workspace: Path) -> dict[str, ActorPolicy]:
    """Read and parse workspace actor policy config."""
    path = workspace / POLICY_CONFIG_RELPATH
    if not path.is_file():
        raise FileNotFoundError(f"workspace policy config not found at {path}")
    doc = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    actors = doc.get("actors") or {}
    if not isinstance(actors, dict) or not actors:
        raise ValueError(f"workspace policy config has no actors: {path}")
    return {
        str(actor): parse_actor_policy(str(actor), body or {}) for actor, body in actors.items()
    }


def load_actor_policy(workspace: Path, actor: str) -> ActorPolicy:
    """Read the workspace policy entry for ``actor``."""
    policies = load_policy_map(workspace)
    try:
        return policies[actor]
    except KeyError as exc:
        raise KeyError(f"workspace policy has no actor '{actor}'") from exc
