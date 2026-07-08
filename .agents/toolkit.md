# Agent Toolkit

`AGENTS.md` is the policy source. This file maps the installed toolkit: what is
available, where it runs, and which component to reach for.

## Layer 1 — generic process

| Component | Claude | Codex | Use when |
|---|---|---|---|
| `superpowers` | `superpowers@superpowers-dev` 6.1.1 | `superpowers@openai-curated` 5.1.3 | Planning, TDD, debugging, parallel work, code review, and finish-the-branch workflows |
| `ponytail` | `ponytail@ponytail` | `ponytail@ponytail` | Keep changes minimal: reuse existing code, stdlib, native features, and installed dependencies before adding machinery |
| `rethink` | `rethink@rethink` | `rethink@rethink` | Tactical architecture and first-principles questions where the current implementation should not anchor the answer |
| `grilling` | loose skill | loose skill | Stress-test an existing plan or design decision by decision |
| `caveman` | loose skill | loose skill | Compress live chat only; never use it in persisted artifacts |
| `codebase-design` | loose skill | loose skill | Name modules, interfaces, seams, adapters, leverage, and locality before design or testing work |
| `improve` | loose skill | loose skill | Produce a scoped, read-only improvement plan or execute one accepted audit finding |
| `interface-design` | `interface-design@interface-design` | loose skill | Review or build product, dashboard, SaaS, admin, and tool UI |
| `frontend-design` | `frontend-design@claude-code-plugins` | loose `frontend-design` skill | Marketing, landing, campaign, brand, or distinctive visual UI |
| `the-elements-of-style` | loose `writing-clearly-and-concisely` skill | loose `writing-clearly-and-concisely` skill | Durable prose clarity: active voice, fewer needless words, clean sentence-level editing |
| `api-design-principles` | loose skill | loose skill | API surface design and review without installing the full backend-development bundle |
| `threat-modeling` | loose skill, pinned `a0962b7` | loose skill, pinned `a0962b7` | Deliberate whole-system STRIDE threat models and attack-surface reviews |
| `codex-security` | — | `codex-security@openai-curated` 0.1.10 | Active Codex security scans, diff scans, finding discovery, triage, validation, and fixes |
| `pr-review-toolkit` | `pr-review-toolkit@claude-code-plugins` | — | Claude-only six-lens PR review agents |
| `security-guidance` | `security-guidance@claude-code-plugins` | — | Claude-only passive security hooks on edits, commits, and pushes |
| `obsidian-skills` | nested skills-dir plugin | loose skills | Obsidian CLI, JSON Canvas, Bases, Defuddle, and Obsidian Markdown workflows |

Superpowers exposes these skill directories on both tools:

`brainstorming`, `dispatching-parallel-agents`, `executing-plans`,
`finishing-a-development-branch`, `receiving-code-review`,
`requesting-code-review`, `subagent-driven-development`,
`systematic-debugging`, `test-driven-development`, `using-git-worktrees`,
`verification-before-completion`, `writing-plans`, and `writing-skills`.
`using-superpowers` is present as the dispatcher/reminder.

The retired loose `tdd` and `grill-me` skills are intentionally absent. The
Anthropic `code-review` plugin and `coderabbit@openai-curated` are intentionally
not installed.

## Layer 2 — repo policy

| File | Owns |
|---|---|
| `.agents/playbooks/code-review.md` | Branch, commit, PR, and working-tree review procedure; it invokes superpowers review isolation plus the tool-native reviewer |
| `.agents/playbooks/verify-change.md` | Observable claim, evidence choice, execution, and verification reporting |
| `.agents/playbooks/exec-plan.md` | How to author, run, validate, and close living ExecPlans |
| `.agents/playbooks/docs-review.md` | Review of changed documentation pages and PRs |
| `.agents/playbooks/docs-audit.md` | Fresh whole-docs audit and repair pass |
| `.agents/playbooks/security-review.md` | Current-diff security review and escalation to full threat modeling |
| `.agents/playbooks/design-history.md` | Design-history chapter maintenance |
| `.agents/playbooks/release.md` | Release issue, milestone, readiness, and release-please workflow |
| `.agents/templates/exec-plan.md` | Living execution-plan skeleton |
| `.agents/templates/handoff.md` | Bounded handoff skeleton with tracker disposition and receiver result |
| `.agents/templates/review-report.md` | Review report shape and severity vocabulary |
| `.agents/templates/release-plan.md` | Release issue prose and readiness scaffold |
| `.agents/system/source-of-truth-map.md` | Source ownership and mirror rules |
| `.agents/system/change-impact-map.md` and `.agents/system/change-impact.yaml` | Change-impact routing and generated map source |
| `.agents/system/test-selection.md` | Check selection by changed surface |
| `.agents/skills/policy-change-review/SKILL.md` | Repo policy-change review |
| `.agents/skills/schema-change/SKILL.md` | Schema-change review |

Layer 2 references Layer 1 by name. It does not restate third-party skill
contracts unless the repo needs a local precedence rule.

