"""Policy data models shared by the decision core and MCP wrapper."""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class LanePolicy:
    """Parsed lane-override policy for one profile."""

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
        """Capitalized short name for policy rule ids."""
        name = (
            self.profile[len("memoria-") :] if self.profile.startswith("memoria-") else self.profile
        )
        return name[:1].upper() + name[1:]


@dataclass
class Decision:
    """Decision response from the pure policy core."""

    decision: str
    policy_rule: str
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
