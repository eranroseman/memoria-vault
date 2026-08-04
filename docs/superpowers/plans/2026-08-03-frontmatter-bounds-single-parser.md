# Frontmatter Bounds Single Parser Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** One implementation of "where does YAML frontmatter end", so the prompt-injection scanner and the content-security masker stop classifying the same bytes differently.

**Architecture:** Three divergent implementations exist today: `vaultio._frontmatter_end` (`src/memoria_vault/runtime/vaultio.py:46`, strict `text.startswith("---")` + `find("\n---")`), `state/markdown._yaml_frontmatter_bounds` (`src/memoria_vault/runtime/state/markdown.py:163`, regex tolerating BOM, leading blank lines, CRLF, and a `...` terminator), and `vocabulary/schema._markdown_frontmatter` (`src/memoria_vault/runtime/vocabulary/schema.py:283`, `split("---\n", 2)`). They disagree on BOM-prefixed, blank-line-prefixed, and `...`-terminated documents — and the disagreement is security-relevant: `grounding._concept_scan_text` decides what the injection scanner reads via `vaultio.split_frontmatter`, while the masker uses the markdown bounds. The careful implementation (the regex) moves **down** into `vaultio` (which imports nothing from `state` — no cycle), becomes the only one, and the two forks delegate to it. Reading becomes uniformly tolerant; writing (`frontmatter_doc`) already emits the canonical strict form and is untouched.

**Tech Stack:** Python 3, `re`, PyYAML, pytest.

## Global Constraints

- Correctness gate: `python scripts/verify` must pass before the PR; `main` requires the `verify` and `gitleaks` checks.
- Stage explicit paths only, never `git add -A` (PreToolUse hook rejects it).
- Work in an isolated worktree, created at execution time per `superpowers:using-git-worktrees`: `git worktree add .claude/worktrees/frontmatter-bounds -b wip/frontmatter-bounds origin/main`, then `EnterWorktree(path: ".claude/worktrees/frontmatter-bounds")`.
- Tests build vaults only under pytest `tmp_path` — never a personal vault.
- Trust order: schema → tests → code → docs. If `tests/test_vaultio_okf.py` or `tests/test_frontmatter_contract.py` pins strict parsing for a case this plan loosens, stop and surface it before changing the test — OKF v0.2 is a format-level commitment.
- `tests/test_import_layering.py` guards module layering; `vaultio` gaining a `re` import and `state/markdown` importing `vaultio` must not violate it (vaultio sits below state today — this plan keeps that direction).
- Merge by squash.

## File Structure

- `src/memoria_vault/runtime/vaultio.py` — gains `FRONTMATTER_OPENING`, `frontmatter_bounds`; `parse_frontmatter` / `split_frontmatter` rewritten on top of it; `_frontmatter_end` deleted. The one home for the bounds question.
- `src/memoria_vault/runtime/state/markdown.py` — local `_yaml_frontmatter_bounds` deleted; imports the vaultio implementation.
- `src/memoria_vault/runtime/vocabulary/schema.py` — `_markdown_frontmatter` detects via vaultio; keeps its diagnostic error strings.
- `tests/test_frontmatter_bounds.py` — new; pins the previously divergent cases through the public `vaultio` interface.

---

### Task 1: `vaultio.frontmatter_bounds` — the tolerant implementation moves down

**Files:**
- Create: `tests/test_frontmatter_bounds.py`
- Modify: `src/memoria_vault/runtime/vaultio.py:46-83`

**Interfaces:**
- Consumes: nothing new.
- Produces: `frontmatter_bounds(text: str) -> tuple[int, int, int] | None` returning `(body_start, body_end, end)` character offsets of closed initial YAML frontmatter, and the compiled `FRONTMATTER_OPENING` regex (used by Task 3 to distinguish "missing" from "unterminated"). `parse_frontmatter` / `split_frontmatter` / `read_frontmatter` / `strip_frontmatter` keep their exact signatures.

- [ ] **Step 1: Write the failing tests**

Create `tests/test_frontmatter_bounds.py`:

