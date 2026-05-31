# Obsidian UI

Two things shape how the vault feels to use: the components Memoria puts on screen, and the restraint applied to how those components look and behave. This document covers both.

---

## Home — the vault front door

`Home.md` at the vault root is the note Memoria opens on launch via the obsidian-homepage plugin. It is a **launchpad**, not a dashboard: it surfaces the dashboards rather than computing anything itself.

**Home is a consumer, never a producer.** It links to Daily Health, the board-state dashboard, quick-capture commands, and research directions. It contains no Dataview queries of its own — any query it shows is defined in a dashboard and embedded here. If Home computed its own health queries, those queries would drift from the authoritative versions in their dedicated dashboards.

**Why a note, not a plugin.** Home is a Markdown note rendered by Dataview — git-tracked, lintable, embeddable. A plugin-rendered start page would be opaque to git, outside the Linter's reach, and unembeddable. The obsidian-homepage plugin simply opens this note on launch; it is a convenience, not a dependency. If the plugin isn't installed, `Home.md` is still an ordinary note the human can pin in the sidebar.

**Graceful degradation.** When the vault is freshly cloned and dashboards have no data yet, Home shows mostly empty states and navigation links. That's intentional — the dashboards degrade gracefully too. Home never breaks because it never does its own computation.

---

## Visual style discipline

Plugin choice is only half the UX. The other half is restraint about how the vault *looks*. A vault that becomes a cockpit of indicators is a vault that gets abandoned. The defaults described here are deliberate; the reasoning behind each choice is the point, because any deviation should be equally deliberate.

## Why typography choices are load-bearing

The three callout types (`[!brief]`, `[!suggestions]`, `[!verification]`) share a single accent color in the default design, differentiated by icon rather than color. The reason is attentional: rainbow callouts train the eye to ignore all of them. Color distinction signals urgency; when every category has a distinct color, the urgency signal collapses into visual noise.

Heading hierarchy is enforced by the Linter not as an aesthetic preference but because Dataview queries that filter on heading content break when the hierarchy is inconsistent. A note with an H4 heading that has no H3 parent is a structural problem, not a cosmetic one — it produces unexpected query results that appear as empty or wrong dashboard views.

Emoji in note titles break filename portability across operating systems. This is not a policy choice; it is a constraint imposed by the filesystems Obsidian runs on. Emoji in note *bodies* is fine because body content is not used as a filename.

## Why chrome is hidden by default

The vault should feel like writing during normal operation. Chrome — tab bars, sidebars, status indicators — is noise during focused reading and writing, and becomes signal when something needs attention. Hiding it by default preserves the signal-to-noise ratio: when the sidebar opens, it means something is happening.

One Obsidian window per vault is a technical constraint as much as a discipline. The agent layer assumes a single active vault; multiple windows attempting to update the same card through the policy MCP produce race conditions in the audit log and board state.

## Why three workspaces, not more

The three workspace design (Human, Reading, Drafting) maps workspaces to cognitive modes rather than to projects. A fourth workspace is a signal that either a new cognitive mode has been identified — in which case the workspace system needs rethinking — or that a project has been mistaken for a mode. Projects change; cognitive modes are stable. A workspace per project would create as many workspaces as there are active projects, which defeats the purpose of workspaces as a stable navigational layer.

The full workspace design is in [reference/obsidian/workspaces.md](../../reference/obsidian/workspaces.md).

## The underlying principle

The architecture is invisible during normal use, legible when something goes wrong. Visual-style discipline supports this: the vault looks like a writing environment most of the time, and indicators surface only when something specific demands attention. Three months in, the mouse hand barely moves and there is no conscious tracking of which workspace is active. That is the success condition.
