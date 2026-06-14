---
title: Memoria v0.1 manual testing
parent: 0.1.0-alpha.1
grand_parent: Releasing
nav_order: 5
---
# Memoria v0.1 manual testing

> **Point-in-time record.** Black-box findings captured against the v0.1.0-alpha.1 build; terminology and paths here (numbered folders such as `00-meta/01-dashboards/` and `30-synthesis/`) reflect that point and are **not current** — the findings were triaged into the PRs/issues listed below. See current docs for present-day naming.

- **Scope:** Black box functional and usability testing of user-facing featured based on documented functionality.
- **Objectives:** Ensures core functionality and user experience.
- **Environments:** memoria-test after completion of the [release-candidate runbook](../../testing/plans/release-candidate-runbook.md)

## Disposition (2026-06-04)

Findings triaged into three buckets:

- **Bucket A — in-place doc fixes → shipped in PR #141** (vapor/deferred commands, dead `Ctrl+Shift+1..4` hotkeys → profile picker, "Open chat view" command name, auto-mention, CLI centralization to the Hermes CLI page, systematic-review status note, write-template active-project note, "Chat with Hermes" → "Run a CLI chat session", classify-a-source rewrite, homepage close-all tip).
- **Bucket B — vault/UX changes → issues:** placeholder-text fields #142 · maturity dropdown #143 · relation field #144 · property reorder/group/color #145 · agent-pane rename #146.
- **Structural doc reorgs → issues:** recovery→troubleshooting #147 · split maintain #148 · zotero folder #149.
- **Bucket C — feature gaps / product questions → issues:** workspaces not implemented #150 · agent-switch latency #151 · clear-after-each-task #152 · auto-promote at evergreen #153 · automate start-a-writing-project #154 · review-link-suggestions empty #155 · detect misplaced files #156.

Original findings preserved below.

## General notes

Some of the remarks are on the docs/ and not the vault/
Some of the issue are vault wide and not specific to the page they are written on.
It is very easy to create folders and files in the wrong places. We should add a process that find them

## how-to-guides/setup

_Not tested_

## how-to-guides/using-obsidian

### Vault homepage

remove link to the plugin page and rewrite sentence
Ass that you can always get back to the homepage view by right clicking on a tab header and choosing close all. It will close all open tabs and launch the home page
Research focus - the open fields have text in them, that you need to delete before you can type in your own text. This occurs in various places in the vault and we should find a better solution. Maybe using something like <https://github.com/danielo515/obsidian-modal-form>

### Workspaces

doesn't seems to be implemented yet

### Agent-client pane

We need to find a better name for it
add an explanation about the auto mention
You can also use the ribbon icon to open it
the command is Agent Client: Open chat view
keyboard binding is not working
replace keyboard binding with keyboard shortcut. This is probably and folder wide issue.
Is it necessary to clear after each task?
Switching and agents take a long time. Compare our current setting to https://rait-09.github.io/obsidian-agent-client/usage/floating-chat.html
Memoria: write draft · Memoria: scaffold canvas · Memoria: scaffold code note · Memoria: write project note - all ask to choose a folder, which isn't very intuitive. It should be explained that you need to have an active project for it.
should 2. Add a QuickAdd entry for each agent command you use. be here?

## how-to-guides/compile

### find new sources

All CLI commands should be moved to HERMES CLI page and linked from here.

### triage fleeting notes

Cmd-P → Memoria: open reading pipeline doesn't work
00-meta/01-dashboards/reading-pipeline.md doesn't match what the page describes

### Capture and ingest a source

CLI

### Classify a source

the entire explanation isn't clear.

### Pin a citekey

all zotero how to need to be in their own folder

### Read a paper through a Socratic lens

this doesn't seem to be implemented yet. has CLI command and the whole concept behind it isn't clear

### Write a claim note

CLI
the maturity files is unrestricted, I can write any value in it. Can it be a dropdown?
The relation field is a long string that is hard to work with and can break easily

### Review link suggestions

there were no suggestions to review

### Promote a claim to canonical reference

pros and cons of auto promoting when a claim achieve maturity: evergreen

### Archive a source

CLI
open field text
We need to reorder the properties by order of importance to the user, lifecycle stage is buried. Can they be grouped? Can they be color coded (ingest_status complete is green, etc.)

### Run a systematic review

Was that implemented or is it deferred?

## how-to-guides/compose

### Start a writing project

can it be automated? I should fill a form and the rest should be done by a script

### Assess your corpus, Assess your corpus

CLI
not enough notes to test it

\*\*I stopped Compose here because these two reason

## how-to-guides/maintain

should be split between knowledge work (run the weekly review) and technical (redeploy profiles)

## how-to-guides/hermes-agent

Configure a profile is part of setup
Chat with Hermes - sound like it is about the telegram use

## how-to-guides/recovery

These are troubleshooting guides. Should be reframed as such and rewritten accordingly

## tutorials

I skipped those as I assumed the same issues will repeat
