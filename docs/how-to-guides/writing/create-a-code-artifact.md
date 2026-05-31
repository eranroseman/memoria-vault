
# How to create a code artifact

Scaffold a code-note linked to the motivating research, then hand off implementation to an external coding agent. Code in Memoria is a research output with provenance — the note records *why* this code exists and what claim it supports.

## Prerequisites

- A writing project in `40-workbench/<project-slug>/` with a `06-code/` subfolder
- The Coder profile installed
- An external coding agent available (Claude Code, Aider, Codex, or similar)

## Steps

**1. Create the `06-code/` subfolder** if it doesn't exist.

```powershell
New-Item -ItemType Directory "vault\40-workbench\<project-slug>\06-code\" -Force
```

**2. Start a Coder session to scaffold the code-note.**

```bash
hermes -p memoria-coder chat
# then, in the session:
/scaffold --project <project-slug> --name <artifact-name> --claim <citekey-or-claim-note>
```

For example:
```text
/scaffold --project jitai-receptivity-review --name figure-3-receptivity-curve --claim receptivity-decreases-under-high-cognitive-load
```

The Coder creates `40-workbench/<project-slug>/06-code/figure-3-receptivity-curve.md` — a `code-note` with:
- Link to the motivating claim note or source
- Empty sections for: Purpose, Implementation, Dependencies, How to run, Outputs

**3. Open the code-note and fill the Purpose section.**

The Coder generates the scaffold but the *purpose* is yours to state. Write 2–3 sentences: what this code produces, what research question it addresses, and which claim it supports.

**4. Hand off to the external coding agent.**

Open the code-note in a split pane alongside your preferred coding tool. Give the coding agent the code-note as context:

```text
# In Claude Code (or equivalent):
Read 40-workbench/<project-slug>/06-code/figure-3-receptivity-curve.md, 
then implement the code described in the Purpose section.
Place the implementation in the same 06-code/ directory.
```

The external agent writes the code; the Coder profile does not implement — it only scaffolds and records provenance.

**5. Review the implementation.**

Apply the same review gate as any other research output: does the code do what the Purpose section says? Does the output match what the claim asserts? Run the code and check the output.

**6. Update the code-note with final details.**

After review, fill in the remaining code-note sections:
- **Dependencies:** list packages and versions
- **How to run:** exact command to reproduce the output
- **Outputs:** what files are produced and where they land

Commit the code-note and the implementation together:

```bash
git add "vault/40-workbench/<project-slug>/06-code/"
git commit -m "code: figure-3 receptivity curve — <project-slug>"
```

## Verify

- The code-note exists in `06-code/` with all sections filled
- The implementation runs and produces the expected output
- The commit links code-note and implementation in the same changeset

## Related

- Coder profile design: [explanation/profiles/coder.md](../../explanation/profiles/coder.md)
- External coding agent workspace: [how-to/coder/external-agent-workspace.md](../../how-to-guides/writing/create-a-code-artifact.md)
- Code workflow reference: [how-to/workflows/downstream/code.md](../../how-to-guides/writing/create-a-code-artifact.md)
- ADR-6 (external coding agent delegation): [project/decisions/06-code-agent-attachment.md](../../../project-files/decisions/07-code-agent-attachment.md)