```python
"""The one frontmatter-bounds implementation: vaultio.frontmatter_bounds."""

from __future__ import annotations

from memoria_vault.runtime.vaultio import (
    frontmatter_bounds,
    parse_frontmatter,
    split_frontmatter,
)

PLAIN = "---\ntype: note\n---\nbody\n"
BOM = "\ufeff---\ntype: note\n---\nbody\n"
BLANK_LEAD = "\n---\ntype: note\n---\nbody\n"
DOTS = "---\ntype: note\n...\nbody\n"
CRLF = "---\r\ntype: note\r\n---\r\nbody\r\n"


def test_plain_document() -> None:
    assert parse_frontmatter(PLAIN) == {"type": "note"}
    assert split_frontmatter(PLAIN) == ({"type": "note"}, "body\n")


def test_bom_document_has_frontmatter() -> None:
    assert parse_frontmatter(BOM) == {"type": "note"}
    assert split_frontmatter(BOM)[1] == "body\n"


def test_leading_blank_line_has_frontmatter() -> None:
    assert parse_frontmatter(BLANK_LEAD) == {"type": "note"}


def test_dots_terminator_closes_frontmatter() -> None:
    assert parse_frontmatter(DOTS) == {"type": "note"}
    assert split_frontmatter(DOTS)[1] == "body\n"


def test_crlf_document_has_frontmatter() -> None:
    assert parse_frontmatter(CRLF) == {"type": "note"}


def test_unclosed_frontmatter_is_absent() -> None:
    assert frontmatter_bounds("---\ntype: note\n") is None
    assert parse_frontmatter("---\ntype: note\n") == {}


def test_plain_body_is_absent() -> None:
    assert frontmatter_bounds("just body\n") is None
    assert split_frontmatter("just body\n") == ({}, "just body\n")


def test_horizontal_rule_mid_body_does_not_close_frontmatter_early() -> None:
    text = "---\ntype: note\n---\nbody\n---\nmore\n"
    assert split_frontmatter(text)[1] == "body\n---\nmore\n"
```

- [ ] **Step 2: Run the tests to verify the divergent cases fail**

Run: `python -m pytest tests/test_frontmatter_bounds.py -v`
Expected: `ImportError` (no `frontmatter_bounds`). After a quick `from memoria_vault.runtime.vaultio import parse_frontmatter` sanity run, the BOM / blank-lead / dots cases fail against the current implementation — that is the divergence being fixed.

- [ ] **Step 3: Implement bounds in vaultio and rewrite the readers on it**

In `src/memoria_vault/runtime/vaultio.py`: add `import re` to the imports; replace lines 46-83 (`_frontmatter_end`, `parse_frontmatter`, `read_frontmatter`, `split_frontmatter`, `strip_frontmatter`) with:

```python
FRONTMATTER_OPENING = re.compile(r"\A\ufeff?(?:[ \t]*\r?\n)*---[ \t]*(?:\r?\n)")
_FRONTMATTER_CLOSING = re.compile(r"(?m)^(?:---|\.\.\.)[ \t]*(?:\r?\n|$)")


def frontmatter_bounds(text: str) -> tuple[int, int, int] | None:
    """Return `(body_start, body_end, end)` offsets of closed initial YAML frontmatter.

    The one answer to "where does frontmatter end" — tolerant of a BOM,
    leading blank lines, CRLF line endings, and the YAML `...` terminator.
    Every reader (parsing, masking, schema validation) must use this; the
    writer (`frontmatter_doc`) emits the canonical strict form.
    """
    opening = FRONTMATTER_OPENING.match(text)
    if opening is None:
        return None
    closing = _FRONTMATTER_CLOSING.search(text[opening.end() :])
    if closing is None:
        return None
    return opening.end(), opening.end() + closing.start(), opening.end() + closing.end()


def parse_frontmatter(text: str) -> dict[str, Any]:
    """Parse leading YAML frontmatter, returning ``{}`` when absent or invalid."""
    bounds = frontmatter_bounds(text)
    if bounds is None:
        return {}
    body_start, body_end, _end = bounds
    try:
        data = yaml.safe_load(text[body_start:body_end]) or {}
    except yaml.YAMLError:
        return {}
    return data if isinstance(data, dict) else {}


def read_frontmatter(path: Path) -> dict[str, Any]:
    return parse_frontmatter(safe_read(path))


def split_frontmatter(text: str) -> tuple[dict[str, Any], str]:
    bounds = frontmatter_bounds(text)
    if bounds is None:
        return {}, text
    return parse_frontmatter(text), text[bounds[2] :]


def strip_frontmatter(text: str) -> str:
    return split_frontmatter(text)[1]
```

- [ ] **Step 4: Run the new tests and the vaultio suites**

Run: `python -m pytest tests/test_frontmatter_bounds.py tests/test_vaultio.py tests/test_vaultio_okf.py -v`
Expected: all pass. A failure in the OKF suite means the format pins strict parsing — stop per Global Constraints and surface the conflict rather than editing the OKF test.

- [ ] **Step 5: Commit**

