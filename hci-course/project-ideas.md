# HCI course — Memoria research project ideas

Date: 2026-07-10. For the HCI research-methods course (next semester):
proposal → progress update → final paper + presentation. Project types the
course accepts: (1) innovative interaction / simple application, (2)
innovative use of an existing technology, (3) an HCI research question,
(4) systematic literature review.

**Standing assumption (owner, 2026-07-10):** everything decided in the
design dossier (`workflow-audit/` on this branch) — the roadmap through
Tier 3, the reactive substrate, the view-spec renderer, the canvas
program, the empirical-plan instrumentation — is implemented before the
semester starts. Each idea below also names its fallback if that slips.

**Positionality note (applies to every idea):** the student is the tool's
author. First-person designs embrace this (it is the method, declared);
participant studies disclose it and use blind rating / preregistered
measures to contain it. Start the ethics process at proposal time, not at
the progress report.

Companion documents: `workflow-audit/roadmap.md` (items 12, 14, 15),
`workflow-audit/user-workflow.md`, `workflow-audit/product-statement.md`,
`releases/0.1.0-beta.1/empirical-use-action-plan.md` (pre-registered
decision rules referenced below).

---

## The six ideas

### 1. Evaluating the grounding interrogation (course type 1 or 3)

**RQ:** Which Toulmin-structured interrogation moves — grounds, warrant,
backing, qualifier, rebuttal questions — cause researchers to revise or
strengthen claims, and at what cost in time and annoyance?

**Method (system built):** controlled evaluation of the real Tier 3
engine-authored interrogation vs a generic-assistant baseline; 8–12
participants each bring one claim from their own work or digest a short
provided paper; measure claim revisions, evidence lookups, question-type →
revision mapping, perceived value vs intrusiveness.
**Fallback (Tier 3 slips):** Wizard-of-Oz with a scripted wizard playing
the engine — a respectable plan B to name explicitly in the proposal.

**Feeds Memoria:** roadmap item 14's question taxonomy — which question
types to generate first. **Anchors:** WoZ methods classics + CHI 2026 WoZ
systematic review; ArgueTutor; Persua; Tankelevitch et al. (metacognition).

### 2. Verdict badges and appropriate reliance (course type 3)

**RQ:** Does displaying epistemic status (checked / unchecked /
quarantined) on notes change whether knowledge workers verify before
reusing content — calibrated reliance, not blind trust?

**Method:** between-subjects controlled task in a seeded vault salted with
planted errors (the seeded-error battery as study materials); memo-writing
task; measure citations of unchecked/wrong claims, verification actions,
confidence calibration. With item 12 built, use the real badge layer;
fallback: fake badges with a CSS snippet + `cssclasses` in stock Obsidian.

**Feeds Memoria:** the badge layer and loudness policy (item 12); the
"verdicts render only in the plugin" ring boundary gets human-side
evidence. **Anchors:** Buçinca 2021; Vasconcelos 2023; Kim CHI 2025;
Schwarz & Morris 2011; RELIC.

### 3. Interview-sealed digest vs free summary (course type 3)

**RQ:** Does forcing engagement before sealing a digest (Memoria's
interview gate) improve retention and integration vs accepting an
auto-digest — the generation effect applied to LLM summarization?

**Method:** within-subjects, counterbalanced, two papers per participant;
delayed recall + use-in-writing task a week later. Real gate once built;
digest quality held constant across conditions (the confound to control).
A null result is as valuable as a positive one — say so in the proposal.

**Feeds Memoria:** validates (or challenges) the product's most
opinionated gate. **Anchors:** Slamecka & Graf 1978; Lee CHI 2025;
Paper Plain; Traceable Texts; Tankelevitch CHI 2024.

### 4. Outline composition: list vs canvas (course type 2)

**RQ:** For arranging claims into an argument outline, does spatial
arrangement (Obsidian canvas) beat linear list reordering — and for whom?

**Method:** within-subjects, counterbalanced, entirely in stock Obsidian:
markdown-list reorder vs claim file-nodes on a `.canvas` (with the canvas
program built, the real generated Toulmin `argument.canvas` supplies the
spatial condition's material). Blind-rated outline quality (rubric +
second rater), revision counts, NASA-TLX, preference.

