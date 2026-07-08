"""Alpha.16 ships no Obsidian Base views."""

from tests.helpers import WORKSPACE_SEED


def test_alpha16_ships_no_base_views():
    assert sorted(WORKSPACE_SEED.rglob("*.base")) == []
