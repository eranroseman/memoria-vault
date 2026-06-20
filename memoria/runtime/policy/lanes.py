"""Lane policy loading and gated-prefix discovery."""

from __future__ import annotations

from pathlib import Path

from .model import LanePolicy
from .paths import REVIEW_GATED_PREFIXES

try:  # PyYAML is a runtime dependency; pure decisions still import without it.
    import yaml
except ImportError:
    yaml = None  # type: ignore[assignment]


LANE_OVERRIDE_RELDIR = ".memoria/lane-overrides"


def load_gated_prefixes(vault: Path) -> tuple[str, ...]:
    """Load review-gated prefixes from the schema home, with a stdlib fallback."""
    try:
        import yaml

        path = Path(vault) / ".memoria" / "schemas" / "folders.yaml"
        data = yaml.safe_load(path.read_text(encoding="utf-8"))
        prefixes = tuple(data["gated_prefixes"])
        return prefixes or REVIEW_GATED_PREFIXES
    except Exception:  # noqa: BLE001 -- schema load with import-inside-try; degrade to default prefixes
        return REVIEW_GATED_PREFIXES


def _auto_fix_classes(block: dict, key: str) -> list[str]:
    sub = (block or {}).get(key) or {}
    if isinstance(sub, dict):
        return list(sub.get("classes") or [])
    return []


def parse_lane(doc: dict) -> LanePolicy:
    """Build a LanePolicy from a parsed lane-override mapping."""
    policy = doc.get("policy") or {}
    allow = policy.get("allow") or {}
    deny = policy.get("deny") or {}
    routing = doc.get("routing") or {}
    return LanePolicy(
        profile=doc.get("profile", ""),
        allow_skills=list(allow.get("skills") or []),
        allow_write=list(allow.get("write") or []),
        allow_read=list(allow.get("read") or []),
        allow_auto_fix_classes=_auto_fix_classes(allow, "auto_fix"),
        deny_skills=list(deny.get("skills") or []),
        deny_write=list(deny.get("write") or []),
        deny_read=list(deny.get("read") or []),
        deny_auto_fix_classes=_auto_fix_classes(deny, "auto_fix"),
        require=list(policy.get("require") or []),
        invocation=routing.get("invocation", "dispatched"),
        external_api_policy=routing.get("external_api_policy", "blocked"),
        write_scope=list(routing.get("write_scope") or []),
    )


def load_lane(vault: Path, profile: str) -> LanePolicy:
    """Read and parse the lane override for ``profile``."""
    if yaml is None:
        raise RuntimeError(
            "PyYAML not installed -- run `pip install -r .memoria/mcp/requirements.txt`."
        )
    lane = profile[len("memoria-") :] if profile.startswith("memoria-") else profile
    path = vault / LANE_OVERRIDE_RELDIR / f"{lane}.yaml"
    if not path.is_file():
        raise FileNotFoundError(f"no lane-override for profile '{profile}' at {path}")
    doc = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    return parse_lane(doc)
