"""The retired alpha.10 sample vault is not shipped in the alpha.11 skeleton."""

from pathlib import Path

SRC = Path(__file__).resolve().parent.parent / "vault-template"
ROOT = SRC.parent
SAMPLE = SRC / ".memoria" / "samples" / "mediterranean-diet"
SCRIPTS = SRC / "system" / "scripts"
FOLDERS = SRC / ".memoria" / "schemas" / "folders.yaml"
MANIFEST = ROOT / "scripts" / "install" / "manifest.sh"


def test_retired_sample_vault_is_not_bundled():
    assert not (ROOT / "sample-vault").exists()
    assert not any(SAMPLE.rglob("*.md"))


def test_retired_sample_commands_are_not_shipped():
    assert not (SCRIPTS / "load-sample-vault.js").exists()
    assert not (SCRIPTS / "remove-sample-vault.js").exists()


def test_retired_sample_skeleton_dirs_are_not_created():
    assert ".memoria/samples" not in FOLDERS.read_text(encoding="utf-8")
    assert ".memoria/samples" not in MANIFEST.read_text(encoding="utf-8")
