# Memoria GitHub Workflow & Issue Tracking Guide

**Project:** Memoria Research Operating System  
**Status:** Active  
**Last Updated:** 2026-06-05  
**Scope:** Issue tracking, pull request conventions, CI/CD integration, release management, changelog, ADRs

---

## Table of Contents

1. [Overview](#overview)
2. [Issue Tracking System](#issue-tracking-system)
3. [Repository Structure](#repository-structure)
4. [Issue Types & Templates](#issue-types--templates)
5. [GitHub Project Board Workflow](#github-project-board-workflow)
6. [Pull Request Conventions](#pull-request-conventions)
7. [CI/CD Integration](#cicd-integration)
8. [Release Management](#release-management)
9. [Changelog Management](#changelog-management)
10. [Architecture Decision Records (ADRs)](#architecture-decision-records-adrs)
11. [Automation Reference](#automation-reference)

---

## Overview

This document defines the end-to-end development workflow for Memoria, covering how work is captured, tracked, reviewed, deployed, and documented.

The core principle is: **issue → PR → CI → deploy → changelog → release**, with ADRs capturing architectural decisions separately from day-to-day work items.

All research notes and draft ADRs live in the Obsidian vault. Finalized ADRs and issue templates are committed to the repository. This keeps transient thinking in the Zettelkasten and durable decisions in version control.

---

## Issue Tracking System

The system for tracking bugs and features is called an **issue tracker**. In GitHub this is **GitHub Issues**, paired with **GitHub Projects** for board-level visibility.

| Term | What It Means |
|------|--------------|
| Issue tracker | General term covering bugs, features, tasks, and other work items |
| Bug tracker | Specifically tracks software bugs/defects |
| Defect tracking system | Alternate name for bug tracking |
| Project management tool | Broader term that includes issue tracking (Jira, Azure DevOps) |

**For Memoria:** GitHub Issues is the right choice. It integrates directly with the repository, supports issue templates and labels, and connects to GitHub Projects for board tracking.

---

## Repository Structure

```
memoria/
├── .github/
│   ├── ISSUE_TEMPLATE/
│   │   ├── config.yml
│   │   ├── bug_report.md
│   │   ├── feature_request.md
│   │   ├── research_library.md
│   │   └── adr_request.md
│   ├── workflows/
│   │   ├── release.yml            # Tag-based release creation
│   │   ├── release-please.yml     # Semantic versioning (optional)
│   │   ├── update-adr-index.yml   # Auto-generate ADR index
│   │   └── validate-adrs.yml      # Front matter validation
│   ├── pull_request_template.md
│   ├── release.yml                # Release notes grouping config
│   └── WORKFLOW_README.md
├── adr/
│   ├── active/                    # Current ADRs (e.g. ADR-0001.md)
│   ├── archive/                   # Deprecated/superseded ADRs
│   └── README.md                  # Auto-generated ADR index
├── docs/                          # System design docs, research docs
├── scripts/
│   └── generate_adr_index.py
└── src/                           # Source code
```

**Key separation principle:**

| Content Type | Where It Lives | Why |
|---|---|---|
| Bugs & Features | GitHub Issues + GitHub Projects | Active work items needing tracking and PR linkage |
| ADRs & Research Docs | `/adr` folder (Markdown files) | Static documentation tied to code version |
| Research Notes | Obsidian vault | Matches Zettelkasten workflow; synced via Git/Syncthing |

---

## Issue Types & Templates

### Issue Categories

| Label | Template | Use For |
|-------|----------|---------|
| `bug` | `bug_report.md` | Bugs, regressions, broken automation |
| `enhancement` | `feature_request.md` | New capabilities, integrations |
| `research` | `research_library.md` | Library evaluation, technology assessment |
| `adr-needed` | `adr_request.md` | Architectural decisions |

### Library Research Template (4-Phase Workflow)

Each library evaluation issue should follow these phases:

**Phase 1 — Discovery**
- [ ] Read README & documentation
- [ ] Check GitHub activity (commits, issues, stars)
- [ ] List core capabilities
- [ ] Note dependencies & requirements

**Phase 2 — Evaluation**
- [ ] Build proof-of-concept in `/experiments/`
- [ ] Test with real data
- [ ] Benchmark performance and cost
- [ ] Compare to alternatives

**Phase 3 — Recommendation**
- [ ] Document findings in Obsidian vault
- [ ] Create ADR if an architectural decision is required
- [ ] Propose specific use cases
- [ ] Estimate integration effort

**Phase 4 — Decision**
- [ ] Create feature issue (if adopting)
- [ ] Add to research roadmap (if deferring)
- [ ] Archive notes in Obsidian (if rejecting)

**Decision logic:**

| Question | Yes → | No → |
|---|---|---|
| Does it solve a real problem? | Is it architectural? | Reject + archive |
| Is it architectural? | Create ADR + feature issue | Create feature issue directly |
| Integration effort > 2 weeks? | Add to research roadmap | Schedule as near-term issue |

---

## GitHub Project Board Workflow

### Board Columns

```
Backlog → Ready → In Progress → Code Review → Done
```

| Column | What Goes Here | WIP Limit |
|--------|---------------|-----------|
| Backlog | Unprocessed ideas, research items | None |
| Ready | Well-defined, assigned, actionable | Per assignee |
| In Progress | Currently being worked on | 1–2 per person |
| Code Review | PR open, awaiting review | None |
| Done | Closed issues / merged PRs | None |

### Full Issue Lifecycle

**Setup**
1. Create project using Kanban template; link to repository
2. Add custom fields: priority (Critical/High/Medium/Low), complexity (1–5), iteration
3. Enable built-in automations (see [Automation Reference](#automation-reference))

**Issue Creation**
1. Use the appropriate issue template
2. Write a clear title and description with acceptance criteria
3. Add labels, assign an owner, set priority field

**Planning**
1. Move to "Ready" when the issue is actionable
2. Break large issues into sub-issues if effort exceeds 2 weeks or requires multiple PRs
3. Add issue dependencies and assign to a milestone or iteration

**Execution**
1. Move to "In Progress" when work begins
2. Create a branch and open a PR linked with `Closes #123`
3. Request reviewers; merge only after CI passes

**Closure**
1. Issue auto-moves to "Done" when closed via automation
2. Confirm in board; add a status update if relevant

### Issues Per PR

| Approach | When to Use |
|---|---|
| 1 issue per PR (standard) | Always preferred — keeps PRs focused and reviewable |
| 2–3 issues per PR | Only when implementing tightly related features |
| Many issues per PR | Avoid — increases review difficulty |

Target PR size: ≤ 500 lines changed, reviewable in under 1 hour.

### Memoria-Specific Board Fields

| Content Type | Board Column | Custom Field |
|---|---|---|
| Bugs | Backlog → Ready → In Progress | Priority: Critical/High/Medium/Low |
| Features | Backlog → Ready → In Progress | Priority + Complexity (1–5) |
| Research / Library eval | Backlog (separate view) | Type: Research/ADR/Experiment |
| Hermes agent tasks | In Progress → Code Review | Agent: Memory/Orchestration/Docs |

---

## Pull Request Conventions

### PR Template Checklist

Every PR should include:

- [ ] Linked issue (`Closes #XXX`)
- [ ] Summary of what changed and why
- [ ] Tests added or updated
- [ ] Docs updated (if user-facing)
- [ ] `CHANGELOG.md` updated (if user-visible change)
- [ ] ADR linked or created (if architectural)
- [ ] Deployment impact noted

### Commit Message Format (Conventional Commits)

```
<type>[optional scope][optional !]: <short description>

[optional body]

[optional footer: BREAKING CHANGE: ...]
```

| Type | Use For |
|------|---------|
| `feat` | New feature (triggers minor version bump) |
| `fix` | Bug fix (triggers patch bump) |
| `docs` | Documentation only |
| `chore` | Maintenance, tooling, deps |
| `refactor` | Code change with no behavior change |
| `research` | Research outcomes |

### Breaking Changes

Use `!` in the header or `BREAKING CHANGE:` in the footer:

```
feat!: rename agent registry schema

BREAKING CHANGE: agent configs must now use `agents.enabled` instead of `enabled_agents`.
Update all config files before upgrading.
```

Breaking change entries must state: **what changed**, **who is affected**, **what action is required**, and **the replacement path**.

---

## CI/CD Integration

### Full Trace: Idea → Deploy

| Stage | GitHub Artifact | Automation |
|-------|----------------|-----------|
| Work created | Issue | Template, labels, project assignment |
| Implementation | PR | Linked to issue with `Closes #...` |
| Verification | CI checks | Tests, lint, build, security scan |
| Merge | Closed issue | Auto-close issue on merge |
| Deployment | Release / environment | Tag-based or main-branch deploy |

### Pipeline Conventions

- Run CI on every PR: tests, linting, build, security scan
- Deploy only after PR passes CI and is merged to `main`
- Tag-based deployments: use semantic version tags (e.g. `v1.2.0`)
- Deployment metadata (SHA, environment, timestamp) posted back to the release

### Label Conventions for CI

| Label | Meaning |
|-------|---------|
| `bug` | Defect fix |
| `enhancement` / `feature` | New capability |
| `research` | Research/evaluation outcome |
| `docs` | Documentation change |
| `adr-needed` | Architectural decision required |
| `skip-release` | Exclude from release notes |
| `breaking` | Breaking change (manual backup label) |

---

## Release Management

### Tag-Based Release (Simple)

Trigger a release by pushing a version tag:

```bash
git tag v0.1.0
git push origin v0.1.0
```

The `.github/workflows/release.yml` workflow creates a GitHub Release and generates notes from merged PRs automatically.

### Release Notes Config (`.github/release.yml`)

```yaml
changelog:
  categories:
    - title: Features
      labels: [feature, enhancement]
    - title: Fixes
      labels: [bug, fix]
    - title: Research
      labels: [research]
    - title: Documentation
      labels: [docs]
  exclude:
    labels: [skip-release]
```

### Semantic Versioning with Release Please (Optional)

For automated semantic versioning, use `release-please`:

1. Adopt Conventional Commits (`feat:`, `fix:`, `chore:`)
2. Add `release-please-config.json` and `.release-please-manifest.json`
3. Add `.github/workflows/release-please.yml`
4. Merge the release PR that Release Please opens — this triggers the version bump, changelog update, and GitHub Release

```json
{
  "packages": {
    ".": {
      "release-type": "simple"
    }
  }
}
```

---

## Changelog Management

### Structure

`CHANGELOG.md` lives in the repository root. Keep an `Unreleased` section at the top; move entries into versioned sections when cutting a release.

```markdown
# Changelog

All notable changes to this project will be documented in this file.

## [Unreleased]

### Added
- ...

### Changed
- ...

### Fixed
- ...

## [0.3.0] - 2026-06-05

### Added
- ...
```

### Section Headings

| Section | Use For |
|---------|---------|
| Added | New capabilities, commands, workflows, integrations |
| Changed | Behavior changes, schema updates, workflow changes |
| Fixed | Bugs, regressions, broken automation |
| Removed | Deleted features, retired paths, dropped support |
| Deprecated | Features that still work but will be removed |
| Security | Auth changes, permission changes, sensitive fixes |
| Research | Important evaluation outcomes affecting roadmap or architecture |

### Writing Rules

Each bullet should:
- Start with a strong action verb
- Name the affected system or workflow
- Explain user impact, not implementation detail
- Include migration guidance when behavior changes

**Strong vs. weak entries:**

| Weak | Strong |
|------|--------|
| Updated system. | Changed GitHub release automation to publish notes from merged PRs. |
| Fixed bug. | Fixed project board status updates that left merged work items in `In Progress`. |
| Added issue stuff. | Added bug and feature issue templates for standardized intake in GitHub. |

### What Belongs in the Changelog

**Include:**
- New user-facing features
- Bug fixes that change observed behavior
- Configuration or schema changes
- Breaking changes with migration steps
- Release or deployment workflow changes affecting maintainers
- Integration changes (GitHub, Obsidian, Hermes agents)

**Exclude:**
- Refactors with no user-visible impact
- Routine dependency bumps with no practical effect
- Test-only changes
- Temporary experiments that never shipped

### Review Checklist

Before merging a changelog update:

- [ ] The entry is understandable without reading code
- [ ] Wording explains user impact, not implementation detail
- [ ] Entry is in the correct section
- [ ] Entry is notable enough to include
- [ ] Migration guidance is present for breaking changes
- [ ] The release section is easy to scan

---

## Architecture Decision Records (ADRs)

### Principle

ADRs are **documentation**, not work items. They explain *why* a decision was made. Issues track *what* needs to be done. Keep them separate.

| Factor | Bugs/Features | ADRs |
|--------|--------------|------|
| Lifecycle | Active, changing, closed when done | Permanent historical record |
| Format | Short issue + comments | Long-form prose with rationale |
| Review | Code review via PRs | Decision review, then archived |
| Frequency | Daily/weekly | Monthly/quarterly |
| Code link | PR closes issue | ADR referenced in PR description |

### ADR Front Matter

Every ADR file must include:

```markdown
---
adr: 0001
title: Use GitHub Projects for issue tracking
status: accepted        # accepted | deprecated | superseded
date: 2026-06-05
related issues: "#12, #18"
related prs: "#34"
superseded by:
---
```

Required fields: `adr`, `title`, `status`, `date`, `related issues`, `related prs`

### Folder Layout

```
adr/
├── active/
│   └── 0001-use-github-projects.md
├── archive/
│   └── 0003-old-agent-registry.md   # deprecated
└── README.md                         # auto-generated index
```

### ADR Index (Auto-Generated)

The `adr/README.md` file is generated automatically by `scripts/generate_adr_index.py`. Do not edit it manually.

To regenerate locally:

```bash
python scripts/generate_adr_index.py
```

The CI workflow `update-adr-index.yml` regenerates and opens a PR when ADR files change.

### ADR Validation in CI

The `validate-adrs.yml` workflow checks that all ADR files have the required front matter fields. PRs that add or modify ADRs without required fields will fail CI.

---

## Automation Reference

### Built-In GitHub Project Workflows

Enable in **Project → Workflows tab**:

| Trigger | Action |
|---------|--------|
| Item added to project | Set status = Backlog |
| Issue closed | Set status = Done |
| PR merged | Set status = Done |
| Status set to Done | Auto-close issue |
| Item archived | After 90 days in Done |

### GitHub Actions Workflows

| File | Trigger | Purpose |
|------|---------|---------|
| `release.yml` | Push tag `v*` | Create GitHub Release with generated notes |
| `release-please.yml` | Push to `main` | Semantic version bump + release PR (optional) |
| `update-adr-index.yml` | Push to `adr/**`, schedule Mon 9am | Regenerate ADR index and open PR |
| `validate-adrs.yml` | PR with `adr/**` changes | Fail if required front matter is missing |

### Label Taxonomy

```
# Priority
priority:critical
priority:high
priority:medium
priority:low

# Type
bug
enhancement
research
docs
adr-needed
breaking

# Process
skip-release
wip
blocked
```

### Claude Code Skills (Optional)

For faster issue creation from the CLI:

```
.claude/skills/memoria-issue-manager/
├── SKILL.md
└── scripts/
    └── create-issue.sh
```

The skill wraps `gh issue create` with Memoria-specific templates and labels. Install with:

```bash
cp -r .claude/skills/memoria-issue-manager ~/.claude/skills/
```

---

*This document is owned by the Memoria project. Update it when the workflow changes, and link relevant PRs when doing so.*
