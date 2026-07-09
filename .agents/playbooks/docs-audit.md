# Documentation audit

Use this playbook for a fresh, whole-docs audit and repair pass. It is larger
than a docs review: it covers structure, Diátaxis placement, terminology,
generated references, implementation drift, coverage gaps, and public-site
links. Do not reuse prior findings.

[`AGENTS.md`](../../AGENTS.md) owns the documentation rules; this file is the
whole-surface pass for applying them end to end.

## 1. Scope

Read the full documentation surface:

- `docs/README.md`, `docs/_config.yml`, and all section `README.md` files.
- `docs/tutorials/`
- `docs/how-to-guides/`
- `docs/reference/`
- `docs/explanation/`
- `design-history/`
- root `CONTRIBUTING.md`

Scan the rest of the repository only where needed to verify implementation
truth: packaged seed files under `src/memoria_vault/product/workspace_seed/`,
`scripts/`, schemas, generated-reference inputs, commands, fields, profile
names, and Hermes or Obsidian claims.

## 2. Audit against AGENTS.md

For each page, record:

- Documentation category expected by `AGENTS.md` and the page's actual shape.
- Duplicate or near-duplicate content.
- Contradictions, stale implementation claims, or missing implementation docs.
- Overloaded, idiosyncratic, or non-standard terms.
- Filename, title, index-link, frontmatter, route, and nav-order mismatches.
- Link and publication-boundary problems.
- Action: stay, move, merge, split, rename, generate, or delete.

Apply the [Documentation review](docs-review.md) checks to every page changed by
the audit.

Treat `docs/explanation/` as the conceptual surface. Its operational pages
describe how the system works; `docs/explanation/rationale/` explains why the
design takes its current shape. Decision history belongs in `design-history/`;
release state lives in GitHub.

Use subagents only for independent audit slices. Verify their claimed coverage
before relying on it.

## 3. Fix

Make the smallest durable change:

- Remove hidden compatibility pages, redirects, stale mirrors, duplicate pages,
  route-preservation pages, and common-knowledge pages.
- Prefer moving, renaming, merging, or deleting over preserving bad historical
  structure. Do not add compatibility pages.
- Split mixed-purpose pages; merge near-duplicates; keep implementation-critical
  detail while trimming verbose prose.
- Keep filenames, titles, README link text, frontmatter, nav order, and routes
  consistent.
- Generate reference pages from their source of truth when a source exists.
  Manual reference pages must not restate machine-readable contracts unless a
  generator or drift check guards them.
- Use the link and citation rules in `AGENTS.md`; do not repeat them here.

## 4. Verify

Run the focused docs checks:

```bash
python3 scripts/checks/docs_doctor.py docs
python3 scripts/checks/agents_doctor.py
python3 scripts/checks/docs_doctor.py --vault-links
```

Then run the standard source gate:

```bash
scripts/verify pr
```

After merge and GitHub Pages deploy, run the live docs link checker against
`https://eranroseman.github.io/memoria-vault/`. Report pages crawled, internal
targets checked, internal link refs checked, broken internal targets, bad
internal fragments, external targets checked, and broken external targets.

## 5. Report

Report only:

- What changed.
- What was deleted, merged, split, moved, renamed, or generated.
- Remaining intentional limitations, if any.
- Verification results.
- Live docs link crawl result.
