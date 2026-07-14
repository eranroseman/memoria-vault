---
title: Why the review gate is structural
parent: Boundaries
grand_parent: Design rationale
nav_order: 5
---

# Why the review gate is structural

Memoria's review gate is **structural**. Machine work can stage and check
material, but promotion to checked knowledge goes through the engine request
envelope and trusted-writer checks. PI attention and curation are recorded as
separate dispositions. The gate is not an advisory suggestion, a setting, or a
prompt instruction.

Promotion makes content consumable by checked-only readers: structural checks
passed and the required warrants resolve. It is not a claim that the PI approved
the content as true. The rule is **propose, not dispose**. Agents and operations
can stage proposals; the PI decides how attention items are handled.

---

## The default in the field: advisory review

Most contemporary multi-agent research systems use an LLM-based reviewer. The pattern: after a worker finishes, a reviewer model evaluates the output and either approves, requests revision, or escalates. The reviewer's verdict is factored into downstream processing — a high score moves the output forward; a low score triggers revision.

This is the advisory model. The reviewer advises; the system uses the advice to route the output. The human is in the loop only when they check the system.

Memoria rejects this model for synthesis. The reasoning follows from the specific failure mode that matters for knowledge work.

---

## The specific failure mode

Hallucinated citations and fabricated claims are not produced with visible uncertainty. They are emitted with high fluency and high confidence. A model that "confidently knows" a paper says something that the paper doesn't actually say does not signal that uncertainty — it asserts the claim fluently.

An advisory reviewer evaluating the same output faces the same problem: if the original agent hallucinated confidently, the reviewer may agree confidently. Two models with correlated errors produce a system that routes confidently wrong outputs forward.

This is not a fringe scenario — it is the dominant failure mode in AI-assisted citation work. Studies consistently find that LLMs cite papers for claims those papers don't make, and that LLM-based reviewers miss these errors at meaningful rates.

The structural gate exists because: **the outputs the gate needs to catch are precisely the ones a confident agent reviewer would approve**.

---

## Why structural, not prompt-based

The alternative to a structural gate is a prompt-based rule: "Always wait for human review before writing to canonical zones." This looks equivalent but isn't.

A prompt-based rule is subject to:

- **In-context instruction following**, which degrades at long context lengths.
- **Override by explicit later instruction**, such as "just move it forward this time."
- **Reasoning about exceptions**, where the agent argues to itself that this case is different.
- **Session restart**, where the instruction isn't carried forward.

A structural gate is code in the write path: the request envelope, trusted
writer, read barrier, and optional adapter policy hook. A machine path can
create an unchecked proposal, run declared checks, or ask for attention. It
cannot silently promote synthesis as checked knowledge. Optional adapters that
write around the engine are denied or audited by policy.

The practical difference: prompt discipline has a mean time to failure.
Structural enforcement does not consult context, reason about exceptions, or
degrade with session length. The engine materializes checked knowledge only when
required checks and warrants exist as recorded state. PI approval remains
separate attention/curation state, not the meaning of `check_status = checked`.

---

## The review state as structured data

Because review is structural rather than conversational, attention state is
queryable. The read API can ask "which items need action?" Dashboards can show
queue depth. WIP caps can apply back-pressure when done-awaiting-action grows too
large.

None of this is possible if review lives in comments, tags, or conversation. "The human acted on this" must be recorded state, not a convention.

The request/attention projection carries exactly this: awaiting action, acted, or archived. These are states in a state machine, not annotations, and they are separate from `check_status`.

---

## The agent verdict is not the review

The Peer-reviewer and the operations (the Linter, the sweeps) can attach a
machine recommendation to a request or attention item. This recommendation is
separate from the review decision:

- **The recommendation can be wrong.** A clean Peer-reviewer report doesn't mean the draft is good; it means the citations trace and the schema is valid. The human judgment about whether the synthesis is correct, useful, and worth keeping is separate.
- **They can disagree.** The Peer-reviewer reports clean; the human reads the draft and rejects it. The separation makes this case coherent — there's no confusion about which verdict counts.
- **The human's decision is the gate.** The agent verdict informs; it never replaces.

---

## The trade-off

The structural gate makes the human a bottleneck. Review does not auto-scale. If
the PI does not act, attention items pile up and WIP pressure slows new work.

That visible slowness is deliberate. A full review queue should slow the system
rather than silently redefine "reviewed" as "agent finished."

This is the design. The human must stay in contact with what agents produce. A
system that can move synthesis to canonical without human attention has removed
the guarantee that makes the vault trustworthy.

An advisory gate would reduce review time by spending the structural guarantee:
machine output is never self-disposing.

---

## Related

**Explanation**

- Why operation postures support this: [Why operation postures](why-operation-postures.md)
- Why the vault won't automate synthesis: [Why Memoria doesn't pursue full autonomy](why-not-autonomous.md)
- How request review state works: [Request states and the review gate](../../execution/control-plane/states.md)
- What the gate enforces at the synthesis boundary: [Promotion and the write boundary](../../knowledge/promotion-and-gated-zones.md)

**Reference**

- Runtime and optional-adapter enforcement details: [Policy gate](../../../reference/control-and-policy/policy-mcp.md) · [Memory substrates](../../../reference/pipelines-and-io/memory-substrates.md) (audit log)
- Request and attention state: [Request states and the review gate](../../execution/control-plane/states.md)
