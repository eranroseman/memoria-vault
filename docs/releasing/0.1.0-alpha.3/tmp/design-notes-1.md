Issues to resolve in alpha.3 - the UI build
After reviewing alpha.2 it became apparent that we have a lot of UI issues to resolve before adding the project functionality that will move to alpha.4. This is a list of issues found in no particular order. For each issue, research for best practices in similar uses cases, suggest various alternatives with the pros and cons of each. Group your solution into categories. Save your report in tmp/

Tutorial 02: Your first note

Can we pin memoria commands in the ribbon?
Can we use this to add the right command to the right place? https://community.obsidian.md/plugins/cmdr
https://community.obsidian.md/plugins/leader-hotkeys-obsidian
https://community.obsidian.md/plugins/obsidian-shellcommands
https://community.obsidian.md/plugins/slash-commander
https://community.obsidian.md/plugins/obsidian-better-command-palette
https://community.obsidian.md/plugins/apex-dashboard
Capture a fleeting note
Creating a new note should be done with a form. A form gives you structure, creates a clear divide between the note structure and the new text, and enables adding instructions that are not part of the final note. 
https://community.obsidian.md/plugins/modalforms 
Should we use this for the updated frontmatter?
https://community.obsidian.md/plugins/update-time-on-edit
Should we use this to enforce the use of frontmatter?
https://community.obsidian.md/plugins/propsec
And this?
https://community.obsidian.md/plugins/conditional-properties 
This looks like a great option for managing anything with a lifecycle  status or state:
https://community.obsidian.md/plugins/base-board 
Step 4 — See where fleeting notes surface
The system folder is for system files that can’t be in .memoria. If the user needs to access a file, it can’t be there. 
I created a fleeting note, and it is not in the fleeting base
Having to navigate folders to find dashboards is not the best solution.
Library workspace
Can we use Icons for the options on the left pane?
The one dataview per pane seems like a waste of real estate. They can all be together.
The pane is not a place for explanation. It should have information. It can have a help link that opens a relevant help page.
The workspace can open with multiple pages. Information that is frequently used and used for navigation should be in the left pane. More details, a deeper dive, or less frequent updates can go to the pages. Both can have buttons for frequently used actions. Bases can be embedded in pages. 
Tutorial 03: Bring in a paper

Step 3 — Judge the candidate card
No Inbox tab or Needs me view in Desk, nor a card in the inbox for the added URL
Step 4 — Read the paper
Expecting the user to find .memoria/data/extracts/<citekey>.md is unreasonable,, and the user should never access .memoria. It is not even in the folder view.
Step 5 — Write the source note

Does the librarian create the proposed source note?
Tutorial 04: Build a reading batch

Step 1 — Ask the co-PI for a batch

Asking the co-PI to perform a task is never the only way to do it. Every task should be able to be performed by the co-PI. I can ask it to create a fleeting note. But it is always on top of the standard process. Things that go only through the co-PI are only things that require LLM-human two-way conversation.
The capture from Zotero doesn’t work.
Tutorial 05: Synthesize toward a writing project

The source note should have a button to create a claim note linked to it.

home.md
It looks like the homepage plugin isn’t working
Buttons can be in a line to take up less space
The Status glance is a good idea. Can we make the status the link? If not, then it should be in pairs of status-link. Are there additional important statuses?
The Resolve card button seems broken.
The Delegate a task button is great. The task list should include a phrase, not just a verb. No need to write memoria- in front of the agent's name
The dashboard callout oben, but there is just a list of links.
Review all the homepage plugin's settings and ensure we are making full use of them. 
reference/system-actions.html 
Each action should include how it can be invoked

explanation/engines/
Engines are Memoria’s deterministic app.
As a rule of thumb, anywhere there are two names or parentheses, there is probably a naming issue. If there are apps, then why do we call the engines? 
What is CI invocation? It is never explained, and the context is not obvious, especially for a non-developer.
Ingest is a complex process with its own page that should be referred tor eference/ingest.html
Why is it a standalone page? To which category does it belong?
The file name engines/ingest/pipeline.py is too generic
The name should have the same form: ingest, search, cluster, verify, lint, ingesting, ingester, etc.
Processing and maintenance engines/apps VS bookkeeping and housekeeping apps/engines?
/reference/ingest 
includes information about other engines as well. 
There should be an engine reference page/s, with the procedural description of the engine, and an explanation page/s with the rationale
Site wide
These issues appear in these two pages, but I believe they are sitewide issues:
Both pages include references such as (D41), which likely refers to an annotation in purged work documents.
The links in the engine and ingest are broken and use a different format. I presume it's a website-wide phenomenon. We need to decide how to refer to a system file. Does engines/ingest/pipeline.py needs to be a link at all? How should it be formatted?
Why are all the links broken?
Do the ADR links add useful information or a distraction?
Few subheadings include the ADR in parentheses, followed by the link in the text. 
General
While some of the remarks refer to a specific page, they may be a system-wide issue/ 
Do we need this plugin https://community.obsidian.md/plugins/cli-rest-mcp ?
What are the files in the eval folder?
What is the system/vocabulary.md file?
Where are the catalog bases?
There is an error message saying that no Python is installed.
Do we need to show all properties in all note types?