**Feeds Memoria:** this study's decision rule is already pre-registered —
the "Canvas authoring (scoped ADR-103 reopen)" row in the empirical plan.
The course project IS the evidence gate. **Anchors:** Kellogg 1988;
Kirsh 1995; VIKI / information triage; Sensecape; Graphologue; DirectGPT.

### 5. Systematic literature review: why argument-structured interfaces fail, and whether LLMs change the equation (course type 4)

**RQ:** Across ~35 years of argumentation tools (gIBIS 1988 → LLM argument
mining 2026), who pays the formalization cost, and does shifting the
authorship of structure from human to machine change adoption?

**Method:** PRISMA-style review; code each system by structure-author
(human / machine / mixed), friction findings, adoption outcome.

**Feeds Memoria:** the warrant-ontology open question — the dossier's
hybrid recommendation ("machine proposes structure, researcher disposes")
is a direct answer to Shipman & Marshall's formality critique; the review
tests it against the literature's failure modes. No participants, no
ethics review, no build dependency — the safe fallback. The reading list
doubles as the course's paper-presentation assignments.

### 6. A thousand papers move in: instrumented first-person study (course type 3; first-person methods) ⭐ primary recommendation

**RQ:** What actually happens — triage load, staleness pain, trust
formation, workflow displacement — when a researcher's entire Zotero
library enters a grounding-gated vault?

**Method:** instrumented autoethnography riding the empirical plan:
`empirical_event.v1` disposition telemetry + the five-line diary, with
null-workflow baseline weeks for an ABA-style contrast. The course
timeline maps one-to-one onto the plan: proposal = Phase 0 complete
(license gate passed, baseline recorded); progress update = Phase 1's
staged 10→100→1000 import with per-stage metrics; final paper = Phase 2's
dogfood loops. The course project and the product's evidence are the same
artifact.

**Check early:** whether the instructor accepts first-person methods —
the anchors below show they pass peer review at CHI/DIS/NordiCHI, but
some experimentalists remain skeptical. **Anchors:** O'Kane 2014; Lucero
2018; Rapp 2018; Kaltenhauser CHI 2024 review; TummyTrials; SleepBandits;
Li 2010; Epstein 2020; INTERACT 2025 Obsidian study; NordiCHI 2024 LLM
autoethnography.

### Recommendation

**Primary: #6** (maximal dual-use; instrumentation ships pre-semester;
timeline maps onto the course's checkpoints). **Alternative: #1** as a
real-system evaluation — the classic build-then-evaluate systems-paper
shape — degrading gracefully to WoZ. **Fallback: #5** (no participants,
no build, feeds the dossier's biggest open design question).

---

## Verified literature (two research passes, 2026-07-10)

All entries below were verified to exist (title, authors, venue) against
the ACM DL, Springer, arXiv, ScienceDirect, or APA PsycNet by the
research agents. Caveats retained from the verification pass: ArguMentor,
the argument-mining survey, and "Conversations in Space" are arXiv
preprints without confirmed venue acceptance; the CHI 2026 author lists
came from search snippets (ACM DL blocks anonymous fetch); the 2026
Elsevier venue name is inferred from the article PII/ISSN.

### A. Appropriate reliance / trust calibration on AI

- Buçinca, Z., Malaya, M. B., & Gajos, K. Z. (2021). To Trust or to
  Think: Cognitive Forcing Functions Can Reduce Overreliance on AI in
  AI-assisted Decision-making. PACM HCI 5(CSCW1), 188. **Seminal
  anchor** — cognitive forcing functions.
  <https://dl.acm.org/doi/10.1145/3449287>
- Vasconcelos, H., Jörke, M., Grunde-McLaughlin, M., Gerstenberg, T.,
  Bernstein, M. S., & Krishna, R. (2023). Explanations Can Reduce
  Overreliance on AI Systems During Decision-Making. PACM HCI 7(CSCW1),
  129. Overreliance as a strategic cost-benefit choice (N=731).
  <https://dl.acm.org/doi/10.1145/3579605>
- Prabhudesai, S., Yang, L., Asthana, S., Huan, X., Liao, Q. V., &
  Banovic, N. (2023). Understanding Uncertainty: How Lay Decision-makers
  Perceive and Interpret Uncertainty in Human-AI Decision Making.
  IUI '23, 379–396. How displayed uncertainty changes reliance.
  <https://dl.acm.org/doi/10.1145/3581641.3584033>
