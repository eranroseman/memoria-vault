# Agent Toolkit

`AGENTS.md` is the policy source. This file records only repo-specific tool
routing and known Claude/Codex asymmetries. Installed plugin inventories and
generic skill procedures belong to the tools that expose them.

## Discovery

`main/CLAUDE.md` contains only `@AGENTS.md`, so Claude Code loads the same repo
policy Codex already reads. The project-container root files
`~/memoria-vault/AGENTS.md` and `~/memoria-vault/CLAUDE.md` may be symlinks to
`main/AGENTS.md` for tools launched from the container root. When those launch
shims exist, `~/memoria-vault/.agents` should also resolve to `main/.agents` so
relative playbook and system-map links work from the same root. Loader files are
allowed only when they add no independent repo policy.

Global `~/.claude/CLAUDE.md` and `~/.codex/AGENTS.md` carry cross-skill
precedence, vocabulary, and tool-specific security routing. Keep repo policy in
`AGENTS.md` or `.agents/`, not in vendored plugins or loose skills.

## Tooling Parity

Every Claude/Codex gap must name a shared fallback and a required check. Do not
try to synchronize plugin inventories; align behavior through repo policy,
playbooks, doctors, and `scripts/verify`.

| Task | Claude path | Codex path | Shared fallback | Required check |
|---|---|---|---|---|
| Skill routing | Global `~/.claude/CLAUDE.md` plus installed skills | Global `~/.codex/AGENTS.md` plus session skills | Use `AGENTS.md` precedence and the matching `.agents/` playbook when a named skill is missing | `python3 scripts/checks/agents_doctor.py` |
| PR review | `superpowers:requesting-code-review` plus `pr-review-toolkit` | `superpowers:requesting-code-review` plus native Codex review | Use [Code review](playbooks/code-review.md) and [Review report](templates/review-report.md) | `python3 scripts/verify pr` |
| Security scanning | `security-guidance` may run passive hooks | `codex-security` runs only when explicitly invoked | Use [Security review](playbooks/security-review.md) for sensitive diffs and explicit scans for broad audits | `python3 scripts/verify pr` |
| Deep security scan | Tool-dependent | `codex-security:deep-security-scan` needs agent depth >= 2 on this machine | Use `codex-security:security-scan` or `codex-security:security-diff-scan`, then [Security review](playbooks/security-review.md) | `python3 scripts/verify pr` |
| UI design commands | Interface-design slash commands may exist | Run the matching interface-design review inline from the skill | Use the installed UI skill's `SKILL.md` plus app-specific verification from [Test selection](system/test-selection.md) | `python3 scripts/checks/agents_doctor.py` |
| Slash commands | Some workflows expose slash commands | Run the same skill or playbook inline | Use the named skill's `SKILL.md`; if unavailable, use the matching `.agents/` playbook | `python3 scripts/checks/agents_doctor.py` |
| Version skew | Active plugin versions live in `~/.claude/plugins/installed_plugins.json`; cache folders may contain older copies | Active versions come from the session skill list and `.codex` cache paths; cache folders may contain older copies | Do not pin repo policy to plugin versions. For version-sensitive behavior, record the active skill/plugin name, version or cache path, and fallback used in the review or handoff. | `python3 scripts/checks/agents_doctor.py` |
| Verification | Tool-specific preflight habits may differ | Explicit `scripts/verify` and focused checks | Use [Test selection](system/test-selection.md) and [Verify a change](playbooks/verify-change.md) | `python3 scripts/verify pr` |

## Routing

- `AGENTS.md` wins for worktrees, branches, source of truth, verification,
  documentation routing, PRs, and merge discipline.
- `.agents/README.md` indexes portable playbooks, templates, and system maps.
- Active skills govern their own procedure unless `AGENTS.md` names a repo
  exception.
- Durable prose uses the prose-clarity skill when available; chat-compression
  skills are chat-only.
- Whole-system security assessment goes to `threat-modeling`; Codex
  scan-internal threat-model phases stay inside `codex-security`.
