---
topic: roadmap
---

# Secret management

`.env` is the baseline. For [the local-only option](deployment-options.md) (one machine) it's the right answer — Hermes reads `~/.hermes/.env` and per-profile `~/.hermes/profiles/memoria-<name>/.env`, and there's nothing to rotate centrally.

For [the always-on option](deployment-options.md) (multiple machines, VPS plus desktop), centralized rotation matters. Hermes ships first-class support for [Bitwarden Secrets Manager](https://hermes-agent.nousresearch.com/docs/user-guide/secrets/bitwarden): one bootstrap token (`BWS_ACCESS_TOKEN`) lives in each machine's `.env`, and every other API key (Anthropic, OpenRouter, Scite, etc.) lives in Bitwarden. At Hermes startup, the `bws` CLI fetches the project's secrets into the process environment. Rotating a key is a single change in the Bitwarden web app; every Hermes process on every machine picks it up on next start.

Set up with `hermes secrets bitwarden setup` — it auto-installs the `bws` binary, prompts for the bootstrap token, and tests the fetch. Same project, same secrets, every machine — the convention that makes the always-on option viable without per-machine credential drift.

Other backends (HashiCorp Vault, AWS Secrets Manager, 1Password CLI) are not built in; Hermes has a plugin point in `agent/secret_sources/` for adding them, but until you have one of them already running, Bitwarden Secrets Manager is the path of least resistance.

## When not to use a secret manager

- **the local-only option** (single machine). `.env` is fine and a network dependency at startup buys you nothing.
- **Air-gapped environments** that can't reach `api.bitwarden.com` or your secret backend.
- **CI/CD with existing injection.** If GitHub Actions / Vault / similar is already wired up, don't add a second path.