- Kim, S. S. Y., Vaughan, J. W., Liao, Q. V., Lombrozo, T., &
  Russakovsky, O. (2025). Fostering Appropriate Reliance on Large
  Language Models: The Role of Explanations, Sources, and
  Inconsistencies. CHI '25. Sources reduce reliance on wrong answers;
  explanations increase reliance on everything.
  <https://dl.acm.org/doi/10.1145/3706598.3714020>
- de Jong, S., Paananen, V., Tag, B., & van Berkel, N. (2025). Cognitive
  Forcing for Better Decision-Making: Reducing Overreliance on AI Systems
  Through Partial Explanations. PACM HCI 9(2), CSCW048.
  <https://dl.acm.org/doi/10.1145/3710946>

### B. Epistemic status / provenance indicators in interfaces

- Schwarz, J., & Morris, M. R. (2011). Augmenting Web Pages and Search
  Results to Support Credibility Assessment. CHI '11, 1245–1254.
  **Seminal anchor** — pre-LLM credibility-cue template.
  <https://dl.acm.org/doi/10.1145/1978942.1979127>
- Hoque, M. N., et al. (2024). The HaLLMark Effect: Supporting Provenance
  and Transparent Use of Large Language Models in Writing with
  Interactive Visualization. CHI '24. Human-vs-LLM contribution
  provenance in documents.
  <https://dl.acm.org/doi/10.1145/3613904.3641895>
- Cheng, F., Zouhar, V., Arora, S., Sachan, M., Strobelt, H., &
  El-Assady, M. (2024). RELIC: Investigating Large Language Model
  Responses using Self-Consistency. CHI '24. Claim-level reliability UI.
  <https://dl.acm.org/doi/10.1145/3613904.3641904>
- Laban, P., Vig, J., Hearst, M. A., Xiong, C., & Wu, C.-S. (2024).
  Beyond the Chat: Executable and Verifiable Text-Editing with LLMs.
  UIST '24. InkSync's warn–verify–audit pipeline.
  <https://dl.acm.org/doi/10.1145/3654777.3676419>
- Kambhamettu, H., Hwang, A., Laban, P., & Head, A. (2026). Attribution
  Gradients: Incrementally Unfolding Citations for Critical Examination
  of Attributed AI Answers. CHI '26 (camera-ready; arXiv:2510.00361 is
  the stable link). <https://arxiv.org/abs/2510.00361>

### C. AI reading assistance: engagement, retention, skill

- Slamecka, N. J., & Graf, P. (1978). The Generation Effect: Delineation
  of a Phenomenon. J. Exp. Psychology: Human Learning and Memory 4(6),
  592–604. **Seminal anchor.**
  <https://doi.org/10.1037/0278-7393.4.6.592>
- Lee, H.-P., Sarkar, A., Tankelevitch, L., Drosos, I., Rintel, S.,
  Banks, R., & Wilson, N. (2025). The Impact of Generative AI on Critical
  Thinking: Self-Reported Reductions in Cognitive Effort and Confidence
  Effects From a Survey of Knowledge Workers. CHI '25.
  <https://dl.acm.org/doi/10.1145/3706598.3713778>
- Tankelevitch, L., Kewenig, V., Simkute, A., Scott, A. E., Sarkar, A.,
  Sellen, A., & Rintel, S. (2024). The Metacognitive Demands and
  Opportunities of Generative AI. CHI '24 (Best Paper).
  <https://dl.acm.org/doi/10.1145/3613904.3642902>
- August, T., Wang, L. L., Bragg, J., Hearst, M. A., Head, A., & Lo, K.
  (2023). Paper Plain: Making Medical Research Papers Approachable to
  Healthcare Consumers with Natural Language Processing. TOCHI 30(5), 74.
  <https://dl.acm.org/doi/10.1145/3589955>
- Kambhamettu, H., Flores, J., & Head, A. (2025). Traceable Texts and
  Their Effects: A Study of Summary-Source Links in AI-Generated
  Summaries. CHI EA '25 (full system paper: arXiv:2409.13099).
  <https://dl.acm.org/doi/10.1145/3706599.3719830>

### D. Argument mapping, Toulmin interfaces, formality friction

- Shipman, F. M., III, & Marshall, C. C. (1999). Formality Considered
  Harmful: Experiences, Emerging Themes, and Directions on the Use of
  Formal Representations in Interactive Systems. CSCW (journal) 8(4),
  333–352. **The classic** on formalization rejection.
  <https://link.springer.com/article/10.1023/A:1008716330212>
