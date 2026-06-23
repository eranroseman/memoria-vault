"""Stateful policy engine: lane loading, hashing, audit, and loudness checks."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from memoria.runtime.jsonl import iter_jsonl
from memoria.runtime.time import now_iso
from memoria.runtime.vaultio import read_frontmatter

from .audit import AUDIT_RELPATH, append_audit, sha256_file
from .decision import compose_skill_deny, decide, is_review_gated
from .lanes import load_lane
from .model import LanePolicy
from .paths import MUTATING_ACTIONS, normalize_path


class PolicyEngine:
    """Stateful wrapper around the pure decision core."""

    def __init__(self, vault: Path):
        self.vault = vault
        self._lane_cache: dict[str, LanePolicy] = {}
        self._session_skill_deny: dict[str, list[str]] = {}

    def lane(self, profile: str) -> LanePolicy:
        if profile not in self._lane_cache:
            self._lane_cache[profile] = load_lane(self.vault, profile)
        return self._lane_cache[profile]

    def set_session_skill(self, task_id: str, skill_policy: dict | None) -> None:
        """Register one loaded skill's additive write-deny policy for a session."""
        lane_stub = LanePolicy(profile="")
        extra = compose_skill_deny(lane_stub, skill_policy)
        if extra:
            self._session_skill_deny[task_id] = extra
        else:
            self._session_skill_deny.pop(task_id, None)

    def clear_session_skill(self, task_id: str) -> None:
        self._session_skill_deny.pop(task_id, None)

    def _audit_traversal(
        self, profile: str, action: str, path: str, task_id: str, message: str
    ) -> None:
        """Log a path traversal denial with the raw path that failed normalization."""
        append_audit(
            self.vault,
            {
                "timestamp": now_iso(),
                "profile": profile,
                "action": action,
                "path": path,
                "task_id": task_id,
                "decision": "deny",
                "policy_rule": "path.traversal",
                "message": message,
            },
        )

    def check(
        self,
        profile: str,
        action: str,
        path: str,
        task_id: str,
        reason: str = "",
        flags: dict | None = None,
    ) -> dict[str, Any]:
        """Decide, hash mutating allows, append audit rows, and shape the response."""
        if not task_id:
            return {
                "decision": "deny",
                "policy_rule": "request.no-task-id",
                "message": "task_id is required on every request",
            }
        try:
            npath = normalize_path(path)
        except ValueError as exc:
            self._audit_traversal(profile, action, path, task_id, str(exc))
            return {"decision": "deny", "policy_rule": "path.traversal", "message": str(exc)}

        if action in MUTATING_ACTIONS and is_review_gated(npath):
            blockers = _open_blockers(self.vault)
            if blockers:
                message = _blocker_message(blockers)
                append_audit(
                    self.vault,
                    {
                        "timestamp": now_iso(),
                        "profile": profile,
                        "action": action,
                        "path": npath,
                        "task_id": task_id,
                        "decision": "deny",
                        "policy_rule": "loudness.block.active",
                        "message": message,
                    },
                )
                return {
                    "decision": "deny",
                    "policy_rule": "loudness.block.active",
                    "message": message,
                    "blockers": blockers,
                }

        try:
            lane = self.lane(profile)
        except (FileNotFoundError, RuntimeError) as exc:
            return {"decision": "deny", "policy_rule": "lane.load-error", "message": str(exc)}

        skill_deny = self._session_skill_deny.get(task_id)
        dec = decide(profile, action, npath, lane, flags=flags, skill_deny_write=skill_deny)

        before_hash = None
        if dec.decision in ("allow", "allow_with_log") and action in MUTATING_ACTIONS:
            try:
                before_hash = sha256_file(self.vault / npath)
            except OSError as exc:
                return {
                    "decision": "deny",
                    "policy_rule": "hash.read-error",
                    "message": f"cannot hash '{npath}': {exc}",
                }

        if dec.log_required or dec.decision in ("allow_with_log", "deny", "dry_run"):
            entry = {
                "timestamp": now_iso(),
                "profile": profile,
                "action": action,
                "path": npath,
                "task_id": task_id,
                "decision": dec.decision,
                "policy_rule": dec.policy_rule,
            }
            if reason:
                entry["reason"] = reason
            if before_hash is not None:
                entry["before_hash"] = before_hash
                entry["after_hash"] = None
            append_audit(self.vault, entry)

        resp = dec.response()
        if before_hash is not None:
            resp["before_hash"] = before_hash
        return resp

    def complete_write(
        self,
        profile: str,
        action: str,
        path: str,
        task_id: str,
        before_hash: str,
    ) -> dict[str, Any]:
        """Record the post-write ``after_hash`` for reversibility."""
        try:
            npath = normalize_path(path)
        except ValueError as exc:
            self._audit_traversal(profile, action, path, task_id, str(exc))
            return {"ok": False, "message": str(exc)}
        try:
            after_hash = sha256_file(self.vault / npath)
        except OSError as exc:
            return {"ok": False, "message": f"cannot hash '{npath}': {exc}"}
        entry = {
            "timestamp": now_iso(),
            "profile": profile,
            "action": action,
            "path": npath,
            "task_id": task_id,
            "decision": "write_complete",
            "before_hash": before_hash,
            "after_hash": after_hash,
        }
        expected = None
        for audit_entry in iter_jsonl(self.vault / AUDIT_RELPATH):
            if (
                audit_entry.get("path") == npath
                and audit_entry.get("task_id") == task_id
                and audit_entry.get("decision") in ("allow", "allow_with_log")
                and audit_entry.get("before_hash")
            ):
                expected = audit_entry["before_hash"]
        if expected is not None and expected != before_hash:
            entry["hash_mismatch"] = True
            entry["expected_before_hash"] = expected
        append_audit(self.vault, entry)
        return {"ok": True, "after_hash": after_hash}


def _open_blockers(vault: Path) -> list[dict[str, str]]:
    blockers: list[dict[str, str]] = []
    for path in sorted((vault / "inbox").glob("*.md")):
        frontmatter = read_frontmatter(path)
        if (
            str(frontmatter.get("loudness") or "").lower() == "block"
            and str(frontmatter.get("lifecycle") or "").lower() == "proposed"
        ):
            blockers.append(
                {
                    "path": str(path.relative_to(vault)).replace("\\", "/"),
                    "title": str(frontmatter.get("title") or path.stem),
                    "type": str(frontmatter.get("type") or "card"),
                }
            )
    return blockers


def _blocker_message(blockers: list[dict[str, str]]) -> str:
    if not blockers:
        return ""
    names = ", ".join(f"{blocker['path']} ({blocker['title']})" for blocker in blockers[:3])
    more = "" if len(blockers) <= 3 else f"; +{len(blockers) - 3} more"
    return (
        "open block-loudness card(s) require PI acknowledgement before "
        f"dispatch/promotion: {names}{more}"
    )
