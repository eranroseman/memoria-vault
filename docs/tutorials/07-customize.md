---
title: "07: Customize"
parent: Tutorials
nav_order: 7
---

# 07: Customize

Now that one loop works, tune what the workspace pursues and confirm that
Memoria reads it back. Effective steering is derived from active projects,
hubs, and unresolved question notes. `steering.md` is a thin override with two
levers: **Watch for** terms that fit no artifact yet, and **Muted** terms to
suppress. This chapter exercises a new project, a watch entry, and a mute
entry.

## Steps

**1. Read the effective steering.**

```bash
memoria steering show --workspace .
```

Every effective steering token renders with its provenance: the project, hub,
question note, or watch entry that contributed it. In this workspace, tokens
already trace to the tutorial project from Tutorial 04. They are derived from
the work you keep active, not authored as steering prose.

**2. Create a second, narrower project.**

```bash
memoria new project "Burden follow-up" \
  --workspace . \
  --description "A follow-up question about participant burden in JITAIs."
```

Run the read command again:

```bash
memoria steering show --workspace .
```

New tokens appear with the new project as their provenance. Framing a project
is the main steering move; an archived project stops contributing.

**3. Add a Watch-for entry.**

Some terms are worth pursuing before any project, hub, or question note exists
for them. Put those in the override file's **Watch for** section. Replace the
override with one watch entry:

```bash
mkdir -p tmp/tutorial
cat > tmp/tutorial/steering.md <<'EOF'
---
type: system
title: Steering
---

# Steering

## Watch for

- ecological momentary assessment

## Muted
EOF
memoria steering edit --workspace . --file tmp/tutorial/steering.md
memoria steering show --workspace .
```

The watch entry's tokens now appear in effective steering with `watch`
provenance, so they can steer discovery before an artifact expresses them.

**4. Mute a term.**

Muting subtracts tokens from effective steering, even when an active project
contributes them. Rewrite the override with a **Muted** entry:

```bash
cat > tmp/tutorial/steering.md <<'EOF'
---
type: system
title: Steering
---

# Steering

## Watch for

- ecological momentary assessment

## Muted

- burden
EOF
memoria steering edit --workspace . --file tmp/tutorial/steering.md
memoria steering show --workspace .
```

The token from "Burden follow-up" is gone from the effective set. A discovery
candidate matching only that term routes to exploration rather than the ranked
list; one that also matches a surviving token still ranks. A multi-word mute
entry suppresses each word separately, so keep mute entries narrow.

**5. Check what changed.**

```bash
memoria workspace scan --workspace .
memoria status --workspace .
git status --short
```

The changed files are ordinary workspace files. Nothing in this step requires
Obsidian, Zotero, or a live model provider.

## What you should have seen

- Steering is derived: active projects, hubs, and unresolved question notes
  aim the system; archiving a project lets that topic go quiet.
- `steering.md` is a thin override for watch and mute terms, not an essay about
  your research.
- `memoria steering show` is the read surface for each effective token and its
  provenance.

For optional setup, continue with [How-to guides](../how-to-guides/README.md).
