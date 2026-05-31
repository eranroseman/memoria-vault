---
topic: tutorials
---

# Tutorial: Set up Memoria from zero

By the end of this tutorial you will have:

- A working vault with the complete folder structure
- All seven Hermes profiles installed and registered
- The Kanban board and all dashboards active
- One research source ingested from Zotero into the vault, carrying its `[!brief]` comparative-read callout
- One audit-log entry proving the policy MCP gated the write

This is the **Memoria v0.1** ([roadmap/README.md](../project/roadmap/README.md#memoria-v01)) setup path — Memoria ships as a complete system from day 1. All components (board, profiles, templates, dashboards) are load-bearing and are stood up together.

> **Status.** See [implementation status](../project/implementation-status.md).

New to terms like *lane*, *card*, *profile*, or *comparative-brief*? Keep the [glossary](../reference/glossary.md) open in a second tab — this tutorial uses a few of them before the architecture docs define them in full.

Expect to spend 60–90 minutes if you're new to all the pieces. Commands are shown in **Windows PowerShell** (the installer is `install.ps1`); blocks labelled `bash` are plain `git`/`hermes` CLI calls that run identically in any shell, so on macOS/Linux you only need to swap PowerShell cmdlets like `Copy-Item` and `notepad` for their local equivalents.

## What you need before starting

- A machine with **Python 3.11+**, **git**, and **Pandoc** available on your `PATH`.
- **Obsidian** (free, [obsidian.md](https://obsidian.md)).
- **Zotero** + the **Better BibTeX** extension installed and signed in.
- **Hermes** installed and on your `PATH` (`hermes --version` returns something). Hermes setup is upstream of Memoria — see [hermes-agent.nousresearch.com](https://hermes-agent.nousresearch.com/) if you need to install it.
- A Claude API key. Set `ANTHROPIC_API_KEY` in your shell.
- An OpenRouter API key (or any cheap-model provider). Set `OPENROUTER_API_KEY`.
- An email for the OpenAlex polite pool. Set `OPENALEX_EMAIL` to a working address you control.

If any are missing, stop and fix that first — the rest of the tutorial assumes them.

## Step 1 — Get the starter vault

Clone the `memoria-vault` repo (or your fork). **The local folder name is your choice** — the installer detects its own location at runtime, so it doesn't matter what you call it:

```bash
# Use the default name…
git clone https://github.com/<your-handle>/memoria-vault.git

# …or pick your own. Both work.
git clone https://github.com/<your-handle>/memoria-vault.git my-research-vault
cd my-research-vault/vault   # the Obsidian vault + install.ps1 live in the vault/ subfolder
```

The repo's `vault/` subfolder **is** the Obsidian vault: inside it you'll see the skeleton (`00-meta/`, `10-inbox/`, `20-sources/`, `30-synthesis/`, …) plus `.obsidian/` (plugin configs + snippets), `.memoria/`, and `install.ps1`. (`docs/` and `scripts/` sit beside `vault/` at the repo root — they are not part of the Obsidian vault.) Inside `.memoria/` the seven profile directories each ship their `SOUL.md` prompt, `cron/`, and `skills/`, and the seven `lane-overrides/*.yaml` ship alongside; only the `mcp/` directory is a placeholder (`.keep` only) until the v0.2 wiring lands (see [implementation-status.md](../project/implementation-status.md)). The starter vault ships pre-populated — no skeleton-creation step needed.

## Step 2 — Open the vault in Obsidian

In Obsidian, **Open vault → Open folder as vault**, point at the `vault/` subfolder of the repo you cloned (that folder *is* the Obsidian vault). The vault name Obsidian shows is whatever that folder is called.

Install the required community plugins (Settings → Community plugins → Browse):

- `obsidian-local-rest-api` — Hermes uses this to write into the vault
- `agent-client` — connects Obsidian command palette actions to Hermes profiles
- `obsidian-citation-plugin` — reads `library.bib` for in-note citations
- `callout-manager` — renders the `[!brief]` and other Memoria callout types with correct icons and colors

`dataview` and `templater-obsidian` are required for the dashboards and templates — install them as part of this step.

After install, copy the example REST API config so Hermes can authenticate (this is the only plugin whose `data.json` is gitignored because it contains generated secrets — every other plugin's settings ship in place):

```powershell
Copy-Item .obsidian/plugins/obsidian-local-rest-api/data.json.example `
          .obsidian/plugins/obsidian-local-rest-api/data.json
```

Then **launch Obsidian once**: on first start the plugin regenerates the real `apiKey` (a 64-char hex token) and its TLS material in place — you don't author the key by hand. Open Settings → Local REST API (or read `data.json`) and copy the generated `apiKey`; you'll feed it to Hermes next. The defaults are correct as shipped: HTTPS on **port 27124**, loopback-only, with the insecure HTTP server (port 27123) **off**.

Restart Obsidian. You should see "Local REST API: started" in the bottom-right status bar.

## Step 3 — Wire up Zotero

In Zotero, **Tools → Preferences → Better BibTeX** (Zotero 7; in Zotero 5/6 this was Edit → Preferences → Better BibTeX):

- **Citation key formula**: `[auth.lower][year][title:lower:condense:6]` (matches Memoria's expected `mamykina2010sense` shape — see [ADR-04](../project/decisions/04-citekey-naming-convention.md)).
- **Automatic export**: configure auto-export to `.memoria/library.bib` inside the vault. This is the authoritative `.bib` Memoria reads.

Drag one PDF you've been meaning to read into Zotero. Better BibTeX assigns it a citekey (e.g., `mamykina2010sense`). Note that key — you'll use it in Step 6.

## Step 4 — Install the seven profiles

The seven Memoria profile directories are already in the vault at `.memoria/profiles/memoria-<name>/`. **In the current v0.1 scaffold each ships only its `SOUL.md` prompt** (plus `cron/` and `skills/`); the `config.yaml`, `mcp.json`, and `distribution.yaml` that `hermes profile install` requires are the v0.2 wiring and are not authored yet. Running the installer is safe and idempotent, but it will **detect the missing files and skip each profile** with an explanatory message — no profile registers until its wiring exists (see [implementation-status.md](../project/implementation-status.md)):

```powershell
# from the vault/ folder (where Step 1 left you)
./install.ps1
```

Once the wiring lands, this installs every profile in one pass. For each profile the script:

1. Stages the profile files.
2. Substitutes `{{VAULT_PATH}}` in `mcp.json` with this vault's absolute path.
3. Calls `hermes profile install <staged> --alias memoria-<name> --force --yes`.
4. Copies `.env.EXAMPLE` to `.env` as a starting point — but only if that profile has no `.env` yet.

To update later, re-run the script after a `git pull`: it always overwrites the author-owned files (`SOUL.md`, `config.yaml`, `mcp.json`, `skills/`, `cron/`) and never touches your `.env`.

Fill in the secrets for the Librarian profile:

```powershell
notepad ~/.hermes/profiles/memoria-librarian/.env
```

```env
ANTHROPIC_API_KEY=sk-ant-...
OPENROUTER_API_KEY=sk-or-...
OPENALEX_EMAIL=you@example.com
OBSIDIAN_API_KEY=<the 64-char hex apiKey from Step 2>   # read by the `obsidian` MCP server (mcp-obsidian)
```

Confirm the install succeeded:

```bash
hermes profile list
```

You should see all seven `memoria-*` profiles in the output. This tutorial drives `memoria-librarian` directly and `memoria-linter` at the end; the rest stay idle until later steps. One wrinkle worth knowing now: the `[!brief]` callout the Librarian writes during ingest is produced by the *comparative-brief* skill, which belongs to the **Mapper** profile's contract — so Step 7 credits it to Mapper even though you never invoke Mapper by hand here.

## Step 5 — Confirm the policy MCP is connected

> **Status.** See [implementation status](../project/implementation-status.md).

The policy MCP reads lane-override YAML files at startup. Under direct profile management those files live at `.memoria/lane-overrides/` in the vault, and the installer pointed each profile's `mcp.json` at the policy MCP code (`.memoria/mcp/policy_mcp.py`) plus the lane-overrides directory via the `{{VAULT_PATH}}` substitution. No copy step needed.

You can confirm this by reading any profile's installed `mcp.json`:

```powershell
Get-Content ~/.hermes/profiles/memoria-librarian/mcp.json
```

You should see the `policy` server pointing at this vault's `.memoria/mcp/policy_mcp.py` with an absolute path. If the path still contains `{{VAULT_PATH}}`, the installer didn't substitute it — re-run `install.ps1`.

The default `.memoria/lane-overrides/librarian.yaml` allows writes to `10-inbox/` and `20-sources/` (these log as `decision: allow_with_log`), degrades any write to `30-synthesis/01-claims/` down to `dry_run`, and routes the audit log to `00-meta/02-logs/audit.jsonl`. You don't need to change anything.

## Step 6 — Ingest your first source

Pick the citekey you noted in Step 3. Then:

```bash
hermes -p memoria-librarian chat -s llm-wiki
# then, in the session:
/llm-wiki ingest --source mamykina2010sense
```

Replace `mamykina2010sense` with your actual citekey. Hermes will:

1. Read the citation from `library.bib`
2. Call OpenAlex / Crossref / Unpaywall to enrich (citation count, abstract, OA status)
3. Run Marker on the PDF to extract markdown into `90-assets/extracts/` (if the PDF is open access; otherwise this step is skipped and the paper-note carries `extract_path: ""`)
4. Compose the `comparative-brief` `[!brief]` callout (the Mapper-defined comparative read — see Step 7)
5. Write the paper-note to `20-sources/01-papers/<citekey>.md`
6. Append an entry to `00-meta/02-logs/audit.jsonl` for every write

This usually takes 30–90 seconds. If `llm-wiki` doesn't resolve, check that `hermes skills list` includes it; if not, install with `hermes skills install llm-wiki`.

## Step 7 — Verify the audit log

In Obsidian (or with `Get-Content`), open `00-meta/02-logs/audit.jsonl` inside the vault. You should see one or more JSON objects on individual lines, each with this shape:

```json
{
  "timestamp": "2026-05-27T14:32:18Z",
  "profile": "memoria-librarian",
  "action": "write",
  "path": "20-sources/01-papers/mamykina2010sense.md",
  "task_id": "TASK-2026-05-27-001",
  "decision": "allow_with_log",
  "policy_rule": "Librarian.write.20-sources",
  "before_hash": "sha256:e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
  "after_hash": "sha256:8f4a..."
}
```

This shape matches the contract in [architecture/policy-mcp.md](../reference/architecture/policy-mcp.md): `timestamp` (not `ts`), a required `task_id`, the matched `policy_rule`, and a `before_hash` that for a freshly-created file is the SHA-256 of the empty byte string (`e3b0c442…`), never `null`. The presence of `before_hash`, `after_hash`, and `decision` is the proof: the policy MCP saw the write and gated it. If the file changes outside this audit trail, the Linter's `vault-hash-drift` detector ([profiles/linter.md](../explanation/profiles/linter.md)) will flag it.

Open the paper-note (`20-sources/01-papers/<citekey>.md`) in Obsidian. The top should show a `[!brief]` callout — the Mapper-defined comparative read against your existing corpus. Since you only have one source, the callout will note that there's nothing to compare against yet; that's correct, and it fills out with genuine comparisons as the corpus grows.

## What just happened

You've exercised all three Memoria layers:

- **Board** — implicit; the ingest ran as a single card flowing through `ready → running → done (→ archived after review)`.
- **Workers** — Librarian claimed the card, called the policy MCP for each write, wrote a paper-note.
- **Vault** — the paper-note now lives in `20-sources/01-papers/`, and the audit log records what happened.

This is the loop you'll repeat. Each new source goes through this path. Promotion to claim notes in `30-synthesis/01-claims/` is a separate, human-driven step — agents can't auto-write there, because (as Step 5 showed) the policy MCP degrades any worker write to that folder down to `dry_run`, regardless of profile.

## What to do next

Now that one source is in the vault:

1. **Ingest 5–10 more sources.** Drag them into Zotero and run `hermes ... ingest --source <citekey>` for each. Once you have 5+, the `[!brief]` callouts finally have a corpus to compare against.
2. **Run the Linter once.** In a Linter session (`hermes -p memoria-linter chat -s lint`), `/lint --target 20-sources/` will report any structural issues (frontmatter shape, link health). The Linter profile was already installed by `install.ps1` in Step 4 — fill in its `~/.hermes/profiles/memoria-linter/.env` the first time you run it, exactly as you did for the Librarian.
3. **Open the [weekly-review](../explanation/dashboards/weekly-review.md)** once a week (Friday afternoon is the recommended ritual). Decide what to promote from `10-inbox/` and classify outstanding paper-notes.

All seven profiles are already installed. As the corpus grows, more profile lanes activate naturally — comparative scope (Mapper), claim verification (Verifier), drafting assistance (Writer). The [configuration tiers](../project/roadmap/README.md#implementation-paths-configuration-tiers) section explains when mode-based fallback applies.

## If something goes wrong

The most common first-time failures are:

- **`install.ps1` errors** — check that `.memoria/profiles/memoria-librarian/` exists in the cloned vault and contains `SOUL.md` (only `SOUL.md` is required in v0.1; `config.yaml` and `mcp.json` are v0.2 wiring not yet present). If `SOUL.md` is missing the vault checkout is incomplete; re-clone or `git pull`.
- **`hermes profile install` fails** — confirm `hermes profile list` works at all (Hermes is installed) and that `~/.hermes/profiles/` is writable.
- **Obsidian REST API connection refused** — confirm Obsidian is running and the plugin is enabled. The plugin binds to `127.0.0.1` by default; if Hermes is on a different machine, you'll hit this.
- **`[!brief]` callout looks unstyled** — it still renders with Obsidian's default callout styling; install the **Callout Manager** plugin and import the Memoria callout set for the proper icons and colors ([obsidian-plugins/required/callout-manager.md](../reference/plugins/callout-manager.md)). It does not silently fail without it.
- **Anything else** — check [operations/failure-modes.md](../how-to/operations/failure-modes.md) for known Detect/Fix/Verify recipes.

## Where to go from here

| If you want to… | Read |
|---|---|
| Understand the three-layer architecture in depth | [architecture/README.md](../explanation/architecture/README.md) |
| Configure the other profiles | [profiles/README.md](../explanation/profiles/README.md), per-profile contracts in [profiles/](../explanation/profiles/) |
| See the full daily / weekly workflow rhythms | [workflows/README.md](../how-to/workflows/README.md) |
| Add deployment options (laptop + desktop, VPS) | [roadmap/deployment-options.md](../project/roadmap/deployment-options.md) |
| Understand why the policy MCP is structured this way | [architecture/policy-mcp.md](../reference/architecture/policy-mcp.md) |
