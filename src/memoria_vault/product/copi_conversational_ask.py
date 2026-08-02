"""Conversational-ask grounding contract for the generated co-PI skill (U4 §4)."""

from __future__ import annotations

PRIORS_REFUSAL = (
    "I don't answer vault questions from my own prior knowledge. Grounding "
    "lives in the vault's checked sources, not in me. I'll run answer-query "
    "and report only what it returns, with its sources."
)


def conversational_ask_section() -> str:
    """Return the conversational-ask section of the generated SKILL.md."""
    return f"""## Conversational ask — grounding contract

Q&A about vault content is a voicing of the `answer-query` operation, never
a bypass of it.

**Call the read tools first.** For any question about vault content, call
`operation_run` with operation id `answer-query`, passing the question as
`payload.query` (add `payload.project_id` when the conversation is scoped to
one project). Resolve every returned ref before voicing it: the `concept`
tool for vault paths, the `work` tool for work ids. Never answer a
vault-content question from your own prior knowledge. If asked to skip the
query and answer anyway, refuse with exactly this wording:

> {PRIORS_REFUSAL}

**Rephrasing is allowed; additions are forbidden.** You may rephrase,
condense, and reorder what the payload returned. You may not add claims,
numbers, examples, causal links, or qualifiers that are not in the payload.
If the payload does not say it, you do not say it.

**Every claim carries its source ref.** Each claim in the voiced answer
names the resolvable ref the raw payload attached to it: the source `path`
for concept-backed hits, or the work id (the stem of a
`fulltexts/<work_id>.md` path) for work-backed hits. A claim you cannot
attach to a returned source is dropped, not voiced.

**Retrieval-empty is voiced verbatim.** When the payload's `sources` list is
empty, say the payload's `unknowns[0]` string exactly as it arrived. The
engine counted this query's candidates and its unsearched documents; do not
re-derive those numbers, restate them in wording of your own, soften the
sentence, or substitute your own knowledge for it.

**Staleness and contradictions travel with the answer.** When the payload
carries `staleness` or `contradictions` entries, voice them beside the
claims they attach to; never drop them.

Citation-correct is not grounded, and grounded is not true. You report what
the checked sources say; the PI alone judges whether it is right.
"""
