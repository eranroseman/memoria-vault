#!/usr/bin/env python3
"""Memoria policy MCP -- the runtime write-gate for vault actions.

Profile permissions and lane scopes are not just documentation; they are
enforced here. Every vault action goes through ``check_permission`` and gets
one of four decisions -- ``allow`` / ``allow_with_log`` / ``deny`` / ``dry_run``
-- per the contract in docs/reference/policy-mcp.md.

Design (mirrors .memoria/profiles/memoria-linter/skills/structural-detectors/scripts/detectors.py): a dependency-
light, unit-testable *core* (the decision engine, the glob matcher, the SHA-256
hashing, the audit append) plus a thin MCP-server wrapper. The core runs and
self-tests without the MCP SDK or even PyYAML installed, so the enforcement
logic is verifiable in isolation:

    python policy_mcp.py --vault <path>              # run the MCP server (needs `mcp`)
    python policy_mcp.py --vault <path> --decide '<json-request>'   # one-shot debug

The one-shot ``--decide`` form is the debugging entry point the design calls
for: "an unexpected deny is a Memoria-side question -- check the lane-override
YAML for what the rule says, then the policy MCP's audit log for the actual
decision."

What this server is NOT (per the design doc): not a substitute for the review
gate, not a content checker, not a hidden controller. Every rule lives in a
versioned lane-override file under .memoria/lane-overrides/.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path

from _shared import (
    append_jsonl,
    now_iso,
)
from _shared import (
    resolve_vault as _resolve_vault,
)

try:                                  # PyYAML is a runtime dep (see requirements.txt)
    import yaml  # but the core/self-test must run without it,
except ImportError:                   # so lane-file parsing degrades, decisions don't.
    yaml = None                       # type: ignore[assignment]


# --------------------------------------------------------------------------- #
# Constants -- the vocabulary the design doc pins down
# --------------------------------------------------------------------------- #
# Eight guarded actions. `report` and `read` are non-mutating; the rest change
# the vault and are subject to the review-gated dry_run rule.
ACTIONS = frozenset(
    {"read", "write", "append", "move", "delete", "mkdir", "auto_fix", "report"}
)
MUTATING_ACTIONS = frozenset({"write", "append", "move", "delete", "mkdir", "auto_fix"})

# Review-gated zones are *never auto-written*: an otherwise-allowed mutating
# action here degrades to dry_run so a human approves the write. (policy.md
# "decision protocol" + "two structural rules".)
REVIEW_GATED_PREFIXES = (
    "notes/claims/",
    "notes/hubs/",
)

# Linter auto_fix is class-gated. These two classes may proceed; the other two
# are pinned to dry_run / deny regardless of who asks. (linter.yaml + policy.md)
AUTO_FIX_ALLOWED_CLASSES = frozenset({"safe-and-unambiguous", "authorized-targeted"})
AUTO_FIX_DRY_RUN_CLASSES = frozenset({"schema-content"})
AUTO_FIX_DENY_CLASSES = frozenset({"review-gated-edit"})

# SHA-256 of the empty byte string -- the before_hash of a freshly-created file.
EMPTY_SHA256 = "sha256:" + hashlib.sha256(b"").hexdigest()

AUDIT_RELPATH = "system/logs/audit.jsonl"
LANE_OVERRIDE_RELDIR = ".memoria/lane-overrides"


# --------------------------------------------------------------------------- #
# Path + glob helpers
# --------------------------------------------------------------------------- #
def normalize_path(path: str) -> str:
    """Normalize to a vault-relative POSIX path: forward slashes, no leading
    ``./`` or ``/``, and no ``..`` traversal segments. Matches the request
    contract ("normalized relative to the vault root, forward slashes only").

    Raises ``ValueError`` if the resolved path escapes the vault root (i.e.
    more ``..`` segments than real parents).
    """
    p = (path or "").strip().replace("\\", "/")
    while p.startswith("./"):
        p = p[2:]
    p = p.lstrip("/")
    # Collapse '..' segments so a path like 'a/b/../../c' becomes 'c' and
    # paths that escape the root ('../../etc/passwd') are rejected.
    parts: list[str] = []
    for seg in p.split("/"):
        if seg == "..":
            if parts:
                parts.pop()
            else:
                raise ValueError(f"path escapes vault root: {path!r}")
        elif seg and seg != ".":
            parts.append(seg)
    return "/".join(parts)


def glob_to_regex(pattern: str) -> str:
    """Translate a lane-override glob to an anchored regex with doublestar
    semantics:

    - ``**`` matches any number of path segments (including zero), crossing ``/``
    - ``*``  matches within a single segment (never crosses ``/``)
    - ``?``  matches a single non-``/`` char

    Verified against the real lane patterns: ``40-workbench/*/06-code/**`` matches
    ``40-workbench/project-x/06-code/main.py`` but not ``.../04-drafts/d.md``;
    ``**`` (Socratic deny-all) matches everything; an exact file path like
    ``40-workbench/*/01-map/corpus-map.md`` matches only that file.
    """
    i, n, out = 0, len(pattern), ["^"]
    while i < n:
        c = pattern[i]
        if c == "*":
            if i + 1 < n and pattern[i + 1] == "*":     # '**'
                if i + 2 < n and pattern[i + 2] == "/":  # '**/' -> zero+ segments
                    out.append("(?:.*/)?")
                    i += 3
                else:                                    # trailing '**' -> rest of path
                    out.append(".*")
                    i += 2
            else:                                        # '*' -> within one segment
                out.append("[^/]*")
                i += 1
        elif c == "?":
            out.append("[^/]")
            i += 1
        else:
            out.append(re.escape(c))
            i += 1
    out.append("$")
    return "".join(out)


def path_matches(path: str, patterns: list[str]) -> bool:
    """True if `path` matches any glob in `patterns`."""
    for pat in patterns or []:
        if re.match(glob_to_regex(pat), path):
            return True
    return False


def is_review_gated(path: str) -> bool:
    return path.startswith(REVIEW_GATED_PREFIXES)


def within_scope(path: str, scope: list[str]) -> bool:
    """True if `path` falls under any write_scope prefix (used for mkdir). Scope
    entries are directory prefixes, possibly with a ``*`` segment."""
    for s in scope or []:
        prefix = s if s.endswith("/") else s + "/"
        # allow the prefix itself or anything beneath it, honoring '*' segments
        if re.match(glob_to_regex(prefix + "**"), path) or re.match(
            glob_to_regex(prefix.rstrip("/")), path.rstrip("/")
        ):
            return True
    return False


# --------------------------------------------------------------------------- #
# Lane policy model
# --------------------------------------------------------------------------- #
@dataclass
class LanePolicy:
    """Parsed lane-override (.memoria/lane-overrides/<lane>.yaml)."""
    profile: str
    allow_skills: list[str] = field(default_factory=list)
    allow_write: list[str] = field(default_factory=list)
    allow_read: list[str] = field(default_factory=list)
    allow_auto_fix_classes: list[str] = field(default_factory=list)
    deny_skills: list[str] = field(default_factory=list)
    deny_write: list[str] = field(default_factory=list)
    deny_read: list[str] = field(default_factory=list)
    deny_auto_fix_classes: list[str] = field(default_factory=list)
    require: list[str] = field(default_factory=list)
    invocation: str = "dispatched"
    external_api_policy: str = "blocked"
    write_scope: list[str] = field(default_factory=list)

    @property
    def short(self) -> str:
        """Capitalized short name for policy_rule ids: memoria-coder -> Coder."""
        name = self.profile[len("memoria-"):] if self.profile.startswith("memoria-") else self.profile
        return name[:1].upper() + name[1:]


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
    """Read and parse the lane-override for `profile` (memoria-coder -> coder.yaml)."""
    if yaml is None:
        raise RuntimeError(
            "PyYAML not installed -- run `pip install -r .memoria/mcp/requirements.txt`."
        )
    lane = profile[len("memoria-"):] if profile.startswith("memoria-") else profile
    path = vault / LANE_OVERRIDE_RELDIR / f"{lane}.yaml"
    if not path.is_file():
        raise FileNotFoundError(f"no lane-override for profile '{profile}' at {path}")
    doc = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    return parse_lane(doc)


# --------------------------------------------------------------------------- #
# Decision engine -- the heart. Pure function; no I/O.
# --------------------------------------------------------------------------- #
@dataclass
class Decision:
    decision: str                       # allow | allow_with_log | deny | dry_run
    policy_rule: str                    # e.g. "Coder.write.40-workbench" | "review_gated.dry_run"
    message: str = ""
    log_required: bool = False

    def response(self) -> dict:
        """Shape the MCP JSON response per policy.md."""
        out: dict = {"decision": self.decision, "policy_rule": self.policy_rule}
        if self.decision in ("allow", "allow_with_log"):
            out["log_required"] = self.log_required
        if self.message:
            out["message"] = self.message
        return out


def decide(
    profile: str,
    action: str,
    path: str,
    lane: LanePolicy,
    flags: dict | None = None,
    skill_deny_write: list[str] | None = None,
) -> Decision:
    """Return the policy Decision for one request. Pure: no file I/O, no logging.

    Precedence (faithful to policy.md):
      1. Invalid action            -> deny.
      2. Skill-conditional deny     -> deny (additive narrowing; mutating actions).
      3. report                     -> allow within lane.
      4. read                       -> default-allow; allow_with_log in review-gated
                                       zones (canonical content); explicit deny.read wins.
      5. auto_fix                   -> Linter class-gating (allow / dry_run / deny).
      6. delete                     -> deny unless explicit_authorization (then
                                       allow_with_log); review-gated -> dry_run.
      7. mkdir                      -> allow within write_scope, else deny.
      8. write / append / move      -> deny.write wins; else allow.write -> base allow;
                                       else default-deny. An otherwise-allowed mutating
                                       action in a review-gated zone degrades to dry_run.
    """
    flags = flags or {}
    npath = normalize_path(path)
    rule = lane.short
    require_log = "audit_log" in lane.require   # all Memoria lanes set this

    if action not in ACTIONS:
        return Decision("deny", f"{rule}.invalid-action", f"unknown action '{action}'")

    # (2) Skill-conditional deny -- a loaded skill can only *narrow* the lane.
    # The narrowing is one-way for the session; a deny here cannot be loosened.
    if skill_deny_write and action in MUTATING_ACTIONS and path_matches(npath, skill_deny_write):
        return Decision("deny", "skill.deny.write",
                        "blocked by the loaded skill's policy.deny (one-way narrowing)")

    # (3) report -- always allowed within the worker's lane.
    if action == "report":
        return Decision("allow", f"{rule}.report", log_required=require_log)

    # (4) read -- broad by design (most profiles are read_only_mode + narrow writes).
    if action == "read":
        if path_matches(npath, lane.deny_read):
            return Decision("deny", f"{rule}.deny.read", "read denied by lane policy")
        if is_review_gated(npath):
            return Decision("allow_with_log", "read.review-gated",
                            "read of canonical/review-gated content", log_required=True)
        return Decision("allow", f"{rule}.read", log_required=require_log)

    # (5) auto_fix -- Linter-only, class-gated. flags.class is required.
    if action == "auto_fix":
        cls = flags.get("class")
        if not cls:
            return Decision("deny", f"{rule}.auto_fix.no-class",
                            "auto_fix requires flags.class")
        if cls in AUTO_FIX_DENY_CLASSES:                 # review-gated-edit: always deny
            return Decision("deny", f"{rule}.auto_fix.{cls}",
                            f"auto_fix class '{cls}' is always denied")
        if cls in AUTO_FIX_DRY_RUN_CLASSES:              # schema-content: always dry_run
            return Decision("dry_run", f"{rule}.auto_fix.{cls}",
                            f"auto_fix class '{cls}' degrades to dry_run -- needs schema-migrate")
        if cls in lane.deny_auto_fix_classes:            # lane-specific class deny
            return Decision("deny", f"{rule}.auto_fix.{cls}",
                            f"auto_fix class '{cls}' denied by lane policy")
        if cls in AUTO_FIX_ALLOWED_CLASSES and cls in lane.allow_auto_fix_classes:
            if not path_matches(npath, lane.allow_write):
                return Decision("deny", f"{rule}.auto_fix.out-of-scope",
                                f"auto_fix path '{npath}' outside the lane's write scope")
            if is_review_gated(npath):
                return Decision("dry_run", "review_gated.dry_run",
                                "review-gated zone -- surface as board comment")
            return Decision("allow_with_log", f"{rule}.auto_fix.{cls}", log_required=True)
        return Decision("deny", f"{rule}.auto_fix.class-not-allowed",
                        f"auto_fix class '{cls}' not permitted for {profile}")

    # (6) delete -- destructive: deny unless explicitly authorized, and only within
    # the lane's write scope. Review-gated deletes degrade to dry_run.
    if action == "delete":
        if not flags.get("explicit_authorization"):
            return Decision("deny", f"{rule}.delete.default-deny",
                            "delete requires flags.explicit_authorization")
        if not path_matches(npath, lane.allow_write):
            return Decision("deny", f"{rule}.delete.out-of-scope",
                            f"delete path '{npath}' outside the lane's write scope")
        if is_review_gated(npath):
            return Decision("dry_run", "review_gated.dry_run",
                            "review-gated zone -- delete must be human-approved")
        return Decision("allow_with_log", f"{rule}.delete", log_required=True)

    # (7) mkdir -- allowed within the routing write_scope.
    if action == "mkdir":
        if not within_scope(npath, lane.write_scope):
            return Decision("deny", f"{rule}.mkdir.out-of-scope",
                            f"mkdir '{npath}' outside routing.write_scope")
        if is_review_gated(npath):
            return Decision("dry_run", "review_gated.dry_run", "review-gated zone")
        return Decision("allow", f"{rule}.mkdir", log_required=require_log)

    # (8) write / append / move -- the dominant cases.
    if path_matches(npath, lane.deny_write):
        return Decision("deny", f"{rule}.deny.write",
                        f"{profile} is denied write to '{npath}'")
    if not path_matches(npath, lane.allow_write):
        # Default-deny: no rule matched at all.
        return Decision("deny", f"{rule}.default-deny",
                        f"no allow rule matches '{npath}' for {profile}")
    # Base decision is allow. Apply the structural review-gated override for
    # mutating actions ("would otherwise allow it" -> dry_run).
    if is_review_gated(npath):
        return Decision("dry_run", "review_gated.dry_run",
                        "review-gated zone write requires approval -- surface as board comment")
    # Operationally-significant allows are logged unconditionally.
    if flags.get("explicit_authorization") or action == "move":
        return Decision("allow_with_log", f"{rule}.{action}.{_zone(npath)}", log_required=True)
    return Decision("allow", f"{rule}.{action}.{_zone(npath)}", log_required=require_log)


def _zone(path: str) -> str:
    """First path segment, for a readable policy_rule id (e.g. '40-workbench')."""
    seg = path.split("/", 1)[0]
    return seg or "root"


def compose_skill_deny(lane: LanePolicy, skill_policy: dict | None) -> list[str]:
    """Compose a loaded skill's ``policy.deny.write`` onto the lane.

    Deny composition is additive: the skill's write-deny patterns are added to
    the session's effective deny set (the narrower set wins). A skill cannot
    declare ``policy.allow`` -- it may only narrow. (policy.md "composition
    semantics".) Returns the extra deny-write patterns the skill contributes.
    """
    if not skill_policy:
        return []
    deny = (skill_policy.get("deny") or {}).get("write") or []
    return list(deny)


# --------------------------------------------------------------------------- #
# SHA-256 + audit log -- the only vault state the policy MCP touches.
# --------------------------------------------------------------------------- #
def sha256_file(path: Path) -> str:
    """``sha256:<64-hex>`` of the file's bytes. A missing file hashes as the
    empty byte string (the before_hash of a create), never null. Raises on a
    read error so the caller can fail the decision closed."""
    if not path.exists():
        return EMPTY_SHA256
    return "sha256:" + hashlib.sha256(path.read_bytes()).hexdigest()


# now_iso: imported from _shared (re-exported for policy_hook compatibility)


def append_audit(vault: Path, entry: dict) -> None:
    """Append one JSON object (one line) to system/logs/audit.jsonl. The
    append-only JSONL format survives crashes and is grep-friendly."""
    append_jsonl(vault / AUDIT_RELPATH, [entry])


# --------------------------------------------------------------------------- #
# Engine: ties lane-loading + decision + hashing + audit together.
# --------------------------------------------------------------------------- #
class PolicyEngine:
    """Stateful wrapper around the pure decision core: loads lanes (cached),
    tracks per-session loaded-skill policy, hashes files, writes the audit log."""

    def __init__(self, vault: Path):
        self.vault = vault
        self._lane_cache: dict[str, LanePolicy] = {}
        self._session_skill_deny: dict[str, list[str]] = {}   # task_id -> extra deny-write

    def lane(self, profile: str) -> LanePolicy:
        if profile not in self._lane_cache:
            self._lane_cache[profile] = load_lane(self.vault, profile)
        return self._lane_cache[profile]

    def set_session_skill(self, task_id: str, skill_policy: dict | None) -> None:
        """Register the policy.deny block of a skill loaded for this session.

        NOTE (integration gap, see open questions): the design says the MCP
        "looks up which skill is loaded for the session" via task_id, but does
        not specify *how* Hermes signals a skill load. This method is the
        injection point; the composition + one-way-narrowing logic it enables is
        implemented and tested."""
        lane_stub = LanePolicy(profile="")
        extra = compose_skill_deny(lane_stub, skill_policy)
        if extra:
            self._session_skill_deny[task_id] = extra
        else:
            self._session_skill_deny.pop(task_id, None)

    def clear_session_skill(self, task_id: str) -> None:
        self._session_skill_deny.pop(task_id, None)

    def _audit_traversal(self, profile: str, action: str, path: str, task_id: str, message: str) -> None:
        """Log a path-traversal denial. The raw `path` is recorded because
        normalization failed; this is the one request class most worth auditing."""
        append_audit(self.vault, {
            "timestamp": now_iso(),
            "profile": profile,
            "action": action,
            "path": path,            # raw -- normalization failed
            "task_id": task_id,
            "decision": "deny",
            "policy_rule": "path.traversal",
            "message": message,
        })

    def check(
        self,
        profile: str,
        action: str,
        path: str,
        task_id: str,
        reason: str = "",
        flags: dict | None = None,
    ) -> dict:
        """The MCP entry point: decide, hash (for mutating allows), log, respond.

        `task_id` is required -- delegated children share summaries, not live
        state, so identity must travel with every request."""
        if not task_id:
            return {"decision": "deny", "policy_rule": "request.no-task-id",
                    "message": "task_id is required on every request"}
        try:
            npath = normalize_path(path)
        except ValueError as exc:
            # A traversal attempt is the request most worth logging. Audit it with
            # the raw path (normalization failed) before returning the deny.
            self._audit_traversal(profile, action, path, task_id, str(exc))
            return {"decision": "deny", "policy_rule": "path.traversal",
                    "message": str(exc)}
        try:
            lane = self.lane(profile)
        except (FileNotFoundError, RuntimeError) as exc:
            return {"decision": "deny", "policy_rule": "lane.load-error", "message": str(exc)}
        skill_deny = self._session_skill_deny.get(task_id)
        dec = decide(profile, action, npath, lane, flags=flags, skill_deny_write=skill_deny)

        # Hash failures are deny (the hash is part of the contract -- no hash, no allow).
        before_hash = None
        if dec.decision in ("allow", "allow_with_log") and action in MUTATING_ACTIONS:
            try:
                before_hash = sha256_file(self.vault / npath)
            except OSError as exc:
                return {"decision": "deny", "policy_rule": "hash.read-error",
                        "message": f"cannot hash '{npath}': {exc}"}

        # Every decision is appended to the audit trail (all lanes require audit_log).
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
                entry["after_hash"] = None   # completed by complete_write() post-write
            append_audit(self.vault, entry)

        resp = dec.response()
        if before_hash is not None:
            resp["before_hash"] = before_hash
        return resp

    def complete_write(self, profile: str, action: str, path: str, task_id: str,
                       before_hash: str) -> dict:
        """Record the post-write ``after_hash`` for reversibility.

        ``check_permission`` is advisory (it returns a decision before the write
        happens), so the file's after-state is captured here once the worker's
        write completes. before_hash + the prior entry's after_hash pin the prior
        state, making every write reversible. (See open questions: whether the
        policy MCP should instead *front* the write so this is atomic.)"""
        try:
            npath = normalize_path(path)
        except ValueError as exc:
            self._audit_traversal(profile, action, path, task_id, str(exc))
            return {"ok": False, "message": str(exc)}
        try:
            after_hash = sha256_file(self.vault / npath)
        except OSError as exc:
            return {"ok": False, "message": f"cannot hash '{npath}': {exc}"}
        append_audit(self.vault, {
            "timestamp": now_iso(),
            "profile": profile,
            "action": action,
            "path": npath,
            "task_id": task_id,
            "decision": "write_complete",
            "before_hash": before_hash,
            "after_hash": after_hash,
        })
        return {"ok": True, "after_hash": after_hash}


# --------------------------------------------------------------------------- #
# MCP server wrapper (thin; optional dependency)
# --------------------------------------------------------------------------- #
def build_server(vault: Path):
    """Wrap the engine as an MCP server. Imported lazily so the core/self-test
    don't require the `mcp` package."""
    from mcp.server.fastmcp import FastMCP  # type: ignore

    engine = PolicyEngine(vault)
    server = FastMCP("memoria-policy")

    @server.tool()
    def check_permission(profile: str, action: str, path: str, task_id: str,
                         reason: str = "", flags: dict | None = None) -> dict:
        """Authorize a vault action. Returns one of allow / allow_with_log /
        deny / dry_run with the matched policy_rule."""
        return engine.check(profile, action, path, task_id, reason, flags)

    @server.tool()
    def complete_write(profile: str, action: str, path: str, task_id: str,
                       before_hash: str) -> dict:
        """Record after_hash once a write completes (reversibility/tamper trail)."""
        return engine.complete_write(profile, action, path, task_id, before_hash)

    @server.tool()
    def set_session_skill(task_id: str, skill_policy: dict | None = None) -> dict:
        """Register a loaded skill's policy block for one-way session narrowing."""
        engine.set_session_skill(task_id, skill_policy)
        return {"ok": True}

    @server.tool()
    def clear_session_skill(task_id: str) -> dict:
        """Drop a session's skill narrowing (returns to lane-only policy)."""
        engine.clear_session_skill(task_id)
        return {"ok": True}

    return server


def resolve_vault(arg: str | None) -> Path:
    """--vault arg, else MEMORIA_VAULT_PATH env. The installer substitutes the
    real path into mcp.json's {{VAULT_PATH}} when wiring this server."""
    return _resolve_vault(arg, "MEMORIA_VAULT_PATH")


# --------------------------------------------------------------------------- #
# Self-test -- synthetic lanes + a throwaway vault; asserts each rule fires.
# --------------------------------------------------------------------------- #
# --------------------------------------------------------------------------- #
def main() -> None:
    ap = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--vault", help="vault root (or set MEMORIA_VAULT_PATH)")
    ap.add_argument("--decide", metavar="JSON",
                    help='one-shot: decide a single request, e.g. '
                         '\'{"profile":"memoria-coder","action":"write",'
                         '"path":"40-workbench/x/06-code/m.py","task_id":"T1"}\'')
    args = ap.parse_args()

    vault = resolve_vault(args.vault)

    if args.decide:
        req = json.loads(args.decide)
        engine = PolicyEngine(vault)
        print(json.dumps(engine.check(
            req["profile"], req["action"], req["path"], req.get("task_id", ""),
            req.get("reason", ""), req.get("flags")), indent=2))
        sys.exit(0)

    # Default: run the MCP server over stdio.
    build_server(vault).run()


if __name__ == "__main__":
    main()
