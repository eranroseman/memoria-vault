---
title: Add a second vault
parent: Setup
grand_parent: How-to guides
nav_order: 5
---

# Add a second vault

Create a second standalone Memoria workspace by running the bootstrap installer
with a different target path. Each workspace owns its own `.memoria/memoria.sqlite`,
search index, provider config, Git history, and optional app settings.

## Steps

**1. Choose a folder.**

Pick a distinct folder outside cloud-synced paths, for example
`~/Memoria-project2`.

**2. Run the installer with that path.**

```bash
bash scripts/install.sh --vault ~/Memoria-project2
```

```powershell
.\scripts\install.ps1 -Vault "$env:USERPROFILE\Memoria-project2"
```

**3. First checkpoint already made.**

The installer already committed the seeded workspace (`initialize memoria workspace`) at `~/Memoria-project2`; the working tree is clean.

**4. Keep adapters isolated.**

If you use optional UI adapters, configure them per workspace. Do not share search
state, SQLite state, or provider config between workspaces.

## Verify

```bash
~/Memoria-project2/.memoria/.venv/bin/memoria doctor bundle --workspace ~/Memoria-project2
~/Memoria-project2/.memoria/.venv/bin/memoria status --workspace ~/Memoria-project2
```

## Related

- Full install walkthrough: [Set up the vault](set-up-the-vault.md)
- Runtime layout: [On-disk layout](../../reference/system/on-disk-layout.md)
