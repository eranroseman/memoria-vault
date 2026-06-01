# Memoria documentation

Seven AI agents that read, enrich, map, verify, and write inside your Obsidian vault — under a policy gate that audits every proposed change before it lands.

→ **[View the project on GitHub](https://github.com/eranroseman/memoria-vault)** · [Install](https://github.com/eranroseman/memoria-vault#install) · [Report an issue](https://github.com/eranroseman/memoria-vault/issues)

<!-- SCREENSHOT: Drop a screenshot of the vault in action here once the system is running.
     Suggested: assets/screenshot.png — an agent's audit callout visible in Obsidian.
     Replace this comment with: ![Memoria vault](assets/screenshot.png)             -->

---

## New here? Start with the tutorials

The tutorial sequence takes you from an empty machine to a working research vault, step by step. Work through them in order — each builds on the last.

| # | Tutorial | What you end with |
|---|---|---|
| [01](tutorials/01-set-up-from-zero.md) | Set up from zero | A working vault with all plugins and profiles installed |
| [02](tutorials/02-your-first-note.md) | Your first note | One permanent claim note, authored in your own words |
| [03](tutorials/03-bring-in-a-paper.md) | Bring in a paper | One classified paper-note and one linked claim-note |
| [04](tutorials/04-build-a-reading-batch.md) | Build a reading batch | Your first connected knowledge cluster |
| [05](tutorials/05-start-a-writing-project.md) | Start a writing project | A project folder with corpus map and a chosen outline |
| [06](tutorials/06-verify-and-address-gaps.md) | Verify and address a gap | A verified draft with a complete citation trail |
| [07](tutorials/07-find-new-sources.md) | Find new sources | A populated candidates queue and one new paper-note |

---

## How-to guides

Step-by-step recipes for specific tasks. Pick the one that matches what you need to do.

**Setup** — [Quickstart](how-to-guides/setup/quickstart.md) · [Set up the vault](how-to-guides/setup/set-up-the-vault.md) · [Set up Obsidian](how-to-guides/setup/set-up-obsidian.md) · [Set up Hermes](how-to-guides/setup/set-up-hermes.md) · [Set up Zotero](how-to-guides/setup/set-up-zotero.md) · [Set up a VPS](how-to-guides/setup/set-up-vps.md)

**Sources (upstream)** — [Find new sources](how-to-guides/sources/find-new-sources.md) · [Capture and ingest](how-to-guides/sources/capture-and-ingest.md) · [Classify a source](how-to-guides/sources/classify-a-source.md) · [Discuss a paper](how-to-guides/sources/discuss-a-paper.md) · [Write a claim note](how-to-guides/sources/write-a-claim-note.md)

**Writing (downstream)** — [Query the vault](how-to-guides/writing/query-the-vault.md) · [Assess your corpus](how-to-guides/writing/assess-your-corpus.md) · [Draft with Writer](how-to-guides/writing/draft-with-writer.md) · [Verify and revise](how-to-guides/writing/verify-and-revise.md) · [Export a draft](how-to-guides/writing/export-a-draft.md)

**Maintenance** — [Return to work](how-to-guides/maintenance/return-to-work.md) · [Weekly review](how-to-guides/maintenance/run-the-weekly-review.md) · [Run the Linter](how-to-guides/maintenance/run-the-linter.md) · [Redeploy profiles](how-to-guides/maintenance/redeploy-profiles.md)

**Recovery** — [Safe mode](how-to-guides/recovery/safe-mode.md) · [Fix broken frontmatter](how-to-guides/recovery/fix-broken-frontmatter.md) · [Fix a stuck card](how-to-guides/recovery/fix-stuck-card.md) · [Fix profile drift](how-to-guides/recovery/fix-profile-drift.md)

→ [Full how-to guide index](how-to-guides/README.md)

---

## Reference

Exact values, schemas, commands, and field names.

| Topic | What it covers |
|---|---|
| [Frontmatter fields](reference/frontmatter.md) | Every YAML field: type, allowed values, owner |
| [Note types](reference/note-types.md) | The 16 note types: folder, template, lifecycle, promotion map |
| [Profiles](reference/profiles.md) | Lane identifiers, capability table, folder permissions |
| [Hermes CLI](reference/hermes-cli.md) | All `hermes …` commands: research, board, profiles, skills, cron |
| [Policy MCP](reference/policy-mcp.md) | Write-gate decision values, audit log format, auto-fix classes |
| [Failure modes](reference/failure-modes.md) | Every failure mode by severity: symptom, cause, fix |
| [Glossary](reference/glossary.md) | Term definitions, alphabetical |

→ [Full reference index](reference/README.md)

---

## Explanation

Background reading on why Memoria is built the way it is.

**Start here:** [What Memoria is](explanation/what-memoria-is.md) · [Intellectual foundations](explanation/intellectual-foundations.md) · [Design principles](explanation/design-principles.md)

**Architecture:** [Three-layer model](explanation/architecture/README.md) · [Why specialist profiles](explanation/architecture/why-specialist-profiles.md) · [Why the human gate](explanation/architecture/why-human-gate.md) · [Why not autonomous](explanation/architecture/why-not-autonomous.md)

**The seven agents:** [Librarian](explanation/profiles/librarian.md) · [Mapper](explanation/profiles/mapper.md) · [Socratic](explanation/profiles/socratic.md) · [Writer](explanation/profiles/writer.md) · [Verifier](explanation/profiles/verifier.md) · [Coder](explanation/profiles/coder.md) · [Linter](explanation/profiles/linter.md)

**Knowledge model:** [How the vault organizes knowledge](explanation/knowledge/README.md) · [Note types](explanation/knowledge/note-types.md) · [Promotion model](explanation/knowledge/promotion-model.md)

→ [Full explanation index](explanation/README.md)

---

## Not sure where to go?

| I want to… | Go to… |
|---|---|
| Get started for the first time | [Tutorial 01 — Set up from zero](tutorials/01-set-up-from-zero.md) |
| Understand what Memoria is | [What Memoria is](explanation/what-memoria-is.md) |
| Do a specific task I've done before | [How-to guides](how-to-guides/README.md) |
| Look up a field name or command | [Reference](reference/README.md) |
| Understand why something works the way it does | [Explanation](explanation/README.md) |
| Recover from a failure | [Failure modes](reference/failure-modes.md) · [Recovery guides](how-to-guides/recovery/README.md) |
