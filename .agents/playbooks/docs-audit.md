# Documentation audit

Use this playbook for a fresh, whole-docs audit and repair pass. It is larger
than a docs review: it covers structure, Diátaxis placement, terminology,
generated references, implementation drift, coverage gaps, and public-site
links. Do not reuse prior findings.

[`AGENTS.md`](../../AGENTS.md) owns the documentation rules; this file is the
portable procedure for applying them end to end.

## 1. Scope

Read the full documentation surface:

- `docs/README.md`, `docs/_config.yml`, and all section `README.md` files.
- `docs/tutorials/`
- `docs/how-to-guides/`
- `docs/reference/`
- `docs/explanation/`
- `docs/design/`
- `docs/adr/`
- `docs/releasing/`
- `docs/testing/`
- root `CONTRIBUTING.md`

Scan the rest of the repository only where needed to verify implementation
truth: `vault-template/`, `scripts/`, schemas, generated-reference inputs, commands,
fields, profile names, and Hermes or Obsidian claims.

## 2. Audit

For each page, record:

- Expected Diátaxis type and actual type.
- Duplicate or near-duplicate content.
- Contradictions, stale implementation claims, or missing implementation docs.
- Overloaded, idiosyncratic, or non-standard terms.
- Filename, title, index-link, frontmatter, route, and nav-order mismatches.
- Link and publication-boundary problems.
- Action: stay, move, merge, split, rename, generate, or delete.

Apply the [Documentation review](docs-review.md) checks to every page changed by
the audit.

Treat `docs/explanation/` and `docs/design/` as one conceptual surface split by
"how it works" vs. "why this design." Ordinary docs describe the current system;
history belongs only in `docs/adr/` and `docs/releasing/`.

Use subagents only for independent audit slices. Verify their claimed coverage
before relying on it.

## 3. Fix

Make the smallest durable change:

- Align pages with Diátaxis: tutorials teach by doing; how-to guides perform a
  task; reference pages give exact values; explanation pages describe how the
  system works; design pages explain why it is designed that way.
- Remove hidden compatibility pages, redirects, stale mirrors, duplicate pages,
  route-preservation pages, and common-knowledge pages.
- Prefer moving, renaming, merging, or deleting over preserving bad historical
  structure. Do not add compatibility pages.
- Split mixed-purpose pages; merge near-duplicates; keep implementation-critical
  detail while trimming verbose prose.
- Keep filenames, titles, README link text, frontmatter, nav order, and routes
  consistent.
- Keep `docs/how-to-guides/` and `docs/reference/` current with implemented
  system functionality.
- Keep project, code, Hermes, and Obsidian names self-explanatory and standard.
- Generate reference pages from their source of truth when a source exists.
  Manual reference pages must not restate machine-readable contracts unless a
  generator or drift check guards them.
- Use public-safe links: published Pages routes must resolve after Jekyll
  `baseurl` rewriting; site-excluded docs and repo files use GitHub blob/tree
  URLs; private GitHub Project URLs are not published; access-blocked outbound
  URLs are replaced or left as plain source text.

## 4. Verify

Run the focused docs checks:

```bash
python scripts/docs_doctor.py docs
python scripts/agents_doctor.py
python scripts/gen_profiles_ref.py --check
python scripts/gen_reference_refs.py --check
bash scripts/check-vault-links.sh
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