co-PI should be Co-PI
There are two ways to navigate the system: bases and dashboards/reports. I don’t see a reason for the user to try to navigate using the files view. We should think about how to provide access to the navigation and how to cluster it in a way that makes sense.
Which views are needed for each base? Which dashboard goes hand in hand with each base? Which kanban view (https://community.obsidian.md/plugins/base-board ) can be used to present that information? How can we cluster them together based on the job to be done (https://strategyn.com/jobs-to-be-done/? How can we divide them between quick navigation on the left pane, dashboard pages for task-oriented work, and dashboard pages for deep work? How can we make the next action as frictionless as possible from the dashboard? Dashboards that are used often should be highly functional and include a help link. Diagnostic dashboards that are used infrequently should provide step-by-step guidance.  
The system comes up with this:


Client Agent 
Export should go to a dedicated folder in the system folder. 
Auto export should be on. Open note after export should be off.
Display name should be Memoria Co-PI.
Workspaces
The workspace design is lacking. First, it doesn’t seem to take advantage of the plugin capabilities. https://obsidian.md/help/plugins/workspaces
Both use home.md as the only open tab, which is pointless since it's always open.  They don’t open th co-PI in the right pane, which should be relevant at least for the library.
The home workspace
What does the name mean? It should be self-describing and thematic, and it’s neither. It has the default home page and file folder with the board state in the right pane. The text description is enigmatic and has an unhelpful link. There is nothing to hint at what the information in it means or what one might do with it.
The library
The reading pipeline looks the same as the board state and shares the same design failures. Why is each one on a different side?
The right pane is empty because there is no data, and is even more anigamatic
Home.md
This one repeats on both. It is supposed to be the system's starting point and control panel. It is always on the page that the PI can use to perform the most frequent action and provide the most needed information. I don’t see a point in reviewing it. It should be discarded and redesigned from scratch.
A few design guidelines:
All 3 workspace should share the same layout.
They should present only the relevant information and enable drill down where needed.  
They should provide easy access to all relevant actions
The home.md is the starting point. It provides what is always needed in all workspaces. If there is no such need for a common card, then it should be discarded.
We can use something like https://community.obsidian.md/plugins/buttons-panel https://community.obsidian.md/plugins/synaptic-view https://community.obsidian.md/plugins/buttons 
The left pane is for navigation. It will enable you to get quickly to relevant stuff.
The co-PI should be in the right pane.
We should think about the workspaces as gates to the system. The first gate is the system/maintenance/housekeeping. This is where the user goes when a system issue requires their attention. The status bar should indicate it. 
The second gate is the sources/library gate. It should enable the user to navigate the catalog and related notes and reports (source notes, gap reports, candidate cards) using bases and network views. It should enable the user to:
See if there are any bookkeeping issues related to the health of the catalog and the source notes that require their attention 
Find new sources based on gap analysis (cards, reports, etc.). 
The next gate is the knowledge base/ZK one. It should enable the user to:
Resolve issues with the links network, including hubs and indexes ( on a second thought, maybe there should be a separate bookkeeping gate that assesses the health of both entities and notes the network, and a separate knowledge/library gate that manages notes)
Although the project is outside the scope of this build, we should have a clear understanding of the parts that connect to the catalog and notes. The basic artifacts of projects are:
The research question - this one informs the next stages 
The knowledge map - the system scan notes and entities, and presents the part of the knowledge network that is relevant to the project, and open issues with the network. 
Knowledge gap - the system identifies gaps in the notes that can be closed using existing entities, including new hubs, indexes, and claims-related notes that can be added based on the existing catalog. This artifact informs the next one.  
Sources gap - new relevant items that can be added to the catalog. 
Outline - this one derived from the knowledge map. 
This is an iterative process. Closing a gap changes the knowledge map. The gaps and map may inform changes in the research question, etc. This gate is the driver for all the catalog/library/source work, and it is the basis for the writing and coding. 

