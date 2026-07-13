from __future__ import annotations

from pathlib import Path

import pytest

from tests.floor_lib import seed_vault, vault_digest


def test_floor_seed_builds_and_passes_detectors(tmp_path: Path) -> None:
    vault, manifest = seed_vault(tmp_path)
    # Preconditions every sweep case relies on:
    assert (vault / manifest["note_claim"]).is_file()
    assert (vault / manifest["note_question"]).is_file()
    assert (vault / manifest["project"]).is_file()
    assert (vault / ".memoria/memoria.sqlite").is_file()
    from test_vault.e2e_smoke import add_repo_paths  # noqa: F401  (scripts on pythonpath)

    from memoria_vault.runtime.subsystems.integrity.linter import detectors

    findings = detectors.run_all(vault)
    assert detectors.verdict(findings) == "PASS", findings


@pytest.mark.skip(reason="vault_digest lands in Task 3")
def test_floor_seed_is_deterministic(tmp_path: Path) -> None:
    a, _ = seed_vault(tmp_path / "a")
    b, _ = seed_vault(tmp_path / "b")
    assert vault_digest(a) == vault_digest(b)
