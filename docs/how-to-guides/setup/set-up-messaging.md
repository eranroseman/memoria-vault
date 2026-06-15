---
title: Set up messaging
parent: Setup
nav_order: 7
---

# Set up messaging

> **Status.** Outbound alert/block push is shipped for the shared Inbox card writer when `MEMORIA_TELEGRAM_BOT_TOKEN` and `MEMORIA_TELEGRAM_CHAT_ID` are present in the runtime environment. The inbound mobile-capture gateway remains deferred (tracked in [#382](https://github.com/eranroseman/memoria-vault/issues/382)); use the in-Obsidian capture commands (`Memoria: capture fleeting` and friends — [Obsidian command palette](../../reference/obsidian-command-palette.md)) as the supported capture path until that lands.

Connect a Telegram bot so Memoria can push urgent alert/block cards to you, and later so you can send fleeting notes from your phone directly into the vault's fleeting queue.

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

For outbound loudness push, put these in the environment that runs Memoria operations (for profile runs, `~/.hermes/.env` is propagated by the installer):

```bash
MEMORIA_TELEGRAM_BOT_TOKEN=<bot token>
MEMORIA_TELEGRAM_CHAT_ID=<your numeric Telegram user ID>
```

For the deferred inbound capture gateway, edit `~/.hermes/gateway.yaml` and add the Telegram integration block:

```yaml
telegram:
  token: "1234567890:ABCdefGHIjklMNOpqrSTUvwxYZ"
  allowed_users:
    - <your numeric user ID>
  inbox_path: "<vault>/notes/fleeting/"
  profile: memoria-librarian
```

Point `inbox_path` at the absolute path of your vault's fleeting folder (`notes/fleeting/` — the same queue the palette's **Memoria: capture fleeting** writes to). Do **not** route captures into `inbox/` (reserved for agent-raised honesty cards) or `.memoria/` (dot-hidden from Obsidian's scanner, so notes landing there are invisible in the vault).

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

Send any message to your bot in Telegram. Within a few seconds, a `.md` file should appear in `<vault>/notes/fleeting/` with the message text as its body.

## Verify

- Creating an `alert` or `block` Inbox card through the shared card writer appends a `system/logs/loudness-push.jsonl` row; with the bot env set, that row reports `status: sent`
- Sending a Telegram message to your bot creates a file in `notes/fleeting/` (deferred inbound gateway)
- The file carries fleeting frontmatter (`type: fleeting`, `lifecycle: proposed` — the value all fleeting notes carry). A capture that lands without frontmatter still enters the flow: the sweeps cron stamps unstamped files in `notes/fleeting/`, after which it shows up in the fleeting queue for triage
- `systemctl --user status hermes-gateway` shows `active (running)` if you set it up as a service

## Related

- Fleeting note triage workflow: [Triage fleeting notes](../compile/triage-fleeting-notes.md)
- The supported capture path meanwhile: [Obsidian command palette](../../reference/obsidian-command-palette.md)
- The two HTTP roles of the gateway: [Distribution model](../../explanation/deployment/distribution-model.md)
- Hermes gateway docs: [hermes-agent.nousresearch.com/docs](https://hermes-agent.nousresearch.com/docs)