```bash
git add tests/test_frontmatter_bounds.py src/memoria_vault/runtime/vaultio.py
git commit -m "vaultio: one tolerant frontmatter-bounds implementation"
```

---

### Task 2: `state/markdown` deletes its fork

**Files:**
- Modify: `src/memoria_vault/runtime/state/markdown.py:163-173`

**Interfaces:**
- Consumes: `vaultio.frontmatter_bounds` from Task 1.
- Produces: unchanged masker behavior; `_mask_yaml_frontmatter` / `_mask_yaml_mapping_frontmatter` keep their signatures.

- [ ] **Step 1: Delete the local bounds and import the one implementation**

In `src/memoria_vault/runtime/state/markdown.py`: delete the `_yaml_frontmatter_bounds` function (lines 163-173) and add to the module imports:

```python
from memoria_vault.runtime.vaultio import frontmatter_bounds as _yaml_frontmatter_bounds
```

The two call sites (`markdown.py:178`, `markdown.py:187`) keep their spelling; the module docstring's "zero SQLite" claim still holds (`vaultio` is pure text + yaml).

- [ ] **Step 2: Run the masking and layering suites**

Run: `python -m pytest tests/test_content_security.py tests/test_detectors.py tests/test_import_layering.py -v`
Expected: all pass — the imported implementation is character-for-character the regex that lived here.

- [ ] **Step 3: Commit**

```bash
git add src/memoria_vault/runtime/state/markdown.py
git commit -m "state/markdown: frontmatter bounds come from vaultio, not a fork"
```

---

### Task 3: `vocabulary/schema` delegates detection, keeps its diagnostics

**Files:**
- Modify: `src/memoria_vault/runtime/vocabulary/schema.py:283-297`

**Interfaces:**
- Consumes: `vaultio.frontmatter_bounds`, `vaultio.FRONTMATTER_OPENING` from Task 1.
- Produces: unchanged `_markdown_frontmatter(path: Path) -> tuple[dict, str, list[str]]` with the same four error strings (`missing YAML frontmatter`, `unterminated YAML frontmatter`, `invalid YAML frontmatter: {exc}`, `YAML frontmatter must be a map`).

- [ ] **Step 1: Rewrite the detector on the shared bounds**

In `src/memoria_vault/runtime/vocabulary/schema.py`: add `from memoria_vault.runtime import vaultio` to the imports, then replace `_markdown_frontmatter` (lines 283-297) with:

```python
def _markdown_frontmatter(path: Path) -> tuple[dict, str, list[str]]:
    text = path.read_text(encoding="utf-8")
    bounds = vaultio.frontmatter_bounds(text)
    if bounds is None:
        if vaultio.FRONTMATTER_OPENING.match(text) is None:
            return {}, text, ["missing YAML frontmatter"]
        return {}, text, ["unterminated YAML frontmatter"]
    body_start, body_end, end = bounds
    body = text[end:]
    try:
        data = yaml.safe_load(text[body_start:body_end]) or {}
    except yaml.YAMLError as exc:
        return {}, body, [f"invalid YAML frontmatter: {exc}"]
    if not isinstance(data, dict):
        return {}, body, ["YAML frontmatter must be a map"]
    return data, body, []
```

- [ ] **Step 2: Run the schema and contract suites**

Run: `python -m pytest tests/test_frontmatter_contract.py tests/test_precommit_schema.py -v`
Expected: all pass (the contract file tests `validate_frontmatter` semantics, which are untouched).

- [ ] **Step 3: Verify the fork count is one**

Run: `grep -rn 'find("\\n---"\|split("---' src/memoria_vault --include='*.py'`
Expected: no output — no remaining ad-hoc frontmatter splitting in `src/`.

- [ ] **Step 4: Full gate**

Run: `python scripts/verify`
Expected: pass. The floor sweep exercises every operation over seeded Concepts whose frontmatter is canonical — goldens must be byte-identical. A golden diff means some seeded document hit a divergent case; investigate before committing.

- [ ] **Step 5: Commit**

```bash
git add src/memoria_vault/runtime/vocabulary/schema.py
git commit -m "vocabulary: schema validation reads frontmatter through vaultio bounds"
```

---

## Completion

Follow `superpowers:finishing-a-development-branch`: push `wip/frontmatter-bounds`, PR to `main` (squash; `verify` + `gitleaks`). PR body names the security fix: the injection scanner (`grounding._concept_scan_text` → `vaultio.split_frontmatter`) and the content-security masker now agree on what is frontmatter for BOM-prefixed, blank-line-prefixed, CRLF, and `...`-terminated Concepts.
