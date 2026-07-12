# 0.1.0-beta.1 resources

This directory is a reference archive only.

Files here are not source of truth, governing requirements, or design
justification. They may help reconstruct context, prior alternatives, review
passes, and research trails, but any load-bearing claim in beta.1 must be stated
in an active top-level release file and grounded in facts or primary sources.

## Precedence

For beta.1, read active top-level files before anything in this directory.

1. `../data-structure-analysis.md` takes precedence for data structure, naming,
   storage, migration, bundle layout, and schema questions.
2. `../query-mechanism-analysis.md` takes precedence for query, retrieval,
   indexing, graph traversal, fusion, reranking, and synthesis mechanics.
3. `../0.1.0-beta.1-requirements.md` defines MVP scope and acceptance, but must
   be read through the two analysis files above when it uses stale data/query
   names.
4. `../0.1.0-beta.1-design.md` describes the system design, but must be updated
   to match the two analysis files above where terminology or mechanics differ.
5. Files in `resources/` never override active top-level files.

If a resource file disagrees with an active top-level file, the resource file is
historical context. Do not use it as justification for implementation.

## What Belongs Here

- prior design drafts;
- borrow/adapt/reject passes;
- gap analyses and review notes;
- research notes that are useful for traceability;
- superseded inputs kept for auditability.

## What Does Not Belong Here

- governing requirements;
- source-of-truth design decisions;
- implementation acceptance criteria;
- claims that are not restated and sourced in active top-level files.
