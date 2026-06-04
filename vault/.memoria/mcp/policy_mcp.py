#!/usr/bin/env python3
"""Memoria policy MCP -- the runtime write-gate for vault actions.

Profile permissions and lane scopes are not just documentation; they are
enforced here. Every vault action goes through ``check_permission`` and gets
one of four decisions -- ``allow`` / ``allow_with_log`` / ``deny`` / ``dry_run``
-- per the contract in docs/reference/policy-mcp.md.

Design (mirrors .memoria/profiles/memoria-linter/detectors.py): a dependency-
light, unit-testable *core* (the decision engine, the glob matcher, the SHA-256
hashing, the audit append) plus a thin MCP-server wrapper. The core runs and
self-tests without the MCP SDK or even PyYAML installed, so the enforcement
logic is verifiable in isolation:

    python policy_mcp.py --self-test                 # synthetic-fixture unit tests
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
import os
import re
import sys
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path

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
    "30-synthesis/01-claims/",
    "30-synthesis/02-reference/",
    "30-synthesis/03-moc/",
    "50-deliverables/",
)

# Linter auto_fix is class-gated. These two classes may proceed; the other two
# are pinned to dry_run / deny regardless of who asks. (linter.yaml + policy.md)
AUTO_FIX_ALLOWED_CLASSES = frozenset({"safe-and-unambiguous", "authorized-targeted"})
AUTO_FIX_DRY_RUN_CLASSES = frozenset({"schema-content"})
AUTO_FIX_DENY_CLASSES = frozenset({"review-gated-edit"})

# SHA-256 of the empty byte string -- the before_hash of a freshly-created file.
EMPTY_SHA256 = "sha256:" + hashlib.sha256(b"").hexdigest()

AUDIT_RELPATH = "99-system/logs/audit.jsonl"
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


def now_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def append_audit(vault: Path, entry: dict) -> None:
    """Append one JSON object (one line) to 99-system/logs/audit.jsonl. The
    append-only JSONL format survives crashes and is grep-friendly."""
    audit = vault / AUDIT_RELPATH
    audit.parent.mkdir(parents=True, exist_ok=True)
    with audit.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(entry, ensure_ascii=False) + "\n")


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
    raw = arg or os.environ.get("MEMORIA_VAULT_PATH")
    if not raw:
        sys.exit("no vault path: pass --vault <path> or set MEMORIA_VAULT_PATH")
    vault = Path(raw).expanduser().resolve()
    if not vault.is_dir():
        sys.exit(f"not a directory: {vault}")
    return vault


# --------------------------------------------------------------------------- #
# Self-test -- synthetic lanes + a throwaway vault; asserts each rule fires.
# --------------------------------------------------------------------------- #
def self_test() -> int:
    import tempfile

    failures = 0

    def check(name: str, cond: bool) -> None:
        nonlocal failures
        failures += not cond
        print(f"  {'PASS' if cond else 'FAIL'}  {name}")

    # ---- glob matcher ------------------------------------------------------ #
    check("glob: '**' matches anything",
          path_matches("a/b/c.md", ["**"]))
    check("glob: '*' stays within a segment",
          not path_matches("a/b.md", ["*"]) and path_matches("a.md", ["*"]))
    check("glob: code scope matches nested file",
          path_matches("40-workbench/project-x/06-code/main.py", ["40-workbench/*/06-code/**"]))
    check("glob: code scope rejects sibling folder",
          not path_matches("40-workbench/project-x/04-drafts/d.md", ["40-workbench/*/06-code/**"]))
    check("glob: exact-file pattern matches only that file",
          path_matches("40-workbench/p/01-map/corpus-map.md", ["40-workbench/*/01-map/corpus-map.md"])
          and not path_matches("40-workbench/p/01-map/other.md", ["40-workbench/*/01-map/corpus-map.md"]))
    check("glob: '**/' matches zero middle segments",
          path_matches("a/b.md", ["a/**/b.md"]) and path_matches("a/x/y/b.md", ["a/**/b.md"]))

    # ---- normalize_path: collapse '..' and reject traversal escapes -------- #
    check("normalize_path: collapse interior '..'",
          normalize_path("a/b/../../c") == "c")
    check("normalize_path: collapse multiple '..'",
          normalize_path("40-workbench/x/../../30-synthesis/c.md") == "30-synthesis/c.md")
    check("normalize_path: strip leading './'",
          normalize_path("./a/b.md") == "a/b.md")
    check("normalize_path: strip leading '/'",
          normalize_path("/a/b.md") == "a/b.md")
    try:
        normalize_path("../../etc/passwd")
        check("normalize_path: reject escape above root", False)
    except ValueError:
        check("normalize_path: reject escape above root", True)
    try:
        normalize_path("a/../../../etc/passwd")
        check("normalize_path: reject deep escape above root", False)
    except ValueError:
        check("normalize_path: reject deep escape above root", True)

    # ---- engine: traversal attempt -> deny --------------------------------- #
    with tempfile.TemporaryDirectory() as td_trav:
        trav_vault = Path(td_trav)
        eng_trav = PolicyEngine(trav_vault)
        trav_resp = eng_trav.check("memoria-coder", "write", "../../etc/passwd", "T-TRAV")
        check("engine denies path-traversal escape",
              trav_resp["decision"] == "deny" and trav_resp["policy_rule"] == "path.traversal")

    # ---- lanes (built directly so the self-test needs no PyYAML) ----------- #
    coder = LanePolicy(
        profile="memoria-coder",
        allow_write=["40-workbench/*/06-code/**"],
        deny_write=["10-inbox/**", "20-sources/**", "30-synthesis/**",
                    "40-workbench/*/04-drafts/**", "50-deliverables/**"],
        require=["audit_log"], write_scope=["40-workbench/*/06-code/"],
    )
    writer = LanePolicy(
        profile="memoria-writer",
        allow_write=["10-inbox/02-answers/**", "40-workbench/*/04-drafts/**",
                     "40-workbench/*/02-framing/**", "30-synthesis/02-reference/**"],
        deny_write=["20-sources/**", "30-synthesis/01-claims/**", "50-deliverables/**"],
        require=["audit_log"],
    )
    socratic = LanePolicy(profile="memoria-socratic", allow_write=[],
                          deny_write=["**"], require=["audit_log"])
    linter = LanePolicy(
        profile="memoria-linter",
        allow_write=["99-system/logs/**"],
        allow_auto_fix_classes=["safe-and-unambiguous", "authorized-targeted"],
        deny_write=["10-inbox/**", "20-sources/**", "30-synthesis/**",
                    "40-workbench/**", "50-deliverables/**"],
        deny_auto_fix_classes=["schema-content", "review-gated-edit"],
        require=["audit_log"], write_scope=["99-system/logs/"],
    )
    # The remaining three lanes mirror their real .memoria/lane-overrides/*.yaml
    # so the gate contract for all seven profiles is unit-covered (closes the
    # hermes-cli protocol's X1 / M4 / V-series write-walls — L2 gate testing).
    librarian = LanePolicy(
        profile="memoria-librarian",
        allow_write=["10-inbox/01-fleeting/**", "10-inbox/03-candidates/**",
                     "20-sources/**"],
        deny_write=["30-synthesis/**", "40-workbench/**", "50-deliverables/**"],
        require=["audit_log"],
        write_scope=["10-inbox/01-fleeting/", "10-inbox/03-candidates/", "20-sources/"],
    )
    mapper = LanePolicy(
        profile="memoria-mapper",
        allow_write=["40-workbench/*/01-map/corpus-map.md",
                     "40-workbench/*/01-map/gap-report.md",
                     "40-workbench/*/01-map/cluster-maps/**"],
        deny_write=["10-inbox/**", "20-sources/**", "30-synthesis/**",
                    "50-deliverables/**"],
        require=["audit_log"], write_scope=["40-workbench/*/01-map/"],
    )
    verifier = LanePolicy(
        profile="memoria-verifier",
        allow_write=["40-workbench/*/05-verification/**", "10-inbox/03-candidates/**"],
        deny_write=["20-sources/**", "30-synthesis/**",
                    "40-workbench/*/04-drafts/**", "50-deliverables/**"],
        require=["audit_log"],
        write_scope=["40-workbench/*/05-verification/", "10-inbox/03-candidates/"],
    )

    d = lambda p, a, pa, fl=None, sk=None: decide(p.profile, a, pa, p, flags=fl, skill_deny_write=sk).decision

    # ---- write decisions --------------------------------------------------- #
    check("Coder write to own code scope -> allow",
          d(coder, "write", "40-workbench/x/06-code/main.py") == "allow")
    check("Coder write to drafts -> deny (lane deny)",
          d(coder, "write", "40-workbench/x/04-drafts/d.md") == "deny")
    check("Coder write to unmapped path -> deny (default-deny)",
          d(coder, "write", "99-nowhere/x.md") == "deny")
    check("Writer write to answers -> allow",
          d(writer, "write", "10-inbox/02-answers/a.md") == "allow")
    check("Writer write to review-gated reference -> dry_run (degrade)",
          d(writer, "write", "30-synthesis/02-reference/r.md") == "dry_run")
    check("Writer write to claims -> deny (lane deny beats degrade)",
          d(writer, "write", "30-synthesis/01-claims/c.md") == "deny")
    check("Socratic write anywhere -> deny (hard write-denial)",
          d(socratic, "write", "10-inbox/01-fleeting/f.md") == "deny")

    # ---- read decisions ---------------------------------------------------- #
    check("Coder read normal zone -> allow",
          d(coder, "read", "20-sources/01-papers/p.md") == "allow")
    check("Coder read review-gated -> allow_with_log",
          d(coder, "read", "30-synthesis/01-claims/c.md") == "allow_with_log")

    # ---- auto_fix class gating (Linter) ------------------------------------ #
    check("Linter auto_fix safe class in logs -> allow_with_log",
          d(linter, "auto_fix", "99-system/logs/audit.jsonl", {"class": "safe-and-unambiguous"}) == "allow_with_log")
    check("Linter auto_fix schema-content -> dry_run",
          d(linter, "auto_fix", "99-system/logs/x.md", {"class": "schema-content"}) == "dry_run")
    check("Linter auto_fix review-gated-edit -> deny",
          d(linter, "auto_fix", "99-system/logs/x.md", {"class": "review-gated-edit"}) == "deny")
    check("Linter auto_fix with no class -> deny",
          d(linter, "auto_fix", "99-system/logs/x.md", None) == "deny")

    # ---- delete / mkdir / report ------------------------------------------- #
    check("Coder delete without authorization -> deny",
          d(coder, "delete", "40-workbench/x/06-code/old.py") == "deny")
    check("Coder delete with explicit_authorization in scope -> allow_with_log",
          d(coder, "delete", "40-workbench/x/06-code/old.py", {"explicit_authorization": True}) == "allow_with_log")
    check("Coder mkdir in write_scope -> allow",
          d(coder, "mkdir", "40-workbench/x/06-code/sub") == "allow")
    check("Coder report -> allow",
          d(coder, "report", "40-workbench/x/06-code/") == "allow")

    # ---- skill-conditional one-way narrowing ------------------------------- #
    # counter-outline narrows Writer to framing-only; drafts then deny.
    co_deny = compose_skill_deny(writer, {"deny": {"write": ["40-workbench/*/04-drafts/**"]}})
    check("counter-outline composes a draft-deny",
          co_deny == ["40-workbench/*/04-drafts/**"])
    check("Writer+counter-outline: draft write now denied",
          d(writer, "write", "40-workbench/x/04-drafts/d.md", None, co_deny) == "deny")
    check("Writer+counter-outline: framing write still allowed",
          d(writer, "write", "40-workbench/x/02-framing/f.md", None, co_deny) == "allow")

    # ---- L2 gate-contract: per-profile write-walls (hermes-cli §4/§5) ------- #
    # Lifted from the protocol's case IDs so the gate contract for librarian /
    # mapper / verifier is unit-tested here, not just observed once at runtime.
    # (A plain allowed write returns "allow" and is *logged* via require:audit_log
    # — the protocol's "allow_with_log row" prose means logged, not the
    # allow_with_log decision, which is for review-gated reads / safe auto-fix.)
    check("L1/L2 Librarian write to candidates + sources -> allow",
          d(librarian, "write", "20-sources/01-papers/smithA.md") == "allow"
          and d(librarian, "write", "10-inbox/03-candidates/c.md") == "allow")
    check("X1 Librarian write to claims -> deny (write-wall)",
          d(librarian, "write", "30-synthesis/01-claims/c.md") == "deny")
    check("Librarian write to deliverables / another lane's map -> deny",
          d(librarian, "write", "50-deliverables/d.md") == "deny"
          and d(librarian, "write", "40-workbench/x/01-map/m.md") == "deny")
    check("M1/M2/M3 Mapper write to its three map artifacts -> allow",
          d(mapper, "write", "40-workbench/x/01-map/corpus-map.md") == "allow"
          and d(mapper, "write", "40-workbench/x/01-map/gap-report.md") == "allow"
          and d(mapper, "write", "40-workbench/x/01-map/cluster-maps/c.md") == "allow")
    check("Mapper write to an unlisted map file -> deny (exact-file scope)",
          d(mapper, "write", "40-workbench/x/01-map/other.md") == "deny")
    check("M4 Mapper write outside its lane -> deny (write-wall)",
          d(mapper, "write", "20-sources/p.md") == "deny"
          and d(mapper, "write", "30-synthesis/01-claims/c.md") == "deny")
    check("V1/V2 Verifier write to verification + gap candidates -> allow",
          d(verifier, "write", "40-workbench/x/05-verification/report.md") == "allow"
          and d(verifier, "write", "10-inbox/03-candidates/gap.md") == "allow")
    check("V1 Verifier write to the draft under test -> deny (no self-edit)",
          d(verifier, "write", "40-workbench/x/04-drafts/draft.md") == "deny")
    check("Verifier write to synthesis -> deny (write-wall)",
          d(verifier, "write", "30-synthesis/01-claims/c.md") == "deny")

    # ---- invalid action + missing task_id ---------------------------------- #
    check("unknown action -> deny",
          d(coder, "frobnicate", "40-workbench/x/06-code/main.py") == "deny")

    # ---- SHA-256 ----------------------------------------------------------- #
    check("empty/missing file hashes to the empty-string sha256",
          sha256_file(Path("/no/such/file/anywhere")) == EMPTY_SHA256)

    # ---- engine: audit append + full request path -------------------------- #
    with tempfile.TemporaryDirectory() as td:
        vault = Path(td)
        lane_dir = vault / LANE_OVERRIDE_RELDIR
        lane_dir.mkdir(parents=True)
        # Write a minimal coder lane so load_lane is exercised when PyYAML is present.
        (lane_dir / "coder.yaml").write_text(
            "profile: memoria-coder\n"
            "policy:\n  allow:\n    write:\n      - \"40-workbench/*/06-code/**\"\n"
            "  deny:\n    write:\n      - \"30-synthesis/**\"\n  require:\n    - audit_log\n"
            "routing:\n  write_scope:\n    - \"40-workbench/*/06-code/\"\n",
            encoding="utf-8")
        engine = PolicyEngine(vault)
        if yaml is not None:
            resp = engine.check("memoria-coder", "write",
                                "40-workbench/x/06-code/main.py", "TASK-1", "impl")
            check("engine allow includes before_hash", resp.get("before_hash") == EMPTY_SHA256)
            check("engine logged the allow to audit.jsonl", (vault / AUDIT_RELPATH).is_file())
            deny = engine.check("memoria-coder", "write", "30-synthesis/01-claims/c.md", "TASK-1")
            check("engine deny on lane-denied path", deny["decision"] == "deny")
            lines = (vault / AUDIT_RELPATH).read_text(encoding="utf-8").strip().splitlines()
            check("audit has one line per decision", len(lines) == 2)
            check("audit lines are valid JSON", all(json.loads(ln) for ln in lines))
        else:
            print("  SKIP  engine YAML-load checks (PyYAML not installed)")
        # task_id is mandatory
        no_task = engine.check("memoria-coder", "write", "40-workbench/x/06-code/m.py", "")
        check("missing task_id -> deny", no_task["decision"] == "deny")

    total = "all" if yaml is not None else "core"
    print(f"\n{'FAILED' if failures else 'OK'}: {failures} failing check(s) [{total} suite].")
    return failures


# --------------------------------------------------------------------------- #
def main() -> None:
    ap = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--vault", help="vault root (or set MEMORIA_VAULT_PATH)")
    ap.add_argument("--self-test", action="store_true", help="run unit tests and exit")
    ap.add_argument("--decide", metavar="JSON",
                    help='one-shot: decide a single request, e.g. '
                         '\'{"profile":"memoria-coder","action":"write",'
                         '"path":"40-workbench/x/06-code/m.py","task_id":"T1"}\'')
    args = ap.parse_args()

    if args.self_test:
        sys.exit(1 if self_test() else 0)

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
