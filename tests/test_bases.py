"""Alpha.16 ships no Obsidian Base views."""

from pathlib import Path

SRC = Path(__file__).resolve().parent.parent / "vault-template"


def test_alpha16_ships_no_base_views():
    assert sorted(SRC.rglob("*.base")) == []
