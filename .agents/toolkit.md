# Agent Toolkit

`AGENTS.md` is the policy source. This file records only repo-specific tool
routing and known Claude/Codex asymmetries; installed plugin inventories belong
to the tools that expose them.

## Discovery

`main/CLAUDE.md` contains only `@AGENTS.md`, so Claude Code loads the same repo
policy Codex already reads. The project-container root files
`~/memoria-vault/AGENTS.md` and `~/memoria-vault/CLAUDE.md` may be symlinks to
`main/AGENTS.md` for tools launched from the container root. Loader files are
allowed only when they add no independent repo policy.

Global `~/.claude/CLAUDE.md` and `~/.codex/AGENTS.md` carry cross-skill
precedence, vocabulary, and tool-specific security routing. Keep repo policy in
`AGENTS.md` or `.agents/`, not in vendored plugins or loose skills.

## Local Asymmetries

| Topic | Claude | Codex |
|---|---|---|
| PR review | `superpowers:requesting-code-review` plus `pr-review-toolkit` | `superpowers:requesting-code-review` plus native Codex review |
| Security scanning | `security-guidance` may run passive hooks | `codex-security` runs only when explicitly invoked |
| Deep security scan | Tool-dependent | `codex-security:deep-security-scan` needs agent depth >= 2; use `security-scan` or `security-diff-scan` on this machine |
| UI design | Interface-design slash commands may exist | Run the matching interface-design review inline from the skill |

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
