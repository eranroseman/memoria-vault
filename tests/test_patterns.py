"""Prompt operations validate as product policies; the runtime runner enforces rules."""

import re
from pathlib import Path

import yaml

from memoria_vault.runtime import patterns
from memoria_vault.runtime.operations import load_operation_policy
from memoria_vault.runtime.subsystems.lib import schema

SRC = Path(__file__).resolve().parent.parent / "vault-template"
PATTERNS = SRC / "system" / "patterns"
OPERATIONS = (
    Path(__file__).resolve().parent.parent / "src/memoria_vault/product/capabilities/operations"
)


def _frontmatter(path: Path) -> dict:
    m = re.match(r"^---\n(.*?)\n---", path.read_text(encoding="utf-8"), re.S)
    return yaml.safe_load(m.group(1))


def _operation_files() -> list[Path]:
    return [p for p in OPERATIONS.glob("*.md") if p.name != ".gitkeep"]


def _prompt_operation_files() -> list[Path]:
    return [p for p in _operation_files() if "{{input}}" in p.read_text(encoding="utf-8")]


def _targeted_operation_files() -> list[Path]:
    return [p for p in _operation_files() if _frontmatter(p).get("output_target")]


def _patch_operation_manifest(monkeypatch, operation_id: str, text: str) -> None:
    item = {
        "path": f"product/capabilities/operations/{operation_id}.md",
        "text": text,
        "frontmatter": yaml.safe_load(re.match(r"^---\n(.*?)\n---", text, re.S).group(1)),
    }

    def read_manifest(capability_type: str, capability_id: str) -> dict:
        if capability_type == "operation" and capability_id == operation_id:
            return item
        raise FileNotFoundError(capability_id)

    monkeypatch.setattr(patterns, "iter_capability_manifests", lambda _type: [item])
    monkeypatch.setattr(patterns, "read_capability_manifest", read_manifest)


def test_shipped_operations_validate_against_policy_loader():
    shipped = _operation_files()
    assert len(shipped) >= 6, "the vault ships checked operation policies"
    for p in shipped:
        load_operation_policy(SRC, p.stem)


def test_no_shipped_prompt_operation_targets_a_gated_zone():
    gated = tuple(schema.gated_prefixes(schema.load_folders()))
    assert _prompt_operation_files(), "the vault ships runnable prompt operations"
    for p in _prompt_operation_files():
        target = (_frontmatter(p).get("output_target") or "").lstrip("/")
        assert not target.startswith(gated), f"{p.name} targets a gated zone"


def test_every_targeted_operation_has_an_input_slot():
    assert _targeted_operation_files(), "the vault ships staged prompt operations"
    for p in _targeted_operation_files():
        assert "{{input}}" in p.read_text(encoding="utf-8"), f"{p.name} has no {{{{input}}}} slot"


def test_runner_lists_shipped_patterns_from_real_vault():
    listed = {p["id"] for p in patterns.list_patterns(SRC)}
    shipped = {p.stem for p in _prompt_operation_files()}
    assert listed == shipped


def test_runner_hides_local_worker_operations_from_patterns():
    result = patterns.run_pattern(SRC, "render-project-argument-canvas", "x")
    assert result["error"] == "unknown-pattern"
    assert "render-project-argument-canvas" not in result["available"]


def test_runner_composes_and_logs(tmp_path, monkeypatch):
    (tmp_path / "system/patterns").mkdir(parents=True)
    (tmp_path / "system/patterns/_preamble.md").write_text("VOICE", encoding="utf-8")
    _patch_operation_manifest(
        monkeypatch,
        "x",
        "---\ntitle: X\ntype: operation\ncheck_status: checked\n"
        "description: Test operation.\nposture: librarian\n"
        "mode: library\naction: a\ninput: note\noutput_target: 'knowledge/projects/'\n---\n"
        "P {{input}} Q\n",
    )
    r = patterns.run_pattern(tmp_path, "x", "BODY", "ref.md")
    assert "VOICE" in r["prompt"] and "P BODY Q" in r["prompt"]
    assert r["dry_run"] is False
    log = (tmp_path / "system/logs/patterns.jsonl").read_text(encoding="utf-8")
    assert '"pattern": "x"' in log


def test_runner_degrades_gated_targets_to_dry_run(tmp_path, monkeypatch):
    _patch_operation_manifest(
        monkeypatch,
        "bad",
        "---\ntitle: B\ntype: operation\ncheck_status: checked\n"
        "description: Test operation.\nposture: librarian\n"
        "mode: library\naction: a\ninput: note\noutput_target: 'knowledge/notes/'\n---\n"
        "Z {{input}}\n",
    )
    r = patterns.run_pattern(tmp_path, "bad", "x")
    assert r["dry_run"] is True and "note" in r


def test_runner_survives_provenance_write_failure(tmp_path, capsys, monkeypatch):
    """An unwritable provenance log degrades loudly: the run (the prompt) is still
    returned, flagged provenance_logged: false, with a stderr warning."""
    _patch_operation_manifest(
        monkeypatch,
        "x",
        "---\ntitle: X\ntype: operation\ncheck_status: checked\n"
        "description: Test operation.\nposture: librarian\n"
        "mode: library\naction: a\ninput: note\noutput_target: 'knowledge/projects/'\n---\n"
        "P {{input}} Q\n",
    )
    # system/logs exists as a FILE -> the jsonl append cannot create the dir
    (tmp_path / "system").mkdir()
    (tmp_path / "system" / "logs").write_text("not a directory", encoding="utf-8")
    r = patterns.run_pattern(tmp_path, "x", "BODY")
    assert r["provenance_logged"] is False
    assert "P BODY Q" in r["prompt"]  # the run itself still succeeds
    assert "provenance" in capsys.readouterr().err


def test_runner_refuses_non_current_and_unknown(tmp_path, monkeypatch):
    _patch_operation_manifest(
        monkeypatch,
        "draft",
        "---\ntitle: Draft\ntype: operation\ncheck_status: unchecked\n"
        "description: Draft operation.\n---\nP {{input}} Q\n",
    )
    assert patterns.run_pattern(tmp_path, "draft", "x")["error"] == "operation-not-checked"
    assert patterns.run_pattern(tmp_path, "ghost", "x")["error"] == "unknown-pattern"
