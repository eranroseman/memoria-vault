# Cross-tool parity — Codex, Kilo, Claude

Codex and Kilo read `AGENTS.md` natively, so all three tools run the same repo
policy. Where they differ, the asymmetry is deliberate and the mechanism is
whichever one that platform actually has. Read the entry for the tool you are.

## Security review

Claude runs it through always-on security-guidance hooks. Codex has no
passive-hook equivalent, so it runs an explicit `codex-security` scan on
installer or runtime-policy changes.

## Write perimeter

Claude: native permission prompts and bash sandboxing. Codex: the sandbox's
`writable_roots`.

## Session isolation

Codex isolates each session in its own worktree by default, under `.worktrees/`.

Claude creates one explicitly — see the worktree command in `AGENTS.md`,
Ground truth. Both directories are gitignored and both stay: two tools' live
working areas. The split is forced, not a preference — Claude Code manages only
`.claude/worktrees/`, and `EnterWorktree` anywhere else raises a `safetyCheck`
prompt that cannot be pre-approved.

Create new worktrees from the main checkout. `EnterWorktree` refuses to create
one from inside another worktree; switching into an existing managed worktree by
`path` is allowed.

## Claude-side repo policy

The checked-in `.claude/settings.json` carries what `AGENTS.md` promises about
Claude sessions: the process spine (superpowers, pinned), security-guidance
enablement, a recurring-safe-command allowlist, and a `PreToolUse` hook
(`.claude/hooks/block-git-add-all.py`) enforcing the shared-index rule.

Codex needs no equivalent — its default worktree isolation gives each session a
private index, which is the same protection by a different route.
