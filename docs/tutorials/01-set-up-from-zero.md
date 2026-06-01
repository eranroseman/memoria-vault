
# Tutorial 01: Set up from zero

**You will end with:** a working Memoria vault open in Obsidian, all eight required plugins installed and configured, all seven profiles installed, and Zotero wired up to auto-export your library.

**Time:** 30–45 minutes.

**You will use:** Terminal (once, for the installer), then Obsidian for everything else.

---

## Prerequisites

- [Obsidian](https://obsidian.md/) installed
- [Hermes](https://hermes-agent.nousresearch.com/) installed (`hermes --version` returns a version number)
- [Zotero 9](https://www.zotero.org/) installed with the [Better BibTeX](https://retorque.re/zotero-better-bibtex/) add-on
- [Git](https://git-scm.com/) installed

---

## Step 1 — Clone the vault

Open a terminal and run:

```bash
git clone https://github.com/eranroseman/memoria-vault.git ~/memoria
cd ~/memoria
```

You now have the vault folder at `~/memoria`. You can rename or move it — the internal shape is what matters, not the folder name.

---

## Step 2 — Run the installer

Still in the terminal:

```bash
./install.ps1    # Windows (PowerShell)
./install.sh     # macOS / Linux
```

The installer:
- Copies the seven profile directories into `~/.hermes/profiles/`
- Substitutes your vault path into each profile's `mcp.json`

You'll see output like:

```
Installing memoria-librarian... done
Installing memoria-mapper... done
Installing memoria-socratic... done
Installing memoria-writer... done
Installing memoria-verifier... done
Installing memoria-coder... done
Installing memoria-linter... done
All seven profiles installed.
```

> This is the only time in the tutorials you'll use the terminal. Day-to-day operation happens entirely in Obsidian.

---

## Step 3 — Open the vault in Obsidian

1. Open Obsidian.
2. Click **Open folder as vault**.
3. Navigate to `~/memoria` and click **Open**.
4. If Obsidian asks about trusting the vault author, click **Trust and enable plugins**. Memoria's plugins are safe to enable.

Obsidian opens. You'll see the vault in Safe Mode because community plugins aren't enabled yet.

---

## Step 4 — Enable community plugins

1. Open **Settings** (gear icon, bottom left).
2. Under **Community plugins**, click **Turn on community plugins**.
3. Close Settings.

---

## Step 5 — Enable the bundled plugins

The starter vault **ships all eight required plugins pre-installed and configured** in `.obsidian/plugins/` — you do not browse or install them. The only action is to let Obsidian load them:

1. **Settings → Community plugins → turn off Restricted mode.**
2. Restart Obsidian. The eight bundled plugins activate on restart.

The eight that ship and should now be active:

| Plugin name | Plugin ID |
| --- | --- |
| Local REST API | `obsidian-local-rest-api` |
| Agent Client | `agent-client` |
| Dataview | `dataview` |
| Templater | `templater-obsidian` |
| QuickAdd | `quickadd` |
| Obsidian Citation Plugin | `obsidian-citation-plugin` |
| Callout Manager | `callout-manager` |
| Obsidian Git | `obsidian-git` |

Confirm all eight appear as enabled under Settings → Community plugins, then close Settings.

---

## Step 6 — Configure the Citation Plugin

The Citation Plugin needs to know where your BibTeX file lives. Most of this is pre-configured in the bundled `data.json`; confirm these values:

1. **Settings → Community plugins → Obsidian Citation Plugin → Options** (the gear icon next to it).
2. Confirm **Citation database path** is: `.memoria/library.bib`
3. Confirm **Literature note folder** is: `20-sources/01-papers`
4. The note body is **not** an external template file — this plugin stores it inline in `literatureNoteContentTemplate` (kept in sync with `00-meta/03-templates/paper-note.md`). There is no template-path setting to set here.
5. Close Settings.

---

## Step 7 — Wire up Zotero

Better BibTeX needs to auto-export your library to `.memoria/library.bib`.

1. In Zotero, open **Edit → Preferences → Better BibTeX**.
2. Under the **Citation keys** tab, confirm the citation key formula is: `[auth:lower][year][shorttitle1_0]`
   - If it's different, update it. This is the citekey format Memoria expects.
3. Right-click your library in the left panel → **Export Library**.
4. Format: **Better BibLaTeX**. Check **Keep updated**.
5. Save the file to: `<your-vault-path>/.memoria/library.bib`

Zotero will now keep that file updated every time you add or modify an item.

---

## Step 8 — Open Home.md

In the Obsidian file tree, open `Home.md` at the vault root. This is your vault's front door.

You'll see links to:
- The dashboard suite (`00-meta/01-dashboards/`)
- System status
- Your research directions

Click **Dashboard index** to open `00-meta/01-dashboards/index.md`. The dashboards will mostly show empty states — that's expected. They'll fill as you add notes.

---

## What you have

- ✓ Vault open in Obsidian
- ✓ All eight required plugins installed and enabled
- ✓ All seven profiles installed in `~/.hermes/profiles/`
- ✓ Zotero auto-exporting to `.memoria/library.bib`
- ✓ Dashboards loading (empty, ready for content)

---

## What's next

[Tutorial 02 — Your first note](02-your-first-note.md): capture a thought and turn it into your first permanent claim note. This is the Zettelkasten loop in miniature — you'll do the whole cycle in about 15 minutes.
