# Human Acceptance Wizard Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Create a one-run Bash wizard that guides a PI through all remaining human-only acceptance actions without automating any judgment, desktop interaction, or real-vault mutation.

**Architecture:** `scripts/human-acceptance-wizard.sh` copies the shared wizard library verbatim, then adds a small authored layer. The layer chooses a section, writes human-entered observations to a private temporary log, displays exact commands and UI journeys, and uses confirmation gates before a human can take an irreversible action. A small static pytest module pins the non-interactive command-line contract.

**Tech Stack:** Bash, the shared wizard template, ShellCheck, and pytest.

## Global Constraints

- The script section above the `STAGES` marker must be byte-identical to `/home/eranr/.agents/skills/wizard/template.sh` above its marker.
- The wizard must never execute `memoria`, `sqlite3`, `git`, `rm`, Obsidian, Zotero, or provider commands. It displays those commands for the PI to run separately.
- It must not capture, print, write, or pass onward credentials or handshake tokens. Do not call `ask_secret`, `write_env`, `set_secret`, or `set_var`.
- `--section` accepts exactly `all`, `plugin`, `canvas`, and `loop13`; `--help` is non-interactive; another value exits 2 with usage.
- Use a new `mktemp` run log under `${TMPDIR:-/tmp}` unless `RUN_LOG` explicitly supplies a path. Set mode 600. The log is working evidence, not an acceptance finding or a committed artifact.
- Each visual, licensing, authority, triage, stop-rule, and cleanup decision remains PI-owned. A stage may explain, prompt, and record, but may not decide or run the action.
- Preserve plan vocabulary and literal commands. Where the plan leaves an interface unspecified, say so and direct the PI to inspect `memoria --help` or record the ambiguity; never invent it.
- Validate only with `bash -n`, ShellCheck if installed, focused pytest, and static trace review. Do not treat the current full-gate MCP-environment failure as a change failure.

---

## File Structure

- `scripts/human-acceptance-wizard.sh` — executable one-run human guidance and evidence log.
- `tests/test_human_acceptance_wizard.py` — static contract for help, section validation, section vocabulary, and human-only safeguards.
- `docs/superpowers/specs/2026-08-07-human-acceptance-wizard-design.md` — accepted design; no change expected during implementation.

### Task 1: Establish the non-interactive contract and authored wizard core

**Files:**
- Create: `tests/test_human_acceptance_wizard.py`
- Create: `scripts/human-acceptance-wizard.sh`

**Interfaces:**
- Consumes: `/home/eranr/.agents/skills/wizard/template.sh` and the accepted design document.
- Produces: `scripts/human-acceptance-wizard.sh --help` and `--section <all|plugin|canvas|loop13>`.

- [ ] **Step 1: Write the failing static contract test.**

Create `tests/test_human_acceptance_wizard.py` with this content:

```python
from __future__ import annotations

import subprocess
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
WIZARD = ROOT / "scripts/human-acceptance-wizard.sh"


def _run(*args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["bash", str(WIZARD), *args],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
    )


def test_help_is_noninteractive_and_lists_every_section() -> None:
    result = _run("--help")

    assert result.returncode == 0
    assert "Usage:" in result.stdout
    for section in ("all", "plugin", "canvas", "loop13"):
        assert section in result.stdout


def test_unknown_section_is_rejected_without_starting_a_wizard() -> None:
    result = _run("--section", "unknown")

    assert result.returncode == 2
    assert "Usage:" in result.stderr


def test_human_only_safety_contract_is_visible_in_the_script() -> None:
    source = WIZARD.read_text(encoding="utf-8")

    assert "do not enter secrets" in source
    assert "Never print or pass a handshake token" in source
    assert "Do not automate Obsidian" in source
    assert "Do not run this command from the wizard" in source
```

- [ ] **Step 2: Run the focused test to verify it fails.**

Run: `python -m pytest tests/test_human_acceptance_wizard.py -q`

Expected: FAIL because the wizard file does not exist.

- [ ] **Step 3: Create the exact template library and core authored layer.**

Create `scripts/human-acceptance-wizard.sh` by copying the template byte-for-byte through the `STAGES` marker. Replace only the template example below that marker with the following core. Leave stage functions for later tasks at the named call sites.

