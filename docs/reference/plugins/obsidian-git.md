---
topic: plugins
---

# obsidian-git

The plugin auto-commits vault changes and pushes them to a **GitHub remote**. Its job is **version history and offsite backup**, not device sync. Per [deployment-options.md](../../project/roadmap/deployment-options.md), Git is the reversibility layer on every option, while sync is a separate concern — Syncthing under local-mesh and always-on, Obsidian Sync under obsidian-sync, and manual Git push under local-only (a single workstation has no peer to sync with). The settings below are valid Git hygiene regardless of which sync layer the deployment uses.

Load-bearing settings (apply on every deployment):

- `commitMessage` — keep a stable template like `"vault: {{date}} {{numFiles}} files"`. Random commit messages clutter the history, and `{{numFiles}}` is genuinely diagnostic — a 200-file auto-commit means something unusual happened, and the human should notice in the git log.
- `autoBackupAfterFileChange: false` — don't auto-commit on every file change; that fights with Hermes writes and produces hundreds of commits per session. Use scheduled commits instead (`autoSaveInterval: 30` minutes is sensible).
- `pullBeforeCommit: true` — fetch and merge before committing. Defensive against multi-machine divergence: catches the case where a different machine pushed changes since the last local pull, before the local commit creates a divergence. *(Verify this key exists in your installed obsidian-git — current builds expose `pullBeforePush` and `autoPullOnBoot` but may not have a pre-commit pull toggle; if absent, rely on `autoPullOnBoot` + `pullBeforePush`.)*
- `pullBeforePush: true` — same defense at push time. The pair (`pullBeforeCommit` + `pullBeforePush`) is what makes multi-machine setups survive without merge conflicts becoming a daily ritual.
- `autoPullOnBoot: true` — pull when Obsidian starts. Catches "I opened the vault on a different machine and started writing without thinking about sync" — the most common multi-machine failure mode.

Deployment-conditional settings (vary by [deployment option](../../project/roadmap/deployment-options.md)):

- **local-only:** `autoPush: false`. A single workstation has no device to sync with, so push to the GitHub remote **manually** for an offsite-backup checkpoint; auto-push would add noise for no sync benefit.
- **local-mesh:** `autoPush: false`. Syncthing handles desktop↔laptop sync; Git is history plus manual GitHub backup — same as local-only, just with a second device. Push manually for checkpoints.
- **obsidian-sync:** `autoPush: false`. Obsidian Sync handles cross-device sync; Git is for history and auditing only. Push to GitHub manually when a checkpoint is wanted.
- **always-on:** `autoPush: true`. The desktop auto-pushes vault history to GitHub as it works (offsite backup plus audit trail). Device sync between desktop and VPS is handled by Syncthing, not Git — so this push is backup, not the sync path. The desktop pushes; the VPS only ever pulls (see the per-machine override below).

Per-machine override:

- `disablePush: true` on the VPS instance, even under the always-on option. The VPS should `git pull` only — letting it push would create writes that bypass the desktop's policy MCP for review and approval. Local-edit-and-push is the desktop's privilege.

Inline `data.json` — desktop instance, the always-on option:

```json
{
  "commitMessage": "vault: {{date}} {{numFiles}} files",
  "autoCommitMessage": "vault: {{date}} {{numFiles}} files",
  "autoSaveInterval": 30,
  "autoSave": true,
  "autoBackupAfterFileChange": false,
  "autoPush": true,
  "autoPushInterval": 0,
  "autoPullInterval": 0,
  "autoPullOnBoot": true,
  "pullBeforeCommit": true,
  "pullBeforePush": true,
  "syncMethod": "merge",
  "commitDateFormat": "YYYY-MM-DD HH:mm:ss",
  "disablePopups": false,
  "listChangedFilesInMessageBody": false,
  "showStatusBar": true,
  "updateSubmodules": false,
  "customMessageOnAutoBackup": false
}
```

For local-only / local-mesh / obsidian-sync desktop or the VPS-side instance, change `autoPush` to `false` and (on the VPS) set `disablePush: true`. No separate shipped template — the variation is small enough that one inline snippet plus the conditional table above is clearer than four parallel files.