- Conklin, J., & Begeman, M. L. (1988). gIBIS: A Hypertext Tool for
  Exploratory Policy Discussion. CSCW '88, 140–152.
  <https://dl.acm.org/doi/10.1145/62266.62278>
- Kirschner, P. A., Buckingham Shum, S. J., & Carr, C. S. (eds.) (2003).
  Visualizing Argumentation: Software Tools for Collaborative and
  Educational Sense-Making. Springer.
  <https://link.springer.com/book/10.1007/978-1-4471-0037-9>
- Suthers, D. D. (2003). Representational Guidance for Collaborative
  Inquiry. In Arguing to Learn. Springer, 27–46.
  <https://link.springer.com/chapter/10.1007/978-94-017-0781-7_2>
- Wambsganss, T., Küng, T., Söllner, M., & Leimeister, J. M. (2021).
  ArgueTutor: An Adaptive Dialog-Based Learning System for Argumentation
  Skills. CHI '21. <https://dl.acm.org/doi/10.1145/3411764.3445781>
- Xia, M., Zhu, Q., Wang, X., Nie, F., Qu, H., & Ma, X. (2022). Persua:
  A Visual Interactive System to Enhance the Persuasiveness of Arguments
  in Online Discussion. PACM HCI 6(CSCW2), 319.
  <https://dl.acm.org/doi/10.1145/3555210>
- Pitre, P., & Luther, K. (2024). ArguMentor: Augmenting User Experiences
  with Counter-Perspectives. arXiv:2406.02795. **Preprint — verify
  acceptance before citing as published.**
  <https://arxiv.org/abs/2406.02795>
- Large Language Models in Argument Mining: A Survey. (2025).
  arXiv:2506.16383. **Preprint.** <https://arxiv.org/html/2506.16383v4>
- Mitigating interpersonal uncertainty in collaborative argumentation:
  Using LLMs as scaffolds… in CSCL. (2026). Elsevier (venue inferred from
  PII/ISSN).
  <https://www.sciencedirect.com/science/article/abs/pii/S0023969026000093>

### E. Spatial vs linear arrangement for sensemaking and writing

- Kirsh, D. (1995). The Intelligent Use of Space. Artificial Intelligence
  73(1–2), 31–68. <https://dl.acm.org/doi/10.1016/0004-3702(94)00017-U>
- Marshall, C. C., Shipman, F. M., III, & Coombs, J. H. (1994). VIKI:
  Spatial Hypertext Supporting Emergent Structure. ECHT '94, 13–23.
  <https://www.semanticscholar.org/paper/76dba0d2a151e248c33c54a94b64d7157932df0e>
- Marshall, C. C., & Shipman, F. M., III (1997). Spatial Hypertext and
  the Practice of Information Triage. Hypertext '97, 124–133.
  <https://dl.acm.org/doi/10.1145/267437.267451>
- Kellogg, R. T. (1988). Attentional Overload and Writing Performance:
  Effects of Rough Draft and Outline Strategies. JEP:LMC 14(2), 355–365.
  <https://psycnet.apa.org/doiLanding?doi=10.1037%2F0278-7393.14.2.355>
- Suh, S., Min, B., Palani, S., & Xia, H. (2023). Sensecape: Enabling
  Multilevel Exploration and Sensemaking with Large Language Models.
  UIST '23. <https://dl.acm.org/doi/10.1145/3586183.3606756>
- Jiang, P., Rayan, J., Dow, S. P., & Xia, H. (2023). Graphologue:
  Exploring Large Language Model Responses with Interactive Diagrams.
  UIST '23. <https://dl.acm.org/doi/10.1145/3586183.3606737>
- Masson, D., Malacria, S., Casiez, G., & Vogel, D. (2024). DirectGPT: A
  Direct Manipulation Interface to Interact with Large Language Models.
  CHI '24. <https://dl.acm.org/doi/10.1145/3613904.3642462>
- Suh, S., Chen, M., Min, B., Li, T. J.-J., & Xia, H. (2024). Luminate:
  Structured Generation and Exploration of Design Space with LLMs for
  Human-AI Co-Creation. CHI '24.
  <https://dl.acm.org/doi/10.1145/3613904.3642400>
