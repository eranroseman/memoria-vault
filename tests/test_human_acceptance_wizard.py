from __future__ import annotations

import re
import subprocess
from pathlib import Path

import pytest

pytestmark = pytest.mark.static


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


def test_canvas_baseline_states_the_disposable_vault_precondition() -> None:
    source = WIZARD.read_text(encoding="utf-8")
    canvas_section = source.split("if include_section canvas; then", 1)[1].split(
        "if include_section loop13; then", 1
    )[0]
    baseline_stage = canvas_section.split('stage "Capture the Canvas Git baseline"', 1)[1].split(
        'stage "Inspect the generated Canvas banner"', 1
    )[0]

    for text in (
        "disposable vault under test-vault/",
        "never a personal vault",
        "memoria available through the plugin's Engine command",
    ):
        assert text in baseline_stage


def test_plugin_server_down_stage_requires_observation_of_no_silent_retry() -> None:
    source = WIZARD.read_text(encoding="utf-8")
    plugin_section = source.split("if include_section plugin; then", 1)[1].split(
        "if include_section canvas; then", 1
    )[0]
    server_down_stage = plugin_section.split('stage "Exercise the server-down state"', 1)[1].split(
        'stage "Check both community-theme variants"', 1
    )[0]

    for text in (
        "red Memoria · server down",
        "remediation naming the log path",
        "memoria serve --workspace",
        "Observe and record that there is no infinite silent retry.",
    ):
        assert text in server_down_stage


def test_plugin_resolve_queue_requires_confirmation_in_its_own_stage() -> None:
    source = WIZARD.read_text(encoding="utf-8")
    plugin_section = source.split("if include_section plugin; then", 1)[1].split(
        "if include_section canvas; then", 1
    )[0]

    resolve_stage = plugin_section.split('stage "Open evidence and queue Resolve"', 1)[1].split(
        'stage "Create and complete a rebuttal relation"', 1
    )[0]
    resolve_confirmation = 'confirm "Queue Resolve / resolve-attention now?"'
    assert "Open an evidence link" in resolve_stage
    assert resolve_confirmation in resolve_stage
    assert "Click Resolve" in resolve_stage
    assert (
        resolve_stage.index("Open an evidence link")
        < resolve_stage.index(resolve_confirmation)
        < resolve_stage.index("Click Resolve")
    )
    assert 'record "Resolve queue result"' in resolve_stage
    assert 'record "Resolve queue skipped"' in resolve_stage


def test_plugin_rebuttal_submission_requires_confirmation_in_its_own_stage() -> None:
    source = WIZARD.read_text(encoding="utf-8")
    plugin_section = source.split("if include_section plugin; then", 1)[1].split(
        "if include_section canvas; then", 1
    )[0]
    rebuttal_stage = plugin_section.split('stage "Create and complete a rebuttal relation"', 1)[
        1
    ].split('stage "Stop and recover the server"', 1)[0]
    rebuttal_confirmation = 'confirm "Submit the completed rebuttal graph edge now?"'
    assert "Try Queue edge with To blank" in rebuttal_stage
    assert rebuttal_confirmation in rebuttal_stage
    assert "Submit a rebuttal" in rebuttal_stage
    assert (
        rebuttal_stage.index("Try Queue edge with To blank")
        < rebuttal_stage.index(rebuttal_confirmation)
        < rebuttal_stage.index("Submit a rebuttal")
    )
    assert 'record "Rebuttal edge result"' in rebuttal_stage
    assert 'record "Rebuttal edge submission skipped"' in rebuttal_stage


def test_plugin_canvas_handoff_is_a_nonstage_pr_evidence_handoff() -> None:
    source = WIZARD.read_text(encoding="utf-8")
    marker = "# STAGES"
    authored = source.split(marker, 1)[1]
    handoff_guard = (
        'if [[ "$SECTION" == "all" || "$SECTION" == "plugin" || "$SECTION" == "canvas" ]]; then'
    )
    assert handoff_guard in authored
    handoff = authored.split(handoff_guard, 1)[1].split("\nfi", 1)[0]

    assert authored.index(handoff_guard) > authored.index("if include_section loop13; then")
    assert "stage " not in handoff
    assert "Review the private temporary run log at $RUN_LOG." in handoff
    assert (
        "Transfer plugin and Canvas pass, fail, blocked, and skipped outcomes "
        "to the relevant PR description."
    ) in handoff
    assert "The temporary log is working evidence, not the acceptance artifact." in handoff
    finish_call_pattern = r"(?m)^\s*finish(?:\s|$)"
    assert re.search(finish_call_pattern, "  finish\n")
    assert not re.search(finish_call_pattern, authored)


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
