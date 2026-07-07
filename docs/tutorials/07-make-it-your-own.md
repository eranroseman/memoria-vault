---
title: "Tutorial 07: Make it your own"
parent: Tutorials
nav_order: 7
---

# Tutorial 07: Make it your own

After the first loop works, customize only the pieces that reduce real friction:
provider config, vocabulary, steering, and optional editor/reference-manager
adapters.

## Steps

**1. Set provider config only where you need live model work.**

Runner providers live in `.memoria/config/providers.yaml`; secrets stay in
environment variables named by that config. Check the runner before using live
mode:

```bash
memoria doctor --workspace . --check runner --provider gateway
memoria eval select-models --workspace . --mode live
```

**2. Keep vocabulary deliberate.**

```bash
memoria vocab list --workspace .
memoria vocab add --workspace . topics jitai
memoria vocab rename --workspace . topics old-term new-term
```

Vocabulary changes affect search, gap analysis, and project slices. Rename or
merge terms instead of letting spelling variants accumulate.

**3. Put project-level intent in steering and projects.**

```bash
memoria steering show --workspace .
memoria steering edit --workspace . --body "Current research focus and constraints."
memoria new project "Next project" --workspace . --description "Scope in one sentence."
```

Steering is durable workspace guidance. Project Concepts carry narrower scope.

**4. Add optional adapters last.**

- Use [Obsidian](../how-to-guides/setup/set-up-obsidian.md) as a plain Markdown editor if it helps.
- Use [Zotero](../how-to-guides/setup/set-up-zotero.md) for stable citekeys and portable BibTeX/CSL exports.
- Use [Add a second vault](../how-to-guides/setup/add-a-second-vault.md) only when you really need another workspace.

## What you should have seen

- Customization is mostly configuration and vocabulary, not new product paths.
- Optional adapters do not replace the CLI/engine boundary.
- Your durable system is the checked workspace plus Git history.

For exact commands, continue with [How-to guides](../how-to-guides/README.md).
