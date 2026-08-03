"""The init template must be indistinguishable from a fresh `memoria init`."""

from __future__ import annotations

from pathlib import Path

import pytest

from memoria_vault.runtime import state
from tests import helpers

pytestmark = pytest.mark.contract


class _NullCapsys:
    def readouterr(self):  # matches the only capsys method the helper uses
        return type("Out", (), {"out": "", "err": ""})()


def test_template_workspace_matches_fresh_init(tmp_path: Path) -> None:
    from memoria_vault.cli import main

    templated = helpers.init_cli_workspace(tmp_path / "a", _NullCapsys())
    fresh = tmp_path / "b" / "workspace"
    assert main(["init", "--workspace", str(fresh), "--yes", "--quiet"]) == 0

    # `.git/objects/**` filenames are content hashes, and `.memoria/vault.json`
    # embeds a fresh `uuid.uuid4()` vault_id on every real `memoria init`
    # (src/memoria_vault/cli.py, minted once and pinned per vault) -- so two
    # independent real inits *always* diverge under `.git/objects`, by
    # design, regardless of templating. Structural equivalence (every
    # workspace path outside git internals) is the actual bar; `.git` being
    # a real repo is checked separately below.
    def _workspace_files(root: Path) -> set[Path]:
        return {
            p.relative_to(root)
            for p in root.rglob("*")
            if p.is_file() and ".git" not in p.relative_to(root).parts
        }

    assert _workspace_files(templated) == _workspace_files(fresh)

    # The DB must be live and current, and the vault git repo intact.
    with state.connect(templated) as conn:
        assert int(conn.execute("PRAGMA user_version").fetchone()[0]) == state.SCHEMA_VERSION
    assert (templated / ".git").is_dir()


def test_two_template_workspaces_are_independent(tmp_path: Path) -> None:
    a = helpers.init_cli_workspace(tmp_path / "a", _NullCapsys())
    b = helpers.init_cli_workspace(tmp_path / "b", _NullCapsys())
    (a / "notes").mkdir(exist_ok=True)
    (a / "notes" / "probe.md").write_text("x", encoding="utf-8")
    assert not (b / "notes" / "probe.md").exists()