## Layer 3 — discovery

`main/CLAUDE.md` contains only `@AGENTS.md`, so Claude Code loads the same repo
policy Codex already reads. The project-container root files
`~/memoria-vault/AGENTS.md` and `~/memoria-vault/CLAUDE.md` may be symlinks to
`main/AGENTS.md` for tools launched from the container root. Global
`~/.claude/CLAUDE.md` and `~/.codex/AGENTS.md` carry cross-skill precedence,
vocabulary, and Codex-only security routing. Loader files are allowed only when
they add no independent repo policy.

## Parity ledger

| Capability | Claude | Codex |
|---|---|---|
| Core process workflows | `superpowers@superpowers-dev` | `superpowers@openai-curated` |
| Minimal implementation discipline | `ponytail` | `ponytail` |
| First-principles tactical architecture | `rethink` | `rethink` |
| Plan grilling | `grilling` | `grilling` |
| Chat compression | `caveman` | `caveman` |
| Design vocabulary | `codebase-design` | `codebase-design` |
| Improvement audits | `improve` | `improve` |
| Prose clarity | `writing-clearly-and-concisely` | `writing-clearly-and-concisely` |
| API design | `api-design-principles` | `api-design-principles` |
| Whole-system threat modeling | `threat-modeling` | `threat-modeling` |
| Product UI review/build | `interface-design` plugin | `interface-design` loose skill |
| Marketing/distinctive UI | `frontend-design` plugin | `frontend-design` loose skill + native model |
| PR review | `superpowers:requesting-code-review` + `pr-review-toolkit` | `superpowers:requesting-code-review` + native Codex review |
| Active security scanning | `security-review` playbook + `threat-modeling` | `codex-security` + `security-review` playbook + `threat-modeling` |
| Passive security hooks | `security-guidance` | no equivalent |
| Obsidian workflows | `obsidian-skills` nested plugin | five loose obsidian skills |

Residual asymmetries are deliberate: Claude has passive `security-guidance`
hooks and interface-design slash commands; Codex has active `codex-security`
scan workflows and runs interface-design inline from the loose skill. Codex
`deep-security-scan` is constrained by this machine's `agents.max_depth = 1`;
use `security-scan` or `security-diff-scan` unless deeper agent nesting is
available.

## How the pieces interlock

Use `AGENTS.md` first for repo rules. Then apply the active skill's own
instructions, with these precedence rules from the global tool configs:

- Ponytail stays on the fast path unless the request needs a new dependency,
  spans independent subsystems, or has real ambiguity about purpose,
  constraints, or success criteria.
- New feature or component design goes through superpowers brainstorming.
  Narrow tactical architecture questions go to rethink.
- `superpowers:test-driven-development` wins over ponytail's code-first default;
  ponytail still keeps the resulting implementation small.
- `codebase-design` supplies the vocabulary for seams, modules, adapters, and
  boundaries. Before a RED test, name the seam being tested.
- Grilling interrogates an existing plan. A bare idea gets brainstorming first.
- `improve` handles one identified audit finding. Spec-derived multi-task
  implementation plans use `superpowers:subagent-driven-development`.
- Single security finding follow-ups stay scoped. Whole-system security
  assessment goes to `threat-modeling`; Codex scan-internal threat-model phases
  stay internal to `codex-security`.
- Durable prose uses `the-elements-of-style`; caveman is chat-only.

Never edit a plugin or vendored loose skill in place. Put routing, precedence,
and repo-specific exceptions in `~/.claude/CLAUDE.md`, `~/.codex/AGENTS.md`, or
this repo's `.agents/` files.

## Review mapping

Claude's `pr-review-toolkit` maps to Codex-native review dimensions this way:

| Claude lens | Codex-native equivalent |
|---|---|
| `comment-analyzer` | Review comments for accuracy, necessity, and drift |
| `pr-test-analyzer` | Review test coverage, missing edge cases, and check output |
| `silent-failure-hunter` | Review error handling, fail-open paths, and observability |
| `type-design-analyzer` | Review type, schema, and API contracts |
| `code-simplifier` | Review complexity, duplication, and avoidable abstraction |
| Security/compliance scan | Review trust boundaries, permissions, secrets, and injection paths |

Run the repo `code-review` playbook before PR handoff. Its report format and
severity terms remain authoritative for persisted reports.

## Sourcing and caveats

Marketplace plugins are installed from Claude marketplaces, Codex
`openai-curated`, or the local Codex plugin marketplaces. Loose skills are copied
from their reviewed source repositories at the pinned commits in the execution
plan. The `am-will/codex-skills` `frontend-design` copy has no license file and
is personal-use only; do not redistribute it.

Discovery sources used for the stack include the installed marketplace manifests,
the OpenAI curated plugin catalog, and the broader Codex plugin indexes reviewed
in the adoption plan. Optional tools such as dataviz, artifact design, and Figma
are not listed because the installed plugin and skill inventory does not prove
they are configured on this machine.
