"""Pure policy decisions with no filesystem or adapter dependency."""

from __future__ import annotations

from .model import ActorPolicy, Decision
from .paths import (
    ACTIONS,
    MUTATING_ACTIONS,
    REVIEW_GATED_PREFIXES,
    normalize_path,
    path_matches,
    within_scope,
)

AUTO_FIX_ALLOWED_CLASSES = frozenset({"safe-and-unambiguous", "authorized-targeted"})
AUTO_FIX_DRY_RUN_CLASSES = frozenset({"schema-content"})
AUTO_FIX_DENY_CLASSES = frozenset({"review-gated-edit"})


def is_review_gated(path: str) -> bool:
    """Return whether ``path`` is under a review-gated prefix."""
    return any(
        path == prefix.rstrip("/") or path.startswith(prefix) for prefix in REVIEW_GATED_PREFIXES
    )


def decide(
    actor: str,
    action: str,
    path: str,
    policy: ActorPolicy,
    flags: dict | None = None,
    skill_deny_write: list[str] | None = None,
) -> Decision:
    """Return the policy decision for one request. Pure: no I/O, no logging."""
    flags = flags or {}
    npath = normalize_path(path)
    rule = policy.short
    require_log = "audit_log" in policy.require

    if action not in ACTIONS:
        return Decision("deny", f"{rule}.invalid-action", f"unknown action '{action}'")

    if skill_deny_write and action in MUTATING_ACTIONS and path_matches(npath, skill_deny_write):
        return Decision(
            "deny",
            "skill.deny.write",
            "blocked by the loaded skill's policy.deny (one-way narrowing)",
        )

    if action == "report":
        return Decision("allow", f"{rule}.report", log_required=require_log)

    if action == "read":
        if path_matches(npath, policy.deny_read):
            return Decision("deny", f"{rule}.deny.read", "read denied by workspace policy")
        if is_review_gated(npath):
            return Decision(
                "allow_with_log",
                "read.review-gated",
                "read of canonical/review-gated content",
                log_required=True,
            )
        return Decision("allow", f"{rule}.read", log_required=require_log)

    if action == "auto_fix":
        cls = flags.get("class")
        if not cls:
            return Decision("deny", f"{rule}.auto_fix.no-class", "auto_fix requires flags.class")
        if cls in AUTO_FIX_DENY_CLASSES:
            return Decision(
                "deny", f"{rule}.auto_fix.{cls}", f"auto_fix class '{cls}' is always denied"
            )
        if cls in AUTO_FIX_DRY_RUN_CLASSES:
            return Decision(
                "dry_run",
                f"{rule}.auto_fix.{cls}",
                f"auto_fix class '{cls}' degrades to dry_run -- needs manual schema/content repair",
            )
        if cls in policy.deny_auto_fix_classes:
            return Decision(
                "deny",
                f"{rule}.auto_fix.{cls}",
                f"auto_fix class '{cls}' denied by workspace policy",
            )
        if cls in AUTO_FIX_ALLOWED_CLASSES and cls in policy.allow_auto_fix_classes:
            if not path_matches(npath, policy.allow_write):
                return Decision(
                    "deny",
                    f"{rule}.auto_fix.out-of-scope",
                    f"auto_fix path '{npath}' outside the actor's write scope",
                )
            if is_review_gated(npath):
                return Decision(
                    "dry_run",
                    "review_gated.dry_run",
                    "review-gated zone -- surface as an attention item",
                )
            return Decision("allow_with_log", f"{rule}.auto_fix.{cls}", log_required=True)
        return Decision(
            "deny",
            f"{rule}.auto_fix.class-not-allowed",
            f"auto_fix class '{cls}' not permitted for {actor}",
        )

    if action == "delete":
        if not flags.get("explicit_authorization"):
            return Decision(
                "deny",
                f"{rule}.delete.default-deny",
                "delete requires flags.explicit_authorization",
            )
        if not path_matches(npath, policy.allow_write):
            return Decision(
                "deny",
                f"{rule}.delete.out-of-scope",
                f"delete path '{npath}' outside the actor's write scope",
            )
        if is_review_gated(npath):
            return Decision(
                "dry_run",
                "review_gated.dry_run",
                "review-gated zone -- delete requires PI disposition through attention",
            )
        return Decision("allow_with_log", f"{rule}.delete", log_required=True)

    if action == "mkdir":
        if not within_scope(npath, policy.write_scope):
            return Decision(
                "deny", f"{rule}.mkdir.out-of-scope", f"mkdir '{npath}' outside write_scope"
            )
        if is_review_gated(npath):
            return Decision("dry_run", "review_gated.dry_run", "review-gated zone")
        return Decision("allow", f"{rule}.mkdir", log_required=require_log)

    if path_matches(npath, policy.deny_write):
        return Decision("deny", f"{rule}.deny.write", f"{actor} is denied write to '{npath}'")
    if not path_matches(npath, policy.allow_write):
        return Decision(
            "deny", f"{rule}.default-deny", f"no allow rule matches '{npath}' for {actor}"
        )
    if is_review_gated(npath):
        return Decision(
            "dry_run",
            "review_gated.dry_run",
            "review-gated zone write requires PI disposition -- surface as an attention item",
        )
    return Decision("allow_with_log", f"{rule}.{action}.{_zone(npath)}", log_required=True)


def compose_skill_deny(skill_policy: dict | None) -> list[str]:
    """Compose a loaded skill's ``policy.deny.write`` onto the actor policy."""
    if not skill_policy:
        return []
    deny = (skill_policy.get("deny") or {}).get("write") or []
    return list(deny)


def _zone(path: str) -> str:
    """First path segment, for readable policy_rule ids."""
    seg = path.split("/", 1)[0]
    return seg or "root"
