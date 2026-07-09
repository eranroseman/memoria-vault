# Documentation review

Use this playbook for changes under `docs/` or documentation changes elsewhere.
[`AGENTS.md`](../../AGENTS.md) owns the documentation rules; this file is the
portable procedure for applying them.

For a fresh whole-docs audit and repair pass, use
[Documentation audit](docs-audit.md). This playbook is for reviewing a docs
change or PR.

## 1. Apply AGENTS.md routing

Use `AGENTS.md` -> "Writing docs" as the source for documentation categories,
linking, indexing, citations, spelling, and decision-history placement. Flag
mixed-purpose pages, stale mirrors, and pages whose filename, title, index link,
frontmatter, or route disagree.

## 2. Check links and publication boundaries

Run:

```bash
python3 scripts/checks/docs_doctor.py docs
python3 scripts/checks/docs_doctor.py --vault-links
```

Distinguish blocking failures from known advisory warnings.

## 3. Check source-backed claims

- Verify commands, paths, profile names, counts, and release references against
  current source files rather than copying older prose.
- If a reference page repeats generated or source-owned contracts, run the
  matching generator or drift check. Decision-history changes should update
  `design-history/arcs.md` and the active release decision ledger when they
  change the current or pending design line.
- If `writing-clearly-and-concisely` is installed, apply its prose rules as a
  clarity pass over changed pages — complementary to this section's terminology
  and citation checks.
- If routes, navigation, `baseurl`-sensitive links, or public outbound links
  changed, run the live docs link checker after deploy or record why it was not
  applicable.

## 4. Report

Report findings by severity with file and line references. Name the violated
rule: quadrant, link, navigation, terminology, factual drift, or citation.
Finish with the checker results and any advisories that remain.
