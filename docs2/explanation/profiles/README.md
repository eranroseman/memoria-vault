---
status: stub
---

# Profiles

> **Stub** — this section contains per-profile design explanations: mission, scope, what makes each profile distinct, and the key design choices.

## What goes here

One document per profile, explaining the *why* behind its design:

- **[librarian.md](librarian.md)** — discovery-optimistic, source-focused; why it's the system's entry point for new knowledge.
- **[mapper.md](mapper.md)** — read-only corpus surveyor; why it never writes canonical content.
- **[socratic.md](socratic.md)** — write-denied conversational profile; why zero write access is a feature.
- **[writer.md](writer.md)** — synthesis producer; why it drafts but cannot canonize.
- **[verifier.md](verifier.md)** — conservative citation checker; why it operates independently from the Writer.
- **[coder.md](coder.md)** — code artifact builder; why it's the one profile with a conditional autonomous loop.
- **[linter.md](linter.md)** — structural validator; why its default is dry-run.

## Overview

For the conceptual model of why seven specialists exist (instead of one generalist), see [why-specialist-profiles.md](../architecture/why-specialist-profiles.md).

For the permission matrices (lookup tables of who can write where), see [reference/profiles.md](../../reference/profiles.md).
