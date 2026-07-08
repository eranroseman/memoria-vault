---
title: Vocabulary
parent: Reference data model
nav_order: 3
grand_parent: Reference
---

# Vocabulary

`system/vocabulary.md` is the visible, PI-editable home for the controlled
values used by catalog Work `research_area`/`methodology` metadata and
claim-bearing note `topics`.

The shipped file lives at `src/memoria_vault/product/workspace_seed/system/vocabulary.md`.
In a runtime vault, edit `system/vocabulary.md` directly and keep note
frontmatter values in lockstep with it.

## Fields

| Field | Applies to | Source list |
| --- | --- | --- |
| `research_area` | SQLite catalog Work metadata | `system/vocabulary.md` -> `## research_area` |
| `methodology` | SQLite catalog Work metadata | `system/vocabulary.md` -> `## methodology` |
| `topics` | claim-bearing `note` Concepts | Draw from `## research_area` so notes and Works stay queryable together |

## Allowed values

The tables below mirror the shipped package-seed `system/vocabulary.md`. That
note is the single source of truth — if these tables and the shipped note ever
disagree, the shipped note wins. Each field takes **many values per note**.

### `research_area`

*What the work is about.* Claim-bearing note `topics` draw from this same list.
Kept to ~30 terms; consolidate drift at roughly fifty Works.

| Term | Definition |
| --- | --- |
| `personal-informatics` | Self-tracking systems and how people collect, reflect on, and act on data about their own behavior and health. |
| `mobile-health` | Health interventions and tools delivered through smartphones and mobile devices (mHealth). |
| `digital-mental-health` | Technology-delivered mental-health screening, support, and therapy. |
| `health-equity` | Fair access to and outcomes from health technology across populations; reducing disparities. |
| `patient-clinician-communication` | How technology mediates interaction between patients and their care providers. |
| `engagement-sustained-use` | Drivers of initial adoption and long-term continued use of health technology. |
| `chronic-disease-management` | Technology supporting the ongoing management of long-term conditions (diabetes, hypertension, and the like). |
| `behavior-change` | Designing systems to initiate and maintain changes in health behavior. |
| `llm-generative-ai-for-health` | Large language models and generative AI applied to health information, support, and care. |
| `patient-generated-data` | Health data created by patients outside clinical settings and its use in care. |
| `family-caregiver-health` | Technology supporting informal caregivers and family involvement in health. |
| `mobile-sensing` | Passive collection of behavioral and physiological signals from mobile-phone sensors. |
| `sociotechnical-systems` | The interplay of social context and technical systems in health settings. |
| `social-computing-for-health` | Social-media and collective-platform dynamics applied to health. |
| `conversational-agents` | Chatbots and voice agents for health support and interaction. |
| `community-health` | Technology serving population- and community-level health needs. |
| `digital-therapeutics` | Evidence-based software interventions that treat or manage a condition (DTx). |
| `wearable-sensing` | Body-worn devices that capture physiological and activity signals. |
| `aging` | Technology for older adults and age-related health needs. |
| `human-ai-interaction` | How people understand, trust, and collaborate with AI systems. |
| `online-health-communities` | Peer-support forums and groups where people discuss health. |
| `implementation-science` | How interventions are adopted, scaled, and sustained in real-world care settings. |
| `sensemaking` | How people interpret and construct understanding from health data and information. |
| `race-intersectionality` | How race and intersecting identities shape health-technology experiences and outcomes. |
| `cscw-collaborative-work` | Computer-supported cooperative work applied to health and care coordination. |
| `jitai` | Just-in-time adaptive interventions that deliver support tailored to a person's changing state and context. |
| `ema-self-report` | Ecological momentary assessment and self-report capture of in-the-moment experience. |

### `methodology`

*How the study was structured, and the techniques it used.* The schema carries study architecture and specific technique in this one field; both groups below are valid `methodology` values.

**Research architecture — how the study was structured**

| Term | Definition |
| --- | --- |
| `rct` | Randomized controlled trial. |
| `clinical-trial` | Interventional study registered or reported as a clinical trial. |
| `quasi-experiment` | Controlled comparison without randomization. |
| `observational` | Non-interventional study of naturally occurring data. |
| `field-study` | In-situ deployment study in a real-world setting. |
| `lab-experiment` | Controlled experiment conducted in a lab. |
| `survey-study` | Cross-sectional questionnaire-based study. |
| `qualitative` | Interview, ethnographic, or grounded inquiry as the primary architecture. |
| `design-science` | Build-and-evaluate of a novel artifact or system. |
| `formative-study` | Early needs-finding or exploratory design study. |
| `case-study` | In-depth study of one or a few instances. |
| `case-report` | Clinical report of one patient or a small case series. |
| `review` | Narrative or broad synthesis of prior work. |
| `systematic-review` | Structured synthesis of prior studies. |
| `meta-analysis` | Statistical pooling of results across studies. |
| `secondary-analysis` | New analysis of an existing dataset. |
| `dataset` | Dataset publication or data-resource paper. |

**Specific methods — the techniques used**

| Term | Definition |
| --- | --- |
| `semi-structured-interview` | Open-ended interviews around a guiding protocol. |
| `thematic-analysis` | Coding qualitative data into recurring themes. |
| `grounded-theory` | Building theory inductively from data. |
| `contextual-inquiry` | Observing and interviewing participants in their own setting. |
| `experience-sampling` | Repeated in-situ prompts capturing momentary experience. |
| `ecological-momentary-assessment` | Time- or event-sampled self-report in daily life. |
| `diary-study` | Participant-logged entries over a study period. |
| `co-design` | Designing artifacts together with stakeholders. |
| `usability-testing` | Observed task performance to surface interaction problems. |
| `think-aloud` | Participants verbalize thought while performing tasks. |
| `survey` | Structured questionnaire administered to a sample. |
| `regression` | Modeling outcomes as functions of predictors. |
| `mixed-effects-model` | Regression with fixed and random effects for nested data. |
| `log-analysis` | Analysis of system interaction logs. |
| `machine-learning` | Supervised or unsupervised modeling for prediction or clustering. |
| `nlp` | Computational analysis of text. |
| `content-analysis` | Systematic categorization of communication content. |
| `participant-observation` | Researcher embeds in the setting being studied. |
| `ab-test` | Randomized comparison of two variants in deployment. |

### `topics`

Claim-bearing notes only. Drawn from the `research_area` terms above so a note
and the Works it rests on share the same controlled values and surface together
in queries. Propose a new provisional term only when no `research_area` value
fits.

## Related

- How to edit the lists: [Manage vocabulary](../../how-to-guides/knowledge/manage-vocabulary.md)
- Why this exists: [Vocabulary discipline](../../explanation/knowledge/vocabulary-discipline.md)
- Frontmatter field grammar: [Frontmatter fields](frontmatter.md)
