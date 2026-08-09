---
title: "08: A captured first session"
parent: Tutorials
nav_order: 8
---

# 08: A captured first session

This is one complete, offline source-to-export traversal captured from the
public CLI in a fresh disposable vault. It is a five-minute read, not a claim
that the workflow takes five minutes. It begins at source capture; use
[Quickstart](../how-to-guides/setup/quickstart.md) if you need a vault first.

The input is a redistributable local text file and the digest uses the test
runner, so no provider, network, or private research material is involved.
Every command and output excerpt below came from one continuous run on
2026-08-08. For readability, the excerpts omit request envelopes, timestamps,
commits, hashes, and generated record IDs; those are transient run metadata.
All remaining paths, the Work ID `receptivity-source`, the evidence ID
`ev-2f01b307`, and the citation key are literal values from that run.

## Capture and check one source

The file contains three short sentences: an intervention invitation should
account for immediate response capacity; recent task burden can reduce that
capacity; and a delivery rule should weigh help against interruption. Capture
it, then inspect the catalog record before recording the PI's checked verdict
and export-safe citation key.

```bash
memoria work add --workspace . \
  --file receptivity-source.txt \
  --title "Local source on intervention receptivity" \
  --json
```

```json
{
  "ok": true,
  "result": {
    "check_status": "unchecked",
    "content_path": ".memoria/blobs/source-content/receptivity-source/content.txt",
    "raw_path": ".memoria/blobs/source-content/receptivity-source/raw/receptivity-source.txt",
    "text_status": "full-text",
    "work_id": "receptivity-source"
  }
}
```

```bash
memoria work export --workspace . receptivity-source --json
```

```json
{
  "api_version": "engine-read-api.v1",
  "ok": true,
  "work": {
    "check_status": "unchecked",
    "content_path": ".memoria/blobs/source-content/receptivity-source/content.txt",
    "raw_path": ".memoria/blobs/source-content/receptivity-source/raw/receptivity-source.txt",
    "text_status": "full-text",
    "title": "Local source on intervention receptivity",
    "work_id": "receptivity-source"
  }
}
```

```bash
memoria work update --workspace . receptivity-source \
  --check-status checked \
  --citekey local-receptivity-2026 \
  --json
```

```json
{
  "ok": true,
  "result": {
    "work": {
      "check_status": "checked",
      "citekey": "local-receptivity-2026",
      "work_id": "receptivity-source"
    }
  }
}
```

`checked` makes the Work eligible for checked-read operations; it is neither a
truth claim nor a substitute for a later evidence disposition. See
[What checked means](../explanation/knowledge/what-checked-means.md) for the
boundary.

Compile the deterministic digest next:

```bash
memoria work digest --workspace . receptivity-source --mode test --json
```

```json
{
  "ok": true,
  "result": {
    "digest_path": "digests/receptivity-source.md",
    "interview_count": 0,
    "payload": {"mode": "test", "work_id": "receptivity-source"}
  }
}
```

## Turn it into a checked claim and project slice

Create a claim note with its Work reference, then check it. The Work reference
is the source bridge; a project is connected later through the slice and
outline, not through a Note project field.

```bash
memoria new note --workspace . "Prompt timing should consider recent burden" \
  --mode claim \
  --work-id receptivity-source \
  --body "The captured source says that recent task burden can reduce a person's immediate capacity to respond to an intervention prompt." \
  --json
```

```json
{
  "ok": true,
  "path": "notes/prompt_timing_should_consider_recent_burden.md",
  "result": {"check_status": "unchecked"}
}
```

```bash
memoria check --workspace . notes/prompt_timing_should_consider_recent_burden.md --json
```

```json
{
  "ok": true,
  "result": {"check": {"status": "passed"}}
}
```

Frame and check a project, then let its query select the checked claim into an
outline:

```bash
memoria new project --workspace . "Burden-aware prompts" \
  --description "A small source-backed argument about prompt timing." \
  --direction "Explain why recent burden matters when deciding whether to deliver an intervention prompt." \
  --json
memoria check --workspace . projects/burden-aware_prompts/project.md --json
memoria project slice --workspace . projects/burden-aware_prompts/project.md \
  --query "recent burden prompt timing" --json
```

```json
{
  "ok": true,
  "path": "projects/burden-aware_prompts/project.md",
  "result": {"check_status": "unchecked"}
}
{
  "ok": true,
  "result": {"check": {"status": "passed"}}
}
{
  "ok": true,
  "result": {
    "member_count": 1,
    "members": [{
      "check_status": "checked",
      "path": "notes/prompt_timing_should_consider_recent_burden.md",
      "title": "Prompt timing should consider recent burden"
    }],
    "outline_path": "projects/burden-aware_prompts/outline.md",
    "retrieval_backend": "bm25"
  }
}
```

