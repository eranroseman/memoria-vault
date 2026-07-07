# Documentation review

Use this playbook for changes under `docs/` or documentation changes elsewhere.
[`AGENTS.md`](../../AGENTS.md) owns the documentation rules; this file is the
portable procedure for applying them.

For a fresh whole-docs audit and repair pass, use
[Documentation audit](docs-audit.md). This playbook is for reviewing a docs
change or PR.

## 1. Route by reader intent

For each published page, choose exactly one Diátaxis purpose:

- Tutorial: learn by doing
- How-to guide: accomplish a task
- Reference: look up exact information
- Explanation: understand how the system works
- Design Book: understand why a design choice was made

Flag mixed-purpose pages for splitting. How-to titles must be concise and must
match their filename and index link text.

## 2. Check links and publication boundaries

- Links between `docs/` pages are relative.
- Published pages must not use relative links into `vault-template/` or other unpublished
  repository paths. Prefer inline paths or an absolute GitHub blob/tree URL.
- Excluded `tmp/` directories may link to repository files.
- Root `CONTRIBUTING.md` and agent playbooks are not published.
- Link text should name the destination concept, not merely repeat a filename.

Run:

```bash
python3 scripts/checks/docs_doctor.py docs
python3 scripts/checks/docs_doctor.py --vault-links
```

Distinguish blocking failures from known advisory warnings.

## 3. Check navigation

- Every new page appears in its section `README.md`.
- Every how-to page also appears in `docs/how-to-guides/README.md`.
- `nav_order`, `parent`, `has_children`, and `permalink` match neighboring pages.
- Section indexes stay concise and order children consistently with the sidebar.

## 4. Check terminology and claims

- Use the repository vocabulary from `AGENTS.md` and `docs/reference/glossary.md`.
- Keep spaces, queues, and agent lanes distinct.
- Put new citations in `docs/reference/bibliography.md` using the existing format.
- Verify commands, paths, profile names, counts, and release references against
  current source files rather than copying older prose.
- If a reference page repeats generated or source-owned contracts, run the
  matching generator or drift check. Decision-history changes should update
  `design-history/arcs.md` and the active release decision ledger when they
  change the current or pending design line.
- If `the-elements-of-style` is installed, apply its
  `writing-clearly-and-concisely` rules (active voice, omit needless words) as a
  prose-clarity pass over changed pages — complementary to this section's
  terminology and citation checks.
- If routes, navigation, `baseurl`-sensitive links, or public outbound links
  changed, run the live docs link checker after deploy or record why it was not
  applicable.

## 5. Report

Report findings by severity with file and line references. Name the violated
rule: quadrant, link, navigation, terminology, factual drift, or citation.
Finish with the checker results and any advisories that remain.
