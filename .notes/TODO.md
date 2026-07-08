
# TODO

<!-- cspell:words SQLite Crossref OpenAlex Unpaywall DOI ISBN PubMed arXiv CSL BibTeX -->
<!-- cspell:words PydanticAI pydantic allowlist frontmatter idempotency Obsidian Hermes Memoria Ollama OKF citekey Zotero materialize Typer sqlite fsync HANS Kilo qmd jsonl -->


Rethink the  from first principles, propose a clean-slate design for it based on requirements and best practice, not current implementation

search for best practice in similiar use cases and suggest a design from first principles, propose a clean-slate design for it based on requirements and best practice, not current implementation


Suggest which ADR can be retired. Suggest also modifications to exisiting ADRs that will enable retitirng ADRs

start gates/spikes

evaluate each OKF feature use in Memoria. Treat this as a fresh analysis: do not reference or carry over any prior findings. Report for eace one if it is used, assess whether usage is optimal; if it is not used, assess whether it should be. In both cases, explain how it could improve Memoria’s alpha.11 design. Then propose a clean-slate  architecture based on requirements and OKF best practices, not the current implementation, with clear recommendations. 

## Hermes

Ensure we are using the latest bersion of Hermes and evaluate each Hermes feature for Memoria. Treat this as a fresh analysis: do not reference or carry over any prior findings. Report for eace one if it is used, assess whether usage is optimal; if it is not used, assess whether it should be. In both cases, explain how it could improve Memoria’s design. Then propose a clean-slate Memoria architecture based on requirements and Hermes best practices, not the current implementation, with clear recommendations. Verify your recommendation with the local installation.

## Fidelity Scan

Scan all files in memoria-vault/main and identify duplicate or near-duplicate content, paraphrased restatements, contradictions, inconsistencies, implementation documentaion gaps, design conformance, overloaded terms used in conflicting contexts, idiosyncratic and non-standard terminology — including subtle ones across documents. Treat this as a fresh analysis: do not reference or carry over any prior findings. For each issue found, cite the relevant files and explain your reasoning. Be thorough and systematic; consistency across this vault is a high-priority concern.

## Fidelity Scan fix repeat

Scan all files in memoria-vault/main, identify duplicate or near-duplicate content, paraphrased restatements, contradictions, inconsistencies, implementation documentaion gaps, design conformance, overloaded terms used in conflicting contexts, idiosyncratic and non-standard terminology — including subtle ones across documents. Treat this as a fresh analysis: do not reference or carry over any prior findings. For each issue found, cite the relevant files and explain your reasoning. Be thorough and systematic; consistency across this vault is a high-priority concern. Resolve all issues. Repeat until no major findings. 

## Diátaxis

Analyze all files in docs/explanation docs/how-to-guides docs/tutorials docs/reference for alignment with Diátaxis based on their folder and docs/design as explenation, and all readme.md files including on docs/ root based on best practice for index page. For each file: Identify expected type, Assess alignment, Flag issues. Use subagents to parallelize the work. Summarize findings and produce a concise report with per-file actionable edit recommendations.

Resolve all the issues you found

## Names  

Ensure all names across the project and the code are self-explanatory and aligned with industry-standard naming conventions and software development best practices, with special attention to Hermes and Obsidian contexts.


##
DO in this order:
- QA your work on alpha.7
- Ensure WSL is updated and wired to run with local llm
- Ensure docs/ is updated beased on your work on alpha.7
- Review all files in releasing/ tmp/. If they were implemnted ensure their content was captured in adrs and system documentation. If they weren't move them to docs/releasing/0.1.0-alpha.8/tmp. delete al files in older tmp/ folders when you are done.
- Ensure docs/how-to-guides and docs/reference cover all system funtionality and that their information is up to date. 



- Analyze all files in docs/explanation docs/how-to-guides docs/tutorials docs/reference for alignment with Diátaxis based on their folder, and readme.md based on best practice for index page. For each file: Identify expected type, Assess alignment, Flag issues. Use subagents to parallelize the work. Summarize findings and produce a concise report with per-file actionable edit recommendations.





## Docs

Files in memoria-vault/ should not include history of the system. We didn't even finish implementing all the features of ver 0.1. People don't need to be confused by every decision we did along the way. The only historical records should be in docs/adr docs/releasing





## Other



Ensure all folders, filenames, classes, functions, variables, tests, skills, etc. names and naming schemes are self explanatory and following industry standards and best practices for software development in general and hermes and Obsidian specifically.

Writer vs author vs cowriter vs coauthor scribe copyist penman scribbler

Expalin how this:
Run `Cmd/Ctrl-P` → **Memoria: verify draft** with the draft as the active note (if you want help shaping the scope, talk it through with the Co-PI first — but the verify pass is the command):
Is better then this:
Run `Cmd/Ctrl-P` → **Memoria: verify draft** with the draft as the active note, or ask in the Co-PI pane if you want help shaping the scope:

Fix the sample vault, "Optional and skippable", and the anti patterns. 


a 450-line AGENTS.md has the same failure mode as a 450-page employee handbook: nobody reliably holds all of it, each rule dilutes attention on the others, and the count grows monotonically because every incident adds one and none get retired. That's exactly what happened with the ADRs — 90 of them, "caused confusion and mistakes," consolidated to six. AGENTS.md is on the same trajectory, and today I made it worse, not better.

Where it doesn't translate: rules-as-a-substitute-for-judgment assumes the workers could carry the judgment themselves if you hired well. Your workers reset to zero every session. The repo's written rules aren't distrust of good people — they're the only institutional memory the workers have. The 73-file commit sweep can't be prevented by "hiring someone who's been burned before," because no session has been burned before. Something has to persist, and you just (correctly) decided that something is the repo, not my memory.

But the project's own doctrine already names the right resolution, and it's sharper than the aphorism: "enforcement is a mechanism, not a label." A rule that lives in prose is the weak form — it's a plea to attention. The strong form makes the failure impossible: the worktree rule becomes a script that just creates one; "stage by explicit path" becomes a hook that rejects git add -A; the docs-doctor and negative deny-tests instead of "keep docs in sync." Every prose rule in AGENTS.md is really a mechanism that hasn't been built yet, or a rule that isn't load-bearing enough to deserve one — and the second kind should probably be deleted rather than obeyed. That's also the honest test for what I added today: "prefix Projects-v2 calls with env -u GITHUB_TOKEN" is a rule; a gh wrapper that does it would be a mechanism, and the rule could die.