```bash
SECTION="all"

usage() {
  cat <<'USAGE'
Usage: scripts/human-acceptance-wizard.sh [--section all|plugin|canvas|loop13]

Guide the PI through the remaining human-only acceptance checks. The wizard
does not execute Memoria, SQLite, Git, Obsidian, Zotero, or provider commands.
USAGE
}

while (($#)); do
  case "$1" in
    --section)
      (($# >= 2)) || { usage >&2; exit 2; }
      SECTION="$2"
      shift 2
      ;;
    --help|-h)
      usage
      exit 0
      ;;
    *)
      usage >&2
      exit 2
      ;;
  esac
done

case "$SECTION" in
  all) TOTAL_STAGES=31 ;;
  plugin) TOTAL_STAGES=13 ;;
  canvas) TOTAL_STAGES=6 ;;
  loop13) TOTAL_STAGES=12 ;;
  *) usage >&2; exit 2 ;;
esac

umask 077
RUN_LOG="${RUN_LOG:-$(mktemp "${TMPDIR:-/tmp}/memoria-human-acceptance.XXXXXX.md")}"
touch "$RUN_LOG"
chmod 600 "$RUN_LOG"

record() {
  local title="$1" observation=""
  ask observation "Record pass, fail, or blocked evidence (do not enter secrets):"
  {
    printf '## %s\n\n' "$title"
    printf '%s\n\n' "$observation"
  } >> "$RUN_LOG"
}

show_command() {
  say "Do not run this command from the wizard. Copy it into your own terminal after reviewing it."
  printf '\n%s\n\n' "$1"
}

include_section() {
  [[ "$SECTION" == "all" || "$SECTION" == "$1" ]]
}

banner "Memoria human acceptance checks"
say "Run log: $RUN_LOG"
say "Never print or pass a handshake token. Do not automate Obsidian, Zotero, licensing, triage, or stop decisions."
pause "Press Enter after you have read the safety boundary."
```

- [ ] **Step 4: Add an executable bit and run the focused tests.**

Run: `chmod +x scripts/human-acceptance-wizard.sh && python -m pytest tests/test_human_acceptance_wizard.py -q`

Expected: PASS.

- [ ] **Step 5: Check template integrity.**

Run:

```bash
python - <<'PY'
from pathlib import Path

template = Path('/home/eranr/.agents/skills/wizard/template.sh').read_text(encoding='utf-8')
wizard = Path('scripts/human-acceptance-wizard.sh').read_text(encoding='utf-8')
marker = '# ──────────────────────────────────────────────────────────────────────────\n# STAGES'
assert wizard.split(marker, 1)[0] == template.split(marker, 1)[0]
PY
```

Expected: exit 0.

### Task 2: Add the U3 plugin and canvas manual sections

**Files:**
- Modify: `scripts/human-acceptance-wizard.sh`
- Modify: `tests/test_human_acceptance_wizard.py`

**Interfaces:**
- Consumes: Task 1's `include_section`, `show_command`, and `record` helpers; U3-PLUG.11 and U3-CANVAS.5 in `docs/superpowers/plans/2026-07-15-surfaces-bootstrap-and-plugins.md`.
- Produces: thirteen plugin stages and six canvas stages, each with manual evidence collection.

- [ ] **Step 1: Extend the static test for both manual sections.**

Append this test:

```python
def test_plugin_and_canvas_sections_keep_their_human_checks_visible() -> None:
    source = WIZARD.read_text(encoding="utf-8")

    for text in (
        "Memoria · connecting…",
        "Memoria · engine missing",
        "Memoria · server down",
        "Memoria: Relate…",
        "rebuttal",
        "Memoria: Fork canvas to scratch",
        "Memoria fork: 1 edge(s) diverged",
        "Memoria: Graduate scratch canvas edges",
        "git status --short",
    ):
        assert text in source
```

- [ ] **Step 2: Run the focused test to verify it fails.**

Run: `python -m pytest tests/test_human_acceptance_wizard.py -q`

Expected: FAIL because the U3 manual language is absent.

- [ ] **Step 3: Implement the U3 plugin stages under `if include_section plugin; then`.**

Add thirteen `stage` calls, in this exact order: open disposable `test-vault/u3-plug-manual`; verify Settings → Memoria; run the token non-persistence snippet only after a real connection; inspect Attention; exercise `j`, `k`, and `Enter`; open evidence and queue Resolve; use `Memoria: Relate…` with a required blank-To validation and a completed `rebuttal` edge; stop and recover the server; mask and restore the engine; set and restore `/bin/false`; install and inspect one light and one dark community theme; observe two-minute unfocused polling and immediate refocus; and confirm before removing the disposable vault.

For every command, call `show_command` with the exact plan command. For every desktop action, use `step` with the described Obsidian path and `record` after the outcome. Before the `memoria serve --stop`, engine-mask, `/bin/false`, and `rm -rf test-vault/u3-plug-manual` instructions, use `confirm`; if it returns false, record the skipped step and continue. The cleanup stage must say to verify the exact disposable target first.

Include the plan's token probe verbatim as an inert display block. It must call `memoria handshake --vault test-vault/u3-plug-manual --json`, retain the token only in the Python process, and assert zero token-bearing files. Do not substitute `--workspace`.

- [ ] **Step 4: Implement the six U3 canvas stages under `if include_section canvas; then`.**

Add stages for: recording a pre-run `git status --short` baseline; opening `projects/<p>/argument.canvas` and checking the top-left `read-only, regenerated` banner; confirming then queuing `Memoria: Fork canvas to scratch`; opening `scratch-<name>.canvas` and verifying it is editable without a banner; manually drawing exactly one `supports` edge and checking `Memoria fork: 1 edge(s) diverged`; confirming then running `Memoria: Graduate scratch canvas edges`, proving the relation after the worker runs, and comparing the final Git status with the baseline.

State the documented success and failure notices. Require the PI to record source and target paths, request/result evidence, and any unaccounted vault file. Do not provide an automation substitute for Canvas drawing, visual review, or the worker result.

