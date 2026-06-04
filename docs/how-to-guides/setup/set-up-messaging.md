---
title: Set up messaging
parent: Setup
nav_order: 7
---

# Set up the messaging gateway [deferred]

> **v0.1 status — deferred.** The Telegram messaging gateway is a designed but not-yet-shipped component. This guide documents the intended setup; the bot wiring and inbound capture path are not validated end-to-end in v0.1. Use Obsidian capture ([Triage fleeting notes](../compile/triage-fleeting-notes.md)) as the supported path until this lands.

Connect a Telegram bot to Hermes so you can send fleeting notes from your phone directly into the vault's inbox.

## Prerequisites

- Hermes installed and profiles set up ([Set up Hermes](set-up-hermes.md))
- A Telegram account
- The Hermes gateway service available (`hermes gateway --help` returns help text)

## Steps

**1. Create a Telegram bot.**

Open Telegram → search for `@BotFather` → `/newbot` → follow the prompts. Copy the **HTTP API token** BotFather gives you — it looks like `1234567890:ABCdefGHIjklMNOpqrSTUvwxYZ`.

**2. Get your Telegram user ID.**

Message `@userinfobot` in Telegram. Copy the numeric `Id` it returns — this is your user ID for the allowlist.

**3. Configure the Hermes gateway.**

```powershell
notepad "$env:USERPROFILE\.hermes\gateway.yaml"
```

Add the Telegram integration block:

```yaml
telegram:
  token: "1234567890:ABCdefGHIjklMNOpqrSTUvwxYZ"
  allowed_users:
    - <your numeric user ID>
  inbox_path: "vault/10-inbox/01-fleeting/"
  profile: memoria-librarian
```

Adjust `inbox_path` to the absolute path for your vault's fleeting-note inbox (`10-inbox/01-fleeting/`). Do **not** route captures into `.memoria/` — that directory is dot-hidden from Obsidian's scanner, so notes landing there are invisible in the vault.

**4. Start the gateway.**

```bash
hermes gateway start
```

On Windows with WSL2, run this inside WSL2 so it runs on the Linux side alongside the agent runtime.

**5. To run the gateway as a service (optional).**

```bash
systemctl --user enable hermes-gateway
systemctl --user start hermes-gateway
```

**6. Test the connection.**

Send any message to your bot in Telegram. Within a few seconds, a `.md` file should appear in `vault/10-inbox/01-fleeting/` with the message text as its body.

## Verify

- Sending a Telegram message to your bot creates a file in `10-inbox/01-fleeting/`
- The file has the message text in the body and `lifecycle: proposed` in frontmatter (the value all fleeting notes carry)
- `systemctl --user status hermes-gateway` shows `active (running)` if you set it up as a service

## Related

- Fleeting note triage workflow: [Triage fleeting notes](../../how-to-guides/compile/triage-fleeting-notes.md)
- Vault-access and agent-interface integrations: [External integrations](../../reference/integrations.md)
- The two HTTP roles of the gateway: [Distribution model](../../explanation/deployment/distribution-model.md)
- Hermes gateway docs: [hermes-agent.nousresearch.com/docs](https://hermes-agent.nousresearch.com/docs)
