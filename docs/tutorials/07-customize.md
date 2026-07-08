---
title: "07: Customize"
parent: Tutorials
nav_order: 7
---

# 07: Customize

Now that one loop works, make one small, reversible customization and confirm
that Memoria reads it back. We will change the workspace steering note, then
create one project that uses the new intent.

## Steps

**1. Read the current steering note.**

```bash
memoria steering show --workspace .
```

Notice that steering is workspace guidance, not a chat message. It lives with
the vault.

**2. Replace it with one concrete research focus.**

```bash
memoria steering edit --workspace . \
  --body "Focus this tutorial workspace on JITAI receptivity and participant burden."
```

Run the read command again:

```bash
memoria steering show --workspace .
```

You should see the new sentence. That is the first customization: durable
workspace intent.

**3. Create a second, narrower project.**

```bash
memoria new project "Burden follow-up" \
  --workspace . \
  --description "A follow-up question about participant burden in JITAIs."
```

Notice the difference: steering says what the workspace is about; the project
says what one piece of work is about.

**4. Check what changed.**

```bash
memoria workspace scan --workspace .
memoria status --workspace .
git status --short
```

The changed files should be ordinary workspace files. Nothing about this step
requires Obsidian, Zotero, or a live model provider.

## What you should have seen

- Customization starts with one durable file, not a new product path.
- Workspace steering and project scope are different levels of intent.
- The CLI remains the surface that reads, checks, and reports the change.

For optional setup, continue with [How-to guides](../how-to-guides/README.md).
