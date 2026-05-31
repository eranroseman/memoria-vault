# How to set up a VPS for always-on operation

Move Hermes from local WSL2 to a persistent VPS so the system runs overnight batch jobs, handles scheduled tasks, and stays reachable from any device. This is the always-on deployment option.

## Prerequisites

- A working local install ([quickstart.md](quickstart.md)) confirmed end-to-end
- A VPS running Ubuntu 24.04 (minimum: 2 vCPU, 4 GB RAM, 40 GB disk)
- SSH access to the VPS from your Windows/WSL2 machine
- Syncthing installed on your desktop (for vault sync)

## Steps

**1. Install dependencies on the VPS.**

```bash
sudo apt update && sudo apt upgrade -y
sudo apt install -y git curl build-essential python3-pip syncthing
```

Install Hermes:

```bash
curl -fsSL https://raw.githubusercontent.com/NousResearch/hermes-agent/main/scripts/install.sh | bash
hermes --version   # confirm
```

Install Python tools:

```bash
pip install markitdown qmd --break-system-packages
```

**2. Set up passwordless SSH.**

```bash
# from WSL2
ssh-keygen -t ed25519 -C "memoria-vps"
ssh-copy-id user@your-vps-ip
ssh user@your-vps-ip   # confirm passwordless
```

**3. Clone the vault on the VPS.**

```bash
# on VPS
git clone git@github.com:<your-handle>/memoria-vault.git ~/memoria-vault
cd ~/memoria-vault && git log --oneline -3   # confirm current
```

**4. Configure Syncthing on the VPS.**

```bash
# on VPS
systemctl --user enable syncthing && systemctl --user start syncthing
```

Expose the Syncthing UI temporarily via SSH tunnel:

```bash
# from WSL2
ssh -L 8384:localhost:8384 user@your-vps-ip
```

Open `http://localhost:8384`. Add the vault folder at `/home/user/memoria-vault/vault`. On your desktop's Syncthing UI, add the VPS as a device and share the vault folder.

Add a `.stignore` in the vault root to exclude noise:

```text
.obsidian/workspace.json
.obsidian/workspace-mobile.json
90-assets/*.pdf
.git
```

**5. Install the Memoria profiles on the VPS.**

```bash
# on VPS — from inside the vault/
cd ~/memoria-vault/vault
./install.ps1   # or install.sh when available
```

**6. Configure the VPS profiles — remove the Obsidian MCP server.**

The VPS has no running Obsidian instance. Edit each profile's `mcp.json` under `~/.hermes/profiles/memoria-<name>/mcp.json` and remove the `obsidian` server entry. The `policy` and `tasks` servers remain.

**7. Set environment variables on the VPS.**

```bash
# Copy from local machine
scp ~/.hermes/profiles/memoria-librarian/.env user@your-vps-ip:~/.hermes/profiles/memoria-librarian/.env
# Repeat for other profiles that need keys
```

Confirm:

```bash
# on VPS
cat ~/.hermes/profiles/memoria-librarian/.env | grep ANTHROPIC_API_KEY
```

**8. Start Hermes as a persistent systemd service.**

Create `~/.config/systemd/user/hermes-gateway.service` on the VPS:

```ini
[Unit]
Description=Hermes Agent gateway — Memoria
After=network.target

[Service]
Type=simple
WorkingDirectory=/home/user/memoria-vault/vault
ExecStart=hermes gateway run
Restart=on-failure
EnvironmentFile=/home/user/.hermes/profiles/memoria-librarian/.env

[Install]
WantedBy=default.target
```

```bash
systemctl --user daemon-reload
systemctl --user enable hermes-gateway
systemctl --user start hermes-gateway
sudo loginctl enable-linger $USER   # survive SSH logout
hermes gateway status
```

**9. Set up the SSH tunnel for ACP from Obsidian.**

Create `~/.config/systemd/user/hermes-tunnel.service` on WSL2 (your local machine):

```ini
[Unit]
Description=SSH tunnel — Hermes gateway (VPS→desktop)
After=network.target

[Service]
Type=simple
ExecStart=ssh -N -L 8642:localhost:8642 \
  -o ServerAliveInterval=60 \
  -o ExitOnForwardFailure=yes \
  user@your-vps-ip
Restart=on-failure
RestartSec=10

[Install]
WantedBy=default.target
```

```bash
systemctl --user daemon-reload
systemctl --user enable hermes-tunnel
systemctl --user start hermes-tunnel
curl http://localhost:8642/health   # confirm tunnel working
```

The agent-client plugin URL in Obsidian stays `http://localhost:8642` regardless of where Hermes runs.

**10. Build the search index and smoke test.**

```bash
# on VPS
cd ~/memoria-vault/vault
qmd embed
git pull --ff-only
hermes -p memoria-librarian chat -s llm-wiki
# in session:
/llm-wiki ingest --source <a-known-citekey> --dry-run
```

Verify in Obsidian: dry-run output appears and the Syncthing sync completes within ~15 seconds.

**11. Schedule recurring jobs.**

```bash
# on VPS
hermes cron create "0 2 * * *" --profile memoria-linter --prompt "Run lint check on vault"
hermes cron create "0 3 * * 0" --profile memoria-linter --prompt "Run retraction sweep"
hermes cron list
```

**12. Decommission local Hermes (optional).**

Once the VPS is running reliably, the desktop only needs: Obsidian, Zotero, Syncthing. Keep a local fallback config in case the VPS is unreachable:

```bash
cp ~/.hermes/config.yaml ~/.hermes/config.local.yaml
```

If the VPS goes down, start Hermes locally and point the agent-client at `http://localhost:8642`.

## Verify

- `hermes gateway status` on VPS shows `active (running)`
- `systemctl --user status hermes-tunnel` on WSL2 shows `active (running)`
- Syncthing web UI shows both devices connected and vault folder in sync
- A test ingest from the VPS creates a note in Obsidian via Syncthing within 15 seconds
- `hermes cron list` shows scheduled jobs registered

## What runs where

| Component | Runs on |
| --- | --- |
| Obsidian, Zotero, Syncthing | Desktop (Windows) |
| Hermes, cron jobs, qmd index | VPS |
| vault files | Syncthing-synced between both |

## Related

- Local install prerequisite: [quickstart.md](quickstart.md)
- Profile configuration: [hermes/configuration.md](../hermes/configuration.md)
- Redeploying profiles after vault changes: [maintenance/redeploy-profiles.md](../maintenance/redeploy-profiles.md)
- Tunnel drops on restart: [recovery/fix-stale-bib.md](../recovery/) — see failure-modes for `VPS tunnel drops`