## Ask the checked vault

`ask` reports the sources it did use and the unknowns it did not fill. This run
has no unknowns; the empty array is part of the captured result, not a hidden
or inferred answer.

```bash
memoria ask --workspace . --question "What should prompt timing consider?" --json
```

```json
{
  "ok": true,
  "result": {
    "backend": "bm25",
    "sources": [
      {"path": "notes/prompt_timing_should_consider_recent_burden.md", "type": "note"},
      {"path": "fulltexts/receptivity-source.md", "type": "fulltext"},
      {"path": "projects/burden-aware_prompts/project.md", "type": "project"},
      {"path": "digests/receptivity-source.md", "type": "digest"}
    ],
    "unknowns": []
  }
}
```

## Compose, verify, and accept the evidence decision

Compose from the outline. The resulting paragraph is source-backed, but its
new evidence set is initially incomplete and therefore holds the draft. That
is a named finding, not a silent warning.

```bash
memoria project compose --workspace . projects/burden-aware_prompts/project.md --json
memoria project verify --workspace . projects/burden-aware_prompts/project.md --json
```

```json
{
  "ok": true,
  "result": {
    "draft_path": "projects/burden-aware_prompts/draft.md",
    "evidence_markers": [{
      "id": "ev-2f01b307",
      "items": ["receptivity-source#^p0001"]
    }]
  }
}
{
  "ok": true,
  "result": {
    "findings": [{
      "evidence_id": "ev-2f01b307",
      "kind": "evidence-incomplete",
      "severity": "high"
    }],
    "ready": false,
    "verification_status": "needs-review"
  }
}
```

Export is refused before the PI records a disposition. The CLI names the exact
blocking finding:

```bash
memoria project export --workspace . projects/burden-aware_prompts/project.md \
  --draft --format markdown --output exports/burden-aware-prompts.md --json
```

```json
{
  "ok": false,
  "result": {
    "error": "project draft is not export-ready: evidence-incomplete:ev-2f01b307"
  }
}
```

The PI accepts this limited claim because the captured source says exactly what
the claim says. The warrant records that judgment; it is not supplied by the
check operation.

```bash
memoria project resolve-evidence --workspace . projects/burden-aware_prompts/project.md \
  --evidence-id ev-2f01b307 \
  --decision accept \
  --reason "The captured local source directly supports the limited claim about recent burden and response capacity." \
  --warrant "The passage states that recent burden can reduce immediate capacity to respond." \
  --json
```

```json
{
  "decision": "accept",
  "evidence_id": "ev-2f01b307",
  "event": {
    "actor": "pi",
    "decision": "accept",
    "event": "resolved",
    "warrant": "The passage states that recent burden can reduce immediate capacity to respond."
  },
  "ok": true
}
```

Re-verify before exporting. The captured output is now ready and has no
findings:

```bash
memoria project verify --workspace . projects/burden-aware_prompts/project.md --json
```

```json
{
  "ok": true,
  "result": {
    "findings": [],
    "ready": true,
    "verification_status": "verified"
  }
}
```

## Export the cited draft

```bash
memoria project export --workspace . projects/burden-aware_prompts/project.md \
  --draft --format markdown --output exports/burden-aware-prompts.md --json
```

```json
{
  "ok": true,
  "result": {
    "format": "markdown",
    "output_path": "exports/burden-aware-prompts.md",
    "readiness": {"ready": true, "status": "verified"}
  }
}
```

The exported Markdown carries the citation key that resolves to the captured
Work:

````markdown
# Burden-aware prompts

Slice includes 1 checked notes.

## Prompt timing should consider recent burden

Source note: `notes/prompt_timing_should_consider_recent_burden.md`

# Prompt timing should consider recent burden

The captured source says that recent task burden can reduce a person’s immediate capacity to respond to an intervention prompt. [@local-receptivity-2026]

## References

```bibtex
@article{local-receptivity-2026,
  title = {{Local source on intervention receptivity}}
}
```
````

You have now seen one Work move through capture, checking, digesting, a
source-backed claim, a project slice, an evidence hold, PI disposition, and a
citation-bearing export. For the full paced lesson sequence, continue with
[Tutorials](README.md); for the mechanics of project drafting, use
[Compose a draft](../how-to-guides/project/compose-a-draft.md).
