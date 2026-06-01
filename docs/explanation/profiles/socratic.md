
# The Socratic profile

The Socratic profile is the interlocutor for the human's thinking. It asks questions about a source, a claim, or a framing — the human answers, arrives at a clearer understanding, and then writes the resulting note themselves, in their own words. Its defining constraint is **architectural write-denial**: Socratic has no path it can write to, not even scratch. The entire product of a Socratic session is the conversation; the outputs live in the human's head and, eventually, in the claim note they author in a different profile.

---

## Why it's designed this way

**Write-denial is architectural, not conventional.** The lane policy enforces an empty write list at the policy MCP layer — there is no path Socratic can write to. This is stricter than the skill-level restrictions used by other profiles. The protection is what makes Socratic safe to invoke from any device, including untrusted ones: there is nothing it can corrupt by design.

**`interactive_only` routing — never queue-dispatched.** A cron entry that tried to schedule a Socratic card would produce a card that sits in `ready` forever. Socratic is reached only through synchronous human invocation. This prevents a misconfigured scheduled task from queueing background "thinking" — Socratic is for the human's active attention, never for delegation.

**Generative but write-denied — an intentional combination.** Socratic is the only profile that is both LLM-required (open-ended conversation has no deterministic algorithm) and architecturally write-denied. The LLM's nondeterminism cannot corrupt canonical state because the LLM has no canonical state to write to. This is the pattern that makes Socratic safe to give genuine conversational latitude — the freedom is bounded by the write wall, not by a stricter prompt.

**One frame per session.** When `lens-reading` loads with a named lens (e.g., `mamykina-sensemaking`), Socratic stays in that frame for the session. Switching frames mid-session muddies whose questions are being asked. A new session for a different lens preserves the discipline.

---

## What Socratic is not

**Not Writer.** Writer drafts prose from evidence; Socratic asks questions to sharpen the human's thinking *before* they write. They are sequential, not interchangeable — Socratic belongs in the Discuss stage, Writer in the Draft stage. The most common failure mode for a question-asking AI is summarizing back what the user said as if it were an answer ("so what you're saying is X"). Socratic must not do this — that move performs the synthesis the human should do themselves.

**Not Mapper.** Mapper surveys the whole corpus; Socratic engages with one source or one claim at a time. Different scope, different abstraction level.

**Not a search agent.** Socratic doesn't fetch new context, run queries, or propose links. It works strictly with what is in front of the human during the session.

---

## Related

- The profile this feeds into: [Writer](writer.md)
- The workflow Socratic anchors: [discuss a paper](../../how-to-guides/sources/discuss-a-paper.md)
- Why synthesis belongs to the human: [why not autonomous](../architecture/why-not-autonomous.md)
- Dashboard that surfaces the Socratic queue: [discuss-queue](../dashboards/discuss-queue.md)
