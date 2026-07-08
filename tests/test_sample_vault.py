"""The retired alpha.10 sample vault is not shipped in the alpha.11 skeleton."""

from tests.helpers import ROOT, WORKSPACE_SEED

SAMPLE = WORKSPACE_SEED / ".memoria" / "samples" / "mediterranean-diet"
FOLDERS = WORKSPACE_SEED / ".memoria" / "schemas" / "folders.yaml"


def test_retired_sample_vault_is_not_bundled():
    assert not (ROOT / "sample-vault").exists()
    assert not any(SAMPLE.rglob("*.md"))


def test_retired_sample_commands_are_not_shipped():
    assert not (WORKSPACE_SEED / "system/scripts/load-sample-vault.js").exists()
    assert not (WORKSPACE_SEED / "system/scripts/remove-sample-vault.js").exists()


def test_retired_sample_skeleton_dirs_are_not_created():
    assert ".memoria/samples" not in FOLDERS.read_text(encoding="utf-8")
