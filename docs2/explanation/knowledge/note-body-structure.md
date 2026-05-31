# Note body structure

What goes inside the three most important note types — paper-notes, claim-notes, and MOCs — and why each section exists. For the frontmatter fields see [reference/note-types.md](../../reference/note-types.md); this document covers the *body*.

---

## Paper-note body

A paper-note has six body sections. The Librarian populates three at ingest; you fill the remaining three at triage.

**Sections the Librarian populates at ingest:**

`## Cites (in vault)` — papers this note cites that are already in your vault, linked by citekey. These are proposals; review them at triage.

`## Cited by (in vault)` — vault papers that cite this one. Same caveat.

`## Discover candidates` — related papers flagged by the Librarian's citation graph and semantic search for your review. Each candidate shows a brief reason ("cited by three of your existing notes," "0.87 semantic similarity to mamykina2010sense"). Review and add the useful ones to Zotero.

**Sections you fill at triage:**

`## Summary` — five prompts, in order:
1. The thesis in one sentence — the strongest claim the paper makes
2. The research question or design challenge the paper addresses
3. Key methods or design choices (what makes this study what it is, not just what it found)
4. Key findings (what you will actually cite)
5. Relation to your project — why this paper matters to what you are building

These are the most important part of a paper-note. In six months, when you need to cite this paper in a draft, the Summary is what you will read. If it is empty or vague, you will have to re-read the paper.

`## Critique and questions` — your critical response: what is missing, what is methodologically weak, what you would push back on. This is where a literature note earns its place in a knowledge system rather than a reading list. A paper note without critique is a summary, not synthesis.

`## Open questions` — what this paper raises but does not answer. These feed the `open-questions` dashboard, which surfaces them for research planning.

---

## Claim-note body

A claim-note has three required sections and one optional.

**Required:**

`## Claim` — the single durable idea, stated in one sentence. If you need two sentences, split the note. This section is usually the same as the note title, stated with slightly more context.

`## Evidence and argument` — why you believe the claim: supporting sources (citekeys), key findings from those sources, and any tension with alternative views. This is where the intellectual work goes. A claim note without evidence is an assertion; a claim note with citekeys is an argument.

`## Connections` — links to related claim notes: notes this one supports, notes this one contradicts, notes this one extends or qualifies. This section is what builds the knowledge graph. A claim note with no connections has not made it into the system.

**Optional:**

`## Open questions` — what this claim does not resolve; where synthesis should go next.

---

## MOC body

Each MOC answers three questions. Structure the body around them.

**1. What is this area about?** (one paragraph) — the scope and frame of the cluster. What kinds of notes belong here, and what kinds don't. This is not a definition; it is the lens through which you are looking at the topic.

**2. What belongs here right now?** (curated note list with brief annotations) — a selective list of the most important member notes, each with a one-sentence annotation explaining why it matters to the cluster. Do not list every note — curate. The Dataview query below handles volume; the static list handles meaning.

Include a live Dataview query for the fast-changing parts:

```dataview
TABLE file.link AS Note, maturity, lifecycle
FROM "30-synthesis/01-claims"
WHERE contains(moc, this.file.link)
SORT maturity DESC
```

**3. What needs review, synthesis, or splitting?** — open questions the cluster raises, thin sub-topics, claims that have no counterpart yet, branches that may have grown large enough to become their own child MOC. This section is what makes a MOC useful for planning rather than just navigation.

Keep the static sections scannable in 30 seconds. The Dataview queries handle scale.

---

## What makes the distinction matter

The note types exist because they answer different questions:

| Note type | Question answered | Written by |
| --- | --- | --- |
| `paper-note` | What does this source say? | Librarian (skeleton) + human (synthesis sections) |
| `claim-note` | What do I think, and why? | Human only |
| `moc` | What is known in this cluster, and how does it connect? | Human only |

Mixing these produces notes that are useful for neither purpose. A paper note that contains your personal claims is a hybrid you cannot cite or link reliably. A claim note that summarizes a paper rather than stating your own claim is not a claim note.

---

## Questions to ask during synthesis

These questions help identify whether a reading session should generate a claim note and which existing note it connects to:

1. What is the strongest claim this paper makes?
2. What changes in my current understanding if this claim is true?
3. Which existing claim note does this support, contradict, or extend?
4. Is this evidence, theory, method, a contradiction, or an implication?
5. Does this belong in a new claim note or strengthen an existing one?

A literature note should generate at most 2–3 claim notes. More than that usually means the reading session was a summary pass rather than a synthesis pass.
