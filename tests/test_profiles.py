"""The standalone runtime ships no installed Hermes profiles or lane overrides."""

from pathlib import Path

from tests.helpers import WORKSPACE_SEED

ROOT = Path(__file__).resolve().parent.parent


def test_installed_profile_packages_are_not_shipped():
    assert not (WORKSPACE_SEED / ".memoria/profiles").exists()


def test_lane_override_packages_are_not_shipped():
    assert not (WORKSPACE_SEED / ".memoria/lane-overrides").exists()


def test_profile_generator_is_retired():
    assert not (ROOT / "scripts/render_profile_configs.py").exists()


def test_profile_tool_registry_is_not_shipped():
    assert not (WORKSPACE_SEED / ".memoria/tool-registry.yaml").exists()
