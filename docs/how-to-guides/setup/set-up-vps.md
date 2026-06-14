---
title: Set up a VPS
parent: Setup
nav_order: 8
---

# Set up a VPS for always-on operation [deferred]

> **Status — deferred.** v0.1.0-alpha.2 ships and is documented around the `local-only` pattern; the `always-on` topology is designed but not validated end-to-end (tracked in [#383](https://github.com/eranroseman/memoria-vault/issues/383); design: [Deployment options](../../explanation/deployment/deployment-options.md), [Multi-machine deployment (topologies and secondary-device patterns)](../../adr/63-multi-machine-deployment.md)). This guide documents the intended setup.

Move Hermes from local WSL2 to a persistent VPS so the system runs the scheduled crons overnight, processes board cards unattended, and stays reachable from any device. The VPS becomes the **one dispatcher** for the vault — the desktop keeps Obsidian and Zotero, and Syncthing carries the vault between them.

## Prerequisites

- A working local install ([Quickstart](quickstart.md)) confirmed end-to-end
- A VPS running Ubuntu 24.04 (minimum: 2 vCPU, 4 GB RAM, 40 GB disk)
- SSH access to the VPS from your Windows/WSL2 machine
- Syncthing installed on your desktop (for vault sync)

## Steps

**1. Install base dependencies on the VPS.**

```bash
sudo apt update && sudo apt upgrade -y
sudo apt install -y git curl pandoc syncthing
```

**2. Set up passwordless SSH.**

```bash
# from WSL2
ssh-keygen -t ed25519 -C "memoria-vps"
ssh-copy-id user@your-vps-ip
ssh user@your-vps-ip   # confirm passwordless
```

**3. Run the Memoria installer on the VPS (headless).**

```bash
# on VPS
curl -fsSL https://raw.githubusercontent.com/eranroseman/memoria-vault/main/scripts/install.sh -o install.sh
bash install.sh --no-apps --vault ~/Memoria
```

`--no-apps` skips the Obsidian guidance. Otherwise, the installer does its usual work — provision Hermes, scaffold the vault, deploy the five profiles, wire the maintenance crons ([Installer (bootstrap)](../../reference/installer.md)) — plus the monthly Retraction Watch refresh wrapper.

**4. Configure the VPS profiles — remove the Obsidian MCP server.**

The VPS has no running Obsidian instance, so the Local REST API native MCP is unreachable there. Edit each profile's `config.yaml` under `~/.hermes/profiles/memoria-<name>/` and remove the `obsidian` entry from its `mcp_servers` block. The vault-shipped servers (`policy`, `ingest`, `cluster`, `tasks`, `patterns`) remain — they run on the vault venv and need no Obsidian.

**5. Set environment variables on the VPS.**

```bash
# Copy the global secrets file, then propagate per profile
scp ~/.hermes/.env user@your-vps-ip:~/.hermes/.env
# on VPS:
bash install.sh --profiles-only --vault ~/Memoria
grep KILOCODE_API_KEY ~/.hermes/profiles/memoria-librarian/.env   # confirm seeded
```

**6. Sync the vault with Syncthing.**

```bash
# on VPS
systemctl --user enable syncthing && systemctl --user start syncthing
sudo loginctl enable-linger $USER   # survive SSH logout
```

Expose the Syncthing UI temporarily via SSH tunnel (`ssh -L 8384:localhost:8384 user@your-vps-ip`, then open `http://localhost:8384`). Share the runtime vault folder (`~/Memoria`) with your desktop device, and add a `.stignore` in the vault root to exclude the noisy, machine-local files:

```text
.obsidian/workspace.json
.obsidian/workspace-mobile.json
.memoria/.venv
.memoria/data
.git
```

The vault stays a git repo on both machines — Git is the version-history layer, Syncthing the sync layer. Distribute `.memoria/memoria.bib` over Git pulls, not Syncthing, to avoid the mid-transfer race ([Failure modes](../../reference/failure-modes.md)).

**7. Make the VPS the only dispatcher.**

Only **one** machine may run the cron + dispatch side against a synced vault — two dispatchers race on card writes and produce conflicting audit logs. The VPS installer already wired its crons; on the desktop, disable yours:

```bash
# on WSL2 (desktop)
for c in memoria-board-export memoria-sweeps memoria-lint memoria-metrics memoria-eval; do
  hermes cron disable "$c"
done
```

**8. Point the co-PI pane at the VPS (optional).**

ACP is a stdio protocol — the `agent-client` plugin launches the agent as a command. To converse with the VPS-side co-PI from desktop Obsidian, set the agent command in Settings → **Agent Client** to an SSH invocation:

```text
ssh user@your-vps-ip hermes -p memoria-copi acp
```

(On Windows, keep WSL mode on so the `ssh` runs inside WSL2.) Alternatively, keep running the co-PI locally — it only reads the vault, so the desktop copy is safe even with dispatch on the VPS.

**9. Smoke test.**

```bash
# on VPS
hermes profile list                 # five memoria-* profiles
hermes cron list                    # the five crons with next-run times
hermes -p memoria-copi chat         # ask: "explain how this vault is organized"
cd ~/Memoria && qmd embed           # build the search index
```

Then capture a source from desktop Obsidian (`Cmd/Ctrl-P` → **Memoria: capture source from URL**) and confirm the Catalog entity appears on the desktop via Syncthing within ~15 seconds of the VPS-side ingest.

## Verify

- `hermes cron list` on the VPS shows the five maintenance crons; the desktop's are disabled
- Syncthing web UI shows both devices connected and the vault folder in sync
- A test capture from the desktop produces `catalog/papers/<citekey>.md` and an Inbox candidate card, synced back within seconds
- `system/logs/audit.jsonl` shows the VPS-side gated writes

## What runs where

| Component | Runs on |
| --- | --- |
| Obsidian, Zotero, Syncthing | Desktop (Windows) |
| Hermes dispatch, crons, qmd index | VPS |
| Vault files | Syncthing-synced between both |

## Related

- Local install prerequisite: [Quickstart](quickstart.md)
- The topology trade-offs and dispatcher rule: [Deployment options](../../explanation/deployment/deployment-options.md)
- Profile configuration: [Configure a profile](../hermes-agent/configuration.md)
- Connection drops on restart: [Failure modes](../../reference/failure-modes.md)
