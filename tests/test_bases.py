"""The package seed ships no Obsidian Base views."""

from tests.helpers import WORKSPACE_SEED


def test_package_seed_ships_no_base_views():
    assert sorted(WORKSPACE_SEED.rglob("*.base")) == []
