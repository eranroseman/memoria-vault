# Documentation review

Use this playbook for changes under `docs/` or documentation changes elsewhere.
[`AGENTS.md`](../../AGENTS.md) owns the documentation rules; this file is the
portable procedure for applying them.

## 1. Route by reader intent

For each published page, choose exactly one Diátaxis purpose:

- Tutorial: learn by doing
- How-to guide: accomplish a task
- Reference: look up exact information
- Explanation: understand why

Flag mixed-purpose pages for splitting. How-to titles must be concise and must
match their filename and index link text.

## 2. Check links and publication boundaries

- Links between `docs/` pages are relative.
- Published pages must not use relative links into `src/` or other unpublished
  repository paths. Prefer inline paths or an absolute GitHub blob/tree URL.
- Repo-internal pages under `docs/contributing/`, `docs/releasing/`,
  `docs/testing/`, and excluded `tmp/` directories may link to repository files.
- Link text should name the destination concept, not merely repeat a filename.

Run:

```bash
python scripts/docs_doctor.py docs
bash scripts/check-vault-links.sh
```

Distinguish blocking failures from known advisory warnings.

## 3. Check navigation

- Every new page appears in its section `README.md`.
- Every how-to page also appears in `docs/how-to-guides/README.md`.
- `nav_order`, `parent`, `has_children`, and `permalink` match neighboring pages.
- Section indexes stay concise and order children consistently with the sidebar.

## 4. Check terminology and claims

- Use the repository vocabulary from `AGENTS.md` and `docs/reference/glossary.md`.
- Keep Compile, Compose, and the knowledge cycle distinct.
- Put new citations in `docs/reference/bibliography.md` using the existing format.
- Verify commands, paths, profile names, counts, and release references against
  current source files rather than copying older prose.

## 5. Report

Report findings by severity with file and line references. Name the violated
rule: quadrant, link, navigation, terminology, factual drift, or citation.
Finish with the checker results and any advisories that remain.
