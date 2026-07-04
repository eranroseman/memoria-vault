"""Stateful policy engine: actor-policy loading, hashing, audit, and loudness checks."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from memoria_vault.runtime.jsonl import iter_jsonl
from memoria_vault.runtime.subsystems.lib import loudness
from memoria_vault.runtime.time import now_iso

from .audit import AUDIT_RELPATH, append_audit, sha256_file
from .decision import compose_skill_deny, decide, is_review_gated
from .model import ActorPolicy
from .paths import MUTATING_ACTIONS, normalize_path
from .workspace import load_actor_policy


class PolicyEngine:
    """Stateful wrapper around the pure decision core."""

    def __init__(self, workspace: Path):
        self.workspace = workspace
        self._policy_cache: dict[str, ActorPolicy] = {}
        self._session_skill_deny: dict[str, list[str]] = {}

    def policy(self, actor: str) -> ActorPolicy:
        if actor not in self._policy_cache:
            self._policy_cache[actor] = load_actor_policy(self.workspace, actor)
        return self._policy_cache[actor]

    def set_session_skill(self, request_id: str, skill_policy: dict | None) -> None:
        """Register one loaded skill's additive write-deny policy for a session."""
        policy_stub = ActorPolicy(actor="")
        extra = compose_skill_deny(policy_stub, skill_policy)
        if extra:
            self._session_skill_deny[request_id] = extra
        else:
            self._session_skill_deny.pop(request_id, None)

    def clear_session_skill(self, request_id: str) -> None:
        self._session_skill_deny.pop(request_id, None)

    def _audit_traversal(
        self, actor: str, action: str, path: str, request_id: str, message: str
    ) -> None:
        """Log a path traversal denial with the raw path that failed normalization."""
        append_audit(
            self.workspace,
            {
                "timestamp": now_iso(),
                "actor": actor,
                "action": action,
                "path": path,
                "request_id": request_id,
                "decision": "deny",
                "policy_rule": "path.traversal",
                "message": message,
            },
        )

    def check(
        self,
        actor: str,
        action: str,
        path: str,
        request_id: str,
        reason: str = "",
        flags: dict | None = None,
    ) -> dict[str, Any]:
        """Decide, hash mutating allows, append audit rows, and shape the response."""
        if not request_id:
            return {
                "decision": "deny",
                "policy_rule": "request.no-request-id",
                "message": "request_id is required on every request",
            }
        try:
            npath = normalize_path(path)
        except ValueError as exc:
            self._audit_traversal(actor, action, path, request_id, str(exc))
            return {"decision": "deny", "policy_rule": "path.traversal", "message": str(exc)}

        if action in MUTATING_ACTIONS and is_review_gated(npath):
            blockers = loudness.open_blockers(self.workspace)
            if blockers:
                message = loudness.blocker_message(blockers)
                append_audit(
                    self.workspace,
                    {
                        "timestamp": now_iso(),
                        "actor": actor,
                        "action": action,
                        "path": npath,
                        "request_id": request_id,
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
            policy = self.policy(actor)
        except (FileNotFoundError, KeyError, RuntimeError, ValueError) as exc:
            return {"decision": "deny", "policy_rule": "policy.load-error", "message": str(exc)}

        skill_deny = self._session_skill_deny.get(request_id)
        dec = decide(actor, action, npath, policy, flags=flags, skill_deny_write=skill_deny)

        before_hash = None
        if dec.decision in ("allow", "allow_with_log") and action in MUTATING_ACTIONS:
            try:
                before_hash = sha256_file(self.workspace / npath)
            except OSError as exc:
                return {
                    "decision": "deny",
                    "policy_rule": "hash.read-error",
                    "message": f"cannot hash '{npath}': {exc}",
                }

        if dec.log_required or dec.decision in ("allow_with_log", "deny", "dry_run"):
            entry = {
                "timestamp": now_iso(),
                "actor": actor,
                "action": action,
                "path": npath,
                "request_id": request_id,
                "decision": dec.decision,
                "policy_rule": dec.policy_rule,
            }
            if reason:
                entry["reason"] = reason
            if before_hash is not None:
                entry["before_hash"] = before_hash
                entry["after_hash"] = None
            append_audit(self.workspace, entry)

        resp = dec.response()
        if before_hash is not None:
            resp["before_hash"] = before_hash
        return resp

    def complete_write(
        self,
        actor: str,
        action: str,
        path: str,
        request_id: str,
        before_hash: str,
    ) -> dict[str, Any]:
        """Record the post-write ``after_hash`` for reversibility."""
        try:
            npath = normalize_path(path)
        except ValueError as exc:
            self._audit_traversal(actor, action, path, request_id, str(exc))
            return {"ok": False, "message": str(exc)}
        try:
            after_hash = sha256_file(self.workspace / npath)
        except OSError as exc:
            return {"ok": False, "message": f"cannot hash '{npath}': {exc}"}
        entry = {
            "timestamp": now_iso(),
            "actor": actor,
            "action": action,
            "path": npath,
            "request_id": request_id,
            "decision": "write_complete",
            "before_hash": before_hash,
            "after_hash": after_hash,
        }
        expected = None
        for audit_entry in iter_jsonl(self.workspace / AUDIT_RELPATH):
            if (
                audit_entry.get("path") == npath
                and audit_entry.get("request_id") == request_id
                and audit_entry.get("decision") in ("allow", "allow_with_log")
                and audit_entry.get("before_hash")
            ):
                expected = audit_entry["before_hash"]
        if expected is not None and expected != before_hash:
            entry["hash_mismatch"] = True
            entry["expected_before_hash"] = expected
        append_audit(self.workspace, entry)
        return {"ok": True, "after_hash": after_hash}