- [ ] **Step 5: Run focused checks.**

Run:

```bash
python -m pytest tests/test_human_acceptance_wizard.py -q
bash -n scripts/human-acceptance-wizard.sh
shellcheck scripts/human-acceptance-wizard.sh
```

Expected: every command exits 0.

### Task 3: Add the LOOP.13 real-vault protocol

**Files:**
- Modify: `scripts/human-acceptance-wizard.sh`
- Modify: `tests/test_human_acceptance_wizard.py`

**Interfaces:**
- Consumes: Task 1 helpers; the corrected W.4 block in `docs/superpowers/plans/2026-07-17-o2-staged-import.md`; Task LOOP.13 in `docs/superpowers/plans/2026-07-15-alpha23-usable-loop.md`.
- Produces: twelve PI-owned LOOP.13 stages and acceptance-record checklist.

- [ ] **Step 1: Extend the static test for LOOP.13's stop and evidence rules.**

Append this test:

```python
def test_loop13_section_names_the_real_vault_and_stop_rules() -> None:
    source = WIZARD.read_text(encoding="utf-8")

    for text in (
        "fresh real vault",
        "never test-vault",
        "stage1.bib",
        "stage2.bib",
        "seeded-error-verdict",
        "import-run.v1",
        "staged-import",
        "Do not hand-write",
        "1000-scale is out of scope",
        "staged-import-acceptance-run.md",
    ):
        assert text in source
```

- [ ] **Step 2: Run the focused test to verify it fails.**

Run: `python -m pytest tests/test_human_acceptance_wizard.py -q`

Expected: FAIL because LOOP.13 language is absent.

- [ ] **Step 3: Implement the twelve LOOP.13 stages under `if include_section loop13; then`.**

Add stages for: licensed 10- and 100-work Zotero exports and a fresh real vault; initialization, project framing, seed installation, and a passed seeded-error verdict; a live grounded first answer and telemetry measurement; frozen-fixture inspection; stage-1 import and enrichment drain; separate `ask`/`explore` timing, attention/worklist, event-log, and database-size evidence; PI triage of every attention item; disposition instrumentation proof; the explicit stop-rule decision and safe `update_rule_status` command; a conditional 100-work repeat; Phase-2 rehearsal; and a PI-authored acceptance record plus optional commit instruction.

Display the plan commands verbatim. Ask the PI to copy the exact frozen fixture arguments rather than retyping them. Say that a failed seeded-error verdict, zero disposition count, a stop-rule observation, a provider-policy prompt, or latency that breaks session flow is a result to record and may block later stages. Never author a judgment, select an attention disposition, fire a rule automatically, or perform an import.

In the stop stage, show the `update_rule_status` command and explain that the PI must never hand-write `.memoria/config/decision-rules.yaml`. In the Stage-2 stage, state that it runs only after Stage 1's instrumentation proof and no stop decision. In the final stage, list every required record field and say that the PI may commit only after writing and reviewing the resulting artifact.

- [ ] **Step 4: Run focused checks.**

Run:

```bash
python -m pytest tests/test_human_acceptance_wizard.py -q
bash -n scripts/human-acceptance-wizard.sh
shellcheck scripts/human-acceptance-wizard.sh
```

Expected: every command exits 0.

### Task 4: Perform the static manual-requirement trace

**Files:**
- Modify: `docs/superpowers/specs/2026-08-07-human-acceptance-wizard-design.md` only if the implemented behavior differs from the accepted design.

**Interfaces:**
- Consumes: the finished wizard and the three owning plan tasks.
- Produces: checked static validation evidence; no automatic run of the wizard.

- [ ] **Step 1: Trace every requirement to a stage.**

Read the completed wizard beside U3-PLUG.11, U3-CANVAS.5, LOOP.13, and the corrected O2 W.4 protocol. Confirm each manual action, confirmation gate, exact literal command, evidence requirement, prohibition, and output artifact has a corresponding stage.

- [ ] **Step 2: Re-run the target checks.**

Run:

```bash
python -m pytest tests/test_human_acceptance_wizard.py -q
bash -n scripts/human-acceptance-wizard.sh
shellcheck scripts/human-acceptance-wizard.sh
git diff --check
```

Expected: every command exits 0.

- [ ] **Step 3: Check executable mode and non-interactive paths.**

Run:

```bash
test -x scripts/human-acceptance-wizard.sh
scripts/human-acceptance-wizard.sh --help
! scripts/human-acceptance-wizard.sh --section unknown
```

Expected: `--help` prints usage without prompting; the unknown section prints usage and exits 2.

- [ ] **Step 4: Do not run the wizard end-to-end.**

Do not launch browsers, Obsidian, Zotero, provider access, real-vault commands, or a cleanup action. Hand the script to the PI with its run command and generated log-path behavior.

## Self-review checklist

- Every human-only action from all three plans has a wizard stage.
- Every plan command is displayed, not executed.
- The library remains unchanged above `STAGES`.
- The log cannot silently become a committed acceptance result.
- The implementation requires no new runtime dependency or CI configuration.
