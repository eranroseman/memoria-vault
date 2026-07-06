---
title: Why the write half is bounded
parent: Design Book
grand_parent: Developers
nav_order: 14
---

# Why the write half is bounded

Memoria writes plain files first: `outline.md`, `draft.md`, and unchecked notes.
That boundary keeps synthesis useful without making the engine a truth oracle.

The engine can propose a slice, compose draft text, verify evidence markers,
and refuse unsafe export. It does not decide that a claim is true, promote a
draft passage to checked knowledge, run analysis code, or hide uncertainty
behind a score.

The constraint is deliberate: text output is valuable only when every claim can
be traced, reviewed, and either exported cleanly or refused clearly.
