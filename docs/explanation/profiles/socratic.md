---
topic: profiles
---

# Socratic — design summary

**Runtime contract.** Full prompt and operational details live at `.memoria/profiles/memoria-socratic/SOUL.md` in the starter vault.

## Mission

Socratic is the interlocutor for the human's thinking. It asks questions about a source, a claim, or a framing — the human answers (out loud, in their head, or in the conversation), arrives at a clearer understanding, and then writes the resulting note themselves, in their own words. The defining trait is **architectural write-denial**: Socratic has no path it can write to, not even scratch. The entire product is the conversation; the conversation's outputs live in the human's head and, eventually, in the claim note they author in a different profile.

## What this profile is not

- **Not Writer.** Writer drafts prose from evidence; Socratic asks questions to sharpen the human's framing before they write. They are sequential, not interchangeable: Socratic in the Discuss stage, Writer in the Draft stage. The most common failure mode for a question-asking AI is to summarize back what the user said as if it were the answer ("so what you're saying is X") — that performs the synthesis the human should do themselves. Socratic must not do that.
- **Not Mapper.** Mapper maps the corpus; Socratic engages with one source or claim at a time. Different scope, different abstraction.
- **Not a search agent.** Socratic doesn't fetch new context, doesn't run queries, doesn't propose links. It works strictly with what's in front of the human.

## Design decisions

- **`policy.allow.write: []` — the architectural wall.** The lane-override enforces an empty write list. There is no path Socratic can write to. This is profile-level enforcement, stricter than the skill-level restrictions used elsewhere. The protection is what makes Socratic safe to invoke from any device, including untrusted ones: there is nothing Socratic can corrupt by design.
- **`routing.invocation: interactive_only` — never queue-dispatched.** A cron entry that tried to schedule a Socratic card would result in a card that sits in `ready` forever. Socratic is reached only through synchronous human invocation (ACP pane, CLI). This prevents a misconfigured cron job from queueing background "thinking" — Socratic is for the human's *active* attention, never for delegation.
- **Generative method class, but write-denied.** Socratic is the only profile that is both LLM-required (open-ended conversation has no deterministic algorithm) and architecturally write-denied. The combination is intentional: the LLM's nondeterminism cannot corrupt canonical state because the LLM has no canonical state to write to. See [architecture/why-computational-methods.md](../architecture/why-computational-methods.md) for why this matters.
- **One frame per session.** When `lens-reading` loads with `mamykina-lens`, Socratic stays in that lens for the session. Switching lenses mid-session muddies whose questions are being asked. The human can start a new session for a different lens.

## Permissions and commands

Folder permission matrix lives in [profiles/README.md](../../reference/profile-matrices.md#folder-permission-matrix); the runtime contract lives in the SOUL.md. Notably brief on both fronts: Socratic has read access everywhere and write access nowhere.

## Related

- Workflows: [discuss](../../how-to/workflows/upstream/discuss.md) — the standard Socratic-in-the-loop pattern.
- Operations: [obsidian-plugins/required/agent-client.md](../../reference/plugins/agent-client.md) — Socratic is the default ACP agent, the persistent-pane case in the agent-client picker.
- Method class: [architecture/why-computational-methods.md](../architecture/why-computational-methods.md) — Socratic sits at the corner of "generative + write-denied," the architectural pattern that makes LLM nondeterminism safe.
- Architecture: [architecture/why-no-autonomous-synthesis.md](../architecture/why-no-autonomous-synthesis.md) — the same principle (humans write canonical content, agents help them think) applied profile-wide.
