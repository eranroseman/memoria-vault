"""Prompt operations validate as product policies; the worker runner enforces rules."""

import re
from pathlib import Path

import yaml

from memoria_vault.runtime.operations import load_operation_policy
from memoria_vault.runtime.policy import REVIEW_GATED_PREFIXES

SRC = Path(__file__).resolve().parent.parent / "vault-template"
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


def test_shipped_operations_validate_against_policy_loader():
    shipped = _operation_files()
    assert len(shipped) >= 6, "the vault ships checked operation policies"
    for p in shipped:
        load_operation_policy(SRC, p.stem)


def test_no_shipped_prompt_operation_targets_a_gated_zone():
    assert _prompt_operation_files(), "the vault ships runnable prompt operations"
    for p in _prompt_operation_files():
        target = (_frontmatter(p).get("output_target") or "").lstrip("/")
        assert not target.startswith(REVIEW_GATED_PREFIXES), f"{p.name} targets a gated zone"


def test_every_targeted_operation_has_an_input_slot():
    assert _targeted_operation_files(), "the vault ships staged prompt operations"
    for p in _targeted_operation_files():
        assert "{{input}}" in p.read_text(encoding="utf-8"), f"{p.name} has no {{{{input}}}} slot"
