---
name: verify-check-citation
description: "The cite-check: every [@citekey] in a draft or claim note must resolve to a real bib entry + paper note, and the cited source must actually support the claim. Token resolution is deterministic (regex + bib lookup); claim-source matching uses embedding similarity bands with an LLM judge confined to the ambiguous middle band. Flag-only — findings land as inbox flag cards; the draft is never edited. Run before export, or whenever a citation's support is questioned."
version: 2.0.0
author: Memoria
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [Verification, Citations, Claims]
    related_skills: [qmd, obsidian]
  memoria:
    skill_id: "verify:check-citation"
    profile: memoria-peer-reviewer
    lane: verify
    mcp_tools:
      - obsidian.get_file_contents
      - obsidian.list_files
      - obsidian.search
      - obsidian.put_content
      - obsidian.append_content
      - pyzotero.get_references
      - pyzotero.get_citations
      - pyzotero.find_related
      - pyzotero.search_semantic_scholar
      - policy.check_permission
      - policy.complete_write
    write_scope: ["inbox/"]
    outputs: [flag]
---

# verify:check-citation

*(legacy name: `cite-check`, shipped inside `claim-checks`; load on disk as
`verify-check-citation`.)*

Answer one mechanical question about a draft or claim note: **does every citation
resolve, and does the cited work actually support the sentence that cites it?** You
contribute no judgment about whether the claim is *true* — that is the PI's call. The
check is **flag-only and never auto-fixes** the thing it inspects (the Peer-reviewer
writes only `inbox/` cards).

## Inputs

| Input | Required | Meaning |
| --- | --- | --- |
| target | yes | A draft (`projects/…`) or claim note path to check. |
| scope | no | `tokens-only` (skip claim-source matching) for a fast pre-export pass. |

## Procedure

1. **Extract** every citation token (`[@citekey]`) with a regex pass — deterministic.
2. **Resolve** each citekey against `.memoria/memoria.bib` and the corresponding paper
   note in `catalog/papers/` (vault reads via the `obsidian` skill). An unresolved
   citekey is a **critical finding**.
3. **Match claim to source** using embedding similarity (the shared `qmd` vector index)
   as a pre-filter, banded: **above ~0.75 auto-clean · below ~0.4 auto-fail · only the
   middle band goes to an LLM judge.** The bands keep the check reproducible; the judge
   is the single non-deterministic surface, bounded to the genuine ambiguity gap.
4. **Pull external citation context** only when needed (a cited source's own references
   or citing papers) via the `pyzotero` MCP's Semantic Scholar tools (`get_references`,
   `get_citations`, `find_related`, `search_semantic_scholar`) — never direct HTTP
   (`web`/`terminal` stay disabled).
5. **Report — gated.** Write ONE `flag` card per checked target to `inbox/`
   (finding-first, ADR-51): unresolved citekeys, auto-fails, and judge verdicts listed
   under the finding. Batch-shaped results stay one card, never N (ADR-54).

Per-band thresholds, failure modes, and false-positive handling:
`references/sub-checks.md` §1.

## Output contract

One `flag` card (schema `flag`): `finding` leads (the verdict is never assumed),
`agent_recommendation` ∈ `clean / issues-found / inconclusive`, `target` = the checked
path, `raised_by: memoria-peer-reviewer`. Your `clean` never substitutes for the PI's
approval (ADR-50).

## Honesty rules

- Mechanical-first, interpretive never: you report whether a citation resolves and
  supports, not whether the claim is right.
- Never edit the draft or the claim note — even for a trivially fixable typo'd citekey;
  the finding names it, the PI (or a delegated lane) fixes it.
- An `inconclusive` middle-band verdict is reported as inconclusive — never rounded up
  to clean because the rest of the draft looked fine.
- Missing-evidence findings are not yours to chase: hand them to `verify:card-gap`.
