---
topic: plugins
---

# obsidian-local-rest-api

Exposes the vault over HTTP for Hermes. The default secure port is **27124 (HTTPS)**; an optional insecure HTTP server listens on **27123** but is **off by default** (`enableInsecureServer: false`). Confirmed by the shipped `data.json.example` (`"port": 27124`, `"insecurePort": 27123`).

**Security caveat (load-bearing).** This plugin's `data.json` contains generated secrets — an `apiKey` token, a TLS certificate, and an RSA private key — written into the file the first time the plugin starts. **These must not be committed to git.** Memoria's general "ship `data.json` files in the vault" pattern (see [the data.json convention](README.md#the-datajson-convention)) does **not** apply to this plugin; the file is per-machine secret material.

The recommended discipline:

- Add `.obsidian/plugins/obsidian-local-rest-api/data.json` to the vault's `.gitignore`.
- A sanitized example ships at `.obsidian/plugins/obsidian-local-rest-api/data.json.example` in the starter vault — copy it to `data.json` (same directory), then launch Obsidian once so the plugin regenerates the actual `apiKey` and TLS material in place.
- If the real `data.json` has already been committed to a repo with public history, treat the keys as compromised: regenerate via the plugin's "Reset" command and rotate the Hermes-side token.

Load-bearing settings (after secrets are gitignored):

- `enableInsecureServer: false` — keep HTTP off; require HTTPS. The TLS cert lives in the same `data.json`.
- `apiKey: "<token>"` — required when reachable from anything other than `127.0.0.1`. For the always-on option (VPS), this is non-optional. Mirrors the [fail-closed startup](../../explanation/architecture/control-plane.md#fail-closed-startup) discipline on the Hermes API side.
