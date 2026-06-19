---
title: Set up messaging
parent: Setup
nav_order: 7
---

# Set up messaging

> **Status.** Outbound alert/block push is shipped for the shared Inbox card writer when `MEMORIA_TELEGRAM_BOT_TOKEN` and `MEMORIA_TELEGRAM_CHAT_ID` are present in the runtime environment. The inbound mobile-capture gateway remains deferred (tracked in [#382](https://github.com/eranroseman/memoria-vault/issues/382)); use the in-Obsidian capture commands (`Memoria: capture fleeting` and friends — [Obsidian command palette](../../reference/obsidian-command-palette.md)) as the supported capture path until that lands.

Connect a Telegram bot so Memoria can push urgent alert/block cards to you. The same bot will later carry fleeting notes from your phone into the vault's fleeting queue once the inbound gateway ships — that half is deferred ([#382](https://github.com/eranroseman/memoria-vault/issues/382)) and is documented separately at the bottom of this page.

## Prerequisites

- Hermes installed and profiles set up ([Set up Hermes](set-up-hermes.md))
- A Telegram account

## Create the bot (shared)

Both the shipped outbound push and the deferred inbound gateway use one Telegram bot.

**1. Create a Telegram bot.**

Open Telegram → search for `@BotFather` → `/newbot` → follow the prompts. Copy the **HTTP API token** BotFather gives you — it looks like `1234567890:ABCdefGHIjklMNOpqrSTUvwxYZ`.

**2. Get your Telegram user ID.**

Message `@userinfobot` in Telegram. Copy the numeric `Id` it returns — this is your chat ID for outbound push and your allowlist entry for inbound capture.

## Shipped: outbound alert push

This is the supported, validated path today: urgent `alert`/`block` Inbox cards are pushed to your phone.

**3. Set the push environment variables.**

Put these in the environment that runs Memoria operations (for profile runs, `~/.hermes/.env` is propagated by the installer):

```bash
MEMORIA_TELEGRAM_BOT_TOKEN=<bot token>
MEMORIA_TELEGRAM_CHAT_ID=<your numeric Telegram user ID>
```

That is the whole shipped setup — no gateway service is required for outbound push.

### Verify (outbound)

- Creating an `alert` or `block` Inbox card through the shared card writer appends a `system/logs/loudness-push.jsonl` row; with the bot env set, that row reports `status: sent`
- A matching message arrives in your Telegram chat with the bot

## Deferred: inbound mobile-capture gateway

> **Status — deferred** ([#382](https://github.com/eranroseman/memoria-vault/issues/382)). The inbound gateway that turns Telegram messages into fleeting notes is **not validated end-to-end** and not part of a supported alpha.8 install. The steps below document the intended setup so future work does not reinvent it; until it lands, use the in-Obsidian capture commands (`Memoria: capture fleeting` and friends — [Obsidian command palette](../../reference/obsidian-command-palette.md)) as the supported capture path.

These steps additionally need the Hermes gateway service available (`hermes gateway --help` returns help text).

**A. Configure the gateway.**

Edit `~/.hermes/gateway.yaml` and add the Telegram integration block:

```yaml
telegram:
  token: "1234567890:ABCdefGHIjklMNOpqrSTUvwxYZ"
  allowed_users:
    - <your numeric user ID>
  inbox_path: "<vault>/notes/fleeting/"
  profile: memoria-librarian
```

Point `inbox_path` at the absolute path of your vault's fleeting folder (`notes/fleeting/` — the same queue the palette's **Memoria: capture fleeting** writes to). Do **not** route captures into `inbox/` (reserved for agent-raised honesty cards) or `.memoria/` (dot-hidden from Obsidian's scanner, so notes landing there are invisible in the vault).

**B. Start the gateway.**

```bash
hermes gateway start
```

On Windows with WSL2, run this inside WSL2 so it runs on the Linux side alongside the agent runtime.

**C. Run the gateway as a service (optional).**

```bash
systemctl --user enable hermes-gateway
systemctl --user start hermes-gateway
```

**D. Test the connection.**

Send any message to your bot in Telegram. Within a few seconds, a `.md` file should appear in `<vault>/notes/fleeting/` with the message text as its body.

### Verify (inbound, when validated)

- Sending a Telegram message to your bot creates a file in `notes/fleeting/`
- The file carries fleeting frontmatter (`type: fleeting`, `lifecycle: proposed` — the value all fleeting notes carry). A capture that lands without frontmatter still enters the flow: the sweeps cron stamps unstamped files in `notes/fleeting/`, after which it shows up in the fleeting queue for triage
- `systemctl --user status hermes-gateway` shows `active (running)` if you set it up as a service

## Related

- Fleeting note triage workflow: [Triage fleeting notes](../inbox/triage-fleeting-notes.md)
- The supported capture path meanwhile: [Obsidian command palette](../../reference/obsidian-command-palette.md)
- The two HTTP roles of the gateway: [Distribution model](../../explanation/deployment/distribution-model.md)
- Hermes gateway docs: [hermes-agent.nousresearch.com/docs](https://hermes-agent.nousresearch.com/docs)