- Amin, R. M., Adatepe, A., Fernandes, D., Buschek, D., & Butz, A.
  (2026). Conversations in Space: Structuring Non-Linear LLM Interactions
  on a Canvas. arXiv:2605.15848. **Preprint.**
  <https://arxiv.org/abs/2605.15848>

### F. Wizard-of-Oz methods (still current in the LLM era)

- Dahlbäck, N., Jönsson, A., & Ahrenberg, L. (1993). Wizard of Oz
  Studies — Why and How. Knowledge-Based Systems 6(4), 258–266.
  <https://www.ida.liu.se/~arnjo82/papers/kbs.pdf>
- Riek, L. D. (2012). Wizard of Oz Studies in HRI: A Systematic Review
  and New Reporting Guidelines. J. Human-Robot Interaction 1(1), 119–136.
  <https://dl.acm.org/doi/10.5898/JHRI.1.1.Riek>
- Hu, S., et al. (2023). Wizundry: A Cooperative Wizard of Oz Platform
  for Simulating Future Speech-based Interfaces with Multiple Wizards.
  PACM HCI 7(CSCW1). <https://dl.acm.org/doi/10.1145/3579591>
- Fang, J., et al. (2024). On LLM Wizards: Identifying Large Language
  Models' Behaviors for Wizard of Oz Experiments. IVA '24.
  <https://dl.acm.org/doi/10.1145/3652988.3673967>
- Yang, R., et al. (2026). Mapping the Wizards' Path: A Systematic Review
  of Wizard-of-Oz in HCI. CHI '26. (Author list from search snippet.)
  <https://dl.acm.org/doi/10.1145/3772318.3791174>
- Wen, R., et al. (2026). AI of Oz: Enhancing Wizard of Oz Studies in HCI
  with AI Assistance for Human Moderation. CHI '26.
  <https://dl.acm.org/doi/10.1145/3772318.3791324>

### G. First-person and self-study methods; PKM studies

- O'Kane, A. A., Rogers, Y., & Blandford, A. E. (2014). Gaining Empathy
  for Non-routine Mobile Device Use through Autoethnography. CHI '14.
  <https://dl.acm.org/doi/10.1145/2556288.2557179>
- Lucero, A. (2018). Living Without a Mobile Phone: An Autoethnography.
  DIS '18. <https://dl.acm.org/doi/abs/10.1145/3196709.3196731>
- Rapp, A. (2018). Autoethnography in Human-Computer Interaction: Theory
  and Practice. In New Directions in Third Wave HCI, Vol. 2. Springer.
  <https://link.springer.com/chapter/10.1007/978-3-319-73374-6_3>
- Kaltenhauser, A., Stefanidi, E., & Schöning, J. (2024). Playing with
  Perspectives and Unveiling the Autoethnographic Kaleidoscope in HCI.
  CHI '24. <https://dl.acm.org/doi/10.1145/3613904.3642355>
- Karkar, R., et al. (2017). TummyTrials: A Feasibility Study of Using
  Self-Experimentation to Detect Individualized Food Triggers. CHI '17.
  <https://dl.acm.org/doi/abs/10.1145/3025453.3025480>
- Daskalova, N., et al. (2020). SleepBandits: Guided Flexible
  Self-Experiments for Sleep. CHI '20.
  <https://dl.acm.org/doi/abs/10.1145/3313831.3376584>
- Li, I., Dey, A., & Forlizzi, J. (2010). A Stage-Based Model of Personal
  Informatics Systems. CHI '10.
  <https://dl.acm.org/doi/10.1145/1753326.1753409>
- Epstein, D. A., et al. (2020). Mapping and Taking Stock of the Personal
  Informatics Literature. PACM IMWUT 4(4), 126.
  <https://dl.acm.org/doi/10.1145/3432231>
- How People Manage Knowledge in Their "Second Brains": A Case Study with
  Industry Researchers Using Obsidian. (2025). INTERACT 2025, Springer
  LNCS (arXiv:2509.20187).
  <https://link.springer.com/chapter/10.1007/978-3-032-05008-3_15>
- In a Quasi-Social Relationship With ChatGPT: An Autoethnography on
  Engaging With Prompt-Engineered LLM Personas. (2024). NordiCHI '24.
  <https://dl.acm.org/doi/abs/10.1145/3679318.3685501>
